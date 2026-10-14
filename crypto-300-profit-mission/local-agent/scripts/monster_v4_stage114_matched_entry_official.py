#!/usr/bin/env python3
"""Monster Stage114: fixed, source-locked original519 D0/D1/PRIORITY price parity.

Read-only exposed historical diagnostics. No monitor, no trading, no Gmail.
"""
from __future__ import annotations

import argparse
import concurrent.futures
from decimal import Decimal
import json
from pathlib import Path

try:
    import monster_v4_stage113_fixed_horizons_official as s113
    import monster_v4_stage113_horizon_aggregate as aggregate113
except ImportError:
    from scripts import monster_v4_stage113_fixed_horizons_official as s113
    from scripts import monster_v4_stage113_horizon_aggregate as aggregate113

old=s113.old
MIN=60_000
HORIZONS=(5,1440)
SCHEMA="MONSTER_STAGE114_ALL519_D0_D1_FIRST_PRIORITY_ENTRY_PRICE_PARITY_OFFICIAL1M_V1"
PIN113="b5e56d4ec50cfb34ace39303e96bbc30e894a5d1"


def frozen():
    source, old_d1, stage112=s113.frozen()
    p=s113.stage112.E/"monster_stage113_real519_5_60_360_1440m_actual.json"
    raw=p.read_bytes()
    if s113.stage112.git_blob(raw)!=PIN113:
        raise ValueError("STAGE114_STAGE113_IMMUTABLE_GIT_BLOB_DRIFT")
    stages=json.loads(raw)
    if (stages["schema"]!=aggregate113.SCHEMA or
            stages["all_original_D0_cases"]!=519 or
            stages["all_original_first_and_repeat_priority_events"]!=740 or
            stages["first_and_repeat_for_each_fixed_horizon"]["FIRST"]["1440"]
            ["complete"]["complete_price_observations"]!=237):
        raise ValueError("STAGE114_STAGE113_RESEARCH_POPULATION_DRIFT")
    keyed113={(r["date"],r["symbol"]):r for r in stages["case_level_price_summary"]}
    if len(keyed113)!=519:
        raise ValueError("STAGE114_STAGE113_CASE_LEVEL_POPULATION_DRIFT")
    return source,old_d1,stage112,keyed113


def valid_entry(t, end, lookup):
    """Return verified research open; no actual execution assumption."""
    if t is None or t>=end:
        return None
    bar=lookup.get(t)
    if bar is None or bar[1]<=0 or bar[5]<=0 or bar[6]<=0:
        return None
    return bar[1]


def price_rel(new, old):
    return str((new/old-1)*Decimal(100)) if new is not None and old is not None else None


def no_fill_horizons(entry_t,anchor_end,lookup):
    if entry_t is None:
        return {str(h):{"status":"NO_HISTORICAL_SIGNAL","gross_pct":None,
                        "holding_minutes":h} for h in HORIZONS}
    return {str(h):s113.price_horizon(entry_t,h,anchor_end,lookup) for h in HORIZONS}


def same_exit_earlier(early_t, later_t, h, end, lookup):
    if early_t is None or later_t is None or early_t > later_t:
        return {"status":"NOT_EARLIER_OR_NO_SIGNAL"}
    first=valid_entry(early_t,end,lookup)
    later=s113.price_horizon(later_t,h,end,lookup)
    if first is None or later["status"]!="COMPLETE_PRICE_ONLY":
        return {"status":"CENSORED_ENTRY_OR_COMMON_EXIT"}
    close=Decimal(later["exit_completed_last_1m_close"])
    later_entry=Decimal(later["entry_next_1m_open"])
    if not (0<first and 0<later_entry and 0<close):
        raise ValueError("STAGE114_NONPOSITIVE_COMMON_EXIT")
    early_return=(close/first-1)*100
    delayed_return=(close/later_entry-1)*100
    return {
        "status":"COMPLETE_PRICE_ONLY",
        "common_exit_anchored_to_first_priority_minutes":h,
        "earlier_return_pct":str(early_return),
        "priority_return_pct":str(delayed_return),
        "earlier_minus_priority_return_pct_points":str(early_return-delayed_return),
        "real_net":"UNKNOWN",
    }


