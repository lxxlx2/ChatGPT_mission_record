#!/usr/bin/env python3
"""Stage111-V1: pure causal research state engine. NO network, email or trading."""
from __future__ import annotations
import argparse
from collections import deque
from decimal import Decimal
from hashlib import sha256
import json

MIN = 60_000
BLOCK = 15
REST_RATIO = Decimal("0.60")
REST_DRAWDOWN = Decimal("0.95")
IGNITION_QUOTE = Decimal("1.50")
IGNITION_PRICE = Decimal("1.03")
TROUGH_RECOVERY = Decimal("1.06")
RESET_TTL = 72 * 60 * MIN
PRIORITY_COOLDOWN = 360 * MIN
SCHEMA = "MONSTER_STAGE111_PERSISTENT_D0_RECOVERY_CAUSAL_V1"


def median4(xs):
    if len(xs) != 4:
        raise ValueError("STAGE111_NEED_PREVIOUS_FOUR_BLOCKS")
    v = sorted(xs)
    return (v[1] + v[2]) / 2


def candle(row, expected_open):
    if row is None:
        raise ValueError("STAGE111_MISSING_MINUTE")
    if len(row) != 7 or row[0] != expected_open:
        raise ValueError("STAGE111_NONCONTIGUOUS_OR_INVALID_MINUTE")
    t, o, h, low, close, quote, trades = row
    nums = (o, h, low, close, quote)
    if (any(not isinstance(z, Decimal) or not z.is_finite() for z in nums)
            or not isinstance(trades, int)
            or not (0 < low <= min(o, close) <= max(o, close) <= h)
            or quote < 0 or trades < 0):
        raise ValueError("STAGE111_INVALID_OHLCV")
    return t, o, h, low, close, quote, trades


def replay(d0_open_ms, anchor_end_ms, rows, original_d1_ms=None):
    """Process completed 1m bar stream only; future labels NEVER passed in.

    D0 at t; first admissible bar opens t+MIN and is only known at t+2MIN.
    rows: chronological 7-tuples of (open_ms, Decimal OHLC, Decimal quote, int trades).
    """
    if (not isinstance(d0_open_ms, int) or not isinstance(anchor_end_ms, int)
            or d0_open_ms >= anchor_end_ms
            or (anchor_end_ms - d0_open_ms) % MIN):
        raise ValueError("STAGE111_INVALID_ANCHOR_TIME")
    if original_d1_ms is not None and original_d1_ms < d0_open_ms:
        raise ValueError("STAGE111_D1_BEFORE_D0")

    events = []
    def emit(state, visible_at, reason, **extra):
        ordinal = len(events)
        event_id = sha256(f"{d0_open_ms}|{visible_at}|{state}|{ordinal}".encode()).hexdigest()[:24]
        events.append({"event_id": event_id, "state": state,
                       "observable_ms": visible_at, "reason": reason, **extra})

    emit("D0_WATCH_ACTIVE", d0_open_ms, "ORIGINAL_IMMUTABLE_D0")
    if original_d1_ms == d0_open_ms:
        emit("D1_SETUP", original_d1_ms, "ORIGINAL_ASOF_D1_NO_PROMOTION")

    last = d0_open_ms
    blockrows = []
    blocks = []
    armed_at = None
    trough = None
    ready_at = d0_open_ms
    priorities = 0
    d1_recorded = original_d1_ms == d0_open_ms
    censor_reason = None

    for raw in rows:
        expected = last + MIN
        if expected >= anchor_end_ms:
            break
        if raw is None or len(raw) != 7 or raw[0] != expected:
            censor_reason = "MISSING_OR_NONCONTIGUOUS_OFFICIAL_1M"
            break
        bar = candle(raw, expected)
        last = expected
        visible = last + MIN
        if original_d1_ms is not None and not d1_recorded and original_d1_ms <= visible:
            emit("D1_SETUP", original_d1_ms, "ORIGINAL_ASOF_D1_NO_PROMOTION")
            d1_recorded = True
        blockrows.append(bar)
        if len(blockrows) != BLOCK:
            continue

        close = blockrows[-1][4]
        q = sum((b[5] for b in blockrows), Decimal(0))
        trades = sum(b[6] for b in blockrows)
        prior = blocks[-4:]
        peak = max((b["close"] for b in blocks), default=close)
        prev_close = blocks[-1]["close"] if blocks else close

        if armed_at is not None and visible - armed_at > RESET_TTL:
            emit("D0_WATCH_ACTIVE", visible, "REST_WINDOW_72H_EXPIRED")
            armed_at, trough = None, None

        if len(prior) == 4 and visible >= ready_at:
            baseline = median4([b["quote"] for b in prior])
            rest = (baseline > 0 and q <= baseline * REST_RATIO
                    and close <= peak * REST_DRAWDOWN)
            # A genuine new rest is necessary after every priority.
            if armed_at is None:
                if rest:
                    armed_at, trough = visible, close
                    emit("WATCH_RECOVERY", visible, "VOLUME_REST_WITH_PRIOR_CLOSE_DRAWDOWN",
                         baseline_quote=str(baseline), rest_quote=str(q),
                         rest_price=str(close))
            else:
                trough = min(trough, close)
                burst = (baseline > 0 and trades > 0
                         and q >= baseline * IGNITION_QUOTE
                         and close >= prev_close * IGNITION_PRICE)
                if burst:
                    emit("REIGNITION_CANDIDATE", visible,
                         "FRESH_CLOSED_15M_PRICE_AND_QUOTE_BURST",
                         baseline_quote=str(baseline), burst_quote=str(q),
                         trough_close=str(trough), signal_close=str(close))
                    if close >= trough * TROUGH_RECOVERY:
                        priorities += 1
                        emit("PRIORITY", visible, "RESET_THEN_ACTUAL_15M_REIGNITION",
                             priority_ordinal=priorities,
                             next_1m_open_ms=visible,
                             price_proxy_not_execution=True)
                        ready_at = visible + PRIORITY_COOLDOWN
                        armed_at, trough = None, None
        blocks.append({"close": close, "quote": q, "trades": trades, "visible": visible})
        blockrows.clear()

    # Source supplied through end of fixed historical anchor, not past it.
    complete = last + MIN >= anchor_end_ms
    status = "EXPIRED" if complete and censor_reason is None else "SOURCE_CENSORED"
    if status == "EXPIRED":
        emit("EXPIRED", anchor_end_ms, "ORIGINAL_SEVEN_DAY_ANCHOR_END")
    else:
        emit("SOURCE_CENSORED", last + MIN,
             censor_reason or "SOURCE_TERMINATED_BEFORE_ANCHOR_END")
    return {"schema": SCHEMA, "D0_first_ms": d0_open_ms,
            "original_D1_observation_ms": original_d1_ms,
            "anchor_end_ms": anchor_end_ms,
            "last_observed_minute_open_ms": last if last > d0_open_ms else None,
            "source_status": status, "complete_168h_source": complete,
            "complete_minute_blocks": len(blocks),
            "priority_count": priorities, "events": events,
            "real_executable_net_profit": "UNKNOWN",
            "trading": "NO_GO", "deployment": "NO_GO"}


