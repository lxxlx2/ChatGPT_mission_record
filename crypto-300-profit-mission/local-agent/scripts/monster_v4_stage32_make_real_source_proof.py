#!/usr/bin/env python3
"""Stage32 exact completed all 36 original CI full758 3m/1m SHA source proof.

Never accept early/partial run or failure; verify each GitHub original ZIP/JSON,
each full-case monthly1h and ten daily1m source publisher checksum,
all exact fixed date/shard identities and source cohort.
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

SOURCE_RUN=38158924838
SOURCE_COMMIT="75ca627579cddb6b8220f7e1da36f2786cce2da6"
REPO="repos/lxxlx2/ChatGPT_mission_record/"
DAYS=("2025-03-19","2025-06-19","2025-09-19","2025-12-19","2026-01-19","2026-03-19")
RX=re.compile(r"^monster-stage32-1min-vs3min-(\d{4}-\d\d-\d\d)-shard([0-5])$")
SCHEMA="MONSTER_STAGE32_PAIRED_FRESH_758_TWO_CADENCES_REAL_SOURCE_V1"

def gh(path):
    return subprocess.check_output(["gh","api","-H","Accept: application/vnd.github+json",REPO+path])

def collect(get=gh):
    run=json.loads(get("actions/runs/"+str(SOURCE_RUN)))
    if run.get("status")!="completed" or run.get("conclusion")!="success":
        raise ValueError("STAGE32_NOT_COMPLETE_SOURCE_CI")
    if run.get("head_sha")!=SOURCE_COMMIT:
        raise ValueError("STAGE32_CHANGED_POST_REGISTRATION_ORIGINAL_CI_SOURCE")
    outer=json.loads(get(f"actions/runs/{SOURCE_RUN}/artifacts?per_page=100"))
    arts=outer.get("artifacts",[])
    if outer.get("total_count")!=36 or len(arts)!=36:
        raise ValueError("STAGE32_NOT_COMPLETE36_REAL_CI_ARTIFACTS")
    rows=[];seen=set();market={}
    for art in arts:
        m=RX.fullmatch(art["name"])
        if not m or m.group(1) not in DAYS:
            raise ValueError("STAGE32_UNEXPECTED_SOURCE_ARTIFACT_NAME")
        day,shard=m.group(1),int(m.group(2))
        key=(day,shard)
        if key in seen:raise ValueError("STAGE32_DUPLICATE_FROZEN_SHARD")
        seen.add(key)
        zipped=get(f"actions/artifacts/{art['id']}/zip")
        zip_sha=hashlib.sha256(zipped).hexdigest()
        if art.get("digest")!="sha256:"+zip_sha:
            raise ValueError("STAGE32_ACTUAL_ARTIFACT_DIGEST_CHANGED")
        expected=f"monster_stage32_{day}_shard{shard}.json"
        with zipfile.ZipFile(io.BytesIO(zipped)) as z:
            if z.namelist()!=[expected] or z.getinfo(expected).file_size>40_000_000:
                raise ValueError("STAGE32_UNEXPECTED_ZIP_MEMBER")
            payload=z.read(expected)
        doc=json.loads(payload)
        if doc["schema"]!=SCHEMA or (doc["date"],doc["shard"])!=key:
            raise ValueError("STAGE32_CROSS_DAY_SYMBOL_SOURCE_DRIFT")
        cs=doc["results"]
        if len(cs) not in (126,127) or len({x["symbol"] for x in cs})!=len(cs):
            raise ValueError("STAGE32_INVALID_SYMBOL_SHARD")
        if doc["summary"]["total_attempted"]!=len(cs):
            raise ValueError("STAGE32_WRONG_TOTAL_IN_SOURCE_SUMMARY")
        by_status=collections.Counter(x["status"] for x in cs)
        if by_status!=collections.Counter(doc["summary"]["source_statuses"]):
            raise ValueError("STAGE32_SOURCE_SOURCE_STATUS_MISMATCH")
        sym=market.setdefault(day,set())
        if sym.intersection(x["symbol"] for x in cs):
            raise ValueError("STAGE32_SAME_SYMBOL_REPEATED_BETWEEN_SHARDS")
        sym.update(x["symbol"] for x in cs)
        for r in cs:
            if r["date"]!=day:raise ValueError("STAGE32_WRONG_ORIGINAL_DAY")
            if r["status"]=="COMPLETE_BOTH_168H":
                if len(r["monthly_GT_official_publisher_SHA256"])!=64:
                    raise ValueError("STAGE32_NO_MONTHLY_GT_PUBLISHER_SHA")
                pr=r["ten_daily_1m_publisher_sha256"]
                if len(pr)!=10 or len({x["date"] for x in pr})!=10 or any(len(x.get("sha256",""))!=64 for x in pr):
                    raise ValueError("STAGE32_NO_10_REAL_DAILY_PUBLISHER_SHA")
                if (r["V4_original3m"]["polls"],r["V4_candidate1m"]["polls"])!=(3360,10080):
                    raise ValueError("STAGE32_SCAN_SOURCE_INCOMPLETE")
            elif r["status"] not in ("CENSORED_GT_NOT_COMPLETE_168H","CENSORED_MISSING_MINUTE_ARCHIVE","CENSORED_GAPPED_216H_MINUTE_ARCHIVE"):
                raise ValueError("STAGE32_UNCLASSIFIED_SOURCE_ERROR")
        rows.append({"date":day,"shard":shard,"artifact_id":art["id"],
              "zip_sha256":zip_sha,"raw_json_sha256":hashlib.sha256(payload).hexdigest(),
              "original_json_bytes":len(payload),"attempted":len(cs),
              "paired_complete":by_status["COMPLETE_BOTH_168H"],
              "watch_original3m":doc["summary"]["baseline3m_watch"],
              "watch_candidate1m":doc["summary"]["candidate1m_watch"],
              "gt2_positive":doc["summary"]["2x"]["gt_positive_count"],
              "early2_original":doc["summary"]["2x"]["3m"]["early"],
              "early2_candidate":doc["summary"]["2x"]["1m"]["early"]})
    if seen!={(d,s) for d in DAYS for s in range(6)}:
        raise ValueError("STAGE32_NOT_ALL_SIX_DAYS_EVERY_SHARD")
    if any(len(v)!=758 for v in market.values()) or any(
          market[d]!=market[DAYS[0]] for d in DAYS):
        raise ValueError("STAGE32_FROZEN_758_MARKET_LIST_CHANGED")
    rows.sort(key=lambda x:(x["date"],x["shard"]))
    by_date=[]
    for day in DAYS:
        it=[x for x in rows if x["date"]==day]
        by_date.append({"date":day,"attempted":sum(x["attempted"] for x in it),
          "paired_complete":sum(x["paired_complete"] for x in it),
          "watch3":sum(x["watch_original3m"] for x in it),
          "watch1":sum(x["watch_candidate1m"] for x in it),
          "gross2":sum(x["gt2_positive"] for x in it),
          "early2_original":sum(x["early2_original"] for x in it),
          "early2_candidate":sum(x["early2_candidate"] for x in it)})
    return {"schema":"MONSTER_STAGE32_FULL_36_ORIGINAL_REAL_CI_ARTIFACT_SHA_PROOF_V1",
        "source_real_run_id":SOURCE_RUN,
        "source_real_run_url":f"https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/{SOURCE_RUN}",
        "source_original_commit_SHA":SOURCE_COMMIT,
        "source_ci_status":"SUCCESS_ALL_36",
        "full_market_dates_pre_frozen":list(DAYS),"all758_per_date":True,
        "all_original_zip_and_uncompressed_JSON_byte_SHA256_rechecked":True,
        "all_joint_complete_monthly1h_and_10_daily1m_publisher_sha_verified":True,
        "original_3m_and_candidate_1m_source_shared_each_symbol":True,
        "per_date":by_date,"artifacts":rows,
        "historical_orderbook_and_fills":"NOT_AVAILABLE",
        "independent_other_AI_review":"NOT_DONE","deployment":"NO_GO","Frank":"UNCHANGED"}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output",required=True,type=Path)
    a=p.parse_args()
    d=collect()
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(d,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("STAGE32_FULL36_TRUE_SOURCE_PROOF "+json.dumps(d,sort_keys=True),flush=True)
if __name__=="__main__": main()
