"""F01/C02/F02 exact-CA *read-only* evidence alignment for isolated product QA.

Does not call RPC, create CA jobs, decide BUY, quote, change Frank signals,
or assert that an archived F02 research account is a current portfolio.
Input is existing API/report data, never an untrusted same-symbol join.
"""
from __future__ import annotations

from typing import Any
from decimal import Decimal, InvalidOperation

FRESH = "FRESH_VERIFIED_ARCHIVED_OBSERVATION"
COMPLETE = "BOTH_PROGRAMS_OBSERVED_NON_ATOMIC"
F02_KIND = "F02_RESEARCH_ARCHIVED_OWNER_POSITIONS"


def _f02_usable(doc: dict) -> bool:
    """Match the F02-R2 fail-closed source/attempt agreement, not just readiness."""
    age = doc.get("capture_age_seconds")
    ttl = doc.get("max_age_seconds")
    if (doc.get("kind") != F02_KIND or doc.get("person_id") != "frank"
            or doc.get("chain") != "solana"
            or doc.get("readiness") != FRESH
            or doc.get("archive_observation_usable") is not True
            or doc.get("capture_fresh") is not True
            or not isinstance(age, (int, float)) or isinstance(age, bool)
            or not isinstance(ttl, (int, float)) or isinstance(ttl, bool)
            or age < 0 or ttl <= 1 or age >= ttl - 1):
        return False
    sha = doc.get("verified_full_wire_capture_sha256")
    return (isinstance(sha, str) and len(sha) == 64
            and doc.get("latest_capture_sha256") == sha
            and doc.get("latest_attempt_capture_sha256") == sha
            and doc.get("source_observation_status") == COMPLETE
            and doc.get("latest_attempt_source_status") == COMPLETE
            and isinstance(doc.get("mints"), list)
            and doc.get("target_mint_count") == 32
            and len(doc["mints"]) == 32
            and len({x.get("mint") for x in doc["mints"]
                     if isinstance(x, dict)}) == 32)


