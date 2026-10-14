#!/usr/bin/env python3
"""Stage135: offline complete-denominator 1m source audit for Stage133/134.

ZIP + CHECKSUM validate source-byte consistency, not independent network origin.
No network, runtime monitor, scheduler, trading, notifications or model fitting.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path

import monster_v4_stage130_first_listed_minute_sha_replay as publisher
import monster_v4_stage131_dynamic_listing_g1_population_bridge as stage131
import monster_v4_stage133_manual_actual_t0_forward_proof as stage133
import monster_v4_stage134_t0_population_readiness_bridge as stage134

SCHEMA = "MONSTER_STAGE135_FULL_POPULATION_1M_PUBLISHER_SOURCE_COVERAGE_V1"
ONE_MINUTE = 60_000
ONE_DAY = 86_400_000
WARMUP = ONE_DAY


def day(ms):
    return datetime.fromtimestamp(ms / 1000, timezone.utc).date().isoformat()


def required_days(first_ms, end_ms):
    """Days overlapping half-open source interval [first_ms, end_ms)."""
    if (type(first_ms) is not int or type(end_ms) is not int or
            first_ms >= end_ms or first_ms % ONE_MINUTE or
            end_ms % ONE_MINUTE):
        raise ValueError("STAGE135_SOURCE_INTERVAL_INVALID")
    begin = datetime.fromtimestamp(first_ms / 1000, timezone.utc).date()
    last = datetime.fromtimestamp((end_ms - 1) / 1000, timezone.utc).date()
    return [(begin + timedelta(days=i)).isoformat()
            for i in range((last - begin).days + 1)]


def locally_verified_day(archive_root, symbol, utc_day):
    """Reuse the exact original Stage130 publisher ZIP/.CHECKSUM CSV verifier.

    A missing file is explicit CENSORING. Corrupt present files fail hard.
    Local CHECKSUM agreement alone is not external HTTP/source attestation.
    """
    root = Path(archive_root)
    folder = root / symbol
    zipped = folder / (utc_day + ".zip")
    checksum = folder / (utc_day + ".zip.CHECKSUM")
    if not zipped.is_file() or not checksum.is_file():
        missing = []
        if not zipped.is_file():
            missing.append("ZIP")
        if not checksum.is_file():
            missing.append("CHECKSUM")
        return None, {"day": utc_day, "missing_components": missing,
                      "status": "CENSORED_SOURCE_MISSING"}

    expected_url = publisher.source_url(symbol, utc_day)

    def read_saved(url, max_bytes):
        if url == expected_url:
            path = zipped
        elif url == expected_url + ".CHECKSUM":
            path = checksum
        else:
            raise ValueError("STAGE135_UNEXPECTED_PUBLISHER_URL")
        if path.stat().st_size > max_bytes:
            raise ValueError("STAGE135_ARCHIVE_OBJECT_TOO_LARGE")
        return path.read_bytes()

    bars, receipt = publisher.verified_day(
        symbol, utc_day, fetch=read_saved, save_dir=None)
    if receipt["url"] != expected_url or not receipt["publisher_sha256_verified"]:
        raise ValueError("STAGE135_SOURCE_PUBLISHER_RECEIPT_NOT_VERIFIED")
    return bars, {
        "day": utc_day, "status": "ARCHIVED_LOCAL_SHA_AND_PUBLISHER_CHECKSUM_MATCH",
        "zip_sha256": receipt["zip_sha256"],
        "source_url_expected": receipt["url"],
        "local_sha_self_consistent_external_origin_unverified": True,
        "bars_in_source_day": receipt["bars"],
    }


def audit_one(row, forward_start_ms, forward_end_ms, archive_root, load=locally_verified_day):
    """Evaluate every candidate, including no-signal and missing-source cases."""
    symbol = row["symbol_exact"]
    lane = row["population_lane"]
    if lane == "PREEXISTING_AT_WINDOW_START":
        required_start = forward_start_ms - WARMUP
        origin = "REQUIRES_24H_HISTORICAL_WARMUP"
    elif lane == "IN_WINDOW_FIRST_TRADABLE_MINUTE_CANDIDATE":
        required_start = stage131.stamp(row["first_observed_minute_utc"])
        if not forward_start_ms <= required_start < forward_end_ms:
            raise ValueError("STAGE135_ARRIVAL_CLOCK_OUTSIDE_WINDOW")
        origin = "SELF_REPORTED_ARRIVAL_CLOCK_PIT_UNVERIFIED"
    else:
        raise ValueError("STAGE135_UNKNOWN_POPULATION_LANE")

    required = required_days(required_start, forward_end_ms)
    receipts = []
    present = []
    missing = []
    for utc_day in required:
        bars, receipt = load(archive_root, symbol, utc_day)
        receipts.append(receipt)
        if bars is None:
            missing.append(utc_day)
            continue
        # Stage130 validated each original publisher ZIP / minute and ordering.
        present.extend(b[0] for b in bars
                       if required_start <= b[0] < forward_end_ms)

    count_expected = (forward_end_ms - required_start) // ONE_MINUTE
    complete = (not missing and len(present) == count_expected
                and all(t == required_start + i * ONE_MINUTE
                        for i, t in enumerate(present)))
    # No extra/overlapping timestamps may be mislabeled as full coverage.
    if len(present) != len(set(present)):
        raise ValueError("STAGE135_DUPLICATE_CROSS_ARCHIVE_MINUTE")
    if present != sorted(present):
        raise ValueError("STAGE135_UNORDERED_CROSS_ARCHIVE_MINUTE")

    return {
        "venue": row["venue"],
        "symbol_exact": symbol,
        "population_lane": lane,
        "first_observation_source_boundary": origin,
        "required_source_from_utc": stage133.iso(required_start),
        "required_source_to_exclusive_utc": stage133.iso(forward_end_ms),
        "expected_minute_count": count_expected,
        "observed_minute_count": len(present),
        "required_publisher_utc_days": required,
        "missing_utc_days": missing,
        "original_archive_receipts": receipts,
        "source_status": ("CONTIGUOUS_LOCAL_ARCHIVE_CHECKSUM_SELF_CONSISTENT"
                          if complete else "CENSORED_SOURCE_GAP_OR_MISSING"),
        "source_minute_continuity": complete,
        "source_archive_origin_independently_attested": False,
        "point_in_time_issuer_and_venue_identity": "UNVERIFIED",
        "first_listing_time_independently_attested": False,
        "eligible_to_claim_full_market_G0_or_G1": False,
        "D0_watch": "NOT_RUN_NO_LIVE_OBSERVATION",
        "execution_net": "UNKNOWN",
    }


def audit(t0_packet, archive_root, arrivals=None, load=locally_verified_day):
    # Preserve one truthful audience of source and denominator by reconstructing
    # Stage134 fresh, including its exact raw Stage133 clock and checksum checks.
    base = stage134.reconcile(t0_packet, arrivals)
    start = stage131.stamp(base["new_forward_start_utc"])
    end = stage131.stamp(base["new_forward_end_exclusive_utc"])
    rows = base["stage131_reconciled_population"]["raw_population_rows"]
    checked = [audit_one(row, start, end, archive_root, load=load)
               for row in rows]
    if len(checked) != base["stage131_reconciled_population"]["raw_symbol_attempts"]:
        raise ValueError("STAGE135_FULL_MARKET_ATTEMPT_LOST")
    completed = sum(row["source_minute_continuity"] for row in checked)
    censored = len(checked) - completed
    return {
        "schema": SCHEMA,
        "source": "SAVED_LOCAL_BINANCE_PUBLISHER_ZIP_AND_CHECKSUM_OFFLINE",
        "stage133_receipt_packet_SHA256": base["stage133_packet_integrity_sha256"],
        "stage134_same_t0_and_population_revalidated": True,
        "source_origin_not_independently_attested": True,
        "source_verification_type": "LOCAL_BYTES_CHECKSUM_AGREEMENT_ONLY",
        "new_forward_start_utc": base["new_forward_start_utc"],
        "new_forward_end_exclusive_utc": base["new_forward_end_exclusive_utc"],
        "full_initial_venue_candidates": base["t0_active_usdt_perpetual_attempts"],
        "in_window_candidates_unverified": base["in_window_arrival_candidates_unverified"],
        "full_market_attempts": len(checked),
        "source_contiguous_since_required_origin": completed,
        "source_missing_or_gapped": censored,
        "in_window_arrival_census_complete": False,
        "crypto_issuer_point_in_time_verified": False,
        "delivery_latency_real_time_observed": False,
        "historical_stage116_original_oct14_failure": "SOURCE_FAILED_NO_BACKFILL",
        "stage118_and_stage127_failed_strategies": "REJECTED_UNCHANGED",
        "stage132_first_momentum_buy": "NEGATIVE_UNCHANGED",
        "G0": "PARTIAL",
        "G1": "NOT_SCORABLE",
        "G2_G3": "NOT_PASSED",
        "G4": "UNKNOWN",
        "G5": "NOT_DONE",
        "G6": "NO_GO",
        "Frank": "UNCHANGED", "Gmail": "OFF",
        "automated_collection_scheduled": False,
        "per_symbol_source_audit": checked,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--t0", type=Path, required=True)
    p.add_argument("--arrival-candidates", type=Path)
    p.add_argument("--archive-root", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    t0 = json.loads(args.t0.read_text(encoding="utf-8"))
    arrivals = (json.loads(args.arrival_candidates.read_text(encoding="utf-8"))
                if args.arrival_candidates is not None else None)
    result = audit(t0, args.archive_root, arrivals)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(
        result, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8")
    print(json.dumps({
        "full_market_attempts": result["full_market_attempts"],
        "source_contiguous": result["source_contiguous_since_required_origin"],
        "source_censored": result["source_missing_or_gapped"],
        "G0": result["G0"], "G1": result["G1"],
        "G6": result["G6"]}, sort_keys=True))


if __name__ == "__main__":
    main()
