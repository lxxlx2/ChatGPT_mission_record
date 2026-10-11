"""Regression tests: full local trade legs can be exported, never invent PnL."""
from __future__ import annotations

import json
from pathlib import Path
import sqlite3

from mission_agent.mission_control.wallet_history import export_history

USDC = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
SOL = "So11111111111111111111111111111111111111112"
MINT = "HzYCHqAN2uoHGRnL9v2ChCfFQX3bvJuJd5zu2Hd5MZQy"


def make_db(path: Path) -> sqlite3.Connection:
    db = sqlite3.connect(path)
    db.executescript("""
        CREATE TABLE signatures(wallet TEXT, person_id TEXT, signature TEXT, block_time INTEGER, body TEXT);
        CREATE TABLE trades(wallet TEXT, signature TEXT, mint TEXT, episode_id TEXT,
                            block_time INTEGER, side TEXT, body TEXT);
    """)
    return db


def add(db, sig, side, ts, body, mint=MINT, classification="ACTIVE_TRADE"):
    wallet="frank_wallet"
    db.execute("INSERT INTO signatures VALUES(?,?,?,?,?)", (
        wallet, "frank", sig, ts, json.dumps({
            "classification": classification, "provider_api_key": "DO_NOT_EXPORT"})))
    db.execute("INSERT INTO trades VALUES(?,?,?,?,?,?,?)",
               (wallet, sig, mint, "episode", ts, side, json.dumps(body)))


def standard_body(amount_raw):
    return {"quote_asset": USDC, "quote_decimals": 6, "quote_amount_raw": str(amount_raw),
            "amount_predicate": "USDC_DIRECT_NUMERIC", "token_decimals": 6,
            "token_amount_raw": "500000000", "source_url": "https://private.invalid/?api_key=secret",
            "private_key": "DO_NOT_EXPORT"}


def test_observed_usdc_roundtrip_is_not_reported_as_realized_pnl(tmp_path):
    dbpath=tmp_path/"forward.sqlite"
    db=make_db(dbpath)
    add(db, "buy-tweetcraft", "BUY", 1791419176, standard_body(6715734492))
    add(db, "sell-tweetcraft", "EXIT", 1791509207, standard_body(7031556770))
    db.commit()
    outcome=export_history(dbpath)
    assert outcome["record_count"] == 2
    cash=outcome["per_mint_cashflow_observations"][MINT]
    assert cash["direct_local_usdc_buy_outflow"] == "6715.734492"
    assert cash["direct_local_usdc_sell_inflow"] == "7031.556770"
    assert cash["profitability_verified"] is False
    assert cash["pnl_usd"] is None
    assert outcome["realized_pnl_usd"] is None
    assert outcome["local_signature_history_chain_complete"] is False
    assert outcome["signature_index_window"]["local_signatures_count"] == 2
    assert "DO_NOT_EXPORT" not in json.dumps(outcome)
    assert "source_url" not in json.dumps(outcome)
    assert db.execute("SELECT COUNT(*) FROM trades").fetchone()[0] == 2
    db.close()


def test_transferless_sell_only_is_positive_proceeds_not_profit(tmp_path):
    dbpath=tmp_path/"forward.sqlite"
    db=make_db(dbpath)
    add(db, "unknown-cost-sell", "SELL_POSITION_UNRESOLVED", 1791509213,
        standard_body(2232343956))
    db.commit()
    result=export_history(dbpath)
    cash=result["per_mint_cashflow_observations"][MINT]
    assert cash["direct_local_usdc_buy_outflow"] == "0"
    assert cash["direct_local_usdc_sell_inflow"] == "2232.343956"
    assert cash["pnl_usd"] is None
    assert cash["recognized_sell_legs"] == 1
    db.close()


def test_non_usdc_and_synthetic_shadow_cannot_be_counted_as_cashflow(tmp_path):
    dbpath=tmp_path/"forward.sqlite"
    db=make_db(dbpath)
    add(db, "sol-direct", "BUY", 1000, {
        "quote_asset": SOL, "quote_amount_raw": "5000000000", "quote_decimals": 9,
        "token_decimals": 6, "token_amount_raw": "500000"})
    add(db, "shadow", "SELL", 2000, {
        "quote_normalization": "SOL_TO_USDC_SHADOW_EQUIVALENT",
        "quote_asset": USDC, "quote_amount_raw": "850000000", "quote_decimals": 6,
        "original_quote": {"quote_asset": SOL, "quote_quantity": "5"},
        "quote_usdc_status": "SOL_EVENT_TIME_USDC_VERIFIED",
        "quote_usdc_equivalent": "850"})
    db.commit()
    result=export_history(dbpath)
    cash=result["per_mint_cashflow_observations"][MINT]
    assert cash["unpriced_or_ambiguous_legs"] == 2
    assert cash["direct_local_usdc_buy_outflow"] == "0"
    assert cash["direct_local_usdc_sell_inflow"] == "0"
    assert result["records"][1]["observed_quote"]["asset"] == SOL
    db.close()


def test_multileg_same_tx_and_duplicate_row_behaviour(tmp_path):
    dbpath=tmp_path/"forward.sqlite"
    db=make_db(dbpath)
    add(db, "sig-complex", "BUY", 3000, standard_body(100000000))
    # Same signature for another trade leg: keep it and flag conflict.
    db.execute("INSERT INTO trades VALUES(?,?,?,?,?,?,?)", (
        "frank_wallet", "sig-complex", MINT, "episode", 3000, "BUY",
        json.dumps(standard_body(200000000))))
    # Exact duplicate should not double count.
    db.execute("INSERT INTO trades SELECT * FROM trades WHERE rowid=1")
    db.commit()
    result=export_history(dbpath)
    assert result["record_count"] == 2
    assert result["duplicate_identical_rows_omitted"] == 1
    assert result["multileg_conflicting_trade_keys"] == 1
    assert result["per_mint_cashflow_observations"][MINT]["has_multileg_conflict"] is True
    assert result["realized_pnl_usd"] is None
    db.close()


def test_bad_amount_is_kept_as_unresolved_not_zero(tmp_path):
    dbpath=tmp_path/"forward.sqlite"
    db=make_db(dbpath)
    add(db, "sig-invalid", "BUY", 4000, {**standard_body(1000000),
                                         "quote_amount_raw": "-999"})
    db.commit()
    result=export_history(dbpath)
    assert result["record_count"] == 1
    assert result["records"][0]["observed_quote"]["quantity"] is None
    assert result["per_mint_cashflow_observations"][MINT]["unpriced_or_ambiguous_legs"] == 1
    assert result["realized_pnl_usd"] is None
    db.close()
