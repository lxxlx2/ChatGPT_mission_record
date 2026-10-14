#!/usr/bin/env python3
"""Stage115 immutable original519 D0 5m/24h cohort stability, exposed only."""
from __future__ import annotations

import argparse
from collections import Counter,defaultdict
from decimal import Decimal
from hashlib import sha1
import json
from pathlib import Path
from statistics import median,mean

E=Path(__file__).resolve().parents[2]/"monster"/"evidence"
RAW=E/"monster_stage114_real519_d0_d1_priority_paired_entry_actual.json"
COMPACT=E/"monster_stage114_source_locked_compact_summary.json"
PIN_RAW="de64a09ff4f8b35009fd1ff71a284542fd5de5ac"
PIN_COMPACT="33e38198a8ad2c0d99ebf4161c77264978ffbcc4"
SCHEMA="MONSTER_STAGE115_FROZEN_ORIGINAL519_D0_COHORT_STABILITY_V1"
DATES=("2025-01-30","2025-06-02","2025-08-01","2025-10-02",
       "2026-06-21","2026-07-28")


def git_blob(data):
    return sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()


def quantile_nearest_rank(values,percent):
    if not values:return None
    from math import ceil
    return str(values[ceil(len(values)*percent)-1])


def grouped(rows):
    out={}
    for x in rows:
        # Stage114 full archive stores an intentionally compact per-case
        # diagnostic projection, not its earlier replay's nested records.
        # Null is an observed 5m/24h missing/censored outcome, NEVER a loss.
        results=x["entry_price_proxy_gross_by_horizon"]["D0"]
        if set(results)!={"5","1440"}:
            raise ValueError("STAGE115_D0_SIGNAL_HORIZON_DRIFT")
        if x["D1_chronology"] not in (
                "NONE","NO_PRIORITY","D1_BEFORE_PRIORITY",
                "D1_AFTER_PRIORITY","D1_EQUALS_PRIORITY"):
            raise ValueError("STAGE115_UNKNOWN_ORIGINAL_D1_CLASS")
        if not x["source_1m_publisher_SHA_receipts"]:
            raise ValueError("STAGE115_MISSING_OFFICIAL_SOURCE_EVIDENCE")
        # D1_chronology=NONE means D1 missing, even when a priority exists.
        d1="D1_PRESENT" if x["D1_chronology"]!="NONE" else "D0_ONLY"
        p="LATER_PRIORITY_EXISTS" if x["first_priority_ms"] is not None else "NO_LATER_PRIORITY"
        groups={
          "ALL":"ALL_ORIGINAL_D0",
          "DATE":x["date"],
          "IDENTITY":x["identity"],
          "ORIGINAL_D1":d1,
          "FUTURE_PRIORITY_DESCRIPTIVE_ONLY":p,
          "DATE_X_ORIGINAL_D1":x["date"]+"|"+d1,
          "DATE_X_FUTURE_PRIORITY_POSTHOC_ONLY":x["date"]+"|"+p,
        }
        for family,k in groups.items():
            bucket=out.setdefault(family,{}).setdefault(k,{"cases":0,"values5":[],"values24":[],
                                                             "censored5":0,"censored24":0})
            bucket["cases"]+=1
            for horizon,slot in (("5","values5"),("1440","values24")):
                value=results[horizon]
                if value is not None:
                    val=Decimal(value)
                    if not val.is_finite():
                        raise ValueError("STAGE115_NONFINITE_ORIGINAL_GROSS")
                    bucket[slot].append(val)
                else:
                    bucket["censored5" if horizon=="5" else "censored24"]+=1
    result={}
    for family,v in out.items():
        result[family]={}
        for label,z in sorted(v.items()):
            def profile(vals,censored):
                v=sorted(vals)
                return {
                    "complete_n":len(v),
                    "censored_n":censored,
                    "positive_n":sum(x>0 for x in v),
                    "nonpositive_n":sum(x<=0 for x in v),
                    "gross_median_pct":str(median(v)) if v else None,
                    "gross_mean_pct":str(mean(v)) if v else None,
                    "gross_p10_pct":quantile_nearest_rank(v,0.10),
                    "gross_p90_pct":quantile_nearest_rank(v,0.90),
                    "loss_20pct_or_worse_n":sum(x<=-20 for x in v),
                    "gain50pct_or_more_n":sum(x>=50 for x in v),
                    "gain100pct_or_more_n":sum(x>=100 for x in v),
                    "real_executable_net":"UNKNOWN",
                }
            if z["cases"]!=len(z["values5"])+z["censored5"] or z["cases"]!=len(z["values24"])+z["censored24"]:
                raise ValueError("STAGE115_GROUP_CENSORING_DENOMINATOR_LOSS")
            result[family][label]={
                "original_cases":z["cases"],
                "D0_5m":profile(z["values5"],z["censored5"]),
                "D0_24h":profile(z["values24"],z["censored24"])
            }
    return result


