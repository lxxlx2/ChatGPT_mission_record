#!/usr/bin/env python3
"""Offline F0 three-slot HEAD-budget postmortem from synthetic coordinator events.

Only reads an independently SHA-verified saved local Journal for request-duration
samples. Calls the PREVIOUSLY APPROVED offline simulation, never any transport.
No RPC, WS, user permit, private wallet/tx fields, background job or live code.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path

from f0_l1_offline_capacity import replay_timings
from f0_l1_three_slot_offline import SCHEMA as SIM_SCHEMA, simulate

SCHEMA = "bsc-f0-three-slot-head-budget-diagnosis-offline-v1"


def require(ok, code):
    if not ok:
        raise ValueError(code)


def diagnose(report: dict, *, refresh_after: int, head_freshness_ms: int = 4000,
             max_blocks: int = 24, max_refreshes: int = 6):
    """Analyze event provenance, not a real HEAD/call transcript.

    Refresh cause is primary priority: no eligible height, periodic checkpoint,
    then HEAD age. All overlapping triggers are counted separately as flags.
    """
    require(type(report) is dict and report.get("schema") == SIM_SCHEMA and
            report.get("actual_network_requests") == 0 and
            report.get("mode") == "OFFLINE_SYNTHETIC_EVENT_SIMULATION_ONLY" and
            type(refresh_after) is int and 1 <= refresh_after <= 8 and
            type(head_freshness_ms) is int and head_freshness_ms >= 250 and
            type(max_blocks) is int and 1 <= max_blocks <= 24 and
            type(max_refreshes) is int and 0 <= max_refreshes <= 6 and
            isinstance(report.get("trace"), list) and
            isinstance(report.get("head_samples"), list),
            "DIAGNOSIS_INVALID_INPUT")
    trace = report["trace"]
    samples = report["head_samples"]
    head_index = 0
    sampled_head = None
    head_completed_ms = None
    next_height = None
    blocks_since_refresh = 0
    pending_heads = {}
    refreshes = []
    triggers = Counter()
    trigger_flags = Counter()
    blocks_while_refresh_pending = 0
    block_reservations = []
    inflight = {}
    active = 0
    last_event_ms = 0.0
    occupied_slot_ms = 0.0
    maximum_active = 0
    for event in trace:
        require(isinstance(event, dict) and event.get("event") in
                ("RESERVE_UNKNOWN", "SETTLE", "COMMIT", "DUPLICATE_IGNORED") and
                type(event.get("at_ms")) in (int, float) and
                event["at_ms"] + 0.00001 >= last_event_ms,
                "DIAGNOSIS_EVENT_ORDER_INVALID")
        t = event["at_ms"]
        occupied_slot_ms += active * max(0, t - last_event_ms)
        last_event_ms = t
        kind = event["event"]
        if kind == "RESERVE_UNKNOWN":
            request_id = event["id"]
            require(type(request_id) is int and request_id not in inflight,
                    "DIAGNOSIS_DUPLICATE_REQUEST_ID")
            inflight[request_id] = event["category"]
            active += 1
            maximum_active = max(maximum_active, active)
            category = event["category"]
            if category == "HEAD_REFRESH":
                require(sampled_head is not None and
                        head_completed_ms is not None and
                        not pending_heads and next_height is not None,
                        "DIAGNOSIS_HEAD_RESERVATION_INVALID")
                no_height = next_height > sampled_head
                checkpoint = blocks_since_refresh >= refresh_after
                expired = t - head_completed_ms >= head_freshness_ms
                require(no_height or checkpoint or expired,
                        "DIAGNOSIS_UNEXPLAINED_HEAD_REFRESH")
                flags = [name for name, yes in
                         (("NO_ELIGIBLE_HEIGHT", no_height),
                          ("DISPATCH_CHECKPOINT", checkpoint),
                          ("HEAD_STALE", expired)) if yes]
                for name in flags:
                    trigger_flags[name] += 1
                primary = flags[0]
                triggers[primary] += 1
                record = {
                    "id": request_id, "at_ms": t, "primary_trigger": primary,
                    "trigger_flags": flags, "last_confirmed_head": sampled_head,
                    "next_unattempted_height": next_height,
                    "available_heights_at_reservation":
                        max(0, sampled_head - next_height + 1),
                    "age_of_last_head_ms": round(t - head_completed_ms, 3),
                    "blocks_dispatched_since_previous_refresh":
                        blocks_since_refresh,
                }
                refreshes.append(record)
                pending_heads[request_id] = record
                blocks_since_refresh = 0
            elif category == "BLOCK":
                require(sampled_head is not None and
                        head_completed_ms is not None and
                        type(event.get("height")) is int and
                        event["height"] == next_height and
                        event["height"] <= sampled_head and
                        t - head_completed_ms < head_freshness_ms,
                        "DIAGNOSIS_BLOCK_WITHOUT_FRESH_CONFIRMED_HEAD")
                block_reservations.append(t)
                blocks_since_refresh += 1
                next_height += 1
                if pending_heads:
                    blocks_while_refresh_pending += 1
        elif kind == "SETTLE":
            request_id = event["id"]
            require(request_id in inflight, "DIAGNOSIS_SETTLE_WITHOUT_RESERVATION")
            category = inflight.pop(request_id)
            active -= 1
            require(category == event.get("category"),
                    "DIAGNOSIS_SETTLE_CATEGORY_MISMATCH")
            if category in ("INITIAL_HEAD", "HEAD_REFRESH"):
                require(head_index < len(samples),
                        "DIAGNOSIS_HEAD_SAMPLE_COUNT_INVALID")
                sample = samples[head_index]
                head_index += 1
                require(abs(sample["at_ms"] - t) < 0.01 and
                        type(sample["head"]) is int,
                        "DIAGNOSIS_HEAD_SAMPLE_TIME_INVALID")
                old_head = sampled_head
                sampled_head = sample["head"]
                head_completed_ms = t
                if category == "INITIAL_HEAD":
                    require(next_height is None,
                            "DIAGNOSIS_DUPLICATE_INITIAL_HEAD")
                    next_height = sampled_head + 1
                else:
                    require(request_id in pending_heads,
                            "DIAGNOSIS_UNKNOWN_PENDING_REFRESH")
                    row = pending_heads.pop(request_id)
                    row["completed_at_ms"] = t
                    row["refresh_latency_ms"] = round(t-row["at_ms"], 3)
                    row["newly_observed_heights"] = sampled_head-old_head
                    row["available_heights_after_completion"] = max(
                        0, sampled_head-next_height+1)
    require(head_index == len(samples) and
            maximum_active <= report["max_allowed_inflight"] and
            len(block_reservations) == report["block_attempts"] and
            len(refreshes) == report["head_refreshes_requested"] and
            not pending_heads and
            active == report["inflight_outcome_unknown_after_stop"],
            "DIAGNOSIS_RECONCILIATION_FAILED")
    elapsed_ms = report["virtual_elapsed_ms"]
    require(type(elapsed_ms) in (int, float) and
            elapsed_ms >= last_event_ms and elapsed_ms > 0,
            "DIAGNOSIS_ELAPSED_INVALID")
    occupied_slot_ms += active * (elapsed_ms - last_event_ms)
    known = report["known_unattempted_heights"]
    ratio = report["head_request_work_share"]
    return {
        "schema": SCHEMA,
        "actual_network_requests": 0,
        "head_values_source": "SYNTHETIC_NOT_INDEPENDENT_GLOBAL_CHAIN_HEAD",
        "stop_state": report["stop_state"],
        "initial_synthetic_head": samples[0]["head"] if samples else None,
        "last_synthetic_head": sampled_head,
        "requested_total": report["requested_total"],
        "block_budget": max_blocks,
        "blocks_attempted": report["block_attempts"],
        "unspent_block_attempt_budget": max_blocks - report["block_attempts"],
        "head_refresh_budget": max_refreshes,
        "head_refreshes_requested": len(refreshes),
        "head_budget_exhausted": report["stop_state"] ==
            "HEAD_REFRESH_BUDGET_EXHAUSTED",
        "primary_refresh_triggers": dict(sorted(triggers.items())),
        "all_refresh_trigger_flags": dict(sorted(trigger_flags.items())),
        "refresh_detail": refreshes,
        "mean_new_confirmed_heights_per_refresh":
            round(sum(row.get("newly_observed_heights", 0)
                      for row in refreshes) / len(refreshes), 3)
            if refreshes else None,
        "block_dispatches_while_refresh_inflight":
            blocks_while_refresh_pending,
        "global_slot_occupancy_ratio_virtual":
            round(occupied_slot_ms / (report["max_allowed_inflight"] *
                                      elapsed_ms), 4),
        "three_shared_slots_verified_by_trace": maximum_active <= 3,
        "block_responses": report["block_responses_received"],
        "contiguous_commits": report["blocks_committed_contiguous"],
        "response_completion_bps": report["response_completion_throughput_bps"],
        "contiguous_commit_bps": report["contiguous_commit_throughput_bps"],
        "head_request_work_share_sum_of_virtual_durations": ratio,
        "known_unattempted_height_count": len(known),
        "sampled_head_minus_last_committed":
            report["sampled_head_minus_committed_height"],
        "virtual_elapsed_ms": elapsed_ms,
        "interpretation": (
            "A refreshed HEAD can unlock only already-confirmed heights. "
            "Exhausting the finite six-refresh budget while still near the "
            "synthetic source tip can stop a fast worker early. "
            "No source-independent final tip, real parallel HTTP performance, "
            "or F0 acceptance is established."
        ),
    }


def run_saved_duration_diagnosis(raw: bytes, journal_sha256: str,
                                 output_dir: Path, *,
                                 source_growth_bps=2.178):
    """Six existing policy scenarios. Private input never leaves local Mac."""
    observed, durations = replay_timings(raw, journal_sha256)
    require(isinstance(output_dir, Path) and output_dir.is_dir() and
            not output_dir.is_symlink() and
            output_dir.stat().st_mode & 0o077 == 0,
            "DIAGNOSIS_PRIVATE_OUTPUT_REQUIRED")
    cases = []
    for refresh_after in (4, 8):
        for slowdown in (1.0, 1.5, 2.0):
            path = output_dir / (
                "head-budget-every%d-slow%d.jsonl" %
                (refresh_after, round(slowdown * 10)))
            simulated = simulate(durations, path,
                                 inflight_slots=3,
                                 refresh_after=refresh_after,
                                 slowdown=slowdown,
                                 source_growth_bps=source_growth_bps)
            d = diagnose(simulated, refresh_after=refresh_after)
            d["refresh_after_blocks"] = refresh_after
            d["hypothetical_request_slowdown"] = slowdown
            cases.append(d)
    return {
        "schema": "bsc-f0-saved30-head-budget-six-offline-diagnostics-v1",
        "verified_original_private_journal_sha256": observed["journal_sha256"],
        "verified_original_method_counts": observed["observed_method_counts"],
        "actual_network_requests": 0,
        "prior_one_shot_live_permit": "CONSUMED",
        "cases": cases,
        "decision": "HEAD_BUDGET_DIAGNOSTICS_ONLY_NOT_REAL_PROVIDER_CAPACITY",
    }


def main():
    parser = argparse.ArgumentParser(
        description="ZERO-NETWORK saved30 HEAD refresh postmortem")
    parser.add_argument("--journal", type=Path, required=True)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    output = run_saved_duration_diagnosis(
        args.journal.read_bytes(), args.expected_sha256, args.output_dir)
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
