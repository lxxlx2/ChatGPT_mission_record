#!/usr/bin/env python3
"""Offline, byte-pinned 2026-10-20 BSC F0 sample-source feasibility gate.

This tool reads only the PUBLIC REDACTED Git-tracked summary. It cannot
reverify the private 62 raw responses or claim independent chain-head timing.
There is no RPC, HTTP, socket, filesystem mutation or live sender.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import re

SCHEMA = "bsc-f0-l1-saved-source-rate-gate-v1"
INPUT_SCHEMA = "bsc-f0-short60-offline-lag-audit-public-summary-v1"
INPUT_BLOB_SHA1 = "ce1d9cb9e19e12e291da1b3e3406f57d6958ad54"
EXPECTED_AUDIT = "INDEPENDENT_REVIEW_REQUEST_CHANGES_P1_PARENT_HASH_ANCHOR"
SUMMARY_FILE = Path(__file__).resolve().parent / (
    "F0_SHORT60_LAG_OFFLINE_RESULT_20261020.json"
)
SELECTOR = re.compile(r"0x[0-9a-fA-F]{8}\Z")


def _need(condition: bool, error: str):
    if not condition:
        raise ValueError(error)


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        _need(key not in result, "DUPLICATE_JSON_FIELD")
        result[key] = value
    return result


def _invalid_constant(_):
    raise ValueError("NONFINITE_JSON_NUMBER")


def git_blob_sha1(raw: bytes) -> str:
    _need(type(raw) is bytes, "INPUT_NOT_BYTES")
    return hashlib.sha1(
        b"blob " + str(len(raw)).encode("ascii") + b"\x00" + raw
    ).hexdigest()


def parse_pinned_summary(raw: bytes) -> dict:
    """The published digest binds only the redacted summary, not private RAW."""
    _need(type(raw) is bytes and 0 < len(raw) <= 16384,
          "PUBLIC_SUMMARY_INPUT_BOUNDS")
    _need(git_blob_sha1(raw) == INPUT_BLOB_SHA1,
          "PUBLIC_SUMMARY_GIT_BLOB_MISMATCH")
    try:
        value = json.loads(raw, object_pairs_hook=_pairs,
                           parse_constant=_invalid_constant)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("PUBLIC_SUMMARY_JSON_INVALID") from exc
    _need(type(value) is dict and value.get("schema") == INPUT_SCHEMA,
          "PUBLIC_SUMMARY_SCHEMA_INVALID")
    return value


def _integer(row: dict, field: str, minimum: int = 0) -> int:
    value = row.get(field)
    _need(type(value) is int and value >= minimum,
          "PUBLIC_SUMMARY_INVALID_INT:" + field)
    return value


def _number(row: dict, field: str, positive: bool = True) -> float:
    value = row.get(field)
    _need(type(value) in (int, float) and math.isfinite(value)
          and (value > 0 if positive else value >= 0),
          "PUBLIC_SUMMARY_INVALID_NUMBER:" + field)
    return float(value)


def assess_public_fields(row: dict) -> dict:
    """Pure fail-closed semantic assessment; does not attest original input."""
    _need(type(row) is dict and row.get("schema") == INPUT_SCHEMA,
          "PUBLIC_SUMMARY_SCHEMA_INVALID")
    heights = _integer(row, "blocks", 2)
    first = _integer(row, "height_first", 1)
    last = _integer(row, "height_last", 1)
    _need(last - first + 1 == heights, "NONCONSECUTIVE_HEIGHT_RANGE")

    raw = _integer(row, "raw_responses_total", 1)
    verified = _integer(row, "raw_responses_verified_sha256")
    _need(raw == heights + 2 and verified == raw,
          "PUBLIC_SUMMARY_RAW_RESPONSE_COUNT_INCONSISTENT")
    _need(_integer(row, "parent_hash_links_verified") == heights - 1
          and row.get("parent_hash_first_block_unanchored") is True,
          "PUBLIC_SUMMARY_PARENT_PROOF_MISMATCH")
    _need(row.get("audit_review_status") == EXPECTED_AUDIT,
          "PUBLIC_SUMMARY_HISTORICAL_P1_STATUS_CHANGED")
    _need(row.get("source_archive") == "PRIVATE_MISSION_EVIDENCE_LOCAL_ONLY"
          and row.get("network_requests_by_analysis") == 0
          and type(row.get("network_requests_by_analysis")) is int,
          "PUBLIC_SUMMARY_PROVENANCE_INVALID")

    onchain_span = _number(row, "header_timestamp_span_s")
    local_span = _number(row, "local_receipt_span_s")
    _need(onchain_span > 0 and local_span > 0,
          "PUBLIC_SUMMARY_TIME_WINDOW_INVALID")
    interval_count = heights - 1
    _need(abs(
        _number(row, "mean_chain_interval_s_from_header_ts")
        - onchain_span / interval_count
    ) <= 0.001, "PUBLIC_SUMMARY_HEADER_INTERVAL_INCOHERENT")
    _need(_number(row, "receipt_minus_header_ms_median", False) >= 0
          and _number(row, "block_response_elapsed_ms_median") > 0,
          "PUBLIC_SUMMARY_CLOCK_PROXY_INVALID")

    watched = _integer(row, "watch_signer_candidate_transactions")
    router = _integer(row, "router_address_candidate_transactions")
    all_tx = _integer(row, "total_full_block_transactions")
    _need(watched <= all_tx and router <= all_tx,
          "PUBLIC_SUMMARY_CANDIDATES_EXCEED_TRANSACTION_COUNT")
    selectors = row.get("router_selector_address_match_distribution")
    _need(type(selectors) is dict and all(
        type(k) is str and SELECTOR.fullmatch(k) is not None
        and type(v) is int and v >= 0
        for k, v in selectors.items()),
        "PUBLIC_SUMMARY_ROUTER_SELECTOR_INVALID")
    _need(sum(selectors.values()) == router,
          "PUBLIC_SUMMARY_ROUTER_SELECTOR_COUNT_MISMATCH")
    _need(row.get("router_swap_causality_attested") is False
          and row.get("control_eligible") is False
          and row.get("wallet_signer_eligibility") == "NOT_ESTABLISHED"
          and row.get("actual_e3") is False
          and _integer(row, "quoted_actual_count") == 0,
          "PUBLIC_SUMMARY_UNPROVEN_OUTCOME_PROMOTION")

    # Both rates describe the same 59 height *intervals*, not 60 new blocks.
    # This is a sample-only post-facto span comparison, NOT observed head lag,
    # provider-wide throughput, prospective first-seen, or independent chain tip.
    chain_rate = interval_count / onchain_span
    receive_rate = interval_count / local_span
    sample_rate_insufficient = receive_rate < chain_rate
    return {
        "schema": SCHEMA,
        "input_git_blob_sha1": INPUT_BLOB_SHA1,
        "input_provenance": "REDACTED_GIT_SUMMARY_NOT_PRIVATE_RAW_REVERIFICATION",
        "network_requests_by_analysis": 0,
        "raw_responses_reported_verified": verified,
        "raw_response_sha256_recomputed_by_this_tool": 0,
        "block_heights": heights,
        "height_interval_count": interval_count,
        "header_timestamp_span_s": onchain_span,
        "local_response_span_s": local_span,
        "sample_header_progress_blocks_per_s": round(chain_rate, 4),
        "sample_response_progress_blocks_per_s": round(receive_rate, 4),
        "sample_progress_rate_ratio_header_over_response":
            round(chain_rate / receive_rate, 4),
        "sample_span_excess_s": round(local_span - onchain_span, 4),
        "sample_extra_response_span_per_height_interval_ms":
            round((local_span - onchain_span) * 1000 / interval_count, 3),
        "serial_sample_rate_gate": (
            "FAIL_OBSERVED_SAMPLE_ONLY" if sample_rate_insufficient
            else "NOT_FAILED_IN_OBSERVED_SAMPLE_ONLY"
        ),
        "independent_live_chain_head_lag_proven": False,
        "improved_three_slot_or_alternate_provider_capacity_proven": False,
        "all_blocks_parent_anchored": False,
        "historical_parent_anchor_review_status": EXPECTED_AUDIT,
        "wallet_signer_candidates_observed": watched,
        "watched_trade_success_and_cost_basis_verified": False,
        "router_address_selector_candidates": router,
        "router_swap_causality_proven": False,
        "randomized_control_eligible": False,
        "actual_executable_quotes": 0,
        "actual_follow_profitability_proven": False,
        "research_evidence_decision": "L1_INSUFFICIENT_FEASIBILITY_EVIDENCE",
        "f0_status": "F0_NOT_PASSED",
        "next_authorized_trial_gates": [
            "FIXED_SHA_INDEPENDENT_CODE_REVIEW_AND_NEW_EXPLICIT_USER_SCOPE",
            "TIMESTAMP_EVERY_REAL_BLOCKNUMBER_HEAD_AND_BLOCK_RESPONSE",
            "FIRST_PARENT_HASH_ANCHOR_AND_INDEPENDENT_MISSING_HEIGHT_AUDIT",
            "CONFIRM_WATCH_BUY_SELL_AND_RECEIPT_CAUSALITY_BEFORE_CONTROL",
            "PRESPECIFIED_RANDOMIZED_ROUTER_CONTROL_DENOMINATOR",
            "REVIEW_ADDITIONAL_READONLY_METHODS_FOR_RECEIPT_AND_L2_QUOTE",
            "NO_60_300_900_QUOTE_OR_PROFIT_CLAIM_WITHOUT_ACTUAL_EVIDENCE",
        ],
    }


def evaluate_pinned_summary(raw: bytes) -> dict:
    return assess_public_fields(parse_pinned_summary(raw))


def main() -> None:
    """Print a deterministic, aggregate-only, no-network JSON decision."""
    result = evaluate_pinned_summary(SUMMARY_FILE.read_bytes())
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
