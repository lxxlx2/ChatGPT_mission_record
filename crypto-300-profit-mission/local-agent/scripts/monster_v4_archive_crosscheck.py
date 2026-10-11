#!/usr/bin/env python3
"""Stage11: read-only Binance official ZIP archive vs frozen REST 1m crosscheck.

One-time independent public source availability pilot, not ongoing monitor.
2025+ Spot Binance Public Data ZIP timestamps use MICROSECONDS; REST uses MS.
Verify published SHA256 checksum before opening CSV, enforce 1m continuity,
then compare every closed minute with the previously frozen authentic REST data.
Never fetch private/account endpoints, trade, or change Frank.
"""
import csv
import hashlib
import io
import json
import re
import urllib.error
import urllib.request
import zipfile
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

BASE = "https://data.binance.vision"
EVIDENCE = Path(__file__).resolve().parents[2] / "monster/evidence"
PILOT = ("QUICKUSDT", "TNSRUSDT", "PORTOUSDT", "LTCUSDT")
ANCHOR = "2026-09-17T12:00:00Z"
DATE = date(2026, 9, 17)
MAX_ZIP_BYTES = 12_000_000


def zip_url(symbol, day):
    if not re.fullmatch(r"[A-Z0-9]+USDT", symbol):
        raise ValueError("INVALID_SYMBOL")
    stamp = day.isoformat()
    filename = symbol + "-1m-" + stamp + ".zip"
    return BASE + "/data/spot/daily/klines/" + symbol + "/1m/" + filename


def read_url(url, max_bytes=MAX_ZIP_BYTES):
    req = urllib.request.Request(url, headers={"User-Agent":"MonsterV4-Research/1.0"})
    with urllib.request.urlopen(req, timeout=35) as f:
        content = f.read(max_bytes + 1)
    if not content or len(content) > max_bytes:
        raise ValueError("EMPTY_OR_OVERSIZE_OFFICIAL_ARCHIVE")
    return content


def extract_verified_archive(zip_bytes, checksum_bytes, symbol, day):
    checksum = checksum_bytes.decode("utf-8").strip().split()
    if not checksum or not re.fullmatch(r"[0-9a-fA-F]{64}", checksum[0]):
        raise ValueError("INVALID_PUBLISHED_SHA256")
    expected = checksum[0].lower()
    got = hashlib.sha256(zip_bytes).hexdigest()
    if got != expected:
        raise ValueError("PUBLISHED_ARCHIVE_CHECKSUM_MISMATCH")
    filename = symbol + "-1m-" + day.isoformat() + ".csv"
    if len(zip_bytes) > MAX_ZIP_BYTES:
        raise ValueError("OVERSIZE_ARCHIVE")
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
        members = [m for m in z.namelist() if m.endswith(".csv")]
        if members != [filename]:
            raise ValueError("UNEXPECTED_ARCHIVE_CSV_MEMBER")
        if z.getinfo(members[0]).file_size > 15_000_000:
            raise ValueError("UNSAFE_DECOMPRESSED_CSV_SIZE")
        with z.open(filename) as csv_file:
            reader = csv.reader(io.TextIOWrapper(csv_file, encoding="utf-8"))
            rows = []
            for row in reader:
                if len(row) < 9 or not row[0].isdigit():
                    raise ValueError("INVALID_OFFICIAL_CSV_BAR")
                ts = int(row[0])
                if ts >= 10**15:
                    if ts % 1000:
                        raise ValueError("NON_MINUTE_ALIGNED_MICROSECOND_TIMESTAMP")
                    ms = ts // 1000
                elif 10**12 <= ts < 10**15:
                    ms = ts
                else:
                    raise ValueError("UNKNOWN_ARCHIVE_TIMESTAMP_UNIT")
                rows.append((ms, *(Decimal(row[i]) for i in (1,2,3,4,7)), int(row[8])))
    day_start = int(__import__("datetime").datetime(
        day.year,day.month,day.day,tzinfo=__import__("datetime").timezone.utc).timestamp()*1000)
    if len(rows) != 1440 or any(row[0] != day_start + i*60000 for i,row in enumerate(rows)):
        raise ValueError("GAPPED_ARCHIVE_DAY")
    return rows, {"url":zip_url(symbol,day),"sha256":got,
                  "rows":len(rows),"verified_published_sha256":True,
                  "timestamp_unit_normalized_to_ms":True}


def load_rest(symbol):
    path = EVIDENCE / ("monster_stage10_neutral_1m_spot_" + symbol + "_2026-09-17.json")
    original = json.loads(path.read_text(encoding="utf-8"))
    if (original.get("symbol"),original.get("cohort"),original.get("data_integrity")) != (
        symbol, "STAGE10_PRE_REGISTERED_NEUTRAL", "CONTIGUOUS_3600"):
        raise ValueError("REST_RESEARCH_SAMPLE_WRONG_IDENTITY")
    result = [(int(x[0]), *(Decimal(str(y)) for y in x[1:6]), int(x[6]))
              for x in original["bars"]]
    if len(result)!=3600:
        raise ValueError("REST_WRONG_BAR_COUNT")
    return result


def verify_crosscheck(symbol, downloader=read_url):
    if symbol not in PILOT:
        raise ValueError("NOT_FROZEN_STAGE10_MATCHED_PILOT")
    days=[DATE+timedelta(days=i) for i in (-1,0,1)]
    bars=[]
    detail=[]
    for day in days:
        url=zip_url(symbol,day)
        compressed=downloader(url)
        checksum=downloader(url+".CHECKSUM",2048)
        rows,meta=extract_verified_archive(compressed,checksum,symbol,day)
        bars.extend(rows)
        detail.append(meta)
    frozen=load_rest(symbol)
    offset=360
    selection=bars[offset:offset+3600]
    if len(selection)!=3600:
        raise ValueError("INSUFFICIENT_ARCHIVED_TIME_WINDOW")
    if selection != frozen:
        index=next((i for i,(a,b) in enumerate(zip(selection,frozen)) if a!=b),None)
        raise ValueError("OFFICIAL_ARCHIVE_AND_REST_SOURCE_DISAGREE_AT_"+str(index))
    return {"symbol":symbol,"archive_days_sha256":detail,
            "matched_rest_minutes":len(frozen),
            "exact_value_agreement":True,
            "result":"OFFICIAL_ARCHIVE_CHECKSUM_AND_GENUINE_REST_1M_MATCHED"}


def main():
    report={"schema":"MONSTER_STAGE11_BINANCE_ZIP_VS_REST_V1",
            "official":BASE,"sample":"4 frozen prereg Sep2026 symbols",
            "status":"ALL_MATCHED","results":[],"deployment":"NO_GO",
            "automated_trading":False,"genuine_forward_return_verified":False}
    for symbol in PILOT:
        report["results"].append(verify_crosscheck(symbol))
    print(json.dumps(report,sort_keys=True))


if __name__=="__main__":
    main()
