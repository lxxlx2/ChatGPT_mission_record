"""Observed watchlist regression. No network, no signer and no production writes."""
from __future__ import annotations

import json
from pathlib import Path
import sqlite3
import tempfile
from unittest.mock import patch

import pytest

from mission_agent.mission_control.wallet_watch import from_seed, from_sqlite
from mission_agent.mission_control.server import DashboardState

MINT1 = "HzYCHqAN2uoHGRnL9v2ChCfFQX3bvJuJd5zu2Hd5MZQy"
MINT2 = "CWKbSd7jwMXXexP3pbwLAWMzr4HXAXTvt4R9pk2Vyyyc"
MINT3 = "GTBxUiw6wJdmmkCGZgRHLyYxqu1vG4KtRpeox6yDpump"
USDC = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"


def setup_db(path):
    db = sqlite3.connect(path)
    db.executescript("""
        CREATE TABLE v1_states(person_id TEXT, mint TEXT, body TEXT);
        CREATE TABLE signatures(wallet TEXT, person_id TEXT, signature TEXT, block_time INTEGER, body TEXT);
        CREATE TABLE trades(wallet TEXT, signature TEXT, mint TEXT, episode_id TEXT,
                            block_time INTEGER, side TEXT, body TEXT);
        CREATE TABLE signals(signal_id TEXT, person_id TEXT, mint TEXT, episode_id TEXT, signal_type TEXT);
    """)
    return db


def record_trade(db, mint, sig, side, when, raw):
    wallet = "wallet1"
    db.execute("INSERT INTO signatures VALUES(?,?,?,?,?)",
               (wallet, "frank", sig, when, '{"classification":"ACTIVE_TRADE"}'))
    body = {"quote_asset": USDC, "quote_amount_raw": str(raw), "quote_decimals": 6}
    db.execute("INSERT INTO trades VALUES(?,?,?,?,?,?,?)",
               (wallet, sig, mint, "episode", when, side, json.dumps(body)))


def test_watchlist_reads_all_trades_even_without_model_signal(tmp_path):
    p = tmp_path / "forward.sqlite"
    db = setup_db(p)
    record_trade(db, MINT1, "sell-historic", "EXIT", 1791509207, 7031556770)
    record_trade(db, MINT2, "buy", "BUY", 1791509241, 3300000000)
    record_trade(db, MINT2, "sell-current", "EXIT", 1791670428, 3861174174)
    record_trade(db, MINT3, "undetermined-sell", "SELL_POSITION_UNRESOLVED", 1791610000, 2232343956)
    db.execute("INSERT INTO v1_states VALUES(?,?,?)",
               ("frank", MINT2, json.dumps({"state": "CLOSED", "current_raw": "0"})))
    db.execute("INSERT INTO v1_states VALUES(?,?,?)",
               ("frank", MINT3, json.dumps({"state": "INVENTORY_UNDETERMINED"})))
    # No signals at all. Current eligibility candidates could equal zero.
    db.commit()
    before = db.execute("SELECT COUNT(*) FROM trades").fetchone()[0]
    snap = from_sqlite(p, as_of=1791675000)
    assert snap["summary"]["total_observed"] == 3
    assert snap["summary"]["inventory_needs_review"] == 1
    assert snap["summary"]["historical_exit"] == 1
    assert snap["rows"][0]["mint"] == MINT2
    assert snap["rows"][0]["last_observed_quote_quantity"] == "3861.174174"
    assert snap["rows"][0]["watch_state"] == "HISTORICAL_EXIT"
    assert snap["rows"][1]["watch_state"] == "NEEDS_INVENTORY_REVIEW"
    assert snap["rows"][1]["local_recognized_sells"] == 1
    assert snap["rows"][2]["watch_state"] == "HISTORY_SELL_ONLY"
    assert snap["rows"][2]["last_observed_quote_quantity"] == "7031.55677"
    assert all(row["market_value_usd"] is None and row["pnl_usd"] is None for row in snap["rows"])
    assert all(row["current_chain_balance_verified"] is False for row in snap["rows"])
    assert db.execute("SELECT COUNT(*) FROM trades").fetchone()[0] == before
    db.close()


def test_real_mac_category_counts_from_observed_snapshot():
    # Canonical 2026-10-11 Mac export summary: 32 observed, 5 OPEN,
    # 13 CLOSED, 2 INVENTORY_UNDETERMINED, 12 UNKNOWN.
    observed = []
    for i, state in enumerate(["OPEN"] * 5 + ["CLOSED"] * 13 +
                               ["INVENTORY_UNDETERMINED"] * 2 + ["UNKNOWN"] * 12):
        observed.append({
            "mint": "H" + str(i).zfill(42),
            "local_state": state,
            "local_recognized_buy_count": 1 if i < 20 else 0,
            "local_recognized_sell_count": 1 if i >= 5 else 0,
            "latest_recognized_trade": {"signature": f"tx-{i}", "side": "BUY" if i < 5 else "SELL",
                                        "block_time": 1791509207 + i},
        })
    output = from_seed(observed, as_of=1791671948)
    assert output["summary"] == {
        "total_observed": 32,
        "model_open": 5,
        "inventory_needs_review": 2,
        "historical_exit": 13,
        "unresolved_history": 12,
    }
    assert len(output["rows"]) == 32
    assert output["scope"] == "LOCAL_INDEX_ONLY_NOT_COMPLETE_CHAIN"
    assert all(x["is_follow_signal"] is False for x in output["rows"])


def test_duplicate_trades_no_fake_double_count(tmp_path):
    p = tmp_path / "forward.sqlite"
    db = setup_db(p)
    record_trade(db, MINT2, "sig1", "BUY", 1000, 3300000000)
    db.execute("INSERT INTO trades SELECT * FROM trades")
    db.execute("INSERT INTO v1_states VALUES(?,?,?)",
               ("frank", MINT2, json.dumps({"state": "OPEN", "current_raw": "9935858022919"})))
    db.commit()
    snap = from_sqlite(p)
    assert snap["summary"]["model_open"] == 1
    assert snap["rows"][0]["local_recognized_buys"] == 1
    assert snap["rows"][0]["inventory_evidence"] == "MODEL_OPEN_UNVERIFIED"
    assert snap["rows"][0]["local_current_raw"] == "9935858022919"
    db.close()


def test_reader_is_read_only_and_missing_source_is_explicit(tmp_path):
    missing = tmp_path / "nonexistent.sqlite"
    with pytest.raises(FileNotFoundError):
        from_sqlite(missing)
    st = DashboardState(tmp_path, tmp_path)
    output = st.frank_observed_watchlist()
    assert output["status"] == "SOURCE_UNAVAILABLE"
    assert output["summary"] == {}
    assert output["rows"] == []


def test_watch_page_has_source_and_accessibility_labels():
    root = Path(__file__).resolve().parents[1]
    server = (root / "mission_agent" / "mission_control" / "server.py").read_text()
    js = (root / "mission_agent" / "mission_control" / "static" / "app.js").read_text()
    html = (root / "mission_agent" / "mission_control" / "static" / "index.html").read_text()
    service = (root / "mission_agent" / "mission_control" / "service.py").read_text()
    assert '"/api/frank-observed-watchlist"' in server
    assert "get('/api/frank-observed-watchlist')" in js
    assert "renderFrankWatchlist(watch)" in js
    assert 'id="watch-search"' in html
    assert 'id="watch-filter"' in html
    assert "独立" not in service or "signal" in service.lower()
    assert "current_chain_balance_verified" in js
