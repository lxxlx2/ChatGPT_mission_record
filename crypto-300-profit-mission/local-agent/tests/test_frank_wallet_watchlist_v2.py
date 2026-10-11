"""Observed watchlist regression. No network, no signer and no production writes."""
from __future__ import annotations

import json
from pathlib import Path
import sqlite3
import tempfile
from unittest.mock import patch

import pytest

from mission_agent.mission_control.wallet_watch import from_seed, from_sqlite, merge_signature_activity
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



def test_conflicting_quote_legs_in_one_signature_are_not_false_precision(tmp_path):
    p = tmp_path / "forward.sqlite"
    db = setup_db(p)
    record_trade(db, MINT2, "complex-route", "BUY", 1791509241, 3300000000)
    conflicting = {"quote_asset": USDC, "quote_amount_raw": "5000000000", "quote_decimals": 6}
    db.execute("INSERT INTO trades VALUES(?,?,?,?,?,?,?)",
               ("wallet1", "complex-route", MINT2, "episode", 1791509241,
                "BUY", json.dumps(conflicting)))
    db.commit()
    watch = from_sqlite(p)
    assert watch["rows"][0]["local_recognized_buys"] == 1
    assert watch["rows"][0]["last_observed_quote_quantity"] is None
    assert watch["rows"][0]["conflicting_trade_signatures"] == 1
    assert watch["rows"][0]["last_event_evidence"] == "LOCAL_INDEX_MULTILEG_UNRESOLVED"
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
    assert "snapshot_inventory_state" in js
    assert "DATED_POINT_IN_TIME_NOT_LIVE" in js
    assert "实时余额已核实" not in js
    assert 'value="WATCH_NOW" selected' in html
    assert 'value="PRIMARY"' in html
    assert "filter === 'WATCH_NOW'" in js
    assert 'value="PASSIVE_RECEIPT_ONLY"' in html
    assert 'value="OTHER_ACCOUNT_ACTIVITY"' in html
    assert "passive_receipt_only" in js


def _sig(signature, mint, amount, classification="PASSIVE_TRANSFER",
         signer=False, ts=1791505760):
    return {"signature": signature, "block_time": ts,
            "body": json.dumps({
                "classification": classification,
                "evidence": {
                    "wallet_is_signer": signer,
                    "wallet_token_transfer_flows": [],
                    "token_balance_deltas": [{
                        "mint": mint, "wallet_owned": True,
                        "decimals": 6, "delta": str(amount),
                        "pre_amount": "0", "post_amount": str(abs(int(amount))),
                    }],
                },
            })}


def test_wallet_signature_delta_adds_passive_mint_without_fake_buy(tmp_path):
    p = tmp_path / "forward.sqlite"
    db = setup_db(p)
    record_trade(db, MINT1, "existing-trade", "BUY", 1791505600, 1500000)
    db.execute("INSERT INTO signatures VALUES (?,?,?,?,?)",
               ("wallet1", "frank", "passive-new", 1791505760,
                _sig("passive-new", MINT2, 2846838050235)["body"]))
    db.execute("INSERT INTO signatures VALUES (?,?,?,?,?)",
               ("wallet1", "frank", "zero-ata", 1791505780,
                _sig("zero-ata", MINT3, 0, "ATA_CREATE")["body"]))
    db.commit()
    output = from_sqlite(p)
    rows = {x["mint"]: x for x in output["rows"]}
    assert output["summary"]["original_trade_or_model_observed"] == 1
    assert output["summary"]["total_observed"] == 3
    assert output["summary"]["passive_receipt_only"] == 1
    assert output["summary"]["other_account_activity_only"] == 1
    assert rows[MINT2]["watch_state"] == "PASSIVE_RECEIPT_ONLY"
    assert rows[MINT2]["local_recognized_buys"] == 0
    assert rows[MINT2]["passive_receipt_events"] == 1
    assert rows[MINT2]["signature_observed_in_raw"] == "2846838050235"
    assert rows[MINT2]["transfer_counterparty_verified"] is False
    assert rows[MINT2]["pnl_usd"] is None
    assert rows[MINT3]["watch_state"] == "OTHER_ACCOUNT_ACTIVITY"
    assert output["signature_activity_provenance"][
        "signature_rows_without_parsed_counterparty_flow"] == 3
    db.close()


