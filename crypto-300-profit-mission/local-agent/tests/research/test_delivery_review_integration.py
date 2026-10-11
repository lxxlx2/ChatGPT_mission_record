"""Real SQLite and real DashboardState tests: no Gmail, no network, no production writes."""
from __future__ import annotations

import json

import pytest

from mission_agent.mission_control.db import ControlDB
from mission_agent.mission_control.server import DashboardState


def seed(control, state="MANUAL_REVIEW", *, channel="gmail",
         error="GMAIL_DECISION_STALE_OR_TIME_UNVERIFIED_BEFORE_SEND",
         attempts=0, gmail_attempts=0, sent_at=None, message_id=None):
    db = control.db
    index = db.execute("SELECT COUNT(*) FROM decision_events").fetchone()[0]
    decision = f"review-{index}"
    snapshot = f"snapshot-{index}"
    now = "2026-10-11T12:00:00Z"
    db.execute(
        "INSERT INTO decision_snapshots (snapshot_id,person_id,mint,"
        "source_signal_type,decision,policy_id,policy_hash,input_hash,"
        "created_at,body) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (snapshot,"frank",f"mint-{index}","MULTIPLE","BUY","frozen",
         "hash",f"input-{index}",now,"{}"))
    db.execute(
        "INSERT INTO decision_events (decision_id,person_id,mint,"
        "snapshot_id,decision,created_at,content_hash,body) "
        "VALUES (?,?,?,?,?,?,?,?)",
        (decision,"frank",f"mint-{index}",snapshot,"BUY",now,"content","{}"))
    db.execute(
        "INSERT INTO decision_outbox (decision_id,channel,status,attempts,"
        "content_hash,created_at,last_error) VALUES (?,?,?,?,?,?,?)",
        (decision,channel,state,attempts,"content",now,error))
    if channel == "gmail":
        db.execute(
            "INSERT INTO gmail_delivery (decision_id,delivery_mode,delivery_forbidden,"
            "subject,body,content_hash,wire_message_id,status,attempt_count,"
            "created_at,sent_at,gmail_message_id) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (decision,"LIVE",0,"subj","body","content",
             f"<{decision}@local.invalid>",state,gmail_attempts,now,sent_at,message_id))
    elif channel == "local":
        db.execute(
            "INSERT INTO local_delivery (decision_id,status,content_hash,created_at) "
            "VALUES (?,?,?,?)", (decision,state,"content",now))
    return decision


@pytest.fixture
def store(tmp_path):
    prod = tmp_path / "prod"
    prod.mkdir()
    ctl = tmp_path / "control"
    ctl.mkdir()
    db = ControlDB(ctl / "mission-control.sqlite")
    (ctl / "mission-control-health.json").write_text(json.dumps({
        "status":"OK","manual_review_total_count":1,
        "manual_review_gmail_count":1,"manual_review_local_count":0
    }))
    dash = DashboardState(prod,ctl)
    yield db,dash
    db.close()


def test_three_uncertain_sends_are_visible_from_actual_sqlite(store):
    db,dash = store
    seed(db, "SENDING", attempts=1,gmail_attempts=1)
    seed(db, "SENT_UNVERIFIED",attempts=1,gmail_attempts=1)
    seed(db, "SENT_UNVERIFIED",attempts=1,gmail_attempts=1,sent_at="bad-date")
    got=dash.mission_control_health()
    assert got["manual_review_pending_count"] == 3
    assert got["manual_review_pending_gmail_count"] == 3
    assert got["manual_review_visible_total_count"] == 3
    assert got["manual_review_total_count"] == 0
    assert got["manual_review_breakdown_error"] is None


def test_expired_one_plus_pending_three_visible_four_legacy_one(store):
    db,dash=store
    seed(db)
    for state in ("SENDING","SENT_UNVERIFIED","SENT_UNVERIFIED"):
        seed(db,state,attempts=1,gmail_attempts=1)
    result=dash.mission_control_health()
    assert result["manual_review_expired_unsent_count"] == 1
    assert result["manual_review_pending_count"] == 3
    assert result["manual_review_total_count"] == 1
    assert result["manual_review_visible_total_count"] == 4


def test_unknown_channel_is_not_discarded(store):
    db,dash=store
    seed(db,channel="unknown-channel",error="uncertain")
    got=dash.mission_control_health()
    assert got["manual_review_actionable_other_count"] == 1
    assert got["manual_review_visible_total_count"] == 1


def test_nonexistent_database_returns_explicit_error(store):
    db,dash=store
    db.close()
    dash.control_db = dash.control_db.with_name("missing.sqlite")
    got=dash.mission_control_health()
    assert got["manual_review_breakdown_available"] is False
    assert got["manual_review_breakdown_error"] == "CONTROL_DB_UNAVAILABLE"


def test_corrupted_database_returns_error_instead_of_zero(store,tmp_path):
    db,dash=store
    db.close()
    bad=tmp_path/"broken.sqlite"
    bad.write_bytes(b"not a database")
    dash.control_db=bad
    got=dash.mission_control_health()
    assert got["manual_review_breakdown_available"] is False
    assert got["manual_review_breakdown_error"]


def test_dashboard_read_is_nonmutating_and_does_not_change_send_state(store):
    db,dash=store
    key=seed(db,"SENT_UNVERIFIED",attempts=1,gmail_attempts=1)
    before=db.db.execute("SELECT status,attempts FROM decision_outbox WHERE decision_id=?",(key,)).fetchone()
    for _ in range(2):
        dash.mission_control_health()
    after=db.db.execute("SELECT status,attempts FROM decision_outbox WHERE decision_id=?",(key,)).fetchone()
    assert tuple(before)==tuple(after)==("SENT_UNVERIFIED",1)


def test_real_sqlite_breakdown_is_not_a_self_consistency_identity(store):
    db,dash=store
    seed(db,"SENT_UNVERIFIED",attempts=1,gmail_attempts=1)
    seed(db,"MANUAL_REVIEW",error="MANUAL_CONSENT_REQUIRED",attempts=2,gmail_attempts=2)
    got=dash.mission_control_health()
    counts=db.db.execute(
        "SELECT status,COUNT(*) FROM decision_outbox GROUP BY status").fetchall()
    actual=dict(counts)
    assert got["manual_review_pending_count"] == actual["SENT_UNVERIFIED"]
    assert got["manual_review_total_count"] == actual["MANUAL_REVIEW"]
    assert got["manual_review_visible_total_count"] == sum(actual.values())
