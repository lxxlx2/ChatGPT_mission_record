#!/usr/bin/env python3
"""Stage44 frozen new-window publisher-SHA independent raw 36 provenance merge.

Original36 GitHub-hosted ZIP SHA must equal API publisher digest; all 900
original historical USD-M symbols at ALL six sealed dates, including censored.
Hindsight gross 2x/5x/10x HIGH event truth only; no V4 score/trades here.
"""
import argparse,collections,csv,hashlib,json,zipfile
from pathlib import Path
EVIDENCE=Path(__file__).resolve().parents[2]/"monster"/"evidence"
INV=EVIDENCE/"monster_stage36_official_usdm_archive_vs_spot758.json"
LEDGER=EVIDENCE/"monster_stage43_frozen_exposure_ledger_and_blind_dates.json"
DATES=("2025-01-09","2025-09-02","2026-01-26","2026-02-24","2026-03-28","2026-05-10")
EXPECTED="MONSTER_STAGE44_BLIND_DISJOINT_DATE_USDM_ALL900_1H_OFFICIAL_SHA_GT_V1"
SCHEMA="MONSTER_STAGE44_SEALED_900x6_ORIGINAL36_GITHUB_SHA_BINANCE_1H_GT_V1"
RUN_ID=38212473972
def sha(raw):return hashlib.sha256(raw).hexdigest()
def load(manifest,zips):
    arts=manifest.get("artifacts",[])
    if manifest.get("source_run_id")!=RUN_ID or len(arts)!=36:
        raise ValueError("STAGE44_NOT_ORIGINAL_SUCCESSFUL36_RUN")
    rows=[];rec=[];seen=set()
    for a in arts:
        day=a["date"];shard=int(a["shard"]);aid=int(a["artifact_id"])
        if (day not in DATES or shard not in range(6) or (day,shard) in seen):
            raise ValueError("STAGE44_BAD_UNIQUE_ID")
        seen.add((day,shard))
        p=Path(zips)/(str(aid)+".zip")
        data=p.read_bytes()
        if sha(data)!=a["sha256"]:raise ValueError("STAGE44_WRONG_ORIGINAL_ZIP_SHA")
        inner=f"monster_stage44_{day}_shard{shard}.json"
        with zipfile.ZipFile(p) as z:
            if z.namelist()!=[inner]:raise ValueError("STAGE44_BAD_ZIP_FILE_NAME")
            raw=z.read(inner)
        obj=json.loads(raw)
        if (obj.get("schema")!=EXPECTED or obj["date"]!=day or obj["shard"]!=shard
            or len(obj["rows"])!=150 or not obj["all150_attempted"]):
            raise ValueError("STAGE44_NOT_ORIGINAL_150_CASES")
        for r in obj["rows"]:
            if r["date"]!=day or r["source_status"] not in ("COMPLETE_168H_OFFICIAL_PUBLISHER_SHA",
                "CENSORED_NOT_168_CONSECUTIVE_HOURS","CENSORED_PUBLISHER_MONTHLY_1H_404"):
                raise ValueError("STAGE44_BAD_SOURCE_STATUS")
            proofs=r.get("source_proofs",[])
            if not all(len(s["publisher_ZIP_sha256"])==64 for s in proofs):
                raise ValueError("STAGE44_MISSING_ORIGINAL_OFFICIAL_SHA")
            if r["source_status"]=="COMPLETE_168H_OFFICIAL_PUBLISHER_SHA":
                if not proofs or any(n not in r for n in ("gt2x","gt5x","gt10x","baseline_1h_open")):
                    raise ValueError("STAGE44_MISSING_VERIFIED_GROUND_TRUTH")
            elif any(k in r for k in ("gt2x","gt5x","gt10x")):
                raise ValueError("STAGE44_CENSORED_HAS_FAKE_GROUND_TRUTH")
        rows+=obj["rows"]
        rec.append({"date":day,"shard":shard,"artifact_id":aid,
           "GitHub_original_zip_SHA256":sha(data),"original_inside_json_SHA256":sha(raw),
           "complete":obj["valid"],"status_counts":obj["original_source_status_counts"]})
    if seen!={(d,s) for d in DATES for s in range(6)}:raise ValueError("STAGE44_MISSING_ANY_ORIGINAL_SHARD")
    return sorted(rows,key=lambda x:(x["date"],x["symbol"])),rec
