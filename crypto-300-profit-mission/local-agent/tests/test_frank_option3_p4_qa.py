"""Synthetic SQLite fixtures only: P4 QA causal signal joins, not live chain proof."""
from __future__ import annotations

import json
from pathlib import Path
import sqlite3
import sys

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import frank_option3_p4_causal_ro as causal  # noqa: E402
from frank_option3_p4_history import run_replay  # noqa: E402
from frank_option3_p4_signal_first import scan as scan_prior_signal_sales  # noqa: E402
from frank_option3_p4_activity_watch import build_activity_watch, render_activity_watch  # noqa: E402


def source_rows():
    chars = "ABCDEFGHJK"
    result = []
    for i, c in enumerate(chars):
        side = ["BUY", "REENTRY", "ADD", "BUY", "BUY",
                "EXIT", "SELL_POSITION_UNRESOLVED", "SELL",
                "EXIT", "SELL_POSITION_UNRESOLVED"][i]
        direction = "BUY" if i < 5 else "SELL"
        result.append({
            "wallet": "D" * 43,
            "signature": "A" * 64 + c,
            "mint": "B" * 42 + c,
            "side": side,
            "block_time": 1_799_000_000 + i * 61,
            "body": {"direction": direction},
        })
    return result


def fixtures(tmp_path, transactions):
    forward = tmp_path / "forward.sqlite"
    control = tmp_path / "control.sqlite"
    db = sqlite3.connect(forward)
    db.executescript("""
        CREATE TABLE signatures (wallet TEXT, signature TEXT, person_id TEXT, body TEXT);
        CREATE TABLE trades (wallet TEXT,signature TEXT,mint TEXT,side TEXT,
                             episode_id TEXT,block_time INTEGER);
        CREATE TABLE v1_states (person_id TEXT,mint TEXT,body TEXT);
        CREATE TABLE v1_evaluations (person_id TEXT,mint TEXT,signature TEXT,
                                     episode_id TEXT,at INTEGER,body TEXT);
        CREATE TABLE signals (signal_id TEXT,person_id TEXT,mint TEXT,
                              signal_type TEXT,episode_id TEXT,created_at INTEGER,
                              body TEXT);
    """)
    for i, tr in enumerate(transactions):
        db.execute("INSERT INTO signatures VALUES(?,?,?,?)",
                   (tr["wallet"], tr["signature"], "frank",
                    json.dumps({"classification": "ACTIVE_TRADE"})))
        db.execute("INSERT INTO trades VALUES(?,?,?,?,?,?)",
                   (tr["wallet"], tr["signature"], tr["mint"], tr["side"],
                    "episode-" + str(i), tr["block_time"]))
        db.execute("INSERT INTO v1_states VALUES(?,?,?)",
                   ("frank", tr["mint"], json.dumps(
                       {"events": [{"signature": tr["signature"]}]})))
        if i in (0, 1, 2, 4):
            ep = ("unrelated-evaluation-episode" if i == 4 else "episode-" + str(i))
            payload = (
                {"kind": "ACTIVE_TRADE", "signal_ids": ["signal-0"]}
                if i == 0 else
                {"kind": "HOURLY_29", "signal_ids": ["signal-3"]}
                if i == 2 else
                {"kind": "ACTIVE_TRADE", "signal_ids": ["signal-2"]}
                if i == 4 else
                {"kind": "ACTIVE_TRADE", "signal_ids": []}
            )
            db.execute("INSERT INTO v1_evaluations VALUES(?,?,?,?,?,?)",
                       ("frank", tr["mint"], tr["signature"], ep,
                        tr["block_time"], json.dumps(payload)))
    first, second, third, fifth = (
        transactions[0], transactions[1], transactions[2], transactions[4])
    samples = (
        ("signal-0", first, first["signature"], "episode-0"),
        ("signal-1", second, "C" * 63 + "A", "episode-1"),
        ("signal-2", fifth, fifth["signature"], "episode-4"),
        ("signal-3", third, third["signature"], "episode-2"),
    )
    for signal_id, tr, triggering, episode in samples:
        db.execute("INSERT INTO signals VALUES(?,?,?,?,?,?,?)",
                   (signal_id, "frank", tr["mint"],
                    "FRANK_ACCUMULATION_SIGNAL", episode,
                    tr["block_time"], json.dumps({
                        "signal_id": signal_id,
                        "triggering_signature": triggering,
                    })))
    sixth, seventh, eighth = transactions[5], transactions[6], transactions[7]
    for signal_id, tr, ep, at in (
        ("earlier-sell-5", sixth, "episode-5", sixth["block_time"] - 100),
        ("different-sell-6", seventh, "old-unrelated-episode", seventh["block_time"] - 100),
        ("later-sell-7", eighth, "episode-7", eighth["block_time"] + 100),
    ):
        db.execute("INSERT INTO signals VALUES(?,?,?,?,?,?,?)",
                   (signal_id, "frank", tr["mint"],
                    "FRANK_ACCUMULATION_SIGNAL", ep, at,
                    json.dumps({
                        "signal_id": signal_id,
                        "policy_id": "FRANK_LOCAL_SIGNAL_V1",
                        "triggering_signature": "C" * 63 + "K",
                    })))
    db.commit()
    db.close()

    ctl = sqlite3.connect(control)
    ctl.execute("""CREATE TABLE candidate_latest
                   (person_id TEXT,mint TEXT,episode_id TEXT,
                    decision TEXT,body TEXT)""")
    ctl.execute("INSERT INTO candidate_latest VALUES(?,?,?,?,?)",
                ("frank", first["mint"], "episode-0",
                 "WAIT", json.dumps({"source_signal_id": "signal-0"})))
    ctl.execute("INSERT INTO candidate_latest VALUES(?,?,?,?,?)",
                ("frank", fifth["mint"], "episode-4",
                 "BUY", json.dumps({"source_signal_id": "signal-2"})))
    ctl.commit()
    ctl.close()
    return forward, control


