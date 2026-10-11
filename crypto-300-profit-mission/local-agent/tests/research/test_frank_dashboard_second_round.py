"""PR33 second-round mandatory regression: real SQLite outbox status completeness.

No live Gmail, Mac services, user wallet, or production database.
"""
from __future__ import annotations

import json
import sqlite3

import pytest

from mission_agent.mission_control.delivery_review import summarize_manual_reviews
from mission_agent.mission_control.db import ControlDB
from mission_agent.mission_control.server import DashboardState
from test_delivery_review_integration import seed


@pytest.fixture
def store(tmp_path):
    prod = tmp_path / "prod"
    prod.mkdir()
    ctl = tmp_path / "control"
    ctl.mkdir()
    db = ControlDB(ctl / "mission-control.sqlite")
    (ctl / "mission-control-health.json").write_text(
        json.dumps({"status": "OK", "manual_review_total_count": 200}))
    dash = DashboardState(prod, ctl)
    yield db, dash
    db.close()


def test_real_sqlite_terminal_sent_identity_mismatch_is_actionable(store):
    db, dash = store
    seed(db, "PERMANENT_ERROR", error="MULTIPLE_SENT_IDENTITIES_REQUIRE_REVIEW",
         attempts=1, gmail_attempts=1)
    seed(db, "PERMANENT_ERROR", error="SENT_IDENTITY_OR_CONTENT_MISMATCH",
         attempts=1, gmail_attempts=1)
    result = dash.mission_control_health()
    assert result["manual_review_actionable_count"] == 2
    assert result["manual_review_actionable_gmail_count"] == 2
    assert result["manual_review_total_count"] == 0
    assert result["manual_review_pending_count"] == 0
    assert result["manual_review_visible_total_count"] == 2


def test_real_sqlite_blocked_credential_and_retry_states_visible(store):
    db, dash = store
    for status in ("CREDENTIAL_BLOCKED", "RETRYABLE_ERROR", "RETRY_PENDING"):
        seed(db, status, attempts=1, gmail_attempts=1)
    result = dash.mission_control_health()
    assert result["manual_review_blocked_count"] == 3
    assert result["manual_review_blocked_gmail_count"] == 3
    assert result["manual_review_actionable_count"] == 0
    assert result["manual_review_total_count"] == 0
    assert result["manual_review_visible_total_count"] == 3


def test_real_sqlite_review_oracle_all_statuses_no_double_count(store):
    db, dash = store
    for _ in range(15):
        seed(db)
    for error in ("UNCLEAR", "INDETERMINATE"):
        seed(db, "MANUAL_REVIEW", error=error, attempts=1, gmail_attempts=1)
    seed(db, "MANUAL_REVIEW", channel="webhook", error="UNKNOWN_CHANNEL")
    for status in ("SENDING", "SENT_UNVERIFIED", "SENT_UNVERIFIED"):
        seed(db, status, attempts=1, gmail_attempts=1)
    seed(db, "PERMANENT_ERROR", error="MULTIPLE_SENT_IDENTITIES_REQUIRE_REVIEW")
    seed(db, "PERMANENT_ERROR", error="SENT_IDENTITY_OR_CONTENT_MISMATCH")
    seed(db, "CREDENTIAL_BLOCKED")
    seed(db, "RETRY_PENDING")
    before = [tuple(r) for r in db.db.execute(
        "SELECT decision_id,channel,status,attempts FROM decision_outbox ORDER BY decision_id")]
    result = dash.mission_control_health()
    assert result["manual_review_expired_unsent_count"] == 15
    assert result["manual_review_actionable_count"] == 5
    assert result["manual_review_pending_count"] == 3
    assert result["manual_review_blocked_count"] == 2
    assert result["manual_review_total_count"] == 18
    assert result["manual_review_visible_total_count"] == 25
    assert result["manual_review_counts_stale"] is False
    assert sum(result[name] for name in (
        "manual_review_expired_unsent_count", "manual_review_actionable_count",
        "manual_review_pending_count", "manual_review_blocked_count")) == 25
    after = [tuple(r) for r in db.db.execute(
        "SELECT decision_id,channel,status,attempts FROM decision_outbox ORDER BY decision_id")]
    assert after == before


def test_true_legacy_counters_do_not_include_terminal_error(store):
    db, dash = store
    seed(db, "MANUAL_REVIEW", channel="gmail", attempts=0)
    seed(db, "PERMANENT_ERROR", channel="gmail", attempts=1)
    result = dash.mission_control_health()
    assert result["manual_review_total_count"] == 1
    assert result["manual_review_gmail_count"] == 1
    assert result["manual_review_actionable_count"] == 1
    assert result["manual_review_visible_total_count"] == 2


@pytest.mark.parametrize("channel", ["gmail", "local", "unsupported"])
def test_classifier_unknown_non_success_never_vanishes(channel):
    result = summarize_manual_reviews([
        {"channel": channel, "outbox_status": "UNEXPECTED_ERROR_STATE"}])
    assert result["manual_review_blocked_count"] == 1
    assert result["manual_review_visible_total_count"] == 1


def test_unreadable_control_db_stale_heartbeat_never_claims_live_status(store, tmp_path):
    db, dash = store
    db.close()
    dash.control_db = tmp_path / "missing.sqlite"
    result = dash.mission_control_health()
    assert result["manual_review_breakdown_available"] is False
    assert result["manual_review_counts_stale"] is True
    assert result["manual_review_breakdown_error"] == "CONTROL_DB_UNAVAILABLE"
