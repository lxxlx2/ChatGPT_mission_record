#!/usr/bin/env python3
"""Stage130 research-only, frozen31 publisher-SHA new-listing one-minute replay.

No live monitoring, automatic trade, real execution, mail or daemon.
"""
from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import io
import json
from pathlib import Path
import re
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen
import zipfile

import monster_v4_stage129_new_listings_hourly_recovery as prev
from monster_v4_stage105_capture_universe_core import valid_exact_venue_symbol

MINUTE=60000
HOUR=60*MINUTE
MAX_ZIP=16_000_000
MAX_CSV=30_000_000
SOURCE_BASE="https://data.binance.vision/data/futures/um/daily/klines"
SCHEMA="MONSTER_STAGE130_FROZEN31_PUBLISHER_SHA_NEW_LISTING_FIRST_1M_V1"
THRESHOLDS=((3,Decimal("0.05")),(15,Decimal("0.08")),(60,Decimal("0.15")))
QUOTE_CONTEXT=Decimal("100000")
FROZEN31=31
E=Path(__file__).resolve().parents[2]/"monster"/"evidence"


def utc(ms):
    return datetime.fromtimestamp(ms/1000,timezone.utc).isoformat().replace("+00:00","Z")


def ms(iso):
    if not isinstance(iso,str) or not iso.endswith("Z"):
        raise ValueError("STAGE130_REQUIRE_UTC_TIME")
    return int(datetime.fromisoformat(iso.replace("Z","+00:00")).timestamp()*1000)


def numeric(v):
    try:
        n=Decimal(str(v))
    except (InvalidOperation,TypeError,ValueError):
        raise ValueError("STAGE130_INVALID_NUMBER") from None
    if not n.is_finite():
        raise ValueError("STAGE130_NONFINITE_NUMBER")
    return n


def exact_symbol(symbol):
    # Reuse established source Unicode/no-normalization contract.
    return valid_exact_venue_symbol(symbol) and symbol.endswith("USDT")


def source_url(symbol, day):
    if not exact_symbol(symbol):
        raise ValueError("STAGE130_EXACT_VENUE_SYMBOL_INVALID")
    encoded=quote(symbol,safe="")
    return f"{SOURCE_BASE}/{encoded}/1m/{encoded}-1m-{day}.zip"


def http_get(url, max_bytes, attempts=2):
    last=None
    for i in range(attempts):
        try:
            with urlopen(Request(url,headers={"User-Agent":"Monster-Stage130-PublisherVerified-HistoricalResearch/1.0"}),timeout=24) as h:
                body=h.read(max_bytes+1)
            if not body or len(body)>max_bytes:
                raise ValueError("STAGE130_EMPTY_OR_OVERSIZED_PUBLISHER_OBJECT")
            return body
        except HTTPError as exc:
            if exc.code==404:
                raise FileNotFoundError("STAGE130_PUBLISHER_HISTORICAL_1M_404 "+url) from exc
            last=exc
        except (URLError,TimeoutError,OSError) as exc:
            last=exc
        if i+1<attempts:
            time.sleep(.8*(i+1))
    raise RuntimeError("STAGE130_SOURCE_FETCH_UNAVAILABLE "+type(last).__name__)


def verified_day(symbol, day, fetch=http_get, save_dir=None):
    url=source_url(symbol,day)
    raw=fetch(url,MAX_ZIP)
    checksum=fetch(url+".CHECKSUM",2048)
    digest=hashlib.sha256(raw).hexdigest()
    match=re.search(rb"(?<![0-9A-Fa-f])([0-9a-fA-F]{64})(?![0-9A-Fa-f])",checksum)
    if not match or match.group(1).decode("ascii").lower()!=digest:
        raise ValueError("STAGE130_PUBLISHER_CHECKSUM_MISMATCH")
    member=f"{symbol}-1m-{day}.csv"
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        if z.namelist()!=[member] or z.getinfo(member).file_size>MAX_CSV:
            raise ValueError("STAGE130_WRONG_PUBLISHER_CSV_MEMBER")
        table=z.read(member)
    arr=[]
    for n,row in enumerate(csv.reader(io.StringIO(table.decode("utf-8-sig")))):
        if n==0 and row and row[0].lower().strip() in ("open_time","open time","opentime"):
            continue
        if len(row)<9:
            raise ValueError("STAGE130_PUBLISHER_INVALID_CSV_COLUMN_COUNT")
        raw_t=row[0]
        if not raw_t.isdigit():
            raise ValueError("STAGE130_PUBLISHER_INVALID_MINUTE_TIMESTAMP")
        ts=int(raw_t)
        if ts>=10**15:
            if ts%1000:
                raise ValueError("STAGE130_NON_EXACT_MICROSECONDS")
            ts//=1000
        if ts<10**12 or ts%MINUTE:
            raise ValueError("STAGE130_INVALID_MINUTE_ALIGNMENT")
        o,h,l,c,quote=(numeric(row[k]) for k in (1,2,3,4,7))
        trades=int(row[8])
        if min(o,h,l,c)<=0 or l>min(o,c) or h<max(o,c) or h<l or quote<0 or trades<0:
            raise ValueError("STAGE130_INVALID_SOURCE_OHLC_OR_VOLUME")
        arr.append((ts,o,h,l,c,quote,trades))
    if not arr or len(arr)>1440:
        raise ValueError("STAGE130_INVALID_DAY_COUNT")
    first=ms(day+"T00:00:00Z")
    if any(r[0]<first or r[0]>=first+86400000 for r in arr):
        raise ValueError("STAGE130_WRONG_UTC_DAY")
    if any(arr[i][0]-arr[i-1][0]!=MINUTE for i in range(1,len(arr))):
        raise ValueError("STAGE130_GAPPED_OR_UNSORTED_SOURCE_DAY")
    if save_dir is not None:
        p=Path(save_dir)/symbol/(day+".zip")
        p.parent.mkdir(parents=True,exist_ok=True)
        p.write_bytes(raw)
        (p.parent/(day+".zip.CHECKSUM")).write_bytes(checksum)
    return arr,{"day":day,"zip_sha256":digest,"publisher_sha256_verified":True,
                "url":url,"bars":len(arr),"first_bar_utc":utc(arr[0][0]),
                "last_bar_utc":utc(arr[-1][0]),"source":"BINANCE_DATA_VISION_ORIGINAL_ZIP_AND_PUBLISHER_CHECKSUM"}


