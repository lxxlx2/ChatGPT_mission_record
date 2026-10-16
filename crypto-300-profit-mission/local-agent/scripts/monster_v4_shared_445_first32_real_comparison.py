#!/usr/bin/env python3
"""First 32 of frozen 445; two source ZIP shards, ONE shared SQLite D0/D1."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import tempfile

import monster_v4_shared_spot_d0_d1_original_core as shared
import monster_v4_shared_445_official_source_shards as shards
import monster_v4_stage26_continuous168h as stage26

SCHEMA="MONSTER_FEB2026_FROZEN_FIRST32_TWO_SOURCE_SHARD_ONE_GLOBAL_SQLITE_V1"


def strict_roster():
    r=shards.roster()
    first32=r[:32]
    if (len(first32)!=32 or
            first32!=shards.members(0)+shards.members(1) or
            len(set(first32))!=32):
        raise ValueError("SHARED_445_FIRST32_NOT_EXACT_ORIGINAL_TWO_SHARDS")
    return first32


def analyze_two(source_dir, *, legacy_scan=None, shared_run=None):
    legacy=stage26.scan_continuous if legacy_scan is None else legacy_scan
    live=shared.run_shared if shared_run is None else shared_run
    truly_ci_archive = legacy_scan is None and shared_run is None
    selected=strict_roster()
    source_proofs=[]
    old=[]
    with tempfile.TemporaryDirectory(prefix="monster_feb445_real_first32_") as td:
        with shared.setup_cache(Path(td)/"first32_offline_1m.sqlite") as db:
            found=[]
            for i in (0,1):
                path=Path(source_dir)/f"monster_feb445_shard{i:02d}.zip"
                pf=Path(source_dir)/f"monster_feb445_shard{i:02d}.proof.json"
                if not pf.is_file() or not path.is_file():
                    raise ValueError("SHARED_445_FIRST32_TWO_VERIFIED_SOURCE_SHARDS_REQUIRED")
                proof=json.loads(pf.read_text())
                if (proof.get("shard")!=i or
                        proof.get("source_origin_verified_at_collection") is not True
                        or proof.get("symbols")!=list(shards.members(i))):
                    raise ValueError("SHARED_445_FIRST32_SOURCE_PROVENANCE_REJECTED")
                source_proofs.append({"shard":i,"source_archive_sha256":proof["sha256_zip"],
                    "producer_sha":proof["trigger_commit_sha"],"source_symbols":16,
                    "publisher_sha_days":160})
                this=[]
                for symbol,bars,receipts,metadata in shards.read_archive(
                        path,proof=proof,expected_shard=i):
                    if symbol in found:
                        raise ValueError("SHARED_445_FIRST32_DUPLICATED_SOURCE_MEMBER")
                    attested=[{"date":r["day"],"sha256":r["sha256"],
                               "verified_published_sha256":True,
                               "verified_by":"PREVIOUS_CI_SOURCE_ARCHIVE_CHECKSUM_READER"}
                              for r in receipts]
                    shared.prepare_symbol(db,symbol,shards.DAY,bars,attested)
                    oldcase=legacy(symbol,shards.DAY,bars)
                    old.append({"symbol":symbol,"old_watch_utcs":oldcase["watch_utcs"],
                                "old_setups":oldcase["setups"]})
                    found.append(symbol)
                    this.append(symbol)
                if this!=list(shards.members(i)):
                    raise ValueError("SHARED_445_FIRST32_INCOMPLETE_SOURCE_SHARD")
            if tuple(found)!=selected:
                raise ValueError("SHARED_445_FIRST32_MEMBER_DRIFT")
            result=live(db,shards.DAY,selected,
                         market_coverage_label="OFFICIAL_VERIFIED_SUBSET_ONLY")
    if (result["execution_counts"]["polls"]!=3360 or
            result["actually_complete_symbols"]!=32 or
            result["true_full_758_replay"]):
        raise ValueError("SHARED_445_FIRST32_ORIGINAL_GLOBAL_ENGINE_FAILED")
    oldutc={x["symbol"]:[stage26.replay.parse_ms(t) for t in x["old_watch_utcs"]]
            for x in old}
    newutc={x:[] for x in selected}
    by_tick=Counter()
    for event in result["events"]:
        if event["event_type"]=="WATCH_EARLY":
            newutc[event["symbol"]].append(event["observed_ms"])
            by_tick[event["observed_ms"]]+=1
    discrepancies=[]
    for sym in selected:
        if sorted(oldutc[sym])!=sorted(newutc[sym]):
            discrepancies.append(sym)
    if discrepancies:
        raise RuntimeError("SHARED_445_FIRST32_OLD_VS_GLOBAL_D0_WATCH_MISMATCH")
    scope=shared.original_758_coverage(shards.DAY,selected,
                                        source_attested=False)
    if (scope["original_758_denominator"]!=758
            or scope["source_complete_original_stage26"]!=445
            or scope["source_missing_or_incomplete_original_stage26"]!=313
            or scope["source_complete_but_not_replayed"]!=413):
        raise ValueError("SHARED_445_FIRST32_SOURCE_CENSOR_DENOMINATOR_WRONG")
    hit=stage26.replay.parse_ms("2026-02-06T00:36:00Z")
    result.update({
      "schema":SCHEMA,
      "source_origin_verified":False,
      "source_attestation":"PREVIOUS_CI_PUBLISHER_ZIP_CHECKSUM_VERIFIED_WITH_RAW_ZIP_AND_PER_MEMBER_SHA_RECHECK",
      "new_downloads_in_this_replay":False,
      "archive_original_download_verified_in_source_ci":truly_ci_archive,
      "market_coverage":"TWO_SOURCE_SHARDS_FIRST32_OF_FROZEN_445_NOT_FULL_758",
      "original_758_coverage":scope,
      "first32_symbols":list(selected),
      "two_original_source_artifact_shas":source_proofs,
      "old_stage26_same_minute_bars":old,
      "same_source_all_32_D0_watch_utc_exact":True,
      "original_per_symbol_old_watch_total":sum(map(len,oldutc.values())),
      "new_shared_D0_max_3minute_simultaneous_watch":max(by_tick.values(),default=0),
      "new_shared_D0_simultaneous_20260206_0036_UTC":by_tick[hit],
      "new_shared_D0_0036_symbols":sorted(
          event["symbol"] for event in result["events"]
          if event["event_type"]=="WATCH_EARLY" and event["observed_ms"]==hit),
      "source_complete_cohort_total":445,
      "source_complete_not_replayed":413,
      "old_source_missing_not_zero":313,
      "true_full_445_replayed":False,
      "historically_exposed_not_OOS":True,
      "no_PIT_listing_or_real_orderbook":True,
      "G4":"UNKNOWN","G6":"NO_GO",
      "trigger_commit_sha":os.environ.get("GITHUB_SHA","LOCAL_UNVERIFIED"),
      "first32_runner_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    })
    return result


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--source-dir",required=True,type=Path)
    parser.add_argument("--out",required=True,type=Path)
    args=parser.parse_args()
    if args.out.exists() or args.out.is_symlink():
        raise ValueError("SHARED_445_FIRST32_OUTPUT_EXISTS")
    report=analyze_two(args.source_dir)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    with args.out.open("x",encoding="utf-8") as h:
        h.write(json.dumps(report,sort_keys=True,ensure_ascii=False,indent=2)+"\n")
    print("MONSTER_FEB445_REAL_SHARED_D0_D1_FIRST32 "+
      json.dumps({k:report[k] for k in (
          "new_shared_D0_simultaneous_20260206_0036_UTC",
          "new_shared_D0_max_3minute_simultaneous_watch",
          "original_per_symbol_old_watch_total",
          "same_source_all_32_D0_watch_utc_exact",
          "queue_status_counts","event_type_counts")},sort_keys=True))


if __name__=="__main__":
    main()
