#!/usr/bin/env python3
"""P2 BSC address model: provenance-bound cross-wallet economic evidence overlay.

Offline, stdlib only, no paid GMGN or network, zero trading/monitor operations.
It imports selected prior completed episodes; never claims complete wallet PnL.
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

ALLOWED_GRADES = frozenset({
    "SETTLED_NATIVE_DIRECT_WBNB_GAS",
    "SIGNED_NATIVE_BLOCK_SCOPE",
    "MIXED_BNB_USDT_SPOT_REFERENCE",
})
ALLOWED_NATIVE_SIGNS = frozenset({"POSITIVE_NATIVE_SCOPE", "NEGATIVE_NATIVE_SCOPE"})
ALLOWED_MARK_SIGNS = frozenset({"POSITIVE_QUOTE_MARK", "NEGATIVE_QUOTE_MARK", "ZERO_QUOTE_MARK"})


class EvidenceError(ValueError):
    pass


def ensure(ok: bool, reason: str) -> None:
    if not ok:
        raise EvidenceError(reason)


def as_int(value: object, field: str) -> int:
    ensure(isinstance(value, str) and value.lstrip("-").isdigit(), field + ": invalid integer wei")
    return int(value)


def build_economic_comparison(baseline: dict, ledger: dict) -> dict:
    ensure(baseline.get("schema") == "BSC_MEME_ADDRESS_MODEL_V1_P1_CROSS_WALLET_TRANSFER_EVIDENCE_BASELINE",
           "wrong P1 baseline schema")
    ensure(ledger.get("schema") == "BSC_MEME_ADDRESS_MODEL_V1_P2_PROVENANCE_EPISODES_V1",
           "wrong P2 evidence schema")
    ensure(baseline.get("production") == ledger.get("production") == "NO_GO", "production gate violated")
    ensure(ledger.get("frozen_source_sha") == baseline["input_source"]["git_blob_sha"],
           "P1 frozen input sha mismatch")
    wallets = baseline.get("wallets", [])
    ensure(len(wallets) == 23 and baseline["cohort"]["cells"] == 437, "not full frozen cohort")
    by_wallet = {w["wallet"]: w for w in wallets}
    ensure(len(by_wallet) == 23, "duplicate baseline wallet")
    refs = {s["path"]: s["blob_sha"] for s in ledger.get("source_manifest", [])}
    ensure(len(refs) == len(ledger.get("source_manifest", [])), "duplicate source manifest path")

    episodes = ledger.get("episodes")
    ensure(isinstance(episodes, list), "no episodes")
    indexed = defaultdict(list)
    keys = set()
    grades = defaultdict(int)
    for event in episodes:
        owner = event.get("wallet")
        ensure(owner in by_wallet, "signed episode belongs to non-frozen wallet")
        ca = event.get("exact_ca")
        token = event.get("token")
        found = next((cell for cell in by_wallet[owner]["cells"]
                      if cell["ca"] == ca and cell["token"] == token), None)
        ensure(found is not None and found["ERC20_presence"] == "PRESENT",
               "signed event has missing/absent exact CA in P1")
        ensure(event.get("raw_token_round_closed") is True and
               event.get("owner_signed_success_source_record") is True,
               "uncorroborated source event marked complete")
        ensure(event.get("is_full_wallet_PnL") is False and
               event.get("is_followable_alpha") is False, "improper PnL or follower claim")
        grade = event.get("evidence_grade")
        ensure(grade in ALLOWED_GRADES, "unknown proof grade")
        eidx = event.get("episode_index")
        ensure(type(eidx) is int and eidx >= 1, "invalid original round index")
        key = (owner, ca, eidx)
        ensure(key not in keys, "double-counted signed wallet/CA/round")
        keys.add(key)
        begin, end = event.get("first_block"), event.get("last_block")
        ensure((begin is None and end is None) or
               (type(begin) is int and type(end) is int and 0 <= begin <= end),
               "partial or inverted block interval")
        src = event.get("provenance", {})
        ensure(isinstance(src, dict) and refs.get(src.get("source_path")) ==
               src.get("source_git_blob_sha"), "source Git SHA not present in manifest")
        bnb = as_int(event.get("net_native_BNB_wallet_event_blocks_wei"), "net native BNB")
        ensure(bnb != 0, "zero native scope needs manual review; not silently positive")
        usdt = event.get("actual_USDT_delta_raw")
        mark = event.get("mark_USDT_equivalent_spot_reference_raw")
        sign = event.get("net_classification")
        if grade == "MIXED_BNB_USDT_SPOT_REFERENCE":
            as_int(usdt, "actual USDT delta")
            ensure(mark is not None, "mixed units require pre-existing historical quote reference")
            quote = as_int(mark, "historical quote mark")
            ensure(sign == ("POSITIVE_QUOTE_MARK" if quote > 0 else
                            "NEGATIVE_QUOTE_MARK" if quote < 0 else "ZERO_QUOTE_MARK"),
                   "mixed quote sign not supported by archived mark")
            ensure(event.get("asset_settlement_mode") == "MIXED_BNB_USDT_WITH_HISTORICAL_SPOT_ESTIMATE",
                   "wrong mixed quote grade")
        else:
            ensure(usdt is None and mark is None and
                   event.get("actual_USDT_leg_state") == "UNVERIFIED_NO_NON_NATIVE_ASSET_CLAIM",
                   "unproven native-only USDT must remain NULL")
            ensure(sign == ("POSITIVE_NATIVE_SCOPE" if bnb > 0 else "NEGATIVE_NATIVE_SCOPE"),
                   "wrong native episode sign")
            ensure(event.get("asset_settlement_mode") == "NATIVE_BNB_ACCOUNT_BLOCK_SCOPE",
                   "native-only route mislabeled as mixed")
        grades[grade] += 1
        indexed[owner].append(event)

    output = []
    for original in wallets:
        owner = original["wallet"]
        selected = indexed[owner]
        positives = [e for e in selected if e["net_classification"].startswith("POSITIVE")]
        negatives = [e for e in selected if e["net_classification"].startswith("NEGATIVE")]
        positive_cas = sorted({e["exact_ca"] for e in positives})
        negative_cas = sorted({e["exact_ca"] for e in negatives})
        native = [e for e in selected if e["evidence_grade"] != "MIXED_BNB_USDT_SPOT_REFERENCE"]
        marked = [e for e in selected if e["evidence_grade"] == "MIXED_BNB_USDT_SPOT_REFERENCE"]
        native_net = sum(as_int(e["net_native_BNB_wallet_event_blocks_wei"], "BNB") for e in native)
        native_win = [as_int(e["net_native_BNB_wallet_event_blocks_wei"], "BNB")
                      for e in native if as_int(e["net_native_BNB_wallet_event_blocks_wei"], "BNB") > 0]
        sum_native_pos = sum(native_win)
        max_win = max(native_win, default=None)
        without_max = native_net - max_win if max_win is not None else None
        # This explicitly measures concentration within the *covered native-BNB
        # evidence subset*, NOT total wallet risk-adjusted performance.
        result = {
            "wallet": owner,
            "research_priority_in_P1": original["investigation_order_only"],
            "major_2026_transfer_present_count": original["priority_2026_major_transfer_present_count"],
            "all_19_transfer_present_count": original["all_19_erc20_present"],
            "source_episodes_imported": len(selected),
            "source_distinct_CAs_imported": len({e["exact_ca"] for e in selected}),
            "selected_positive_episode_count": len(positives),
            "selected_negative_episode_count": len(negatives),
            "selected_positive_distinct_CAs": positive_cas,
            "selected_negative_distinct_CAs": negative_cas,
            "selected_positive_distinct_major_CAs_count": len(positive_cas),
            "native_only_source_episodes": len(native),
            "mixed_source_episodes": len(marked),
            "native_only_event_block_scope_sum_wei": str(native_net) if native else None,
            "native_only_positive_gross_wei": str(sum_native_pos) if native else None,
            "native_only_largest_positive_episode_wei": str(max_win) if max_win is not None else None,
            "native_only_scope_excluding_largest_positive_wei": (
                str(without_max) if without_max is not None else None
            ),
            "native_only_biggest_win_fraction_of_positive_gross": (
                round(max_win / sum_native_pos, 6) if max_win is not None else None
            ),
            "mixed_quote_actual_USDT_delta_sum_raw": (
                str(sum(as_int(e["actual_USDT_delta_raw"], "USDT") for e in marked))
                if marked else None
            ),
            "mixed_quote_actual_BNB_delta_sum_wei": (
                str(sum(as_int(e["net_native_BNB_wallet_event_blocks_wei"], "BNB")
                        for e in marked)) if marked else None
            ),
            "mixed_quote_historical_spot_reference_sum_raw": (
                str(sum(as_int(e["mark_USDT_equivalent_spot_reference_raw"], "MARK")
                        for e in marked)) if marked else None
            ),
            "economic_evidence_grade": (
                "SOME_CURATED_CLOSED_ROUNDS_NOT_FULL_WALLET"
                if selected else "NO_CURATED_P2_EPISODES_NOT_ZERO_PROFIT"
            ),
            "completed_full_wallet_all_CA_PnL": "UNRESOLVED",
            "realized_profit_rank": None,
            "can_rank_by_profit": False,
            "recent_30d_signed_meme_swap": "UNRESOLVED",
            "followable_alpha_approved": False,
            "source_refs": sorted(set(e["provenance"]["source_path"] for e in selected)),
            "source_rounds": [
                {"token": e["token"], "episode_index": e["episode_index"],
                 "first_block": e["first_block"], "last_block": e["last_block"],
                 "evidence_grade": e["evidence_grade"], "classification": e["net_classification"],
                 "source": e["provenance"]["source_path"]}
                for e in sorted(selected, key=lambda e: (e["token"], e["episode_index"]))
            ],
        }
        output.append(result)

    ensure(len(output) == 23, "not all frozen 23 wallets represented")
    ensure(sum(w["source_episodes_imported"] for w in output) == len(episodes),
           "P2 output lost signed episodes")
    return {
        "schema": "BSC_MEME_ADDRESS_MODEL_V1_P2_CROSS_WALLET_ECONOMIC_EVIDENCE_MATRIX",
        "as_of": "2026-10-13",
        "production": "NO_GO",
        "authority": "PARTIAL_CURATED_EVIDENCE_ONLY_NOT_GLOBAL_WALLET_PNL",
        "inputs": {
            "p1_frozen_source_git_blob_sha": baseline["input_source"]["git_blob_sha"],
            "p2_evidence_schema": ledger["schema"],
            "p2_source_manifest": ledger["source_manifest"],
        },
        "summary": {
            "wallets_included": 23,
            "signed_closed_episodes_imported": len(episodes),
            "wallets_with_curated_evidence": sum(bool(w["source_episodes_imported"]) for w in output),
            "wallets_not_yet_economically_curated": sum(not w["source_episodes_imported"] for w in output),
            "selected_positive_episodes": sum(w["selected_positive_episode_count"] for w in output),
            "selected_negative_episodes": sum(w["selected_negative_episode_count"] for w in output),
            "evidence_by_grade": dict(sorted(grades.items())),
            "all_23_comparable_full_PnL_ready": False,
            "any_ranked_wallet": False,
        },
        "ranking_safety": {
            "wallet_order_remains_P1_RESEARCH_PRIORITY_NOT_PROFIT_RANK": True,
            "incomparable_selective_coverage_must_not_determine_winner": True,
            "unreviewed_native_delta_cannot_be_traded": True,
            "simulated_spot_price_is_not_real_USDT_conversion": True,
            "unknown_19_wallets_not_assigned_zero_profit": True,
            "all_recent_active_unknown_without_P3": True,
        },
        "wallets": output,
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--baseline", type=Path, required=True)
    p.add_argument("--ledger", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    for incoming in (args.baseline, args.ledger):
        ensure(args.output.resolve() != incoming.resolve(), "output would overwrite immutable source")
    result = build_economic_comparison(
        json.loads(args.baseline.read_text(encoding="utf-8")),
        json.loads(args.ledger.read_text(encoding="utf-8")),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    print(json.dumps({"status": "PASS_PARTIAL_ECONOMIC_CENSUS",
                      **result["summary"], "production": "NO_GO"},
                     ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
