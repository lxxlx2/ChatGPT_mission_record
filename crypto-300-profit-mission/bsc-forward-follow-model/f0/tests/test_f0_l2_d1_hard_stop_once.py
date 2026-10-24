"""D1 hard OS deadline for the exact offline three-slot + HTTPS seam."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from f0_l2_d1_hard_stop_once import run_bounded_offline_once, send_live


class D1HardStopOnceTests(unittest.TestCase):
    def roots(self, folder):
        reg = Path(folder) / "registry"
        out = Path(folder) / "private-evidence"
        reg.mkdir(mode=0o700)
        out.mkdir(mode=0o700)
        return reg, out

    def test_success_is_fully_accounted_one_use_with_no_real_network(self):
        with tempfile.TemporaryDirectory() as td:
            registry, evidence = self.roots(td)
            report = run_bounded_offline_once(
                registry, evidence, grant_id="d1-hard-stop-test-001",
                permit_sha256="a"*64, hard_seconds=10.0)
            self.assertEqual(report["state"], "OFFLINE_CHILD_EXITED_ACCOUNTED")
            self.assertEqual(report["child_exit_code"], 0)
            self.assertEqual(report["live_network_requests"], 0)
            self.assertTrue(report["no_automatic_retry"])
            self.assertFalse(report["real_d2_approved"])
            self.assertFalse(report["real_d3_approved"])
            self.assertEqual(report["production"], "NO_GO")
            child = report["offline_child"]
            self.assertIsNotNone(child)
            self.assertEqual(child["network_requests"], 0)
            self.assertEqual(child["reserved"], child["settled"])
            self.assertLessEqual(child["max_shared_slots"], 3)
            self.assertLessEqual(child["reserved"], 6)
            self.assertGreaterEqual(child["min_actual_fake_start_gap_ms"], 248.5)
            self.assertEqual(report["audit"]["network_retries"], 0)
            self.assertEqual(report["audit"]["unknown_request_ids"], [])
            self.assertTrue((evidence / "attempts.jsonl").is_file())
            self.assertEqual(
                (evidence / "attempts.jsonl").stat().st_mode & 0o077, 0)
            self.assertEqual(len(list(registry.glob("*.consumed.json"))), 1)
            second_evidence = Path(td) / "second-evidence"
            second_evidence.mkdir(mode=0o700)
            with self.assertRaisesRegex(ValueError, "ALREADY_CONSUMED"):
                run_bounded_offline_once(
                    registry, second_evidence,
                    grant_id="d1-hard-stop-test-001",
                    permit_sha256="a"*64, hard_seconds=10.0)
            self.assertFalse((second_evidence / "attempts.jsonl").exists())

    def test_hard_deadline_kills_child_preserves_unknown_and_spent_grant(self):
        with tempfile.TemporaryDirectory() as td:
            registry, evidence = self.roots(td)
            report = run_bounded_offline_once(
                registry, evidence, grant_id="d1-hard-stop-test-002",
                permit_sha256="b"*64, scenario="hang_after_reserve",
                hard_seconds=2.0)
            self.assertEqual(report["state"], "HARD_STOP_KILLED_NO_RETRY")
            self.assertNotEqual(report["child_exit_code"], 0)
            self.assertLess(report["elapsed_s"], 4.0)
            self.assertTrue(report["no_automatic_retry"])
            self.assertTrue((evidence / "attempts.jsonl").is_file())
            audit = report["audit"]
            self.assertEqual(audit["audit_status"],
                             "INVALID_FOR_PERFORMANCE_CLAIM")
            self.assertGreaterEqual(audit["reserved"], 1)
            self.assertGreaterEqual(len(audit["unknown_request_ids"]), 1)
            self.assertEqual(audit["settled"], 0)
            retry_evidence = Path(td) / "another-private-evidence"
            retry_evidence.mkdir(mode=0o700)
            with self.assertRaisesRegex(ValueError, "ALREADY_CONSUMED"):
                run_bounded_offline_once(
                    registry, retry_evidence,
                    grant_id="d1-hard-stop-test-002",
                    permit_sha256="b"*64)
            self.assertFalse((retry_evidence / "attempts.jsonl").exists())

    def test_invalid_scope_and_existing_journal_rejected_before_consuming(self):
        with tempfile.TemporaryDirectory() as td:
            registry, evidence = self.roots(td)
            args = dict(grant_id="d1-hard-stop-test-003",
                        permit_sha256="c"*64)
            with self.assertRaisesRegex(ValueError, "SCOPE_INVALID"):
                run_bounded_offline_once(
                    registry, evidence, scenario="unexpected", **args)
            self.assertEqual(list(registry.iterdir()), [])
            (evidence / "attempts.jsonl").write_text("{}")
            with self.assertRaisesRegex(ValueError, "SCOPE_INVALID"):
                run_bounded_offline_once(registry, evidence, **args)
            self.assertEqual(list(registry.iterdir()), [])

    def test_overlapping_or_symlink_roots_and_prod_path_denied(self):
        with tempfile.TemporaryDirectory() as td:
            registry, evidence = self.roots(td)
            args = dict(grant_id="d1-hard-stop-test-004",
                        permit_sha256="d"*64)
            with self.assertRaisesRegex(ValueError, "ROOTS_OVERLAP"):
                run_bounded_offline_once(
                    registry, registry, **args)
            alias = Path(td) / "alias"
            alias.symlink_to(evidence)
            with self.assertRaisesRegex(ValueError, "NOT_PRIVATE"):
                run_bounded_offline_once(registry, alias, **args)
            self.assertEqual(list(registry.iterdir()), [])

    def test_real_sender_and_public_child_cli_are_denied(self):
        from f0_l2_d1_hard_stop_once import _main
        with self.assertRaisesRegex(ValueError, "LIVE_NOT_AUTHORIZED"):
            send_live()
        with self.assertRaisesRegex(ValueError, "NO_PUBLIC_LIVE_CLI"):
            _main(["module", "--run"])
