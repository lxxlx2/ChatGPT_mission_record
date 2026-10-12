#!/usr/bin/env python3
"""Stage54 factual UTC06 bucket capacity feasibility from pinned Stage52/53.

Noncausal hindsight "oracle" is explicitly only an UPPER BOUND: it may select
true future winners and MUST NEVER be presented as a deployable algorithm.
Ask whether frozen ≤5 urgent messages per 24h could mathematically retain
80% of original D0 early 2x *with perfect hindsight*, and where capacity is
wasted on normal/non2x candidates. Neither threshold nor delivery is changed.
"""
import argparse,collections,csv,datetime as dt,hashlib,json
from pathlib import Path

E=Path(__file__).resolve().parents[2]/"monster"/"evidence"
MET=E/"monster_stage52_pinned_v03_all5400_36SHA_true_global_cap_metrics.json"
EVENTS=E/"monster_stage52_all_real_v03_eligible_and_global_budget_fates.jsonl"
CASES=E/"monster_stage52_all5400_originalV4_P1v03_true_minute_source_cases.jsonl"
AUDIT=E/"monster_stage53_rejected_v03_full29_2x_fate_reasons_and_global_budget.json"
PIN={
  MET.name:"42d455a6cc9d0164a8dd94aa12a475bad5ed126e",
  EVENTS.name:"95ab2eda27880fc53dee7e5fe2d53007e9b9456f",
  CASES.name:"ad7544f97e8a0d6c1f2635aa54052cca42d08cf1",
  AUDIT.name:"eb52ff8f5eae51237a905eddbd3c5ce33ecf9904"
}
DAYS=("2025-01-30","2025-06-02","2025-08-01","2025-10-02","2026-06-21","2026-07-28")
SCHEMA="MONSTER_STAGE54_V03_SOURCE_SHA_ORACLE_ONLY_UTC06_GLOBAL_CAP_FEASIBILITY_V1"
ONE_DAY=86400000
COMPLETE="COMPLETE_REAL_USDM_1M_SHA_CAUSAL_V4"

def sha_blob(p):
    b=p.read_bytes()
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()

def timestamp(t):
    return int(dt.datetime.fromisoformat(t.replace("Z","+00:00")).timestamp()*1000)

def load():
    for p in (MET,EVENTS,CASES,AUDIT):
        if sha_blob(p)!=PIN[p.name]:
            raise ValueError("STAGE54_FROZEN_RESEARCH_SOURCE_CHANGED "+p.name)
    m=json.loads(MET.read_text(encoding="utf-8"))
    a=json.loads(AUDIT.read_text(encoding="utf-8"))
    e=[json.loads(x) for x in EVENTS.read_text(encoding="utf-8").splitlines() if x]
    c=[json.loads(x) for x in CASES.read_text(encoding="utf-8").splitlines() if x]
    if (m["GT2x"],m["D0_early_ge5min_GT2x"],a["missed_D0_early_GT2x"],
        len(c),len(e))!=(29,28,7,5400,166):
        raise ValueError("STAGE54_GT_SOURCE_NOT_FROZEN")
    if len(m["original36_source_sha_receipts"])!=36:
        raise ValueError("STAGE54_NEED_REAL36_ORIGINAL_GITHUB_SHA")
    return m,a,c,e

