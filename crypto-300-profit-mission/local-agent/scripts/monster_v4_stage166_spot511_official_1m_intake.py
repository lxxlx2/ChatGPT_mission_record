#!/usr/bin/env python3
"""Stage166: immutable Spot T0 511-roster to official daily minute-file readiness.

Pure local source admission; NO HTTP, no scheduler, no replay, no trade.
An absent local archive is SOURCE_NOT_SUPPLIED, never a historical zero signal.
"""
import argparse
from collections import Counter
import csv
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
import re
import zipfile

import monster_v4_stage163_spot_t0_quote_friction as stage163

SCHEMA = "MONSTER_STAGE166_FROZEN_T0_511_OFFICIAL_SPOT_1M_INTAKE_V1"
START = date(2026, 10, 16)
DAYS = 9
ACTIVE = 511
T0_MS = 1792274680094
CHECKSUM = re.compile(r"([0-9a-fA-F]{64})\s+\*?([^\s]+)")
MAX_CSV_BYTES = 2_000_000


def frozen_roster(zip_path=None, receipts_path=None):
    opts = {}
    if zip_path is not None:
        opts["zip_path"] = zip_path
    if receipts_path is not None:
        opts["receipts_path"] = receipts_path
    blobs, receipts = stage163.load_archived(**opts)
    info = blobs["exchangeInfo"]
    if int(info["serverTime"]) != T0_MS:
        raise ValueError("STAGE166_SPOT_T0_EXCHANGE_CLOCK_DRIFT")
    usdt = [s for s in info["symbols"]
            if s.get("quoteAsset") == "USDT"
            and s.get("isSpotTradingAllowed") is not False]
    eligible = [s["symbol"] for s in usdt if s["status"] == "TRADING"]
    if (len(eligible) != ACTIVE or len(set(eligible)) != ACTIVE
        or len(usdt) != 725
        or sum(x["status"] == "BREAK" for x in usdt) != 214
        or any(not x.isalnum() or not x.endswith("USDT") for x in eligible)
        or receipts["stats"]["spot_usdt_active"] != ACTIVE):
        raise ValueError("STAGE166_FROZEN_511_USDT_CENSUS_DRIFT")
    return sorted(eligible)


def daily_paths(root, symbol, day):
    # All path components are frozen exchange symbols or date.fromisoformat.
    basename = f"{symbol}-1m-{day.isoformat()}.zip"
    path = Path(root) / symbol / "1m" / basename
    return path, path.with_name(basename + ".CHECKSUM")


def validate_daily_zip(zip_path, checksum_path, symbol, day):
    """Official issuer-hash + complete 1440 closed 1m Spot microsecond rows."""
    original = zip_path.read_bytes()
    raw_checksum = checksum_path.read_text(encoding="utf-8")
    matches = CHECKSUM.fullmatch(raw_checksum.strip())
    if not matches or matches.group(2) != zip_path.name:
        raise ValueError("STAGE166_OFFICIAL_SHA256_CHECKSUM_FORMAT_OR_NAME_DRIFT")
    sha = hashlib.sha256(original).hexdigest()
    if sha != matches.group(1).lower():
        raise ValueError("STAGE166_OFFICIAL_ZIP_SHA256_MISMATCH")
    expected = f"{symbol}-1m-{day.isoformat()}.csv"
    start = int(datetime.combine(day, datetime.min.time(), timezone.utc).timestamp()) * 1_000_000
    interval = 60 * 1_000_000
    with zipfile.ZipFile(zip_path) as z:
        files = z.infolist()
        if (len(files) != 1 or files[0].filename != expected
            or files[0].file_size > MAX_CSV_BYTES or files[0].is_dir()):
            raise ValueError("STAGE166_OFFICIAL_ZIP_CSV_MEMBER_SHAPE")
        with z.open(files[0]) as stream:
            import io
            rdr = csv.reader(io.TextIOWrapper(stream, encoding="utf-8", newline=""))
            count = 0
            for row in rdr:
                if len(row) != 12 or count >= 1440:
                    raise ValueError("STAGE166_SPOT_1M_ROW_COUNT_OR_FIELDS")
                try:
                    opening = int(row[0])
                    closing = int(row[6])
                    op,hi,lo,cl,vol,qvol = (Decimal(row[k]) for k in (1,2,3,4,5,7))
                    trades = int(row[8])
                except (ValueError, TypeError, InvalidOperation) as exc:
                    raise ValueError("STAGE166_SPOT_1M_INVALID_PUBLISHER_FIELDS") from exc
                if (opening != start + count * interval
                    or closing != opening + interval - 1
                    or any(not n.is_finite() for n in (op,hi,lo,cl,vol,qvol))
                    or min(op,hi,lo,cl) <= 0 or not (lo <= op <= hi and lo <= cl <= hi)
                    or vol < 0 or qvol < 0 or trades < 0):
                    raise ValueError("STAGE166_SPOT_1M_MICROSECOND_GRID_OR_OHLC_DRIFT")
                count += 1
            if count != 1440:
                raise ValueError("STAGE166_SPOT_1M_INCOMPLETE_1440")
    return {"zip_sha256": sha, "closed_one_minute_rows": count,
            "original_publisher_checksum_valid": True, "spot_timestamp_units": "MICROSECONDS"}


