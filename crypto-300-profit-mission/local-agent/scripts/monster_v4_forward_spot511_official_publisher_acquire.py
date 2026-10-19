#!/usr/bin/env python3
"""One-shot bounded official Binance Spot publisher ZIP+CHECKSUM acquisition.

Manual push-only offline research inputs; real publisher HTTPS downloads are
read-only and may NOT produce WATCH/SETUP/trade/production claims.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import monster_v4_stage166_spot511_official_1m_intake as admitted

SCHEMA = "MONSTER_SPOT511_ORIGINAL_PUBLISHER_DAILY_1M_ACQUISITION_V1"
BASE = "https://data.binance.vision/data/spot/daily/klines"
FIXED_DAYS = ("2026-10-16", "2026-10-17")
MAX_WORKERS = 8
ZIP_MAX = 20_000_000
CHECKSUM_MAX = 2048
REQ_TIMEOUT_SECONDS = 18
MAX_RETRIES = 2
OFFICIAL_SHA = "b47e206345c0a04b16b37c38795d726553ef83ca679f443f9fba89805483216b"


def utc():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def url_parts(symbol,day):
    if not (symbol.isalnum() and symbol.endswith("USDT")
            and day in FIXED_DAYS):
        raise ValueError("MONSTER_PUBLISHER_FROZEN_SYMBOL_OR_DAY_DRIFT")
    filename = f"{symbol}-1m-{day}.zip"
    url=f"{BASE}/{symbol}/1m/{filename}"
    return filename,url,url+".CHECKSUM"


def fetch_one_url(url, limit, *, getter=None):
    """Only publisher domain, finite bytes, HTTP response metadata and retries."""
    if not url.startswith(BASE+"/") or (not url.endswith(".zip") and
                                       not url.endswith(".zip.CHECKSUM")):
        raise ValueError("MONSTER_OFFICIAL_PUBLISHER_URL_NOT_ALLOWED")
    errors=[]
    for attempt in range(MAX_RETRIES+1):
        try:
            if getter is not None:
                data,metadata = getter(url)
                if len(data)>limit:
                    raise ValueError("PUBLISHER_RESPONSE_SIZE_LIMIT")
                return data,metadata
            request=Request(url,headers={"User-Agent":"monster-research-official-readonly/1.0"})
            with urlopen(request,timeout=REQ_TIMEOUT_SECONDS) as response:
                final=response.geturl()
                if final != url:
                    raise ValueError("PUBLISHER_UNEXPECTED_REDIRECT")
                data=response.read(limit+1)
                if len(data)>limit:
                    raise ValueError("PUBLISHER_RESPONSE_SIZE_LIMIT")
                headers={
                    "http_status":response.status,
                    "server_date":response.headers.get("Date"),
                    "last_modified":response.headers.get("Last-Modified"),
                    "etag":response.headers.get("ETag"),
                    "content_type":response.headers.get("Content-Type"),
                    "obtained_at_utc":utc()
                }
                return data,headers
        except HTTPError as exc:
            if exc.code in (404,410,403):
                raise RuntimeError(f"PUBLISHER_HTTP_{exc.code}") from exc
            errors.append(f"HTTP_{exc.code}")
        except (URLError,TimeoutError,OSError) as exc:
            errors.append(f"NETWORK_{type(exc).__name__}")
        if attempt<MAX_RETRIES:
            time.sleep(0.3*(attempt+1))
    raise RuntimeError("PUBLISHER_TRANSPORT_RETRIES_EXHAUSTED:"+",".join(errors))


def one_pair(symbol,day,root,*,getter=None):
    filename,zip_url,checksum_url=url_parts(symbol,day)
    result={
        "symbol":symbol,"date_utc":day,
        "publisher_zip_url":zip_url,"publisher_checksum_url":checksum_url,
        "source_provenance":"OFFICIAL_HTTPS_DATA_BINANCE_VISION",
        "status":"UNVERIFIED",
        "zip_sha256":None,
        "publisher_checksum_sha256":None,
        "error":None,
        "attempt_observed_at_utc":utc()
    }
    try:
        # Checksum first avoids downloading a huge ZIP for unpublished dates.
        checksum,cr=fetch_one_url(checksum_url,CHECKSUM_MAX,getter=getter)
        expected=checksum.decode("utf-8").strip()
        m=re.fullmatch(r"([a-fA-F0-9]{64})\s+\*?(\S+)",expected)
        if not m or m.group(2)!=filename:
            raise ValueError("PUBLISHER_OFFICIAL_CHECKSUM_BAD_FORMAT")
        zipped,zr=fetch_one_url(zip_url,ZIP_MAX,getter=getter)
        actual=hashlib.sha256(zipped).hexdigest()
        if actual!=m.group(1).lower():
            raise ValueError("PUBLISHER_OFFICIAL_CHECKSUM_SHA256_MISMATCH")
        filedir=Path(root)/symbol/"1m"
        filedir.mkdir(parents=True,exist_ok=True)
        zpath=filedir/filename
        cpath=filedir/(filename+".CHECKSUM")
        if zpath.exists() or cpath.exists():
            raise ValueError("MONSTER_SOURCE_PAIR_ALREADY_EXISTS_NO_REWRITE")
        zpath.write_bytes(zipped)
        cpath.write_bytes(checksum)
        # Reuse Stage166's fixed independently approved publisher validator;
        # full-day 1440 is required for admission, never silently pad.
        validation=admitted.validate_daily_zip(zpath,cpath,symbol,date.fromisoformat(day))
        result.update({
            "status":"VERIFIED_FULL_DAY_1440",
            "zip_sha256":validation["zip_sha256"],
            "publisher_checksum_sha256":hashlib.sha256(checksum).hexdigest(),
            "csv_closed_1m_rows":validation["closed_one_minute_rows"],
            "timestamp_unit":"MICROSECONDS",
            "zip_bytes":len(zipped),
            "original_publisher_checksum_valid":True,
            "zip_http_receipt":zr,
            "checksum_http_receipt":cr
        })
    except (ValueError,RuntimeError,OSError,UnicodeError,EOFError) as exc:
        result["status"]="SOURCE_REJECTED_OR_UNAVAILABLE"
        result["error"]=str(exc)
        # Never retain invalid ZIP/CHECKSUM as an admitted publisher pair.
        zpath,cpath=admitted.daily_paths(root,symbol,date.fromisoformat(day))
        zpath.unlink(missing_ok=True)
        cpath.unlink(missing_ok=True)
    return result


def collect(root,*,roster,days=FIXED_DAYS,max_workers=MAX_WORKERS,getter=None):
    if (not roster or len(roster)!=len(set(roster)) or
        any(not x.isalnum() or not x.endswith("USDT") for x in roster)
        or tuple(days)!=FIXED_DAYS or max_workers<1 or max_workers>MAX_WORKERS):
        raise ValueError("MONSTER_PUBLISHER_SOURCE_SCOPE_DRIFT")
    tasks=[(s,d) for s in sorted(roster) for d in FIXED_DAYS]
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        results=list(pool.map(lambda pair:one_pair(pair[0],pair[1],root,getter=getter),tasks))
    by_status={}
    for row in results:
        by_status[row["status"]]=by_status.get(row["status"],0)+1
    if sum(by_status.values())!=len(tasks):
        raise ValueError("MONSTER_PUBLISHER_ATTEMPT_COUNT_DRIFT")
    return {
        "schema":SCHEMA,
        "fixed_T0_original_http_zip_sha256":OFFICIAL_SHA,
        "source_scope":"ORIGINAL_SPOT_USDT_511_T0_TRADING",
        "original_roster_count":len(roster),
        "original_roster":sorted(roster),
        "days_utc":list(FIXED_DAYS),
        "attempts_total":len(tasks),
        "status_counts":by_status,
        "acquired_at_utc":utc(),
        "all_attempts":results,
        "no_failed_archive_can_count_as_no_WATCH_or_no_SETUP":True,
        "not_complete_seven_day_OOS":True,
        "market_listing_PIT_for_entire_window":"UNVERIFIED",
        "real_ask_bid_execution":"UNVERIFIED",
        "G4":"UNKNOWN","G6":"NO_GO",
        "NO_MERGE":True,"NO_DEPLOY":True,"NO_GMAIL":True,"NO_TRADE":True
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source-dir",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    p.add_argument("--workers",type=int,default=MAX_WORKERS)
    a=p.parse_args()
    if a.out.exists() or a.out.is_symlink():
        raise ValueError("MONSTER_PUBLISHER_RESULT_EXISTS_NO_REWRITE")
    roster=admitted.frozen_roster()
    if len(roster)!=511:
        raise ValueError("MONSTER_ORIGINAL_T0_511_DRIFT")
    report=collect(a.source_dir,roster=roster,max_workers=a.workers)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    with a.out.open("x",encoding="utf-8") as output:
        json.dump(report,output,sort_keys=True,indent=2,ensure_ascii=False)
        output.write("\n")
    print("MONSTER_ACTUAL_SPOT511_OCT16_17_PUBLISHER_SOURCE",
          json.dumps({"attempts":report["attempts_total"],
                      "statuses":report["status_counts"],
                      "original_T0_roster":report["original_roster_count"],
                      "G6":report["G6"]},sort_keys=True))


if __name__=="__main__":
    main()
