#!/usr/bin/env python3
"""Stage39 full 900 USD-M archived-symbol × six-day unchanged V4 census.

Unlike enriched Stage38 52-winners + 120 negative controls, this studies
EVERY 900 symbol in all six original date windows, retaining hourly and
minute source censoring and a truly market-wide ordinary-WATCH denominator.
Original V4 D0/D1 code remains locked; 5x/10x only scored AFTER original scan.
No BTC strategy, holding, PnL, new thresholds, deploy, Gmail or Frank changes.
"""
import argparse,collections,concurrent.futures,csv,hashlib,json,sys
from datetime import datetime,timezone
from decimal import Decimal
from pathlib import Path

try:
    import monster_v4_stage38_usdm_original_v4_1m_pilot as original
except ImportError:
    from scripts import monster_v4_stage38_usdm_original_v4_1m_pilot as original

EVIDENCE=Path(__file__).resolve().parents[2]/"monster"/"evidence"
FROZEN=EVIDENCE/"monster_stage39_usdm_full900_sixdate_1m_original_v4_prereg_20261012.json"
STAGE37=EVIDENCE/"monster_stage37_sixdate_all5400_usdm_source_and_GT.csv"
DAYS=("2025-01-19","2025-04-19","2025-07-19","2025-10-19","2026-04-19","2026-07-19")
SCHEMA="MONSTER_STAGE39_USDM_900x6_ORIGINAL_V4_FULL168H_SHA_GROSS_2x5x10x_V1"
COMPLETE="COMPLETE_REAL_USDM_1M_SHA_CAUSAL_V4"
CONFLICT="CENSORED_PUBLISHER_VERIFIED_1H_VS_1M_PRICE_CONFLICT"

def lock():
    p=json.loads(FROZEN.read_text(encoding="utf-8"))
    if p["schema"]!="MONSTER_STAGE39_FROZEN_ALL900x6_USDM_GROSS_GT_AND_UNCHANGED_V4_FUTURES_MINUTE_1M_CENSUS_V1" or (
        p["original_dataset"]["git_blob_sha1"]!=original.blob(STAGE37) or
        p["locked_original_V4_git_blob"]!=original.ORIGINAL_V4_GIT_BLOB or
        original.blob(original.production.__file__)!=original.ORIGINAL_V4_GIT_BLOB or
        tuple(p["dates"])!=DAYS):
        raise ValueError("STAGE39_NOT_SOURCE_PRE_REGISTERED_OR_PRODUCTION_CHANGED")
    with STAGE37.open(encoding="utf-8",newline="") as f:rows=list(csv.DictReader(f))
    valid=[r for r in rows if r["status"]=="COMPLETE_168H_PUBLISHER_SHA"]
    if (len(rows),len(valid),sum(r["gt2x"]=="True" for r in valid))!=(5400,3333,52):
        raise ValueError("STAGE39_ORIGINAL_HOURLY_ALL900_GT_DRIFT")
    for day in DAYS:
        entries=[r for r in rows if r["date"]==day]
        if len(entries)!=900 or len({x["symbol"] for x in entries})!=900:
            raise ValueError("STAGE39_ORIGINAL_900_EACH_DATE_DRIFT")
    return rows

def future_multiple_label(row,bars,watch_utc,n):
    if n not in (5,10):raise ValueError("STAGE39_INVALID_MULTIPLE")
    baseline=Decimal(row["baseline_1h_open"])
    clock=next((b[0] for b in bars[original.WARMUP:original.WARMUP+original.ACTIVE]
                if b[2]>=baseline*n),None)
    true=(row[f"gt{n}x"]=="True")
    if (clock is not None)!=true:raise ValueError("STAGE39_REAL_1MIN_HIGH_NOT_MATCH_FROZEN_HOUR_GT")
    watches=[original.msutc(x) for x in watch_utc]
    strictly=[w for w in watches if clock is not None and w<clock]
    if clock is None:cl="NO_FUTURE_MULTIPLE"
    elif strictly:cl="STRICTLY_EARLY_WATCH"
    elif clock in watches:cl="SAME_MINUTE_NOT_EARLY"
    elif watches:cl="WATCH_LATE"
    else:cl="NO_WATCH"
    return {"gross_high_gt"+str(n)+"x":true,
            "first_real_1m_HIGH_gt"+str(n)+"x_UTC":original.stamp(clock) if clock is not None else None,
            "watch_vs_gt"+str(n)+"x_class":cl,
            "pre_cross_nearest_watch_gt"+str(n)+"x_lead_min":
              (round((clock-max(strictly))/60000,3) if strictly else None)}

