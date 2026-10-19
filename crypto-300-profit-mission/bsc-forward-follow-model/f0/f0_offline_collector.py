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
ALLOWED_KINDS = frozenset({"detection", "receipt", "quote", "reorg"})
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
        self.queue: list[tuple[int, str, int]] = []
        self.pending_quotes: dict[tuple[str, int], dict] = {}
        self.trace: list[dict] = []
        self.now_ms = -1
        self.input_count = 0
        self.duplicate_count = 0
        self.input_hashes: set[str] = set()

    def _log(self, kind: str, **data: object) -> None:
        self.trace.append({"kind": kind, **data})

    def _run_due(self, until_ms: int) -> None:
        while self.queue and self.queue[0][0] <= until_ms:
            deadline, eid, delta = heapq.heappop(self.queue)
            event = self.events[eid]
            key = str(delta // 1000)
            if event.state in ("REJECTED", "INVALIDATED"):
                event.quote_state[key] = "REJECTED"
                self._log("quote_cancelled", event_id=eid, delta_seconds=delta // 1000,
                          reason="EVENT_INVALIDATED")
                continue
            event.quote_state[key] = "REQUEST_SCHEDULED_SYNTHETIC"
            self._log("quote_request_scheduled", event_id=eid, group=event.group,
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
        self._log("detected", event_id=eid, group=group, side=side, first_received_ms=e.first_received_ms,
                  actionable_ms=action, selected=selected, ingest_path=path)
        if selected and path != "BACKFILL" and side == "BUY":
            for delta in DELTAS_MS:
                heapq.heappush(self.queue, (action + delta, eid, delta))
        elif side == "UNKNOWN":
            self._log("excluded_from_l2", event_id=eid, reason="SIDE_UNKNOWN")
        elif path == "BACKFILL":
            self._log("excluded_from_l2", event_id=eid, reason="BACKFILL_NO_E3")

    def _receipt(self, x: dict) -> None:
        _require(x["event_id"] in self.events, "orphan receipt before detection")
        e = self.events[x["event_id"]]
        _require(e.state not in ("REJECTED", "INVALIDATED"), "receipt cannot resurrect rejected/reorg event")
        _require(x["tx_hash"] == e.tx_hash, "receipt transaction mismatch")
        _require(x["chain_id"] == 56, "receipt chain mismatch")
        # This is a synthetic fixture interface, not real receipt/RPC verification.
        if (x["status"] != 1 or x["tx_from"] != e.wallet or
                not isinstance(x["confirmations"], int) or x["confirmations"] < self.min_confirmations):
            e.state, e.reason = "REJECTED", "E1_FAILED_SYNTHETIC"
            for delta in DELTAS_MS:
                e.quote_state[str(delta // 1000)] = "REJECTED" if e.side == "BUY" else "NOT_SCHEDULED"
            self._log("receipt_rejected", event_id=e.event_id, reason=e.reason)
            return
        e.confirmations = x["confirmations"]
        e.block_hash = x["block_hash"]
        e.evidence = "E1_CONFIRMED_SYNTHETIC"
        e.state = "CONFIRMED"
        if e.side == "UNKNOWN":
            self._log("receipt_confirmed_unknown", event_id=e.event_id)
            return
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
        else:
            e.reason = "QUOTE_PATH_UNRESOLVED_SYNTHETIC"
        self._log("receipt_evaluated", event_id=e.event_id, evidence=e.evidence, state=e.state,
                  reason=e.reason)

    def _quote(self, x: dict) -> None:
        _require(x["event_id"] in self.events, "orphan quote")
        e = self.events[x["event_id"]]
        delta = x["delta_ms"]
        _require(delta in DELTAS_MS and isinstance(x["requested_ms"], int) and
                 isinstance(x["received_ms"], int) and x["received_ms"] >= x["requested_ms"],
                 "invalid quote time/delta")
        if not (e.selected and e.side == "BUY" and e.ingest_path != "BACKFILL"):
            self._log("quote_rejected", event_id=e.event_id, reason="INELIGIBLE_EVENT")
            return
        key = (e.event_id, delta)
        label = str(delta // 1000)
        scheduled = e.actionable_ms + delta
        _require(x["at_ms"] == x["received_ms"], "quote replay at_ms must be receipt time")
        _require(x["at_ms"] >= scheduled and e.quote_state.get(label) in
                 ("REQUEST_SCHEDULED_SYNTHETIC", "REJECTED"),
                 "quote cannot arrive before scheduled virtual request")
        _require(key not in self.pending_quotes, "duplicate quote response")
        self.pending_quotes[key] = dict(x)
        if e.state in ("REJECTED", "INVALIDATED"):
            e.quote_state[label] = "REJECTED"
            self._log("quote_rejected", event_id=e.event_id, delta_seconds=delta // 1000,
                      reason="E1_FAILED_OR_REORG")
        elif x["requested_ms"] != scheduled:
            e.quote_state[label] = "MISSED_DEADLINE"
            self._log("quote_missed", event_id=e.event_id, delta_seconds=delta // 1000,
                      scheduled_ms=scheduled, requested_ms=x["requested_ms"])
        else:
            e.quote_state[label] = "SYNTHETIC_REPLAY_QUOTE"
            self._log("quote_replay", event_id=e.event_id, group=e.group,
                      delta_seconds=delta // 1000, scheduled_ms=scheduled,
                      requested_ms=x["requested_ms"], received_ms=x["received_ms"],
                      source="SYNTHETIC_ONLY", raw_blob_sha256=_row_digest(x))

    def _reorg(self, x: dict) -> None:
        _require(x["event_id"] in self.events, "orphan reorg")
        e = self.events[x["event_id"]]
        _require(x["tx_hash"] == e.tx_hash, "reorg tx mismatch")
        e.state, e.reason = "INVALIDATED", "REORGED_SYNTHETIC"
        for delta in DELTAS_MS:
            if e.side == "BUY" and e.selected:
                e.quote_state[str(delta // 1000)] = "REJECTED"
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
            for seconds, state in list(event.quote_state.items()):
                if state == "REQUEST_SCHEDULED_SYNTHETIC":
                    event.quote_state[seconds] = "NO_QUOTE"
                    self._log("quote_missing", event_id=event.event_id, delta_seconds=int(seconds))
        quote_counts = Counter(q for e in self.events.values() for q in e.quote_state.values())
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
