"""BSC P4-B source-pinned cross-market evidence decision table.

Research-only, historical selected cases, no observer timestamps, public U,
follower ROI, score, production signal or trade recommendation.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

RESEARCH = Path(__file__).resolve().parent
SOURCES = {
    "ddac": ("bsc-meme-address-model-v1-p4c-dragon-ddac-closed-native-loss-2026-10-15.json", "4e76eea4d7ab001360af82f15de5eefc8509c501"),
    "239e": ("bsc-meme-address-model-v1-p4c-239e-dragon-two-owner-native-settlements-2026-10-15.json", "46e90123b98d5324e05388b17b8a3bbb77cb5361"),
    "8e6b": ("bsc-meme-address-model-v1-p4c-8e6b-hajimi-dragon-two-verified-native-positive-2026-10-15.json", "dc144d9d259ef1392478d1e25d48f2f649744f20"),
    "negatives": ("bsc-meme-address-model-v1-p2-stage4-two-negative-2026-signed-rounds-2026-10-13.json", "5d3b64a96f6ae59585953a620e9414154ee44985"),
    "balances": ("bsc-meme-address-model-v1-p4b-2026-thirteen-historic-erc20-owner-balances-actual-readback-2026-10-18.json", "7e930c57fb5ba3a3dfd795575c059ade9f8a387d"),
    "5e60_inventory": ("bsc-meme-address-model-v1-p4b-5e60-real-opening-966415-and-33in17out-inventory-2026-10-18.json", "7c732dddf4b7693b769cfd98a980d92dd5afeed4"),
    "5e60_exit": ("bsc-meme-address-model-v1-p4b-5e60-eight-real-signed-usdt-sells-and-five-full-exit-2026-10-18.json", "902871db18ac42d98647ce43d61438e8e32b7947"),
}
DRAGON = "0xeccbb861c0dda7efd964010085488b69317e4444"
NO_GO = {"public_executable_U": "UNRESOLVED", "follower_1_5_15min_net_pnl": "UNRESOLVED", "production": "NO_GO"}


def git_blob_sha(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + bytes((0,)) + raw).hexdigest()


def read_all(root: Path = RESEARCH) -> dict:
    result = {}
    for key, (name, expected_sha) in SOURCES.items():
        raw = (root / name).read_bytes()
        if git_blob_sha(raw) != expected_sha:
            raise ValueError("SOURCE_BLOB_SHA_MISMATCH:" + key)
        result[key] = json.loads(raw)
    return result


def owner_row(owner: str, token: str, ca: str, case: str, entry: int, exit_block: int, net_wei: str, tier: str) -> dict:
    net = int(net_wei)
    if net == 0 or entry >= exit_block or not ca.startswith("0x") or len(ca) != 42:
        raise ValueError("INVALID_SELECTED_ECONOMIC_OR_TIMING_ROW")
    return {
        "case": case, "role": "FROZEN_23_OWNER", "wallet": owner,
        "token": token, "exact_ca": ca, "first_selected_buy_block": entry,
        "last_selected_exit_block": exit_block,
        "observed_selected_native_net_wei": str(net),
        "selected_sign": "POSITIVE" if net > 0 else "NEGATIVE",
        "evidence_tier": tier, "historical_selected_only": True,
        "wallet_lifetime_pnl": "UNRESOLVED", **NO_GO,
    }


def build(s: dict) -> dict:
    d = s["ddac"]["round"]
    p = s["239e"]["rounds"]
    h = s["8e6b"]["rounds"][0]
    n = s["negatives"]["rounds"]
    if len(p) != 2 or len(n) != 2 or h["round_key"] != "8E6B_HAJIMI_R1":
        raise ValueError("FROZEN_CASE_IDENTITY_DRIFT")
    rows = [
        owner_row(d["owner"], "龙虾", d["exact_CA"], "DDAC_DRAGON", d["entry_block"], d["exit_block"], d["native_closed_owner_round_net_wei"], "OWNER_SIGNED_NATIVE_WINDOW"),
    ]
    for i, x in enumerate(p, 1):
        tx = x["txs"]
        if x["owner"] != p[0]["owner"] or x["exact_CA"] != DRAGON or x["token_inventory_residual_raw"] != "0":
            raise ValueError("239E_ROUND_OR_CA_DRIFT")
        rows.append(owner_row(x["owner"], "龙虾", x["exact_CA"], "239E_DRAGON_R"+str(i), tx[0]["block"], tx[-1]["block"], x["original_native_wallet_net_wei"], "OWNER_SIGNED_NATIVE_WBNB_GAS_SCOPE"))
    rows.append(owner_row(h["owner"], "HAJIMI", h["exact_CA"], "8E6B_HAJIMI", h["buy"][0]["block"], h["sells"][-1]["block"], h["actual_native_round_net_wei"], "OWNER_SIGNED_WBNB_GAS_SETTLED"))
    for x in n:
        if x["economic_sign"] != "NEGATIVE_NATIVE_SCOPE" or not x["signed_success_all"]:
            raise ValueError("NEGATIVE_CONTROL_SOURCE_DRIFT")
        rows.append(owner_row(x["wallet"], x["token"], x["exact_ca"], x["scope"], x["first_block"], x["last_block"], x["native_wallet_block_scope_wei"], "SIGNED_NATIVE_BLOCK_SCOPE_NOT_CAUSAL_NET_PNL"))
    if len(rows) != 6 or len({r["wallet"] for r in rows}) != 5 or len({r["exact_ca"] for r in rows}) != 4:
        raise ValueError("FROZEN_CROSS_MARKET_DENOMINATOR_DRIFT")

    bal = s["balances"]["historical_exact_CA_and_owner_balance_rows"]
    ddac_at_external = [x for x in bal if x["wallet"] == d["owner"] and x["block"] == 83636000 and x["token_CA"] == DRAGON]
    if len(ddac_at_external) != 1 or ddac_at_external[0]["observed_raw_balance"] != "0":
        raise ValueError("STALE_OWNER_SIGNAL_NOT_PROVEN")
    inventory = s["5e60_inventory"]
    ext = s["5e60_exit"]
    opening, closed = inventory["observations"], ext["first_five"]
    if len(opening) != 2 or not inventory["fixed_window_transfers"]["owner_balance_match"]:
        raise ValueError("EXTERNAL_COST_BASIS_WINDOW_DRIFT")
    tr = inventory["fixed_window_transfers"]
    if int(opening[0]["rawDecimal"]) + int(tr["inbound_raw"]) - int(tr["outbound_raw"]) != int(opening[1]["rawDecimal"]):
        raise ValueError("EXTERNAL_TOKEN_INVENTORY_NOT_CLOSED")
    if opening[0]["rawDecimal"] == "0" or not closed["token_fully_exited"]:
        raise ValueError("EXTERNAL_OLD_HOLDING_OR_EXIT_DRIFT")
    if closed["Dragon_sold_raw"] != ext["checkpoints"]["before_first_sell_Dragon_raw"] or closed["Dragon_sold_raw"] != str(sum(int(z["actual_signed_Dragon_sold_raw"]) for z in ext["rows"][:5])):
        raise ValueError("EXTERNAL_FIRST_FIVE_SELL_NOT_CLOSED")
    if closed["USDT_received_raw"] != closed["wallet_USDT_actual_increase_raw"] or int(closed["USDT_received_raw"]) != sum(int(z["actual_USDT_received_raw"]) for z in ext["rows"][:5]):
        raise ValueError("EXTERNAL_USDT_CASH_RECEIPT_DRIFT")
    if ext["checkpoints"]["after_fifth_sell_Dragon_raw"] != "0" or tr["inbound_count"] != 33 or tr["outbound_count"] != 17:
        raise ValueError("EXTERNAL_SCOPE_DRIFT")
    return {
        "schema": "BSC_P4B_SOURCE_PINNED_CROSSMARKET_OBSERVER_DECISION_V1",
        "status": "RESEARCH_ONLY_HISTORICAL_SELECTED_NOT_UNTOUCHED",
        "original_cohort_wallets": 23, "original_exact_ca_count": 19, "original_cells": 437,
        "source_git_blobs": {k: {"path": name, "git_blob_sha": sha} for k, (name, sha) in SOURCES.items()},
        "selected_owner_rounds": rows,
        "selected_wallets": 5, "selected_CAs": 4,
        "historical_stale_control": {"owner": d["owner"], "token_ca": DRAGON, "after_exit_external_buy_block": 83636000, "actual_owner_balance_raw": "0", "conclusion": "OLD_DDAC_BUY_SIGNAL_ALREADY_EXPIRED_NOT_FOLLOWER_PROFIT"},
        "outside_cohort_5e60": {
            "wallet": inventory["wallet"], "role": "EXTERNAL_MARKET_CONTROL_ONLY",
            "prior_inventory_open_raw": opening[0]["rawDecimal"],
            "before_observed_additional_buy_raw": opening[1]["rawDecimal"],
            "prior_window_inbound_transfers": 33, "prior_window_outbound_transfers": 17,
            "five_signed_sells_dragon_raw": closed["Dragon_sold_raw"],
            "five_signed_sells_actual_USDT_receipt_raw": closed["USDT_received_raw"],
            "first_five_full_token_exit": True,
            "realized_net_profit": "UNRESOLVED_PREEXISTING_COST_BASIS",
            "follower_239e_causality": "UNRESOLVED",
            **NO_GO,
        },
        "no_strategy_success_rate": True, **NO_GO,
    }


if __name__ == "__main__":
    print(json.dumps(build(read_all()), ensure_ascii=False, indent=2, sort_keys=True))
