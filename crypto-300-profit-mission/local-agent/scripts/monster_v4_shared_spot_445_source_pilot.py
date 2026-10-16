#!/usr/bin/env python3
"""Frozen February-2026 445 eligible Spot universe: original-source shared D0 pilot.

One predeclared alphabetical slice of the 445 Stage26-SHA-verified source-complete
roster; not signal/winner picked. Historical exposed data, NOT full 758 replay,
not whole 445 replay, not OOS, no production/mail/trade/deployment.
"""
from __future__ import annotations

import argparse
from datetime import date
import hashlib
import json
from pathlib import Path
import tempfile

import monster_v4_shared_spot_d0_d1_original_core as shared
import monster_v4_stage26_continuous168h as original

SCHEMA = "MONSTER_SHARED_SPOT_445_SOURCE_COMPLETE_ORIGINAL_D0_D1_PILOT_V1"
DAY = date(2026, 2, 4)
ELIGIBLE_COUNT = 445
CENSORED_COUNT = 313
PILOT_SIZE = 8
ENGINE_GIT_BLOB = "3a9e4bbd75ff4f5ef6cd0bfe87895d932c95892c"


def frozen_selection(size=PILOT_SIZE):
    if type(size) is not int or not (1 <= size <= 16):
        raise ValueError("SHARED_445_PILOT_SIZE_OUT_OF_PREREG_RANGE")
    if shared.production_blob() != shared.ORIGINAL_SHADOW_BLOB:
        raise ValueError("SHARED_445_PRODUCTION_MODEL_DRIFT")
    full, day_map = shared.original_source_freeze()
    frozen = day_map[DAY.isoformat()]
    eligible = tuple(sorted(frozen["complete_symbols"]))
    if (len(full) != 758 or len(eligible) != ELIGIBLE_COUNT or
            len(full) - len(eligible) != CENSORED_COUNT):
        raise ValueError("SHARED_445_FROZEN_758_DENOMINATOR_CHANGED")
    if not set(eligible).issubset(full) or len(set(eligible)) != len(eligible):
        raise ValueError("SHARED_445_ORIGINAL_ROSTER_IDENTITY_DRIFT")
    return eligible[:size]


def _sha_snapshot(symbol, receipts):
    return {"symbol": symbol, "publisher_daily_sha": [
        {"day": r["date"], "sha256": r["sha256"]}
        for r in receipts]}


