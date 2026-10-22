#!/usr/bin/env python3
"""F0 bounded THREE-SLOT CLOSED-LOOP FAKE JSON-RPC collector. OFFLINE ONLY.

No network, urllib, socket, transport callbacks, user permit, or live entrypoint.
All responses are constructed in memory by a deterministic synthetic oracle,
and are parsed *on completion* before any subsequent scheduler decision.
Journal RESERVE_UNKNOWN is fsynced before a fake in-flight event is scheduled.
This is a simulation, NOT measured public provider performance or F0 PASS.
"""
from __future__ import annotations

import argparse
from collections import Counter
import heapq
import json
import math
from pathlib import Path

from f0_l1_http_wire import parse_http_response, valid_rpc_payload
from f0_l1_offline_capacity import replay_timings
from f0_l1_three_slot_offline import OfflineLedger, _synthetic_hash
from f0_rpc_adapter import block_candidates, hexb

SCHEMA = "bsc-f0-three-slot-closed-loop-fake-v1"
METHODS = ("eth_chainId", "eth_blockNumber", "eth_getBlockByNumber")


def require(ok, code):
    if not ok:
        raise ValueError(code)


def _p95(values):
    if not values:
        return None
    ordered = sorted(values)
    return round(ordered[max(0, math.ceil(.95 * len(values)) - 1)], 3)


class SyntheticBscOracle:
    """Only scripted, internally generated RPC responses. Not a pluggable sender."""

    def __init__(self, *, initial_head=1000, growth_bps=2.178,
                 fail_blocks=(), timeout_blocks=(), bad_id_blocks=(),
                 bad_parent_blocks=(), hash_only_blocks=(), malformed_blocks=(),
                 bad_height_blocks=(), head_fail_refreshes=(),
                 head_regress_refreshes=()):
        require(type(initial_head) is int and initial_head >= 1 and
                type(growth_bps) in (int, float) and 0 < growth_bps <= 10,
                "FAKE_SOURCE_SCOPE_INVALID")
        self.initial_head, self.growth_bps = initial_head, growth_bps
        for key, group in {
            "fail": fail_blocks, "timeout": timeout_blocks,
            "bad_id": bad_id_blocks, "bad_parent": bad_parent_blocks,
            "hash_only": hash_only_blocks, "malformed": malformed_blocks,
            "bad_height": bad_height_blocks,
            "head_fail": head_fail_refreshes,
            "head_regress": head_regress_refreshes,
        }.items():
            require(isinstance(group, (list, tuple, set)) and
                    all(type(x) is int and x >= 0 for x in group),
                    "FAKE_SOURCE_FAULT_INVALID_" + key)
        self.fail_blocks = set(fail_blocks)
        self.timeout_blocks = set(timeout_blocks)
        self.bad_id_blocks = set(bad_id_blocks)
        self.bad_parent_blocks = set(bad_parent_blocks)
        self.hash_only_blocks = set(hash_only_blocks)
        self.malformed_blocks = set(malformed_blocks)
        self.bad_height_blocks = set(bad_height_blocks)
        self.head_fail_refreshes = set(head_fail_refreshes)
        self.head_regress_refreshes = set(head_regress_refreshes)

    def head_at(self, elapsed_ms):
        return self.initial_head + math.floor(self.growth_bps * elapsed_ms / 1000)

    def respond(self, request, completed_ms, *, refresh_index=0):
        """Return fake HTTP (status, headers, bytes); NEVER performs I/O."""
        valid_rpc_payload(request)
        method, rid = request["method"], request["id"]
        result, status = None, 200
        if method == "eth_chainId":
            result = "0x38"
        elif method == "eth_blockNumber":
            if refresh_index in self.head_fail_refreshes:
                status = 503
            result = hex(max(1, self.head_at(completed_ms) -
                             (100 if refresh_index in self.head_regress_refreshes else 0)))
        else:
            height = int(request["params"][0], 16)
            if height in self.fail_blocks:
                status = 503
            result = {
                "number": hex(height + (1 if height in self.bad_height_blocks else 0)),
                "hash": "0x" + _synthetic_hash(height),
                "parentHash": ("0x" + "ab" * 32 if height in self.bad_parent_blocks
                               else "0x" + _synthetic_hash(height - 1)),
                "transactions": (["0x" + "12" * 32] if height in self.hash_only_blocks
                                 else []),
            }
            if height in self.malformed_blocks:
                return 200, {"content-type": "application/json"}, b"{not-json"
        if method == "eth_getBlockByNumber" and height in self.bad_id_blocks:
            rid += 10000
        return (status, {"content-type": "application/json"},
                json.dumps({"jsonrpc":"2.0", "id":rid, "result":result},
                           separators=(",", ":"), sort_keys=True).encode())


