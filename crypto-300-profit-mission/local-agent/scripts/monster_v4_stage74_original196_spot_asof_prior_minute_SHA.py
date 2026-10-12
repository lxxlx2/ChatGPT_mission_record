#!/usr/bin/env python3
"""Monster Stage74: original all 196 frozen USD-M D0s checked against historical
same-name Binance SPOT *prior closed minute* publisher SHA-verified 1m bars.

This proves at most that Spot had recorded trades during [D0-1m,D0). NOT
a known executable ask, historic order book, Spot market universe, Alpha,
DEX, CA mapping, or actual profit. No model threshold changes or live actions.
"""
from __future__ import annotations

import argparse
import collections
import concurrent.futures
import csv
import hashlib
import io
import json
import re
import time
import urllib.error
import urllib.request
import zipfile
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]/"monster"
E=ROOT/"evidence"
PREREG=ROOT/"MONSTER_STAGE74_PREREG_196_ORIGINAL_D0_ASOF_BINANCE_SPOT_BUYABILITY_EVIDENCE_20261013.md"
OLD=E/"monster_stage66_full2700_originalV4_D0_and_P1v03_source_SHA.jsonl"
SOURCE_LOCK={
    PREREG.name:"0",
    OLD.name:"9eb19c22ae8d34d030ccabd7176c3cd4d2e2e3f8",
}
SCHEMA="MONSTER_STAGE74_ORIGINAL196_D0_SPOT_CLOSED_1M_SHA_EXECUTION_EVIDENCE_V1"
D=Decimal
ONE=60000
STATES=(
    "SPOT_PRIOR_MINUTE_TRADES_VERIFIED",
    "SPOT_PRIOR_MINUTE_BAR_ZERO_TRADES",
    "SPOT_ARCHIVE_SAME_DAY_NO_PRIOR_1M_BAR",
    "SPOT_DAILY_ARCHIVE_404_UNVERIFIED",
)
CACHE={}
GOOD="COMPLETE_REAL_USDM_1M_SHA_CAUSAL_V4"


def blob(path):
    raw=path.read_bytes()
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()


def utc_ms(value):
    t=datetime.fromisoformat(value.replace("Z","+00:00"))
    if t.utcoffset()!=timezone.utc.utcoffset(t) or t.second or t.microsecond:
        raise ValueError("STAGE74_NOT_AN_EXACT_UTC_MINUTE")
    return int(t.timestamp()*1000)


def source():
    for p in (PREREG,OLD):
        if blob(p)!=SOURCE_LOCK[p.name]:
            raise ValueError("STAGE74_FROZEN_UNIVERSE_OR_PROTOCOL_CHANGED "+p.name)
    src=[json.loads(x) for x in OLD.read_text(encoding="utf-8").splitlines() if x]
    if len(src)!=2700 or len({(x["date"],x["symbol"]) for x in src})!=2700:
        raise ValueError("STAGE74_ORIGINAL2700_NOT_LOCKED")
    watch=sorted((x for x in src if x["original_D0_first_UTC"] is not None),
                 key=lambda x:(x["date"],x["symbol"]))
    if len(watch)!=196:
        raise ValueError("STAGE74_ALL196_ORIGINAL_D0_CHANGED")
    by=collections.Counter(x["date"] for x in watch)
    if dict(by)!={"2025-03-30":44,"2025-06-30":49,"2025-11-27":103}:
        raise ValueError("STAGE74_OLD3_WINDOW_D0_GROUP_COUNTS_CHANGED")
    for row in watch:
        if row["minute_source_status"]!=GOOD or not row["original_D0_all_WATCH_UTC"] or (
            row["original_D0_all_WATCH_UTC"][0]!=row["original_D0_first_UTC"]
        ):
            raise ValueError("STAGE74_D0_SIGNAL_SOURCE_MISMATCH")
        if not (utc_ms(row["original_D0_first_UTC"])>=utc_ms(row["date"]+"T06:00:00Z")
                and utc_ms(row["original_D0_first_UTC"])<utc_ms(row["date"]+"T06:00:00Z")+7*86400000):
            raise ValueError("STAGE74_SIGNAL_OUTSIDE_ORIGINAL_SEVEN_DAY_WINDOW")
    return watch


