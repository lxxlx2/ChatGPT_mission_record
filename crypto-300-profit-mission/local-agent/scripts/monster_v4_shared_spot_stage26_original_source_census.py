#!/usr/bin/env python3
"""Strict 36 original Stage26 SHA-locked source eligibility; NOT full D0 replay."""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path

import monster_v4_stage26_aggregate as stage26

SCHEMA="MONSTER_SHARED_SPOT_STAGE26_36_ORIGINAL_SOURCE_ELIGIBILITY_V1"
EXPOSED_DATES=("2025-11-04","2025-12-04","2026-02-04",
               "2026-04-04","2026-08-04","2026-09-04")


def roster_sha(symbols):
    return hashlib.sha256(("\\n".join(symbols)+"\n").encode()).hexdigest()


def evaluate(all_reports, manifest):
    if len(all_reports)!=36 or len(manifest["artifacts"])!=36:
        raise ValueError("SHARED_SPOT_SOURCE_36_ORIGINAL_SHARDS_REQUIRED")
    if {d for d,_ in all_reports}!=set(EXPOSED_DATES):
        raise ValueError("SHARED_SPOT_ALL_SIX_EXPOSED_DATES_REQUIRED")
    daily=[]
    cohort=None
    full_total=0
    watch_total=0
    for day in EXPOSED_DATES:
        day_reports=[all_reports.get((day,s)) for s in range(6)]
        if any(r is None for r in day_reports):
            raise ValueError("SHARED_SPOT_MISSING_ORIGINAL_STAGE26_SHARD")
        cases=[c for report in day_reports for c in report["cases"]]
        symbols=tuple(sorted(c["symbol"] for c in cases))
        if len(symbols)!=758 or len(set(symbols))!=758:
            raise ValueError("SHARED_SPOT_INCOMPLETE_758_ORIGINAL_DATE_UNIVERSE")
        if cohort is None:
            cohort=symbols
        if symbols!=cohort:
            raise ValueError("SHARED_SPOT_ORIGINAL_758_UNIVERSE_CHANGED_BETWEEN_DATES")
        states=Counter(c["status"] for c in cases)
        full=states["COMPLETE_168H_CONTINUOUS_V4"]
        n_watches=sum(c["continuous"]["watch_count"] for c in cases
                      if c["status"]=="COMPLETE_168H_CONTINUOUS_V4")
        # Each complete case's official 10-day SHA is already checked in load_zip.
        if full!=sum(x["complete168h"] for x in manifest["artifacts"]
                     if x["date"]==day):
            raise ValueError("SHARED_SPOT_ORIGINAL_COMPLETE_COUNT_NOT_RECONCILED")
        if n_watches!=sum(x["watch_episodes"] for x in manifest["artifacts"]
                          if x["date"]==day):
            raise ValueError("SHARED_SPOT_ORIGINAL_WATCH_COUNT_NOT_RECONCILED")
        full_total+=full
        watch_total+=n_watches
        daily.append({
          "date":day,"original_universe_attempted":758,
          "source_complete_216h_eligible_for_original_model":full,
          "source_missing_or_incomplete":758-full,
          "source_status_counts":dict(sorted(states.items())),
          "complete_symbol_ids":[c["symbol"] for c in cases
                                  if c["status"]=="COMPLETE_168H_CONTINUOUS_V4"],
          "original_per_symbol_watch_events_NOT_SHARED_D0":n_watches,
          "full_universe_D0_shared_replayed":False})
    if full_total!=2719 or watch_total!=1132:
        raise ValueError("SHARED_SPOT_STAGE26_FROZEN_SOURCE_TOTAL_CHANGED")
    if manifest.get("source_complete_total")!=full_total or manifest.get("watch_total")!=watch_total:
        raise ValueError("SHARED_SPOT_SOURCE_MANIFEST_TOTAL_DISAGREES")
    return {
        "schema":SCHEMA,
        "trigger_commit_sha":os.environ.get("GITHUB_SHA","LOCAL_UNVERIFIED"),
        "source_census_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "frozen_source_commit_sha":manifest["source_git_sha"],
        "original_manifest_schema":manifest["schema"],
        "old_stage26_shard_count":36,
        "original_758_symbols":list(cohort),
        "original_758_symbols_sha256":roster_sha(cohort),
        "all_six_dates_population_attempts":4548,
        "all_six_dates_source_complete":full_total,
        "all_six_dates_source_missing_or_incomplete":4548-full_total,
        "total_original_individual_spot_watch_events":watch_total,
        "actual_full_758_shared_D0_D1_run":"NOT_RUN",
        "retrospective_exposed_not_OOS":True,
        "data_source":"ORIGINAL_GITHUB_STAGE26_ZIP_AND_INTERNAL_JSON_SHA256_VERIFIED",
        "daily":daily,
        "G4":"UNKNOWN","G6":"NO_GO",
        "no_gmail_deploy_frank_trade":True}


def run(artifact_dir,proof=stage26.PROOF):
    manifest=json.loads(Path(proof).read_text())
    reports={}
    for rec in manifest["artifacts"]:
        target=Path(artifact_dir)/f"monster_stage26_{rec['date']}_shard{rec['shard']}.zip"
        reports[rec["date"],rec["shard"]]=stage26.load_zip(target,rec)
    return evaluate(reports,manifest)


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source-artifact-dir",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    if args.out.exists():
        raise ValueError("SHARED_SPOT_CENSUS_OUTPUT_EXISTS_REFUSE_OVERWRITE")
    result=run(args.source_artifact_dir)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    with args.out.open("x",encoding="utf-8") as h:
        h.write(json.dumps(result,sort_keys=True,ensure_ascii=False,indent=2)+"\\n")
    print("SHARED_SPOT_ORIGINAL_SOURCE_ELIGIBILITY "+
          json.dumps({k:result[k] for k in
                      ("all_six_dates_population_attempts",
                       "all_six_dates_source_complete",
                       "all_six_dates_source_missing_or_incomplete",
                       "original_758_symbols_sha256")},sort_keys=True))


if __name__=="__main__":
    main()
