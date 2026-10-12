"""Read-only presentation of historic expired Frank notices vs manual work.

The authoritative outbox and frozen Gmail send/verification states are unchanged.
"""

GMAIL_EXPIRED_BEFORE_SEND = "GMAIL_DECISION_STALE_OR_TIME_UNVERIFIED_BEFORE_SEND"
LOCAL_EXPIRED_BEFORE_SEND = "LOCAL_DECISION_STALE_OR_TIME_UNVERIFIED_BEFORE_SEND"


def summarize_manual_reviews(rows):
    """Split immutable MANUAL_REVIEW records into clearly labeled UI buckets.

    Unknown channels, missing receipts, or ambiguous send attempts never enter
    the harmless historical-expiry bucket and remain actionable for review.
    """
    historical = {"gmail": 0, "local": 0}
    actionable = {"gmail": 0, "local": 0, "other": 0}
    pending = {"gmail": 0, "local": 0, "other": 0}
    queued = {"gmail": 0, "local": 0, "other": 0}
    blocked = {"gmail": 0, "local": 0, "other": 0}
    manual_total = 0
    manual_channels = {"gmail": 0, "local": 0, "other": 0}
    for row in rows:
        channel = row.get("channel")
        channel = channel if channel in ("gmail", "local") else "other"
        # A send may already have taken place. Until Sent readback verifies it,
        # show a distinct pending outcome bucket; this does not authorize retry.
        status = row.get("outbox_status", "MANUAL_REVIEW")
        if status in ("SENDING", "SENT_UNVERIFIED"):
            pending[channel] += 1
            continue
        if status == "PENDING":
            # This has not reached the send attempt yet. In particular an old
            # PENDING must NOT disappear from Dashboard/acceptance. Visibility
            # does not authorize retry, expiry or any send-side transition.
            queued[channel] += 1
            continue
        if status in ("CREDENTIAL_BLOCKED", "RETRYABLE_ERROR", "RETRY_PENDING"):
            blocked[channel] += 1
            continue
        if status == "PERMANENT_ERROR":
            actionable[channel] += 1
            continue
        if status != "MANUAL_REVIEW":
            # Unknown non-success states must never be silently thrown away.
            blocked[channel] += 1
            continue
        manual_total += 1
        manual_channels[channel] += 1
        if channel == "other":
            actionable["other"] += 1
            continue
        try:
            outbox_attempts = int(row.get("outbox_attempts") or 0)
            gmail_attempts = int(row.get("gmail_attempts") or 0)
        except (ValueError, TypeError, OverflowError):
            actionable[channel] += 1
            continue
        if channel == "gmail":
            expired_unsent = (
                row.get("last_error") == GMAIL_EXPIRED_BEFORE_SEND
                and row.get("gmail_status") == "MANUAL_REVIEW"
                and outbox_attempts == 0 and gmail_attempts == 0
                and not row.get("sent_at") and not row.get("gmail_message_id")
            )
        else:
            expired_unsent = (
                row.get("last_error") == LOCAL_EXPIRED_BEFORE_SEND
                and row.get("local_status") == "MANUAL_REVIEW"
                and outbox_attempts == 0
                and not row.get("local_delivered_at")
            )
        target = historical if expired_unsent else actionable
        target[channel] += 1
    return {
        "manual_review_breakdown_available": True,
        "manual_review_expired_unsent_count": sum(historical.values()),
        "manual_review_expired_unsent_gmail_count": historical["gmail"],
        "manual_review_expired_unsent_local_count": historical["local"],
        "manual_review_actionable_count": sum(actionable.values()),
        "manual_review_actionable_gmail_count": actionable["gmail"],
        "manual_review_actionable_local_count": actionable["local"],
        "manual_review_actionable_other_count": actionable["other"],
        "manual_review_manual_only_total_count": manual_total,
        "manual_review_manual_only_gmail_count": manual_channels["gmail"],
        "manual_review_manual_only_local_count": manual_channels["local"],
        "manual_review_manual_only_other_count": manual_channels["other"],
        "manual_review_blocked_count": sum(blocked.values()),
        "manual_review_blocked_gmail_count": blocked["gmail"],
        "manual_review_blocked_local_count": blocked["local"],
        "manual_review_blocked_other_count": blocked["other"],
        "manual_review_pending_count": sum(pending.values()),
        "manual_review_pending_gmail_count": pending["gmail"],
        "manual_review_pending_local_count": pending["local"],
        "manual_review_pending_other_count": pending["other"],
        "manual_review_queued_count": sum(queued.values()),
        "manual_review_queued_gmail_count": queued["gmail"],
        "manual_review_queued_local_count": queued["local"],
        "manual_review_queued_other_count": queued["other"],
        "manual_review_visible_total_count": (
            sum(historical.values()) + sum(actionable.values())
            + sum(pending.values()) + sum(queued.values()) + sum(blocked.values())
        ),
    }
