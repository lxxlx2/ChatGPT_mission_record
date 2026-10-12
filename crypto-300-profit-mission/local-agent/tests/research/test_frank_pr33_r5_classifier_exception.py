"""R5 classifier exception containment with actual SQLite and a live HTTP handler.

No production files, Gmail APIs, OAuth, real email or trading actions are used.
"""
from __future__ import annotations

import json
import threading
import urllib.request

import pytest

from mission_agent.mission_control.db import ControlDB
from mission_agent.mission_control import server as server_module
from mission_agent.mission_control.server import DashboardState, Handler, ThreadingHTTPServer
from test_delivery_review_integration import seed


@pytest.fixture
def db_dashboard(tmp_path):
    control = tmp_path / "control"
    control.mkdir()
    product = tmp_path / "product"
    product.mkdir()
    db = ControlDB(control / "mission-control.sqlite")
    (control / "mission-control-health.json").write_text(json.dumps({
        "status": "OK", "manual_review_total_count": 99,
        "manual_review_gmail_count": 99,
    }))
    yield db, DashboardState(product, control)
    db.close()


def raise_error(exc):
    def failing_classifier(_rows):
        raise exc
    return failing_classifier


@pytest.mark.parametrize("exc", [
    KeyError("private-decision-id"),
    ValueError("private-mailbox-value"),
    TypeError("private-internal-field"),
])
def test_classifier_exception_is_explicit_and_never_leaks_or_mutates(
        db_dashboard, monkeypatch, exc):
    db, dashboard = db_dashboard
    decision = seed(db, "SENT_UNVERIFIED", attempts=1, gmail_attempts=1)
    original = tuple(db.db.execute(
        "SELECT status,attempts FROM decision_outbox WHERE decision_id=?",
        (decision,)).fetchone())
    monkeypatch.setattr(server_module, "summarize_manual_reviews", raise_error(exc))
    got = dashboard.mission_control_health()
    assert got["status"] == "OK"
    assert got["manual_review_breakdown_available"] is False
    assert got["manual_review_breakdown_error"] == "DELIVERY_REVIEW_CLASSIFIER_ERROR"
    assert got["manual_review_counts_stale"] is True
    assert got["manual_review_total_count"] == 99
    assert "manual_review_pending_count" not in got
    assert "private-" not in json.dumps(got)
    assert tuple(db.db.execute(
        "SELECT status,attempts FROM decision_outbox WHERE decision_id=?",
        (decision,)).fetchone()) == original


@pytest.mark.parametrize("exc", [
    KeyError("private-email"), ValueError("private-credential")
])
def test_real_loopback_http_does_not_disconnect_on_classifier_failure(
        db_dashboard, monkeypatch, exc):
    db, dashboard = db_dashboard
    seed(db, "PENDING", error=None)
    monkeypatch.setattr(server_module, "summarize_manual_reviews", raise_error(exc))
    monkeypatch.setattr(Handler, "state", dashboard)
    srv = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    worker = threading.Thread(target=srv.serve_forever, daemon=True)
    worker.start()
    try:
        with urllib.request.urlopen(
            f"http://127.0.0.1:{srv.server_port}/api/control-health",
            timeout=4) as response:
            assert response.status == 200
            body = json.load(response)
        assert body["manual_review_breakdown_available"] is False
        assert body["manual_review_breakdown_error"] == "DELIVERY_REVIEW_CLASSIFIER_ERROR"
        assert body["manual_review_counts_stale"] is True
        assert "private-" not in json.dumps(body)
    finally:
        srv.shutdown()
        worker.join(timeout=5)
        srv.server_close()


def test_valid_classifier_still_surfaces_pending_and_expired(db_dashboard):
    db, dashboard = db_dashboard
    seed(db, "PENDING", error=None)
    seed(db, "MANUAL_REVIEW")
    response = dashboard.mission_control_health()
    assert response["manual_review_breakdown_available"] is True
    assert response["manual_review_breakdown_error"] is None
    assert response["manual_review_queued_count"] == 1
    assert response["manual_review_expired_unsent_count"] == 1
    assert response["manual_review_visible_total_count"] == 2
    assert response["manual_review_total_count"] == 1
