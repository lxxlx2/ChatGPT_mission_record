#!/usr/bin/env python3
"""Monster Stage24: six preregistered unseen 758-symbol historical dates.

Join Binance official 168h (1h) gross future outcomes with the original
production V4 12h (1m) WATCH replay, no forward price leaked into the scanner.
Do NOT misrepresent first-crossing-hour intrabar ordering or missing listings.
"""
import argparse
import concurrent.futures
import hashlib
import json
import statistics
import sys
import urllib.error
from collections import Counter
from datetime import date,datetime,timedelta,timezone
from pathlib import Path

try:
    import monster_v4_stage16_seven_day_labels as gt
    import monster_v4_stage20_quality_exit_holdout as source
    import monster_v4_historical_replay as replay
except ImportError:
    from scripts import monster_v4_stage16_seven_day_labels as gt
    from scripts import monster_v4_stage20_quality_exit_holdout as source
    from scripts import monster_v4_historical_replay as replay

EVIDENCE=source.archive.source.EVIDENCE
PREREG=EVIDENCE/"monster_stage24_unseen_7d_whole_market_watch_gt_prereg_20261011.json"
DATES=("2025-11-04","2025-12-04","2026-02-04","2026-04-04","2026-08-04","2026-09-04")
WORKERS=8

def git_blob_sha1(path):
    raw=Path(path).read_bytes()
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()

def frozen():
    cfg=json.loads(PREREG.read_text(encoding="utf-8"))
    if cfg.get("schema")!="MONSTER_STAGE24_FROZEN_FULL_758_SEVEN_DAY_2X5X_V4_CAUSAL_WATCH_AUDIT_V1":
        raise ValueError("STAGE24_BAD_PREREGISTRATION")
    if tuple(cfg["frozen_new_dates"])!=DATES:
        raise ValueError("STAGE24_DATE_DRIFT")
    sha=cfg["original_code_git_blobs_locked"]
    paths={
        "seven_day_hourly_label":Path(gt.__file__).resolve(),
        "sixty_hour_minute_loader":Path(source.__file__).resolve(),
        "original_v4_replayer":Path(replay.__file__).resolve(),
        "archived_symbol_inventory_evidence":EVIDENCE/"monster_stage15_archive_only_5date_actual_ci_20261011.json"}
    for k,p in paths.items():
        if git_blob_sha1(p)!=sha[k]:
            raise ValueError("STAGE24_LOCKED_ORIGINAL_SOURCE_CHANGED:"+k)
    if cfg["historical_universe"]["symbols"]!=758 or cfg["source"]["labels_gross_high"]!=[2,5,10]:
        raise ValueError("STAGE24_UNIVERSE_OR_LABEL_DRIFT")
    if cfg["source"]["watch_window"]!="Date 06:00–18:00 UTC only; never claim 168h watch window":
        raise ValueError("STAGE24_WATCH_WINDOW_CHANGED")
    return cfg

def minute_60h(symbol,day, loader=source.official_60h, scanner=replay.replay_case):
    try:
        bars,proof=loader(symbol,day)
        result=scanner({"venue":"spot","symbol":symbol,
                "cohort":"STAGE24_ALL_758_DATE_WINDOW",
                "old_watch_utc":day.isoformat()+"T12:00:00Z"},
                bars,include_zero_trade_ticks=True)
        proxies=[p["scenario_0_20_100bps"]["20"] for p in result["trade_proxies"]]
        return {
            "status":"VERIFIED_COMPLETE_60H_1M","archive_sha256":proof,
            "watch_count":result["watch_count"],
            "first_watch_utc":result["first_watch_utc"],
            "all_watch_utc":[w["utc"] for w in result["watch_events"]],
            "d1_count":result["d1_setups"],"polls":result["polls"],
            "zero_traded_minutes":result["polls_zero_trade_minute"],
            "price_proxies_20bps":proxies,
            "trading_is_not_real":True}
    except ValueError as exc:
        reason=str(exc)
        if reason.startswith("SOURCE_NOT_HISTORICALLY_AVAILABLE_HTTP_"):
            status="SOURCE_MISSING_DAY_ARCHIVE"
        elif reason in ("GAPPED_ARCHIVE_DAY","INCOMPLETE_60H_REAL_ARCHIVE",
                        "STAGE20_GAPPED_OR_INCOMPLETE_60H"):
            status="CENSORED_60H_1M_GAP"
        else:
            status="SOURCE_INTEGRITY_REJECTED"
        return {"status":status,"reason":reason[:140]}
    except urllib.error.HTTPError as exc:
        return {"status":"SOURCE_MISSING_DAY_ARCHIVE" if exc.code in (403,404) else "SOURCE_HTTP_FAILED",
                "reason":str(exc)[:140]}
    except (urllib.error.URLError,TimeoutError,OSError,ConnectionError) as exc:
        return {"status":"SOURCE_NETWORK_FAILED","reason":str(exc)[:140]}

