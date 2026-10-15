#!/usr/bin/env python3
"""Stage151 preregistered research: original305 D1 pullback/reclaim, price proxy ONLY.

No change to original D0/D1; no BUY, notional, historical L2, mail, schedule or trade.
"""
from __future__ import annotations

import argparse
from collections import Counter
import concurrent.futures
import hashlib
import os
from datetime import datetime, timezone
from decimal import Decimal
import json
from pathlib import Path

import monster_v4_stage101_exit_minute_backtest as stage101

old = stage101.old
MIN = 60_000
SCHEMA = "MONSTER_STAGE151_FROZEN_D1_PULLBACK_RECLAIM_PRICE_ONLY_V1"
DROP = Decimal("0.97")
RECLAIM = Decimal("1.01")
MAX_BARS = 120
HORIZONS = (360, 1440)
FEE = Decimal("0.002")
LATENCY_MINUTES = (0, 1, 3)
LIQUIDITY_QUOTE_THRESHOLDS_USDT = (Decimal(0), Decimal(10000), Decimal(100000))


def validate_one_bar(bar, at_ms):
    if (bar is None or len(bar) != 7 or bar[0] != at_ms
            or not all(type(v) is Decimal and v.is_finite() for v in bar[1:6])
            or not (0 < bar[3] <= min(bar[1], bar[4])
                    and bar[2] >= max(bar[1], bar[4])
                    and bar[3] <= bar[2])
            or bar[5] < 0 or type(bar[6]) is not int or bar[6] < 0):
        raise ValueError("STAGE152_MISSING_OR_INVALID_OBSERVABLE_MINUTE")
    return bar


def validate_bars(bars, first_ms, *, n=MAX_BARS):
    """Read-source coverage check, not a future bar validation before decision."""
    if len(bars) < n:
        raise ValueError("STAGE151_MISSING_CONTIGUOUS_120M_SOURCE")
    return True


def decision(bars, frozen_d1_close, first_ms):
    """Consumes 120 1m closed bars at each bar END, never bar HIGH for entry."""
    p0 = Decimal(frozen_d1_close)
    if not p0.is_finite() or p0 <= 0:
        raise ValueError("STAGE151_INVALID_FROZEN_D1_ASOF_CLOSE")
    validate_bars(bars, first_ms)
    trough = None
    armed_at = None
    prev = p0
    for i, candle in enumerate(bars[:MAX_BARS]):
        validate_one_bar(candle, first_ms + i * MIN)
        close = candle[4]
        if trough is None:
            if close <= p0 * DROP:
                trough = close
                armed_at = i
        else:
            trough = min(trough, close)
            if close >= trough * RECLAIM and close > prev:
                return {
                    "state": "PULLBACK_RECLAIM_CONFIRMED_PRICE_ONLY",
                    "decision_visible_ms": first_ms + (i + 1) * MIN,
                    "decision_bar_index": i,
                    "armed_bar_index": armed_at,
                    "trough_from_completed_closes": str(trough),
                    "frozen_D1_baseline": str(p0),
                    "reclaim_bar_quote_volume_USDT": str(candle[5]),
                    "reclaim_bar_trade_count": candle[6],
                    "reclaim_bar_no_trades_price_only":
                        candle[5] <= 0 or candle[6] <= 0,
                }
        prev = close
    return {
        "state": "PULLBACK_NO_RECLAIM" if trough is not None
                 else "NO_PULLBACK_WITHIN_120M",
        "decision_visible_ms": None,
        "decision_bar_index": None,
        "armed_bar_index": armed_at,
        "trough_from_completed_closes": str(trough) if trough is not None else None,
        "frozen_D1_baseline": str(p0),
    }