def test_exact_trigger_join_rejects_old_same_mint_and_wrong_episode(tmp_path, monkeypatch):
    rows = source_rows()
    source, control = fixtures(tmp_path, rows)
    monkeypatch.setattr(causal, "get_existing_trades", lambda: rows)
    result = causal.analyze(source, control)
    assert result["distinct_locally_indexed_rows"] == 10
    assert result["source_reconciled_rows"] == 10
    assert result["status"] == "TEN_LOCAL_SOURCE_ROWS_RECONCILED"
    assert result["source_database"] == "EXISTING_FORWARD_SQLITE_MODE_RO_QUERY_ONLY"
    assert result["rows"][0]["causal_status"] == "SOURCE_SIGNAL_EMITTED_BY_ACTIVE_TRADE_EVALUATION"
    assert result["rows"][0]["active_trade_signal_emission_proven"] is True
    assert result["rows"][0]["control_link"] == "EXACT_SIGNAL_TO_CONTROL_WAIT"
    assert result["rows"][1]["causal_status"] == "EXACT_TRANSACTION_EVALUATED_NO_NEW_SIGNAL"
    assert result["rows"][1]["exact_v1_signals"] == 0
    assert result["rows"][2]["causal_status"] == "SIGNAL_REFERENCES_BUY_SIGNATURE_EMITTED_ON_HOURLY_TICK"
    assert result["rows"][2]["active_trade_signal_emission_proven"] is False
    assert result["rows"][2]["hourly_tick_signal_emission_proven"] is True
    assert result["rows"][4]["causal_status"] == "SIGNAL_EVALUATION_EPISODE_MISMATCH"
    assert result["rows"][4]["control_link"] == "SIGNAL_EVALUATION_EPISODE_MISMATCH_NO_JOIN"
    assert result["rows"][6]["causal_status"] == "SELL_NO_V1_BUY_SIGNAL_EXPECTED"
    assert result["rows"][5]["sell_prior_signal_context"] == "EARLIER_SAME_EPISODE_V1_SIGNAL_CONFIRMED"
    assert result["rows"][6]["sell_prior_signal_context"] == "OLDER_SIGNAL_EXISTS_DIFFERENT_EPISODE_NOT_JOINED"
    assert result["rows"][7]["sell_prior_signal_context"] == "NO_EARLIER_SAME_EPISODE_V1_SIGNAL_PROVEN"
    assert result["rows"][5]["current_wallet_balance_verified"] is False
    assert all("mint" not in row and "signature" not in row for row in result["rows"])
    display = json.dumps(result, sort_keys=True)
    assert rows[0]["mint"] not in display
    assert rows[0]["signature"] not in display


def test_source_timestamp_change_is_not_silent_causal_pass(tmp_path, monkeypatch):
    rows = source_rows()
    source, control = fixtures(tmp_path, rows)
    modified = [dict(x) for x in rows]
    modified[0]["block_time"] += 100
    monkeypatch.setattr(causal, "get_existing_trades", lambda: modified)
    result = causal.analyze(source, control)
    assert result["source_reconciled_rows"] == 9
    assert result["status"] == "LOCAL_SOURCE_RECONCILIATION_INCOMPLETE_NOT_ZERO_TRADES"
    assert result["rows"][0]["source_match"] == "SOURCE_TRADE_CHANGED_SINCE_LOCAL_HTTP_CAPTURE"
    assert result["rows"][0]["causal_status"] == "NOT_EVALUATED_SOURCE_INCONSISTENT"


