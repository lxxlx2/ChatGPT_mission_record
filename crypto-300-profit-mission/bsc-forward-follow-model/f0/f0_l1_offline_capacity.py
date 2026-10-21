#!/usr/bin/env python3
"""Offline-only BSC F0 throughput capacity evaluation from a saved local journal.

NO HTTP/WS, RPC, signing, wallet data lookup, daemon or live permit support.
Hypothetical overlapping timings are NOT a measured parallel BSC capability.
"""
from __future__ import annotations

import argparse
import hashlib
import heapq
import json
from pathlib import Path
import statistics

SCHEMA = "bsc-f0-l1-short-http-single-use-v1"
METHODS = ("eth_chainId", "eth_blockNumber", "eth_getBlockByNumber")


def require(ok, code):
    if not ok:
        raise ValueError(code)


def replay_timings(raw: bytes, expected_sha256: str):
    """Verify exact saved journal bytes and extract only timing/method aggregates."""
    require(type(raw) is bytes and type(expected_sha256) is str and
            len(expected_sha256) == 64 and
            hashlib.sha256(raw).hexdigest() == expected_sha256.lower(),
            "JOURNAL_SHA256_MISMATCH")
    doc = json.loads(raw)
    require(isinstance(doc, dict) and doc.get("schema") == SCHEMA and
            isinstance(doc.get("attempts"), list) and
            type(doc.get("attempted_calls")) is int and
            doc["attempted_calls"] == len(doc["attempts"]),
            "JOURNAL_ACCOUNTING_INVALID")
    durations = {method: [] for method in METHODS}
    for index, row in enumerate(doc["attempts"], 1):
        require(isinstance(row, dict) and row.get("index") == index and
                row.get("method") in METHODS and row.get("state") == "RPC_RESPONSE",
                "JOURNAL_INCOMPLETE_OR_UNSUPPORTED")
        start, finish = row.get("requested_monotonic_ns"), row.get("completed_monotonic_ns")
        require(type(start) is int and type(finish) is int and
                0 < finish - start <= 60_000_000_000,
                "JOURNAL_DURATION_INVALID")
        durations[row["method"]].append((finish - start) / 1_000_000)
    require(len(durations["eth_chainId"]) == 1 and
            len(durations["eth_blockNumber"]) >= 2 and
            len(durations["eth_getBlockByNumber"]) >= 2,
            "JOURNAL_SAMPLE_INSUFFICIENT")
    # Privacy: NEVER echo wallet/tx identifiers, params, or individual RPC rows.
    return {
        "journal_sha256": hashlib.sha256(raw).hexdigest(),
        "observed_attempts": len(doc["attempts"]),
        "observed_method_counts": {m: len(v) for m, v in durations.items()},
        "block_latency_mean_ms": round(statistics.mean(durations["eth_getBlockByNumber"]), 3),
        "block_latency_median_ms": round(statistics.median(durations["eth_getBlockByNumber"]), 3),
        "head_latency_median_ms": round(statistics.median(durations["eth_blockNumber"]), 3),
        "source": "PRIVATE_JOURNAL_OBSERVED_SEQUENTIAL_REQUEST_DURATIONS",
    }, durations


def scenario_jobs(*, full_blocks, head_every, max_refreshes, total_cap):
    """Fixed hypothetical jobs; real head-dependent availability NOT simulated."""
    require(all(type(x) is int for x in
                (full_blocks, head_every, max_refreshes, total_cap)) and
            1 <= full_blocks <= 24 and 1 <= head_every <= 24 and
            0 <= max_refreshes <= 6 and 2 <= total_cap <= 32,
            "SCENARIO_SCOPE_INVALID")
    jobs = ["eth_chainId", "eth_blockNumber"]
    refreshes = 0
    for count in range(1, full_blocks + 1):
        jobs.append("eth_getBlockByNumber")
        if count < full_blocks and count % head_every == 0:
            if refreshes >= max_refreshes:
                return None
            jobs.append("eth_blockNumber")
            refreshes += 1
    if len(jobs) > total_cap:
        return None
    return jobs