def price_path(lookup, entry_ms, entry, horizon):
    """Full minute path; missing exit is not an innocent right-censor."""
    entry_bar = validate_one_bar(lookup.get(entry_ms), entry_ms)
    if entry != entry_bar[1] or entry <= 0:
        raise ValueError("STAGE152_ENTRY_PRICE_MISMATCH")
    last_ms = entry_ms + horizon * MIN
    exit_bar = validate_one_bar(lookup.get(last_ms), last_ms)
    minute_rows = [lookup.get(entry_ms + k * MIN) for k in range(horizon)]
    if any(bar is None for bar in minute_rows):
        raise ValueError("STAGE152_MISSING_HOLD_MINUTE")
    # All historical issuer/contract/cost facts remain UNKNOWN; quote turnover
    # is whole-market 1m activity, not an executable order size.
    if entry_bar[5] <= 0 or entry_bar[6] <= 0:
        return {"status": "ENTRY_NO_TRADES_PRICE_PROXY_UNSUPPORTED",
                "horizon_minutes": horizon}
    if exit_bar[5] <= 0 or exit_bar[6] <= 0:
        return {"status": "EXIT_NO_TRADES_PRICE_PROXY_UNSUPPORTED",
                "horizon_minutes": horizon,
                "entry_minute_quote_volume_USDT":str(entry_bar[5]),
                "entry_minute_trade_count":entry_bar[6],
                "exit_minute_quote_volume_USDT":str(exit_bar[5]),
                "exit_minute_trade_count":exit_bar[6]}
    exit_price = exit_bar[1]
    gross = 100 * (exit_price / entry - 1)
    fee_case = 100 * ((exit_price * (1 - FEE)) / (entry * (1 + FEE)) - 1)
    worst = min(validate_one_bar(bar, entry_ms+i*MIN)[3]
                for i, bar in enumerate(minute_rows))
    return {
        "status": "COMPLETE_UNFILLED_PRICE_PROXY",
        "horizon_minutes": horizon, "entry_ms": entry_ms,
        "exit_ms": last_ms,
        "entry_OPEN": str(entry), "exit_OPEN": str(exit_price),
        "entry_minute_quote_volume_USDT":str(entry_bar[5]),
        "entry_minute_trade_count":entry_bar[6],
        "exit_minute_quote_volume_USDT":str(exit_bar[5]),
        "exit_minute_trade_count":exit_bar[6],
        "gross_pct": str(gross),
        "illustrative_20bps_each_side_pct": str(fee_case),
        "adverse_LOW_proxy_pct_not_stop_fill": str(100*(worst / entry - 1)),
        "real_bid_ask_fill_net": "UNKNOWN",
        "observed_1m_turnover_not_order_book_depth": True,
    }


def evaluate_one(asof, archived, *, reader=None):
    if reader is None:
        reader = old.publisher.verified_1m_day
    t = old.utc_ms(asof["D1_FIRST_UTC"])
    receipts_expected = {x["date"]: x["zip_sha256"]
                         for x in archived["source_days_verified"]}
    lookup = {}
    receipts = []
    for day in old.days_for(t):
        source, receipt = reader(asof["symbol"], day)
        key = day.isoformat()
        if len(source) != 1440:
            raise ValueError("STAGE152_PUBLISHER_DAY_ROW_COUNT_NOT_1440")
        if (receipt.get("verified_official_publisher_SHA256") is not True or
                receipt.get("date") != key or
                receipt.get("zip_sha256") != receipts_expected.get(key)):
            raise ValueError("STAGE151_STAGE88_ORIGINAL_PUBLISHER_SHA_CHANGED")
        receipts.append({"date": key, "zip_sha256": receipt["zip_sha256"]})
        day_start = int(datetime(day.year, day.month, day.day,
                                 tzinfo=timezone.utc).timestamp()*1000)
        for i, bar in enumerate(source):
            if bar[0] != day_start + i*MIN:
                raise ValueError("STAGE152_PUBLISHER_UTC_DAY_NONCONTIGUOUS")
            if bar[0] in lookup:
                raise ValueError("STAGE151_DUPLICATE_MINUTE")
            lookup[bar[0]] = bar
    direct = lookup.get(t + MIN)
    if (direct is None or direct[1] !=
            Decimal(archived["entry_delayed_1m"]["entry_open"])):
        raise ValueError("STAGE151_ORIGINAL_STAGE88_D1_ENTRY_MISMATCH")
    # Distinguish scan source gap from price-baseline drift.
    scan = [lookup.get(t + i*MIN) for i in range(MAX_BARS)]
    if any(v is None for v in scan):
        raise ValueError("STAGE152_MISSING_SCAN_MINUTE")
    # Verify the complete old baseline horizon before comparing economics.
    if any(lookup.get(t+MIN+i*MIN) is None for i in range(1440)):
        raise ValueError("STAGE152_MISSING_ORIGINAL_24H_MINUTE")
    original = old.score_path(lookup, t, 1440, direct[1])
    if (original["status"] != stage101.COMPLETE or
            original["fixed_exit_gross_return_pct"] !=
            archived["h24"]["fixed_exit_gross_return_pct"]):
        raise ValueError("STAGE151_ORIGINAL_STAGE88_H24_DRIFT")
    result = decision(scan, asof["asof_D1_last_closed_price"], t)
    paths = {}
    latencies = {}
    entry_minute_evidence = None
    if result["decision_visible_ms"] is not None:
        visible_ms = result["decision_visible_ms"]
        entry_bar = validate_one_bar(lookup.get(visible_ms), visible_ms)
        entry_minute_evidence = {
            "entry_ms":visible_ms,
            "quote_volume_USDT":str(entry_bar[5]),
            "trade_count":entry_bar[6],
            "OPEN":str(entry_bar[1]),
            "not_verified_fill":True,
        }
        if entry_bar[5] <= 0 or entry_bar[6] <= 0:
            result["state"] = "CONFIRMED_NEXT_OPEN_NO_TRADES"
        else:
            for h in HORIZONS:
                paths[str(h)] = price_path(lookup, visible_ms, entry_bar[1], h)
            for delay in LATENCY_MINUTES[1:]:
                future_ms = visible_ms + delay*MIN
                future_bar = validate_one_bar(lookup.get(future_ms), future_ms)
                latencies[str(delay)] = {}
                for h in HORIZONS:
                    latencies[str(delay)][str(h)] = price_path(
                        lookup, future_ms, future_bar[1], h)
    return {
        "date": asof["date"], "symbol": asof["symbol"],
        "D0_FIRST_UTC": asof["D0_FIRST_UTC"],
        "D1_FIRST_UTC": asof["D1_FIRST_UTC"],
        "D1_PATH": asof["D1_PATH"],
        "identity": asof["identity"],
        "old_D1_early5_gt2_evaluation_only": bool(
            asof["early5_gt2_evaluation_only"]),
        "baseline_Stage88_D1_direct_24h_gross_price_only_pct":
            archived["h24"]["fixed_exit_gross_return_pct"],
        "preregistered_decision": result,
        "entry_and_exit_fixed_horizon_price_only": paths,
        "entry_minute_market_activity_not_fill":entry_minute_evidence,
        "delayed_entry_open_same_holding_horizon_price_only":latencies,
        "original_official_daily_sha_receipts": receipts,
        "no_tuning_after_exposed_305": True,
        "real_fill": "NOT_OBSERVED",
        "G4": "UNKNOWN",
    }


