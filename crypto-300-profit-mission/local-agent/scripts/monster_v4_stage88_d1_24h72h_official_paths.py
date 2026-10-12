#!/usr/bin/env python3
"""Monster Stage88: frozen complete305 D1 post-alert gross PRICE paths, no trade execution."""
from __future__ import annotations
import argparse
import collections
import concurrent.futures
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import json
from pathlib import Path

try:
    import monster_v4_stage38_usdm_original_v4_1m_pilot as publisher
    from monster_v4_stage80_dual_entry_core import sha_blob, utc_ms, decimal
except ImportError:
    from scripts import monster_v4_stage38_usdm_original_v4_1m_pilot as publisher
    from scripts.monster_v4_stage80_dual_entry_core import sha_blob, utc_ms, decimal

E=Path(__file__).resolve().parents[2]/"monster/evidence"
SOURCE=E/"monster_stage85_all305_official_D1_asof_features.jsonl"
SOURCE83=E/"monster_stage83_all519_source_and_D1_result.jsonl"
PIN85="622299fec16400e189cb8fa668ecbc8bc31ec630"
PIN83="c76b3a137c8dbe56feed3a79a63adcc0752f5e2e"
DATES=("2025-01-30","2025-06-02","2025-08-01","2025-10-02","2026-06-21","2026-07-28")
SCHEMA="MONSTER_STAGE88_D1_GROSS_NEXT1MIN_OPEN_24H72H_REAL1M_V1"
MIN=60_000
H24=1440
H72=4320
COMPLETE="COMPLETE_OFFICIAL_1M_SHA_PRICE_ONLY_PROXY"
CENSORED="CENSORED_DAILY_SOURCE_UNKNOWN"
NO_BAR="ENTRY_BAR_HAS_NO_REAL_TRADES_PROXY_UNSUPPORTED"


def frozen():
    old85=SOURCE.read_bytes()
    old83=SOURCE83.read_bytes()
    if sha_blob(old85)!=PIN85 or sha_blob(old83)!=PIN83:
        raise ValueError("STAGE88_FROZEN_SOURCE_BLOB_CHANGED")
    x=[json.loads(s) for s in old85.decode().splitlines() if s.strip()]
    y=[json.loads(s) for s in old83.decode().splitlines() if s.strip()]
    if len(x)!=305 or len(y)!=519:
        raise ValueError("STAGE88_ORIGINAL_POPULATION_DRIFT")
    index={(r["date"],r["symbol"]):r for r in y}
    if len(index)!=519 or len({(r["date"],r["symbol"]) for r in x})!=305:
        raise ValueError("STAGE88_ORIGINAL_IDENTITY_DRIFT")
    if sum(r["D1_PATH"]=="DIRECT_AT_FIRST_D0" for r in x)!=164 \
            or sum(r["D1_PATH"]=="REIGNITION_AFTER_D0" for r in x)!=141:
        raise ValueError("STAGE88_D1_PATH_COHORT_DRIFT")
    for row in x:
        old=index[(row["date"],row["symbol"])]
        if (row["D1_FIRST_UTC"]!=old["D1_FIRST_UTC"]
            or row["D0_FIRST_UTC"]!=old["D0_FIRST_UTC"]
            or old["source_status"]!="COMPLETE_OFFICIAL_PREFIX_SHA_VERIFIED_3M_48H"
            or row["source_status"]!="COMPLETE_OFFICIAL_BINANCE_SHA_ASOF_D1"):
            raise ValueError("STAGE88_OLD_D0_D1_SOURCE_TIME_DRIFT")
    return x,index


def shard_rows(date:int|str,shard:int,source=None):
    if date not in DATES or shard not in range(4):
        raise ValueError("STAGE88_INVALID_DATE_OR_SHARD")
    if source is None:source=frozen()[0]
    subset=sorted((r for r in source if r["date"]==date),key=lambda x:x["symbol"])
    if not subset:raise ValueError("STAGE88_EMPTY_DATE")
    return [x for i,x in enumerate(subset) if i%4==shard]


def days_for(t:int):
    # t = exact D1 UTC minute. Exit bar starts at t + 4320m, exactly 72h from
    # synthetic delayed entry t+1m after 4320 observations.
    begin=datetime.fromtimestamp(t/1000,timezone.utc).date()
    final=datetime.fromtimestamp((t+H72*MIN)/1000,timezone.utc).date()
    return [begin+timedelta(days=i) for i in range((final-begin).days+1)]


def pct(a:Decimal,b:Decimal)->str:
    return str((a/b-1)*100)


