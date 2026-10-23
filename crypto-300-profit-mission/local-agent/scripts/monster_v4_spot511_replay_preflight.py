"""Offline Spot511 D0/D1 3m source preflight from the frozen Stage166 report.

This never reads markets, ranks signals, generates BUY, or assumes a missing
publisher minute file means a zero signal. Source readiness is not G0/PIT.
"""
from collections import Counter
from datetime import date, datetime, timedelta, timezone
import hashlib
import json
import re

SCHEMA = "MONSTER_SPOT511_3M_REPLAY_PREFLIGHT_V1"
SOURCE_SCHEMA = "MONSTER_STAGE166_FROZEN_T0_511_OFFICIAL_SPOT_1M_INTAKE_V1"
START = datetime(2026, 10, 17, 22, 6, tzinfo=timezone.utc)
END = datetime(2026, 10, 24, 22, 6, tzinfo=timezone.utc)
DATES = tuple((date(2026, 10, 16) + timedelta(days=i)).isoformat() for i in range(9))
VALID = {"VERIFIED_FULL_DAY_1440", "SOURCE_NOT_SUPPLIED",
         "SOURCE_REJECTED_OR_INCOMPLETE", "UTC_DAY_NOT_YET_ENDED"}
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
SYMBOL = re.compile(r"[A-Z0-9]+USDT\Z")


