"""Synthetic no-network tests for the Mac upgrade preflight's delivery safety gate."""
import importlib.util
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sqlite3

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts/frank_loop_upgrade_readonly_preflight_20261012.py"
S = importlib.util.spec_from_file_location("frank_loop_upgrade_readonly_preflight", SCRIPT)
ops = importlib.util.module_from_spec(S)
S.loader.exec_module(ops)

NOW = datetime(2026, 10, 12, 5, 20, 0, tzinfo=timezone.utc)


def db():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.executescript("""
       CREATE TABLE decision_events(decision_id TEXT PRIMARY KEY,created_at TEXT);
       CREATE TABLE gmail_delivery(
           decision_id TEXT,status TEXT,delivery_forbidden INTEGER,
           gmail_message_id TEXT
       );
       CREATE TABLE local_delivery(decision_id TEXT,status TEXT);
    """)
    return connection


def put(db, name, channel, status, seconds_ago=100, forbidden=0, message_id=None):
    when = (NOW - timedelta(seconds=seconds_ago)).isoformat()
    db.execute("INSERT INTO decision_events VALUES(?,?)", (name, when))
    if channel == "gmail":
        db.execute("INSERT INTO gmail_delivery VALUES(?,?,?,?)",
                   (name, status, forbidden, message_id))
    else:
        db.execute("INSERT INTO local_delivery VALUES(?,?)", (name, status))


def test_manual_review_and_historical_expired_are_never_reenqueued():
    con = db()
    put(con, "one", "gmail", "MANUAL_REVIEW", 90000)
    put(con, "two", "gmail", "DRY_RUN_AUDIT", 70000, forbidden=1)
    put(con, "three", "gmail", "PENDING", 650)
    put(con, "four", "local", "MANUAL_REVIEW", 64000)
    counts = ops.classify_pending(con, 600, NOW)
    assert counts["gmail_closed"] == 1
    assert counts["gmail_unsent_stale_review"] == 1
    assert counts["local_closed"] == 1
    assert counts.get("gmail_potential_fresh_send", 0) == 0
    assert counts.get("local_potential_fresh_notification", 0) == 0


def test_fresh_unsent_gmail_or_local_creates_upgrade_stop_signal():
    con = db()
    put(con, "fresh-gmail", "gmail", "PENDING", 100)
    put(con, "failed-gmail", "gmail", "RETRYABLE_ERROR", 130)
    put(con, "fresh-local", "local", "RETRY_PENDING", 100)
    counts = ops.classify_pending(con, 600, NOW)
    assert counts["gmail_potential_fresh_send"] == 2
    assert counts["local_potential_fresh_notification"] == 1


def test_uncertain_gmail_can_only_be_read_back_not_send_again():
    con = db()
    put(con, "sending", "gmail", "SENDING", 9000)
    put(con, "unverified", "gmail", "SENT_UNVERIFIED", 500)
    put(con, "message-known", "gmail", "PENDING", 200, message_id="provider-id")
    counts = ops.classify_pending(con, 600, NOW)
    assert counts["gmail_uncertain_readback_only"] == 3
    assert counts.get("gmail_potential_fresh_send", 0) == 0


def test_forbidden_non_audit_is_explicitly_blocked():
    con = db()
    put(con, "invalid", "gmail", "PENDING", forbidden=1)
    counts = ops.classify_pending(con, 600, NOW)
    assert counts["gmail_forbidden_non_audit"] == 1


def test_missing_or_invalid_timestamp_fails_closed_for_new_send_risk():
    con = db()
    con.execute("INSERT INTO gmail_delivery VALUES(?,?,?,?)", ("missing","PENDING",0,None))
    con.execute("INSERT INTO local_delivery VALUES(?,?)", ("unknown","RETRY_PENDING"))
    counts = ops.classify_pending(con, 600, NOW)
    assert counts["gmail_unsent_timestamp_unknown"] == 1
    assert counts["local_stale_or_unknown"] == 1
    assert counts.get("gmail_potential_fresh_send", 0) == 0


def test_stale_malformed_and_future_timestamp_handling():
    assert ops.decision_age_seconds(None, NOW) is None
    assert ops.decision_age_seconds("invalid", NOW) is None
    assert ops.decision_age_seconds("2026-10-12T05:19:30Z", NOW) == 30.0
    assert ops.decision_age_seconds("2026-10-12T05:19:30", NOW) is None
    assert ops.decision_age_seconds("2026-10-12T05:21:30+00:00", NOW) == -90.0


