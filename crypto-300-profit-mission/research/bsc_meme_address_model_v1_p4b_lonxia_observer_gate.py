#!/usr/bin/env python3
"""Pinned, offline evidence classification for the 2026 DDAC/龙虾 observer U case.

Source replay only. No RPC, no onchain execution, no signals or real PnL.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PINS = (
    ("bsc-meme-address-model-v1-p4b-lonxia-observer-nplus1-buy-sim-2026-10-16.json",
     "2af3ed1be2ed15ce90f2233959594a177a09f1fe"),
    ("bsc-meme-address-model-v1-p4b-lonxia-3-real-market-sells-2026-10-16.json",
     "8f6a5e87580149a66ac753902f2e74c4e30e2397"),
    ("bsc-meme-address-model-v1-p4b-lonxia-independent-review-errata-2026-10-16.json",
     "41ce4ea1f2661f0c12ce804e4a2cda828f15639d"),
)
TOKEN = "0xeccbb861c0dda7efd964010085488b69317e4444"
MANAGER = "0x5c952063c7fc8610ffdb798152d69f0b9550762b"
OWNER = "0xddac928a240bdace3994c2cc0783d4e29a002127"
TOPIC_SALE = "0x0a5575b3648bae2210cee56bf33254cc1ddfbc7bf637c0af2ac18b14fb1bae19"
TOPIC_TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"

def require(ok, label):
    if not ok:
        raise ValueError(label)

def load(root=ROOT):
    docs = []
    for filename, blob in PINS:
        raw = (root / filename).read_bytes()
        digest = hashlib.sha1(
            b"blob " + str(len(raw)).encode() + bytes((0,)) + raw
        ).hexdigest()
        require(digest == blob, "pinned evidence drift: " + filename)
        docs.append(json.loads(raw))
    return docs


def verify_source_correction(buyer, sells, correction):
    """Append-only evidence corrections, not a rewrite of original source JSON."""
    require(correction["source_earlier_old_SHA"] ==
            "e2895bc8fc0a5c73754201504439d738ab1aa992",
            "source review version identity drift")
    source = correction["source_blobs"]
    require(source["buy_nplus1"] == PINS[0][1] and
            source["sampled_sell"] == PINS[1][1] and
            source["frozen_23wallet_19ca_overlay"] ==
            "3761b9140d0c64b1ffd8d8d243d63a2a1a4fc690",
            "source prior or frozen denominator changed")
    require(correction["frozen_universe"]["cells"] == 437 and
            correction["frozen_universe"]["count_wallets"] == 23 and
            correction["frozen_universe"]["count_CAs"] == 19,
            "frozen denominator changed")
    headers = correction["block_headers_selected_RPC_fields"]
    require(len(headers) == len({z["block"] for z in headers}) == 4,
            "duplicated or missing original headers")
    lookup = {z["block"]: z for z in headers}
    require(set(lookup) == {83635777, 83636000, 83636127, 83636128},
            "wrong original header block windows")
    from datetime import datetime, timezone
    for z in headers:
        milli = int(z["milliTimestamp"], 16)
        seconds = int(z["timestamp"], 16)
        require(milli // 1000 == seconds and
                datetime.fromtimestamp(milli/1000, tz=timezone.utc).
                isoformat(timespec="milliseconds").replace("+00:00","Z") ==
                z["utc_from_milliTimestamp"] and
                z["blockNumber_hex"] == hex(z["block"]) and
                len(z["hash"]) == 66,
                "RPC millisecond block time / timestamp mismatch")
    require(buyer["token"]["post_owner_test_utc"] ==
            lookup[83635777]["utc_from_milliTimestamp"] and
            sells["utc"] == lookup[83636000]["utc_from_milliTimestamp"],
            "unbacked old millisecond time")
    original_ms = int(correction["block_time_math"]["original_buy_milliTimestamp_hex"],16)
    sampled_gap = int(lookup[83636000]["milliTimestamp"],16) - original_ms
    require(sampled_gap == 100800 and
            correction["block_time_math"]["interval_in_milliseconds"] ==
            str(sampled_gap) and
            abs(float(sells["elapsed_seconds_since_owner_buy"]) -
                sampled_gap / 1000) < 1e-8,
            "unbacked 100.8 second block timestamp interval")
    scope = correction["sampled_block_exact_83636000"]
    require(scope["scope"] == "ONLY_BLOCK_83636000_NOT_FULL_83635777_TO_83636127_WINDOW" and
            scope["manager_sale_log_query"] == sells["manager_sale_getLogs_query"] and
            scope["dragon_token_transfer_query"] == sells["token_transfer_getLogs_query"],
            "sampled block versus entire trade-window scope changed")
    all_sales = scope["manager_all_TokenSale_logs"]
    all_transfers = scope["dragon_all_ERC20_Transfer_logs"]
    require(len(all_sales) == scope["manager_all_token_sales_total"] == 4 and
            len(all_transfers) == scope["dragon_Transfer_count"] == 5 and
            len({x["transactionHash"]+x["logIndex"] for x in all_sales}) == 4 and
            len({x["transactionHash"]+x["logIndex"] for x in all_transfers}) == 5,
            "incomplete single-block TokenSale or Transfer population")
    require(all(x["address"].lower() == MANAGER and
                x["topics"][0] == TOPIC_SALE and
                int(x["blockNumber"],16) == 83636000 for x in all_sales),
            "invalid source TokenSale log")
    require(all(x["address"].lower() == TOKEN and
                x["topics"][0] == TOPIC_TRANSFER and
                int(x["blockNumber"],16) == 83636000 for x in all_transfers),
            "invalid source Transfer log")
    target_sales = [x for x in all_sales
                    if "0x" + x["data"][26:66].lower() == TOKEN]
    require(len(target_sales) == scope["manager_target_CA_sales"] == 3 and
            scope["manager_other_CA_sale_count"] == 1,
            "other CA's TokenSale attributed to Dragon")
    archived = sells["actual_token_market_sell_events"]
    for x in archived:
        require(x["raw_sale_log"] in target_sales and
                x["corresponding_token_erc20_transfer_log"] in all_transfers,
                "original selected sale outside sampled block full logs")
    to_manager = [x for x in all_transfers if
                  "0x"+x["topics"][2][-40:].lower() == MANAGER]
    from_manager = [x for x in all_transfers if
                    "0x"+x["topics"][1][-40:].lower() == MANAGER]
    require(len(to_manager) == scope["dragon_Transfer_seller_to_manager_count"] == 3
            and len(from_manager) ==
            scope["dragon_Transfer_manager_to_other_count"] == 2,
            "two purchase-direction transfers or three sales omitted")
    receipt = scope["three_sale_receipt_excerpt"]
    require(len(receipt) == 3 and
            {x["txhash"].lower() for x in receipt} ==
            {x["decoded_sale_event"]["tx_hash"].lower() for x in archived} and
            all(x["status"]=="0x1" and x["truncated_result"] is True for x in receipt),
            "truncated receipt must preserve success evidence grade")
    membership = correction["seller_frozen_sample_membership"]
    require(len(membership) == 3, "missing exposed seller identity control")
    by_wallet = {x["wallet"].lower():x for x in membership}
    require(set(by_wallet) ==
            {x["decoded_sale_event"]["account"].lower() for x in archived},
            "seller / cohort identity drift")
    sample_inside = {"0x5c48a7c2113aa044d9c1381588b9c7b3c352387c":20,
                     "0x9d1240b262d91ec3a4ea24bfec5e3b21c2eca35c":22}
    for wallet,row in by_wallet.items():
        require(wallet != OWNER and wallet !=
                buyer["hypothetical_external_caller"]["EOA"].lower(),
                "market seller must be different from DDAC and simulated caller")
        if wallet in sample_inside:
            require(row["member_of_frozen_23"] is True and
                    row["source_wallet_index"] == sample_inside[wallet] and
                    row["frozen_dragon_CA_evidence"]["state"] == "COMPLETE_OBSERVED"
                    and row["frozen_dragon_CA_evidence"]["trade_signer"] ==
                    "UNVERIFIED_FROM_ERC20_ONLY",
                    "frozen research sample overlap hidden or upgraded")
        else:
            require(wallet == "0xbb99a969db5df28f032e2023058ce64c14a46a9b"
                    and row["member_of_frozen_23"] is False and
                    row["source_wallet_index"] is None,
                    "outside sample seller misclassified")
    ddac = correction["DDAC_initial_0p8_BNB_payment"]
    residual = (int(ddac["tx_value_wei"]) -
                int(ddac["source_TokenPurchase_curve_cost_wei"]) -
                int(ddac["source_TokenPurchase_protocol_fee_wei"]))
    require(ddac["source_tx"] == buyer["token"]["original_signed_early_buy_tx"]
            and ddac["tx_value_wei"] == "800000000000000000" and
            residual == 8000000000000004 and
            ddac["unattributed_value_minus_curve_cost_minus_fee_wei"] == str(residual)
            and ddac["attribution"] == "UNRESOLVED",
            "original DDAC paid native amount residual silently attributed")
    disabled = correction["migration_disabled_probe"]
    require(disabled["block"] == 83636127 and
            disabled["error_type"] == "RPC_ERROR_REVERT" and
            disabled["revert_reason"] == "Disabled" and
            disabled["revert_payload"].startswith("0x08c379a0"),
            "original disabled curve historical revert not captured")
    require(correction["gate"]["public_actionable_U"] == "UNRESOLVED" and
            correction["gate"]["follower_1_5_15_min_profit"] == "UNRESOLVED" and
            correction["gate"]["production"] == "NO_GO",
            "research outcome promoted after source correction")
    return {"total_all_CA_manager_sales":len(all_sales),
            "manager_to_buyer_transfers":len(from_manager),
            "in_cohort":sum(x["member_of_frozen_23"] for x in membership),
            "outside_cohort":sum(not x["member_of_frozen_23"] for x in membership),
            "timestamp_gap_millis":str(sampled_gap),
            "residual_wei":str(residual)}

def classify(docs):
    require(len(docs) == 3, "must load original two and append-only reviewer correction")
    buyer, sells, correction = docs
    token = buyer["token"]
    require(token["exact_CA"] == sells["token"] == TOKEN, "wrong exact CA")
    require(token["manager"] == sells["manager"] == MANAGER, "wrong manager")
    require(token["original_signed_early_buy_from"] == OWNER, "owner attribution changed")
    require(token["original_buy_block"] == 83635776, "source owner buy block changed")
    require(token["post_owner_observer_test_block"] == 83635777,
            "observer must not have same-block hindsight")
    require(sells["original_owner_DDAC_buy_block"] == 83635776,
            "sale source references a different owner entry")
    require(sells["block"] == 83636000 < buyer["terminal_observation"]["dex_liquidity_added_block"],
            "sales not in pre-DEX window")
    require(sells["elapsed_seconds_since_owner_buy"] > 0,
            "sale timestamp must follow owner entry")
    require(buyer["provenance"]["approved_prior_code_SHA"] ==
            "47945ca77806d23d942fa2abb681c70244e273a7",
            "changed review provenance")
    lookup = {x["block"]: x for x in buyer["historical_helper3_getTokenInfo"]["sampling"]}
    require({83635775, 83635776, 83635777, 83636127, 83636128} <= set(lookup),
            "frozen market states missing")
    entry = lookup[83635777]
    require(entry["version"] == "2" and entry["tokenManager"] == MANAGER and
            entry["quote"] == "0x" + "0" * 40 and not entry["liquidityAdded"] and
            int(entry["offers_raw"]) > 0, "post-owner native V2 curve not proven")
    require(not lookup[83636127]["liquidityAdded"] and
            lookup[83636128]["liquidityAdded"], "DEX migration boundary changed")
    follower = buyer["hypothetical_external_caller"]
    require(follower["EOA"] != OWNER and
            int(follower["BNB_balance_wei_at_83635777"]) > 100000000000000000,
            "external funded observer source missing")
    budgets = sorted(buyer["historical_pre_sell_buy_quotes"],
                     key=lambda b: int(b["budget_native_BNB_wei"]))
    require([int(q["budget_native_BNB_wei"]) for q in budgets] ==
            [10**16, 10**17], "budget cases drift")
    for q in budgets:
        require(q["block"] == 83635777 and
                q["simulation_from"] == follower["EOA"] and
                q["simulation_to"] == MANAGER and
                q["simulation_signature"] == "buyTokenAMAP(address,uint256,uint256)" and
                q["simulation_minAmount"] == "0" and
                q["read_only_call_return"] == "0x" and
                q["eth_call_reverted"] is False and
                q["real_fill"] is False, "simulated buy misreported as real fill")
        require(q["suggested_payable_msg_value_wei"] == q["budget_native_BNB_wei"] and
                int(q["curve_cost_wei"]) + int(q["protocol_fee_wei"]) <=
                int(q["budget_native_BNB_wei"]) and
                int(q["estimated_token_amount_raw"]) > 0, "funded buy quote inconsistent")
    require(buyer["ddac_observed_sell_permission"]["tokenManager_allowance_raw"] == "0",
            "DDAC historical sell allowance changed")
    require("insufficient allowance" in
            buyer["ddac_observed_sell_permission"]["direct_sell_ethCall_result"],
            "missing failed original owner direct-sell evidence")
    require(buyer["historical_sell_at_post_owner_state"]["block"] == 83635777,
            "sell quote not frozen to observer state")
    require(sells["manager_sale_getLogs_query"]["topics"] == [TOPIC_SALE] and
            sells["token_transfer_getLogs_query"]["topics"] == [TOPIC_TRANSFER] and
            sells["manager_sale_getLogs_query"]["address"] == MANAGER and
            sells["token_transfer_getLogs_query"]["address"] == TOKEN,
            "wrong original event query scope")
    sales = sells["actual_token_market_sell_events"]
    require(len(sales) == 3, "three sale witnesses missing")
    unique = set()
    for row in sales:
        event, log, transfer, tx = (
            row["decoded_sale_event"], row["raw_sale_log"],
            row["corresponding_token_erc20_transfer_log"],
            row["transaction_by_hash_raw"])
        h = event["tx_hash"].lower()
        require(h not in unique, "duplicate sale transaction")
        unique.add(h)
        require(event["token"] == TOKEN and event["account"].lower() == tx["from"].lower()
                and tx["hash"].lower() == h
                and log["transactionHash"].lower() == h
                and transfer["transactionHash"].lower() == h
                and log["topics"][0] == TOPIC_SALE and
                transfer["topics"][0] == TOPIC_TRANSFER
                and log["address"].lower() == MANAGER and
                transfer["address"].lower() == TOKEN,
                "sale signer/source identity not closed")
        require("0x" + transfer["topics"][1][-40:].lower() == event["account"].lower()
                and "0x" + transfer["topics"][2][-40:].lower() == MANAGER and
                int(transfer["data"], 16) == int(event["amount_token_raw"]) and
                int(event["gross_curve_quote_cost_raw"]) >
                int(event["protocol_base_fee_raw"]) >= 0,
                "sale token transfer or event amount/cost mismatch")
    correction_grade = verify_source_correction(buyer, sells, correction)
    require(buyer["gate"]["qualified_public_actionable_buy_AND_sell_U"] ==
            sells["gate"]["public_observer_U"] == "UNRESOLVED" and
            buyer["gate"]["follower_PnL_at_1_5_15min"] ==
            sells["gate"]["follower_lag_PnL"] == "UNRESOLVED",
            "unsupported U/follower PnL promotion")
    require(buyer["gate"]["production"] == sells["gate"]["production"] == "NO_GO",
            "production gate changed")
    return {
        "schema": "BSC_P4B_LONXIA_OBSERVER_EVIDENCE_GATE_V1",
        "source_files": [{"path": name, "git_blob_sha": sha} for name, sha in PINS],
        "source_owner": OWNER, "token": TOKEN,
        "first_approved_owner_entry_block": 83635776,
        "post_owner_test_block": 83635777,
        "native_BNB_budgets_simulated_wei": [str(10**16), str(10**17)],
        "historical_buy_simulations_success": len(budgets),
        "sampled_block_83636000_distinct_signed_dragon_sells": len(unique),
        "sampled_block_total_manager_sales_all_CAs": correction_grade["total_all_CA_manager_sales"],
        "sampled_block_dragon_manager_outgoing_transfers": correction_grade["manager_to_buyer_transfers"],
        "sale_signers_in_frozen_23": correction_grade["in_cohort"],
        "sale_signers_outside_frozen_23": correction_grade["outside_cohort"],
        "observed_buy_to_sale_block_timestamp_diff_milliseconds": correction_grade["timestamp_gap_millis"],
        "DDAC_initial_buy_unattributed_value_residual_wei": correction_grade["residual_wei"],
        "distinct_signers_NOT_controller_independent": True,
        "reported_sale_scope": "BLOCK_83636000_ONLY_NOT_FULL_WINDOW",
        "historical_buy_then_sell_same_follower_transaction_sequence": "NOT_PROVEN",
        "observer_first_public_execution_U": "UNRESOLVED",
        "follower_lag_1_5_15min_PnL": "UNRESOLVED",
        "P4_B": "PARTIAL", "P5": "BLOCKED", "production": "NO_GO"
    }

if __name__ == "__main__":
    print(json.dumps(classify(load()), ensure_ascii=False, indent=2))
