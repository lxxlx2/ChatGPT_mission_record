#!/usr/bin/env python3
"""Stage46: factual full Stage45 SHA-verified original5400 event-case review.

One full pass over the *already publisher-SHA-verified* Stage45 full5400
results, not a new trading/model candidate or frozen threshold optimizer.
Report every 2x/5x/10x true 1m HIGH case and precise original D0/P1 times,
including censoring and all non2x P1 burden by six 7d windows.
"""
from __future__ import annotations
import argparse,collections,csv,datetime as dt,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]/"monster"/"evidence"
SUMMARY=ROOT/"monster_stage45_blind_900x6_SHA_P1v02_metrics_and_gates.json"
CASES=ROOT/"monster_stage45_blind_all5400_originalV4_P1v02_cases.jsonl"
GOOD="COMPLETE_REAL_USDM_1M_SHA_CAUSAL_V4"
P1="P1_V02_UPGRADE_IMMEDIATE_FIRST_WATCH"
VERSION="MONSTER_STAGE46_ORIGINAL_STAGE45_SHA_POSTRUN_5X10X_REAL_1M_MISS_CASE_AUDIT_V1"
DAYS=("2025-01-09","2025-09-02","2026-01-26","2026-02-24","2026-03-28","2026-05-10")

def sha(raw):return hashlib.sha256(raw).hexdigest()
def read():
    summary=json.loads(SUMMARY.read_text(encoding="utf-8"))
    if summary["schema"]!="MONSTER_STAGE45_ORIGINAL36_SHA_FROZEN_SIX_DAY_P1V02_FUTURES_TRUTH_V1":
        raise ValueError("STAGE46_CANNOT_AUDIT_UNVERIFIED_STAGE45_AGGREGATE")
    if summary["source_stage45_run_id"]!=38213103621 or len(summary["original36_verified_GitHub_SHA_receipts"])!=36:
        raise ValueError("STAGE46_REAL_ORIGINAL36_GITHUB_SHA_REQUIRED")
    raw=CASES.read_bytes()
    rows=[json.loads(x) for x in raw.splitlines() if x.strip()]
    if len(rows)!=5400 or len({(r["date"],r["symbol"]) for r in rows})!=5400:
        raise ValueError("STAGE46_ORIGINAL5400_MISSING_OR_DUPLICATE")
    return summary,rows,sha(raw),sha(SUMMARY.read_bytes())

