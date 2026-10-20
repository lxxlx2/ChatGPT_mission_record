"""Amount-independent, evidence-first Frank research observations.

Pure/offline P2 prototype. No order sizing, Jupiter, Gmail, OS notifications,
production SQLite, market fetching, or current-time lookup. The caller provides
*all* source evidence and an explicit as-of cutoff. This module does not create
BUY/SMALL_BUY decisions or trading instructions.
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation
from math import isfinite
from typing import Any, Mapping

_VALID_BUY_PRICE = {"USDC_DIRECT", "SOL_EVENT_TIME_USDC_VERIFIED"}
_VALID_PATTERNS = {"ACCUMULATION", "MULTIPLE", "REENTRY_WATCH"}
_VALID_SIDES = {"BUY", "SELL"}
_VALID_CHAIN = "solana"


def _decimal(value: Any) -> Decimal | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        converted = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None
    return converted if converted.is_finite() and converted > 0 else None


def _epoch(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (ValueError, TypeError, OverflowError):
        return None
    return number if isfinite(number) and number > 0 else None


def _count(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        return None
    return value


def analyze_candidate(
    candidate: Mapping[str, Any],
    *,
    as_of: float,
    market: Mapping[str, Any] | None = None,
    max_market_age_seconds: int,
) -> dict[str, Any]:
    """Summarize facts verifiable by as_of; never silently make up a market mark.

    market must identify same Solana mint, source, observed_at (Unix UTC seconds)
    and price_usdc_per_token. max_market_age_seconds is chosen explicitly by
    offline caller; it is NOT an implicit trading signal/order threshold.
    """
    cutoff = _epoch(as_of)
    if cutoff is None:
        raise ValueError("AS_OF_INVALID")
    if not isinstance(max_market_age_seconds, int) or isinstance(max_market_age_seconds, bool) or max_market_age_seconds <= 0:
        raise ValueError("MARKET_FRESHNESS_LIMIT_REQUIRED")
    mint = candidate.get("mint")
    if not isinstance(mint, str) or not mint.strip():
        raise ValueError("MINT_REQUIRED")

    pattern = candidate.get("pattern")
    if pattern not in _VALID_PATTERNS:
        pattern = "UNKNOWN"
    side = candidate.get("latest_side")
    if side not in _VALID_SIDES:
        side = "UNKNOWN"

    last = _epoch(candidate.get("latest_at"))
    buy_at = _epoch(candidate.get("latest_buy_at"))
    signal_at = _epoch(candidate.get("source_signal_at"))
    verified_action = (last is not None and last <= cutoff and
                       bool(candidate.get("latest_signature")) and side != "UNKNOWN")
    future_event = any(t is not None and t > cutoff for t in (last, buy_at, signal_at))
    if future_event:
        # A retrospective signal must never use a future buy/action/alert.
        verified_action = False

    facts = []
    missing = []
    if verified_action:
        facts.append("FRANK_LATEST_ACTION_" + side)
    elif future_event:
        missing.append("CANDIDATE_EVENT_AFTER_AS_OF")
    else:
        missing.append("LATEST_ACTION_NOT_PROVEN")

    buy_count, sell_count = _count(candidate.get("buy_count")), _count(candidate.get("sell_count"))
    if buy_count is not None and not future_event:
        facts.append("OBSERVED_BUY_COUNT_" + str(buy_count))
    if sell_count is not None and not future_event:
        facts.append("OBSERVED_SELL_COUNT_" + str(sell_count))

    source_signal_id = candidate.get("source_signal_id")
    if (pattern in {"ACCUMULATION", "MULTIPLE"} and source_signal_id
            and signal_at is not None and signal_at <= cutoff):
        facts.append("V1_SOURCE_" + pattern)
    elif pattern == "REENTRY_WATCH":
        facts.append("REENTRY_OBSERVE_ONLY" if verified_action else "REENTRY_UNCONFIRMED")
    else:
        missing.append("V1_SOURCE_SIGNAL_NOT_VERIFIED")

    if verified_action and side == "SELL":
        facts.append("FRANK_SELL_OBSERVED_REVIEW_RISK")
    if not candidate.get("position_state"):
        missing.append("POSITION_STATE_UNKNOWN")

    price = {
        "status": "PRICE_UNAVAILABLE",
        "change_pct_vs_last_verified_buy": None,
        "buy_price_usdc": None,
        "market_price_usdc": None,
        "buy_observed_at": buy_at if buy_at is not None and buy_at <= cutoff else None,
        "market_observed_at": None,
        "market_source": None,
        "basis": "REFERENCE_PRICE_ONLY_NOT_EXECUTABLE_QUOTE_OR_PNL",
    }
    verified_buy = _decimal(candidate.get("latest_buy_price_usdc"))
    price_status = candidate.get("latest_buy_price_status")
    if verified_buy is None or price_status not in _VALID_BUY_PRICE or buy_at is None or buy_at > cutoff:
        missing.append("VERIFIED_COMPARABLE_FRANK_BUY_PRICE_UNAVAILABLE")
    else:
        price["buy_price_usdc"] = str(verified_buy)

    if market is None:
        missing.append("MARKET_REFERENCE_MISSING")
    elif market.get("mint") != mint or market.get("chain") != _VALID_CHAIN:
        price["status"] = "PRICE_SOURCE_MISMATCH"
        missing.append("MARKET_REFERENCE_MINT_OR_CHAIN_MISMATCH")
    else:
        mark = _decimal(market.get("price_usdc_per_token"))
        mark_at = _epoch(market.get("observed_at"))
        source = market.get("source")
        if mark is None or mark_at is None or not isinstance(source, str) or not source.strip():
            price["status"] = "PRICE_SOURCE_UNVERIFIED"
            missing.append("MARKET_REFERENCE_UNVERIFIABLE")
        elif mark_at > cutoff:
            price["status"] = "PRICE_FROM_FUTURE"
            missing.append("MARKET_REFERENCE_AFTER_AS_OF")
        elif cutoff - mark_at > max_market_age_seconds:
            price["status"] = "PRICE_STALE"
            missing.append("MARKET_REFERENCE_STALE")
        else:
            price.update(market_price_usdc=str(mark), market_observed_at=mark_at, market_source=source)
            if price["buy_price_usdc"] is not None and not future_event:
                movement = (mark / verified_buy - Decimal("1")) * 100
                price["change_pct_vs_last_verified_buy"] = str(movement.quantize(Decimal("0.0001")))
                price["status"] = "COMPARABLE_REFERENCE_CHANGE"
                if movement > 0:
                    facts.append("PRICE_ABOVE_VERIFIED_FRANK_BUY_REFERENCE")
                elif movement < 0:
                    facts.append("PRICE_BELOW_VERIFIED_FRANK_BUY_REFERENCE")
                else:
                    facts.append("PRICE_EQUAL_TO_VERIFIED_FRANK_BUY_REFERENCE")
            else:
                price["status"] = "VERIFIED_BUY_REFERENCE_MISSING"

    return {
        "schema_version": 1,
        "category": "RESEARCH_ONLY_NOT_EXECUTION_OR_TRADE",
        "chain": _VALID_CHAIN,
        "mint": mint,
        "as_of": cutoff,
        "pattern": pattern,
        "latest_side": side if verified_action else "UNVERIFIED",
        "source_signal_id": source_signal_id if signal_at is not None and signal_at <= cutoff else None,
        "latest_signature": candidate.get("latest_signature") if verified_action else None,
        "latest_action_at": last if verified_action else None,
        "facts": facts,
        "missing": missing,
        "price": price,
        "execution_assessment": "NOT_ASSESSED_NO_USER_AMOUNT",
        "suggested_action": "REVIEW_EVIDENCE_ONLY",
        "order_amount_usdc": None,
        "user_order_authorized": False,
        "alert_delivery_authorized": False,
    }
