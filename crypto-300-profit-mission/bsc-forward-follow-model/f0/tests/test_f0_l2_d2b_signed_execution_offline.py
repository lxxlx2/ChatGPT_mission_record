"""D2-B signed 3-role OFFLINE fixtures; keys generated only in memory."""
from __future__ import annotations

import http.client
import json
from pathlib import Path
import socket
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import test_f0_l2_d1_real_sender_contract as binding_fixture
from f0_l2_d1_grant import (
    approval_message, require_ed25519_backend, sha,
    PINNED_LIVE_TRUST_ROOTS)
from f0_l2_d2b_signed_execution_offline import (
    D3_SIGNING_DOMAIN, PRODUCTION_D2_D3_TRUST_ROOTS,
    d3_operator_signing_message, verify_three_role_test_proofs_offline,
    send_live)


class ThreeRoleOfflineSignatureTests(unittest.TestCase):
    def setUp(self):
        self.fixture = binding_fixture.RealSenderContractTests(
            "test_bound_candidate_still_denies_network_and_real_sender")
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.b = self.fixture
        self.permit = self.b.f.raw
        self.intent = self.b.bytes()
        self.commit = self.b.f.sha
        self.manifest = self.b.manifest
        self.now = self.b.f.now
        require_ed25519_backend()
        from cryptography.hazmat.primitives.asymmetric.ed25519 import (
            Ed25519PrivateKey)
        from cryptography.hazmat.primitives.serialization import (
            Encoding, PublicFormat)
        self.private = {}
        self.roots = {}
        self.proofs = {}
        for role in ("user", "reviewer", "operator"):
            key = Ed25519PrivateKey.generate()
            pub = key.public_key().public_bytes(
                Encoding.PEM, PublicFormat.SubjectPublicKeyInfo)
            self.private[role] = key
            self.roots[role] = {
                "key_id": "d2b-" + role + "-fixture-001",
                "public_pem": pub}
            self.proofs[role] = {
                "key_id": self.roots[role]["key_id"],
                "signature": self.signature(role)}

    def signature(self, role, permit=None, intent=None, manifest=None,
                  reviewed=None):
        permit = self.permit if permit is None else permit
        intent = self.intent if intent is None else intent
        manifest = self.manifest if manifest is None else manifest
        reviewed = self.commit if reviewed is None else reviewed
        if role == "operator":
            message = d3_operator_signing_message(
                sha(intent), sha(permit), reviewed, manifest)
        else:
            message = approval_message(role, sha(permit), reviewed)
        return self.private[role].sign(message)

    def check(self, *, permit=None, intent=None, roots=None, proofs=None,
              reviewed=None, manifest=None, now=None):
        return verify_three_role_test_proofs_offline(
            self.permit if permit is None else permit,
            self.intent if intent is None else intent,
            self.commit if reviewed is None else reviewed,
            self.now if now is None else now,
            actual_source_manifest_sha256=(
                self.manifest if manifest is None else manifest),
            test_only_public_roots=self.roots if roots is None else roots,
            test_only_proofs=self.proofs if proofs is None else proofs)

    def test_three_distinct_ephemeral_test_signers_verify_without_io(self):
        from f0_l2_d1_grant import OfflineGrantRegistry
        with (
            patch("http.client.HTTPSConnection",
                  side_effect=AssertionError("HTTPS_FORBIDDEN")) as conn,
            patch.object(socket, "create_connection",
                         side_effect=AssertionError("SOCKET_FORBIDDEN")) as sock,
            patch.object(OfflineGrantRegistry, "consume",
                         side_effect=AssertionError("LEASE_FORBIDDEN")) as marker,
        ):
            result = self.check()
            conn.assert_not_called()
            sock.assert_not_called()
            marker.assert_not_called()
        self.assertTrue(result["test_only_signatures_cryptographically_valid"])
        self.assertEqual(result["test_only_roles"],
                         ["user", "reviewer", "operator"])
        self.assertFalse(result["production_trust_roots_enrolled"])
        self.assertFalse(result["real_user_authorization_proven"])
        self.assertEqual(result["actual_rpc_requests"], 0)
        self.assertEqual(result["decision"], "D1_BLOCKED_AUTHORITY")
        self.assertEqual(list(self.b.registry.iterdir()), [])

    def test_mutated_d3_bytes_but_valid_candidate_scope_break_signature(self):
        changed = dict(json.loads(self.intent), min_start_gap_ms=500)
        new_raw = json.dumps(changed, sort_keys=True).encode()
        with self.assertRaisesRegex(
                ValueError, "D2B_OPERATOR_SIGNATURE_INVALID"):
            self.check(intent=new_raw)

    def test_mutated_d2_permit_bytes_cannot_reuse_two_old_signatures(self):
        permit = dict(json.loads(self.permit), min_start_gap_ms=500)
        new_permit = json.dumps(permit, sort_keys=True).encode()
        d3 = dict(json.loads(self.intent),
                  permit_sha256=sha(new_permit), min_start_gap_ms=500)
        new_intent = json.dumps(d3, sort_keys=True).encode()
        with self.assertRaisesRegex(ValueError, "D1_SIGNED_PROOF_INVALID"):
            self.check(permit=new_permit, intent=new_intent)

    def test_d3_signature_cannot_be_d2_signature_or_wrong_domain(self):
        for signature in (self.proofs["user"]["signature"],
                          self.proofs["reviewer"]["signature"],
                          self.private["operator"].sign(
                              b"wrong-domain\n" + sha(self.intent).encode())):
            proofs = {k: dict(v) for k, v in self.proofs.items()}
            proofs["operator"]["signature"] = signature
            with self.assertRaisesRegex(
                    ValueError, "D2B_OPERATOR_SIGNATURE_INVALID"):
                self.check(proofs=proofs)
        self.assertIn("TEST-ONLY", D3_SIGNING_DOMAIN)

    def test_operator_must_not_reuse_d2_user_or_reviewer_key(self):
        for role in ("user", "reviewer"):
            roots = {k: dict(v) for k, v in self.roots.items()}
            roots["operator"]["public_pem"] = roots[role]["public_pem"]
            proofs = {k: dict(v) for k, v in self.proofs.items()}
            proofs["operator"]["signature"] = self.private[role].sign(
                d3_operator_signing_message(
                    sha(self.intent), sha(self.permit),
                    self.commit, self.manifest))
            with self.assertRaisesRegex(
                    ValueError, "D2B_THREE_DISTINCT_SIGNERS_REQUIRED"):
                self.check(roots=roots, proofs=proofs)

    def test_key_id_alias_or_extra_role_refused(self):
        roots = {k: dict(v) for k, v in self.roots.items()}
        proofs = {k: dict(v) for k, v in self.proofs.items()}
        roots["operator"]["key_id"] = roots["user"]["key_id"]
        proofs["operator"]["key_id"] = roots["operator"]["key_id"]
        with self.assertRaisesRegex(
                ValueError, "D2B_THREE_DISTINCT_SIGNERS_REQUIRED"):
            self.check(roots=roots, proofs=proofs)
        with self.assertRaisesRegex(ValueError, "D2B_ROLES_EXACTLY_THREE"):
            self.check(roots=dict(self.roots, fourth={}))
        with self.assertRaisesRegex(ValueError, "D2B_ROLES_EXACTLY_THREE"):
            self.check(proofs={"user": self.proofs["user"],
                               "reviewer": self.proofs["reviewer"]})

    def test_unauthorized_source_digest_sha_and_time_denied(self):
        with self.assertRaisesRegex(ValueError, "IDENTITY_MISMATCH"):
            self.check(manifest="f" * 64)
        with self.assertRaisesRegex(ValueError, "CODE_SHA_MISMATCH"):
            self.check(reviewed="f" * 40)
        from datetime import timedelta
        with self.assertRaisesRegex(ValueError, "WINDOW_INACTIVE"):
            self.check(now=self.now + timedelta(hours=1))

    def test_operator_proof_malformed_key_or_signature_refused(self):
        for change in (
                {"signature": b"x" * 63},
                {"signature": b"x" * 64},
                {"signature": None},
                {"key_id": "bad"},
                {"extra": True}):
            proof = dict(self.proofs["operator"], **change)
            proofs = dict(self.proofs, operator=proof)
            with self.assertRaises(ValueError):
                self.check(proofs=proofs)
        roots = {k: dict(v) for k, v in self.roots.items()}
        roots["operator"]["public_pem"] = b"not-ed25519"
        with self.assertRaises(ValueError):
            self.check(roots=roots)

    def test_duplicate_d3_json_fields_and_widened_scope_denied(self):
        duplicate = self.intent[:-1] + b',"run_id":"forged-run-test-001"}'
        with self.assertRaisesRegex(ValueError, "DUPLICATE_JSON_FIELD"):
            self.check(intent=duplicate)
        changed = dict(json.loads(self.intent), max_inflight=4)
        with self.assertRaisesRegex(ValueError, "SHARED_SLOT_NOT_THREE"):
            self.check(intent=json.dumps(changed).encode())

    def test_never_enrolls_real_trust_or_releases_sender(self):
        self.assertEqual(PRODUCTION_D2_D3_TRUST_ROOTS, {})
        self.assertEqual(PINNED_LIVE_TRUST_ROOTS, {})
        with patch("http.client.HTTPSConnection",
                   side_effect=AssertionError("NETWORK_FORBIDDEN")) as ctor:
            with self.assertRaisesRegex(
                    ValueError, "D2B_LIVE_SENDER_NOT_AUTHORIZED"):
                send_live(self.check(), allow=True)
            ctor.assert_not_called()
        self.assertEqual(list(self.b.registry.iterdir()), [])
        self.assertEqual(list(self.b.out.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
