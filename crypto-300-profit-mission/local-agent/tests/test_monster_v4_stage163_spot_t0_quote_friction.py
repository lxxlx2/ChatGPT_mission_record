"""Stage163 original Spot T0 source-locked friction and no-P&L regressions."""
import copy
import importlib.util
from pathlib import Path
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "monster_v4_stage163_spot_t0_quote_friction.py"
spec = importlib.util.spec_from_file_location("monster_v4_stage163_spot_t0_quote_friction", SCRIPT)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


def fake():
    entries = [
        {"symbol": f"TEST{i}USDT", "quoteAsset": "USDT", "status": "TRADING",
         "isSpotTradingAllowed": True}
        for i in range(gate.EXPECTED_ACTIVE)
    ]
    # Keep one known BBO and one known notional for deterministic arithmetic.
    books = [
        {"symbol": x["symbol"], "bidPrice": "1", "askPrice": "1.01",
         "bidQty": "20", "askQty": "20"}
        for x in entries
    ]
    ticker = [{"symbol": x["symbol"], "quoteVolume": "123.45"} for x in entries]
    receipts = {"source_sha_receipts": {
        "bookTicker": {"start_utc": "2026-10-17T22:04:42Z", "end_utc": "2026-10-17T22:04:44Z"},
        "ticker24": {"start_utc": "2026-10-17T22:04:44Z", "end_utc": "2026-10-17T22:04:47Z"},
    }}
    return {"exchangeInfo": {"serverTime": gate.T0_MS, "symbols": entries},
            "bookTicker": books, "ticker24": ticker}, receipts


