#!/usr/bin/env python3
"""One-shot 28 frozen original publisher source Artifact downloader and replay attestor.

Does not run an exchange API, production DB, remote Mac, Gmail or trades.
Called by a single research CI request; no background or scheduled task.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

import monster_v4_shared_445_official_source_shards as shards
import monster_v4_shared_445_one_db_from_shards as assembler

SCHEMA = "MONSTER_FEB445_REAL_28_SHARDS_ONE_SQLITE_ARCHIVED_SOURCE_REPLAY_V1"
EVIDENCE = Path(__file__).resolve().parents[2] / "monster/evidence"
REPO = "lxxlx2/ChatGPT_mission_record"

# Immutable source artifact IDs in the 2026-10-16 all-source evidence record.
# Original 0..7 archives contain one frozen source shard each; 08..27 are pairs.
FROZEN_ARTIFACTS = (
    (12021352471, (0,)),
    (12021445690, (1,)),
    (12031203151, (2,)),
    (12031003792, (3,)),
    (12034075028, (4,)),
    (12033058858, (5,)),
    (12033614509, (6,)),
    (12034650662, (7,)),
    (12034158512, (8, 9)),
    (12035280222, (10, 11)),
    (12034634353, (12, 13)),
    (12034849164, (14, 15)),
    (12034639057, (16, 17)),
    (12034824063, (18, 19)),
    (12034424934, (20, 21)),
    (12035491878, (22, 23)),
    (12035133391, (24, 25)),
    (12036060934, (26, 27)),
)


def validate_ledger():
    if (len(FROZEN_ARTIFACTS) != 18
            or len({aid for aid, _ in FROZEN_ARTIFACTS}) != 18
            or tuple(i for _, indices in FROZEN_ARTIFACTS for i in indices)
                != tuple(range(28))
            or sum(len(shards.members(i)) for _, ids in FROZEN_ARTIFACTS
                   for i in ids) != 445):
        raise ValueError("MONSTER445_REPLAY_ARCHIVED_ARTIFACT_LEDGER_DRIFT")
    return True


def gh_json(*args):
    proc = subprocess.run(["gh", "api", "--hostname", "github.com", *args],
                          text=True, capture_output=True, check=True)
    return json.loads(proc.stdout)


def gh_download(run_id, name, dest):
    subprocess.run(["gh", "run", "download", str(run_id),
                    "--repo", REPO, "--name", name,
                    "--dir", str(dest)], check=True)


def collect(source_dir: Path, audit_file: Path, *, api=gh_json, downloader=gh_download):
    validate_ledger()
    if source_dir.exists() or source_dir.is_symlink():
        raise ValueError("MONSTER445_REPLAY_SOURCE_DIR_ALREADY_EXISTS")
    if audit_file.exists() or audit_file.is_symlink():
        raise ValueError("MONSTER445_REPLAY_AUDIT_OUTPUT_EXISTS")
    if not os.environ.get("GH_TOKEN"):
        raise RuntimeError("MONSTER445_REPLAY_GH_TOKEN_READ_ONLY_REQUIRED")
    source_dir.mkdir(parents=True)
    run_cache = {}
    audit = []
    for artifact_id, pair in FROZEN_ARTIFACTS:
        artifact = api(f"repos/{REPO}/actions/artifacts/{artifact_id}")
        if (artifact.get("id") != artifact_id
                or artifact.get("expired") is not False
                or not isinstance(artifact.get("name"), str)
                or not artifact["name"].startswith("monster-")
                or not isinstance(artifact.get("size_in_bytes"), int)
                or artifact["size_in_bytes"] <= 0
                or not isinstance(artifact.get("workflow_run"), dict)
                or type(artifact["workflow_run"].get("id")) is not int):
            raise RuntimeError("MONSTER445_REPLAY_ARTIFACT_METADATA_OR_EXPIRY_UNVERIFIED")
        run_id = artifact["workflow_run"]["id"]
        if run_id not in run_cache:
            run_cache[run_id] = api(f"repos/{REPO}/actions/runs/{run_id}")
        run = run_cache[run_id]
        if (run.get("id") != run_id or run.get("status") != "completed"
                or run.get("repository", {}).get("full_name") != REPO):
            raise RuntimeError("MONSTER445_REPLAY_PRODUCER_RUN_IDENTITY_OR_STATE_DRIFT")
        source_job_attested = "COMPLETE_PRODUCER_RUN_SUCCESS"
        if run.get("conclusion") != "success":
            # Two first source shards came from early 32-cohort workflows where
            # a *later model replay* failed despite the publisher source job
            # succeeding. Do not relabel those entire runs as successful.
            if len(pair)!=1 or pair[0] not in (0,1):
                raise RuntimeError("MONSTER445_REPLAY_NONFIRST_PRODUCER_RUN_FAILED")
            old_jobs=api(f"repos/{REPO}/actions/runs/{run_id}/jobs?per_page=100")
            target=f"official_shard{pair[0]:02d}_16_times_10_daily"
            if (not isinstance(old_jobs.get("jobs"),list)
                    or not any(j.get("name")==target
                               and j.get("status")=="completed"
                               and j.get("conclusion")=="success"
                               for j in old_jobs["jobs"])):
                raise RuntimeError("MONSTER445_REPLAY_FIRST_SOURCE_JOB_NOT_VERIFIED")
            source_job_attested="PUBLISHER_SOURCE_JOB_SUCCESS_OVERALL_RUN_FAILED"
        subdir = source_dir / f"artifact_{artifact_id}"
        subdir.mkdir()
        downloader(run_id, artifact["name"], subdir)
        expected = {f"monster_feb445_shard{i:02d}.{suffix}"
                    for i in pair for suffix in ("zip", "proof.json")}
        actual = {p.name for p in subdir.iterdir()}
        if actual != expected or not all(p.is_file() for p in subdir.iterdir()):
            raise RuntimeError("MONSTER445_REPLAY_ARCHIVE_CONTAINS_WRONG_SHARDS")
        for i in pair:
            stem=f"monster_feb445_shard{i:02d}"
            repo_proof = EVIDENCE / f"{stem}.proof.json"
            copied_proof = subdir / f"{stem}.proof.json"
            if (not repo_proof.is_file()
                    or copied_proof.read_bytes() != repo_proof.read_bytes()):
                raise RuntimeError("MONSTER445_REPLAY_GIT_SOURCE_PROOF_NOT_EQUAL_ARTIFACT")
            proof = json.loads(repo_proof.read_text(encoding="utf-8"))
            if (proof.get("shard") != i
                    or proof.get("trigger_commit_sha") != run.get("head_sha")
                    or proof.get("source_origin_verified_at_collection") is not True
                    or proof.get("symbols") != list(shards.members(i))):
                raise RuntimeError("MONSTER445_REPLAY_SHARD_SOURCE_TRIGGER_OR_ROSTER_DRIFT")
            zip_file=subdir / f"{stem}.zip"
            if (hashlib.sha256(zip_file.read_bytes()).hexdigest()
                    != proof.get("sha256_zip")):
                raise RuntimeError("MONSTER445_REPLAY_ORIGINAL_ZIP_SHA_MISMATCH")
            shutil.copyfile(zip_file, source_dir / zip_file.name)
            shutil.copyfile(repo_proof, source_dir / repo_proof.name)
            audit.append({
                "shard": i,
                "symbol_count": len(shards.members(i)),
                "artifact_id": artifact_id,
                "artifact_name": artifact["name"],
                "artifact_expires_at": artifact.get("expires_at"),
                "source_run_id": run_id,
                "source_run_sha": run["head_sha"],
                "source_run_conclusion": run["conclusion"],
                "source_job_attestation": source_job_attested,
                "zip_sha256": proof["sha256_zip"],
                "git_proof_sha256": hashlib.sha256(repo_proof.read_bytes()).hexdigest(),
                "ten_day_publisher_sha_count":
                    sum(len(x["publisher_days"]) for x in proof["source_sha256_by_symbol"]),
            })
        print("MONSTER445_REPLAY_REAL_SOURCE_ARCHIVE_PAIR_DOWNLOADED_VERIFIED",
              artifact_id, ",".join(map(str,pair)), flush=True)
    archives = assembler.verified_shard_paths(source_dir)
    if (len(archives) != 28 or len(audit) != 28
            or sum(x["ten_day_publisher_sha_count"] for x in audit) != 4450):
        raise RuntimeError("MONSTER445_REPLAY_SOURCE_COMPLETENESS_FALSE")
    audit_file.parent.mkdir(parents=True, exist_ok=True)
    with audit_file.open("x",encoding="utf-8") as f:
        json.dump({
            "schema": SCHEMA, "source_28_shards_verified": True,
            "source_445_symbols": True,
            "original_758_source_incomplete": 313,
            "source_artifacts": audit,
            "source_zip_only_research": True,
            "independent_other_ai_review": "NOT_DONE",
            "G4": "UNKNOWN", "G6": "NO_GO",
        },f,indent=2,sort_keys=True)
        f.write("\n")
    return audit


def summarize(audit_file: Path, replay_file: Path, output: Path):
    if output.exists() or output.is_symlink():
        raise ValueError("MONSTER445_REPLAY_REPORT_EXISTS")
    audit=json.loads(audit_file.read_text(encoding="utf-8"))
    replay=json.loads(replay_file.read_text(encoding="utf-8"))
    counts=replay.get("execution_counts",{})
    if (audit["source_28_shards_verified"] is not True
            or len(audit["source_artifacts"])!=28
            or len(replay.get("all_28_source_archive_shas",[]))!=28
            or replay.get("source_complete_445_members_observed")!=445
            or replay.get("actually_complete_symbols")!=445
            or replay.get("one_shared_sqlite_for_all_symbols") is not True
            or replay.get("true_full_445_shared_source_complete_subset_replayed") is not True
            or replay.get("true_full_758_replay") is not False
            or replay.get("not_independent_OOS") is not True
            or replay.get("not_real_PIT_listing") is not True
            or counts.get("polls")!=3360
            or replay.get("G6")!="NO_GO"):
        raise RuntimeError("MONSTER445_REPLAY_ACTUAL_SHARED_ENGINE_INCOMPLETE")
    if [(r["shard"],r["zip_sha256"]) for r in audit["source_artifacts"]] != [
        (r["shard"],r["zip_sha256"])
        for r in replay["all_28_source_archive_shas"]]:
        raise RuntimeError("MONSTER445_REPLAY_SOURCE_AUDIT_NOT_EQUAL_REPLAY")
    watches = [x for x in replay["events"] if x["event_type"]=="WATCH_EARLY"]
    per_tick=collections.Counter(x["observed_ms"] for x in watches)
    max_same_tick=max(per_tick.values(),default=0)
    report={
        "schema":SCHEMA,"research_date":"2026-02-04",
        "trigger_commit_sha":os.environ.get("GITHUB_SHA","LOCAL_UNVERIFIED"),
        "source_shards":28,"source_artifacts":18,"source_symbols":445,
        "historical_original_attempted":758,"censored":313,
        "publisher_day_sha_receipts":4450,
        "all_source_zip_sha256":[{"shard":e["shard"],"sha256":e["zip_sha256"]}
                                 for e in audit["source_artifacts"]],
        "one_shared_sqlite":True,"global_polls":3360,
        "original_production_core_blob":replay["origin_core_blob"],
        "core_sha256":replay["shared_replayer_sha256"],
        "assembler_sha256":replay["assembler_sha256"],
        "D0_watch_total":counts.get("D0_watch_new"),
        "max_watch_same_tick":max_same_tick,
        "D1_per_tick_capacity":8,
        "D1_execution_counts":{k:v for k,v in counts.items() if k.startswith("D1_")},
        "D1_queue_status_counts":replay.get("queue_status_counts",{}),
        "event_type_counts":replay.get("event_type_counts",{}),
        "full_replay_json_sha256":hashlib.sha256(replay_file.read_bytes()).hexdigest(),
        "source_audit_json_sha256":hashlib.sha256(audit_file.read_bytes()).hexdigest(),
        "candidate_rows":len(replay["queue_rows"]),
        "historical_exposed_not_OOS":True,"point_in_time_listing":"UNVERIFIED",
        "historical_orderbook_slippage_fees":"UNKNOWN",
        "executable_net_profit":"UNVERIFIED",
        "independent_other_ai_review":"NOT_DONE",
        "NO_MERGE":True,"NO_DEPLOY":True,"NO_GMAIL":True,"NO_TRADE":True,
        "G4":"UNKNOWN","G6":"NO_GO",
    }
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open("x",encoding="utf-8") as f:
        json.dump(report,f,sort_keys=True,indent=2)
        f.write("\n")
    print("MONSTER445_REAL_ALL_SOURCE_COMPLETE_ONE_SQLITE_D0_D1_REPLAY",
          json.dumps({k:report[k] for k in ("source_symbols","global_polls",
                "D0_watch_total","max_watch_same_tick","D1_queue_status_counts",
                "G4","G6")},sort_keys=True),flush=True)
    return report


def main():
    p=argparse.ArgumentParser()
    sub=p.add_subparsers(dest="command",required=True)
    cp=sub.add_parser("collect")
    cp.add_argument("--source-dir",type=Path,required=True)
    cp.add_argument("--audit",type=Path,required=True)
    sp=sub.add_parser("summarize")
    sp.add_argument("--audit",type=Path,required=True)
    sp.add_argument("--replay",type=Path,required=True)
    sp.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    if a.command=="collect":
        collect(a.source_dir,a.audit)
    else:
        summarize(a.audit,a.replay,a.out)


if __name__=="__main__":
    main()