def test_j7_source_still_missing_two_onchain_transfers_remains_unresolved():
    watch = from_seed([{
        "mint": MINT1, "local_state": "UNKNOWN",
        "local_recognized_buy_count": 0, "local_recognized_sell_count": 1,
    }])
    records = [
        _sig("first-external-transfer", MINT1, "2846838050235", ts=1791505760),
        _sig("later-sell", MINT1, "-12508217470763",
             classification="ACTIVE_TRADE", signer=True, ts=1791509213),
    ]
    result = merge_signature_activity(watch, records)
    row = result["rows"][0]
    assert row["watch_state"] == "HISTORY_SELL_ONLY"
    assert row["passive_receipt_events"] == 1
    assert row["signature_observed_in_raw"] == "2846838050235"
    assert row["signature_observed_out_raw"] == "12508217470763"
    assert row["sender_cost_basis_usd"] is None
    assert row["current_chain_balance_verified"] is False
    assert result["signature_activity_provenance"]["counterparty_flow_is_complete"] is False


def test_mac_20261011_delta_scope_224_mints_33_core_104_passive_87_other():
    # Actual source count baseline from real 1720-row 2026-10-11 Git upload:
    # 224 unique wallet-owned delta mints (33 trade/model + 191 extras).
    # Of 191 extras, 104 had a passive incoming delta and 87 had only
    # non-positive/zero or other account activity. Fake signatures are not
    # used to claim exact real transaction coverage.
    mint = lambda i: "H" + str(i).zfill(42)
    base = from_seed([{"mint": mint(i), "local_state": "OPEN"}
                      for i in range(33)])
    recs = [_sig(f"sig-{i}", mint(i), "10", ts=1791505760 + i,
                 classification="ACTIVE_TRADE", signer=True)
            for i in range(33)]
    recs += [_sig(f"passive-{i}", mint(i), "1", ts=1791506000 + i)
             for i in range(33, 137)]
    recs += [_sig(f"other-{i}", mint(i), "0", ts=1791506000 + i,
                  classification="ATA_CREATE")
             for i in range(137,224)]
    result = merge_signature_activity(base, recs)
    assert result["summary"]["original_trade_or_model_observed"] == 33
    assert result["summary"]["total_observed"] == 224
    assert result["summary"]["passive_receipt_only"] == 104
    assert result["summary"]["other_account_activity_only"] == 87
    assert all(not x["is_follow_signal"] for x in result["rows"])
    assert all(x["market_value_usd"] is None for x in result["rows"])


def test_passive_activity_never_overwrites_existing_closed_trade_status():
    watch = from_seed([{"mint": MINT1, "local_state": "CLOSED",
                        "local_recognized_sell_count": 2}])
    result = merge_signature_activity(watch, [_sig("passive", MINT1, 5)])
    row = result["rows"][0]
    assert row["watch_state"] == "HISTORICAL_EXIT"
    assert row["passive_receipt_events"] == 1
    assert row["origin_scope"] == "LOCAL_TRADE_OR_MODEL_WITH_SIGNATURE_DELTA"


def test_known_ata_gap_overlay_does_not_relabel_owner_index_trades():
    from mission_agent.mission_control.wallet_watch import annotate_known_ata_gaps
    original = from_seed([{"mint": MINT1, "local_state": "UNKNOWN"}])
    source = {"schema_version": 1,
              "owner_wallet": "498g1rVnFcnjBjpfw1xyqA1WvgQXUU8RWuELjxkjAayQ",
              "records": [{"mint": MINT1, "owner_index_missing_signatures": 2,
                           "verified_extra_passive_receipts": 2,
                           "source_date_utc": "2026-10-11"}]}
    overlay = annotate_known_ata_gaps(original, source)
    row = overlay["rows"][0]
    assert row["owner_index_gap_status"] == "CONFIRMED_HISTORICAL_GAP"
    assert row["owner_index_missing_signatures"] == 2
    assert row["ata_verified_extra_passive_receipts"] == 2
    assert row["local_recognized_buys"] == 0
    assert row["local_recognized_sells"] == 0
    assert not row["is_follow_signal"]
    assert overlay["summary"]["known_owner_index_gap_mints"] == 1
    missing = annotate_known_ata_gaps(original, None)
    assert missing["rows"][0]["owner_index_gap_status"] == "NOT_AUDITED"


def test_known_ata_gap_invalid_count_fails_closed():
    from mission_agent.mission_control.wallet_watch import annotate_known_ata_gaps
    observed = from_seed([{"mint": MINT1, "local_state": "UNKNOWN"}])
    bad = {"schema_version": 1,
           "owner_wallet": "498g1rVnFcnjBjpfw1xyqA1WvgQXUU8RWuELjxkjAayQ",
           "records": [{"mint": MINT1, "owner_index_missing_signatures": 2,
                        "verified_extra_passive_receipts": 3,
                        "source_date_utc": "2026-10-11"}]}
    with pytest.raises(ValueError, match="INVALID_ATA_GAP_RECORD"):
        annotate_known_ata_gaps(observed, bad)
