#!/usr/bin/env python3
"""Only report all-six-day complete official BTC/ETH reference comparison."""
from __future__ import annotations
import argparse
from collections import Counter
import json
from decimal import Decimal
from pathlib import Path
try:
    import monster_v4_stage87_d1_market_relative_official as m
    import monster_v4_stage86_asof_d1_within_date_diagnostic as e
    from monster_v4_stage80_dual_entry_core import decimal
except ImportError:
    from scripts import monster_v4_stage87_d1_market_relative_official as m
    from scripts import monster_v4_stage86_asof_d1_within_date_diagnostic as e
    from scripts.monster_v4_stage80_dual_entry_core import decimal
SCHEMA="MONSTER_STAGE87_FULL305_ASOF_MARKET_RELATIVE_SAME_DATE_DIAGNOSTIC_V1"
FIELDS=(
    "candidate_excess_ret60_vs_BTC_pct",
    "candidate_excess_ret60_vs_ETH_pct",
    "candidate_excess_ret60_vs_BTCETH_mean_pct",
    "candidate_excess_quote_ratio_vs_BTCETH_mean"
)

def load(folder:Path):
    paths=sorted(folder.glob("monster-stage87-*.json"))
    if len(paths)!=6:
        raise ValueError("STAGE87_REQUIRE_SIX_ORIGINAL_DATE_SHARDS")
    allrows=[]
    all_proofs=[]
    seen=set()
    for path in paths:
        x=json.loads(path.read_text())
        if x["schema"]!=m.SCHEMA or x["date"] not in m.DATES or x["date"] in seen:
            raise ValueError("STAGE87_SOURCE_SHARD_DUPLICATED_OR_WRONG")
        seen.add(x["date"])
        actual=[r for r in m.frozen_rows() if r["date"]==x["date"]]
        if len(x["rows"])!=len(actual) or {
                (y["date"],y["symbol"]) for y in x["rows"]}!={
                (y["date"],y["symbol"]) for y in actual}:
            raise ValueError("STAGE87_MISSING_OR_ADDED_D1")
        allrows+=x["rows"]
        all_proofs+=x["official_reference_source_day_SHA"]
    if len(allrows)!=305 or seen!=set(m.DATES):
        raise ValueError("STAGE87_ALL305_UNION_INCOMPLETE")
    return allrows,all_proofs


def auc_by_date(rows,old):
    outcome={}
    for field in FIELDS:
        fullpos=[x for x in rows if old[(x["date"],x["symbol"])]["early5_gt2_evaluation_only"]]
        neg=[x for x in rows if not old[(x["date"],x["symbol"])]["calendar_2x_evaluation_only"]]
        bydate={}
        weighted=[]
        for d in m.DATES:
            p=[x for x in fullpos if x["date"]==d]
            n=[x for x in neg if x["date"]==d]
            v=e.pairwise_auc([decimal(x[field]) for x in p],
                             [decimal(x[field]) for x in n])
            bydate[d]=v
            if v:weighted.append(v["auc"])
        pooled=e.pairwise_auc([decimal(x[field]) for x in fullpos],
                              [decimal(x[field]) for x in neg])
        outcome[field]={
            "global_cross_day_auc":pooled["auc"] if pooled else None,
            "same_date_equal_date_auc":round(sum(weighted)/len(weighted),6)
                if weighted else None,
            "same_date_individual":{d:(v["auc"] if v else None) for d,v in bydate.items()},
            "same_date_evaluable_count":len(weighted)}
    return outcome


def audit(rows,proofs):
    old={(x["date"],x["symbol"]):x for x in m.frozen_rows()}
    if len(old)!=305:
        raise ValueError("STAGE87_ORIGINAL_305_NOT_RECOGNIZED")
    complete=[x for x in rows if x["benchmark_status"]=="COMPLETE_SHA_VERIFIED_BTC_ETH_REFERENCE"]
    censored=[x for x in rows if x["benchmark_status"]!="COMPLETE_SHA_VERIFIED_BTC_ETH_REFERENCE"]
    if any(x["symbol"] in m.REFERENCES for x in rows):
        raise ValueError("STAGE87_REFERENCE_NOT_A_MONSTER")
    keyset=set()
    for p in proofs:
        k=(p["symbol"],p["date"])
        if k in keyset or p["symbol"] not in m.REFERENCES:
            raise ValueError("STAGE87_DUPLICATE_OR_WRONG_REFERENCE_DAY")
        keyset.add(k)
        if not p["verified_official_publisher_SHA256"] or len(p["zip_sha256"])!=64:
            raise ValueError("STAGE87_UNVERIFIED_REFERENCE_SOURCE")
    summary={
        "schema":SCHEMA,"original_stage85_git_blob":m.PIN,
        "all_original_D1_events":305,"benchmark_complete":len(complete),
        "benchmark_unknown":len(censored),"source_reference_official_SHA_receipts":proofs,
        "reference_asset_names_BENCHMARK_ONLY":list(m.REFERENCES),
        "no_reference_in_monster_watch":True,
        "original_2x_early5_of_305":sum(x["early5_gt2_evaluation_only"] for x in old.values()),
        "reference_results":{
            "status":"PARTIAL_SOURCE" if censored else "COMPLETE_SOURCE",
            "excess_feature_auc_date_matched":auc_by_date(complete,old),
            "comparison_unadjusted_stage86_ret60_same_date_auc":"0.426901",
            "comparison_unadjusted_stage86_quote15_accel_same_date_auc":"0.485389",
            "note":"Same exposed date cohorts, descriptive label-open. If source missing, AUC subset not all305."
        },
        "research_exposure":"HISTORICAL_EXPOSED_NOT_OOS",
        "new_strategy_thresholds":"NONE",
        "profit_actual":"UNKNOWN","new_oos":"NOT_DONE",
        "other_ai_review":"NOT_DONE","deployment":"NO_GO",
        "gmail":"OFF","autotrade":"NO_GO","frank":"UNCHANGED"
    }
    return summary, rows

def selftest():
    assert len(m.frozen_rows())==305
    assert len(FIELDS)==4
    print("STAGE87_BTC_ETH_ONLY_ASOF_AUC_NO_TUNING_SELFTEST_PASS")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--selftest",action="store_true")
    p.add_argument("--artifact-dir",type=Path)
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    if a.selftest:selftest();return
    if not a.artifact_dir or not a.out:
        p.error("--artifact-dir and --out required")
    rows,proofs=load(a.artifact_dir)
    report,detailed=audit(rows,proofs)
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"monster_stage87_all305_market_relative_D1_features.jsonl").write_text(
      "".join(json.dumps(x,sort_keys=True,ensure_ascii=False)+"\n"
              for x in sorted(detailed,key=lambda y:(y["date"],y["symbol"]))))
    (a.out/"monster_stage87_full305_market_relative_diagnostic.json").write_text(
      json.dumps(report,sort_keys=True,ensure_ascii=False,indent=2)+"\n")
    print("STAGE87_FULL305_SAME_DATE_MARKET_EXCESS_DIAGNOSTIC "+json.dumps({
        "complete":report["benchmark_complete"],
        "unknown":report["benchmark_unknown"],
        "auc":{k:v["same_date_equal_date_auc"] for k,v in report[
          "reference_results"]["excess_feature_auc_date_matched"].items()}
    },sort_keys=True))
if __name__=="__main__":
    main()
