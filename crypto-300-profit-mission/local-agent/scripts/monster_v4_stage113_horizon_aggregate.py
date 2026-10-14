#!/usr/bin/env python3
"""Stage113 original519 5/60/360/1440 minute price-only horizon diagnostics."""
from __future__ import annotations
import argparse
from collections import Counter,defaultdict
from decimal import Decimal
import json
from pathlib import Path
from statistics import median

try:
    import monster_v4_stage113_fixed_horizons_official as replay
except ImportError:
    from scripts import monster_v4_stage113_fixed_horizons_official as replay

SCHEMA="MONSTER_STAGE113_ALL519_FIXED_FOUR_HORIZON_PRICE_ONLY_V1"
GROSS="gross_pct"


def profile(nums):
    vals=sorted(nums)
    return {
        "complete_price_observations":len(vals),
        "gross_median_pct":str(median(vals)) if vals else None,
        "positive":sum(x>0 for x in vals),
        "nonpositive":sum(x<=0 for x in vals),
        "loss20_or_worse":sum(x<=-20 for x in vals),
        "hypothetical_20bps_each_side_gross_median_pct":
            str(median([((1+x/100)*(Decimal("0.998")/
                     Decimal("1.002"))-1)*100 for x in vals])) if vals else None,
        "price_only_not_executable":True,
    }


