#!/usr/bin/env python3
"""One-shot Stage165: exact original D1 features for the 27 frozen Fair8 first evaluations.

Only previously SHA-attested Stage162/Stage164 and February-2026 publisher
archives. Never reads live market prices, modifies model thresholds, or trades.
"""
import argparse
from collections import Counter
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import statistics
import tempfile

import monster_v4_shadow as production
import monster_v4_shared_spot_d0_d1_original_core as shared
import monster_v4_shared_445_official_source_shards as shards
import monster_v4_shared_445_one_db_from_shards as assembler

SCHEMA = "MONSTER_STAGE165_ORIGINAL_FROZEN27_D1_THREE_CONDITION_REAL_SOURCE_V1"
STAGE162_SHA = "c30c8b6467b0017b36efc33fadfa2c7853f29f9c7e32993249774269ba4e2ae2"
STAGE164_BLOB = "40aeb187320ea3efc3b8b6bd8a0a8ae1d4d10098"
D1_SOURCE_BLOB = "bc958b3d90a8a52afa51515cb53f7e5fafaffaaa"


def git_blob_sha1(raw):
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def source_inputs(stage162_file, stage164_file):
    raw = stage162_file.read_bytes()
    if hashlib.sha256(raw).hexdigest() != STAGE162_SHA:
        raise ValueError("STAGE165_STAGE162_FULL_SOURCE_SHA_DRIFT")
    older = stage164_file.read_bytes()
    if git_blob_sha1(older) != STAGE164_BLOB:
        raise ValueError("STAGE165_STAGE164_IMMUTABLE_GIT_BLOB_DRIFT")
    j, prior = json.loads(raw), json.loads(older)
    episodes = prior["candidate_episode_rows"]
    if (len(episodes) != 27
        or len({e["candidate_id"] for e in episodes}) != 27
        or len({e["symbol"] for e in episodes}) != 27
        or prior["gained_first_valid_d1"] != 27
        or prior["new_setup_count"] != 0
        or j["setup_event_id_baseline"] != j["setup_event_id_alternative"]
        or j["setup_event_id_baseline"] != 120
        or j["setup_new_ids"] != 0 or j["setup_lost_ids"] != 0
        or j["D0_watch_269_event_and_queue_identity_exact"] is not True):
        raise ValueError("STAGE165_STAGE164_EPISODE_OR_SETUPS_DRIFT")
    full = {r["id"]: r for r in j["candidate_outcomes"]}
    if len(full) != 269:
        raise ValueError("STAGE165_ORIGINAL_WATCH_DENOMINATOR_DRIFT")
    for e in episodes:
        q = full.get(e["candidate_id"])
        if q is None or any(e[k] != q[oldk] for k, oldk in [
                ("symbol", "symbol"),
                ("first_seen_ms", "first_seen_ms"),
                ("first_valid_evaluation_delay_minutes", "alternative_selected_slots")
                ] if k != "first_valid_evaluation_delay_minutes"):
            raise ValueError("STAGE165_EPISODE_ID_OR_SYMBOL_DRIFT")
        if q["baseline_first_evaluation_ms"] is not None or q["alternative_first_evaluation_ms"] is None:
            raise ValueError("STAGE165_NOT_GAINED_FIRST_EVAL")
        if ((q["alternative_first_evaluation_ms"] - q["first_seen_ms"]) // 60_000
                != e["first_valid_evaluation_delay_minutes"]):
            raise ValueError("STAGE165_FIRST_EVAL_DELAY_DRIFT")
    return j, prior


def classify_original_d1(candles, observed_ms):
    # Original frozen production logic is the final authority on SETUP.
    actual = production.evaluate_closed_5m(candles, observed_ms)
    last = candles[-6:]
    closes = [Decimal(str(c[4])) for c in last]
    quotes = [Decimal(str(c[7])) for c in last]
    positive_steps = sum(closes[i] > closes[i-1] for i in (3,4,5))
    qratio = statistics.median(quotes[3:])/statistics.median(quotes[:3])
    conditions = {
        "positive_steps_last3_at_least_2": positive_steps >= 2,
        "recent_vs_earlier_15m_quote_ratio_at_least_1p5": qratio >= Decimal("1.5"),
        "last_close_gte_prior15m_close": closes[-1] >= closes[2],
    }
    if (actual["positive_steps_last3"] != positive_steps
        or actual["recent_vs_earlier_15m_quote_ratio"] != round(float(qratio),4)
        or actual["setup_candidate"] is not all(conditions.values())):
        raise RuntimeError("STAGE165_DIAGNOSTIC_NOT_ORIGINAL_PRODUCTION_D1")
    return actual, str(qratio), conditions


