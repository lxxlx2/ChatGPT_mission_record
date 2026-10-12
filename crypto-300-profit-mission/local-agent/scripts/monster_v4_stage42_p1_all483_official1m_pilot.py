#!/usr/bin/env python3
"""Stage42 exposed-data Stage39 all483 original Futures first WATCH P1 study.

Publisher-SHA OFFICIAL daily1m source. Same source-frozen pure Stage42 P1
candidate code. Never a new independent performance validation, alert, BUY,
Frank edit, Gmail send or trading bot.
"""
import argparse,concurrent.futures,csv,hashlib,json
from collections import Counter
from datetime import datetime,date,timedelta,timezone
from pathlib import Path

try:
    import monster_v4_stage42_p1_priority_v01 as p1
    import monster_v4_stage38_usdm_original_v4_1m_pilot as replay
except ImportError:
    from scripts import monster_v4_stage42_p1_priority_v01 as p1
    from scripts import monster_v4_stage38_usdm_original_v4_1m_pilot as replay

EVIDENCE=Path(__file__).resolve().parents[2]/"monster"/"evidence"
STAGE39=EVIDENCE/"monster_stage39_all5400_usdm_real1m_originalV4_cases.jsonl"
STAGE40=EVIDENCE/"monster_stage40_candidate_priority_v01_frozen_before_any_holdout_20261012.json"
FROZEN=EVIDENCE/"monster_stage42_all483_exposed_firstwatch_p1_pilot_prereg_20261012.json"
STAGE39_BLOB="a2f66aa2331d02d14c0276b446381dc6856cba0e"
STAGE40_BLOB="d5b2b2522e9baa9a89c468ca4c3abc2d922cd8a7"
SCHEMA="MONSTER_STAGE42_EXPOSED483_P1_RESEARCH_ONLY_ORIGINAL_V4_FIRST_WATCH_REAL_SHA_V1"
DAYS=("2025-01-19","2025-04-19","2025-07-19","2025-10-19","2026-04-19","2026-07-19")
EXPECTED=(36,100,75,80,113,79)

def blob(path):
    b=Path(path).read_bytes()
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()

def frozen():
    spec=json.loads(FROZEN.read_text())
    if (spec["schema"]!="MONSTER_STAGE42_FROZEN_ALL483_ORIGINAL_V4_FUTURES_FIRST_WATCH_P1_EXPOSED_PILOT_V1" or
       blob(STAGE39)!=STAGE39_BLOB or blob(STAGE40)!=STAGE40_BLOB or
       spec["stage39_full5400_git_blob_sha1"]!=STAGE39_BLOB or
       spec["stage40_candidate_git_blob_sha1"]!=STAGE40_BLOB):
        raise ValueError("STAGE42_FROZEN_INPUTS_OR_THRESHOLDS_DRIFT")
    rows=[json.loads(line) for line in STAGE39.read_text().splitlines() if line]
    if len(rows)!=5400:
        raise ValueError("STAGE42_STAGE39_FULL5400_NOT_PRESENT")
    watches=[r for r in rows if r["source_status"]=="COMPLETE_REAL_USDM_1M_SHA_CAUSAL_V4" and r["watch_count"]>0]
    if len(watches)!=483 or len({(r["date"],r["symbol"]) for r in watches})!=483:
        raise ValueError("STAGE42_ORIGINAL483_FIRST_WATCH_COHORT_NOT_FROZEN")
    for day,n in zip(DAYS,EXPECTED):
        if sum(r["date"]==day for r in watches)!=n:raise ValueError("STAGE42_DATE_WATCH_COHORT_DRIFT")
    return sorted(watches,key=lambda r:(r["date"],r["symbol"]))

def load_closed_bars(symbol,watch_utc,getday=replay.verified_1m_day):
    watch_ms=p1.parse_utc(watch_utc)
    start=watch_ms-61*60000
    end=watch_ms+5*60000
    lo=datetime.fromtimestamp(start/1000,timezone.utc).date()
    hi=datetime.fromtimestamp(end/1000,timezone.utc).date()
    bars=[];proof=[]
    for num in range((hi-lo).days+1):
        d=lo+timedelta(days=num)
        k,p=getday(symbol,d)
        if len(k)!=1440 or not p.get("verified_official_publisher_SHA256"):
            raise ValueError("STAGE42_UNVERIFIED_SOURCE_PUBLISHER_SHA")
        bars.extend(k)
        proof.append(p)
    if len(proof) not in (1,2):raise ValueError("STAGE42_UNEXPECTED_SOURCE_DAYS")
    return bars,proof