def shard_run(date, shard, workers=3):
    if workers not in range(1, 5):
        raise ValueError("STAGE151_INVALID_WORKERS")
    source, archived = stage101.frozen()
    if len(source) != 305 or len(archived) != 305:
        raise ValueError("STAGE151_ORIGINAL305_COHORT_DRIFT")
    group = old.shard_rows(date, shard, source)
    rows = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(evaluate_one, asof, archived[
            (asof["date"], asof["symbol"])]): asof for asof in group}
        for job in concurrent.futures.as_completed(futures):
            asof = futures[job]
            try:
                rows.append(job.result())
            except Exception as exc:
                raise RuntimeError("STAGE151_SOURCE_CASE_FAILED " +
                                   asof["date"] + " " + asof["symbol"]) from exc
    if len(rows) != len(group):
        raise ValueError("STAGE151_LOST_D1_CASE")
    return {
        "schema": SCHEMA, "date": date, "shard": shard,
        "trigger_commit_sha": os.environ.get("GITHUB_SHA", "LOCAL_UNVERIFIED"),
        "stage151_core_sha256":hashlib.sha256(
            Path(__file__).read_bytes()).hexdigest(),
        "original_D1_total_expected": 305,
        "original_D0_total_reference_untouched": 519,
        "D0_only_reference_untouched": 214,
        "rows": sorted(rows, key=lambda x: x["symbol"]),
        "historical_exposed_NOT_OOS": True,
        "G0": "PARTIAL", "G1": "NOT_SCORABLE",
        "G2_G3": "NOT_PASSED", "G4": "UNKNOWN",
        "G6": "NO_GO", "Frank": "UNCHANGED",
        "Gmail": "OFF", "trading": "NO_GO",
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--date", required=True)
    p.add_argument("--shard", type=int, required=True)
    p.add_argument("--workers", type=int, default=3)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    output = shard_run(a.date, a.shard, a.workers)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(output, sort_keys=True,
                                ensure_ascii=False, indent=2) + "\n")
    print("STAGE151_RESEARCH_SHARD " + json.dumps({
        "date": a.date, "shard": a.shard, "n": len(output["rows"]),
        "states": dict(Counter(x["preregistered_decision"]["state"]
                               for x in output["rows"])),
        "G4": output["G4"]}, sort_keys=True))


if __name__ == "__main__":
    main()
