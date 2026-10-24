"""One Mac launch surface: exact-SHA preflight, NO real network access."""
from datetime import timedelta
from hashlib import sha256
import json
import http.client
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import test_f0_l2_d1_inventory_gate as source_fixture
from f0_l2_d1_protected_mac_entry import (
    inspect_supervised_mac_scope_offline, send_live,
    main as protected_main,
)


class MacEntryNoNetworkTests(unittest.TestCase):
    def setUp(self):
        f=source_fixture.D1InventoryGateTests(
            "test_independent_fake_signed_inventory_and_permit_are_bound")
        f.setUp()
        self.addCleanup(f.doCleanups)
        self.f=f
        self.home=Path(f.temp.name).absolute()
        self.registry=(self.home/"Library"/"Application Support"/
                       "MissionEvidence"/"f0-grant-registry")
        self.registry.mkdir(mode=0o700,parents=True)
        self.mock_runtime={
            "status":"REVIEWED_LOCAL_BYTES_MATCH_NOT_LIVE_AUTHORIZATION",
            "source_commit_sha":f.sha,
            "tracked_paths_checked":170,
            "critical_module_origins_checked":{"x":{"sha256":"a"*64}},
            "production_grant_authorized":False,
            "network_requests":0,
        }

    def inspect(self, **overrides):
        f=self.f
        class ControlledUTC:
            @staticmethod
            def now(tz):
                return overrides.get("utc",f.now)
        with patch("f0_l2_d1_protected_mac_entry.platform.system",
                   return_value=overrides.get("system","Darwin")):
            with patch("f0_l2_d1_protected_mac_entry.datetime",
                       ControlledUTC):
                with patch(
                    "f0_l2_d1_protected_mac_entry.PRIVATE_FIXED_REGISTRY",
                    overrides.get("registry",self.registry)
                ):
                    with patch("f0_l2_d1_protected_mac_entry._os_user_home",
                               return_value=self.home):
                        with patch("f0_l2_d1_protected_mac_entry."
                                   "review_loaded_runtime_offline",
                                   return_value=self.mock_runtime) as provenance:
                        with patch("http.client.HTTPSConnection",
                                   side_effect=AssertionError(
                                       "REAL_HTTPS_NOT_ALLOWED")) as network:
                            result=inspect_supervised_mac_scope_offline(
                                overrides.get("checkout",f.repo),
                                overrides.get("sha",f.sha),
                                overrides.get("permit",f.raw),
                                evidence_root=overrides.get("evidence",f.out))
                            network.assert_not_called()
                            provenance.assert_called_once_with(
                                overrides.get("checkout",f.repo),
                                overrides.get("sha",f.sha))
                            return result

    def test_actual_mac_entry_scope_has_no_grant_or_send_and_fixed_root(self):
        result=self.inspect()
        self.assertEqual(result["decision"],"D1_BLOCKED_AUTHORITY")
        self.assertEqual(result["network_requests"],0)
        self.assertFalse(result["d2_permit_approved"])
        self.assertFalse(result["d3_run_approved"])
        self.assertFalse(result["real_sender_bound_to_unique_coordinator"])
        self.assertEqual(result["reviewed_sha"],self.f.sha)
        self.assertEqual(result["permit_raw_sha256"],
                         sha256(self.f.raw).hexdigest())
        self.assertEqual(result["max_live_slots"],3)
        self.assertEqual(result["post_gap_ms"],250)
        self.assertEqual(result["fixed_registry_state"][
                         "fixed_private_registry"],str(self.registry))
        self.assertTrue(result["fixed_registry_state"][
                        "registry_exists_and_private"])
        self.assertFalse(result["fixed_registry_state"]["marker_consumed"])
        self.assertEqual(list(self.registry.iterdir()),[])
        self.assertEqual(list(self.f.out.iterdir()),[])

    def test_wrong_commit_and_modified_raw_permit_reject_before_any_marker(self):
        with self.assertRaisesRegex(ValueError,"PERMIT_CODE_SHA_MISMATCH"):
            self.inspect(sha="f"*40)
        tampered=json.loads(self.f.raw)
        tampered["max_inflight"]=2
        with self.assertRaisesRegex(ValueError,"RESOURCE_SCOPE_INVALID"):
            self.inspect(permit=json.dumps(tampered).encode())
        self.assertEqual(list(self.registry.iterdir()),[])
        self.assertEqual(list(self.f.out.iterdir()),[])

    def test_expired_scope_fails_closed_not_a_new_grant(self):
        with self.assertRaisesRegex(ValueError,"WINDOW_INACTIVE"):
            self.inspect(utc=self.f.now+timedelta(hours=1))
        self.assertFalse(list(self.registry.iterdir()))

    def test_non_mac_and_nonprivate_evidence_denied(self):
        with self.assertRaisesRegex(ValueError,"MAC_ONLY"):
            self.inspect(system="Linux")
        self.f.out.chmod(0o755)
        self.addCleanup(lambda:self.f.out.chmod(0o700))
        with self.assertRaisesRegex(ValueError,"DIRECTORY_PERMISSIONS"):
            self.inspect()

    def test_fixed_registry_symlink_and_bad_mode_refused(self):
        sym=Path(self.f.temp.name).absolute()/"fake-link"
        sym.symlink_to(self.registry,target_is_directory=True)
        with self.assertRaisesRegex(ValueError,"FIXED_REGISTRY_PATH_ENV_MISMATCH"):
            self.inspect(registry=sym)
        self.registry.chmod(0o777)
        self.addCleanup(lambda:self.registry.chmod(0o700))
        with self.assertRaisesRegex(ValueError,"DIRECTORY_PERMISSIONS"):
            self.inspect()

    def test_fixed_registry_can_be_missing_without_creating_it(self):
        missing=self.registry
        self.registry.rmdir()
        result=self.inspect()
        self.assertFalse(result["fixed_registry_state"][
                         "registry_exists_and_private"])
        self.assertFalse(missing.exists())
        self.assertFalse(result["fixed_registry_state"]["marker_consumed"])

    def test_send_live_never_opens_socket_or_spends_marker(self):
        with patch("http.client.HTTPSConnection",
                   side_effect=AssertionError("NO_REAL_RPC")) as socket:
            with self.assertRaisesRegex(ValueError,"D2_D3_REQUIRED"):
                send_live(
                    execute_live=True,
                    permit_raw=self.f.raw,
                    grant_id="candidate-00001",
                    registry_root=str(self.registry))
            socket.assert_not_called()
        self.assertEqual(list(self.registry.iterdir()),[])

    def test_cli_rejects_run_flag_no_network_no_grant(self):
        with patch("http.client.HTTPSConnection",
                   side_effect=AssertionError("NO_NETWORK")) as socket:
            with self.assertRaises(SystemExit) as error:
                protected_main(["--run"])
            self.assertEqual(error.exception.code,2)
            socket.assert_not_called()
        self.assertFalse(list(self.registry.iterdir()))


if __name__=="__main__":
    unittest.main()
