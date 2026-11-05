#!/usr/bin/env python3
"""Read-only P3 owner-signed real Meme swap witness gate for 23 frozen BSC wallets.

Exact frozen original transaction, full receipt and historical pool identities
are required. This never infers realized PnL, general activity, follower alpha
or a production signal. stdlib only, offline deterministic provenance.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from bsc_meme_address_model_v1_p3 import (
    DIRECTORY, EvidenceError, build_overlay, git_blob_sha, load_pinned, require,
)

WITNESS_FILENAME = "bsc-meme-address-model-v1-p3-a83b-tst-true-owner-swap-witness-2026-10-13.json"
WITNESS_BLOB_SHA = "3536fcfae67f387e4b01564f26c959a62c298f6c"
TOKEN = "0x86bb94ddd16efc8bc58e6b056e8df71d9e666429"
WBNB = "0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c"
SWAP_TOPIC = "0x19b47279256b2a23a1665c810c8d55a1758940ee09377d4f8d26497a3577dc83"
POOL = "0x16969fa79651bae11736f2f6576a86fe2726b42b"
OWNER = "0xa83b73f5644cde337b61da79589f10ea15548811"
TX = "0xcfcc99e6a8d6900fa805cf5b8da72761e9d175455914772ebf394778d9d8aed4"


def load_witness(root: Path) -> dict:
    blob = (root / WITNESS_FILENAME).read_bytes()
    require(git_blob_sha(blob) == WITNESS_BLOB_SHA, "witness Git blob drift")
    return json.loads(blob)


def promote_verified_witness(overlay: dict, witness: dict) -> dict:
    """Upgrade a *single* full-receipt swap while all unrelated rows stay UNKNOWN."""
    require(overlay["schema"] == "BSC_MEME_ADDRESS_MODEL_V1_P3_23_WALLET_SIGNED_ACTIVITY_EVIDENCE_OVERLAY",
            "wrong source model schema")
    summary = overlay["summary"]
    require(overlay["status"] == "P3_IN_PROGRESS_NOT_ACTIVE_TRADER_RANKING"
            and summary["wallets"] == 23 and summary["exact_CA"] == 19
            and summary["original_hashes_read"] == 71 and summary["original_hashes_pending"] == 0
            and summary["confirmed_owner_market_swaps"] == 0
            and summary["production"] == "NO_GO", "full-source owner-signer census missing")
    require(witness["schema"] == "BSC_MEME_ADDRESS_MODEL_V1_P3_FULL_RECEIPT_POOL_SWAP_OWNER_EVIDENCE"
            and witness["network"] == "bnb-mainnet", "unexpected witness schema or network")
    tx, rc, pool = witness["tx"], witness["receipt"], witness["pool"]
    token, quote, swap = witness["token_transfer"], witness["quote_transfer"], witness["swap_event"]
    gate = witness["gate"]
    require(tx["hash"] == TX and tx["from"] == OWNER and tx["block_number"] == int(tx["block_hex"], 16)
            and pool["at_block"] == tx["block_hex"], "transaction hash/owner/block not corroborated")
    require(witness["frozen_window_UTC"]["start"] == overlay["strict_window_start_UTC"]
            and witness["frozen_window_UTC"]["end"] == overlay["as_of_snapshot_UTC"]
            and overlay["strict_window_start_UTC"] <= tx["block_UTC"] <= overlay["as_of_snapshot_UTC"],
            "outside frozen time range")
    require(rc["status"] == "0x1" and rc["complete_body"] is True
            and type(rc["log_count"]) is int and rc["log_count"] >= 3
            and int(rc["gas_used_units"]) > 0
            and int(rc["effective_gas_price_wei"]) > 0,
            "original receipt success/full-body/gas missing")
    require(pool["address"] == POOL and pool["token0"] == TOKEN
            and pool["token1"] == WBNB and pool["fee_pips"] == 10000 and pool["fee_fraction"] == "10000/1000000"
            and pool["swap_topic0"] == SWAP_TOPIC, "historical BNB pool identity changed")
    require(token["contract"] == TOKEN and token["from"] == OWNER and token["to"] == POOL
            and quote["contract"] == WBNB and quote["from"] == POOL
            and quote["to"] == tx["to"], "no exact owner token into pool / pool quote to router")
    require(type(token["log_index"]) is int and type(quote["log_index"]) is int
            and type(swap["log_index"]) is int and
            len({token["log_index"], quote["log_index"], swap["log_index"]}) == 3
            and max(token["log_index"], quote["log_index"]) < swap["log_index"],
            "missing unique ordered logs before pool swap")
    require(swap["contract"] == POOL and swap["topic0"] == SWAP_TOPIC
            and isinstance(swap["raw_data"], str) and swap["raw_data"].startswith("0x")
            and len(swap["raw_data"]) >= 2 + 64 * 5, "missing pool swap proof")
    require(int(token["raw_value_base10"]) > 0 and int(quote["raw_value_base10"]) > 0,
            "invalid nonpositive swap amounts")
    require(gate["owner_signed_success_and_token_sell_to_swap_pool"] is True
            and gate["actual_30d_owner_meme_market_swap"] is True
            and gate["quote_received_by_original_wallet"] == "UNVERIFIED"
            and gate["complete_realized_profit"] == gate["follower_executability"] == "UNRESOLVED"
            and gate["production"] == "NO_GO", "trading/PnL claim overreach")
    rows = overlay["wallets"]
    require(len(rows) == 23 and len({r["wallet"] for r in rows}) == 23, "invalid 23-wallet overlay")
    owner_row = next((r for r in rows if r["wallet"] == OWNER), None)
    require(owner_row is not None and owner_row["exact19_30d_transfer_events"] > 0,
            "unfrozen owner or no exact19 transfer")
    original = next((t for t in owner_row["original_transactions"] if t["hash"] == TX), None)
    require(original is not None and original["owner_signed_original"] is True
            and original["tx_from"] == OWNER and tx["block_number"] in original["transfer_blocks"]
            and TOKEN in original["token_CAs"], "witness does not match pinned signed original")
    require(all(r["recent_30d_true_owner_market_swap"] == "UNRESOLVED"
                and r["realized_profit"] == "UNRESOLVED" for r in rows),
            "prior unreviewed active/profit flags present")
    result = {
        "schema": "BSC_MEME_ADDRESS_MODEL_V1_P3_CONFIRMED_OWNER_SWAP_OVERLAY",
        "status": "P3_PARTIAL_ONE_VERIFIED_SWAP_OTHER_TRADES_UNRESOLVED",
        "as_of_snapshot_UTC": overlay["as_of_snapshot_UTC"],
        "strict_window_start_UTC": overlay["strict_window_start_UTC"],
        "source_manifest": overlay["source_manifest"] + [{
            "path": "crypto-300-profit-mission/research/" + WITNESS_FILENAME,
            "git_blob_sha": WITNESS_BLOB_SHA,
        }],
        "summary": {
            "wallets": 23,
            "frozen_CAs": 19,
            "original_hashes_read": 71,
            "confirmed_owner_original_wallet_tx_pairs": 38,
            "wallets_with_verified_recent_true_swap": 1,
            "verified_recent_true_swap_witnesses": 1,
            "remaining_owner_original_pairs_without_full_swap_evidence": 37,
            "wallets_unknown_recent_true_swap": 22,
            "realized_PnL_rank_available": False,
            "followable_alpha_proven": False,
            "production": "NO_GO",
        },
        "wallets": [],
    }
    for row in rows:
        active = row["wallet"] == OWNER
        result["wallets"].append({
            "wallet": row["wallet"],
            "frozen_19_CA_transfer_events": row["exact19_30d_transfer_events"],
            "owner_original_tx_pairs": row["owner_original_reads"],
            "recent_true_owner_meme_swap_state":
                "VERIFIED_ACTIVE_ON_FROZEN_19_CA" if active else "UNRESOLVED",
            "latest_verified_true_swap_UTC": tx["block_UTC"] if active else None,
            "latest_verified_true_swap_hash": TX if active else None,
            "recent_30d_all_Meme_activity_state": "UNRESOLVED",
            "realized_PnL": "UNRESOLVED",
            "follower_executability": "UNRESOLVED",
            "production": "NO_GO",
        })
    return result


def main() -> None:
    ap = argparse.ArgumentParser(description="Verify one P3 true Meme signed swap witness")
    ap.add_argument("--source-dir", type=Path, default=DIRECTORY)
    ap.add_argument("--output", type=Path, required=True)
    opts = ap.parse_args()
    docs, refs = load_pinned(opts.source_dir, include_full=True)
    result = promote_verified_witness(build_overlay(docs, refs), load_witness(opts.source_dir))
    opts.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