def request_bytes(url,cap):
    req=urllib.request.Request(url,headers={"User-Agent":"Monster-Stage74-Spot-Publisher-SHA-Causal-Audit/1"})
    for n in range(3):
        try:
            with urllib.request.urlopen(req,timeout=32) as response:
                raw=response.read(cap+1)
            if not raw or len(raw)>cap:
                raise ValueError("STAGE74_SPOT_SOURCE_EMPTY_OR_TOO_LARGE")
            return raw
        except urllib.error.HTTPError as e:
            if e.code==404:
                raise FileNotFoundError("STAGE74_SPOT_DAILY_ZIP_404") from e
            if n==2:raise
        except (urllib.error.URLError,ConnectionError,TimeoutError,OSError):
            if n==2:raise
        time.sleep(1+n)
    raise RuntimeError("STAGE74_SOURCE_RETRY_EXHAUSTED")


def parse_spot_1m(symbol,day,zip_data,digest):
    if hashlib.sha256(zip_data).hexdigest()!=digest.lower():
        raise ValueError("STAGE74_SPOT_CHECKSUM_MISMATCH")
    member=f"{symbol}-1m-{day}.csv"
    with zipfile.ZipFile(io.BytesIO(zip_data)) as z:
        if z.namelist()!=[member] or z.getinfo(member).file_size>25_000_000:
            raise ValueError("STAGE74_SPOT_ZIP_CSV_MEMBER_OR_SIZE_MISMATCH")
        raw=z.read(member).decode("utf-8-sig")
    start=utc_ms(day+"T00:00:00Z")
    bars={}
    for i,line in enumerate(csv.reader(io.StringIO(raw))):
        if i==0 and line and line[0].strip().lower() in ("open_time","open time","opentime"):
            continue
        if len(line)<9 or not line[0].strip().isdigit():
            raise ValueError("STAGE74_BAD_SPOT_OFFICIAL_1M_ROW")
        micro=int(line[0])
        if micro<10**15 or micro%1000:
            raise ValueError("STAGE74_OFFICIAL_SPOT_2025_MICROSECOND_TIMESTAMP_REQUIRED")
        ms=micro//1000
        if ms%ONE or ms<start or ms>=start+86400000 or ms in bars:
            raise ValueError("STAGE74_SPOT_MINUTE_OUT_OF_DAY_DUPLICATE_OR_UNALIGNED")
        try:
            o,h,l,c,base,q=[D(line[k]) for k in (1,2,3,4,5,7)]
            trades=int(line[8])
        except (InvalidOperation,ValueError,IndexError) as e:
            raise ValueError("STAGE74_SPOT_OHLCV_INVALID_NUMBER") from e
        if any(not x.is_finite() for x in (o,h,l,c,base,q)):
            raise ValueError("STAGE74_NONFINITE_OHLCV")
        if (min(o,h,l,c)<=0 or h<max(o,c) or l>min(o,c) or
            h<l or min(base,q)<0 or trades<0):
            raise ValueError("STAGE74_SPOT_INVALID_OHLCV_TRADECOUNT")
        bars[ms]={"close":str(c),"quote":str(q),"base":str(base),"trades":trades}
    if not bars:
        raise ValueError("STAGE74_EMPTY_SPOT_DAILY_WITH_VALID_ZIP")
    return bars


