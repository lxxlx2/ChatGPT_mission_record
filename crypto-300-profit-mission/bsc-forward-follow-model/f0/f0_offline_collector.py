#!/usr/bin/env python3
"""Bounded SYNTHETIC replay of the BSC F0 collector interfaces.

NO network endpoints, API credentials, background timers, wallets, signatures,
execution endpoints, or real price claims. All time is injected, never wall-clock.
"""
from __future__ import annotations

import argparse
import hashlib
import heapq
import json
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

SCHEMA = "bsc-forward-f0-offline-replay-v1"
DELTAS_MS = (60_000, 300_000, 900_000)
ALLOWED_KINDS = frozenset({"detection", "direction_update", "receipt", "quote", "reorg"})
FORBIDDEN_OUTCOME_KEYS = frozenset({
    "profit_rank", "pnl_30d", "pnl_lifetime", "win_rate", "score",
    "independently_closed_positive_major_count", "independently_closed_negative_major_count",
})
ALLOWED_GROUPS = frozenset({"WATCHLIST", "CONTROL_RANDOM"})


def _require(flag: bool, explanation: str) -> None:
    if not flag:
        raise ValueError(explanation)


def _ascii_wallet(s: str) -> str:
    _require(isinstance(s, str) and len(s) == 42 and s.startswith("0x") and
             all(c in "0123456789abcdef" for c in s[2:]), "invalid lowercase EVM wallet/CA")
    return s


def _hash32(s: str) -> int:
    h = 2166136261
    for byte in s.encode("ascii"):
        h = ((h ^ byte) * 16777619) & 0xffffffff
    return h


def _row_digest(row: dict) -> str:
    return hashlib.sha256(json.dumps(row, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":")).encode()).hexdigest()


def _check_allowed(row: dict) -> None:
    _require(not FORBIDDEN_OUTCOME_KEYS.intersection(row), "outcome data forbidden in collector inputs")


@dataclass
class Event:
    event_id: str
    group: str
    wallet: str
    tx_hash: str
    ca: str | None
    side: str
    first_received_ms: int
    actionable_ms: int | None
    ingest_path: str
    selected: bool
    trial: bool = True
    evidence: str = "E0_SEEN_SYNTHETIC"
    state: str = "SEEN"
    reason: str | None = None
    confirmations: int | None = None
    block_hash: str | None = None
    quote_state: dict = field(default_factory=dict)
    exit_quote_state: dict = field(default_factory=dict)
    receipt_input: dict | None = field(default=None, repr=False)