def build_report(source_dir, asof_utc, *, zip_path=None, receipts_path=None):
    if asof_utc.tzinfo is None:
        raise ValueError("STAGE166_ASOF_MUST_BE_UTC_AWARE")
    asof_utc = asof_utc.astimezone(timezone.utc)
    roster = frozen_roster(zip_path, receipts_path)
    rows = []
    errors = Counter()
    for sym in roster:
        for delta in range(DAYS):
            day = START + timedelta(days=delta)
            local_zip, checksum_path = daily_paths(source_dir, sym, day)
            future_day = datetime.combine(day+timedelta(days=1),
                                          datetime.min.time(), timezone.utc) > asof_utc
            if future_day:
                status = "UTC_DAY_NOT_YET_ENDED"
                detail = None
            elif not local_zip.is_file() and not checksum_path.is_file():
                status = "SOURCE_NOT_SUPPLIED"
                detail = None
            elif not local_zip.is_file() or not checksum_path.is_file():
                status = "SOURCE_REJECTED_OR_INCOMPLETE"
                detail = "PUBLISHER_ZIP_AND_CHECKSUM_PAIR_REQUIRED"
            else:
                try:
                    detail = validate_daily_zip(local_zip,checksum_path,sym,day)
                    status = "VERIFIED_FULL_DAY_1440"
                except (ValueError, zipfile.BadZipFile, OSError, UnicodeError) as exc:
                    status = "SOURCE_REJECTED_OR_INCOMPLETE"
                    detail = str(exc)
            errors[status] += 1
            basename = f"{sym}-1m-{day.isoformat()}.zip"
            rows.append({
                "symbol": sym,
                "date_utc": day.isoformat(),
                "publisher_zip_url": ("https://data.binance.vision/data/spot/daily/"
                    f"klines/{sym}/1m/{basename}"),
                "archive_status": status,
                "source_detail": detail,
            })
    if len(rows) != 511*9 or sum(errors.values()) != 511*9:
        raise RuntimeError("STAGE166_FULL_T0_UNIVERSE_SOURCE_ATTEMPT_DRIFT")
    verified = errors["VERIFIED_FULL_DAY_1440"]
    return {
        "schema": SCHEMA, "source_t0_server_time_ms": T0_MS,
        "t0_spot_usdt_trading": ACTIVE, "t0_spot_usdt_break_excluded": 214,
        "t0_eligible_symbol_ids": roster, "utc_daily_source_dates": [
            (START+timedelta(days=d)).isoformat() for d in range(DAYS)],
        "window_start_utc": "2026-10-17T22:06:00Z",
        "window_end_exclusive_utc": "2026-10-24T22:06:00Z",
        "three_minute_ticks_total": 3360,
        "asof_source_check_utc": asof_utc.isoformat().replace("+00:00","Z"),
        "daily_source_attempts": len(rows), "admission_counts": dict(sorted(errors.items())),
        "attempts": rows,
        "all_511_nine_days_officially_verified": verified == len(rows),
        "full_7d_exchange_listing_changes_proven": False,
        "stage166_is_not_historical_pit_full_execution": True,
        "no_absent_source_is_classified_as_zero_signal": True,
        "historical_bid_ask_at_each_signal": "UNVERIFIED",
        "real_net_profit": "UNVERIFIED",
        "G4": "UNKNOWN", "G6": "NO_GO",
        "NO_MERGE": True, "NO_DEPLOY": True, "NO_GMAIL": True, "NO_TRADE": True
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-dir", type=Path, required=True)
    ap.add_argument("--asof-utc", required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--t0-zip", type=Path)
    ap.add_argument("--t0-receipts", type=Path)
    args = ap.parse_args()
    if args.out.exists() or args.out.is_symlink():
        raise ValueError("STAGE166_OUTPUT_ALREADY_EXISTS_REFUSE_OVERWRITE")
    asof = datetime.fromisoformat(args.asof_utc.replace("Z","+00:00"))
    report = build_report(args.source_dir, asof,
        zip_path=args.t0_zip, receipts_path=args.t0_receipts)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x", encoding="utf-8") as stream:
        json.dump(report,stream,indent=2,sort_keys=True,ensure_ascii=False)
        stream.write("\n")
    print("MONSTER166_OFFLINE_T0_511_SOURCE_ADMISSION",
        json.dumps({"t0_population":len(report["t0_eligible_symbol_ids"]),
            "source_attempts":report["daily_source_attempts"],
            "admissions":report["admission_counts"],
            "full_7d_data_verified":report["all_511_nine_days_officially_verified"],
            "G6":report["G6"]},sort_keys=True))


if __name__ == "__main__":
    main()
