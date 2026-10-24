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


def _direct_child_pid(parent_pid):
    """Locate the exact one OS child before terminating the supervisor."""
    ps = subprocess.run(
        ["ps", "-axo", "pid=,ppid=,stat="],
        capture_output=True, text=True, check=True, timeout=3)
    matches = []
    for line in ps.stdout.splitlines():
        pieces = line.split()
        if len(pieces) >= 3 and pieces[0].isdigit() and pieces[1].isdigit():
            if int(pieces[1]) == parent_pid:
                matches.append((int(pieces[0]), pieces[2]))
    if len(matches) != 1 or matches[0][1].startswith("Z"):
        raise AssertionError("D1_EXPECT_ONE_RUNNING_DIRECT_CHILD: " + repr(matches))
    return matches[0][0]


def _child_state(pid):
    """Return RUNNING, ZOMBIE_EXITED or GONE; zombies have exited."""
    ps = subprocess.run(
        ["ps", "-p", str(pid), "-o", "stat="],
        capture_output=True, text=True, timeout=2)
    if ps.returncode not in (0, 1):
        raise AssertionError("D1_PS_CHILD_STATE_FAILED: " + ps.stderr)
    state = ps.stdout.strip().split()
    if ps.returncode == 1 or not state:
        return "GONE"
    return "ZOMBIE_EXITED" if state[0].startswith("Z") else "RUNNING"


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
                child_pid = _direct_child_pid(supervisor.pid)
                self.assertEqual(_child_state(child_pid), "RUNNING")
                # Parent process dies abruptly without calling proc.kill().
                supervisor.kill()
                supervisor.communicate(timeout=3)
                deadline = time.monotonic() + 4
                report = None
                state = "RUNNING"
                while time.monotonic() < deadline:
                    # O_EXCL creates the diagnostic before its JSON is
                    # written/fsynced. File existence is NOT a completion
                    # barrier. A finished record AND dead child are required.
                    if watchdog.is_file():
                        try:
                            report = json.loads(watchdog.read_text())
                        except (OSError, UnicodeError, json.JSONDecodeError):
                            report = None
                    state = _child_state(child_pid)
                    if report is not None and state in ("GONE", "ZOMBIE_EXITED"):
                        break
                    time.sleep(0.025)
                self.assertIsNotNone(report, "CHILD_DIAGNOSTIC_NOT_COMPLETE")
                self.assertIn(state, ("GONE", "ZOMBIE_EXITED"),
                              "CHILD_STILL_RUNNING_AFTER_PARENT_LOSS")
                # ZOMBIE_EXITED has no executing code; some Linux CI init
                # processes do not promptly reap orphan zombies.
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
                if "child_pid" in locals() and _child_state(child_pid) == "RUNNING":
                    # Failure cleanup only: the real test watches the child's
                    # own exit, not a test-initiated kill of that child.
                    os.kill(child_pid, signal.SIGKILL)

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
