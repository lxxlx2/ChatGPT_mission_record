"""Account order, fixed-evidence costs, and optional coverage in the W07 ledger."""
from copy import deepcopy
from fractions import Fraction

import pytest

from mission_agent.frank.parser import WSOL
from mission_agent.hashing import digest
from mission_agent.mission_control.ata_backfill import b58encode
from mission_agent.mission_control.wallet_cost_fifo import EXCHANGE_BASIS, build_cost_ledger
from mission_agent.mission_control.wallet_facts import _denomination
from mission_agent.signals.policy import USDC


WALLET, MINT, ATA1, ATA2 = (b58encode(bytes([n]) * 32) for n in (1, 2, 3, 4))


def balance(index, account, pre, post):
    return {"account_index": index, "account": account, "mint": MINT, "decimals": 2,
            "pre_raw": str(pre), "post_raw": str(post), "delta_raw": str(post-pre)}


def txn(slot, pre, post, *, quote=USDC, price=None, sequence=0, account=ATA1, other=(), fee=5,
        execution_status="SUCCEEDED", main_only=False):
    sig = b58encode(bytes([slot * 2 + sequence]) * 32)
    side = "BUY" if post > pre else "SELL"
    economics = None if price is None else {
        "basis": EXCHANGE_BASIS, "mint": MINT, "side": side,
        "token_amount_raw": str(abs(post-pre)), "token_decimals": 2,
        "quotes": [{"mint": quote, "denomination": _denomination(quote),
                    "decimals": 6 if quote == USDC else 9,
                    "raw_delta": str(-price if side == "BUY" else price)}]}
    bound = {"signature": sig, "wallet": WALLET, "slot": slot,
             "fee": {"wallet_fee_raw": str(fee) if fee is not None else None},
             "rent": {"wallet_paid_lamports": None, "wallet_refunded_lamports": None},
             "source_ref": {"raw_transaction_sha256": digest([sig])},
             "coverage": {"normalized_evidence": "BOUND", "components": {"token_account_balances": "RECORDED"}},
             "token_account_balances": [balance(0, account, pre, post), *other],
             "execution_status": execution_status}
    trade = {"mint": MINT,
             "recorded_token": {"direction": side, "decimals": 2, "raw_amount": str(abs(post-pre))},
             "recorded_primary_quote": {"mint": quote, "decimals": 6, "raw_amount": "999"}}
    fact = {**deepcopy(bound), "fact_id": digest([sig, "fact"]), "trade_legs": [trade, trade]}
    if not main_only:
        fact["archived_replay"] = {"status": "VERIFIED", "raw_sha256": digest([sig]),
                                   "fact": {**bound, "economic_exchange": economics}}
    return {"transaction_fact": fact}


def exact(rows, mint=USDC):
    (value,) = [row for row in rows if row["mint"] == mint]
    return Fraction(int(value["raw_numerator"]), int(value["raw_denominator"]))


def asset(result):
    return next(asset for asset in result["assets"] if asset["mint"] == MINT)


def test_fifo_multiple_fills_and_partial_exit_use_exact_raw_rationals():
    rows = [txn(1, 0, 3, price=20), txn(2, 3, 5, price=17), txn(3, 5, 1, price=51)]
    result = build_cost_ledger(reversed(rows), opening_known=True)
    a = asset(result)
    assert a["quantity_raw"] == a["known_cost_quantity_raw"] == "1"
    assert a["unknown_cost_quantity_raw"] == "0"
    sold = a["realized"][0]
    assert sold["covered_quantity_raw"] == "4"
    assert exact(sold["costs"]) == Fraction(57, 2)
    assert exact(sold["pnl"]) == Fraction(45, 2)
    assert exact(a["remaining_costs"]) == Fraction(17, 2)
    assert a["lots"][0]["remaining_quantity_raw"] == "0"
    assert a["lots"][1]["remaining_quantity_raw"] == "1"
    assert result["fees"]["network_fee_lamports"] == "15"
    assert result["fees"]["rent_paid_lamports"] is None
    assert result == build_cost_ledger(rows, opening_known=True)


def test_opening_and_external_inflow_keep_unknown_cost_fifo():
    a = asset(build_cost_ledger([txn(1, 4, 7, price=21), txn(2, 7, 9), txn(3, 9, 3, price=96)]))
    assert a["quantity_raw"] == "3"
    assert a["known_cost_quantity_raw"] == "1"
    assert a["unknown_cost_quantity_raw"] == "2"
    assert a["coverage"] == "PARTIAL"
    sell = a["realized"][0]
    assert sell["covered_quantity_raw"] == "2"
    assert exact(sell["partial_pnl"]) == 18
    assert sell["pnl"] is None and a["realized_summary"]["pnl"] is None