def classification(day,hourly,minute,mult):
    if hourly["status"]!="VERIFIED_COMPLETE_168H":
        return "GT_NOT_VERIFIED"
    if not hourly["gross_high_ge_"+str(mult)+"x"]:
        return "NO_FUTURE_"+str(mult)+"X_GROSS_HIGH"
    if minute["status"]!="VERIFIED_COMPLETE_60H_1M":
        return "WATCH_SOURCE_UNVERIFIED"
    first=minute["first_watch_utc"]
    if not first:
        return "NO_WATCH_IN_FIXED_12H"
    hour_i=hourly["first_high_"+str(mult)+"x_hour_index"]
    hour0=datetime(day.year,day.month,day.day,6,tzinfo=timezone.utc)+timedelta(hours=hour_i)
    watch=datetime.fromisoformat(first.replace("Z","+00:00"))
    if watch<hour0:
        return "WATCH_BEFORE_FIRST_CROSSING_HOUR"
    if watch<hour0+timedelta(hours=1):
        return "WATCH_INSIDE_CROSSING_HOUR_UNORDERED"
    return "WATCH_AFTER_FIRST_CROSSING_HOUR"

def run_symbol(symbol,day,hourly_label=gt.label,minute_loader=minute_60h):
    hour=hourly_label(symbol,day)
    minute=minute_loader(symbol,day)
    first={str(k)+"x":classification(day,hour,minute,k) for k in (2,5,10)}
    return {"symbol":symbol,"day":day.isoformat(),
            "hourly":hour,"minute":minute,"watch_vs_2x_5x_10x":first}

def summarize(rows):
    hours=Counter(r["hourly"]["status"] for r in rows)
    minutes=Counter(r["minute"]["status"] for r in rows)
    intersect=[r for r in rows if (r["hourly"]["status"]=="VERIFIED_COMPLETE_168H"
                    and r["minute"]["status"]=="VERIFIED_COMPLETE_60H_1M")]
    valid_minute=[r for r in rows if r["minute"]["status"]=="VERIFIED_COMPLETE_60H_1M"]
    future={}
    for x in (2,5,10):
        subset=[r for r in intersect if r["hourly"]["gross_high_ge_"+str(x)+"x"]]
        classes=dict(Counter(r["watch_vs_2x_5x_10x"][str(x)+"x"] for r in subset))
        future[str(x)+"x"]={
           "verified_168h_positive_all_hourly":sum(r["hourly"]["status"]=="VERIFIED_COMPLETE_168H"
                                         and r["hourly"]["gross_high_ge_"+str(x)+"x"] for r in rows),
           "verified_168h_positive_joint_source":len(subset),
           "unambiguous_early_watch_fixed12h":classes.get("WATCH_BEFORE_FIRST_CROSSING_HOUR",0),
           "inside_crossing_hour_ambiguous":classes.get("WATCH_INSIDE_CROSSING_HOUR_UNORDERED",0),
           "late_watch":classes.get("WATCH_AFTER_FIRST_CROSSING_HOUR",0),
           "no_watch_in_fixed12h":classes.get("NO_WATCH_IN_FIXED_12H",0),
           "gt_positive_missing_minute_replay":sum(r["hourly"]["status"]=="VERIFIED_COMPLETE_168H"
             and r["hourly"]["gross_high_ge_"+str(x)+"x"]
             and r["minute"]["status"]!="VERIFIED_COMPLETE_60H_1M" for r in rows),
           "gross_close_positive_joint":sum(r["hourly"]["gross_close_ge_"+str(x)+"x"] for r in subset),
           "symbol_events":[{"symbol":r["symbol"],
                   "first_cross_hour_index":r["hourly"]["first_high_"+str(x)+"x_hour_index"],
                   "max_high_multiple":r["hourly"]["maximum_high_multiple"],
                   "first_watch_utc":r["minute"]["first_watch_utc"],
                   "classification":r["watch_vs_2x_5x_10x"][str(x)+"x"]} for r in subset]}
    cases_with_watch=[r for r in intersect if r["minute"]["watch_count"]>0]
    gt2watch=sum(r["hourly"]["gross_high_ge_2x"] for r in cases_with_watch)
    proxies=[t for r in valid_minute for t in r["minute"]["price_proxies_20bps"]]
    done=[p["net_pct"] for p in proxies if p["status"]=="PRICE_PROXY_ONLY"]
    return {
      "attempted":len(rows),
      "hourly_status":dict(hours),"minute_status":dict(minutes),
      "hourly_complete_168h":hours["VERIFIED_COMPLETE_168H"],
      "minute_complete_60h":minutes["VERIFIED_COMPLETE_60H_1M"],
      "joint_verified_168h_and_60h":len(intersect),
      "v4_watch_episodes_all_valid_minute":sum(r["minute"]["watch_count"] for r in valid_minute),
      "v4_watch_symbol_dates_all_valid_minute":sum(r["minute"]["watch_count"]>0 for r in valid_minute),
      "v4_watch_episodes_joint":sum(r["minute"]["watch_count"] for r in intersect),
      "v4_watch_symbol_dates_joint":len(cases_with_watch),
      "v4_d1_episodes_all_valid_minute":sum(r["minute"]["d1_count"] for r in valid_minute),
      "watch_symbol_dates_followed_by_verified_future_gross_2x":gt2watch,
      "watch_symbol_dates_without_future_gross_2x":len(cases_with_watch)-gt2watch,
      "original_24h_cost_assumed_trade_proxies":{
         "evaluable":len(done),"wins":sum(x>0 for x in done),
         "losses":sum(x<0 for x in done),
         "censored":len(proxies)-len(done),
         "median_net_pct":round(statistics.median(done),6) if done else None,
         "sum_independent_30_usdt_simulated_pnl":round(sum(x*.3 for x in done),6)},
      "gross_price_label_results":future}