class OfflineReplay:
    """Pure, bounded clock-injected state-machine; NEVER actual E3 or QUOTED."""

    def __init__(self, control_seed: str = "f0-control-precommit-v1", control_modulo: int = 2,
                 min_confirmations: int = 2, routers: tuple[str, ...] = ()) -> None:
        _require(isinstance(control_seed, str) and control_seed and control_seed.isascii(), "invalid seed")
        _require(isinstance(control_modulo, int) and control_modulo >= 1, "invalid control modulo")
        _require(min_confirmations >= 1, "invalid confirmations")
        self.control_seed = control_seed
        self.control_modulo = control_modulo
        self.min_confirmations = min_confirmations
        self.routers = frozenset(_ascii_wallet(r) for r in routers)
        self.events: dict[str, Event] = {}
        self.queue: list[tuple[int, str, str, int]] = []
        self.pending_quotes: dict[tuple[str, str, int], dict] = {}
        self.tx_identity: dict[tuple[str, str], str] = {}
        self.trace: list[dict] = []
        self.now_ms = -1
        self.input_count = 0
        self.duplicate_count = 0
        self.input_hashes: set[str] = set()

    def _log(self, kind: str, **data: object) -> None:
        self.trace.append({"kind": kind, **data})

    @staticmethod
    def _quote_purpose(event: Event) -> str | None:
        return {"BUY": "ENTRY", "SELL": "EXIT"}.get(event.side)

    @staticmethod
    def _quote_states(event: Event, purpose: str) -> dict:
        return event.quote_state if purpose == "ENTRY" else event.exit_quote_state

    def _schedule_direction(self, event: Event) -> None:
        purpose = self._quote_purpose(event)
        if not purpose:
            return
        if not event.selected:
            self._log("excluded_from_l2", event_id=event.event_id, reason="CONTROL_NOT_SELECTED")
            return
        if event.ingest_path == "BACKFILL":
            self._log("excluded_from_l2", event_id=event.event_id, reason="BACKFILL_NO_E3")
            return
        # Pure virtual deadlines, NOT network requests. SELL tasks are separate
        # from BUY entry tasks and must never be mislabelled BUY quotes.
        for delta in DELTAS_MS:
            heapq.heappush(self.queue, (event.actionable_ms + delta,
                                        event.event_id, purpose, delta))

    def _reject_all_quotes(self, event: Event) -> None:
        purpose = self._quote_purpose(event)
        if not purpose or not event.selected or event.ingest_path == "BACKFILL":
            return
        states = self._quote_states(event, purpose)
        for delta in DELTAS_MS:
            states[str(delta // 1000)] = "REJECTED"

    def _run_due(self, until_ms: int) -> None:
        while self.queue and self.queue[0][0] <= until_ms:
            deadline, eid, purpose, delta = heapq.heappop(self.queue)
            event = self.events[eid]
            states = self._quote_states(event, purpose)
            label = str(delta // 1000)
            if event.state in ("REJECTED", "INVALIDATED"):
                states[label] = "REJECTED"
                self._log("quote_cancelled", event_id=eid, purpose=purpose,
                          delta_seconds=delta // 1000, reason="EVENT_INVALIDATED")
                continue
            states[label] = "REQUEST_SCHEDULED_SYNTHETIC"
            self._log("quote_request_scheduled" if purpose == "ENTRY" else
                      "exit_quote_request_scheduled", event_id=eid,
                      purpose=purpose, group=event.group,
                      delta_seconds=delta // 1000, scheduled_ms=deadline,
                      actual_real_request=False, source="SYNTHETIC_ONLY")

    def _detection(self, x: dict) -> None:
        eid = x["event_id"]
        _require(eid not in self.events, "duplicate conflicting event_id")
        _require(x["chain_id"] == 56, "F0 BSC-only")
        wallet = _ascii_wallet(x["wallet"])
        tx_hash = x["tx_hash"]
        _require(isinstance(tx_hash, str) and len(tx_hash) == 66 and tx_hash.startswith("0x") and
                 all(c in "0123456789abcdef" for c in tx_hash[2:]), "invalid tx hash")
        identity = (wallet, tx_hash)
        _require(identity not in self.tx_identity, "same wallet and tx cannot create another event_id")
        side, group, path = x["side"], x["group"], x["ingest_path"]
        _require(side in ("BUY", "SELL", "UNKNOWN") and group in ALLOWED_GROUPS and
                 path in ("WS", "POLL", "BACKFILL"), "invalid group/side/path")
        ca = _ascii_wallet(x["ca"]) if x.get("ca") is not None else None
        action = x.get("actionable_ms")
        _require((side == "UNKNOWN" and action is None) or
                 (side != "UNKNOWN" and ca is not None and isinstance(action, int)),
                 "BUY/SELL needs first live actionable timestamp and exact CA; UNKNOWN must not trigger L2")
        _require(isinstance(x["first_received_ms"], int) and
                 x["first_received_ms"] <= x["at_ms"] and
                 (action is None or action == x["at_ms"]), "backdated/future-actionable or invalid clock")
        _require(x.get("trial") is True, "offline replay accepts trial=true only")
        selected = group == "WATCHLIST" or _hash32(f"{self.control_seed}|{wallet}|{tx_hash}") % self.control_modulo == 0
        e = Event(eid, group, wallet, tx_hash, ca, side, x["first_received_ms"], action, path, selected)
        self.events[eid] = e
        self.tx_identity[identity] = eid
        self._log("detected", event_id=eid, group=group, side=side, first_received_ms=e.first_received_ms,
                  actionable_ms=action, selected=selected, ingest_path=path)
        if side == "UNKNOWN":
            self._log("excluded_from_l2", event_id=eid, reason="SIDE_UNKNOWN")
        else:
            self._schedule_direction(e)

    def _direction_update(self, x: dict) -> None:
        """Append-only UNKNOWN -> BUY/SELL identification, same event identity."""
        eid = x["event_id"]
        _require(eid in self.events, "orphan direction update")
        e = self.events[eid]
        _require(e.side == "UNKNOWN" and e.state not in ("REJECTED", "INVALIDATED"),
                 "direction update requires active UNKNOWN event")
        _require(x["chain_id"] == 56 and x["wallet"] == e.wallet and
                 x["tx_hash"] == e.tx_hash, "direction update identity mismatch")
        _require(x.get("side") in ("BUY", "SELL"), "direction update must identify BUY/SELL")
        ca = _ascii_wallet(x["ca"])
        _require(isinstance(x.get("actionable_ms"), int) and
                 x["actionable_ms"] == x["at_ms"] and
                 x["at_ms"] >= e.first_received_ms,
                 "direction update must timestamp first actual identification")
        _require(x.get("first_received_ms") == e.first_received_ms,
                 "direction update cannot rewrite first receive time")
        _require(x.get("trial") is True, "direction update requires trial=true")
        e.side = x["side"]
        e.ca = ca
        e.actionable_ms = x["actionable_ms"]
        self._log("direction_identified", event_id=eid, side=e.side, ca=ca,
                  first_received_ms=e.first_received_ms, actionable_ms=e.actionable_ms)
        self._schedule_direction(e)
        # A receipt may have arrived while the direction was still UNKNOWN.
        # Re-evaluate *only now*, never backdate this new trading signal.
        if e.receipt_input is not None:
            self._attest_flow(e, e.receipt_input)

    def _attest_flow(self, e: Event, x: dict) -> None:
        """Synthetic causal-path fixture assertion, NOT a real log decoder."""
        _require(x["router"] in self.routers, "router not on trial allowlist")
        flow = x.get("flow", {})
        token = flow.get("token", {})
        quote = flow.get("quote", {})
        proper = (
            flow.get("swap_route_connected") is True and
            token.get("ca") == e.ca and isinstance(token.get("raw"), str) and
            token["raw"].isdigit() and int(token["raw"]) > 0 and
            quote.get("ca") == x["quote_ca"] and isinstance(quote.get("raw"), str) and
            quote["raw"].isdigit() and int(quote["raw"]) > 0 and
            (e.side == "BUY" and token.get("to") == e.wallet and
             quote.get("from") == e.wallet and quote.get("to") == x["router"] or
             e.side == "SELL" and token.get("from") == e.wallet and
             quote.get("to") == e.wallet)
        )
        if proper:
            e.evidence = "E2_TRADE_ATTESTED_SYNTHETIC"
            e.state = "ATTESTED_TRIAL"
            e.reason = None
        else:
            e.reason = "QUOTE_PATH_UNRESOLVED_SYNTHETIC"
        self._log("receipt_evaluated", event_id=e.event_id, evidence=e.evidence,
                  state=e.state, reason=e.reason)

    def _receipt(self, x: dict) -> None:
        _require(x["event_id"] in self.events, "orphan receipt before detection")
        e = self.events[x["event_id"]]
        _require(e.state not in ("REJECTED", "INVALIDATED"),
                 "receipt cannot resurrect rejected/reorg event")
        _require(x["tx_hash"] == e.tx_hash, "receipt transaction mismatch")
        _require(x["chain_id"] == 56, "receipt chain mismatch")
        if (x["status"] != 1 or x["tx_from"] != e.wallet or
                not isinstance(x["confirmations"], int) or
                x["confirmations"] < self.min_confirmations):
            e.state, e.reason = "REJECTED", "E1_FAILED_SYNTHETIC"
            self._reject_all_quotes(e)
            self._log("receipt_rejected", event_id=e.event_id, reason=e.reason)
            return
        e.confirmations = x["confirmations"]
        e.block_hash = x["block_hash"]
        e.receipt_input = dict(x)
        e.evidence = "E1_CONFIRMED_SYNTHETIC"
        e.state = "CONFIRMED"
        if e.side == "UNKNOWN":
            self._log("receipt_confirmed_unknown", event_id=e.event_id)
            return
        self._attest_flow(e, x)

    @staticmethod
    def _response_verdict(x: dict) -> tuple[bool, str]:
        """Fail-closed quote adapter contract: explicit status plus positive raw amount."""
        if x.get("response_status") != "SUCCESS":
            return False, "ERROR_RESPONSE" if x.get("response_status") == "ERROR" or x.get("error") is not None else "MISSING_SUCCESS_STATUS"
        if x.get("error") is not None:
            return False, "ERROR_RESPONSE"
        amount = x.get("synthetic_amount_out_raw")
        if amount is None:
            return False, "MISSING_AMOUNT"
        if not isinstance(amount, str) or not amount.isascii() or not amount.isdecimal() or int(amount) <= 0:
            return False, "INVALID_AMOUNT"
        return True, "OK"

    def _quote(self, x: dict) -> None:
        _require(x["event_id"] in self.events, "orphan quote")
        e = self.events[x["event_id"]]
        delta = x["delta_ms"]
        _require(delta in DELTAS_MS and isinstance(x["requested_ms"], int) and
                 isinstance(x["received_ms"], int) and x["received_ms"] >= x["requested_ms"],
                 "invalid quote time/delta")
        purpose = x.get("purpose", "ENTRY")
        _require(purpose in ("ENTRY", "EXIT"), "unknown quote purpose")
        if not (e.selected and self._quote_purpose(e) == purpose and
                e.ingest_path != "BACKFILL"):
            self._log("quote_rejected", event_id=e.event_id,
                      purpose=purpose, reason="INELIGIBLE_EVENT")
            return
        key = (e.event_id, purpose, delta)
        label = str(delta // 1000)
        scheduled = e.actionable_ms + delta
        state = self._quote_states(e, purpose)
        _require(x["at_ms"] == x["received_ms"], "quote replay at_ms must be receipt time")
        _require(x["at_ms"] >= scheduled and state.get(label) in
                 ("REQUEST_SCHEDULED_SYNTHETIC", "REJECTED"),
                 "quote cannot arrive before scheduled virtual request")
        _require(key not in self.pending_quotes, "duplicate quote response")
        self.pending_quotes[key] = dict(x)
        if e.state in ("REJECTED", "INVALIDATED"):
            state[label] = "REJECTED"
            self._log("quote_rejected", event_id=e.event_id, purpose=purpose,
                      delta_seconds=delta // 1000, reason="E1_FAILED_OR_REORG")
        elif x["requested_ms"] != scheduled:
            state[label] = "MISSED_DEADLINE"
            self._log("quote_missed", event_id=e.event_id, purpose=purpose,
                      delta_seconds=delta // 1000, scheduled_ms=scheduled,
                      requested_ms=x["requested_ms"])
        else:
            valid, reason = self._response_verdict(x)
            if not valid:
                state[label] = "NO_QUOTE"
                self._log("quote_unavailable", event_id=e.event_id, purpose=purpose,
                          group=e.group, delta_seconds=delta // 1000,
                          reason=reason, raw_blob_sha256=_row_digest(x))
                return
            state[label] = "SYNTHETIC_REPLAY_QUOTE"
            self._log("quote_replay" if purpose == "ENTRY" else "exit_quote_replay",
                      event_id=e.event_id, purpose=purpose, group=e.group,
                      delta_seconds=delta // 1000, scheduled_ms=scheduled,
                      requested_ms=x["requested_ms"], received_ms=x["received_ms"],
                      synthetic_amount_out_raw=x["synthetic_amount_out_raw"],
                      source="SYNTHETIC_ONLY", raw_blob_sha256=_row_digest(x))

    def _reorg(self, x: dict) -> None:
        _require(x["event_id"] in self.events, "orphan reorg")
        e = self.events[x["event_id"]]
        _require(x["tx_hash"] == e.tx_hash, "reorg tx mismatch")
        e.state, e.reason = "INVALIDATED", "REORGED_SYNTHETIC"
        self._reject_all_quotes(e)
        self._log("reorg_invalidated", event_id=e.event_id)

    def ingest(self, row: dict) -> None:
        _require(isinstance(row, dict) and row.get("kind") in ALLOWED_KINDS,
                 "unknown replay row kind")
        _check_allowed(row)
        sig = _row_digest(row)
        if sig in self.input_hashes:
            self.duplicate_count += 1
            self._log("input_duplicate", digest=sig)
            return
        self.input_hashes.add(sig)
        when = row["at_ms"]
        _require(isinstance(when, int) and when >= self.now_ms, "out of order simulated clock")
        self._run_due(when)
        self.now_ms = when
        self.input_count += 1
        if row["kind"] == "detection":
            self._detection(row)
        elif row["kind"] == "direction_update":
            self._direction_update(row)
        elif row["kind"] == "receipt":
            self._receipt(row)
        elif row["kind"] == "quote":
            self._quote(row)
        else:
            self._reorg(row)

    def finish(self, end_ms: int) -> dict:
        _require(isinstance(end_ms, int) and end_ms >= self.now_ms, "bad finish time")
        self._run_due(end_ms)
        self.now_ms = end_ms
        counts = Counter((e.group, e.side, e.state) for e in self.events.values())
        for event in self.events.values():
            for purpose, states in (("ENTRY", event.quote_state),
                                    ("EXIT", event.exit_quote_state)):
                for seconds, state in list(states.items()):
                    if state == "REQUEST_SCHEDULED_SYNTHETIC":
                        states[seconds] = "NO_QUOTE"
                        self._log("quote_missing", event_id=event.event_id,
                                  purpose=purpose, delta_seconds=int(seconds))
        quote_counts = Counter(q for e in self.events.values()
                               for q in (*e.quote_state.values(), *e.exit_quote_state.values()))
        _require(not self.queue or self.queue[0][0] > end_ms, "unexecuted due task")
        result = {
            "schema": SCHEMA,
            "mode": "SYNTHETIC_TRIAL_ONLY_NO_CHAIN_NO_EXECUTION",
            "e3_actual_count": 0,
            "quoted_actual_count": 0,
            "paper_profit_labels": 0,
            "input_records": self.input_count,
            "duplicates_skipped": self.duplicate_count,
            "events": len(self.events),
            "selected_control_events": sum(e.group == "CONTROL_RANDOM" and e.selected for e in self.events.values()),
            "unknown_direction_events": sum(e.side == "UNKNOWN" for e in self.events.values()),
            "backfill_events": sum(e.ingest_path == "BACKFILL" for e in self.events.values()),
            "group_state_counts": {"/".join(k): v for k, v in sorted(counts.items())},
            "quote_counts": dict(sorted(quote_counts.items())),
            "event_rows": [
                {
                    "event_id": e.event_id, "group": e.group, "wallet": e.wallet,
                    "side": e.side, "selected": e.selected, "evidence": e.evidence,
                    "state": e.state, "reason": e.reason,
                    "quote_state": dict(sorted(e.quote_state.items())),
                    "exit_quote_state": dict(sorted(e.exit_quote_state.items())),
                    "first_received_ms": e.first_received_ms,
                    "actionable_ms": e.actionable_ms,
                    "trial": True, "source": "SYNTHETIC_ONLY",
                }
                for e in sorted(self.events.values(), key=lambda x: x.event_id)
            ],
            "audit_trace": self.trace,
            "safety": ["NO_NETWORK", "NO_TRADE", "NO_NOTIFICATIONS", "NO_REAL_TIME_QUOTE"],
        }
        return result


def replay_fixture(fixture: dict) -> dict:
    _require(fixture.get("schema") == SCHEMA and fixture.get("mode") == "SYNTHETIC_ONLY",
             "Only schema-labeled synthetic fixtures are accepted")
    c = fixture.get("config", {})
    engine = OfflineReplay(control_seed=c.get("control_seed", "f0-control-precommit-v1"),
                           control_modulo=c.get("control_modulo", 2),
                           min_confirmations=c.get("min_confirmations", 2),
                           routers=tuple(c.get("trial_routers", [])))
    for row in fixture["records"]:
        engine.ingest(row)
    return engine.finish(fixture["end_ms"])


def main() -> None:
    parser = argparse.ArgumentParser(description="OFFLINE SYNTHETIC F0 only — no RPC")
    parser.add_argument("--fixture", required=True, type=Path)
    parser.add_argument("--report", type=Path, help="optional local JSON output file; never auto-commits")
    args = parser.parse_args()
    fixture_bytes = args.fixture.read_bytes()
    result = replay_fixture(json.loads(fixture_bytes))
    result["fixture_sha256"] = hashlib.sha256(fixture_bytes).hexdigest()
    contents = json.dumps(result, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(contents, encoding="utf-8")
    else:
        print(contents, end="")


if __name__ == "__main__":
    main()