def assess(m,a,cs,events):
    cases={(x["date"],x["symbol"]):x for x in cs}
    if len(cases)!=5400:raise ValueError("STAGE54_DUPLICATE_ORIGINAL_CASES")
    wins={(x["date"],x["symbol"]):x for x in a["all_GT2x_case_level_frozen_fate"]
          if x["original_D0_pre_2x_ge5min"]}
    if len(wins)!=28:raise ValueError("STAGE54_ORIGINAL28_NEEDS_TO_BE_VALID")
    blocks=collections.defaultdict(list)
    entries=[]
    for e in events:
        key=e["date"],e["symbol"]
        if key not in cases or cases[key]["source_status"]!=COMPLETE:
            raise ValueError("STAGE54_EVENT_NOT_SOURCE_COMPLETE")
        start=timestamp(e["date"]+"T06:00:00Z")
        t=timestamp(e["asof_UTC"])
        offset=(t-start)//ONE_DAY
        if offset not in range(7) or offset!=e["window_day_index"]:
            raise ValueError("STAGE54_ORIGINAL_WINDOW_DAY_WRONG")
        win=wins.get(key)
        cand=cases[key]["p1v03_eligible_unbudgeted"]
        if cand is None or cand["at_UTC"]!=e["asof_UTC"]:
            raise ValueError("STAGE54_NOT_ORIGINAL_ASOF_CANDIDATE")
        early=bool(win and t+5*60000<=timestamp(win["real_first_2x_HIGH_UTC"]))
        new=dict(e,source_verified=True,GT2x_before5min=early,ever_GT2x=bool(cases[key]["hourly_gt2x"]))
        blocks[e["date"],offset].append(new)
        entries.append(new)
    if len(entries)!=166:raise ValueError("STAGE54_MISSING_EVENTS")
    dayrows=[]
    pure_upper=0
    for day in DAYS:
        for index in range(7):
            group=blocks.get((day,index),[])
            cap=len([x for x in group if x["delivered"]])
            if cap>5:raise ValueError("STAGE54_FROZEN_CAP_VIOLATED")
            real_early=sum(x["GT2x_before5min"] for x in group)
            delivered_real=sum(x["GT2x_before5min"] and x["delivered"] for x in group)
            oracle_min=min(5,real_early)
            pure_upper+=oracle_min
            dayrows.append({
             "research_window_start":day,"utc06_day_index":index,
             "candidate_count":len(group),"urgent_research_delivered":cap,
             "over_budget":len(group)-cap,
             "early_GT2x_eligible_with_hindsight":real_early,
             "early_GT2x_actually_delivered":delivered_real,
             "best_possible_early_GT2x_with_perfect_future_knowledge":oracle_min,
             "non2x_candidates":sum(not x["ever_GT2x"] for x in group),
             "non2x_delivered":sum(not x["ever_GT2x"] and x["delivered"] for x in group),
             "minimum_hindsight_urgent_slot_swaps_for_oracle":max(0,oracle_min-delivered_real)
            })
    if sum(r["urgent_research_delivered"] for r in dayrows)!=127:
        raise ValueError("STAGE54_BUDGETED_TOTAL_DRIFT")
    if sum(r["early_GT2x_actually_delivered"] for r in dayrows)!=21:
        raise ValueError("STAGE54_ACTUAL_EARLY_GT2X_DRIFT")
    assert len(dayrows)==42
    direct_possible=sum(r["early_GT2x_eligible_with_hindsight"] for r in dayrows)
    missed_due_temporal_or_signal=28-direct_possible
    return {
     "schema":SCHEMA,"source_original_Git_blobs":PIN,
     "source_real_original36_GitHub_SHA_receipts":36,
     "not_a_candidate_model":"YES",
     "ORACLE_IS_NOT_REAL_TIME_DEPLOYABLE":"HINDSIGHT_UPPER_BOUND_ONLY",
     "original_D0_early_ge5min_GT2x":28,
     "v03_actual_urgent_early2x":21,
     "early2x_have_an_eligible_v03_candidate_before_cross":direct_possible,
     "early2x_no_pre5_candidate":missed_due_temporal_or_signal,
     "absolute_upper_bound_early2x_coverage_with_perfect_future_label_budget5":pure_upper,
     "absolute_upper_bound_early2x_fraction":round(pure_upper/28,6),
     "original_frozen_v03_urgent_limit_per_UTC06_day":5,
     "total_real_candidate_events":len(entries),
     "real_research_delivered":127,
     "real_over_capacity":39,
     "sum_theoretical_urgent_slot_replacements_to_save_additional_early2x":sum(x["minimum_hindsight_urgent_slot_swaps_for_oracle"] for x in dayrows),
     "all_42_anchored_24h_cohorts":dayrows,
     "overbudget_early2x_original_events":[{
          "date":x["date"],"symbol":x["symbol"],"first_candidate_UTC":x["asof_UTC"],
          "bucket_index":x["window_day_index"],"quote15_USDT":x["quote15_USDT"],
          "ret60_pct":x["ret60_pct"]
       } for x in entries if x["GT2x_before5min"] and not x["delivered"]],
     "all_candidates_and_hindsight_labels_used_only_for_diagnostic":True,
     "do_not_change_v03_after_exposed_history":True,
     "no_future_label_allowed_in_live_priority_logic":True,
     "not_a_gmail_or_trade_execution":True,
     "other_AI_review":"NOT_DONE","Monster_deployment":"NO_GO","Frank":"UNCHANGED","Gmail":"OFF"
    }

def selftest():
    assert timestamp("2025-01-30T06:00:00Z")<timestamp("2025-01-30T06:05:00Z")
    assert (timestamp("2025-01-31T06:00:00Z")-timestamp("2025-01-30T06:00:00Z"))==ONE_DAY
    assert min(5,0)==0 and min(5,7)==5
    print("STAGE54_UTC06_DAY_SLOT_AND_HINDSIGHT_ONLY_BOUND_SELFTEST_PASS")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path)
    p.add_argument("--selftest",action="store_true")
    a=p.parse_args()
    if a.selftest:selftest();return
    if not a.out:p.error("--out required")
    m,au,cs,e=load()
    out=assess(m,au,cs,e)
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"monster_stage54_source_sha_global5_day_feasibility_oracle_upper_bound.json").write_text(
       json.dumps(out,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    with (a.out/"monster_stage54_real42_24h_source_completed_budget_and_oracle.csv").open("w",newline="",encoding="utf-8") as f:
        rows=out["all_42_anchored_24h_cohorts"]
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator="\n")
        w.writeheader();w.writerows(rows)
    print("STAGE54_HINDSIGHT_ONLY_GLOBAL_CAP_FEASIBILITY_TRUE_SOURCE_SHA_PASS "+json.dumps({
      k:out[k] for k in ("original_D0_early_ge5min_GT2x","v03_actual_urgent_early2x",
        "early2x_have_an_eligible_v03_candidate_before_cross",
        "absolute_upper_bound_early2x_coverage_with_perfect_future_label_budget5",
        "sum_theoretical_urgent_slot_replacements_to_save_additional_early2x")},sort_keys=True))
if __name__=="__main__":
    main()