def run(day_str, symbols_get=source.universe, evaluator=run_symbol,workers=WORKERS):
    cfg=frozen()
    if day_str not in DATES:
        raise ValueError("STAGE24_NON_PREREGISTERED_DATE")
    if not 1<=workers<=WORKERS:
        raise ValueError("STAGE24_WORKER_CAP")
    syms,inventory=symbols_get(source.frozen_manifest())
    if len(syms)!=758 or len(set(syms))!=758 or inventory["archive_only_sha256"]!=cfg["historical_universe"]["archive_only_sha256"]:
        raise ValueError("STAGE24_FROZEN_UNIVERSE_DRIFT")
    day=date.fromisoformat(day_str)
    all_rows=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futures={pool.submit(evaluator,s,day):s for s in syms}
        for future in concurrent.futures.as_completed(futures):
            row=future.result()
            if row["symbol"]!=futures[future]:
                raise ValueError("STAGE24_FUTURE_IDENTITY_MISMATCH")
            all_rows.append(row)
            if len(all_rows)%100==0:
                print("STAGE24_PROGRESS "+json.dumps({"date":day_str,"attempted":len(all_rows),
                   "complete_hours":sum(r["hourly"]["status"]=="VERIFIED_COMPLETE_168H" for r in all_rows),
                   "complete_minutes":sum(r["minute"]["status"]=="VERIFIED_COMPLETE_60H_1M" for r in all_rows)}),
                   file=sys.stderr,flush=True)
    all_rows.sort(key=lambda r:r["symbol"])
    result={"schema":"MONSTER_STAGE24_FROZEN_6D_758_FULL_MARKET_7D_GT_V4_WATCH_REPLAY_V1",
       "date":day_str,
       "original_model_thresholds_changed":False,
       "source":"BINANCE_PUBLISHER_SHA256_MONTHLY_1H_AND_DAILY_1M",
       "earliest_watch_is_06_TO_18_UTC_ONLY":True,
       "v4_24h_returns_are_not_actual_fills":True,
       "summary":summarize(all_rows),"cases":all_rows,
       "other_ai_review":"NOT_DONE","monster_deployment":"NO_GO",
       "frank":"UNTOUCHED","gmail":"OFF","trading":"NO_GO"}
    return result

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--date",required=True,choices=DATES)
    parser.add_argument("--output",required=True,type=Path)
    a=parser.parse_args()
    report=run(a.date)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    s=report["summary"]
    print("STAGE24_RESULT_JSON "+json.dumps({k:v for k,v in s.items()
       if k!="gross_price_label_results"} | {"gross_price_label_results":
       {k:{key:v for key,v in val.items() if key!="symbol_events"}
        for k,val in s["gross_price_label_results"].items()}},sort_keys=True),flush=True)
    if s["joint_verified_168h_and_60h"]<100:
        raise SystemExit("STAGE24_INSUFFICIENT_VERIFIED_JOINT")
    if any("NETWORK_FAILED" in k or "HTTP_FAILED" in k or "INTEGRITY_REJECTED" in k
           for name in ("hourly_status","minute_status") for k in s[name]):
        raise SystemExit("STAGE24_SOURCE_OR_INTEGRITY_UNVERIFIED")
if __name__=="__main__":
    main()
