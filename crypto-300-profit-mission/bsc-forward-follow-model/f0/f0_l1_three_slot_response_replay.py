#!/usr/bin/env python3
"""Offline three-slot response-envelope replay. NO HTTP, WS, callback or permit.

Only verifies pre-recorded byte frames against an already-generated synthetic
coordinator trace. A malformed frame cannot replan that trace; never equate
this gate with a live closed-loop dispatcher or real provider performance.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

from f0_l1_http_wire import parse_http_response, valid_rpc_payload
from f0_l1_offline_capacity import replay_timings
from f0_l1_three_slot_offline import simulate, _synthetic_hash
from f0_rpc_adapter import block_candidates, hexb

SCHEMA = "bsc-f0-three-slot-offline-envelope-replay-v1"


def need(ok, code):
    if not ok:
        raise ValueError(code)


def payload_for(reserve):
    method, rid, height = reserve["method"], reserve["id"], reserve["height"]
    need(method in ("eth_chainId", "eth_blockNumber", "eth_getBlockByNumber"),
         "REPLAY_METHOD_FORBIDDEN")
    params = [hex(height), True] if method == "eth_getBlockByNumber" else []
    return valid_rpc_payload({"jsonrpc": "2.0", "id": rid,
                              "method": method, "params": params})


def fake_frames(sim):
    """Generate HTTP-shaped SYNTHETIC, not actual BSC provider, response bytes."""
    need(sim.get("actual_network_requests") == 0, "REPLAY_LIVE_SIMULATION_FORBIDDEN")
    pending, frames, hi = {}, {}, 0
    for e in sim["trace"]:
        if e["event"] == "RESERVE_UNKNOWN":
            pending[e["id"]] = e
        if e["event"] != "SETTLE":
            continue
        rid = e["id"]
        need(rid in pending, "REPLAY_FRAME_UNRESERVED")
        r = pending[rid]
        if r["method"] == "eth_chainId":
            result = "0x38"
        elif r["method"] == "eth_blockNumber":
            need(hi < len(sim["head_samples"]), "REPLAY_MISSING_HEAD_SAMPLE")
            sample = sim["head_samples"][hi]
            need(abs(sample["at_ms"] - e["at_ms"]) < .01,
                 "REPLAY_HEAD_TIMESTAMP_MISMATCH")
            result = hex(sample["head"])
            hi += 1
        else:
            h = r["height"]
            result = {"number": hex(h),
                      "hash": "0x" + _synthetic_hash(h),
                      "parentHash": "0x" + _synthetic_hash(h - 1),
                      "transactions": []}
        ident = rid + 10000 if e["state"] == "WRONG_REQUEST_ID" else rid
        raw = json.dumps({"jsonrpc": "2.0", "id": ident, "result": result},
                         separators=(",", ":"), sort_keys=True).encode()
        frames[rid] = (503 if e["state"] in ("FAILED", "TIMEOUT") else 200,
                       {"Content-Type": "application/json"}, raw)
    need(hi == len(sim["head_samples"]), "REPLAY_HEAD_SAMPLE_COUNT_MISMATCH")
    return frames


def replay(sim, frames):
    """Validate in-memory saved HTTP-shaped frames; never sends requests.

    Valid replay cross-checks full blocks, ordered parent links and schedule
    reservations. Bad frames give a failed diagnostic, never successful trades.
    """
    need(sim.get("actual_network_requests") == 0 and
         sim.get("mode") == "OFFLINE_SYNTHETIC_EVENT_SIMULATION_ONLY" and
         isinstance(frames, dict), "REPLAY_ONLY_SYNTHETIC_SCHEDULE")
    pending, all_reservations = {}, {}
    received, committed, links = 0, 0, 0
    missing, faults, buffered = [], [], {}
    latest_head, last_head_ms, next_commit, last_hash = None, None, None, None
    head_index, last_start, max_active = 0, None, 0
    for e in sim["trace"]:
        event = e["event"]
        if event == "RESERVE_UNKNOWN":
            rid = e["id"]
            need(type(rid) is int and rid not in all_reservations and
                 len(pending) < 3, "REPLAY_SLOT_OR_ID_VIOLATION")
            if last_start is not None:
                need(e["at_ms"] - last_start >= 249.998,
                     "REPLAY_GLOBAL_SPACING_VIOLATION")
            last_start = e["at_ms"]
            request = payload_for(e)
            if e["category"] == "BLOCK":
                need(latest_head is not None and e["height"] <= latest_head and
                     e["at_ms"] - last_head_ms < 4000,
                     "REPLAY_DISPATCH_WITHOUT_FRESH_HEAD")
            pending[rid] = (e, request)
            all_reservations[rid] = (e, request)
            max_active = max(max_active, len(pending))
        elif event == "SETTLE":
            rid = e["id"]
            need(rid in pending, "REPLAY_UNRESERVED_SETTLEMENT")
            reservation, request = pending.pop(rid)
            need(e["method"] == request["method"] and
                 e["category"] == reservation["category"],
                 "REPLAY_SETTLEMENT_METHOD_MISMATCH")
            method = request["method"]
            try:
                need(rid in frames and type(frames[rid]) is tuple and
                     len(frames[rid]) == 3, "REPLAY_MISSING_FRAME")
                status, headers, body = frames[rid]
                envelope = parse_http_response(status, headers, body, request)
                value = envelope["result"]
                if method == "eth_chainId":
                    need(value == "0x38", "REPLAY_CHAIN_NOT_BSC")
                elif method == "eth_blockNumber":
                    need(isinstance(value, str) and value.startswith("0x") and
                         len(value) > 2 and int(value, 16) > 0,
                         "REPLAY_BAD_HEAD_VALUE")
                    height = int(value, 16)
                    need(head_index < len(sim["head_samples"]) and
                         height == sim["head_samples"][head_index]["head"],
                         "REPLAY_HEAD_NOT_MATCHING_RECORDED_SCHEDULE")
                    need(latest_head is None or height >= latest_head,
                         "REPLAY_HEAD_REGRESSION")
                    latest_head, last_head_ms = height, e["at_ms"]
                    if next_commit is None:
                        next_commit = height + 1
                    head_index += 1
                else:
                    data = block_candidates(envelope, set(), set())
                    height = reservation["height"]
                    need(data["block_number"] == height, "REPLAY_BLOCK_HEIGHT_MISMATCH")
                    need(height >= next_commit and height not in buffered,
                         "REPLAY_BLOCK_DUPLICATE_OR_BACKWARD")
                    received += 1
                    buffered[height] = (data["block_hash"],
                                        hexb(value["parentHash"], 32))
                    while next_commit in buffered:
                        block_hash, parent = buffered[next_commit]
                        if last_hash is not None and parent != last_hash:
                            faults.append({"id": rid, "height": next_commit,
                                           "reason": "REPLAY_PARENT_MISMATCH"})
                            break
                        if last_hash is not None:
                            links += 1
                        buffered.pop(next_commit)
                        committed += 1
                        last_hash = block_hash
                        next_commit += 1
            except (ValueError, TypeError, KeyError, OverflowError) as exc:
                faults.append({"id": rid, "height": reservation["height"],
                               "reason": str(exc)[:90]})
                if method == "eth_getBlockByNumber":
                    missing.append(reservation["height"])
        elif event == "DUPLICATE_IGNORED":
            need(e["id"] in all_reservations and e["id"] not in pending,
                 "REPLAY_INVALID_DUPLICATE_RECEIPT")
        elif event != "COMMIT":
            raise ValueError("REPLAY_UNKNOWN_TRACE_EVENT")
    need(not pending or sim["stop_state"] == "SIMULATED_PROCESS_CRASH_OUTCOME_UNKNOWN",
         "REPLAY_UNKNOWN_PENDING_REQUEST")
    need(len(all_reservations) == sim["requested_total"] and
         len(all_reservations) <= 32 and
         sum(row["method"] == "eth_getBlockByNumber"
             for row, _ in all_reservations.values()) <= 24 and
         sum(row["category"] == "HEAD_REFRESH"
             for row, _ in all_reservations.values()) <= 6,
         "REPLAY_GLOBAL_BUDGET_INVALID")
    valid = not faults and not pending and head_index == len(sim["head_samples"])
    all_attempted = [r["height"] for r, _ in all_reservations.values()
                     if r["category"] == "BLOCK"]
    return {
        "schema": SCHEMA,
        "source": "IN_MEMORY_SYNTHETIC_HTTP_SHAPED_FRAMES",
        "actual_new_rpc_requests": 0, "live_sender_present": False,
        "reactive_to_frame_failure": False,
        "real_concurrent_provider_capacity": "UNVERIFIED",
        "overall_valid": valid,
        "total_attempts": len(all_reservations),
        "head_refreshes": sum(r["category"] == "HEAD_REFRESH"
                              for r, _ in all_reservations.values()),
        "block_attempts": len(all_attempted),
        "max_inflight_including_head": max_active,
        "received_parsed_blocks": received,
        "contiguous_committed_blocks": committed,
        "verified_internal_parent_links": links,
        "first_block_independently_anchored": False,
        "failed_attempted_heights": sorted(set(missing)),
        "known_unattempted_heights_last_sampled":
            max(0, latest_head - max(all_attempted, default=latest_head))
            if latest_head is not None else None,
        "buffered_uncommitted_heights": sorted(buffered),
        "integrity_faults": faults,
        "unsettled_request_count": len(pending),
        "virtual_elapsed_ms": sim["virtual_elapsed_ms"],
        "contiguous_commit_bps": round(1000*committed/sim["virtual_elapsed_ms"],3)
            if sim["virtual_elapsed_ms"] else 0.0,
        "simulated_source_stop": sim["stop_state"],
        "global_tip_independently_checked": False,
        "f0_status": "NOT_PASSED",
    }


def main():
    cli = argparse.ArgumentParser(description="OFFLINE saved30 synthetic RPC-frame audit")
    cli.add_argument("--journal", type=Path, required=True)
    cli.add_argument("--expected-sha256", required=True)
    cli.add_argument("--output-dir", type=Path, required=True)
    a = cli.parse_args()
    observed, durations = replay_timings(a.journal.read_bytes(), a.expected_sha256)
    root = a.output_dir
    need(root.is_dir() and not root.is_symlink() and
         root.stat().st_mode & 0o077 == 0, "REPLAY_PRIVATE_OUTPUT_REQUIRED")
    cases = []
    for policy in ("checkpoint", "availability_wait"):
        for factor in (1.0, 1.5, 2.0):
            name = policy + "-" + str(int(factor * 10))
            sim = simulate(durations, root / (name + ".jsonl"),
                           head_policy=policy, min_head_refresh_age_ms=1500,
                           slowdown=factor, inflight_slots=3,
                           max_total_attempts=32, max_blocks=24,
                           max_refreshes=6, min_start_spacing_ms=250)
            row = replay(sim, fake_frames(sim))
            row.update(policy=policy, slowdown=factor)
            cases.append(row)
    print(json.dumps({
        "schema":"bsc-f0-saved30-offline-frame-six-scenario-v1",
        "actual_rpc_requests":0, "raw_rpc_frames_from_network":False,
        "saved_input_sha256_verified":observed["journal_sha256"],
        "cases":cases, "decision":"OFFLINE_PROTOCOL_ONLY_PRODUCTION_NO_GO",
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
