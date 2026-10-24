"""Single-path D2/D3 candidate + Mac preflight + journal-first HTTPS rehearsal.

No actual BSC connection: child replaces the HTTPS constructor and socket.
"""
from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from f0_l2_d1_protected_mac_entry import rehearse_supervised_mac_entry_offline
import test_f0_l2_d1_real_sender_contract as candidate_fixture


class BoundWireRehearsalTests(unittest.TestCase):
    def setUp(self):
        f = candidate_fixture.RealSenderContractTests(
            "test_bound_candidate_still_denies_network_and_real_sender")
        f.setUp()
        self.addCleanup(f.doCleanups)
        self.f = f
        self.tmp = tempfile.TemporaryDirectory(prefix="d1-wire-bound-")
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name).resolve()
        self.registry = self.base / "registry"
        self.evidence = self.base / "evidence"
        self.registry.mkdir(mode=0o700)
        self.evidence.mkdir(mode=0o700)

    def rehearse(self, *, intent=None, grant_id="offline-rehearsal-bound-0001",
                 scenario="complete", seconds=5.0):
        f = self.f

        class FixedUTC:
            @staticmethod
            def now(_tz):
                return f.f.now

        with patch(
            "f0_l2_d1_protected_mac_entry.platform.system",
            return_value="Darwin"
        ), patch(
            "f0_l2_d1_protected_mac_entry.datetime", FixedUTC
        ), patch(
            "f0_l2_d1_protected_mac_entry.PRIVATE_FIXED_REGISTRY",
            f.registry
        ), patch(
            "f0_l2_d1_protected_mac_entry._os_user_home",
            return_value=f.fixture.home
        ), patch(
            "f0_l2_d1_protected_mac_entry.review_loaded_runtime_offline",
            return_value=f.fixture.mock_runtime
        ), patch(
            "http.client.HTTPSConnection",
            side_effect=AssertionError("D1_PARENT_HTTP_NOT_ALLOWED")
        ) as constructor:
            result = rehearse_supervised_mac_entry_offline(
                f.f.repo, f.f.sha, f.f.raw,
                evidence_root=f.out, test_registry=self.registry,
                test_evidence=self.evidence, test_grant_id=grant_id,
                scenario=scenario, hard_seconds=seconds,
                one_shot_intent_raw=f.bytes(intent))
            constructor.assert_not_called()
        return result

    def test_candidate_bind_and_same_supervised_three_slot_ledger(self):
        info = self.rehearse()
        source = info["real_sender_candidate"]
        self.assertIsNotNone(source)
        self.assertEqual(source["approved_commit_sha"], self.f.f.sha)
        self.assertEqual(source["candidate_source_manifest_sha256"],
                         self.f.manifest)
        self.assertFalse(source["real_https_enabled"])
        self.assertEqual(source["actual_rpc_calls"], 0)
        self.assertEqual(info["decision"], "D1_BLOCKED_AUTHORITY")
        self.assertEqual(info["production"], "PRODUCTION_NO_GO")
        child = info["test_child"]
        self.assertEqual(child["state"], "OFFLINE_CHILD_EXITED_ACCOUNTED")
        self.assertEqual(child["offline_child"]["reserved"], 6)
        self.assertEqual(child["offline_child"]["settled"], 6)
        self.assertLessEqual(child["offline_child"]["max_shared_slots"], 3)
        self.assertEqual(child["audit"]["unknown_request_ids"], [])
        self.assertEqual(len(child["audit"]["raw_frames_sha256"]), 6)
        self.assertEqual(list(self.f.registry.iterdir()), [])
        self.assertEqual(list(self.f.out.iterdir()), [])
        retry = self.base / "retry"
        retry.mkdir(mode=0o700)
        with self.assertRaisesRegex(ValueError, "ALREADY_CONSUMED"):
            self.rehearse()
        self.assertEqual(list(self.f.registry.iterdir()), [])

    def test_invalid_candidate_never_spends_disposable_marker(self):
        bad = dict(self.f.intent, source_manifest_sha256="f" * 64)
        with self.assertRaisesRegex(ValueError, "IDENTITY_MISMATCH"):
            self.rehearse(intent=bad)
        self.assertEqual(list(self.registry.iterdir()), [])
        self.assertEqual(list(self.evidence.iterdir()), [])
        self.assertEqual(list(self.f.registry.iterdir()), [])

    def test_candidate_guarded_mock_connect_timeout_stays_unknown(self):
        info = self.rehearse(scenario="hang_after_reserve", seconds=2.0)
        self.assertFalse(info["real_sender_candidate"]["real_https_enabled"])
        child = info["test_child"]
        self.assertEqual(child["state"], "HARD_STOP_KILLED_NO_RETRY")
        self.assertEqual(child["audit"]["unknown_request_ids"], [1])
        self.assertEqual(child["audit"]["settled"], 0)
        self.assertEqual(list(self.f.registry.iterdir()), [])
        self.assertEqual(list(self.f.out.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