def fetch_day(symbol,day,fetch=request_bytes):
    key=(symbol,day)
    if key in CACHE:return CACHE[key]
    name=f"{symbol}-1m-{day}.zip"
    address=f"https://data.binance.vision/data/spot/daily/klines/{symbol}/1m/{name}"
    try:
        zip_data=fetch(address,12_000_000)
    except FileNotFoundError as e:
        if "STAGE74_SPOT_DAILY_ZIP_404" not in str(e):
            raise
        CACHE[key]=(None,{"status":"SPOT_DAILY_ARCHIVE_404_UNVERIFIED",
                           "archive_path":address,
                           "publisher_zip_sha256":None,
                           "provenance":"NO_PUBLIC_ARCHIVE_AT_THIS_EXACT_PATH_NOT_HISTORICAL_DELIST_PROOF"})
        return CACHE[key]
    checksum=fetch(address+".CHECKSUM",2048).decode("utf-8","strict").strip().split()
    if not checksum or not re.fullmatch("[A-Fa-f0-9]{64}",checksum[0]):
        raise ValueError("STAGE74_INVALID_OR_MISSING_PUBLISHER_CHECKSUM")
    sha=checksum[0].lower()
    bars=parse_spot_1m(symbol,day,zip_data,sha)
    CACHE[key]=(bars,{"status":"OFFICIAL_SPOT_ONE_DAY_PUBLISHER_SHA_VERIFIED",
                     "archive_path":address,"publisher_zip_sha256":sha,
                     "number_of_actual_source_minutes":len(bars),
                     "provenance":"BINANCE_SPOT_ARCHIVE_SOURCE_NOT_ORDERBOOK_NOT_ASOF_ZIP_AVAILABLE"})
    return CACHE[key]


def classify(row,fetcher=fetch_day):
    t=row["original_D0_first_UTC"]
    signal=utc_ms(t)
    day=t[:10]
    prior=signal-ONE
    bars,proof=fetcher(row["symbol"],day)
    if bars is None:
        status="SPOT_DAILY_ARCHIVE_404_UNVERIFIED"
        bar=None
    else:
        bar=bars.get(prior)
        if bar is None:
            status="SPOT_ARCHIVE_SAME_DAY_NO_PRIOR_1M_BAR"
        elif bar["trades"]>0 and D(bar["quote"])>0 and D(bar["base"])>0:
            status="SPOT_PRIOR_MINUTE_TRADES_VERIFIED"
        else:
            status="SPOT_PRIOR_MINUTE_BAR_ZERO_TRADES"
    if status not in STATES:
        raise ValueError("STAGE74_UNKNOWN_STATE")
    return {
        "date":row["date"],"symbol":row["symbol"],
        "original_usdm_first_D0_UTC":t,
        "spot_exact_same_symbol":row["symbol"],
        "spot_day_UTC":day,
        "spot_only_completed_one_minute_UTC":datetime.fromtimestamp(prior/1000,timezone.utc).isoformat().replace("+00:00","Z"),
        "spot_historical_evidence_status":status,
        "spot_prior_1m_close_NOT_EXACT_TRADE_FILL":bar["close"] if bar else None,
        "spot_prior_1m_quote_volume_USDT":bar["quote"] if bar else None,
        "spot_prior_1m_base_volume":bar["base"] if bar else None,
        "spot_prior_1m_number_of_trades":bar["trades"] if bar else None,
        "spot_daily_source":proof,
        "historical_spot_execution_or_spread_verified":False,
        "historical_ALPHA_DEX_CA_buyability_verified":False,
        "exact_historical_listing_and_delisting_manifest_verified":False,
        "original_V4_strategy_unchanged":True,
        "NO_GMAIL_OR_AUTOTRADE":True,
        "ORDER_NOTIONAL_UNSPECIFIED":True,
    }


def group_stats(rows):
    cnt=collections.Counter(x["spot_historical_evidence_status"] for x in rows)
    for k in STATES:cnt.setdefault(k,0)
    return dict(sorted(cnt.items()))


