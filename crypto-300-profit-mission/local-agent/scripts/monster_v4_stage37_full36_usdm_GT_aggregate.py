#!/usr/bin/env python3
"""Stage37 original 36 GHA artifact SHA rehash and all900 USD-M facts.

No model run, no 1m WATCH, no hindsight-filled trade profitability.
Missing Binance hourly ZIP never means no pump or no tradable contract.
"""
import argparse,collections,csv,hashlib,json,zipfile
from pathlib import Path

EVIDENCE=Path(__file__).resolve().parents[2]/"monster"/"evidence"
INVENTORY=EVIDENCE/"monster_stage36_official_usdm_archive_vs_spot758.json"
DAYS=("2025-01-19","2025-04-19","2025-07-19","2025-10-19","2026-04-19","2026-07-19")
SOURCE_SCHEMA="MONSTER_STAGE37_USDM_PUBLISHER_SHA_FULL900_SIX_DATE_168H_GT_V1"
SCHEMA="MONSTER_STAGE37_36_GITHUB_ORIGINAL_PUBLISHER_SHA_5400_USDM_HOURLY_GT_AGGREGATE_V1"

def sha(b):return hashlib.sha256(b).hexdigest()

def read_all(manifest,path):
    a=manifest.get("artifacts",[])
    if manifest.get("source_run_id")!=38206141845 or len(a)!=36:
        raise ValueError("STAGE37_EXACT_ORIGINAL36_SOURCE_RUN_REQUIRED")
    result=[];receipts=[]
    for item in a:
        day=item["date"];shard=int(item["shard"]);aid=int(item["artifact_id"])
        if day not in DAYS or shard not in range(6) or any(r["date"]==day and r["shard"]==shard for r in receipts):
            raise ValueError("STAGE37_BAD_SOURCE_UNIQUE_SHARD")
        data=(Path(path)/(str(aid)+".zip")).read_bytes()
        if sha(data)!=item["zip_sha256"]:raise ValueError("STAGE37_GITHUB_SOURCE_ZIP_SHA_MISMATCH")
        member=f"monster_stage37_{day}_shard{shard}.json"
        with zipfile.ZipFile(Path(path)/(str(aid)+".zip")) as z:
            if z.namelist()!=[member]:raise ValueError("STAGE37_BAD_GITHUB_ARTIFACT_JSON_MEMBER")
            raw=z.read(member)
        obj=json.loads(raw)
        if obj["schema"]!=SOURCE_SCHEMA or obj["date"]!=day or obj["shard"]!=shard or len(obj["rows"])!=150:
            raise ValueError("STAGE37_ORIGINAL_SOURCE_SCHEMA_IDENTITY_WRONG")
        if obj["full_frozen900_universe_attempted"]!=True:
            raise ValueError("STAGE37_NOT_ORIGINAL_COMPLETE_UNIVERSE")
        states=collections.Counter(x["status"] for x in obj["rows"])
        if dict(states)!=obj["status_counts"]:
            raise ValueError("STAGE37_LOCAL_PER_SHARD_SOURCE_COUNT_CHANGED")
        good=[x for x in obj["rows"] if x["status"]=="COMPLETE_168H_PUBLISHER_SHA"]
        if len(good)!=obj["valid"] or any(len(x["publisher_1h_month_sha256"])!=64 for x in good):
            raise ValueError("STAGE37_PUBLISHER_SHA_MISSING")
        if any(sum(x[f"gt{k}x"] for x in good)!=obj[f"positive_high_gt{k}x"] for k in (2,5,10)):
            raise ValueError("STAGE37_ORIGINAL_GT_TOTAL_NOT_EQUAL_ROWS")
        if any(x["date"]!=day for x in obj["rows"]):
            raise ValueError("STAGE37_CROSSDAY_ORIGINAL_CASE")
        result.extend(obj["rows"])
        receipts.append({"date":day,"shard":shard,"artifact_id":aid,
                         "original_zip_sha256":sha(data),"original_json_sha256":sha(raw),
                         "publisher_verified_complete_cases":len(good),"source_status_counts":dict(states)})
    if {(x["date"],x["shard"]) for x in receipts}!={(d,i) for d in DAYS for i in range(6)}:
        raise ValueError("STAGE37_NOT_ALL_36_REQUIRED")
    return result,receipts

