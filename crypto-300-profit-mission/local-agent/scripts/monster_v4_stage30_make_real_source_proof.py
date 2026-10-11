#!/usr/bin/env python3
"""Derive Stage30 original real 36 artifact ZIP + inner JSON SHA256 proof.

Does NOT claim signal profit or success from a queued/in-progress CI.
Requires the exact preregistered six day source CI run completely successful,
checks source commit, the 36 artifact sets, publisher-source SHA and full 758
case coverage by day. Prints the WHOLE proof for audit and uploads JSON.
"""
import argparse
import collections
import hashlib
import io
import json
import re
import subprocess
import zipfile
from pathlib import Path

RUN=38154393594
SOURCE_COMMIT="bd37cdf4f006845b9ce7c8b81a4c6c2f518d0a57"
REPO="repos/lxxlx2/ChatGPT_mission_record/"
DATES=("2025-01-19","2025-04-19","2025-07-19","2025-10-19","2026-04-19","2026-07-19")
NAME=re.compile(r"^monster-stage30-758-full168h-newdate-(\d{4}-\d\d-\d\d)-shard([0-5])$")

def api(path):
    return subprocess.check_output(["gh","api","-H","Accept: application/vnd.github+json",REPO+path])

def prove(get=api):
    run=json.loads(get("actions/runs/"+str(RUN)))
    if run.get("status")!="completed" or run.get("conclusion")!="success":
        raise ValueError("STAGE30_SOURCE_RUN_NOT_COMPLETE_SUCCESS")
    if run.get("head_sha")!=SOURCE_COMMIT:
        raise ValueError("STAGE30_PRECOMMITTED_SOURCE_HEAD_CHANGED")
    raw=json.loads(get("actions/runs/"+str(RUN)+"/artifacts?per_page=100"))
    artifacts=raw.get("artifacts",[])
    if raw.get("total_count")!=36 or len(artifacts)!=36:
        raise ValueError("STAGE30_NOT_ALL_36_ARTIFACTS_IN_REAL_RUN")
    out=[];cohorts={};seen=set()
    for item in artifacts:
        match=NAME.fullmatch(item["name"])
        if not match or match[1] not in DATES:
            raise ValueError("STAGE30_UNEXPECTED_REAL_ARTIFACT")
        day,shard=match[1],int(match[2])
        if (day,shard) in seen:
            raise ValueError("STAGE30_DUPLICATE_ARTIFACT")
        seen.add((day,shard))
        orig=get("actions/artifacts/"+str(item["id"])+"/zip")
        digest=hashlib.sha256(orig).hexdigest()
        if item.get("digest")!="sha256:"+digest:
            raise ValueError("STAGE30_ORIGINAL_ZIP_DIGEST_CHANGED")
        path=f"monster_stage30_{day}_shard{shard}.json"
        with zipfile.ZipFile(io.BytesIO(orig)) as z:
            if z.namelist()!=[path] or z.getinfo(path).file_size>20_000_000:
                raise ValueError("STAGE30_UNEXPECTED_ZIP_MEMBER")
            raw_json=z.read(path)
        doc=json.loads(raw_json)
        if doc["schema"]!="MONSTER_STAGE30_NEW_FROZEN_758x6_FULL168H_ORIGINAL_V4_SHA_VERIFIED_V1":
            raise ValueError("STAGE30_WRONG_SCHEMA")
        if (doc["date"],doc["shard"])!=(day,shard):
            raise ValueError("STAGE30_WRONG_DATE_OR_SHARD")
        cases=doc["cases"]
        if len(cases) not in (126,127):
            raise ValueError("STAGE30_BAD_SHARD_CASE_COUNT")
        ss={r["symbol"] for r in cases}
        if len(ss)!=len(cases):
            raise ValueError("STAGE30_DUPLICATE_SYMBOL")
        prior=cohorts.setdefault(day,set())
        if prior.intersection(ss):
            raise ValueError("STAGE30_REPEATED_SYMBOL_ACROSS_SHARDS")
        prior.update(ss)
        count=collections.Counter(r["status"] for r in cases)
        if count!=collections.Counter(doc["summary"]["source_status_counts"]):
            raise ValueError("STAGE30_SUMMARY_SOURCE_COUNTS_DIFFER")
        for row in cases:
            if row["date"]!=day:
                raise ValueError("STAGE30_WRONG_SOURCE_DATE")
            if row["status"]=="COMPLETE_168H_CONTINUOUS_V4":
                if len(row.get("hourly_GT_monthly_SHA256") or "")!=64:
                    raise ValueError("STAGE30_MISSING_REAL_MONTHLY_GT_PUBLISHER_SHA")
                if row.get("hourly_GT_original_status")!="VERIFIED_COMPLETE_168H":
                    raise ValueError("STAGE30_GT_NOT_COMPLETE")
                pp=row.get("official_source_SHA256_days")
                if len(pp)!=10 or len({x["date"] for x in pp})!=10 or any(len(x.get("sha256",""))!=64 for x in pp):
                    raise ValueError("STAGE30_MISSING_TEN_DAILY_1M_PUBLISHER_SHA")
                if row["continuous"].get("polls")!=3360 or row["continuous"].get("continuous_sqlite_reset_count")!=0:
                    raise ValueError("STAGE30_WRONG_ORIGINAL_SEVEN_DAY_SNAPSHOT_POLL_COUNTS")
        for s in count:
            if "NETWORK" in s or "INTEGRITY_REJECTED" in s or "HTTP_FAILED" in s:
                raise ValueError("STAGE30_NONDETERMINISTIC_SOURCE_ERROR")
        out.append({"date":day,"shard":shard,"artifact_id":item["id"],
            "zip_sha256":digest,"raw_json_sha256":hashlib.sha256(raw_json).hexdigest(),
            "case_count":len(cases),
            "complete":count["COMPLETE_168H_CONTINUOUS_V4"],
            "source_status_counts":dict(count),
            "WATCH":doc["summary"]["watch_events"],
            "D1":doc["summary"]["D1_SETUPS"],
            "gross_2x_positive":doc["summary"]["gross_2x"]["source_verifiable_positive_coin_dates"],
            "early_2x":doc["summary"]["gross_2x"]["early_watch"],
            "gross_5x_positive":doc["summary"]["gross_5x"]["source_verifiable_positive_coin_dates"],
            "gross_10x_positive":doc["summary"]["gross_10x"]["source_verifiable_positive_coin_dates"]})
    if seen!={(day,shard) for day in DATES for shard in range(6)}:
        raise ValueError("STAGE30_SIX_DATES_X_SIX_SHARDS_INCOMPLETE")
    if any(len(v)!=758 for v in cohorts.values()):
        raise ValueError("STAGE30_EACH_DATE_NOT_758_SYMBOLS")
    if any(v!=cohorts[DATES[0]] for v in cohorts.values()):
        raise ValueError("STAGE30_NOT_SAME_FROZEN_758_COHORT_ACROSS_DATES")
    out.sort(key=lambda x:(x["date"],x["shard"]))
    perdate=[]
    for d in DATES:
        subset=[r for r in out if r["date"]==d]
        perdate.append({"date":d,
            "attempted":sum(r["case_count"] for r in subset),
            "complete":sum(r["complete"] for r in subset),
            "watch":sum(r["WATCH"] for r in subset),
            "D1":sum(r["D1"] for r in subset),
            "gross_2x":sum(r["gross_2x_positive"] for r in subset),
            "early_2x":sum(r["early_2x"] for r in subset),
            "gross_5x":sum(r["gross_5x_positive"] for r in subset),
            "gross_10x":sum(r["gross_10x_positive"] for r in subset)})
    return {"schema":"MONSTER_STAGE30_TRUE_SIX_NEW_CALENDAR_36_ARTIFACT_ZIP_JSON_SHA256_V1",
        "source_run_id":RUN,"source_run":"https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/"+str(RUN),
        "source_ci_status":"SUCCESS_ALL_36",
        "source_model_and_tests_commit":SOURCE_COMMIT,
        "exact_original_36_ZIP_and_JSON_bytes_SHA_recomputed":True,
        "both_hourly_and_minute_official_publishers_checksums_verified_per_complete_case":True,
        "frozen_sample_each_date_758_real_cases":True,
        "same_frozen_cohort_across_new_six_dates":True,
        "per_date":perdate,"artifacts":out,
        "historical_L2_or_actual_fills":False,
        "full_real_global_D1_queue_replayed":False,
        "independent_other_AI_review":"NOT_DONE",
        "deployment":"NO_GO","gmail":"OFF","trading":"NO_GO","frank":"UNCHANGED"}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    d=prove()
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(d,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("STAGE30_TRUE_ORIGINAL36_SOURCE_PROOF_JSON "+json.dumps(d,sort_keys=True),flush=True)
if __name__=="__main__":main()