def score_path(records:dict[int,tuple],t:int,minutes:int,entry:Decimal|None):
    start=t+MIN
    last=t+minutes*MIN
    if entry is None:
        return {"status":NO_BAR}
    needed=[records.get(t+i*MIN) for i in range(1,minutes+1)]
    if any(x is None for x in needed):
        return {"status":CENSORED,"missing_first_minute_UTC":publisher.stamp(
            start+next(i for i,x in enumerate(needed) if x is None)*MIN)}
    if len(needed)!=minutes or needed[-1][0]!=last:
        raise ValueError("STAGE88_NOT_24_OR_72_FULL_MINUTE_HORIZON")
    high=max(x[2] for x in needed)
    low=min(x[3] for x in needed)
    exit_price=needed[-1][4]
    peak=entry
    worst=Decimal(0)
    for row in needed:
        peak=max(peak,row[4])
        dd=(row[4]/peak-1)*100
        worst=min(worst,dd)
    max_idx=next(i for i,x in enumerate(needed) if x[2]==high)
    min_idx=next(i for i,x in enumerate(needed) if x[3]==low)
    return {
      "status":COMPLETE,
      "entry_UTC":publisher.stamp(start),
      "exit_last_bar_open_UTC":publisher.stamp(last),
      "exit_bar_closes_UTC":publisher.stamp(last+MIN),
      "minutes":minutes,
      "exit_close":str(exit_price),
      "fixed_exit_gross_return_pct":pct(exit_price,entry),
      "max_favorable_HIGH_pct_not_realized":pct(high,entry),
      "max_adverse_LOW_pct_not_realized":pct(low,entry),
      "max_close_to_close_drawdown_pct":str(worst),
      "high_minute_UTC":publisher.stamp(needed[max_idx][0]),
      "low_minute_UTC":publisher.stamp(needed[min_idx][0]),
      "risk_is_1m_OHLC_price_only":True
    }


def replay(row:dict, previous:dict,*,reader=publisher.verified_1m_day):
    if row["D1_FIRST_UTC"]!=previous["D1_FIRST_UTC"]:
        raise ValueError("STAGE88_FIRST_D1_CHANGED")
    t=utc_ms(row["D1_FIRST_UTC"])
    actual={p["date"]:p["zip_sha256"] for p in
            row["verified_source_publisher_SHA"]+
            previous["source_day_sha256_receipts"]}
    for a in row["verified_source_publisher_SHA"]+previous["source_day_sha256_receipts"]:
        if actual[a["date"]]!=a["zip_sha256"] or not a["verified_official_publisher_SHA256"]:
            raise ValueError("STAGE88_INCONSISTENT_PREVIOUS_SOURCE_RECEIPTS")
    output={"date":row["date"],"symbol":row["symbol"],
        "venue":"BINANCE_USDM_HISTORIC_MIXED",
        "D0_FIRST_UTC":row["D0_FIRST_UTC"],"D1_FIRST_UTC":row["D1_FIRST_UTC"],
        "D1_PATH":row["D1_PATH"],"identity":row["identity"],
        "historical_anchor_2x_EVALUATION_ONLY":
            bool(previous["historical_anchor_GT2"]),
        "source_original_stage85_git_blob":PIN85,
        "source_days_verified":[],
        "official_source_days_missing":[],
        "order_notional":"UNSPECIFIED","real_execution":"UNKNOWN",
        "no_buy_no_email":True}
    bars={}
    for d in days_for(t):
        try:
            fetched,receipt=reader(row["symbol"],d)
        except FileNotFoundError:
            output["official_source_days_missing"].append(d.isoformat())
            continue
        if not receipt["verified_official_publisher_SHA256"] or len(fetched)!=1440:
            raise ValueError("STAGE88_NO_OFFICIAL_PUBLISHER_SHA_OR_DAY_INCOMPLETE")
        if receipt["date"]!=d.isoformat():
            raise ValueError("STAGE88_WRONG_DAY_RECEIPT")
        previous_sha=actual.get(receipt["date"])
        if previous_sha is not None and previous_sha!=receipt["zip_sha256"]:
            raise ValueError("STAGE88_REPEATED_DAILY_OFFICIAL_SHA_DIFFERS")
        output["source_days_verified"].append(receipt)
        for kline in fetched:
            stamp=kline[0]
            if stamp in bars:raise ValueError("STAGE88_DUPLICATE_TIMESTAMPS")
            bars[stamp]=kline
    signal_minute=bars.get(t)
    delayed_minute=bars.get(t+MIN)
    if delayed_minute is None:
        entry=None
        entry_status=CENSORED
    elif delayed_minute[6]<=0 or delayed_minute[5]<=0:
        entry=None
        entry_status=NO_BAR
    else:
        entry=delayed_minute[1]
        entry_status="BAR_HAS_TRADES_PRICE_ONLY"
    output["entry_delayed_1m"]= {
        "minute_UTC":publisher.stamp(t+MIN),
        "entry_open":str(entry) if entry is not None else None,
        "status":entry_status,
        "bar_quote_volume":str(delayed_minute[5]) if delayed_minute else None,
        "bar_trade_count":delayed_minute[6] if delayed_minute else None}
    if signal_minute is not None:
        output["optimistic_signal_bar_open_no_delay"]=str(signal_minute[1])
    else:output["optimistic_signal_bar_open_no_delay"]=None
    output["h24"]=score_path(bars,t,H24,entry)
    output["h72"]=score_path(bars,t,H72,entry)
    if entry is None and entry_status==CENSORED and (output["h24"]["status"]!=CENSORED or output["h72"]["status"]!=CENSORED):
        raise ValueError("STAGE88_UNKNOWN_ENTRY_MUST_CENSOR")
    return output


