"""Real frozen Stage30/Stage152 evidence and synthetic negative-gate controls."""
import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "monster_v4_economic_readiness.py"
spec = importlib.util.spec_from_file_location("monster_v4_economic_readiness", SCRIPT)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


class TestEconomicReadiness(unittest.TestCase):
    def test_frozen_real_two_cohorts_prove_no_go(self):
        doc = gate.read_report()
        self.assertEqual(doc["verdict"], "FAIL_ECONOMIC_RELEASE_GATE_NO_BUY")
        s = doc["stage30_original_spot_v4"]
        self.assertEqual((s["watch"], s["price_proxy_evaluable"], s["price_proxy_wins"],
                          s["price_proxy_losses"]), (760, 430, 133, 297))
        self.assertEqual(s["historical_funded_300u_10slots_30u_fixed_lot"]["net_usdt_price_proxy"], -79.489406)
        d = doc["stage152_distinct_original305_d1_research"]
        self.assertEqual((d["original_d1_count"], d["pullback_reclaim_price_only_confirmed"],
                          d["no_pullback_no_trade"]), (305, 184, 113))
        self.assertEqual(d["confirmed_24h_illustrative_fee_positive"], 78)
        self.assertLess(d["confirmed_24h_fee_proxy_median_pct"], 0)
        self.assertTrue(doc["source_cohorts_are_different_no_pooling"])
        self.assertTrue(d["do_not_filter_on_future_exit_minute_turnover"])
        self.assertEqual(doc["g4_real_executable_net_profit"], "UNKNOWN")
        self.assertEqual(doc["g6"], "NO_GO")
        self.assertEqual(doc["trading"], "NO_GO")

    def test_tampered_source_bytes_fail_before_economic_analysis(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            for name in gate.BLOBS:
                (folder / name).write_bytes((gate.EVIDENCE / name).read_bytes())
            self.assertEqual(gate.read_report(folder)["g6"], "NO_GO")
            target = folder / gate.STAGE30
            target.write_bytes(target.read_bytes() + b" ")
            with self.assertRaisesRegex(ValueError, "SOURCE_BLOB_DRIFT"):
                gate.read_report(folder)

    def test_wrong_population_denominator_is_not_accepted(self):
        a = gate.source(gate.EVIDENCE, gate.STAGE30)
        b = gate.source(gate.EVIDENCE, gate.STAGE152)
        copya = copy.deepcopy(a)
        copya["all_24h_original_WATCH_20bps"]["wins"] += 1
        with self.assertRaisesRegex(ValueError, "PRICE_COHORT_DRIFT"):
            gate.analyze(copya, b)
        copyb = copy.deepcopy(b)
        copyb["full305"]["states"]["NO_PULLBACK_WITHIN_120M"] += 1
        with self.assertRaisesRegex(ValueError, "D1_COHORT_DRIFT"):
            gate.analyze(a, copyb)

    def test_sign_reversal_is_not_silently_promoted(self):
        a = gate.source(gate.EVIDENCE, gate.STAGE30)
        b = gate.source(gate.EVIDENCE, gate.STAGE152)
        copya = copy.deepcopy(a)
        copya["original_WATCH_funded_fixed_lot_300USDT_10_slots"]["optimistic_unknown_exit_20bps"]["realized_proxy_profit_USDT"] = 1
        with self.assertRaisesRegex(ValueError, "UNEXPECTED_ECONOMIC_RESULT"):
            gate.analyze(copya, b)
        copyb = copy.deepcopy(b)
        copyb["full305"]["confirmed_1440m_complete_unfilled_price_proxy"]["full_illustrative_fee_distribution"]["median_pct"] = "0.01"
        with self.assertRaisesRegex(ValueError, "UNEXPECTED_ECONOMIC_RESULT"):
            gate.analyze(a, copyb)

    def test_no_user_trade_amount_or_fill_is_implied(self):
        doc = gate.read_report()
        self.assertNotIn("trade_amount", doc)
        self.assertEqual(doc["stage152_distinct_original305_d1_research"]["user_notional_and_actual_fee_tier"], "UNKNOWN")
        self.assertEqual(doc["recommendation"], "RESEARCH_ONLY_DO_NOT_TRADE")
        self.assertEqual(doc["stage30_original_spot_v4"]["historical_2x_recall_not_entry_profit"],
                         {"correct_before_first_2x": 30, "later_2x_sample_total": 33})


if __name__ == "__main__":
    unittest.main()
