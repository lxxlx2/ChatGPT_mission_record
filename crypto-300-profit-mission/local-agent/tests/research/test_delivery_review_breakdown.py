"""Regression tests for the read-only Mission Control review badge breakdown."""
import importlib.util
from pathlib import Path
import unittest

MODULE = Path(__file__).resolve().parents[2] / "mission_agent" / "mission_control" / "delivery_review.py"
spec = importlib.util.spec_from_file_location("delivery_review", MODULE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def example(channel="gmail", **kwargs):
    row = dict(channel=channel, last_error=mod.GMAIL_EXPIRED_BEFORE_SEND,
               gmail_status="MANUAL_REVIEW", local_status=None,
               outbox_attempts=0, gmail_attempts=0,
               sent_at=None, gmail_message_id=None, local_delivered_at=None)
    row.update(kwargs)
    return row


class DeliveryReviewClassificationTests(unittest.TestCase):
    def test_fifteen_unattempted_expired_are_historical(self):
        summary = mod.summarize_manual_reviews([example() for _ in range(15)])
        self.assertEqual(summary["manual_review_expired_unsent_gmail_count"], 15)
        self.assertEqual(summary["manual_review_actionable_count"], 0)

    def test_uncertain_send_never_classified_as_harmless_history(self):
        rows = [example(gmail_attempts=1), example(gmail_message_id="api-id"),
                example(sent_at="2026-10-11T12:00Z"),
                example(last_error="GMAIL_SENT_OUTCOME_UNRESOLVED_TOO_LONG"),
                example(gmail_status="SENT_UNVERIFIED"), example(outbox_attempts=1)]
        self.assertEqual(mod.summarize_manual_reviews(rows)["manual_review_actionable_gmail_count"], 6)

    def test_expired_local_and_ambiguous_local(self):
        rows = [example("local", last_error=mod.LOCAL_EXPIRED_BEFORE_SEND, local_status="MANUAL_REVIEW"),
                example("local", last_error=mod.LOCAL_EXPIRED_BEFORE_SEND,
                        local_status="MANUAL_REVIEW", local_delivered_at="already"),
                example("local", last_error="OTHER")]
        s = mod.summarize_manual_reviews(rows)
        self.assertEqual(s["manual_review_expired_unsent_local_count"], 1)
        self.assertEqual(s["manual_review_actionable_local_count"], 2)

    def test_empty(self):
        s = mod.summarize_manual_reviews([])
        self.assertTrue(s["manual_review_breakdown_available"])
        self.assertEqual(s["manual_review_expired_unsent_count"], 0)
        self.assertEqual(s["manual_review_actionable_count"], 0)

    def test_missing_or_inconsistent_delivery_fails_closed(self):
        rows = [example(gmail_attempts="invalid"), example(gmail_status=None),
                example(last_error=None), example(outbox_attempts="invalid")]
        self.assertEqual(mod.summarize_manual_reviews(rows)["manual_review_actionable_gmail_count"], 4)

    def test_aggregate_consistency(self):
        rows = [example(), example(),
                example("local", last_error=mod.LOCAL_EXPIRED_BEFORE_SEND, local_status="MANUAL_REVIEW"),
                example(last_error="SENT_UNVERIFIED")]
        s = mod.summarize_manual_reviews(rows)
        self.assertEqual(s["manual_review_expired_unsent_count"], 3)
        self.assertEqual(s["manual_review_actionable_count"], 1)
        self.assertEqual(s["manual_review_expired_unsent_count"]+s["manual_review_actionable_count"], len(rows))


if __name__ == "__main__":
    unittest.main()
