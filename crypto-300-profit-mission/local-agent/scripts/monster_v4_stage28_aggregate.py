#!/usr/bin/env python3
"""Rehash six exact production-shared-D1 result ZIPs & aggregate real queue output.

No profitability/true full-global D0 claim. Requires all source cases, verifies
first-pass official 5m publisher SHA256 metadata and original queue events.
"""
import argparse
import collections
import hashlib
import json
import zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]/"monster/evidence"
PROOF=ROOT/"monster_stage28_original_six_real_shared_sqlite_artifact_proof_20261011.json"
DATES=["2025-11-04","2025-12-04","2026-02-04","2026-04-04","2026-08-04","2026-09-04"]

def read_artifact(path,rec):
    blob=Path(path).read_bytes()
    if hashlib.sha256(blob).hexdigest()!=rec["zip_sha256"]:
        raise ValueError("STAGE28_ORIGINAL_ZIP_SHA256_CHANGED")
    member="monster_stage28_"+rec["date"]+"_real_shared_sqlite.json"
    with zipfile.ZipFile(path) as z:
        if z.namelist()!=[member] or z.getinfo(member).file_size>12_000_000:
            raise ValueError("STAGE28_ORIGINAL_ZIP_MEMBER_CHANGED")
        raw=z.read(member)
    if hashlib.sha256(raw).hexdigest()!=rec["raw_json_sha256"]:
        raise ValueError("STAGE28_ORIGINAL_JSON_SHA256_CHANGED")
    d=json.loads(raw)
    if d.get("schema")!="MONSTER_STAGE28_ACTUAL_PRODUCTION_SHARED_SQLITE_D1_WITH_FROZEN_WATCH_V1" or d["date"]!=rec["date"]:
        raise ValueError("STAGE28_SOURCE_IDENTITY_OR_SCHEMA_CHANGED")
    if d.get("actual_shared_sqlite_process_queue") is not True or d.get("global_observe_snapshot_replayed") is not False:
        raise ValueError("STAGE28_FALSE_COMPLETE_GLOBAL_D0_CLAIM")
    if d.get("pending_at_end")!=0:
        raise ValueError("STAGE28_UNFINISHED_D1_QUEUE")
    if sum(d.get("candidate_status_counts",{}).values())!=d["queue_candidates"]:
        raise ValueError("STAGE28_QUEUE_COUNT_CHANGED")
    if len(d["setups"])!=d["event_counts"].get("SETUP_ACTIVE",0):
        raise ValueError("STAGE28_SETUP_COUNT_CHANGED")
    if d["event_counts"].get("WATCH_EARLY",0)!=d["watch_arrivals"]:
        raise ValueError("STAGE28_WATCH_EVENTS_DIFFER_FROM_FROZEN_ARRIVALS")
    for p in d["source_5m_official_SHA256"]:
        if p.get("publisher_verified") is not True or len(p.get("sha256",""))!=64 or p.get("rows")!=288:
            raise ValueError("STAGE28_5M_UNVERIFIED_SOURCE")
    return d

