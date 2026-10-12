#!/usr/bin/env python3
"""Monster Stage53: explain P1v03's rejected 7/28 missed 2x opportunities.

Read ONLY existing Stage52 independently verified original36 GitHub/binance SHA
full5400 real 1m cases + real globally budgeted fates. This is explanatory
research on an EXPOSED holdout, NOT a new threshold/model, profitable trade,
other-AI review, or authorization to send messages.
"""
from __future__ import annotations
import argparse
import collections
import csv
import datetime as dt
import hashlib
import json
from pathlib import Path

EVIDENCE=Path(__file__).resolve().parents[2]/"monster"/"evidence"
METRICS=EVIDENCE/"monster_stage52_pinned_v03_all5400_36SHA_true_global_cap_metrics.json"
CASES=EVIDENCE/"monster_stage52_all5400_originalV4_P1v03_true_minute_source_cases.jsonl"
BUDGET=EVIDENCE/"monster_stage52_all_real_v03_eligible_and_global_budget_fates.jsonl"
LOCKED={
 METRICS.name:"42d455a6cc9d0164a8dd94aa12a475bad5ed126e",
 CASES.name:"ad7544f97e8a0d6c1f2635aa54052cca42d08cf1",
 BUDGET.name:"95ab2eda27880fc53dee7e5fe2d53007e9b9456f",
}
SCHEMA="MONSTER_STAGE53_ORIGINAL36_SHA_FROZEN_V03_FALSE_NEGATIVE_CAUSAL_ATTRIBUTION_V1"
DAYS=("2025-01-30","2025-06-02","2025-08-01","2025-10-02","2026-06-21","2026-07-28")
COMPLETE="COMPLETE_REAL_USDM_1M_SHA_CAUSAL_V4"
DELIVERED="CAP_DELIVERED_RESEARCH"
OVER="OVER_BUDGET_RESEARCH_NOT_DELIVERED"

def git_blob(path):
    raw=path.read_bytes()
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()

def read():
    for path in (METRICS,CASES,BUDGET):
        if git_blob(path)!=LOCKED[path.name]:
            raise ValueError("STAGE53_PINNED_ORIGINAL_STAGE52_GIT_BLOB_CHANGED "+path.name)
    m=json.loads(METRICS.read_text(encoding="utf-8"))
    if (m["schema"]!="MONSTER_STAGE52_FROZEN_P1V03_ORIGINAL36_SHA_NEWDATE_GLOBAL_BUDGET_AND_HUGE_WINNER_GATES_V1"
        or m["original_run_id"]!=38218974455 or len(m["original36_source_sha_receipts"])!=36
        or m["attempted"]!=5400 or m["verdict"]!="REJECTED_P1V03_FROZEN_GATE"):
        raise ValueError("STAGE53_ORIGINAL_FROZEN_GATES_NOT_SOURCE_SHA_VERIFIED")
    cs=[json.loads(line) for line in CASES.read_text(encoding="utf-8").splitlines() if line]
    bs=[json.loads(line) for line in BUDGET.read_text(encoding="utf-8").splitlines() if line]
    if len(cs)!=5400 or len({(x["date"],x["symbol"]) for x in cs})!=5400:
        raise ValueError("STAGE53_EXACT_5400_SOURCE_CASES_REQUIRED")
    if len(bs)!=m["P1v03_unbudgeted_candidates"] or len({(x["date"],x["symbol"]) for x in bs})!=len(bs):
        raise ValueError("STAGE53_ORIGINAL_EVENT_BUDGET_MISSING")
    if sum(x["delivered"] for x in bs)!=m["P1v03_budget_delivered"]:
        raise ValueError("STAGE53_ORIGINAL_BUDGET_DELIVERED_DRIFT")
    return m,cs,bs

def ms(x):
    return int(dt.datetime.fromisoformat(x.replace("Z","+00:00")).timestamp()*1000)

def d0_pre5(case):
    target=case.get("first_true_2x_HIGH_minute_UTC")
    return bool(target) and any(ms(w)+5*60000<=ms(target) for w in case["WATCH_UTC"])

def diagnosis(case,urgent):
    """Diagnostic classification, NEVER used as a market signal."""
    target=case.get("first_true_2x_HIGH_minute_UTC")
    if not target or not d0_pre5(case):
        return "ORIGINAL_D0_NOT_EARLY_AT_LEAST_5_MINUTES"
    cand=case["p1v03_eligible_unbudgeted"]
    if cand is None:
        if urgent is not None:raise ValueError("STAGE53_BUDGET_EVENT_WITHOUT_CANDIDATE")
        return "NEVER_MET_FROZEN_FIRST_OR_SECOND_IGNITION_GATE"
    if urgent is None or urgent["asof_UTC"]!=cand["at_UTC"]:
        raise ValueError("STAGE53_ORIGINAL_GLOBAL_BUDGET_EVENT_ID_MISMATCH")
    if ms(cand["at_UTC"])+5*60000>ms(target):
        return "FIRST_ELIGIBLE_CANDIDATE_TOO_LATE_FOR_2X"
    if urgent["status"]==OVER and not urgent["delivered"]:
        return "ELIGIBLE_EARLY_BUT_DROPPED_BY_GLOBAL_FIVE_PER_DAY_CAP"
    if urgent["status"]==DELIVERED and urgent["delivered"]:
        return "DELIVERED_AT_LEAST_FIVE_MINUTES_BEFORE_2X"
    raise ValueError("STAGE53_UNRECOGNIZED_ORIGINAL_BUDGET_FATE")

