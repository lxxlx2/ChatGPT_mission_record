"""Third independent review regression: never hide old unsent PENDING or channel mismatches.

This is isolated real ControlDB/SQLite & DashboardState; does not send mail.
"""
from __future__ import annotations

import json

import pytest

from mission_agent.mission_control.db import ControlDB
from mission_agent.mission_control.server import DashboardState
from test_delivery_review_integration import seed


@pytest.fixture
def state(tmp_path):
    prod = tmp_path / "prod"
    prod.mkdir()
    ctl = tmp_path / "control"
    ctl.mkdir()
    db = ControlDB(ctl / "mission-control.sqlite")
    (ctl / "mission-control-health.json").write_text(
        json.dumps({"status": "OK", "manual_review_total_count": 17}))
    dashboard = DashboardState(prod, ctl)
    yield db, dashboard
    db.close()


@pytest.mark.parametrize("channel", ["gmail", "local", "future-channel"])
def test_expired_pending_is_visible_and_not_reclassified_as_sent(state, channel):
    db, dashboard = state
    decision = seed(db, "PENDING", channel=channel, attempts=0,
                    error=None, gmail_attempts=0)
    original = tuple(db.db.execute(
        "SELECT status,attempts FROM decision_outbox WHERE decision_id=?",
        (decision,)).fetchone())
    summary = dashboard.mission_control_health()
    assert summary["manual_review_queued_count"] == 1
    assert summary["manual_review_queued_" +
                   (channel if channel in ("gmail", "local") else "other") +
                   "_count"] == 1
    assert summary["manual_review_pending_count"] == 0
    assert summary["manual_review_total_count"] == 0
    assert summary["manual_review_visible_total_count"] == 1
    assert tuple(db.db.execute(
        "SELECT status,attempts FROM decision_outbox WHERE decision_id=?",
        (decision,)).fetchone()) == original


@pytest.mark.parametrize("channel,status", [
    ("gmail", "COMMAND_ACCEPTED"),
    ("local", "SENT_VERIFIED"),
    ("gmail", "DELIVERED"),
    ("webhook", "DRY_RUN_AUDIT"),
])
def test_channel_mismatched_status_is_not_silently_whitelisted(
        state, channel, status):
    db, dashboard = state
    seed(db, status, channel=channel, attempts=1)
    summary = dashboard.mission_control_health()
    assert summary["manual_review_visible_total_count"] == 1
    assert summary["manual_review_blocked_count"] == 1
    assert summary["manual_review_total_count"] == 0


@pytest.mark.parametrize("channel,status", [
    ("local", "COMMAND_ACCEPTED"),
    ("gmail", "SENT_VERIFIED"),
    ("local", "DRY_RUN_AUDIT"),
    ("gmail", "DRY_RUN_AUDIT"),
])
def test_known_success_status_pairs_remain_excluded(state, channel, status):
    db, dashboard = state
    seed(db, status, channel=channel, attempts=1)
    summary = dashboard.mission_control_health()
    assert summary["manual_review_visible_total_count"] == 0
    assert summary["manual_review_queued_count"] == 0
    assert summary["manual_review_blocked_count"] == 0


def test_old_pending_and_manual_history_do_not_double_count(state):
    db, dashboard = state
    seed(db, "PENDING", channel="gmail", error=None)
    seed(db, "PENDING", channel="local", error=None)
    seed(db, "MANUAL_REVIEW", channel="gmail")
    seed(db, "PERMANENT_ERROR", channel="gmail", attempts=1)
    seed(db, "COMMAND_ACCEPTED", channel="local", attempts=1)
    got = dashboard.mission_control_health()
    assert got["manual_review_total_count"] == 1
    assert got["manual_review_expired_unsent_count"] == 1
    assert got["manual_review_queued_count"] == 2
    assert got["manual_review_actionable_count"] == 1
    assert got["manual_review_visible_total_count"] == 4
    assert got["manual_review_queued_count"] + got["manual_review_pending_count"] + (
        got["manual_review_actionable_count"] +
        got["manual_review_expired_unsent_count"] +
        got["manual_review_blocked_count"]) == 4
