#!/usr/bin/env python3
"""OFFLINE-only adaptive-head integration with the audited durable Journal.

Only consumes predeclared in-memory JSON-RPC response fixtures. There is NO
network callback parameter, socket transport, CLI, permit or background worker.
The existing Journal is imported from the real runner to exercise its exact
durable presend/accounting implementation; live_https_post is NEVER called.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path

from f0_l1_adaptive_head_plan import (
    init_plan, next_action, apply_block_result, apply_head_result, summarize)
from f0_l1_durable_journal import Journal, atomic_json
from f0_l1_http_wire import _parse_quantity
from f0_l1_window import (
    FROZEN_ROUTER_REGISTRY_BLOB, git_blob_sha1, load_frozen_cohort,
    cohort_watchlist)
from f0_l1_preflight import official_router_addresses
from f0_rpc_adapter import block_candidates

SCHEMA = "bsc-f0-adaptive-journal-fake-replay-v1"
MAX_SIMULATED_CALLS = 128


def require(ok, error):
    if not ok:
        raise ValueError(error)


class FakeClock:
    """Deterministic virtual time, including fake transport latency."""
    def __init__(self):
        self.start = datetime(2026, 10, 20, tzinfo=timezone.utc)
        self.now_ms = 0

    def utc(self):
        return self.start + timedelta(milliseconds=self.now_ms)

    def mono(self):
        return self.now_ms / 1000

    def sleep(self, seconds):
        require(type(seconds) in (int, float) and seconds > 0,
                "FAKE_CLOCK_SLEEP_INVALID")
        delta = max(1, round(seconds * 1000))
        self.now_ms += delta


def replay_fake_head_and_blocks(
    *, frames: list[dict], cohort_raw: bytes, router_raw: bytes,
    output_root: Path, max_total_attempts: int,
    max_head_polls: int, max_block_reads: int,
    refresh_after_blocks: int = 4,
    head_poll_interval_ms: int = 500,
    max_stagnant_poll_wait_ms: int = 8000,
    min_request_interval_ms: int = 250,
    max_simulated_duration_ms: int = 120000,
) -> dict:
    """Run strict in-memory responses using the SAME persisted Journal as live.

    Script frames have {method, params, result/error, latency_ms} but NO HTTP
    provider, URL or transport callback. Never label fixture HEAD as real.
    Caller cannot supply a network sender through this public API.
    """
    require(type(max_total_attempts) is int and
            2 <= max_total_attempts <= MAX_SIMULATED_CALLS and
            type(max_head_polls) is int and 1 <= max_head_polls <= 120 and
            type(max_block_reads) is int and 1 <= max_block_reads <= 120 and
            type(max_simulated_duration_ms) is int and
            1000 <= max_simulated_duration_ms <= 600000,
            "INVALID_FAKE_TOTAL_BUDGET")
    require(isinstance(frames, list) and len(frames) <= MAX_SIMULATED_CALLS and
            all(type(x) is dict for x in frames),
            "FAKE_FRAMES_REQUIRED")
    require(isinstance(output_root, Path) and output_root.is_dir() and
            not output_root.is_symlink() and
            not (output_root / "journal.json").exists() and
            not (output_root / "report.json").exists() and
            not (output_root / "raw_responses").exists(),
            "FAKE_OUTPUTS_NOT_FRESH")
    cohort = load_frozen_cohort(cohort_raw)
    watched, _ = cohort_watchlist(cohort)
    require(git_blob_sha1(router_raw) == FROZEN_ROUTER_REGISTRY_BLOB,
            "FROZEN_ROUTER_REGISTRY_REQUIRED")
    routers = set(official_router_addresses(json.loads(router_raw)))
    require(len(watched) == 20 and len(routers) == 2,
            "FROZEN_SIGNER_ROUTER_COUNTS_INVALID")

    clock = FakeClock()
    audit = Journal(
        output_root / "journal.json",
        limit=max_total_attempts, clock=clock.utc, mono=clock.mono,
        sleep=clock.sleep, interval_ms=min_request_interval_ms,
        deadline=clock.utc() + timedelta(milliseconds=max_simulated_duration_ms),
        raw_dir=output_root / "raw_responses")
    audit.timeout_seconds = 5.0
    audit.response_cap = 2_000_000

    def in_memory_only_post(endpoint, request_bytes, timeout, cap):
        request = json.loads(request_bytes)
        idx = request["id"] - 1
        require(idx < len(frames), "SCRIPT_EXHAUSTED")
        frame = frames[idx]
        require(set(frame) <= {"method", "params", "result", "error", "latency_ms"} and
                frame.get("method") == request["method"] and
                frame.get("params") == request["params"] and
                ("result" in frame) != ("error" in frame),
                "SCRIPTED_REQUEST_MISMATCH")
        latency = frame.get("latency_ms", 0)
        require(type(latency) is int and 0 <= latency <= 5000,
                "SCRIPTED_LATENCY_INVALID")
        if latency:
            clock.sleep(latency / 1000)
        payload = {"jsonrpc": "2.0", "id": request["id"]}
        payload["result" if "result" in frame else "error"] = (
            frame["result"] if "result" in frame else frame["error"])
        raw = json.dumps(payload, separators=(",", ":")).encode()
        require(len(raw) <= cap, "SCRIPTED_RESPONSE_TOO_LARGE")
        return 200, {"Content-Type": "application/json"}, raw

    state = None
    stop = None
    source_issue = None
    observations = []
    candidates = Counter()
    consecutive_block_errors = 0

    def take(method, params, category):
        return audit.request(method, params, category, in_memory_only_post)

    try:
        chain, problem, _ = take("eth_chainId", [], "CHAIN_ID")
        if problem or chain is None or "error" in chain:
            stop = "FAKE_CHAIN_SOURCE_FAILED"
        else:
            try:
                _parse_quantity(chain, "eth_chainId", 1)
            except ValueError:
                stop = "FAKE_WRONG_CHAIN"
        if stop is None and len(audit.rows) >= max_total_attempts:
            stop = "TOTAL_ATTEMPT_BUDGET_EXHAUSTED"
        if stop is None:
            first_head, problem, _ = take("eth_blockNumber", [], "INITIAL_HEAD")
            if problem or first_head is None or "error" in first_head:
                stop = "FAKE_INITIAL_HEAD_FAILED"
            else:
                try:
                    initial_height = _parse_quantity(first_head, "eth_blockNumber", 2)
                except ValueError:
                    stop = "FAKE_INITIAL_HEAD_FAILED"
        if stop is None:
            state = init_plan(
                initial_head=initial_height,
                max_head_polls=max_head_polls, max_block_reads=max_block_reads,
                refresh_after_blocks=refresh_after_blocks,
                head_poll_interval_ms=head_poll_interval_ms,
                min_request_interval_ms=min_request_interval_ms,
                max_stagnant_poll_wait_ms=max_stagnant_poll_wait_ms,
                initial_monotonic_ms=clock.now_ms)
            observations.append({
                "type": "INITIAL_HEAD", "sampled_head": initial_height,
                "next_needed_height": initial_height + 1,
                "sampled_head_minus_processed_height": 0,
                "virtual_monotonic_ms": clock.now_ms})
        while stop is None:
            if clock.now_ms >= max_simulated_duration_ms:
                stop = "VIRTUAL_TIME_CAP_REACHED"
                break
            action = next_action(state, now_ms=clock.now_ms)
            if action["action"] == "WAIT":
                next_wait = action["wait_ms"]
                require(type(next_wait) is int and next_wait > 0,
                        "FAKE_WAIT_MUST_MAKE_PROGRESS")
                if clock.now_ms + next_wait > max_simulated_duration_ms:
                    stop = "VIRTUAL_TIME_CAP_REACHED"
                    break
                clock.sleep(next_wait / 1000)
                continue
            if action["action"] == "STOP":
                stop = action["reason"]
                break
            if len(audit.rows) >= max_total_attempts:
                stop = "TOTAL_ATTEMPT_BUDGET_EXHAUSTED"
                break
            result, problem, item = take(
                action["method"], action["params"], action["action"],
                )
            send_ms = item["requested_monotonic_ns"] // 1_000_000
            if action["action"] == "READ_HEAD":
                updated = None
                if problem is None and result is not None and "error" not in result:
                    try:
                        updated = _parse_quantity(
                            result, "eth_blockNumber", item["index"])
                    except ValueError:
                        pass
                state = apply_head_result(state, now_ms=send_ms,
                                          observed_head=updated)
                if updated is not None:
                    observations.append({
                        "type": "REFRESHED_HEAD",
                        "sampled_head": updated,
                        "next_needed_height": state["next_height"],
                        "sampled_head_minus_processed_height":
                            updated - (state["next_height"] - 1),
                        "virtual_monotonic_ms": clock.now_ms,
                        "head_stagnation_streak":
                            state["head_stagnation_streak"]})
                if state["stopped_reason"]:
                    stop = state["stopped_reason"]
            else:
                accepted = False
                if problem is None and result is not None and "error" not in result:
                    try:
                        parsed = block_candidates(result, watched, routers)
                        accepted = parsed["block_number"] == action["height"]
                    except (ValueError, TypeError, KeyError):
                        accepted = False
                if accepted:
                    for match in parsed["candidates"]:
                        candidates[match["group"]] += 1
                    consecutive_block_errors = 0
                else:
                    consecutive_block_errors += 1
                state = apply_block_result(
                    state, now_ms=send_ms, received=accepted)
                if consecutive_block_errors >= 3:
                    stop = "THREE_CONSECUTIVE_BLOCK_FAILURES"

    except KeyboardInterrupt:
        # The live Journal has *already* persisted any interrupted send as
        # ATTEMPTED_OUTCOME_UNKNOWN. No report is forged on interruption.
        raise

    totals = dict(Counter(row["method"] for row in audit.rows))
    report = {
        "schema": SCHEMA, "mode": "OFFLINE_FAKE_RESPONSES_ONLY",
        "stop_state": stop,
        "actual_rpc_calls": 0,
        "simulated_attempts_persisted": len(audit.rows),
        "total_attempt_cap": max_total_attempts,
        "method_counts": dict(sorted(totals.items())),
        "identity_and_initial_head_attempts":
            sum(row["category"] in ("CHAIN_ID", "INITIAL_HEAD") for row in audit.rows),
        "periodic_head_polls_attempted":
            sum(row["category"] == "READ_HEAD" for row in audit.rows),
        "full_block_attempts":
            sum(row["category"] == "READ_BLOCK" for row in audit.rows),
        "all_method_counts_sum_to_attempted":
            sum(totals.values()) == len(audit.rows),
        "head_snapshots": observations,
        "scheduler": summarize(state) if state else None,
        "candidate_counts": dict(sorted(candidates.items())),
        "control_eligible": False,
        "wallet_signer_verified": False,
        "e2_attested": False,
        "actual_e3": False,
        "quote_count": 0,
        "source_issue": source_issue,
        "pending_fixture_frames": max(0, len(frames) - len(audit.rows)),
        "private_raw_responses_recorded":
            sum("local_raw_response_file" in row for row in audit.rows),
        "source_provenance": "IN_MEMORY_SCRIPTED_RPC_ONLY_NOT_CHAIN",
    }
    atomic_json(output_root / "report.json", report)
    return report
