"""Stage137 synthetic fixtures are never real forward Binance or live delivery."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import monster_v4_stage133_manual_actual_t0_forward_proof as s133
import monster_v4_stage131_dynamic_listing_g1_population_bridge as s131
import monster_v4_stage137_dynamic_t0_original_core_causal_replay as s137
from test_monster_v4_stage133_manual_actual_t0_forward_proof import fixture
from test_monster_v4_stage135_full_market_publisher_minute_coverage import make_one_day


def t0():
    return s133.validate_three_http_records(*fixture())


def arrivals():
    return {"schema": "MONSTER_STAGE134_UNVERIFIED_ARRIVAL_CANDIDATES_V1",
            "rows": [{
                "symbol": "NEWUSDT",
                "first_observed_minute_utc": "2026-10-28T06:21:00Z",
                "source_status": "RAW_UNVERIFIED_CANDIDATE"}]}


def special_day(root, symbol, day):
    """Real CSV/ZIP parser, synthetic causal WATCH then later 2x HIGH wick."""
    start = s131.stamp(day + "T00:00:00Z")
    lines = []
    for i in range(1440):
        minute = i * 60_000
        price = "1.15" if minute >= 12 * 3600_000 else "1"
        high = "2.1" if minute == 13 * 3600_000 else (
            "1.2" if price == "1.15" else "1.1")
        low = "0.9" if price == "1" else "1.1"
        lines.append(",".join([
            str(start + minute), price, high, low, price, "1000", "1000",
            "1000", "20", "20", "20", "0"]))
    folder = root / symbol
    folder.mkdir(parents=True, exist_ok=True)
    zipped = folder / (day + ".zip")
    with zipfile.ZipFile(zipped, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(symbol + "-1m-" + day + ".csv", "\n".join(lines) + "\n")
    (folder / (day + ".zip.CHECKSUM")).write_text(
        hashlib.sha256(zipped.read_bytes()).hexdigest() + "\n")


class Stage137Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dir = tempfile.TemporaryDirectory()
        cls.root = Path(cls.dir.name)
        cls.packet = t0()
        days = [
            (datetime.fromisoformat("2026-10-27T00:00:00+00:00").date() +
             __import__("datetime").timedelta(days=i)).isoformat()
            for i in range(9)]
        cls.days = days
        for day in days:
            make_one_day(cls.root, "ABCUSDT", day)
            make_one_day(cls.root, "币安人生USDT", day)
            if day >= "2026-10-28":
                make_one_day(cls.root, "NEWUSDT", day)
        special_day(cls.root, "ABCUSDT", "2026-10-28")
        # This actually executes the ORIGINAL shadow watch/queue and Stage80 D1.
        cls.result = s137.run(cls.packet, cls.root, arrivals())

    @classmethod
    def tearDownClass(cls):
        cls.dir.cleanup()

    def test_original_d0_and_stage80_causal_dynamic_t0_source_events(self):
        x = next(z for z in self.result["all_source_population_rows"]
                 if z["symbol_exact"] == "ABCUSDT")
        self.assertEqual(x["replay_status"],
                         "ORIGINAL_ASCII_V4_D0_AND_FROZEN_D1_CAUSAL_OFFLINE")
        self.assertEqual(x["original_core_three_minute_ticks"], 3359)
        self.assertEqual(x["first_tick_utc"], "2026-10-28T06:24:00Z")
        self.assertEqual(x["last_tick_utc"], "2026-11-04T06:18:00Z")
        self.assertEqual(x["original_archive_receipts_count"], 9)
        self.assertIsNotNone(x["D0_first_UTC"])
        self.assertGreaterEqual(s131.stamp(x["D0_first_UTC"]),
                                s131.stamp("2026-10-28T12:00:00Z"))
        self.assertEqual(x["gross_future_labels_not_real_profit"][
            "first_GT2x_HIGH_UTC_EVALUATION_ONLY"], "2026-10-28T13:00:00Z")
        self.assertTrue(x["gross_future_labels_not_real_profit"][
            "D0_first_pre_GT2x_5m"])
        if x["D1_first_UTC"]:
            self.assertGreaterEqual(s131.stamp(x["D1_first_UTC"]),
                                    s131.stamp(x["D0_first_UTC"]))
            self.assertEqual(s131.stamp(x["D1_first_UTC"]) % (3 * 60_000), 0)

    def test_full_venue_denominator_survives_new_listing_unicode_and_censor(self):
        r = self.result
        self.assertEqual(r["stage135_reverified_full_market_attempts"], 4)
        self.assertEqual(r["model_attempts_scored_or_classified"], 4)
        self.assertEqual(len(r["all_source_population_rows"]), 4)
        a = {x["symbol_exact"]: x for x in r["all_source_population_rows"]}
        self.assertEqual(a["MSFTUSDT"]["replay_status"], "SOURCE_CENSORED_NO_REPLAY")
        self.assertEqual(a["币安人生USDT"]["replay_status"],
                         "ORIGINAL_V4_NUMERIC_CORE_WITH_UNICODE_IDENTITY_ADAPTER_CAUSAL_OFFLINE")
        self.assertTrue(a["币安人生USDT"]["source_core_unicode_adapter_used"])
        self.assertEqual(a["币安人生USDT"]["original_exact_venue_symbol"], "币安人生USDT")
        self.assertEqual(a["NEWUSDT"]["replay_status"],
                         "NEW_LISTING_REPLAY_NOT_YET_SUPPORTED_PIT_UNVERIFIED")
        self.assertEqual(r["raw_usdm_venue_descriptive_only"]["source_censored"], 1)
        self.assertEqual(r["raw_usdm_venue_descriptive_only"].get("model_symbol_unsupported", 0), 0)
        self.assertEqual(r["raw_usdm_venue_descriptive_only"]["model_compatible_complete"], 2)
        self.assertEqual(r["raw_usdm_venue_descriptive_only"]["new_listing_unscored"], 1)
        self.assertFalse(any(x["G1_crypto_eligible"] for x in a.values()))
        self.assertEqual((r["G0"], r["G1"], r["G4"], r["G6"]),
                         ("PARTIAL", "NOT_SCORABLE", "UNKNOWN", "NO_GO"))

    def test_first_d0_not_repeated_watches_and_only_posthoc_gross(self):
        r = self.result
        stats = r["raw_usdm_venue_descriptive_only"]
        self.assertEqual(stats["model_compatible_complete"], 2)
        self.assertEqual(stats["gross_2x"], 1)
        self.assertEqual(stats["D0_early5_2x"], 1)
        self.assertEqual(stats["first_D0"], 1)
        self.assertLessEqual(stats.get("first_D1", 0), 1)
        self.assertTrue(r["not_live_one_minute_capture_proof"])
        self.assertFalse(r["complete_asof_issuer_scope_verified"])
        self.assertEqual(r["historical_stage116_first_window"],
                         "SOURCE_FAILED_NO_BACKFILL")
        self.assertEqual(r["stage132_buy_proxy"], "NEGATIVE_UNCHANGED")
        self.assertFalse(r["scheduled_capture"])

    def test_unicode_causes_identical_original_v4_d0_and_stage80_d1_numeric_signals(self):
        start = s131.stamp("2026-10-28T06:20:00Z")
        end = start + 168 * 3600_000
        bars, _ = s137.full_window_minutes(self.root, "ABCUSDT", start, end)
        contract = s137.original_core_contract()
        ascii_result = s137.replay_original_d0_d1("ABCUSDT", start, end, bars, contract)
        unicode_result = s137.replay_original_d0_d1("币安人生USDT", start, end, bars, contract)
        self.assertIsNotNone(ascii_result["D0_first_UTC"])
        for name in ("D0_first_UTC", "D1_first_UTC", "D1_entry_path",
                     "gross_future_labels_not_real_profit",
                     "original_WATCH_EARLY_event_count_not_independent_2x"):
            self.assertEqual(ascii_result[name], unicode_result[name])
        self.assertTrue(unicode_result["source_core_unicode_adapter_used"])
        self.assertFalse(ascii_result["source_core_unicode_adapter_used"])
        self.assertEqual(unicode_result["original_exact_venue_symbol"], "币安人生USDT")
        self.assertNotEqual(unicode_result["isolated_original_D0_SQLite_symbol"], "币安人生USDT")
        self.assertTrue(unicode_result["isolated_original_D0_SQLite_symbol"].isascii())
        self.assertTrue(unicode_result["isolated_original_D0_SQLite_symbol"].endswith("USDT"))
        self.assertEqual(unicode_result["replay_status"],
                         "ORIGINAL_V4_NUMERIC_CORE_WITH_UNICODE_IDENTITY_ADAPTER_CAUSAL_OFFLINE")

    def test_actual_stage140_525_original_symbol_aliases_collision_free(self):
        file = Path(__file__).resolve().parents[2] / (
            "monster/evidence/monster_stage140_user_authorized_real_www_mirror_20261015/"
            "t0_2026-10-14T175247096Z/stage139_original_T0_asof_contract_metadata.json")
        record = json.loads(file.read_text(encoding="utf-8"))
        original = [x["symbol_exact"] for x in record["initial_original_instrument_rows"]]
        self.assertEqual(len(original), 525)
        unicode = [name for name in original if not name.isascii()]
        self.assertEqual(set(unicode), {
            "哈基米USDT", "币安人生USDT", "我踏马来了USDT", "牛来USDT", "龙虾USDT"})
        aliases = s137.assert_original_population_aliases(
            [{"symbol_exact": name} for name in original])
        self.assertEqual(len(aliases), 525)
        self.assertEqual(sum(k != v for k, v in aliases.items()), 5)
        for name in unicode:
            self.assertEqual(aliases[s137.original_d0_internal_symbol(name)], name)

    def test_original_ascii_name_collision_with_unicode_proxy_is_rejected(self):
        proxy = s137.original_d0_internal_symbol("币安人生USDT")
        with self.assertRaisesRegex(ValueError, "ALIAS_SHADOWS_REAL_MARKET_SYMBOL"):
            s137.assert_original_population_aliases([
                {"symbol_exact": proxy}, {"symbol_exact": "币安人生USDT"}])

    def test_off_grid_relative_t0_never_unaligned_at_utc(self):
        start = s131.stamp("2026-10-28T06:20:00Z")
        end = start + 168 * 3600_000
        polls = s137.clocks(start, end)
        self.assertEqual(len(polls), 3359)
        self.assertEqual(polls[0], s131.stamp("2026-10-28T06:24:00Z"))
        self.assertEqual(polls[-1], s131.stamp("2026-11-04T06:18:00Z"))
        self.assertTrue(all(t % (3 * 60_000) == 0 for t in polls))
        self.assertTrue(all(start <= t < end for t in polls))
        with self.assertRaises(ValueError):
            s137.clocks(start + 60_000, end)

    def test_censored_full_universe_has_no_fabricated_negative(self):
        with tempfile.TemporaryDirectory() as folder:
            x = s137.run(self.packet, folder)
        self.assertEqual(x["model_attempts_scored_or_classified"], 3)
        self.assertEqual(x["raw_usdm_venue_descriptive_only"]["source_censored"], 3)
        self.assertEqual(x["raw_usdm_venue_descriptive_only"].get("gross_2x", 0), 0)
        self.assertTrue(all(row["replay_status"] == "SOURCE_CENSORED_NO_REPLAY"
                            for row in x["all_source_population_rows"]))
        self.assertEqual(x["G1"], "NOT_SCORABLE")

    def test_original_model_blob_fails_closed_without_tuning(self):
        with patch.object(s137.v4, "ORIGINAL_V4_GIT_BLOB", "0" * 40):
            with self.assertRaisesRegex(ValueError, "FROZEN_PRODUCTION_V4_BLOB_CHANGED"):
                s137.original_core_contract()

    def test_real_byte_checksum_tamper_never_grants_replay(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            source = folder / "ABCUSDT"
            source.mkdir()
            (source / (self.days[0] + ".zip")).write_bytes(b"bad")
            (source / (self.days[0] + ".zip.CHECKSUM")).write_text("0"*64)
            with self.assertRaises((ValueError, zipfile.BadZipFile)):
                s137.run(self.packet, folder)

    def test_offline_cli_end_to_end_saved_full_source_all_attempts(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            t0_path, a_path, result_path = (folder / "t0.json",
                                           folder / "arrivals.json",
                                           folder / "stage137.json")
            t0_path.write_text(json.dumps(self.packet, ensure_ascii=False))
            a_path.write_text(json.dumps(arrivals(), ensure_ascii=False))
            cmd = [sys.executable, str(Path(s137.__file__)),
                   "--t0", str(t0_path), "--arrival-candidates", str(a_path),
                   "--archive-root", str(self.root), "--out", str(result_path)]
            run = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
            self.assertEqual(run.returncode, 0, run.stderr)
            result = json.loads(result_path.read_text())
            self.assertEqual(result["model_attempts_scored_or_classified"], 4)
            self.assertEqual(result["G1"], "NOT_SCORABLE")
            self.assertEqual(result["G6"], "NO_GO")
            self.assertTrue(result["not_live_one_minute_capture_proof"])


if __name__ == "__main__":
    unittest.main()
