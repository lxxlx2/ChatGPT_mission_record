"""Manual, bounded official Binance Spot511 daily 1m acquisition (no schedule).

Default is no-network plan. --download must be explicitly requested for a
completed UTC day; verifies the original publisher ZIP SHA + 1440 microsecond
rows with the already-reviewed Stage166 validator before persisting any pair.
Does not trade, send mail, install services, or run D0/D1 signals.
"""
import argparse
from datetime import date, datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
import zipfile
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

import monster_v4_stage166_spot511_official_1m_intake as stage166

SCHEMA = "MONSTER_SPOT511_MANUAL_PUBLISHER_BATCH_V1"
START = date(2026, 10, 16)
END = date(2026, 10, 24)
MAX_BATCH = 64
MAX_ZIP_BYTES = 3_000_000
BASE = "https://data.binance.vision/data/spot/daily/klines"
HASH_RE = re.compile(r"([0-9a-fA-F]{64})\s+\*?([^\s/\\]+\.zip)\Z")


class SourceRejected(Exception):
    pass


class SameHostRedirects(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        parsed = urlsplit(newurl)
        if parsed.scheme != "https" or parsed.hostname != "data.binance.vision":
            raise SourceRejected("REDIRECT_OUTSIDE_OFFICIAL_SOURCE")
        return super().redirect_request(request, fp, code, msg, headers, newurl)


_OPENER = build_opener(SameHostRedirects())


def _read_https(url, limit):
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.hostname != "data.binance.vision":
        raise SourceRejected("UNAPPROVED_SOURCE_URL")
    with _OPENER.open(Request(url, headers={"User-Agent": "MonsterP0ManualSource/1.0"}),
                      timeout=15) as response:
        if response.getcode() != 200:
            raise SourceRejected("OFFICIAL_HTTP_NOT_200")
        body = response.read(limit + 1)
    if len(body) > limit:
        raise SourceRejected("PUBLISHER_RESPONSE_TOO_LARGE")
    return body


def _completed(day, now):
    midnight_after = datetime.combine(day + timedelta(days=1),
                                      datetime.min.time(), timezone.utc)
    return now >= midnight_after


def batch(day, destination, *, start_index=0, count=32, now=None,
          download=False, fetcher=None, roster=None):
    if not isinstance(day, date) or isinstance(day, datetime) or not START <= day <= END:
        raise ValueError("DAY_OUTSIDE_FROZEN_T0_WINDOW")
    if (type(start_index) is not int or type(count) is not int
            or start_index < 0 or count < 1 or count > MAX_BATCH
            or start_index + count > 511):
        raise ValueError("UNBOUNDED_OR_INVALID_ROSTER_SLICE")
    now = now or datetime.now(timezone.utc)
    if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("UTC_AWARE_CLOCK_REQUIRED")
    now = now.astimezone(timezone.utc)
    if not _completed(day, now):
        raise ValueError("DAY_NOT_YET_ENDED_NEVER_FETCH_FUTURE")
    actual = stage166.frozen_roster() if roster is None else roster
    if (not isinstance(actual, list) or len(actual) != 511
            or actual != sorted(set(actual))
            or any(not isinstance(s, str) or not s.isalnum()
                   or not s.endswith("USDT") for s in actual)):
        raise ValueError("ORIGINAL_T0_FROZEN_511_REQUIRED")
    selected = actual[start_index:start_index+count]
    destination = Path(destination)
    fetch = fetcher if fetcher is not None else _read_https
    rows = []
    for symbol in selected:
        target_zip, target_checksum = stage166.daily_paths(destination, symbol, day)
        url = f"{BASE}/{quote(symbol, safe='')}/1m/{quote(target_zip.name, safe='')}"
        row = {"symbol": symbol, "day_utc": day.isoformat(),
               "source_url": url, "status": "PLANNED_NO_NETWORK",
               "zip_sha256": None, "closed_one_minute_rows": None}
        if download:
            if target_zip.is_symlink() or target_checksum.is_symlink():
                row["status"] = "LOCAL_SOURCE_SYMLINK_REJECTED_NO_OVERWRITE"
            elif target_zip.exists() or target_checksum.exists():
                if target_zip.is_file() and target_checksum.is_file():
                    try:
                        proof = stage166.validate_daily_zip(
                            target_zip, target_checksum, symbol, day)
                        row.update(status="ALREADY_VERIFIED_LOCAL",
                                   zip_sha256=proof["zip_sha256"],
                                   closed_one_minute_rows=1440)
                    except (ValueError, OSError, UnicodeError) as exc:
                        row.update(status="LOCAL_SOURCE_REJECTED_NO_OVERWRITE",
                                   error=type(exc).__name__ + ":" + str(exc)[:150])
                else:
                    row["status"] = "INCOMPLETE_EXISTING_LOCAL_PAIR_NO_OVERWRITE"
            else:
                try:
                    checksum_bytes = fetch(url + ".CHECKSUM", 256)
                    checksum_text = checksum_bytes.decode("utf-8").strip()
                    match = HASH_RE.fullmatch(checksum_text)
                    if not match or match.group(2) != target_zip.name:
                        raise SourceRejected("CHECKSUM_NAME_OR_FORMAT_INVALID")
                    original = fetch(url, MAX_ZIP_BYTES)
                    digest = hashlib.sha256(original).hexdigest()
                    if digest != match.group(1).lower():
                        raise SourceRejected("OFFICIAL_CHECKSUM_MISMATCH")
                    # Stage166's exact official ZIP parser runs on temporary bytes.
                    # Stage on the destination volume to avoid EXDEV, and use
                    # exclusive hard links: an existence-check followed by
                    # os.replace() could silently overwrite a competing writer.
                    target_zip.parent.mkdir(parents=True, exist_ok=True)
                    with tempfile.TemporaryDirectory(
                            prefix=".monster-src-", dir=target_zip.parent) as tmp:
                        temp_zip = Path(tmp) / target_zip.name
                        temp_sum = Path(tmp) / target_checksum.name
                        temp_zip.write_bytes(original)
                        temp_sum.write_bytes(checksum_bytes)
                        proof = stage166.validate_daily_zip(
                            temp_zip, temp_sum, symbol, day)
                        if target_zip.exists() or target_checksum.exists():
                            raise SourceRejected("CONCURRENT_LOCAL_FILE_NO_OVERWRITE")
                        target_zip.parent.mkdir(parents=True, exist_ok=True)
                        # If interrupted between two exclusive links, the next
                        # run observes a partial pair and refuses to overwrite it.
                        # Never count partial pairs as source-admitted.
                        os.link(temp_sum, target_checksum)
                        os.link(temp_zip, target_zip)
                    row.update(status="VERIFIED_FULL_DAY_1440",
                               zip_sha256=proof["zip_sha256"],
                               closed_one_minute_rows=proof["closed_one_minute_rows"])
                except (HTTPError, URLError, TimeoutError, OSError,
                        UnicodeError, ValueError, zipfile.BadZipFile,
                        zipfile.LargeZipFile, SourceRejected) as exc:
                    row.update(status="SOURCE_UNAVAILABLE_OR_REJECTED",
                               error=type(exc).__name__ + ":" + str(exc)[:150])
        rows.append(row)
    return {"schema": SCHEMA, "execution": "MANUAL_DOWNLOAD" if download else "PLAN_ONLY",
            "checked_at_utc": now.isoformat(), "frozen_total": 511,
            "day_utc": day.isoformat(), "start_index": start_index,
            "batch_size": count, "source_records": rows,
            "verified_downloads": sum(x["status"] == "VERIFIED_FULL_DAY_1440" for x in rows),
            "source_missing_is_not_a_zero_watch": True, "actual_d0_d1_replay": False,
            "PIT_listing_changes_verified": False,
            "G0": "PARTIAL", "G4": "UNKNOWN", "G6": "NO_GO",
            "NO_SCHEDULE": True, "NO_DEPLOY": True,
            "NO_GMAIL": True, "NO_TRADES": True}


def main():
    p = argparse.ArgumentParser(description="Manual bounded Spot 511 official daily source intake")
    p.add_argument("--day", type=date.fromisoformat, required=True)
    p.add_argument("--dest", type=Path, required=True)
    p.add_argument("--start-index", type=int, default=0)
    p.add_argument("--count", type=int, default=32)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--download", action="store_true",
                   help="explicitly authorize one bounded foreground batch")
    args = p.parse_args()
    if args.out.exists() or args.out.is_symlink():
        raise ValueError("SOURCE_MANIFEST_ALREADY_EXISTS_NO_OVERWRITE")
    result = batch(args.day, args.dest, start_index=args.start_index,
                   count=args.count, download=args.download)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x", encoding="utf-8") as fp:
        json.dump(result, fp, indent=2, sort_keys=True)
        fp.write("\n")
    print(json.dumps({"day": result["day_utc"], "mode": result["execution"],
                      "batch_size": result["batch_size"],
                      "verified_downloads": result["verified_downloads"],
                      "G6": result["G6"]}, sort_keys=True))


if __name__ == "__main__":
    main()
