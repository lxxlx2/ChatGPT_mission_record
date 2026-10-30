"""Offline launchd management tests: never call real launchctl or modify Mac services."""
from __future__ import annotations

import os
import plistlib
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import machine_fun_service as service


class MachineLaunchdTests(unittest.TestCase):
    def test_label_is_independent_of_frank(self):
        self.assertIn("machine-fun-first-launch", service.LABEL)
        self.assertNotIn("frank", service.LABEL.lower())

    def test_plist_has_user_login_and_restart_only_for_machine(self):
        with tempfile.TemporaryDirectory() as root:
            base = Path(root)
            folder = base / "research/projects/machine-fun/detector"
            folder.mkdir(parents=True)
            runner = folder / "run_machine_fun.sh"
            runner.write_text("echo run\n")
            python = folder / ".venv/bin/python"
            python.parent.mkdir(parents=True)
            python.write_text("test")
            with patch.object(service, "RUNNER", runner), patch.object(service, "EXPECTED_DIR", folder):
                result = service.plist_object()
            self.assertTrue(result["RunAtLoad"])
            self.assertFalse(result["KeepAlive"]["SuccessfulExit"])
            self.assertEqual(result["ThrottleInterval"], 120)
            self.assertEqual(result["ProgramArguments"], ["/bin/bash", str(runner), "run"])
            self.assertNotIn("frank", str(result["ProgramArguments"]).lower())
            self.assertNotIn("Alchemy", str(result))
            self.assertEqual(result["Umask"], 0o077)

    def test_install_bootstraps_only_own_label_and_keeps_private_plist(self):
        with tempfile.TemporaryDirectory() as root:
            base = Path(root)
            folder = base / "research/projects/machine-fun/detector"
            folder.mkdir(parents=True)
            runner = folder / "run_machine_fun.sh"
            runner.write_text("echo run\n")
            python = folder / ".venv/bin/python"
            python.parent.mkdir(parents=True)
            python.write_text("test")
            state = base / "state"
            plist = base / "Library/LaunchAgents/com.test.machine-fun-first-launch.plist"
            invocations = []
            def fake_launchctl(*args):
                invocations.append(args)
                return SimpleNamespace(returncode=0, stdout="", stderr="")
            with patch.object(service, "PLIST", plist), patch.object(service, "STATE", state), \
                 patch.object(service, "RUNNER", runner), patch.object(service, "EXPECTED_DIR", folder), \
                 patch.object(service, "launchctl", side_effect=fake_launchctl), \
                 patch.object(service.platform, "system", return_value="Darwin"):
                service.install()
                self.assertTrue(plist.is_file())
                value = plistlib.loads(plist.read_bytes())
                self.assertEqual(value["Label"], service.LABEL)
                self.assertEqual(invocations, [("bootstrap", service.DOMAIN, str(plist))])
                self.assertEqual(os.stat(plist).st_mode & 0o077, 0)
                self.assertEqual(os.stat(state).st_mode & 0o077, 0)

    def test_failed_bootstrap_rolls_back_only_own_plist(self):
        with tempfile.TemporaryDirectory() as root:
            base = Path(root)
            folder = base / "research/projects/machine-fun/detector"
            folder.mkdir(parents=True)
            runner = folder / "run_machine_fun.sh"
            runner.write_text("run")
            py = folder / ".venv/bin/python"
            py.parent.mkdir(parents=True)
            py.write_text("test")
            plist = base / "LaunchAgents/com.test.machine-fun-first-launch.plist"
            with patch.object(service, "PLIST", plist), patch.object(service, "STATE", base / "state"), \
                 patch.object(service, "RUNNER", runner), patch.object(service, "EXPECTED_DIR", folder), \
                 patch.object(service.platform, "system", return_value="Darwin"), \
                 patch.object(service, "launchctl", return_value=SimpleNamespace(returncode=5)):
                with self.assertRaisesRegex(service.ServiceFailure, "BOOTSTRAP_FAILED"):
                    service.install()
                self.assertFalse(plist.exists())

    def test_uninstall_refuses_other_service_even_if_same_path(self):
        with tempfile.TemporaryDirectory() as root:
            plist = Path(root) / "test.plist"
            plist.write_bytes(plistlib.dumps({"Label": "com.example.frank"}))
            with patch.object(service, "PLIST", plist), patch.object(service.platform, "system", return_value="Darwin"), \
                 patch.object(service, "launchctl") as ctl:
                with self.assertRaisesRegex(service.ServiceFailure, "WRONG_SERVICE"):
                    service.uninstall()
                self.assertTrue(plist.exists())
                ctl.assert_not_called()

    def test_uninstall_stops_only_own_label_and_preserves_data(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            plist = root / "test.plist"
            plist.write_bytes(plistlib.dumps({"Label": service.LABEL}))
            notes = root / "keep.txt"
            notes.write_text("keep")
            calls = []
            def ctl(*args):
                calls.append(args)
                return SimpleNamespace(returncode=0)
            with patch.object(service, "PLIST", plist), patch.object(service.platform, "system", return_value="Darwin"), \
                 patch.object(service, "launchctl", side_effect=ctl):
                service.uninstall()
            self.assertEqual(calls, [("bootout", service.TARGET)])
            self.assertFalse(plist.exists())
            self.assertTrue(notes.exists())

    def test_uninstall_does_not_claim_success_if_bootout_fails_and_still_loaded(self):
        with tempfile.TemporaryDirectory() as root:
            plist = Path(root) / "test.plist"
            plist.write_bytes(plistlib.dumps({"Label": service.LABEL}))
            with patch.object(service, "PLIST", plist), patch.object(service.platform, "system", return_value="Darwin"), \
                 patch.object(service, "launchctl", side_effect=[SimpleNamespace(returncode=1), SimpleNamespace(returncode=0)]):
                with self.assertRaisesRegex(service.ServiceFailure, "STILL_LOADED"):
                    service.uninstall()
            self.assertTrue(plist.exists())


if __name__ == "__main__":
    unittest.main()
