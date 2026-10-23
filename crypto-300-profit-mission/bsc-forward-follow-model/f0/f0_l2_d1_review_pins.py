"""Offline verifier requiring independent predeclared evidence digests.

The verifier DOES NOT enroll production identities or enable HTTP.
"""
from dataclasses import dataclass
from hashlib import sha256
import re

from f0_l2_d1_grant import _public_key_fingerprint
from f0_l2_d1_inventory_gate import verify_test_inventory_attestation

HEX40 = re.compile(r"[0-9a-f]{40}\\Z")
HEX64 = re.compile(r"[0-9a-f]{64}\\Z")


@dataclass(frozen=True)
class OfflineReviewerPins:
    source_sha: str
    permit_digest: str
    inventory_digest: str
    user_fingerprint: str
    reviewer_fingerprint: str


def verify_pinned_offline_evidence(permit_raw, source_sha, checkout_root,
                                   inventory_raw, signatures, trust_roots,
                                   pins):
    if type(pins) is not OfflineReviewerPins:
        raise ValueError("D1_EXTERNAL_PINS_REQUIRED")
    digests = (pins.permit_digest, pins.inventory_digest,
               pins.user_fingerprint, pins.reviewer_fingerprint)
    if (type(source_sha) is not str or not HEX40.fullmatch(source_sha)
            or type(pins.source_sha) is not str
            or not HEX40.fullmatch(pins.source_sha)
            or not all(type(x) is str and HEX64.fullmatch(x)
                       for x in digests)):
        raise ValueError("D1_EXTERNAL_PIN_FORMAT_INVALID")
    if (type(permit_raw) is not bytes or type(inventory_raw) is not bytes
            or not 0 < len(permit_raw) <= 8192
            or not 0 < len(inventory_raw) <= 8192):
        raise ValueError("D1_EXTERNAL_PIN_INPUT_INVALID")
    if (source_sha != pins.source_sha
            or sha256(permit_raw).hexdigest() != pins.permit_digest
            or sha256(inventory_raw).hexdigest() != pins.inventory_digest):
        raise ValueError("D1_EXTERNAL_PIN_BYTES_MISMATCH")
    if (pins.user_fingerprint == pins.reviewer_fingerprint
            or type(trust_roots) is not dict
            or set(trust_roots) != {"user", "reviewer"}):
        raise ValueError("D1_EXTERNAL_PIN_ROLES_INVALID")
    for role, expected in (("user", pins.user_fingerprint),
                           ("reviewer", pins.reviewer_fingerprint)):
        row = trust_roots[role]
        if (type(row) is not dict
                or set(row) != {"key_id", "public_pem"}
                or type(row["public_pem"]) is not bytes):
            raise ValueError("D1_EXTERNAL_PIN_KEY_INVALID")
        if _public_key_fingerprint(row["public_pem"]) != expected:
            raise ValueError("D1_EXTERNAL_PIN_KEY_MISMATCH")
    evidence = verify_test_inventory_attestation(
        permit_raw, source_sha, checkout_root, inventory_raw,
        signatures, trust_roots)
    if (evidence["inventory_statement_sha256"] != pins.inventory_digest
            or evidence["complete_dependency_closure_attested"] is not False):
        raise ValueError("D1_EXTERNAL_PIN_INVENTORY_INCOMPLETE")
    return {
        "status": "OFFLINE_EXTERNAL_PIN_MATCH_NOT_AUTHORIZATION",
        "source_sha": pins.source_sha,
        "inventory_digest": pins.inventory_digest,
        "independent_pin_origin_authenticated": False,
        "complete_dependency_closure_attested": False,
        "production_trust_roots_enrolled": False,
        "actual_rpc_requests": 0,
        "production": "NO_GO",
    }
