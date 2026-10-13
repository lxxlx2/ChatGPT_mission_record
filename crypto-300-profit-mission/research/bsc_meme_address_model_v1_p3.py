#!/usr/bin/env python3
"""P3 strict 30-day BSC wallet evidence overlay, offline and source-pinned.

Only frozen 19-CA ERC20 events and independently fetched original transaction
signers are considered. A signed token transaction is NEVER promoted to a
successful DEX market swap without a receipt and an attributable trading path.
This tool cannot send transactions, query keys or modify production state.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path

DIRECTORY = Path(__file__).resolve().parent
PREFIX = "crypto-300-profit-mission/research/"
SOURCES = (
    ("bsc-meme-address-model-v1-p3-recent30d-precommit-2026-10-13.json",
     "18cc2246135b381044403e09dc73eb1c0d436597"),
    ("bsc-meme-address-model-v1-p3-23wallet-19ca-transfer-census-2026-10-13.json",
     "5592cc84099adf23b4862b8addb888b5f581c661"),
    ("bsc-meme-address-model-v1-p3-original-tx-candidates-precommit-2026-10-13.json",
     "9364abfbeedb9201afa0036df849dc9c43101d4f"),
    ("bsc-meme-address-model-v1-p3-original-signer-part1-2026-10-13.json",
     "2f952533161c2145f331da345e679fb206244732"),
    ("bsc-meme-address-model-v1-p3-original-signer-part2-2026-10-13.json",
     "cf3c4ae05d35a4a5b0cb32065ae81d0f83a46216"),
)


class EvidenceError(ValueError):
    pass


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise EvidenceError(reason)


def git_blob_sha(blob: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(blob)).encode("ascii") + b"\0" + blob).hexdigest()


def load_pinned(root: Path) -> tuple[list[dict], list[dict]]:
    docs, refs = [], []
    for name, pin in SOURCES:
        blob = (root / name).read_bytes()
        sha = git_blob_sha(blob)
        require(sha == pin, f"pinned immutable P3 source changed: {name}")
        docs.append(json.loads(blob))
        refs.append({"path": PREFIX + name, "git_blob_sha": sha})
    return docs, refs


def build_overlay(docs: list[dict], refs: list[dict]) -> dict:
    require(len(docs) == len(refs) == 5, "missing source")
    frozen, census, candidates, signer1, signer2 = docs
    require(len(frozen["wallets"]) == 23 and len(set(frozen["wallets"])) == 23,
            "frozen cohort wrong")
    require(len(frozen["exact_19_CA"]) == 19, "exact CA cohort wrong")
    require(frozen["production"] == census["network"].replace("bnb-mainnet", "NO_GO")
            == candidates["production"] == signer1["production"] == signer2["production"],
            "production or chain mismatch")
    require(census["source_frozen_precommit_sha"] == refs[0]["git_blob_sha"]
            and candidates["source_census_sha"] == refs[1]["git_blob_sha"]
            and signer1["precommit_sha"] == signer2["precommit_sha"] == refs[2]["git_blob_sha"],
            "source links unpinned")
    require(census["exact_asof_UTC"] == frozen["as_of_snapshot_utc"]
            and census["exact_cutoff_block_UTC"] == frozen["exact_last30d_start_utc"],
            "30-day causal window drift")
    s = census["summary"]
    require((s["wallets"], s["fully_paginated_directions"], s["strict30d_token_transfer_events"],
             s["wallets_with_transfer_on_frozen_CA"], s["wallets_without_transfer_on_frozen_CA"])
            == (23, 46, 89, 8, 15), "incomplete/different 23-wallet transfer census")
    known = set(frozen["wallets"])
    ca_set = {t["ca"] for t in frozen["exact_19_CA"]}
    scans = {w["wallet"]: w for w in census["wallets"]}
    require(set(scans) == known and len(census["wallets"]) == 23, "missing/duplicate census wallet")
    pairs: dict[tuple[str, str], dict] = {}
    hashes: dict[str, set[str]] = defaultdict(set)
    for event in candidates["original_candidates"]:
        wallet, tx = event["wallet"], event["hash"].lower()
        require(wallet in known and len(tx) == 66 and tx.startswith("0x"), "unknown wallet/tx")
        require(bool(event["token_CAs"]) and set(event["token_CAs"]) <= ca_set, "unexpected CA")
        require(bool(event["transfer_blocks"]) and all(type(x) is int for x in event["transfer_blocks"]),
                "invalid transfer block")
        require((wallet, tx) not in pairs, "duplicate wallet|tx original")
        pairs[wallet, tx] = event
        hashes[tx].add(wallet)
    require(len(pairs) == 75 and len(hashes) == 71, "source candidate drift")

    parsed: dict[str, dict] = {}
    require(signer1["range"] == [0, 7] and signer2["range"] == [8, 15],
            "signed tx source partition drift")
    for src in (signer1, signer2):
        for record in src["records"]:
            tx = record["hash"].lower()
            require(tx in hashes and tx not in parsed, "unknown/duplicate signed transaction")
            require(set(record["wallets"]) == hashes[tx], "source signer wallet scope drift")
            require(set(record["transfer_blocks"]) ==
                    {b for w in hashes[tx] for b in pairs[w, tx]["transfer_blocks"]},
                    "source original transaction block drift")
            parsed[tx] = record
    require(len(parsed) == 16, "16-signer freeze changed")
    rows = []
    for wallet in frozen["wallets"]:
        scan = scans[wallet]
        txs = []
        for (_, tx), event in sorted(pairs.items(), key=lambda item: item[0][1]):
            if event["wallet"] != wallet:
                continue
            raw = parsed.get(tx)
            valid = (raw is not None and
                     raw["original_tx_read_state"] == "ORIGINAL_TX_PARSED" and
                     raw["full_response"] is True)
            if valid:
                require(isinstance(raw.get("from"), str) and isinstance(raw.get("block"), int),
                        "complete original signer missing")
                require(raw["block"] in event["transfer_blocks"], "original block differs from event")
            owner = raw["from"].lower() == wallet if valid else None
            txs.append({
                "hash": event["hash"], "token_CAs": event["token_CAs"],
                "transfer_blocks": event["transfer_blocks"],
                "original_tx_state": ("NOT_YET_READ" if raw is None else
                                      "PARSED" if valid else "UNREADABLE_TRUNCATED"),
                "tx_from": raw["from"].lower() if valid else None,
                "owner_signed_original": owner,
                "receipt_success": "UNRESOLVED",
                "market_swap_confirmed": False,
            })
        cnt = scan["strict30d_erc20_transfer_evidence"]
        require(sum(side["strict30d_events"] for side in scan["by_direction"]) == cnt,
                "per-wallet transfer census mismatch")
        require(len(txs) == len(set(x["hash"] for x in txs)), "double counted original tx")
        rows.append({
            "wallet": wallet, "exact19_30d_transfer_events": cnt,
            "exact19_30d_transfer_evidence_state":
                "PRESENT" if cnt > 0 else "ABSENT_IN_FROZEN_19_CA",
            "frozen_original_candidates": len(txs),
            "owner_original_reads": sum(x["owner_signed_original"] is True for x in txs),
            "third_party_original_reads": sum(x["owner_signed_original"] is False for x in txs),
            "original_unread_or_unreadable": sum(x["owner_signed_original"] is None for x in txs),
            "recent_30d_true_owner_market_swap": "UNRESOLVED",
            "not_proven_inactive": True,
            "realized_profit": "UNRESOLVED",
            "original_transactions": txs,
        })
    summary = {
        "wallets": 23, "exact_CA": 19, "transfer_queries": 46,
        "fully_paginated_queries": 46, "erc20_transfer_events": 89,
        "wallets_transfer_present": 8, "wallets_transfer_absent": 15,
        "candidate_wallet_transaction_pairs": len(pairs),
        "distinct_original_hashes": len(hashes),
        "original_hashes_read": len(parsed),
        "original_hashes_pending": len(hashes) - len(parsed),
        "confirmed_owner_original_wallet_tx_pairs": sum(w["owner_original_reads"] for w in rows),
        "confirmed_third_party_original_wallet_tx_pairs": sum(w["third_party_original_reads"] for w in rows),
        "unread_wallet_tx_pairs": sum(w["original_unread_or_unreadable"] for w in rows),
        "confirmed_owner_market_swaps": 0,
        "production": "NO_GO",
    }
    return {
        "schema": "BSC_MEME_ADDRESS_MODEL_V1_P3_23_WALLET_SIGNED_ACTIVITY_EVIDENCE_OVERLAY",
        "status": "P3_IN_PROGRESS_NOT_ACTIVE_TRADER_RANKING",
        "as_of_snapshot_UTC": frozen["as_of_snapshot_utc"],
        "strict_window_start_UTC": frozen["exact_last30d_start_utc"],
        "source_manifest": refs,
        "interpretation": ("19-CA transfer census is exhaustive for frozen 23 addresses and block window; "
                           "original TX reads do not alone establish receipt success, actual market swap, "
                           "all-token inactivity, or realized PnL"),
        "summary": summary, "wallets": rows,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Build pinned P3 BSC owner-signer evidence overlay")
    ap.add_argument("--source-dir", type=Path, default=DIRECTORY)
    ap.add_argument("--output", type=Path, required=True)
    opts = ap.parse_args()
    docs, refs = load_pinned(opts.source_dir)
    result = build_overlay(docs, refs)
    opts.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
