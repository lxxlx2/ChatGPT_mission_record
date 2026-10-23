#!/usr/bin/env python3
"""D1 fake-only composed approval/checkout/scope gate and audit.

This module deliberately has NO live-sender callback, installed production
trust roots, permit issuer or grant-consumption capability. Its injected
temporary keys and reviewed file hashes support OFFLINE tests only.
"""
from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path

from f0_l2_d1_coordinator import (FakeSource, SealedMemoryHTTPSSource,
                                      run_fake_concurrent)
from f0_l2_d1_grant import (require_ed25519_backend,
                            validate_approvals_offline)
from f0_l2_d1_preflight import (validate_window_contract,
                               verify_fixed_checkout_offline)
from f0_l2_d1_recovery import reconcile_saved_attempts

REQUIRED_PERMIT_KEYS = frozenset({
    "approved_commit_sha", "grant_id", "endpoint", "chain_id", "methods",
    "read_only", "free_only", "no_retries", "no_ws", "background",
    "no_proxy", "no_redirects", "max_total_attempts", "max_block_reads",
    "max_head_refreshes", "max_inflight", "min_start_gap_ms",
    "head_ttl_ms", "request_timeout_ms", "max_response_bytes",
    "max_dispatch_seconds", "window_start_utc", "window_end_utc",
})


def _reject_duplicate_fields(pairs):
    result = {}
    for name, value in pairs:
        if name in result:
            raise ValueError("D1_BUNDLE_DUPLICATE_JSON_FIELD")
        result[name] = value
    return result


def _strict_permit(permit_raw):
    if type(permit_raw) is not bytes or not 0 < len(permit_raw) <= 8192:
        raise ValueError("D1_BUNDLE_PERMIT_BYTES_INVALID")
    try:
        value = json.loads(permit_raw, object_pairs_hook=_reject_duplicate_fields)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("D1_BUNDLE_PERMIT_JSON_INVALID") from exc
    if type(value) is not dict or set(value) != REQUIRED_PERMIT_KEYS:
        raise ValueError("D1_BUNDLE_UNREVIEWED_PERMIT_FIELDS")
    return value


def validate_offline_bundle(permit_raw, expected_sha, proofs,
                            test_only_trust_roots, checkout_root,
                            reviewed_files, now):
    """Compose three distinct D1 checks; result NEVER becomes a live permit.

    Critical: test_only_trust_roots and reviewed_files are INJECTED and can be
    user-supplied. That is acceptable ONLY because no live sender is exposed.
    Production must pin independently authenticated roots+complete code and
    dependency closure in another audited commit before D2.
    """
    if not isinstance(checkout_root, Path) or not isinstance(now, datetime):
        raise ValueError("D1_BUNDLE_ARGUMENT_INVALID")
    permit = _strict_permit(permit_raw)
    if permit.get("approved_commit_sha") != expected_sha:
        raise ValueError("D1_BUNDLE_SHA_NOT_BOUND")
    require_ed25519_backend()
    proof = validate_approvals_offline(
        permit_raw, expected_sha, proofs, test_only_trust_roots)
    scope = validate_window_contract(permit, now)
    source = verify_fixed_checkout_offline(
        checkout_root, expected_sha, reviewed_files)
    if proof["commit_sha"] != source["head_sha"] or (
        scope["approved_commit_sha"] != proof["commit_sha"]
    ):
        raise ValueError("D1_BUNDLE_CROSS_GATE_MISMATCH")
    return {
        "status": "OFFLINE_BUNDLE_VALIDATED_NO_NETWORK_PERMISSION",
        "fake_only": True,
        "production_trust_root_enrolled": False,
        "real_grant_activated": False,
        "code_sha": proof["commit_sha"],
        "permit_sha256": proof["permit_sha256"],
        "user_key_id": proof["user_key_id"],
        "reviewer_key_id": proof["reviewer_key_id"],
        "manifest_entries_checked": source["verified_files"],
    }


def run_gated_fake_session(source, evidence_root, *, permit_raw,
                           expected_sha, proofs, test_only_trust_roots,
                           checkout_root, reviewed_files, now,
                           test_only_fake_post_utc_clock=None):
    """Fake-only end-to-end rehearsal: checks -> fake dispatch -> raw audit.

    The only worker type accepted is the original in-memory FakeSource.
    No HTTPS connection factory, transport callback, nonce consume or real
    authority can be injected through this function.
    """
    if (type(source) not in (FakeSource, SealedMemoryHTTPSSource) or
            "reply" in getattr(source, "__dict__", {}) or
            "reply_over_memory_https" in getattr(source, "__dict__", {})):
        raise ValueError("D1_BUNDLE_FAKE_SOURCE_ONLY")
    verified = validate_offline_bundle(
        permit_raw, expected_sha, proofs, test_only_trust_roots,
        checkout_root, reviewed_files, now)
    permit = _strict_permit(permit_raw)
    # The already-reviewed FakeSource evidence writer has a fixed 2 MB
    # body cap. An otherwise valid *smaller* signed permit would not
    # actually constrain it. DENY instead of silently relaxing the grant;
    # dynamically scoped raw limits require a separate source review.
    if permit["max_response_bytes"] != 2_000_000:
        raise ValueError("D1_BUNDLE_RAW_LIMIT_NOT_ENFORCEABLE")
    post_gate=None
    if test_only_fake_post_utc_clock is not None:
        if type(source) is not SealedMemoryHTTPSSource:
            raise ValueError("D1_BUNDLE_POST_UTC_REQUIRES_SEALED_FAKE")
        # The test clock cannot grant actual network permission.
        # Real UTC is independently required at D2 and the actual socket.
        from f0_l2_d1_post_utc import OfflinePostUTCWindow
        post_gate=OfflinePostUTCWindow(
            permit_raw,expected_sha,test_only_fake_post_utc_clock)
    # The approved coordinator stays the sole owner of the 3 shared slots,
    # request IDs and globally spaced fake starts; no alternate sender path.
    result = run_fake_concurrent(
        source, evidence_root,
        max_total=permit["max_total_attempts"],
        max_blocks=permit["max_block_reads"],
        max_refreshes=permit["max_head_refreshes"],
        spacing_ms=permit["min_start_gap_ms"],
        slots=permit["max_inflight"],
        head_ttl_ms=permit["head_ttl_ms"],
        window_ms=permit["max_dispatch_seconds"] * 1000,
        max_block_response_ms=permit["request_timeout_ms"],
        fake_post_utc_window=post_gate,
    )
    audited = reconcile_saved_attempts(evidence_root)
    return {
        "bundle": verified,
        "fake": result,
        "audit": audited,
        "actual_rpc_requests": 0,
        "real_permit": "NOT_CREATED_NOT_ACTIVATED",
        "production": "NO_GO",
        "f0_status": "NOT_PASSED",
    }
