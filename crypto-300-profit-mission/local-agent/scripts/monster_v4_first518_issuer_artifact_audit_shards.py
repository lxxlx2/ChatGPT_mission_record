#!/usr/bin/env python3
"""Repackage EXACT existing issuer ZIP/CHECKSUM bytes for independent small downloads.

No network access, no redownloading from Binance, no altered source archives.
Eight disjoint small artifacts restore the 1018 issuer pairs from original
Oct16–17 run. Their issuer hashes are verified against frozen Git receipts.
"""
from __future__ import annotations

import argparse
from datetime import date
import hashlib
import json
from pathlib import Path
import shutil

import monster_v4_forward_spot511_first518_fifo8_bridge as bridge
import monster_v4_stage166_spot511_official_1m_intake as admitted

SHARDS = 8
COUNT = 1018
DAYS = bridge.DAY_UTC[:2]
SKIPPED = {"币安人生USDT", "牛来USDT"}
SCHEMA = "MONSTER_FIRST518_OCT16_17_ORIGINAL_1018_SPLIT_FOR_INDEPENDENT_AUDIT_V1"


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build(original_dir: Path, destination: Path):
    if destination.exists():
        raise ValueError("MONSTER_SPLIT_OUTPUT_ALREADY_EXISTS")
    roster = admitted.frozen_roster()
    if len(roster) != 511:
        raise ValueError("MONSTER_SPLIT_T0_511_DRIFT")
    receipts = bridge.evidence_receipts(roster)
    expected = sorted(
        (f"{symbol}-1m-{day}.zip", symbol, day)
        for symbol in roster if symbol not in SKIPPED for day in DAYS
    )
    if len(expected) != COUNT:
        raise ValueError("MONSTER_SPLIT_ORIGINAL_VERIFIED_1018_DRIFT")
    source_zips, source_checksums = bridge.source_files([original_dir])
    expected_names = {n for n, _, _ in expected}
    if set(source_zips) != expected_names or set(source_checksums) != {
            name + ".CHECKSUM" for name in expected_names}:
        raise ValueError("MONSTER_SPLIT_INPUT_SET_NOT_EXACTLY_ORIGINAL_1018")
    destination.mkdir(parents=True)
    shards = [[] for _ in range(SHARDS)]
    for index, (name, symbol, day) in enumerate(expected):
        original = source_zips[name]
        original_checksum = source_checksums[name + ".CHECKSUM"]
        actual = admitted.validate_daily_zip(
            original, original_checksum, symbol, date.fromisoformat(day))
        expected_zip_sha, expected_checksum_sha = receipts[(symbol, day)]
        zip_sha = digest(original)
        check_sha = digest(original_checksum)
        if (actual["closed_one_minute_rows"] != 1440
                or actual["spot_timestamp_units"] != "MICROSECONDS"
                or actual["zip_sha256"] != zip_sha
                or zip_sha != expected_zip_sha
                or check_sha != expected_checksum_sha):
            raise ValueError("MONSTER_SPLIT_ORIGINAL_ISSUER_SHA_DRIFT:" + name)
        shard_index = index * SHARDS // COUNT
        shard_name = f"shard_{shard_index:02d}"
        shard_dir = destination / shard_name
        shard_dir.mkdir(exist_ok=True)
        target_zip = shard_dir / name
        target_checksum = shard_dir / (name + ".CHECKSUM")
        shutil.copyfile(original, target_zip)
        shutil.copyfile(original_checksum, target_checksum)
        if digest(target_zip) != zip_sha or digest(target_checksum) != check_sha:
            raise ValueError("MONSTER_SPLIT_COPY_NOT_BYTE_IDENTICAL")
        shards[shard_index].append({
            "symbol": symbol,
            "date_utc": day,
            "zip": name,
            "original_zip_sha256": zip_sha,
            "original_publisher_checksum_bytes_sha256": check_sha,
            "zip_size_bytes": target_zip.stat().st_size,
            "checksum_size_bytes": target_checksum.stat().st_size,
            "csv_rows": 1440,
        })
    if sum(map(len, shards)) != COUNT:
        raise ValueError("MONSTER_SPLIT_FINAL_POPULATION_DRIFT")
    if len({row["zip"] for rows in shards for row in rows}) != COUNT:
        raise ValueError("MONSTER_SPLIT_NON_DISJOINT")
    all_shard_manifest_sha = []
    for index, rows in enumerate(shards):
        if not 120 <= len(rows) <= 130:
            raise ValueError("MONSTER_SPLIT_SHARD_SIZE_BAD")
        folder = destination / f"shard_{index:02d}"
        manifest = {
            "schema": SCHEMA,
            "source_original_run_id": 39212800265,
            "source_original_artifact_id": 12167818438,
            "original_issuer_pairs": len(rows),
            "original_issuer_checksum_verified": len(rows),
            "all_original_source_bytes_unchanged": True,
            "not_an_independent_other_AI_review": True,
            "new_market_requests": 0,
            "shard": index, "shards_total": SHARDS,
            "rows": rows,
            "G0": "PARTIAL", "G4": "UNKNOWN", "G6": "NO_GO",
            "NO_MERGE": True, "NO_DEPLOY": True,
            "NO_GMAIL": True, "NO_TRADE": True,
        }
        mp = folder / "manifest.json"
        mp.write_text(json.dumps(manifest, sort_keys=True, indent=2,
                                  ensure_ascii=False) + "\n", encoding="utf-8")
        all_shard_manifest_sha.append(digest(mp))
    index_record = {
        "schema": SCHEMA,
        "old_run": 39212800265,
        "old_artifact": 12167818438,
        "old_issuer_pairs_present": COUNT,
        "unicode_four_pairs_live_in_original_separate_artifact": 4,
        "shards_total": SHARDS,
        "each_shard_has_original_issuer_zip_and_checksum_bytes": True,
        "shard_pair_counts": [len(x) for x in shards],
        "shard_manifest_sha256": all_shard_manifest_sha,
        "total_verified_issuer_pairs": COUNT,
        "independent_Codex_download_replay": "NOT_DONE",
        "do_not_count_this_as_live_trading_or_independent_review": True,
    }
    (destination / "index.json").write_text(
        json.dumps(index_record, sort_keys=True, indent=2) + "\n")
    return index_record


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--original-dir", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    result = build(args.original_dir, args.out_dir)
    print("MONSTER_FIRST518_AUDIT_EIGHT_SMALL_ORIGINAL_BYTE_SHARDS",
          json.dumps(result, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