def momentums(bars):
    """No future high, each decision uses only already-closed one-minute bars."""
    prefix=[Decimal(0)]
    for b in bars:
        prefix.append(prefix[-1]+b[5])
    decisions=[]
    for i in range(len(bars)):
        t=bars[i][0]+MINUTE
        if t%(3*MINUTE)!=0:
            continue
        if prefix[i+1] < QUOTE_CONTEXT:
            continue
        active=[]
        for count,threshold in THRESHOLDS:
            if i<count:
                continue
            old=bars[i-count][4]
            if bars[i][4]/old-1>=threshold:
                active.append(f"{count}m")
        if active:
            decisions.append({"utc":utc(t),"event_epoch_ms":t,"reason":active,
                              "partial_since_listing_quote_USDT":str(prefix[i+1]),
                              "not_real_binance_24h_ticker":True})
    return decisions


def score_case(case, hourly, fetch=http_get,save_dir=None):
    symbol=case["symbol"]
    anchor=case["date"]
    start,end=prev.window(anchor)
    stage129_first=ms(hourly["first_1h_open_utc"])
    first_day=datetime.fromtimestamp(stage129_first/1000,timezone.utc).date()
    last_day=datetime.fromtimestamp((end-1)/1000,timezone.utc).date()
    today=first_day
    days=[]
    bars=[]
    records=[]
    while today<=last_day:
        day=today.isoformat()
        rows,receipt=verified_day(symbol,day,fetch=fetch,save_dir=save_dir)
        bars.extend(rows)
        records.append(receipt)
        today+=timedelta(days=1)
    bars=[r for r in bars if start<=r[0]<end]
    if not bars or bars[0][0]//HOUR*HOUR!=stage129_first or bars[-1][0]!=end-MINUTE:
        raise ValueError("STAGE130_HISTORICAL_INCOMPLETE_LISTING_WINDOW")
    if any(bars[i][0]-bars[i-1][0]!=MINUTE for i in range(1,len(bars))):
        raise ValueError("STAGE130_HISTORICAL_1M_GAP")
    if bars[0][1]!=numeric(hourly["first_open_USDT"]):
        raise ValueError("STAGE130_HOURLY_FIRST_OPEN_VS_1M_PUBLISHER_CONFLICT")
    baseline=bars[0][1]
    cross=next((row[0] for row in bars if row[2]>=baseline*2),None)
    maxhigh=max(r[2] for r in bars)
    signals=momentums(bars)
    first=signals[0]["event_epoch_ms"] if signals else None
    first_obs=bars[0][0]+MINUTE
    return {
        "anchor":anchor,"symbol":symbol,
        "status":"COMPLETE_VERIFIED_PUBLISHER_1M_FROM_LISTING_FIRST_MINUTE_TO_WINDOW_END",
        "frozen_listing_first_observed_1m_open_utc":utc(bars[0][0]),
        "first_minute_close_observable_at_utc":utc(first_obs),
        "minute_rows":len(bars),"verified_publisher_day_count":len(records),
        "official_publisher_SHA256_daily_receipts":records,
        "first_1m_open":str(baseline),
        "max_1m_high":str(maxhigh),"gross_max_1m_high_over_initial_1m_open":str(maxhigh/baseline),
        "first_2x_high_minute_utc_evaluation_only":utc(cross) if cross is not None else None,
        "gross_first1m_2x_case_evaluation_only":cross is not None,
        "first_observed_close_before_2x_5m":first_obs+5*MINUTE<=cross if cross is not None else None,
        "new_listing_research_momentum_first_utc":utc(first) if first is not None else None,
        "new_listing_research_momentum_first_reasons":signals[0]["reason"] if signals else [],
        "momentum_research_early_5m_before_2x":first+5*MINUTE<=cross if (first is not None and cross is not None) else (False if cross is not None else None),
        "all_3m_UTC_aligned_momentum_research_events_not_sent":signals,
        "partial_listing_not_real_binance_ticker":True,
        "contemporaneous_crypto_issuer_verified":False,
        "actual_bid_ask_fills_fee_net": "UNKNOWN",
        "future_labels_separate_from_research_features":True,
    }


