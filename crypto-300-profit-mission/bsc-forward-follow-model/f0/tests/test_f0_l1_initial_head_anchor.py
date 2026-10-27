"""Budgeted initial HEAD block parent anchor: OFFLINE injected source only."""
import ast
from pathlib import Path
import tempfile
import unittest

import test_f0_l1_adaptive_source_core as existing


ROOT = Path(__file__).resolve().parents[1]


class InitialHeadAnchorTests(unittest.TestCase):
    def frames(self, root, frames, **kwargs):
        return existing.AdaptiveSourceCoreFakeTests.run_frames(
            self, root, frames, anchor_initial_head=True, **kwargs)

    def test_same_source_initial_head_anchor_is_one_extra_journaled_call(self):
        steps = [
            existing.chain(), existing.head(100), existing.block(100),
            existing.head(102), existing.block(101), existing.block(102),
        ]
        with tempfile.TemporaryDirectory() as d:
            r, calls = self.frames(Path(d), steps, total=6,
                                   head_cap=1, block_cap=2)
            self.assertEqual(len(calls), 6)
            self.assertEqual(r["total_attempts"], 6)
            self.assertEqual(r["initial_anchor_attempts"], 1)
            self.assertEqual(r["initial_anchor_height"], 100)
            self.assertTrue(r["initial_saved_block_parent_anchored"])
            self.assertEqual(r["verified_initial_parent_links"], 1)
            self.assertEqual(r["verified_internal_parent_links"], 1)
            self.assertEqual(r["block_read_attempts"], 2)
            self.assertEqual(r["block_read_successes"], 2)
            self.assertEqual(r["category_counts"]["INITIAL_ANCHOR"], 1)
            self.assertEqual(r["private_raw_archives"], 6)
            self.assertEqual(r["all_received_transactions"], 0)
            self.assertEqual(r["initial_anchor_evidence_scope"],
                             "SAME_SOURCE_NOT_CANONICAL_FINALITY_OR_INDEPENDENT_ANCHOR")
            self.assertEqual(r["external_real_rpc_calls"], "UNVERIFIED")
            self.assertFalse(r["candidate_control_eligible"])
            self.assertFalse(r["actual_e3"])

    def test_unavailable_initial_anchor_fails_without_future_block_retry(self):
        with tempfile.TemporaryDirectory() as d:
            r, calls = self.frames(
                Path(d), [existing.chain(), existing.head(100),
                          existing.null_block(100)],
                total=6, head_cap=1, block_cap=2)
            self.assertEqual(len(calls), 3)
            self.assertEqual(r["stop_state"], "INITIAL_ANCHOR_SOURCE_FAILED")
            self.assertEqual(r["initial_anchor_attempts"], 1)
            self.assertIsNone(r["initial_anchor_hash"])
            self.assertEqual(r["block_read_attempts"], 0)
            self.assertFalse(r["initial_saved_block_parent_anchored"])

    def test_wrong_anchor_returned_block_height_fails(self):
        invalid = existing.block(101)
        invalid["params"] = [hex(100), True]
        with tempfile.TemporaryDirectory() as d:
            r, calls = self.frames(
                Path(d), [existing.chain(), existing.head(100), invalid],
                total=6, head_cap=1, block_cap=2)
            self.assertEqual(len(calls), 3)
            self.assertEqual(r["stop_state"], "INITIAL_ANCHOR_INVALID")
            self.assertEqual(r["block_read_successes"], 0)
            self.assertIsNone(r["initial_anchor_height"])

    def test_wrong_first_future_parent_stops_and_never_marks_verified(self):
        steps = [
            existing.chain(), existing.head(100), existing.block(100),
            existing.head(101),
            existing.block(101, parent="0x" + "f" * 64),
        ]
        with tempfile.TemporaryDirectory() as d:
            r, calls = self.frames(Path(d), steps, total=5,
                                   head_cap=1, block_cap=1)
            self.assertEqual(len(calls), 5)
            self.assertEqual(r["stop_state"],
                             "CONSECUTIVE_BLOCK_PARENT_MISMATCH")
            self.assertEqual(r["verified_initial_parent_links"], 0)
            self.assertEqual(r["verified_internal_parent_links"], 0)
            self.assertFalse(r["initial_saved_block_parent_anchored"])
            self.assertEqual(r["block_read_successes"], 0)
            self.assertEqual(r["attempted_missing_heights"], [101])

    def test_gap_in_first_future_height_never_fabricates_anchor_to_later(self):
        steps = [
            existing.chain(), existing.head(100), existing.block(100),
            existing.head(102), existing.null_block(101), existing.block(102),
        ]
        with tempfile.TemporaryDirectory() as d:
            r, calls = self.frames(Path(d), steps, total=6,
                                   head_cap=1, block_cap=2)
            self.assertEqual(len(calls), 6)
            self.assertEqual(r["attempted_missing_heights"], [101])
            self.assertEqual(r["block_read_successes"], 1)
            self.assertEqual(r["verified_initial_parent_links"], 0)
            self.assertFalse(r["initial_saved_block_parent_anchored"])

    def test_default_legacy_sequence_has_no_extra_anchor_attempt(self):
        steps = [existing.chain(), existing.head(100),
                 existing.head(101), existing.block(101)]
        with tempfile.TemporaryDirectory() as d:
            r, calls = existing.AdaptiveSourceCoreFakeTests.run_frames(
                self, Path(d), steps, total=4, head_cap=1, block_cap=1)
            self.assertEqual(len(calls), 4)
            self.assertFalse(r["initial_anchor_requested"])
            self.assertEqual(r["initial_anchor_attempts"], 0)
            self.assertFalse(r["initial_saved_block_parent_anchored"])

    def test_bad_mode_and_insufficient_total_budget_fail_before_journal(self):
        for value, cap in ((1, 6), ("true", 6), (True, 2)):
            with self.subTest(value=value, total=cap):
                with tempfile.TemporaryDirectory() as d:
                    root = Path(d)
                    with self.assertRaisesRegex(
                            ValueError, "ADAPTIVE_ANCHOR_SCOPE_INVALID"):
                        existing.AdaptiveSourceCoreFakeTests.run_frames(
                            self, root, [], total=cap,
                            block_cap=1, anchor_initial_head=value)
                    self.assertFalse((root / "journal.json").exists())
                    self.assertFalse((root / "raw_responses").exists())

    def test_no_extra_transport_or_scheduler_import(self):
        tree = ast.parse((ROOT / "f0_l1_adaptive_source_core.py").read_text())
        roots = set()
        for item in ast.walk(tree):
            if isinstance(item, ast.Import):
                roots.update(n.name.split(".")[0] for n in item.names)
            elif isinstance(item, ast.ImportFrom) and item.module:
                roots.add(item.module.split(".")[0])
        self.assertFalse(roots & {
            "requests", "urllib", "ssl", "socket", "http",
            "aiohttp", "websocket", "subprocess", "threading",
        })


if __name__ == "__main__":
    unittest.main()
