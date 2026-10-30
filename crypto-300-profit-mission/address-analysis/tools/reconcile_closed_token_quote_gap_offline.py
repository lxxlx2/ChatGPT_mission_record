#!/usr/bin/env python3
"""Offline-only reconciliation of frozen 449-wallet activity and 5 token rounds.

This does NOT infer token-level net PnL from native block-balance changes or
WBNB Router wrapping events. Recomputes exact integer wei arithmetic and
source-row identities from three Git-frozen datasets; no RPC/network/trades.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    "ledger": ("state/pnl-canonical-closed-token-ledger-20261019.json",
               "e1e1e1eea4f8c5aa998d3278eb18bc9c6b20c623"),
    "quote": ("evidence/pnl-mainline-wbnb-event-quotes-20261019.json",
              "53f4e00610c5a7540b1f8641d26b23f9870e8194"),
    "screen": ("evidence/activity-candidates-001-449.json",
               "4727b8b53dcd63b350d9e5f27922cd06db8a2a14"),
}
WBNB_CA = "0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c"


def require(condition, code):
    if not condition:
        raise ValueError(code)


def load_frozen_inputs(base=ROOT):
    result = {}
    for key, (relative, expected_blob) in SOURCES.items():
        raw = (Path(base) / relative).read_bytes()
        actual = hashlib.sha1(
            ("blob " + str(len(raw)) + "\x00").encode() + raw
        ).hexdigest()
        require(actual == expected_blob, "FROZEN_SOURCE_BLOB_CHANGED_" + key)
        result[key] = json.loads(raw)
    return result


def integer(value, code):
    require(type(value) is str and value.lstrip("-").isdigit(), code)
    return int(value)


def wei_as_bnb(value):
    from decimal import Decimal
    return format(Decimal(value) / Decimal(10**18), "f")


def audit(sources):
    ledger, quote, screen = (
        sources["ledger"], sources["quote"], sources["screen"])
    counts = screen["stats"]
    require((counts["universe"], counts["screened"],
             counts["active_wallets"], counts["signed_zero_on_checked_chains"],
             counts["profitability_audited_whole_wallets"]) ==
            (449, 449, 237, 212, 0), "FROZEN_449_COUNTS_MISMATCH")
    active = set(screen["active_source_rows"])
    inactive = set(screen["signed_zero_source_rows"])
    require(len(active) == 237 and len(inactive) == 212
            and not (active & inactive)
            and active | inactive == set(range(1, 450)),
            "FROZEN_449_ROWS_NOT_PARTITION")
    address_by_row = {
        int(r["source_row"]): r["address"].lower()
        for r in screen["records"]
    }
    require(len(address_by_row) == 449,
            "SCREEN_DUPLICATE_OR_MISSING_SOURCE_ROW")
    require((ledger["total_closed_token_roundtrips"],
             ledger["unique_original_source_wallets"],
             ledger["with_hash_matched_wbnb_event"]) == (5, 4, 3),
            "LEDGER_AGGREGATE_MISMATCH")
    require((ledger["approved_token_net_pnl"],
             ledger["approved_wallet_30d_pnl"],
             ledger["approved_wallet_lifetime_pnl"]) == (0, 0, 0),
            "UNSUPPORTED_PNL_PROMOTION")
    require(len(ledger["records"]) == 5 and len(quote["cases"]) == 3,
            "UNEXPECTED_LEDGER_SCOPE")

    quote_by_key = {}
    for q in quote["cases"]:
        key = (q["source_row"], q["wallet"].lower(), q["ca"].lower())
        require(key not in quote_by_key, "DUPLICATE_QUOTE_CASE")
        quote_by_key[key] = q

    rows, touched = [], set()
    for r in ledger["records"]:
        source_row = r["source_row"]
        wallet, ca = r["wallet"].lower(), r["contract_ca"].lower()
        key = (source_row, wallet, ca)
        require(source_row in active and address_by_row[source_row] == wallet,
                "SOURCE_ROW_WALLET_MISMATCH")
        require(key not in touched, "DUPLICATE_TOKEN_ROUNDTRIP")
        touched.add(key)
        require(r["closed"] is True and r["token_inventory_closed"] is True
                and integer(r["token_raw_received"], "TOKEN_IN_INVALID") ==
                    integer(r["token_raw_sold"], "TOKEN_OUT_INVALID"),
                "TOKEN_INVENTORY_NOT_CLOSED")
        require(r["wallet_trade_settlement_pnl"] == "UNRESOLVED"
                and r["whole_wallet_30d_pnl"] == "UNRESOLVED"
                and r["whole_wallet_lifetime_pnl"] == "UNRESOLVED",
                "UNSUPPORTED_REALIZED_PNL_CLAIM")
        native = integer(r["combined_native_execution_block_delta_wei"],
                         "NATIVE_BALANCE_INVALID")
        require(r["observed_direction"] ==
                ("POSITIVE" if native > 0 else "NEGATIVE" if native < 0
                 else "ZERO"),
                "DIRECTION_MISMATCH")
        q = quote_by_key.get(key)
        grade = "CLOSED_TOKEN_NATIVE_BLOCK_DELTA_ONLY"
        gross, difference = None, None
        if q is not None:
            require(r["quote_wbnb_contract"].lower() == WBNB_CA
                    and q["token"] == r["token"]
                    and q["buy"] in r["buy_tx_hashes"]
                    and q["sell"] == r["sell_tx_hash"]
                    and q["nativeBlockDeltaWei"] ==
                        r["combined_native_execution_block_delta_wei"],
                    "QUOTE_CASE_IDENTITY_OR_TRANSACTION_MISMATCH")
            gross = integer(q["sellWbnbWei"], "SELL_WBNB_INVALID") - integer(
                q["buyWbnbWei"], "BUY_WBNB_INVALID")
            difference = native - gross
            require(str(gross) == r["gross_wbnb_event_spread_wei"]
                    == q["wbnb_quote_event_spread_wei"]
                    and str(difference) ==
                        q["native_minus_event_quote_spread_wei"],
                    "WBNB_SPREAD_OR_DIFFERENCE_MISMATCH")
            grade = "HASH_MATCHED_WBNB_EVENT_NOT_WALLET_NET_PNL"
        else:
            require(r["gross_wbnb_event_spread_wei"] is None
                    and r["gross_wbnb_input_buy_wei"] is None,
                    "QUOTE_CASE_MISSING_BUT_AMOUNT_PRESENT")
        rows.append({
            "source_row": source_row, "wallet": wallet, "token": r["token"],
            "exact_ca": ca,
            "token_inventory_closed": True,
            "evidence_grade": grade,
            "native_execution_block_change_wei": str(native),
            "native_execution_block_change_bnb": wei_as_bnb(native),
            "wbnb_router_event_spread_wei": None if gross is None else str(gross),
            "wbnb_router_event_spread_bnb": None if gross is None else wei_as_bnb(gross),
            "unattributed_native_minus_wbnb_wei":
                None if difference is None else str(difference),
            "unattributed_native_minus_wbnb_bnb":
                None if difference is None else wei_as_bnb(difference),
            "approved_wallet_trade_net_pnl": None,
            "net_pnl_reason": "NO_INDEPENDENT_WALLET_SETTLEMENT_AND_FULL_COST_GAS",
            "source_tx_buy": r["buy_tx_hashes"],
            "source_tx_sell": r["sell_tx_hash"],
        })

    require(set(quote_by_key) == set(k for k in touched if k in quote_by_key),
            "UNMATCHED_QUOTE_CASE")
    require(sum(1 for r in rows if r["wbnb_router_event_spread_wei"]
                is not None) == 3, "QUOTE_COVERAGE_CHANGED")
    rows.sort(key=lambda r: (r["source_row"], r["token"], r["exact_ca"]))
    return {
        "schema": "address-analysis-449-closed-token-quote-gap-audit-v1",
        "date": "2026-10-19",
        "mode": "OFFLINE_FROZEN_INPUT_ONLY_NO_NEW_RPC",
        "source_blobs": {name: blob for name, (_, blob) in SOURCES.items()},
        "wallet_universe": 449,
        "three_chain_signed_active": 237,
        "three_chain_signed_zero": 212,
        "full_wallet_30d_or_lifetime_pnl_approved": 0,
        "closed_token_candidate_roundtrips": len(rows),
        "matched_wbnb_event_cases": 3,
        "without_matched_wbnb_event": 2,
        "approved_trade_net_pnl_cases": 0,
        "wallets_in_this_candidate_ledger": len(set(r["wallet"] for r in rows)),
        "limitations": [
            "WBNB wrapping events are not independently attributed wallet receipts.",
            "Execution-block native balance is not transaction-level realized PnL.",
            "Historic RTX5090 row016 remains separate; this 5-round ledger is not all historic token trades.",
            "171 active candidate queue positions have unfinished event pagination.",
            "No complete 30-day or lifetime wallet PnL audits; no profitable-wallet ranking.",
        ],
        "next_research": "DIRECT_WALLET_QUOTE_ASSET_BUY_SELL_WITH_GAS_COST_OR_DEFER",
        "rows": rows,
    }


if __name__ == "__main__":
    print(json.dumps(audit(load_frozen_inputs()), ensure_ascii=False,
                     indent=2, sort_keys=True))
