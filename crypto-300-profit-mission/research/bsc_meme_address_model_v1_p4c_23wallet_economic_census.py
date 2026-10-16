#!/usr/bin/env python3
"""Frozen 23x19 cross-wallet economic evidence census: not a profit leaderboard.

Original 50 P2 rounds are selected signed *historical* episodes, not a
random sample, lifetime history, or evidence a follower could trade them.
Use for proof coverage and research prioritization only; no real money.
"""
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PINS = {
    "scope": ("bsc-meme-address-model-v1-p4c-frozen-23wallet-economic-proof-census-scope-2026-10-17.json", "43834dbee14fae0646f2ebbfad4bac70d6ff214a"),
    "baseline": ("bsc-meme-address-model-v1-baseline-2026-10-13.json", "e3c8815630878dddc03b7a6e11b8f0d2d89cbf6a"),
    "ledger": ("bsc-meme-address-model-v1-p2-evidence-ledger-2026-10-13.json", "2a19dbd88c2971efff60a15894d952d0d05e64d9"),
    "two_major": ("BSC_MEME_STAGE23_8E6B_REPEAT_WINNER_HAJIMI_LOBSTER_IFML_CROSS_MAJOR_ROUNDS_2026-10-13.json", "6227e69fabd6c0d991add0d7ff5c6e406babd40b"),
    "adff_boundary": ("bsc-meme-address-model-v1-p4c-adff-bounded-acquisition-asset-outgoing-source-2026-10-16.json", "b921270650e00b4de190b1c396a0bbc78c89150e"),
}
GRADES = ("SIGNED_NATIVE_BLOCK_SCOPE", "SETTLED_NATIVE_DIRECT_WBNB_GAS", "MIXED_BNB_USDT_SPOT_REFERENCE")
SIGNS = ("POSITIVE_NATIVE_SCOPE", "NEGATIVE_NATIVE_SCOPE", "POSITIVE_QUOTE_MARK")
FROZEN_8E6B = "0x8e6b3c9c72ca592bbab470f761fa869c174e9ea0"
ADFF = "0xadffbebbd2d9141cff80f8a905846ba8f9e3946d"

def require(condition, message):
    if not condition:
        raise ValueError(message)

def load(root=ROOT):
    result = {}
    for kind, (name, expected) in PINS.items():
        raw = (Path(root) / name).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
        require(actual == expected, "FROZEN_SOURCE_GIT_BLOB_CHANGED:" + kind)
        result[kind] = json.loads(raw)
    return result

