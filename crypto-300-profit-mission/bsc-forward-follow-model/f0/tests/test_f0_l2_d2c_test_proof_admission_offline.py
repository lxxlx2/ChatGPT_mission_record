"""D2-C: offline TEST proof cannot become physical source authority."""
from __future__ import annotations

import http.client
import json
from pathlib import Path
import socket
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import test_f0_l2_d2b_signed_execution_offline as three_role_fixture
from f0_l2_d2c_test_proof_admission_offline import (
    try_admit_signed_test_fixture_offline, send_live)
from f0_l2_d2a_physical_admission import UnreleasedPhysicalHTTPSProposal
from f0_l2_d1_grant import OfflineGrantRegistry


class TestProofClosedPhysicalSourceTests(unittest.TestCase):
    def setUp(self):
        fixture = three_role_fixture.ThreeRoleOfflineSignatureTests(
            "test_three_distinct_ephemeral_test_signers_verify_without_io")
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        self.f = fixture

    def run_attempt(self, **overrides):
        params = dict(
            permit_raw=self.f.permit,
            intent_raw=self.f.intent,
            reviewed_sha=self.f.commit,
            at_test_utc=self.f.now,
            actual_source_manifest_sha256=self.f.manifest,
            test_only_proofs=self.f.proofs,
            test_only_public_roots=self.f.roots)
        params.update(overrides)
        return try_admit_signed_test_fixture_offline(**params)

    def test_valid_three_signatures_still_denied_by_same_coordinator(self):
        called = []
        from f0_l2_d1_coordinator import (
            request_physical_source_admission as original)
        def checked(proposal):
            called.append(proposal)
            return original(proposal)
        with (
            patch("f0_l2_d2c_test_proof_admission_offline."
                  "request_physical_source_admission", side_effect=checked),
            patch("http.client.HTTPSConnection",
                  side_effect=AssertionError("REAL_HTTPS_FORBIDDEN")) as https,
            patch.object(socket, "create_connection",
                         side_effect=AssertionError("SOCKET_FORBIDDEN")) as sock,
            patch.object(OfflineGrantRegistry, "consume",
                         side_effect=AssertionError("MARKER_FORBIDDEN")) as mark,
        ):
            with self.assertRaisesRegex(
                    ValueError,
                    "D2A_PHYSICAL_SOURCE_ADMISSION_BLOCKED_D2_D3"):
                self.run_attempt()
            https.assert_not_called()
            sock.assert_not_called()
            mark.assert_not_called()
        self.assertEqual(len(called), 1)
        self.assertIs(type(called[0]), UnreleasedPhysicalHTTPSProposal)
        self.assertEqual(called[0].reviewed_sha, self.f.commit)
        self.assertEqual(called[0].permit_sha256,
                         __import__("hashlib").sha256(self.f.permit).hexdigest())
        self.assertEqual(called[0].candidate_intent_sha256,
                         __import__("hashlib").sha256(self.f.intent).hexdigest())
        self.assertEqual(list(self.f.b.registry.iterdir()), [])
        self.assertEqual(list(self.f.b.out.iterdir()), [])

    def test_tampered_signed_d3_rejected_before_admission(self):
        d3 = dict(json.loads(self.f.intent), min_start_gap_ms=500)
        bad = json.dumps(d3, sort_keys=True).encode()
        with patch(
             "f0_l2_d2c_test_proof_admission_offline."
             "request_physical_source_admission",
             side_effect=AssertionError("GATE_MUST_NOT_BE_CALLED")) as gate:
            with self.assertRaisesRegex(
                    ValueError, "D2B_OPERATOR_SIGNATURE_INVALID"):
                self.run_attempt(intent_raw=bad)
            gate.assert_not_called()

    def test_tampered_d2_but_updated_d3_rejected_before_admission(self):
        d2 = dict(json.loads(self.f.permit), min_start_gap_ms=500)
        d2_raw = json.dumps(d2, sort_keys=True).encode()
        d3 = dict(json.loads(self.f.intent),
                  permit_sha256=__import__("hashlib").sha256(d2_raw).hexdigest(),
                  min_start_gap_ms=500)
        d3_raw = json.dumps(d3, sort_keys=True).encode()
        with patch(
             "f0_l2_d2c_test_proof_admission_offline."
             "request_physical_source_admission",
             side_effect=AssertionError("GATE_MUST_NOT_BE_CALLED")) as gate:
            with self.assertRaisesRegex(
                    ValueError, "D1_SIGNED_PROOF_INVALID"):
                self.run_attempt(permit_raw=d2_raw, intent_raw=d3_raw)
            gate.assert_not_called()

    def test_duplicated_signer_fingerprint_denied_before_admission(self):
        roots = {k: dict(v) for k,v in self.f.roots.items()}
        roots["operator"]["public_pem"] = roots["user"]["public_pem"]
        with patch(
             "f0_l2_d2c_test_proof_admission_offline."
             "request_physical_source_admission",
             side_effect=AssertionError("GATE_MUST_NOT_BE_CALLED")) as gate:
            with self.assertRaisesRegex(
                    ValueError, "D2B_THREE_DISTINCT_SIGNERS_REQUIRED"):
                self.run_attempt(test_only_public_roots=roots)
            gate.assert_not_called()

    def test_test_rehearsal_disabled_if_production_root_enrolled(self):
        with patch(
             "f0_l2_d2c_test_proof_admission_offline.PINNED_LIVE_TRUST_ROOTS",
             {"user": b"not-a-real-key"}), patch(
             "f0_l2_d2c_test_proof_admission_offline."
             "verify_three_role_test_proofs_offline",
             side_effect=AssertionError("VERIFY_MUST_NOT_START")) as verify:
            with self.assertRaisesRegex(
                    ValueError, "D2C_TEST_REHEARSAL_PRODUCTION_ROOTS_PRESENT"):
                self.run_attempt()
            verify.assert_not_called()

    def test_forged_test_diagnostic_is_not_authority(self):
        valid = self.f.check()
        valid["real_user_authorization_proven"] = True
        with patch(
             "f0_l2_d2c_test_proof_admission_offline."
             "verify_three_role_test_proofs_offline",
             return_value=valid), patch(
             "f0_l2_d2c_test_proof_admission_offline."
             "request_physical_source_admission",
             side_effect=AssertionError("GATE_MUST_NOT_BE_CALLED")) as gate:
            with self.assertRaisesRegex(
                    ValueError, "D2C_TEST_DIAGNOSTIC_NOT_AUTHORITY"):
                self.run_attempt()
            gate.assert_not_called()

    def test_even_erroneously_permissive_gate_cannot_return_grant(self):
        with patch(
             "f0_l2_d2c_test_proof_admission_offline."
             "request_physical_source_admission",
             return_value={"fake_grant": True}) as gate:
            with self.assertRaisesRegex(
                    ValueError,
                    "D2C_TEST_FIXTURE_NOT_PRODUCTION_AUTHORIZATION"):
                self.run_attempt()
            gate.assert_called_once()
        with self.assertRaisesRegex(
                ValueError, "D2C_REAL_SOURCE_NOT_RELEASED"):
            send_live(physical=True, grant={"trusted": True})


if __name__ == "__main__":
    unittest.main()
