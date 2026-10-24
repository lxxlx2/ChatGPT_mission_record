"""Pre-registered Monster research-only D1_RBTC15_LAST5_V1 comparator.

Locked design: see monster/adr/ADR-005-spot-d1-btc-relative-confirmation-preregister-20261024.md.
Runs alongside the immutable original evaluate_closed_5m, never writes its SQLite,
changes original SETUP IDs, sends messages, executes orders or starts any scheduler.
"""
from decimal import Decimal, InvalidOperation

import monster_v4_shadow as original


SCHEMA = "MONSTER_D1_RBTC15_LAST5_PRE_REGISTERED_V1"
FIVE_MS = 300_000
THREE_MS = 180_000
EPISODE_MS = 900_000
REQUIRED_BARS = 6


class ResearchSourceCensored(ValueError):
    """Data missing or inconsistent: neither a positive nor a negative label."""


def _strict_six_closed(candles, tick_ms, name):
    if not isinstance(candles, (list, tuple)) or len(candles) != REQUIRED_BARS:
        raise ResearchSourceCensored(name + "_EXACT_SIX_CLOSED_REQUIRED")
    expected_last = (tick_ms // FIVE_MS) * FIVE_MS - FIVE_MS
    expected_first = expected_last - 5 * FIVE_MS
    parsed = []
    for i, c in enumerate(candles):
        if not isinstance(c, (list, tuple)) or len(c) < 8:
            raise ResearchSourceCensored(name + "_BAD_CANDLE_SHAPE")
        try:
            start, finish = int(c[0]), int(c[6])
            op, high, low, cl, quote = (
                Decimal(str(c[j])) for j in (1, 2, 3, 4, 7)
            )
        except (ValueError, TypeError, InvalidOperation, OverflowError):
            raise ResearchSourceCensored(name + "_BAD_CANDLE_VALUE")
        if (start != expected_first + i * FIVE_MS or
                finish != start + FIVE_MS - 1 or finish >= tick_ms):
            raise ResearchSourceCensored(name + "_GAP_OR_NOT_LAST_CLOSED_BAR")
        if (not all(v.is_finite() for v in (op, high, low, cl, quote)) or
                min(op, high, low, cl, quote) <= 0 or
                low > min(op, cl) or high < max(op, cl)):
            raise ResearchSourceCensored(name + "_BAD_OHLC_OR_QUOTE")
        parsed.append({"open_ms": start, "close_ms": finish,
                       "close": cl, "quote": quote})
    return parsed


def evaluate_research_candidate(*, symbol, observed_ms, watch_ms, deadline_ms,
                                coin_closed5, btc_closed5,
                                last_reviewed_open_ms=None):
    """Pure optional research classifier at an original 3-minute D1 poll.

    The last eligible 5m bar MUST be the exact last UTC closed 5m bar at
    observed_ms. All six bars must have identical timestamps for coin/BTC.
    The first post-WATCH 5m close must have happened to be scoreable.
    This function does not infer historical live ticker/PIT/order eligibility.
    """
    if not isinstance(symbol, str) or not symbol.endswith("USDT") or symbol == "BTCUSDT":
        raise ValueError("RESEARCH_REQUIRES_NON_BTC_SPOT_USDT_TARGET")
    if (type(observed_ms) is not int or type(watch_ms) is not int or
            type(deadline_ms) is not int or observed_ms % THREE_MS or
            watch_ms > observed_ms or deadline_ms - watch_ms != EPISODE_MS):
        raise ValueError("INVALID_FROZEN_D0_QUEUE_CLOCK")
    if last_reviewed_open_ms is not None and type(last_reviewed_open_ms) is not int:
        raise ValueError("BAD_LAST_REVIEWED_OPEN_MS")
    common = {"schema": SCHEMA, "symbol": symbol, "observed_ms": observed_ms,
              "classification": "OFFLINE_RESEARCH_ONLY_NOT_BUY",
              "baseline_source": "ORIGINAL_MONSTER_V4_CLOSED5",
              "historical_live_PIT": "UNPROVEN",
              "historical_executable_net_profit": "UNKNOWN"}
    if observed_ms > deadline_ms:
        return {**common, "state": "EXPIRED", "research_setup_candidate": False}
    try:
        coin = _strict_six_closed(coin_closed5, observed_ms, "COIN")
        btc = _strict_six_closed(btc_closed5, observed_ms, "BTC")
    except ResearchSourceCensored as exc:
        return {**common, "state": "SOURCE_CENSORED", "research_setup_candidate": None,
                "reason": str(exc)}
    if [r["open_ms"] for r in coin] != [r["open_ms"] for r in btc]:
        return {**common, "state": "SOURCE_CENSORED",
                "research_setup_candidate": None, "reason": "COIN_BTC_CLOCK_MISMATCH"}
    current_last_open = coin[-1]["open_ms"]
    if current_last_open + FIVE_MS <= watch_ms:
        return {**common, "state": "WAIT_POST_WATCH_CLOSED_5M",
                "research_setup_candidate": None}
    if last_reviewed_open_ms is not None and current_last_open <= last_reviewed_open_ms:
        return {**common, "state": "SAME_BAR_NO_DUPLICATE",
                "research_setup_candidate": None}
    try:
        old = original.evaluate_closed_5m(coin_closed5, observed_ms)
    except (TypeError, ValueError, KeyError, InvalidOperation) as exc:
        return {**common, "state": "SOURCE_CENSORED", "research_setup_candidate": None,
                "reason": "ORIGINAL_D1_SOURCE_REJECTED:" + type(exc).__name__}
    coin15 = coin[5]["close"] / coin[2]["close"] - Decimal(1)
    btc15 = btc[5]["close"] / btc[2]["close"] - Decimal(1)
    rel15 = coin15 - btc15
    last5_not_down = coin[5]["close"] >= coin[4]["close"]
    passes = bool(old["setup_candidate"] and rel15 >= 0 and last5_not_down)
    return {**common,
            "state": "RESEARCH_SETUP" if passes else "RESEARCH_NO_SETUP_YET",
            "research_setup_candidate": passes,
            "original_d1_candidate": bool(old["setup_candidate"]),
            "coin_15m_pct": str(coin15 * 100),
            "btc_15m_pct": str(btc15 * 100),
            "coin_minus_btc_15m_percentage_points": str(rel15 * 100),
            "last5_nonnegative": last5_not_down,
            "latest_5m_open_ms": current_last_open,
            "original_d1_features": old}
