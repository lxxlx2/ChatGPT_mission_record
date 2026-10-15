#!/usr/bin/env python3
"""Stage151 all305 source-locked cohort analysis, exposed historical diagnostic."""
from __future__ import annotations
import argparse
import hashlib
import os
from collections import Counter
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


def distribution(xs):
    v=list(xs)
    return {
        "n":len(v), "median_pct":str(median(v)) if v else None,
        "mean_pct":str(sum(v)/len(v)) if v else None,
        "sum_pct_points_not_Portfolio_PNL":str(sum(v)) if v else None,
        "positive":sum(z>0 for z in v),
        "gain_20pct_or_better":sum(z>=20 for z in v),
        "gain_100pct_or_better":sum(z>=100 for z in v),
        "loss_20pct_or_worse":sum(z<=-20 for z in v),
    }


def groups(rows):
    r=list(rows)
    state_counts=Counter(x["preregistered_decision"]["state"] for x in r)
    if any(k not in STATES for k in state_counts):
        raise ValueError("STAGE151_UNKNOWN_FROZEN_MODEL_STATE")
    result={"n":len(r), "states":dict(state_counts)}
    original=[Decimal(x["baseline_Stage88_D1_direct_24h_gross_price_only_pct"])
              for x in r]
    baseline=distribution(original)
    result["baseline_Stage88_original_D1_direct_all_24h"]={
        "n":len(original),
        "gross_pct_median":str(median(original)) if original else None,
        "positive":sum(x>0 for x in original),
        "loss_20pct_or_worse":sum(x<=-20 for x in original),
        "full_distribution":baseline,
    }
    confirmed=[x for x in r if x["preregistered_decision"]["state"]==
               "PULLBACK_RECLAIM_CONFIRMED_PRICE_ONLY"]
    result["original_D1_early5_2x_EVALUATION_ONLY"]={
        "full_D1_early5_count":sum(x["old_D1_early5_gt2_evaluation_only"] for x in r),
        "retained_among_model_confirmations":sum(
            x["old_D1_early5_gt2_evaluation_only"] for x in confirmed),
        "NOT_G1_OR_G2_PASS":True,
    }
    result["no_model_entry_state_baseline_by_state"]={
        k:distribution(Decimal(x["baseline_Stage88_D1_direct_24h_gross_price_only_pct"])
                       for x in r if x["preregistered_decision"]["state"]==k)
        for k in STATES}
    for h in ("360","1440"):
        rows_ok=[]; unsupported=Counter()
        for x in r:
            path=x["entry_and_exit_fixed_horizon_price_only"].get(h)
            if path is None:
                if x["preregistered_decision"]["state"]==STATES[0]:
                    raise ValueError("STAGE152_CONFIRMED_MISSING_FIXED_PATH")
                continue
            if path["status"]=="COMPLETE_UNFILLED_PRICE_PROXY":
                rows_ok.append((x,path))
            else:
                unsupported[path["status"]]+=1
        valid=[Decimal(p["gross_pct"]) for _,p in rows_ok]
        fee=[Decimal(p["illustrative_20bps_each_side_pct"])
             for _,p in rows_ok]
        mae=[Decimal(p["adverse_LOW_proxy_pct_not_stop_fill"])
             for _,p in rows_ok]
        result["confirmed_"+h+"m_complete_unfilled_price_proxy"]={
            "n":len(valid),
            "gross_pct_median":str(median(valid)) if valid else None,
            "gross_positive":sum(x>0 for x in valid),
            "gross_loss_20pct_or_worse":sum(x<=-20 for x in valid),
            "illustrative_20bps_each_side_pct_median":
                str(median(fee)) if fee else None,
            "adverse_LOW_proxy_pct_median":str(median(mae)) if mae else None,
            "notional_and_true_executable_net":"UNKNOWN",
            "full_gross_distribution":distribution(valid),
            "full_illustrative_fee_distribution":distribution(fee),
            "confirmed_but_unsupported_by_status":dict(unsupported),
            "missing_or_censored_fixed_exit":sum(
                v for k,v in unsupported.items() if "CENSOR" in k or "MISSING" in k),
            "NO_TRADE":len(r)-len(confirmed),
            "CONFIRMED_NO_TRADES":sum(
                x["preregistered_decision"]["state"]==STATES[3] for x in r),
            "not_entered_is_not_zero_return":True,
        }
        # The 24h comparison's original direct D1 entry occurs at a DIFFERENT
        # clock time and its exit is also earlier. Paired correlations != alpha.
        baseline_same=[Decimal(x[
            "baseline_Stage88_D1_direct_24h_gross_price_only_pct"])
            for x,p in rows_ok]
        if h=="1440":
            result["same_selected_184_original_D1_baseline_NOT_same_clock_exit"]=(
                distribution(baseline_same))
            result["paired_24h_pct_point_difference_DIFFERENT_exit_clocks"]=(
                distribution(Decimal(p["gross_pct"])-Decimal(x[
                    "baseline_Stage88_D1_direct_24h_gross_price_only_pct"])
                    for x,p in rows_ok))
            winners=sorted(rows_ok,key=lambda xp: (
                -Decimal(xp[1]["gross_pct"]),xp[0]["date"],xp[0]["symbol"]))
            trimmed={}
            for k in (1,3,5):
                remaining=winners[k:]
                trimmed[str(k)]={
                    "remaining":len(remaining),
                    "removed_winners":[{
                        "date":x["date"],"symbol":x["symbol"],
                        "gross_pct":p["gross_pct"]} for x,p in winners[:k]],
                    "remaining_distribution":distribution(
                        Decimal(p["gross_pct"]) for _,p in remaining),
                }
            result["top_winner_concentration_and_leave_top_k_out"]=trimmed
        # All liquidity subsets are only as-of archival 1m turnover filters,
        # not user quote-order amounts, live spreads, fills, or capital.
        tiers={}
        for threshold in stage151.LIQUIDITY_QUOTE_THRESHOLDS_USDT:
            kept=[Decimal(p["gross_pct"]) for x,p in rows_ok
                  if (Decimal(p["entry_minute_quote_volume_USDT"])>=threshold
                      and Decimal(p["exit_minute_quote_volume_USDT"])>=threshold
                      and p["entry_minute_trade_count"]>=1
                      and p["exit_minute_trade_count"]>=1)]
            tiers[str(threshold)]={
                "min_entry_and_exit_market_1m_quote_USDT":str(threshold),
                "not_order_notional_or_orderbook_depth":True,
                "filtered_out_of_complete":len(rows_ok)-len(kept),
                "distribution_on_observed_market_activity_only":distribution(kept),
            }
        result["market_1m_turnover_sensitivity_NOT_execution"]=tiers
        delays={}
        for delay in stage151.LATENCY_MINUTES[1:]:
            delayed=[]; unusable=Counter()
            for x,p in rows_ok:
                cand=x.get("delayed_entry_open_same_holding_horizon_price_only",{}).get(
                    str(delay),{}).get(h)
                if cand is None:
                    raise ValueError("STAGE152_MISSING_LATENCY_PATH")
                if cand["status"]=="COMPLETE_UNFILLED_PRICE_PROXY":
                    delayed.append(Decimal(cand["gross_pct"]))
                else:
                    unusable[cand["status"]]+=1
            delays[str(delay)]={
                "additional_entry_delay_minutes":delay,
                "exit_also_shifted_same_holding_horizon":True,
                "different_clock_exits_NOT_causal_real_fill":True,
                "unsupported":dict(unusable),
                "price_only_distribution":distribution(delayed),
            }
        result["entry_delay_price_only_sensitivity_NOT_execution"]=delays
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
    trigger_pins=set()
    source_sha_pins=set()
    actual_source_sha=hashlib.sha256(
        Path(stage151.__file__).read_bytes()).hexdigest()
    trigger_expected=os.environ.get("GITHUB_SHA", "LOCAL_UNVERIFIED")
    for shard in shards:
        key=(shard.get("date"),shard.get("shard"))
        if (key[0] not in DATES or type(key[1]) is not int
                or key[1] not in range(4) or key in seen_shards):
            raise ValueError("STAGE151_DUPLICATE_OR_INVALID_SHARD")
        seen_shards.add(key)
        trigger_pins.add(shard.get("trigger_commit_sha"))
        source_sha_pins.add(shard.get("stage151_core_sha256"))
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
    if (trigger_pins!={trigger_expected}
            or source_sha_pins!={actual_source_sha}):
        raise ValueError("STAGE152_MIXED_OR_DRIFTED_SHARD_SOURCE_SHA")
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
        "trigger_commit_sha":trigger_expected,
        "stage151_core_sha256":actual_source_sha,
        "original_519_D0_untouched":519,
        "original_305_D1_all_scored":len(all_rows),
        "original_214_D0_only_untouched":214,
        "all_original_date_shards":len(shards),
        "six_dates_research_exposed_not_independent_OOS":True,
        "full305":overall,
        "date_window_stability":bydate,
        "DIRECT_and_REIGNITION":bypath,
        "no_picking_only_profitable_outcomes":True,
        "frozen_parameters":{"P0_DROP_FACTOR":str(stage151.DROP),
                             "TROUGH_RECLAIM_FACTOR":str(stage151.RECLAIM),
                             "MAX_POST_D1_COMPLETED_1M":stage151.MAX_BARS,
                             "FIXED_HORIZONS_M":list(stage151.HORIZONS),
                             "ADDITIONAL_DELAY_M":list(stage151.LATENCY_MINUTES),
                             "MIN_ENTRY_AND_EXIT_MARKET_1M_QUOTE_TIERS_USDT":[
                                 str(x) for x in stage151.LIQUIDITY_QUOTE_THRESHOLDS_USDT]},
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
    (a.out/"monster_stage152_original305_integrity_and_economics_summary.json").write_text(
        json.dumps(summary,ensure_ascii=False,sort_keys=True,indent=2)+"\n")
    (a.out/"monster_stage152_original305_integrity_and_economics_rows.jsonl").write_text(
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
