"""Pure deterministic D2 liquidity/round-trip simulator tests; no network."""
import importlib.util
import unittest
from decimal import Decimal
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/monster_v4_d2.py"
spec = importlib.util.spec_from_file_location("monster_v4_d2", SCRIPT)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

RULE = {"symbol": "TESTUSDT", "status": "TRADING",
        "quoteAsset": "USDT", "isSpotTradingAllowed": True,
        "filters": [
            {"filterType": "MARKET_LOT_SIZE", "minQty": "0",
             "maxQty": "100000", "stepSize": "0"},
            {"filterType": "LOT_SIZE", "minQty": "1",
             "maxQty": "100000", "stepSize": "1"},
            {"filterType": "NOTIONAL", "minNotional": "5",
             "maxNotional": "100000"}]}
BOOK = {"lastUpdateId": 42,
        "bids": [["1.00", "100"], ["0.99", "200"]],
        "asks": [["1.01", "100"], ["1.02", "200"]]}


class MonsterD2Tests(unittest.TestCase):
    def calc(self, rule=None, book=None, fee="10", amount="30"):
        return m.evaluate_spot_execution(rule or RULE, book or BOOK, 1800000000000,
                                         budget_usdt=amount, assumed_fee_bps=fee)

    def test_full_30_usdt_fill_with_fees_and_lot_rounding(self):
        x = self.calc()
        self.assertTrue(x["snapshot_executable_proxy"])
        self.assertTrue(x["research_liquidity_gate"])
        self.assertEqual(x["fee_source"], "USER_UNCONFIRMED_SCENARIO")
        self.assertEqual(x["base_sellable_after_fee_and_step"], "29")
        self.assertEqual(x["buy_quote_unfilled"], "0")
        self.assertGreater(x["instant_roundtrip_loss_usdt"], 0)
        self.assertEqual(x["classification"], "RESEARCH_LIQUIDITY_NOT_BUY")

    def test_insufficient_asks_not_marked_executable(self):
        x = self.calc(book={"lastUpdateId": 4,
                             "bids": [["1", "100"]],
                             "asks": [["1.01", "2"]]})
        self.assertFalse(x["snapshot_executable_proxy"])
        self.assertFalse(x["research_liquidity_gate"])
        self.assertGreater(Decimal(x["buy_quote_unfilled"]), 25)

    def test_insufficient_exit_bids_not_marked_executable(self):
        x = self.calc(book={"lastUpdateId": 4,
                             "bids": [["1", "1"]],
                             "asks": [["1.01", "100"]]})
        self.assertFalse(x["snapshot_executable_proxy"])
        self.assertGreater(Decimal(x["sell_base_unfilled"]), 20)

    def test_expensive_spread_fails_research_gate_but_may_fill(self):
        x = self.calc(book={"lastUpdateId": 1,
                             "bids": [["0.80", "200"]],
                             "asks": [["1.01", "200"]]})
        self.assertTrue(x["snapshot_executable_proxy"])
        self.assertFalse(x["research_liquidity_gate"])
        self.assertGreater(x["spread_bps"], 100)

    def test_crossed_or_unsorted_book_rejected(self):
        for book in (
            {"lastUpdateId": 42, "bids": [["1.02", "100"]],
             "asks": [["1.01", "100"]]},
            {"lastUpdateId": 42, "bids": [["1", "100"], ["1.01", "90"]],
             "asks": [["1.02", "100"]]},
            {"lastUpdateId": 42, "bids": [["1", "100"]],
             "asks": [["1.02", "100"], ["1.01", "90"]]},
        ):
            with self.subTest(book=book), self.assertRaises(ValueError):
                self.calc(book=book)

    def test_bad_data_cannot_claim_real_trade(self):
        for x in ("NaN", "-3", "0", "Infinity"):
            with self.subTest(x=x), self.assertRaises(ValueError):
                self.calc(book={"lastUpdateId": 12,
                                "bids": [[x, "100"]],
                                "asks": [["2", "100"]]})
        with self.assertRaisesRegex(ValueError, "NOT_ACTIVE_USDT_SPOT"):
            self.calc(rule={**RULE, "status": "BREAK"})

    def test_tiny_trade_below_notional_not_executable(self):
        x = self.calc(amount="2")
        self.assertFalse(x["notional_pass"])
        self.assertFalse(x["snapshot_executable_proxy"])

    def test_notional_lot_ceiling_blocked(self):
        filters=[dict(f) for f in RULE["filters"]]
        filters[0]["maxQty"]="2"
        r={**RULE,"filters":filters}
        x=self.calc(rule=r)
        self.assertFalse(x["min_qty_pass"])
        self.assertFalse(x["snapshot_executable_proxy"])

    def test_fee_scenario_is_explicit_and_cost_increases(self):
        cheap=self.calc(fee="0")
        expensive=self.calc(fee="25")
        self.assertLess(cheap["instant_roundtrip_loss_usdt"],
                        expensive["instant_roundtrip_loss_usdt"])
        with self.assertRaisesRegex(ValueError, "INVALID_FEE_BPS"):
            self.calc(fee="10000")

    def test_default_missing_rules_not_treated_as_zero(self):
        with self.assertRaisesRegex(ValueError,"UNKNOWN_NOTIONAL_FILTER"):
            self.calc(rule={**RULE, "filters": RULE["filters"][:-1]})
        with self.assertRaisesRegex(ValueError,"UNKNOWN_MARKET_LOT_FILTER"):
            self.calc(rule={**RULE, "filters": RULE["filters"][-1:]})


if __name__ == "__main__":
    unittest.main()
