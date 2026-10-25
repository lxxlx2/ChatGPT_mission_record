"""D2-B OFFLINE-only three-signature D2/D3 proof composition.

Verifies ephemeral TEST roots only. Neither valid fixture signatures nor the
signed D3 JSON constitutes an independently enrolled production authority.
No live sender, production registry, key issuer, filesystem or socket here.
"""
from __future__ import annotations

from datetime import datetime
from hashlib import sha256

from f0_l2_d1_grant import (
    GRANT_ID, HEX40, HEX64, _public_key_fingerprint,
    _verify_signature, validate_approvals_offline,
)
from f0_l2_d1_real_sender_contract import bind_real_https_candidate_offline

D3_SIGNING_DOMAIN = "bsc-f0-d2b-one-shot-operator-signature-TEST-ONLY-v1"
# INTENTIONALLY NOT ENROLLED; user-supplied test roots must never unlock live.
PRODUCTION_D2_D3_TRUST_ROOTS = {}


def d3_operator_signing_message(intent_sha256, permit_sha256,
                                reviewed_sha, source_manifest_sha256):
    """Domain-separate a single exact D3 intent from both D2 signatures."""
    if (any(type(x) is not str for x in (
            intent_sha256, permit_sha256, reviewed_sha,
            source_manifest_sha256))
            or not HEX64.fullmatch(intent_sha256)
            or not HEX64.fullmatch(permit_sha256)
            or not HEX40.fullmatch(reviewed_sha)
            or not HEX64.fullmatch(source_manifest_sha256)):
        raise ValueError("D2B_D3_MESSAGE_BINDING_INVALID")
    return ("\n".join((D3_SIGNING_DOMAIN, intent_sha256,
                       permit_sha256, reviewed_sha,
                       source_manifest_sha256)) + "\n").encode("ascii")


def verify_three_role_test_proofs_offline(
        permit_raw: bytes, intent_raw: bytes, reviewed_sha: str,
        at_test_utc: datetime, *, actual_source_manifest_sha256: str,
        test_only_proofs: dict, test_only_public_roots: dict):
    """Read/test Ed25519 proofs, NEVER issue a live authorization.

    All public roots are CALLER INJECTED, so this can only prove fixture
    signatures match those untrusted keys. A return value is diagnostic
    and must never be accepted by D2/D3 production admission.
    """
    if (type(test_only_proofs) is not dict or
            set(test_only_proofs) != {"user", "reviewer", "operator"} or
            type(test_only_public_roots) is not dict or
            set(test_only_public_roots) != {"user", "reviewer", "operator"}):
        raise ValueError("D2B_ROLES_EXACTLY_THREE_REQUIRED")

    # Strict existing D2/D3 candidate validation binds raw bytes, reviewed
    # source, manifest, fixed BSC endpoint, UTC and all numeric caps.
    # It does NOT produce an executable source object or a live grant.
    candidate = bind_real_https_candidate_offline(
        permit_raw, intent_raw, reviewed_sha, at_test_utc,
        actual_source_manifest_sha256=actual_source_manifest_sha256)
    user_reviewer = validate_approvals_offline(
        permit_raw, reviewed_sha,
        {r: test_only_proofs[r] for r in ("user", "reviewer")},
        {r: test_only_public_roots[r] for r in ("user", "reviewer")})

    proof = test_only_proofs["operator"]
    trust = test_only_public_roots["operator"]
    if (type(proof) is not dict or set(proof) != {"key_id", "signature"}
            or type(trust) is not dict
            or set(trust) != {"key_id", "public_pem"}
            or type(proof["key_id"]) is not str
            or not GRANT_ID.fullmatch(proof["key_id"])
            or proof["key_id"] != trust["key_id"]
            or type(trust["public_pem"]) is not bytes):
        raise ValueError("D2B_OPERATOR_IDENTITY_INVALID")

    # Enforce three different actual Ed25519 public-key bytes, not merely
    # three labels or aliases for the same PEM key.
    fingerprints = []
    names = []
    for role in ("user", "reviewer", "operator"):
        role_proof = test_only_proofs[role]
        role_root = test_only_public_roots[role]
        names.append(role_proof["key_id"])
        fingerprints.append(
            _public_key_fingerprint(role_root["public_pem"]))
    if len(set(names)) != 3 or len(set(fingerprints)) != 3:
        raise ValueError("D2B_THREE_DISTINCT_SIGNERS_REQUIRED")

    permit_digest = sha256(permit_raw).hexdigest()
    intent_digest = sha256(intent_raw).hexdigest()
    message = d3_operator_signing_message(
        intent_digest, permit_digest, reviewed_sha,
        actual_source_manifest_sha256)
    if not _verify_signature(
            trust["public_pem"], message, proof["signature"]):
        raise ValueError("D2B_OPERATOR_SIGNATURE_INVALID")

    if (user_reviewer["permit_sha256"] != candidate.permit_sha256
            or user_reviewer["commit_sha"] !=
            candidate.approved_commit_sha
            or candidate.candidate_intent_sha256 != intent_digest
            or candidate.candidate_source_manifest_sha256 !=
            actual_source_manifest_sha256):
        raise ValueError("D2B_CROSS_SIGNATURE_BINDING_MISMATCH")
    return {
        "schema": "f0-d2b-three-role-signed-fixture-no-network-v1",
        "test_only_signatures_cryptographically_valid": True,
        "verified_for": "OFFLINE_EPHEMERAL_TEST_ROOTS_ONLY",
        "approved_commit_sha": reviewed_sha,
        "permit_sha256": permit_digest,
        "intent_sha256": intent_digest,
        "source_manifest_sha256": actual_source_manifest_sha256,
        "test_only_roles": ["user", "reviewer", "operator"],
        "production_trust_roots_enrolled": False,
        "real_user_authorization_proven": False,
        "production_registry_consumed": False,
        "physical_sender_constructed": False,
        "actual_rpc_requests": 0,
        "decision": "D1_BLOCKED_AUTHORITY",
        "production": "PRODUCTION_NO_GO",
    }


def send_live(*_args, **_kwargs):
    raise ValueError("D2B_LIVE_SENDER_NOT_AUTHORIZED")
