"""Offline-only admission, census and comparison tests for actual SQLite driver.

These synthetic ledger rows are NOT real SQLite backtest results. Only the
driver run against pinned paired bytes and 57 official issuer ZIPs can provide
that research-grade output.
"""
from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import monster_v4_adr005_real53_original_sqlite_replay as replay


ROOT = Path(__file__).resolve().parents[2]
REFERENCE = (ROOT / "monster" / "evidence" /
             "MONSTER_ADR005_REAL53_OFFICIAL_MINUTE_INDEPENDENT_EXPLORATION_20261025.json")


def exploration():
    return json.loads(REFERENCE.read_text(encoding="utf-8"))


def original_rows():
    rows = exploration()["original_watch_linked_research_episode_rows"]
    return tuple(sorted(
        ((r["symbol"], r["original_watch_observed_ms"],
          r["original_watch_event_id"]) for r in rows),
        key=lambda x: (x[1], x[2]),
    ))


def synthetic_ledger(reference):
    result = []
    for item in reference["original_watch_linked_research_episode_rows"]:
        result.append({
            "watch_event_id": item["original_watch_event_id"],
            "symbol": item["symbol"],
            "first_seen_ms": item["original_watch_observed_ms"],
            "status": item["status"],
            "source_censored_count": item["source_censored_evaluations"],
            "research_observed_ms": (
                item["research_terminal_ms"]
                if item["status"] == "RESEARCH_SETUP" else None),
        })
    return {"rows": result}


class PinnedOriginalResearchReplayTests(unittest.TestCase):
    def test_existing_original53_derived_exact_57_source_days(self):
        required = replay.required_source_days(original_rows())
        self.assertEqual(len(required), 57)
        self.assertIn(("BTCUSDT", "2026-10-18"), required)
        self.assertEqual(len(original_rows()), 53)
        self.assertEqual({day for _, day in required},
                         {f"2026-10-{n:02d}" for n in range(18, 24)})

    def test_distinct_watch_ids_not_collapsed_by_repeated_symbol(self):
        rows = original_rows()
        self.assertEqual(len({r[2] for r in rows}), 53)
        self.assertEqual(len({r[0] for r in rows}), 39)
        self.assertGreater(len(rows), len({r[0] for r in rows}))

    def test_rejects_incomplete_watch_population(self):
        with self.assertRaisesRegex(ValueError, "PINNED_53"):
            replay.required_source_days(original_rows()[:-1])

    def test_reference_format_matches_ledger_interface_only(self):
        ref = exploration()
        got = replay.compare_exposed_exploration(synthetic_ledger(ref), ref)
        self.assertEqual(got["status"], "MATCH")
        self.assertEqual(got["original_watch_rows"], 53)
        self.assertTrue(got["reference_is_previously_exposed_not_forward_validation"])

    def test_change_a_single_sqlite_status_fails_closed(self):
        ref = exploration()
        ledger = synthetic_ledger(ref)
        ledger["rows"][0]["status"] = "SOURCE_UNSCORED"
        got = replay.compare_exposed_exploration(ledger, ref)
        self.assertEqual(got["status"], "DIFFERENCE_FAIL_CLOSED")
        self.assertTrue(any(x["field"] == "status" for x in got["mismatches"]))

    def test_change_setup_timestamp_detected(self):
        ref = exploration()
        ledger = synthetic_ledger(ref)
        ix = next(i for i, row in enumerate(ledger["rows"])
                  if row["status"] == "RESEARCH_SETUP")
        ledger["rows"][ix]["research_observed_ms"] += 180_000
        got = replay.compare_exposed_exploration(ledger, ref)
        self.assertEqual(got["status"], "DIFFERENCE_FAIL_CLOSED")
        self.assertTrue(any(x["field"] == "setup_ms" for x in got["mismatches"]))

    def test_duplicate_reference_id_and_wrong_report_sha_rejected(self):
        ref = exploration()
        ref["original_watch_linked_research_episode_rows"][-1]["original_watch_event_id"] = (
            ref["original_watch_linked_research_episode_rows"][0]["original_watch_event_id"]
        )
        with self.assertRaisesRegex(ValueError, "EXPLORATION_DUPLICATE"):
            replay.compare_exposed_exploration(synthetic_ledger(exploration()), ref)
        ref = exploration()
        ref["source_original_core_sha256"] = "f" * 64
        with self.assertRaisesRegex(ValueError, "EXPLORATION_SOURCE"):
            replay.compare_exposed_exploration(synthetic_ledger(exploration()), ref)

    def test_aware_mature_utc_asof_required_before_any_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            common = dict(
                original_paired_json=base / "does-not-exist.json",
                publisher_dir=base, ledger_path=base / "ledger.sqlite",
                comparison_path=REFERENCE,
            )
            with self.assertRaisesRegex(ValueError, "AWARE_SOURCE_ASOF"):
                replay.replay(**common, asof_utc=datetime(2026, 10, 25))
            with self.assertRaisesRegex(ValueError, "PUBLISHER_DAY"):
                replay.replay(**common, asof_utc=datetime(
                    2026, 10, 24, 23, 59, tzinfo=timezone.utc))
            self.assertFalse((base / "ledger.sqlite").exists())

    def test_missing_required_publisher_sources_cannot_start_sqlite(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            tape = {"watch_identity_rows": original_rows()}
            class MissingAllDays:
                def __init__(self, *args, **kwargs):
                    self.day_states = {}
            with patch.object(replay, "load_pinned_original_watch_tape", return_value=tape):
                with patch.object(replay, "VerifiedClosedMinuteTape", MissingAllDays):
                    with self.assertRaisesRegex(ValueError, "REQUIRED_57_PUBLISHER_DAY"):
                        replay.replay(
                            original_paired_json=base / "not-really-paired.json",
                            publisher_dir=base,
                            ledger_path=base / "research.sqlite",
                            comparison_path=REFERENCE,
                            asof_utc=datetime(2026, 10, 25, tzinfo=timezone.utc))
            self.assertFalse((base / "research.sqlite").exists())


if __name__ == "__main__":
    unittest.main()
