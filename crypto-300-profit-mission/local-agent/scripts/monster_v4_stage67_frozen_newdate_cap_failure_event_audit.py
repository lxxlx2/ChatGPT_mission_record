#!/usr/bin/env python3
"""Stage67: independent post-hoc audit of Stage66 real global 24h cap failures.

Frozen historical GT2x sources, old vs new fates; never optimizes thresholds.
Fail status prioritizes strategy failures even with underpowered samples.
All rankings are as-of quote tie-breaks only; future GT is evaluation-only.
"""
from __future__ import annotations
import argparse
import collections
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

E=Path(__file__).resolve().parents[2]/"monster"/"evidence"
GT=E/"monster_stage65_new3_full2700_hourly_official_source_SHA.jsonl"
EVAL=E/"monster_stage66_new3_full2700_global_cap5_firstD0_vs_P1v03_summary.json"
FATES=E/"monster_stage66_firstD0_first5_full2700_vs_oldP1_urgent_fates.jsonl"
PINS={
    GT.name:"98ea5137d97307da9fb614b7707f435997d9bee9",
    EVAL.name:"5305f0cbe482691a01575a6bb368dbe8422035e8",
    FATES.name:"9b4b64f133853f0effc7e47d8b1b8c35cb6d5d81",
}
SCHEMA="MONSTER_STAGE67_SOURCE_LOCKED_NEW_DATE_FULL5_WINNERS_GLOBAL_CAP_FAILURE_V1"
KINDS=("FIRST_D0_FIRST5","OLD_P1V03")
GT_GOOD="COMPLETE_168H_OFFICIAL_PUBLISHER_SHA"


def blob(path):
    raw=path.read_bytes()
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()


def read():
    for p in (GT,EVAL,FATES):
        if blob(p)!=PINS[p.name]:
            raise ValueError("STAGE67_ORIGINAL_IMMUTABLE_SOURCE_GIT_BLOB_CHANGED "+p.name)
    full=[json.loads(s) for s in GT.read_text(encoding="utf-8").splitlines() if s]
    eval_=json.loads(EVAL.read_text(encoding="utf-8"))
    fate=[json.loads(s) for s in FATES.read_text(encoding="utf-8").splitlines() if s]
    if len(full)!=2700 or eval_["original_all_archive_attempted"]!=2700:
        raise ValueError("STAGE67_ALL2700_FUTURES_UNIVERSE_NOT_PRESENT")
    if (eval_["original_verified_2x"],eval_["original_1m_and_1h_source_valid"],
        eval_["new_first5_urgent"],eval_["old_P1v03_urgent"])!=(5,1497,91,50):
        raise ValueError("STAGE67_STAGE66_GLOBAL_UNIVERSE_OR_BUDGET_DRIFT")
    winners=[r for r in full if r["source_status"]==GT_GOOD and r["gt2x"]]
    if len(winners)!=5 or len({(r["date"],r["symbol"]) for r in winners})!=5:
        raise ValueError("STAGE67_ORIGINAL_FIVE_2X_GT_SOURCE_DRIFT")
    if len(fate)!=252 or len({(r["allocation"],r["date"],r["symbol"]) for r in fate})!=252:
        raise ValueError("STAGE67_ORIGINAL_ALL_ALLOCATION_FATES_DRIFT")
    if collections.Counter(r["allocation"] for r in fate)!={"FIRST_D0_FIRST5":196,"OLD_P1V03":56}:
        raise ValueError("STAGE67_ORIGINAL_FIRSTD0_AND_P1_CANDIDATES_DRIFT")
    return winners,eval_,fate


