#!/usr/bin/env python3
"""Pure offline F0 block-head scheduling decisions, not a network runner.

Prospective: do not fetch beyond the last OBSERVED head; checkpoint the head
regularly; never skip a missing height silently. This module neither issues
RPC nor contains an executable CLI, permit, HTTP callback, sleeping or signing.
All elapsed times supplied here are from synthetic caller inputs.
"""
from __future__ import annotations

import copy

SCHEMA = "bsc-f0-adaptive-head-plan-offline-v1"


def require(ok, code):
    if not ok:
        raise ValueError(code)


def init_plan(*, initial_head, max_head_polls, max_block_reads,
              refresh_after_blocks=4, head_poll_interval_ms=500,
              min_request_interval_ms=250, initial_monotonic_ms=0,
              max_stagnant_poll_wait_ms=8000):
    """Initial head MUST come from a separately journalled verified source.

    Budgets below exclude initial chainId and initial head reads, both of which
    still consume any prospective live permit's overall RPC attempt budget.
    """
    require(type(initial_head) is int and initial_head > 0 and
            type(max_head_polls) is int and 1 <= max_head_polls <= 1000 and
            type(max_block_reads) is int and 1 <= max_block_reads <= 4600 and
            type(refresh_after_blocks) is int and 1 <= refresh_after_blocks <= 100 and
            type(head_poll_interval_ms) is int and 250 <= head_poll_interval_ms <= 60000 and
            type(min_request_interval_ms) is int and 250 <= min_request_interval_ms <= 60000 and
            type(initial_monotonic_ms) is int and initial_monotonic_ms >= 0 and
            type(max_stagnant_poll_wait_ms) is int and
            head_poll_interval_ms <= max_stagnant_poll_wait_ms <= 60000,
            "ADAPTIVE_INVALID_PLAN")
    return {
        "schema": SCHEMA, "initial_head": initial_head,
        "confirmed_head": initial_head, "next_height": initial_head + 1,
        "head_polls_attempted": 0, "block_reads_attempted": 0,
        "blocks_received": 0, "blocks_failed": 0,
        "missing_heights": [], "head_poll_failure": False,
        "max_head_polls": max_head_polls, "max_block_reads": max_block_reads,
        "refresh_after_blocks": refresh_after_blocks,
        "head_poll_interval_ms": head_poll_interval_ms,
        "max_stagnant_poll_wait_ms": max_stagnant_poll_wait_ms,
        "head_stagnation_streak": 0,
        "min_request_interval_ms": min_request_interval_ms,
        "last_head_sample_ms": initial_monotonic_ms,
        "last_request_ms": None, "blocks_since_head_poll": 0,
        "stopped_reason": None,
        "source": "OFFLINE_INJECTED_HEAD_SNAPSHOTS_ONLY",
        "actual_rpc_calls_by_this_module": 0,
        "real_head_lag_verified": False,
        "live_control_eligible": False,
    }


def next_action(state, *, now_ms):
    """Decide one step without mutating state or sending network requests."""
    require(isinstance(state, dict) and state.get("schema") == SCHEMA and
            type(now_ms) is int and now_ms >= state["last_head_sample_ms"],
            "ADAPTIVE_INVALID_CLOCK_OR_STATE")
    if state["stopped_reason"]:
        return {"action": "STOP", "reason": state["stopped_reason"]}
    if state["block_reads_attempted"] >= state["max_block_reads"]:
        return {"action": "STOP", "reason": "BLOCK_ATTEMPT_BUDGET_COMPLETE"}
    last = state["last_request_ms"]
    if last is not None:
        require(now_ms >= last, "ADAPTIVE_CLOCK_REGRESSION")
        if now_ms - last < state["min_request_interval_ms"]:
            return {"action": "WAIT", "reason": "REQUEST_RATE_LIMIT",
                    "wait_ms": state["min_request_interval_ms"] - (now_ms-last)}

    head_due = (state["next_height"] > state["confirmed_head"] or
                state["blocks_since_head_poll"] >= state["refresh_after_blocks"])
    if head_due:
        if state["head_polls_attempted"] >= state["max_head_polls"]:
            return {"action": "STOP", "reason": "HEAD_POLL_BUDGET_EXHAUSTED"}
        delta = now_ms - state["last_head_sample_ms"]
        # Stalled heads must not consume the finite HEAD budget every 500ms.
        # After N unchanged samples wait 2^N times the normal poll interval,
        # capped at the explicit maximum. This is only a wait decision; the
        # next real HEAD call would still count as an attempted request.
        stagnant = min(state["head_stagnation_streak"], 16)
        effective_wait = min(state["head_poll_interval_ms"] * (1 << stagnant),
                             state["max_stagnant_poll_wait_ms"])
        if delta < effective_wait:
            return {"action": "WAIT", "reason": "HEAD_STAGNATION_BACKOFF"
                    if stagnant else "HEAD_POLL_MIN_INTERVAL",
                    "wait_ms": effective_wait - delta}
        return {"action": "READ_HEAD", "method": "eth_blockNumber",
                "params": [], "reason": "UNKNOWN_OR_STALE_CONFIRMED_HEAD"}
    return {"action": "READ_BLOCK", "method": "eth_getBlockByNumber",
            "params": [hex(state["next_height"]), True],
            "height": state["next_height"],
            "reason": "AT_OR_BELOW_LAST_CONFIRMED_HEAD_ONLY"}


