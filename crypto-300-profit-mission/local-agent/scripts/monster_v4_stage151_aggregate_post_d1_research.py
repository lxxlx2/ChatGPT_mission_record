#!/usr/bin/env python3
"""Stage151 all305 source-locked cohort analysis, exposed historical diagnostic."""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
from decimal import Decimal
import json
from pathlib import Path
from statistics import median

import monster_v4_stage151_post_d1_pullback_reclaim as stage151

SCHEMA="MONSTER_STAGE151_ALL305_PREREG_HISTORICAL_EXPOSED_ECONOMICS_V1"
SHARD_SCHEMA=stage151.SCHEMA
DATES=("2025-01-30","2025-06-02","2025-08-01","2025-10-02",
       "2026-06-21","2026-07-28")
STATES=("PULLBACK_RECLAIM_CONFIRMED_PRICE_ONLY",
        "NO_PULLBACK_WITHIN_120M","PULLBACK_NO_RECLAIM",
        "CONFIRMED_NEXT_OPEN_NO_TRADES")


def groups(rows):
    r=list(rows)
    state_counts=Counter(x["preregistered_decision"]["state"] for x in r)
    if any(k not in STATES for k in state_counts):
        raise ValueError("STAGE151_UNKNOWN_FROZEN_MODEL_STATE")
    result={"n":len(r), "states":dict(state_counts)}
    original=[Decimal(x["baseline_Stage88_D1_direct_24h_gross_price_only_pct"])
              for x in r]
    result["baseline_Stage88_original_D1_direct_all_24h"]={
        "n":len(original),
        "gross_pct_median":str(median(original)) if original else None,
        "positive":sum(x>0 for x in original),
        "loss_20pct_or_worse":sum(x<=-20 for x in original)}
    for h in ("360","1440"):
        valid=[]
        fee=[]
        mae=[]
        for x in r:
            path=x["entry_and_exit_fixed_horizon_price_only"].get(h)
            if path and path["status"]=="COMPLETE_UNFILLED_PRICE_PROXY":
                valid.append(Decimal(path["gross_pct"]))
                fee.append(Decimal(path["illustrative_20bps_each_side_pct"]))
                mae.append(Decimal(path["adverse_LOW_proxy_pct_not_stop_fill"]))
        result["confirmed_"+h+"m_complete_unfilled_price_proxy"]={
            "n":len(valid),
            "gross_pct_median":str(median(valid)) if valid else None,
            "gross_positive":sum(x>0 for x in valid),
            "gross_loss_20pct_or_worse":sum(x<=-20 for x in valid),
            "illustrative_20bps_each_side_pct_median":
                str(median(fee)) if fee else None,
            "adverse_LOW_proxy_pct_median":str(median(mae)) if mae else None,
            "notional_and_true_executable_net":"UNKNOWN",
        }
    result["not_entered_is_NOT_zero_pnl"]=True
    return result