def minute(s):
    t=datetime.fromisoformat(s.replace("Z","+00:00"))
    if t.utcoffset().total_seconds()!=0 or t.second or t.microsecond:
        raise ValueError("STAGE67_INVALID_ORIGINAL_MINUTE_UTC")
    return int(t.timestamp()//60)


def audit(winners,old_summary,fates):
    by={(r["allocation"],r["date"],r["symbol"]):r for r in fates}
    if len(by)!=len(fates):
        raise ValueError("STAGE67_DUPLICATE_SOURCE_FATE")
    cases=[]
    captured={k:0 for k in KINDS}
    facts_by_strategy={}
    for name in KINDS:
        own=[r for r in fates if r["allocation"]==name]
        ordinary=[r for r in own if r["urgent_under_cap_research"] and not r["original_hourly_gt2x_EVALUATION_ONLY"]]
        selected=[r for r in own if r["urgent_under_cap_research"]]
        if len(ordinary)!=(89 if name==KINDS[0] else 48):
            raise ValueError("STAGE67_NON2X_URGENT_BURDEN_DRIFT")
        by_date={}
        for d in sorted({x["date"] for x in own}):
            xs=[x for x in own if x["date"]==d]
            by_date[d]={"all_candidates":len(xs),
                        "allocated_under_same_global_24h_cap":sum(x["urgent_under_cap_research"] for x in xs),
                        "ordinary_non2x_urgent":sum(x["urgent_under_cap_research"] and not x["original_hourly_gt2x_EVALUATION_ONLY"] for x in xs)}
        slots=collections.Counter((x["date"],x["utc06_24h_slot"]) for x in selected)
        if any(x>5 for x in slots.values()):
            raise ValueError("STAGE67_GLOBAL_24H_BUDGET_EXCEEDED")
        facts_by_strategy[name]={
            "all_source_verified_qualifying_candidates":len(own),
            "urgent_under_cap":len(selected),
            "non2x_urgent_descriptive_only":len(ordinary),
            "non2x_urgent_fraction":f"{len(ordinary)}/{len(selected)}",
            "by_date":by_date,
        }
    for winner in sorted(winners,key=lambda q:(q["date"],q["symbol"])):
        case={
            "date":winner["date"],"symbol":winner["symbol"],
            "historical_7day_GT2x_HOURLY_AND_REAL1M_SOURCE_VERIFIED":True,
            "calendar_peak_multiple_NOT_TRADE":winner["max_high_multiple"],
            "per_strategy":{},
        }
        for name in KINDS:
            fate=by.get((name,winner["date"],winner["symbol"]))
            if fate is None:
                case["per_strategy"][name]={"candidate":False,"miss_reason":"NEVER_QUALIFIED"}
                continue
            group=sorted((r for r in fates if
                    r["allocation"]==name and r["date"]==fate["date"] and
                    r["utc06_24h_slot"]==fate["utc06_24h_slot"]),
                key=lambda r:(r["time_UTC"],-float(r["asof_quote15_USDM_for_same_tick_ranking"]),r["symbol"]))
            n=next(i+1 for i,r in enumerate(group) if r["symbol"]==winner["symbol"])
            if n<=5 and not fate["urgent_under_cap_research"]:
                raise ValueError("STAGE67_GAVE_UP_EARLY_SLOT_BEFORE_CAP")
            if n>5 and fate["urgent_under_cap_research"]:
                raise ValueError("STAGE67_CAP_TIE_OR_RANK_DRIFT")
            t=fate["first_2x_HIGH_UTC_EVALUATION_ONLY"]
            if not t:
                raise ValueError("STAGE67_WINNER_MISSING_MINUTE_GT2X_TIME")
            delta=minute(t)-minute(fate["time_UTC"])
            prev=[x["symbol"] for x in group[:n-1] if x["urgent_under_cap_research"]]
            flag=bool(fate["urgent_under_cap_research"] and delta>=5)
            captured[name]+=int(flag)
            case["per_strategy"][name]={
                "candidate":True,"asof_qualified_UTC":fate["time_UTC"],
                "first_actual_GT2x_HIGH_UTC_EVALUATION_ONLY":t,
                "lead_minutes_at_signal":delta,
                "asof_candidate_rank_within_UTC06_24h":n,
                "original_same_UTC06_24h_slot":fate["utc06_24h_slot"],
                "eligible_at_least5m_before_high":delta>=5,
                "under_cap_urgent":bool(fate["urgent_under_cap_research"]),
                "captured_early_by_research_urgent":flag,
                "miss_reason":"CAP_FULL" if not fate["urgent_under_cap_research"]
                      else "QUALIFIED_TOO_LATE" if delta<5 else None,
                "five_preceding_urgent_coins" : prev,
            }
        cases.append(case)
    if captured!={KINDS[0]:2,KINDS[1]:2}:
        raise ValueError("STAGE67_ORIGINAL_ST66_TWO_V_TWO_GT2X_CAPTURE_MISMATCH")
    rules=old_summary["quality_gates"]
    if rules["minimum_20_source_valid_2x"] is not False or rules["new_first5_retains_80pct_original_D0_early5_2x"] is not False:
        raise ValueError("STAGE67_STAGE66_REAL_FAILURE_GATES_NOT_PRESENT")
    first_set={x["symbol"] for x in cases if x["per_strategy"][KINDS[0]].get("captured_early_by_research_urgent")}
    old_set={x["symbol"] for x in cases if x["per_strategy"][KINDS[1]].get("captured_early_by_research_urgent")}
    if first_set!={"HFTUSDT","PIPPINUSDT"} or old_set!={"HFTUSDT","HUSDT"}:
        raise ValueError("STAGE67_REAL_CAPTURED_COIN_SET_UNEXPECTED")
    return {
        "schema":SCHEMA,"immutable_input_blobs":PINS,
        "all_original_USDM_archive_attempts":2700,
        "real_1h_and_1m_price_source_valid":old_summary["original_1m_and_1h_source_valid"],
        "original_7day_GT2x_count":len(winners),
        "original_D0_at_least5m_early_GT2x":old_summary["original_D0_at_least_5m_pre2x"],
        "new_first5_delivered_early_GT2x":captured[KINDS[0]],
        "old_P1_delivered_early_GT2x":captured[KINDS[1]],
        "new_first5_early_2x_retention_pct_of_original_D0":str(100*captured[KINDS[0]]/5),
        "frozen_recall_floor_pct":80,
        "frozen_GT2x_event_minimum":20,
        "rejection_gates":{
            "D0_FIRST5_STRATEGY_RECALL_BELOW_PREDECLARED_80_PCT":True,
            "INDEPENDENT_NEW_DATE_GT2X_COUNT_BELOW_PREDECLARED_20":True,
            "FIRST5_LOSES_OLD_P1_CAPTURE_OF_HUSDT":True,
            "NO_SOURCE_VERIFIED_GT5X_OR_GT10X_TO_TEST_BIG_WINNER_RECALL":True,
            "NO_SPOT_ALPHA_DEX_HISTORICAL_EXECUTION_PROOF":True,
            "OTHER_AI_INDEPENDENT_REVIEW_NOT_DONE":True,
        },
        "truthful_combined_release_verdict":"REJECTED_AND_UNDERPOWERED_NOT_A_DEPLOYABLE_STRATEGY",
        "original_Stage66_summary_verdict":"INSUFFICIENT_NEW_DATE_GT2X_POWER",
        "WHY_STAGE66_SUMMARY_ALONE_WAS_TOO_WEAK":"underpowered should not hide observed frozen 40%-vs-80% recall failure; Stage67 carries both facts without modifying source",
        "new_captured_set":sorted(first_set),"original_P1_captured_set":sorted(old_set),
        "strategy_research_burden":facts_by_strategy,
        "five_true_2x_event_fates":cases,
        "FUTURES_HIGH_IS_NOT_EXECUTABLE_SELL":True,
        "NO_NEW_RANKING_RULE_OR_THRESHOLD_FIT":True,
        "NOT_REALIZED_TRADE_RETURN":True,
        "NO_ASSUMED_ORDER_AMOUNT":True,
        "P1V03":"REJECTED","MONSTER_DEPLOY":"NO_GO",
        "OTHER_AI_REVIEW":"NOT_DONE","GMAIL":"OFF","AUTOTRADE":"NO_GO",
    }


def test():
    assert minute("2025-07-01T14:36:00Z") +846 == minute("2025-07-02T04:42:00Z")
    assert minute("2025-11-27T19:30:00Z") +15 == minute("2025-11-27T19:45:00Z")
    assert 2/5<0.8 and 5<20
    print("STAGE67_RECALL_FAILURE_AND_UNDERPOWER_DISTINCT_NO_NET_PROFIT_SELFTEST_PASS")


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--selftest",action="store_true")
    ap.add_argument("--out",type=Path)
    a=ap.parse_args()
    if a.selftest:test();return
    if not a.out:ap.error("--out required")
    out=audit(*read())
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"monster_stage67_five_gt2x_global_cap_miss_reason_and_release_verdict.json").write_text(
        json.dumps(out,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf-8")
    print("STAGE67_VERIFIED_FIVE_2X_REAL_MINUTE_FAILURE_DIAGNOSIS "+json.dumps({
        "captured_new":out["new_first5_delivered_early_GT2x"],
        "captured_old":out["old_P1_delivered_early_GT2x"],
        "first5_urgent":out["strategy_research_burden"][KINDS[0]]["urgent_under_cap"],
        "old_P1_urgent":out["strategy_research_burden"][KINDS[1]]["urgent_under_cap"],
        "verdict":out["truthful_combined_release_verdict"]},sort_keys=True))


if __name__=="__main__":
    main()
