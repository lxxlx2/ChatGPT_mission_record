#!/usr/bin/env python3
"""Monster Stage64b: label evaluation ONLY; all519 global vs within-date rank.

The original 519 D0 signal cohort and as-of features never change here.
AUC-like concordance evaluates posthoc calendar 2x, not executable return.
No threshold fitting, priority selection, or model version changes.
"""
from __future__ import annotations
import argparse
import collections
import hashlib
import json
from decimal import Decimal
from pathlib import Path

E=Path(__file__).resolve().parents[2]/"monster"/"evidence"
SOURCE=E/"monster_stage64_all519_D0_asof61m_official_1m_taker_trades_SHA.jsonl"
SUMMARY=E/"monster_stage64_all519_asof61m_quote_taker_tradecount_summary.json"
PINS={
    SOURCE.name:"8ebe53acfdfe10413ac1e6f03457d6ace25d9d5a",
    SUMMARY.name:"e72d678e548e182c7edc8ab43191515c13b7f4ad",
}
KEYS=("ret60_pct","quote15_USDT","quote15_normalized_prev45",
      "taker_buy_share15","trade_count60")
SCHEMA="MONSTER_STAGE64B_FULL519_EXPOSED_GLOBAL_VS_WITHIN_DATE_2X_PAIRWISE_ASOF_DIAGNOSTIC_V1"

def blob(p):
    d=p.read_bytes()
    return hashlib.sha1(b"blob "+str(len(d)).encode()+b"\0"+d).hexdigest()

def read():
    for p in (SOURCE,SUMMARY):
        if blob(p)!=PINS[p.name]:raise ValueError("STAGE64B_ORIGINAL519_SHA_CHANGED "+p.name)
    xs=[json.loads(x) for x in SOURCE.read_text(encoding="utf-8").splitlines() if x]
    summary=json.loads(SUMMARY.read_text())
    if (len(xs),summary["full_source_complete"],
        summary["independent_immediate_P1_46_full_ASOF_feature_parity"])!=(519,519,46):
        raise ValueError("STAGE64B_WRONG_SOURCE")
    if len({(x["date"],x["symbol"]) for x in xs})!=519:
        raise ValueError("STAGE64B_DUPLICATE_SOURCE_KEYS")
    if sum(bool(x["original_7day_calendar_2x_EVALUATION_ONLY"]) for x in xs)!=29:
        raise ValueError("STAGE64B_ORIGINAL29_2X_DRIFT")
    return xs

def value(row,key):
    v=row["features_ASOF_ONLY"][key]
    return Decimal(str(v)) if v is not None else None

def concordance(winners,controls,key):
    numerator=0
    pairs=0
    dropped=0
    for a in winners:
        v=value(a,key)
        for b in controls:
            w=value(b,key)
            if v is None or w is None:
                dropped+=1
                continue
            pairs+=1
            if v>w:numerator+=2
            elif v==w:numerator+=1
    return {"pairs_compared":pairs,"missing_feature_pairs":dropped,
            "twice_concordant_pair_score":numerator,
            "pairwise_rank_concordance":str(Decimal(numerator)/(2*pairs)) if pairs else None}

def evaluate(data):
    winners=[x for x in data if x["original_7day_calendar_2x_EVALUATION_ONLY"]]
    others=[x for x in data if not x["original_7day_calendar_2x_EVALUATION_ONLY"]]
    dates=sorted({x["date"] for x in data})
    metrics={}
    for key in KEYS:
        g=concordance(winners,others,key)
        num=0;count=0;missing=0;by_date={}
        for d in dates:
            a=[x for x in winners if x["date"]==d]
            b=[x for x in others if x["date"]==d]
            t=concordance(a,b,key)
            num+=t["twice_concordant_pair_score"];count+=t["pairs_compared"]
            missing+=t["missing_feature_pairs"]
            by_date[d]={"winner_cases":len(a),"ordinary_cases":len(b),
                        "same_date_pairs":t["pairs_compared"],
                        "rank_concordance":t["pairwise_rank_concordance"]}
        metrics[key]={
            "global_pairwise":g,
            "same_date_pairwise":{
                "pairs_compared":count,"missing_feature_pairs":missing,
                "twice_concordant_pair_score":num,
                "pairwise_rank_concordance":str(Decimal(num)/(2*count)) if count else None,
            },
            "same_date_counts":by_date,
        }
    return {
        "schema":SCHEMA,
        "original519_sha_locked":PINS,
        "exposed_first_D0_candidate_count":len(data),
        "future_calendar_2x_positive_count":len(winners),
        "future_calendar_2x_negative_count":len(others),
        "source_verified_asof_real_1m":True,
        "descriptive_only_pairwise_feature_distinctions":metrics,
        "HISTORIC_LABEL_ONLY_NOT_CROSS_VALIDATED":True,
        "NO_NEW_THRESHOLDS":True,"NO_ASSUMED_NOTIONAL":True,
        "NOT_REALIZED_BUY_SELL_PNL":True,"P1V03":"REJECTED",
        "MONSTER_DEPLOY":"NO_GO","OTHER_AI_REVIEW":"NOT_DONE",
    }

def selftest():
    def r(d,s,v,gt):
        return {"date":d,"symbol":s,"original_7day_calendar_2x_EVALUATION_ONLY":gt,
                "features_ASOF_ONLY":{k:v for k in KEYS}}
    a=[r("2025-01-01","A","2",True)]
    b=[r("2025-01-01","B","1",False)]
    assert concordance(a,b,"ret60_pct")["pairwise_rank_concordance"]=="1"
    assert concordance(b,a,"ret60_pct")["pairwise_rank_concordance"]=="0"
    assert concordance(a,a,"ret60_pct")["pairwise_rank_concordance"]=="0.5"
    print("STAGE64B_GLOBAL_SAME_DATE_PAIRED_CONCORDANCE_EXPOSED_NO_THRESHOLD_SELFTEST_PASS")

def main():
    p=argparse.ArgumentParser();p.add_argument("--selftest",action="store_true")
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    if a.selftest:selftest();return
    if a.out is None:p.error("--out required")
    result=evaluate(read())
    for key in KEYS:
        g=result["descriptive_only_pairwise_feature_distinctions"][key]
        if (g["global_pairwise"]["pairs_compared"]!=14210 or
            g["same_date_pairwise"]["pairs_compared"]!=2001):
            raise ValueError("STAGE64B_ALL_ORIGINAL_CALENDAR_PAIRS_NOT_INCLUDED "+key)
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"monster_stage64b_all519_global_vs_within_date_asof_feature_pairwise_evaluation.json").write_text(
        json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print("STAGE64B_LABEL_BLIND_COHORT_ASOF_POSTHOC_METRICS "+
          json.dumps({k:{
              "global":v["global_pairwise"]["pairwise_rank_concordance"],
              "within_date":v["same_date_pairwise"]["pairwise_rank_concordance"]}
              for k,v in result["descriptive_only_pairwise_feature_distinctions"].items()},sort_keys=True))
if __name__=="__main__":
    main()
