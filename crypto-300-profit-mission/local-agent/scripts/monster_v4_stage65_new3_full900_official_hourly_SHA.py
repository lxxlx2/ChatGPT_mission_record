#!/usr/bin/env python3
"""Monster Stage65: calendar-frozen three new 900-symbol USD-M official hourly GT.

STRICT SOURCE ONLY. A new D0 first5 strategy was frozen BEFORE this script.
Never select winners based on future highs or price data, never assume buyability.
The same Stage44 official publisher SHA and hourly 168h ground-truth engine.
"""
from __future__ import annotations
import argparse
import collections
import concurrent.futures
import datetime as dt
import hashlib
import json
from pathlib import Path

try:
    import monster_v4_stage44_six_blind_hourly_truth as orig44
    import monster_v4_stage72_imported_dependency_integrity as integrity
except ImportError:
    from scripts import monster_v4_stage44_six_blind_hourly_truth as orig44
    from scripts import monster_v4_stage72_imported_dependency_integrity as integrity

ROOT=Path(__file__).resolve().parents[2]/"monster"/"evidence"
PRE=ROOT.parent/"MONSTER_STAGE65_PREDECLARED_NEW3_FULL900_FIRSTD0_CAP5_HOLDOUT_PROTOCOL_20261012.md"
LEDGER=ROOT/"monster_stage49_frozen_after_stage48_exposure_and_new_dates.json"
INVENTORY=ROOT/"monster_stage36_official_usdm_archive_vs_spot758.json"
PINS={
    PRE.name:"49669c734ec4add4f5134e5ea49559f353b44931",
    LEDGER.name:"a2d360e5326f9d9befc679b752e9e6df366f4998",
    INVENTORY.name:"91b0f99ef85adb48494c5be5c7cc13a7cedcb686",
    "monster_v4_stage44_six_blind_hourly_truth.py":"8d6936a99f91ac10fc3d913f5a95eff2c460a131",
    "monster_v4_stage72_imported_dependency_integrity.py":"8ae3066afa9b01d419b735ae4045ef2fb8d10264",
}
DATES=("2025-03-30","2025-06-30","2025-11-27")
OLD=("2025-01-30","2025-06-02","2025-08-01","2025-10-02","2026-06-21","2026-07-28")
SCHEMA="MONSTER_STAGE65_FROZEN_NEW_THREE_DATES_ALL900_USDM_OFFICIAL_1H_GT_V1"
GOOD="COMPLETE_168H_OFFICIAL_PUBLISHER_SHA"

def blob(path):
    data=path.read_bytes()
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()

def frozen():
    for p in (PRE,LEDGER,INVENTORY,Path(orig44.__file__),Path(integrity.__file__)):
        if blob(p)!=PINS[p.name]:
            raise ValueError("STAGE65_ORIGINAL_PREMARKET_TEXT_OR_SOURCE_BLOB_CHANGED "+p.name)
    integrity.assert_integrity_stage65(orig44)
    text=PRE.read_text(encoding="utf-8")
    if any(d not in text for d in DATES) or "D0_FIRST5_BASELINE_V1" not in text:
        raise ValueError("STAGE65_PRE_PRICE_DATE_OR_MODEL_NOT_FROZEN")
    old=json.loads(LEDGER.read_text(encoding="utf-8"))
    forbidden=set(old["historical_exposed_or_potentially_exposed_ISO_dates"])|set(OLD)
    def day(s):return dt.date.fromisoformat(s)
    if any(abs((day(d)-day(o)).days)<7 for d in DATES for o in forbidden):
        raise ValueError("STAGE65_CALENDAR_OVERLAP_EARLIER_AUDITED_RESEARCH")
    if any(abs((day(a)-day(b)).days)<60 for i,a in enumerate(DATES) for b in DATES[i+1:]):
        raise ValueError("STAGE65_CALENDAR_SELECTED_TOO_CLOSE")
    inv=json.loads(INVENTORY.read_text(encoding="utf-8"))
    names=sorted(q["symbol"] for q in inv["source_rows"] if q["archive_symbol_class"]=="EXACT_PLAIN_USDT_ARCHIVED")
    if len(names)!=900 or len(set(names))!=900:
        raise ValueError("STAGE65_ORIGINAL_900_FUTURES_ARCHIVE_CHANGED")
    return names

def research(day,shard,workers=4):
    names=frozen()
    if day not in DATES or shard not in range(6) or workers not in range(1,7):
        raise ValueError("STAGE65_NONFROZEN_DATE_SHARD_OR_WORKERS")
    poolsyms=[s for i,s in enumerate(names) if i%6==shard]
    if len(poolsyms)!=150:raise ValueError("STAGE65_NOT_COMPLETE_150_PER_SHARD")
    rows=[];errors=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        tasks={pool.submit(orig44.eval_coin,s,day):s for s in poolsyms}
        for fut in concurrent.futures.as_completed(tasks):
            s=tasks[fut]
            try:
                x=fut.result()
                if (x["date"],x["symbol"])!=(day,s):
                    raise ValueError("STAGE65_CROSS_COIN_SOURCE_MISMATCH")
                rows.append(x)
            except Exception as exc:
                errors.append({"symbol":s,"message":type(exc).__name__+":"+str(exc)[:200]})
    if errors or len(rows)!=150:
        raise RuntimeError("STAGE65_OFFICIAL_HOURLY_SOURCE_ERROR_NO_PARTIAL_SUCCESS "+json.dumps(errors[:30]))
    good=[x for x in rows if x["source_status"]==GOOD]
    return {
        "schema":SCHEMA,"date":day,"shard":shard,
        "original_archive_attempts":150,"source_verified":len(good),
        "censored_by_source_status":dict(sorted(collections.Counter(x["source_status"] for x in rows if x["source_status"]!=GOOD).items())),
        "gt2x_source_verified":sum(bool(x["gt2x"]) for x in good),
        "gt5x_source_verified":sum(bool(x["gt5x"]) for x in good),
        "gt10x_source_verified":sum(bool(x["gt10x"]) for x in good),
        "rows":sorted(rows,key=lambda x:x["symbol"]),
        "publisher_verified_official_source_only":True,
        "new_D0_priority_test":"NOT_YET_RUN",
        "non_crypto_or_stock_like_futures_symbols_in_archive":"NOT_CLASSIFIED",
        "NO_ASSUMED_TRADING_NOTIONAL":True,
        "MONSTER_DEPLOY":"NO_GO",
    }

