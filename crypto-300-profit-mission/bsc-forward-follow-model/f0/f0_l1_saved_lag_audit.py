#!/usr/bin/env python3
"""Offline only: recompute first 60-block archive quality from LOCAL raw bytes.

No network, RPC, chain lookup, request sender, retries, or write to originals.
Block timestamp comparison is NOT public first-seen or a measured network RTT.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import statistics

from f0_l1_preflight import official_router_addresses
from f0_l1_window import (load_frozen_cohort, cohort_watchlist,
                          FROZEN_ROUTER_REGISTRY_BLOB, git_blob_sha1)
from f0_rpc_adapter import block_candidates, address

SCHEMA = "bsc-f0-first-short60-offline-private-replay-diagnostics-v1"


def fail(condition, code):
    if not condition:
        raise ValueError(code)


def utc(text):
    fail(type(text) is str and text.endswith("Z"), "INVALID_JOURNAL_UTC")
    dt = datetime.fromisoformat(text[:-1] + "+00:00")
    fail(dt.utcoffset().total_seconds() == 0, "INVALID_JOURNAL_UTC")
    return dt


def quantity(hex_value):
    fail(type(hex_value) is str and hex_value.startswith("0x") and
         len(hex_value) > 2 and all(c in "0123456789abcdefABCDEF" for c in hex_value[2:]),
         "INVALID_SAVED_QUANTITY")
    return int(hex_value, 16)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def replay_saved(journal_bytes: bytes, raw_dir: Path,
                 manifest_bytes: bytes, registry_bytes: bytes) -> dict:
    """All inputs local and immutable; outputs sanitized aggregate only."""
    journal = json.loads(journal_bytes)
    fail(isinstance(journal, dict) and journal.get("schema") ==
         "bsc-f0-l1-short-http-single-use-v1", "WRONG_JOURNAL_SCHEMA")
    rows = journal.get("attempts")
    fail(isinstance(rows, list) and len(rows) == 62 and
         journal.get("attempted_calls") == 62, "EXPECTED_EXACTLY_62_ROWS")
    cohort = load_frozen_cohort(manifest_bytes)
    watched, _ = cohort_watchlist(cohort)
    fail(git_blob_sha1(registry_bytes) == FROZEN_ROUTER_REGISTRY_BLOB,
         "FROZEN_ROUTER_REGISTRY_REQUIRED")
    routers = set(official_router_addresses(json.loads(registry_bytes)))
    fail(len(watched) == 20 and len(routers) == 2, "FROZEN_COHORT_ROUTER_COUNT")
    fail(raw_dir.is_dir() and not raw_dir.is_symlink(), "RAW_DIR_NOT_FOUND")

    heights = []
    timestamps = []
    receipts = []
    per_block_elapsed = []
    local_ages_ms = []
    watched_n = router_n = tx_count = 0
    selectors = Counter()
    prior_hash = None
    verified_parent_links = 0
    observed_head = None
    all_requests = []

    for number, item in enumerate(rows, start=1):
        fail(item.get("index") == number and
             item.get("state") == "RPC_RESPONSE" and
             isinstance(item.get("params"), list), "JOURNAL_SEQUENCE_OR_OUTCOME_INVALID")
        method = item.get("method")
        expected_method = ("eth_chainId" if number == 1 else
                           "eth_blockNumber" if number == 2 else "eth_getBlockByNumber")
        fail(method == expected_method, "JOURNAL_METHOD_SEQUENCE_INVALID")
        if number <= 2:
            fail(item["params"] == [], "INVALID_IDENTITY_PARAMS")
        else:
            fail(len(item["params"]) == 2 and item["params"][1] is True,
                 "INVALID_FULL_BLOCK_PARAMS")
        name = item.get("local_raw_response_file")
        fail(type(name) is str and name == f"{number:03d}.response.json",
             "RAW_RESPONSE_FILENAME_MISMATCH")
        file = raw_dir / name
        fail(file.is_file() and not file.is_symlink(), "RAW_RESPONSE_MISSING")
        body = file.read_bytes()
        fail(0 < len(body) <= 2_000_000 and
             sha(body) == item.get("response_sha256"), "RAW_RESPONSE_SHA256_MISMATCH")
        rpc = json.loads(body)
        fail(type(rpc) is dict and rpc.get("jsonrpc") == "2.0" and
             type(rpc.get("id")) is int and rpc["id"] == number and
             "error" not in rpc and "result" in rpc, "INVALID_SAVED_RPC_ENVELOPE")
        req_utc, complete_utc = utc(item["requested_utc"]), utc(item["completed_utc"])
        fail(complete_utc >= req_utc, "INVALID_REQUEST_RESPONSE_CLOCK_ORDER")
        first_ns, done_ns = item.get("requested_monotonic_ns"), item.get("completed_monotonic_ns")
        fail(type(first_ns) is int and type(done_ns) is int and done_ns >= first_ns,
             "INVALID_SAVED_MONOTONIC")
        elapsed_ms = (done_ns-first_ns)/1_000_000
        all_requests.append(elapsed_ms)
        if number == 1:
            fail(quantity(rpc["result"]) == 56, "WRONG_CHAIN")
        elif number == 2:
            observed_head = quantity(rpc["result"])
            fail(observed_head > 0, "NO_OBSERVED_HEAD")
        else:
            height = quantity(item["params"][0])
            fail(height == observed_head + number - 2, "NOT_CONSECUTIVE_FUTURE_HEIGHTS")
            parsed = block_candidates(rpc, watched, routers)
            fail(parsed["block_number"] == height, "BLOCK_HEIGHT_MISMATCH")
            block = rpc["result"]
            block_hash = block["hash"].lower()
            parent_hash = block["parentHash"].lower()
            if prior_hash is not None:
                fail(parent_hash == prior_hash, "PARENT_HASH_NOT_CONTIGUOUS")
                verified_parent_links += 1
            # The first saved block's parentHash is NOT verified against the
            # initial eth_blockNumber: that RPC returned a height, not a hash.
            # Do not infer or fabricate a parent anchor from adjacent blocks.
            prior_hash = block_hash
            raw_timestamp = block.get("timestamp")
            fail(raw_timestamp is not None, "BLOCK_TIMESTAMP_MISSING")
            block_timestamp = datetime.fromtimestamp(quantity(raw_timestamp), timezone.utc)
            if timestamps:
                fail(block_timestamp >= timestamps[-1], "BLOCK_TIMESTAMPS_NOT_MONOTONIC")
            age_ms = (complete_utc - block_timestamp).total_seconds()*1000
            local_ages_ms.append(round(age_ms, 3))
            timestamps.append(block_timestamp)
            receipts.append(complete_utc)
            heights.append(height)
            per_block_elapsed.append(elapsed_ms)
            tx_count += parsed["full_block_tx_count"]
            for candidate in parsed["candidates"]:
                if candidate["group"] == "WATCHLIST":
                    watched_n += 1
                else:
                    router_n += 1
            for tx in block["transactions"]:
                if address(tx["from"]) not in watched and tx.get("to") is not None and address(tx["to"]) in routers:
                    selector = tx.get("input", "0x")
                    selectors[selector[:10].lower() if type(selector) is str and len(selector)>=10
                              else "UNKNOWN_OR_EMPTY"] += 1

    fail(len(heights) == 60 and tx_count >= router_n and
         verified_parent_links == len(heights) - 1,
         "SAVED_BLOCK_COVERAGE_INVALID")
    elapsed_local = (receipts[-1] - receipts[0]).total_seconds()
    elapsed_chain = (timestamps[-1] - timestamps[0]).total_seconds()
    result = {
        "schema": SCHEMA,
        "mode": "OFFLINE_LOCAL_ARCHIVE_ONLY",
        "network_requests_by_this_tool": 0,
        "journal_sha256": sha(journal_bytes),
        "verified_raw_responses": len(all_requests),
        "observed_head": observed_head,
        "start_height": heights[0],
        "end_height": heights[-1],
        "complete_requested_interval_blocks": len(heights),
        "consecutive_height_count": len(heights),
        "internal_parent_links_verified": verified_parent_links,
        "internal_parent_links_possible": len(heights) - 1,
        "first_saved_block_parent_anchored_to_observed_head": False,
        "observed_head_hash_available": False,
        "parentage_verification_scope": "59_INTERNAL_LINKS_ONLY_FIRST_PARENT_UNANCHORED",
        "total_full_block_transactions": tx_count,
        "watch_signer_candidate_transactions": watched_n,
        "router_address_candidate_transactions": router_n,
        "router_selectors_address_match_only": dict(sorted(selectors.items())),
        "local_span_first_to_last_block_response_s": round(elapsed_local, 3),
        "onchain_header_timestamp_span_s": round(elapsed_chain, 3),
        "local_span_minus_header_span_s": round(elapsed_local-elapsed_chain, 3),
        "lag_change_interpretation": "ONLY_TIME_SPAN_PROXY_NOT_INDEPENDENT_HEAD_LAG",
        "local_receipt_minus_header_timestamp_ms_first": local_ages_ms[0],
        "local_receipt_minus_header_timestamp_ms_last": local_ages_ms[-1],
        "local_receipt_minus_header_timestamp_ms_median": round(statistics.median(local_ages_ms),3),
        "block_response_monotonic_elapsed_ms_median": round(statistics.median(per_block_elapsed), 3),
        "block_response_monotonic_elapsed_ms_max": round(max(per_block_elapsed), 3),
        "wallet_signer_eligibility": "NOT_ESTABLISHED",
        "router_swap_causality_attested": False,
        "control_eligible": False,
        "actual_e3": False,
        "quoted_actual_count": 0,
        "provider_billed": "UNVERIFIED",
        "original_raw_bytes_changed": False,
    }
    return result


def main():
    p=argparse.ArgumentParser(description="Offline-only replay of saved real 62-call BSC F0 archive")
    p.add_argument("--journal", type=Path, required=True)
    p.add_argument("--raw-dir", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args=p.parse_args()
    fail(not args.out.exists() and args.out.resolve(strict=False) != args.journal.resolve() and
         not args.out.is_symlink(), "OUTPUT_MUST_BE_NEW_AND_SEPARATE")
    root=Path(__file__).resolve().parent
    result=replay_saved(args.journal.read_bytes(), args.raw_dir,
                        (root/"F0_COHORT_PRESELECTION.json").read_bytes(),
                        (root/"F0_ROUTER_SOURCE_CANDIDATES.json").read_bytes())
    # Never write into public repository by default; caller supplies private new path.
    flags="x"
    with args.out.open(flags, encoding="utf-8") as out:
        json.dump(result, out, sort_keys=True, indent=2)
        out.write("\n")
    print(json.dumps({k:result[k] for k in
          ("verified_raw_responses","local_span_minus_header_span_s",
           "watch_signer_candidate_transactions","router_address_candidate_transactions",
           "network_requests_by_this_tool")},sort_keys=True))


if __name__=="__main__":
    main()
