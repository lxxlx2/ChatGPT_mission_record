"""Genuine minute-bar Stage10 unselected calendar/symbol V4 replay tests."""
import importlib.util
import json
import unittest
from pathlib import Path

PATH = Path(__file__).resolve().parents[1] / "scripts/monster_v4_neutral_control_replay.py"
spec = importlib.util.spec_from_file_location("monster_v4_neutral_control_replay", PATH)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class Stage10NeutralTests(unittest.TestCase):
    def test_registration_recomputes_all_hashes_before_using_source(self):
        manifest = json.loads(m.MANIFEST.read_text())
        missing = json.loads(m.FETCH.read_text())
        selected, excluded = m.validate_registration(manifest, missing)
        self.assertEqual(len(selected), 24)
        self.assertEqual(len(excluded), 7)
        self.assertEqual(manifest["universe_count"], 504)
        self.assertEqual(len({x["symbol"] for x in selected}),24)

    def test_forged_optimization_or_source_exclusion_is_rejected(self):
        data = json.loads(m.MANIFEST.read_text())
        source = json.loads(m.FETCH.read_text())
        data["selected"][0]["symbol"] = "BTCUSDT"
        with self.assertRaisesRegex(ValueError, "SELECTION_NOT_REPRODUCIBLE"):
            m.validate_registration(data, source)
        data = json.loads(m.MANIFEST.read_text())
        source["unavailable"].append(source["unavailable"][0])
        with self.assertRaisesRegex(ValueError, "SOURCE_STATUS_INCOMPLETE|UNREGISTERED_SOURCE_EXCLUSION"):
            m.validate_registration(data, source)

    def test_real_17_case_production_d0_d1_uses_every_precommitted_source(self):
        results = m.run()
        summary = results["summary"]
        self.assertEqual(summary["frozen_candidates"], 24)
        self.assertEqual(summary["valid_contiguous_60h"], 17)
        self.assertEqual(summary["source_not_historically_available"], 7)
        self.assertEqual(summary["nominal_window_symbol_hours"], 204)
        self.assertEqual(summary["intended_3m_poll_intervals"], 240 * 17)
        self.assertEqual(summary["dense_ticker_continuity_observed_symbol_hours"], 204)
        self.assertEqual(summary["sparse_zero_trade_skip_watches"],
                         sum(x["sparse_policy_watches"] for x in results["cases"]))
        self.assertEqual(summary["actual_nonzero_trade_3m_polls"] +
                         summary["skipped_zero_trade_3m_polls"], 240 * 17)
        self.assertLessEqual(summary["actual_nonzero_trade_symbol_hours"], 204)
        self.assertEqual(len(results["cases"]), 17)
        self.assertEqual(len(results["source_unavailable"]), 7)
        self.assertEqual(len(summary["per_calendar_day"]), 6)
        self.assertEqual(results["production_gate"], "NO_GO")
        self.assertFalse(results["independent_ai_review_completed"])
        for case in results["cases"]:
            self.assertEqual(case["intended_polls"], 240)
            self.assertEqual(case["polls"], 240)
            self.assertEqual(case["polls_skipped_no_trade"], 0)
            self.assertEqual(case["sparse_policy_polls"] + case["zero_trade_last_minute_3m_polls"], 240)
            if case["first_watch_utc"]:
                self.assertGreaterEqual(case["first_watch_utc"], case["replay_start_utc"])
                self.assertLessEqual(case["first_watch_utc"], case["replay_end_utc"])


if __name__ == "__main__":
    unittest.main()