def preflight(report):
    """Return complete frozen 511 x 3360 slot accounting, no market replay."""
    if not isinstance(report, dict) or report.get("schema") != SOURCE_SCHEMA:
        raise ValueError("STAGE166_REPORT_SCHEMA_REQUIRED")
    symbols = report.get("t0_eligible_symbol_ids")
    if (not isinstance(symbols, list) or len(symbols) != 511
            or symbols != sorted(set(symbols))
            or any(not isinstance(s, str) or not SYMBOL.fullmatch(s) for s in symbols)
            or report.get("t0_spot_usdt_trading") != 511
            or report.get("t0_spot_usdt_break_excluded") != 214
            or report.get("source_t0_server_time_ms") != 1792274680094
            or report.get("daily_source_attempts") != 4599
            or report.get("utc_daily_source_dates") != list(DATES)
            or report.get("window_start_utc") != "2026-10-17T22:06:00Z"
            or report.get("window_end_exclusive_utc") != "2026-10-24T22:06:00Z"
            or report.get("three_minute_ticks_total") != 3360
            or report.get("full_7d_exchange_listing_changes_proven") is not False):
        raise ValueError("FROZEN_SPOT511_COHORT_OR_WINDOW_DRIFT")
    try:
        asof = datetime.fromisoformat(report["asof_source_check_utc"].replace("Z", "+00:00"))
    except (TypeError, ValueError, KeyError) as exc:
        raise ValueError("SOURCE_ASOF_INVALID") from exc
    if asof.tzinfo is None or asof.utcoffset() is None:
        raise ValueError("SOURCE_ASOF_INVALID")
    asof = asof.astimezone(timezone.utc)
    attempts = report.get("attempts")
    if not isinstance(attempts, list) or len(attempts) != 4599:
        raise ValueError("SOURCE_ATTEMPTS_INCOMPLETE")
    by_key = {}
    counts = Counter()
    for row in attempts:
        if not isinstance(row, dict):
            raise ValueError("SOURCE_ATTEMPT_INVALID")
        sym, day, status = (row.get("symbol"), row.get("date_utc"),
                            row.get("archive_status"))
        if (sym not in symbols or day not in DATES or status not in VALID
                or (sym, day) in by_key):
            raise ValueError("SOURCE_IDENTITY_DUPLICATE_OR_INVALID")
        end_of_day = datetime.combine(date.fromisoformat(day) + timedelta(days=1),
                                      datetime.min.time(), timezone.utc)
        if (status == "UTC_DAY_NOT_YET_ENDED") != (end_of_day > asof):
            raise ValueError("SOURCE_AVAILABILITY_FUTURE_DRIFT")
        if status == "VERIFIED_FULL_DAY_1440":
            proof = row.get("source_detail")
            if (not isinstance(proof, dict)
                    or proof.get("closed_one_minute_rows") != 1440
                    or proof.get("original_publisher_checksum_valid") is not True
                    or proof.get("spot_timestamp_units") != "MICROSECONDS"
                    or not isinstance(proof.get("zip_sha256"), str)
                    or not HEX64.fullmatch(proof["zip_sha256"])):
                raise ValueError("UNBACKED_VERIFIED_MINUTE_FILE")
        by_key[(sym, day)] = status
        counts[status] += 1
    declared_counts = report.get("admission_counts")
    if (not isinstance(declared_counts, dict)
            or {k: v for k, v in declared_counts.items() if v} != dict(counts)
            or report.get("all_511_nine_days_officially_verified") is not
               (counts["VERIFIED_FULL_DAY_1440"] == 4599)):
        raise ValueError("SOURCE_ADMISSION_AGGREGATE_DRIFT")

    # A tick at T may only use fully closed 1m candles in [T-24h, T).
    # In particular T=00:00 needs the previous day, not the future day.
    required_groups = Counter()
    tick = START
    while tick < END:
        first = (tick - timedelta(hours=24)).date()
        last = (tick - timedelta(microseconds=1)).date()
        dates = tuple((first + timedelta(days=i)).isoformat()
                      for i in range((last - first).days + 1))
        required_groups[dates] += 1
        tick += timedelta(minutes=3)
    if sum(required_groups.values()) != 3360:
        raise ValueError("REPLAY_TICK_GRID_INVALID")
    ready = 0
    blocked = Counter()
    per_symbol = []
    for sym in symbols:
        symbol_ready = 0
        reasons = Counter()
        for days, n_ticks in required_groups.items():
            states = [by_key[(sym, d)] for d in days]
            if all(s == "VERIFIED_FULL_DAY_1440" for s in states):
                symbol_ready += n_ticks
            else:
                # One loss per symbol/tick, not twice for two missing days.
                reason = ("SOURCE_REJECTED_OR_INCOMPLETE"
                          if "SOURCE_REJECTED_OR_INCOMPLETE" in states else
                          "UTC_DAY_NOT_YET_ENDED"
                          if "UTC_DAY_NOT_YET_ENDED" in states else
                          "SOURCE_NOT_SUPPLIED")
                reasons[reason] += n_ticks
        ready += symbol_ready
        blocked.update(reasons)
        per_symbol.append({"symbol": sym, "source_ready_ticks": symbol_ready,
                           "source_blocked_ticks": 3360-symbol_ready})
    total = 511 * 3360
    if ready + sum(blocked.values()) != total:
        raise ValueError("REPLAY_DENOMINATOR_INVALID")
    digest = hashlib.sha256(json.dumps(report, sort_keys=True,
                  ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()
    return {
        "schema": SCHEMA, "upstream_stage166_report_canonical_sha256": digest,
        "frozen_symbols": 511, "three_minute_ticks": 3360,
        "total_symbol_ticks": total, "source_ready_symbol_ticks": ready,
        "source_blocked_symbol_ticks": total-ready,
        "blocked_reason_symbol_ticks": dict(sorted(blocked.items())),
        "per_symbol": per_symbol,
        "source_ready_only": True,
        "stage166_claims_rechecked_against_original_zip_bytes": False,
        "market_signal_replay_performed": False,
        "spot_24h_ticker_equivalence_proven": False,
        "dynamic_listing_pit_proven": False,
        "actual_d0_watch_or_d1_setup_found": "NOT_SCORABLE",
        "G0": "PARTIAL", "G1": "NOT_SCORABLE", "G2": "NOT_PASSED",
        "G3": "NOT_PASSED", "G4": "UNKNOWN", "G6": "NO_GO",
        "NO_DEPLOY": True, "NO_GMAIL": True, "NO_TRADE": True,
    }
