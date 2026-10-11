#!/usr/bin/env python3
"""Stage30: six preregistered NEW 19th days, all frozen 758 Spot USDT symbols.

True official publisher-checksummed MONTHLY 1h GT; ten publisher-checksummed
DAILY 1m archives per valid coin; exactly the old Stage26 168h, one SQLite
per symbol calling unchanged production V4 observe_snapshot/process_queue.
GT never enters the V4 signals, only post-scoring verification. No real buys.
"""
import argparse
import concurrent.futures
import json
import sys
from collections import Counter
from datetime import date
from pathlib import Path

try:
    import monster_v4_stage16_seven_day_labels as gt
    import monster_v4_stage20_quality_exit_holdout as inv
    import monster_v4_stage24_aggregate as oldzip
    import monster_v4_stage26_continuous168h as runner
    import monster_v4_shadow as production
except ImportError:
    from scripts import monster_v4_stage16_seven_day_labels as gt
    from scripts import monster_v4_stage20_quality_exit_holdout as inv
    from scripts import monster_v4_stage24_aggregate as oldzip
    from scripts import monster_v4_stage26_continuous168h as runner
    from scripts import monster_v4_shadow as production

PROOF=oldzip.PROOF
EVIDENCE=oldzip.EVIDENCE
PREREG=EVIDENCE/"monster_stage30_six_new_dates_full758_7d_watch_holdout_prereg_20261011.json"
SHARDS=6
EXPECTED_SYMBOLS=758

def frozen():
    p=json.loads(PREREG.read_text(encoding="utf-8"))
    if p.get("schema")!="MONSTER_STAGE30_NEW_SIX_DATE_758_FULL168H_ORIGINAL_V4_HOLDOUT_FROZEN_BEFORE_SOURCE_V1":
        raise ValueError("STAGE30_NOT_FROZEN")
    days=["2025-01-19","2025-04-19","2025-07-19","2025-10-19","2026-04-19","2026-07-19"]
    if p["new_dates_UTC"]!=days or p["cohort_source"]["original_stage24_known_758_universe_artifact_id"]!=11700651924:
        raise ValueError("STAGE30_DATE_COHORT_FROZEN_CHANGED")
    code={
      "production_V4":production.__file__,
      "stage26_scanner":runner.__file__,
      "stage16_hourly_GT":gt.__file__,
      "stage20_758_snapshot_universe":inv.__file__,
      "stage24_old_source_SHA_decoder":oldzip.__file__
    }
    for k,f in code.items():
        if runner.git_sha(f)!=p["original_frozen_code_blobs"][k]:
            raise ValueError("STAGE30_ORIGINAL_MODEL_OR_SOURCE_CHANGED:"+k)
    if p["primary_success_gates"]["burst_distinct_market_poll_episodes_min_for_claim"]!=6 or (
            p["primary_success_gates"]["burst_distinct_calendar_dates_min_for_claim"]!=3):
        raise ValueError("STAGE30_BURST_GATE_CHANGED")
    return p

def original_universe(path):
    cfg=frozen()
    original=cfg["cohort_source"]
    if original["original_stage24_known_758_universe_artifact_id"]!=11700651924:
        raise ValueError("STAGE30_COHORT_SOURCE_CHANGED")
    results=oldzip.open_artifact(path,{
        "date":original["old_day"],
        "zip_sha256":original["zip_sha256"],
        "raw_json_sha256":original["json_sha256"]})
    symbols=sorted(x["symbol"] for x in results["cases"])
    if len(symbols)!=EXPECTED_SYMBOLS or len(set(symbols))!=EXPECTED_SYMBOLS or not all(
          s.endswith("USDT") and s.isascii() for s in symbols):
        raise ValueError("STAGE30_FROZEN_UNIVERSE_758_BAD")
    return symbols

def eval_one(symbol,day):
    hourly=gt.label(symbol,day)
    if hourly.get("symbol")!=symbol:
        raise ValueError("STAGE30_GT_SYMBOL_IDENTITY")
    if hourly["status"] not in ("MONTH_ARCHIVE_MISSING_404","VERIFIED_COMPLETE_168H","CENSORED_7D_HOURLY_GAP"):
        raise RuntimeError("STAGE30_OFFICIAL_HOURLY_NETWORK_OR_INTEGRITY_FAILURE:"+str(hourly))
    if hourly["status"]=="VERIFIED_COMPLETE_168H" and len(hourly.get("archive_sha256",""))!=64:
        raise RuntimeError("STAGE30_HOURLY_GT_PUBLISHER_SHA_NOT_PRESENT")
    source={"symbol":symbol,"hourly":hourly}
    result=runner.evaluate_one(source,day)
    result["hourly_GT_monthly_SHA256"]=hourly.get("archive_sha256")
    result["hourly_GT_original_status"]=hourly["status"]
    return result

