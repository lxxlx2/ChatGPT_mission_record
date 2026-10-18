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
    "5e60_in1": ("bsc-meme-address-model-v1-p4b-5e60-earlier-ten-inbound-dragon-cost-basis-censored-2026-10-18.json", "cee0c1be380f9509d5c30b73cc64d1350ad66c87"),
    "5e60_page2": ("bsc-meme-address-model-v1-p4b-5e60-historical-dragon-in-page2-out-page1-censored-2026-10-18.json", "bcb9bb22e57c5030ecb8e0addd31b67d9b4bbf5d"),
    "5e60_page3": ("bsc-meme-address-model-v1-p4b-5e60-historic-dragon-in3-out2-readback-2026-10-18.json", "6635527c2e2f17b238165c25ebf10fb4d334feda"),
    "5e60_page4": ("bsc-meme-address-model-v1-p4b-5e60-prior-inbound-page4-final-33in17out-2026-10-18.json", "ec3fafb7d95f1928438f6cd3aa5a1bde32da252b"),
    "frozen_grid": ("bsc-meme-address-model-v1-p4b-23x19-early-opportunity-ledger-2026-10-14.json", "f88ed9abfcb0f321ec31e98a029303aca48a8623"),
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


def frozen_cohort(s: dict) -> tuple:
    """Derive the unchanged research denominator from actual frozen source rows."""
    grid = s["frozen_grid"]
    wallets, markets = grid["wallets"], grid["markets"]
    wallet_ids = [w["wallet"].lower() for w in wallets]
    ca_ids = [m["ca"].lower() for m in markets]
    if (len(wallets), len(markets)) != (23, 19):
        raise ValueError("FROZEN_23X19_SOURCE_DENOMINATOR_DRIFT")
    if len(set(wallet_ids)) != len(wallet_ids) or len(set(ca_ids)) != len(ca_ids):
        raise ValueError("FROZEN_23X19_DUPLICATE_WALLET_OR_CA")
    if any(len(w["early_owner_trade_statuses"]) != len(markets) for w in wallets):
        raise ValueError("FROZEN_23X19_ROW_WIDTH_DRIFT")
    summary = grid["summary"]
    if (summary["wallets"], summary["major_exact_CAs"], summary["implicit_wallet_CA_cells"]) != (len(wallets), len(markets), len(wallets) * len(markets)):
        raise ValueError("FROZEN_23X19_SUMMARY_DRIFT")
    return len(wallets), len(markets), len(wallets) * len(markets), set(wallet_ids), set(ca_ids)


