#!/usr/bin/env python3
"""D1 REAL HTTPS release interface contract; fully OFFLINE and NON-AUTHORIZING.

The transport implementation and shared 3-slot dispatcher already have an
audited MOCK integration. This module binds the shape of a distinct D3
one-shot execution intent to an exact D2 *candidate* permit and immutable
transport budgets BEFORE anyone can propose the actual live release.

There is deliberately NO way in this SHA to turn these checks into permission
for a real HTTPSConnection. No injectable trust roots, clock, path, transport
factory or authorization callback can activate a live sender.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
import re

from f0_l2_d1_bundle import _strict_permit, _reject_duplicate_fields
from f0_l2_d1_grant import GRANT_ID
from f0_l2_d1_preflight import (
    ENDPOINT, HEX40, HEX64, RPC, parse_utc_timestamp, validate_window_contract,
)

D3_SCHEMA = "bsc-f0-d1-live-one-shot-intent-v1"
D3_REQUIRED = frozenset({
    "schema", "approved_commit_sha", "permit_sha256", "grant_id", "run_id",
    "source_manifest_sha256", "window_start_utc", "window_end_utc",
    "endpoint", "chain_id", "methods", "read_only", "no_ws", "no_retries",
    "background", "free_only", "execute_once", "max_total_attempts",
    "max_block_reads", "max_head_refreshes", "max_inflight",
    "min_start_gap_ms", "head_ttl_ms", "request_timeout_ms",
    "max_response_bytes", "max_dispatch_seconds",
})
D3_MAX_BYTES = 8192
_INTENT_ROLES_NOT_ENROLLED = True
_ALLOWED_SUBSET = (
    "max_total_attempts", "max_block_reads", "max_head_refreshes",
    "max_dispatch_seconds", "request_timeout_ms", "max_response_bytes",
    "head_ttl_ms",
)
# Smaller min_start_gap_ms would SEND faster; it may never be relaxed.
_MIN_GAP = "min_start_gap_ms"


@dataclass(frozen=True, slots=True)
class BlockedRealHTTPSBinding:
    """An immutable diagnostic, NEVER a live-authority bearer capability."""

    approved_commit_sha: str
    permit_sha256: str
    candidate_intent_sha256: str
    candidate_source_manifest_sha256: str
    endpoint: str
    chain_id: int
    methods: tuple[str, ...]
    slots: int
    attempts_cap: int
    gap_ms: int
    raw_bytes_cap: int
    deadline_utc: str

    def to_diagnostic(self):
        return {
            "schema": "f0-d1-real-https-boundary-offline-not-released-v1",
            "approved_commit_sha": self.approved_commit_sha,
            "candidate_permit_sha256": self.permit_sha256,
            "candidate_intent_sha256": self.candidate_intent_sha256,
            "candidate_source_manifest_sha256":
                self.candidate_source_manifest_sha256,
            "endpoint": self.endpoint,
            "chain_id": self.chain_id,
            "methods": list(self.methods),
            "coordinator": "EXISTING_SINGLE_GLOBAL_3_SLOT_ONLY",
            "slots": self.slots,
            "max_attempts": self.attempts_cap,
            "min_actual_post_gap_ms": self.gap_ms,
            "raw_response_bytes_cap": self.raw_bytes_cap,
            "deadline_utc": self.deadline_utc,
            "signed_user_intent_verified": False,
            "signed_reviewer_d2_verified": False,
            "production_registry_consumed": False,
            "actual_rpc_calls": 0,
            "real_https_enabled": False,
            "readiness": "CANDIDATE_D2_D3_CONTRACT_ONLY",
            "decision": "D1_BLOCKED_AUTHORITY",
            "production": "PRODUCTION_NO_GO",
        }


def _strict_d3_intent(intent_raw):
    if type(intent_raw) is not bytes or not 0 < len(intent_raw) <= D3_MAX_BYTES:
        raise ValueError("D1_D3_INTENT_BYTES_INVALID")
    try:
        intent = json.loads(intent_raw, object_pairs_hook=_reject_duplicate_fields)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ValueError("D1_D3_INTENT_JSON_INVALID") from exc
    if type(intent) is not dict or set(intent) != D3_REQUIRED:
        raise ValueError("D1_D3_INTENT_FIELD_SET_INVALID")
    return intent


def bind_real_https_candidate_offline(
        permit_raw: bytes, intent_raw: bytes, expected_sha: str,
        now_utc: datetime, *, actual_source_manifest_sha256: str):
    """Inspect exact dual candidate scope. NOT cryptographic live validation.

    D2 signature trust and D3 independent one-shot authorization are both
    ABSENT. This routine cannot sign, consume a grant or construct a sender.
    The actual manifest digest must come from the pinned source inventory,
    never from the untrusted D3 candidate itself.
    """
    if (type(expected_sha) is not str or not HEX40.fullmatch(expected_sha)
            or type(actual_source_manifest_sha256) is not str
            or not HEX64.fullmatch(actual_source_manifest_sha256)
            or type(now_utc) is not datetime or now_utc.tzinfo is None
            or now_utc.utcoffset() != timezone.utc.utcoffset(now_utc)):
        raise ValueError("D1_REAL_BINDING_REFERENCE_INVALID")
    permit = _strict_permit(permit_raw)
    if permit["approved_commit_sha"] != expected_sha:
        raise ValueError("D1_REAL_BINDING_CODE_SHA_MISMATCH")
    # Scope check is local-time dependent, never an authoritative clock.
    scope = validate_window_contract(permit, now_utc)
    intent = _strict_d3_intent(intent_raw)
    if (intent["schema"] != D3_SCHEMA
            or intent["approved_commit_sha"] != expected_sha
            or intent["permit_sha256"] != sha256(permit_raw).hexdigest()
            or intent["grant_id"] != permit["grant_id"]
            or not isinstance(intent["run_id"], str)
            or not GRANT_ID.fullmatch(intent["run_id"])
            or intent["run_id"] == permit["grant_id"]
            or intent["source_manifest_sha256"] !=
                actual_source_manifest_sha256):
        raise ValueError("D1_REAL_BINDING_IDENTITY_MISMATCH")
    if (intent["endpoint"] != ENDPOINT or intent["chain_id"] != 56
            or intent["methods"] != list(RPC)
            or intent["read_only"] is not True
            or intent["no_ws"] is not True
            or intent["no_retries"] is not True
            or intent["free_only"] is not True
            or intent["background"] is not False
            or intent["execute_once"] is not True):
        raise ValueError("D1_REAL_BINDING_TRANSPORT_SCOPE_INVALID")
    if (intent["window_start_utc"] != permit["window_start_utc"]
            or intent["window_end_utc"] != permit["window_end_utc"]
            or not (parse_utc_timestamp(intent["window_start_utc"]) <=
                    now_utc <=
                    parse_utc_timestamp(intent["window_end_utc"]))):
        raise ValueError("D1_REAL_BINDING_WINDOW_MISMATCH")
    # Explicitly compare exact types: booleans are integers in Python.
    for key in _ALLOWED_SUBSET:
        low = 0 if key == "max_head_refreshes" else 1
        if (type(intent[key]) is not int or intent[key] < low or
                type(permit[key]) is not int or
                intent[key] > permit[key]):
            raise ValueError("D1_REAL_BINDING_BUDGET_RELAXED:" + key)
    for key in ("max_inflight",):
        if (type(intent[key]) is not int or intent[key] != 3
                or type(permit[key]) is not int or permit[key] != 3):
            raise ValueError("D1_REAL_BINDING_SHARED_SLOT_NOT_THREE")
    if (type(intent[_MIN_GAP]) is not int
            or intent[_MIN_GAP] < permit[_MIN_GAP]
            or intent[_MIN_GAP] > 5000):
        raise ValueError("D1_REAL_BINDING_POST_GAP_RELAXED")
    if (intent["max_total_attempts"] > intent["max_block_reads"] +
            intent["max_head_refreshes"] + 2):
        raise ValueError("D1_REAL_BINDING_BUDGET_INCOHERENT")
    # The coordinator's existing cap is fixed to 2 MB. Smaller D3 budgets
    # cannot yet be enforced for RAW by that unchanged coordinator: refuse.
    if intent["max_response_bytes"] != 2_000_000:
        raise ValueError("D1_REAL_BINDING_RAW_CAP_NOT_ENFORCEABLE")
    return BlockedRealHTTPSBinding(
        approved_commit_sha=expected_sha,
        permit_sha256=sha256(permit_raw).hexdigest(),
        candidate_intent_sha256=sha256(intent_raw).hexdigest(),
        candidate_source_manifest_sha256=actual_source_manifest_sha256,
        endpoint=ENDPOINT, chain_id=56, methods=RPC, slots=3,
        attempts_cap=intent["max_total_attempts"],
        gap_ms=intent["min_start_gap_ms"],
        raw_bytes_cap=intent["max_response_bytes"],
        deadline_utc=scope["deadline_utc"])


def require_real_sender_release(*_args, **_kwargs):
    """An unconditionally closed boundary; never accepts injectable auth.

    D2 has no independently enrolled production keys, and D3 has no signed
    activation. A candidate may be valid but NEVER becomes a live release.
    """
    raise ValueError("D1_REAL_HTTPS_NOT_RELEASED_D2_D3_REQUIRED")


def send_live(*_args, **_kwargs):
    """No real HTTP, no registry consumption, no 'run' flag at this SHA."""
    raise ValueError("D1_REAL_HTTPS_NOT_RELEASED_D2_D3_REQUIRED")