def one_case(x,old_d1,ref112,ref113,reader=None):
    if reader is None:
        reader=old.publisher.verified_1m_day
    captured={}
    def inspect(symbol,day):
        bars,receipt=reader(symbol,day)
        captured[day.isoformat()]=bars
        return bars,receipt
    archive=s113.one_case(x,old_d1,ref112,reader=inspect)
    if ((archive["date"],archive["symbol"])!=(x["date"],x["symbol"]) or
        ref113["identity"]!=x["identity"] or
        ref113["priority_count"]!=archive["original_priorities"]):
        raise ValueError("STAGE114_FIRST_PRIORITY_113_CASE_IDENTITY_DRIFT")
    if archive["source_status"]!="EXPIRED":
        # Preserve the original source status rather than calling zero profit.
        raise ValueError("STAGE114_HISTORIC_SOURCE_NOT_FULL_ORIGINAL_ANCHOR")
    lookup={bar[0]:bar for arr in captured.values() for bar in arr}
    end=old.utc_ms(x["date"]+"T06:00:00Z")+7*86_400_000
    d0=old.utc_ms(x["D0_FIRST_UTC"])
    d1=old.utc_ms(x["D1_FIRST_UTC"]) if x["D1_FIRST_UTC"] is not None else None
    if d0>=end or (d1 is not None and d1<d0):
        raise ValueError("STAGE114_ORIGINAL_SIGNAL_TIME_INVALID")
    episodes=archive["horizon_episodes"]
    p=episodes[0]["observable_ms"] if episodes else None
    if p is not None and not d0<p<end:
        raise ValueError("STAGE114_FIRST_PRIORITY_BAD_ORIGINAL_CLOCK")
    d0_t=d0+MIN
    d1_t=d1+MIN if d1 is not None else None
    p_latency_t=p+MIN if p is not None else None
    timeline={"D0":d0_t,"D1":d1_t,"PRIORITY":p,
              "PRIORITY_PLUS_1M_LATENCY":p_latency_t}
    entries={name:valid_entry(t,end,lookup) for name,t in timeline.items()}
    all_horizons={name:no_fill_horizons(t,end,lookup)
                  for name,t in timeline.items()}

    # This is a literal immutable cross-check on Stage113 for FIRST PRIORITY.
    if p is not None:
        prior=episodes[0]["horizons"]
        for h in HORIZONS:
            now=all_horizons["PRIORITY"][str(h)]
            prev=prior[str(h)]
            if (now["status"]=="COMPLETE_PRICE_ONLY") != (
                prev["status"]=="COMPLETE_PRICE_ONLY"):
                raise ValueError("STAGE114_PRIOR_FIRST_PRIORITY_HORIZON_STATUS_CHANGED")
            if now["status"]=="COMPLETE_PRICE_ONLY":
                if Decimal(now["gross_pct"])!=Decimal(prev["gross_pct"]):
                    raise ValueError("STAGE114_STAGE113_FIRST_PRIORITY_RETURN_DRIFT")
    raw_gross={name:{str(h):row[str(h)]["gross_pct"] for h in HORIZONS}
               for name,row in all_horizons.items()}
    same={}
    if p is not None:
        for label,t in (("D0",d0_t),("D1",d1_t)):
            same[label]={str(h):same_exit_earlier(t,p,h,end,lookup)
                         for h in HORIZONS}

    return {
        "date":x["date"],"symbol":x["symbol"],"identity":x["identity"],
        "D0_FIRST_UTC":x["D0_FIRST_UTC"],
        "original_D1_FIRST_UTC":x["D1_FIRST_UTC"],
        "original_D0_early5_2x_EVAL_ONLY":bool(x["D0_at_least_5m_before_2x"]),
        "original_D1_early5_2x_EVAL_ONLY":bool(x["D1_at_least_5m_before_2x"]),
        "first_priority_observable_ms":p,
        "original_first_priority_ordinal":1 if p is not None else None,
        "original_priority_count":len(episodes),
        "original_first_2x_HIGH_EVAL_ONLY":x["true_first_2x_HIGH_UTC_EVALUATION_ONLY"],
        "original_7d_anchor_end_ms":end,
        "signal_proxy_entry_ms":timeline,
        "signal_proxy_entry_open":{name:str(v) if v is not None else None
                                   for name,v in entries.items()},
        "D0_to_PRIORITY_minutes":(p-d0)//MIN if p is not None else None,
        "D1_to_PRIORITY_minutes":(p-d1)//MIN if p is not None and d1 is not None else None,
        "D1_chronology":("NONE" if d1 is None else
                         "NO_PRIORITY" if p is None else
                         "D1_BEFORE_PRIORITY" if d1<p else
                         "D1_EQUALS_PRIORITY" if d1==p else
                         "D1_AFTER_PRIORITY"),
        "priority_vs_D0_entry_pct":price_rel(entries["PRIORITY"],entries["D0"]),
        "priority_vs_D1_entry_pct":(price_rel(entries["PRIORITY"],entries["D1"])
              if d1 is not None and p is not None and d1<=p else None),
        "latency_plus_1m_vs_original_priority_open_pct":
            price_rel(entries["PRIORITY_PLUS_1M_LATENCY"],entries["PRIORITY"]),
        "frozen_5m_24h_entry_horizon_price_proxies":all_horizons,
        "frozen_5m_24h_only_gross_comparison":raw_gross,
        "common_exit_first_priority_5m_24h_earlier_entry_comparison":same,
        "official_publisher_1m_sha_receipts":archive["publisher_1m_sha_receipts"],
        "source_status":archive["source_status"],
        "history_exposed_not_OOS":True,
        "execution_net_pnl":"UNKNOWN",
        "monster_deployment":"NO_GO",
    }