def audit(packets:list[dict]):
    rows, prior, stage112 = replay.frozen()
    expected={(z["date"],z["symbol"]) for z in rows}
    expected_shards={(date,shard) for date in replay.old.DATES for shard in range(4)}
    seen=set()
    all_cases=[]
    if len(packets)!=24:
        raise ValueError("STAGE113_EXACT_24_ARCHIVED_SOURCE_SHARDS_REQUIRED")
    for p in packets:
        k=p["date"],p["shard"]
        if (p["schema"]!=replay.SCHEMA or k in seen or
                p["source_stage112_git_blob"]!=replay.PIN112 or
                p["source_stage111_aggregate_git_blob"]!=replay.stage112.PIN_AGG_BLOB
                or p["original_D0_population"]!=519
                or p["fixed_minutes"]!=list(replay.HORIZONS)):
            raise ValueError("STAGE113_FROZEN_SHARD_OR_SCHEMA_MISMATCH")
        seen.add(k)
        selected=replay.old.shard_rows(p["date"],p["shard"],rows)
        if {(z["date"],z["symbol"]) for z in selected} != {
                (z["date"],z["symbol"]) for z in p["rows"]}:
            raise ValueError("STAGE113_LOST_OR_CROSS_SHARD_CASE")
        all_cases.extend(p["rows"])
    if seen!=expected_shards or len(all_cases)!=519:
        raise ValueError("STAGE113_INCOMPLETE_REAL_ORIGINAL_COHORT")
    if {(z["date"],z["symbol"]) for z in all_cases}!=expected:
        raise ValueError("STAGE113_ORIGINAL_CASE_DRIFT")

    values=defaultdict(list)
    common_24=defaultdict(list)
    censored=Counter()
    bydate=Counter()
    bysource=Counter()
    case_summary=[]
    original_priorities=0
    for case in sorted(all_cases,key=lambda x:(x["date"],x["symbol"])):
        k=case["date"],case["symbol"]
        source=stage112[k]
        if (case["identity"]!=source["identity"] or
                case["original_priorities"]!=source["priorities"] and
                case["source_status"]=="EXPIRED"):
            raise ValueError("STAGE113_EVENT_COHORT_CHANGED")
        episodes=case["horizon_episodes"]
        if case["original_priorities"]!=len(episodes):
            raise ValueError("STAGE113_EVENT_RECORD_LOSS")
        original_priorities+=len(episodes)
        bydate[case["date"]]+=len(episodes)
        bysource[case["source_status"]]+=1
        bycase=defaultdict(list)
        for i,episode in enumerate(episodes):
            mode="FIRST" if i==0 else "REPEAT"
            if episode["mode"]!=mode or episode["priority_ordinal"]!=i+1:
                raise ValueError("STAGE113_EPISODE_ORDINAL_DRIFT")
            horizon=episode["horizons"]
            if set(horizon)!={str(h) for h in replay.HORIZONS}:
                raise ValueError("STAGE113_DIFFERENT_HORIZON_CANDIDATES")
            for h in replay.HORIZONS:
                rec=horizon[str(h)]
                if rec["holding_minutes"]!=h:
                    raise ValueError("STAGE113_HOLDING_INTERVAL_CHANGED")
                name=f"{mode}_{h}"
                if rec["status"]=="COMPLETE_PRICE_ONLY":
                    v=Decimal(rec[GROSS])
                    if not v.is_finite() or Decimal(rec["entry_next_1m_open"])<=0:
                        raise ValueError("STAGE113_BAD_OFFICIAL_GROSS_ENTRY")
                    values[name].append(v)
                    values[f"ALL_{h}"].append(v)
                    bycase[name].append(v)
                else:
                    if rec[GROSS] is not None:
                        raise ValueError("STAGE113_CENSORED_BUT_RETURN_PRESENT")
                    censored[name]+=1
                    censored[f"ALL_{h}"]+=1
            if horizon["1440"]["status"]=="COMPLETE_PRICE_ONLY":
                for h in replay.HORIZONS:
                    short=horizon[str(h)]
                    if short["status"]=="COMPLETE_PRICE_ONLY":
                        v=Decimal(short[GROSS])
                        common_24[f"{mode}_{h}"].append(v)
                        common_24[f"ALL_{h}"].append(v)
        case_summary.append({
            "date":case["date"],"symbol":case["symbol"],
            "identity":case["identity"],
            "D1_PRESENT":case["original_D1_FIRST_UTC"] is not None,
            "source_status":case["source_status"],
            "source_days_publisher_sha":case["publisher_1m_sha_receipts"],
            "priority_count":len(episodes),
            "by_horizon_first_and_repeat_median_price_only_pct":{
                key:str(median(vals)) for key,vals in sorted(bycase.items())},
        })

    if bysource["EXPIRED"]!=519 or original_priorities!=740:
        raise ValueError("STAGE113_ORIGINAL519_CONTIGUOUS_SOURCE_OR740_EPISODES_INCOMPLETE")
    if len(values["FIRST_1440"])!=237 or len(values["REPEAT_1440"])!=361:
        raise ValueError("STAGE113_SOURCE_STAGE112_FIRST_REPEAT_COMPLETE24_DRIFT")
    old_first=replay.stage112.frozen_aggregate()
    if len(values["ALL_1440"])!=old_first["preregistered_gates"][
        "G4_price_only_only"]["complete_24h_price_proxy_count"]:
        raise ValueError("STAGE113_STAGE111_598_PRICE_ONLY_COUNT_DRIFT")
    if str(median(values["ALL_1440"]))!=old_first[
        "preregistered_gates"]["G4_price_only_only"]["price_only_median_gross_pct"]:
        raise ValueError("STAGE113_ORIGINAL_24H_GROSS_MEDIAN_DRIFT")
    if len(values["ALL_1440"])!=598:
        raise ValueError("STAGE113_24H_598_MISSING")

    result={}
    same24={}
    for mode in ("FIRST","REPEAT","ALL"):
        result[mode]={}
        same24[mode]={}
        for h in replay.HORIZONS:
            key=f"{mode}_{h}"
            result[mode][str(h)]={"complete":profile(values[key]),
                                  "censored":censored[key]}
            same24[mode][str(h)]=profile(common_24[key])
    return {
        "schema":SCHEMA,
        "frozen_research_horizons_minutes":list(replay.HORIZONS),
        "source_stage112_git_blob":replay.PIN112,
        "source_stage111_git_blob":replay.stage112.PIN_AGG_BLOB,
        "all_original_D0_cases":519,
        "all_original_first_and_repeat_priority_events":original_priorities,
        "first_and_repeat_for_each_fixed_horizon":result,
        "same_24h_complete_population_for_all_horizons":same24,
        "source_case_statuses":dict(bysource),
        "original_anchor_total_priority_by_date":dict(sorted(bydate.items())),
        "case_level_price_summary":case_summary,
        "censored_not_assumed_losses":True,
        "no_grid_or_best_holding_period_selection":True,
        "research_exposed_historical_not_OOS":True,
        "real_orderbook_impact_notional_and_net":"UNKNOWN",
        "new_strategy_pass":"NOT_EVALUATED",
        "monster_deployment":"NO_GO",
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--artifact-dir",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    packets=[]
    for file in sorted(args.artifact_dir.rglob("monster-stage113-*.json")):
        p=json.loads(file.read_text())
        if p.get("schema")==replay.SCHEMA:
            packets.append(p)
    result=audit(packets)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("STAGE113_ALL519_CAUSAL_HORIZON_DECISION "+
          json.dumps({k:v for k,v in result.items() if k!="case_level_price_summary"},sort_keys=True))


if __name__=="__main__":
    main()
