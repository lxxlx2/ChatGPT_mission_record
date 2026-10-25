"""Candidate-scoped budgets applied by the ORIGINAL one-child 3-slot replay.

All connections are in-process memory objects; zero RPC/WS/network.
"""
from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from f0_l2_d1_hard_stop_once import run_bounded_offline_once
import test_f0_l2_d1_bound_wire_rehearsal as bound_fixture


class D1CandidateActualBudgetTests(unittest.TestCase):
    def base(self):
        fixture = bound_fixture.BoundWireRehearsalTests(
            "test_candidate_bind_and_same_supervised_three_slot_ledger")
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        return fixture

    def test_d3_two_attempt_cap_is_applied_not_just_reported(self):
        f = self.base()
        candidate = dict(f.f.intent, max_total_attempts=2)
        output = f.rehearse(intent=candidate)["test_child"]
        self.assertEqual(output["effective_offline_scope"]["max_total"], 2)
        self.assertEqual(output["offline_child"]["reserved"], 2)
        self.assertEqual(output["offline_child"]["settled"], 2)
        self.assertEqual(output["offline_child"]["network_requests"], 0)
        self.assertEqual(output["audit"]["unknown_request_ids"], [])
        self.assertEqual(list(f.f.registry.iterdir()), [])

    def test_smaller_block_budget_and_slower_post_gap_are_real(self):
        f = self.base()
        candidate = dict(f.f.intent,
                         max_total_attempts=4, max_block_reads=1,
                         max_head_refreshes=1,
                         min_start_gap_ms=700,
                         head_ttl_ms=2500,
                         request_timeout_ms=1200,
                         max_dispatch_seconds=6)
        output = f.rehearse(intent=candidate, seconds=6)["test_child"]
        scope = output["effective_offline_scope"]
        self.assertEqual(scope["max_total"], 4)
        self.assertEqual(scope["max_blocks"], 1)
        self.assertEqual(scope["max_refreshes"], 1)
        self.assertEqual(scope["spacing_ms"], 700)
        self.assertEqual(scope["timeout_ms"], 1200)
        self.assertEqual(scope["head_ttl_ms"], 2500)
        self.assertEqual(scope["window_ms"], 5000)
        child = output["offline_child"]
        self.assertEqual(child["network_requests"], 0)
        self.assertLessEqual(child["reserved"], 4)
        self.assertLessEqual(child["block_attempts"], 1)
        self.assertLessEqual(child["head_refreshes"], 1)
        self.assertLessEqual(child["max_shared_slots"], 3)
        if child["min_actual_fake_start_gap_ms"] is not None:
            self.assertGreaterEqual(child["min_actual_fake_start_gap_ms"],
                                    698.5)
        self.assertEqual(output["audit"]["unknown_request_ids"], [])

    def test_invalid_test_scope_rejected_before_any_spent_marker(self):
        with tempfile.TemporaryDirectory(prefix="d1-budget-") as td:
            root = Path(td).resolve()
            registry, evidence = root / "registry", root / "evidence"
            registry.mkdir(mode=0o700)
            evidence.mkdir(mode=0o700)
            good = {
                "max_total": 6, "max_blocks": 3, "max_refreshes": 1,
                "spacing_ms": 250, "slots": 3, "head_ttl_ms": 4000,
                "window_ms": 5000, "timeout_ms": 5000,
            }
            for broken in (
                dict(good, max_total=7),
                dict(good, max_blocks=4),
                dict(good, max_refreshes=2),
                dict(good, spacing_ms=249),
                dict(good, slots=4),
                dict(good, max_total=True),
                dict(good, unexpected_scope=True),
                dict(good, window_ms=6000),
                dict(good, timeout_ms=5001),
            ):
                with self.subTest(broken=broken):
                    with self.assertRaisesRegex(ValueError,
                                                "OFFLINE_SCOPE"):
                        run_bounded_offline_once(
                            registry, evidence,
                            grant_id="d1-invalid-offline-scope-001",
                            permit_sha256="a" * 64,
                            offline_scope=broken, hard_seconds=8)
                    self.assertEqual(list(registry.iterdir()), [])
                    self.assertEqual(list(evidence.iterdir()), [])

    def test_scope_must_fit_hard_deadline_before_marker(self):
        with tempfile.TemporaryDirectory(prefix="d1-budget-") as td:
            root = Path(td).resolve()
            registry, evidence = root / "registry", root / "evidence"
            registry.mkdir(mode=0o700)
            evidence.mkdir(mode=0o700)
            scope = {
                "max_total": 2, "max_blocks": 1, "max_refreshes": 0,
                "spacing_ms": 250, "slots": 3, "head_ttl_ms": 1000,
                "window_ms": 5000, "timeout_ms": 1000,
            }
            with self.assertRaisesRegex(ValueError, "OUTLIVES_HARD_STOP"):
                run_bounded_offline_once(
                    registry, evidence,
                    grant_id="d1-too-short-hard-deadline-001",
                    permit_sha256="b" * 64,
                    offline_scope=scope, hard_seconds=2)
            self.assertEqual(list(registry.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
