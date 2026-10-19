#!/usr/bin/env python3
"""Explicit on-demand independent source download and replay, never scheduled.

Run from an isolated checkout using own GitHub CLI authentication.  Downloads
eight small unchanged issuer archives plus two previously accessible archives.
Prints and saves actual locally recomputed events/economics and sha256 evidence.
No network to crypto exchanges, production DB or wallet. No notification/trade.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from monster_v4_first518_original_shards_computed_review import report, read

REPO = "lxxlx2/ChatGPT_mission_record"
RUN = 39235915099
COMP = Path(__file__).resolve().parents[2] / "monster/evidence"
ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def fetch(run, name, destination):
    destination.mkdir(parents=True)
    command = ["gh", "run", "download", str(run), "--repo", REPO,
               "--name", name, "--dir", str(destination)]
    subprocess.run(command, check=True)
    if not any(destination.rglob("*")):
        raise ValueError("MONSTER_AUDIT_DOWNLOADED_EMPTY:" + name)


def verify_shards(shards, manifest_reference):
    index = read(manifest_reference)
    index_sha = read(COMP / "monster_first518_split1018_sha_validated_computed_comparison_v2_20261019.json")
    if (index["total_verified_issuer_pairs"] != 1018 or index["shards_total"] != 8
            or index["shard_manifest_sha256"] != index_sha["shard_manifest_sha256"]):
        raise ValueError("MONSTER_AUDIT_UNTRUSTED_SHARD_INDEX")
    names = set()
    for i in range(8):
        folder = shards / f"shard_{i:02d}"
        manifest_path = folder / "manifest.json"
        if sha(manifest_path) != index["shard_manifest_sha256"][i]:
            raise ValueError("MONSTER_AUDIT_SHARD_MANIFEST_SHA_MISMATCH")
        doc = read(manifest_path)
        if (doc["shard"] != i or doc["shards_total"] != 8
                or doc["original_issuer_pairs"] != index["shard_pair_counts"][i]):
            raise ValueError("MONSTER_AUDIT_SHARD_IDENTITY_MISMATCH")
        expected = {"manifest.json"}
        for row in doc["rows"]:
            name = row["zip"]
            if name in names:
                raise ValueError("MONSTER_AUDIT_DUPLICATE_ISSUER_ZIP")
            names.add(name)
            z = folder / name
            c = folder / (name + ".CHECKSUM")
            expected.add(name)
            expected.add(name + ".CHECKSUM")
            if (sha(z) != row["original_zip_sha256"]
                    or sha(c) != row["original_publisher_checksum_bytes_sha256"]):
                raise ValueError("MONSTER_AUDIT_ORIGINAL_SOURCE_SHA_FAILED:" + name)
        actual = {f.name for f in folder.iterdir() if f.is_file()}
        if actual != expected:
            raise ValueError("MONSTER_AUDIT_SHARD_HAS_UNEXPECTED_SOURCE_FILES")
    if len(names) != 1018:
        raise ValueError("MONSTER_AUDIT_SHARD_INCOMPLETE")
    return index


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", type=Path, required=True)
    a = ap.parse_args()
    output = a.out_dir.expanduser().resolve()
    if output.exists() or output.is_symlink():
        raise ValueError("MONSTER_AUDIT_REFUSE_OVERWRITE_OUTPUT_DIRECTORY")
    output.mkdir(parents=True)
    shards = output / "shards"
    for i in range(8):
        fetch(RUN, f"monster-first518-issuer-original1018-shard-{i:02d}",
              shards / f"shard_{i:02d}")
    fetch(RUN, "monster-first518-original-shards-computed-source-proof-v2",
          output / "original_split_metadata")
    idx = list((output / "original_split_metadata").rglob("index.json"))
    if len(idx) != 1:
        raise ValueError("MONSTER_AUDIT_EXPECT_ONE_INDEX")
    index = verify_shards(shards, idx[0])
    unicode_folder = output / "unicode4"
    oct18_folder = output / "oct18"
    fetch(39213387756, "monster-frozen-spot511-unicode4-source-gap-official-publisher-originals", unicode_folder)
    fetch(39214007356, "monster-real-spot511-20261018-original-issuer-zip-and-checksum", oct18_folder)

    bridge_path = SCRIPTS / "monster_v4_forward_spot511_first518_fifo8_bridge.py"
    econ_path = SCRIPTS / "monster_v4_forward_spot511_first518_postsignal_economics.py"
    runner_args = [
        "--source-dir", str(shards), "--source-dir", str(unicode_folder),
        "--source-dir", str(oct18_folder)]
    new_bridge = output / "independently_replayed_bridge.json"
    new_econ = output / "independently_replayed_economics.json"
    subprocess.run([sys.executable, "-B", str(bridge_path), *runner_args,
                    "--operator-view", "--out", str(new_bridge)],
                   cwd=ROOT, check=True)
    subprocess.run([sys.executable, "-B", str(econ_path), *runner_args,
                    "--out", str(new_econ)], cwd=ROOT, check=True)
    reviewed = report(
        index, read(new_bridge), read(new_econ),
        read(COMP / "monster_forward_spot511_first518_official_minute_causal_fifo8_actual_v1.json"),
        read(COMP / "monster_forward_spot511_first518_8watch_8setup_fixed_horizons_actual_v1.json"),
        read(COMP / "monster_first518_real_operator_d0_d1_d2_no_buy_research_p2_fixed_v1.json"),
        run_input_commit=subprocess.check_output(["git", "rev-parse", "HEAD"],
                                                  cwd=ROOT, text=True).strip())
    reviewed["reviewer_local_exec_source"] = "EXECUTED_ON_LOCAL_MACHINE_NOT_GITHUB_AUTHOR_CI"
    reviewed["independent_reviewer_identity"] = "NOT_SET_BY_AUTOMATIC_SCRIPT"
    reviewed["local_original_1018_byte_manifests_validated"] = len(index["shard_manifest_sha256"])
    reviewed["local_bridge_sha256"] = sha(new_bridge)
    reviewed["local_economics_sha256"] = sha(new_econ)
    destination = output / "independent_raw_source_and_replay_actual_result.json"
    destination.write_text(json.dumps(reviewed, ensure_ascii=False, indent=2,
                                      sort_keys=True) + "\n")
    print("MONSTER_LOCAL_REVIEWER_RETRIEVED_ALL_1533_AND_REPLAYED_518",
          json.dumps({
              "original_issuer_1018_downloaded_from_small_shards": 1018,
              "unicode_4_and_oct18_511": 515,
              "actual_equality_checks": reviewed["computed_from_actual_JSON_field_comparisons"],
              "report_file": str(destination),
              "reviewer_must_independently_inspect_and_judge": True
          }, ensure_ascii=False, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
