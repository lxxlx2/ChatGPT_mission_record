import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import monster_v4_stage133_manual_actual_t0_forward_proof as s133
import monster_v4_stage134_t0_population_readiness_bridge as s134
from test_monster_v4_stage133_manual_actual_t0_forward_proof import fixture


def packet():
    return s133.validate_three_http_records(*fixture())


def candidates(rows):
    return {"schema": s134.ARRIVAL_SCHEMA, "rows": rows}


def item(symbol, t, source="RAW_UNVERIFIED_CANDIDATE"):
    return {"symbol": symbol, "first_observed_minute_utc": t,
            "source_status": source}


class Stage134Tests(unittest.TestCase):
    def test_full_t0_active_roster_no_crypto_upgrade_or_invented_arrivals(self):
        x = s134.reconcile(packet())
        self.assertEqual(x["full_t0_exchangeinfo_symbols_in_original_raw"], 5)
        self.assertEqual(x["t0_active_usdt_perpetual_attempts"], 3)
        self.assertEqual(x["in_window_arrival_candidates_unverified"], 0)
        self.assertFalse(x["arrival_census_complete"])
        rows = x["stage131_reconciled_population"]["raw_population_rows"]
        self.assertEqual([z["symbol_exact"] for z in rows],
                         ["ABCUSDT", "MSFTUSDT", "币安人生USDT"])
        self.assertTrue(all(z["included_in_raw_attempt_ledger"] for z in rows))
        self.assertTrue(all(not z["asof_crypto_issuer_verified"] for z in rows))
        self.assertEqual(x["G0"], "PARTIAL")
        self.assertEqual(x["G1"], "NOT_SCORABLE")
        self.assertEqual(x["G4"], "UNKNOWN")
        self.assertFalse(x["live_market_source_capture"])
        self.assertEqual(x["original_stage116_oct14_0600"],
                         "SOURCE_FAILED_NO_BACKFILL")
        self.assertFalse(x["scheduled_capture_or_notification_created"])
        self.assertEqual(x["Stage132_first_momentum_buy_proxy"],
                         "NEGATIVE_UNCHANGED")

    def test_new_arrivals_and_t0_inactive_transition_stay_unverified(self):
        a = candidates([
            item("NEWUSDT", "2026-10-28T06:21:00Z"),
            item("OLDUSDT", "2026-10-28T06:22:00Z"),
        ])
        x = s134.reconcile(packet(), a)
        self.assertEqual(x["t0_active_usdt_perpetual_attempts"], 3)
        self.assertEqual(x["in_window_arrival_candidates_unverified"], 2)
        self.assertEqual(x["stage131_reconciled_population"]["raw_symbol_attempts"], 5)
        rows = {z["symbol_exact"]: z
                for z in x["stage131_reconciled_population"]["raw_population_rows"]}
        self.assertEqual(rows["NEWUSDT"]["arrival_source_classification"],
                         "NOT_PRESENT_IN_T0_EXCHANGEINFO")
        self.assertEqual(rows["OLDUSDT"]["arrival_source_classification"],
                         "T0_PRESENT_BUT_NOT_IN_ACTIVE_USDT_PERPETUAL_ROSTER")
        self.assertEqual(rows["NEWUSDT"]["source_status"],
                         "UNVERIFIED_OFFLINE_ARRIVAL_CANDIDATE")
        self.assertFalse(rows["NEWUSDT"]["asof_trading_eligibility_verified"])
        self.assertFalse(x["arrival_census_complete"])

    def test_empty_supplied_arrivals_not_zero_listing_certification(self):
        x = s134.reconcile(packet(), candidates([]))
        self.assertEqual(x["arrival_evidence"], "UNVERIFIED_CANDIDATES_ONLY")
        self.assertFalse(x["arrival_census_complete"])
        self.assertEqual(x["G1"], "NOT_SCORABLE")

    def test_stage133_saved_roster_and_gates_must_recompute_identically(self):
        for change in (
            ("exact_usdt_perpetual_symbols", ["ABCUSDT"]),
            ("G1", "PASS"),
            ("new_forward_start_utc", "2026-10-28T06:15:00Z"),
            ("exchange_full_original_symbols", 3),
            ("future_all_market_7day_source", "COMPLETE"),
        ):
            p = packet()
            p[change[0]] = change[1]
            with self.subTest(change=change), self.assertRaisesRegex(
                    ValueError, "RECEIPT_OR_ROSTER_DRIFT"):
                s134.reconcile(p)

    def test_raw_market_sha_tamper_and_missing_time_fail_closed(self):
        p = packet()
        p["raw_http_records"]["official_exchange_info"]["raw_sha256"] = "0"*64
        with self.assertRaisesRegex(ValueError, "SHA256_CHANGED"):
            s134.reconcile(p)
        p = packet()
        del p["raw_http_records"]["official_before_time"]
        with self.assertRaisesRegex(ValueError, "EXACT_THREE_RAW"):
            s134.reconcile(p)

    def test_collision_repeated_arrival_and_out_of_window_rejected(self):
        for c in (
            candidates([item("ABCUSDT", "2026-10-28T06:21:00Z")]),
            candidates([item("NEWUSDT", "2026-10-28T06:21:00Z"),
                        item("NEWUSDT", "2026-10-28T06:22:00Z")]),
        ):
            with self.subTest(c=c), self.assertRaisesRegex(
                    ValueError, "DOUBLE_COUNT"):
                s134.reconcile(packet(), c)
        for t in ("2026-10-28T06:19:00Z",
                  "2026-11-04T06:20:00Z",
                  "2026-10-28T06:21:01Z"):
            with self.subTest(t=t), self.assertRaises(ValueError):
                s134.reconcile(packet(), candidates([item("NEWUSDT", t)]))

    def test_self_claimed_source_proof_rejected_and_cannot_buy(self):
        for word in ("ATTESTED", "VERIFIED_CRYPTO", "COMPLETE_PUBLISHER_SHA",
                     "AUTHENTIC_BINANCE"):
            with self.subTest(word=word), self.assertRaisesRegex(
                    ValueError, "CANNOT_SELF_ATTEST"):
                s134.reconcile(packet(), candidates([
                    item("NEWUSDT", "2026-10-28T06:21:00Z", word)]))
        bad = candidates([{"symbol": "NEWUSDT",
                           "first_observed_minute_utc": "2026-10-28T06:21:00Z",
                           "source_status": "PENDING",
                           "G1": "PASS"}])
        with self.assertRaisesRegex(ValueError, "EXACT_FIELDS"):
            s134.reconcile(packet(), bad)

    def test_schema_and_stage133_synthetic_source_not_live(self):
        with self.assertRaisesRegex(ValueError, "BAD_STAGE133_PACKET_SCHEMA"):
            s134.reconcile({"schema": "MONSTER_STAGE123_CONNECTOR_JSON"})
        with self.assertRaisesRegex(ValueError, "UNVERIFIED_ARRIVAL_SCHEMA"):
            s134.reconcile(packet(), {"rows": []})
        self.assertEqual(s134.reconcile(packet())["stage77_frozen_acceptance"],
                         {"G1_min_independent_2x":20,
                          "G1_min_independent_windows":3,
                          "G1_first_D0_strict_pct":90,
                          "G1_first_D0_early5_pct":85,
                          "G2_first_D1_retention_pct":80,
                          "G3_mean_D1_per_day_max":5,
                          "G3_peak_D1_per_day_max":12,
                          "G4_independent_full_buy_sell_observations_min":30})

    def test_offline_cli_real_modules_no_network_and_json_round_trip(self):
        p = packet()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "stage133.json"
            out = root / "stage134.json"
            source.write_text(json.dumps(p, ensure_ascii=False))
            script = Path(s134.__file__)
            result = subprocess.run([sys.executable, str(script), "--t0",
                                     str(source), "--out", str(out)],
                                    capture_output=True, text=True, timeout=25)
            self.assertEqual(result.returncode, 0, result.stderr)
            saved = json.loads(out.read_text())
            self.assertEqual(saved["t0_active_usdt_perpetual_attempts"], 3)
            self.assertEqual(saved["G1"], "NOT_SCORABLE")
            self.assertFalse(saved["live_market_source_capture"])


if __name__ == "__main__":
    unittest.main()
