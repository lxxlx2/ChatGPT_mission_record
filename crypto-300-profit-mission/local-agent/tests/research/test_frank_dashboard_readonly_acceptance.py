"""Nonmutating one-shot Mac acceptance against a synthetic real SQLite store."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from mission_agent.mission_control.db import ControlDB
from test_delivery_review_integration import seed

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "frank_dashboard_readonly_acceptance.py"
spec = importlib.util.spec_from_file_location("frank_readonly_acceptance", SCRIPT)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


@pytest.fixture
def source(tmp_path):
    ctl = tmp_path / "control"
    ctl.mkdir()
    db = ControlDB(ctl / "mission-control.sqlite")
    yield ctl, db
    db.close()


def test_real_sqlite_one_expired_plus_three_pending_counted_separately(source):
    root, db = source
    seed(db)
    for kind in ("SENDING", "SENT_UNVERIFIED", "SENT_UNVERIFIED"):
        seed(db, kind, attempts=1, gmail_attempts=1)
    before = db.db.execute("SELECT COUNT(*) FROM decision_outbox").fetchone()[0]
    got = probe.summary_from_database(root)
    assert got["manual_review_total_count"] == 1
    assert got["manual_review_expired_unsent_count"] == 1
    assert got["manual_review_pending_count"] == 3
    assert got["manual_review_pending_gmail_count"] == 3
    assert got["manual_review_visible_total_count"] == 4
    assert db.db.execute("SELECT COUNT(*) FROM decision_outbox").fetchone()[0] == before


def test_readonly_script_returns_prebrowser_acceptance_not_full_release(
        source, tmp_path, monkeypatch, capsys):
    root, db = source
    seed(db, "SENDING", attempts=1, gmail_attempts=1)
    counts = probe.summary_from_database(root)
    monkeypatch.setattr(probe, "dashboard_root", lambda: tmp_path)
    monkeypatch.setattr(probe, "source_state", lambda path: "TARGET")
    monkeypatch.setattr(probe, "control_root", lambda: root)
    monkeypatch.setattr(probe, "local_dashboard_health",
                        lambda path: {"manual_review_breakdown_available": True,
                                      "manual_review_breakdown_error": None,
                                      **counts})
    assert probe.main() == 0
    output = json.loads(capsys.readouterr().out)
    assert output["operational_acceptance"] == "READ_ONLY_COUNTS_PASS_BROWSER_PENDING"
    assert output["mac_browser_ui_rendered"] is False
    assert output["gmail_sent"] is False
    assert output["mac_rollout_performed"] is False
    assert output["production_sqlite_modified"] is False
    assert output["database_counts"]["manual_review_pending_count"] == 1
    assert output["source_matches_target"] is True
    assert db.db.execute(
        "SELECT COUNT(*) FROM decision_outbox WHERE status='SENDING'").fetchone()[0] == 1


@pytest.mark.parametrize("case", ["legacy_source", "wrong_http", "missing_http"])
def test_readonly_failure_exits_nonzero_without_faking_success(
        source, monkeypatch, capsys, tmp_path, case):
    root, db = source
    seed(db, "SENT_UNVERIFIED", attempts=1, gmail_attempts=1)
    expected = probe.summary_from_database(root)
    monkeypatch.setattr(probe, "dashboard_root", lambda: tmp_path)
    monkeypatch.setattr(probe, "source_state",
                        lambda path: "LEGACY" if case == "legacy_source" else "TARGET")
    monkeypatch.setattr(probe, "control_root", lambda: root)
    if case == "missing_http":
        def broken(_):
            raise OSError("local path /Users/private must not leak")
        monkeypatch.setattr(probe, "local_dashboard_health", broken)
    else:
        response = dict(expected)
        if case == "wrong_http":
            response["manual_review_pending_count"] = 0
        monkeypatch.setattr(probe, "local_dashboard_health",
                            lambda path: {"manual_review_breakdown_available": True,
                                          "manual_review_breakdown_error": None, **response})
    assert probe.main() == 3
    output = json.loads(capsys.readouterr().out)
    assert output["operational_acceptance"].startswith("BLOCKED")
    assert "/Users/private" not in json.dumps(output)
    assert output["gmail_sent"] is False
    assert db.db.execute("SELECT status FROM decision_outbox").fetchone()[0] == "SENT_UNVERIFIED"


def test_missing_control_database_never_creates_sqlite_file(tmp_path):
    with pytest.raises(ValueError, match="CONTROL_SQLITE_UNAVAILABLE"):
        probe.summary_from_database(tmp_path)
    assert not (tmp_path / "mission-control.sqlite").exists()


def test_readonly_blocks_hidden_unknown_nonsuccess_with_even_matching_http(
        source, monkeypatch, capsys, tmp_path):
    root, db = source
    seed(db, "UNKNOWN_TERMINAL_ERROR", attempts=1, gmail_attempts=1)
    observed = probe.summary_from_database(root)
    assert observed["dashboard_hidden_nonsuccess_rows"] == 1
    monkeypatch.setattr(probe, "dashboard_root", lambda: tmp_path)
    monkeypatch.setattr(probe, "source_state", lambda path: "TARGET")
    monkeypatch.setattr(probe, "control_root", lambda: root)
    monkeypatch.setattr(probe, "local_dashboard_health",
                        lambda path: {"manual_review_breakdown_available": True,
                                      "manual_review_breakdown_error": None,
                                      **observed})
    assert probe.main() == 3
    report = json.loads(capsys.readouterr().out)
    assert report["operational_acceptance"] == "BLOCKED_DASHBOARD_HIDES_NONSUCCESS_ROWS"
    assert report["dashboard_hidden_nonsuccess_rows"] == 1


def test_readonly_explicitly_reports_legacy_schema_missing_fields(
        source, monkeypatch, capsys, tmp_path):
    root, db = source
    seed(db, "SENT_UNVERIFIED", attempts=1, gmail_attempts=1)
    monkeypatch.setattr(probe, "dashboard_root", lambda: tmp_path)
    monkeypatch.setattr(probe, "source_state", lambda path: "LEGACY")
    monkeypatch.setattr(probe, "control_root", lambda: root)
    monkeypatch.setattr(probe, "local_dashboard_health",
                        lambda path: {"manual_review_breakdown_available": True,
                                      "manual_review_breakdown_error": None,
                                      "manual_review_total_count": 0})
    assert probe.main() == 3
    report = json.loads(capsys.readouterr().out)
    assert report["operational_acceptance"] == "BLOCKED_BACKEND_SCHEMA_MISSING_FIELDS"
    assert "manual_review_blocked_count" in report["http_missing_count_fields"]
    assert "manual_review_pending_count" in report["http_missing_count_fields"]
    assert report["http_matches_sqlite"] is False


def test_independent_database_oracle_counts_terminal_and_blocked_outcomes(source):
    root, db = source
    seed(db, "PERMANENT_ERROR", attempts=1, gmail_attempts=1)
    seed(db, "CREDENTIAL_BLOCKED", attempts=0, gmail_attempts=0)
    seed(db, "SENT_UNVERIFIED", attempts=1, gmail_attempts=1)
    actual = probe.summary_from_database(root)
    assert actual["manual_review_total_count"] == 0
    assert actual["manual_review_actionable_count"] == 1
    assert actual["manual_review_pending_count"] == 1
    assert actual["manual_review_blocked_count"] == 1
    assert actual["manual_review_visible_total_count"] == 3
    assert actual["dashboard_hidden_nonsuccess_rows"] == 0


def test_mac_local_command_accepted_is_not_a_hidden_send_failure(source):
    # Local delivery success is COMMAND_ACCEPTED, as set in delivery.py.
    root, db = source
    seed(db, "COMMAND_ACCEPTED", channel="local",
         error=None, attempts=1)
    actual = probe.summary_from_database(root)
    assert actual["dashboard_hidden_nonsuccess_rows"] == 0
    assert actual["outbox_status_counts_by_channel"]["local/COMMAND_ACCEPTED"] == 1
    assert actual["manual_review_visible_total_count"] == 0
    assert actual["manual_review_pending_count"] == 0


def test_mac_status_groups_distinguish_success_and_unknown_and_do_not_leak_values(source):
    root, db = source
    for _ in range(16):
        seed(db, "COMMAND_ACCEPTED", channel="local", attempts=1)
    seed(db, "UNKNOWN_TERMINAL_ERROR", channel="gmail", attempts=1)
    seed(db, "CUSTOM_SECRET_abc@example.com", channel="local", attempts=1)
    result = probe.summary_from_database(root)
    assert result["outbox_status_counts_by_channel"]["local/COMMAND_ACCEPTED"] == 16
    assert result["outbox_status_counts_by_channel"]["gmail/UNKNOWN_TERMINAL_ERROR"] == 1
    assert result["outbox_status_counts_by_channel"]["local/NONSTANDARD_STATUS"] == 1
    assert "abc@example.com" not in str(result)
    assert result["dashboard_hidden_nonsuccess_rows"] == 2


def test_command_accepted_only_mac_probe_may_still_reject_legacy_backend(
        source, tmp_path, monkeypatch, capsys):
    root, db = source
    seed(db, "COMMAND_ACCEPTED", channel="local", attempts=1)
    monkeypatch.setattr(probe, "dashboard_root", lambda: tmp_path)
    monkeypatch.setattr(probe, "source_state", lambda path: "LEGACY")
    monkeypatch.setattr(probe, "control_root", lambda: root)
    monkeypatch.setattr(probe, "local_dashboard_health",
                        lambda path: {"status": "OK", "manual_review_total_count": 0})
    assert probe.main() == 3
    result = json.loads(capsys.readouterr().out)
    assert result["dashboard_hidden_nonsuccess_rows"] == 0
    assert result["outbox_status_counts_by_channel"] == {"local/COMMAND_ACCEPTED": 1}
    assert result["source_matches_target"] is False
    assert result["http_missing_count_fields"]
