"""Original foreground child supervisor + original anchored three-slot source, offline only."""
from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from f0_l2_d1_hard_stop_once import run_bounded_offline_once
from f0_l2_d1_recovery import reconcile_saved_attempts


def scoped(*, anchor=True, max_total=6):
    return {
        "max_total": max_total, "max_blocks": 3, "max_refreshes": 1,
        "spacing_ms": 250, "slots": 3, "head_ttl_ms": 4000,
        "window_ms": 5000, "timeout_ms": 5000,
        "anchor_initial_head": anchor,
    }


class AnchoredForegroundChildTests(unittest.TestCase):
    @staticmethod
    def roots(folder):
        reg = (Path(folder) / "private-test-registry").resolve()
        evidence = (Path(folder) / "private-evidence").resolve()
        reg.mkdir(mode=0o700)
        evidence.mkdir(mode=0o700)
        return reg, evidence

    def test_one_supervised_foreground_child_anchor_and_reconcile(self):
        with tempfile.TemporaryDirectory() as td:
            registry, evidence = self.roots(td)
            result = run_bounded_offline_once(
                registry, evidence,
                grant_id="d1-anchored-foreground-test-001",
                permit_sha256="a"*64,
                offline_scope=scoped(), hard_seconds=10.0)
            self.assertEqual(result["state"], "OFFLINE_CHILD_EXITED_ACCOUNTED")
            self.assertEqual(result["child_exit_code"], 0)
            self.assertEqual(result["live_network_requests"], 0)
            self.assertEqual(result["production"], "NO_GO")
            child = result["offline_child"]
            self.assertEqual(child["initial_anchor_attempts"], 1)
            self.assertTrue(child["initial_anchor_same_source_verified"])
            self.assertEqual(child["verified_initial_parent_links"], 1)
            self.assertTrue(child["first_parent_same_source_anchored"])
            self.assertFalse(child["first_parent_independently_anchored"])
            self.assertGreaterEqual(child["contiguous_commits"], 1)
            self.assertEqual(child["verified_internal_parent_links"],
                             child["contiguous_commits"]-1)
            self.assertLessEqual(child["reserved"], 6)
            self.assertEqual(child["reserved"], child["settled"])
            self.assertLessEqual(child["max_shared_slots"], 3)
            self.assertGreaterEqual(child["min_actual_fake_start_gap_ms"], 248)
            recovery = result["audit"]
            self.assertEqual(recovery["audit_status"], "OFFLINE_ACCOUNTED_NOT_LIVE")
            self.assertEqual(recovery["initial_anchor_attempts"], 1)
            self.assertTrue(recovery["initial_anchor_raw_verified"])
            self.assertEqual(recovery["verified_initial_parent_links"], 1)
            self.assertEqual(recovery["verified_internal_parent_links"],
                             recovery["contiguous_commits"]-1)
            self.assertFalse(recovery["first_parent_independently_anchored"])
            self.assertEqual(recovery["unknown_request_ids"], [])
            self.assertEqual(recovery["network_retries"], 0)
            self.assertEqual(reconcile_saved_attempts(evidence),recovery)
            self.assertEqual(len(list(registry.glob("*.consumed.json"))), 1)
            second = (Path(td)/"retry-evidence").resolve()
            second.mkdir(mode=0o700)
            with self.assertRaisesRegex(ValueError, "ALREADY_CONSUMED"):
                run_bounded_offline_once(
                    registry, second,
                    grant_id="d1-anchored-foreground-test-001",
                    permit_sha256="a"*64,
                    offline_scope=scoped(), hard_seconds=10.0)
            self.assertFalse((second/"attempts.jsonl").exists())

    def test_explicit_legacy_default_no_anchor_has_no_extra_request(self):
        with tempfile.TemporaryDirectory() as td:
            registry,evidence=self.roots(td)
            result=run_bounded_offline_once(
                registry,evidence,
                grant_id="d1-unanchored-foreground-test-002",
                permit_sha256="b"*64,
                offline_scope=scoped(anchor=False),hard_seconds=10.0)
            self.assertEqual(result["state"],"OFFLINE_CHILD_EXITED_ACCOUNTED")
            self.assertEqual(result["live_network_requests"],0)
            self.assertFalse(result["offline_child"]["initial_anchor_requested"])
            self.assertEqual(result["offline_child"]["initial_anchor_attempts"],0)
            self.assertFalse(result["audit"]["first_parent_same_source_anchored"])

    def test_bad_anchor_scope_fails_before_spending_test_nonce(self):
        for label,scope in (
            ("non_bool", dict(scoped(),anchor_initial_head=1)),
            ("too_many",scoped(max_total=7)),
            ("unknown",dict(scoped(),unreviewed_live=True)),
            ("too_few",dict(scoped(),max_total=2)),
        ):
            with self.subTest(label=label):
                with tempfile.TemporaryDirectory() as td:
                    registry,evidence=self.roots(td)
                    with self.assertRaisesRegex(ValueError, "D1_CHILD_"):
                        run_bounded_offline_once(
                            registry,evidence, grant_id="d1-reject-"+label,
                            permit_sha256="c"*64,offline_scope=scope,
                            hard_seconds=10.0)
                    self.assertEqual(list(registry.iterdir()),[])
                    self.assertFalse((evidence/"attempts.jsonl").exists())

    def test_child_hard_kill_preserves_original_unknown_and_no_retry(self):
        with tempfile.TemporaryDirectory() as td:
            registry,evidence=self.roots(td)
            r=run_bounded_offline_once(
                registry,evidence,
                grant_id="d1-anchored-hang-test-003",
                permit_sha256="d"*64,
                offline_scope=scoped(),
                scenario="hang_after_reserve",
                hard_seconds=2.0)
            self.assertEqual(r["state"],"HARD_STOP_KILLED_NO_RETRY")
            self.assertEqual(r["live_network_requests"],0)
            self.assertTrue(r["no_automatic_retry"])
            self.assertEqual(r["audit"]["audit_status"],
                             "INVALID_FOR_PERFORMANCE_CLAIM")
            self.assertGreaterEqual(len(r["audit"]["unknown_request_ids"]),1)
            self.assertEqual(len(list(registry.glob("*.consumed.json"))),1)
            self.assertFalse(r["audit"]["first_parent_same_source_anchored"])


if __name__=="__main__":
    unittest.main()
