#!/usr/bin/env python3
"""Offline, read-only verification of F0 cohort preselection.

No RPC, no wallet keys, no installation dependencies and no Git writes.
Usage: python3 f0_verify_cohort.py --repo /path/to/ChatGPT_mission_record
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

SEED = "9134fcd41df49ef836b81c8a040974ad89c1fde1"
PR40_COMMIT = "431c02d1fcbe4babe8a2223e4e6fb1b0c0ac3a2c"
PR97_COMMIT = "5bca0e8f26c23c56ed4562e5ed260d8b3b7e7b8c"
PR40_PATH = "crypto-300-profit-mission/research/bsc-meme-address-model-v1-baseline-2026-10-13.json"
PR97_PATH = "crypto-300-profit-mission/address-analysis/evidence/activity-candidates-001-449.json"
PR40_BLOB = "e3c8815630878dddc03b7a6e11b8f0d2d89cbf6a"
PR97_BLOB = "4727b8b53dcd63b350d9e5f27922cd06db8a2a14"


def source_blob(repo: Path, commit: str, path: str, expected_blob: str) -> dict:
    source = f"{commit}:{path}"
    try:
        raw = subprocess.check_output(["git", "-C", str(repo), "cat-file", "blob", source])
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"Missing pinned local Git object {source}; fetch the PR refs first") from exc
    actual = hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()
    if actual != expected_blob:
        raise ValueError(f"Git blob mismatch: {source}: expected={expected_blob}, actual={actual}")
    return json.loads(raw)


def fnv1a32(text: str) -> int:
    h = 2166136261
    for byte in text.encode("ascii"):
        h = ((h ^ byte) * 16777619) & 0xFFFFFFFF
    return h


def ranked(source: str, candidates: list[dict]) -> list[dict]:
    for item in candidates:
        item["rank_uint32"] = fnv1a32(f"{SEED}|{source}|{item['wallet']}")
    return sorted(candidates, key=lambda x: (x["rank_uint32"], x["wallet"]))


def construct(repo: Path) -> tuple[list[dict], list[dict]]:
    p40 = source_blob(repo, PR40_COMMIT, PR40_PATH, PR40_BLOB)
    p97 = source_blob(repo, PR97_COMMIT, PR97_PATH, PR97_BLOB)
    forty = [
        {
            "source": "PR40_23",
            "wallet": w["wallet"].lower(),
            "source_index": i,
            "source_row": None,
            "qualification": "FROZEN_BSC_RESEARCH_CANDIDATE",
        }
        for i, w in enumerate(p40["wallets"], start=1)
    ]
    existing = {x["wallet"] for x in forty}
    ninetyseven = [
        {
            "source": "PR97_449_BSC_SIGNED",
            "wallet": x["address"].lower(),
            "source_index": None,
            "source_row": x["source_row"],
            "qualification": "BSC_FIRST_POSITIVE_NONCE_2026_09_17_TO_2026_10_17",
        }
        for x in p97["records"]
        if x["activity"] == "ACTIVE"
        and x["first_positive_chain"] == "bsc"
        and x["address"].lower() not in existing
    ]
    if len(forty) != 23 or len(ninetyseven) != 217:
        raise ValueError(f"Unexpected candidate counts: {len(forty)}, {len(ninetyseven)}")

    def choose(source: str, values: list[dict]) -> list[dict]:
        out = []
        for pos, item in enumerate(ranked(source, values)[:15], start=1):
            out.append({
                **item,
                "role": "PRIMARY" if pos <= 10 else "BACKUP",
                "cohort_position": pos,
                "eligibility": "PRESELECTED_UNVERIFIED_EOA_AND_CURRENT_ACTIVITY",
                "watch_runtime_enabled": False,
            })
        return out

    chosen = choose("PR40_23", forty) + choose("PR97_449_BSC_SIGNED", ninetyseven)
    overlaps = [
        {"source_row": x["source_row"], "wallet": x["address"].lower()}
        for x in p97["records"]
        if x["address"].lower() in existing
    ]
    return chosen, overlaps


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, help="path to a Git clone containing fixed PR40/PR97 objects")
    parser.add_argument("--manifest", default=str(Path(__file__).with_name("F0_COHORT_PRESELECTION.json")))
    args = parser.parse_args()
    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    if manifest["selection_seed"] != SEED:
        raise ValueError("Seed mismatch")
    actual, overlaps = construct(Path(args.repo))
    if actual != manifest["preliminary_wallets"]:
        for i, (a, b) in enumerate(zip(actual, manifest["preliminary_wallets"])):
            if a != b:
                raise ValueError(f"Selected row mismatch at {i}: {a} != {b}")
        raise ValueError("Selected sample count mismatch")
    if overlaps != manifest["excluded_pr97_overlap"]:
        raise ValueError("Cross-PR overlap mismatch")
    if len(actual) != 30 or len({x["wallet"] for x in actual}) != 30:
        raise ValueError("Selection or uniqueness test failed")
    if any(x["watch_runtime_enabled"] for x in actual):
        raise ValueError("Runtime flag enabled in offline-only preselection")
    print(json.dumps({
        "result": "PASS",
        "selection_seed": SEED,
        "PR40_total_pool": 23,
        "PR97_BSC_nonoverlap_pool": 217,
        "primaries": 20,
        "backups": 10,
        "excluded_PR97_overlaps": len(overlaps),
        "live_RPC_calls": 0,
        "production": "NO_GO",
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
