"""Offline safety/contract tests for the one-shot read-only Mac audit."""
from __future__ import annotations

import importlib.util
import json
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/accept_meme_live_readonly.py"
spec = importlib.util.spec_from_file_location("meme_live_readonly_audit", SCRIPT)
auditor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(auditor)


def test_mac_auditor_source_has_no_mutation_paths():
    code = SCRIPT.read_text(encoding="utf-8")
    for forbidden in (
        "kickstart", "bootstrap", "launchctl load", "CREATE TABLE",
        "UPDATE gmail_delivery", "INSERT INTO", "DELETE FROM",
        "send_email(", "provider.send(", "urllib.request.urlopen(",
        "MissionMemeService(", "ControlDB(", "Engine(", "Scanner(",
    ):
        assert forbidden not in code
    assert "PRAGMA query_only=ON" in code
    assert "?mode=ro" in code
    assert "ProxyHandler({})" in code
    assert '"MAC_REBOOT_LOGIN_RECOVERY": "NOT_RUN_NO_REBOOT"' in code
    assert '"GMAIL_SENT_CURRENT_HEAD_END_TO_END": "NOT_RUN_NO_NEW_MAIL_SENT"' in code


def test_mac_auditor_db_is_opened_read_only(tmp_path):
    db = tmp_path / "state.sqlite"
    with sqlite3.connect(db) as conn:
        conn.execute("CREATE TABLE events (x INTEGER)")
        conn.execute("INSERT INTO events VALUES (42)")
    with auditor.db_ro(db) as conn:
        assert conn.execute("SELECT x FROM events").fetchone()[0] == 42
        with pytest.raises(sqlite3.OperationalError):
            conn.execute("INSERT INTO events VALUES (99)")
    with sqlite3.connect(db) as conn:
        assert conn.execute("SELECT count(*) FROM events").fetchone()[0] == 1
    with pytest.raises(FileNotFoundError):
        auditor.db_ro(tmp_path / "nonexistent.sqlite")
    assert not (tmp_path / "nonexistent.sqlite").exists()


def test_mac_auditor_receipt_correlation_is_exact(tmp_path):
    path = tmp_path / "mission-control.sqlite"
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE TABLE gmail_delivery "
                     "(decision_id TEXT,status TEXT,readback_verified INTEGER,"
                     " gmail_message_id TEXT,delivery_forbidden INTEGER,"
                     " delivery_mode TEXT,content_hash TEXT)")
        conn.execute("CREATE TABLE decision_outbox (channel TEXT,status TEXT)")
        conn.execute("CREATE TABLE decision_events "
                     "(decision_id TEXT,decision TEXT,created_at TEXT)")
        conn.execute("INSERT INTO gmail_delivery VALUES (?,?,?,?,?,?,?)", (
            auditor.HISTORICAL_SENT_DECISION,"SENT_VERIFIED",1,
            auditor.HISTORICAL_GMAIL_ID,0,"LIVE","abc",
        ))
        conn.execute("INSERT INTO decision_outbox VALUES ('gmail','SENT_VERIFIED')")
        conn.execute("INSERT INTO decision_events VALUES (?,?,?)",
                     (auditor.HISTORICAL_SENT_DECISION, "NO_BUY", "2026-10-08T00:00:00Z"))
    report = auditor.receipt_summary(path)
    assert report["gmail_status_counts"] == {"SENT_VERIFIED": 1}
    assert report["historical_identity"]["local_receipt_id_matches_gmail_sent"] is True
    assert report["historical_identity"]["local_readback_verified"] is True
    assert report["last_three_decisions"][0]["decision"] == "NO_BUY"
    with sqlite3.connect(path) as conn:
        conn.execute("UPDATE gmail_delivery SET gmail_message_id = 'unrelated-id'")
    result = auditor.receipt_summary(path)
    assert result["historical_identity"]["local_receipt_id_matches_gmail_sent"] is False


def test_mac_auditor_timestamp_parsing_has_no_false_freshness():
    now = datetime(2026, 10, 10, tzinfo=timezone.utc).timestamp()
    assert auditor.seconds_old("2026-10-09T23:59:30+00:00", now=now) == 30
    assert auditor.seconds_old("2026-10-09T23:59:30Z", now=now) == 30
    assert auditor.seconds_old(None, now=now) is None
    assert auditor.seconds_old("not a date", now=now) is None
    assert auditor.seconds_old("2026-10-09T23:59:30", now=now) is None
