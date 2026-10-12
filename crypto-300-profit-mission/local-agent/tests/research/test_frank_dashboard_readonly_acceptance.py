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
