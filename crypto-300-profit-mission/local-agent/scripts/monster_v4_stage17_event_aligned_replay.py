#!/usr/bin/env python3
"""Stage17: event-aligned, explicitly EXPOSED, production V4 1m replay.

Frozen 20 genuine 2x and 1 genuine 5x outcome labels from Stage16. These
are hindsight-selected diagnostics to investigate missed lead time, NOT
unbiased market precision or independent out-of-sample verification.
"""
import argparse
import concurrent.futures
import json
import sys
import urllib.error
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

try:
    import monster_v4_archive_universe_replay as archive
    import monster_v4_historical_replay as replay
except ImportError:
    from scripts import monster_v4_archive_universe_replay as archive
    from scripts import monster_v4_historical_replay as replay

FROZEN = archive.source.EVIDENCE / "monster_stage16_actual_frozen_7d_outcome_labels_20261011.json"
MAX_WORKERS = 4

def frozen_events():
    doc=json.loads(FROZEN.read_text(encoding="utf-8"))
    if (doc.get("schema")!="MONSTER_STAGE16_FROZEN_7D_2X5X10X_OFFICIAL_1H_ACTUAL_CI_V1"
            or doc.get("totals",{}).get("gross_high_2x")!=20
            or len(doc.get("gross_high_2x_event_register",[]))!=20):
        raise ValueError("STAGE17_GT_INPUT_NOT_FROZEN")
    entries=[]
    for row in doc["gross_high_2x_event_register"]:
        entries.append({
            "date":row["date"],"symbol":row["symbol"],"threshold":2,
            "base_open":row["base_open"],"hour_index":row["first_hourly_high_2x_index"]})
    top=doc["only_5x"]
    if (top.get("symbol")!="TNSRUSDT" or top.get("date")!="2025-11-17"
            or top.get("first_high_5x_hour_index")!=78):
        raise ValueError("STAGE17_UNEXPECTED_5X_ID")
    entries.append({"date":top["date"],"symbol":top["symbol"],"threshold":5,
                    "base_open":top["baseline_open"],"hour_index":78})
    keys=[(x["date"],x["symbol"],x["threshold"]) for x in entries]
    if len(set(keys))!=21:
        raise ValueError("STAGE17_DUPLICATE_FROZEN_EVENTS")
    return entries

def utc_ms(time):
    return int(time.timestamp()*1000)

def replay_event(event, downloader=archive.get_day,
                 scorer=replay.replay_case):
    base_day=date.fromisoformat(event["date"])
    anchor=datetime(base_day.year,base_day.month,base_day.day,6,
                    tzinfo=timezone.utc)+timedelta(hours=event["hour_index"])
    start=anchor-timedelta(hours=30)
    stop=anchor+timedelta(hours=30)
    all_rows={}
    proof=[]
    day=start.date()
    try:
        while day<=stop.date():
            rows,detail=downloader(event["symbol"],day)
            proof.append({"date":day.isoformat(),"sha256":detail["sha256"]})
            for row in rows:
                if row[0] in all_rows:
                    raise ValueError("DUPLICATE_1M_BAR")
                all_rows[row[0]]=row
            day+=timedelta(days=1)
        begin=utc_ms(start)
        bars=[all_rows.get(begin+i*60000) for i in range(3600)]
        if any(row is None for row in bars):
            raise ValueError("INCOMPLETE_60H_1M_DATA")
        first_hour=utc_ms(anchor)
        threshold=Decimal(str(event["base_open"]))*event["threshold"]
        crossing=next((x[0] for x in bars if first_hour<=x[0]<first_hour+3600000
                       and x[2]>=threshold),None)
        if crossing is None:
            raise ValueError("STAGE17_HOURLY_GT_AND_1M_SOURCE_DISAGREE")
        context={"symbol":event["symbol"],"venue":"spot",
                 "cohort":"STAGE17_EXPOSED_EVENT_ALIGNED",
                 "old_watch_utc":anchor.isoformat().replace("+00:00","Z")}
        result=scorer(context,bars,include_zero_trade_ticks=True)
        if result["symbol"]!=event["symbol"]:
            raise ValueError("WRONG_EVENT_SYMBOL")
        first_watch=result.get("first_watch_utc")
        watch_ms=replay.parse_ms(first_watch) if first_watch else None
        if watch_ms is None:
            status="NO_WATCH_IN_EVENT_ALIGNED_12H"
        elif watch_ms<=crossing:
            status="WATCH_BEFORE_OR_AT_FIRST_1M_CROSS"
        else:
            status="WATCH_AFTER_FIRST_1M_CROSS"
        return {
            "date":event["date"],"symbol":event["symbol"],
            "threshold":event["threshold"],"hour_index":event["hour_index"],
            "status":"COMPLETE_CAUSAL_1M_REPLAY",
            "classification":status,"first_cross_minute_utc":replay.utc(crossing),
            "first_watch_utc":first_watch,
            "lead_minutes_if_watch":round((crossing-watch_ms)/60000,3)
                    if watch_ms is not None else None,
            "watch_events":result["watch_count"],"d1_setups":result["d1_setups"],
            "trade_proxies":result["trade_proxies"],
            "source_sha256":proof,
            "historical_l2_verified":False,
            "event_selected_using_known_future":True,
        }
    except (ValueError,urllib.error.HTTPError,urllib.error.URLError,
            TimeoutError,OSError,KeyError) as exc:
        return {"date":event["date"],"symbol":event["symbol"],
                "threshold":event["threshold"],"hour_index":event["hour_index"],
                "status":"CENSORED_OR_SOURCE_FAILED",
                "reason":type(exc).__name__+":"+str(exc)[:180],
                "watch_events":None,"d1_setups":None}

