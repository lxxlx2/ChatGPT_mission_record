#!/usr/bin/env python3
"""Stage114: strict original 519-case D0/D1/first-PRIORITY paired source attribution."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from decimal import Decimal
import json
from pathlib import Path
from statistics import median

try:
    import monster_v4_stage114_matched_entry_official as replay
except ImportError:
    from scripts import monster_v4_stage114_matched_entry_official as replay

SCHEMA="MONSTER_STAGE114_FULL519_D0_D1_FIRST_PRIORITY_MATCHED_ECONOMICS_V1"
MODES=("D0","D1","PRIORITY","PRIORITY_PLUS_1M_LATENCY")
HORIZONS=("5","1440")


def summary(vals):
    v=sorted(vals)
    return {
        "n":len(v),"median_pct":str(median(v)) if v else None,
        "positive":sum(x>0 for x in v),
        "loss_20pct_or_worse":sum(x<=-20 for x in v),
        "synthetic_fee_20bps_each_side_median_pct":
            str(median([((1+x/100)*(Decimal("0.998")/Decimal("1.002"))-1)*100
                        for x in v])) if v else None,
        "actual_exec_net":"UNKNOWN",
    }


def scalar_summary(vals):
    v=sorted(vals)
    return {"n":len(v),"median":str(median(v)) if v else None,
            "positive":sum(x>0 for x in v),
            "negative":sum(x<0 for x in v),
            "zero":sum(x==0 for x in v)}


def audit(packets):
    source, archive, stage112, stage113=replay.frozen()
    keys={(x["date"],x["symbol"]) for x in source}
    if len(keys)!=519 or len(packets)!=24:
        raise ValueError("STAGE114_MISSING_ORIGINAL_COHORT_OR_24_SHARDS")
    seen_shards=set()
    all_rows=[]
    for shard in packets:
        tag=(shard["date"],shard["shard"])
        if (tag in seen_shards or shard["schema"]!=replay.SCHEMA
            or shard["source_stage113_git_blob"]!=replay.PIN113
            or shard["source_stage112_git_blob"]!=replay.s113.PIN112
            or shard["original_D0_cases"]!=519 or shard["original_D1_cases"]!=305):
            raise ValueError("STAGE114_SHARD_OR_UPSTREAM_SHA_DRIFT")
        seen_shards.add(tag)
        expected=replay.old.shard_rows(shard["date"],shard["shard"],source)
        if ({(x["date"],x["symbol"]) for x in shard["rows"]} !=
            {(x["date"],x["symbol"]) for x in expected}
            or len(shard["rows"])!=len(expected)):
            raise ValueError("STAGE114_ORIGINAL_SHARD_SYMBOL_LOSS")
        all_rows.extend(shard["rows"])
    if seen_shards!={(date,shard) for date in replay.old.DATES for shard in range(4)}:
        raise ValueError("STAGE114_NOT_EXACT_24_SHARDS")
    if len(all_rows)!=519 or {(x["date"],x["symbol"]) for x in all_rows}!=keys:
        raise ValueError("STAGE114_ALL519_NOT_RECONCILED")
    priors={(x["date"],x["symbol"]):x for x in source}
    valid=defaultdict(list)
    missing=Counter()
    mode_by_original_D1=defaultdict(Counter)
    nsignal=Counter()
    identities=Counter()
    original_d1_timing=Counter()
    wait_minutes=defaultdict(list)
    entry_price_rel=defaultdict(list)
    entry_pct_missing=Counter()
    same_exit=defaultdict(list)
    same_exit_censor=Counter()
    separately_anchored_pairs=defaultdict(list)
    major=Counter()
    bydate=defaultdict(Counter)
    bycase=[]
    for case in sorted(all_rows,key=lambda x:(x["date"],x["symbol"])):
        key=(case["date"],case["symbol"])
        x=priors[key]
        if (case["D0_FIRST_UTC"]!=x["D0_FIRST_UTC"]
            or case["original_D1_FIRST_UTC"]!=x["D1_FIRST_UTC"]
            or case["identity"]!=x["identity"]
            or case["original_D0_early5_2x_EVAL_ONLY"]!=bool(x["D0_at_least_5m_before_2x"])):
            raise ValueError("STAGE114_PRIOR_ORIGINAL_CASE_DRIFT")
        if case["source_status"]!="EXPIRED":
            raise ValueError("STAGE114_ORIGINAL_ALL519_SOURCE_REPLAY_NOT_COMPLETE")
        identities[case["identity"]]+=1
        first=case["first_priority_observable_ms"]
        old112=stage112[key]
        if (old112["first_priority_utc_ms"]!=first or
            old112["priorities"]!=case["original_priority_count"]):
            raise ValueError("STAGE114_PRIOR_STAGE112_FIRST_SIGNAL_DRIFT")
        has_d1=x["D1_FIRST_UTC"] is not None
        nsignal["D0"]+=1
        if has_d1:nsignal["D1"]+=1
        if first is not None:
            nsignal["PRIORITY"]+=1
            nsignal["PRIORITY_PLUS_1M_LATENCY"]+=1
            bydate[x["date"]]["priority_cases"]+=1
        bydate[x["date"]]["all_cases"]+=1
        original_d1_timing[case["D1_chronology"]]+=1
        if first is not None:
            wait_minutes["D0_TO_PRIORITY"].append(Decimal(case["D0_to_PRIORITY_minutes"]))
            if has_d1:
                wait_minutes["D1_TO_PRIORITY"].append(Decimal(case["D1_to_PRIORITY_minutes"]))
        if x["D0_at_least_5m_before_2x"]:
            major["D0_EARLY_2X"]=major["D0_EARLY_2X"]+1
            if first is not None and replay.old.utc_ms(
                x["true_first_2x_HIGH_UTC_EVALUATION_ONLY"])-first>=5*replay.MIN:
                major["PRIORITY_EARLY_2X"]+=1

        hz=case["frozen_5m_24h_entry_horizon_price_proxies"]
        for mode in MODES:
            if set(hz[mode])!=set(HORIZONS):
                raise ValueError("STAGE114_HOLDING_HORIZON_DRIFT")
            for h in HORIZONS:
                event=hz[mode][h]
                bin=mode+"_"+h
                if event["status"]=="COMPLETE_PRICE_ONLY":
                    r=Decimal(event["gross_pct"])
                    if not r.is_finite():
                        raise ValueError("STAGE114_NONFINITE_GROSS")
                    valid[bin].append(r)
                    mode_by_original_D1["D1_PRESENT" if has_d1 else "D0_ONLY"][bin]+=1
                else:
                    if event["gross_pct"] is not None:
                        raise ValueError("STAGE114_CENSORED_BUT_RETURN_PRESENT")
                    missing[bin]+=1
        for name,raw in (
            ("P_VS_D0",case["priority_vs_D0_entry_pct"]),
            ("P_VS_D1_EARLIER",case["priority_vs_D1_entry_pct"]),
            ("P_PLUS1M_VS_P",case["latency_plus_1m_vs_original_priority_open_pct"]),
        ):
            if raw is not None:
                entry_price_rel[name].append(Decimal(raw))
            elif first is not None:
                entry_pct_missing[name]+=1
        if first is not None:
            for other in ("D0","D1"):
                pairs=case["common_exit_first_priority_5m_24h_earlier_entry_comparison"][other]
                for h in HORIZONS:
                    pair=pairs[h]
                    label=other+"_VS_P_"+h
                    if pair["status"]=="COMPLETE_PRICE_ONLY":
                        same_exit[label].append(Decimal(pair[
                            "earlier_minus_priority_return_pct_points"]))
                    else:
                        same_exit_censor[label]+=1
                    first_exit=hz[other][h]
                    prior_exit=hz["PRIORITY"][h]
                    if (first_exit["status"]=="COMPLETE_PRICE_ONLY" and
                        prior_exit["status"]=="COMPLETE_PRICE_ONLY" and
                        (other=="D0" or case["D1_chronology"] in (
                            "D1_BEFORE_PRIORITY","D1_EQUALS_PRIORITY"))):
                        separately_anchored_pairs[label].append(
                            Decimal(first_exit["gross_pct"])-Decimal(prior_exit["gross_pct"]))
        bycase.append({
            "date":case["date"],"symbol":case["symbol"],"identity":case["identity"],
            "D1_chronology":case["D1_chronology"],
            "first_priority_ms":first,
            "D0_to_first_priority_minutes":case["D0_to_PRIORITY_minutes"],
            "D1_to_first_priority_priority_minutes":case["D1_to_PRIORITY_minutes"],
            "priority_vs_D0_open_pct":case["priority_vs_D0_entry_pct"],
            "priority_vs_D1_earlier_open_pct":case["priority_vs_D1_entry_pct"],
            "priority_plus1m_vs_priority_open_pct":
                case["latency_plus_1m_vs_original_priority_open_pct"],
            "original_D0_early2x5m_evaluation_only":bool(x["D0_at_least_5m_before_2x"]),
            "entry_price_proxy_gross_by_horizon":case[
                "frozen_5m_24h_only_gross_comparison"],
            "same_exit_price_parity":case[
                "common_exit_first_priority_5m_24h_earlier_entry_comparison"],
            "source_1m_publisher_SHA_receipts":
                case["official_publisher_1m_sha_receipts"],
            "real_exec_net":"UNKNOWN",
        })
    if (nsignal!=Counter({"D0":519,"D1":305,"PRIORITY":277,
                          "PRIORITY_PLUS_1M_LATENCY":277})
        or major["D0_EARLY_2X"]!=28 or major["PRIORITY_EARLY_2X"]!=19):
        raise ValueError("STAGE114_FULL_COHORT_OR_MAJOR_G2_DRIFT")
    frozen_first=replay.s113.stage112.frozen_aggregate()
    orig24=frozen_first["preregistered_gates"]["G4_price_only_only"]
    # The Stage113 FIRST priority's 24h source-complete population is 237,
    # not the Stage111 all-episode 598 denominator. Keep both immutable.
    original113=replay.s113.stage112.E/"monster_stage113_real519_5_60_360_1440m_actual.json"
    stage113agg=json.loads(original113.read_text())
    for h in HORIZONS:
        old=stage113agg["first_and_repeat_for_each_fixed_horizon"]["FIRST"][h]["complete"]
        here=summary(valid["PRIORITY_"+h])
        if here["n"]!=old["complete_price_observations"] or here["median_pct"]!=old["gross_median_pct"]:
            raise ValueError("STAGE114_FIRST_PRIORITY_RETURN_PARITY_FAIL_"+h)
    if orig24["complete_24h_price_proxy_count"]!=598:
        raise ValueError("STAGE114_STAGE111_598_DRIFT")
    return {
        "schema":SCHEMA,
        "source_Stage111_D0_git_blob":replay.s113.stage112.PIN_AGG_BLOB,
        "source_Stage112_git_blob":replay.s113.PIN112,
        "source_Stage113_git_blob":replay.PIN113,
        "original_D0_cases":519,"original_D1_count":305,
        "cases_with_first_priority":277,
        "major_D0_early5_2x":28,"major_first_priority_early5_2x":19,
        "signal_case_count":dict(nsignal),
        "D1_relative_chronology":dict(sorted(original_d1_timing.items())),
        "identities":dict(sorted(identities.items())),
        "signal_to_priority_waittime_minutes":{name:scalar_summary(vals)
                  for name,vals in sorted(wait_minutes.items())},
        "entry_price_relative_change_pct":{name:scalar_summary(vals)
                  for name,vals in sorted(entry_price_rel.items())},
        "missing_entry_price_comparisons":dict(entry_pct_missing),
        "independent_5m_and_24h_entry_horizon_gross":{
                  mode:{h:{"complete":summary(valid[mode+"_"+h]),
                            "censored":missing[mode+"_"+h]} for h in HORIZONS}
                  for mode in MODES},
        "same_terminal_priority_5m_24h_earlier_vs_delayed_gross_pct_point_difference":{
                  key:{"complete":scalar_summary(vals),"censored":same_exit_censor[key]}
                  for key,vals in sorted(same_exit.items())},
        "separate_own_exit_horizon_matched_case_return_difference_pct_points":{
                  key:scalar_summary(vals) for key,vals in sorted(separately_anchored_pairs.items())},
        "source_complete_price_by_has_original_D1":{
                  key:dict(value) for key,value in mode_by_original_D1.items()},
        "original_anchor_cases_by_date":dict(sorted(bydate.items())),
        "all_519_original_cases":bycase,
        "historical_exposed_not_OOS":True,
        "no_strategy_trading_admission_frozen_or_executed":True,
        "real_executable_net":"UNKNOWN",
        "new_other_AI_review":"NOT_DONE",
        "monster_deployment":"NO_GO",
        "frank":"UNCHANGED",
        "stage99_local_collector":"UNCHANGED",
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--artifact-dir",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    packets=[]
    for file in sorted(args.artifact_dir.rglob("monster-stage114-*.json")):
        item=json.loads(file.read_text())
        if item.get("schema")==replay.SCHEMA:
            packets.append(item)
    result=audit(packets)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("STAGE114_ORIGINAL519_PAIRED_D0_D1_P_PRICE_AUDIT "+
          json.dumps({k:v for k,v in result.items() if k!="all_519_original_cases"},sort_keys=True))


if __name__=="__main__":
    main()
