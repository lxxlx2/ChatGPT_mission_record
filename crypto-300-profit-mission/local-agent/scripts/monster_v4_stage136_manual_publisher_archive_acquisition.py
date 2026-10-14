#!/usr/bin/env python3
"""Stage136: complete-market official publisher archive acquisition, MANUAL ONLY.

Default --plan is offline. Live GETs require --fetch-manual AND explicit
--capture-request after the whole seven-day window +48h. Research only:
a locally verified ZIP/CHECKSUM pair cannot independently attest HTTP origin.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import tempfile
import time

import monster_v4_stage130_first_listed_minute_sha_replay as publisher
import monster_v4_stage131_dynamic_listing_g1_population_bridge as stage131
import monster_v4_stage134_t0_population_readiness_bridge as stage134
import monster_v4_stage135_full_market_publisher_minute_coverage as stage135

SCHEMA = "MONSTER_STAGE136_MANUAL_PUBLISHER_ARCHIVE_ACQUISITION_V1"
REQUEST_SCHEMA = "MONSTER_STAGE136_USER_REQUESTED_ONE_SHOT_V1"
PUBLISHER_MARGIN_MS = 48 * 3_600_000


def validate_request(request):
    if (not isinstance(request, dict)
            or request.get("schema") != REQUEST_SCHEMA
            or request.get("explicit_manual_request") is not True
            or request.get("allow_official_historical_publisher_fetch") is not True):
        raise ValueError("STAGE136_EXPLICIT_USER_MANUAL_FETCH_REQUIRED")


def planned_files(t0, arrivals=None):
    """Use exact Stage134 revalidated all-venue attempt roster, no winner filtering."""
    base = stage134.reconcile(t0, arrivals)
    start = stage131.stamp(base["new_forward_start_utc"])
    end = stage131.stamp(base["new_forward_end_exclusive_utc"])
    records = []
    rows = base["stage131_reconciled_population"]["raw_population_rows"]
    for row in rows:
        symbol = row["symbol_exact"]
        lane = row["population_lane"]
        from_ms = (
            stage131.stamp(row["pre_T0_recent_onboarding_minute_utc"])
            if lane == "PREEXISTING_AT_WINDOW_START"
               and row.get("pre_T0_recent_onboarding_minute_utc") is not None
            else start - stage135.WARMUP
            if lane == "PREEXISTING_AT_WINDOW_START"
            else stage131.stamp(row["first_observed_minute_utc"]))
        for d in stage135.required_days(from_ms, end):
            records.append({
                "symbol": symbol,
                "day": d,
                "lane": lane,
                "publisher_zip_url": publisher.source_url(symbol, d),
            })
    if len({(x["symbol"], x["day"]) for x in records}) != len(records):
        raise ValueError("STAGE136_DUPLICATE_PLANNED_SOURCE_ID")
    return base, sorted(records, key=lambda r: (r["symbol"], r["day"]))


def read_saved(archive_root, record):
    """Reject corrupt existing pairs; a missing component is an incomplete pair."""
    bars, receipt = stage135.locally_verified_day(
        archive_root, record["symbol"], record["day"])
    if bars is None:
        return None
    if receipt.get("status") != "ARCHIVED_LOCAL_SHA_AND_PUBLISHER_CHECKSUM_MATCH":
        raise ValueError("STAGE136_EXISTING_SOURCE_NOT_PUBLISHER_SHA")
    return receipt["zip_sha256"]


def acquire(t0, archive_root, arrivals=None, *, fetch_manual=False,
            capture_request=None, now_ms=None, get=publisher.http_get,
            max_fetch_files=None):
    """Pure plan by default; only explicitly authorized run may make source GETs.

    The request JSON by itself is not proof of prior chat authorization:
    the operator must obtain that authorization before using --fetch-manual.
    """
    if fetch_manual:
        validate_request(capture_request)
    elif capture_request is not None:
        raise ValueError("STAGE136_CAPTURE_REQUEST_REQUIRES_FETCH_MANUAL")
    if (max_fetch_files is not None and
            (type(max_fetch_files) is not int or max_fetch_files < 1)):
        raise ValueError("STAGE136_INVALID_FILE_BUDGET")
    base, planned = planned_files(t0, arrivals)
    end_ms = stage131.stamp(base["new_forward_end_exclusive_utc"])
    if fetch_manual:
        moment = int(time.time()*1000) if now_ms is None else now_ms
        if type(moment) is not int or moment < end_ms + PUBLISHER_MARGIN_MS:
            raise ValueError("STAGE136_FUTURE_WINDOW_OR_PUBLISHER_MARGIN_NOT_REACHED")
    root = Path(archive_root)
    # Planning may inspect existing files but never creates directories or writes data.
    source_records = []
    reused = fetched = unavailable = pending = 0
    attempts = 0
    for record in planned:
        existing = read_saved(root, record)
        entry = {
            "symbol": record["symbol"], "day": record["day"],
            "population_lane": record["lane"],
            "expected_official_publisher_zip_url": record["publisher_zip_url"],
            "sha256": existing,
        }
        if existing is not None:
            reused += 1
            entry["status"] = "REUSED_SAVED_PUBLISHER_CHECKSUM_MATCH"
        elif not fetch_manual:
            pending += 1
            entry["status"] = "PENDING_EXPLICIT_MANUAL_FETCH"
        elif max_fetch_files is not None and attempts >= max_fetch_files:
            pending += 1
            entry["status"] = "PENDING_MANUAL_BUDGET"
        else:
            attempts += 1
            pair = {}
            url = record["publisher_zip_url"]

            def transport(request_url, max_bytes):
                if request_url not in (url, url + ".CHECKSUM"):
                    raise ValueError("STAGE136_NON_FROZEN_SOURCE_URL")
                data = get(request_url, max_bytes)
                if not isinstance(data, bytes) or not data or len(data) > max_bytes:
                    raise ValueError("STAGE136_INVALID_SOURCE_RESPONSE_BYTES")
                pair[request_url] = data
                return data

            try:
                _, receipt = publisher.verified_day(
                    record["symbol"], record["day"], fetch=transport,
                    save_dir=None)
            except (FileNotFoundError, RuntimeError) as exc:
                unavailable += 1
                entry["status"] = "SOURCE_UNAVAILABLE_RETRY_ONLY_ON_NEW_MANUAL_RUN"
                entry["source_error_type"] = type(exc).__name__
            else:
                if set(pair) != {url, url + ".CHECKSUM"}:
                    raise ValueError("STAGE136_MISSING_OR_DUPLICATE_HTTP_RECEIPT")
                # Both source bytes pass the original unmodified parser + checksum
                # before being moved to the Stage135 archive convention.
                root.mkdir(parents=True, exist_ok=True)
                dest = root / record["symbol"]
                dest.mkdir(parents=True, exist_ok=True)
                with tempfile.TemporaryDirectory(prefix="monster136_", dir=root) as tmp:
                    zip_tmp = Path(tmp) / "verified.zip"
                    checksum_tmp = Path(tmp) / "verified.zip.CHECKSUM"
                    zip_tmp.write_bytes(pair[url])
                    checksum_tmp.write_bytes(pair[url + ".CHECKSUM"])
                    os.replace(zip_tmp, dest / (record["day"] + ".zip"))
                    os.replace(checksum_tmp, dest / (record["day"] + ".zip.CHECKSUM"))
                # Actual Stage135 local reader must recheck persisted bytes.
                saved = read_saved(root, record)
                if saved != receipt["zip_sha256"]:
                    raise ValueError("STAGE136_PERSISTED_SOURCE_SHA_DRIFT")
                fetched += 1
                entry["status"] = "FETCHED_PUBLISHER_CHECKSUM_MATCH"
                entry["sha256"] = saved
        source_records.append(entry)
    if reused + fetched + unavailable + pending != len(planned):
        raise ValueError("STAGE136_MANIFEST_POPULATION_COUNT_DRIFT")
    return {
        "schema": SCHEMA, "mode": "EXPLICIT_MANUAL_FETCH" if fetch_manual else "OFFLINE_PLAN",
        "stage134_t0_source_sha256": base["stage133_packet_integrity_sha256"],
        "window_utc_start": base["new_forward_start_utc"],
        "window_utc_end_exclusive": base["new_forward_end_exclusive_utc"],
        "full_initial_venue_symbol_attempts": base["t0_active_usdt_perpetual_attempts"],
        "in_window_arrival_candidates_unverified": base["in_window_arrival_candidates_unverified"],
        "all_symbol_day_attempts": len(planned),
        "reused_checksum_verified": reused,
        "newly_fetched_checksum_verified": fetched,
        "unavailable_not_negative": unavailable,
        "pending_manual_run": pending,
        "fetch_attempts_this_run": attempts,
        "independently_authenticated_http_origin": False,
        "in_window_new_listing_census_complete": False,
        "next_validation": "RUN_STAGE135_FULL_MARKET_SOURCE_COVERAGE_AUDIT",
        "G0": "PARTIAL", "G1": "NOT_SCORABLE", "G2_G3": "NOT_PASSED",
        "G4": "UNKNOWN", "G5": "NOT_DONE", "G6": "NO_GO",
        "model_buy": "NO_GO",
        "historical_stage116_first": "SOURCE_FAILED_NO_BACKFILL",
        "old_stage118_stage127": "REJECTED_UNCHANGED",
        "stage132_early_momentum_buy_proxy": "NEGATIVE_UNCHANGED",
        "scheduled_automation_created": False, "Gmail": "OFF", "Frank": "UNCHANGED",
        "file_receipts": source_records,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--t0", type=Path, required=True)
    p.add_argument("--arrival-candidates", type=Path)
    p.add_argument("--archive-root", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--fetch-manual", action="store_true")
    p.add_argument("--capture-request", type=Path)
    p.add_argument("--max-fetch-files", type=int)
    args = p.parse_args()
    if args.fetch_manual and args.capture_request is None:
        p.error("--fetch-manual requires explicit --capture-request")
    if args.capture_request is not None and not args.fetch_manual:
        p.error("--capture-request cannot start a fetch without --fetch-manual")
    # No GET and no archives changed before source/T0 and operator permission.
    t0 = json.loads(args.t0.read_text(encoding="utf-8"))
    arrivals = (json.loads(args.arrival_candidates.read_text(encoding="utf-8"))
                if args.arrival_candidates is not None else None)
    request = (json.loads(args.capture_request.read_text(encoding="utf-8"))
               if args.capture_request is not None else None)
    result = acquire(
        t0, args.archive_root, arrivals, fetch_manual=args.fetch_manual,
        capture_request=request, max_fetch_files=args.max_fetch_files)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False,
                                   sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in (
        "mode", "all_symbol_day_attempts", "reused_checksum_verified",
        "newly_fetched_checksum_verified", "unavailable_not_negative",
        "pending_manual_run", "G0", "G1", "model_buy")}, sort_keys=True))


if __name__ == "__main__":
    main()