def aggregate(rows,receipts):
    if len(rows)!=5400 or len({(r["date"],r["symbol"]) for r in rows})!=5400:
        raise ValueError("STAGE37_FULL_5400_UNIVERSE_INCOMPLETE_OR_DUPLICATE")
    inventory=json.loads(INVENTORY.read_text(encoding="utf-8"))
    frozen={r["symbol"] for r in inventory["source_rows"] if r["archive_symbol_class"]=="EXACT_PLAIN_USDT_ARCHIVED"}
    if len(frozen)!=900:
        raise ValueError("STAGE37_STAGE36_FROZEN_UNIVERSE_CHANGED")
    venue_spot={r["symbol"] for r in inventory["source_rows"] if r["archive_symbol_class"]=="EXACT_PLAIN_USDT_ARCHIVED" and r["in_frozen_Spot_758"]}
    if len(venue_spot)!=472:raise ValueError("STAGE37_ORIGINAL_SPOT_OVERLAP_CHANGED")
    overall=collections.Counter()
    bydate=[]; byvenue=collections.defaultdict(collections.Counter)
    for d in DAYS:
        subset=[r for r in rows if r["date"]==d]
        if len(subset)!=900 or {r["symbol"] for r in subset}!=frozen:raise ValueError("STAGE37_FROZEN_DAY_COHORT_UNMATCHED")
        statuses=collections.Counter(r["status"] for r in subset)
        complete=[r for r in subset if r["status"]=="COMPLETE_168H_PUBLISHER_SHA"]
        rec={"date":d,"attempted":900,"complete":len(complete),"source_status_counts":dict(statuses)}
        for n in (2,5,10):rec[f"future_hour_HIGH_{n}x"]=sum(r[f"gt{n}x"] for r in complete)
        bydate.append(rec);overall.update(statuses)
    if sum(x["attempted"] for x in bydate)!=5400:raise ValueError("STAGE37_BAD_AGGREGATE")
    for r in rows:
        k=("NAMED_SPOT_COHORT_OVERLAP" if r["symbol"] in venue_spot else "NOT_IN_FROZEN_SPOT_758")
        group=byvenue[k];group["attempted"]+=1
        if r["status"]=="COMPLETE_168H_PUBLISHER_SHA":
            group["source_complete"]+=1
            for n in (2,5,10):group[f"gross_{n}x_high"]+=int(r[f"gt{n}x"])
        else:group["source_censored"]+=1
    winners=[r for r in rows if r["status"]=="COMPLETE_168H_PUBLISHER_SHA" and r["gt2x"]]
    return {"schema":SCHEMA,"official_data_source":"BINANCE_USDM_FUTURES_MONTHLY_1H_PLUS_PUBLISHER_SHA256",
            "six_unseen_futures_source_dates":list(DAYS),"retrospective_already_exposed_Spot_dates":True,
            "historical_perpetual_vs_other_contract_type":"NOT_VERIFIED",
            "mixed_crypto_noncrypto_usdm_symbols":"YES_NOT_YET_CLASSIFIED",
            "attempted":len(rows),"source_complete":overall["COMPLETE_168H_PUBLISHER_SHA"],
            "source_censored":len(rows)-overall["COMPLETE_168H_PUBLISHER_SHA"],
            "overall_source_status_counts":dict(overall),"by_date":bydate,
            "by_archive_symbol_overlap_vs_frozen_Spot758":{k:dict(v) for k,v in byvenue.items()},
            "gross_hourly_high_gt2x":len(winners),
            "gross_hourly_high_gt5x":sum(r["gt5x"] for r in winners),
            "gross_hourly_high_gt10x":sum(r["gt10x"] for r in winners),
            "original36_GitHub_SHA_proofs":sorted(receipts,key=lambda r:(r["date"],r["shard"])),
            "hourly_high_is_not_trade_fill":True,"future_data_not_model_input":True,
            "original_V4_1m_Futures_WATCH_replay":"NOT_DONE","new_strategy_validation":False,
            "independent_other_AI_review":"NOT_DONE","deployment":"NO_GO","Gmail":"OFF","trading":"NO_GO","Frank":"UNCHANGED"}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--manifest",type=Path,required=True)
    p.add_argument("--zip-dir",type=Path,required=True)
    p.add_argument("--output-dir",type=Path,required=True)
    a=p.parse_args()
    rows,receipts=read_all(json.loads(a.manifest.read_text()),a.zip_dir)
    summary=aggregate(rows,receipts)
    a.output_dir.mkdir(parents=True,exist_ok=True)
    out=a.output_dir/"monster_stage37_sixdate_all900_source_SHA_historical_GT_summary.json"
    out.write_text(json.dumps(summary,indent=2,ensure_ascii=False,sort_keys=True)+"\n",encoding="utf-8")
    fields=("date","symbol","venue","status","publisher_1h_month_sha256",
            "baseline_1h_open","max_high_multiple","gt2x","gt5x","gt10x",
            "first_2x_high_hour_utc","first_5x_high_hour_utc","first_10x_high_hour_utc")
    for name,items in (("monster_stage37_sixdate_all5400_usdm_source_and_GT.csv",rows),
                       ("monster_stage37_all_source_verified_2x_winner_registry.csv",
                        [r for r in rows if r["status"]=="COMPLETE_168H_PUBLISHER_SHA" and r["gt2x"]])):
        with (a.output_dir/name).open("w",encoding="utf-8",newline="") as f:
            w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore",lineterminator="\n")
            w.writeheader()
            for r in sorted(items,key=lambda r:(r["date"],r["symbol"])):w.writerow(r)
    print("STAGE37_ORIGINAL36_SOURCE_SHA_FULL900_GT_RECOMPUTE_PASS "+json.dumps({
      k:summary[k] for k in ("attempted","source_complete","source_censored",
      "gross_hourly_high_gt2x","gross_hourly_high_gt5x","gross_hourly_high_gt10x")},sort_keys=True))
if __name__=="__main__":main()
