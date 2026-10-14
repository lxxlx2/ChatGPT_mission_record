#!/usr/bin/env python3
"""Stage113: source-verified fixed 5m/60m/360m/1440m gross price profiles.
Read-only historical research. Stage111 frozen causal model NEVER modified.
"""
from __future__ import annotations

import argparse
import concurrent.futures
from datetime import datetime, timezone
from decimal import Decimal
import json
from pathlib import Path

try:
    import monster_v4_stage111_full519_replay_official as replay
    import monster_v4_stage112_repeated_ignition_diagnostic as stage112
except ImportError:
    from scripts import monster_v4_stage111_full519_replay_official as replay
    from scripts import monster_v4_stage112_repeated_ignition_diagnostic as stage112

old = replay.old
MIN = 60_000
HORIZONS = (5,60,360,1440)
SCHEMA = "MONSTER_STAGE113_ORIGINAL519_4_FROZEN_HORIZONS_OFFICIAL1M_V1"
PIN112 = "1f07c873a8cddbac5128a4b97d64cf4c6d554ba3"


def frozen():
    stage112.frozen_aggregate()
    f = stage112.E / "monster_stage112_real519_first_repeat_diagnostic.json"
    raw = f.read_bytes()
    if stage112.git_blob(raw) != PIN112:
        raise ValueError("STAGE113_STAGE112_SOURCE_DIAGNOSTIC_GIT_BLOB_CHANGED")
    base=json.loads(raw)
    rows, original = replay.frozen()
    if base["original519"]!=519 or base["original_priorities_740"]!=740:
        raise ValueError("STAGE113_SOURCE_COHORT_CHANGED")
    bycase={(x["date"],x["symbol"]):x for x in base["case_rows"]}
    if len(bycase)!=519 or len(rows)!=519:
        raise ValueError("STAGE113_SOURCE_CASES_NOT_519")
    return rows, original, bycase


def price_horizon(t:int, h:int, end:int, minutes:dict):
    if h not in HORIZONS or t % MIN or end % MIN or t >= end:
        raise ValueError("STAGE113_HORIZON_OR_TIME_CONTRACT_DRIFT")
    exit_close_visible=t+h*MIN
    if exit_close_visible > end:
        return {"status":"CENSORED_FROZEN_7DAY_BOUNDARY",
                "gross_pct":None, "holding_minutes":h}
    candles=[minutes.get(t+i*MIN) for i in range(h)]
    if any(z is None for z in candles):
        return {"status":"CENSORED_MISSING_1M",
                "gross_pct":None, "holding_minutes":h}
    if not candles or candles[0][0]!=t or candles[-1][0]!=t+(h-1)*MIN:
        raise ValueError("STAGE113_NONCONTIGUOUS_MINUTE_SOURCE")
    first, final=candles[0],candles[-1]
    if (first[1]<=0 or first[5]<=0 or first[6]<=0 or
            final[4]<=0 or final[5]<=0 or final[6]<=0):
        return {"status":"CENSORED_UNTRADED_ENTRY_OR_EXIT",
                "gross_pct":None, "holding_minutes":h}
    entry, last=first[1],final[4]
    gross=(last/entry-1)*100
    low=min(z[3] for z in candles)
    fee_20bps=((last/entry)*(Decimal("0.998")/Decimal("1.002"))-1)*100
    return {
        "status":"COMPLETE_PRICE_ONLY",
        "holding_minutes":h,
        "entry_next_1m_open":str(entry),
        "exit_completed_last_1m_close":str(last),
        "exit_bar_open_ms":final[0],
        "gross_pct":str(gross),
        "theoretical_20bps_each_side_pct":str(fee_20bps),
        "lowest_1m_low_from_entry_pct_NOT_A_STOP_FILL":str((low/entry-1)*100),
        "real_executable_net_pnl":"UNKNOWN",
    }


