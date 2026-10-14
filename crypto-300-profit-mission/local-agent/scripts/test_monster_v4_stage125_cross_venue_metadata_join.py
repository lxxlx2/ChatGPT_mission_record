import importlib.util
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("monster_v4_stage125_cross_venue_metadata_join.py")
spec = importlib.util.spec_from_file_location("monster_stage125", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def source(rows, time):
    return {"structuredContent": {"serverTime": time, "symbols": rows}}


def usd(name, base, kind="COIN"):
    return {"symbol": name, "status": "TRADING", "contractType": "PERPETUAL", "quoteAsset": "USDT", "baseAsset": base, "pair": base+"USDT", "underlyingType": kind}


def spot(name, base, status="TRADING", allowed=True, quote="USDT"):
    return {"symbol": name, "status": status, "quoteAsset": quote, "baseAsset": base, "isSpotTradingAllowed": allowed}


class Stage125Test(unittest.TestCase):
    def setUp(self):
        self.f = source([usd("ONEUSDT", "ONE"), usd("1000PEPEUSDT", "1000PEPE"), usd("停牌USDT", "停牌")], 10000)
        self.s = source([spot("ONEUSDT", "ONE"), spot("PEPEUSDT", "PEPE"), spot("停牌USDT", "停牌", status="BREAK")], 20000)

    def test_all_rows_and_unverified_identity(self):
        output = module.assess(self.f, self.s)
        self.assertEqual(output["usdm_active_usdt_perpetual"], 3)
        self.assertEqual(output["exact_spot_usdt_metadata_trading_unverified"], 1)
        self.assertEqual(output["exact_spot_usdt_not_trading_or_disabled"], 1)
        self.assertEqual(output["no_exact_spot_usdt_symbol"], 1)
        self.assertEqual(output["eligible_buy_recommendations"], 0)
        self.assertTrue(all(not x["spot_execution_confirmed"] for x in output["full_cohort"]))
        self.assertEqual(output["full_cohort"][0]["usdm_symbol"], "1000PEPEUSDT")

    def test_no_inference_by_token_prefix(self):
        output = module.assess(self.f, self.s)
        row = next(x for x in output["full_cohort"] if x["usdm_symbol"] == "1000PEPEUSDT")
        self.assertIsNone(row["exact_spot_usdt_symbol"])
        self.assertEqual(row["other_same_base_spot_trading_pairs_diagnostic_only"], [])

    def test_duplicate_usdm_rejected(self):
        self.f["structuredContent"]["symbols"].append(usd("ONEUSDT", "ONE"))
        with self.assertRaisesRegex(ValueError, "duplicate symbol"):
            module.assess(self.f, self.s)

    def test_bad_source_rejected(self):
        del self.s["structuredContent"]["serverTime"]
        with self.assertRaisesRegex(ValueError, "serverTime"):
            module.assess(self.f, self.s)

    def test_universe_without_current_pairs_rejected(self):
        for row in self.f["structuredContent"]["symbols"]:
            row["status"] = "CLOSE"
        with self.assertRaisesRegex(ValueError, "no active"):
            module.assess(self.f, self.s)


if __name__ == "__main__":
    unittest.main()
