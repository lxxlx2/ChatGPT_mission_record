#!/usr/bin/env python3
"""Stage38 12 original GitHub SHA ZIPs + source SHA original V4 causal assessment.

Retrospective GT2x-enriched 52 vs 120 pre-frozen label-blind controls.
Any missing 1m source CENSORED, not a successful no-WATCH classifier.
No full USD-M universe recall claim, no new thresholds, no trading.
"""
import argparse,collections,csv,hashlib,json,statistics,zipfile
from pathlib import Path
DAYS=("2025-01-19","2025-04-19","2025-07-19","2025-10-19","2026-04-19","2026-07-19")
SCHEMA="MONSTER_STAGE38_ORIGINAL12_USDM_V4_REAL_1M_CAUSAL_SHA_AGGREGATE_V1"
BASE="MONSTER_STAGE38_REAL_BINANCE_UM_1M_ORIGINAL_V4_FUTURES_CAUSAL_PILOT_V1"

def sha(data):return hashlib.sha256(data).hexdigest()

def decode(manifest,folder):
    if manifest.get("run_id")!=38207595586 or len(manifest.get("artifacts",[]))!=12:
        raise ValueError("STAGE38_ORIGINAL12_RUN_ID_OR_COUNT_INVALID")
    out=[];receipts=[]
    for item in manifest["artifacts"]:
        day=item["date"];shard=int(item["shard"]);aid=int(item["artifact_id"])
        if (day not in DAYS or shard not in (0,1) or
            any(x["date"]==day and x["shard"]==shard for x in receipts)):
            raise ValueError("STAGE38_DUPLICATE_OR_INVALID_ORIGINAL_SHARD")
        data=(Path(folder)/(str(aid)+".zip")).read_bytes()
        if sha(data)!=item["zip_sha256"]:raise ValueError("STAGE38_ARTIFACT_ZIP_SHA_NOT_MATCH_ORIGINAL")
        inner=f"monster_stage38_{day}_shard{shard}.json"
        with zipfile.ZipFile(Path(folder)/(str(aid)+".zip")) as z:
            if z.namelist()!=[inner]:raise ValueError("STAGE38_WRONG_MEMBER")
            raw=z.read(inner)
        obj=json.loads(raw)
        if obj.get("schema")!=BASE or obj["date"]!=day or obj["shard"]!=shard or obj["source_errors"]:
            raise ValueError("STAGE38_ORIGINAL_PRODUCTION_OUTPUT_INVALID")
        if obj["model_untouched"]!=True or len(obj["result"])!=obj["original_expected"]:
            raise ValueError("STAGE38_ORIGINAL_SHARD_INCOMPLETE")
        for r in obj["result"]:
            if r["date"]!=day or r["cohort"] not in ("FROZEN_GT_2X_CASE","LABEL_BLIND_HASH_CONTROL"):
                raise ValueError("STAGE38_COHORT_SOURCE_MISMATCH")
            if (r["cohort"]=="FROZEN_GT_2X_CASE")!=r["frozen_GT2x"]:
                raise ValueError("STAGE38_GT_LABEL_MISMATCH")
            status=r["source_status"]
            if status=="COMPLETE_REAL_USDM_1M_SHA_CAUSAL_V4":
                if r["polls"]!=3360 or len(r["official_9_daily_1m_publisher_SHA256"])!=9 or not r["unchanged_original_v4_futures"]:
                    raise ValueError("STAGE38_ORIGINAL_V4_OR_SOURCE_INCOMPLETE")
                if any(p["verified_official_publisher_SHA256"]!=True or len(p["zip_sha256"])!=64 or p["bars"]!=1440
                       for p in r["official_9_daily_1m_publisher_SHA256"]):
                    raise ValueError("STAGE38_PUBLISHER_SHA_NOT_PROVEN")
            elif status not in ("CENSORED_DAILY_1M_404","CENSORED_DAILY_1M_GAP"):
                raise ValueError("STAGE38_UNRESOLVED_SOURCE_STATE")
        out.extend(obj["result"])
        receipts.append({"date":day,"shard":shard,"artifact_id":aid,
                         "source_original_zip_SHA256":sha(data),"source_original_inner_JSON_SHA256":sha(raw),
                         "attempted":len(obj["result"]),"minute_complete":obj["complete_replay"],
                         "minute_source_censored":obj["source_censored"]})
    if {(x["date"],x["shard"]) for x in receipts}!={(d,s) for d in DAYS for s in (0,1)}:
        raise ValueError("STAGE38_NOT_ALL_SIX_DATES_BOTH_SHARDS")
    return sorted(out,key=lambda r:(r["date"],r["symbol"])),sorted(receipts,key=lambda r:(r["date"],r["shard"]))

