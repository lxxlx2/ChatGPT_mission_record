#!/usr/bin/env python3
"""Stage29 MONSTER meme WATCH 3min burst-vs-net cost outcomes diagnostic.

Historical discovery cohort only: source dates and all returns were already
exposed, no feature tuning / buy strategy permission. Exactly 36 publisher-SHA
verified Stage26 originals loaded through Stage27 strict artifact verifier.
"""
import argparse
import collections
import json
import statistics
from datetime import datetime, timezone
from pathlib import Path

try:
    import monster_v4_stage27_shared_queue_cash_ledger as source
except ImportError:
    from scripts import monster_v4_stage27_shared_queue_cash_ledger as source

CONTRACT=source.EVIDENCE/"monster_stage29_frozen_watch_burst_vs_24h_net_profit_diagnostic_20261011.json"
BINS=("ISOLATED_1","LOCAL_2_TO_7","BURST_8PLUS")
COSTS=(20,100)

def contract():
    m=json.loads(CONTRACT.read_text(encoding="utf-8"))
    if m["schema"]!="MONSTER_STAGE29_FROZEN_MME_STANDALONE_VS_SONIC_BURST_RETURNS_DIAGNOSTIC_V1" or (
        m["expected_source_attempts"],m["verified_complete"],m["watch_events"])!=(4548,2719,1132):
        raise ValueError("STAGE29_CONTRACT_CHANGED")
    return m

def bucket(n):
    if n==1:return BINS[0]
    if 2<=n<=7:return BINS[1]
    if n>=8:return BINS[2]
    raise ValueError("STAGE29_ZERO_WATCH_TICK")

def make_event_cases(rows):
    """Return ALL WATCHs; no random sampling, post-hoc winner selection or exits filled."""
    timeline=[]
    for case in rows:
        if case["status"]!="COMPLETE_168H_CONTINUOUS_V4":
            raise ValueError("STAGE29_NOT_COMPLETE_SOURCE")
        symbol,day=case["symbol"],case["date"]
        w=case["continuous"]["watch_utcs"]
        px=case["continuous"]["trade_proxies"]
        if len(w)!=len(px) or case["continuous"]["watch_count"]!=len(w):
            raise ValueError("STAGE29_SOURCE_WATCH_TRADE_ALIGNMENT_CHANGED")
        gt=case["labels"]["2x"]
        for watch,trade in zip(w,px):
            if watch!=trade["watch_utc"]:
                raise ValueError("STAGE29_MISMATCHED_TRADE_WATCH")
            lead=None
            if gt["gross_hourly_high_gt"]:
                t=source.previous.utc(gt["real_1m_cross_utc"])
                observed=source.previous.utc(watch)
                lead=round((t-observed).total_seconds()/60,6)
            case_data={"date":day,"symbol":symbol,"watch_utc":watch,
                "gross_high_2x_in_frozen_168h":gt["gross_hourly_high_gt"],
                "minutes_until_first_2x_if_valid":lead,
                "cost_proxies":{}}
            for cost in COSTS:
                p=trade[f"proxy_{cost}bps"]
                if p is None:
                    case_data["cost_proxies"][str(cost)]={"status":"SKIP_SAME_SYMBOL_24H_CAPITAL_OCCUPIED"}
                else:
                    case_data["cost_proxies"][str(cost)]={
                        "status":p["status"],"net_pct":p.get("net_pct")}
            timeline.append(case_data)
    counts=collections.Counter((r["date"],r["watch_utc"]) for r in timeline)
    for r in timeline:
        if not r["watch_utc"].endswith("Z"):
            raise ValueError("STAGE29_WATCH_TIMEZONE_NOT_UTC")
        size=counts[(r["date"],r["watch_utc"])]
        r["same_3m_watch_count"]=size
        r["bucket"]=bucket(size)
    if len(set((r["date"],r["symbol"],r["watch_utc"]) for r in timeline))!=len(timeline):
        raise ValueError("STAGE29_DUPLICATE_SOURCE_WATCH")
    return sorted(timeline,key=lambda x:(x["date"],x["watch_utc"],x["symbol"]))

def arm_stats(events,cost):
    stat=collections.Counter()
    prices=[]
    for e in events:
        p=e["cost_proxies"][str(cost)]
        status=p["status"]
        stat[status]+=1
        if status=="PRICE_PROXY_ONLY":
            v=p["net_pct"]
            if not isinstance(v,(int,float)):
                raise ValueError("STAGE29_VALID_NET_RETURN_MISSING")
            prices.append(v)
    n=len(events)
    if sum(stat.values())!=n:raise ValueError("STAGE29_EVENTS_MISSING")
    return {"watch_count":n,
            "proxy_evaluable":len(prices),
            "wins":sum(x>0 for x in prices),
            "losses":sum(x<0 for x in prices),
            "source_censored_excluding_overlap":sum(v for s,v in stat.items() if s.startswith("CENSORED_")),
            "same_symbol_24h_overlap_skip":stat["SKIP_SAME_SYMBOL_24H_CAPITAL_OCCUPIED"],
            "source_proxy_status_counts":dict(stat),
            "median_net_pct":round(statistics.median(prices),6) if prices else None,
            "mean_net_pct":round(statistics.mean(prices),6) if prices else None,
            "independent_30USDT_proxy_PnL_sum":round(sum(x*0.3 for x in prices),6),
            "real_L2_execution_verified":False}