def selftest():
    D=Decimal
    t=1_740_000_000_000
    rows={}
    for i in range(1441):
        o=D(100+i)
        rows[t+i*MIN]=(t+i*MIN,o,o,D(1),o,D(100),1)
    assert valid_entry(t,t+1441*MIN,rows)==D(100)
    assert valid_entry(t,t,rows) is None
    assert price_rel(D(120),D(100))=="20.0"
    common=same_exit_earlier(t,t+MIN,5,t+1441*MIN,rows)
    assert common["status"]=="COMPLETE_PRICE_ONLY"
    assert Decimal(common["earlier_minus_priority_return_pct_points"])>0
    assert same_exit_earlier(t+2*MIN,t+MIN,5,t+1441*MIN,rows)["status"]=="NOT_EARLIER_OR_NO_SIGNAL"
    assert no_fill_horizons(None,t+1441*MIN,rows)["5"]["status"]=="NO_HISTORICAL_SIGNAL"
    assert no_fill_horizons(t,t+5*MIN,rows)["1440"]["status"]=="CENSORED_FROZEN_7DAY_BOUNDARY"
    print("STAGE114_NEXT_OPEN_ASOF_MATCHED_EXIT_POSITIVE_NEGATIVE_CENSORING_SELFTEST_PASS")


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
        ap.error("--date, --shard, --out required")
    if args.workers not in range(1,5):
        raise ValueError("STAGE114_WORKERS")
    allx,prior,ref112,ref113=frozen()
    source=old.shard_rows(args.date,args.shard,allx)
    actual=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        jobs={pool.submit(one_case,x,prior.get((x["date"],x["symbol"])),
                           ref112[(x["date"],x["symbol"])],
                           ref113[(x["date"],x["symbol"])]):x for x in source}
        for fut in concurrent.futures.as_completed(jobs):
            x=jobs[fut]
            try:
                result=fut.result()
            except Exception as exc:
                raise RuntimeError("STAGE114_SOURCE_CASE_FAILED "+
                                   x["date"]+" "+x["symbol"]+" "+str(exc)) from exc
            actual.append(result)
            print("STAGE114_OFFICIAL_1M_ASOF "+
                  x["date"]+" "+x["symbol"]+" "+result["D1_chronology"],flush=True)
    if len(actual)!=len(source):
        raise ValueError("STAGE114_LOST_ORIGINAL_CASE")
    output={
        "schema":SCHEMA,"date":args.date,"shard":args.shard,
        "source_stage113_git_blob":PIN113,
        "source_stage112_git_blob":s113.PIN112,
        "original_D0_cases":519,"original_D1_cases":305,
        "historical_not_OOS":True,
        "rows":sorted(actual,key=lambda x:x["symbol"]),
        "real_net":"UNKNOWN","monster_deployment":"NO_GO",
    }
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(output,indent=2,sort_keys=True)+"\n")
    print("STAGE114_IMMUTABLE_SOURCE_SHARD "+
          json.dumps({"date":args.date,"shard":args.shard,"n":len(actual)},sort_keys=True))


if __name__=="__main__":
    main()
