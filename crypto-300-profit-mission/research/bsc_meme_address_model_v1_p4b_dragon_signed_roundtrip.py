#!/usr/bin/env python3
"""Pinned historical Dragon signed owner rounds after DDAC; NOT follower backtesting.

Replays seven archived original sender transactions, exact token inventory,
and BOTH precommitted wallets' full 10-block segmented pre-migration curve-exit
Transfer scans. All arithmetic is integer wei; no RPC, trading or wallet access.
"""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PINS = {
    "pre": ("bsc-meme-address-model-v1-p4b-dragon-postowner-signed-roundtrip-precommit-2026-10-16.json",
            "a0937b2aca1c83cd99bf7e0678538a6067cc2d3f"),
    "dscan": ("bsc-meme-address-model-v1-p4b-dragon-d503-exhaustive-curve-sell-scan-2026-10-16.json",
              "5bf50fcb868d56e78fcdc26ac37da67ab56bdd1f"),
    "escan": ("bsc-meme-address-model-v1-p4b-dragon-e11b-exhaustive-curve-sell-scan-2026-10-16.json",
              "f749434738598922365b2d61e68a76a99262ae3d"),
    "token": ("bsc-meme-address-model-v1-p4b-dragon-two-buyers-historic-token-inventory-2026-10-16.json",
             "06bba24e15530cf9f0f7fde24ab876fcc764d173"),
    "native": ("bsc-meme-address-model-v1-p4b-dragon-two-buyers-historic-native-balances-2026-10-16.json",
              "9ac3c2bef80e5ada78c87f0949d19f80eb55ecab"),
    "tx": ("bsc-meme-address-model-v1-p4b-dragon-postowner-original-seven-txs-2026-10-16.json",
          "b06b2ef565ebd74bc7f83ad4a2ea731eeb5cb2b9"),
    "headers": ("bsc-meme-address-model-v1-p4b-dragon-postowner-four-execution-block-headers-2026-10-16.json",
               "e1f03de64a7716625ad5968df8fd389b48e8b261"),
}
TOKEN = "0xeccbb861c0dda7efd964010085488b69317e4444"
MANAGER = "0x5c952063c7fc8610ffdb798152d69f0b9550762b"
D503 = "0xd503f69b37efbfe510e37f46a4ca34e0adb1a7aa"
E11B = "0xe11b917d591db3bf40ecb5bf7ea4ea5af503460c"
TOPIC_TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"


def need(ok, code):
    if not ok:
        raise ValueError(code)


def load(root=ROOT):
    docs = {}
    for key, (name, blob) in PINS.items():
        raw = (Path(root) / name).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes((0,)) + raw).hexdigest()
        need(actual == blob, "SOURCE_BLOB_CHANGED:" + key)
        docs[key] = json.loads(raw)
    return docs


def _address(raw_word):
    return "0x" + format(int(raw_word), "040x")