def study(rows,receipts):
    if len(rows)!=172 or len({(x["date"],x["symbol"]) for x in rows})!=172:
        raise ValueError("STAGE38_ORIGINAL172_MISSING_OR_DUPLICATE")
    pos=[x for x in rows if x["frozen_GT2x"]]
    control=[x for x in rows if not x["frozen_GT2x"]]
    if len(pos)!=52 or len(control)!=120 or any(sum(r["date"]==d for r in control)!=20 for d in DAYS):
        raise ValueError("STAGE38_FROZEN_52_WINNERS_120_CONTROLS_NOT_MET")
    complete=[x for x in rows if x["source_status"]=="COMPLETE_REAL_USDM_1M_SHA_CAUSAL_V4"]
    positive=[x for x in complete if x["frozen_GT2x"]]
    negatives=[x for x in complete if not x["frozen_GT2x"]]
    classes=collections.Counter(x["classification"] for x in positive)
    if len(positive)!=sum(classes.values()):
        raise ValueError("STAGE38_CLASSIFICATION_GT_INCONSISTENT")
    selected_control_watch=sum(x["watch_count"]>0 for x in negatives)
    early=[x["nearest_strictly_earlier_WATCH_lead_min"] for x in positive
           if x["classification"]=="STRICTLY_EARLY_WATCH"]
    bydate=[]
    for d in DAYS:
        subset=[x for x in rows if x["date"]==d]
        p=[x for x in subset if x["frozen_GT2x"]]
        n=[x for x in subset if not x["frozen_GT2x"]]
        verified=[x for x in subset if x["source_status"]=="COMPLETE_REAL_USDM_1M_SHA_CAUSAL_V4"]
        bydate.append({"date":d,"frozen_GT2x":len(p),"selected_control":len(n),
          "official_1m_verified":len(verified),
          "original_V4_strict_early":sum(x["frozen_GT2x"] and x["classification"]=="STRICTLY_EARLY_WATCH" for x in verified),
          "ordinary_control_with_watch":sum(not x["frozen_GT2x"] and x["watch_count"]>0 for x in verified),
          "minute_source_censored":len(subset)-len(verified)})
        if len(n)!=20:raise ValueError("STAGE38_MISSING_LABEL_BLIND_CONTROLS")
    return {"schema":SCHEMA,"retrospectively_enriched_and_exposed":True,
            "VENUE":"BINANCE_USDM_FUTURES","original_production_V4_replayed_without_threshold_changes":True,
            "historical_anchor_UTC_06":True,"source":"BINANCE_9_DAILY_USDM_1M_PUBLISHER_SHA_AND_PRIOR_STAGE37_1H_SHA",
            "historical_complete_1h_GT_universe":3333,"historical_complete_1h_2x_count":52,
            "frozen_GT2x_selected":len(pos),"label_blind_no2x_controls_selected":len(control),
            "source_complete_cases":len(complete),
            "source_complete_positive_2x":len(positive),
            "source_complete_negative_controls":len(negatives),
            "minute_source_censored":len(rows)-len(complete),
            "minute_source_censored_positive_2x":len(pos)-len(positive),
            "strictly_early_2x_count":classes["STRICTLY_EARLY_WATCH"],
            "same_minute_not_early_2x_count":classes["SAME_MINUTE_NOT_EARLY"],
            "late_watch_2x_count":classes["WATCH_LATE"],
            "no_watch_2x_count":classes["NO_WATCH"],
            "control_has_any_WATCH":selected_control_watch,
            "control_WATCH_total":sum(x["watch_count"] for x in negatives),
            "positive_WATCH_total":sum(x["watch_count"] for x in positive),
            "strict_early_nearest_1m_cross_median_lead_minutes":statistics.median(early) if early else None,
            "strict_early_nearest_1m_cross_lead_ge5_minutes":sum(x>=5 for x in early),
            "strict_early_nearest_1m_cross_lead_ge15_minutes":sum(x>=15 for x in early),
            "strict_early_nearest_1m_cross_lead_ge60_minutes":sum(x>=60 for x in early),
            "all_six_dates":bydate,"original12_artifact_SHA_receipts":receipts,
            "CANNOT_CLAIM":"FULL_USDM_RECALL_OR_PRECISION_52_WINNERS_ENRICHED_120_CONTROLS_ONLY",
            "true_global_shared_D1_queue":"NOT_REPLAYED","historical_contract_type":"UNKNOWN",
            "historical_actual_orderbook_or_fills":"UNVERIFIED",
            "independent_other_AI_review":"NOT_DONE","Monster_deployment":"NO_GO","Frank":"UNCHANGED",
            "Gmail":"OFF","trading":"NO_GO"}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--manifest",type=Path,required=True)
    p.add_argument("--dir",type=Path,required=True)
    p.add_argument("--output-dir",type=Path,required=True)
    a=p.parse_args()
    rows,receipts=decode(json.loads(a.manifest.read_text()),a.dir)
    summary=study(rows,receipts)
    a.output_dir.mkdir(parents=True,exist_ok=True)
    (a.output_dir/"monster_stage38_original12_sha_full172_causal_summary.json").write_text(
       json.dumps(summary,sort_keys=True,indent=2,ensure_ascii=False)+"\n")
    with (a.output_dir/"monster_stage38_original12_full172_futures_causal_cases.jsonl").open("w") as f:
        for row in rows:f.write(json.dumps(row,sort_keys=True,ensure_ascii=False)+"\n")
    print("STAGE38_ORIGINAL12_GITHUB_ZIP_AND_USDM_1M_CAUSAL_PASS "+json.dumps({
      k:summary[k] for k in ("source_complete_positive_2x","source_complete_negative_controls",
      "minute_source_censored_positive_2x","strictly_early_2x_count","same_minute_not_early_2x_count",
      "late_watch_2x_count","no_watch_2x_count","control_has_any_WATCH")},sort_keys=True))
if __name__=="__main__":main()
