#!/usr/bin/env python3
"""Stage25 read-only hindsight-selected 40 winner cohort first 1m crossing audit.

All 40 gross-high 2x and associated 4 x5 + 1 x10 are derived exclusively
from Stage24 six original ZIPs rehashed with official source evidence.
Replays original production V4 using unchanged Stage17 60h event-local code.
NOT an unbiased full-market seven-day model-recall estimate.
"""
import argparse
import concurrent.futures
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

try:
    import monster_v4_stage24_aggregate as old
    import monster_v4_stage17_event_aligned_replay as scorer
    import monster_v4_historical_replay as production
except ImportError:
    from scripts import monster_v4_stage24_aggregate as old
    from scripts import monster_v4_stage17_event_aligned_replay as scorer
    from scripts import monster_v4_historical_replay as production

PRE=old.EVIDENCE/"monster_stage25_known_2x5x10x_event_time_diagnostic_prereg_20261011.json"
REGISTER=old.EVIDENCE/"monster_stage24_40_joint_verified_2x_events_20261011.csv"

def git_blob(path):
    content=Path(path).read_bytes()
    return hashlib.sha1(b"blob "+str(len(content)).encode()+b"\0"+content).hexdigest()

def frozen_original_events(zips):
    cfg=json.loads(PRE.read_text(encoding="utf-8"))
    if cfg["schema"]!="MONSTER_STAGE25_STAGE24_ALL_VERIFIED_WINNER_EVENT_ALIGNED_CAUSAL_DIAGNOSTIC_PREREG_V1":
        raise ValueError("STAGE25_MANIFEST_SCHEMA_MISMATCH")
    if git_blob(scorer.__file__)!=cfg["exact_existing_event_scorer_git_blob_sha1"] or git_blob(production.__file__)!=cfg["exact_original_production_v4_replayer_git_blob_sha1"]:
        raise ValueError("STAGE25_SOURCE_CODE_CHANGED")
    proof=json.loads(old.PROOF.read_text(encoding="utf-8"))
    expected={a["date"]:a for a in proof["artifacts"]}
    dates=cfg["dates"]
    if len(zips)!=6 or set(expected)!=set(dates):
        raise ValueError("STAGE25_REQUIRE_SIX_ORIGINAL_758_DATES")
    register=list(csv.DictReader(REGISTER.read_text(encoding="utf-8").splitlines()))
    if len(register)!=40 or len({(r["date_utc"],r["symbol"]) for r in register})!=40:
        raise ValueError("STAGE25_PRECOMMITTED_EVENT_COHORT_NOT_40")
    byday={}
    for path in zips:
        import zipfile
        with zipfile.ZipFile(path) as z:
            members=z.namelist()
        if len(members)!=1:raise ValueError("STAGE25_WRONG_ARTIFACT_MEMBERS")
        day=members[0].removeprefix("monster_stage24_").removesuffix(".json")
        if day not in expected or day in byday:raise ValueError("STAGE25_NONFROZEN_OR_DUPLICATE_DATE")
        byday[day]=old.open_artifact(path,expected[day])
    if set(byday)!=set(dates):raise ValueError("STAGE25_ORIGINAL_DATES_INCOMPLETE")
    events=[]
    eligible=[]
    for day in dates:
        for r in byday[day]["cases"]:
            h=r["hourly"]
            if (h["status"]=="VERIFIED_COMPLETE_168H"
                    and r["minute"]["status"]=="VERIFIED_COMPLETE_60H_1M"
                    and h["gross_high_ge_2x"]):
                eligible.append((day,r["symbol"]))
                for multiple in (2,5,10):
                    if h["gross_high_ge_"+str(multiple)+"x"]:
                        events.append({
                           "date":day,"symbol":r["symbol"],"threshold":multiple,
                           "base_open":h["baseline_1h_open"],
                           "hour_index":h["first_high_"+str(multiple)+"x_hour_index"]})
    assert_items={(r["date_utc"],r["symbol"]) for r in register}
    if set(eligible)!=assert_items:
        raise ValueError("STAGE25_GT_REGISTER_AND_ORIGINAL_DATA_NOT_EQUAL")
    counts=Counter(e["threshold"] for e in events)
    if len(eligible)!=40 or counts!={2:40,5:4,10:1}:
        raise ValueError("STAGE25_CHANGED_40_4_1_HISTORICAL_COHORT")
    return sorted(events,key=lambda r:(r["date"],r["symbol"],r["threshold"]))

def summary(rows):
    valid=[r for r in rows if r["status"]=="COMPLETE_CAUSAL_1M_REPLAY"]
    result={"attempted":len(rows),"status":dict(Counter(r["status"] for r in rows)),
      "complete":len(valid),"by_multiple":{}}
    for multiple in (2,5,10):
        selected=[r for r in valid if r["threshold"]==multiple]
        result["by_multiple"][str(multiple)+"x"]={
            "complete":len(selected),
            "early_or_same_minute":sum(r["classification"]=="WATCH_BEFORE_OR_AT_FIRST_1M_CROSS" for r in selected),
            "late":sum(r["classification"]=="WATCH_AFTER_FIRST_1M_CROSS" for r in selected),
            "no_watch_in_aligned_12h":sum(r["classification"]=="NO_WATCH_IN_EVENT_ALIGNED_12H" for r in selected),
            "median_lead_minutes_if_early":None}
        import statistics
        positive_leads=[r["lead_minutes_if_watch"] for r in selected
                        if r["classification"]=="WATCH_BEFORE_OR_AT_FIRST_1M_CROSS"]
        if positive_leads:
            result["by_multiple"][str(multiple)+"x"]["median_lead_minutes_if_early"]=round(statistics.median(positive_leads),6)
    return result

def run(original_zips,worker=scorer.replay_event,max_workers=4):
    events=frozen_original_events(original_zips)
    if max_workers<1 or max_workers>4:raise ValueError("STAGE25_MAX_CONCURRENCY")
    output=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
        jobs={pool.submit(worker,ev):(ev["date"],ev["symbol"],ev["threshold"]) for ev in events}
        for future in concurrent.futures.as_completed(jobs):
            r=future.result()
            if (r["date"],r["symbol"],r["threshold"])!=jobs[future]:
                raise ValueError("STAGE25_RESULT_IDENTITY_DRIFT")
            output.append(r)
    output.sort(key=lambda r:(r["date"],r["symbol"],r["threshold"]))
    return {"schema":"MONSTER_STAGE25_ALL40_KNOWN_WINNERS_EXPOSED_EVENT_ALIGNED_1M_V4_V1",
       "source":"STAGE24_SIX_ORIGINAL_SHA256_VERIFIED_GT_AND_BINANCE_DAILY_1M",
       "hindsight_selected_known_winners":True,
       "not_full_market_168h_watch_recall":True,
       "original_v4_unchanged":True,
       "summary":summary(output),"cases":output,
       "other_ai_review":"NOT_DONE","deployment":"NO_GO",
       "frank":"UNCHANGED","real_gmail":False,"trading":False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--stage24-zips",type=Path,nargs=6,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    result=run(a.stage24_zips)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("STAGE25_RESULT_JSON "+json.dumps(result["summary"],sort_keys=True),flush=True)
    if result["summary"]["complete"]!=45:
        raise SystemExit("STAGE25_INCOMPLETE_EVENT_DIAGNOSTIC")
if __name__=="__main__":
    main()
