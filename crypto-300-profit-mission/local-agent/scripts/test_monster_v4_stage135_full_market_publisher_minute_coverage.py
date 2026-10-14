import copy
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

import monster_v4_stage133_manual_actual_t0_forward_proof as stage133
import monster_v4_stage135_full_market_publisher_minute_coverage as stage135
from test_monster_v4_stage133_manual_actual_t0_forward_proof import fixture


def timestamp(day, minute):
    start = int(datetime.fromisoformat(day + "T00:00:00+00:00").timestamp()*1000)
    return start + 60000*minute


def make_one_day(root, symbol, day, *, omit=None):
    # Offline synthetic, original Stage130 CSV parser and ZIP/CHECKSUM format.
    lines = []
    for m in range(1440):
        if m == omit:
            continue
        lines.append(",".join((str(timestamp(day, m)), "1", "1.1", "0.9",
                               "1", "100", "100", "1000", "10",
                               "10", "10", "0")))
    folder = root / symbol
    folder.mkdir(parents=True, exist_ok=True)
    zipped = folder / (day + ".zip")
    with zipfile.ZipFile(zipped, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(symbol + "-1m-" + day + ".csv", "\n".join(lines) + "\n")
    checksum = hashlib.sha256(zipped.read_bytes()).hexdigest()
    (folder / (day + ".zip.CHECKSUM")).write_text(checksum + "  " + zipped.name + "\n")
    return zipped


def t0():
    return stage133.validate_three_http_records(*fixture())


class Stage135Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temp.name)
        start = datetime(2026, 10, 27, tzinfo=timezone.utc).date()
        cls.days = [(start + timedelta(days=i)).isoformat() for i in range(9)]
        for day in cls.days:
            make_one_day(cls.root, "ABCUSDT", day)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_t0_full_population_no_watch_and_one_real_archive_parser_complete(self):
        r = stage135.audit(t0(), self.root)
        self.assertEqual(r["full_initial_venue_candidates"], 3)
        self.assertEqual(r["full_market_attempts"], 3)
        self.assertEqual(r["source_contiguous_since_required_origin"], 1)
        self.assertEqual(r["source_missing_or_gapped"], 2)
        by_symbol = {x["symbol_exact"]: x for x in r["per_symbol_source_audit"]}
        abc = by_symbol["ABCUSDT"]
        self.assertTrue(abc["source_minute_continuity"])
        self.assertEqual(abc["expected_minute_count"], 8*1440)
        self.assertEqual(abc["observed_minute_count"], 8*1440)
        self.assertEqual(len(abc["original_archive_receipts"]), 9)
        self.assertTrue(all(x["zip_sha256"]
                            for x in abc["original_archive_receipts"]))
        self.assertFalse(abc["eligible_to_claim_full_market_G0_or_G1"])
        self.assertEqual(by_symbol["MSFTUSDT"]["source_status"],
                         "CENSORED_SOURCE_GAP_OR_MISSING")
        self.assertFalse(r["in_window_arrival_census_complete"])
        self.assertFalse(r["source_origin_not_independently_attested"] is False)
        self.assertFalse(r["delivery_latency_real_time_observed"])
        self.assertEqual((r["G0"], r["G1"], r["G4"], r["G6"]),
                         ("PARTIAL", "NOT_SCORABLE", "UNKNOWN", "NO_GO"))
        self.assertEqual(r["historical_stage116_original_oct14_failure"],
                         "SOURCE_FAILED_NO_BACKFILL")

    def test_full_missing_archive_retained_as_censored_not_negative(self):
        with tempfile.TemporaryDirectory() as d:
            r = stage135.audit(t0(), Path(d))
        self.assertEqual(r["full_market_attempts"], 3)
        self.assertEqual(r["source_contiguous_since_required_origin"], 0)
        self.assertEqual(r["source_missing_or_gapped"], 3)
        self.assertTrue(all(x["missing_utc_days"] for x in r["per_symbol_source_audit"]))
        self.assertTrue(all(x["D0_watch"] == "NOT_RUN_NO_LIVE_OBSERVATION"
                            for x in r["per_symbol_source_audit"]))
        self.assertEqual(r["G1"], "NOT_SCORABLE")

    def test_censored_publisher_missing_checksum_and_corrupt_existing_bytes_fail(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            make_one_day(root, "ABCUSDT", self.days[0])
            p = root / "ABCUSDT" / (self.days[0] + ".zip.CHECKSUM")
            p.unlink()
            missing = stage135.locally_verified_day(root, "ABCUSDT", self.days[0])
            self.assertIsNone(missing[0])
            self.assertEqual(missing[1]["missing_components"], ["CHECKSUM"])
            p.write_text("0"*64)
            with self.assertRaisesRegex(ValueError, "CHECKSUM_MISMATCH"):
                stage135.locally_verified_day(root, "ABCUSDT", self.days[0])

    def test_present_but_gap_in_a_day_is_invalid_and_not_zero(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            make_one_day(root, "ABCUSDT", self.days[0], omit=60)
            with self.assertRaisesRegex(ValueError, "GAPPED_OR_UNSORTED"):
                stage135.locally_verified_day(root, "ABCUSDT", self.days[0])

    def test_in_window_arrival_is_always_unverified_pit(self):
        arrivals = {"schema": "MONSTER_STAGE134_UNVERIFIED_ARRIVAL_CANDIDATES_V1",
                    "rows": [{"symbol": "NEWUSDT",
                              "first_observed_minute_utc": "2026-10-28T06:21:00Z",
                              "source_status": "RAW_UNVERIFIED_CANDIDATE"}]}
        r = stage135.audit(t0(), self.root, arrivals)
        self.assertEqual(r["full_market_attempts"], 4)
        self.assertEqual(r["in_window_candidates_unverified"], 1)
        self.assertEqual(r["source_missing_or_gapped"], 3)
        item = next(x for x in r["per_symbol_source_audit"]
                    if x["symbol_exact"] == "NEWUSDT")
        self.assertEqual(item["first_observation_source_boundary"],
                         "SELF_REPORTED_ARRIVAL_CLOCK_PIT_UNVERIFIED")
        self.assertFalse(item["first_listing_time_independently_attested"])
        self.assertEqual(item["required_source_from_utc"],
                         "2026-10-28T06:21:00Z")
        self.assertLess(item["expected_minute_count"], 8*1440)

    def test_wrong_source_ledger_rejected_before_archive_read(self):
        p = t0()
        p["G1"] = "PASS"
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError, "RECEIPT_OR_ROSTER_DRIFT"):
                stage135.audit(p, Path(d))

    def test_offline_cli_real_zip_receipts_no_network_or_buy(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            source = root/"stage133.json"
            output = root/"stage135.json"
            source.write_text(json.dumps(t0(), ensure_ascii=False))
            cmd = [sys.executable, str(Path(stage135.__file__)), "--t0",
                   str(source), "--archive-root", str(self.root),
                   "--out", str(output)]
            run = subprocess.run(cmd, capture_output=True, text=True, timeout=40)
            self.assertEqual(run.returncode, 0, run.stderr)
            result = json.loads(output.read_text())
            self.assertEqual(result["full_market_attempts"], 3)
            self.assertEqual(result["source_contiguous_since_required_origin"], 1)
            self.assertEqual(result["G1"], "NOT_SCORABLE")
            self.assertFalse(result["automated_collection_scheduled"])


if __name__ == "__main__":
    unittest.main()