def selftest():
    D = Decimal
    start = 1_760_000_000_000
    def rows(prices, quotes, highs=None):
        out = []
        for block, (price, quote) in enumerate(zip(prices, quotes)):
            for m in range(BLOCK):
                t = start + (block * BLOCK + m + 1) * MIN
                val = D(str(price))
                q = D(str(quote)) / BLOCK
                h = max(val, D(str(highs[block]))) if highs else val
                out.append((t, val, h, val, val, q, 1))
        return out
    prices = [100, 100, 100, 100, 94, 101]
    quotes = [1000, 1000, 1000, 1000, 500, 2000]
    base = rows(prices, quotes)
    end = start + (len(base) + 1) * MIN
    x = replay(start, end, base, start)
    priority = [v for v in x["events"] if v["state"] == "PRIORITY"]
    assert x["source_status"] == "EXPIRED" and x["priority_count"] == 1
    assert len(priority) == 1 and priority[0]["observable_ms"] == end
    assert priority[0]["next_1m_open_ms"] == end
    assert sum(v["state"] == "D1_SETUP" for v in x["events"]) == 1

    # High is not an input to the decision; no future right-tail lookahead.
    high_changed = rows(prices, quotes, [100000] * len(prices))
    y = replay(start, end, high_changed, start)
    assert [e for e in y["events"] if e["state"] == "PRIORITY"] == priority

    # More future after the first priority may not alter that priority.
    extended = base + rows([100], [1000])[-15:]
    z = replay(start, end + 15 * MIN, extended, start)
    assert [e for e in z["events"] if e["state"] == "PRIORITY"][:1] == priority

    no_burst = replay(start, end, rows(prices, [1000,1000,1000,1000,500,800]))
    assert no_burst["priority_count"] == 0
    assert no_burst["source_status"] == "EXPIRED"

    missing = replay(start, end, base[:-1])
    assert missing["source_status"] == "SOURCE_CENSORED"
    assert missing["priority_count"] == 0
    assert missing["events"][-1]["state"] == "SOURCE_CENSORED"

    tampered = list(base)
    tampered[25] = (tampered[25][0] + MIN,) + tampered[25][1:]
    cut = replay(start, end, tampered)
    assert cut["source_status"] == "SOURCE_CENSORED"

    # One original D1 can't manufacture a new priority in a quiet path.
    assert replay(start, end, rows([100]*6, [1000]*6),
                  start + 20*MIN)["priority_count"] == 0
    print("STAGE111_REST_BURST_CLOSE_ONLY_CAUSAL_SOURCE_CENSORED_SELFTEST_PASS")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        selftest()
    else:
        ap.error("Historical pure state core: use --selftest; no network/live mode")
