#!/usr/bin/env python3
"""Bounded adaptive HEAD/block collection CORE. Never launches an RPC connection.

Transport is an explicit injected callback. This library does not validate a
user permit and MUST NOT be wired to a real sender until independently audited
code+concrete permit and fresh explicit user authorization. Test fake only.
"""
from __future__ import annotations

from collections import Counter
from datetime import timedelta
import json
from pathlib import Path

from f0_l1_adaptive_head_plan import (
    init_plan, next_action, apply_head_result, apply_block_result, summarize,
)
from f0_l1_durable_journal import Journal, atomic_json
from f0_l1_http_wire import _parse_quantity
from f0_l1_window import (
    FROZEN_ROUTER_REGISTRY_BLOB, git_blob_sha1, load_frozen_cohort, cohort_watchlist,
)
from f0_l1_preflight import official_router_addresses
from f0_rpc_adapter import block_candidates, hexb

SCHEMA = "bsc-f0-adaptive-source-core-v1"
MAX_BUDGET = 128


def require(value, code):
    if not value:
        raise ValueError(code)


def collect_adaptive_injected(
    *, post, clock, mono, sleep, output_root: Path,
    cohort_raw: bytes, router_raw: bytes,
    max_total_attempts: int, max_block_reads: int, max_head_polls: int,
    duration_ms: int = 60000, min_interval_ms: int = 250,
    head_poll_interval_ms: int = 500, max_stagnant_poll_wait_ms: int = 8000,
    refresh_after_blocks: int = 4, max_response_bytes: int = 2_000_000,
    timeout_ms: int = 5000, anchor_initial_head: bool = False,
):
    """Orchestrate journalled HEAD checkpoints and full-block processing.

    *post* could itself use a real network. This function DOES NOT authorize it
    or attest its source. Only provided fake callbacks may be called without a
    separately approved real-runner and permit. No built-in HTTP/WS or CLI.
    """
    require(callable(post) and callable(clock) and callable(mono) and callable(sleep),
            "ADAPTIVE_EXPLICIT_DEPENDENCIES_REQUIRED")
    require(type(max_total_attempts) is int and 2 <= max_total_attempts <= MAX_BUDGET
            and type(max_block_reads) is int and 1 <= max_block_reads <= MAX_BUDGET
            and type(max_head_polls) is int and 1 <= max_head_polls <= MAX_BUDGET
            and type(duration_ms) is int and 1000 <= duration_ms <= 600000
            and type(timeout_ms) is int and 1000 <= timeout_ms <= 8000
            and type(max_response_bytes) is int and 1 <= max_response_bytes <= 2_000_000,
            "ADAPTIVE_SCOPE_INVALID")
    require(type(anchor_initial_head) is bool and
            (not anchor_initial_head or max_total_attempts >= 3),
            "ADAPTIVE_ANCHOR_SCOPE_INVALID")
    require(isinstance(output_root, Path) and output_root.is_dir()
            and not output_root.is_symlink()
            and not any((output_root / x).exists() or (output_root / x).is_symlink()
                        for x in ("report.json", "journal.json", "raw_responses")),
            "ADAPTIVE_OUTPUTS_NOT_FRESH")
    # Frozen source checks must precede even fake callback creation/invocation.
    cohort = load_frozen_cohort(cohort_raw)
    watched, _ = cohort_watchlist(cohort)
    require(git_blob_sha1(router_raw) == FROZEN_ROUTER_REGISTRY_BLOB,
            "FROZEN_ROUTER_REGISTRY_REQUIRED")
    routers = set(official_router_addresses(json.loads(router_raw)))
    require(len(watched) == 20 and len(routers) == 2,
            "FROZEN_PRIMARY_AND_ROUTER_REQUIRED")
    start_mono = mono()
    require(type(start_mono) in (int, float) and start_mono >= 0,
            "ADAPTIVE_MONOTONIC_INVALID")
    base_utc = clock()
    journal = Journal(
        output_root / "journal.json", limit=max_total_attempts, clock=clock,
        mono=mono, sleep=sleep, interval_ms=min_interval_ms,
        deadline=base_utc + timedelta(milliseconds=duration_ms),
        raw_dir=output_root / "raw_responses")
    journal.timeout_seconds = timeout_ms / 1000
    journal.response_cap = max_response_bytes

    def elapsed_ms():
        value = round((mono() - start_mono) * 1000)
        require(type(value) is int and value >= 0, "ADAPTIVE_MONOTONIC_REGRESSION")
        return value

    def take(method, params, category):
        require(len(journal.rows) < max_total_attempts,
                "ADAPTIVE_TOTAL_CAP_EXHAUSTED")
        return journal.request(method, params, category, post)

    state = None
    stop = None
    samples = []
    watch_tx = 0
    router_tx = 0
    total_block_tx = 0
    successful_height = None
    successful_hash = None
    verified_internal_parent_links = 0
    verified_initial_parent_links = 0
    initial_anchor_attempts = 0
    initial_anchor_height = None
    initial_anchor_hash = None
    parse_failures = 0
    block_failure_streak = 0

    try:
        chain, fault, _ = take("eth_chainId", [], "CHAIN_ID")
        if fault or chain is None:
            stop = "CHAIN_SOURCE_FAILED"
        else:
            try:
                _parse_quantity(chain, "eth_chainId", 1)
            except ValueError:
                stop = "CHAIN_ID_NOT_BSC"
        if stop is None and len(journal.rows) >= max_total_attempts:
            stop = "TOTAL_ATTEMPT_BUDGET_EXHAUSTED"
        if stop is None:
            head, fault, head_journal = take("eth_blockNumber", [], "INITIAL_HEAD")
            if fault or head is None:
                stop = "INITIAL_HEAD_SOURCE_FAILED"
            else:
                try:
                    initial_head = _parse_quantity(head, "eth_blockNumber", 2)
                except ValueError:
                    stop = "INITIAL_HEAD_INVALID"
        if stop is None:
            now_ms = elapsed_ms()
            state = init_plan(
                initial_head=initial_head, max_head_polls=max_head_polls,
                max_block_reads=max_block_reads,
                refresh_after_blocks=refresh_after_blocks,
                head_poll_interval_ms=head_poll_interval_ms,
                max_stagnant_poll_wait_ms=max_stagnant_poll_wait_ms,
                min_request_interval_ms=min_interval_ms,
                initial_monotonic_ms=now_ms)
            samples.append({
                "type": "INITIAL_HEAD", "sampled_head": initial_head,
                "sampled_local_utc": head_journal["completed_utc"],
                "last_attempted_height": initial_head,
                "sampled_head_minus_last_attempted_height": 0,
                "sampled_head_minus_last_received_height": 0,
                "source_type": "INJECTED_POST_UNVERIFIED",
            })

        # Optional, explicitly budgeted same-source anchor for initial HEAD.
        # This is NOT an independently verified canonical or finalized block.
        # It uses the existing Journal / caller-injected post and consumes one
        # total attempt. It does not count as a prospective watched block,
        # ordinary Router control, or a successful future-height read.
        if stop is None and anchor_initial_head:
            if len(journal.rows) >= max_total_attempts:
                stop = "TOTAL_ATTEMPT_BUDGET_EXHAUSTED"
            else:
                initial_anchor_attempts += 1
                anchor, fault, _ = take(
                    "eth_getBlockByNumber", [hex(initial_head), True],
                    "INITIAL_ANCHOR")
                if (fault is not None or anchor is None or
                        (type(anchor) is dict and anchor.get("result") is None)):
                    stop = "INITIAL_ANCHOR_SOURCE_FAILED"
                else:
                    try:
                        pinned = block_candidates(anchor, watched, routers)
                        require(pinned["block_number"] == initial_head,
                                "INITIAL_ANCHOR_HEIGHT_MISMATCH")
                        candidate = anchor["result"]
                        ahash = hexb(candidate["hash"], 32)
                        hexb(candidate["parentHash"], 32)
                    except (ValueError, TypeError, KeyError):
                        stop = "INITIAL_ANCHOR_INVALID"
                    else:
                        initial_anchor_height = initial_head
                        initial_anchor_hash = ahash
                        successful_height = initial_head
                        successful_hash = ahash

        while stop is None:
            remaining = duration_ms - elapsed_ms()
            if remaining <= 0:
                stop = "DURATION_CAP_EXPIRED"
                break
            decision = next_action(state, now_ms=elapsed_ms())
            if decision["action"] == "WAIT":
                wait_ms = decision["wait_ms"]
                require(type(wait_ms) is int and wait_ms > 0,
                        "ADAPTIVE_WAIT_INVALID")
                if wait_ms >= remaining:
                    stop = "DURATION_CAP_EXPIRED"
                    break
                sleep(wait_ms / 1000)
                continue
            if decision["action"] == "STOP":
                stop = decision["reason"]
                break
            if len(journal.rows) >= max_total_attempts:
                stop = "TOTAL_ATTEMPT_BUDGET_EXHAUSTED"
                break
            result, fault, item = take(
                decision["method"], decision["params"], decision["action"])
            request_started = round(
                item["requested_monotonic_ns"] / 1_000_000 - start_mono * 1000)
            require(type(request_started) is int and request_started >= 0,
                    "ADAPTIVE_REQUEST_CLOCK_INVALID")

            if decision["action"] == "READ_HEAD":
                sampled = None
                if fault is None and result is not None:
                    try:
                        sampled = _parse_quantity(
                            result, "eth_blockNumber", item["index"])
                    except ValueError:
                        pass
                state = apply_head_result(
                    state, now_ms=request_started, observed_head=sampled)
                if sampled is not None:
                    last_attempted = state["next_height"] - 1
                    samples.append({
                        "type": "HEAD_REFRESH",
                        "sampled_head": sampled,
                        "sampled_local_utc": item["completed_utc"],
                        "last_attempted_height": last_attempted,
                        "sampled_head_minus_last_attempted_height":
                            sampled - last_attempted,
                        "sampled_head_minus_last_received_height":
                            None if successful_height is None
                            else sampled - successful_height,
                        "source_type": "INJECTED_POST_UNVERIFIED",
                    })
                if state["stopped_reason"]:
                    stop = state["stopped_reason"]
                continue

            accepted = False
            parent_mismatch = False
            if fault is None and result is not None:
                try:
                    parsed = block_candidates(result, watched, routers)
                    if parsed["block_number"] == decision["height"]:
                        block = result["result"]
                        block_hash = hexb(block["hash"], 32)
                        parent_hash = hexb(block["parentHash"], 32)
                        if successful_height == decision["height"] - 1:
                            if parent_hash != successful_hash:
                                parent_mismatch = True
                            elif (successful_height == initial_anchor_height and
                                  state["blocks_received"] == 0):
                                verified_initial_parent_links += 1
                            else:
                                verified_internal_parent_links += 1
                        if not parent_mismatch:
                            accepted = True
                except (ValueError, TypeError, KeyError):
                    parse_failures += 1
            if accepted:
                successful_height = decision["height"]
                successful_hash = block_hash
                total_block_tx += parsed["full_block_tx_count"]
                for candidate in parsed["candidates"]:
                    if candidate["group"] == "WATCHLIST":
                        watch_tx += 1
                    else:
                        router_tx += 1
                block_failure_streak = 0
            else:
                block_failure_streak += 1
            state = apply_block_result(
                state, now_ms=request_started, received=accepted)
            if parent_mismatch:
                stop = "CONSECUTIVE_BLOCK_PARENT_MISMATCH"
            elif block_failure_streak >= 3:
                stop = "THREE_CONSECUTIVE_UNUSABLE_BLOCKS"

    except KeyboardInterrupt:
        # Do not synthesize completion if Journal left a durable UNKNOWN attempt.
        raise

    method_counts = Counter(row["method"] for row in journal.rows)
    out = {
        "schema": SCHEMA, "mode": "INJECTED_TRANSPORT_UNVERIFIED",
        "network_calls_implemented_in_this_module": 0,
        "injected_post_may_perform_real_network": True,
        "external_real_rpc_calls": "UNVERIFIED",
        "source_attestation": "UNVERIFIED_CALLER_CALLBACK",
        "stop_state": stop, "sample_duration_elapsed_ms": elapsed_ms(),
        "total_attempts": len(journal.rows),
        "max_total_attempts": max_total_attempts,
        "method_counts": dict(sorted(method_counts.items())),
        "category_counts": dict(sorted(Counter(
            row["category"] for row in journal.rows).items())),
        "method_counts_reconcile": sum(method_counts.values()) == len(journal.rows),
        "head_samples": samples, "head_refreshes":
            sum(row["category"] == "READ_HEAD" for row in journal.rows),
        "block_read_attempts":
            sum(row["category"] == "READ_BLOCK" for row in journal.rows),
        "block_read_successes": state["blocks_received"] if state else 0,
        "block_read_failures": state["blocks_failed"] if state else 0,
        "unattempted_block_budget":
            max_block_reads - (state["block_reads_attempted"] if state else 0),
        "attempted_missing_heights":
            list(state["missing_heights"]) if state else [],
        "verified_internal_parent_links": verified_internal_parent_links,
        "verified_initial_parent_links": verified_initial_parent_links,
        "initial_anchor_requested": anchor_initial_head,
        "initial_anchor_attempts": initial_anchor_attempts,
        "initial_anchor_height": initial_anchor_height,
        "initial_anchor_hash": initial_anchor_hash,
        "initial_anchor_evidence_scope": (
            "SAME_SOURCE_NOT_CANONICAL_FINALITY_OR_INDEPENDENT_ANCHOR"
            if initial_anchor_height is not None else "NOT_ESTABLISHED"),
        "initial_saved_block_parent_anchored":
            verified_initial_parent_links == 1,
        "all_received_transactions": total_block_tx,
        "watch_sender_candidates": watch_tx,
        "documentary_router_address_candidates": router_tx,
        "candidate_control_eligible": False,
        "e2_attested": False, "actual_e3": False, "actual_quote_count": 0,
        "parse_failures": parse_failures,
        "journal_attempts": len(journal.rows),
        "private_raw_archives": sum(
            "local_raw_response_file" in row for row in journal.rows),
        "provider_billed": "UNVERIFIED",
        "scheduler": summarize(state) if state else None,
        "head_lag_interpretation":
            "LAST_SOURCE_SAMPLED_HEAD_ONLY_NOT_INDEPENDENT_NETWORK_HEAD",
    }
    atomic_json(output_root / "report.json", out)
    return out
