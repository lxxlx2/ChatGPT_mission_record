#!/usr/bin/env python3
"""Stage55: descriptive as-of feature audit of ALL frozen Stage52 166 candidates.

Exhaustive original P1v03-eligible universe (winner and normal), no top-result
selection, no threshold sweep, no re-fit or recomputation with future bars.
Comparison by future gross high2x is POST HOC grouping only. Historical
futures high is not a fill/BUY. Source SHA and statuses are pinned immutably.
"""
from __future__ import annotations
import argparse,collections,csv,hashlib,json,statistics
from decimal import Decimal
from pathlib import Path

E=Path(__file__).resolve().parents[2]/"monster"/"evidence"
SUMMARY=E/"monster_stage52_pinned_v03_all5400_36SHA_true_global_cap_metrics.json"
CASES=E/"monster_stage52_all5400_originalV4_P1v03_true_minute_source_cases.jsonl"
FATES=E/"monster_stage52_all_real_v03_eligible_and_global_budget_fates.jsonl"
LOCK={
SUMMARY.name:"42d455a6cc9d0164a8dd94aa12a475bad5ed126e",
CASES.name:"ad7544f97e8a0d6c1f2635aa54052cca42d08cf1",
FATES.name:"95ab2eda27880fc53dee7e5fe2d53007e9b9456f"}
SCHEMA="MONSTER_STAGE55_PINNED_ORIGINAL36_SHA_166_ASOF_CANDIDATES_NORMAL_BASELINE_V1"
KEYS=("ret60_pct","quote15_USDT","quote15_normalized_prev45","ret_from_first_D0_pct")

def blob(p):
    b=p.read_bytes()
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()

def read():
    for p in (SUMMARY,CASES,FATES):
        if blob(p)!=LOCK[p.name]:raise ValueError("STAGE55_EXPOSED_SOURCE_CHANGED "+p.name)
    m=json.loads(SUMMARY.read_text(encoding="utf-8"))
    rows=[json.loads(s) for s in CASES.read_text(encoding="utf-8").splitlines() if s]
    fates=[json.loads(s) for s in FATES.read_text(encoding="utf-8").splitlines() if s]
    if (len(rows),len(fates),m["P1v03_unbudgeted_candidates"],len(m["original36_source_sha_receipts"]))!=(5400,166,166,36):
        raise ValueError("STAGE55_UNVERIFIED_MARKET_DENOMINATORS")
    return m,rows,fates

def collect(m,rows,fates):
    cases={(x["date"],x["symbol"]):x for x in rows}
    fs={(x["date"],x["symbol"]):x for x in fates}
    if len(cases)!=5400 or len(fs)!=166:raise ValueError("STAGE55_DUPLICATE_COINS")
    data=[]
    for (d,s),fate in sorted(fs.items()):
        x=cases[d,s]
        cand=x.get("p1v03_eligible_unbudgeted")
        if x["source_status"]!="COMPLETE_REAL_USDM_1M_SHA_CAUSAL_V4" or cand is None or not cand["publisher_verified_asof_no_future_source"]:
            raise ValueError("STAGE55_NONVERIFIABLE_CANDIDATE")
        if cand["at_UTC"]!=fate["asof_UTC"]:raise ValueError("STAGE55_SOURCE_EVENT_TIME_DIFFERS")
        metrics=cand["features"]
        vals={k:Decimal(metrics[k]) if metrics[k] is not None else None for k in KEYS}
        if any(vals[k] is not None and not vals[k].is_finite() for k in KEYS):
            raise ValueError("STAGE55_PRICE_NONFINITE")
        is2=bool(x["hourly_gt2x"])
        target=x.get("first_true_2x_HIGH_minute_UTC")
        if bool(target)!=is2:raise ValueError("STAGE55_SOURCE_GT2X_CLOCK_MISMATCH")
        # Labels are joined AFTER reading the historically available features.
        if not is2:
            label="ORDINARY_NOT_CALENDAR_2X"
        else:
            import datetime as dt
            t=int(dt.datetime.fromisoformat(cand["at_UTC"].replace("Z","+00:00")).timestamp())
            t2=int(dt.datetime.fromisoformat(target.replace("Z","+00:00")).timestamp())
            label="FUTURE_2X_AND_CANDIDATE_BEFORE_5MIN" if t+300<=t2 else "FUTURE_2X_BUT_CANDIDATE_LATE"
        entry={"date":d,"symbol":s,"future_label_AFTER_signal":label,
          "eligible_timestamp_UTC":cand["at_UTC"],"mode":cand["kind"],
          "research_delivered":bool(fate["delivered"]),
          "global_budget_status":fate["status"],
          "polls_until_eligible":cand["polls_until_eligible"]}
        entry.update({k:str(vals[k]) if vals[k] is not None else None for k in KEYS})
        data.append(entry)
    if len(data)!=166 or sum(x["research_delivered"] for x in data)!=127:
        raise ValueError("STAGE55_SOURCE_GLOBAL_BUDGET_DRIFT")
    return data

