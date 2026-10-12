#!/usr/bin/env python3
"""Stage47: all-market descriptive repeated D0 WATCH vs actual minute crosses.

Facts only, NO second-ignition feature threshold, trade claim or newly trained
model. Use 5400 Stage45 source-verified binance 1m time stamps and original V4
events. Never use future GT to compute a candidate signal; here future GT is
only a grouping label *after* original signals are preserved.
"""
import argparse,collections,datetime as dt,hashlib,json,statistics
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]/"monster"/"evidence"
SOURCE=ROOT/"monster_stage45_blind_all5400_originalV4_P1v02_cases.jsonl"
METRICS=ROOT/"monster_stage45_blind_900x6_SHA_P1v02_metrics_and_gates.json"
GOOD="COMPLETE_REAL_USDM_1M_SHA_CAUSAL_V4"
P1="P1_V02_UPGRADE_IMMEDIATE_FIRST_WATCH"
SCHEMA="MONSTER_STAGE47_EXPOSED_ALL5400_ORIGINAL_D0_MULTI_WATCH_CAUSAL_TIMELINE_FACT_AUDIT_V1"
DAYS=("2025-01-09","2025-09-02","2026-01-26","2026-02-24","2026-03-28","2026-05-10")

def parse(x):return dt.datetime.fromisoformat(x.replace("Z","+00:00"))
def sha(data):return hashlib.sha256(data).hexdigest()
def load():
    summary=json.loads(METRICS.read_text(encoding="utf-8"))
    if summary.get("schema")!="MONSTER_STAGE45_ORIGINAL36_SHA_FROZEN_SIX_DAY_P1V02_FUTURES_TRUTH_V1" or (
        summary.get("source_stage45_run_id")!=38213103621
        or len(summary.get("original36_verified_GitHub_SHA_receipts",[]))!=36):
        raise ValueError("STAGE47_NOT_PROVEN_ORIGINAL36_STAGE45")
    data=SOURCE.read_bytes()
    cases=[json.loads(row) for row in data.splitlines() if row.strip()]
    if len(cases)!=5400 or len({(x["date"],x["symbol"]) for x in cases})!=5400:
        raise ValueError("STAGE47_NOT_FULL_MARKET_5400_ORIGINAL")
    return summary,cases,sha(data),sha(METRICS.read_bytes())