def reconstructed_5e60_erc20_pages(s: dict, wallet: str) -> dict:
    """Recompute raw token inventory from all six frozen pages in four unchanged files.

    Complete only for the original bounded Dragon ERC20 Transfer window;
    never promote a Transfer to an original signer-funded BUY or cost basis.
    """
    a, b = s["5e60_in1"], s["5e60_page2"]
    c, d = s["5e60_page3"], s["5e60_page4"]
    in2, out1 = b["results"]["INBOUND_PAGE2"], b["results"]["OUTBOUND_PAGE1"]
    in3, out2 = c["in_page3"], c["out_page2"]
    if (a["scope_from"], a["scope_to"]) != (85900000, 85959961):
        raise ValueError("EXTERNAL_PAGE_WINDOW_DRIFT")
    if (a["page_key_preserved"] != in2["original_cursor"]
            or in2["next_pageKey"] != in3["prevCursor"]
            or in3["nextCursor"] != d["input_cursor"]
            or out1["next_pageKey"] != out2["prevCursor"]):
        raise ValueError("EXTERNAL_PAGE_CURSOR_CHAIN_DRIFT")
    if (not a["pageKey_exists"] or a["complete_full_window"]
            or in3["nextCursor"] is None or in2["next_pageKey"] is None
            or out2["nextCursor"] is not None or d["remaining_pageKey"] is not None
            or not d["window_complete_inbound_stream"]
            or not d["complete_window_summary"]["all_transfer_pages_have_empty_final_cursor"]):
        raise ValueError("EXTERNAL_PAGE_COMPLETENESS_DRIFT")
    if b["fixed_token"].lower() != DRAGON or c["filters"]["tokenContract"].lower() != DRAGON or c["filters"]["wallet"].lower() != wallet.lower():
        raise ValueError("EXTERNAL_PAGE_IDENTITY_DRIFT")
    inbound_pages = [a["rows"], in2["rows"], in3["rows"], d["rows"]]
    outbound_pages = [out1["rows"], out2["rows"]]
    if [len(x) for x in inbound_pages] != [10, 10, 10, 3] or [len(x) for x in outbound_pages] != [10, 7]:
        raise ValueError("EXTERNAL_PAGE_COUNTS_DRIFT")
    if ([a["returned_count"], in2["returned_count"], in3["returned_count"], d["returned_count"]]
            != [10, 10, 10, 3] or
            [out1["returned_count"], out2["returned_count"]] != [10, 7]):
        raise ValueError("EXTERNAL_PAGE_REPORTED_COUNT_DRIFT")
    def sum_rows(pages: list, is_in: bool) -> tuple:
        seen = set()
        total, position = 0, 0
        for page in pages:
            for r in page:
                position += 1
                seq = r.get("rank", r.get("sequence", position))
                if seq != position:
                    raise ValueError("EXTERNAL_PAGE_SEQUENCE_DRIFT")
                if r["hash"] in seen:
                    raise ValueError("EXTERNAL_PAGE_DUPLICATE_HASH")
                seen.add(r["hash"])
                block = r["block"]
                if (not (85900000 <= block <= 85959961)
                        or (r["to"] if is_in else r["from"]).lower() != wallet.lower()
                        or ("token" in r and r["token"].lower() != DRAGON)
                        or r["hash"][:2] != "0x"):
                    raise ValueError("EXTERNAL_PAGE_TRANSFER_IDENTITY_DRIFT")
                raw = r.get("raw_Dragon_received", r.get("raw_amount_uint", r.get("rawUint")))
                if raw is None:
                    raise ValueError("EXTERNAL_PAGE_RAW_AMOUNT_MISSING")
                amount = int(raw)
                if amount <= 0:
                    raise ValueError("EXTERNAL_PAGE_NONPOSITIVE_RAW_AMOUNT")
                hex_raw = r.get("raw_amount_hex", r.get("rawHex"))
                if hex_raw is not None and int(hex_raw, 16) != amount:
                    raise ValueError("EXTERNAL_PAGE_HEX_RAW_MISMATCH")
                total += amount
        return position, total
    in_n, in_raw = sum_rows(inbound_pages, True)
    out_n, out_raw = sum_rows(outbound_pages, False)
    return {"inbound_count": in_n, "outbound_count": out_n,
            "inbound_raw": str(in_raw), "outbound_raw": str(out_raw),
            "complete_fixed_window_only": True}


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
        owner_row(d["owner"], "龙虾", d["exact_CA"], "DDAC_DRAGON", d["entry_block"], d["exit_block"], d["native_closed_owner_round_net_wei"], "OWNER_NATIVE_WINDOW_UNATTRIBUTED_BUY_AND_EXIT_FLOWS"),
    ]
    for i, x in enumerate(p, 1):
        tx = x["txs"]
        if x["owner"] != p[0]["owner"] or x["exact_CA"] != DRAGON or x["token_inventory_residual_raw"] != "0":
            raise ValueError("239E_ROUND_OR_CA_DRIFT")
        rows.append(owner_row(x["owner"], "龙虾", x["exact_CA"], "239E_DRAGON_R"+str(i), tx[0]["block"], tx[-1]["block"], x["original_native_wallet_net_wei"], "OWNER_SIGNED_NATIVE_WBNB_GAS_SCOPE"))
    rows.append(owner_row(h["owner"], "HAJIMI", h["exact_CA"], "8E6B_HAJIMI", h["buy"][0]["block"], h["sells"][-1]["block"], h["actual_native_round_net_wei"], "OWNER_NATIVE_POSITIVE_WITH_UNATTRIBUTED_BUY_ROUTING"))
    for x in n:
        if x["economic_sign"] != "NEGATIVE_NATIVE_SCOPE" or not x["signed_success_all"]:
            raise ValueError("NEGATIVE_CONTROL_SOURCE_DRIFT")
        rows.append(owner_row(x["wallet"], x["token"], x["exact_ca"], x["scope"], x["first_block"], x["last_block"], x["native_wallet_block_scope_wei"], "SIGNED_NATIVE_BLOCK_SCOPE_NOT_CAUSAL_NET_PNL"))
    if len(rows) != 6 or len({r["wallet"] for r in rows}) != 5 or len({r["exact_ca"] for r in rows}) != 4:
        raise ValueError("FROZEN_CROSS_MARKET_DENOMINATOR_DRIFT")

    n_wallets, n_markets, n_cells, original_wallets, original_cas = frozen_cohort(s)
    if any(x["wallet"].lower() not in original_wallets or x["exact_ca"].lower() not in original_cas for x in rows):
        raise ValueError("FROZEN_SELECTED_OWNER_NOT_IN_23X19")

    # Source text stays immutable; disclose its missing causal fund attribution here.
    ddac_buy_unattributed = (int(d["native_buy_block_debit_wei"])
                            - int(d["original_buy_event_cost_wei"]) - int(d["original_buy_event_fee_wei"]))
    ddac_exit_unattributed = (int(d["exit_TokenSale_cost_event_wei"]) - int(d["exit_TokenSale_fee_event_wei"])
                             - (int(d["native_exit_block_credit_after_gas_wei"]) + int(d["exit_block_total_signed_gas_wei"])))
    h_buy = h["buy"][0]
    hajimi_unattributed = int(h_buy["sent_signed_native_wei"]) - int(h_buy["WBNB_route_to_pool_wei"])
    if (ddac_buy_unattributed != 17007577000000000
            or ddac_exit_unattributed != 7314989186993731
            or len(d["exit_block_original_signed_txs"]) != 2
            or d["source_buy_full_receipt"] != "TRUNCATED"
            or hajimi_unattributed != 50000000000000000):
        raise ValueError("UNATTRIBUTED_NATIVE_SOURCE_GAP_DRIFT")
    unresolved_fund_flows = {
        "DDAC_DRAGON": {
            "native_buy_block_gap_wei": str(ddac_buy_unattributed),
            "exit_expected_single_event_fee_gap_wei": str(ddac_exit_unattributed),
            "owner_signed_exit_block_tx_count": len(d["exit_block_original_signed_txs"]),
            "buy_receipt": "TRUNCATED", "causal_fee_or_transfer_semantics": "UNRESOLVED",
            "proven_level": "OWNER_NATIVE_WINDOW_ONLY_NOT_FULL_CAUSAL_ECONOMIC_CLOSURE",
        },
        "8E6B_HAJIMI": {
            "signed_native_to_pool_WBNB_gap_wei": str(hajimi_unattributed),
            "classification": "UNATTRIBUTED_ROUTING_NATIVE_FLOW_NOT_CONFIRMED_PROTOCOL_FEE",
            "proven_level": "OWNER_NATIVE_WALLET_NET_POSITIVE_ROUTING_COMPONENT_UNRESOLVED",
        },
    }

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
    transfer_rows = reconstructed_5e60_erc20_pages(s, inventory["wallet"])
    if any(tr[key] != transfer_rows[key] for key in ("inbound_raw", "outbound_raw", "inbound_count", "outbound_count")):
        raise ValueError("EXTERNAL_PAGE_ROWS_VS_AGGREGATE_MISMATCH")
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
        "original_cohort_wallets": n_wallets, "original_exact_ca_count": n_markets, "original_cells": n_cells,
        "source_git_blobs": {k: {"path": name, "git_blob_sha": sha} for k, (name, sha) in SOURCES.items()},
        "selected_owner_rounds": rows,
        "unattributed_native_fund_flow_disclosures": unresolved_fund_flows,
        "selected_wallets": 5, "selected_CAs": 4,
        "historical_stale_control": {"owner": d["owner"], "token_ca": DRAGON, "after_exit_external_buy_block": 83636000, "actual_owner_balance_raw": "0", "conclusion": "OLD_DDAC_BUY_SIGNAL_ALREADY_EXPIRED_NOT_FOLLOWER_PROFIT"},
        "outside_cohort_5e60": {
            "wallet": inventory["wallet"], "role": "EXTERNAL_MARKET_CONTROL_ONLY",
            "prior_inventory_open_raw": opening[0]["rawDecimal"],
            "before_observed_additional_buy_raw": opening[1]["rawDecimal"],
            "prior_window_inbound_transfers": transfer_rows["inbound_count"],
            "prior_window_outbound_transfers": transfer_rows["outbound_count"],
            "in_out_from_source_pages_recomputed": True,
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