def audit(stage162_file, stage164_file, source_dir):
    j, prior = source_inputs(stage162_file, stage164_file)
    if git_blob_sha1(Path(production.__file__).read_bytes()) != D1_SOURCE_BLOB:
        raise ValueError("STAGE165_FROZEN_PRODUCTION_D1_CODE_DRIFT")
    episodes = prior["candidate_episode_rows"]
    by_id = {e["candidate_id"]: e for e in episodes}
    target = {e["symbol"] for e in episodes}
    slots = [s for s in j["selected_slot_trace"] if s["id"] in by_id]
    if (len(slots) != 44
        or {s["id"] for s in slots} != set(by_id)
        or len({s["id"] for s in slots if s["valid_5m_evaluation_marker_advanced"]}) != 27):
        raise ValueError("STAGE165_ACTUAL_SELECTED_SLOT_TRACE_DRIFT")
    advanced = {}
    for s in slots:
        e = by_id[s["id"]]
        if s["symbol"] != e["symbol"] or s["first_seen_ms"] != e["first_seen_ms"]:
            raise ValueError("STAGE165_SLOT_TO_EPISODE_DRIFT")
        if s["valid_5m_evaluation_marker_advanced"]:
            if s["id"] in advanced or s["tick_ms"] != (
                    e["first_seen_ms"] + 60_000 * e["first_valid_evaluation_delay_minutes"]):
                raise ValueError("STAGE165_FIRST_EVAL_EVENT_TIME_OR_DUPLICATE")
            if s["tick_ms"] > s["deadline_ms"]:
                raise ValueError("STAGE165_PAST_DEADLINE_EVAL")
            advanced[s["id"]] = s
    if len(advanced) != 27:
        raise ValueError("STAGE165_EVALUATED_27_EVENT_COVERAGE_DRIFT")
    # Existing Stage162 source collector already downloaded 28 vetted ZIPs.
    archives = assembler.verified_shard_paths(source_dir)
    if len(archives) != 28 or sum(len(shards.members(i)) for i,_,_ in archives) != 445:
        raise ValueError("STAGE165_SHARD_28_FROZEN_ORIGINAL_445_DRIFT")
    rows = []
    source_count = 0
    with tempfile.TemporaryDirectory(prefix="monster_stage165_d1_") as folder:
        with shared.setup_cache(Path(folder)/"read_only_history_derivative.sqlite") as db:
            for shard_id, path, proof in archives:
                members = set(shards.members(shard_id))
                if not members.intersection(target):
                    continue
                for symbol, bars, receipts, meta in shards.read_archive(
                        path, proof=proof, expected_shard=shard_id):
                    if symbol not in target:
                        continue
                    if meta.get("source_origin_verified_at_collection") is not True:
                        raise ValueError("STAGE165_SOURCE_COLLECTION_ATTESTATION_MISSING")
                    attested = [{"date": r["day"], "sha256": r["sha256"],
                                 "verified_published_sha256": True,
                                 "verified_by": "PREVIOUS_OFFICIAL_SHARD_ARTIFACT"}
                                for r in receipts]
                    prepared = shared.prepare_symbol(db, symbol, shards.DAY, bars, attested)
                    if prepared["closed_5m"] != 2592 or prepared["poll_rows"] != 3360:
                        raise ValueError("STAGE165_ORIGINAL_MINUTE_SOURCE_PREPARATION_DRIFT")
                    source_count += 1
            if source_count != 27:
                raise ValueError("STAGE165_SOURCE_SYMBOL_27_INCOMPLETE")
            for e in sorted(episodes, key=lambda x: x["candidate_id"]):
                slot = advanced[e["candidate_id"]]
                candles = shared.verified_closed_5m_for_original_d1(
                    db, (e["symbol"],), "spot", e["symbol"], slot["tick_ms"])
                actual, exact_ratio, conditions = classify_original_d1(
                    candles, slot["tick_ms"])
                # At the original 15m deadline a genuine negative D1
                # evaluation closes the queue with EVALUATED/NO_SETUP;
                # earlier negative evaluations stay PENDING/NO_SETUP_YET.
                terminal = slot["tick_ms"] >= slot["deadline_ms"]
                expected_status = "EVALUATED" if terminal else "PENDING"
                expected_error = "NO_SETUP_WITHIN_WINDOW" if terminal else "NO_SETUP_YET"
                if (actual["setup_candidate"] is not False
                    or slot["status_after"] != expected_status
                    or slot["last_error_after"] != expected_error
                    or actual["bar_last_open_ms"] != slot["last_evaluated_bar_ms_after"]):
                    raise ValueError("STAGE165_REAL_EVALUATION_OR_NO_SETUP_DRIFT")
                failed = sorted(k for k,v in conditions.items() if not v)
                if not failed:
                    raise ValueError("STAGE165_EMPTY_REASONS_FOR_NO_SETUP")
                rows.append({
                    "candidate_id": e["candidate_id"],
                    "symbol": e["symbol"],
                    "cohort": e["cohort"],
                    "original_watch_ms": e["first_seen_ms"],
                    "evaluation_tick_ms": slot["tick_ms"],
                    "original_deadline_ms": slot["deadline_ms"],
                    "actual_5m_bar_last_open_ms": actual["bar_last_open_ms"],
                    "first_valid_d1_delay_minutes": e["first_valid_evaluation_delay_minutes"],
                    "positive_steps_last3": actual["positive_steps_last3"],
                    "exact_quote_ratio_decimal": exact_ratio,
                    "original_quote_ratio_display_4dp": actual["recent_vs_earlier_15m_quote_ratio"],
                    "last_close": str(candles[-1][4]),
                    "prior15m_close": str(candles[-4][4]),
                    "feature_conditions": conditions,
                    "failed_feature_conditions": failed,
                    "original_setup_candidate": False,
                    "research_only": True
                })
    freq = Counter(key for r in rows for key in r["failed_feature_conditions"])
    combination = Counter("|".join(r["failed_feature_conditions"]) for r in rows)
    if len(rows) != 27:
        raise ValueError("STAGE165_FEATURE_ROW_COUNT_DRIFT")
    return {
        "schema": SCHEMA,
        "original_stage162_full_sha256": STAGE162_SHA,
        "original_stage164_git_blob": STAGE164_BLOB,
        "frozen_production_d1_blob": D1_SOURCE_BLOB,
        "original_758_attempted": 758,
        "source_complete_445": 445,
        "source_censored_313": 313,
        "sample_fair8_new_d1": len(rows),
        "actually_advanced_5m_candle_evaluation_events": len(rows),
        "actual_setup_from_these_events": 0,
        "failed_condition_frequency_overlap_allowed": dict(sorted(freq.items())),
        "mutually_exclusive_failed_condition_combinations": dict(sorted(combination.items())),
        "real_source_per_candidate": rows,
        "not_all_758": True,
        "not_independent_OOS": True,
        "historical_tradeable_pit": "UNVERIFIED",
        "net_realizable_profit": "UNVERIFIED",
        "strategy_threshold_changed": False,
        "G4": "UNKNOWN", "G6": "NO_GO", "NO_MERGE": True,
        "NO_DEPLOY": True, "NO_GMAIL": True, "NO_TRADE": True
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--stage162-full", type=Path, required=True)
    p.add_argument("--stage164-git-evidence", type=Path, required=True)
    p.add_argument("--source-dir", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    x = p.parse_args()
    if x.out.exists() or x.out.is_symlink():
        raise ValueError("STAGE165_OUTPUT_ALREADY_EXISTS")
    result = audit(x.stage162_full, x.stage164_git_evidence, x.source_dir)
    x.out.parent.mkdir(parents=True, exist_ok=True)
    with x.out.open("x", encoding="utf-8") as file:
        json.dump(result, file, sort_keys=True, indent=2, ensure_ascii=False)
        file.write("\n")
    print("MONSTER_STAGE165_ACTUAL_FROZEN27_D1_FAIL_CONDITION_DETAILS",
          json.dumps({
              "rows": len(result["real_source_per_candidate"]),
              "failing_conditions": result["failed_condition_frequency_overlap_allowed"],
              "combos": result["mutually_exclusive_failed_condition_combinations"],
              "G6": result["G6"]}, sort_keys=True))


if __name__ == "__main__":
    main()
