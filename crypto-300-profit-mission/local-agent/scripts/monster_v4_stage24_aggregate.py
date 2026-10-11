#!/usr/bin/env python3
"""Stage24 original-artifact SHA-gated causal V4 WATCH vs 7d opportunity audit.

Every result is recomputed from the immutable six GitHub CI artifact ZIPs.
No post-hoc GT-positive universe selection; all 758 symbols on each UTC date.
Hourly first-crossing timestamp is uncertain within 1h, so ambiguous WATCH
during the crossing hour does NOT count as early.
"""
import argparse
import hashlib
import json
import statistics
import zipfile
from collections import Counter
from datetime import datetime,timedelta,timezone
from pathlib import Path

EVIDENCE=Path(__file__).resolve().parents[2]/"monster/evidence"
MANIFEST=EVIDENCE/"monster_stage24_unseen_7d_whole_market_watch_gt_prereg_20261011.json"
PROOF=EVIDENCE/"monster_stage24_6date_original_zip_shas_and_results_20261011.json"
MAX_BYTES=25_000_000
CLASS_NAMES=("WATCH_BEFORE_FIRST_CROSSING_HOUR",
             "WATCH_INSIDE_CROSSING_HOUR_UNORDERED",
             "WATCH_AFTER_FIRST_CROSSING_HOUR","NO_WATCH_IN_FIXED_12H")

def sha256(content):
    return hashlib.sha256(content).hexdigest()

def open_artifact(path, expected):
    zipdata=Path(path).read_bytes()
    if sha256(zipdata)!=expected["zip_sha256"]:
        raise ValueError("STAGE24_ZIP_SHA256_MISMATCH:"+expected["date"])
    name="monster_stage24_"+expected["date"]+".json"
    with zipfile.ZipFile(path) as f:
        if f.namelist()!=[name] or f.getinfo(name).file_size>MAX_BYTES:
            raise ValueError("STAGE24_WRONG_ZIP_MEMBER_OR_SIZE")
        raw=f.read(name)
    if sha256(raw)!=expected["raw_json_sha256"]:
        raise ValueError("STAGE24_ORIGINAL_JSON_SHA256_MISMATCH")
    obj=json.loads(raw)
    if obj.get("schema")!="MONSTER_STAGE24_FROZEN_6D_758_FULL_MARKET_7D_GT_V4_WATCH_REPLAY_V1":
        raise ValueError("STAGE24_WRONG_ARTIFACT_SCHEMA")
    if obj.get("date")!=expected["date"] or obj.get("original_model_thresholds_changed") is not False:
        raise ValueError("STAGE24_DATE_OR_MODEL_CHANGED")
    if len(obj["cases"])!=758 or len({x["symbol"] for x in obj["cases"]})!=758:
        raise ValueError("STAGE24_INCOMPLETE_758_FULL_UNIVERSE")
    for item in obj["cases"]:
        if item["day"]!=expected["date"]:
            raise ValueError("STAGE24_WRONG_CASE_DATE")
        h=item["hourly"];m=item["minute"]
        if h["status"]=="VERIFIED_COMPLETE_168H":
            if len(h.get("archive_sha256",""))!=64:
                raise ValueError("STAGE24_MISSING_OFFICIAL_MONTHLY_SHA")
        if m["status"]=="VERIFIED_COMPLETE_60H_1M":
            if len(m.get("archive_sha256",[]))!=3 or not all(
               len(x.get("sha256",""))==64 for x in m["archive_sha256"]):
                raise ValueError("STAGE24_MISSING_OFFICIAL_DAILY_SHA")
        if any(q in h["status"] for q in ("INTEGRITY_REJECTED","NETWORK_FAILED","HTTP_FAILED")):
            raise ValueError("STAGE24_BAD_HOURLY_SOURCE")
        if any(q in m["status"] for q in ("INTEGRITY_REJECTED","NETWORK_FAILED","HTTP_FAILED")):
            raise ValueError("STAGE24_BAD_MINUTE_SOURCE")
    return obj