def study(metrics,cases,budgets):
    allcases={(x["date"],x["symbol"]):x for x in cases}
    events={(x["date"],x["symbol"]):x for x in budgets}
    valid=[x for x in cases if x["source_status"]==COMPLETE]
    gt2=[x for x in valid if x["hourly_gt2x"]]
    no2=[x for x in valid if not x["hourly_gt2x"]]
    if (len(valid),len(gt2),len(no2))!=(
        metrics["publisher_1h_and_1m_valid"],metrics["GT2x"],
        metrics["publisher_1h_and_1m_valid"]-metrics["GT2x"]):
        raise ValueError("STAGE53_FROZEN_SOURCE_DENOMINATORS_WRONG")
    if any(x["source_status"]!=COMPLETE for x in cases if (x["date"],x["symbol"]) in events):
        raise ValueError("STAGE53_CENSORED_GOT_URGENT")

    ledger=[]
    for x in sorted(gt2,key=lambda r:(r["date"],r["symbol"])):
        key=x["date"],x["symbol"]
        ev=events.get(key)
        cause=diagnosis(x,ev)
        cand=x["p1v03_eligible_unbudgeted"]
        ledger.append({
         "date":x["date"],"symbol":x["symbol"],"GT2x":True,
         "GT5x":bool(x["hourly_gt5x"]),"GT10x":bool(x["hourly_gt10x"]),
         "real_first_2x_HIGH_UTC":x["first_true_2x_HIGH_minute_UTC"],
         "original_D0_first_WATCH_UTC":x["WATCH_UTC"][0] if x["WATCH_UTC"] else None,
         "original_D0_count":len(x["WATCH_UTC"]),
         "original_D0_pre_2x_ge5min":d0_pre5(x),
         "P1v03_first_eligible_UTC":cand["at_UTC"] if cand else None,
         "P1v03_mode":cand["kind"] if cand else None,
         "P1v03_eligible_2x_lead_min":(
             round((ms(x["first_true_2x_HIGH_minute_UTC"])-ms(cand["at_UTC"]))/60000,2)
             if cand else None),
         "globally_budgeted_fate":ev["status"] if ev else "NO_URGENT_CANDIDATE",
         "gate_reason":cause})
    by_reason=collections.Counter(x["gate_reason"] for x in ledger)
    if sum(by_reason.values())!=metrics["GT2x"]:
        raise ValueError("STAGE53_2X_EVENT_COUNTS_INCONSISTENT")
    good=by_reason["DELIVERED_AT_LEAST_FIVE_MINUTES_BEFORE_2X"]
    if good!=metrics["P1v03_budgeted_early_ge5min_GT2x_from_D0_pre5"]:
        raise ValueError("STAGE53_RECOMPUTED_FROZEN_SUCCESS_DIFFERS")
    early=sum(x["original_D0_pre_2x_ge5min"] for x in ledger)
    if early!=metrics["D0_early_ge5min_GT2x"]:
        raise ValueError("STAGE53_RECOMPUTED_D0_EARLY_DIFFERS")
    if sum(x["delivered"] for x in budgets)!=127 or len(budgets)!=166:
        raise ValueError("STAGE53_SOURCE_BUDGET_DRIFT")
    normal_urgent=[b for b in budgets if not allcases[(b["date"],b["symbol"])]["hourly_gt2x"]]
    normal_delivered=sum(b["delivered"] for b in normal_urgent)
    if normal_delivered!=metrics["budgeted_priority_on_non2x_coin_dates"]:
        raise ValueError("STAGE53_NORMAL_URGENT_COUNT_DRIFT")
    first_modes=collections.Counter(x["kind"] for x in budgets)
    delivered_modes=collections.Counter(x["kind"] for x in budgets if x["delivered"])
    over_modes=collections.Counter(x["kind"] for x in budgets if not x["delivered"])
    source_status=collections.Counter(x["source_status"] for x in cases)
    day_stats=[]
    for d in DAYS:
        cs=[x for x in valid if x["date"]==d]
        es=[x for x in budgets if x["date"]==d]
        wins=[x for x in ledger if x["date"]==d]
        day_stats.append({
         "date":d,"source_valid":len(cs),"valid_GT2x":len(wins),
         "original_D0_ge5":sum(x["original_D0_pre_2x_ge5min"] for x in wins),
         "budgeted_P1_early2x":sum(x["gate_reason"]=="DELIVERED_AT_LEAST_FIVE_MINUTES_BEFORE_2X" for x in wins),
         "raw_eligible":len(es),
         "delivered":sum(x["delivered"] for x in es),
         "overbudget":sum(not x["delivered"] for x in es),
         "ordinary_not2x_delivered":sum(x["delivered"] and not allcases[(x["date"],x["symbol"])]["hourly_gt2x"] for x in es)
        })
    return {
     "schema":SCHEMA,"data_role":"DESCRIPTIVE_EXPOSED_HOLDOUT_CAUSAL_AUDIT_NO_MODEL_TUNING",
     "locked_evidence_sha1":LOCKED,
     "input_unchanged_stage52_conclusion":metrics["verdict"],
     "original36_SHA_receipts":len(metrics["original36_source_sha_receipts"]),
     "all_market_attempted":len(cases),"source_complete":len(valid),
     "true_GT2x_count":len(gt2),"D0_early_at_least5min_GT2x":early,
     "v03_delivered_early_at_least5min_GT2x":good,
     "missed_D0_early_GT2x":early-good,
     "all_GT2x_case_level_frozen_fate":ledger,
     "original_GT2x_diagnostic_reason_counts":dict(by_reason),
     "P1v03_raw_candidate_count":len(budgets),
     "P1v03_delivered":sum(x["delivered"] for x in budgets),
     "P1v03_over_budget":sum(not x["delivered"] for x in budgets),
     "eligible_candidate_kind_counts":dict(first_modes),
     "delivered_kind_counts":dict(delivered_modes),
     "overbudget_kind_counts":dict(over_modes),
     "all_non2x_normal_symbol_dates":len(no2),
     "non2x_eligible_urgent":len(normal_urgent),
     "non2x_urgent_after_cap":normal_delivered,
     "source_status":dict(source_status),
     "by_six_frozen_date":day_stats,
     "do_not_change_frozen_P1v03":True,
     "historical_2x_price_label_is_not_execution":True,
     "historical_orderbook_and_contract_type":"UNVERIFIED",
     "other_AI_review":"NOT_DONE","deployment":"NO_GO","Frank":"UNCHANGED","Gmail":"OFF","automated_trading":"NO_GO"
    }

