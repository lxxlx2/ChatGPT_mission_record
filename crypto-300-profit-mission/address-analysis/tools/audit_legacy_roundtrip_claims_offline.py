#!/usr/bin/env python3
"""Reconcile historic 3 positive cashflow claims with stricter PnL evidence.

NO new chain access. Independent source blob pin + original 449 row mapping.
Historical single-token block-balance cashflow is NOT audited settlement PnL.
RTX5090 source uses IEEE float estimates and is never converted to exact wei.
"""
from __future__ import annotations

from decimal import Decimal
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BLOBS = {
    "rtx": ("evidence/batch-001-row-016-rtx5090-roundtrip.json",
            "6d4575b37e9363a1c1832b4a9e58218de86f6f0a"),
    "sauce": ("evidence/batch-001-rows-002-004-sauce-roundtrips.json",
              "83eee8f0699c650b0faad550776163146f524f51"),
    "canonical": ("state/pnl-canonical-closed-token-ledger-20261019.json",
                  "e1e1e1eea4f8c5aa998d3278eb18bc9c6b20c623"),
    "screen": ("evidence/activity-candidates-001-449.json",
               "4727b8b53dcd63b350d9e5f27922cd06db8a2a14"),
}


def need(condition, error):
    if not condition:
        raise ValueError(error)


def load(base=ROOT):
    result = {}
    for name, (relative, expected) in BLOBS.items():
        raw = (Path(base) / relative).read_bytes()
        digest = hashlib.sha1(
            ("blob " + str(len(raw)) + "\x00").encode() + raw
        ).hexdigest()
        need(digest == expected, "HISTORICAL_SOURCE_BLOB_CHANGED_" + name)
        result[name] = json.loads(raw)
    return result