def run_closed_loop(durations: dict, ledger_path: Path, *,
                    oracle: SyntheticBscOracle,
                    policy="availability_wait",
                    min_head_refresh_age_ms=1500,
                    refresh_after_blocks=4,
                    head_ttl_ms=4000,
                    spacing_ms=250,
                    slots=3,
                    max_total=32,
                    max_blocks=24,
                    max_refreshes=6,
                    duration_ms=60000,
                    timeout_ms=5000,
                    slowdown=1.0):
    """Single-coordinator event loop: REAL parse outcomes change NEXT decisions.

    Fake source HEAD is calculated only at a HEAD completion event; the
    scheduler cannot inspect future oracle HEAD values. No retry, no resuming
    consumed fake attempts, no actual network request. Normal stop drains all
    already-reserved calls; a failed block/HEAD prevents further dispatch.
    """
    require(type(oracle) is SyntheticBscOracle and
            policy in ("checkpoint", "availability_wait") and
            type(min_head_refresh_age_ms) is int and
            250 <= min_head_refresh_age_ms and
            (policy == "checkpoint" or
             min_head_refresh_age_ms < head_ttl_ms) and
            type(head_ttl_ms) is int and 250 <= head_ttl_ms <= 10000 and
            type(spacing_ms) is int and spacing_ms >= 250 and
            type(slots) is int and slots == 3 and
            type(refresh_after_blocks) is int and
            1 <= refresh_after_blocks <= 8 and
            type(max_total) is int and 2 <= max_total <= 32 and
            type(max_blocks) is int and 1 <= max_blocks <= 24 and
            type(max_refreshes) is int and 0 <= max_refreshes <= 6 and
            type(duration_ms) is int and 1000 <= duration_ms <= 60000 and
            type(timeout_ms) is int and 250 <= timeout_ms <= 5000 and
            type(slowdown) in (float, int) and 0 < slowdown <= 10 and
            isinstance(durations, dict) and all(
                isinstance(durations.get(name), list) and
                durations[name] and
                all(type(v) in (int, float) and 0 < v <= 60000 and
                    math.isfinite(v) for v in durations[name])
                for name in METHODS), "CLOSED_LOOP_SCOPE_INVALID")
    # All timing/horizon values are finite synthetic milliseconds.
    require(isinstance(ledger_path, Path), "CLOSED_LOOP_LEDGER_PATH_INVALID")
    now = next_start = 0.0
    seq = 0
    events = []
    pending = {}
    attempts = []
    latency_indices = Counter()
    started_by_method = Counter()
    completions = Counter()
    max_inflight = 0
    last_head = last_head_finished = None
    next_height = next_commit = None
    head_inflight = None
    head_refreshes = 0
    since_head = 0
    chain_valid = False
    first_chain_started = False
    first_head_started = False
    stop = None
    faults = []
    received = committed = linked = 0
    buffered = {}
    invalid_parent_height = None
    buffer_peak = 0
    requested_missing = []
    head_samples = []
    sample_events = []
    started = []
    latencies = []
    idle_head_wait_ms = 0.0
    slot_work_ms = 0.0
    last_event = 0.0
    last_committed_hash = None
    completion_order = []

    def decide():
        if not chain_valid:
            return ("CHAIN", None, None) if not first_chain_started else None
        if last_head is None:
            return ("INITIAL_HEAD", None, None) if not first_head_started else None
        if started_by_method["eth_getBlockByNumber"] >= max_blocks:
            return ("STOP", "BLOCK_ATTEMPT_BUDGET_COMPLETE", None)
        if len(attempts) >= max_total:
            return ("STOP", "TOTAL_ATTEMPT_BUDGET_EXHAUSTED", None)
        available = last_head - next_height + 1
        fresh = now < last_head_finished + head_ttl_ms
        due = (
            (available <= 1 if policy == "availability_wait" else
             available <= 0 or since_head >= refresh_after_blocks) or not fresh)
        if head_inflight is not None:
            if available > 0 and fresh and (
                    policy == "availability_wait" or
                    since_head < refresh_after_blocks):
                return ("BLOCK", next_height, None)
            return None
        if due:
            if head_refreshes >= max_refreshes:
                if policy == "availability_wait" and available > 0 and fresh:
                    return ("BLOCK", next_height, None)
                return ("STOP", "HEAD_REFRESH_BUDGET_EXHAUSTED", None)
            if (policy == "availability_wait" and
                    now < last_head_finished + min_head_refresh_age_ms):
                if available > 0 and fresh:
                    return ("BLOCK", next_height, None)
                # Wakeup is same ABSOLUTE deadline as comparison, no float age bug.
                return ("WAIT_HEAD", None,
                        last_head_finished + min_head_refresh_age_ms)
            return ("HEAD_REFRESH", None, None)
        require(available > 0 and fresh, "CLOSED_LOOP_HEIGHT_DECISION_INVALID")
        return ("BLOCK", next_height, None)

    def settle(call):
        nonlocal chain_valid, last_head, last_head_finished
        nonlocal next_height, next_commit, head_inflight, stop
        nonlocal received, committed, linked, last_committed_hash, buffer_peak
        nonlocal invalid_parent_height
        category, rid, height = call["category"], call["id"], call["height"]
        require(rid in pending, "CLOSED_LOOP_SETTLE_WITHOUT_RESERVATION")
        del pending[rid]
        elapsed = now - call["started"]
        latencies.append(elapsed)
        completion_order.append(rid)
        state = "RPC_RESPONSE"
        fault = None
        parsed_block = None
        if category == "BLOCK" and height in oracle.timeout_blocks:
            state, fault = "TIMEOUT", "SCRIPTED_SOURCE_TIMEOUT"
        else:
            try:
                status, headers, raw = oracle.respond(
                    call["request"], now, refresh_index=call["refresh_index"])
                response = parse_http_response(
                    status, headers, raw, call["request"])
                value = response["result"]
                if category == "CHAIN":
                    require(value == "0x38", "CLOSED_LOOP_CHAIN_NOT_BSC")
                    chain_valid = True
                elif category in ("INITIAL_HEAD", "HEAD_REFRESH"):
                    require(type(value) is str and value.startswith("0x") and
                            len(value) > 2 and
                            all(ch in "0123456789abcdefABCDEF" for ch in value[2:]),
                            "CLOSED_LOOP_HEAD_INVALID")
                    sampled = int(value, 16)
                    require(sampled > 0 and
                            (last_head is None or sampled >= last_head),
                            "CLOSED_LOOP_HEAD_REGRESSION")
                    last_head, last_head_finished = sampled, now
                    if category == "INITIAL_HEAD":
                        next_height = next_commit = sampled + 1
                    head_samples.append({
                        "head":sampled, "at_ms":round(now, 3),
                        "next_unattempted_height":next_height,
                        "sampled_head_minus_last_committed":
                            sampled - (next_commit - 1),
                        "source_kind":"SYNTHETIC_ORACLE_HEAD",
                    })
                else:
                    parsed = block_candidates(response, set(), set())
                    require(parsed["block_number"] == height,
                            "CLOSED_LOOP_WRONG_BLOCK_HEIGHT")
                    require(height not in buffered and height >= next_commit,
                            "CLOSED_LOOP_DUPLICATE_OR_BACKWARD")
                    block_hash = parsed["block_hash"]
                    parent_hash = hexb(value["parentHash"], 32)
                    # Parse only here. Chain integrity is checked AFTER this
                    # request has its own SETTLE outcome persisted, so an
                    # earlier buffered block cannot turn this RPC into FAILED.
                    parsed_block = (block_hash, parent_hash)
            except (TypeError, KeyError, ValueError, OverflowError) as exc:
                state, fault = "FAILED", str(exc)[:100]
        if category in ("INITIAL_HEAD", "HEAD_REFRESH"):
            head_inflight = None
        completions[state] += 1
        ledger.append({"event":"SETTLE", "id":rid,
                       "at_ms":round(now, 3), "state":state,
                       "fault":fault})
        sample_events.append({
            "event":"SETTLE", "id":rid, "method":call["method"],
            "category":category, "height":height, "state":state,
            "at_ms":round(now, 3),
        })
        if fault is not None:
            faults.append({"id":rid, "height":height, "category":category,
                           "reason":fault})
            if category == "BLOCK":
                requested_missing.append(height)
                stop = stop or "BLOCK_FAULT_STOP_NO_RETRY"
            else:
                stop = stop or "SOURCE_IDENTITY_OR_HEAD_FAULT_STOP"
        if category == "BLOCK" and state == "RPC_RESPONSE":
            require(parsed_block is not None,
                    "CLOSED_LOOP_PARSED_BLOCK_MISSING")
            # The buffer retains the owning request ID, not only its hash.
            # A later request may unlock this earlier out-of-order block.
            buffered[height] = (rid, *parsed_block)
            received += 1
            buffer_peak = max(buffer_peak, len(buffered))
            ledger.append({"event":"COMPLETION_ACCEPTED", "id":rid,
                           "height":height, "at_ms":round(now, 3)})
            # A bad buffered parent is a CHAIN_INTEGRITY fault belonging to
            # the BUFFERED block. It does not change any already recorded
            # RPC_RESPONSE state, and is reported only once during draining.
            while invalid_parent_height is None and next_commit in buffered:
                owner_id, block_hash, parent_hash = buffered[next_commit]
                if (last_committed_hash is not None and
                        parent_hash != last_committed_hash):
                    invalid_parent_height = next_commit
                    evidence = {
                        "id":owner_id, "height":next_commit,
                        "category":"BLOCK",
                        "reason":"CLOSED_LOOP_PARENT_HASH_MISMATCH",
                        "fault_type":"CHAIN_INTEGRITY",
                    }
                    faults.append(evidence)
                    requested_missing.append(next_commit)
                    integrity_event = {
                        "event":"CHAIN_INTEGRITY_FAULT",
                        "id":owner_id, "height":next_commit,
                        "reason":"CLOSED_LOOP_PARENT_HASH_MISMATCH",
                        "at_ms":round(now, 3),
                    }
                    ledger.append(integrity_event)
                    sample_events.append(integrity_event)
                    stop = stop or "BLOCK_FAULT_STOP_NO_RETRY"
                    break
                del buffered[next_commit]
                if last_committed_hash is not None:
                    linked += 1
                last_committed_hash = block_hash
                ledger.append({"event":"COMMIT_CONTIGUOUS",
                               "id":owner_id, "height":next_commit,
                               "at_ms":round(now, 3)})
                sample_events.append({"event":"COMMIT_CONTIGUOUS",
                                      "id":owner_id, "height":next_commit,
                                      "at_ms":round(now, 3)})
                next_commit += 1
                committed += 1
        # A terminal error does not cancel or falsely settle already in-flight
        # requests: remaining events will drain with their own outcomes.

    with OfflineLedger(ledger_path) as ledger:
        for _ in range(20000):
            while events and events[0][0] <= now:
                _, _, rid = heapq.heappop(events)
                settle(next(item for item in attempts if item["id"] == rid))
            if stop is None and now >= duration_ms:
                stop = "VIRTUAL_DISPATCH_DURATION_EXPIRED"
            action = None
            if stop is None and len(pending) < slots and now >= next_start:
                action = decide()
                if action is not None and action[0] == "STOP":
                    stop = action[1]
                elif action is not None and action[0] not in ("WAIT_HEAD",):
                    category, height, _ = action
                    if len(attempts) >= max_total:
                        stop = "TOTAL_ATTEMPT_BUDGET_EXHAUSTED"
                    else:
                        method = ("eth_chainId" if category == "CHAIN" else
                                  "eth_blockNumber" if category in
                                  ("INITIAL_HEAD", "HEAD_REFRESH") else
                                  "eth_getBlockByNumber")
                        rid = len(attempts) + 1
                        payload = {
                            "jsonrpc":"2.0", "id":rid, "method":method,
                            "params":[hex(height), True] if category == "BLOCK" else [],
                        }
                        valid_rpc_payload(payload)
                        require(len(pending) < 3 and
                                len(attempts) < max_total,
                                "CLOSED_LOOP_BUDGET_OVERFLOW")
                        if category == "BLOCK":
                            require(last_head is not None and
                                    height == next_height and height <= last_head and
                                    now < last_head_finished + head_ttl_ms,
                                    "CLOSED_LOOP_INVALID_BLOCK_DISPATCH")
                            next_height += 1
                            since_head += 1
                        elif category == "CHAIN":
                            first_chain_started = True
                        elif category == "INITIAL_HEAD":
                            first_head_started = True
                        else:
                            head_refreshes += 1
                            since_head = 0
                        if category in ("INITIAL_HEAD", "HEAD_REFRESH"):
                            require(head_inflight is None,
                                    "CLOSED_LOOP_DUPLICATE_HEAD_INFLIGHT")
                            head_inflight = rid
                        item_ms = durations[method][
                            latency_indices[method] % len(durations[method])]
                        latency_indices[method] += 1
                        nominal = item_ms * slowdown
                        latency = (min(nominal, timeout_ms) if
                                   category == "BLOCK" and height in
                                   oracle.timeout_blocks else nominal)
                        call = {"id":rid, "category":category, "height":height,
                                "method":method, "request":payload, "started":now,
                                "refresh_index":head_refreshes}
                        # Persist UNKNOWN synchronously BEFORE any completion
                        # event is put in the virtual network queue.
                        ledger.append({"event":"RESERVE_UNKNOWN", "id":rid,
                                       "category":category, "height":height,
                                       "method":method, "at_ms":round(now, 3),
                                       "confirmed_head":last_head})
                        sample_events.append({
                            "event":"RESERVE_UNKNOWN","id":rid,
                            "category":category,"height":height,"method":method,
                            "at_ms":round(now, 3),"confirmed_head":last_head,
                        })
                        attempts.append(call)
                        pending[rid] = call
                        started_by_method[method] += 1
                        started.append(now)
                        next_start = now + spacing_ms
                        max_inflight = max(max_inflight, len(pending))
                        heapq.heappush(events, (now + latency, seq, rid))
                        seq += 1
                        continue
            if stop is not None and not events:
                break
            candidates = [events[0][0]] if events else []
            if stop is None:
                if (action is not None and action[0] == "WAIT_HEAD" and
                        action[2] > now):
                    candidates.append(action[2])
                    idle_head_wait_ms += max(0, action[2] - now)
                if len(pending) < slots and now < next_start:
                    candidates.append(next_start)
                if now < duration_ms:
                    candidates.append(float(duration_ms))
            later = [v for v in candidates if v > now]
            if not later:
                stop = stop or "NO_ACTIONABLE_SCHEDULE"
                if not events:
                    break
                raise ValueError("CLOSED_LOOP_EVENT_QUEUE_STALLED")
            now = min(later)
        else:
            raise ValueError("CLOSED_LOOP_MAX_LOOP_ITERATIONS")
    require(not pending and len(attempts) <= max_total and
            started_by_method["eth_getBlockByNumber"] <= max_blocks and
            head_refreshes <= max_refreshes and max_inflight <= 3,
            "CLOSED_LOOP_ACCOUNTING_CONSTRAINT_FAILED")
    gaps = [started[i]-started[i-1] for i in range(1,len(started))]
    require(not gaps or min(gaps) >= spacing_ms - .001,
            "CLOSED_LOOP_GLOBAL_START_GAP_FAILED")
    elapsed_s = now / 1000
    last_height = next_commit - 1 if next_commit is not None else None
    source_tip_at_exit = oracle.head_at(now)
    known_unattempted = (
        max(0, last_head - (next_height - 1)) if
        last_head is not None and next_height is not None else None)
    return {
        "schema":SCHEMA,
        "mode":"OFFLINE_CLOSED_LOOP_SYNTHETIC_RPC_ONLY",
        "actual_network_requests":0, "network_sender_exists":False,
        "new_user_rpc_authorization":False,
        "source_oracle_is_real_bsc":False,
        "source_head_independent_live_network_verified":False,
        "prior_real_one_shot_permit":"CONSUMED",
        "stop_state":stop, "policy":policy,
        "virtual_elapsed_ms":round(now,3),
        "attempts":len(attempts),
        "method_attempt_counts":{k:started_by_method[k] for k in METHODS},
        "head_refreshes":head_refreshes,
        "block_attempts":started_by_method["eth_getBlockByNumber"],
        "block_responses_parsed_full":received,
        "contiguous_parent_verified_blocks":committed,
        "internal_parent_links":linked,
        "first_block_independently_anchored":False,
        "block_response_rate_bps":round(received/elapsed_s,3) if elapsed_s else 0,
        "contiguous_commit_rate_bps":round(committed/elapsed_s,3) if elapsed_s else 0,
        "attempted_missing_heights":sorted(set(requested_missing)),
        "invalid_parent_height":invalid_parent_height,
        "known_unattempted_from_last_sampled_head":known_unattempted,
        "last_confirmed_synthetic_head":last_head,
        "last_contiguously_committed_height":last_height,
        "last_sampled_head_minus_committed":(
            last_head-last_height if last_head is not None and
            last_height is not None else None),
        "synthetic_oracle_tip_at_exit_not_real_network":source_tip_at_exit,
        "synthetic_oracle_tip_minus_committed":(
            source_tip_at_exit-last_height if last_height is not None else None),
        "max_inflight_including_head":max_inflight,
        "min_global_start_gap_ms":round(min(gaps),3) if gaps else None,
        "pending_after_stop":len(pending),
        "buffer_peak":buffer_peak,
        "buffer_uncommitted_heights":sorted(buffered),
        "request_completion_p95_ms":_p95(latencies),
        "fake_outcome_counts":dict(sorted(completions.items())),
        "head_samples":head_samples,
        "faults":faults,
        "trace":sample_events,
        "completion_order_ids":completion_order,
        "real_provider_concurrent_rate":"UNVERIFIED",
        "f0_status":"NOT_PASSED", "production":"NO_GO",
    }