def summarize(rows):
    valid=[x for x in rows if x["status"]=="COMPLETE_168H_CONTINUOUS_V4"]
    statuses=Counter(x["status"] for x in rows)
    result={"attempted":len(rows),"source_status_counts":dict(statuses),
        "joint_verifiable":len(valid),
        "watch_events":sum(x["continuous"]["watch_count"] for x in valid),
        "D1_SETUPS":sum(x["continuous"]["setups"] for x in valid),
        "full_V4_3m_polls":sum(x["continuous"]["polls"] for x in valid),
        "prior_24h_source_warmup_each_case":True,
        "source_missing_not_no_watch":True}
    for multiple in (2,5,10):
        matching=[x for x in valid if x["labels"][str(multiple)+"x"]["gross_hourly_high_gt"]]
        classes=Counter(x["labels"][str(multiple)+"x"]["classification"] for x in matching)
        result["gross_"+str(multiple)+"x"]={
            "source_verifiable_positive_coin_dates":len(matching),
            "early_watch":classes["WATCH_BEFORE_OR_AT_REAL_FIRST_1M_CROSS"],
            "late_watch":classes["WATCH_AFTER_REAL_FIRST_1M_CROSS"],
            "no_watch":classes["NO_WATCH_IN_CONTINUOUS_168H"],
            "source_censored_positive_1h_only":sum(
              x["status"]!="COMPLETE_168H_CONTINUOUS_V4" and
              x.get("hourly_status")=="VERIFIED_COMPLETE_168H" for x in rows)}
    original=[p["proxy_20bps"] for r in valid for p in r["continuous"]["trade_proxies"]]
    prices=[x["net_pct"] for x in original if x["status"]=="PRICE_PROXY_ONLY"]
    result["unfiltered_original_WATCH_price_proxy"]={
        "observed":len(original),
        "evaluable":len(prices),
        "wins":sum(x>0 for x in prices),
        "losses":sum(x<0 for x in prices),
        "not_evaluable_or_original_overlap":len(original)-len(prices),
        "independent_30U_net_sum":round(sum(x*0.3 for x in prices),6)}
    return result

def replay_shard(date_utc,shard,stage24_zip,workers=2):
    cfg=frozen()
    if date_utc not in cfg["new_dates_UTC"] or shard not in range(SHARDS):
        raise ValueError("STAGE30_UNREGISTERED_DAY_OR_SHARD")
    if workers not in (1,2):raise ValueError("STAGE30_EXCESSIVE_SOURCE_THREADS")
    symbols=original_universe(stage24_zip)
    selected=[symbol for index,symbol in enumerate(symbols) if index%SHARDS==shard]
    if len(selected) not in (126,127):raise ValueError("STAGE30_SOURCE_SHARD_SIZE_MISMATCH")
    day=date.fromisoformat(date_utc)
    rows=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        jobs={pool.submit(eval_one,s,day):s for s in selected}
        for job in concurrent.futures.as_completed(jobs):
            item=job.result()
            if item["symbol"]!=jobs[job]:raise ValueError("STAGE30_PRICE_CASE_SYMBOL_CHANGED")
            rows.append(item)
            if len(rows)%20==0:
                print("STAGE30_PROGRESS "+json.dumps({"date":date_utc,"shard":shard,
                      "completed":len(rows),"target":len(selected)}),
                      file=sys.stderr,flush=True)
    rows.sort(key=lambda x:x["symbol"])
    report={"schema":"MONSTER_STAGE30_NEW_FROZEN_758x6_FULL168H_ORIGINAL_V4_SHA_VERIFIED_V1",
       "date":date_utc,"shard":shard,"shard_total":SHARDS,
       "original_source_758_all_attempted":True,
       "raw_hourly_GT_not_signal":True,
       "source_zip_SHA_is_publisher_verified_for_each_complete_case":True,
       "source_calendar_new_and_precommitted":True,
       "original_watch_and_D1_production_functions_unchanged":True,
       "model_or_threshold_tuned_after_data":False,
       "summary":summarize(rows),"cases":rows,
       "retrospective_historical_prices_not_real_orderfills":True,
       "independent_other_AI_review":"NOT_DONE","deployment":"NO_GO",
       "trading":"NO_GO","gmail":"OFF","frank":"UNCHANGED"}
    source_errors=[k for k in report["summary"]["source_status_counts"]
       if "NETWORK" in k or "INTEGRITY_REJECTED" in k or "HTTP_FAILED" in k]
    if source_errors:
        raise RuntimeError("STAGE30_FAIL_CLOSED_SOURCE_ERRORS:"+repr(source_errors))
    return report

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--date",required=True)
    p.add_argument("--shard",type=int,required=True)
    p.add_argument("--original-stage24-zip",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    result=replay_shard(args.date,args.shard,args.original_stage24_zip)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("STAGE30_RESULT_JSON "+json.dumps(result["summary"],sort_keys=True),flush=True)
if __name__=="__main__":main()
