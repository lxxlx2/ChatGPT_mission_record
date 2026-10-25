"""Bound D3 UTC survives child boundary and checks each final fake POST.

Source is the already approved patched-constructor / single 3-slot coordinator;
no real socket or signed/live permit.
"""
from __future__ import annotations

from pathlib import Path
import json
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import test_f0_l2_d1_bound_wire_rehearsal as bound_fixture
from f0_l2_d1_hard_stop_once import run_bounded_offline_once


class CandidateChildPostUTCTests(unittest.TestCase):
    def make_fixture(self):
        f = bound_fixture.BoundWireRehearsalTests(
            "test_candidate_bind_and_same_supervised_three_slot_ledger")
        f.setUp()
        self.addCleanup(f.doCleanups)
        return f

    def test_approved_candidate_checks_utc_at_every_fake_post(self):
        fixture = self.make_fixture()
        run = fixture.rehearse()["test_child"]
        child = run["offline_child"]
        self.assertIsNotNone(run["effective_offline_scope"]["post_utc"])
        self.assertGreaterEqual(child["fake_post_utc_checks"], 2)
        self.assertEqual(child["fake_post_utc_checks"],
                         child["physically_started_fake"])
        self.assertEqual(child["reserved"], 6)
        self.assertEqual(child["settled"], 6)
        self.assertEqual(child["network_requests"], 0)
        self.assertFalse(list(fixture.f.registry.iterdir()))

    def test_expired_exact_final_post_window_preserves_failed_journal(self):
        with tempfile.TemporaryDirectory(prefix="d1-post-utc-") as d:
            root = Path(d).resolve()
            reg, out = root / "registry", root / "evidence"
            reg.mkdir(mode=0o700)
            out.mkdir(mode=0o700)
            permit_digest = "a" * 64
            scope = self.scope(permit_digest)
            run = run_bounded_offline_once(
                reg, out, grant_id="offline-last-utc-expiry-test-001",
                permit_sha256=permit_digest, scenario="complete",
                hard_seconds=5.0, offline_scope=scope)
            self.assertEqual(run["state"], "OFFLINE_CHILD_EXITED_ACCOUNTED")
            child = run["offline_child"]
            self.assertEqual(child["fake_post_utc_checks"], 0)
            self.assertEqual(child["physically_started_fake"], 0)
            self.assertEqual(child["reserved"], 1)
            self.assertEqual(child["settled"], 1)
            self.assertEqual(child["contiguous_commits"], 0)
            self.assertEqual(child["stop"], "RPC_OR_HEAD_FAULT")
            rows = [json.loads(x) for x in
                    (out / "attempts.jsonl").read_text().splitlines()]
            self.assertEqual([r["event"] for r in rows],
                             ["RESERVE_UNKNOWN", "SETTLE"])
            self.assertEqual(rows[1]["state"], "FAILED")
            self.assertIn("PRESTART_OFFLINE_PERMIT_UTC_DENIED",
                          rows[1]["reason"])
            self.assertEqual(list((out / "raw_responses").iterdir()), [])
            self.assertEqual(run["audit"]["unknown_request_ids"], [])
            self.assertEqual(run["live_network_requests"], 0)

    @staticmethod
    def scope(digest):
        return {
            "max_total": 3, "max_blocks": 1, "max_refreshes": 0,
            "spacing_ms": 250, "slots": 3, "head_ttl_ms": 2000,
            "window_ms": 2500, "timeout_ms": 1000,
            "post_utc": {
                "window_start_utc": "2026-10-25T05:59:00Z",
                "window_end_utc": "2026-10-25T06:00:00Z",
                "checked_at_utc": "2026-10-25T06:00:00Z",
                "approved_commit_sha": "b" * 40,
                "permit_sha256": digest,
            },
        }

    def test_wrong_digest_or_expired_checked_window_spends_no_marker(self):
        with tempfile.TemporaryDirectory(prefix="d1-post-utc-") as d:
            root = Path(d).resolve()
            reg, out = root / "registry", root / "evidence"
            reg.mkdir(mode=0o700)
            out.mkdir(mode=0o700)
            for case in ("digest", "window", "fields"):
                with self.subTest(case=case):
                    scope = self.scope("a" * 64)
                    if case == "digest":
                        scope["post_utc"]["permit_sha256"] = "f" * 64
                    elif case == "window":
                        scope["post_utc"]["checked_at_utc"] = (
                            "2026-10-25T06:00:01Z")
                    else:
                        scope["post_utc"]["unexpected"] = True
                    with self.assertRaisesRegex(ValueError,
                                                "D1_CHILD_"):
                        run_bounded_offline_once(
                            reg, out, grant_id="offline-bad-utc-test-001",
                            permit_sha256="a" * 64,
                            offline_scope=scope, hard_seconds=5.0)
                    self.assertEqual(list(reg.iterdir()), [])
                    self.assertEqual(list(out.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