def projection(durations, *, inflight, full_blocks=24, head_every=4,
               max_refreshes=6, total_cap=32, spacing_ms=250,
               source_growth_bps=2.178):
    """Optimistic overlap thought experiment, not a live/source-valid scheduler.

    Assumes observed SEQUENTIAL latencies do not change under parallel load.
    Ignores HEAD dependence, server throttling, retry and ordered block release.
    All methods share the start-spacing gate and one unified call budget.
    """
    require(type(inflight) is int and 1 <= inflight <= 3 and
            type(spacing_ms) is int and spacing_ms >= 250 and
            type(source_growth_bps) in (int, float) and source_growth_bps > 0,
            "PROJECTION_LIMIT_INVALID")
    jobs = scenario_jobs(full_blocks=full_blocks, head_every=head_every,
                         max_refreshes=max_refreshes, total_cap=total_cap)
    if jobs is None:
        return {"status": "NOT_FEASIBLE_WITHIN_GIVEN_REQUEST_BUDGET",
                "inflight": inflight, "head_every": head_every}
    worker_available = [0.0] * inflight
    last_sent_next = 0.0
    indexes = {m: 0 for m in METHODS}
    for method in jobs:
        samples = durations[method]
        require(bool(samples) and all(type(t) in (float, int) and t > 0
                                      for t in samples), "DURATION_INPUT_INVALID")
        duration = samples[indexes[method] % len(samples)]
        indexes[method] += 1
        slot = min(range(inflight), key=lambda i: worker_available[i])
        start_ms = max(worker_available[slot], last_sent_next)
        worker_available[slot] = start_ms + duration
        last_sent_next = start_ms + spacing_ms
    elapsed_ms = max(worker_available)
    bps = full_blocks * 1000 / elapsed_ms
    return {
        "status": "HYPOTHETICAL_ONLY_NO_PROVIDER_CONCURRENCY_VERIFIED",
        "inflight": inflight,
        "head_every": head_every,
        "total_requests": len(jobs),
        "head_refreshes": len(jobs) - full_blocks - 2,
        "full_blocks": full_blocks,
        "global_min_start_spacing_ms": spacing_ms,
        "projected_elapsed_ms": round(elapsed_ms, 3),
        "projected_full_block_delivery_bps": round(bps, 3),
        "observed_sample_source_head_growth_bps": source_growth_bps,
        "capacity_above_sample_growth_in_ideal_model": bps > source_growth_bps,
        "capacity_margin_ratio_ideal_model": round(bps / source_growth_bps, 3),
        "replayed_sequential_durations_under_optimistic_parallel_assumptions": True,
        "not_modelled": [
            "REAL_PARALLEL_HTTP_LATENCY_AND_PROVIDER_THROTTLING",
            "HEAD_CONFIRMED_HEIGHT_GATING",
            "BLOCK_ORDER_AND_PARENT_VERIFICATION",
            "SHARED_FSYNC_JOURNAL_CONTENTION",
            "INDEPENDENT_NETWORK_TIP",
            "ACTUAL_LIVE_BLOCK_COMPLETENESS",
        ],
    }


def analyze(raw: bytes, *, expected_sha256: str, source_growth_bps=2.178):
    observed, durations = replay_timings(raw, expected_sha256)
    scenarios = [
        projection(durations, inflight=workers, head_every=head_every,
                   source_growth_bps=source_growth_bps)
        for head_every in (4, 8) for workers in (1, 2, 3)
    ]
    return {
        "schema": "bsc-f0-saved30-offline-capacity-v1",
        "actual_rpc_calls_during_this_program": 0,
        "live_run_authorized_by_this_program": False,
        "original_live_permit_consumed": True,
        "private_evidence": observed,
        "projections": scenarios,
        "interpretation": (
            "This is a capacity bound under repeated serial observed durations, "
            "NOT an actual parallel run, a valid prospective HEAD scheduler, "
            "a completeness measurement or an F0 PASS. "
            "Do not run new RPC without new user authorization and reviewed permit."
        ),
    }


def main():
    parser = argparse.ArgumentParser(description="Offline-only saved Journal timing projection")
    parser.add_argument("--journal", type=Path, required=True)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--source-growth-bps", type=float, default=2.178)
    args = parser.parse_args()
    print(json.dumps(analyze(args.journal.read_bytes(),
                             expected_sha256=args.expected_sha256,
                             source_growth_bps=args.source_growth_bps),
                     indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
