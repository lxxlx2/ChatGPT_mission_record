#!/usr/bin/env python3
"""BSC P3 frozen 37-owner-signature strict Swap proof, offline and stdlib-only.

The 37 were preselected before reading receipts. Every result is represented:
true pool Swap with readable successful receipt status, matching pool Swap with
missing receipt status, or no direct-counterparty Swap topic observed. Absence
does not establish no trade through aggregators or other contracts.
NO production, no trading, no PnL or follower claims.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from bsc_meme_address_model_v1_p3 import DIRECTORY, EvidenceError, build_overlay, git_blob_sha, load_pinned, require
from bsc_meme_address_model_v1_p3_swap import OWNER, TX, load_witness, promote_verified_witness

ROOT = "crypto-300-profit-mission/research/"
PRECOMMIT = {
    "bsc-meme-address-model-v1-p3-owner37-receipt-pool-precommit-2026-10-13.json": "9d1a95b864a631b6c8559bf65817c30e871da19e",
    "bsc-meme-address-model-v1-p3-pool11-historical-precommit-2026-10-13.json": "e252399af01896a2bfcb05e3a2be73b53c8a8d43",
    "bsc-meme-address-model-v1-p3-missing14-standard-v3-precommit-2026-10-13.json": "66f5d8b7f398bc7928ee6d9b0576d26d939a932a",
}
SHARDS = {
    "receipt": ["f3d77f0c298c059d5b32a478fc5b0776a9f9bcfd",
                "02e45030d7d2179640dcbd7ed7c9ae36fdebc866",
                "8ceeb0f06f506e9d8acf51fb0426cc865df7456b",
                "fac3b417a999b18b56e444fd1b24e6f1240cfbc7",
                "a0b30c0717f29989ba052905fc8ed3365303af2a",
                "7cdc28e7395c08d93d4669b5553a9ea9fbdc4006"],
    "transfer-log": ["f7f8d43e0fbe54b9e022d0d3c171e8e075d2620c",
                     "a6025d52c265900c9a9dc5db71ad2afb461c1321",
                     "9be666a859d2e2ec8137831d8de1f24c6fc23ff6",
                     "a64e16cfb129ba593f107852e0a37429d4604261",
                     "855e0f12787d2d19584689aeead0ee404b1d74a9",
                     "3960c577f0292fa70d1f65f4d19a6fa39ba39899"],
    "venue-swap-log": ["65dd14dd798e70bcac7cee4b2ae74034800406ac",
                       "4480961c6a790e4a3038414f83749067e2552db4",
                       "ebbca4ccb8dc94716a13d4f2ac1a36b36cfabcfc",
                       "d5a38a161d91660f19d4e5ec6c561ebd2d3f655a",
                       "6f2c57e22e897c1620b09effb6058fd1cc6e558f",
                       "2fd36f10c9ed8131ac7703c5208e240b68f4a3b1"],
    "pool-historical": ["dee2fd482d75e3174e6df419919908c79e5f79f2",
                        "28801e4843cc38779f78230c942fa1124fb0374a",
                        "c88af00da6f15fb0f40d760a0f0e572f74065b5a"],
    "missing14-standard-v3": ["a676c3ee11424fabc82f44b5328f522fddd54514",
                              "a43f3479feafa6805ca95a7bd01a7e967daa9e06"],
}
PREFIX = "bsc-meme-address-model-v1-p3-"
SWAP_TOPIC = frozenset({
    "0xd78ad95fa46c994b6551d0da85fc275fe613ce37657fb8d5e3d130840159d822",
    "0x19b47279256b2a23a1665c810c8d55a1758940ee09377d4f8d26497a3577dc83",
})
STANDARD_V3 = "0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67"


def load_source(root: Path, name: str, sha: str) -> dict:
    blob = (root / name).read_bytes()
    require(git_blob_sha(blob) == sha, "Git blob changed: " + name)
    return json.loads(blob)


def load_evidence(root: Path) -> tuple[dict, list[dict]]:
    sources = []
    pre = {}
    for name, sha in PRECOMMIT.items():
        pre[name] = load_source(root, name, sha)
        sources.append({"path": ROOT + name, "git_blob_sha": sha})
    rows = {}
    for kind, shas in SHARDS.items():
        rows[kind] = []
        for i, sha in enumerate(shas, 1):
            name = PREFIX + (
                "owner37-receipt-part" if kind == "receipt" else
                "owner37-transfer-log-part" if kind == "transfer-log" else
                "owner37-venue-swap-log-part" if kind == "venue-swap-log" else
                "pool11-historical-part" if kind == "pool-historical" else
                "missing14-standard-v3-part"
            ) + str(i) + "-2026-10-13.json"
            d = load_source(root, name, sha)
            require(d["part"] == i and d["production"] == "NO_GO",
                    "part or production gate changed")
            rows[kind].append(d)
            sources.append({"path": ROOT + name, "git_blob_sha": sha})
    return {"pre": pre, "rows": rows}, sources


def build_evidence(overlay: dict, evidence: dict, previous: dict, refs: list[dict]) -> dict:
    require(overlay["summary"]["original_hashes_read"] == 71
            and overlay["summary"]["confirmed_owner_original_wallet_tx_pairs"] == 38,
            "full frozen original signer census absent")
    pre, doc = evidence["pre"], evidence["rows"]
    fixed = pre[PREFIX + "owner37-receipt-pool-precommit-2026-10-13.json"]
    pool_plan = pre[PREFIX + "pool11-historical-precommit-2026-10-13.json"]
    miss_plan = pre[PREFIX + "missing14-standard-v3-precommit-2026-10-13.json"]
    require(len(fixed["candidates"]) == 37
            and fixed["summary"]["wallet_tx_to_audit"] == 37
            and fixed["already_confirmed_swap_hash"] == TX,
            "37-signature precommit drift")
    require(pool_plan["summary"] == {"observed_matching_swaps": 23, "pool_contracts": 11},
            "pool selection/denominator changed")
    require(miss_plan["summary"]["remaining_missing_swap_topic_cases"] == 14
            and miss_plan["standard_V3_Swap_event_topic"] == STANDARD_V3,
            "standard V3 completion missing")
    owner = {row["wallet"]: row for row in overlay["wallets"]}
    pooled = [x for d in doc["pool-historical"] for x in d["records"]]
    pool_by = {x["pool"]: x for x in pooled}
    require(len(pooled) == len(pool_by) == 11 and all(x["target_ca_in_pair"] for x in pooled),
            "historical pool identity incomplete")
    permitted_pool_tokens = {x["pool"]: {x["call_values"]["token0"], x["call_values"]["token1"]}
                             for x in pooled}
    for x in pooled:
        require(x["target_CA"] in permitted_pool_tokens[x["pool"]]
                and len(permitted_pool_tokens[x["pool"]]) == 2,
                "pool did not contain independently sourced target CA")
    stages = {}
    expected_ranges = [[i * 7, min(i * 7 + 6, 36)] for i in range(6)]
    for kind in ("receipt", "transfer-log", "venue-swap-log"):
        chunks = doc[kind]
        require([x["range"] for x in chunks] == expected_ranges, "37 receipt/log partition drift")
        rows = [r for d in chunks for r in d["records"]]
        require(len(rows) == 37, kind + ": wrong transaction count")
        require([(r["wallet"], r["hash"], r["block"]) for r in rows]
                == [(q["wallet"], q["hash"], q["block"]) for q in fixed["candidates"]],
                kind + ": changed original selection/order")
        require(len({r["hash"] for r in rows}) == 37, kind + ": duplicated hash")
        stages[kind] = rows
    require([d["range"] for d in doc["pool-historical"]] == [[0,3],[4,7],[8,10]],
            "pool partition changed")
    standard = [r for d in doc["missing14-standard-v3"] for r in d["records"]]
    require(len(standard) == 14 and [d["range"] for d in doc["missing14-standard-v3"]]
            == [[0,6],[7,13]], "missing14 coverage changed")
    require(set(x["hash"] for x in standard) == set(x["hash"] for x in miss_plan["queries"])
            and all(x["query_state"] == "FULL_EVENT_QUERY" and not x["matching_events"] for x in standard),
            "standard V3 exclusions unproved")

    results = []
    for i, q in enumerate(fixed["candidates"]):
        rc, tr, venue = (stages[kind][i] for kind in ("receipt", "transfer-log", "venue-swap-log"))
        row = owner.get(q["wallet"])
        original = next((x for x in row["original_transactions"] if x["hash"] == q["hash"]), None) if row else None
        require(original is not None and original["owner_signed_original"] is True
                and original["tx_from"] == q["wallet"] and original["transfer_blocks"].count(q["block"]) >= 1,
                "original self-signer and transfer block mismatch")
        require(tr["source_log_query_state"] == "FULL_EVENT_QUERY"
                and venue["query_state"] == "FULL_MATCHING_SWAP_EVENT_QUERY"
                and bool(tr["exact_tx_token_transfer_events"]),
                "partial target token or pool event query")
        require(set(t["ca"] for t in tr["exact_tx_token_transfer_events"]) <= set(q["token_cas"]),
                "unfrozen token log appeared")
        confirmed = []
        for log in venue["events"]:
            require(log["topic0"] in SWAP_TOPIC and log["pool"] in pool_by,
                    "unknown/unverified pool Swap event")
            match = [t for t in tr["exact_tx_token_transfer_events"]
                     if t["ca"] in permitted_pool_tokens[log["pool"]]
                     and (t["from"] == log["pool"] or t["to"] == log["pool"])
                     and (t["from"] == q["wallet"] or t["to"] == q["wallet"])]
            require(len(match) == 1, "Swap event not directly linked to owner token movement")
            direction = "BUY" if match[0]["to"] == q["wallet"] else "SELL"
            require(int(match[0]["raw"]) > 0, "nonpositive token movement")
            require(log["pool"] in {v["pool"] for v in pool_plan["pool_queries"]},
                    "pool absent from precommitted historic queries")
            confirmed.append({"pool": log["pool"], "token_CA": match[0]["ca"],
                              "direction": direction, "swap_topic0": log["topic0"],
                              "token_log_index": match[0]["logIndex"],
                              "pool_swap_log_index": log["log_index"]})
        require(len(confirmed) <= 1, "multi-hop/same-tx ambiguity requires separate audit")
        if confirmed and rc["status_header"] == "0x1":
            status = "VERIFIED_OWNER_SIGNED_POOL_SWAP"
        elif confirmed:
            require(rc["status_header"] is None, "non-successful receipt with Swap event")
            status = "POOL_SWAP_SEEN_RECEIPT_STATUS_UNRESOLVED"
        else:
            require(q["hash"] in {v["hash"] for v in standard},
                    "unclassified standard V3 candidate not checked")
            status = "NO_DIRECT_POOL_SWAP_SEEN_ROUTING_UNRESOLVED"
        results.append({
            "wallet": q["wallet"], "hash": q["hash"], "block": q["block"],
            "status": status, "receipt_read_state": rc["receipt_state"],
            "receipt_status_header": rc["status_header"], "matching_pool": confirmed[0] if confirmed else None,
            "realized_profit": "UNRESOLVED", "follower_execution": "UNRESOLVED",
        })
    counts = Counter(x["status"] for x in results)
    require(counts == {
        "VERIFIED_OWNER_SIGNED_POOL_SWAP": 19,
        "POOL_SWAP_SEEN_RECEIPT_STATUS_UNRESOLVED": 4,
        "NO_DIRECT_POOL_SWAP_SEEN_ROUTING_UNRESOLVED": 14,
    }, "37-transaction P3 classification drift")
    require(previous["summary"]["verified_recent_true_swap_witnesses"] == 1
            and previous["summary"]["wallets_with_verified_recent_true_swap"] == 1
            and len([x for x in results if x["hash"] == TX]) == 0,
            "prior TST duplicate or unverified")
    by_wallet = defaultdict(list)
    for x in results:
        by_wallet[x["wallet"]].append(x)
    by_wallet[OWNER].append({"wallet": OWNER, "hash": TX, "status": "VERIFIED_OWNER_SIGNED_POOL_SWAP",
                             "block": 127174819})
    wallet_rows = []
    for w in overlay["wallets"]:
        rr = by_wallet[w["wallet"]]
        valid = [r for r in rr if r["status"] == "VERIFIED_OWNER_SIGNED_POOL_SWAP"]
        wallet_rows.append({
            "wallet": w["wallet"], "original_owner_tx_count": w["owner_original_reads"],
            "verified_recent_swap_count": len(valid),
            "verified_recent_swap_last_block": max((r["block"] for r in valid), default=None),
            "recent_true_swap_state": ("VERIFIED_ACTIVE_ON_FROZEN_19_CA" if valid else "UNRESOLVED"),
            "lifetime_pnl": "UNRESOLVED", "follower_alpha": "UNRESOLVED",
        })
    wallets_active = sum(w["recent_true_swap_state"] == "VERIFIED_ACTIVE_ON_FROZEN_19_CA"
                         for w in wallet_rows)
    require(wallets_active == 7 and len(wallet_rows) == 23, "wallet recent activity count drift")
    return {
        "schema": "BSC_MEME_P3_37_OWNER_TX_STRICT_POOL_SWAP_CLASSIFICATION",
        "status": "PARTIAL_P3_FIXED_19CA_ONLY_NOT_FULL_TRADER_ACTIVITY",
        "window_start_UTC": overlay["strict_window_start_UTC"],
        "as_of_snapshot_UTC": overlay["as_of_snapshot_UTC"],
        "source_manifest": refs,
        "summary": {
            "wallets": 23, "candidate_owner_tx_excluding_prior": 37,
            "new_confirmed_owner_swap_txs": 19, "prior_confirmed_owner_swap_txs": 1,
            "total_confirmed_owner_swap_txs": 20,
            "pool_swap_seen_but_receipt_status_unverified": 4,
            "direct_pool_swap_not_found_routing_unknown": 14,
            "historical_verified_pools": 11,
            "wallets_with_confirmed_frozen_CA_recent_swap": wallets_active,
            "wallets_without_confirmed_swap_still_unknown": 23-wallets_active,
            "PnL": "UNRESOLVED", "reproducible_follow": "UNRESOLVED", "production": "NO_GO",
        },
        "wallets": wallet_rows, "candidates": results,
    }



LATEST_NAME = "bsc-meme-address-model-v1-p3-7wallet-latest-verified-swap-utc-2026-10-13.json"
LATEST_BLOB_SHA = "b4a58cd285941a9f99dacbcad4d5a9865f75bfdb"


def attach_latest_verified_swap_utc(result: dict, source: dict) -> dict:
    """Validate last-verified event block and UTC; never infer latest all-token swap."""
    require(source["schema"] == "BSC_MEME_P3_SEVEN_WALLETS_LATEST_STRICT_SWAP_UTC"
            and source["wallet_count"] == 7 and source["production"] == "NO_GO",
            "wrong latest swap timestamp source")
    require(source["window"] == {"start": result["window_start_UTC"],
                                 "end": result["as_of_snapshot_UTC"]},
            "latest timestamp window drift")
    seen = set()
    index = {w["wallet"]: w for w in result["wallets"]}
    require(len(index) == 23, "latest UTC needs full wallet census")
    for item in source["wallets"]:
        wallet, block, h = item["wallet"], item["block"], item["hash"]
        require(wallet in index and wallet not in seen, "unknown or duplicated latest wallet")
        seen.add(wallet)
        dst = index[wallet]
        require(dst["recent_true_swap_state"] == "VERIFIED_ACTIVE_ON_FROZEN_19_CA"
                and dst["verified_recent_swap_last_block"] == block
                and item["original_signer_verified"] is True
                and item["original_block_verified"] is True, "latest observed block/signer mismatch")
        time = datetime.fromtimestamp(int(item["blockTimestampHex"], 16), tz=timezone.utc)
        utc = time.isoformat(timespec="milliseconds").replace("+00:00", "Z")
        require(utc == item["block_UTC"]
                and datetime.fromisoformat(result["window_start_UTC"].replace("Z", "+00:00")) <= time <=
                datetime.fromisoformat(result["as_of_snapshot_UTC"].replace("Z", "+00:00")),
                "historical UTC/date mismatch")
        valid = (wallet == OWNER and h == TX and block == 127174819) or any(
            x["wallet"] == wallet and x["hash"] == h
            and x["block"] == block and x["status"] == "VERIFIED_OWNER_SIGNED_POOL_SWAP"
            for x in result["candidates"])
        require(valid, "latest transaction has no full pool swap and success evidence")
        dst["latest_verified_swap_hash"] = h
        dst["latest_verified_swap_UTC"] = utc
    require(len(seen) == 7 and
            {w["wallet"] for w in result["wallets"] if w["verified_recent_swap_count"] > 0} == seen,
            "missing last verified swap date for eligible wallet")
    for row in result["wallets"]:
        if row["wallet"] not in seen:
            row["latest_verified_swap_hash"] = None
            row["latest_verified_swap_UTC"] = None
    result["source_manifest"].append({
        "path": ROOT + LATEST_NAME, "git_blob_sha": LATEST_BLOB_SHA,
    })
    return result


def main() -> None:
    ap = argparse.ArgumentParser(description="Rebuild strict P3 owner-signed Swap evidence")
    ap.add_argument("--source-dir", type=Path, default=DIRECTORY)
    ap.add_argument("--output", type=Path, required=True)
    opts = ap.parse_args()
    docs, refs = load_pinned(opts.source_dir, include_full=True)
    overlay = build_overlay(docs, refs)
    prev = promote_verified_witness(overlay, load_witness(opts.source_dir))
    evidence, evidence_refs = load_evidence(opts.source_dir)
    result = build_evidence(overlay, evidence, prev, refs + evidence_refs)
    last = load_source(opts.source_dir, LATEST_NAME, LATEST_BLOB_SHA)
    result = attach_latest_verified_swap_utc(result, last)
    opts.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
