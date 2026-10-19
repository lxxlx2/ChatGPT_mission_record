#!/usr/bin/env python3
"""Offline-only seam: saved BSC JSON-RPC -> provisional OfflineReplay events.

STRICT LIMITS: no sockets, actual observation clocks, E1 finality, E2 swap causality,
E3, live QUOTED, executed trades, paper PnL or automated timers. Archive eth_call
quotes are NEVER passed into OfflineReplay as timed responses. Only explicit
synthetic virtual responses from a separately named fixture field may do that.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from f0_offline_collector import OfflineReplay, SCHEMA as STATE_SCHEMA
from f0_rpc_adapter import (
    address, block_candidates, decode_get_amounts_out, digest,
    envelope, hexb, hexnum, receipt_observation,
)

SCHEMA = "bsc-f0-offline-rpc-state-bridge-v1"


def require(value: bool, reason: str) -> None:
    if not value:
        raise ValueError(reason)


def clock(value: object, name: str) -> int:
    require(type(value) is int and value >= 0, f"INVALID_INJECTED_CLOCK:{name}")
    return value


def event_id(wallet: str, tx_hash: str) -> str:
    return "f0-" + hashlib.sha256(("56|" + wallet + "|" + tx_hash).encode("ascii")).hexdigest()[:24]


def bridge_fixture(fixture: dict) -> dict:
    require(isinstance(fixture, dict) and fixture.get("schema") == SCHEMA and
            fixture.get("mode") == "OFFLINE_BRIDGE_FIXTURE_ONLY" and
            fixture.get("trial") is True and fixture.get("chain_id") == 56,
            "BRIDGE_ONLY_OFFLINE_TRIAL_INPUT")
    watched = {address(x) for x in fixture["watchlist"]}
    routers = {address(x) for x in fixture["routers"]}
    assets = {address(x) for x in fixture["quote_assets"]}
    require(routers and assets and fixture.get("blocks"), "MISSING_OFFLINE_BRIDGE_INPUTS")
    replay = OfflineReplay(
        control_seed=fixture.get("control_seed", "f0-control-precommit-v1"),
        control_modulo=fixture.get("control_modulo", 2),
        min_confirmations=fixture.get("min_confirmations", 2),
        routers=tuple(sorted(routers)),
    )
    # Build an in-memory, time-ordered replay plan. Future receipt details are
    # not used to construct earlier detections or to select random controls.
    scheduled = []
    tx_lookup = {}
    raw_provenance = []
    order = 0
    for block_pack in fixture["blocks"]:
        observed_ms = clock(block_pack["observed_ms"], "block_observed_ms")
        path = block_pack["ingest_path"]
        require(path in ("WS", "POLL", "BACKFILL"), "UNKNOWN_INGEST_PATH")
        parsed = block_candidates(block_pack["rpc"], watched, routers)
        raw_provenance.append({"source": "SAVED_FULL_BLOCK", "sha256": parsed["raw_rpc_sha256"],
                               "block": parsed["block_number"], "observed_ms": observed_ms})
        for tx in parsed["candidates"]:
            tx_hash = tx["tx_hash"]
            require(tx_hash not in tx_lookup, "REPEATED_TX_IN_BRIDGE_BATCH")
            group = "WATCHLIST" if tx["group"] == "WATCHLIST" else "CONTROL_RANDOM"
            eid = event_id(tx["wallet"], tx_hash)
            tx_lookup[tx_hash] = (eid, tx)
            detection = {"kind": "detection", "at_ms": observed_ms,
                         "first_received_ms": observed_ms, "actionable_ms": None,
                         "chain_id": 56, "event_id": eid, "wallet": tx["wallet"],
                         "tx_hash": tx_hash, "side": "UNKNOWN", "ca": None,
                         "group": group, "ingest_path": path, "trial": True}
            scheduled.append((observed_ms, 0, order, "engine", detection))
            order += 1
        for receipt_pack in block_pack.get("receipts", []):
            receipt_at = clock(receipt_pack["observed_ms"], "receipt_observed_ms")
            require(receipt_at >= observed_ms, "RECEIPT_PRECEDES_BLOCK_OBSERVATION")
            raw = receipt_pack["rpc"]
            obj = envelope(raw)
            require(isinstance(obj, dict), "INVALID_SAVED_RECEIPT")
            tx_hash = hexb(obj["transactionHash"], 32)
            require(tx_hash in tx_lookup, "RECEIPT_FOR_UNOBSERVED_TX")
            eid, tx = tx_lookup[tx_hash]
            parsed_r = receipt_observation(raw, tx, receipt_pack["tip_number"],
                                           assets, routers)
            raw_provenance.append({"source": "SAVED_RECEIPT", "sha256": parsed_r["raw_rpc_sha256"],
                                   "tx_hash": tx_hash, "observed_ms": receipt_at})
            # A receipt-side BUY_CANDIDATE is an unverified Transfer-flow hint:
            # do NOT call the synthetic E2 attest method with fabricated swap logs.
            # Nor can receipt confirmations be asserted as F1 finalized.
            scheduled.append((receipt_at, 1, order, "provisional_receipt",
                              {"event_id": eid, "tx": tx, "parsed": parsed_r,
                               "observed_ms": receipt_at, "receipt": obj}))
            order += 1
    for q in fixture.get("archive_quotes", []):
        at = clock(q["observed_ms"], "archive_quote_observed_ms")
        decoded = decode_get_amounts_out(q["rpc"], q["expected_path_length"])
        raw_provenance.append({"source": "SAVED_ARCHIVE_ETH_CALL", "sha256": decoded["raw_rpc_sha256"],
                               "observed_ms": at})
        scheduled.append((at, 3, order, "archive_quote", decoded))
        order += 1
    for item in fixture.get("virtual_quotes", []):
        require(item.get("synthetic_response") is True, "LIVE_OR_ARCHIVE_QUOTE_AS_SYNTHETIC_FORBIDDEN")
        tx_hash = hexb(item["tx_hash"], 32)
        require(tx_hash in tx_lookup, "VIRTUAL_QUOTE_FOR_UNOBSERVED_TX")
        eid, _ = tx_lookup[tx_hash]
        received = clock(item["received_ms"], "virtual_quote_received_ms")
        requested = clock(item["requested_ms"], "virtual_quote_requested_ms")
        row = {"kind": "quote", "event_id": eid,
               "purpose": item["purpose"], "delta_ms": item["delta_ms"],
               "at_ms": received, "requested_ms": requested, "received_ms": received,
               "response_status": item.get("response_status"),
               "synthetic_amount_out_raw": item.get("synthetic_amount_out_raw"),
               "error": item.get("error")}
        scheduled.append((received, 2, order, "engine", row))
        order += 1
    for r in fixture.get("synthetic_reorgs", []):
        require(r.get("synthetic_reorg") is True, "UNVERIFIED_REORG_SOURCE")
        tx_hash = hexb(r["tx_hash"], 32)
        require(tx_hash in tx_lookup, "REORG_FOR_UNOBSERVED_TX")
        t = clock(r["observed_ms"], "reorg_observed_ms")
        scheduled.append((t, 1, order, "engine",
                          {"kind": "reorg", "event_id": tx_lookup[tx_hash][0],
                           "tx_hash": tx_hash, "at_ms": t}))
        order += 1
    scheduled.sort(key=lambda row: row[:3])
    updates, archived = [], []
    for at, _, _, kind, payload in scheduled:
        if kind == "engine":
            replay.ingest(payload)
        elif kind == "archive_quote":
            # Return archive evidence in a separate table ONLY; never invent a
            # time-qualified quote request from an historical eth_call envelope.
            archived.append({**payload, "bridge_observed_ms": at,
                             "usable_as_live_quoted": False})
        else:
            parsed = payload["parsed"]
            eid = payload["event_id"]
            event = replay.events[eid]
            update = {"event_id": eid, "source": "SAVED_RECEIPT",
                      "raw_rpc_sha256": parsed["raw_rpc_sha256"],
                      "observed_ms": at, "side_hint": parsed["side_hint"],
                      "ca_hint": parsed["ca_hint"], "reason": parsed["reason"],
                      "receipt_success": parsed["receipt_success"],
                      "confirmations_seen": parsed["confirmations_seen"],
                      "finality": "UNRESOLVED_F1_POLICY", "E2_attested": False}
            updates.append(update)
            if not parsed["receipt_success"]:
                # Failed receipt can reject a tentative event, never attest one.
                replay.ingest({"kind": "receipt", "at_ms": at, "chain_id": 56,
                               "event_id": eid, "tx_hash": event.tx_hash,
                               "tx_from": event.wallet, "status": 0,
                               "confirmations": 0, "block_hash": payload["tx"]["block_hash"]})
            elif parsed["side_hint"] in ("BUY_CANDIDATE", "SELL_CANDIDATE") and event.side == "UNKNOWN" and event.state not in ("REJECTED", "INVALIDATED"):
                replay.ingest({"kind": "direction_update", "at_ms": at,
                               "first_received_ms": event.first_received_ms,
                               "actionable_ms": at, "chain_id": 56,
                               "event_id": eid, "wallet": event.wallet,
                               "tx_hash": event.tx_hash,
                               "side": "BUY" if parsed["side_hint"] == "BUY_CANDIDATE" else "SELL",
                               "ca": parsed["ca_hint"], "trial": True})
            # NO success _receipt()/E1 attestation, even if tip-confirmations
            # exceeds the synthetic engine's threshold: finality is unresolved.
    end_ms = clock(fixture["end_ms"], "end_ms")
    report = replay.finish(end_ms)
    require(report["e3_actual_count"] == report["quoted_actual_count"] ==
            report["paper_profit_labels"] == 0, "REAL_LABEL_LEAK")
    require(all(row["evidence"] == "E0_SEEN_SYNTHETIC" for row in report["event_rows"] if
                row["state"] != "REJECTED" and row["state"] != "INVALIDATED"),
            "UNVERIFIED_CANDIDATE_UPGRADED")
    return {"schema": SCHEMA, "mode": "OFFLINE_BRIDGE_FIXTURE_ONLY",
            "trial": True, "clock_provenance": "INJECTED_OFFLINE_TIMESTAMPS_NOT_PUBLIC_FIRST_SEEN",
            "events_from_rpc": len(tx_lookup), "receipt_observations": updates,
            "archive_quote_observations": archived, "source_provenance": raw_provenance,
            "state_machine": report, "actual_rpc_calls": 0, "e3_actual_count": 0,
            "quoted_actual_count": 0, "paper_profit_labels": 0,
            "live_control_coverage": "NOT_MEASURED",
            "independent_denominator": "NOT_MEASURED",
            "finality_rule": "UNRESOLVED_F1_POLICY",
            "safety": ["SYNTHETIC_TIME", "NO_NETWORK", "NO_TRADE", "NO_REAL_QUOTES", "NO_E2_ATTESTATION"]}


def main() -> None:
    parser = argparse.ArgumentParser(description="Offline saved-RPC -> trial state machine; NEVER real RPC")
    parser.add_argument("--fixture", required=True, type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    raw = args.fixture.read_bytes()
    report = bridge_fixture(json.loads(raw))
    report["fixture_sha256"] = hashlib.sha256(raw).hexdigest()
    text = json.dumps(report, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(text, encoding="utf-8")
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
