"""F01 read-only presentation gate for current Frank follow opportunities.

Never creates a new follow decision or changes frozen Frank V1 thresholds.
A stored BUY/SMALL_BUY is an historical decision unless latest source evidence,
quote and the current Frank runtime remain valid at display time.
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import math


_ACTION = frozenset({"BUY", "SMALL_BUY"})
_FOLLOW_PATTERN = frozenset({"MULTIPLE", "ACCUMULATION"})
_LAST_BUY = frozenset({"BUY", "ADD", "REENTRY"})


def _epoch(value) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        number = float(value)
        return number if math.isfinite(number) else None
    if not isinstance(value, str):
        return None
    try:
        number = float(value)
        return number if math.isfinite(number) else None
    except (ValueError, OverflowError):
        pass
    try:
        date = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if date.tzinfo is None:
            return None
        return date.astimezone(timezone.utc).timestamp()
    except (OverflowError, ValueError):
        return None


def _fresh(value, *, now: float, max_age_seconds: int) -> bool:
    at = _epoch(value)
    return at is not None and 0 <= now - at <= max_age_seconds


def _positive(value) -> bool:
    if type(value) is bool or value is None:
        return False
    try:
        number = Decimal(str(value))
        return number.is_finite() and number > 0
    except (TypeError, InvalidOperation, ValueError):
        return False


def _reason(item: dict, *, now: float, runtime_status: str,
            max_frank_buy_age_seconds: int, max_quote_age_seconds: int) -> str | None:
    # Existing V1 is Frank-only; do not treat an injected research person or
    # SOL sidecar-only candidate as a production follow decision.
    if item.get("person_id") != "frank":
        return "NOT_APPROVED_FRANK_SCOPE"
    if item.get("candidate_source") == "MISSION_CONTROL_OVERLAY":
        return "NOT_FROZEN_FRANK_SOURCE"
    if runtime_status != "LIVE":
        return "FRANK_RUNTIME_NOT_LIVE"
    if item.get("decision") not in _ACTION:
        return "NOT_ACTIONABLE_DECISION"
    if item.get("position_state") != "OPEN":
        return "MODEL_POSITION_NOT_OPEN"
    if item.get("latest_side") not in _LAST_BUY:
        return "LATEST_ACTION_NOT_BUY"
    if not _positive(item.get("current_raw")):
        return "MODEL_INVENTORY_UNKNOWN_OR_ZERO"
    if item.get("pattern") not in _FOLLOW_PATTERN or not item.get("source_signal_id"):
        return "SOURCE_SIGNAL_UNVERIFIED"
    if not _fresh(item.get("latest_buy_at"), now=now, max_age_seconds=max_frank_buy_age_seconds):
        return "FRANK_BUY_STALE"
    if not _fresh(item.get("decision_created_at"), now=now, max_age_seconds=max_frank_buy_age_seconds):
        return "DECISION_STALE"
    quote = item.get("decision_quote") or {}
    if quote.get("status") != "OK" or quote.get("route_exists") is not True:
        return "QUOTE_NOT_EXECUTABLE"
    # The BUY flag alone is not actionable when the corresponding execution
    # price/impact evidence is missing, as reproduced in Mac synthetic Safari.
    metrics = item.get("metrics") or {}
    price = quote.get("execution_price_usdc")
    if price is None:
        price = metrics.get("execution_price_usdc")
    impact = quote.get("price_impact_pct")
    if impact is None:
        impact = metrics.get("price_impact_pct")
    try:
        impact_value = Decimal(str(impact))
    except (TypeError, InvalidOperation, ValueError):
        return "QUOTE_NOT_EXECUTABLE"
    if not _positive(price) or not impact_value.is_finite() or impact_value < 0:
        return "QUOTE_NOT_EXECUTABLE"
    if not _fresh(item.get("quote_observed_at"), now=now,
                  max_age_seconds=max_quote_age_seconds):
        return "QUOTE_STALE"
    return None


def partition_candidates(candidates: list[dict], *, now: float,
                         runtime_status: str, max_frank_buy_age_seconds: int,
                         max_quote_age_seconds: int) -> dict:
    if (not isinstance(candidates, list) or
        type(max_frank_buy_age_seconds) is not int or
        type(max_quote_age_seconds) is not int or
        max_frank_buy_age_seconds <= 0 or max_quote_age_seconds <= 0 or
        isinstance(now, bool) or not isinstance(now, (float, int)) or
        not math.isfinite(now)):
        raise ValueError("FOLLOW_VIEW_INPUT_INVALID")
    eligible, excluded = [], []
    for item in candidates:
        if not isinstance(item, dict):
            raise ValueError("FOLLOW_VIEW_CANDIDATE_INVALID")
        reason = _reason(item, now=float(now), runtime_status=runtime_status,
                         max_frank_buy_age_seconds=max_frank_buy_age_seconds,
                         max_quote_age_seconds=max_quote_age_seconds)
        if reason is None:
            eligible.append(dict(item))
        else:
            excluded.append({**item, "exclusion_reason": reason})
    return {
        "schema_version": 1,
        "scope": "FRANK_FROZEN_DECISIONS_PRESENTATION_ONLY",
        "status": "OK" if runtime_status == "LIVE" else "RUNTIME_UNAVAILABLE",
        "as_of_epoch": float(now),
        "eligible_count": len(eligible),
        "excluded_count": len(excluded),
        "eligible": eligible,
        "not_followed": excluded,
    }