class TestT0Friction(unittest.TestCase):
    def test_real_source_all511_and_expected_t0_quality(self):
        blobs, receipt = gate.load_archived()
        self.assertEqual(receipt["stats"]["spot_usdt_active"], 511)
        result = gate.evaluate(blobs, receipt)
        self.assertEqual(result["t0_active_spot_usdt_denominator"], 511)
        self.assertFalse(result["population_scope_is_all_binance_spot"])
        self.assertTrue(result["complete_archived_exchangeinfo_t0_eligible_cohort_represented"])
        pop = result["population_counts_from_exchangeinfo"]
        self.assertEqual((pop["usdt_all_statuses_including_spot_disallowed"],
                          pop["usdt_trading_spot_allowed"],
                          pop["usdt_break_all_spot_permissions"],
                          pop["usdt_break_spot_allowed"],
                          pop["usdt_break_spot_disallowed"]), (765, 511, 254, 214, 40))
        self.assertEqual(result["excluded_market_symbols_not_in_exchangeinfo"]["bookTicker"],
                         ["AXSBIDR", "NBTBIDR", "NBTUSDT"])
        self.assertFalse(result["t0_causal_quote_at_t0_proven"])
        self.assertFalse(result["eligible_for_t0_asof_executable_execution_or_signal_backtest"])
        intervals = result["post_t0_receipt_windows_vs_exchangeinfo_t0_approx"]
        self.assertEqual(intervals["bookTicker"]["start_offset_from_exchange_t0_ms_approx"], "2561.682")
        self.assertEqual(intervals["bookTicker"]["end_offset_from_exchange_t0_ms_approx"], "4349.393")
        self.assertEqual(intervals["ticker24"]["start_offset_from_exchange_t0_ms_approx"], "4349.727")
        self.assertEqual(intervals["ticker24"]["end_offset_from_exchange_t0_ms_approx"], "6835.464")
        self.assertEqual(result["quote_bundle_not_available_until_client_receipt_utc"],
                         "2026-10-17T22:04:46.929464Z")
        self.assertEqual(len(result["rows"]), 511)
        self.assertEqual(len({x["symbol"] for x in result["rows"]}), 511)
        self.assertEqual(result["exchange_server_time_ms"], gate.T0_MS)
        # The original T0 QA published rounded four-decimal presentation.
        # Its median 11.2170 vs new high precision 11.217050 is not drift.
        for actual, published in zip(result["post_t0_bookticker_spread_bps_p10_median_p90"],
                                     [2.0608, 11.2170, 28.9715]):
            self.assertAlmostEqual(float(actual), published, delta=0.0001)
        self.assertEqual(result["research_notional_usdt"], "UNKNOWN_NOT_SPECIFIED")
        self.assertEqual(result["research_notional_displayed_top_level_size_coverage_only"],
                         "NOT_EVALUATED_WITHOUT_EXPLICIT_RESEARCH_AMOUNT")
        self.assertEqual((result["G4"], result["G6"], result["NO_TRADE"]), ("UNKNOWN", "NO_GO", True))
        self.assertEqual(result["original_exited_24h_funding_economics"], "NOT_SCORABLE")
        self.assertTrue(result["no_historical_exit_L2"])

    def test_spread_math_and_optional_research_amount_only(self):
        blobs, receipt = fake()
        result = gate.evaluate(blobs, receipt)
        first = result["rows"][0]
        self.assertEqual(first["displayed_bid_notional_usdt"], "20.000000")
        self.assertEqual(first["displayed_ask_notional_usdt"], "20.200000")
        self.assertEqual(first["post_t0_bookticker_spread_bps"], "99.502488")
        self.assertEqual(first["post_t0_bookticker_cross_loss_before_fees_bps"], "99.009901")
        self.assertNotIn("optional_research_notional_displayed_top_quote_size_only", first)
        smaller = gate.evaluate(blobs, receipt, "20")
        self.assertEqual(smaller["research_notional_displayed_top_level_size_coverage_only"],
                         {"count": 511, "denominator": 511})
        bigger = gate.evaluate(blobs, receipt, "20.1")
        self.assertEqual(bigger["research_notional_displayed_top_level_size_coverage_only"],
                         {"count": 0, "denominator": 511})
        self.assertEqual(bigger["G6"], "NO_GO")

    def test_no_future_exit_or_user_fee_tier_implied(self):
        blobs, receipt = fake()
        d = gate.evaluate(blobs, receipt)
        self.assertEqual(d["user_fee_tier"], "UNKNOWN")
        self.assertFalse(d["current_market_quote"])
        self.assertTrue(d["historical_post_t0_quote_receipts_once_not_forward_live_signal"])
        self.assertTrue(d["market_endpoint_snapshots_not_atomic"])
        self.assertNotIn("pnl", d)
        self.assertNotIn("buy_signal", d)

    def test_missing_symbol_and_duplicate_quote_fail_without_511_reduction(self):
        blobs, receipt = fake()
        missing = copy.deepcopy(blobs)
        missing["bookTicker"].pop()
        with self.assertRaisesRegex(ValueError, "SOURCE_MISSING"):
            gate.evaluate(missing, receipt)
        doubled = copy.deepcopy(blobs)
        doubled["ticker24"][1] = copy.deepcopy(doubled["ticker24"][0])
        with self.assertRaisesRegex(ValueError, "DUPLICATE"):
            gate.evaluate(doubled, receipt)
        fewer = copy.deepcopy(blobs)
        fewer["exchangeInfo"]["symbols"].pop()
        with self.assertRaisesRegex(ValueError, "FULL511"):
            gate.evaluate(fewer, receipt)

    def test_crossed_and_nonfinite_or_bad_notional_rejected(self):
        blobs, receipt = fake()
        crossed = copy.deepcopy(blobs)
        crossed["bookTicker"][0]["askPrice"] = "0.99"
        with self.assertRaisesRegex(ValueError, "INVALID_BBO"):
            gate.evaluate(crossed, receipt)
        nan = copy.deepcopy(blobs)
        nan["bookTicker"][0]["bidQty"] = "NaN"
        with self.assertRaisesRegex(ValueError, "NONFINITE"):
            gate.evaluate(nan, receipt)
        for amount in ("0", "-1", "NaN"):
            with self.assertRaises(ValueError):
                gate.evaluate(blobs, receipt, amount)

    def test_after_t0_receipt_boundaries_are_explicit_and_fail_closed(self):
        blobs, receipts = fake()
        r = gate.evaluate(blobs, receipts)
        self.assertFalse(r["t0_causal_quote_at_t0_proven"])
        self.assertGreater(float(r["post_t0_receipt_windows_vs_exchangeinfo_t0_approx"]["bookTicker"]["start_offset_from_exchange_t0_ms_approx"]), 0)
        early = copy.deepcopy(receipts)
        early["source_sha_receipts"]["bookTicker"]["start_utc"] = "2026-10-17T22:04:39Z"
        with self.assertRaisesRegex(ValueError, "NOT_POST_T0"):
            gate.evaluate(blobs, early)
        backwards = copy.deepcopy(receipts)
        backwards["source_sha_receipts"]["ticker24"]["end_utc"] = "2026-10-17T22:04:43Z"
        with self.assertRaisesRegex(ValueError, "CHRONOLOGY"):
            gate.evaluate(blobs, backwards)

    def test_break_and_spot_ineligible_population_exclusions_are_reported(self):
        blobs, receipts = fake()
        blobs["exchangeInfo"]["symbols"].extend([
            {"symbol": "BREAK1USDT", "quoteAsset": "USDT", "status": "BREAK", "isSpotTradingAllowed": True},
            {"symbol": "BREAK2USDT", "quoteAsset": "USDT", "status": "BREAK", "isSpotTradingAllowed": False},
            {"symbol": "DENIEDUSDT", "quoteAsset": "USDT", "status": "TRADING", "isSpotTradingAllowed": False},
            {"symbol": "ANOTHERBTC", "quoteAsset": "BTC", "status": "TRADING", "isSpotTradingAllowed": True},
        ])
        r = gate.evaluate(blobs, receipts)
        counts = r["population_counts_from_exchangeinfo"]
        self.assertEqual((counts["usdt_all_statuses_including_spot_disallowed"],
                          counts["usdt_trading_spot_disallowed"],
                          counts["usdt_break_all_spot_permissions"],
                          counts["usdt_break_spot_allowed"],
                          counts["usdt_break_spot_disallowed"]), (514, 1, 2, 1, 1))
        self.assertEqual(r["t0_active_spot_usdt_denominator"], 511)
        self.assertTrue(r["complete_archived_exchangeinfo_t0_eligible_cohort_represented"])
        self.assertNotIn("DENIEDUSDT", [x["symbol"] for x in r["rows"]])
        self.assertNotIn("BREAK1USDT", [x["symbol"] for x in r["rows"]])

    def test_extra_market_symbols_not_in_exchangeinfo_are_not_silent(self):
        blobs, receipts = fake()
        blobs["bookTicker"].append({"symbol": "LISTEDLATERUSDT", "bidPrice": "2",
                                   "askPrice": "2.1", "bidQty": "5", "askQty": "5"})
        r = gate.evaluate(blobs, receipts)
        self.assertEqual(r["excluded_market_symbols_not_in_exchangeinfo"]["bookTicker"],
                         ["LISTEDLATERUSDT"])
        self.assertEqual(len(r["rows"]), 511)
        self.assertNotIn("LISTEDLATERUSDT", [x["symbol"] for x in r["rows"]])

    def test_locked_quotes_and_empty_top_levels_are_rejected(self):
        blobs, receipts = fake()
        for field, value in (("askPrice", "1"), ("bidQty", "0"), ("askQty", "0")):
            bad = copy.deepcopy(blobs)
            bad["bookTicker"][0][field] = value
            with self.assertRaisesRegex(ValueError, "INVALID_BBO"):
                gate.evaluate(bad, receipts)

    def test_zip_byte_tamper_fails_sha(self):
        import tempfile
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp) / "test.zip"
            p.write_bytes(gate.ZIP.read_bytes() + b"x")
            with self.assertRaisesRegex(ValueError, "ZIP_SHA_DRIFT"):
                gate.load_archived(p, gate.RECEIPTS)


if __name__ == "__main__":
    unittest.main()
