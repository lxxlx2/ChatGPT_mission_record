"""Deterministic Frank follow-decision policy."""
from __future__ import annotations

import hashlib
import json
import time
from decimal import Decimal, InvalidOperation
from pathlib import Path

VALID_DECISIONS = {"BUY", "SMALL_BUY", "WAIT", "NO_BUY"}


def load_policy(path: Path) -> tuple[dict, str]:
    raw = Path(path).read_bytes()
    policy = json.loads(raw)
    if policy.get("schema_version") != 1:
        raise ValueError("FOLLOW_POLICY_SCHEMA_UNSUPPORTED")
    if policy.get("status") not in {"REVIEW_ONLY", "FROZEN_APPROVED"}:
        raise ValueError("FOLLOW_POLICY_STATUS_INVALID")
    return policy, hashlib.sha256(raw).hexdigest()


def _decimal(value):
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None


def _fresh_timestamp(value, now, max_age_seconds):
    at = _decimal(value)
    if at is None:
        return False, None
    age = Decimal(str(now)) - at
    if age < 0:
        return False, age
    return age <= Decimal(str(max_age_seconds)), age


def evaluate(candidate: dict, quote: dict, policy: dict, *, now: float | None = None) -> dict:
    now = time.time() if now is None else now
    rules = policy["decision"]
    reasons, missing, invalidation = [], [], []
    if candidate.get("runtime_status") != "LIVE":
        return {"decision":"WAIT","reasons":["FRANK_RUNTIME_NOT_LIVE"],"missing":["LIVE_FRANK_RUNTIME"],"invalidation":["DO_NOT_FOLLOW_UNTIL_RUNTIME_RECOVERS"],"metrics":{}}
    state = candidate.get("position_state")
    pattern = candidate.get("pattern") or "NONE"
    latest_side = candidate.get("latest_side")
    if state in set(rules["hard_no_buy_position_states"]):
        return {"decision":"NO_BUY","reasons":["POSITION_STATE_"+str(state)],"missing":[],"invalidation":[],"metrics":{}}
    current_raw = _decimal(candidate.get("current_raw"))
    if current_raw is None:
        return {"decision":"NO_BUY","reasons":["INVENTORY_UNDETERMINED"],"missing":[],"invalidation":[],"metrics":{}}
    if current_raw <= 0:
        return {"decision":"NO_BUY","reasons":["ZERO_OR_NEGATIVE_INVENTORY"],"missing":[],"invalidation":[],"metrics":{}}
    if latest_side == "SELL":
        return {"decision":"WAIT","reasons":["LATEST_ACTION_SELL"],"missing":[],"invalidation":["WAIT_FOR_FRESH_BUY_SEQUENCE"],"metrics":{}}
    if pattern not in {"ACCUMULATION","MULTIPLE"}:
        return {"decision":"WAIT","reasons":["NO_FOLLOW_PATTERN"],"missing":[],"invalidation":[],"metrics":{}}

    frank_max_age = int(rules.get("max_frank_buy_age_seconds", rules.get("initial_notification_max_age_seconds", 600)))
    frank_fresh, frank_age = _fresh_timestamp(candidate.get("latest_buy_at"), now, frank_max_age)
    if not frank_fresh:
        return {
            "decision":"WAIT",
            "reasons":["FRANK_BUY_SIGNAL_STALE_OR_UNKNOWN"],
            "missing":["FRESH_FRANK_BUY"],
            "invalidation":["WAIT_FOR_FRESH_BUY_SEQUENCE"],
            "metrics":{"frank_buy_age_seconds":None if frank_age is None else str(frank_age)},
        }

    if quote.get("status") != "OK":
        missing.append(quote.get("reason") or "JUPITER_QUOTE_UNAVAILABLE")
    observed_at = _decimal(quote.get("observed_at"))
    if observed_at is None:
        missing.append("QUOTE_TIMESTAMP")
    else:
        quote_age = Decimal(str(now)) - observed_at
        if quote_age < 0 or quote_age > Decimal(str(rules["max_quote_age_seconds"])):
            missing.append("QUOTE_STALE")
    if missing:
        return {"decision":"WAIT","reasons":["CRITICAL_DATA_INCOMPLETE"],"missing":sorted(set(missing)),"invalidation":["DO_NOT_FOLLOW_UNTIL_DATA_FRESH"],"metrics":{"frank_buy_age_seconds":str(frank_age)}}

    if not quote.get("route_exists"):
        return {"decision":"NO_BUY","reasons":["NO_EXECUTABLE_JUPITER_ROUTE"],"missing":[],"invalidation":[],"metrics":{"frank_buy_age_seconds":str(frank_age)}}

    latest_buy_price = _decimal(candidate.get("latest_buy_price_usdc"))
    if latest_buy_price is None or latest_buy_price <= 0:
        reason = candidate.get("latest_buy_price_status") or "FRANK_LATEST_BUY_PRICE"
        return {
            "decision":"WAIT",
            "reasons":["CRITICAL_DATA_INCOMPLETE"],
            "missing":[reason],
            "invalidation":["DO_NOT_FOLLOW_UNTIL_EVENT_TIME_REFERENCE_PRICE_EXISTS"],
            "metrics":{"frank_buy_age_seconds":str(frank_age)},
        }

    execution_price = _decimal(quote.get("execution_price_usdc"))
    impact = _decimal(quote.get("price_impact_pct"))
    if execution_price is None or impact is None:
        return {"decision":"WAIT","reasons":["QUOTE_METRICS_INVALID"],"missing":["EXECUTION_PRICE_OR_IMPACT"],"invalidation":["DO_NOT_FOLLOW_UNTIL_DATA_FRESH"],"metrics":{"frank_buy_age_seconds":str(frank_age)}}
    deviation = (execution_price / latest_buy_price - Decimal(1)) * Decimal(100)
    metrics = {
        "frank_latest_buy_price_usdc":str(latest_buy_price),
        "execution_price_usdc":str(execution_price),
        "price_deviation_pct":str(deviation),
        "price_impact_pct":str(impact),
        "quote_input_usdc":quote.get("input_usdc"),
        "frank_buy_age_seconds":str(frank_age),
    }
    buy, small = rules["buy"], rules["small_buy"]
    required_pattern = buy.get("required_pattern", "MULTIPLE")
    if pattern == required_pattern and deviation <= Decimal(str(buy["max_price_deviation_pct"])) and impact <= Decimal(str(buy["max_price_impact_pct"])):
        decision="BUY"; reasons += ["FRANK_MULTIPLE_ACTIVE","PRICE_STILL_CLOSE_TO_FRANK","EXECUTION_IMPACT_ACCEPTABLE"]; invalidation += ["FRANK_SELL","FRANK_EXIT","PRICE_DEVIATION_EXCEEDS_SMALL_BUY_LIMIT","JUPITER_ROUTE_LOST"]
    elif pattern in set(small["allowed_patterns"]) and deviation <= Decimal(str(small["max_price_deviation_pct"])) and impact <= Decimal(str(small["max_price_impact_pct"])):
        decision="SMALL_BUY"; reasons += ["FRANK_PATTERN_ACTIVE","FOLLOWABLE_WITH_SMALL_SIZE"]
        if pattern == "ACCUMULATION": reasons.append("ACCUMULATION_NOT_MULTIPLE")
        if deviation > Decimal(str(buy["max_price_deviation_pct"])): reasons.append("PRICE_DEVIATION_ABOVE_BUY_LIMIT")
        if impact > Decimal(str(buy["max_price_impact_pct"])): reasons.append("PRICE_IMPACT_ABOVE_BUY_LIMIT")
        invalidation += ["FRANK_SELL","FRANK_EXIT","PRICE_DEVIATION_EXCEEDS_SMALL_BUY_LIMIT","JUPITER_ROUTE_LOST"]
    else:
        decision="WAIT"
        if deviation > Decimal(str(small["max_price_deviation_pct"])): reasons.append("PRICE_TOO_FAR_FROM_FRANK")
        if impact > Decimal(str(small["max_price_impact_pct"])): reasons.append("EXECUTION_IMPACT_TOO_HIGH")
        invalidation.append("WAIT_FOR_BETTER_EXECUTION_OR_FRESH_FRANK_BUY")
    assert decision in VALID_DECISIONS
    return {"decision":decision,"reasons":reasons,"missing":[],"invalidation":invalidation,"metrics":metrics}


def should_notify(previous_decision: str | None, decision: str) -> bool:
    """Every new durable result/state transition is meaningful; identical state is silent."""
    return previous_decision != decision
