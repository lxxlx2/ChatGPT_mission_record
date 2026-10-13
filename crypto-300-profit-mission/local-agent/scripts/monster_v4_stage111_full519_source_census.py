#!/usr/bin/env python3
"""Stage111: all-519 immutable historical source/time census. Read-only research.
No market polling, scheduling, notification, or deployment side effects.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timedelta, timezone
from hashlib import sha1
import json
from pathlib import Path
import re

MISSION = Path(__file__).resolve().parents[2]
EVIDENCE = MISSION / "monster" / "evidence"
CENSUS = EVIDENCE / "monster_stage83_all519_source_and_D1_result.jsonl"
STAGE110 = EVIDENCE / "monster_stage110_real519D0_305D1_causal_confirm_states.json"
PIN83 = "c76b3a137c8dbe56feed3a79a63adcc0752f5e2e"
PIN110 = "314c0ee532b93dd24dbda4ec6a146e03ee2c5c1b"
SCHEMA = "MONSTER_STAGE111_ALL519_HISTORIC_SOURCE_CENSUS_V1"
MINUTE = timedelta(minutes=1)
DAY = timedelta(days=1)


def blob_sha(raw: bytes) -> str:
    return sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def iso(s: str) -> datetime:
    dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
    if dt.tzinfo != timezone.utc or not s.endswith("Z"):
        raise ValueError("STAGE111_NON_UTC_TIME")
    return dt


def date_days(begin: datetime, end: datetime) -> list[str]:
    """Calendar days whose 1m OPEN can lie in the half-open [begin,end)."""
    if begin >= end:
        return []
    cur = begin.date()
    last = (end - MINUTE).date()
    days = []
    while cur <= last:
        days.append(cur.isoformat())
        cur += DAY
    return days


def check_receipts(x: dict) -> dict[str, str]:
    receipts = x["source_day_sha256_receipts"]
    if not isinstance(receipts, list) or not receipts:
        raise ValueError("STAGE111_SOURCE_PREFIX_MISSING")
    by_day = {}
    for item in receipts:
        day = item["date"]
        if (day in by_day or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", day)
                or item.get("bars") != 1440
                or item.get("verified_official_publisher_SHA256") is not True
                or not re.fullmatch(r"[0-9a-f]{64}", item["zip_sha256"])):
            raise ValueError("STAGE111_BAD_OR_DUPLICATE_OFFICIAL_RECEIPT")
        by_day[day] = item["zip_sha256"]
    if x["source_status"] != "COMPLETE_OFFICIAL_PREFIX_SHA_VERIFIED_3M_48H":
        raise ValueError("STAGE111_UNEXPECTED_PRIOR_SOURCE_STATUS")
    return by_day


def analyze(census: list[dict], archive: dict) -> dict:
    if len(census) != 519 or archive["all_D0_original_preserved"] != 519:
        raise ValueError("STAGE111_ORIGINAL_D0_COUNT_DRIFT")
    if archive["all_D1_original_preserved"] != 305:
        raise ValueError("STAGE111_ORIGINAL_D1_COUNT_DRIFT")
    keys = {(x["date"], x["symbol"]) for x in census}
    if len(keys) != 519:
        raise ValueError("STAGE111_DUPLICATE_ORIGINAL_D0")
    d1 = {(x["date"], x["symbol"]) for x in census if x["D1_FIRST_UTC"] is not None}
    archive_d1 = {(x["date"], x["symbol"]) for x in archive["all_source_cases"]}
    d0only = {(x["date"], x["symbol"]) for x in archive["D0_WATCH_without_original_D1"]}
    if (len(d1) != 305 or len(archive_d1) != 305
            or len(d0only) != 214 or d1 != archive_d1
            or d1 & d0only or d1 | d0only != keys):
        raise ValueError("STAGE111_519_305_214_PARTITION_CHANGED")
    if (sum(bool(x["D0_at_least_5m_before_2x"]) for x in census) != 28
            or sum(bool(x["D1_at_least_5m_before_2x"]) for x in census) != 27
            or archive["original_D1_7day_2x_early5_over_D0_28"] != 27):
        raise ValueError("STAGE111_FIXED_DISCOVERY_LABEL_DRIFT")

    indexed = {(x["date"], x["symbol"]): x for x in archive["all_source_cases"]}
    old_only = {(x["date"], x["symbol"]): x for x in archive["D0_WATCH_without_original_D1"]}
    identities, by_anchor, prefix_counts = Counter(), Counter(), Counter()
    all_rows = []
    for x in sorted(census, key=lambda z: (z["date"], z["symbol"])):
        key = (x["date"], x["symbol"])
        earliest = iso(x["D0_FIRST_UTC"])
        anchor = iso(x["date"] + "T06:00:00Z")
        limit = anchor + 7 * DAY
        if not anchor <= earliest < limit:
            raise ValueError("STAGE111_D0_OUTSIDE_ANCHOR_WINDOW")
        d1_at = iso(x["D1_FIRST_UTC"]) if x["D1_FIRST_UTC"] else None
        if d1_at and d1_at < earliest:
            raise ValueError("STAGE111_D1_BEFORE_D0")
        previous = indexed.get(key)
        if previous:
            if (previous["D0_FIRST_UTC"] != x["D0_FIRST_UTC"]
                    or previous["D1_FIRST_UTC"] != x["D1_FIRST_UTC"]
                    or previous["D1_PATH"] != x["D1_PATH"]
                    or previous["identity"] != x["identity"]):
                raise ValueError("STAGE111_STAGE110_ORIGINAL_SIGNAL_DRIFT")
            for rec in previous["source_days_real_official_sha"]:
                old_hash = {d["date"]: d["zip_sha256"] for d in x["source_day_sha256_receipts"]}.get(rec["date"])
                if old_hash and rec["zip_sha256"] != old_hash:
                    raise ValueError("STAGE111_STAGE110_ORIGINAL_ZIP_SHA_CONFLICT")
        elif old_only[key]["D0_FIRST_UTC"] != x["D0_FIRST_UTC"]:
            raise ValueError("STAGE111_ARCHIVED_D0_ONLY_TIMESTAMP_DRIFT")

        receipts = check_receipts(x)
        # D0 t is a signal evaluation timestamp; first downstream completed
        # 1m source bar can open at t+1m, and is visible at t+2m.
        start = earliest + MINUTE
        needed = date_days(start, limit)
        existing = [day for day in needed if day in receipts]
        unknown = [day for day in needed if day not in receipts]
        if not needed:
            raise ValueError("STAGE111_NO_POST_D0_MINUTE_WITHIN_WINDOW")
        identities[x["identity"]] += 1
        by_anchor[x["date"]] += 1
        prefix_counts[len(receipts)] += 1
        all_rows.append({
            "date": x["date"], "symbol": x["symbol"],
            "identity": x["identity"],
            "D0_FIRST_UTC": x["D0_FIRST_UTC"],
            "original_D1_FIRST_UTC": x["D1_FIRST_UTC"],
            "original_D1_path": x["D1_PATH"],
            "original_D0_early5_2x_EVAL_ONLY": x["D0_at_least_5m_before_2x"],
            "original_D1_early5_2x_EVAL_ONLY": x["D1_at_least_5m_before_2x"],
            "first_post_D0_minute_open_UTC": start.isoformat().replace("+00:00", "Z"),
            "censor_at_fixed_anchor_end_UTC": limit.isoformat().replace("+00:00", "Z"),
            "maximum_remaining_minutes": int((limit - start).total_seconds() // 60),
            "prior_prefix_receipt_days": sorted(receipts),
            "required_calendar_days_to_anchor_end": needed,
            "required_days_with_existing_prefix_receipts": existing,
            "required_days_without_existing_prefix_receipts": unknown,
            "all_required_days_receipted": not unknown,
            "full_minute_sequence_checked": False,
            "future_trade_executable": "UNKNOWN",
            "research_only_exposed": True,
        })
    return {
        "schema": SCHEMA,
        "input_stage83_git_blob": PIN83,
        "input_stage110_git_blob": PIN110,
        "D0_original_total": len(all_rows),
        "original_D1_total": len(d1),
        "D0_only_total": len(d0only),
        "original_D0_early_2x_ge5min_EVAL_ONLY": 28,
        "original_D1_early_2x_ge5min_EVAL_ONLY": 27,
        "identities_not_assumed_tradeable": dict(sorted(identities.items())),
        "original_anchor_date_counts": dict(sorted(by_anchor.items())),
        "source_prefix_receipt_day_counts": dict(sorted(prefix_counts.items())),
        "cases_missing_at_least_one_seven_day_source_day_receipt":
            sum(bool(x["required_days_without_existing_prefix_receipts"]) for x in all_rows),
        "cases_with_all_required_day_receipts":
            sum(x["all_required_days_receipted"] for x in all_rows),
        "all_519_seven_day_continuous_minute_sources_replayed": False,
        "actual_bid_ask_notional_and_net": "UNKNOWN",
        "strategy_frozen": False,
        "monster_deployment": "NO_GO",
        "rows": all_rows,
    }


def frozen() -> tuple[list[dict], dict]:
    raw83, raw110 = CENSUS.read_bytes(), STAGE110.read_bytes()
    if blob_sha(raw83) != PIN83 or blob_sha(raw110) != PIN110:
        raise ValueError("STAGE111_IMMUTABLE_SOURCE_GIT_BLOB_CHANGED")
    return ([json.loads(s) for s in raw83.decode().splitlines() if s.strip()],
            json.loads(raw110))


def selftest() -> None:
    assert date_days(iso("2026-10-13T23:59:00Z"),
                     iso("2026-10-14T00:00:00Z")) == ["2026-10-13"]
    assert date_days(iso("2026-10-13T23:59:00Z"),
                     iso("2026-10-14T00:01:00Z")) == ["2026-10-13", "2026-10-14"]
    assert blob_sha(b"test") == "30d74d258442c7c65512eafab474568dd706c430"
    bad = {"source_status": "COMPLETE_OFFICIAL_PREFIX_SHA_VERIFIED_3M_48H",
           "source_day_sha256_receipts": [
               {"date": "2026-10-13", "bars": 1440,
                "verified_official_publisher_SHA256": True, "zip_sha256": "a" * 64}]}
    assert check_receipts(bad)["2026-10-13"] == "a" * 64
    bad["source_day_sha256_receipts"].append(dict(bad["source_day_sha256_receipts"][0]))
    try:
        check_receipts(bad)
    except ValueError:
        pass
    else:
        raise AssertionError("STAGE111_DUPLICATE_RECEIPT_NOT_REJECTED")
    print("STAGE111_SOURCE_CENSUS_TIME_SHA_DUPLICATE_SELFTEST_PASS")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.selftest:
        selftest()
        return
    if args.out is None:
        parser.error("--out required")
    rows, prior = frozen()
    result = analyze(rows, prior)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
    print("STAGE111_FULL519_IMMUTABLE_CENSUS_PASS " + json.dumps(
        {k: v for k, v in result.items() if k != "rows"}, sort_keys=True))


if __name__ == "__main__":
    main()