def run_pilot(size=PILOT_SIZE, source_reader=None, legacy_replayer=None,
              shared_replayer=None):
    # Injections are exclusively for synthetic tests; they cannot claim
    # trusted official downloaded source. The live CI uses both original
    # source and original per-symbol runner unchanged.
    official = (source_reader is None)
    reader = original.read_complete_216h if official else source_reader
    legacy = original.scan_continuous if legacy_replayer is None else legacy_replayer
    replay = shared.run_shared if shared_replayer is None else shared_replayer
    selected = frozen_selection(size)
    prereg_size = len(selected)
    if (legacy_replayer is not None or shared_replayer is not None):
        official = False
    with tempfile.TemporaryDirectory(prefix="monster_445_shared_pilot_") as td:
        with shared.setup_cache(Path(td) / "one_source_cache.sqlite") as db:
            legacy_rows = []
            archives = []
            for symbol in selected:
                bars, receipt = reader(symbol, DAY)
                # The original default reader has just actually read ten
                # publisher-verified ZIP/CHECKSUM archives and checked UTC.
                sha_status = shared.check_secondary_daily_sha_pins(symbol, receipt)
                attested = [dict(r,
                    verified_published_sha256=True,
                    verified_by=("STAGE26_OFFICIAL_CHECKSUM_READER" if official
                                 else "SYNTHETIC_TEST_ONLY"))
                    for r in receipt]
                preparation = shared.prepare_symbol(db, symbol, DAY, bars, attested)
                legacy_case = legacy(symbol, DAY, bars)
                archives.append({**_sha_snapshot(symbol, receipt),
                                 "archived_prior_sha_match": sha_status,
                                 "poll_rows": preparation["poll_rows"],
                                 "closed_5m": preparation["closed_5m"]})
                legacy_rows.append({"symbol": symbol,
                                    "per_symbol_original_watch_utcs":
                                        legacy_case["watch_utcs"],
                                    "per_symbol_original_setups":
                                        legacy_case["setups"]})
            result = replay(db, DAY, selected,
                         market_coverage_label=(
                           "OFFICIAL_VERIFIED_SUBSET_ONLY" if official
                           else "SYNTHETIC_TEST_ONLY"))
    if result.get("actually_complete_symbols") != prereg_size:
        raise ValueError("SHARED_445_PILOT_ENGINE_ROSTER_SIZE_CHANGED")
    # Original per-symbol D0 comparison holds only on same actual historical
    # minutes, not on old Stage28 injected WATCH or a winner-only list.
    shared_watch = {s:[] for s in selected}
    for item in result["events"]:
        if item["event_type"] == "WATCH_EARLY":
            if item["symbol"] not in shared_watch:
                raise ValueError("SHARED_445_UNREGISTERED_WATCH_SYMBOL")
            shared_watch[item["symbol"]].append(item["observed_ms"])
    first_mismatches = []
    legacy_watches=0
    for r in legacy_rows:
        expected = [original.replay.parse_ms(t)
                    for t in r["per_symbol_original_watch_utcs"]]
        got = sorted(shared_watch[r["symbol"]])
        legacy_watches += len(expected)
        if sorted(expected) != got:
            first_mismatches.append({"symbol":r["symbol"],
                      "old_count":len(expected),"shared_count":len(got)})
    if first_mismatches:
        raise RuntimeError("SHARED_445_REAL_ORIGINAL_D0_WATCH_CLOCK_DRIFT")
    if result["source_origin_verified"]:
        raise ValueError("SHARED_445_CACHE_SELF_ATTESTED_SOURCE_BUG")
    inventory = shared.original_758_coverage(DAY, selected,
                                              source_attested=official)
    expected = {"source_complete_original_stage26":445,
                "source_missing_or_incomplete_original_stage26":313,
                "replayed_verifiable_subset":prereg_size,
                "source_complete_but_not_replayed":445-prereg_size}
    if any(inventory[k] != v for k,v in expected.items()):
        raise ValueError("SHARED_445_CENSORED_DENOMINATOR_WRONG")
    result["original_758_coverage"]=inventory
    result["source_origin_verified"]=official
    result["source_attestation"]=(
        "STAGE26_ACTUAL_OFFICIAL_PUBLISHER_ZIP_CHECKSUM_PER_SYMBOL_AT_RUN_TIME"
        if official else "SYNTHETIC_INJECTED_NOT_OFFICIAL")
    result["market_coverage"]=(
        "OFFICIAL_VERIFIED_445_SOURCE_COMPLETE_PILOT_ONLY"
        if official else "SYNTHETIC_TEST_ONLY")
    result["source"]=(
        "OFFICIAL_SPOT_1M_HISTORICAL_216H_PREFIX_CONTEXT_PILOT_ONLY"
        if official else "SYNTHETIC_FIXTURE_ONLY")
    result["schema"]=SCHEMA
    result["preregistered_selection"]="FIRST_N_ALPHA_OF_ORIGINAL_445_COMPLETE_NO_KNOWN_WINNER_SELECTION"
    result["original_source_complete_445_pilot_not_complete"] = True
    result["original_source_complete_445_subset_total"] = 445
    result["pilot_selected"] = list(selected)
    result["publisher_proof"] = archives
    result["old_individual_D0_same_source"] = legacy_rows
    result["matched_D0_watch_exact_for_all_pilot_symbols"] = True
    result["original_per_symbol_watch_total"]=legacy_watches
    result["not_full_445_shared_replay"] = True
    result["not_full_758_shared_replay"] = True
    result["not_independent_out_of_sample"] = True
    result["not_market_listing_point_in_time"] = True
    return result


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--size",type=int,default=PILOT_SIZE)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    if args.out.exists() or args.out.is_symlink():
        raise ValueError("SHARED_445_PILOT_OUTPUT_EXISTS")
    report=run_pilot(args.size)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    with args.out.open("x",encoding="utf-8") as f:
        f.write(json.dumps(report,sort_keys=True,ensure_ascii=False,indent=2)+"\n")
    print("MONSTER_SHARED_SPOT_445_REAL_SOURCE_PILOT "+
          json.dumps({"symbols":report["pilot_selected"],
                      "shared_polls":report["execution_counts"]["polls"],
                      "legacy_watches":report["original_per_symbol_watch_total"],
                      "shared_event_counts":report["event_type_counts"],
                      "D1":report["queue_status_counts"],
                      "coverage_denominator":758,
                      "historical_censored":313,
                      "full_445":False},sort_keys=True))


if __name__=="__main__":
    main()