def selftest():
    x={"first_true_2x_HIGH_minute_UTC":"2025-01-30T09:00:00Z",
       "WATCH_UTC":["2025-01-30T08:00:00Z"],
       "p1v03_eligible_unbudgeted":None}
    assert diagnosis(x,None)=="NEVER_MET_FROZEN_FIRST_OR_SECOND_IGNITION_GATE"
    x["p1v03_eligible_unbudgeted"]={"at_UTC":"2025-01-30T08:30:00Z"}
    ev={"asof_UTC":"2025-01-30T08:30:00Z","status":OVER,"delivered":False}
    assert diagnosis(x,ev)=="ELIGIBLE_EARLY_BUT_DROPPED_BY_GLOBAL_FIVE_PER_DAY_CAP"
    ev=dict(ev,status=DELIVERED,delivered=True)
    assert diagnosis(x,ev)=="DELIVERED_AT_LEAST_FIVE_MINUTES_BEFORE_2X"
    x["p1v03_eligible_unbudgeted"]["at_UTC"]="2025-01-30T08:58:00Z"
    ev["asof_UTC"]="2025-01-30T08:58:00Z"
    assert diagnosis(x,ev)=="FIRST_ELIGIBLE_CANDIDATE_TOO_LATE_FOR_2X"
    x["WATCH_UTC"]=["2025-01-30T08:59:00Z"]
    assert diagnosis(x,ev)=="ORIGINAL_D0_NOT_EARLY_AT_LEAST_5_MINUTES"
    print("STAGE53_REAL_HISTORY_GROUP_DIAGNOSIS_AND_BUDGET_FATE_SELFTEST_PASS")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--selftest",action="store_true")
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    if a.selftest:selftest();return
    if not a.out:p.error("--out required")
    m,c,b=read()
    r=study(m,c,b)
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"monster_stage53_rejected_v03_full29_2x_fate_reasons_and_global_budget.json").write_text(
      json.dumps(r,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    fields=["date","symbol","GT5x","GT10x","real_first_2x_HIGH_UTC","original_D0_first_WATCH_UTC",
      "original_D0_count","original_D0_pre_2x_ge5min","P1v03_first_eligible_UTC",
      "P1v03_mode","P1v03_eligible_2x_lead_min","globally_budgeted_fate","gate_reason"]
    with (a.out/"monster_stage53_all29_real_gt2x_D0_P1v03_budget_failure.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore",lineterminator="\n")
        w.writeheader();w.writerows(r["all_GT2x_case_level_frozen_fate"])
    print("STAGE53_ORIGINAL_STAGE52_SHA_29_REAL_GT2X_MISSED_P1v03_DIAGNOSIS_PASS "+
      json.dumps({k:r[k] for k in ("true_GT2x_count","D0_early_at_least5min_GT2x",
       "v03_delivered_early_at_least5min_GT2x","missed_D0_early_GT2x",
       "original_GT2x_diagnostic_reason_counts","non2x_urgent_after_cap")},sort_keys=True))
if __name__=="__main__":
    main()