def audit(summary,cases,source_sha,summary_sha):
    valid=[r for r in cases if r["source_status"]==GOOD]
    positive=[r for r in valid if r["original_GT2x_1h"]=="True"]
    normal=[r for r in valid if r["original_GT2x_1h"]=="False"]
    if (len(valid),len(positive),len(normal))!=(
        summary["source_complete"],summary["GT2x_source_complete"],summary["normal_gt2x_FALSE"]):
        raise ValueError("STAGE47_ORIGINAL_SUMMARY_DIVERGED")
    result=[]
    for r in valid:
        original=r["WATCH_UTC"]
        watch=[parse(x) for x in original]
        if watch!=sorted(watch) or len(watch)!=r["watch_count"] or len(set(watch))!=len(watch):
            raise ValueError("STAGE47_ORIGINAL_WATCH_TIME_ORDER_OR_COUNT_BAD")
        crossed=parse(r["first_true_2x_HIGH_minute_UTC"]) if r["first_true_2x_HIGH_minute_UTC"] else None
        if bool(crossed)!=(r["original_GT2x_1h"]=="True"):
            raise ValueError("STAGE47_GT_VS_FIRST_REAL_MINUTE_DIFFER")
        before=[w for w in watch if crossed is not None and w<crossed]
        recent6=[w for w in before if crossed-w<=dt.timedelta(hours=6)] if crossed else []
        pre_after_first=[w for w in before[1:]] if before else []
        detail={
         "date":r["date"],"symbol":r["symbol"],"historical_gt2x":crossed is not None,
         "P1_immediate":r["p1_status"]==P1,"first_GT2x_minute":r["first_true_2x_HIGH_minute_UTC"],
         "D0_first_WATCH":original[0] if original else None,
         "D0_all_watch_count":len(watch),
         "D0_repeated_watch_count":max(0,len(watch)-1),
         "D0_strictly_before_GT2x_watch_count":len(before),
         "D0_any_second_WATCH_before_GT2x":len(pre_after_first)>0,
         "D0_watch_within_six_hours_pre_GT2x_count":len(recent6),
         "D0_first_subsequent_early_watch":(
             pre_after_first[0].isoformat().replace("+00:00","Z") if pre_after_first else None),
         "D0_NEAREST_early_watch_before_GT2x":(
             before[-1].isoformat().replace("+00:00","Z") if before else None),
         "D0_last_early_watch_lead_min":(
             round((crossed-before[-1]).total_seconds()/60,2) if before else None),
         "D0_first_WATCH_lead_GT2x_min":(
             round((crossed-watch[0]).total_seconds()/60,2) if crossed and watch else None)
        }
        result.append(detail)
    witnesses=[r for r in result if r["historical_gt2x"]]
    normals=[r for r in result if not r["historical_gt2x"]]
    def count_with_watch(rows):return sum(x["D0_all_watch_count"]>0 for x in rows)
    def count_repeat(rows):return sum(x["D0_all_watch_count"]>=2 for x in rows)
    byday=[]
    for day in DAYS:
        ww=[x for x in witnesses if x["date"]==day]
        nn=[x for x in normals if x["date"]==day]
        byday.append({"date":day,"2x_count":len(ww),"2x_with_first_WATCH":count_with_watch(ww),
         "2x_second_WATCH_before_2x":sum(x["D0_any_second_WATCH_before_GT2x"] for x in ww),
         "non2x_complete":len(nn),"non2x_any_WATCH":count_with_watch(nn),
         "non2x_repeated_WATCH":count_repeat(nn),
         "total_extra_WATCH_event_count":sum(x["D0_repeated_watch_count"] for x in ww+nn)})
    special=[r for r in result if r["symbol"]=="BULLAUSDT" and r["date"]=="2026-01-26"]
    if len(special)!=1:raise ValueError("STAGE47_BULLA_SOURCE_CASE_MISSING")
    return {"schema":SCHEMA,"original_stage45_all5400_SHA256":source_sha,
       "original_stage45_summary_SHA256":summary_sha,
       "valid_source_total":len(valid),"positive_2x":len(witnesses),
       "normal_not2x":len(normals),
       "total_valid_original_WATCH_events":sum(r["D0_all_watch_count"] for r in result),
       "distinct_coin_date_with_WATCH":count_with_watch(result),
       "positive2x_with_at_least_two_total_WATCH":count_repeat(witnesses),
       "positive2x_second_WATCH_strictly_before_GT2x":sum(r["D0_any_second_WATCH_before_GT2x"] for r in witnesses),
       "positive2x_with_at_least_one_D0_WATCH_within6h_of_GT2x":sum(bool(r["D0_watch_within_six_hours_pre_GT2x_count"]) for r in witnesses),
       "normal_not2x_with_at_least_two_WATCH":count_repeat(normals),
       "normal_not2x_with_any_WATCH":count_with_watch(normals),
       "original_total_repeated_WATCH_events":sum(r["D0_repeated_watch_count"] for r in result),
       "source_complete_by_day_and_non2x_control":byday,
       "BULLA_10x_original_D0_repeat_timeline":special[0],
       "positive2x_all_original_repeat_watch_details":sorted(witnesses,key=lambda x:(x["date"],x["symbol"])),
       "RESEARCH_ONLY_NOT_PREDICTION":True,
       "no_new_P1_candidate_or_threshold":True,"true_shared_global_8_D1_queue":"NOT_REPLAYED",
       "trade_execution":"UNVERIFIED","other_AI_review":"NOT_DONE",
       "Monster_deployment":"NO_GO","Frank":"UNCHANGED","Gmail":"OFF"}

def main():
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path,required=True)
    a=p.parse_args();s,rows,source_sha,summary_sha=load();out=audit(s,rows,source_sha,summary_sha)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(out,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print("STAGE47_ALLMARKET_STAGE45_SOURCE_SHA_REPEAT_WATCH_DIAGNOSTIC_PASS "+
          json.dumps({k:out[k] for k in ("positive_2x","positive2x_second_WATCH_strictly_before_GT2x",
          "normal_not2x_with_at_least_two_WATCH","original_total_repeated_WATCH_events")},sort_keys=True))
if __name__=="__main__":main()
