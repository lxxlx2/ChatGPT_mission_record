#!/usr/bin/env python3
"""F0 three-slot *offline-only* discrete-event scheduler.

Only synthetic source responses and previously recorded timing distributions are
accepted. There is NO user-supplied callback, no HTTP/WS, no execution permit,
no live entrypoint, no subprocess, no daemon, and no trading functionality.
A durable local fixture ledger charges every virtual attempt before scheduling
its completion. This is NOT real provider throughput evidence.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import heapq
import json
import os
from pathlib import Path
import statistics

from f0_l1_offline_capacity import replay_timings

SCHEMA = "bsc-f0-three-slot-injected-discrete-event-v1"
METHODS = ("eth_chainId", "eth_blockNumber", "eth_getBlockByNumber")


def require(ok, code):
    if not ok:
        raise ValueError(code)


def _sync_directory(root):
    fd = os.open(root, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


class OfflineLedger:
    """Exclusive-create append-only JSONL event record; never overwrites."""
    def __init__(self, path: Path):
        require(isinstance(path, Path) and not path.exists() and
                not path.is_symlink() and path.parent.is_dir() and
                not path.parent.is_symlink() and
                path.parent.stat().st_mode & 0o077 == 0,
                "OFFLINE_LEDGER_NOT_PRIVATE_OR_FRESH")
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        self.fd = os.open(path, flags, 0o600)
        self.path = path
        self.open = True
        _sync_directory(path.parent)

    def append(self, row):
        require(self.open, "OFFLINE_LEDGER_CLOSED")
        raw = (json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n").encode()
        while raw:
            written = os.write(self.fd, raw)
            require(written > 0, "OFFLINE_LEDGER_WRITE_FAILED")
            raw = raw[written:]
        os.fsync(self.fd)

    def close(self):
        if self.open:
            os.close(self.fd)
            self.open = False

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def _synthetic_hash(height):
    return hashlib.sha256(("synthetic-fixture-block-" + str(height)).encode()).hexdigest()


def _p95(data):
    if not data:
        return None
    sorted_values = sorted(data)
    return round(sorted_values[max(0, (95 * len(data) + 99) // 100 - 1)], 3)


def simulate(durations, ledger_path, *, inflight_slots=3, refresh_after=4,
             min_start_spacing_ms=250, head_freshness_ms=4000,
             source_growth_bps=2.178, initial_height=1000,
             max_total_attempts=32, max_blocks=24, max_refreshes=6,
             max_duration_ms=60000, slowdown=1.0,
             slow_heights=None, failed_heights=None, timeout_heights=None,
             bad_parent_heights=None, duplicate_heights=None,
             wrong_id_heights=None, head_values=None,
             crash_after_reservations=None,
             head_policy="checkpoint", min_head_refresh_age_ms=2500,
             prefetch_available_heights=1):
    """Deterministic single-coordinator scenario; no real sender is invoked.

    Fake work-slot completion events are generated from sequential observed
    elapsed times. Network/server slowdown, queueing and HEAD values are solely
    fixture assumptions. Only the coordinator may reserve and write attempts.
    """
    require(type(inflight_slots) is int and 1 <= inflight_slots <= 3 and
            type(refresh_after) is int and 1 <= refresh_after <= 8 and
            type(min_start_spacing_ms) is int and min_start_spacing_ms >= 250 and
            type(head_freshness_ms) is int and head_freshness_ms >= 250 and
            type(max_total_attempts) is int and 2 <= max_total_attempts <= 32 and
            type(max_blocks) is int and 1 <= max_blocks <= 24 and
            type(max_refreshes) is int and 0 <= max_refreshes <= 6 and
            type(max_duration_ms) is int and 1000 <= max_duration_ms <= 60000 and
            type(initial_height) is int and initial_height > 0 and
            type(source_growth_bps) in (float, int) and 0 < source_growth_bps <= 10 and
            type(slowdown) in (float, int) and 0 < slowdown <= 10 and
            head_policy in ("checkpoint", "availability_wait") and
            type(min_head_refresh_age_ms) is int and
            250 <= min_head_refresh_age_ms and
            (head_policy == "checkpoint" or
             min_head_refresh_age_ms < head_freshness_ms) and
            type(prefetch_available_heights) is int and
            0 <= prefetch_available_heights <= 3,
            "OFFLINE_SIMULATION_SCOPE_INVALID")
    require(isinstance(durations, dict) and all(
        isinstance(durations.get(method), list) and durations[method] and
        all(type(x) in (int, float) and 0 < x <= 60000 for x in durations[method])
        for method in METHODS), "OFFLINE_TIMINGS_INVALID")
    slow_heights = slow_heights or {}
    failed_heights = set(failed_heights or ())
    timeout_heights = set(timeout_heights or ())
    bad_parent_heights = set(bad_parent_heights or ())
    duplicate_heights = set(duplicate_heights or ())
    wrong_id_heights = set(wrong_id_heights or ())
    head_values = list(head_values or ())
    require(isinstance(slow_heights, dict) and all(
        type(h) is int and type(factor) in (int, float) and
        1 <= factor <= 10 for h, factor in slow_heights.items()),
        "OFFLINE_SLOW_FIXTURE_INVALID")
    require(crash_after_reservations is None or
            type(crash_after_reservations) is int and
            1 <= crash_after_reservations <= max_total_attempts,
            "OFFLINE_CRASH_SCOPE_INVALID")

    now = 0.0
    next_start = 0.0
    seq = 0
    events = []  # (virtual completion milliseconds, unique event seq, request ID)
    outstanding = {}
    finished_ids = set()
    attempts = []
    starts = []
    trace = []
    idx = Counter()
    counts = Counter()
    stop = None
    chain_issued = chain_done = False
    first_head_issued = first_head_done = False
    refreshing_id = None
    confirmed_head = None
    head_finished_ms = None
    first_height = None
    next_height = None
    next_contiguous = None
    contiguous_hash = None
    buffered = {}
    received = failed = committed = 0
    ignored_duplicates = 0
    head_samples = []
    attempted_missing = []
    parent_mismatches = []
    observed_inflight = 0
    buffer_peak = 0
    blocks_since_head = 0
    response_durations = []
    settlement_states = Counter()
    head_hold_until_ms = None

    def choose_action():
        nonlocal stop, head_hold_until_ms
        head_hold_until_ms = None
        if not chain_done:
            return ("eth_chainId", None, "CHAIN") if not chain_issued else None
        if not first_head_done:
            return ("eth_blockNumber", None, "INITIAL_HEAD") if not first_head_issued else None
        if counts["eth_getBlockByNumber"] >= max_blocks:
            stop = "BLOCK_ATTEMPT_BUDGET_COMPLETE"
            return None
        if len(attempts) >= max_total_attempts:
            stop = "TOTAL_ATTEMPT_BUDGET_EXHAUSTED"
            return None
        age_ms = now - head_finished_ms
        available = max(0, confirmed_head - next_height + 1)
        if head_policy == "availability_wait":
            # Decisions use ONLY the latest completed HEAD, monotonic time,
            # and reserved heights. Never peek at future synthetic source HEAD.
            due = (available <= prefetch_available_heights or
                   age_ms >= head_freshness_ms)
        else:
            due = (next_height > confirmed_head or
                   blocks_since_head >= refresh_after or
                   age_ms >= head_freshness_ms)
        if refreshing_id is not None:
            # Pending refresh does NOT extend the most recent completed HEAD.
            # The availability policy has no fixed block-count checkpoint.
            if (age_ms < head_freshness_ms and
                    next_height <= confirmed_head and
                    (head_policy == "availability_wait" or
                     blocks_since_head < refresh_after)):
                return ("eth_getBlockByNumber", next_height, "BLOCK")
            return None
        if due:
            if counts["HEAD_REFRESH"] >= max_refreshes:
                # Under the alternative policy, do not discard the last
                # already-confirmed fresh block merely because no more HEAD
                # polls are permitted. Never read above confirmed HEAD.
                if (head_policy == "availability_wait" and available > 0 and
                        age_ms < head_freshness_ms):
                    return ("eth_getBlockByNumber", next_height, "BLOCK")
                stop = "HEAD_REFRESH_BUDGET_EXHAUSTED"
                return None
            if (head_policy == "availability_wait" and
                    now < head_finished_ms + min_head_refresh_age_ms):
                # Compare the same absolute deadline used by the event loop.
                # Subtracting two floats can round a 3500ms age just below
                # threshold after the event clock reached the exact deadline.
                if available > 0 and age_ms < head_freshness_ms:
                    return ("eth_getBlockByNumber", next_height, "BLOCK")
                # With no eligible height, remain idle until a deliberate
                # poll time. We cannot infer new blocks without sampling HEAD.
                head_hold_until_ms = head_finished_ms + min_head_refresh_age_ms
                return None
            return ("eth_blockNumber", None, "HEAD_REFRESH")
        return ("eth_getBlockByNumber", next_height, "BLOCK")

    def complete(call):
        nonlocal chain_done, first_head_done, refreshing_id, confirmed_head
        nonlocal head_finished_ms, next_height, first_height, next_contiguous
        nonlocal contiguous_hash, received, failed, committed, stop, buffer_peak
        nonlocal ignored_duplicates
        request_id = call["id"]
        if request_id in finished_ids:
            ignored_duplicates += 1
            trace.append({"event": "DUPLICATE_IGNORED", "id": request_id, "at_ms": round(now, 3)})
            return
        require(request_id in outstanding, "OFFLINE_COMPLETION_WITHOUT_RESERVATION")
        finished_ids.add(request_id)
        del outstanding[request_id]
        method, category, height = call["method"], call["category"], call["height"]
        status = "RPC_RESPONSE"
        if category == "BLOCK" and height in timeout_heights:
            status = "TIMEOUT"
        elif category == "BLOCK" and height in failed_heights:
            status = "FAILED"
        elif category == "BLOCK" and height in wrong_id_heights:
            status = "WRONG_REQUEST_ID"
        latency = now - call["started_ms"]
        response_durations.append(latency)
        settlement_states[status] += 1
        ledger.append({"event": "SETTLE", "id": request_id, "at_ms": round(now, 3),
                       "state": status})
        trace.append({"event": "SETTLE", "id": request_id, "method": method,
                      "category": category, "height": height, "state": status,
                      "at_ms": round(now, 3)})
        if category == "CHAIN":
            chain_done = True
        elif category in ("INITIAL_HEAD", "HEAD_REFRESH"):
            if category == "HEAD_REFRESH":
                refreshing_id = None
            index = len(head_samples)
            head = (head_values[index] if index < len(head_values)
                    else initial_height + int(source_growth_bps * now / 1000))
            if head is None:
                stop = "HEAD_SOURCE_FAILED_NO_RETRY"
                return
            require(type(head) is int and head > 0, "OFFLINE_HEAD_INVALID")
            if confirmed_head is not None and head < confirmed_head:
                stop = "HEAD_REGRESSED_UNVERIFIED"
                return
            confirmed_head = head
            head_finished_ms = now
            if category == "INITIAL_HEAD":
                first_head_done = True
                first_height = head + 1
                next_height = first_height
                next_contiguous = first_height
            backlog = head - ((next_contiguous - 1) if next_contiguous else head)
            head_samples.append({"head": head, "at_ms": round(now, 3),
                                 "committed_backlog": backlog,
                                 "source_kind": "SYNTHETIC_HEAD_ONLY"})
        else:
            if status != "RPC_RESPONSE":
                failed += 1
                attempted_missing.append(height)
            else:
                received += 1
                block_hash = _synthetic_hash(height)
                parent_hash = ("f" * 64 if height in bad_parent_heights
                               else _synthetic_hash(height - 1))
                require(height not in buffered and height >= first_height,
                        "OFFLINE_DUPLICATE_HEIGHT")
                buffered[height] = (block_hash, parent_hash)
                buffer_peak = max(buffer_peak, len(buffered))
                while next_contiguous in buffered:
                    hash_value, parent = buffered[next_contiguous]
                    if contiguous_hash is not None and parent != contiguous_hash:
                        parent_mismatches.append(next_contiguous)
                        stop = "PARENT_HASH_MISMATCH"
                        break
                    del buffered[next_contiguous]
                    contiguous_hash = hash_value
                    committed += 1
                    ledger.append({"event": "COMMIT", "height": next_contiguous,
                                   "at_ms": round(now, 3)})
                    trace.append({"event": "COMMIT", "height": next_contiguous,
                                  "at_ms": round(now, 3)})
                    next_contiguous += 1

    with OfflineLedger(ledger_path) as ledger:
        for _ in range(10000):
            # Settle every fake event that has become available, including
            # synthetic duplicate receipts; never count them as new attempts.
            while events and events[0][0] <= now + 0.000001:
                end, _, request_id = heapq.heappop(events)
                call = next(row for row in attempts if row["id"] == request_id)
                complete(call)

            if stop is None and now >= max_duration_ms:
                stop = "VIRTUAL_DURATION_CAP_EXPIRED"

            if stop is None and len(outstanding) < inflight_slots and now >= next_start:
                action = choose_action()
                if action is not None:
                    method, height, category = action
                    require(len(attempts) < max_total_attempts,
                            "OFFLINE_TOTAL_CAP_EXCEEDED")
                    require(len(outstanding) < inflight_slots, "OFFLINE_SLOT_CAP_EXCEEDED")
                    if category == "BLOCK":
                        require(chain_done and first_head_done and
                                height <= confirmed_head and height == next_height,
                                "OFFLINE_READ_ABOVE_HEAD")
                        next_height += 1
                        blocks_since_head += 1
                    elif category == "CHAIN":
                        chain_issued = True
                    elif category == "INITIAL_HEAD":
                        require(chain_done, "OFFLINE_HEAD_BEFORE_CHAIN")
                        first_head_issued = True
                    else:
                        require(first_head_done, "OFFLINE_REFRESH_BEFORE_INITIAL_HEAD")
                        refreshing_id = len(attempts) + 1
                        blocks_since_head = 0
                    request_id = len(attempts) + 1
                    duration = durations[method][idx[method] % len(durations[method])]
                    idx[method] += 1
                    duration *= slowdown
                    if category == "BLOCK":
                        duration *= slow_heights.get(height, 1)
                    call = {"id": request_id, "method": method, "category": category,
                            "height": height, "started_ms": now,
                            "confirmed_head_at_dispatch": confirmed_head,
                            "duration_ms": duration}
                    # Single coordinator, serialized fsync BEFORE scheduling
                    # completion of any simulated send.
                    ledger.append({"event": "RESERVE_UNKNOWN", "id": request_id,
                                   "method": method, "category": category,
                                   "height": height, "at_ms": round(now, 3),
                                   "confirmed_head": confirmed_head})
                    trace.append({"event": "RESERVE_UNKNOWN", "id": request_id,
                                  "method": method, "category": category,
                                  "height": height, "at_ms": round(now, 3),
                                  "confirmed_head": confirmed_head})
                    attempts.append(call)
                    outstanding[request_id] = call
                    counts[method] += 1
                    counts[category] += 1
                    starts.append(now)
                    next_start = now + min_start_spacing_ms
                    observed_inflight = max(observed_inflight, len(outstanding))
                    heapq.heappush(events, (now + duration, seq, request_id))
                    seq += 1
                    if category == "BLOCK" and height in duplicate_heights:
                        heapq.heappush(events, (now + duration + 1, seq, request_id))
                        seq += 1
                    if crash_after_reservations == len(attempts):
                        stop = "SIMULATED_PROCESS_CRASH_OUTCOME_UNKNOWN"
                        # An abrupt crash deliberately does not settle in-flight.
                        break
                    continue

            if stop == "SIMULATED_PROCESS_CRASH_OUTCOME_UNKNOWN":
                break
            if stop is not None and not events:
                break
            next_times = [events[0][0]] if events else []
            if (stop is None and head_hold_until_ms is not None and
                    head_hold_until_ms > now):
                next_times.append(head_hold_until_ms)
            if stop is None and len(outstanding) < inflight_slots and next_start > now:
                next_times.append(next_start)
            if stop is None and now < max_duration_ms:
                next_times.append(float(max_duration_ms))
            if not next_times:
                stop = stop or "NO_ACTIONABLE_SOURCE_HEAD"
                break
            later = [t for t in next_times if t > now + 0.000001]
            require(bool(later), "OFFLINE_EVENT_LOOP_STALLED")
            now = min(later)
        else:
            raise ValueError("OFFLINE_SIMULATION_LOOP_LIMIT")

    if stop is None:
        stop = "STOP_CONDITION_UNSPECIFIED"
    known_unattempted = (
        list(range(next_height, confirmed_head + 1))
        if next_height is not None and confirmed_head is not None and
        next_height <= confirmed_head else []
    )
    total_head = counts["eth_blockNumber"]
    elapsed_s = now / 1000 if now > 0 else 0
    method_counts = {method: counts[method] for method in METHODS}
    start_differences = [starts[i] - starts[i - 1] for i in range(1, len(starts))]
    return {
        "schema": SCHEMA, "mode": "OFFLINE_SYNTHETIC_EVENT_SIMULATION_ONLY",
        "actual_network_requests": 0, "live_source_concurrency_verified": False,
        "real_provider_capacity_claim": "UNVERIFIED",
        "original_live_permit": "CONSUMED_NOT_REUSABLE",
        "head_policy": head_policy,
        "min_head_refresh_age_ms": min_head_refresh_age_ms if
            head_policy == "availability_wait" else None,
        "prefetch_available_heights": prefetch_available_heights if
            head_policy == "availability_wait" else None,
        "stop_state": stop, "virtual_elapsed_ms": round(now, 3),
        "requested_total": len(attempts), "method_counts": method_counts,
        "head_refreshes_requested": counts["HEAD_REFRESH"],
        "block_attempts": counts["BLOCK"], "block_responses_received": received,
        "block_failures": failed, "blocks_committed_contiguous": committed,
        "attempted_missing_heights": attempted_missing,
        "known_unattempted_heights": known_unattempted,
        "inflight_outcome_unknown_after_stop": len(outstanding),
        "duplicate_receipts_ignored": ignored_duplicates,
        "parent_mismatch_heights": parent_mismatches,
        "max_observed_inflight": observed_inflight,
        "max_allowed_inflight": inflight_slots,
        "global_min_start_gap_ms": round(min(start_differences), 3)
        if start_differences else None,
        "minimum_allowed_start_gap_ms": min_start_spacing_ms,
        "response_completion_throughput_bps": round(received / elapsed_s, 3)
        if elapsed_s else 0.0,
        "contiguous_commit_throughput_bps": round(committed / elapsed_s, 3)
        if elapsed_s else 0.0,
        "p95_completion_duration_ms": _p95(response_durations),
        "head_request_work_share": round(
            sum(row["duration_ms"] for row in attempts
                if row["method"] == "eth_blockNumber") /
            sum(row["duration_ms"] for row in attempts), 4)
        if attempts else 0,
        "reorder_buffer_peak": buffer_peak,
        "reorder_buffer_uncommitted_after_stop": sorted(buffered),
        "last_source_sampled_head": confirmed_head,
        "last_committed_height": (next_contiguous - 1) if next_contiguous else None,
        "sampled_head_minus_committed_height":
            confirmed_head - next_contiguous + 1
            if confirmed_head is not None and next_contiguous else None,
        "head_samples": head_samples, "trace": trace,
        "scenarios_not_modelled": [
            "REAL_PARALLEL_PROVIDER_LATENCY", "NETWORK_RATE_LIMIT",
            "ACTUAL_BLOCK_AVAILABILITY", "FSYNC_WALLCLOCK_OVERHEAD",
            "INDEPENDENT_NETWORK_HEAD", "TRANSACTION_DIRECTION_OR_PROFIT",
        ],
        "ledger_path": str(ledger_path),
    }


def main():
    parser = argparse.ArgumentParser(description="OFFLINE three-slot synthetic BSC capacity only")
    parser.add_argument("--journal", required=True, type=Path)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--synthetic-source-growth", type=float, default=2.178)
    args = parser.parse_args()
    observed, durations = replay_timings(
        args.journal.read_bytes(), args.expected_sha256)
    root = args.output_dir
    require(root.is_dir() and not root.is_symlink() and
            root.stat().st_mode & 0o077 == 0,
            "OFFLINE_OUTPUT_ROOT_NOT_PRIVATE")
    scenarios = []
    for every in (4, 8):
        for factor in (1.0, 1.5, 2.0):
            label = "offline-three-head%d-slow%d" % (every, factor * 10)
            report = simulate(
                durations, root / (label + ".jsonl"), inflight_slots=3,
                refresh_after=every, slowdown=factor,
                source_growth_bps=args.synthetic_source_growth)
            report.pop("trace")
            scenarios.append(report)
    print(json.dumps({
        "schema": "bsc-f0-three-slot-six-synthetic-scenarios-v1",
        "actual_network_requests": 0,
        "private_journal_sha256_verified": observed["journal_sha256"],
        "private_observed_method_counts": observed["observed_method_counts"],
        "simulations": scenarios,
        "decision": "NOT_REAL_PROVIDER_VERIFICATION_NO_F0_PASS",
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