def aggregate(files,out):
    src=source()
    old={(x["date"],x["symbol"]):x for x in src}
    collected=[]
    for shard in range(4):
        fn=files/f"monster_stage74_original196_shard{shard}.json"
        part=json.loads(fn.read_text(encoding="utf-8"))
        if len(part)!=49:
            raise ValueError("STAGE74_EXPECTED49_PER_FOUR_SHARDS")
        collected.extend(part)
    ids={(x["date"],x["symbol"]):x for x in collected}
    if len(collected)!=196 or len(ids)!=196 or set(ids)!=set(old):
        raise ValueError("STAGE74_ORIGINAL196_NOT_EXHAUSTIVELY_CHECKED")
    for key,row in ids.items():
        if row["original_usdm_first_D0_UTC"]!=old[key]["original_D0_first_UTC"]:
            raise ValueError("STAGE74_FIRST_D0_TIME_CHANGED")
        if row["spot_historical_evidence_status"] not in STATES:
            raise ValueError("STAGE74_INVALID_SPOT_EVIDENCE_STATUS")
        if row["spot_historical_evidence_status"]=="SPOT_PRIOR_MINUTE_TRADES_VERIFIED" and (
            row["spot_prior_1m_number_of_trades"]<=0 or
            D(row["spot_prior_1m_quote_volume_USDT"])<=0 or
            not row["spot_daily_source"]["publisher_zip_sha256"]
        ):
            raise ValueError("STAGE74_CLAIMED_SPOT_TRADE_NO_PROOF")
    counts={date:group_stats([x for x in collected if x["date"]==date])
            for date in ("2025-03-30","2025-06-30","2025-11-27")}
    result={
        "schema":SCHEMA,"original_2700_git_blob":SOURCE_LOCK[OLD.name],
        "preregistered_contract_git_blob":SOURCE_LOCK[PREREG.name],
        "all_frozen_original_D0_signal_count":196,
        "all_exact_original_D0_coin_dates_and_times_parity":True,
        "states_total":group_stats(collected),
        "states_by_original_window":counts,
        "source_date_SHAs":[{"date":x["date"],"symbol":x["symbol"],
            "spot_zip_sha256":x["spot_daily_source"]["publisher_zip_sha256"]}
                for x in sorted(collected,key=lambda x:(x["date"],x["symbol"]))],
        "what_counts_as_positive":"ONLY_EXACT_MATCHED_SPOT_USDT_PAIR_T_MINUS_ONE_MINUTE_KLINE_WITH_REAL_TRADES_AND_QUOTE",
        "not_a_full_market_or_all_Dex_Alpha_buyability_denominator":True,
        "orderbook_spread_slippage_and_realizable_net_PNL":"UNKNOWN",
        "other_AI_review_of_stage74":"NOT_DONE",
        "Monster":"NO_GO","P1":"REJECTED","P2":"REJECTED",
        "GMAIL":"OFF","AUTOTRADE":"NO_GO",
    }
    out.mkdir(parents=True,exist_ok=True)
    (out/"monster_stage74_original196_exact_asof_spot_prior_trades_source_SHA.jsonl").write_text(
        "".join(json.dumps(x,ensure_ascii=False,sort_keys=True)+"\n"
                for x in sorted(collected,key=lambda x:(x["date"],x["symbol"]))),encoding="utf-8")
    (out/"monster_stage74_original196_spot_trading_source_summary.json").write_text(
        json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print("STAGE74_ORIGINAL196_HISTORIC_SPOT_1M_EVIDENCE_GLOBAL "+
          json.dumps({"all":196,"totals":result["states_total"],"by_date":counts},sort_keys=True))


def selftest():
    day="2025-06-30";name="HFTUSDT"
    start=utc_ms(day+"T00:00:00Z")
    def zipped(lines):
        with io.BytesIO() as blobfile:
            with zipfile.ZipFile(blobfile,"w",compression=zipfile.ZIP_DEFLATED) as z:
                z.writestr(f"{name}-1m-{day}.csv","\n".join(lines)+"\n")
            return blobfile.getvalue()
    def line(i,trades=5,q=100):
        t=(start+i*ONE)*1000
        return f"{t},1,2,0.5,1,100,{t+59999999},{q},{trades},5,10,0"
    raw=zipped([line(0),line(1),line(2)])
    digest=hashlib.sha256(raw).hexdigest()
    bars=parse_spot_1m(name,day,raw,digest)
    assert len(bars)==3
    row={"date":day,"symbol":name,"original_D0_first_UTC":day+"T00:02:00Z"}
    proof={"publisher_zip_sha256":digest}
    got=classify(row,lambda symbol,dd:(bars,proof))
    assert got["spot_historical_evidence_status"]=="SPOT_PRIOR_MINUTE_TRADES_VERIFIED" and got["spot_prior_1m_close_NOT_EXACT_TRADE_FILL"]=="1"
    # Mutate future bar without touching t-1: classification and all evidence
    # from the one-minute predecessor must remain strictly identical.
    later=dict(bars);later[start+2*ONE]=dict(bars[start+2*ONE],quote="999999999")
    assert classify(row,lambda symbol,dd:(later,proof))==got
    missing=dict(bars);del missing[start+ONE]
    assert classify(row,lambda symbol,dd:(missing,proof))["spot_historical_evidence_status"]=="SPOT_ARCHIVE_SAME_DAY_NO_PRIOR_1M_BAR"
    zero=dict(bars);zero[start+ONE]=dict(bars[start+ONE],trades=0,quote="0")
    assert classify(row,lambda symbol,dd:(zero,proof))["spot_historical_evidence_status"]=="SPOT_PRIOR_MINUTE_BAR_ZERO_TRADES"
    assert classify(row,lambda symbol,dd:(None,{"status":"SPOT_DAILY_ARCHIVE_404_UNVERIFIED",
                                                   "publisher_zip_sha256":None}))["spot_historical_evidence_status"]=="SPOT_DAILY_ARCHIVE_404_UNVERIFIED"
    try:parse_spot_1m(name,day,raw,"f"*64)
    except ValueError as e:assert "CHECKSUM_MISMATCH" in str(e)
    else:raise AssertionError("SHA_CHECKSUM_ACCEPTED_WRONG")
    try:parse_spot_1m(name,day,zipped([line(0),line(0)]),hashlib.sha256(zipped([line(0),line(0)])).hexdigest())
    except ValueError as e:assert "DUPLICATE" in str(e)
    else:raise AssertionError("DUPLICATE_MINUTE_ACCEPTED")
    try:parse_spot_1m(name,day,zipped([line(0).replace(str(start*1000),str(start),1)]),hashlib.sha256(zipped([line(0).replace(str(start*1000),str(start),1)])).hexdigest())
    except ValueError as e:assert "MICROSECOND" in str(e)
    else:raise AssertionError("MILLISECOND_ACCEPTED_AS_MICROSECOND")
    print("STAGE74_SPOT_SHA_MICROSECOND_NO_FUTURE_LEAK_SAFE_NO_ARCHIVE_FAIL_CLOSED_TEST_PASS")


def run(pilot,shard,workers,out):
    original=source()
    if pilot:
        wanted=(("2025-06-30","HFTUSDT"),("2025-06-30","HUSDT"),
                ("2025-11-27","PIPPINUSDT"),("2025-11-27","TANSSIUSDT"),
                ("2025-11-27","TRADOORUSDT"),("2025-03-30","ACTUSDT"))
        d={(x["date"],x["symbol"]):x for x in original}
        group=[d[k] for k in wanted]
    else:
        if shard not in range(4):raise ValueError("STAGE74_SHARD_NOT_0_1_2_3")
        group=[x for i,x in enumerate(original) if i%4==shard]
        if len(group)!=49:raise ValueError("STAGE74_EACH_SHARD_MUST_HAVE49_D0")
    data=[];errors=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futures={pool.submit(classify,row):row for row in group}
        for f in concurrent.futures.as_completed(futures):
            row=futures[f]
            try:data.append(f.result())
            except Exception as e:errors.append({"symbol":row["symbol"],"date":row["date"],
                                                  "error":str(e)[:220],"type":type(e).__name__})
    if errors or len(data)!=len(group):
        raise RuntimeError("STAGE74_SPOT_CANNOT_CLAIM_SOURCE_AVAILABLE "+json.dumps(errors[:15]))
    data.sort(key=lambda x:(x["date"],x["symbol"]))
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(data,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print("STAGE74_SOURCE_SHA_SPOT_HISTORIC_SIGNAL "+
          json.dumps({"pilot":pilot,"shard":shard,"sample_size":len(data),
                      "states":group_stats(data)},sort_keys=True))
    return data


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--selftest",action="store_true")
    p.add_argument("--pilot",action="store_true")
    p.add_argument("--shard",type=int)
    p.add_argument("--workers",type=int,default=4)
    p.add_argument("--out",type=Path)
    p.add_argument("--aggregate-dir",type=Path)
    a=p.parse_args()
    if a.selftest:selftest();return
    if a.out is None:p.error("--out is required")
    if a.aggregate_dir:
        aggregate(a.aggregate_dir,a.out)
    else:
        run(a.pilot,a.shard,a.workers,a.out)


if __name__=="__main__":
    main()