def summarize(rows):
    events=make_event_cases(rows)
    if len(events)!=1132:raise ValueError("STAGE29_NOT_ALL_ORIGINAL_1132")
    watch_case_count=sum(x["continuous"]["watch_count"]>0 for x in rows)
    day_map={}
    group_stats={}
    for b in BINS:
        members=[e for e in events if e["bucket"]==b]
        byday={}
        for day in sorted({r["date"] for r in rows}):
            matching=[e for e in members if e["date"]==day]
            byday[day]={str(c):arm_stats(matching,c) for c in COSTS}
        group_stats[b]={
            "events":len(members),
            "WATCH_GROSS_2X_DATE_SYMBOL_EVENTS":sum(x["gross_high_2x_in_frozen_168h"] for x in members),
            "WATCH_2X_BEFORE_CROSS_EVENTS":sum(x["minutes_until_first_2x_if_valid"] is not None and x["minutes_until_first_2x_if_valid"]>=0 for x in members),
            "WATCH_2X_WITHIN_6H_BEFORE_CROSS_EVENTS":sum(x["minutes_until_first_2x_if_valid"] is not None and 0<=x["minutes_until_first_2x_if_valid"]<=360 for x in members),
            "by_cost_bps":{str(c):arm_stats(members,c) for c in COSTS},
            "by_original_date_and_cost":byday,
            "positive_median_calendar_dates":sum(v["20"]["median_net_pct"] is not None and v["20"]["median_net_pct"]>0 for v in byday.values()),
            "negative_median_calendar_dates":sum(v["20"]["median_net_pct"] is not None and v["20"]["median_net_pct"]<0 for v in byday.values())
        }
    total20=arm_stats(events,20);total100=arm_stats(events,100)
    if (total20["proxy_evaluable"],total20["wins"],total20["losses"])!=(549,206,343):
        raise ValueError("STAGE29_STAGE26_GENUINE_549_206_343_OUTCOME_DRIFT")
    if total20["same_symbol_24h_overlap_skip"]!=326 or total20["source_censored_excluding_overlap"]!=257:
        raise ValueError("STAGE29_UNCHANGED_CENSORING_326_257_FAILED")
    n=collections.Counter(r["same_3m_watch_count"] for r in events)
    peaks=[{"UTC":dt,"calendar_date":day,"simultaneous_distinct_symbols":count,
        "symbols":[r["symbol"] for r in events if r["date"]==day and r["watch_utc"]==dt]}
        for (day,dt),count in sorted(collections.Counter(
            (r["date"],r["watch_utc"]) for r in events).items(),
            key=lambda x:(-x[1],x[0][0],x[0][1]))[:10]]
    huge=[r for r in events if r["watch_utc"]=="2026-02-06T00:36:00Z"]
    if len(huge)!=98:
        raise ValueError("STAGE29_FEB2026_ACTUAL_98_POLL_SOURCE_DRIFT")
    return {"schema":"MONSTER_STAGE29_EXPOSED_ALL1132_WATCH_REAL_PRICE_PROXY_NO_STRATEGY_TUNING_V1",
         "source_original_36_ZIP_AND_JSON_SHA256_verified":True,
         "all_original_758x6_source_attempts":4548,"source_verified_complete":2719,
         "sample_exposure":"EXPOSED_RETROSPECTIVE_DIAGNOSTIC_ONLY",
         "watch_symbol_dates":watch_case_count,
         "watch_event_count":len(events),
         "all_20bps":total20,"all_100bps":total100,
         "original_3m_tick_concurrent_watch_histogram":dict(n),
         "groups":group_stats,
         "largest_ten_same_poll_bursts":peaks,
         "2026_02_06T0036_all_98_watch_event_audit":huge,
         "sample_source_trades_include_future_prices_only_in_outcome_label":True,
         "not_new_unseen_holdout":True,
         "not_buy_signal":True,"independent_other_AI_review":"NOT_DONE",
         "deployment":"NO_GO","real_gmail":"OFF","trading":"NO_GO","frank":"UNCHANGED"}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--stage26-original-zips",type=Path,nargs=36,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    contract()
    original=source.original_cases(a.stage26_original_zips)
    if len(original)!=2719:
        raise SystemExit("STAGE29_NOT_ALL_2719_VERIFIED_SOURCE_CASES")
    result=summarize(original)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    compact={k:v for k,v in result.items() if k not in ("groups","largest_ten_same_poll_bursts","2026_02_06T0036_all_98_watch_event_audit","original_3m_tick_concurrent_watch_histogram")}
    compact["groups"]={k:{kk:vv for kk,vv in val.items() if kk!="by_original_date_and_cost"} for k,val in result["groups"].items()}
    print("STAGE29_DIAGNOSTIC_JSON "+json.dumps(compact,sort_keys=True),flush=True)
if __name__=="__main__":
    main()