def stats(data):
    def numeric(xs,k):
        return [Decimal(x[k]) for x in xs if x[k] is not None]
    def s(xs):
        out={"n":len(xs),"actual_research_delivered":sum(x["research_delivered"] for x in xs),
             "initial_urgent_candidates":sum(x["mode"]=="FIRST_D0_IMMEDIATE" for x in xs),
             "ongoing_reignition_candidates":sum(x["mode"]=="ONGOING_3M_SECOND_IGNITION" for x in xs)}
        for k in KEYS:
            arr=numeric(xs,k)
            out[k+"_median_asof"]=str(statistics.median(arr)) if arr else None
            out[k+"_n"]=len(arr)
        return out
    groups={label:s([x for x in data if x["future_label_AFTER_signal"]==label])
       for label in ("ORDINARY_NOT_CALENDAR_2X","FUTURE_2X_AND_CANDIDATE_BEFORE_5MIN","FUTURE_2X_BUT_CANDIDATE_LATE")}
    budget_groups={fate:s([x for x in data if x["global_budget_status"]==fate])
       for fate in ("CAP_DELIVERED_RESEARCH","OVER_BUDGET_RESEARCH_NOT_DELIVERED")}
    result={
     "schema":SCHEMA,"locked_original_source_Git_blobs":LOCK,
     "original_source_verified_case_count":5400,
     "source_verified_original_sha_receipts":36,
     "all_v03_eligible_asof_candidates":len(data),
     "all_2x_source_cases_eligible_pre_5min":groups["FUTURE_2X_AND_CANDIDATE_BEFORE_5MIN"]["n"],
     "groups_by_POSTHOC_label":groups,
     "groups_by_REAL_global_budget_fate":budget_groups,
     "data_is_already_exposed_and_NOT_holdout_for_next_threshold":True,
     "DO_NOT_USE_FUTURE_GT_AS_RANKING_FEATURE":True,
     "no_new_P1_threshold_selected":True,
     "historical_high_is_not_trade_profit":True,
     "other_AI_review":"NOT_DONE","deploy":"NO_GO","Frank":"UNCHANGED","Gmail":"OFF"}
    return result

def selftest():
    assert statistics.median([Decimal("1"),Decimal("2"),Decimal("3")])==Decimal("2")
    assert statistics.median([Decimal("1"),Decimal("2")])==Decimal("1.5")
    print("STAGE55_DECIMAL_ASOF_ALL166_EXPOSED_LABEL_ONLY_SELFTEST_PASS")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path)
    p.add_argument("--selftest",action="store_true")
    a=p.parse_args()
    if a.selftest:selftest();return
    if not a.out:p.error("--out required")
    m,c,b=read()
    data=collect(m,c,b)
    summary=stats(data)
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"monster_stage55_all166_asof_closed_1m_vs_posthoc_GT2x_descriptive_summary.json").write_text(
      json.dumps(summary,indent=2,sort_keys=True,ensure_ascii=False)+"\n")
    with (a.out/"monster_stage55_all166_candidate_asof_features_and_fate.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(data[0]),lineterminator="\n")
        w.writeheader();w.writerows(data)
    print("STAGE55_REAL_ORIGINAL36_SHA_ALL166_FIRST_ONGOING_ASOF_FEATURE_GROUPS_PASS "+
          json.dumps({k:summary[k] for k in ("all_v03_eligible_asof_candidates",
           "all_2x_source_cases_eligible_pre_5min")},sort_keys=True))
if __name__=="__main__":main()