def run(fetch=http_get, save_dir=None,workers=4):
    baseline=prev.run()
    originals=baseline["all_source_cohort_rows"]
    if len(originals)!=FROZEN31:
        raise ValueError("STAGE130_ORIGINAL_FROZEN31_DRIFT")
    chosen=sorted(originals,key=lambda x:(x["date"],x["symbol"]))
    if any(r["analysis_status"]!="COMPLETE_FROM_FIRST_OBSERVED_1H_TO_END_PRICE_PROXY_ONLY" for r in chosen):
        raise ValueError("STAGE130_BASE_HOURLY_SOURCE_NOT_COMPLETE")
    result=[]
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures={pool.submit(score_case,r,r,fetch,save_dir):r for r in chosen}
        for done in as_completed(futures):
            v=futures[done]
            try:
                result.append(done.result())
            except Exception as exc:
                result.append({"anchor":v["date"],"symbol":v["symbol"],"status":"CENSORED_1M_SOURCE_NOT_A_NEGATIVE",
                               "source_error_type":type(exc).__name__,"source_error":str(exc)[:300],
                               "actual_bid_ask_fills_fee_net":"UNKNOWN"})
    result.sort(key=lambda v:(v["anchor"],v["symbol"]))
    if len(result)!=FROZEN31:
        raise ValueError("STAGE130_SILENTLY_LOST_COHORT_ROW")
    good=[r for r in result if r["status"].startswith("COMPLETE")]
    winners=[r for r in good if r["gross_first1m_2x_case_evaluation_only"]]
    firstmom=[r for r in good if r["new_listing_research_momentum_first_utc"]]
    eligible_early=[r for r in winners if r["momentum_research_early_5m_before_2x"]]
    return {
        "schema":SCHEMA,"stage129_fixed31_1h_reference":"ORIGINAL_EXPOSED_HISTORICAL",
        "source":"BINANCE_OFFICIAL_DATA_VISION_ARCHIVE_ZIPS_AND_PUBLISHER_SHA256",
        "source_is_archived_historical_NOT_LIVE":True,
        "frozen31":31,"source_complete":len(good),"source_censored":31-len(good),
        "source_status_counts":dict(sorted(Counter(r["status"] for r in result).items())),
        "listing_first1m_relative_gross2x_cases":len(winners),
        "listing_first1m_relative_gross5x_cases":sum(numeric(r["gross_max_1m_high_over_initial_1m_open"])>=5 for r in good),
        "listing_first1m_relative_gross10x_cases":sum(numeric(r["gross_max_1m_high_over_initial_1m_open"])>=10 for r in good),
        "research_momentum_first_triggers":len(firstmom),
        "research_momentum_early5_of_source_complete_2x":len(eligible_early),
        "research_momentum_2x_positive_symbol_dates":[[r["anchor"],r["symbol"]] for r in winners],
        "research_momentum_missed_2x_symbol_dates":[[r["anchor"],r["symbol"]] for r in winners if not r["momentum_research_early_5m_before_2x"]],
        "original_Stage93_gross51_discovery_denominator_unchanged":True,
        "old_stage118_model":"REJECTED",
        "old_stage127_model":"REJECTED",
        "G0":"PARTIAL", "G1_true_new_OOS":"NOT_SCORABLE", "G4_actual_executable_net":"UNKNOWN",
        "other_AI_independent_review":"NOT_DONE", "monster_deployment":"NO_GO",
        "frank":"UNCHANGED","gmail":"OFF",
        "full31_source_results":result,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--save-source",type=Path)
    p.add_argument("--workers",type=int,default=4)
    a=p.parse_args()
    if not 1<=a.workers<=4:
        raise ValueError("STAGE130_NO_UNBOUNDED_NETWORK_WORKERS")
    z=run(save_dir=a.save_source,workers=a.workers)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(z,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in z.items() if k!="full31_source_results"},ensure_ascii=False,sort_keys=True))


if __name__=="__main__":
    main()