def evaluate(row,minute_get=original.minute_source,runner=original.production_scan):
    d={"date":row["date"],"symbol":row["symbol"],
       "hourly_status":row["status"],"original_GT2x_1h":row.get("gt2x",""),
       "original_GT5x_1h":row.get("gt5x",""),"original_GT10x_1h":row.get("gt10x",""),
       "source_status":"UNVERIFIED"}
    if row["status"]!="COMPLETE_168H_PUBLISHER_SHA":
        d.update(source_status="CENSORED_STAGE37_HOURLY_SOURCE")
        return d
    try:bars,proof=minute_get(row["symbol"],row["date"])
    except FileNotFoundError as e:
        d.update(source_status="CENSORED_DAILY_1M_404",source_reason=str(e)[:180])
        return d
    except ValueError as e:
        if str(e) in ("STAGE38_GAPPED_DAILY_1M","STAGE38_INCOMPLETE_FULL192H_OR_WRONG_UTC"):
            d.update(source_status="CENSORED_DAILY_1M_GAP",source_reason=str(e))
            return d
        raise
    hourly=Decimal(row["baseline_1h_open"])
    minute_start=bars[original.WARMUP][1]
    max_1m=max(b[2] for b in bars[original.WARMUP:original.WARMUP+original.ACTIVE])
    if minute_start!=hourly or max_1m/hourly!=Decimal(row["max_high_multiple"]):
        d.update(source_status=CONFLICT,
                 verified_original_1h_publisher_sha256=row["publisher_1h_month_sha256"],
                 verified_9_daily_1m_publisher_sha256=proof,
                 actual_1h_anchor_open=str(hourly),actual_1m_anchor_open=str(minute_start),
                 original_hour_max_high_multiple=row["max_high_multiple"],
                 reconstructed_1m_high_multiple_vs_hour_open=str(max_1m/hourly))
        return d
    actual=runner(row["symbol"],row["date"],bars)
    crossing=original.score(row,bars,actual)
    extra={}
    for n in (5,10):
        extra.update(future_multiple_label(row,bars,actual["WATCH_UTC"],n))
    d.update(source_status=COMPLETE,verified_original_1h_publisher_sha256=row["publisher_1h_month_sha256"],
             verified_9_daily_1m_publisher_sha256=proof,
             unchanged_V4_original_futures=True,
             **actual,**crossing,**extra)
    return d

