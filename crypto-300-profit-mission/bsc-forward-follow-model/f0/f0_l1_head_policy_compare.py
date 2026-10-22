#!/usr/bin/env python3
"""F0 HEAD strategy comparison; offline saved-Journal times and synthetic HEAD only.

No transport implementation, no real block queries, no real permit, no live
entrypoint, no wallet/signature/quote, and no background service. A bounded
three-slot discrete-event simulation is reused with identical budget caps.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from f0_l1_offline_capacity import replay_timings
from f0_l1_three_slot_offline import simulate

SCHEMA = "bsc-f0-head-policy-saved30-comparison-v1"
SHA = "e069b7cd38c2ad3c8a3af3a1b1c220efab1714fe4de0bb7a9e2b814a2302d61a"


def require(ok, code):
    if not ok:
        raise ValueError(code)


def compare(durations, root: Path, *, growth_bps=2.178):
    """Fixed 6 prior-proven input scenarios x baseline and wait candidates.

    Output is aggregate only; fake reservation ledgers remain in the private
    directory. All virtual scheduling is still subject to source-confirmed
    height, HEAD freshness, and immutable 32/24/6 and three-slot caps.
    """
    require(isinstance(root, Path) and root.is_dir() and not root.is_symlink()
            and root.stat().st_mode & 0o077 == 0,
            "HEAD_POLICY_PRIVATE_OUTPUT_ROOT_REQUIRED")
    settings = [
        ("checkpoint", 2500),
        ("availability_wait", 1500),
        ("availability_wait", 2500),
        ("availability_wait", 3500),
    ]
    cases = []
    for every in (4, 8):
        for slowdown in (1.0, 1.5, 2.0):
            variants = []
            for mode, hold_ms in settings:
                name = ("head%d-slow%d-%s-%d.jsonl" %
                        (every, round(slowdown * 10), mode, hold_ms))
                data = simulate(
                    durations, root / name, inflight_slots=3,
                    refresh_after=every, min_start_spacing_ms=250,
                    head_freshness_ms=4000,
                    head_policy=mode, min_head_refresh_age_ms=hold_ms,
                    prefetch_available_heights=1,
                    max_total_attempts=32, max_blocks=24,
                    max_refreshes=6, max_duration_ms=60000,
                    slowdown=slowdown, source_growth_bps=growth_bps)
                require(data["actual_network_requests"] == 0 and
                        data["max_observed_inflight"] <= 3 and
                        data["requested_total"] <= 32 and
                        data["block_attempts"] <= 24 and
                        data["head_refreshes_requested"] <= 6 and
                        data["inflight_outcome_unknown_after_stop"] == 0 and
                        (data["global_min_start_gap_ms"] is None or
                         data["global_min_start_gap_ms"] >= 250),
                        "HEAD_POLICY_SIMULATION_INVARIANT_FAILED")
                variants.append({
                    "policy": mode,
                    "min_head_refresh_age_ms": hold_ms if
                        mode == "availability_wait" else None,
                    "stop_state": data["stop_state"],
                    "virtual_elapsed_ms": data["virtual_elapsed_ms"],
                    "total_attempts": data["requested_total"],
                    "head_refresh_attempts": data["head_refreshes_requested"],
                    "full_block_attempts": data["block_attempts"],
                    "unspent_full_block_budget": 24 - data["block_attempts"],
                    "responses_received": data["block_responses_received"],
                    "committed_contiguous": data["blocks_committed_contiguous"],
                    "response_bps": data["response_completion_throughput_bps"],
                    "contiguous_commit_bps": data["contiguous_commit_throughput_bps"],
                    "last_sampled_head_minus_committed":
                        data["sampled_head_minus_committed_height"],
                    "known_unattempted_count":
                        len(data["known_unattempted_heights"]),
                    "head_virtual_work_share":
                        data["head_request_work_share"],
                    "max_inflight": data["max_observed_inflight"],
                    "buffer_peak": data["reorder_buffer_peak"],
                    "p95_duration_ms": data["p95_completion_duration_ms"],
                })
            baseline = variants[0]
            for variant in variants:
                variant["additional_contiguous_commits_vs_baseline"] = (
                    variant["committed_contiguous"] -
                    baseline["committed_contiguous"])
                variant["head_calls_saved_vs_baseline"] = (
                    baseline["head_refresh_attempts"] -
                    variant["head_refresh_attempts"])
                variant["commit_bps_delta_vs_baseline"] = round(
                    variant["contiguous_commit_bps"] -
                    baseline["contiguous_commit_bps"], 3)
            cases.append({
                "refresh_after_blocks": every,
                "synthetic_latency_multiplier": slowdown,
                "variants": variants,
            })
    return {
        "schema": SCHEMA,
        "actual_network_requests": 0,
        "head_source": "SYNTHETIC_INCREMENT_MODEL_UNVERIFIED",
        "user_authorized_new_rpc": False,
        "previous_real_30_call_grant": "CONSUMED",
        "f0_status": "NOT_PASSED",
        "source_growth_bps_assumption": growth_bps,
        "budgets_unchanged": {
            "shared_inflight": 3, "global_start_spacing_ms": 250,
            "head_freshness_ms": 4000, "max_total_attempts": 32,
            "max_full_blocks": 24, "max_refreshed_heads": 6,
            "max_virtual_duration_ms": 60000,
        },
        "cases": cases,
        "interpretation": (
            "A waiting policy trades earlier HEAD queries for later simulated "
            "HEAD discoveries. It uses last-confirmed HEAD, elapsed time and "
            "height margins only. Throughput is synthetic (saved serial "
            "latencies replayed under hypothetical concurrency), not actual "
            "provider parallel throughput, independent chain-tip completeness "
            "or permission for future RPC. Lower HEAD use alone is NOT success."
        ),
    }


def run_saved_comparison(raw: bytes, expected_sha256: str, root: Path,
                         *, growth_bps=2.178):
    observed, durations = replay_timings(raw, expected_sha256)
    result = compare(durations, root, growth_bps=growth_bps)
    result["verified_private_source_journal_sha256"] = observed["journal_sha256"]
    result["verified_private_request_method_counts"] = (
        observed["observed_method_counts"])
    return result


def main():
    parser = argparse.ArgumentParser(
        description="OFFLINE synthetic source HEAD wait policy comparison")
    parser.add_argument("--journal", type=Path, required=True)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run_saved_comparison(
        args.journal.read_bytes(), args.expected_sha256, args.output_dir),
        indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
