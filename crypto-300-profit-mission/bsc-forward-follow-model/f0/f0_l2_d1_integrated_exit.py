#!/usr/bin/env python3
"""F0 D1 single OFFLINE integrated gate and non-authorizing exit verdict.

Pinned test provenance -> signed scoped fake grant -> O_EXCL/fsync test registry
-> one sealed-memory 3-slot session -> read-only durable ledger audit.

No actual HTTPS factory, sender callback, trusted UTC source, production roots,
real signer enrollment, real nonce or production registry can enter this path.
Production exit is deliberately BLOCKED_AUTHORITY until a NEW independently
reviewed implementation supplies all actual prerequisites. It is not possible
to promote this test result to a live authorization by changing inputs.
"""
from __future__ import annotations

from f0_l2_d1_coordinator import SealedMemoryHTTPSSource
from f0_l2_d1_concrete_https import SealedConcreteOfflineSource
from f0_l2_d1_grant import PINNED_LIVE_TRUST_ROOTS
from f0_l2_d1_inventory_gate import consume_then_run_fake_once
from f0_l2_d1_review_pins import (
    OfflineReviewerPins, verify_pinned_offline_evidence,
)


def production_d1_exit_verdict():
    """Static current-source exit decision; no caller-provided trust flags."""
    # The test "pins" are *not* independent user authentication and the
    # installed wheel/Python inventory explicitly claims incomplete closure.
    # A registered public key alone could not satisfy D1: there must also be
    # independent source provenance, issuer authority, trusted time, and a
    # real sender joined to fsync-before-network and raw-before-settle.
    blockers = (
        "G02_INDEPENDENT_FULL_RUNTIME_CLOSURE_UNPROVEN",
        "G03_G04_INDEPENDENT_HUMAN_IDENTITIES_AND_TRUSTED_UTC_ABSENT",
        "G05_G06_PRODUCTION_ONCE_REGISTRY_NOT_BOUND_TO_SENDER",
        "J02_J03_J06_REAL_THREE_SLOT_TLS_AND_JOURNAL_NOT_INTEGRATED",
        "J10_REAL_SOCKET_CRASH_RECOVERY_UNVERIFIED",
        "M02_M03_REAL_PROVIDER_CAPACITY_UNMEASURED",
    )
    return {
        "status": "D1_BLOCKED_AUTHORITY",
        "blockers": list(blockers),
        "enrolled_production_root_count": len(PINNED_LIVE_TRUST_ROOTS),
        "offline_tests_can_authorize_live": False,
        "d2_actual_permit_authorized": False,
        "d3_real_sampling_authorized": False,
        "f0_status": "F0_NOT_PASSED",
        "production": "PRODUCTION_NO_GO",
    }


def send_live(*_args, **_kwargs):
    """Single D1 integration entry: never contacts network or consumes nonce."""
    raise ValueError("D1_BLOCKED_AUTHORITY_NO_NETWORK_OR_PERMIT")


def run_offline_integrated_fake_with_pins(
        source, evidence_root, *, permit_raw, expected_sha, proofs,
        test_only_trust_roots, checkout_root, reviewed_files, now,
        raw_inventory_statement, inventory_signatures,
        offline_test_registry_root, externally_provided_test_pins,
        test_only_fake_post_utc_clock):
    """Exercise already-approved fake modules under ONE pre-consumption gate.

    This function intentionally accepts NO HTTPS constructor, arbitrary
    request sender, production root, execution mode, or trusted real clock.
    Even valid caller-supplied pins/keys cannot grant network permission.
    """
    if type(source) not in (SealedMemoryHTTPSSource,
                            SealedConcreteOfflineSource):
        raise ValueError("D1_INTEGRATED_SEALED_MEMORY_SOURCE_ONLY")
    if (type(externally_provided_test_pins) is not OfflineReviewerPins
            or not callable(test_only_fake_post_utc_clock)):
        raise ValueError("D1_INTEGRATED_TEST_REFERENCE_OR_CLOCK_REQUIRED")
    checked = verify_pinned_offline_evidence(
        permit_raw, expected_sha, checkout_root,
        raw_inventory_statement, inventory_signatures,
        test_only_trust_roots, externally_provided_test_pins)
    if checked["status"] != "OFFLINE_EXTERNAL_PIN_MATCH_NOT_AUTHORIZATION":
        raise ValueError("D1_INTEGRATED_PIN_NOT_ACCEPTED")
    # Pinned approval+installed bytes verified before any registry mutation.
    # The callee repeats exact ephemeral user/reviewer signature, checkout,
    # signed-UTC budget and identity checks before spending its TEST grant.
    session = consume_then_run_fake_once(
        source, evidence_root, permit_raw=permit_raw,
        expected_sha=expected_sha, proofs=proofs,
        test_only_trust_roots=test_only_trust_roots,
        checkout_root=checkout_root, reviewed_files=reviewed_files,
        now=now, raw_inventory_statement=raw_inventory_statement,
        inventory_signatures=inventory_signatures,
        offline_test_registry_root=offline_test_registry_root,
        test_only_fake_post_utc_clock=test_only_fake_post_utc_clock)
    if (session["session"]["fake"]["network_requests"] != 0
            or session["actual_rpc_requests"] != 0
            or session["session"]["actual_rpc_requests"] != 0):
        raise ValueError("D1_INTEGRATED_REAL_NETWORK_CLAIM_FORBIDDEN")
    return {
        "mode": "D1_END_TO_END_OFFLINE_FAKE_REHEARSAL_NOT_LIVE",
        "pinned_test_evidence": checked,
        "test_one_use_session": session,
        "audit_status": session["session"]["audit"]["audit_status"],
        "d1_exit": production_d1_exit_verdict(),
        "actual_rpc_requests": 0,
        "never_promote_test_evidence_to_authority": True,
    }