def census(d):
    require(set(d) == set(PINS), "MISSING_OR_EXTRA_SOURCE")
    scope, base, ledger = d["scope"], d["baseline"], d["ledger"]
    require(scope["source_approved_exact_sha"] == "b2fb255dd486a2bd6502e21dbd14eaa6ef557c2e"
            and scope["frozen_denominator"] == {"wallets":23,"exact_CA":19,"cells":437,
                                                  "transfer_present":148,"transfer_absent":289}
            and scope["expected_grades"] == {"SIGNED_NATIVE_BLOCK_SCOPE":44,
                 "SETTLED_NATIVE_DIRECT_WBNB_GAS":4, "MIXED_BNB_USDT_SPOT_REFERENCE":2},
            "FREEZE_EVIDENCE_POLICY_CHANGED")
    listed = {x["path"].split("/")[-1]: x["blob"] for x in scope["baseline_sources"]}
    require(len(listed) == 4 and all(listed[PINS[k][0]] == PINS[k][1]
            for k in ("baseline","ledger","two_major","adff_boundary")),
            "CENSUS_ORIGINAL_SOURCES_NOT_PINNED")
    require(base["input_source"]["git_blob_sha"] == ledger["frozen_source_sha"]
            and base["cohort"]["wallets"] == 23
            and base["cohort"]["exact_CAs"] == 19
            and base["cohort"]["cells"] == 437
            and base["cohort"]["ERC20_present"] == 148
            and base["cohort"]["ERC20_absent"] == 289,
            "BASELINE_23_19_437_CHANGED")

    original = base["wallets"]
    cohort_wallets = [w["wallet"].lower() for w in original]
    require(len(original) == len(set(cohort_wallets)) == 23, "FROZEN_WALLET_DUPLICATE_OR_REMOVED")
    majors = [c["ca"].lower() for c in original[0]["cells"]]
    require(len(majors) == len(set(majors)) == 19, "FROZEN_CA_DUPLICATE_OR_REMOVED")

    selected = defaultdict(list)
    known = set()
    grades = Counter()
    for x in ledger["episodes"]:
        wallet, ca = x["wallet"].lower(), x["exact_ca"].lower()
        identity = (wallet, ca, x["episode_index"])
        require(wallet in cohort_wallets and ca in majors and identity not in known,
                "FOREIGN_OR_DUPLICATE_CURATED_ROUND")
        known.add(identity)
        require(x["owner_signed_success_source_record"] is True
                and x["raw_token_round_closed"] is True
                and x["evidence_grade"] in GRADES
                and x["net_classification"] in SIGNS
                and x["is_full_wallet_PnL"] is False
                and x["is_followable_alpha"] is False
                and x["provenance"]["source_git_blob_sha"],
                "CURATED_EPISODE_NOT_SIGNED_CLOSED_OR_PROVENANCE_INVALID")
        if x["evidence_grade"] == "MIXED_BNB_USDT_SPOT_REFERENCE":
            require(x["net_classification"] == "POSITIVE_QUOTE_MARK"
                    and x["actual_USDT_delta_raw"] is not None,
                    "MIXED_QUOTE_CANNOT_BE_NATIVE_PROFIT")
        elif x["evidence_grade"] == "SETTLED_NATIVE_DIRECT_WBNB_GAS":
            require(x["net_classification"] in SIGNS[:2],
                    "SETTLEMENT_WITHOUT_NATIVE_SCOPE_DIRECTION")
        selected[(wallet, ca)].append(x)
        grades[x["evidence_grade"]] += 1
    require(len(known) == scope["historical_curated_episodes"] == 50
            and dict(grades) == scope["expected_grades"],
            "CURATED_EPISODE_GRADE_DENOMINATOR_CHANGED")

    proofs = d["two_major"]["selected_two_major_positive_receipt_proofs"]
    bound = scope["selected_2026_8e6b_cross_major_positive_proofs"]
    token_ca = {c["token"]: c["exact_ca"].lower() for c in d["two_major"]["cross_coin_summary"]}
    require(d["two_major"]["wallet"].lower() == FROZEN_8E6B
            and len(proofs) == len(bound) == 2
            and {x["ca"].lower() for x in bound} == {token_ca[p["token"]] for p in proofs}
            and {p["token"] for p in proofs} == {"哈基米 / HAJIMI", "龙虾"}
            and {(x["ca"].lower(), x["stage23_round"]) for x in bound} ==
                {(token_ca[p["token"]], p["round"]) for p in proofs},
            "TWO_MAJOR_SELECTED_RECEIPT_GAS_PROOFS_RESELECTED")
    proofcas = set()
    for p in proofs:
        ca = token_ca[p["token"]]
        require(p["settlement_reconciled_all_sells"] is True
                and p["closed_raw_token_inventory"] is True
                and p["buy_utc"].startswith("2026-")
                and p["last_sell_utc"].startswith("2026-"),
                "TWO_MAJOR_SOURCE_2026_OR_SETTLEMENT_NOT_VERIFIED")
        matched = [x for x in selected[(FROZEN_8E6B, ca)]
                   if x["first_block"] == p["buy_block"]
                   and x["last_block"] == p["last_sell_block"]
                   and x["evidence_grade"] == "SETTLED_NATIVE_DIRECT_WBNB_GAS"
                   and x["net_classification"] == "POSITIVE_NATIVE_SCOPE"]
        require(len(matched) == 1, "TWO_MAJOR_RECEIPT_PROOF_NOT_IN_ORIGINAL_CURATED_LEDGER")
        proofcas.add(ca)
    require(proofcas == {x["ca"].lower() for x in bound},
            "TWO_MAJOR_PROOF_EXACT_CA_DRIFT")
    require(d["adff_boundary"]["original_owner"] == ADFF
            and d["adff_boundary"]["original_acquisition_payment_source"].startswith("UNRESOLVED")
            and d["adff_boundary"]["original_owner_realized_pnl"] == "UNRESOLVED"
            and d["adff_boundary"]["P5"] == "BLOCKED"
            and d["adff_boundary"]["PRODUCTION"] == "NO_GO",
            "ADFF_PAYMENT_BASIS_UNRESOLVED")
    # No dynamic winner score, and no current wallet activity inference.
    rows = []
    counted = Counter()
    for w in original:
        owner = w["wallet"].lower()
        cells = []
        wc = Counter()
        for c in w["cells"]:
            ca = c["ca"].lower()
            require(c["wallet"].lower() == owner and ca in majors
                    and c["ERC20_presence"] in ("PRESENT", "ABSENT_IN_FROZEN_CA")
                    and c["realized_cashflow_and_profit"] == "UNRESOLVED",
                    "P1_TRANSFER_NOT_REALIZED_PNL")
            rounds = selected.get((owner, ca), [])
            gc = Counter(x["evidence_grade"] for x in rounds)
            positive = sum(x["net_classification"] == "POSITIVE_NATIVE_SCOPE" for x in rounds)
            negative = sum(x["net_classification"] == "NEGATIVE_NATIVE_SCOPE" for x in rounds)
            mixed = sum(x["net_classification"] == "POSITIVE_QUOTE_MARK" for x in rounds)
            wc["selected_episodes"] += len(rounds)
            wc["native_positive"] += positive
            wc["native_negative"] += negative
            wc["mixed_quote_reference"] += mixed
            counted[c["ERC20_presence"]] += 1
            cells.append({
                "ca":ca,"token":c["token"],"frozen_erc20_presence":c["ERC20_presence"],
                "original_selected_episode_count":len(rounds),
                "selected_native_block_positive":positive,
                "selected_native_block_negative":negative,
                "selected_mixed_quote_reference":mixed,
                "selected_receipt_gas_scope_count":gc["SETTLED_NATIVE_DIRECT_WBNB_GAS"],
                "selected_2026_positive_receipt_gas_major_witness":owner == FROZEN_8E6B and ca in proofcas,
                "economic_evidence_state":(
                    "SELECTED_WBNB_GAS_SCOPE_NOT_LIFETIME_PNL" if gc["SETTLED_NATIVE_DIRECT_WBNB_GAS"]
                    else "SELECTED_MIXED_QUOTE_REFERENCE_NOT_PNL" if mixed
                    else "SELECTED_NATIVE_BLOCK_SCOPE_NOT_PNL" if rounds
                    else "NO_CURATED_ROUND_DOES_NOT_MEAN_NO_TRADE_OR_LOSS"),
                "owner_true_all_asset_net_profit":"UNRESOLVED",
                "observer_first_public_executable_U":"UNRESOLVED",
            })
        require(len(cells) == 19 and {x["ca"] for x in cells} == set(majors),
                "ORIGINAL_WALLET_19_CA_GRID_TRUNCATED")
        rows.append({
            "wallet":owner,"frozen_erc20_present":w["all_19_erc20_present"],
            "frozen_erc20_absent":w["all_19_erc20_absent"],
            "curated_original_signed_closed_episodes":wc["selected_episodes"],
            "curated_native_block_positive":wc["native_positive"],
            "curated_native_block_negative":wc["native_negative"],
            "curated_mixed_quote_reference":wc["mixed_quote_reference"],
            "2026_two_distinct_major_selected_positive_gas_witness":
                owner == FROZEN_8E6B and len(proofcas) == 2,
            "wallet_full_history_realized_PnL":"UNRESOLVED",
            "recent_true_signed_swap":"UNRESOLVED_UNLESS_SEPARATE_P3_SOURCE_GRADE",
            "profit_rank":None,"buy_signal":"NONE_RESEARCH_ONLY",
            "cells":cells,
        })
    require(len(rows) == 23 and sum(len(w["cells"]) for w in rows) == 437
            and counted["PRESENT"] == 148 and counted["ABSENT_IN_FROZEN_CA"] == 289
            and sum(r["curated_original_signed_closed_episodes"] for r in rows) == 50
            and sum(r["curated_native_block_positive"] for r in rows) == 31
            and sum(r["curated_native_block_negative"] for r in rows) == 17
            and sum(r["curated_mixed_quote_reference"] for r in rows) == 2,
            "CENSUS_437_ORIGINAL_ECONOMIC_SOURCE_DENOMINATOR_CHANGED")
    require(sum(r["curated_original_signed_closed_episodes"] > 0 for r in rows) == 7
            and sum(r["curated_original_signed_closed_episodes"] == 0 for r in rows) == 16
            and sum(r["2026_two_distinct_major_selected_positive_gas_witness"] for r in rows) == 1,
            "SELECTED_SOURCE_UNEVEN_WALLET_COVERAGE_NOT_PRESERVED")
    return {
        "schema":"BSC_P4C_23x19_ECONOMIC_SOURCE_EVIDENCE_CENSUS_NOT_PERFORMANCE_MODEL_V1",
        "scope_approved_prior_sha":scope["source_approved_exact_sha"],
        "frozen_wallets":23,"frozen_exact_CAs":19,"frozen_cells":437,
        "ERC20_present":148,"ERC20_absent":289,
        "curated_signed_closed_episodes":50,"curated_wallets":7,
        "other_wallets_without_selected_rounds_not_losses":16,
        "curated_native_scope_positive_not_realized_PnL":30,
        "curated_native_scope_negative_not_realized_PnL":18,
        "curated_mixed_quote_references_not_native_PnL":2,
        "curated_gas_WBNB_partial_settlement_grade":4,
        "selected_2026_two_major_positive_receipt_gas_case":"8E6B_ONLY_SELECTED_SOURCE_NOT_STATISTICAL_WINNER",
        "full_wallet_economic_profitable_ranks":0,
        "ranking_state":"PROHIBITED_NO_ALL_ASSET_ATTRIBUTABLE_COMPARABLE_PNL",
        "U":"UNRESOLVED","P4_B":"PARTIAL","P4_C":"PARTIAL","P5":"BLOCKED",
        "PRODUCTION":"NO_GO","NO_MERGE":True,"NO_DEPLOY":True,
        "NO_GMAIL":True,"NO_TRADE":True,
        "wallets":rows,
    }

if __name__ == "__main__":
    print(json.dumps(census(load()),ensure_ascii=False,indent=2))
