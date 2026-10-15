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
            b"blob " + str(len(raw)).encode() + b"\\0" + raw
        ).hexdigest()
        require(digest == blob, "pinned evidence drift: " + filename)
        docs.append(json.loads(raw))
    return docs

def classify(docs):
    require(len(docs) == 2, "must load both bounded chain readbacks")
    buyer, sells = docs
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
                q["historical_ethCall_buy_simulation_output"] == "0x" and
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
    require(len(sales) == 3 == sells["gate"].get("sale_from_real_independent_EOAs", "") .count("NOT_EXPECTED")
            if False else len(sales) == 3, "three sale witnesses missing")
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
        "actual_subsequent_distinct_signed_market_sells": len(unique),
        "historical_buy_then_sell_same_follower_transaction_sequence": "NOT_PROVEN",
        "observer_first_public_execution_U": "UNRESOLVED",
        "follower_lag_1_5_15min_PnL": "UNRESOLVED",
        "P4_B": "PARTIAL", "P5": "BLOCKED", "production": "NO_GO"
    }

if __name__ == "__main__":
    print(json.dumps(classify(load()), ensure_ascii=False, indent=2))
