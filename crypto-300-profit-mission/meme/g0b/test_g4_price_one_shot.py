"""Offline-only tests. NEVER call a public provider."""
import unittest
from unittest.mock import patch

from g0b_gecko_one_shot import PublicGet
from g4_price_one_shot import (
    CASES, LAGS, MAX_HTTP, MIN_SPACING_SECONDS, assess_lags,
    get_manifest, run,
)


class TestG4OneShot(unittest.TestCase):
    def test_frozen_six_case_manifest(self):
        rows, digest, baseline_hash = get_manifest()
        self.assertEqual([x["id"] for x in rows], ["M2", "M3", "M4", "A2", "A3", "C3"])
        self.assertEqual(len(set(x["mint"] for x in rows)), 6)
        self.assertEqual(len(digest), 64)
        self.assertEqual(len(baseline_hash), 64)
        self.assertEqual(len(CASES), 6)
        self.assertEqual([x["kind"] for x in rows[:3]], ["FORMAL_MULT"] * 3)
        self.assertTrue(all(x["entry_time"] - x["old_pilot_t0"] > 3600 for x in rows[:3]))
        self.assertTrue(all(x["exit_target"] - x["entry_time"] < 86400 for x in rows[3:5]))
        self.assertEqual(rows[5]["kind"], "NO_SIGNAL_BUY_CONTROL")

    def test_safe_offline_default_no_network(self):
        with patch.object(PublicGet, "get", side_effect=AssertionError("NETWORK_FORBIDDEN")):
            r = run()
        self.assertEqual(r["status"], "OFFLINE_PREDECLARATION_ONLY")
        self.assertEqual(r["summary"]["requests"], 0)
        self.assertEqual(r["verified_executable_follower_quotes"], 0)
        self.assertEqual(r["strategy_verdict"], "NEED_MORE_DATA")

    def test_hard_eighteen_get_cap_and_pacing(self):
        self.assertEqual(MAX_HTTP, 18)
        self.assertEqual(LAGS, (30, 120, 300, 900, 3600))
        self.assertGreaterEqual(MIN_SPACING_SECONDS, 12.0)
        for wrong in (0, 19, 50, 100):
            with self.assertRaises(ValueError):
                run(max_http=wrong)
        with self.assertRaises(ValueError):
            PublicGet(max_calls=MAX_HTTP+1) if False else run(max_http=MAX_HTTP+1)

    def test_exit_before_entry_is_excluded_not_profitable(self):
        entry_time, exit_time = 1000, 2400
        entry = [{"t": 1060, "c": 10.0, "v": 100.0},
                 {"t": 1300, "c": 12.0, "v": 100.0},
                 {"t": 1900, "c": 15.0, "v": 100.0}]
        exit_ = [{"t": 2400, "c": 20.0, "v": 100.0}]
        out = assess_lags(entry, exit_, entry_time, exit_time)
        self.assertEqual(out["3600"]["status"], "ENTRY_AT_OR_AFTER_EXIT")
        self.assertIsNone(out["3600"]["gross_candle_close_proxy_pct"])
        self.assertEqual(out["300"]["status"], "CANDLE_PROXY_ONLY_NOT_EXECUTABLE")
        self.assertIsNotNone(out["300"]["gross_candle_close_proxy_pct"])

    def test_no_zero_volume_and_no_late_unbounded_candle(self):
        entry = [{"t": 1060, "c": 10, "v": 0},
                 {"t": 1120, "c": 12, "v": 0},
                 {"t": 5000, "c": 13, "v": 100}]
        exit_ = [{"t": 2400, "c": 20, "v": 0}]
        out = assess_lags(entry, exit_, 1000, 2400)
        for key in ("30", "120", "300"):
            self.assertEqual(out[key]["status"], "MISSING_NONZERO_VOLUME_CANDLE")
            self.assertIsNone(out[key]["gross_candle_close_proxy_pct"])

    def test_future_known_entry_after_actual_exit_rejected(self):
        entry = [{"t": 2350, "c": 12, "v": 10}]
        exit_ = [{"t": 2400, "c": 20, "v": 10}]
        row = assess_lags(entry, exit_, 2000, 2400)["300"]
        self.assertEqual(row["status"], "ENTRY_CANDLE_KNOWN_AT_OR_AFTER_EXIT")
        self.assertIsNone(row["gross_candle_close_proxy_pct"])


if __name__ == "__main__":
    unittest.main()