def analyze():
    rdata=RAW.read_bytes()
    compact_bytes=COMPACT.read_bytes()
    if git_blob(rdata)!=PIN_RAW or git_blob(compact_bytes)!=PIN_COMPACT:
        raise ValueError("STAGE115_PINNED_FULL_SOURCE_OR_COMPACT_BLOB_CHANGED")
    original=json.loads(rdata)
    compact=json.loads(compact_bytes)
    rows=original["all_519_original_cases"]
    if (len(rows)!=519 or original["original_D0_cases"]!=519
            or original["original_D1_count"]!=305
            or original["cases_with_first_priority"]!=277
            or compact["source_full_results_git_blob"]!=PIN_RAW):
        raise ValueError("STAGE115_ORIGINAL519_PINNED_COHORT_DRIFT")
    if len({(x["date"],x["symbol"]) for x in rows})!=519 or set(x["date"] for x in rows)!=set(DATES):
        raise ValueError("STAGE115_ALL_ORIGINAL_DATE_SYMBOL_CASES_MISSING")
    result=grouped(rows)
    allz=result["ALL"]["ALL_ORIGINAL_D0"]
    if (allz["original_cases"]!=519 or allz["D0_5m"]["complete_n"]!=519
        or allz["D0_24h"]["complete_n"]!=480
        or allz["D0_24h"]["censored_n"]!=39
        or allz["D0_24h"]["positive_n"]!=266
        or allz["D0_24h"]["gross_median_pct"]!=
           compact["independent_5m_and_24h_entry_horizon_gross"]["D0"]["1440"]["complete"]["median_pct"]):
        raise ValueError("STAGE115_ALL519_D0_PRICE_RECONCILIATION_FAILED")
    if {x:result["DATE"][x]["original_cases"] for x in DATES}!={
         "2025-01-30":161,"2025-06-02":34,"2025-08-01":54,
         "2025-10-02":75,"2026-06-21":100,"2026-07-28":95}:
        raise ValueError("STAGE115_ALL_SIX_ANCHOR_POPULATIONS_DRIFT")
    if (result["ORIGINAL_D1"]["D1_PRESENT"]["original_cases"]!=305
        or result["ORIGINAL_D1"]["D0_ONLY"]["original_cases"]!=214
        or result["FUTURE_PRIORITY_DESCRIPTIVE_ONLY"]["LATER_PRIORITY_EXISTS"]["original_cases"]!=277
        or result["FUTURE_PRIORITY_DESCRIPTIVE_ONLY"]["NO_LATER_PRIORITY"]["original_cases"]!=242):
        raise ValueError("STAGE115_D1_PRIORITY_DENOMINATORS_CHANGED")
    return {
        "schema":SCHEMA,
        "source_original519_stage114_blob":PIN_RAW,
        "source_verified_compact_stage114_blob":PIN_COMPACT,
        "exposed_research_only_no_new_OOS":True,
        "original_D0_cases":519,
        "original_D0_24h_completed":480,
        "all_predefined_groups":result,
        "posthoc_future_priority_segment_never_a_live_input":True,
        "no_strategy_parameters_fitted":True,
        "real_executable_net":"UNKNOWN",
        "new_model_independent_AI_review":"NOT_DONE",
        "monster_deployment":"NO_GO",
        "Frank":"UNCHANGED",
        "Stage99":"UNCHANGED",
    }


def selftest():
    v=[Decimal("-25"),Decimal("0"),Decimal("8"),Decimal("51"),Decimal("104")]
    assert str(median(v))=="8"
    assert quantile_nearest_rank(v,0.10)=="-25"
    assert quantile_nearest_rank(v,0.90)=="104"
    assert git_blob(b"test")=="30d74d258442c7c65512eafab474568dd706c430"
    print("STAGE115_FIXED_519_DATE_D1_FUTURE_PRIORITY_STRATA_UNIT_PASS")


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--selftest",action="store_true")
    ap.add_argument("--out",type=Path)
    args=ap.parse_args()
    if args.selftest:
        selftest()
        return
    if args.out is None:ap.error("--out required")
    result=analyze()
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False)+"\n")
    print("STAGE115_SOURCE_LOCKED_D0_STABILITY "+
          json.dumps({k:v for k,v in result.items() if k!="all_predefined_groups"},sort_keys=True))


if __name__=="__main__":
    main()
