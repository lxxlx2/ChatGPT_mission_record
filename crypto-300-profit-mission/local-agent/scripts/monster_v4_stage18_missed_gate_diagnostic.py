#!/usr/bin/env python3
"""Stage18: diagnosed real missed/late V4 2x events, no threshold changes.

Freeze only the 7 genuinely absent/late first-cross Stage17 cases and rerun
exact source-aligned pre-cross D0 gates: 3m 5%, 15m 8%, 60m 15%, 24h
quote turnover 100k. Retrospective causal diagnostic, not validation.
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
    import monster_v4_stage17_event_aligned_replay as stage17
except ImportError:
    from scripts import monster_v4_stage17_event_aligned_replay as stage17

EVIDENCE = stage17.archive.source.EVIDENCE
STAGE17_PROOF = EVIDENCE / "monster_stage17_actual_firstcross_minute_replay_ci_20261011.json"
FAILURES = {"ENSOUSDT","ENAUSDT","STXUSDT","NILUSDT",
            "SAGAUSDT","ZAMAUSDT","ARUSDT"}
REQUIRE_QUOTE=Decimal("100000")
WINDOWS={3:Decimal("0.05"),15:Decimal("0.08"),60:Decimal("0.15")}

def frozen_failed_events():
    proof=json.loads(STAGE17_PROOF.read_text(encoding="utf-8"))
    if proof.get("schema")!="MONSTER_STAGE17_EXPOSED_EVENT_ALIGNED_TRUE_1M_V4_CI_V1":
        raise ValueError("STAGE18_WRONG_FROZEN_PRIOR")
    failures={row["symbol"]:row for row in proof["cases"]
              if row["threshold_x"]==2 and row["classification"] in ("NO_WATCH","LATE")}
    if set(failures)!=FAILURES or len(failures)!=7:
        raise ValueError("STAGE18_FAILED_SET_DRIFT")
    selected=[event for event in stage17.frozen_events()
              if event["threshold"]==2 and event["symbol"] in FAILURES]
    if len(selected)!=7:
        raise ValueError("STAGE18_BAD_PREREG_SIZE")
    return selected

def analyze(event, download=stage17.archive.get_day):
    base_day=date.fromisoformat(event["date"])
    anchor=datetime(base_day.year,base_day.month,base_day.day,6,
                    tzinfo=timezone.utc)+timedelta(hours=event["hour_index"])
    start=anchor-timedelta(hours=30)
    stop=anchor+timedelta(hours=30)
    all_rows={}
    proof=[]
    try:
        day=start.date()
        while day<=stop.date():
            rows,meta=download(event["symbol"],day)
            proof.append({"day":day.isoformat(),"sha256":meta["sha256"]})
            for row in rows:
                if row[0] in all_rows:
                    raise ValueError("DUPLICATE_MINUTE")
                all_rows[row[0]]=row
            day+=timedelta(days=1)
        begin=stage17.utc_ms(start)
        bars=[all_rows.get(begin+i*60000) for i in range(3600)]
        if any(x is None for x in bars):
            raise ValueError("INCOMPLETE_60H")
        hour_start=stage17.utc_ms(anchor)
        threshold=Decimal(str(event["base_open"]))*event["threshold"]
        crossed=next((x[0] for x in bars if hour_start<=x[0]<hour_start+3600000
                      and x[2]>=threshold),None)
        if crossed is None:
            raise ValueError("PREVIOUS_1H_GT_SOURCE_MISMATCH")
        quote_prefix=[Decimal(0)]
        for row in bars:
            quote_prefix.append(quote_prefix[-1]+row[5])
        ticks=0;quote_pass=0;price_pass=0;both_pass=0
        by_window=Counter();best={3:Decimal("-1"),15:Decimal("-1"),60:Decimal("-1")}
        max_quote=Decimal(0);quote_at_last=None
        first_price_gate=None;first_both_gate=None
        for i in range(1442,2160,3):
            observed=bars[i][0]+60000
            if observed>crossed:
                break
            ticks+=1
            price=bars[i][4]
            quote=quote_prefix[i+1]-quote_prefix[i+1-1440]
            quote_at_last=quote
            max_quote=max(quote,max_quote)
            if quote>=REQUIRE_QUOTE:
                quote_pass+=1
            fires=[]
            for n,level in WINDOWS.items():
                # first polled source has no historical snapshot; 3m, 15m,
                # 60m lags start only after their first sampled baseline.
                if i < 1442+n:
                    continue
                pct=price/bars[i-n][4]-1
                best[n]=max(pct,best[n])
                if pct>=level:
                    fires.append(n)
                    by_window[n]+=1
            if fires:
                price_pass+=1
                if first_price_gate is None:
                    first_price_gate=observed
                if quote>=REQUIRE_QUOTE:
                    both_pass+=1
                    if first_both_gate is None:
                        first_both_gate=observed
        if not ticks:
            raise ValueError("NO_OBSERVABLE_BEFORE_FIRST_CROSS")
        if both_pass:
            cause="PRE_CROSS_BOTH_GATES_PRESENT_INVESTIGATE_D0_TIME_MATCH"
        elif price_pass and not both_pass:
            cause="LIQUIDITY_GATE_BLOCKED_ALL_PRICE_TRIGGERS"
        else:
            cause="NO_FROZEN_MOMENTUM_TRIGGER_BEFORE_2X"
        return {"symbol":event["symbol"],"date":event["date"],"threshold":2,
            "status":"COMPLETE_GATE_DIAGNOSTIC",
            "cause":cause,
            "cross_utc":stage17.replay.utc(crossed),
            "ticks_before_cross":ticks,"ticks_quote24_ge_100k":quote_pass,
            "ticks_price_trigger_without_quote_gate":price_pass,
            "ticks_price_and_quote_both_pass":both_pass,
            "window_trigger_counts":{str(k):by_window[k] for k in WINDOWS},
            "maximum_pct_pre_cross":{str(k):round(float(best[k]*100),6) for k in WINDOWS},
            "quote24_last_before_cross":str(quote_at_last),
            "quote24_max_pre_cross":str(max_quote),
            "first_price_gate_utc":stage17.replay.utc(first_price_gate)
                    if first_price_gate is not None else None,
            "first_both_gate_utc":stage17.replay.utc(first_both_gate)
                    if first_both_gate is not None else None,
            "verified_daily_sha256":proof,
            "production_thresholds_unchanged":True}
    except (ValueError,KeyError,urllib.error.HTTPError,urllib.error.URLError,
            TimeoutError,OSError) as e:
        return {"symbol":event["symbol"],"date":event["date"],"threshold":2,
                "status":"SOURCE_FAILED_OR_CENSORED",
                "reason":type(e).__name__+":"+str(e)[:150]}

def run(events=None, worker=analyze):
    expected=frozen_failed_events()
    chosen=expected if events is None else events
    ids={(e["date"],e["symbol"]) for e in expected}
    if len(chosen)!=len({(e["date"],e["symbol"]) for e in chosen}) or any(
            (e["date"],e["symbol"]) not in ids for e in chosen):
        raise ValueError("STAGE18_NONFROZEN_EVENT")
    output=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        futures={pool.submit(worker,e):e for e in chosen}
        for f in concurrent.futures.as_completed(futures):
            item=f.result()
            if (item["date"],item["symbol"])!=(
                    futures[f]["date"],futures[f]["symbol"]):
                raise ValueError("STAGE18_WORKER_IDENTITY")
            output.append(item)
    output.sort(key=lambda x:(x["date"],x["symbol"]))
    statuses=Counter(x["status"] for x in output)
    causes=Counter(x["cause"] for x in output if x["status"]=="COMPLETE_GATE_DIAGNOSTIC")
    return {"schema":"MONSTER_STAGE18_MISSED_SEVEN_V4_CAUSAL_GATE_DIAGNOSTIC_V1",
        "research_only":True,"exposed_known_outcomes":True,
        "data":"BINANCE_PUBLISHER_SHA256_VERIFIED_DAILY_SPOT_1M",
        "strictly_pre_first_high_cross":True,
        "summary":{"attempted":len(output),"statuses":dict(statuses),"causes":dict(causes)},
        "cases":output,"threshold_changes":False,"mac_deployment":"NO_GO"}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output",required=True,type=Path)
    args=p.parse_args()
    report=run()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("STAGE18_RESULT_JSON "+json.dumps(report["summary"],sort_keys=True),flush=True)
    if report["summary"]["statuses"].get("COMPLETE_GATE_DIAGNOSTIC",0)<5:
        raise SystemExit("STAGE18_SOURCE_TOO_INCOMPLETE")

if __name__=="__main__":
    main()
