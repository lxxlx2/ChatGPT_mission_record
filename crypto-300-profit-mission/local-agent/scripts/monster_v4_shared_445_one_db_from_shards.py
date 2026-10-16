#!/usr/bin/env python3
"""All 28 validated source shards -> ONE 445-symbol production D0/D1 SQLite.

Never replay one shard as a surrogate 445 market. Zero live side effects.
Historical exposed data, source-complete survivor subset not full 758/PIT.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile

import monster_v4_shared_spot_d0_d1_original_core as shared
import monster_v4_shared_445_official_source_shards as shards

SCHEMA = "MONSTER_FEB2026_ALL445_ONE_SQLITE_CAUSAL_D0_D1_SOURCE_COMPLETE_V1"


def expected_file_pair(folder, i):
    return (Path(folder)/f"monster_feb445_shard{i:02d}.zip",
            Path(folder)/f"monster_feb445_shard{i:02d}.proof.json")


def verified_shard_paths(folder):
    """Preflight all 28 ZIP/proofs and their raw SHA before model starts.

    Read publisher source rows *one symbol at a time* in the later ingest;
    never materialize 445 x 12,960 Decimal bars in process memory.
    """
    archives=[]
    for i in range(shards.SHARD_COUNT):
        path,pf=expected_file_pair(folder,i)
        if not path.is_file() or not pf.is_file():
            raise ValueError("SHARED_445_REQUIRED_28_ORIGINAL_SOURCE_SHARDS_MISSING")
        proof=json.loads(pf.read_text(encoding="utf-8"))
        if (proof.get("schema")!="MONSTER_FEB2026_445_OFFICIAL_SHARD_ARTIFACT_PROOF_V1"
                or proof.get("shard")!=i
                or proof.get("source_origin_verified_at_collection") is not True
                or proof.get("source_symbol_count")!=len(shards.members(i))
                or proof.get("symbols")!=list(shards.members(i))
                or shards.sha(path.read_bytes())!=proof.get("sha256_zip")):
            raise ValueError("SHARED_445_SHARD_PROOF_OR_OFFICIAL_ORIGIN_UNVERIFIED")
        archives.append((i,path,proof))
    return archives


def run_all(folder, *, actual_replayer=None, read_inputs=None,
            research_zeroquote_v2=False):
    # Explicit research variant is only a selection between frozen
    # implementation functions; custom callback test hooks remain untrusted.
    if research_zeroquote_v2 and actual_replayer is not None:
        raise ValueError("SHARED_445_CANNOT_COMBINE_RESEARCH_V2_WITH_CUSTOM_ENGINE")
    trusted=read_inputs is None and actual_replayer is None
    if research_zeroquote_v2:
        from monster_v4_shared_d1_zeroquote_research_v2 import run_v2
        engine=run_v2
    else:
        engine=shared.run_shared if actual_replayer is None else actual_replayer
    frozen=shards.roster()
    if read_inputs is None:
        archives=verified_shard_paths(folder)
        provenance=[{"shard":i,"zip_sha256":proof["sha256_zip"],
                      "producer_trigger_sha":proof["trigger_commit_sha"],
                      "symbols":len(shards.members(i))}
                    for i,_,proof in archives]
    else:
        source,provenance=read_inputs(folder)
        if tuple(sorted(source))!=frozen or len(source)!=445:
            raise ValueError("SHARED_445_CANNOT_RUN_PARTIAL_MARKET")
        if len(provenance)!=28 or sorted(x["shard"] for x in provenance)!=list(range(28)):
            raise ValueError("SHARED_445_PROVENANCE_NOT_ALL_28_SHARDS")
    with tempfile.TemporaryDirectory(prefix="monster_445_offline_one_sqlite_") as td:
        with shared.setup_cache(Path(td)/"all445_official_minute_cache.sqlite") as db:
            checked_symbols=[]
            def ingest(symbol, bars, receipts):
                if (symbol not in frozen or
                        (checked_symbols and symbol<=checked_symbols[-1])):
                    raise ValueError("SHARED_445_INGEST_ORDER_DUPLICATE_OR_FOREIGN")
                attest=[{"date":r["day"],"sha256":r["sha256"],
                         "verified_published_sha256":True,
                         "verified_by":"PREVIOUS_OFFICIAL_SHARD_ARTIFACT"}
                        for r in receipts]
                shared.prepare_symbol(db,symbol,shards.DAY,bars,attest)
                checked_symbols.append(symbol)
            if read_inputs is None:
                for i,path,proof in archives:
                    actual=[]
                    for sym,bars,receipts,meta in shards.read_archive(
                            path,proof=proof,expected_shard=i):
                        if meta.get("source_origin_verified_at_collection") is not True:
                            raise ValueError("SHARED_445_SOURCE_ARCHIVED_ORIGIN_UNATTESTED")
                        ingest(sym,bars,receipts)
                        actual.append(sym)
                    if actual!=list(shards.members(i)):
                        raise ValueError("SHARED_445_SOURCE_SHARD_POPULATION_SHORT")
            else:
                for sym in frozen:
                    bars,receipts=source[sym]
                    ingest(sym,bars,receipts)
            if tuple(checked_symbols)!=frozen or len(checked_symbols)!=445:
                raise ValueError("SHARED_445_FULL_FROZEN_UNIVERSE_MISSING_OR_EXTRA")
            # The genuine model executes once only after all 445 verified
            # historical sources have been assembled in one staging cache.
            result=engine(db,shards.DAY,frozen,
                          market_coverage_label="OFFICIAL_VERIFIED_SUBSET_ONLY")
    if result.get("actually_complete_symbols")!=445:
        raise ValueError("SHARED_445_ENGINE_DID_NOT_SCAN_ALL_SYMBOLS")
    if result.get("execution_counts",{}).get("polls")!=3360:
        raise ValueError("SHARED_445_ENGINE_WRONG_GLOBAL_POLL_COUNT")
    if result.get("true_full_758_replay") is not False:
        raise ValueError("SHARED_445_FALSIFIED_FULL_758_VERIFICATION")
    original=shared.original_758_coverage(shards.DAY,frozen,source_attested=False)
    if (original["source_complete_original_stage26"]!=445
         or original["source_missing_or_incomplete_original_stage26"]!=313
         or original["replayed_verifiable_subset"]!=445):
        raise ValueError("SHARED_445_ORIGINAL_758_CENSORED_SCOPE_DRIFT")
    result.update({
      "schema":SCHEMA,
      "source_origin_verified":False,
      "source_origin_provenance":(
        "ARCHIVED_SAME_HOST_PUBLISHER_ZIP_CHECKSUM_ASSERTIONS_NEED_ORIGINAL_CI_ATTESTATION"
        if trusted else "SYNTHETIC_TEST_NOT_OFFICIAL"),
      "all_28_source_archive_shas":provenance,
      "publisher_archive_sha_after_source_ingestion_verified":trusted,
      "original_758_coverage":original,
      "source_complete_445_members_observed":445,
      "source_missing_313_not_assumed_zero":True,
      "full_758_market_replayed":False,
      "true_full_445_shared_source_complete_subset_replayed":trusted,
      "not_independent_OOS":True,
      "not_real_PIT_listing":True,
      "D1_model_semantics":("RESEARCH_V2_SOURCE_UNSUPPORTED_ZEROQUOTE"
                             if research_zeroquote_v2 else
                             "FROZEN_ORIGINAL_PRODUCTION_D1"),
      "all445_original_production_D1_completed":not research_zeroquote_v2,
      "experimental_source_semantics_approved_for_trading":False,
      "G4":"UNKNOWN","G6":"NO_GO",
      "trigger_commit_sha":os.environ.get("GITHUB_SHA","LOCAL_UNVERIFIED"),
      "assembler_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    })
    return result


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source-dir",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    p.add_argument("--research-zeroquote-v2",action="store_true")
    a=p.parse_args()
    if a.out.exists() or a.out.is_symlink():
        raise ValueError("SHARED_445_ASSEMBLER_OUTPUT_EXISTS")
    result=run_all(a.source_dir,research_zeroquote_v2=a.research_zeroquote_v2)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    with a.out.open("x",encoding="utf-8") as out:
        out.write(json.dumps(result,sort_keys=True,ensure_ascii=False,indent=2)+"\n")
    print("MONSTER_FEB445_ALL_SOURCE_COMPLETE_ONE_SQLITE "+
          json.dumps({"source_shards":len(result["all_28_source_archive_shas"]),
            "source_complete":445,"old_censored":313,
            "global_polls":result["execution_counts"]["polls"],
            "D0_WATCH":result["execution_counts"]["D0_watch_new"],
            "D1":result["queue_status_counts"],
            "D1_model_semantics":result["D1_model_semantics"],
            "true_full_758_replayed":False},sort_keys=True))


if __name__=="__main__":
    main()
