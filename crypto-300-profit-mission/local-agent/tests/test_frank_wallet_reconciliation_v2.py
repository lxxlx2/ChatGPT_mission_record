"""Frank source-ledger reconciliation must never manufacture costs or profit."""
from copy import deepcopy
import pytest
from mission_agent.mission_control.wallet_reconciliation import analyze

M1 = "2j5SaS7xy776qCBpyPQbZjyQSAtKiFgrwjfErthnW2ZM"
M2 = "J7bhFegCHZAeRzdYDwmbSp1CJ1bDJkutSg26B4SXpump"
USDC = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"


def event(mint, side, token_raw, usdc, *, missing_after=False):
    return {
        "mint": mint, "side": side,
        "observed_token_quantity": str(int(token_raw) / 1000000),
        "trade_raw_fields": {"token_amount_raw": str(token_raw), "token_decimals": 6,
                             "position_after_raw": None if missing_after else str(token_raw)},
        "observed_quote": {"asset": USDC, "quantity": usdc,
                           "status": "LOCAL_USDC_DIRECT_PREDICATE"},
    }


def fixture():
    records = [
        event(M1, "BUY", 885664587075, "4435.255282"),
        event(M2, "SELL_POSITION_UNRESOLVED", 12508217470763, "2232.343956",
              missing_after=True),
    ]
    history = {"person_id": "frank",
               "source_scope": "COMPLETE_LOCAL_RECOGNIZED_TRADES_NOT_FULL_CHAIN",
               "record_count": 2, "records": records}
    snap = {"wallet": "498g1rVnFcnjBjpfw1xyqA1WvgQXUU8RWuELjxkjAayQ",
            "network": "solana-mainnet", "commitment": "finalized",
            "status": "VERIFIED_POINT_IN_TIME_MINT_FILTERED_SOLANA_ACCOUNT_READS",
            "records": [{"mint": M1, "raw_amount": "886664587075",
                         "decimals": 6, "slot": 455530134}]}
    return history, snap


def test_new_mint_and_sell_only_gap_provenance():
    h,s = fixture()
    r = analyze(h,s)
    assert r["counts"]["snapshot_gap"] == 1
    assert r["counts"]["snapshot_missing"] == 1
    assert r["counts"]["sell_only_no_local_buy"] == 1
    assert r["counts"]["unresolved_sell_events"] == 1
    assert r["counts"]["missing_position_after_events"] == 1
    assert r["gross_local_buy_usdc"] == "4435.255282"
    assert r["gross_local_sell_usdc"] == "2232.343956"
    assert r["wallet_pnl_usd"] is None
    m = {row["mint"]: row for row in r["per_mint"]}
    assert m[M1]["unexplained_quantity_delta"] == "1000.000000"
    assert m[M2]["dated_chain_quantity"] is None
    assert all(row["realized_pnl_usd"] is None for row in m.values())


def test_reject_untrusted_snapshot_and_invalid_raw_units():
    h,s=fixture()
    s["wallet"] = "wrong-wallet"
    with pytest.raises(ValueError, match="INVALID_SNAPSHOT"):
        analyze(h,s)
    h,s=fixture()
    h["records"][0]["trade_raw_fields"]["token_amount_raw"] = "-5"
    with pytest.raises(ValueError, match="INVALID_TRADE_UNITS"):
        analyze(h,s)


def test_reject_local_token_amount_mismatch_and_wrong_count():
    h,s=fixture()
    h["records"][0]["observed_token_quantity"] = "0"
    with pytest.raises(ValueError, match="MISMATCH"):
        analyze(h,s)
    h,s=fixture()
    h["record_count"] = 77
    with pytest.raises(ValueError, match="INVALID_HISTORY"):
        analyze(h,s)