def selftest():
    x,index=frozen()
    union=[r for date in DATES for sh in range(4) for r in shard_rows(date,sh,x)]
    assert len(union)==305
    assert {(r["date"],r["symbol"]) for r in union}=={(r["date"],r["symbol"]) for r in x}
    t=utc_ms("2025-01-30T06:00:00Z")
    assert len(days_for(t))==4
    d=Decimal
    records={t+i*MIN:(t+i*MIN,d("100"),d("110"),d("95"),
                       d("105"),d("100000"),150)
             for i in range(1,H72+1)}
    p24=score_path(records,t,H24,d("100"))
    p72=score_path(records,t,H72,d("100"))
    assert p24["status"]==COMPLETE and p72["status"]==COMPLETE
    assert p24["minutes"]==1440 and p72["minutes"]==4320
    assert p24["fixed_exit_gross_return_pct"]=="5.00"
    records.pop(t+1800*MIN)
    assert score_path(records,t,H24,d("100"))["status"]==COMPLETE
    assert score_path(records,t,H72,d("100"))["status"]==CENSORED
    assert score_path(records,t,H24,None)["status"]==NO_BAR
    print("STAGE88_ALL305_FROZEN_SOURCE_HORIZON_CAUSAL_MINUTE_SELFTEST_PASS")


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--selftest",action="store_true")
    parser.add_argument("--date")
    parser.add_argument("--shard",type=int)
    parser.add_argument("--workers",type=int,default=3)
    parser.add_argument("--out",type=Path)
    args=parser.parse_args()
    if args.selftest:selftest();return
    if not args.date or args.shard is None or not args.out:
        parser.error("--date --shard --out required")
    if args.workers not in range(1,5):
        raise ValueError("STAGE88_MAX_FOUR_WORKERS")
    rows,index=frozen()
    selected=shard_rows(args.date,args.shard,rows)
    out=[];errors=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        jobs={pool.submit(replay,row,index[(row["date"],row["symbol"])]):row for row in selected}
        for job in concurrent.futures.as_completed(jobs):
            row=jobs[job]
            try:
                response=job.result()
                out.append(response)
                print("STAGE88_CASE "+json.dumps({
                    "date":response["date"],"symbol":response["symbol"],
                    "h24":response["h24"]["status"],"h72":response["h72"]["status"],
                },sort_keys=True),flush=True)
            except Exception as exc:
                errors.append({"date":row["date"],"symbol":row["symbol"],
                               "reason":type(exc).__name__+":"+str(exc)[:240]})
    if errors or len(out)!=len(selected):
        raise RuntimeError("STAGE88_SOURCE_PRICE_PATH_FAIL_CLOSED "+json.dumps(errors[:30]))
    response={
       "schema":SCHEMA,"date":args.date,"shard":args.shard,
       "expected":len(selected),"rows":sorted(out,key=lambda x:x["symbol"]),
       "valid24":sum(x["h24"]["status"]==COMPLETE for x in out),
       "valid72":sum(x["h72"]["status"]==COMPLETE for x in out),
       "gross_price_path_only":True,"oos":"NOT_DONE",
       "real_executable_net_pnl":"UNKNOWN","deployment":"NO_GO",
       "gmail":"OFF","autotrade":"NO_GO","frank":"UNCHANGED"}
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(response,sort_keys=True,ensure_ascii=False,indent=2)+"\n")
    print("STAGE88_SHARD "+json.dumps({
       k:response[k] for k in ("date","shard","expected","valid24","valid72")},sort_keys=True))


if __name__=="__main__":
    main()