def aggregate(rows,rec):
    frozen=json.loads(INV.read_text(encoding="utf-8"))
    names={x["symbol"] for x in frozen["source_rows"] if x["archive_symbol_class"]=="EXACT_PLAIN_USDT_ARCHIVED"}
    ledger=json.loads(LEDGER.read_text(encoding="utf-8"))
    if len(names)!=900 or ledger["selection"]["holdout_selected_blind_by_hashed_date_only"]!=list(DATES):
        raise ValueError("STAGE44_POSTRUN_FROZEN_LEDGER_DRIFT")
    if len(rows)!=5400 or len({(r["date"],r["symbol"]) for r in rows})!=5400:
        raise ValueError("STAGE44_NOT_5400_UNIQUE_PAIR")
    per=[];states=collections.Counter()
    for date in DATES:
        subset=[r for r in rows if r["date"]==date]
        if len(subset)!=900 or {r["symbol"] for r in subset}!=names:
            raise ValueError("STAGE44_NOT_ALL900_SYMBOLS_PER_DATE")
        ct=collections.Counter(r["source_status"] for r in subset);states.update(ct)
        ok=[r for r in subset if r["source_status"]=="COMPLETE_168H_OFFICIAL_PUBLISHER_SHA"]
        per.append({"date":date,"attempted":900,"source_verified":len(ok),"statuses":dict(ct),
                    "gt2x":sum(r["gt2x"] for r in ok),"gt5x":sum(r["gt5x"] for r in ok),
                    "gt10x":sum(r["gt10x"] for r in ok)})
    positives=[r for r in rows if r["source_status"]=="COMPLETE_168H_OFFICIAL_PUBLISHER_SHA" and r["gt2x"]]
    return {"schema":SCHEMA,"frozen_no_overlapping_historical_dates":list(DATES),
            "source_run_id":RUN_ID,"original_all36_GitHub_SHA_receipts":sorted(rec,key=lambda r:(r["date"],r["shard"])),
            "attempted":len(rows),"source_complete":states["COMPLETE_168H_OFFICIAL_PUBLISHER_SHA"],
            "source_censored":len(rows)-states["COMPLETE_168H_OFFICIAL_PUBLISHER_SHA"],
            "status_counts":dict(states),"gross2x_high":len(positives),
            "gross5x_high":sum(r["gt5x"] for r in positives),"gross10x_high":sum(r["gt10x"] for r in positives),
            "per_date":per,
            "SOURCE_AND_LABEL_DONE_NOT_SIGNAL_MODEL":True,"P1_v02_candidate_FROZEN_UNTESTED":True,
            "point_in_time_exchange_listing":"UNVERIFIED","orderbook_fills":"UNVERIFIED",
            "other_AI_review":"NOT_DONE","deployment":"NO_GO","Frank":"UNCHANGED","Gmail":"OFF"}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--manifest",type=Path,required=True)
    p.add_argument("--zip-dir",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    rows,rec=load(json.loads(a.manifest.read_text()),a.zip_dir)
    report=aggregate(rows,rec)
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"monster_stage44_original36_sha_six_blind_900x6_hourly_GT_summary.json").write_text(
        json.dumps(report,indent=2,sort_keys=True,ensure_ascii=False)+"\n")
    # The CSV is compact. Preserve every original source-month SHA per symbol
    # in Git before Stage45 uses the ground truth; never fabricate SHA receipts.
    with (a.out/"monster_stage44_full5400_blind_source_publisher_hourly_SHA.jsonl").open("w",encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row,ensure_ascii=False,sort_keys=True)+"\n")
    cols=["date","symbol","source_status","baseline_1h_open","max_high_multiple","gt2x","gt5x","gt10x",
          "first_gt2x_1h_utc","first_gt5x_1h_utc","first_gt10x_1h_utc"]
    for name,selected in (
      ("monster_stage44_all5400_blind_dates_source_status_and_GT.csv",rows),
      ("monster_stage44_actual_complete_GT2x_registry.csv",
          [r for r in rows if r["source_status"]=="COMPLETE_168H_OFFICIAL_PUBLISHER_SHA" and r["gt2x"]])):
        with (a.out/name).open("w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f,fieldnames=cols,extrasaction="ignore",lineterminator="\n");w.writeheader()
            for r in selected:w.writerow(r)
    print("STAGE44_36_ORIGINAL_SHA_FROZEN_900x6_PASS "+json.dumps({
       k:report[k] for k in ("attempted","source_complete","source_censored","gross2x_high","gross5x_high","gross10x_high")},sort_keys=True))
if __name__=="__main__":main()