def summarize(reports):
    if set(reports)!=set(DATES):
        raise ValueError("STAGE28_REQUIRE_EXACTLY_SIX_FROZEN_DATES")
    count=collections.Counter()
    statuses=collections.Counter()
    hours=collections.Counter()
    deltas=[]
    rows=[]
    for day in DATES:
        d=reports[day]
        count["watch"]+=d["watch_arrivals"]
        count["individual_setups"]+=d["original_stage26_individual_D1_setups"]
        count["real_shared_setups"]+=len(d["setups"])
        count["late"]+=len(d["late_events"])
        count["sources"]+=len(d["source_5m_official_SHA256"])
        count["shared_queue_candidates"]+=d["queue_candidates"]
        count["processor_evaluations"]+=d["production_processor_selected_total"]
        count["retries_or_deferred"]+=d["production_processor_deferred_total"]
        statuses.update(d["candidate_status_counts"])
        for s in d["setups"]:
            hours[s["utc"][:13]]+=1
            rows.append({"date":day,"symbol":s["symbol"],"utc":s["utc"]})
        deltas.append({"date":day,"actual_watch":d["watch_arrivals"],
            "independent_setups":d["original_stage26_individual_D1_setups"],
            "shared_original_production_setups":len(d["setups"]),
            "late_review":len(d["late_events"]),"queue_status":d["candidate_status_counts"],
            "max_pending_before_poll":d["max_pending_before_poll"],
            "official_5m_daily_archives_publisher_SHA_verified":len(d["source_5m_official_SHA256"])})
    if count["watch"]!=1132 or count["individual_setups"]!=826:
        raise ValueError("STAGE28_ORIGINAL_SOURCE_EVENTS_CHANGED")
    if count["shared_queue_candidates"]>count["watch"]:
        raise ValueError("STAGE28_ADDED_UNAUTHORIZED_CANDIDATES")
    return {"schema":"MONSTER_STAGE28_SIX_REAL_SHARED_PRODUCTION_QUEUE_SHA_RECOMPUTED_V1",
      "all_six_original_ZIP_and_internal_JSON_SHA256_verified":True,
      "six_dates_already_exposed":True,
      "date_count":len(DATES),
      "source_original_WATCH_count":count["watch"],
      "source_original_individual_SQLite_D1_SETUPS":count["individual_setups"],
      "real_one_shared_SQLite_production_D1_SETUPS":count["real_shared_setups"],
      "real_LATE_REVIEW_events":count["late"],
      "unique_publisher_SHA_verified_daily_5m_archives":count["sources"],
      "queue_candidates":count["shared_queue_candidates"],
      "actual_production_process_queue_selected_total":count["processor_evaluations"],
      "actual_production_deferred_total":count["retries_or_deferred"],
      "queue_status":dict(statuses),
      "per_date":deltas,
      "setup_UTC_hour_histogram":dict(hours),
      "setup_event_register":rows,
      "actual_single_global_observe_snapshot_and_invalidation":"NOT_REPLAYED",
      "historical_source_5m_vs_reconstructed_1m_exact_identity":"NOT_VERIFIED",
      "global_spot_plus_futures_queue":"NOT_REPLAYED",
      "independent_other_AI_review":"NOT_DONE",
      "deployment":"NO_GO","real_gmail":"OFF","trading":"NO_GO"}

def run(paths,proof=PROOF):
    data=json.loads(Path(proof).read_text(encoding="utf-8"))
    sources={r["date"]:r for r in data["artifacts"]}
    if len(paths)!=6 or len(sources)!=6 or set(sources)!=set(DATES):
        raise ValueError("STAGE28_WRONG_ARTIFACT_COUNT_OR_DATES")
    out={}
    for p in paths:
        with zipfile.ZipFile(p) as z:
            files=z.namelist()
        if len(files)!=1:raise ValueError("STAGE28_UNKNOWN_ZIP_MEMBERS")
        name=files[0]
        if not name.startswith("monster_stage28_") or not name.endswith("_real_shared_sqlite.json"):
            raise ValueError("STAGE28_UNRELATED_ARTIFACT")
        day=name.removeprefix("monster_stage28_").removesuffix("_real_shared_sqlite.json")
        if day not in sources or day in out:
            raise ValueError("STAGE28_DUPLICATE_OR_NONFROZEN_DATE")
        out[day]=read_artifact(p,sources[day])
    return summarize(out)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--original-zips",nargs=6,required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    a=p.parse_args()
    d=run(a.original_zips)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(d,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("STAGE28_AGGREGATE_JSON "+json.dumps(
       {k:v for k,v in d.items() if k not in ("setup_UTC_hour_histogram","setup_event_register")},
       sort_keys=True),flush=True)

if __name__=="__main__":main()
