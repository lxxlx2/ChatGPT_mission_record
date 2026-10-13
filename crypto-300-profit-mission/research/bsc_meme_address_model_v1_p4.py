#!/usr/bin/env python3
"""P4: deterministic P2 economic vs P3 verified recent-Swap, all 23 BSC EOAs.

Research ordering only; four preliminarily repeated positive event-block
wallets are NOT certified profitable, tradable or eligible for automatic copying.
Never infer inactive from no frozen-19-CA transfer. No external calls/trading.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from bsc_meme_address_model_v1_p3 import DIRECTORY, EvidenceError, git_blob_sha, require

P = "crypto-300-profit-mission/research/"
P2_NAME = "bsc-meme-address-model-v1-p2-economic-comparison-2026-10-13.json"
P3_NAME = "bsc-meme-address-model-v1-p3-7wallet-latest-verified-swap-utc-2026-10-13.json"
P2_SHA = "94f0de2439171d173a13b5ed82560ec4bf623c9b"
P3_SHA = "b4a58cd285941a9f99dacbcad4d5a9865f75bfdb"
INTERPRETATION = ("P2 positive means historical selected native BNB account-block or mixed-quote sign, "
                  "not complete attributable realized profit. P3 positive is proven recent signed pool swap "
                  "only on frozen 19 CAs. All 23 kept; absent evidence is UNKNOWN, never no-trade. "
                  "P4 priority is research ordering, not alpha, final G3, or performance ranking.")


def load_checked(root: Path) -> tuple[dict, dict]:
    objs = []
    for name, sha in ((P2_NAME, P2_SHA), (P3_NAME, P3_SHA)):
        data = (root / name).read_bytes()
        require(git_blob_sha(data) == sha, "P2/P3 input Git SHA drift: " + name)
        objs.append(json.loads(data))
    return objs[0], objs[1]


def build_matrix(p2: dict, p3: dict) -> dict:
    require(p2["schema"] == "BSC_MEME_ADDRESS_MODEL_V1_P2_CROSS_WALLET_ECONOMIC_EVIDENCE_MATRIX",
            "unexpected P2 schema")
    require(p2["production"] == p3["production"] == "NO_GO",
            "prohibited production stage")
    require(len(p2["wallets"]) == p2["summary"]["wallets_included"] == 23
            and p2["summary"]["signed_closed_episodes_imported"] == 50
            and p2["summary"]["selected_positive_episodes"] == 32
            and p2["summary"]["selected_negative_episodes"] == 18,
            "P2 economic denominator/source changed")
    require(p3["schema"] == "BSC_MEME_P3_SEVEN_WALLETS_LATEST_STRICT_SWAP_UTC"
            and p3["wallet_count"] == len(p3["wallets"]) == 7,
            "P3 UTC owner-signed pool Swap source changed")
    active = {r["wallet"]: r for r in p3["wallets"]}
    require(len(active) == 7, "duplicate P3 wallet")
    roster = {w["wallet"] for w in p2["wallets"]}
    require(len(roster) == 23 and set(active).issubset(roster), "P3 unknown wallet")
    require(p3["window"] == {"start": "2026-09-13T08:37:36Z",
                              "end": "2026-10-13T08:37:36Z"}, "P3 window drift")
    for row in p3["wallets"]:
        require(row["original_signer_verified"] is True
                and row["original_block_verified"] is True
                and isinstance(row["hash"], str) and len(row["hash"]) == 66
                and p3["window"]["start"] <= row["block_UTC"] <=
                    p3["window"]["end"], "recent P3 proof invalid")
    wallets = []
    for w in p2["wallets"]:
        a = active.get(w["wallet"])
        recent = a is not None
        count = w["selected_positive_distinct_major_CAs_count"]
        require(type(count) is int and count >= 0 and
                w["source_episodes_imported"] ==
                w["selected_positive_episode_count"] + w["selected_negative_episode_count"] and
                w["completed_full_wallet_all_CA_PnL"] == "UNRESOLVED" and
                w["realized_profit_rank"] is None, "cannot turn curated round into final PnL")
        decision = ("PRIORITY_REPEAT_NATIVE_OR_QUOTE_POSITIVE_WITH_RECENT_SWAP_NOT_REALIZED_PROFIT"
                    if recent and count >= 2 else
                    "RECENT_SWAP_CONFIRMED_ECONOMICS_INCOMPLETE" if recent else
                    "RECENT_SIGNED_SWAP_UNRESOLVED")
        wallets.append({
            "wallet": w["wallet"], "p3_verified_recent_19CA_swap": recent,
            "p3_latest_verified_swap_UTC": a["block_UTC"] if a else None,
            "p3_latest_verified_swap_hash": a["hash"] if a else None,
            "p2_selected_closed_episodes": w["source_episodes_imported"],
            "p2_selected_positive_episodes": w["selected_positive_episode_count"],
            "p2_selected_negative_episodes": w["selected_negative_episode_count"],
            "p2_positive_distinct_major_CAs_count": count,
            "p2_positive_distinct_CAs": w["selected_positive_distinct_CAs"],
            "p2_full_wallet_PnL": w["completed_full_wallet_all_CA_PnL"],
            "p4_research_qualification": decision,
            "p4_funding_and_pool_eligibility": "UNRESOLVED",
            "p4_qualified_missed_major_opportunities": "UNRESOLVED",
            "p5_follower_1_5_15m": "UNRESOLVED",
            "profit_rank": None, "production": "NO_GO",
        })
    candidates = sum(w["p4_research_qualification"].startswith("PRIORITY_") for w in wallets)
    recent_incomplete = sum(w["p4_research_qualification"] ==
                            "RECENT_SWAP_CONFIRMED_ECONOMICS_INCOMPLETE" for w in wallets)
    unknown = sum(w["p4_research_qualification"] == "RECENT_SIGNED_SWAP_UNRESOLVED"
                  for w in wallets)
    require((candidates, recent_incomplete, unknown) == (4, 3, 16),
            "P4 evidence-derived frozen comparison changed")
    return {
        "schema": "BSC_MEME_ADDRESS_MODEL_V1_P4_P2_P3_INTERSECTION_RESEARCH_ONLY",
        "date": "2026-10-13",
        "source_manifest": [{"path": P + P2_NAME, "git_blob_sha": P2_SHA},
                            {"path": P + P3_NAME, "git_blob_sha": P3_SHA}],
        "frozen_19CA_snapshot_window": p3["window"],
        "interpretation": INTERPRETATION,
        "summary": {
            "wallets": 23, "strict19CA_30day_owner_swap_verified_wallets": 7,
            "sampled_two_plus_major_positive_with_recent_activity": candidates,
            "recent_active_but_economics_incomplete": recent_incomplete,
            "recent_swap_unknown_wallets": unknown,
            "full_2026_economic_PnL_proven_wallets": 0,
            "qualified_major_misses_proven": 0,
            "executable_follower_alpha_proven": False,
            "production": "NO_GO",
        },
        "wallets": wallets,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate read-only P4 P2/P3 matrix")
    ap.add_argument("--source-dir", type=Path, default=DIRECTORY)
    ap.add_argument("--output", required=True, type=Path)
    args = ap.parse_args()
    data = build_matrix(*load_checked(args.source_dir))
    args.output.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
