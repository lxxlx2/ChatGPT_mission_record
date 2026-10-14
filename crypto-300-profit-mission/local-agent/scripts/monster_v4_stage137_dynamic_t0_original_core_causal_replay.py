#!/usr/bin/env python3
"""Stage137 read-only dynamic-T0 causal D0/D1 replay using unmodified original cores.

Only offline locally verified publisher ZIP/CHECKSUM bytes; original shadow D0
and Stage80 frozen D1. Mixed USD-M venue evidence, NOT confirmed crypto G1,
real-time delivery, executable net, or deployment.
"""
from __future__ import annotations

import argparse
import bisect
from collections import Counter
from decimal import Decimal
import json
from pathlib import Path
import tempfile

import monster_v4_historical_replay as replay
import monster_v4_stage38_usdm_original_v4_1m_pilot as v4
import monster_v4_stage80_dual_entry_core as d1
import monster_v4_stage131_dynamic_listing_g1_population_bridge as stage131
import monster_v4_stage133_manual_actual_t0_forward_proof as stage133
import monster_v4_stage135_full_market_publisher_minute_coverage as stage135

SCHEMA = "MONSTER_STAGE137_DYNAMIC_T0_ORIGINAL_D0_D1_CAUSAL_FULL_MARKET_V1"
MIN = 60_000
TICK = 3 * MIN
WARMUP = 1_440
ACTIVE = 10_080
BARS = WARMUP + ACTIVE


def original_core_contract():
    # Model pins are unchanged: reject unreviewed drift before claiming SAME core.
    if v4.blob(v4.production.__file__) != v4.ORIGINAL_V4_GIT_BLOB:
        raise ValueError("STAGE137_FROZEN_PRODUCTION_V4_BLOB_CHANGED")
    contract = d1.load_contract()
    return contract


