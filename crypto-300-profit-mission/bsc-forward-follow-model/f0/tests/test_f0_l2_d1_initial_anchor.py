"""Existing single three-slot fake coordinator: one extra HEAD anchor RID, offline only."""
from hashlib import sha256
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from f0_l2_d1_coordinator import FakeSource, run_fake_concurrent


class SharedCoordinatorInitialAnchorTests(unittest.TestCase):
    def scenario(self, source=None, *, anchor=True, total=8,
                 blocks=3, refreshes=2, **options):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "private"
            root.mkdir(mode=0o700)
            if source is None:
                source = FakeSource(first_head=1000, growth_bps=10.0, delay_ms=5)
            with patch("http.client.HTTPSConnection",
                       side_effect=AssertionError("REAL_NETWORK_FORBIDDEN")) as ctor:
                report = run_fake_concurrent(
                    source, root, max_total=total, max_blocks=blocks,
                    max_refreshes=refreshes, spacing_ms=250, window_ms=8000,
                    head_min_poll_age_ms=250,
                    anchor_initial_head=anchor, **options)
                ctor.assert_not_called()
            log = [json.loads(row) for row in
                   (root / "attempts.jsonl").read_text().splitlines()]
            raw = {}
            for event in log:
                if "raw_name" in event:
                    payload = (root / "raw_responses" / event["raw_name"]).read_bytes()
                    self.assertEqual(sha256(payload).hexdigest(),
                                     event["raw_sha256"])
                    raw[event["id"]] = payload
            return report, log, raw

    def test_first_parent_plus_internal_link_separate_with_original_budget(self):
        report, log, raw = self.scenario()
        self.assertTrue(report["initial_anchor_requested"])
        self.assertEqual(report["initial_anchor_attempts"], 1)
        self.assertEqual(report["initial_anchor_height"],
                         report["source_head_samples"][0]["sampled_head"])
        self.assertTrue(report["initial_anchor_same_source_verified"])
        self.assertEqual(report["verified_initial_parent_links"], 1)
        self.assertTrue(report["first_parent_same_source_anchored"])
        self.assertFalse(report["first_parent_independently_anchored"])
        self.assertEqual(report["verified_internal_parent_links"],
                         report["contiguous_commits"] - 1)
        self.assertEqual(report["contiguous_commits"], blocks := 3)
        self.assertEqual(report["block_attempts"], blocks)
        self.assertEqual(report["reserved"], report["settled"])
        self.assertLessEqual(report["reserved"], 8)
        self.assertLessEqual(report["max_shared_slots"], 3)
        self.assertGreaterEqual(report["min_actual_fake_start_gap_ms"], 248.5)
        anchors = [e for e in log
                   if e.get("category") == "ANCHOR"]
        self.assertEqual(
            [e["event"] for e in anchors], ["RESERVE_UNKNOWN", "SETTLE"])
        self.assertEqual(anchors[0]["id"], anchors[1]["id"])
        self.assertEqual(anchors[0]["method"], "eth_getBlockByNumber")
        self.assertEqual(anchors[0]["height"], report["initial_anchor_height"])
        self.assertEqual(anchors[1]["state"], "RPC_RESPONSE")
        self.assertIn(anchors[1]["id"], raw)
        self.assertEqual(report["network_requests"], 0)
        self.assertFalse(report["real_user_grant_active"])
        self.assertEqual(report["f0_status"], "NOT_PASSED")

    def test_failed_anchor_stops_without_future_dispatch_or_retry(self):
        src = FakeSource(first_head=1000, growth_bps=10,
                         delay_ms=5, fail_block_ordinal=1)
        report, log, raw = self.scenario(source=src)
        self.assertEqual(report["stop"], "INITIAL_ANCHOR_FAILED")
        self.assertEqual(report["reserved"], 3)
        self.assertEqual(report["block_attempts"], 0)
        self.assertEqual(report["contiguous_commits"], 0)
        self.assertIsNone(report["initial_anchor_height"])
        self.assertFalse(report["initial_anchor_same_source_verified"])
        self.assertEqual(report["verified_initial_parent_links"], 0)
        self.assertEqual(src.block_count, 1)
        self.assertEqual(len([r for r in log
                              if r.get("event") == "RESERVE_UNKNOWN"
                              and r["category"] == "ANCHOR"]), 1)
        self.assertEqual(len(raw), 3)

    def test_bad_first_future_parent_never_claims_initial_link_or_commit(self):
        source = FakeSource(first_head=1000, growth_bps=10,
                            delay_ms=5, bad_parent_ordinal=2)
        r, rows, _ = self.scenario(source=source)
        self.assertEqual(r["stop"], "CHAIN_FAULT")
        self.assertEqual(r["bad_parent_height"], r["initial_anchor_height"]+1)
        self.assertEqual(r["verified_initial_parent_links"], 0)
        self.assertEqual(r["verified_internal_parent_links"], 0)
        self.assertFalse(r["first_parent_same_source_anchored"])
        self.assertEqual(r["contiguous_commits"], 0)
        self.assertTrue(any(e["event"] == "CHAIN_INTEGRITY_FAULT"
                            for e in rows))

    def test_three_attempt_total_cap_spent_by_identity_head_anchor(self):
        r, events, _ = self.scenario(total=3, blocks=1, refreshes=0)
        self.assertEqual(r["stop"], "TOTAL_BUDGET")
        self.assertEqual(r["reserved"], 3)
        self.assertEqual(r["initial_anchor_attempts"], 1)
        self.assertTrue(r["initial_anchor_same_source_verified"])
        self.assertEqual(r["block_attempts"], 0)
        self.assertEqual(r["contiguous_commits"], 0)
        self.assertEqual(len([x for x in events
                              if x["event"] == "RESERVE_UNKNOWN"]), 3)

    def test_default_disabled_does_not_add_fourth_identity_call(self):
        # Without the extra anchor, original max_total <= 2+blocks+HEADs.
        r, rows, _ = self.scenario(anchor=False, total=7)
        self.assertEqual(r["initial_anchor_attempts"], 0)
        self.assertFalse(r["initial_anchor_requested"])
        self.assertIsNone(r["initial_anchor_height"])
        self.assertEqual(r["verified_initial_parent_links"], 0)
        self.assertFalse(r["first_parent_same_source_anchored"])
        self.assertFalse(any(row.get("category") == "ANCHOR" for row in rows))

    def test_untrusted_source_and_invalid_anchor_flags_denied_before_journal(self):
        class ArbitrarySource:
            def reply(self, _req):
                raise AssertionError("SOURCE_MUST_NOT_BE_CALLED")
        for source, flag in (
            (ArbitrarySource(), True), (FakeSource(delay_ms=0), 1),
            (FakeSource(delay_ms=0), "true")
        ):
            with tempfile.TemporaryDirectory() as d:
                root = Path(d) / "private"
                root.mkdir(mode=0o700)
                with self.assertRaisesRegex(ValueError, "D1_SCOPE_INVALID"):
                    run_fake_concurrent(
                        source, root, max_total=3,
                        max_blocks=1, max_refreshes=0,
                        anchor_initial_head=flag)
                self.assertFalse((root/"attempts.jsonl").exists())
                self.assertFalse((root/"raw_responses").exists())

    def test_same_shared_gate_presend_unknown_before_fake_post(self):
        from f0_l2_d1_coordinator import FakeSource as ActualFake
        reply = ActualFake.reply
        captures = []
        def inspected_reply(source, request):
            captures.append(request["method"])
            return reply(source, request)
        with patch.object(ActualFake, "reply", inspected_reply):
            result, records, _ = self.scenario()
        self.assertEqual(result["reserved"], result["settled"])
        self.assertEqual(captures.count("eth_getBlockByNumber"),
                         result["block_attempts"]+1)
        for i, row in enumerate(records):
            if row["event"] == "SETTLE":
                earlier = records[:i]
                self.assertTrue(any(x["event"] == "RESERVE_UNKNOWN"
                                    and x["id"] == row["id"] for x in earlier))
        self.assertEqual(result["network_requests"], 0)


if __name__ == "__main__":
    unittest.main()