def count_by_event(rows,x):
    valid=[r for r in rows if r["hourly"]["status"]=="VERIFIED_COMPLETE_168H"]
    joint=[r for r in valid if r["minute"]["status"]=="VERIFIED_COMPLETE_60H_1M"]
    pos_hour=[r for r in valid if r["hourly"]["gross_high_ge_"+str(x)+"x"]]
    positives=[r for r in joint if r["hourly"]["gross_high_ge_"+str(x)+"x"]]
    label=str(x)+"x"
    classes=Counter(r["watch_vs_2x_5x_10x"][label] for r in positives)
    if set(classes)-set(CLASS_NAMES):
        raise ValueError("STAGE24_UNKNOWN_2X_TIMING_CLASS")
    details=[]
    for r in positives:
        crossing_idx=r["hourly"]["first_high_"+str(x)+"x_hour_index"]
        first_watch=r["minute"]["first_watch_utc"]
        detail={"day":r["day"],"symbol":r["symbol"],
          "first_high_crossing_hour_index":crossing_idx,
          "raw_high_multiple":r["hourly"]["maximum_high_multiple"],
          "first_v4_watch_utc":first_watch,
          "watch_classification":r["watch_vs_2x_5x_10x"][label],
          "crossed_after_fixed_watch_window":crossing_idx>=12}
        if detail["watch_classification"]=="WATCH_BEFORE_FIRST_CROSSING_HOUR":
            base=datetime.fromisoformat(r["day"]+"T06:00:00+00:00")
            cross_hour_start=base+timedelta(hours=crossing_idx)
            watch=datetime.fromisoformat(first_watch.replace("Z","+00:00"))
            detail["minimum_early_lead_hours"]=round((cross_hour_start-watch).total_seconds()/3600,6)
        details.append(detail)
    early=[r["minimum_early_lead_hours"] for r in details
           if "minimum_early_lead_hours" in r]
    return {
      "verified_168h_GT":len(valid),
      "verified_joint_GT_and_V4_1m":len(joint),
      "gross_high_positive_all_GT":len(pos_hour),
      "gross_high_positive_joint":len(positives),
      "gross_close_positive_joint":sum(r["hourly"]["gross_close_ge_"+str(x)+"x"] for r in positives),
      "positive_GT_but_no_60h_minutes":len(pos_hour)-len(positives),
      "crossed_after_fixed_watch_window":sum(r["hourly"]["first_high_"+str(x)+"x_hour_index"]>=12 for r in positives),
      "timing_classes":dict(classes),
      "strict_early_count":classes["WATCH_BEFORE_FIRST_CROSSING_HOUR"],
      "strict_early_minimum_lead_hours_median":round(statistics.median(early),6) if early else None,
      "confirmed_GT_event_register":details}

