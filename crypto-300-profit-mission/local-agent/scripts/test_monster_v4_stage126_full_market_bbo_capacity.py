import unittest
from decimal import Decimal
from pathlib import Path
from monster_v4_stage126_full_market_bbo_capacity import analyze, evaluate, dist
from monster_v4_stage124_manual_snapshot_comparison import load


def book(bid="1.00", ask="1.01", bq="20", aq="10", time=9500):
    return {
        "symbol": "普通币USDT", "bidPrice": bid, "askPrice": ask,
        "bidQty": bq, "askQty": aq, "time": time,
    }


class Stage126Test(unittest.TestCase):
    def setUp(self):
        self.symbol = "普通币USDT"
        self.meta = {"symbol": self.symbol, "baseAsset": "普通币", "underlyingType": "COIN"}
        self.tick = {"symbol": self.symbol, "priceChangePercent": "12.5"}

    def evaluate(self, **kwargs):
        return evaluate(self.symbol, self.meta, book(**kwargs), self.tick, 10000)

    def test_true_both_sides_l1_capacity_decimal(self):
        r = self.evaluate()
        self.assertEqual(r["source_status"], "VALID_FRESH_DISPLAYED_BBO")
        self.assertEqual(Decimal(r["bid_display_quote_USDT_proxy"]), Decimal("20.00"))
        self.assertEqual(Decimal(r["ask_display_quote_USDT_proxy"]), Decimal("10.10"))
        self.assertEqual(Decimal(r["visible_roundtrip_buy_quote_USDT_ceiling_proxy"]), Decimal("10.10"))
        self.assertEqual(Decimal(r["two_sided_common_contract_qty_proxy"]), Decimal("10"))
        self.assertEqual(r["crypto_asset_identity"], "UNVERIFIED")
        self.assertEqual(r["actual_bid_ask_fills_or_net"], "UNKNOWN")
        self.assertEqual(r["rolling_24h_ret_cohort_NOT_FUTURE"], "ROLLING_24H_UP_GE10")

    def test_zero_size_censored_not_zero_capacity(self):
        r = self.evaluate(aq="0")
        self.assertEqual(r["source_status"], "ZERO_OR_INCOMPLETE_DISPLAYED_SIZE")
        self.assertIsNone(r["visible_roundtrip_buy_quote_USDT_ceiling_proxy"])

    def test_negative_or_nonfinite_or_crossed_rejected(self):
        for params, status in [
            ({"bq": "-1"}, "INVALID_BBO_PRICE_SIZE_OR_CROSSED"),
            ({"bid": "NaN"}, "INVALID_BBO_NUMBER"),
            ({"ask": "Infinity"}, "INVALID_BBO_NUMBER"),
            ({"bid": "1.02"}, "INVALID_BBO_PRICE_SIZE_OR_CROSSED"),
        ]:
            with self.subTest(params=params):
                self.assertEqual(self.evaluate(**params)["source_status"], status)

    def test_stamp_invalid_and_time_gap(self):
        self.assertEqual(self.evaluate(time="9500")["source_status"], "INVALID_BBO_TIME")
        self.assertEqual(self.evaluate(time=10000+60001)["source_status"], "SOURCE_TIME_GAP_GT_60S")
        self.assertEqual(self.evaluate(time=10000-60001)["source_status"], "SOURCE_TIME_GAP_GT_60S")

    def test_missing_bbo_and_cohort_denominator(self):
        snapshot = {
            "batch": "2026-10-14T09:48:24Z",
            "batch_ms": 10000, "manifest": "synthetic_fixture_not_binance.json",
            "market": {self.symbol: self.meta, "普通币2USDT": {}},
            "active": {self.symbol: self.meta, "普通币2USDT": {"baseAsset": "普通币2"}},
            "bbo": {self.symbol: book()}, "rolling": {self.symbol: self.tick},
            "coverage": {"active_usdt_perpetual_symbols": 2},
        }
        report = analyze(snapshot)
        self.assertEqual(report["full_active_usdt_perpetual_denominator"], 2)
        self.assertEqual(report["bbo_status_counts"]["VALID_FRESH_DISPLAYED_BBO"], 1)
        self.assertEqual(report["bbo_status_counts"]["MISSING_BBO"], 1)
        self.assertEqual(len(report["all_venue_symbol_rows"]), 2)
        self.assertEqual(report["entry_and_future_exit_actual_net"], "UNKNOWN")
        self.assertEqual(report["G4"], "UNKNOWN")

    def test_weak_source_and_percentile(self):
        self.assertEqual(dist([])["n"], 0)
        self.assertEqual(dist([Decimal("1"), Decimal("2"), Decimal("3")])["median"], "2")
        self.assertEqual(self.evaluate()["bbo_batch_minus_event_ms"], 500)

    def test_real_stage123_all_sources_original_population(self):
        manifest = Path(__file__).resolve().parents[2] / "monster" / "evidence" / "monster_stage123_20261014T094824Z_manifest.json"
        real = analyze(load(manifest))
        self.assertEqual(real["all_exchangeinfo_symbols"], 927)
        self.assertEqual(real["full_active_usdt_perpetual_denominator"], 525)
        self.assertEqual(len(real["all_venue_symbol_rows"]), 525)
        self.assertEqual(sum(real["bbo_status_counts"].values()), 525)
        self.assertIn("我踏马来了USDT", {r["symbol"] for r in real["all_venue_symbol_rows"]})
        self.assertEqual(real["independent_other_AI_review"], "NOT_DONE")
        self.assertEqual(real["stage118_historical_model"], "REJECTED_UNCHANGED")


if __name__ == "__main__":
    unittest.main()
