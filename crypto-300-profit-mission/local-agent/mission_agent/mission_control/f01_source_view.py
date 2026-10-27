"""Frank F01 source-only observation gate; never creates executable eligibility.

The previous quote-dependent F01 contract is intentionally NOT reused for an
amount-free product. Fresh source facts can be observed, while all execution
eligibility remains unverified and no new quote/RPC request is made.
"""
from __future__ import annotations

from datetime import datetime, timezone
import math

BUY_SIDES = frozenset({"BUY", "ADD", "REENTRY"})
PATTERNS = frozenset({"ACCUMULATION", "MULTIPLE"})
WINDOW_SECONDS = 600


def _epoch(value):
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        number = float(value)
        return number if math.isfinite(number) else None
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        number = float(value)
        return number if math.isfinite(number) else None
    except (ValueError, OverflowError):
        pass
    try:
        stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if stamp.tzinfo is None:
            return None
        return stamp.astimezone(timezone.utc).timestamp()
    except (ValueError, OverflowError):
        return None


def _fresh(value, now):
    stamp = _epoch(value)
    return stamp is not None and 0 <= now - stamp <= WINDOW_SECONDS


def _reason(row, now, runtime_status):
    if runtime_status != "LIVE":
        return "RUNTIME_NOT_VERIFIED_LIVE"
    if row.get("person_id") != "frank":
        return "OUTSIDE_FRANK_SCOPE"
    if row.get("candidate_source") == "MISSION_CONTROL_OVERLAY":
        return "OVERLAY_NOT_FROZEN_SOURCE"
    if row.get("pattern") not in PATTERNS or not isinstance(row.get("source_signal_id"), str) or not row["source_signal_id"]:
        return "FROZEN_SOURCE_SIGNAL_NOT_VERIFIED"
    if row.get("position_state") != "OPEN":
        return "MODEL_POSITION_NOT_OPEN"
    if row.get("latest_side") not in BUY_SIDES:
        return "LATEST_ACTION_NOT_BUY"
    if not _fresh(row.get("latest_buy_at"), now) or not _fresh(row.get("latest_at"), now):
        return "SOURCE_BUY_STALE_OR_UNVERIFIED"
    return None


def partition_source_only(rows, *, now, runtime_status):
    """Partition observed candidates without inferring balances or executable prices."""
    if not isinstance(rows, list) or isinstance(now, bool) or not isinstance(now, (int, float)) or not math.isfinite(now):
        raise ValueError("F01_INVALID_INPUT")
    recent, other = [], []
    reasons = {}
    newest_chain_buy_age_seconds = None
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("F01_INVALID_ROW")
        reason = _reason(row, now, runtime_status)
        buy_at = _epoch(row.get("latest_buy_at"))
        buy_age = (float(now) - buy_at) if buy_at is not None and buy_at <= now else None
        if buy_age is not None and row.get("person_id") == "frank" and row.get("latest_side") in BUY_SIDES:
            if newest_chain_buy_age_seconds is None or buy_age < newest_chain_buy_age_seconds:
                newest_chain_buy_age_seconds = buy_age
        if reason is None:
            recent.append({**row, "f01_source_state": "RECENT_SOURCE_BUY_ONLY",
                           "chain_buy_age_seconds_at_observation": buy_age,
                           "source_window_remaining_seconds": max(0.0, WINDOW_SECONDS - buy_age),
                           "execution_eligibility": "NOT_ASSESSED_USER_AMOUNT_MISSING",
                           "current_chain_balance_verified": False})
        else:
            reasons[reason] = reasons.get(reason, 0) + 1
            other.append({**row, "f01_source_state": "HISTORICAL_OR_UNVERIFIED",
                          "exclusion_reason": reason})
    return {
        "schema_version": 2,
        "scope": "FRANK_LOCAL_INDEX_SOURCE_ONLY_NO_EXECUTION_QUOTE",
        "status": "SOURCE_ONLY" if runtime_status == "LIVE" else "RUNTIME_UNAVAILABLE",
        "as_of_epoch": float(now),
        "source_window_seconds": WINDOW_SECONDS,
        "event_time_basis": "ONCHAIN_BLOCK_TIME_SECONDS",
        "index_ingest_timestamp_status": "UNAVAILABLE_IN_EXISTING_CANDIDATE_SCHEMA",
        "index_ingest_latency_seconds": None,
        "newest_indexed_buy_age_seconds": newest_chain_buy_age_seconds,
        "excluded_reason_counts": reasons,
        "source_recent": recent,
        "source_recent_count": len(recent),
        "not_followed": other,
        "excluded_count": len(other),
        "eligible": [],
        "eligible_count": 0,
        "execution_eligibility": "NOT_ASSESSED_USER_AMOUNT_MISSING",
        "full_chain_verified": False,
        "current_balance_verified": False,
        "live_notification_authorized": False,
    }