def main():
    p = argparse.ArgumentParser(description="Strict offline BSC 3-slot closed-loop FAKE")
    p.add_argument("--journal", type=Path, required=True)
    p.add_argument("--expected-sha256", required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    a = p.parse_args()
    observed, timing = replay_timings(a.journal.read_bytes(), a.expected_sha256)
    require(a.output_dir.is_dir() and not a.output_dir.is_symlink() and
            a.output_dir.stat().st_mode & 0o077 == 0,
            "CLOSED_LOOP_PRIVATE_OUTPUT_REQUIRED")
    cases = []
    for policy in ("checkpoint", "availability_wait"):
        for slowdown in (1.0, 1.5, 2.0):
            report = run_closed_loop(
                timing, a.output_dir /
                ("%s-%d.jsonl" % (policy, slowdown*10)),
                oracle=SyntheticBscOracle(), policy=policy,
                slowdown=slowdown)
            report.pop("trace")
            report.pop("completion_order_ids")
            cases.append(report)
    print(json.dumps({
        "schema":"bsc-f0-saved30-closed-loop-six-synthetic-cases-v1",
        "original_private_journal_sha256_verified":observed["journal_sha256"],
        "actual_network_requests":0,
        "synthetic_heads_and_blocks_only":True,
        "cases":cases,
        "decision":"F0_NOT_PASSED_PRODUCTION_NO_GO",
    }, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
