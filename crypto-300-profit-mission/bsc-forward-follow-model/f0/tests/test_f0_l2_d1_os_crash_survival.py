"""D1 OS-level abrupt child-process termination, wholly fake/no live sender.

Child opens only disposable private directories and in-memory HTTPS frames.
The parent process verifies the durable grant marker, UNKNOWN ledger and
non-replay behavior without ever resuming the interrupted fake session.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

F0 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(F0))

from f0_l2_d1_grant import OfflineGrantRegistry
from f0_l2_d1_recovery import reconcile_saved_attempts

TEST_GRANT = "d1-fake-process-crash-0001"
TEST_DIGEST = "a"*64


def _abrupt_child(mode: str, evidence: Path, registry: Path):
    """Intentionally SIGKILL self after a selected FSYNC completion."""
    from f0_l2_d1_coordinator import (
        ExclusiveEvidence, SealedMemoryHTTPSSource, run_fake_concurrent)
    import http.client

    def denied_socket(*args, **kwargs):
        raise AssertionError("REAL_SOCKET_FORBIDDEN")
    http.client.HTTPSConnection = denied_socket

    consumed = OfflineGrantRegistry(registry).consume(TEST_GRANT, TEST_DIGEST)
    if consumed["status"] != "CONSUMED_NOT_A_NETWORK_AUTHORIZATION":
        raise AssertionError("NOT_CONSUMED")
    if mode == "marker":
        os.kill(os.getpid(), signal.SIGKILL)

    original_add = ExclusiveEvidence.add

    def crash_at_fsync_boundary(self, event):
        if mode == "reserve" and (
                event.get("event") == "RESERVE_UNKNOWN" and
                event.get("category") == "CHAIN"):
            original_add(self, event)
            os.kill(os.getpid(), signal.SIGKILL)
        if mode == "raw" and event.get("event") == "SETTLE" and (
                event.get("category") == "BLOCK" and
                event.get("raw_name") is not None):
            # settle() fsynced RAW bytes and raw directory, but SETTLE
            # has not been persisted at all; the BLOCK remains UNKNOWN.
            raw_path = self.raw_dir / event["raw_name"]
            if not raw_path.is_file():
                raise AssertionError("RAW_NOT_DURABLE")
            with raw_path.open("rb") as fh:
                os.fsync(fh.fileno())
            os.kill(os.getpid(), signal.SIGKILL)
        return original_add(self, event)

    ExclusiveEvidence.add = crash_at_fsync_boundary
    run_fake_concurrent(
        SealedMemoryHTTPSSource(delay_ms=10, growth_bps=10.0),
        evidence,max_total=9,max_blocks=3,max_refreshes=4,
        window_ms=6500,head_min_poll_age_ms=250)
    raise AssertionError("CHILD_DID_NOT_CRASH")


class D1OsCrashSurvivalTests(unittest.TestCase):
    def child(self, mode):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d).absolute()
            registry, evidence = root/"registry", root/"evidence"
            registry.mkdir(mode=0o700)
            evidence.mkdir(mode=0o700)
            command = [
                sys.executable, str(Path(__file__).resolve()),
                "--fake-crash-child", mode, str(evidence), str(registry),
            ]
            # No shell; no network; child bounded to a short foreground run.
            run = subprocess.run(command,timeout=15,
                                 capture_output=True,text=True)
            self.assertEqual(run.returncode,-signal.SIGKILL,
                             f"Child {mode} returned {run.returncode}: "+
                             run.stderr[-1400:])
            marker_files=list(registry.glob("*.consumed.json"))
            self.assertEqual(len(marker_files),1)
            marker=marker_files[0]
            self.assertEqual(marker.stat().st_mode & 0o077,0)
            with self.assertRaisesRegex(ValueError,
                                        "D1_GRANT_ALREADY_CONSUMED"):
                OfflineGrantRegistry(registry).consume(
                    TEST_GRANT, "b"*64)
            self.assertEqual(len(list(registry.iterdir())),1)

            log=evidence/"attempts.jsonl"
            if mode=="marker":
                self.assertFalse(log.exists())
                self.assertEqual(list(evidence.iterdir()),[])
                return

            self.assertTrue(log.is_file())
            before=log.read_bytes()
            self.assertEqual(log.stat().st_mode & 0o077,0)
            self.assertTrue(before.endswith(b"\n"))
            rows=[json.loads(line) for line in before.splitlines()]
            reservations=[x for x in rows
                          if x["event"]=="RESERVE_UNKNOWN"]
            pending={x["id"] for x in reservations}
            for row in rows:
                if row["event"]=="SETTLE":
                    pending.discard(row["id"])
            self.assertTrue(pending)
            self.assertNotIn("COMMIT_CONTIGUOUS",
                             [x["event"] for x in rows])
            result=reconcile_saved_attempts(evidence)
            self.assertEqual(result["audit_status"],
                             "INVALID_FOR_PERFORMANCE_CLAIM")
            self.assertEqual(result["unknown_request_ids"],
                             sorted(pending))
            self.assertEqual(result["network_retries"],0)
            self.assertEqual(log.read_bytes(),before)

            raw_files=list((evidence/"raw_responses").glob("*.body"))
            if mode=="reserve":
                self.assertEqual(len(reservations),1)
                self.assertEqual(reservations[0]["category"],"CHAIN")
                self.assertEqual(raw_files,[])
            elif mode=="raw":
                self.assertTrue(any(x["category"]=="BLOCK"
                                    for x in reservations))
                self.assertTrue(raw_files)
                self.assertTrue(all(x.stat().st_mode & 0o077 == 0
                                    for x in raw_files))
                # Last RAW archived but without matching SETTLE is an
                # orphan after crash, never a completed/committed BLOCK.
                latest=max(raw_files)
                self.assertFalse(any(x["event"]=="SETTLE" and
                                     x.get("raw_name")==latest.name
                                     for x in rows))
            self.assertEqual(log.read_bytes(),before)
            with self.assertRaisesRegex(ValueError,
                                        "D1_GRANT_ALREADY_CONSUMED"):
                OfflineGrantRegistry(registry).consume(
                    TEST_GRANT,TEST_DIGEST)
            self.assertEqual(log.read_bytes(),before)

    def test_kill_after_one_use_marker_before_any_evidence(self):
        self.child("marker")

    def test_kill_immediately_after_presend_reservation_fsync(self):
        self.child("reserve")

    def test_kill_after_raw_fsync_before_settlement(self):
        self.child("raw")


if __name__=="__main__":
    if len(sys.argv)==5 and sys.argv[1]=="--fake-crash-child":
        _abrupt_child(sys.argv[2], Path(sys.argv[3]),Path(sys.argv[4]))
    else:
        unittest.main()
