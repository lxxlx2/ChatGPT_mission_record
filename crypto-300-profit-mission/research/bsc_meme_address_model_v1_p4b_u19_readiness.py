#!/usr/bin/env python3
"""P4-B source-only all-19 public-executability readiness gate; never issues signals."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
P = "crypto-300-profit-mission/research/"
SOURCES = {
    "market": ("bsc-meme-address-model-v1-p4b-19ca-unified-early-market-buy-evidence-2026-10-14.json",
               "c42ad01e896f30262f89f7852f927fc84fb3ea18"),
    "pools": ("bsc-meme-address-model-v1-p4b-19ca-cross-venue-candidate-u-2026-10-14.json",
              "49377dad6324a1089ca1233a7db6327443d0e4e6"),
    "quotes": ("bsc-meme-address-model-v1-p4b-19ca-v2-001wbnb-router-math-quotes-2026-10-14.json",
               "1f44ed58bab1dec1b4ccdc4cc449dde90d6131e7"),
    "origin": ("bsc-meme-address-model-v1-p4b-19ca-early-launch-origin-2026-10-14.json",
               "847c83fb1e1c523ebebc152f6fddacdcf128a5b7"),
    "wallet_grid": ("bsc-meme-address-model-v1-p4b-23x19-early-opportunity-ledger-2026-10-14.json",
                    "f88ed9abfcb0f321ec31e98a029303aca48a8623"),
    "dragon_probe": ("bsc-meme-address-model-v1-p4b-lonxia-observer-nplus1-buy-sim-2026-10-16.json",
                     "2af3ed1be2ed15ce90f2233959594a177a09f1fe"),
    "dragon_sells": ("bsc-meme-address-model-v1-p4b-lonxia-3-real-market-sells-2026-10-16.json",
                     "8f6a5e87580149a66ac753902f2e74c4e30e2397"),
}

def require(ok, reason):
    if not ok:
        raise ValueError("P4B_U19_" + reason)

def load(root=ROOT):
    found = {}
    for label, (name, expected) in SOURCES.items():
        raw = (root / P / name).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
        require(actual == expected, "SOURCE_BLOB_CHANGED_" + label)
        found[label] = json.loads(raw)
    return found

def keyed(rows):
    keys = [r["exact_CA"] for r in rows]
    require(len(keys) == 19 and len(set(keys)) == 19, "CA_COUNT_OR_DUPLICATE")
    return {r["exact_CA"]: r for r in rows}

def census(s):
    market, pools, quotes, origin = (keyed(s[k]["rows"]) for k in ("market", "pools", "quotes", "origin"))
    universe = set(market)
    require(set(pools) == set(quotes) == set(origin) == universe, "CROSS_SOURCE_CA")
    grid = s["wallet_grid"]
    wallets = grid["wallets"]
    gm = grid["markets"]
    require(len(gm) == 19 and {x["ca"] for x in gm} == universe, "WALLET_GRID_CA")
    owners = [w["wallet"] for w in wallets]
    require(len(owners) == len(set(owners)) == 23, "WALLET_COUNT_OR_DUPLICATE")
    require(all(len(w["early_owner_trade_statuses"]) == 19 for w in wallets), "WALLET_GRID_CELLS")
    require(grid["summary"]["implicit_wallet_CA_cells"] == 437, "WALLET_GRID_DENOMINATOR")
    require(all(gm[i]["market_U"] == "UNRESOLVED" for i in range(19)), "GRID_U_PROMOTION")

    observed = s["dragon_probe"]
    sales = s["dragon_sells"]
    dragon_ca = "0xeccbb861c0dda7efd964010085488b69317e4444"
    require(observed["token"]["exact_CA"] == dragon_ca == sales["token"], "DRAGON_EXACT_CA")
    require(observed["gate"]["qualified_public_actionable_buy_AND_sell_U"] == "UNRESOLVED", "DRAGON_FALSE_U")
    require(observed["gate"]["follower_PnL_at_1_5_15min"] == "UNRESOLVED", "DRAGON_FALSE_FOLLOW")
    require(observed["gate"]["post_owner_historical_buy_call_probe"] == "READ_ONLY_SIMULATED_SUCCESS",
            "DRAGON_PROBE_GRADE")
    require(all(x["real_fill"] is False for x in observed["historical_pre_sell_buy_quotes"]),
            "DRAGON_SIMULATED_FILL_PROMOTED")
    require(len(sales["actual_token_market_sell_events"]) == 3, "DRAGON_LATER_SALE_COUNT")
    require(sales["gate"]["same_wallet_buy_then_sell_actual_follower_roundtrip"] == "UNRESOLVED",
            "DRAGON_LATER_SALES_PROMOTED")
    later_sales = []
    for sale in sales["actual_token_market_sell_events"]:
        tx = sale["transaction_by_hash_raw"]
        sale_event = sale["decoded_sale_event"]
        sale_log = sale["raw_sale_log"]
        transfer = sale["corresponding_token_erc20_transfer_log"]
        signer = tx["from"].lower()
        tx_hash = tx["hash"].lower()
        require(sale_event["account"].lower() == signer and
                sale_event["token"].lower() == dragon_ca and
                sale_event["tx_hash"].lower() == tx_hash and
                sale_log["transactionHash"].lower() == tx_hash and
                transfer["transactionHash"].lower() == tx_hash and
                transfer["address"].lower() == dragon_ca,
                "DRAGON_LATER_SALE_TX_OWNER_CA_MISMATCH")
        later_sales.append({"tx": tx_hash, "signer": signer,
                            "frozen_cohort": "IN_ORIGINAL_23" if signer in owners
                            else "OUTSIDE_ORIGINAL_23"})
    require(len({x["tx"] for x in later_sales}) == 3 and
            len({x["signer"] for x in later_sales}) == 3,
            "DRAGON_LATER_SALE_DUPLICATE")
    require(sum(x["frozen_cohort"] == "IN_ORIGINAL_23" for x in later_sales) == 2 and
            sum(x["frozen_cohort"] == "OUTSIDE_ORIGINAL_23" for x in later_sales) == 1,
            "DRAGON_LATER_SALE_COHORT_MEMBERSHIP")
    require(all(x["signer"] != observed["token"]["original_signed_early_buy_from"].lower()
                for x in later_sales), "DRAGON_LATER_SALE_NOT_DDAC")

    rows = []
    venue_counts = {"SAME_EARLIEST_SCOPED_V2_WBNB": 0,
                    "EARLIER_SCOPED_V3_WBNB_LATER_V2_WBNB": 0,
                    "EARLIER_SCOPED_V3_USDT_LATER_V2_WBNB": 0}
    witnesses = {"FOUR_MEME_SIGNED_EARLY_BUY": 0, "FLAP_SIGNED_EARLY_BUY": 0,
                 "EARLY_ERC20_TRANSFER_ONLY_NO_SIGNED_BUY_AUDIT": 0}
    for i, cell in enumerate(gm):
        ca = cell["ca"]
        a, b, q, o = market[ca], pools[ca], quotes[ca], origin[ca]
        require(a["token"] == b["token"] == q["token"] == o["token"] == cell["token"],
                "TOKEN_CA_MISMATCH")
        require(a["index"] == b["index"] == q["index"] == o["index"] == i,
                "INDEX_REORDER")
        require(a["actual_global_observer_market_U"] == "UNRESOLVED" and
                b["globally_first_executable_venue"] == "UNRESOLVED" and
                q["global_market_first_U"] == "UNRESOLVED" and
                o["first_global_buy_and_sell_U"] == "UNRESOLVED",
                "SOURCE_U_PROMOTED")
        require(q["historical_read_block"] > b["scoped_first_active_block"] and
                q["first_positive_reserves_block"] == b["v2_reference_block"] and
                o["first_scoped_dex_positive_block"] == b["scoped_first_active_block"] and
                o["first_observed_erc20_transfer_block"] <= b["scoped_first_active_block"],
                "CROSS_VENUE_TIME_CAUSALITY")
        require(q["quote_in_wei"] == "10000000000000000" and
                q["router_matches_pair_reserves"] is True and
                q["historical_reverse_sell"] == "UNRESOLVED" and
                q["historical_token_transfer_simulation"] == "NOT_PERFORMED",
                "MATH_QUOTE_MISREPRESENTED")
        scoped = [x for x in b["pools_scoped_first_active"]
                  if x["pool"].lower() == b["scoped_first_active_pool"].lower()]
        v2 = [x for x in b["pools_scoped_first_active"]
              if x["origin"] == "V2_WBNB_REFERENCE"]
        require(len(scoped) == 1 and
                scoped[0]["first_active_block"] == b["scoped_first_active_block"] and
                scoped[0]["protocol"] == b["scoped_first_active_protocol"] and
                scoped[0]["quote"] == b["scoped_first_active_quote"],
                "EARLIEST_SCOPED_POOL_IDENTITY")
        require(len(v2) == 1 and
                v2[0]["pool"].lower() == q["pool"].lower() and
                v2[0]["protocol"] == "V2" and v2[0]["quote"] == "WBNB" and
                q["quote_token"] == "WBNB" and
                v2[0]["first_active_block"] == q["first_positive_reserves_block"],
                "V2_MATH_QUOTE_POOL_AND_ASSET_IDENTITY")
        same_pool = b["scoped_first_active_pool"].lower() == q["pool"].lower()
        if same_pool:
            venue_grade = "SAME_EARLIEST_SCOPED_V2_WBNB"
        else:
            venue_grade = ("EARLIER_SCOPED_" + b["scoped_first_active_protocol"] +
                           "_" + b["scoped_first_active_quote"] + "_LATER_V2_WBNB")
        require(venue_grade in venue_counts, "CROSS_VENUE_PROTOCOL_OR_ASSET_UNEXPECTED")
        venue_counts[venue_grade] += 1
        typ = a["earlier_actual_signed_purchase_evidence"]
        require(typ in witnesses, "UNEXPECTED_EARLY_EVIDENCE_TYPE")
        witnesses[typ] += 1
        if typ != "EARLY_ERC20_TRANSFER_ONLY_NO_SIGNED_BUY_AUDIT":
            require(a["selected_early_buy_original_tx"] and
                    a["selected_early_buy_signer"] and a["selected_early_buy_block"] and
                    a["selected_signer_is_in_original_23"] is (a["selected_early_buy_signer"] in owners),
                    "SIGNED_BUY_OWNER_IDENTITY")
            if typ == "FOUR_MEME_SIGNED_EARLY_BUY":
                require(ca == dragon_ca and a["selected_signer_is_in_original_23"], "DRAGON_OWNER")
            else:
                require(not a["selected_signer_is_in_original_23"], "EXTERNAL_OWNER_INSERTED")
        else:
            require(a["selected_early_buy_original_tx"] is None and
                    a["selected_early_buy_signer"] is None, "TRANSFER_AS_SIGNED_BUY")
        require(a["historical_signed_roundtrip_PnL"] == "UNRESOLVED" and
                a["following_at_1_5_15min"] == "UNRESOLVED", "PREMATURE_PROFIT_OR_FOLLOW")
        rows.append({
            "index": i,
            "token": a["token"],
            "exact_CA": ca,
            "first_observed_transfer_block_NOT_U": o["first_observed_erc20_transfer_block"],
            "earliest_proven_scoped_pool_block_NOT_GLOBAL_U": b["scoped_first_active_block"],
            "earliest_scoped_pool_address": b["scoped_first_active_pool"],
            "earliest_scoped_pool_protocol": b["scoped_first_active_protocol"],
            "earliest_scoped_pool_quote": b["scoped_first_active_quote"],
            "historical_V2_quote_pool_address": q["pool"],
            "historical_V2_quote_asset": q["quote_token"],
            "source_comparison_venue_grade": venue_grade,
            "same_pool_as_earliest_scoped_market": same_pool,
            "inactive_competitor_pools_historical_unknown": b["inactive_at_reference_historical_unknown_count"],
            "historical_V2_math_quote_block_NOT_SAME_AS_EARLIEST": q["historical_read_block"],
            "historical_V2_fixed_input_wei": q["quote_in_wei"],
            "historical_V2_mid_gap_bps_NOT_REAL_SLIPPAGE": q["spot_mid_vs_router_output_gap_bps"],
            "launchpad_origin_at_probe": o["pre_dex_helper_status"],
            "signed_early_buy_witness": typ,
            "signed_early_buy_in_frozen_23": a["selected_signer_is_in_original_23"],
            "signed_early_buy_original_tx": a["selected_early_buy_original_tx"],
            "historical_later_market_sale_witness": (
                "DRAGON_THREE_LATER_SELLS_TWO_IN_COHORT_ONE_OUTSIDE"
                if ca == dragon_ca else "NOT_AUDITED_HERE"),
            "later_market_sale_signer_membership": (
                later_sales if ca == dragon_ca else []),
            "N_plus_1_historical_only_unpersisted_buy_probe":
                ("READ_ONLY_NONREVERT_NOT_REAL_FILL" if ca == dragon_ca else "NOT_AUDITED_HERE"),
            "publicly_observable_signal_timestamp": "UNRESOLVED",
            "historical_same_signal_size_buy_and_sell": "UNRESOLVED",
            "tax_gas_fees_and_capital_at_signal": "UNRESOLVED",
            "qualified_global_first_executable_U": "UNRESOLVED",
            "qualified_wallet_miss": "UNRESOLVED",
            "follower_1_5_15min_return": "UNRESOLVED",
            "research_only": True,
        })
    require(witnesses == {"FOUR_MEME_SIGNED_EARLY_BUY": 1, "FLAP_SIGNED_EARLY_BUY": 2,
                          "EARLY_ERC20_TRANSFER_ONLY_NO_SIGNED_BUY_AUDIT": 16},
            "WITNESS_DISTRIBUTION")
    require(venue_counts == {"SAME_EARLIEST_SCOPED_V2_WBNB": 7,
                             "EARLIER_SCOPED_V3_WBNB_LATER_V2_WBNB": 10,
                             "EARLIER_SCOPED_V3_USDT_LATER_V2_WBNB": 2},
            "CROSS_VENUE_DISTRIBUTION")
    recorded = grid["known_early_owner_trades"]
    require(len(recorded) == 1 and recorded[0]["CA"] == dragon_ca and
            recorded[0]["wallet"] == market[dragon_ca]["selected_early_buy_signer"] and
            recorded[0]["tx"] == market[dragon_ca]["selected_early_buy_original_tx"],
            "GRID_EARLY_OWNER_WITNESS")
    require(all(x["qualified_global_first_executable_U"] == "UNRESOLVED" for x in rows),
            "FALSE_PUBLIC_U")
    return {
        "schema": "BSC_P4B_U19_FROZEN_SOURCE_EXECUTABILITY_READINESS_V1",
        "scope": "Source-only cross-market audit, NOT new RPC or sampled executable U",
        "source_blob_pins": {name: sha for name, (_, sha) in SOURCES.items()},
        "summary": {"original_wallets": 23, "exact_CAs": 19, "wallet_CA_cells": 437,
                    "early_owner_signed_witnesses_inside_cohort": 1,
                    "early_owner_signed_witnesses_external_controls": 2,
                    "not_audited_early_signed_purchases": 16,
                    "V2_historical_math_quotes_later_than_earliest_scoped_pool": 19,
                    "cross_venue_or_same_pool_breakdown": venue_counts,
                    "Dragon_later_seller_in_original_23": 2,
                    "Dragon_later_seller_outside_original_23": 1,
                    "verified_global_public_executable_U": 0,
                    "verified_follower_lag_returns": 0,
                    "P4_B": "PARTIAL", "P5": "BLOCKED", "PRODUCTION": "NO_GO"},
        "rows": rows,
    }

if __name__ == "__main__":
    print(json.dumps(census(load()), ensure_ascii=False, indent=2, sort_keys=True))
