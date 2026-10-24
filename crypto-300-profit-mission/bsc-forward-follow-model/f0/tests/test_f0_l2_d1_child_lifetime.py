"""D1 offline child-lifetime gate: parent SIGKILL cannot orphan fake worker."""
from __future__ import annotations

import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest

F0 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(F0))
from f0_l2_d1_recovery import reconcile_saved_attempts
from f0_l2_d1_hard_stop_once import run_bounded_offline_once


class ChildLifetimeOfflineTests(unittest.TestCase):
    def test_supervisor_sigkill_makes_blocked_child_self_exit(self):
        """Kill actual parent after preconnect reservation; no auto replay."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            registry = root / "private-registry"
            evidence = root / "private-evidence"
            registry.mkdir(mode=0o700)
            evidence.mkdir(mode=0o700)
            ident = "d1-parent-loss-fixture-0001"
            digest = "e" * 64
            fixture = (
                "import sys\n"
                f"sys.path.insert(0, {str(F0)!r})\n"
                "from pathlib import Path\n"
                "from f0_l2_d1_hard_stop_once import run_bounded_offline_once\n"
                f"run_bounded_offline_once(Path({str(registry)!r}), "
                f"Path({str(evidence)!r}), grant_id={ident!r}, "
                f"permit_sha256={digest!r}, "
                "scenario='hang_after_reserve', hard_seconds=9.0)\n"
            )
            supervisor = subprocess.Popen(
                [sys.executable, "-B", "-c", fixture],
                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE, close_fds=True)
            journal = evidence / "attempts.jsonl"
            watchdog = evidence / "child_watchdog_termination.json"
            try:
                expires = time.monotonic() + 5
                observed = False
                while time.monotonic() < expires:
                    if journal.exists() and "RESERVE_UNKNOWN" in journal.read_text():
                        observed = True
                        break
                    if supervisor.poll() is not None:
                        break
                    time.sleep(0.025)
                self.assertTrue(observed, "NO_CHILD_DURABLE_RESERVATION")
                # Parent process dies abruptly without calling proc.kill().
                supervisor.kill()
                supervisor.communicate(timeout=3)
                deadline = time.monotonic() + 4
                while time.monotonic() < deadline and not watchdog.is_file():
                    time.sleep(0.025)
                self.assertTrue(watchdog.is_file(),
                                "CHILD_DID_NOT_DETECT_PARENT_LOSS")
                report = json.loads(watchdog.read_text())
                self.assertEqual(report["reason"], "PARENT_PIPE_CLOSED")
                self.assertIs(report["real_network"], False)
                audit = reconcile_saved_attempts(evidence)
                self.assertEqual(audit["audit_status"],
                                 "INVALID_FOR_PERFORMANCE_CLAIM")
                self.assertEqual(audit["unknown_request_ids"], [1])
                self.assertEqual(audit["settled"], 0)
                self.assertEqual(len(list(registry.glob("*.consumed.json"))), 1)
                retry_root = root / "retry-evidence"
                retry_root.mkdir(mode=0o700)
                with self.assertRaisesRegex(ValueError, "ALREADY_CONSUMED"):
                    run_bounded_offline_once(
                        registry, retry_root, grant_id=ident,
                        permit_sha256=digest)
                self.assertFalse((retry_root / "attempts.jsonl").exists())
            finally:
                if supervisor.poll() is None:
                    supervisor.kill()
                    supervisor.communicate(timeout=3)

    def test_guard_cli_requires_inherited_read_pipe(self):
        from f0_l2_d1_hard_stop_once import _main
        with tempfile.TemporaryDirectory() as td:
            # A direct invocation cannot fabricate a parent liveness
            # channel from a CLI flag or candidate grant input.
            evidence = Path(td)
            with self.assertRaises((OSError, ValueError)):
                _main(["fixture", "--offline-child", str(evidence),
                       str(evidence), "fake-grant-identity",
                       "f" * 64, "complete", "999999", "1.0"])


if __name__ == "__main__":
    unittest.main()
