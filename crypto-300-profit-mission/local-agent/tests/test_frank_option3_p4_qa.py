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
            db.execute("INSERT INTO v1_evaluations VALUES(?,?,?,?,?,?)",
                       ("frank", tr["mint"], tr["signature"], ep,
                        tr["block_time"], '{"stages":[]}'))
    first, second, fifth = transactions[0], transactions[1], transactions[4]
    for idx, (tr, triggering) in enumerate(
        ((first, first["signature"]),
         (second, "C" * 63 + "A"),
         (fifth, fifth["signature"]))
    ):
        db.execute("INSERT INTO signals VALUES(?,?,?,?,?,?,?)",
                   ("signal-" + str(idx), "frank", tr["mint"],
                    "FRANK_ACCUMULATION_SIGNAL", "episode-" + str(idx),
                    tr["block_time"], json.dumps({
                        "signal_id": "signal-" + str(idx),
                        "triggering_signature": triggering,
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
    assert result["source_database"] == "EXISTING_FORWARD_SQLITE_MODE_RO_QUERY_ONLY"
    assert result["rows"][0]["causal_status"] == "EXACT_TRANSACTION_TRIGGERED_V1_SIGNAL"
    assert result["rows"][0]["control_link"] == "EXACT_SIGNAL_TO_CONTROL_WAIT"
    assert result["rows"][1]["causal_status"] == "EXACT_TRANSACTION_EVALUATED_NO_NEW_SIGNAL"
    assert result["rows"][1]["exact_v1_signals"] == 0
    assert result["rows"][4]["causal_status"] == "EXACT_TRANSACTION_TRIGGERED_V1_SIGNAL"
    assert result["rows"][4]["control_link"] == "NO_SAME_EPISODE_CONTROL_CANDIDATE"
    assert result["rows"][6]["causal_status"] == "SELL_NO_V1_BUY_SIGNAL_EXPECTED"
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
