"""The old manual-review queue remains immutable; dismissal is UI-only."""
from pathlib import Path

from mission_agent.mission_control.delivery_review import summarize_manual_reviews
from mission_agent.mission_control import server


def row(decision_id, *, channel="gmail", attempts=0, gmail_attempts=0,
        error="GMAIL_DECISION_STALE_OR_TIME_UNVERIFIED_BEFORE_SEND",
        status="MANUAL_REVIEW", receipt=None):
    return dict(
        decision_id=decision_id, channel=channel, outbox_status=status,
        outbox_attempts=attempts, gmail_attempts=gmail_attempts,
        gmail_status="MANUAL_REVIEW", local_status=None, last_error=error,
        sent_at=receipt, gmail_message_id=None, local_delivered_at=None,
    )


def test_fingerprint_is_stable_for_the_exact_unsent_history_not_just_count():
    old = [row("historical-1"), row("historical-2")]
    first = summarize_manual_reviews(old)
    same = summarize_manual_reviews(list(reversed(old)))
    replaced = summarize_manual_reviews([row("historical-1"), row("NEW-2")])
    assert first["manual_review_expired_unsent_count"] == 2
    assert first["manual_review_expired_unsent_fingerprint"] == same["manual_review_expired_unsent_fingerprint"]
    assert replaced["manual_review_expired_unsent_count"] == 2
    assert replaced["manual_review_expired_unsent_fingerprint"] != first["manual_review_expired_unsent_fingerprint"]
    assert len(first["manual_review_expired_unsent_fingerprint"]) == 64
    assert "historical-1" not in first["manual_review_expired_unsent_fingerprint"]


def test_sent_attempts_pending_unknown_or_missing_ids_cannot_be_silenced():
    rows = [
        row("real-expired"),
        row("attempted", attempts=1),
        row("receipt", receipt="2026-10-22T01:00Z"),
        row("sending", status="SENT_UNVERIFIED"),
    ]
    result = summarize_manual_reviews(rows)
    assert result["manual_review_expired_unsent_count"] == 1
    assert result["manual_review_actionable_count"] == 2
    assert result["manual_review_pending_count"] == 1
    no_id = summarize_manual_reviews([row(None)])
    assert no_id["manual_review_expired_unsent_count"] == 1
    assert no_id["manual_review_expired_unsent_fingerprint"] is None
    assert summarize_manual_reviews([])["manual_review_expired_unsent_fingerprint"] is None


def test_current_dashboard_still_reads_ro_and_only_browser_acks_without_posts():
    source = Path(server.__file__).read_text()
    js = (Path(server.__file__).parent / "static" / "app.js").read_text()
    review = Path(server.__file__).parent / "delivery_review.py"
    assert review.is_file()
    assert "SELECT o.decision_id, o.channel" in source
    assert "open_control_ro(self.control_db)" in source
    assert "manual_review_expired_unsent_fingerprint" in js
    assert "localStorage.setItem('frank.expired-review.ack.v1',fingerprint)" in js
    assert "localStorage.removeItem('frank.expired-review.ack.v1')" in js
    assert "data-review-expiry=\"hide\"" in js
    assert "data-review-expiry=\"show\"" in js
    assert "get('/api/control-health')" in js
    assert "setInterval(refresh,5000)" in js