def apply_head_result(state, *, now_ms, observed_head):
    """Consume one journalled HEAD attempt. A failure stops, not retries."""
    action = next_action(state, now_ms=now_ms)
    require(action["action"] == "READ_HEAD", "ADAPTIVE_NOT_READY_FOR_HEAD")
    new = copy.deepcopy(state)
    new["head_polls_attempted"] += 1
    new["last_request_ms"] = now_ms
    new["last_head_sample_ms"] = now_ms
    new["blocks_since_head_poll"] = 0
    if observed_head is None:
        new["head_poll_failure"] = True
        new["stopped_reason"] = "HEAD_SOURCE_FAILED_NO_RETRY"
    else:
        require(type(observed_head) is int and observed_head > 0,
                "ADAPTIVE_HEAD_RESPONSE_INVALID")
        if observed_head < new["confirmed_head"]:
            new["stopped_reason"] = "HEAD_REGRESSED_UNVERIFIED"
        else:
            if observed_head == new["confirmed_head"]:
                new["head_stagnation_streak"] += 1
            else:
                new["confirmed_head"] = observed_head
                new["head_stagnation_streak"] = 0
    return new


def apply_block_result(state, *, now_ms, received):
    """Consume one previously journalled exact-height attempt. No backfill retry."""
    action = next_action(state, now_ms=now_ms)
    require(action["action"] == "READ_BLOCK" and type(received) is bool,
            "ADAPTIVE_NOT_READY_FOR_BLOCK")
    new = copy.deepcopy(state)
    new["block_reads_attempted"] += 1
    new["last_request_ms"] = now_ms
    new["blocks_since_head_poll"] += 1
    if received:
        new["blocks_received"] += 1
    else:
        new["blocks_failed"] += 1
        new["missing_heights"].append(action["height"])
    new["next_height"] += 1
    return new


def summarize(state):
    require(isinstance(state, dict) and state.get("schema") == SCHEMA,
            "ADAPTIVE_INVALID_STATE")
    return {
        "schema": SCHEMA, "mode": "OFFLINE_SCHEDULER_STATE_NOT_LIVE",
        "initial_head": state["initial_head"],
        "latest_sampled_head": state["confirmed_head"],
        "next_unattempted_height": state["next_height"],
        "head_polls_attempted_after_initial": state["head_polls_attempted"],
        "head_stagnation_streak": state["head_stagnation_streak"],
        "block_reads_attempted": state["block_reads_attempted"],
        "block_reads_received": state["blocks_received"],
        "block_reads_failed": state["blocks_failed"],
        "explicit_missing_heights": list(state["missing_heights"]),
        "counting_identity_and_initial_head_calls": "NOT_INCLUDED_IN_SIMULATED_BUDGET",
        "first_seen_source": "NONE_OFFLINE_ONLY",
        "actual_rpc_calls_by_this_module": 0,
        "live_head_lag_verified": False,
        "live_control_eligible": False,
        "stopped_reason": state["stopped_reason"],
    }


def throughput_scenarios(*, saved_blocks, header_span_s, local_receipt_span_s,
                         recorded_block_request_median_ms,
                         candidate_interval_ms=250):
    """Arithmetic what-if only; NOT measured actual head-lag or future rate."""
    require(type(saved_blocks) is int and saved_blocks >= 2 and
            type(header_span_s) in (int,float) and header_span_s > 0 and
            type(local_receipt_span_s) in (int,float) and local_receipt_span_s > 0 and
            type(recorded_block_request_median_ms) in (int,float) and
            recorded_block_request_median_ms > 0 and
            type(candidate_interval_ms) is int and candidate_interval_ms >= 250,
            "ADAPTIVE_RATE_SCENARIO_INVALID")
    intervals=saved_blocks-1
    chain_interval_ms=header_span_s*1000/intervals
    observed_receipt_pace_ms=local_receipt_span_s*1000/intervals
    no_fixed_wait_pace_ms=max(recorded_block_request_median_ms,
                              candidate_interval_ms)
    return {
        "scenario_only": True,
        "input_kind": "HISTORICAL_SAVED_HEADER_AND_LOCAL_RECEIPT_SPANS",
        "observed_block_interval_mean_ms": round(chain_interval_ms,3),
        "observed_local_receipt_pace_ms": round(observed_receipt_pace_ms,3),
        "observed_elapsed_minus_header_span_s":
            round(local_receipt_span_s-header_span_s,3),
        "optimistic_sequential_no_fixed_wait_pace_ms":
            round(no_fixed_wait_pace_ms,3),
        "projected_sequential_gap_growth_over_same_intervals_s":
            round((no_fixed_wait_pace_ms-chain_interval_ms)*intervals/1000,3),
        "sequential_median_alone_can_keep_up":
            no_fixed_wait_pace_ms <= chain_interval_ms,
        "minimum_capacity_to_keep_up_ms_per_block_estimate":
            round(chain_interval_ms,3),
        "not_measured": [
            "LIVE_HEAD_LAG", "GLOBAL_FIRST_SEEN",
            "FUTURE_HTTP_THROUGHPUT", "PARALLEL_SOURCE_CAPACITY",
            "FILL_RATE_FOR_FAILED_BLOCKS"],
        "decision": ("ADAPTIVE_WAIT_REMOVAL_ALONE_INSUFFICIENT"
                     if no_fixed_wait_pace_ms > chain_interval_ms
                     else "SEQUENTIAL_POSSIBLY_FAST_ENOUGH_NOT_YET_PROVEN"),
    }