def clocks(start, end):
    """UTC-global 3min ticks only, after >=3m closed source, end exclusive."""
    if (type(start) is not int or type(end) is not int
            or start % (5 * MIN) or end - start != ACTIVE * MIN):
        raise ValueError("STAGE137_DYNAMIC_FROZEN_5M_T0_REQUIRED")
    first = ((start + 3 * MIN + TICK - 1) // TICK) * TICK
    return range(first, end, TICK)


def full_window_minutes(archive_root, symbol, start, end):
    """Re-read and re-verify every exact original minute, not a cached summary."""
    full_start = start - WARMUP * MIN
    blocks = []
    day_receipts = []
    for day in stage135.required_days(full_start, end):
        bars, receipt = stage135.locally_verified_day(archive_root, symbol, day)
        if bars is None:
            raise ValueError("STAGE137_SOURCE_CHANGED_TO_MISSING_AFTER_COVERAGE_AUDIT")
        blocks.extend(x for x in bars if full_start <= x[0] < end)
        day_receipts.append(receipt)
    if (len(blocks) != BARS or
            any(x[0] != full_start + i * MIN or len(x) != 7
                for i, x in enumerate(blocks))):
        raise ValueError("STAGE137_11520_CONTIGUOUS_ORIGINAL_MINUTES_REQUIRED")
    return blocks, day_receipts


def first_high_cross(bars, multiplier, start, end):
    threshold = bars[WARMUP][1] * Decimal(multiplier)
    for candle in bars[WARMUP:]:
        if start <= candle[0] < end and candle[2] >= threshold:
            return candle[0]
    return None


def replay_original_d0_d1(symbol, start, end, bars, contract):
    """Original shadow.observe_snapshot/process_queue and Stage80 D1.evaluate.

    Isolated temporary SQLite per instrument. Never use production SQLite.
    """
    if not symbol.isascii():
        raise ValueError("STAGE137_ORIGINAL_D0_CORE_ASCII_ONLY")
    if len(bars) != BARS:
        raise ValueError("STAGE137_FULL_SOURCE_REQUIRED_FOR_D0")
    prefix = [Decimal(0)]
    for b in bars:
        prefix.append(prefix[-1] + b[5])
    candles = replay.make_closed_five_minute_bars(bars)
    candle_ends = [int(c[6]) for c in candles]
    ticks = clocks(start, end)
    tick_count = 0
    first_d0 = None
    first_d1 = None
    d1_path = None
    state = None
    # G0 clock: a poll at t consumes only candles with end < t.
    with tempfile.TemporaryDirectory(prefix="monster137_original_core_") as folder:
        db = v4.production.open_store(Path(folder) / "isolated_d0_only.sqlite")
        try:
            def last_closed_five(_venue, _symbol, at_ms):
                k = bisect.bisect_left(candle_ends, at_ms)
                return candles[max(0, k - 8):k]
            for t in ticks:
                idx = (t - (start - WARMUP * MIN)) // MIN - 1
                if not WARMUP <= idx + 1 < BARS:
                    raise ValueError("STAGE137_TICK_BAR_INDEX_DRIFT")
                # Exactly 24h quote context ending at the last fully closed
                # minute; user-supplied 1m publisher rows are not a 24h ticker.
                quote = prefix[idx + 1] - prefix[idx + 1 - WARMUP]
                v4.production.observe_snapshot(db, "futures", t, [{
                    "symbol": symbol,
                    "lastPrice": str(bars[idx][4]),
                    "quoteVolume": str(quote)}])
                v4.production.process_queue(db, t, last_closed_five)
                tick_count += 1
                if first_d0 is None:
                    watch = db.execute(
                        "SELECT MIN(observed_ms) FROM events "
                        "WHERE event_type='WATCH_EARLY'").fetchone()[0]
                    if watch is not None:
                        if watch != t:
                            raise ValueError("STAGE137_NONCAUSAL_FIRST_WATCH_CLOCK")
                        first_d0 = watch
                if first_d0 is not None and first_d1 is None:
                    if t - first_d0 <= contract["from_first_d0_expiration_hours"] * 3_600_000:
                        features = d1.from_archived_closed_bars(
                            bars[(t - (start - WARMUP * MIN)) // MIN - 61:
                                 (t - (start - WARMUP * MIN)) // MIN], t)
                        state, response = d1.evaluate(
                            state, venue="BINANCE_USDM", symbol=symbol,
                            at_utc=stage133.iso(t), features=features,
                            is_first_d0=(t == first_d0), contract=contract)
                        if response in ("DIRECT_AT_FIRST_D0", "REIGNITION_AFTER_D0"):
                            first_d1 = t
                            d1_path = response
            actual = db.execute(
                "SELECT COUNT(*) FROM events WHERE event_type='WATCH_EARLY'").fetchone()[0]
        finally:
            db.close()
    if first_d1 is not None and (first_d0 is None or first_d1 < first_d0):
        raise ValueError("STAGE137_ORPHAN_OR_PRE_D0_D1")
    if tick_count != len(ticks):
        raise ValueError("STAGE137_LOST_THREE_MINUTE_POLL")
    crosses = {m: first_high_cross(bars, m, start, end) for m in (2, 5, 10)}
    labels = {}
    for m, peak in crosses.items():
        labels[f"first_GT{m}x_HIGH_UTC_EVALUATION_ONLY"] = (
            stage133.iso(peak) if peak is not None else None)
        labels[f"D0_first_strict_pre_GT{m}x"] = bool(
            first_d0 is not None and peak is not None and first_d0 < peak)
        labels[f"D0_first_pre_GT{m}x_5m"] = bool(
            first_d0 is not None and peak is not None and first_d0 + 5 * MIN <= peak)
        labels[f"D1_first_pre_GT{m}x_5m"] = bool(
            first_d1 is not None and peak is not None and first_d1 + 5 * MIN <= peak)
    return {
        "replay_status": "ORIGINAL_ASCII_V4_D0_AND_FROZEN_D1_CAUSAL_OFFLINE",
        "original_core_three_minute_ticks": tick_count,
        "first_tick_utc": stage133.iso(ticks[0]),
        "last_tick_utc": stage133.iso(ticks[-1]),
        "end_exclusive_boundary_tick_excluded": True,
        "original_WATCH_EARLY_event_count_not_independent_2x": actual,
        "D0_first_UTC": stage133.iso(first_d0) if first_d0 is not None else None,
        "D1_first_UTC": stage133.iso(first_d1) if first_d1 is not None else None,
        "D1_entry_path": d1_path,
        "gross_future_labels_not_real_profit": labels,
        "raw_venue_source_complete_but_issuer_unverified": True,
    }


def run(t0_packet, archive_root, arrivals=None):
    # Stage135 recomputes Stage133/134 identities and all original source days.
    census = stage135.audit(t0_packet, archive_root, arrivals)
    start = stage131.stamp(census["new_forward_start_utc"])
    end = stage131.stamp(census["new_forward_end_exclusive_utc"])
    contract = original_core_contract()
    out = []
    totals = Counter()
    d1_daily = Counter()
    for source in census["per_symbol_source_audit"]:
        symbol = source["symbol_exact"]
        lane = source["population_lane"]
        row = {
            "venue": source["venue"],
            "symbol_exact": symbol, "population_lane": lane,
            "original_archive_source_status": source["source_status"],
            "original_archive_receipts_count":
                len(source["original_archive_receipts"]),
            "covered_minute_count": source["observed_minute_count"],
            "D0_first_UTC": None, "D1_first_UTC": None,
            "G1_crypto_eligible": False,
            "actual_execution_net": "UNKNOWN",
        }
        if not source["source_minute_continuity"]:
            row["replay_status"] = "SOURCE_CENSORED_NO_REPLAY"
            totals["source_censored"] += 1
        elif lane != "PREEXISTING_AT_WINDOW_START":
            row["replay_status"] = "NEW_LISTING_REPLAY_NOT_YET_SUPPORTED_PIT_UNVERIFIED"
            totals["new_listing_unscored"] += 1
        elif not symbol.isascii():
            row["replay_status"] = "MODEL_SYMBOL_UNSUPPORTED_NOT_A_NO_WATCH"
            totals["model_symbol_unsupported"] += 1
        else:
            bars, receipts = full_window_minutes(archive_root, symbol, start, end)
            row.update(replay_original_d0_d1(symbol, start, end, bars, contract))
            row["original_archive_receipts_count"] = len(receipts)
            totals["model_compatible_complete"] += 1
            if row["D0_first_UTC"] is not None:
                totals["first_D0"] += 1
            if row["D1_first_UTC"] is not None:
                totals["first_D1"] += 1
                day_bucket = (stage131.stamp(row["D1_first_UTC"]) - start) // (24 * 3_600_000)
                if not 0 <= day_bucket < 7:
                    raise ValueError("STAGE137_D1_OUTSIDE_FORWARD_WINDOW")
                d1_daily[day_bucket] += 1
            labels = row["gross_future_labels_not_real_profit"]
            for m in (2, 5, 10):
                if labels[f"first_GT{m}x_HIGH_UTC_EVALUATION_ONLY"] is not None:
                    totals[f"gross_{m}x"] += 1
                if labels[f"D0_first_strict_pre_GT{m}x"]:
                    totals[f"D0_strict_{m}x"] += 1
                if labels[f"D0_first_pre_GT{m}x_5m"]:
                    totals[f"D0_early5_{m}x"] += 1
                    if labels[f"D1_first_pre_GT{m}x_5m"]:
                        totals[f"D1_early5_given_D0_{m}x"] += 1
        out.append(row)
    if len(out) != census["full_market_attempts"]:
        raise ValueError("STAGE137_DROPPED_FULL_MARKET_POPULATION")
    if len({r["symbol_exact"] for r in out}) != len(out):
        raise ValueError("STAGE137_DUPLICATE_SYMBOL_OR_BIASED_POPULATION")
    return {
        "schema": SCHEMA,
        "evidence_mode": "POST_WINDOW_CAUSAL_ARCHIVE_REPLAY_NOT_LIVE_ALERT_DELIVERY",
        "stage133_original_packet_sha256": census["stage133_receipt_packet_SHA256"],
        "new_forward_start_utc": census["new_forward_start_utc"],
        "new_forward_end_exclusive_utc": census["new_forward_end_exclusive_utc"],
        "original_unmodified_V4_git_blob": v4.ORIGINAL_V4_GIT_BLOB,
        "original_unmodified_stage80_contract_sha": d1.CONTRACT_SHA,
        "stage135_reverified_full_market_attempts": census["full_market_attempts"],
        "stage135_source_contiguous": census["source_contiguous_since_required_origin"],
        "stage135_source_censored": census["source_missing_or_gapped"],
        "model_attempts_scored_or_classified": len(out),
        "raw_usdm_venue_descriptive_only": dict(totals),
        "raw_D1_daily_by_UTC_forward_day": [d1_daily[i] for i in range(7)],
        "all_source_population_rows": out,
        "not_live_one_minute_capture_proof": True,
        "complete_asof_issuer_scope_verified": False,
        "in_window_arrival_census_complete": False,
        "historical_stage116_first_window": "SOURCE_FAILED_NO_BACKFILL",
        "stage118_127": "REJECTED_UNCHANGED",
        "stage132_buy_proxy": "NEGATIVE_UNCHANGED",
        "G0": "PARTIAL", "G1": "NOT_SCORABLE", "G2_G3": "RAW_DESCRIPTIVE_ONLY_NOT_PASSED",
        "G4": "UNKNOWN", "G5": "NOT_DONE", "G6": "NO_GO",
        "real_execution": "UNKNOWN", "monster_deploy": "NO_GO",
        "scheduled_capture": False, "Gmail": "OFF", "Frank": "UNCHANGED",
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--t0", type=Path, required=True)
    p.add_argument("--archive-root", type=Path, required=True)
    p.add_argument("--arrival-candidates", type=Path)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    packet = json.loads(a.t0.read_text(encoding="utf-8"))
    arrivals = json.loads(a.arrival_candidates.read_text(
        encoding="utf-8")) if a.arrival_candidates else None
    result = run(packet, a.archive_root, arrivals)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(result, ensure_ascii=False,
                                sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "schema": SCHEMA, "attempts": result["model_attempts_scored_or_classified"],
        "raw_venue": result["raw_usdm_venue_descriptive_only"],
        "G0": result["G0"], "G1": result["G1"],
        "G6": result["G6"],
    }, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