def compute(r,read=load_closed_bars,calculate=p1.calculate):
    if not r["WATCH_UTC"] or r["watch_count"]!=len(r["WATCH_UTC"]):
        raise ValueError("STAGE42_ORIGINAL_V4_WATCH_LIST_WRONG")
    watch=r["WATCH_UTC"][0]
    bars,proof=read(r["symbol"],watch)
    ev_id=hashlib.sha256(("MONSTER_V4_OFFLINE|futures|"+r["symbol"]+"|"+watch).encode()).hexdigest()
    model=calculate("futures",r["symbol"],watch,bars,ev_id)
    if model["status"]=="UNSCORABLE_SOURCE":
        raise ValueError("STAGE42_SOURCE_BEFORE_AFTER_WATCH_IS_INCOMPLETE")
    d={"date":r["date"],"symbol":r["symbol"],"stage39_first_v4_WATCH_UTC":watch,
       "original_watch_events":r["watch_count"],
       "source_dated_1m_publisher_SHA":proof,
       "source_status":"VERIFIED_CAUSAL_P1_ASOF",
       "prior_stage39_GT2x":r["original_GT2x_1h"]=="True",
       "prior_stage39_GT5x":r["gross_high_gt5x"],
       "prior_stage39_GT10x":r["gross_high_gt10x"],
       "prior_stage39_first_2x_high_1m_UTC":r["first_true_2x_HIGH_minute_UTC"],
       "original_stage39_EARLY_2x":r["classification"]=="STRICTLY_EARLY_WATCH",
       "research_p1":model}
    end_window=replay.msutc(r["date"]+"T06:00:00Z")+168*60*60000
    decision=model.get("P1_escalation_UTC")
    if decision and p1.parse_utc(decision)>=end_window:
        d["research_p1"]={**model,"status":"P1_OUTSIDE_FROZEN_ACTIVE_WINDOW",
            "P1_escalation_UTC":None}
    return d

def run(day,shard,workers=3):
    if day not in DAYS or shard not in (0,1) or workers not in (1,2,3,4):
        raise ValueError("STAGE42_DATE_OR_SHARD_OR_WORKERS_INVALID")
    rows=[r for r in frozen() if r["date"]==day]
    selected=[r for i,r in enumerate(rows) if i%2==shard]
    if not selected:raise ValueError("STAGE42_EMPTY_FIRST_WATCH_SHARD")
    out=[];errors=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        jobs={pool.submit(compute,r):r for r in selected}
        for job in concurrent.futures.as_completed(jobs):
            r=jobs[job]
            try:out.append(job.result())
            except Exception as e:errors.append({"symbol":r["symbol"],"type":type(e).__name__,"error":str(e)[:220]})
            if (len(out)+len(errors))%10==0:
                print("STAGE42_P1_REAL_SOURCE_PROGRESS "+json.dumps({
                    "date":day,"shard":shard,"seen":len(out)+len(errors),
                    "expected":len(selected),"hard_errors":len(errors)}),flush=True)
    if errors or len(out)!=len(selected):
        raise RuntimeError("STAGE42_REAL_MINUTE_SOURCE_FAIL_CLOSED "+json.dumps(errors[:8]))
    out.sort(key=lambda r:r["symbol"])
    return {"schema":SCHEMA,"date":day,"shard":shard,"selected_cases":len(selected),
            "research_p1_eligible":sum(r["research_p1"]["status"]=="P1_RESEARCH_ELIGIBLE" for r in out),
            "research_p1_not_eligible":sum(r["research_p1"]["status"]!="P1_RESEARCH_ELIGIBLE" for r in out),
            "rows":out,"source_errors":[],"historical_exposed_only":True,
            "otherAIreview":"NOT_DONE","Gmail":"OFF","Frank":"UNCHANGED","auto_trade":"NO_GO"}

def selftest():
    assert sum(EXPECTED)==483
    assert p1.parse_utc("2025-04-19T09:00:00Z")%60000==0
    print("STAGE42_PRE_FROZEN_483_SHA_PILOT_SELFTEST_PASS")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--selftest",action="store_true")
    p.add_argument("--date")
    p.add_argument("--shard",type=int)
    p.add_argument("--workers",type=int,default=3)
    p.add_argument("--output",type=Path)
    a=p.parse_args()
    if a.selftest:selftest();return
    if a.date is None or a.shard is None or a.output is None:p.error("--date --shard --output required")
    result=run(a.date,a.shard,a.workers)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+"\n")
    print("STAGE42_EXPOSED_P1_OFFICIAL_SHA_COHORT "+json.dumps({
        k:result[k] for k in ("date","shard","selected_cases","research_p1_eligible")},sort_keys=True))
if __name__=="__main__":main()