def run(day,shard,workers=2):
    rows=lock()
    if day not in DAYS or shard not in range(6) or workers not in (1,2):
        raise ValueError("STAGE39_BAD_ORIGINAL_DAY_SHARD_WORKERS")
    selected=sorted((r for r in rows if r["date"]==day),key=lambda r:r["symbol"])
    subset=[r for i,r in enumerate(selected) if i%6==shard]
    if len(subset)!=150:raise ValueError("STAGE39_NOT_150_PER_SHARD")
    results=[];errors=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        jobs={pool.submit(evaluate,r):r for r in subset}
        for job in concurrent.futures.as_completed(jobs):
            r=jobs[job]
            try:
                result=job.result()
                if (result["date"],result["symbol"])!=(r["date"],r["symbol"]):
                    raise ValueError("STAGE39_WRONG_RETURNED_SYMBOL")
                results.append(result)
            except Exception as e:
                errors.append({"symbol":r["symbol"],"error":type(e).__name__+":"+str(e)[:220]})
            n=len(results)+len(errors)
            if n%25==0:
                print("STAGE39_ORIGINAL_REPLAY_PROGRESS "+json.dumps({"date":day,"shard":shard,
                  "cases_finished":n,"of":150,"hard_errors":len(errors),
                  "source_complete":sum(v["source_status"]==COMPLETE for v in results)}),flush=True)
    if errors or len(results)!=150:
        raise RuntimeError("STAGE39_REAL_SOURCE_OR_MODEL_FAIL_CLOSED "+json.dumps(errors[:10]))
    ordered=sorted(results,key=lambda r:r["symbol"])
    stats=collections.Counter(v["source_status"] for v in ordered)
    valid=[v for v in ordered if v["source_status"]==COMPLETE]
    return {"schema":SCHEMA,"date":day,"shard":shard,"original_stage37_data_sha":original.blob(STAGE37),
      "all900_per_date_and150_per_shard":True,"source_cases":len(ordered),
      "status_counts":dict(stats),"source_verified_good":len(valid),
      "gt2x_fullminute":sum(v["original_GT2x_1h"]=="True" for v in valid),
      "gt2x_pre_1min_high_WATCH":sum(v["classification"]=="STRICTLY_EARLY_WATCH" and v["original_GT2x_1h"]=="True" for v in valid),
      "gt5x_fullminute":sum(v["gross_high_gt5x"] for v in valid),
      "gt5x_pre_HIGH_WATCH":sum(v["gross_high_gt5x"] and v["watch_vs_gt5x_class"]=="STRICTLY_EARLY_WATCH" for v in valid),
      "negative_gt2x_WATCH_coin_dates":sum(v["original_GT2x_1h"]=="False" and v["watch_count"]>0 for v in valid),
      "all_WATCH_events":sum(v["watch_count"] for v in valid),
      "rows":ordered,
      "otherAIreview":"NOT_DONE","trading":"NO_GO","mail":"OFF","Monster_deployment":"NO_GO","Frank":"UNCHANGED"}

def selftest():
    row={"gt5x":"True","gt10x":"False","baseline_1h_open":"1"}
    at=original.msutc("2025-01-19T06:00:00Z")
    bars=[(at-original.WARMUP*60000+i*60000,Decimal(1),Decimal(1),Decimal(1),Decimal(1),Decimal(1),2)
          for i in range(original.BARS)]
    i=original.WARMUP+100
    bars[i]=(bars[i][0],Decimal(1),Decimal(5),Decimal(1),Decimal(1),Decimal(1),2)
    r=future_multiple_label(row,bars,[original.stamp(at+90*60000)],5)
    assert r["gross_high_gt5x"] and r["watch_vs_gt5x_class"]=="STRICTLY_EARLY_WATCH"
    assert r["pre_cross_nearest_watch_gt5x_lead_min"]==10
    same=future_multiple_label(row,bars,[original.stamp(at+100*60000)],5)
    assert same["watch_vs_gt5x_class"]=="SAME_MINUTE_NOT_EARLY"
    assert not future_multiple_label(row,bars,[],10)["gross_high_gt10x"]
    print("STAGE39_GT5_GT10_REAL_MINUTE_CROSS_CAUSAL_SELFTEST_PASS")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--selftest",action="store_true")
    p.add_argument("--date")
    p.add_argument("--shard",type=int)
    p.add_argument("--workers",type=int,default=2)
    p.add_argument("--output",type=Path)
    a=p.parse_args()
    if a.selftest:selftest();return
    if not a.date or a.shard is None or not a.output:p.error("--date, --shard, --output required")
    report=run(a.date,a.shard,a.workers)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)+"\n")
    print("STAGE39_FULL_ORIGINAL_MARKET_SHA_COMPLETE "+json.dumps({
      k:report[k] for k in ("date","shard","source_verified_good","gt2x_fullminute","gt2x_pre_1min_high_WATCH",
         "gt5x_fullminute","negative_gt2x_WATCH_coin_dates","all_WATCH_events","status_counts")},sort_keys=True))
if __name__=="__main__":main()