def align_frank_ca_f02(*, mint: str, follow: dict | None,
                        ca_report: dict | None,
                        f02_positions: dict | None) -> dict[str, Any]:
    """Prepare one display-only exact-mint cross-module comparison.

    F01 eligibility remains *its own* frozen decision. F02 positions only
    describe verified archived original-wire observation inside frozen
    target scope. C02 may describe an entirely independent research job.
    No combined permission to trade is ever issued.
    """
    if not isinstance(mint, str) or not mint or len(mint) > 64:
        raise ValueError("JOINT_INVALID_MINT")
    follow = follow if isinstance(follow, dict) else {}
    ca_report = ca_report if isinstance(ca_report, dict) else {}
    f02_positions = f02_positions if isinstance(f02_positions, dict) else {}

    eligible = [
        x for x in (follow.get("eligible") or [])
        if isinstance(x, dict) and x.get("mint") == mint
        and x.get("person_id") == "frank"
    ] if follow.get("status") == "OK" else []
    # A duplicate in any source is ambiguity, not multiple independent BUY votes.
    follow_state = ("F01_ELIGIBLE" if len(eligible) == 1
                    and eligible[0].get("decision") in ("BUY", "SMALL_BUY")
                    and eligible[0].get("source_signal_id")
                    else "F01_AMBIGUOUS" if len(eligible) > 1
                    else "F01_NOT_ELIGIBLE")
    selected = eligible[0] if follow_state == "F01_ELIGIBLE" else None

    f02_rows = [
        x for x in (f02_positions.get("mints") or [])
        if isinstance(x, dict) and x.get("mint") == mint
    ]
    f02_safe = _f02_usable(f02_positions)
    visible = f02_safe and len(f02_rows) == 1
    row = f02_rows[0] if visible else {}
    wallet_state = row.get("state") if visible else "SOURCE_UNAVAILABLE"
    if visible and wallet_state not in (
            "OPEN_ACCOUNT_NONZERO", "OPEN_ACCOUNT_ZERO",
            "NO_OPEN_ACCOUNT_OBSERVED"):
        visible = False
        wallet_state = "SOURCE_UNAVAILABLE"
    quantity = (row.get("observed_quantity") if visible and
                wallet_state in ("OPEN_ACCOUNT_NONZERO", "OPEN_ACCOUNT_ZERO")
                else None)
    count = (row.get("token_account_count") if visible and
             wallet_state in ("OPEN_ACCOUNT_NONZERO", "OPEN_ACCOUNT_ZERO")
             else None)
    # Missing target is not a proven zero; stale or partial is not a current sale.
    if not visible:
        wallet_state = ("OUTSIDE_FROZEN_TARGET_ROSTER" if f02_safe
                        and len(f02_rows) == 0 else "SOURCE_UNAVAILABLE")
    if wallet_state == "OPEN_ACCOUNT_NONZERO" and quantity is None:
        wallet_state, visible, count = "SOURCE_UNAVAILABLE", False, None
    if wallet_state == "OPEN_ACCOUNT_ZERO":
        try:
            is_zero = (isinstance(quantity, str)
                       and Decimal(quantity).is_finite()
                       and Decimal(quantity) == 0)
        except (InvalidOperation, ValueError):
            is_zero = False
        if not is_zero:
            wallet_state, visible, quantity, count = (
                "SOURCE_UNAVAILABLE", False, None, None)

    ca_state = "CA_NOT_QUERIED"
    ca_label = None
    narrative_status = "UNVERIFIED"
    if ca_report:
        if ca_report.get("mint") != mint:
            ca_state = "CA_MINT_MISMATCH"
        elif ca_report.get("chain") not in (None, "solana"):
            ca_state = "CA_CHAIN_MISMATCH"
        else:
            identity = ca_report.get("token_identity") or {}
            if (isinstance(identity, dict) and
                    identity.get("identity_status") == "VERIFIED" and
                    identity.get("conflict_status") == "NO_CONFLICT_OBSERVED"):
                ca_state = "CA_EXACT_MINT_IDENTITY_VERIFIED"
                ca_label = identity.get("display_label")
            else:
                ca_state = "CA_IDENTITY_UNCONFIRMED"
            # Do not manufacture an "official narrative" from social hints
            # or a completed HTTP job. Preserve source-assessment semantics.
            assessment = ca_report.get("assessment") or {}
            if isinstance(assessment, dict):
                narrative_status = assessment.get("narrative_status") or "UNVERIFIED"

    contradiction = (
        "F01_SIGNAL_VS_ARCHIVED_WALLET_REQUIRES_REVIEW"
        if selected is not None and visible and
        wallet_state in ("OPEN_ACCOUNT_ZERO", "NO_OPEN_ACCOUNT_OBSERVED")
        else None
    )
    return {
        "schema_version": 1,
        "scope": "FRANK_F01_C02_F02_RESEARCH_ALIGNMENT_ONLY",
        "mint": mint, "chain": "solana", "person_id": "frank",
        "f01": {
            "status": follow_state,
            "frozen_decision": selected.get("decision") if selected else None,
            "source_signal_id": selected.get("source_signal_id") if selected else None,
            "f01_evidence_still_separately_required": True,
        },
        "f02": {
            "state": wallet_state,
            "observed_quantity": quantity if visible else None,
            "token_account_count": count if visible else None,
            "capture_observed_at_utc": (
                f02_positions.get("capture_observed_at_utc") if visible else None),
            "capture_sha256": (
                f02_positions.get("verified_full_wire_capture_sha256") if visible else None),
            "archived_source_only": True,
            "does_not_confirm_sale_or_current_portfolio": True,
        },
        "c02": {
            "status": ca_state, "exact_mint_label": ca_label,
            "narrative_status": narrative_status,
            "independent_ca_diligence": True,
        },
        "cross_source_review_reason": contradiction,
        "combined_trade_permission": False,
        "no_new_rpc_or_sidecar_writes": True,
    }
