#!/usr/bin/env python3
"""Offline-only tests for enhanced candidate review; fake wallets and fake profits."""
import csv
import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path

from bsc_top_trader_crosscheck import review, parse_timestamp


class CrosscheckTests(unittest.TestCase):
    def test_timestamp_units(self):
        self.assertEqual(
            parse_timestamp(1791000000000),
            parse_timestamp(1791000000))
        self.assertIsNone(parse_timestamp(None))
        self.assertIsNone(parse_timestamp(0))

    def test_recent_vendor_activity_is_not_confirmed_swap(self):
        wallet = "0x" + "1" * 40
        now = int(dt.datetime.now(dt.timezone.utc).timestamp())
        with tempfile.TemporaryDirectory() as base:
            path = Path(base) / "analysis"
            path.mkdir()
            with (path / "token_trader_samples.csv").open(
                    "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=[
                    "wallet", "token", "year", "provisional_realized_winner",
                    "last_token_activity_utc", "flags"
                ])
                writer.writeheader()
                writer.writerow({"wallet": wallet, "token": "龙虾", "year": 2026,
                                 "provisional_realized_winner": "True",
                                 "last_token_activity_utc": now,
                                 "flags": ""})
                writer.writerow({"wallet": wallet, "token": "牛来", "year": 2026,
                                 "provisional_realized_winner": "True",
                                 "last_token_activity_utc": now,
                                 "flags": ""})
            with (path / "cross_token_wallets.csv").open(
                    "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=["wallet"])
                writer.writeheader()
                writer.writerow({"wallet": wallet})
            self.assertEqual(review(Path(base), 30), 0)
            rows = list(csv.DictReader(
                (path / "active_candidate_review.csv").open(
                    encoding="utf-8-sig", newline="")))
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["provisional_positive_2026_tokens"], "2")
            self.assertEqual(rows[0]["vendor_token_activity_in_last_30d"], "True")
            self.assertEqual(rows[0]["direct_30d_meme_swap_confirmed"], "False")
            self.assertEqual(rows[0]["research_status"], "OBSERVE_ONLY")
            summary = json.loads((path / "review_summary.json").read_text())
            self.assertFalse(summary["all_dex_alltime_top100_verified"])
            self.assertEqual(summary["production_trading"], "NO_GO")


if __name__ == "__main__":
    unittest.main()
