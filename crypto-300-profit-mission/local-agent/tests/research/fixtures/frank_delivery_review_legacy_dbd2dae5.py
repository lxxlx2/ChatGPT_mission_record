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
    actionable = {"gmail": 0, "local": 0}
    for row in rows:
        channel = row.get("channel")
        if channel not in historical:
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
    }