def test_p4_historical_fake_notices_separate_unresolved_sell_from_index_exit():
    rows = source_rows()
    result = run_replay(rows, snapshot_at=1_799_000_999)
    assert result["status"] == "PASS_LOCAL_INDEX_RETROSPECTIVE_REPLAY"
    assert result["counts"]["historical_fake_sell_notices"] == 5
    assert result["errors"] == []
    assert "观察到卖出 · 剩余仓位未核实" in result["html"]
    assert "本地索引标记退出 · 当前钱包余额未核实" in result["html"]
    assert all(all(c["checks"].values()) for c in result["cases"])
    assert all(c["fake_only"] for c in result["cases"])
    assert result["old_v1_signal_emission_proven"] is False
    assert result["profit_or_executability_proven"] is False


def test_signal_first_finds_verified_source_signal_before_same_episode_sale_only(tmp_path):
    rows = source_rows()
    source, control = fixtures(tmp_path, rows)
    first, sale = rows[0], rows[5]
    db = sqlite3.connect(source)
    db.execute("UPDATE trades SET mint=?,episode_id=? WHERE signature=?",
               (first["mint"], "episode-0", sale["signature"]))
    db.execute("UPDATE signals SET body=? WHERE signal_id='signal-0'",
               (json.dumps({
                   "policy_id": "FRANK_LOCAL_SIGNAL_V1",
                   "signal_id": "signal-0",
                   "episode_id": "episode-0",
                   "mint": first["mint"],
                   "triggering_signature": first["signature"],
               }),))
    db.commit()
    db.close()
    db = causal.open_ro(source)
    try:
        summary = scan_prior_signal_sales(db, as_of=sale["block_time"] + 1)
        assert summary["status"] == "SOME_PRIOR_SIGNAL_TO_LATER_SELL_LOCAL_FACTS"
        assert summary["source_signal_emission_bound"] == 1
        assert summary["signals_with_same_episode_later_sell"] == 1
        assert summary["distinct_verified_sale_signatures"] == 1
        assert summary["distinct_linked_episodes"] == 1
        assert summary["linked_sale_sides"] == {"EXIT": 1}
        assert summary["source_emission_modes_for_sales"] == {"ACTIVE_TRADE": 1}
        assert summary["recipient_delivery_verified"] is False
        assert summary["current_wallet_balance_verified"] is False
        serialized = json.dumps(summary)
        assert sale["signature"] not in serialized
        assert first["mint"] not in serialized
    finally:
        db.close()


def test_activity_watch_keeps_signed_sell_facts_absent_from_current_candidates():
    rows = source_rows()
    as_of = 1_799_000_999
    report = build_activity_watch(rows, [
        {"mint": rows[0]["mint"], "pattern": "REENTRY_WATCH"}
    ], as_of=as_of)
    assert report["status"] == "LOCAL_SOURCE_ACTIVITY_RESEARCH_ONLY"
    assert report["displayed_transactions"] == 10
    assert report["counts"]["buy_category"] == 5
    assert report["counts"]["sell_category"] == 5
    assert report["counts"]["unresolved_position_sell"] == 2
    assert report["counts"]["sell_not_in_current_candidate_mint_set"] == 5
    assert report["prior_v1_signal_linkage_verified"] is False
    assert report["real_notifications_authorized"] is False
    assert report["user_order_amount"] is None
    sell = [x for x in report["items"] if x["source_side"] in
            {"SELL", "EXIT", "SELL_POSITION_UNRESOLVED"}]
    assert len(sell) == 5
    assert all(not x["send_allowed"] and not x["channels"] for x in sell)
    assert all(x["related_to_prior_v1_signal"] == "NOT_VERIFIED" for x in sell)
    assert all(x["current_wallet_balance"] == "NOT_VERIFIED" for x in sell)
    html = render_activity_watch(report)
    assert "观察到卖出；剩余仓位无法确定" in html
    assert "本地索引分类为退出；当前链上余额未核实" in html
    assert "当前候选无此币种" in html
    assert "复制 CA" in html
    assert rows[0]["signature"] in html

    duplicates = build_activity_watch(rows + [dict(rows[0])], [], as_of=as_of)
    assert duplicates["displayed_transactions"] == 10
    assert duplicates["counts"]["omissions"]["DUPLICATE_SIGNATURE_SUPPRESSED"] == 1

    future = build_activity_watch(
        [dict(rows[0], block_time=as_of + 1)], [], as_of=as_of
    )
    assert future["displayed_transactions"] == 0
    assert future["counts"]["omissions"]["UNVERIFIABLE_SOURCE_FIELDS"] == 1
