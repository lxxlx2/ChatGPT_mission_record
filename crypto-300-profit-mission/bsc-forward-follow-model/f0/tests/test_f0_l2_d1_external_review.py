"""Strictly offline reviewer reference tests, ephemeral keys and temp Git."""
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import f0_l2_d1_external_review as review
from f0_l2_d1_grant import _public_key_fingerprint


def git(root, *args):
    return subprocess.run(
        ["git", "-C", str(root), *args], check=True,
        capture_output=True, text=True).stdout.strip()


class D1IndependentReviewTests(unittest.TestCase):
    def setUp(self):
        from cryptography.hazmat.primitives.asymmetric.ed25519 import (
            Ed25519PrivateKey)
        from cryptography.hazmat.primitives.serialization import (
            Encoding, PublicFormat)
        self.holder = tempfile.TemporaryDirectory()
        self.addCleanup(self.holder.cleanup)
        self.root = Path(self.holder.name).absolute() / "project"
        self.root.mkdir(mode=0o700)
        git(self.root, "init", "-q")
        git(self.root, "config", "user.name", "Offline Reviewer")
        git(self.root, "config", "user.email", "offline@example.invalid")
        self.src = (
            self.root /
            "crypto-300-profit-mission/bsc-forward-follow-model/f0/offline.py"
        )
        self.src.parent.mkdir(parents=True)
        self.src.write_text("OFFLINE\n")
        git(self.root, "add", ".")
        git(self.root, "commit", "-qm", "fixture")
        self.commit = git(self.root, "rev-parse", "HEAD")
        self.private_key = Ed25519PrivateKey.generate()
        self.alternate_key = Ed25519PrivateKey.generate()
        self.public_pem = self.private_key.public_key().public_bytes(
            Encoding.PEM, PublicFormat.SubjectPublicKeyInfo)
        self.key_id = "independent-ephemeral-reviewer"
        self.permit = {
            "approved_commit_sha": self.commit,
            "grant_id": "offline-review-gate-00001",
            "endpoint": "https://bsc-dataseed.bnbchain.org",
            "chain_id": 56,
            "methods": ["eth_chainId", "eth_blockNumber",
                        "eth_getBlockByNumber"],
            "read_only": True, "free_only": True, "no_retries": True,
            "no_ws": True, "background": False,
            "no_proxy": True, "no_redirects": True,
            "max_total_attempts": 6, "max_block_reads": 3,
            "max_head_refreshes": 1, "max_inflight": 3,
            "min_start_gap_ms": 250, "head_ttl_ms": 4000,
            "request_timeout_ms": 5000, "max_response_bytes": 2_000_000,
            "max_dispatch_seconds": 10,
            "window_start_utc": "2026-10-23T08:00:00Z",
            "window_end_utc": "2026-10-23T08:01:00Z",
        }
        self.permit_raw = json.dumps(
            self.permit, sort_keys=True, separators=(",", ":")).encode()
        self.reference = review.build_local_review_reference_offline(
            permit_raw=self.permit_raw, checkout_root=self.root,
            reviewed_commit_sha=self.commit, reviewer_key_id=self.key_id,
            reviewer_public_fingerprint=_public_key_fingerprint(
                self.public_pem))
        self.raw = json.dumps(
            self.reference, sort_keys=True, separators=(",", ":")).encode()
        self.signature = self.private_key.sign(
            review.reviewer_attestation_message(self.raw))

    def verify(self, raw=None, signature=None, permit_raw=None):
        with patch.object(review, "PINNED_REVIEW_AUTHORITY_KEY_ID",
                          self.key_id), patch.object(
                review, "PINNED_REVIEW_AUTHORITY_PUBLIC_PEM",
                self.public_pem):
            return review.verify_independently_signed_reference_offline(
                raw_reference=self.raw if raw is None else raw,
                signature=self.signature if signature is None else signature,
                permit_raw=self.permit_raw if permit_raw is None
                else permit_raw, checkout_root=self.root)

    def test_default_unenrolled_authority_never_passes(self):
        self.assertIsNone(review.PINNED_REVIEW_AUTHORITY_KEY_ID)
        self.assertIsNone(review.PINNED_REVIEW_AUTHORITY_PUBLIC_PEM)
        with self.assertRaisesRegex(ValueError,
                                    "D1_REVIEW_AUTHORITY_NOT_ENROLLED"):
            review.verify_independently_signed_reference_offline(
                raw_reference=self.raw, signature=self.signature,
                permit_raw=self.permit_raw, checkout_root=self.root)

    def test_independently_pinned_fixture_signature_matches_local_bytes(self):
        result = self.verify()
        self.assertEqual(
            result["status"],
            "OFFLINE_INDEPENDENT_REFERENCE_MATCH_PARTIAL_ONLY")
        self.assertEqual(result["reviewed_commit_sha"], self.commit)
        self.assertEqual(result["tracked_f0_file_count"], 1)
        self.assertFalse(result["complete_runtime_closure_attested"])
        self.assertFalse(result["production_user_consent_verified"])
        self.assertFalse(result["live_sender_authorized"])
        self.assertFalse(result["grant_consumed"])
        self.assertEqual(result["actual_rpc_requests"], 0)

    def test_operator_cannot_substitute_self_signed_key(self):
        fake_signature = self.alternate_key.sign(
            review.reviewer_attestation_message(self.raw))
        with self.assertRaisesRegex(ValueError,
                                    "D1_REVIEW_SIGNATURE_INVALID"):
            self.verify(signature=fake_signature)

    def test_valid_reviewer_signature_on_wrong_measured_bytes_is_denied(self):
        for field, forged in (
            ("tracked_f0_manifest_sha256", "f"*64),
            ("wheel_file_manifest_sha256", "f"*64),
            ("python_executable_sha256", "f"*64),
            ("permit_sha256", "f"*64),
            ("tracked_f0_file_count", 2000),
            ("wheel_entries_without_record_sha256", 0),
        ):
            with self.subTest(field=field):
                mutated = dict(self.reference, **{field: forged})
                raw = json.dumps(
                    mutated, sort_keys=True, separators=(",", ":")).encode()
                signed = self.private_key.sign(
                    review.reviewer_attestation_message(raw))
                with self.assertRaisesRegex(
                        ValueError,
                        "D1_REVIEW_SIGNED_REFERENCE_DOES_NOT_MATCH_RUNTIME"):
                    self.verify(raw=raw, signature=signed)

    def test_wrong_commit_or_dirty_tree_is_denied(self):
        self.src.write_text("CHANGED\n")
        with self.assertRaisesRegex(ValueError, "D1_CHECKOUT_DIRTY"):
            self.verify()
        self.src.write_text("OFFLINE\n")
        altered_permit = dict(self.permit,
                              grant_id="different-offline-grant-0002")
        raw = json.dumps(altered_permit, sort_keys=True,
                         separators=(",", ":")).encode()
        with self.assertRaisesRegex(ValueError,
                                    "D1_REVIEW_SIGNED_REFERENCE_DOES_NOT_MATCH_RUNTIME"):
            self.verify(permit_raw=raw)

    def test_duplicates_extra_fields_and_false_closure_denied(self):
        for raw in (
            self.raw[:-1] + b',"schema":"duplicate"}',
            json.dumps(dict(self.reference, enable_live=True)).encode(),
            json.dumps(dict(
                self.reference, complete_runtime_closure_attested=True)
                       ).encode(),
        ):
            with self.assertRaises(ValueError):
                self.verify(raw=raw)

    def test_pinned_key_id_mismatch_not_authority(self):
        alias = dict(self.reference, reviewer_key_id="unrelated-key-id")
        raw = json.dumps(alias, sort_keys=True,
                         separators=(",", ":")).encode()
        signed = self.private_key.sign(
            review.reviewer_attestation_message(raw))
        with self.assertRaisesRegex(ValueError,
                                    "D1_REVIEW_INDEPENDENT_AUTHORITY_ID_MISMATCH"):
            self.verify(raw=raw, signature=signed)


if __name__ == "__main__":
    unittest.main()
