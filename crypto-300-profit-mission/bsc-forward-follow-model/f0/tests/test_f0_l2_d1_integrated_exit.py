"""D1 one integrated offline rehearsal, with production entry ALWAYS blocked.

Reusable fixture is addressed through a module import to avoid unittest
discovering the same parent TestCase twice.
"""
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import test_f0_l2_d1_inventory_gate as fixture_module
from f0_l2_d1_grant import _public_key_fingerprint
from f0_l2_d1_coordinator import SealedMemoryHTTPSSource, FakeSource
from f0_l2_d1_review_pins import OfflineReviewerPins
from f0_l2_d1_integrated_exit import (
    production_d1_exit_verdict, run_offline_integrated_fake_with_pins,
    send_live,
)


class D1IntegratedExitTests(unittest.TestCase):
    def setUp(self):
        f=fixture_module.D1InventoryGateTests(
            "test_independent_fake_signed_inventory_and_permit_are_bound")
        f.setUp()
        self.addCleanup(f.doCleanups)
        self.f=f
        self.pins=OfflineReviewerPins(
            source_sha=f.sha,
            permit_digest=sha256(f.raw).hexdigest(),
            inventory_digest=sha256(f.statement).hexdigest(),
            user_fingerprint=_public_key_fingerprint(
                f.trust["user"]["public_pem"]),
            reviewer_fingerprint=_public_key_fingerprint(
                f.trust["reviewer"]["public_pem"]))
        self.source=SealedMemoryHTTPSSource(delay_ms=10,growth_bps=10.0)

    def execute(self, **kwargs):
        f=self.f
        with patch("http.client.HTTPSConnection",
                   side_effect=AssertionError("NETWORK_MUST_NOT_BE_USED")):
            return run_offline_integrated_fake_with_pins(
                kwargs.get("source",self.source),
                f.out, permit_raw=kwargs.get("permit_raw",f.raw),
                expected_sha=f.sha, proofs=f.proofs,
                test_only_trust_roots=f.trust,
                checkout_root=f.repo, reviewed_files=f.manifest,
                now=f.now,
                raw_inventory_statement=kwargs.get("inventory",f.statement),
                inventory_signatures=f.inv_proofs,
                offline_test_registry_root=f.registry,
                externally_provided_test_pins=kwargs.get("pins",self.pins),
                test_only_fake_post_utc_clock=kwargs.get(
                    "clock",lambda:f.now))

    def test_exact_end_to_end_test_reference_once_raw_audit_and_exit_blocked(self):
        report=self.execute()
        self.assertEqual(report["mode"],
                         "D1_END_TO_END_OFFLINE_FAKE_REHEARSAL_NOT_LIVE")
        self.assertEqual(report["actual_rpc_requests"],0)
        self.assertEqual(report["audit_status"],"OFFLINE_ACCOUNTED_NOT_LIVE")
        self.assertEqual(report["pinned_test_evidence"]["status"],
                         "OFFLINE_EXTERNAL_PIN_MATCH_NOT_AUTHORIZATION")
        session=report["test_one_use_session"]
        self.assertEqual(session["session"]["fake"]["contiguous_commits"],3)
        self.assertEqual(session["session"]["fake"]["fake_post_utc_checks"],
                         session["session"]["fake"]["physically_started_fake"])
        self.assertEqual(session["marker"]["status"],
                         "CONSUMED_NOT_A_NETWORK_AUTHORIZATION")
        self.assertEqual(len(list(self.f.registry.iterdir())),1)
        self.assertTrue((self.f.out/"attempts.jsonl").is_file())
        self.assertTrue((self.f.out/"raw_responses").is_dir())
        self.assertEqual(report["d1_exit"]["status"],"D1_BLOCKED_AUTHORITY")
        self.assertFalse(report["d1_exit"]["d2_actual_permit_authorized"])
        self.assertFalse(report["d1_exit"]["d3_real_sampling_authorized"])
        self.assertTrue(report["never_promote_test_evidence_to_authority"])

    def test_wrong_reference_before_consumption_or_evidence_creation(self):
        cases=(
            {"pins":replace(self.pins, permit_digest="f"*64)},
            {"pins":replace(self.pins, reviewer_fingerprint="0"*64)},
            {"permit_raw":self.f.raw+b" "},
            {"source":FakeSource(delay_ms=0)},
            {"clock":None},
        )
        for case in cases:
            with self.subTest(case=tuple(case)):
                with self.assertRaises(ValueError):
                    self.execute(**case)
                self.assertFalse(list(self.f.registry.iterdir()))
                self.assertFalse(list(self.f.out.iterdir()))
                self.assertEqual(self.source.head_count,0)
                self.assertEqual(self.source.block_count,0)

    def test_second_run_denied_and_test_consumption_stays_spent(self):
        self.execute()
        new_out=Path(self.f.temp.name).absolute()/"changed_output"
        new_out.mkdir(mode=0o700)
        self.f.out=new_out
        with self.assertRaisesRegex(ValueError,"GRANT_ALREADY_CONSUMED"):
            self.execute(source=SealedMemoryHTTPSSource(delay_ms=0))
        self.assertEqual(len(list(self.f.registry.iterdir())),1)
        self.assertFalse(list(new_out.iterdir()))

    def test_expired_clock_keeps_test_marker_but_zero_fake_post(self):
        from datetime import timedelta
        bad_clock=lambda:self.f.now+timedelta(minutes=5)
        result=self.execute(clock=bad_clock)
        self.assertEqual(result["audit_status"],
                         "INVALID_FOR_PERFORMANCE_CLAIM")
        self.assertEqual(self.source.head_count,0)
        self.assertEqual(self.source.block_count,0)
        self.assertEqual(result["test_one_use_session"]["session"]["fake"][
                         "physically_started_fake"],0)
        self.assertEqual(result["d1_exit"]["status"],"D1_BLOCKED_AUTHORITY")
        self.assertEqual(len(list(self.f.registry.iterdir())),1)
        with self.assertRaisesRegex(ValueError,"GRANT_ALREADY_CONSUMED"):
            self.execute(source=SealedMemoryHTTPSSource(delay_ms=0))

    def test_production_exit_always_blocks_and_live_entry_never_instantiates(self):
        decision=production_d1_exit_verdict()
        self.assertEqual(decision["status"],"D1_BLOCKED_AUTHORITY")
        self.assertEqual(decision["enrolled_production_root_count"],0)
        self.assertEqual(len(decision["blockers"]),6)
        self.assertEqual(decision["production"],"PRODUCTION_NO_GO")
        with patch("http.client.HTTPSConnection",
                   side_effect=AssertionError("NO_NETWORK")) as mock:
            with self.assertRaisesRegex(ValueError,"BLOCKED_AUTHORITY"):
                send_live()
            with self.assertRaisesRegex(ValueError,"BLOCKED_AUTHORITY"):
                send_live(permit_raw=self.f.raw, execute_live=True,
                          trust_roots=self.f.trust)
            mock.assert_not_called()


if __name__=="__main__":
    unittest.main()
