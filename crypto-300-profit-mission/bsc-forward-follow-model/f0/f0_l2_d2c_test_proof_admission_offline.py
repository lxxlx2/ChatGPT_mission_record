"""D2-C offline signed-fixture -> SINGLE closed coordinator admission seam.

The test fixture's caller-supplied public keys are NOT enrolled authorities.
No output path, constructor/factory, socket, nonce, scheduler or send switch
is accepted here. Even a cryptographically valid TEST fixture is refused.
"""
from __future__ import annotations

from datetime import datetime

from f0_l2_d1_grant import PINNED_LIVE_TRUST_ROOTS
from f0_l2_d2b_signed_execution_offline import (
    PRODUCTION_D2_D3_TRUST_ROOTS, verify_three_role_test_proofs_offline,
)
from f0_l2_d2a_physical_admission import UnreleasedPhysicalHTTPSProposal
from f0_l2_d1_coordinator import request_physical_source_admission


def try_admit_signed_test_fixture_offline(
        permit_raw: bytes, intent_raw: bytes, reviewed_sha: str,
        at_test_utc: datetime, *, actual_source_manifest_sha256: str,
        test_only_proofs: dict, test_only_public_roots: dict):
    """Check TEST signatures then unconditionally refuse the SAME source gate.

    No return value can be used as authorization. If signed inputs are
    invalid, stop at D2-B. If they validate against injected test roots,
    construct a non-executable D2-A descriptor and call the original
    coordinator's permanently closed admission function. NEVER dispatch.
    """
    if (PINNED_LIVE_TRUST_ROOTS != {}
            or PRODUCTION_D2_D3_TRUST_ROOTS != {}):
        raise ValueError("D2C_TEST_REHEARSAL_PRODUCTION_ROOTS_PRESENT")
    diagnostic = verify_three_role_test_proofs_offline(
        permit_raw, intent_raw, reviewed_sha, at_test_utc,
        actual_source_manifest_sha256=actual_source_manifest_sha256,
        test_only_proofs=test_only_proofs,
        test_only_public_roots=test_only_public_roots)
    if (type(diagnostic) is not dict
            or diagnostic.get("verified_for") !=
                "OFFLINE_EPHEMERAL_TEST_ROOTS_ONLY"
            or diagnostic.get("test_only_signatures_cryptographically_valid")
                is not True
            or diagnostic.get("production_trust_roots_enrolled") is not False
            or diagnostic.get("real_user_authorization_proven") is not False
            or diagnostic.get("physical_sender_constructed") is not False
            or diagnostic.get("actual_rpc_requests") != 0
            or diagnostic.get("decision") != "D1_BLOCKED_AUTHORITY"
            or diagnostic.get("production") != "PRODUCTION_NO_GO"):
        raise ValueError("D2C_TEST_DIAGNOSTIC_NOT_AUTHORITY")
    proposal = UnreleasedPhysicalHTTPSProposal(
        reviewed_sha=diagnostic["approved_commit_sha"],
        source_manifest_sha256=diagnostic["source_manifest_sha256"],
        permit_sha256=diagnostic["permit_sha256"],
        candidate_intent_sha256=diagnostic["intent_sha256"])
    # The SAME D2-A source gate inside the single reviewed coordinator.
    # This raises on every path. Do not add an alternate admission path.
    request_physical_source_admission(proposal)
    # Fail even if a future edit accidentally turns the gate into a
    # permissive no-op. This point is not an executable dispatcher.
    raise ValueError("D2C_TEST_FIXTURE_NOT_PRODUCTION_AUTHORIZATION")


def send_live(*_args, **_kwargs):
    raise ValueError("D2C_REAL_SOURCE_NOT_RELEASED")
