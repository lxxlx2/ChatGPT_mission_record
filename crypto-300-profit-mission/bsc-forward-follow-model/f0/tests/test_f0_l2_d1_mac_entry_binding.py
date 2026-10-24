"""Mac preflight -> one OS protected, test-only HTTPS constructor child."""
from __future__ import annotations

from pathlib import Path
import http.client
import json
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import test_f0_l2_d1_protected_mac_entry as mac_fixture
from f0_l2_d1_protected_mac_entry import (
    rehearse_supervised_mac_entry_offline, send_live)


class MacEntryTransportBindingTests(unittest.TestCase):
    def setUp(self):
        self.fixture = mac_fixture.MacEntryNoNetworkTests(
            "test_actual_mac_entry_scope_has_no_grant_or_send_and_fixed_root")
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.f = self.fixture.f
        self.registry = self.fixture.registry
        self.out = self.f.out
        self.temp = tempfile.TemporaryDirectory(prefix="d1-entry-rehearsal-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.test_reg = self.base / "test-registry"
        self.test_out = self.base / "test-evidence"
        self.test_reg.mkdir(mode=0o700)
        self.test_out.mkdir(mode=0o700)

    def perform(self, **kwargs):
        class ControlledUTC:
            @staticmethod
            def now(_tz):
                return self.f.now
        args = dict(
            checkout_root=self.f.repo, expected_sha=self.f.sha,
            permit_raw=self.f.raw, evidence_root=self.out,
            test_registry=self.test_reg, test_evidence=self.test_out,
            test_grant_id="offline-rehearsal-test-00001",
            hard_seconds=5.0,
        )
        args.update(kwargs)
        with patch(
            "f0_l2_d1_protected_mac_entry.platform.system",
            return_value="Darwin"
        ), patch(
            "f0_l2_d1_protected_mac_entry.datetime", ControlledUTC
        ), patch(
            "f0_l2_d1_protected_mac_entry.PRIVATE_FIXED_REGISTRY",
            self.registry
        ), patch(
            "f0_l2_d1_protected_mac_entry._os_user_home",
            return_value=self.fixture.home
        ), patch(
            "f0_l2_d1_protected_mac_entry.review_loaded_runtime_offline",
            return_value=self.fixture.mock_runtime
        ), patch(
            "http.client.HTTPSConnection",
            side_effect=AssertionError("PARENT_NETWORK_FORBIDDEN")
        ) as network:
            result = rehearse_supervised_mac_entry_offline(**args)
            network.assert_not_called()
        return result

    def test_mac_preflight_to_one_child_enforces_no_live_source(self):
        report = self.perform()
        self.assertEqual(report["reviewed_sha"], self.f.sha)
        self.assertEqual(report["decision"], "D1_BLOCKED_AUTHORITY")
        self.assertEqual(report["production"], "PRODUCTION_NO_GO")
        self.assertFalse(report["real_sender_enabled"])
        self.assertFalse(report["d2_granted"])
        self.assertFalse(report["d3_granted"])
        self.assertEqual(report["network_requests"], 0)
        self.assertTrue(report["fixed_production_registry_inspected_only"])
        self.assertFalse(report["fixed_production_registry_marker_consumed"])
        self.assertEqual(list(self.registry.iterdir()), [])
        self.assertEqual(list(self.out.iterdir()), [])
        run = report["test_child"]
        self.assertEqual(run["state"], "OFFLINE_CHILD_EXITED_ACCOUNTED")
        self.assertEqual(run["live_network_requests"], 0)
        self.assertEqual(run["child_exit_code"], 0)
        self.assertEqual(run["offline_child"]["reserved"],
                         run["offline_child"]["settled"])
        self.assertLessEqual(run["offline_child"]["max_shared_slots"], 3)
        self.assertEqual(run["audit"]["unknown_request_ids"], [])

    def test_same_scope_test_grant_spent_and_different_digest_rejected(self):
        self.perform()
        old_marker = next(self.test_reg.glob("*.consumed.json"))
        original = old_marker.read_bytes()
        next_root = self.base / "new-test-evidence"
        next_root.mkdir(mode=0o700)
        with self.assertRaisesRegex(ValueError, "ALREADY_CONSUMED"):
            self.perform(test_evidence=next_root)
        self.assertEqual(old_marker.read_bytes(), original)
        self.assertEqual(list(self.registry.iterdir()), [])
        self.assertEqual(list(self.out.iterdir()), [])

    def test_mac_preflight_denial_consumes_no_test_grant(self):
        with self.assertRaisesRegex(ValueError, "PERMIT_CODE_SHA_MISMATCH"):
            self.perform(expected_sha="f" * 40)
        self.assertEqual(list(self.test_reg.iterdir()), [])
        self.assertEqual(list(self.test_out.iterdir()), [])
        self.assertEqual(list(self.registry.iterdir()), [])

    def test_real_registry_and_mac_evidence_cannot_be_test_outputs(self):
        with self.assertRaisesRegex(ValueError, "PRODUCTION_ROOT_FORBIDDEN"):
            self.perform(test_registry=self.registry)
        with self.assertRaisesRegex(ValueError, "PRODUCTION_ROOT_FORBIDDEN"):
            self.perform(test_evidence=self.registry)
        self.assertEqual(list(self.registry.iterdir()), [])
        with self.assertRaisesRegex(ValueError, "EVIDENCE_ROOT_OVERLAP"):
            self.perform(test_evidence=self.out)
        self.assertEqual(list(self.out.iterdir()), [])
        self.assertEqual(list(self.test_reg.iterdir()), [])

    def test_release_constants_cannot_turn_rehearsal_into_live(self):
        with patch("f0_l2_d1_protected_mac_entry._REAL_SENDER_RELEASED", True):
            with self.assertRaisesRegex(ValueError, "CONSTANTS_NOT_FROZEN"):
                self.perform()
        with patch(
            "f0_l2_d1_protected_mac_entry._D2_REVIEWED_PERMIT_SHA256",
            "a" * 64,
        ):
            with self.assertRaisesRegex(ValueError, "CONSTANTS_NOT_FROZEN"):
                self.perform()
        self.assertFalse(list(self.test_reg.iterdir()))
        self.assertFalse(list(self.registry.iterdir()))
        with self.assertRaisesRegex(ValueError, "D2_D3_REQUIRED"):
            send_live()

    def test_whole_operation_timeout_preserves_unknown_and_test_marker(self):
        # Exercise real parent-child OS supervisor with patched child HTTPS.
        run = self.perform(scenario="hang_after_reserve",
                           hard_seconds=2.0)["test_child"]
        self.assertEqual(run["state"], "HARD_STOP_KILLED_NO_RETRY")
        self.assertTrue(run["no_automatic_retry"])
        self.assertEqual(run["audit"]["unknown_request_ids"], [1])
        self.assertEqual(run["audit"]["settled"], 0)
        self.assertEqual(list(self.registry.iterdir()), [])
        next_dir = self.base / "third-evidence"
        next_dir.mkdir(mode=0o700)
        with self.assertRaisesRegex(ValueError, "ALREADY_CONSUMED"):
            self.perform(test_evidence=next_dir)

    def test_rehearsal_deadline_exceeds_candidate_dispatch_rejected(self):
        with self.assertRaisesRegex(ValueError, "DEADLINE_INVALID"):
            self.perform(hard_seconds=15.01)
        self.assertEqual(list(self.test_reg.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