def run(events=None, worker=replay_event, max_workers=MAX_WORKERS):
    prereg=frozen_events()
    chosen=prereg if events is None else events
    frozen_keys={(x["date"],x["symbol"],x["threshold"]) for x in prereg}
    chosen_keys=[(x["date"],x["symbol"],x["threshold"]) for x in chosen]
    if len(chosen_keys)!=len(set(chosen_keys)) or any(x not in frozen_keys for x in chosen_keys):
        raise ValueError("STAGE17_NONFROZEN_EVENT")
    if not 1<=max_workers<=MAX_WORKERS:
        raise ValueError("STAGE17_UNSAFE_CONCURRENCY")
    output=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
        jobs={pool.submit(worker,event):event for event in chosen}
        for future in concurrent.futures.as_completed(jobs):
            item=future.result()
            expected=jobs[future]
            if (item["date"],item["symbol"],item["threshold"])!=(
                    expected["date"],expected["symbol"],expected["threshold"]):
                raise ValueError("STAGE17_WORKER_ID_MISMATCH")
            output.append(item)
    output.sort(key=lambda x:(x["date"],x["symbol"],x["threshold"]))
    statuses=Counter(r["status"] for r in output)
    valid=[r for r in output if r["status"]=="COMPLETE_CAUSAL_1M_REPLAY"]
    classes=Counter(r["classification"] for r in valid)
    return {"schema":"MONSTER_STAGE17_EXPOSED_2X5X_EVENT_ALIGNED_V4_1M_V1",
            "research_only":True,"not_out_of_sample":True,
            "not_true_unbiased_recall_rate":True,
            "baseline_gt":"STAGE16_FROZEN_MONTHLY_1H_FUTURE_HIGH",
            "actual_cross":"FIRST_VERIFIED_OFFICIAL_1M_HIGH_WITHIN_FIRST_1H_GT_CROSS_HOUR",
            "production_engine":"MONSTER_V4_D0_D1_EXISTING_UNMODIFIED",
            "summary":{"attempted":len(output),"status_counts":dict(statuses),
                 "complete":len(valid),"classification_counts":dict(classes),
                 "five_x_events":sum(r["threshold"]==5 for r in valid)},
            "cases":output,"deployment":"NO_GO",
            "real_mail_sent":False,"automated_trading":False}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    report=run()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("STAGE17_RESULT_JSON "+json.dumps(report["summary"],sort_keys=True),flush=True)
    if report["summary"]["attempted"]!=21 or report["summary"]["complete"]<10:
        raise SystemExit("STAGE17_TOO_FEW_COMPLETE_CAUSAL_EVENTS")

if __name__=="__main__":
    main()