def rebuild(reports,manifest):
    days=manifest["frozen_new_dates"]
    if set(reports)!=set(days) or len(days)!=6:
        raise ValueError("STAGE24_MISSING_OR_EXTRA_DATES")
    rows=[r for day in days for r in reports[day]["cases"]]
    allsymbols=[set(r["symbol"] for r in reports[day]["cases"]) for day in days]
    if not all(s==allsymbols[0] for s in allsymbols):
        raise ValueError("STAGE24_COHORT_SYMBOLS_CHANGED_BETWEEN_DATES")
    minute=[r for r in rows if r["minute"]["status"]=="VERIFIED_COMPLETE_60H_1M"]
    joint=[r for r in minute if r["hourly"]["status"]=="VERIFIED_COMPLETE_168H"]
    watch_joint=[r for r in joint if r["minute"]["watch_count"]>0]
    all_proxy=[p for r in minute for p in r["minute"]["price_proxies_20bps"]]
    exits=[x["net_pct"] for x in all_proxy if x["status"]=="PRICE_PROXY_ONLY"]
    statuses_hour=Counter(r["hourly"]["status"] for r in rows)
    statuses_minute=Counter(r["minute"]["status"] for r in rows)
    for d,source in reports.items():
        summary=source["summary"]
        if Counter(r["hourly"]["status"] for r in source["cases"])!=Counter(summary["hourly_status"]):
            raise ValueError("STAGE24_GT_STATUS_SUMMARY_MISMATCH")
        if Counter(r["minute"]["status"] for r in source["cases"])!=Counter(summary["minute_status"]):
            raise ValueError("STAGE24_MINUTE_STATUS_SUMMARY_MISMATCH")
        for mult in (2,5,10):
            value=count_by_event(source["cases"],mult)
            orig=summary["gross_price_label_results"][str(mult)+"x"]
            if value["strict_early_count"]!=orig["unambiguous_early_watch_fixed12h"] or value["gross_high_positive_joint"]!=orig["verified_168h_positive_joint_source"]:
                raise ValueError("STAGE24_SOURCE_GROSS_HIGH_WATCH_MISMATCH:"+d)
    labels={str(mult)+"x":count_by_event(rows,mult) for mult in (2,5,10)}
    non2x=len(watch_joint)-sum(x["hourly"]["gross_high_ge_2x"] for x in watch_joint)
    return {"schema":"MONSTER_STAGE24_SIX_SHA_VERIFIED_758_BY6_GROSS_HIGH_V4_RECOMPUTED_V1",
      "six_original_zip_and_json_sha256_verified":True,
      "date_count":len(days),"dates":days,
      "attempted_symbol_date":len(rows),
      "historical_universe_size":len(allsymbols[0]),
      "hourly_source_status":dict(statuses_hour),
      "minute_source_status":dict(statuses_minute),
      "verified_complete_168h":statuses_hour["VERIFIED_COMPLETE_168H"],
      "verified_complete_60h":statuses_minute["VERIFIED_COMPLETE_60H_1M"],
      "verified_joint_168h_gt_60h_watch":len(joint),
      "all_60h_v4_watch_event_count":sum(r["minute"]["watch_count"] for r in minute),
      "all_60h_v4_watch_symbol_dates":sum(r["minute"]["watch_count"]>0 for r in minute),
      "joint_watch_symbol_dates":len(watch_joint),
      "joint_watch_without_future_gross_2x":non2x,
      "gross_high_labels":labels,
      "assumed_original_v4_24h_30usdt_price_proxy":{
          "evaluable":len(exits),"wins":sum(x>0 for x in exits),
          "losses":sum(x<0 for x in exits),"censored":len(all_proxy)-len(exits),
          "median_net_pct":round(statistics.median(exits),6) if exits else None,
          "sum_independent_30u_simulated_pnl":round(sum(x*.3 for x in exits),6)},
      "date_summaries":[{"date":day,"valid_168h":reports[day]["summary"]["hourly_complete_168h"],
                        "valid_60h":reports[day]["summary"]["minute_complete_60h"],
                        "joint":reports[day]["summary"]["joint_verified_168h_and_60h"],
                        "v4_watch_events":reports[day]["summary"]["v4_watch_episodes_all_valid_minute"],
                        "gross_high_2x_joint":reports[day]["summary"]["gross_price_label_results"]["2x"]["verified_168h_positive_joint_source"]}
                       for day in days],
      "real_exchangeinfo_history":"UNVERIFIED",
      "real_L2_order_fill":"UNVERIFIED","other_AI_review":"NOT_DONE",
      "monster_deployment":"NO_GO","real_gmail":"OFF","trading":"NO_GO"}

def aggregate(zips,proof=PROOF,manifest=MANIFEST):
    record=json.loads(Path(proof).read_text(encoding="utf-8"))
    cfg=json.loads(Path(manifest).read_text(encoding="utf-8"))
    frozen=cfg["frozen_new_dates"]
    sources={x["date"]:x for x in record["artifacts"]}
    if len(frozen)!=6 or len(sources)!=6 or len(zips)!=6 or set(sources)!=set(frozen):
        raise ValueError("STAGE24_EXACT_SIX_PREREG_DATES_REQUIRED")
    reports={}
    for path in zips:
        with zipfile.ZipFile(path) as z:
            members=z.namelist()
        if len(members)!=1:
            raise ValueError("STAGE24_MULTIPLE_MEMBERS")
        day=members[0].removeprefix("monster_stage24_").removesuffix(".json")
        if day not in sources or day in reports:
            raise ValueError("STAGE24_DUPLICATE_OR_UNFROZEN_DATE")
        reports[day]=open_artifact(path,sources[day])
    return rebuild(reports,cfg)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--artifact-zips",nargs=6,required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    args=p.parse_args()
    data=aggregate(args.artifact_zips)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(data,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("STAGE24_AGGREGATE "+json.dumps({k:v for k,v in data.items() if k not in ("gross_high_labels","date_summaries")}|
       {"gross_high_labels":{k:{s:v for s,v in obj.items() if s!="confirmed_GT_event_register"}
          for k,obj in data["gross_high_labels"].items()}},sort_keys=True),flush=True)
if __name__=="__main__":
    main()