def classify(docs):
    need(set(docs) == set(PINS), "MISSING_FROZEN_DOCUMENTS")
    pre, ds, es, inv, bal, txs, headers = (
        docs[k] for k in ("pre", "dscan", "escan", "token", "native", "tx", "headers"))
    need(pre["source_revision"] == "7c7c17d001114cbebd4afe6f056143955a73b025"
         and pre["token_exact_CA"] == TOKEN and pre["manager"] == MANAGER
         and pre["owner"]["block"] == 83635776, "PRECOMMIT_SCOPE_DRIFT")
    cases = pre["actual_buy_candidates_frozen_before_new_exit_RPC"]
    need(len(cases) == 2 and [c["wallet"] for c in cases] == [D503, E11B]
         and [c["buy_block"] for c in cases] == [83636000, 83636000],
         "BIASED_OR_RESELECTED_TWO_BUYER_COHORT")
    signed = {r["label"]: r for r in txs["cases"]}
    expected_labels = ("D503_BUY_1", "D503_APPROVE_1", "D503_SELL_1",
                       "D503_BUY_2", "D503_APPROVE_2", "D503_SELL_2", "E11B_BUY_1")
    need(set(signed) == set(expected_labels) and len(txs["cases"]) == 7,
         "SIGNED_SOURCE_SEVEN_TRANSACTION_COUNT_CHANGED")
    for k in expected_labels:
        row = signed[k]
        need(row["receipt"]["status"] == "0x1" and row["matched_original_event"]
             and row["receipt"]["complete"] == (row["kind"] != "purchase"),
             "SOURCE_SIGNED_RECEIPT_SUCCESS_OR_COMPLETENESS_CHANGED")
        need(row["from"] == (E11B if k == "E11B_BUY_1" else D503)
             and row["block"] < 83636128, "SOURCE_SIGNER_OR_BLOCK_DRIFT")
        need(row["matched_original_event"]["word_count"] ==
             (1 if row["kind"] == "approve" else 8),
             "EVENT_ABI_LENGTH_CHANGED")
        if row["kind"] != "approve":
            words = row["matched_original_event"]["words"]
            need(_address(words[0]) == TOKEN and
                 _address(words[1]) == row["from"] and
                 int(words[3]) > 0 and int(words[4]) > int(words[5]) > 0,
                 "SIGNED_TRADE_TOKEN_AMOUNT_OR_QUOTE_MISMATCH")
        else:
            need(row["to"] == TOKEN and row["selector"] == "0x095ea7b3" and
                 row["approve_input"][10:74].lower() == MANAGER[2:].rjust(64, "0"),
                 "ORIGINAL_ALLOWANCE_SIGNER_OR_SPENDER_INVALID")
    need([signed[k]["nonce"] for k in expected_labels[:-1]] ==
         [1957, 1958, 1959, 1960, 1961, 1962], "D503_NONCE_SEQUENCE_DRIFT")
    need(signed["E11B_BUY_1"]["nonce"] == 5908 and
         signed["E11B_BUY_1"]["tx"] == cases[1]["original_purchase_tx"] and
         signed["D503_BUY_1"]["tx"] == cases[0]["original_purchase_tx"],
         "ORIGINAL_BUY_SELECTION_CHANGED")

    scan_results = {}
    for key, wallet, expected_hashes in (
        ("dscan", D503, (signed["D503_SELL_1"]["tx"], signed["D503_SELL_2"]["tx"])),
        ("escan", E11B, ())):
        doc = docs[key]
        need(doc["wallet"] == wallet and doc["exact_CA"] == TOKEN
             and doc["manager"] == MANAGER and doc["topic"] == TOPIC_TRANSFER
             and doc["from_block_inclusive"] == 83636001
             and doc["to_block_inclusive"] == 83636127, "CURVE_SCAN_SOURCE_SCOPE_CHANGED")
        chunks = doc["scans"]
        need(len(chunks) == 13 and
             [(r["from"], r["to"]) for r in chunks] ==
             [(n, min(n + 9, 83636127)) for n in range(83636001, 83636128, 10)],
             "MISSING_10_BLOCK_FREE_TIER_COVERAGE")
        logs = []
        for row in chunks:
            need(row["status"] == "COMPLETE" and len(row["logs"]) == row["n"],
                 "PARTIAL_OR_TRUNCATED_SCAN_TREATED_AS_ZERO")
            for item in row["logs"]:
                need(int(item["blockNumber"], 16) in range(row["from"], row["to"] + 1)
                     and item["address"].lower() == TOKEN
                     and item["topics"][0] == TOPIC_TRANSFER
                     and _address(str(int(item["topics"][1], 16))) == wallet
                     and _address(str(int(item["topics"][2], 16))) == MANAGER
                     and int(item["data"], 16) > 0,
                     "SIGNED_SELL_SCAN_TRANSFER_SOURCE_MISMATCH")
                logs.append(item)
        need(tuple(x["transactionHash"] for x in logs) == expected_hashes,
             "FROZEN_BUYER_EXIT_COUNT_OR_HASH_CHANGED")
        scan_results[wallet] = logs

    inventory = {(s["wallet"], s["block"]): int(s["token_raw"])
                 for s in inv["samples"]}
    need(len(inventory) == len(inv["samples"]), "DUPLICATE_BLOCK_BALANCE_SOURCE")
    native = {s["block"]: s for s in bal["movements"]}
    need(set(native) == {83636000, 83636018, 83636084, 83636094},
         "MISSING_BUY_OR_SELL_NATIVE_BLOCK_DELTA")
    header = {x["block"]: x for x in headers["rows"]}
    need(set(header) == set(native), "MISSING_OR_WRONG_TRADE_BLOCK_HEADERS")
    for n, row in header.items():
        ms = int(row["milliTimestamp_hex"], 16)
        need(ms // 1000 == int(row["timestamp_hex"], 16) and
             datetime.fromtimestamp(ms / 1000, tz=timezone.utc).isoformat(
                 timespec="milliseconds").replace("+00:00", "Z") == row["utc"]
             and row["block_hash"], "BLOCK_MILLISECONDS_NOT_REPRODUCIBLE")
    need(int(header[83636000]["milliTimestamp_hex"], 16) -
         int(headers["owner_original_milliTimestamp_hex"], 16) == 100800,
         "POST_OWNER_INTERVAL_NOT_100_800MS")
    need(inventory[D503, 83635999] == 0 and inventory[E11B, 83635999] == 0
         and inventory[E11B, 83636000] ==
         int(signed["E11B_BUY_1"]["matched_original_event"]["words"][3])
         and inventory[E11B, 83636127] == inventory[E11B, 83636000],
         "E11B_ZERO_EXIT_OR_INVENTORY_NEGATIVE_CONTROL_CHANGED")

    rounds = []
    for index, buy_block, sell_block, prebuy_block, presell_block in (
        (1, 83636000, 83636018, 83635999, 83636017),
        (2, 83636084, 83636094, 83636083, 83636093)):
        buy, approve, sell = (signed[f"D503_{act}_{index}"]
                              for act in ("BUY", "APPROVE", "SELL"))
        amount = int(buy["matched_original_event"]["words"][3])
        need(sell["block"] == approve["block"] == sell_block and
             buy["block"] == buy_block and approve["nonce"] + 1 == sell["nonce"]
             and approve["matched_original_event"]["words"][0] == str(amount)
             and int(sell["matched_original_event"]["words"][3]) == amount
             and int(scan_results[D503][index - 1]["data"], 16) == amount,
             "ORIGINAL_BUY_APPROVE_SELL_TOKEN_NOT_ONE_MATCHED_AMOUNT")
        need(inventory[D503, prebuy_block] == 0 and
             inventory[D503, buy_block] == inventory[D503, presell_block] == amount
             and inventory[D503, sell_block] == 0,
             "TWO_ROUNDS_ERC20_INVENTORY_NOT_CLOSED")
        cost, fee = (int(sell["matched_original_event"]["words"][pos])
                     for pos in (4, 5))
        approval_gas, sale_gas = (
            int(x["receipt"]["gas_used_wei_gas_units"]) *
            int(x["receipt"]["effective_gas_price_wei"])
            for x in (approve, sell))
        sale_delta = int(native[sell_block]["block_native_delta_wei"])
        need(sale_delta == cost - 2 * fee - approval_gas - sale_gas,
             "HISTORIC_SALE_NATIVE_BLOCK_DELTA_NOT_RECONCILED_TO_TWO_FEES_AND_GAS")
        buy_delta = int(native[buy_block]["block_native_delta_wei"])
        need(buy_delta < 0 and buy["receipt"]["complete"] is False,
             "TRUNCATED_BUY_RECEIPT_MISREPRESENTED_AS_FULL_GAS_PROOF")
        need(buy["tx_value_wei"].isdigit() and
             int(buy["tx_value_wei"]) >
             int(buy["matched_original_event"]["words"][4]) +
             int(buy["matched_original_event"]["words"][5]),
             "SOURCE_NATIVE_BUY_COST_NOT_CLOSED")
        rounds.append({
            "round": index, "buyer": D503,
            "buy_tx": buy["tx"], "approve_tx": approve["tx"], "sell_tx": sell["tx"],
            "buy_block": buy_block, "sell_block": sell_block,
            "buy_utc": header[buy_block]["utc"],
            "sell_utc": header[sell_block]["utc"],
            "token_raw": str(amount),
            "actual_origin_signed_buy_and_sale_same_EOA": "CONFIRMED",
            "token_inventory_zero_buy_zero": "CONFIRMED_END_OF_BLOCK",
            "sale_native_wallet_block_delta_matches_quote_cost_minus_two_logged_fees_and_both_txs_gas": True,
            "purchase_tx_value_wei": buy["tx_value_wei"],
            "purchase_cost_minus_event_fee_residual_wei": str(
                int(buy["tx_value_wei"]) -
                int(buy["matched_original_event"]["words"][4]) -
                int(buy["matched_original_event"]["words"][5])),
            "sale_logged_curve_cost_wei": str(cost),
            "sale_logged_single_protocol_fee_wei": str(fee),
            "sale_approval_plus_execution_gas_wei": str(approval_gas + sale_gas),
            "native_2_block_EOA_delta_wei": str(buy_delta + sale_delta),
            "unattributed_buy_receipt_gas_and_internal_native_paths": "UNRESOLVED",
            "real_transaction_attributable_net_PnL": "UNRESOLVED",
        })
    return {
        "schema": "BSC_P4B_DRAGON_POST_OWNER_SIGNED_OWNER_ROUNDTRIPS_V1",
        "source_blobs": {key: {"path": n, "git_blob": blob}
                         for key, (n, blob) in PINS.items()},
        "frozen_actual_buyers": 2, "postowner_buy_senders_with_direct_pre_migration_sell": 1,
        "d503_confirmed_original_signed_token_roundtrips": 2,
        "e11b_direct_curve_sell_to_manager_observed": 0,
        "e11b_retained_token_at_83636127": str(inventory[E11B, 83636127]),
        "rounds": rounds,
        "sum_4_selected_wallet_native_block_deltas_wei": str(sum(
            int(v["block_native_delta_wei"]) for v in native.values())),
        "sum_grade": "RAW_EOA_BLOCK_SCOPE_NOT_FOLLOWER_TRADING_PROFIT",
        "public_third_party_signal_receipt_time": "UNRESOLVED",
        "first_executable_public_observer_U": "UNRESOLVED",
        "1_5_15_minute_follower_backtest": "BLOCKED_NO_UNTOUCHED_VISIBLE_U",
        "P4_B": "PARTIAL", "P4_C": "PARTIAL", "P5": "BLOCKED",
        "production": "NO_GO",
    }


if __name__ == "__main__":
    print(json.dumps(classify(load()), ensure_ascii=False, indent=2))