def reconcile(inputs):
    screen, canonical = inputs["screen"], inputs["canonical"]
    sauce, rtx = inputs["sauce"], inputs["rtx"]
    need(screen["stats"]["screened"] == 449
         and screen["stats"]["active_wallets"] == 237
         and screen["stats"]["signed_zero_on_checked_chains"] == 212
         and screen["stats"]["profitability_audited_whole_wallets"] == 0,
         "449_SOURCE_DENOMINATOR_INVALID")
    indexed = {int(x["source_row"]): x["address"].lower()
               for x in screen["records"]}
    need(len(indexed) == 449, "449_DUPLICATE_OR_MISSING_ROWS")
    known = {(x["source_row"], x["wallet"].lower(),
              x["contract_ca"].lower()): x
             for x in canonical["records"]}
    need(len(known) == 5
         and canonical["approved_token_net_pnl"] == 0
         and canonical["approved_wallet_30d_pnl"] == 0
         and canonical["approved_wallet_lifetime_pnl"] == 0,
         "STRICT_NET_PNL_CANNOT_BE_PROMOTED")
    results = []

    need(len(sauce["roundtrips"]) == 2, "SAUCE_COUNT_INVALID")
    for rec in sauce["roundtrips"]:
        row = rec["row"]
        wallet = rec["wallet"].lower()
        ca = rec["token"].lower()
        key = (row, wallet, ca)
        need(row in (2, 4) and indexed[row] == wallet
             and key in known, "SAUCE_ORIGINAL_IDENTITY_MISMATCH")
        need(rec["balance_of_raw"]["before_buy"] == "0"
             and rec["balance_of_raw"]["after_sale"] == "0",
             "SAUCE_POSITION_NOT_CLOSED")
        buys = rec["buy_native_net_wallet_deltas_wei"]
        cost = -sum(int(x) for x in buys)
        received = int(rec["native_sale_net_wallet_delta_wei"])
        proxy = received - cost
        need(str(cost) == rec["net_cost_wei"]
             and str(proxy) == rec["net_gain_wei"]
             and str(proxy) == known[key][
                 "combined_native_execution_block_delta_wei"]
             and known[key]["wallet_trade_settlement_pnl"] == "UNRESOLVED",
             "SAUCE_PROXY_OR_GRADE_MISMATCH")
        results.append({
            "source_row": row, "token": "sauce",
            "exact_ca": ca, "wallet": wallet,
            "cashflow_proxy_bnb": str(Decimal(proxy) / 10**18),
            "proxy_precision": "EXACT_INTEGER_WEI_BLOCK_BALANCE_DELTAS",
            "legacy_single_token_cashflow_direction": "POSITIVE",
            "strict_attributed_net_pnl": None,
            "evidence_grade": "HISTORICAL_BLOCK_CASHFLOW_PROXY_TRACE_MISSING",
            "source_in_five_round_canonical": True,
        })

    rec = rtx
    row = rec["source_row"]
    need(row == 16 and indexed[row] == rec["wallet"].lower()
         and rec["opening_token_balance_before_buy_raw"] == "0"
         and rec["ending_token_balance_after_sells_raw"] == "0",
         "RTX_SOURCE_OR_POSITION_INVALID")
    txs = rec["txs"]
    need(len(txs) == 6 and sum(x["kind"] == "buy" for x in txs) == 1
         and sum(x["kind"] == "sell" for x in txs) == 5
         and len({x["hash"] for x in txs}) == 6,
         "RTX_TX_COUNT_OR_HASH_INVALID")
    observed = sum((Decimal(str(x["delta_bnb"])) for x in txs),
                   Decimal("0"))
    legacy = Decimal(str(rec["calculation"]["net_bnb"]))
    need(abs(observed - legacy) <= Decimal("0.000000000000001"),
         "RTX_FLOAT_CASHFLOW_RECONCILE_FAIL")
    need(not any(key[0] == row for key in known),
         "RTX_ALREADY_IN_FIVE_ROUND_LEDGER")
    results.append({
        "source_row": row, "token": rec["token_symbol"],
        "exact_ca": rec["token"].lower(), "wallet": rec["wallet"].lower(),
        "cashflow_proxy_bnb": str(observed),
        "source_legacy_net_bnb": str(legacy),
        "proxy_precision": "FLOAT_ORIGIN_APPROXIMATE_NOT_INTEGER_WEI",
        "legacy_single_token_cashflow_direction": "POSITIVE",
        "strict_attributed_net_pnl": None,
        "evidence_grade": "HISTORICAL_BLOCK_CASHFLOW_PROXY_NOT_SETTLEMENT_TRACE",
        "source_in_five_round_canonical": False,
    })
    need({(x["source_row"], x["wallet"], x["exact_ca"])
          for x in results}.__len__() == 3, "CROSS_SOURCE_DUPLICATE")
    results.sort(key=lambda x: x["source_row"])

    return {
        "schema": "address-analysis-legacy-cashflow-vs-strict-pnl-v1",
        "scope": "449_WALLET_HISTORY_ONLY_NO_PR40_MERGE",
        "mode": "FROZEN_EVIDENCE_OFFLINE_NO_NEW_RPC",
        "fixed_blob_sha1": {k: v[1] for k, v in BLOBS.items()},
        "historic_positive_single_token_block_cashflow_examples": 3,
        "examples_already_in_canonical_five": 2,
        "distinct_known_closed_token_cases_across_two_ledgers": 6,
        "strict_attributable_net_trade_pnl_cases": 0,
        "fully_audited_whole_wallet_30d_and_lifetime": 0,
        "wallets_screened": 449,
        "active_candidates": 237,
        "historical_erc20_transfer_presence_not_profit": True,
        "limitations": [
            "RTX historical tx delta_bnb entries are floating values: no exact wei PnL can be reconstructed from this archived source alone.",
            "SAUCE balance changes are exact integer wei but native balance changes may include same-block activity not assigned to the token swap.",
            "This source lacks separately attributed wallet-native internal trade settlement for the historical positive examples.",
            "No independent full-wallet 30d/lifetime PnL or forward-copyable returns proven.",
        ],
        "cases": results,
    }


if __name__ == "__main__":
    print(json.dumps(reconcile(load()), ensure_ascii=False, indent=2,
                     sort_keys=True))
