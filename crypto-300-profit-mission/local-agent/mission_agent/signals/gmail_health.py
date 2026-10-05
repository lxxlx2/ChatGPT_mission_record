"""Local outbox observability only. Never checks credentials or calls Gmail."""

def health_from_summary(summary):
    if summary['failed']:status='FAILED'
    elif summary['sent_unverified']:status='SENT_UNVERIFIED'
    elif summary['blocked']:status='BLOCKED'
    elif summary['pending']:status='PENDING'
    else:status='LIVE'
    return dict(email_delivery_status=status,gmail_pending=summary['pending'],
                gmail_sent_verified=summary['sent_verified'],gmail_sent_unverified=summary['sent_unverified'],
                gmail_blocked=summary['blocked'],gmail_failed=summary['failed'])