def test_distinct_quote_currencies_are_not_equated():
    a = asset(build_cost_ledger([txn(1, 0, 2, quote=WSOL, price=8), txn(2, 2, 5, price=9),
                                  txn(3, 5, 1, price=32)]))
    sold = a["realized"][0]
    assert sold["covered_quantity_raw"] == "2"
    assert exact(sold["costs"], WSOL) == 8
    assert exact(sold["costs"], USDC) == 6
    assert exact(sold["proceeds"]) == 32
    assert exact(sold["partial_pnl"]) == 10
    assert sold["pnl"] is None


def test_wallet_account_move_retains_original_lot_basis():
    rows = [txn(1, 0, 9, price=17), txn(2, 9, 5, other=[balance(1, ATA2, 0, 4)]),
            txn(3, 4, 1, account=ATA2, price=23)]
    a = asset(build_cost_ledger(rows))
    assert a["quantity_raw"] == a["known_cost_quantity_raw"] == "6"
    assert [m["kind"] for m in a["movements"]] == ["BUY", "WALLET_NET_ZERO", "SELL"]
    assert exact(a["realized"][0]["costs"]) == Fraction(17, 3)
    assert exact(a["remaining_costs"]) == Fraction(34, 3)


def test_same_slot_never_picks_an_arbitrary_fifo_sequence():
    buy, first, sell = txn(1, 0, 5, price=5), txn(2, 5, 10, price=10), txn(2, 10, 6, sequence=1, price=100)
    result = build_cost_ledger([buy, first, sell])
    assert result == build_cost_ledger([sell, first, buy])
    a = asset(result)
    assert a["quantity_raw"] == a["unknown_cost_quantity_raw"] == "6"
    assert a["known_cost_quantity_raw"] == "0"
    assert a["realized"][0]["pnl"] is None
    assert "SLOT_ORDER_UNVERIFIED" in a["coverage_reasons"]


def test_duplicate_rows_safe_and_conflicting_fact_rejected():
    event = txn(1, 0, 4, price=100)
    result = build_cost_ledger([event, deepcopy(event)])
    assert result["duplicate_transaction_count"] == 1
    assert asset(result)["quantity_raw"] == "4"
    assert result["fees"]["network_fee_lamports"] == "5"
    different = deepcopy(event)
    different["transaction_fact"]["fact_id"] = digest(["other"])
    with pytest.raises(ValueError, match="CONFLICTING_DUPLICATE_COST_FACT"):
        build_cost_ledger([event, different])


def test_failed_instructions_do_not_move_tokens_but_fees_and_cost_gaps_remain():
    buy = txn(1, 0, 3, price=12)
    failed = txn(2, 3, 0, price=20, fee=10, execution_status="FAILED")
    later = txn(3, 5, 8, price=21, fee=None)
    archived = buy["transaction_fact"]["archived_replay"]["fact"]
    archived["account_funding"] = {"items": [
        {"payer_role": "WALLET", "status": "CONFIRMED_INITIAL_FUNDING", "amount_raw": "2039280"},
        {"payer_role": "OTHER", "status": "CONFIRMED_INITIAL_FUNDING", "amount_raw": "2039280"},
    ]}
    archived["account_close_refunds"] = [
        {"destination_role": "WALLET", "status": "CONFIRMED_CLOSE_REFUND", "amount_raw": "100"},
    ]
    result = build_cost_ledger([buy, failed, later])
    assert result["fees"]["network_fee_lamports"] == "15"
    assert result["fees"]["network_fee_unknown_transactions"] == 1
    assert result["fees"]["initial_funding_paid_lamports"] == "2039280"
    assert result["fees"]["close_refund_received_lamports"] == "100"
    a = asset(result)
    assert a["quantity_raw"] == "8"
    assert a["known_cost_quantity_raw"] == "3"
    assert a["unknown_cost_quantity_raw"] == "5"
    assert len(a["realized"]) == 0
    assert "ACCOUNT_BALANCE_DISCONTINUITY" in a["coverage_reasons"]


def test_old_snapshot_has_quantities_but_never_promotes_legacy_quote():
    buy, sell = txn(1, 0, 3, main_only=True), txn(2, 3, 1, main_only=True)
    a = asset(build_cost_ledger([buy, sell]))
    assert a["quantity_raw"] == a["unknown_cost_quantity_raw"] == "1"
    assert a["remaining_costs"] == []
    sold = a["realized"][0]
    assert sold["proceeds"] is None and sold["pnl"] is None