def test_no_side_effect_flags_are_fail_closed(monkeypatch):
    check_log = {}
    monkeypatch.setattr(ops, "checks", check_log)
    with pytest.raises(RuntimeError, match="FAILED_NO_FRESH_SENDABLE_LEGACY_GMAIL"):
        ops.check("NO_FRESH_SENDABLE_LEGACY_GMAIL", False)
    assert check_log["NO_FRESH_SENDABLE_LEGACY_GMAIL"] == "FAIL"


@pytest.mark.parametrize("missing", [
    "POLICY", "APPROVED_HASH_FILE", "RPC_FILE",
])
def test_missing_authorization_file_identifies_exact_item_without_secret_leak(tmp_path, monkeypatch, capsys, missing):
    paths = {
        "POLICY": tmp_path / "approved-policy.json",
        "APPROVED_HASH_FILE": tmp_path / "approved-sha256",
        "RPC_FILE": tmp_path / "solana-rpc",
    }
    for key, path in paths.items():
        if key != missing:
            path.write_text("SECRET_SYNTHETIC_DO_NOT_PRINT")
    monkeypatch.setattr(ops, "checks", {})
    monkeypatch.setattr(ops, "details", {})
    assert ops.inspect_authorization_artifacts(paths) is False
    expected = {
        "POLICY": "POLICY_JSON_PRESENT",
        "APPROVED_HASH_FILE": "APPROVED_SHA256_FILE_PRESENT",
        "RPC_FILE": "SOLANA_RPC_FILE_PRESENT",
    }[missing]
    assert ops.details["missing_authorization_artifacts"] == [expected]
    assert ops.checks[expected] == "FAIL"
    printed = capsys.readouterr().out
    assert "SECRET_SYNTHETIC" not in printed
    assert str(tmp_path) not in printed


def test_all_authorization_artifacts_present(tmp_path, monkeypatch):
    paths = {
        "POLICY": tmp_path / "policy",
        "APPROVED_HASH_FILE": tmp_path / "sha",
        "RPC_FILE": tmp_path / "rpc",
    }
    for path in paths.values():
        path.write_text("PRIVATE_FIXTURE")
    monkeypatch.setattr(ops, "checks", {})
    monkeypatch.setattr(ops, "details", {})
    assert ops.inspect_authorization_artifacts(paths) is True
    assert all(status == "PASS" for status in ops.checks.values())
    assert ops.details["missing_authorization_artifacts"] == []



def test_post_clone_reopen_reports_stage_and_sqlite_error_name_without_paths(tmp_path, monkeypatch, capsys):
    from pathlib import Path
    import sqlite3
    monkeypatch.setattr(ops, "details", {})
    monkeypatch.setattr(ops, "checks", {})
    private = tmp_path / "private-auth-data"
    def raise_cantopen(_path):
        raise sqlite3.OperationalError("unable to open database file: SECRET_NEVER_PRINT")
    monkeypatch.setattr(ops, "query_ro", raise_cantopen)
    with pytest.raises(sqlite3.OperationalError):
        ops.check_post_clone_status(private, {})
    assert ops.details["clone_stage"] == "POST_CLONE_OPEN_READONLY"
    assert ops.details["clone_sqlite_error_name"] == "OperationalError"
    assert "SECRET_NEVER_PRINT" not in capsys.readouterr().out
    assert str(tmp_path) not in capsys.readouterr().out


def test_post_clone_checks_valid_sqlite_rows_unchanged(tmp_path, monkeypatch):
    from mission_agent.mission_control.db import ControlDB
    monkeypatch.setattr(ops, "details", {})
    monkeypatch.setattr(ops, "checks", {})
    p = tmp_path / "control-copy.sqlite"
    writer = ControlDB(p)
    writer.close()
    with ops.closing(ops.query_ro(p)) as ro:
        before = ops.counters(ro)
    ops.check_post_clone_status(p, before)
    assert ops.details["clone_stage"] == "COMPLETE"
    assert ops.checks["POST_CLONE_READONLY_REOPEN"] == "PASS"
    assert ops.checks["POST_CLONE_INTEGRITY"] == "PASS"
    assert ops.checks["EXISTING_EVENTS_AND_DELIVERY_UNCHANGED"] == "PASS"


def test_cloned_database_error_code_does_not_allow_fake_success(tmp_path, monkeypatch):
    from pathlib import Path
    monkeypatch.setattr(ops, "details", {})
    monkeypatch.setattr(ops, "checks", {})
    p = tmp_path / "missing.sqlite"
    with pytest.raises(ops.sqlite3.Error):
        ops.check_post_clone_status(p, {})
    assert ops.details["clone_stage"] == "POST_CLONE_OPEN_READONLY"
    assert "POST_CLONE_INTEGRITY" not in ops.checks
    assert "EXISTING_EVENTS_AND_DELIVERY_UNCHANGED" not in ops.checks
