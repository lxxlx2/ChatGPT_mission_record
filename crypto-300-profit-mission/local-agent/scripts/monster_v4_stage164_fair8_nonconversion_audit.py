#!/usr/bin/env python3
"""Audit the 27 added D1 first evaluations from immutable Stage162 real-source A/B.

This is offline source analysis. It does not collect data, change the model,
reconstruct historical trade fills or recommend buying any token.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

SOURCE_SHA256 = "c30c8b6467b0017b36efc33fadfa2c7853f29f9c7e32993249774269ba4e2ae2"
SCHEMA = "MONSTER_STAGE164_FAIR8_NEW27_NONCONVERSION_SOURCE_BOUNDED_V1"


def make_report(j, *, strict=True):
    candidates = j["candidate_outcomes"]
    queues = j["raw_alternative_queue"]
    if len({r["id"] for r in candidates}) != len(candidates):
        raise ValueError("STAGE164_DUPLICATE_CANDIDATE_ID")
    if len({q["id"] for q in queues}) != len(queues):
        raise ValueError("STAGE164_DUPLICATE_QUEUE_ID")
    by_id = {q["id"]: q for q in queues}
    if set(by_id) != {r["id"] for r in candidates}:
        raise ValueError("STAGE164_QUEUE_TO_CANDIDATE_MISMATCH")
    if j["setup_new_ids"] != 0 or j["setup_lost_ids"] != 0:
        raise ValueError("STAGE164_UNEXPECTED_SETUP_ID_DRIFT")
    if j["setup_event_id_baseline"] != j["setup_event_id_alternative"]:
        raise ValueError("STAGE164_TOTAL_SETUP_DRIFT")
    gained = [r for r in candidates
              if r["baseline_first_evaluation_ms"] is None
              and r["alternative_first_evaluation_ms"] is not None]
    lost = [r for r in candidates
            if r["baseline_first_evaluation_ms"] is not None
            and r["alternative_first_evaluation_ms"] is None]
    timing = Counter()
    episodes = []
    for r in gained:
        q = by_id[r["id"]]
        if ((q["symbol"], q["first_seen_ms"], q["deadline_ms"], q["status"])
                != (r["symbol"], r["first_seen_ms"], r["deadline_ms"],
                    r["alternative_status"])):
            raise ValueError("STAGE164_CANDIDATE_SOURCE_JOIN_DRIFT")
        delay = r["alternative_first_evaluation_ms"] - r["first_seen_ms"]
        if delay < 0 or delay > r["deadline_ms"] - r["first_seen_ms"]:
            raise ValueError("STAGE164_NOT_IN_WATCH_DEADLINE")
        if delay % 60_000:
            raise ValueError("STAGE164_NONMINUTE_EVAL_DELAY")
        timing[str(delay // 60_000)] += 1
        episodes.append({
            "candidate_id": r["id"],
            "symbol": r["symbol"],
            "cohort": r["cohort"],
            "first_seen_ms": r["first_seen_ms"],
            "baseline_status_final": r["baseline_status"],
            "fair8_status_final": q["status"],
            "first_valid_evaluation_delay_minutes": delay // 60_000,
            "fair8_selected_slot_count": r["alternative_selected_slots"],
            "final_queue_d1_last_error": q["last_error"],
            "setup_from_fair8_for_candidate": False
        })
    episodes.sort(key=lambda x: x["candidate_id"])
    def counts(key):
        return dict(sorted(Counter(r[key] for r in episodes).items()))
    cohort = counts("cohort")
    status = counts("fair8_status_final")
    final_error = counts("final_queue_d1_last_error")
    old_status = counts("baseline_status_final")
    slots = counts("fair8_selected_slot_count")
    if strict and not (
        j.get("schema") == "MONSTER445_STAGE162_FIRST_VALID_5M_ONCE_PRIORITY_8_RESEARCH_V1"
        and len(candidates) == len(queues) == 269
        and len(gained) == 27 and len(lost) == 0
        and sum(r["baseline_first_evaluation_ms"] is not None for r in candidates) == 172
        and sum(r["alternative_first_evaluation_ms"] is not None for r in candidates) == 199
        and cohort == {"OTHER_171": 2, "PEAK_98": 25}
        and status == {"EVALUATED": 27}
        and old_status == {"LATE": 27}
        and final_error == {"NO_SETUP_WITHIN_WINDOW": 27}
        and timing == {"6": 1, "9": 8, "12": 8, "15": 10}
        and slots == {1: 10, 2: 17}
        and j["setup_event_id_baseline"] == 120
        and j["setup_retained_ids"] == 120
        and not j["setup_new_event_ids"] and not j["setup_lost_event_ids"]
        and j["G4"] == "UNKNOWN" and j["G6"] == "NO_GO"
        and j["not_independent_OOS"] is True
    ):
        raise ValueError("STAGE164_FROZEN_ORIGINAL_445_AB_SEMANTIC_DRIFT")
    return {
        "schema": SCHEMA,
        "source_full_stage162_sha256": SOURCE_SHA256 if strict else "TEST_FIXTURE",
        "sample_population": "HISTORICAL_445_OF_ORIGINAL_758_313_CENSORED_NOT_PIT",
        "total_watch_episodes": len(candidates),
        "baseline_valid_first_d1": sum(r["baseline_first_evaluation_ms"] is not None for r in candidates),
        "fair8_valid_first_d1": sum(r["alternative_first_evaluation_ms"] is not None for r in candidates),
        "gained_first_valid_d1": len(gained),
        "lost_first_valid_d1": len(lost),
        "new_setup_count": j["setup_new_ids"],
        "lost_setup_count": j["setup_lost_ids"],
        "retained_original_setup_count": j["setup_retained_ids"],
        "gained_cohort_count": cohort,
        "gained_baseline_final_status": old_status,
        "gained_fair8_final_status": status,
        "gained_final_queue_error": final_error,
        "gained_first_valid_delay_minutes": dict(sorted(timing.items(), key=lambda pair: int(pair[0]))),
        "gained_selected_slot_count": dict(sorted(slots.items())),
        "candidate_episode_rows": episodes,
        "conclusion_from_final_episode_source":
            "ALL_27_GAINED_D1_EVALUATED_AND_FINAL_NO_SETUP_WITHIN_WINDOW",
        "specific_5m_feature_threshold_reasons": "UNVERIFIED_NOT_IN_STAGE162_CANDIDATE_TRACE",
        "historical_pit_listing": "UNVERIFIED",
        "real_executable_positive_net_profit": "UNVERIFIED",
        "not_independent_OOS": True,
        "not_a_buy_recommendation": True,
        "G4": "UNKNOWN",
        "G6": "NO_GO",
        "NO_MERGE": True,
        "NO_DEPLOY": True,
        "NO_GMAIL": True,
        "NO_TRADE": True
    }


def main():
    parser = argparse.ArgumentParser(description="One-shot original Stage162 Fair8 nonconversion diagnostic")
    parser.add_argument("--stage162-full", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    raw = args.stage162_full.read_bytes()
    if hashlib.sha256(raw).hexdigest() != SOURCE_SHA256:
        raise ValueError("STAGE164_SOURCE_FULL_ARTIFACT_SHA256_MISMATCH")
    if args.out.exists() or args.out.is_symlink():
        raise ValueError("STAGE164_REFUSE_EVIDENCE_OVERWRITE")
    result = make_report(json.loads(raw))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x", encoding="utf-8") as fd:
        json.dump(result, fd, ensure_ascii=False, indent=2, sort_keys=True)
        fd.write("\n")
    print("MONSTER_STAGE164_ORIGINAL_445_FAIR8_NEW27_SOURCE_BOUNDED", json.dumps({
        k: result[k] for k in
        ("gained_first_valid_d1", "gained_cohort_count", "gained_final_queue_error",
         "gained_first_valid_delay_minutes", "new_setup_count", "G6")}, sort_keys=True))


if __name__ == "__main__":
    main()
