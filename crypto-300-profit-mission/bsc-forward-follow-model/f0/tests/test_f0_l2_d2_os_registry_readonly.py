"""D2 OS-bound registry inspection is READ-ONLY and cannot consume grants."""
from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import f0_l2_d2_os_registry_readonly as reg
from f0_l2_d1_protected_mac_entry import _inspect_fixed_registry


class OSFixedRegistryReadOnlyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name).resolve() / "account-home"
        self.home.mkdir(mode=0o700)
        self.fixed = (self.home / "Library" / "Application Support" /
                      "MissionEvidence" / "f0-grant-registry")
        self.patchers = [
            patch.object(reg.pwd, "getpwuid",
                         return_value=SimpleNamespace(pw_dir=str(self.home))),
            patch.object(reg, "PRIVATE_FIXED_REGISTRY", self.fixed),
        ]
        for p in self.patchers:
            p.start()
            self.addCleanup(p.stop)

    def make_ready(self):
        for part in ("Library", "Application Support", "MissionEvidence",
                     "f0-grant-registry"):
            parent = (self.home / "Library" / "Application Support" /
                      "MissionEvidence" / "f0-grant-registry")
            if part == "Library":
                node = self.home / part
            elif part == "Application Support":
                node = self.home / "Library" / part
            elif part == "MissionEvidence":
                node = self.home / "Library" / "Application Support" / part
            else:
                node = parent
            node.mkdir(mode=0o700)
        return self.fixed

    def test_missing_root_no_create_no_marker_or_io(self):
        result = reg.inspect_fixed_production_registry_readonly()
        self.assertFalse(result["filesystem_ready"])
        self.assertEqual(result["reason"], "MISSING_COMPONENT_NO_AUTO_CREATE")
        self.assertFalse(result["registry_opened_readonly"])
        self.assertFalse(result["marker_consumed"])
        self.assertFalse(result["production_authorized"])
        self.assertFalse(self.fixed.exists())
        self.assertEqual(list(self.home.iterdir()), [])

    def test_fixed_owner_private_root_readonly_open_never_authorizes(self):
        self.make_ready()
        with patch("http.client.HTTPSConnection",
                   side_effect=AssertionError("NO_NETWORK")) as net:
            result = reg.inspect_fixed_production_registry_readonly()
            net.assert_not_called()
        self.assertTrue(result["filesystem_ready"])
        self.assertTrue(result["registry_opened_readonly"])
        self.assertFalse(result["production_authorized"])
        self.assertFalse(result["marker_consumed"])
        self.assertEqual(result["network_requests"], 0)
        self.assertEqual(result["production"], "PRODUCTION_NO_GO")
        self.assertEqual(list(self.fixed.iterdir()), [])

    def test_home_environment_does_not_redirect_os_account(self):
        self.make_ready()
        with patch.dict(os.environ, {"HOME": str(self.home / "attacker")},
                        clear=False):
            result = reg.inspect_fixed_production_registry_readonly()
        self.assertEqual(result["fixed_registry"], str(self.fixed))
        self.assertTrue(result["filesystem_ready"])

    def test_mismatched_legacy_home_based_registry_path_denied(self):
        self.make_ready()
        with patch.object(reg, "PRIVATE_FIXED_REGISTRY",
                          self.home / "attacker-registry"):
            with self.assertRaisesRegex(
                    ValueError, "D2_OS_FIXED_REGISTRY_ENV_OR_PATH_MISMATCH"):
                reg.inspect_fixed_production_registry_readonly()
        self.assertEqual(list(self.fixed.iterdir()), [])

    def test_private_namespace_symlink_disallowed_before_open(self):
        leaf = self.home / "Library" / "Application Support"
        leaf.mkdir(parents=True, mode=0o700)
        outside = self.home / "other"
        outside.mkdir(mode=0o700)
        (leaf / "MissionEvidence").symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(
                ValueError, "D2_OS_REGISTRY_SYMLINK_OR_OWNER_INVALID"):
            reg.inspect_fixed_production_registry_readonly()
        self.assertEqual(list(outside.iterdir()), [])

    def test_group_readable_namespace_disallowed(self):
        self.make_ready()
        evidence = self.fixed.parent
        evidence.chmod(0o750)
        with self.assertRaisesRegex(
                ValueError, "D2_OS_REGISTRY_NOT_PRIVATE"):
            reg.inspect_fixed_production_registry_readonly()
        self.assertEqual(list(self.fixed.iterdir()), [])

    def test_non_directory_fixed_root_disallowed(self):
        self.fixed.parent.mkdir(parents=True, mode=0o700)
        self.fixed.write_text("not a directory")
        with self.assertRaisesRegex(
                ValueError, "D2_OS_REGISTRY_SYMLINK_OR_OWNER_INVALID"):
            reg.inspect_fixed_production_registry_readonly()

    def test_os_home_owner_mismatch_fails_closed(self):
        self.make_ready()
        with patch.object(reg.os, "getuid", return_value=os.getuid() + 1):
            with self.assertRaisesRegex(
                    ValueError, "D2_OS_ACCOUNT_HOME_OWNERSHIP_INVALID"):
                reg.inspect_fixed_production_registry_readonly()

    def test_existing_mac_preflight_uses_same_readonly_audit(self):
        self.make_ready()
        with patch("f0_l2_d1_protected_mac_entry.PRIVATE_FIXED_REGISTRY",
                   self.fixed), patch(
                   "f0_l2_d1_protected_mac_entry._os_user_home",
                   return_value=self.home):
            result = _inspect_fixed_registry()
        self.assertEqual(result["fixed_private_registry"], str(self.fixed))
        self.assertTrue(result["registry_exists_and_private"])
        self.assertTrue(result["registry_opened"])
        self.assertTrue(result["os_account_bound"])
        self.assertFalse(result["marker_consumed"])
        self.assertFalse(result["production_authorized"])
        self.assertEqual(list(self.fixed.iterdir()), [])

    def test_no_live_entry_or_production_marker_factory(self):
        self.make_ready()
        result = reg.inspect_fixed_production_registry_readonly()
        self.assertTrue(result["filesystem_ready"])
        self.assertFalse(hasattr(reg, "consume"))
        self.assertFalse(hasattr(reg, "claim"))
        with self.assertRaisesRegex(
                ValueError, "D2_OS_REGISTRY_INSPECTION_NOT_LIVE_AUTHORITY"):
            reg.send_live(result, enable=True)
        self.assertEqual(list(self.fixed.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
