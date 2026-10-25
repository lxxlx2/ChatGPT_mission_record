"""Replay the 53 pinned original WATCHs in the existing ADR-005 SQLite engine.

Offline only. Input original paired JSON must match its exact SHA256, and each
needed issuer ZIP must pass the existing Stage166 CHECKSUM + 1440-row validator.
All comparison rows are an *exposed October* diagnostic, never OOS or live PIT.
This file performs no download, network access, trading, scheduling, or mailing.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from monster_v4_d1_rbtc15_episode_research import (
    admit_original_watch, create_ledger, poll_episodes, summary,
    _negative_fully_reviewed_through_deadline,
)
from monster_v4_spot511_d0_d1_tape import VerifiedClosedMinuteTape
from monster_v4_spot511_verified_watch_tape import (
    EXPECTED_WATCH_COUNT, PINNED_PAIRED_REPORT_SHA256,
    load_pinned_original_watch_tape, watches_at_tick,
)
import monster_v4_spot511_closed_minute_feed as d0
import monster_v4_shadow as original

TICK_MS = 180_000
FIVE_MS = 300_000
EXPECTED_REQUIRED_SOURCE_DAYS = 57
SCHEMA = "MONSTER_ADR005_REAL53_ORIGINAL_SQLITE_OFFLINE_REPLAY_V1"
PINNED_EXPLORATORY_REFERENCE_GIT_BLOB = "4bb360a376223da1ba594c320f31ceccc335202a"


def required_source_days(identity_rows):
    """Conservative closed 5m source-day set over each original WATCH deadline."""
    if not isinstance(identity_rows, tuple) or len(identity_rows) != EXPECTED_WATCH_COUNT:
        raise ValueError("PINNED_53_IDENTITY_ROWS_REQUIRED")
    result = set()
    for symbol, observed_ms, _ in identity_rows:
        if type(observed_ms) is not int or observed_ms % TICK_MS:
            raise ValueError("WATCH_CLOCK_DRIFT")
        for tick in range(observed_ms, observed_ms + original.QUEUE_DEADLINE_MS + 1, TICK_MS):
            right = (tick // FIVE_MS) * FIVE_MS
            for sym in (symbol, "BTCUSDT"):
                first_bar_ms = right - 6 * FIVE_MS
                last_bar_ms = right - 1
                for day_ms in (first_bar_ms, last_bar_ms):
                    day = datetime.fromtimestamp(day_ms / 1000, timezone.utc).date().isoformat()
                    result.add((sym, day))
    return tuple(sorted(result))


def load_pinned_exploration(path):
    """Exact immutable repo Git blob; exploratory rows cannot self-certify."""
    source = Path(path)
    if not source.is_file() or source.is_symlink():
        raise ValueError("PINNED_EXPLORATORY_REFERENCE_FILE_REQUIRED")
    raw = source.read_bytes()
    # Git blob SHA-1 hashes the header as well as raw file bytes.
    header = b"blob " + str(len(raw)).encode("ascii") + b"\0"
    if hashlib.sha1(header + raw).hexdigest() != PINNED_EXPLORATORY_REFERENCE_GIT_BLOB:
        raise ValueError("EXPLORATORY_REFERENCE_GIT_BLOB_DRIFT")
    try:
        return json.loads(raw)
    except (ValueError, UnicodeError) as exc:
        raise ValueError("EXPLORATORY_REFERENCE_JSON_INVALID") from exc


def compare_exposed_exploration(ledger, exploration, *, allow_semantic_deadline_repair=False):
    """Compare event IDs/status/clocks; cannot certify source or execution."""
    reference = exploration.get("original_watch_linked_research_episode_rows")
    if (exploration.get("source_original_core_sha256") != PINNED_PAIRED_REPORT_SHA256
            or not isinstance(reference, list) or len(reference) != EXPECTED_WATCH_COUNT):
        raise ValueError("EXPLORATION_SOURCE_IDENTITY_INVALID")
    expected = {}
    for x in reference:
        eid = x.get("original_watch_event_id")
        if not isinstance(eid, str) or eid in expected:
            raise ValueError("EXPLORATION_DUPLICATE_OR_INVALID_EVENT")
        expected[eid] = x
    rows = ledger["rows"]
    actual = {r["watch_event_id"]: r for r in rows}
    if len(actual) != EXPECTED_WATCH_COUNT or set(actual) != set(expected):
        raise ValueError("ORIGINAL_WATCH_TO_RESEARCH_LEDGER_MEMBERSHIP_DRIFT")
    mismatches = []
    corrected_deadline_ids = []
    for eid, x in expected.items():
        a = actual[eid]
        status_is_approved_repair = (
            allow_semantic_deadline_repair
            and x.get("status") == "LATE_UNSCORED"
            and a["status"] == "NO_SETUP"
            and a.get("last_reviewed_open_ms") is not None
            and a.get("deadline_ms") is not None
            and _negative_fully_reviewed_through_deadline(a)
            and a["source_censored_count"] == 0
        )
        if status_is_approved_repair:
            corrected_deadline_ids.append(eid)
        checked = {
            "symbol": (a["symbol"], x.get("symbol")),
            "watch_ms": (a["first_seen_ms"], x.get("original_watch_observed_ms")),
            "status": (a["status"], a["status"] if status_is_approved_repair else x.get("status")),
            "censored_checks": (
                a["source_censored_count"], x.get("source_censored_evaluations")),
        }
        if x.get("status") == "RESEARCH_SETUP":
            checked["setup_ms"] = (a["research_observed_ms"], x.get("research_terminal_ms"))
        for field, (got, want) in checked.items():
            if got != want:
                mismatches.append({
                    "event_id": eid, "field": field, "actual_sqlite": got,
                    "exploratory_reference": want,
                })
    return {
        "status": ("DIFFERENCE_FAIL_CLOSED" if mismatches else
                   "SEMANTIC_DEADLINE_REPAIR_MATCH" if corrected_deadline_ids else "MATCH"),
        "explicit_late_to_no_setup_corrected_event_ids": sorted(corrected_deadline_ids),
        "legacy_reference_statuses_were_not_rewritten": True,
        "terminal_time_comparison": "NOT_AVAILABLE_IN_LEGACY_SQLITE",
        "original_watch_rows": len(actual),
        "mismatches": mismatches,
        "reference_is_previously_exposed_not_forward_validation": True,
    }


def replay(*, original_paired_json, publisher_dir, ledger_path, comparison_path,
           asof_utc):
    """Exact repository engine: admit at true tick, then poll original SQLite."""
    if asof_utc.tzinfo is None or asof_utc.utcoffset() is None:
        raise ValueError("AWARE_SOURCE_ASOF_REQUIRED")
    if asof_utc.astimezone(timezone.utc) < datetime(
            2026, 10, 25, tzinfo=timezone.utc):
        raise ValueError("PUBLISHER_DAY_2026_10_24_NOT_YET_CLOSED")
    reference = load_pinned_exploration(comparison_path)
    verified = load_pinned_original_watch_tape(original_paired_json)
    required = required_source_days(verified["watch_identity_rows"])
    if len(required) != EXPECTED_REQUIRED_SOURCE_DAYS:
        raise ValueError("FROZEN_57_SOURCE_DAY_CENSUS_DRIFT")
    symbols = sorted({sym for sym, _ in required})
    tapes = {sym: VerifiedClosedMinuteTape(
        publisher_dir, sym, asof_utc=asof_utc) for sym in symbols}
    missing = [(sym, day) for sym, day in required
               if tapes[sym].day_states.get(day) != "VERIFIED_FULL_DAY_1440"]
    if missing:
        raise ValueError("REQUIRED_57_PUBLISHER_DAY_SOURCE_NOT_VERIFIED: " +
                         json.dumps(missing, separators=(",", ":")))
    if Path(ledger_path).exists() or Path(ledger_path).is_symlink():
        raise ValueError("REPLAY_LEDGER_REFUSE_EXISTING_OUTPUT")
    if Path(comparison_path).resolve() == Path(ledger_path).resolve():
        raise ValueError("REPLAY_OUTPUT_PATHS_MUST_DIFFER")
    db = create_ledger(ledger_path)
    admitted = 0
    polled = 0
    try:
        def closed5(symbol, tick):
            return tapes[symbol].six_closed_5m(tick)

        for tick in range(d0.START_MS, d0.END_MS, TICK_MS):
            for event in watches_at_tick(verified, tick):
                if not admit_original_watch(db, event):
                    raise RuntimeError("DUPLICATE_ORIGINAL_WATCH_ADMISSION")
                admitted += 1
            poll_episodes(db, tick, closed5)
            polled += 1
        result = summary(db)
    finally:
        db.close()
    if admitted != EXPECTED_WATCH_COUNT or polled != 3360:
        raise RuntimeError("ORIGINAL_53_OR_3360_TICK_CENSUS_DRIFT")
    if result["episodes"] != admitted or result["status_counts"].get("PENDING", 0):
        raise RuntimeError("ORIGINAL_RESEARCH_EPISODES_NOT_FULLY_TERMINAL")
    for r in result["rows"]:
        if r["status"] == "RESEARCH_SETUP" and r["research_observed_ms"] is None:
            raise RuntimeError("SETUP_WITHOUT_PERSISTED_RESEARCH_EVENT")
    comparison = compare_exposed_exploration(
        result, reference, allow_semantic_deadline_repair=True)
    if comparison["status"] == "DIFFERENCE_FAIL_CLOSED":
        raise RuntimeError("FROZEN_53_NONSEMANTIC_RESEARCH_RESULT_DRIFT")
    return {
        "schema": SCHEMA,
        "original_paired_sha256": PINNED_PAIRED_REPORT_SHA256,
        "source_grade": "HISTORICAL_OFFICIAL_PUBLISHER_ARCHIVES_NOT_LIVE_RECEIPTS",
        "source_day_count": len(required),
        "source_days": [{"symbol": sym, "utc_day": day,
                         "publisher_zip_sha256": tapes[sym].publisher_zip_sha[day]}
                        for sym, day in required],
        "original_d0_watch_events": admitted,
        "spot_three_minute_ticks": polled,
        "isolated_sqlite_episode_status_counts": result["status_counts"],
        "sqlite_episode_rows": result["rows"],
        "prior_exploratory_comparison": comparison,
        "G0": "PARTIAL", "G1": "NOT_SCORABLE", "G2": "UNKNOWN",
        "G3": "UNKNOWN", "G4": "UNKNOWN",
        "G5": "ORIGINAL_SQLITE_REAL_SOURCE_REPLAY_NEEDS_INDEPENDENT_REVIEW",
        "G6": "NO_GO", "NO_MERGE": True, "NO_DEPLOY": True,
        "NO_MAC": True, "NO_GMAIL": True, "NO_TRADE": True,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--original-paired-json", type=Path, required=True)
    p.add_argument("--publisher-dir", type=Path, required=True)
    p.add_argument("--research-ledger-out", type=Path, required=True)
    p.add_argument("--exploratory-reference", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--asof-utc", default="2026-10-25T00:00:00Z")
    args = p.parse_args()
    output = Path(args.out)
    if output.exists() or output.is_symlink():
        p.error("REPLAY_REPORT_REFUSE_EXISTING_OUTPUT")
    at = datetime.fromisoformat(args.asof_utc.replace("Z", "+00:00"))
    # Compare reference is explicitly separate from the independent SQLite DB.
    output_data = replay(
        original_paired_json=args.original_paired_json,
        publisher_dir=args.publisher_dir,
        ledger_path=args.research_ledger_out,
        comparison_path=args.exploratory_reference, asof_utc=at)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as file:
        json.dump(output_data, file, ensure_ascii=False, indent=2, sort_keys=True)
        file.write("\n")
    print(json.dumps({
        "schema": SCHEMA,
        "counts": output_data["isolated_sqlite_episode_status_counts"],
        "reference_comparison": output_data["prior_exploratory_comparison"]["status"],
        "G6": "NO_GO"}, sort_keys=True))
    if output_data["prior_exploratory_comparison"]["status"] not in (
            "MATCH", "SEMANTIC_DEADLINE_REPAIR_MATCH"):
        raise SystemExit("ACTUAL_SQLITE_VS_EXPLORATORY_REFERENCE_MISMATCH")


if __name__ == "__main__":
    main()