def aggregate(shards, original):
    if len(shards)!=24:
        raise ValueError("STAGE151_EXPECTED_24_ORIGINAL_DATE_SHARDS")
    if len(original)!=305 or len({(x["date"],x["symbol"]) for x in original})!=305:
        raise ValueError("STAGE151_ORIGINAL305_INVALID")
    expected={(x["date"],x["symbol"]):x for x in original}
    seen_shards=set()
    all_rows=[]
    for shard in shards:
        key=(shard.get("date"),shard.get("shard"))
        if (key[0] not in DATES or type(key[1]) is not int
                or key[1] not in range(4) or key in seen_shards):
            raise ValueError("STAGE151_DUPLICATE_OR_INVALID_SHARD")
        seen_shards.add(key)
        if (shard.get("schema")!=SHARD_SCHEMA or
                shard.get("original_D1_total_expected")!=305 or
                shard.get("original_D0_total_reference_untouched")!=519 or
                shard.get("D0_only_reference_untouched")!=214 or
                shard.get("historical_exposed_NOT_OOS") is not True or
                shard.get("G4")!="UNKNOWN" or shard.get("G6")!="NO_GO"):
            raise ValueError("STAGE151_SHARD_GATE_DRIFT")
        for row in shard["rows"]:
            k=(row.get("date"),row.get("symbol"))
            if (k not in expected or row["date"]!=shard["date"] or
                    row["D0_FIRST_UTC"]!=expected[k]["D0_FIRST_UTC"] or
                    row["D1_FIRST_UTC"]!=expected[k]["D1_FIRST_UTC"] or
                    row["D1_PATH"]!=expected[k]["D1_PATH"] or
                    row["identity"]!=expected[k]["identity"] or
                    row.get("real_fill")!="NOT_OBSERVED" or
                    row.get("G4")!="UNKNOWN"):
                raise ValueError("STAGE151_NOT_ORIGINAL_305_SAME_D0_D1")
            if row["preregistered_decision"]["state"] not in STATES:
                raise ValueError("STAGE151_ILLEGAL_STATE")
            all_rows.append(row)
    keys=[(x["date"],x["symbol"]) for x in all_rows]
    if (len(keys)!=305 or len(set(keys))!=305 or set(keys)!=set(expected)):
        raise ValueError("STAGE151_NOT_FULL_ORIGINAL305_DENOMINATOR")
    bydate={}
    for date in DATES:
        bydate[date]=groups(x for x in all_rows if x["date"]==date)
    bypath={}
    for label in sorted({x["D1_PATH"] for x in all_rows}):
        bypath[label]=groups(x for x in all_rows if x["D1_PATH"]==label)
    overall=groups(all_rows)
    return {
        "schema":SCHEMA,
        "source":"FROZEN_STAGE101_STAGE88_STAGE85_OFFICIAL_1M_PUBLISHER_SHA",
        "original_519_D0_untouched":519,
        "original_305_D1_all_scored":len(all_rows),
        "original_214_D0_only_untouched":214,
        "all_original_date_shards":len(shards),
        "six_dates_research_exposed_not_independent_OOS":True,
        "full305":overall,
        "date_window_stability":bydate,
        "DIRECT_and_REIGNITION":bypath,
        "no_picking_only_profitable_outcomes":True,
        "frozen_parameters":{"P0_DROP_FACTOR":"0.97",
                             "TROUGH_RECLAIM_FACTOR":"1.01",
                             "MAX_POST_D1_COMPLETED_1M":120,
                             "FIXED_HORIZONS_M":[360,1440]},
        "verdict":"EXPOSED_HISTORICAL_DESCRIPTION_ONLY_NOT_VALIDATED_STRATEGY",
        "D0_D1_original_core":"UNCHANGED",
        "historical_stage110_118_127":"REJECTED_UNCHANGED",
        "historical_stage132_first_momentum_buy":"NEGATIVE_UNCHANGED",
        "real_bid_ask_depth_fees_fill_and_net":"UNKNOWN",
        "source_universe_crypto_issuer":"PARTIAL",
        "G0":"PARTIAL","G1":"NOT_SCORABLE","G2_G3":"NOT_PASSED",
        "G4":"UNKNOWN","G5":"NOT_DONE","G6":"NO_GO",
        "production_trading":"NO_GO","Gmail":"OFF","Frank":"UNCHANGED",
        "new_schedule":False,
        "rows":sorted(all_rows,key=lambda r:(r["date"],r["symbol"])),
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--artifact-dir",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    source,_=stage151.stage101.frozen()
    paths=sorted(a.artifact_dir.glob("monster-stage151-*-s*.json"))
    reports=[json.loads(f.read_text()) for f in paths]
    report=aggregate(reports,source)
    a.out.mkdir(parents=True,exist_ok=True)
    summary={k:v for k,v in report.items() if k!="rows"}
    (a.out/"monster_stage151_original305_preregistered_summary.json").write_text(
        json.dumps(summary,ensure_ascii=False,sort_keys=True,indent=2)+"\n")
    (a.out/"monster_stage151_original305_preregistered_rows.jsonl").write_text(
        "".join(json.dumps(x,ensure_ascii=False,sort_keys=True)+"\n"
                for x in report["rows"]))
    print("STAGE151_REAL305_FROZEN_OUTCOME "+json.dumps({
        "n":report["original_305_D1_all_scored"],
        "states":report["full305"]["states"],
        "median_24h":report["full305"][
            "confirmed_1440m_complete_unfilled_price_proxy"]["gross_pct_median"],
        "verdict":report["verdict"]},sort_keys=True))


if __name__=="__main__":
    main()