def aggregate(folder,out):
    frozen()
    allrows=[];reports=[];seen=set()
    for day in DATES:
        for shard in range(6):
            path=folder/("monster_stage65_"+day+"_shard"+str(shard)+".json")
            if not path.exists():raise ValueError("STAGE65_MISSING_ORIGINAL_FROZEN_SHARD "+str(path))
            j=json.loads(path.read_text(encoding="utf-8"))
            if j["schema"]!=SCHEMA or (j["date"],j["shard"],len(j["rows"]))!=(day,shard,150):
                raise ValueError("STAGE65_SHARD_SOURCE_IDENTITY_OR_COUNT_WRONG")
            if j["source_verified"]!=sum(x["source_status"]==GOOD for x in j["rows"]):
                raise ValueError("STAGE65_VERIFIED_SOURCE_COUNT_DRIFT")
            for x in j["rows"]:
                key=x["date"],x["symbol"]
                if key in seen:raise ValueError("STAGE65_DUPLICATE_ARCHIVE_COIN_DATE")
                seen.add(key)
                if x["source_status"]==GOOD:
                    if not all(y["publisher_ZIP_sha256"] and len(y["publisher_ZIP_sha256"])==64 for y in x["source_proofs"]):
                        raise ValueError("STAGE65_MISSING_ORIGINAL_PUBLISHER_SHA_PROOFS")
                allrows.append(x)
            reports.append({
                "date":day,"shard":shard,
                "raw_shard_json_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
                "source_complete":j["source_verified"],
                "gt2x":j["gt2x_source_verified"],
                "gt5x":j["gt5x_source_verified"],
                "gt10x":j["gt10x_source_verified"],
            })
    if len(allrows)!=2700 or len(seen)!=2700:
        raise ValueError("STAGE65_NOT_ALL_2700")
    output={
        "schema":"MONSTER_STAGE65_ORIGINAL18_SHA_HOURLY_AGGREGATE_V1",
        "original_frozen_date_protocol_git_blob":PINS[PRE.name],
        "original_preregistered_USDM_archive_attempts":2700,
        "official_1h_publisher_sha_complete":sum(r["source_status"]==GOOD for r in allrows),
        "original_18_source_shards_SHA_receipts":reports,
        "verified_GT2x":sum(bool(r["gt2x"]) for r in allrows if r["source_status"]==GOOD),
        "verified_GT5x":sum(bool(r["gt5x"]) for r in allrows if r["source_status"]==GOOD),
        "verified_GT10x":sum(bool(r["gt10x"]) for r in allrows if r["source_status"]==GOOD),
        "historical_hourly_SOURCE_ONLY":True,
        "minute_D0_and_NEW_priority_model_not_tested":True,
        "NO_REALIZED_PNL_OR_ORDER_SIZE":True,
        "P1V03":"REJECTED",
        "OTHER_AI_REVIEW":"NOT_DONE",
        "DEPLOYMENT":"NO_GO",
        "GMAIL":"OFF","AUTOTRADE":"NO_GO",
    }
    out.mkdir(parents=True,exist_ok=True)
    (out/"monster_stage65_new3_full2700_hourly_official_source_SHA.jsonl").write_text(
        "".join(json.dumps(r,sort_keys=True,ensure_ascii=False)+"\n" for r in sorted(allrows,key=lambda x:(x["date"],x["symbol"]))),encoding="utf-8")
    (out/"monster_stage65_new3_full2700_hourly_source_GT_summary.json").write_text(
        json.dumps(output,sort_keys=True,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("STAGE65_ALL2700_OFFICIAL_SOURCE_SHA_GT_SUCCESS "+json.dumps({
        k:output[k] for k in ("original_preregistered_USDM_archive_attempts","official_1h_publisher_sha_complete","verified_GT2x","verified_GT5x","verified_GT10x")},sort_keys=True))

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--selftest",action="store_true")
    p.add_argument("--date")
    p.add_argument("--shard",type=int)
    p.add_argument("--workers",type=int,default=4)
    p.add_argument("--out",type=Path)
    p.add_argument("--aggregate-dir",type=Path)
    a=p.parse_args()
    if a.selftest:
        assert len(frozen())==900
        orig44.test()
        print("STAGE65_BLIND_CALENDAR_OVERLAP_FROZEN_ARCHIVE_SOURCE_SELFTEST_PASS")
        return
    if not a.out:p.error("--out required")
    if a.aggregate_dir:
        aggregate(a.aggregate_dir,a.out)
    else:
        if not a.date or a.shard is None:p.error("--date and --shard required")
        result=research(a.date,a.shard,a.workers)
        a.out.parent.mkdir(parents=True,exist_ok=True)
        a.out.write_text(json.dumps(result,sort_keys=True,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        print("STAGE65_FIRST_RAW_150_OFFICIAL_SOURCE "+
              json.dumps({k:result[k] for k in ("date","shard","source_verified","gt2x_source_verified")},sort_keys=True))
if __name__=="__main__":
    main()