def one_case(x, previous, reference, reader=None):
    if reader is None:
        reader=old.publisher.verified_1m_day
    captured={}
    def read(symbol,day):
        bars,proof=reader(symbol,day)
        captured[day.isoformat()]=bars
        return bars,proof
    original=replay.official_case(x,previous,reader=read)
    keys=(x["date"],x["symbol"])
    if ((original["date"],original["symbol"])!=keys
            or reference["date"]!=x["date"]
            or reference["symbol"]!=x["symbol"]):
        raise ValueError("STAGE113_STAGE112_CASE_IDENTITY_CHANGED")
    status=original["causal_state"]["source_status"]
    events=[v for v in original["causal_state"]["events"] if v["state"]=="PRIORITY"]
    if status=="EXPIRED":
        if (reference["priorities"]!=len(events)
                or reference["first_priority_utc_ms"]!=(
                    events[0]["observable_ms"] if events else None)):
            raise ValueError("STAGE113_STAGE112_EVENT_TIMELINE_DRIFT")
    lookup={z[0]:z for rows in captured.values() for z in rows}
    obs=[]
    proxies=original["price_only_24h"]
    if len(events)!=len(proxies):
        raise ValueError("STAGE113_PRIORITY_24H_BASELINE_MISMATCH")
    end=original["causal_state"]["anchor_end_ms"]
    for i,(evt,old_24) in enumerate(zip(events,proxies)):
        t=evt["observable_ms"]
        if old_24["priority_visible_ms"]!=t:
            raise ValueError("STAGE113_ORIGINAL_EVENT_TO_PRICE_CLOCK_DRIFT")
        hz={str(h):price_horizon(t,h,end,lookup) for h in HORIZONS}
        now=hz["1440"]
        if old_24["status"]=="PRICE_ONLY_PROXY_COMPLETE":
            if (now["status"]!="COMPLETE_PRICE_ONLY" or
                    Decimal(now["gross_pct"])!=Decimal(old_24["gross_24h_price_pct"])):
                raise ValueError("STAGE113_STAGE111_24H_GROSS_OFFICIAL_SHA_MISMATCH")
        elif now["status"]=="COMPLETE_PRICE_ONLY":
            raise ValueError("STAGE113_RECALCULATED_24H_WAS_PRIORLY_CENSORED")
        obs.append({
            "mode":"FIRST" if i==0 else "REPEAT",
            "priority_ordinal":i+1,
            "event_local_id":evt["event_id"],
            "scoped_research_id":x["date"]+":"+x["symbol"]+":"+evt["event_id"],
            "observable_ms":t,
            "horizons":hz,
        })
    return {
        "date":x["date"],"symbol":x["symbol"],"identity":x["identity"],
        "D0_FIRST_UTC":x["D0_FIRST_UTC"],
        "original_D1_FIRST_UTC":x["D1_FIRST_UTC"],
        "source_status":status,
        "publisher_1m_sha_receipts":original["source_days_downloaded_verified_1m"],
        "original_priorities":len(events),
        "horizon_episodes":obs,
        "user_notional":"UNSPECIFIED",
        "real_executable_net_pnl":"UNKNOWN",
        "new_strategy_model":"NONE",
    }


def selftest():
    D=Decimal
    t=1_740_000_000_000
    bars={}
    for i in range(1440):
        px=D("100")+D(i)/1000
        bars[t+i*MIN]=(t+i*MIN,D("100"),px,D("90"),px,D("1000"),1)
    for h in HORIZONS:
        row=price_horizon(t,h,t+1440*MIN,bars)
        assert row["status"]=="COMPLETE_PRICE_ONLY"
        assert row["holding_minutes"]==h
        assert Decimal(row["gross_pct"])>=0
    assert price_horizon(t,1440,t+60*MIN,bars)["status"]=="CENSORED_FROZEN_7DAY_BOUNDARY"
    missing=dict(bars)
    missing.pop(t+2*MIN)
    assert price_horizon(t,5,t+1440*MIN,missing)["status"]=="CENSORED_MISSING_1M"
    zero=dict(bars)
    z=zero[t+4*MIN]
    zero[t+4*MIN]=(z[0],z[1],z[2],z[3],z[4],D(0),0)
    assert price_horizon(t,5,t+1440*MIN,zero)["status"]=="CENSORED_UNTRADED_ENTRY_OR_EXIT"
    print("STAGE113_FROZEN_HORIZON_5_60_360_1440_CAUSAL_EXIT_CLOCK_SELFTEST_PASS")


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--selftest",action="store_true")
    ap.add_argument("--date")
    ap.add_argument("--shard",type=int)
    ap.add_argument("--workers",type=int,default=3)
    ap.add_argument("--out",type=Path)
    args=ap.parse_args()
    if args.selftest:
        selftest()
        return
    if not args.date or args.shard is None or args.out is None:
        ap.error("--date --shard --out required")
    if args.workers not in range(1,5):
        raise ValueError("STAGE113_WORKERS")
    source,previous,reference=frozen()
    selected=old.shard_rows(args.date,args.shard,source)
    rows=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        jobs={pool.submit(one_case,x,previous.get((x["date"],x["symbol"])),
                          reference[(x["date"],x["symbol"])]):x for x in selected}
        for task in concurrent.futures.as_completed(jobs):
            x=jobs[task]
            try:
                result=task.result()
            except Exception as exc:
                raise RuntimeError("STAGE113_CASE_READ_ERROR "+
                                   x["date"]+" "+x["symbol"]+" "+str(exc)) from exc
            rows.append(result)
            print("STAGE113_HORIZON_CASE "+
                  x["date"]+" "+x["symbol"]+" "+result["source_status"],flush=True)
    if len(rows)!=len(selected):
        raise ValueError("STAGE113_SHARD_CASE_LOSS")
    packet={
        "schema":SCHEMA,"date":args.date,"shard":args.shard,
        "source_stage112_git_blob":PIN112,
        "source_stage111_aggregate_git_blob":stage112.PIN_AGG_BLOB,
        "original_D0_population":519,
        "fixed_minutes":list(HORIZONS),
        "source_exposed_history_only":True,
        "rows":sorted(rows,key=lambda q:q["symbol"]),
        "monster_deployment":"NO_GO",
    }
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(packet,indent=2,sort_keys=True)+"\n")
    print("STAGE113_OFFICIAL_HORIZON_SHARD "+
          json.dumps({"date":args.date,"shard":args.shard,
                      "original_cases":len(rows),
                      "original_priorities":sum(r["original_priorities"] for r in rows)}))


if __name__=="__main__":
    main()