def summarize(summary,rows,source_sha,summary_sha):
    good=[r for r in rows if r["source_status"]==GOOD]
    gt2=[r for r in good if r["original_GT2x_1h"]=="True"]
    gt5=[r for r in good if r["original_GT5x_1h"]=="True"]
    gt10=[r for r in good if r["original_GT10x_1h"]=="True"]
    normal=[r for r in good if r["original_GT2x_1h"]=="False"]
    p1=[r for r in good if r["p1_status"]==P1]
    if (len(good),len(gt2),len(gt5),len(gt10),len(normal),len(p1))!=(
        summary["source_complete"],summary["GT2x_source_complete"],
        summary["GT5x_source_complete"],summary["GT10x_source_complete"],
        summary["normal_gt2x_FALSE"],summary["P1_upgraded_distinct_coin_dates"]):
        raise ValueError("STAGE46_SOURCE_AND_COUNTS_MUST_MATCH_ORIGINAL_AGGREGATE")
    if not set((r["date"],r["symbol"]) for r in gt10).issubset(set((r["date"],r["symbol"]) for r in gt5)):
        raise ValueError("STAGE46_GROSS_10X_MUST_BE_GT5")
    if not set((r["date"],r["symbol"]) for r in gt5).issubset(set((r["date"],r["symbol"]) for r in gt2)):
        raise ValueError("STAGE46_GROSS_5X_MUST_BE_GT2")
    maxwins=[]
    for r in sorted(gt5,key=lambda x:(x["date"],x["symbol"])):
        d={"date":r["date"],"symbol":r["symbol"],"gt5x":True,
           "gt10x":r["original_GT10x_1h"]=="True",
           "first_GT2x_HIGH_utc":r["first_true_2x_HIGH_minute_UTC"],
           "first_GT5x_HIGH_utc":r["first_real_1m_HIGH_gt5x_UTC"],
           "first_GT10x_HIGH_utc":r["first_real_1m_HIGH_gt10x_UTC"],
           "D0_first_WATCH_utc":r["WATCH_UTC"][0] if r["WATCH_UTC"] else None,
           "D0_number_of_WATCH_events":r["watch_count"],
           "D0_vs_GT2x":r["classification"],
           "D0_vs_GT5x":r["watch_vs_gt5x_class"],
           "D0_vs_GT10x":r["watch_vs_gt10x_class"],
           "D0_nearest_early_GT2x_lead_minutes":r["nearest_strictly_earlier_WATCH_lead_min"],
           "D0_nearest_early_GT5x_lead_minutes":r["pre_cross_nearest_watch_gt5x_lead_min"],
           "D0_nearest_early_GT10x_lead_minutes":r["pre_cross_nearest_watch_gt10x_lead_min"],
           "P1_status":r["p1_status"],
           "P1_first_decision_utc":r.get("p1_decision_UTC"),
           "P1_before_gt2x":r.get("P1_before_1m_high_2x"),
           "P1_before_gt5x":r.get("P1_before_1m_high_5x"),
           "P1_before_gt10x":r.get("P1_before_1m_high_10x"),
           "P1_trigger_arm":r.get("p1_trigger_arm"),
           "P1_ret60_pct":r.get("p1_ret60_pct"),
           "P1_quote15_USDT":r.get("p1_quote15_usdt")}
        if not d["first_GT5x_HIGH_utc"] or not d["first_GT2x_HIGH_utc"]:
            raise ValueError("STAGE46_FIRST_REAL_MINUTE_HIGH_MISSING")
        maxwins.append(d)
    missed=[{
      "date":r["date"],"symbol":r["symbol"],"source_verified":True,
      "first_GT2x_HIGH_utc":r["first_true_2x_HIGH_minute_UTC"],
      "D0_classification":r["classification"],
      "D0_first_watch_utc":r["WATCH_UTC"][0] if r["WATCH_UTC"] else None,
      "P1_status":r["p1_status"],
      "P1_first_utc":r.get("p1_decision_UTC"),
      "P1_before_2x":r.get("P1_before_1m_high_2x")
      } for r in gt2 if r["classification"]!="STRICTLY_EARLY_WATCH"]
    controls_by_day=collections.defaultdict(lambda:{"complete_non2x":0,"non2x_D0_WATCH":0,
                    "non2x_D0_EVENTS":0,"non2x_P1":0,"complete_2x":0,
                    "2x_D0_early":0,"2x_P1":0})
    for r in good:
        p=controls_by_day[r["date"]]
        if r["original_GT2x_1h"]=="False":
            p["complete_non2x"]+=1
            p["non2x_D0_WATCH"]+=int(r["watch_count"]>0)
            p["non2x_D0_EVENTS"]+=r["watch_count"]
            p["non2x_P1"]+=int(r["p1_status"]==P1)
        else:
            p["complete_2x"]+=1
            p["2x_D0_early"]+=int(r["classification"]=="STRICTLY_EARLY_WATCH")
            p["2x_P1"]+=int(r["p1_status"]==P1)
    byday=[{"date":date,**controls_by_day[date]} for date in DAYS]
    total_p1_arms=collections.Counter(r.get("p1_trigger_arm","NONE") for r in p1)
    source_censored=collections.Counter(r["source_status"] for r in rows if r["source_status"]!=GOOD)
    return {"schema":VERSION,"frozen_candidate":"P1v02_NOT_TUNED_AFTER_STAGE44",
        "original_stage45_full5400_JSONL_SHA256":source_sha,
        "original_stage45_metrics_SHA256":summary_sha,
        "source_cases_verified_5400":len(rows),"source_complete":len(good),
        "source_censored_by_status":dict(source_censored),
        "positive_gt2x":len(gt2),"positive_gt5x":len(gt5),"positive_gt10x":len(gt10),
        "all_GT5x_and_GT10x_original_actual_minute_signals":maxwins,
        "GT2x_not_strictly_early_D0":missed,
        "GT5x_p1_did_not_early_detect":[r["symbol"]+"|"+r["date"] for r in maxwins
             if not r["P1_before_gt5x"]],
        "GT10x_p1_did_not_early_detect":[r["symbol"]+"|"+r["date"] for r in maxwins
             if r["gt10x"] and not r["P1_before_gt10x"]],
        "P1_ret60_vs_quote_trigger_counts":dict(total_p1_arms),
        "historical_per_window_non2x_watch_burden":byday,
        "verdict_from_original_aggregator":summary["verdict"],
        "frozen_gates_from_original_aggregator":summary["frozen_P1_v02_gates"],
        "no_new_thresholds_or_model_fitting":True,
        "real_trade_profit":"UNVERIFIED_NO_ORDERBOOK",
        "independent_other_AI_review":"NOT_DONE","Frank":"UNCHANGED",
        "Gmail":"OFF","Monster_deploy":"NO_GO"}

def main():
    p=argparse.ArgumentParser();p.add_argument("--output-dir",type=Path,required=True)
    a=p.parse_args();s,r,sh,sj=read();out=summarize(s,r,sh,sj)
    a.output_dir.mkdir(parents=True,exist_ok=True)
    (a.output_dir/"monster_stage46_original45_SHA_winners_normalburden_audit.json").write_text(
        json.dumps(out,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    name=a.output_dir/"monster_stage46_all_verified_gt5x_gt10x_true_first_cross_vs_D0_P1.csv"
    data=out["all_GT5x_and_GT10x_original_actual_minute_signals"]
    if data:
        with name.open("w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f,fieldnames=list(data[0]),extrasaction="raise",lineterminator="\n")
            w.writeheader();w.writerows(data)
    else:
        name.write_text("NO_5X_EVENTS\n")
    print("STAGE46_FROZEN_REAL_FIRST_MINUTE_5X_10X_SOURCE_CASES_AUDIT "+json.dumps({
      "source_complete":out["source_complete"],
      "GT2x":out["positive_gt2x"],"GT5x":out["positive_gt5x"],
      "GT10x":out["positive_gt10x"],"D0_missed_2x":len(out["GT2x_not_strictly_early_D0"]),
      "P1_missed_5x":len(out["GT5x_p1_did_not_early_detect"]),
      "original_gate":out["verdict_from_original_aggregator"]},sort_keys=True))
if __name__=="__main__":main()
