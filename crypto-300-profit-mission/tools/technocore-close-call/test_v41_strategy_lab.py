from decimal import Decimal
import unittest

import close_call_fleet as c


class V41StrategyLabTests(unittest.TestCase):
    def samples(self):
        applied = Decimal("230")
        moves = [
            "-0.020", "-0.015", "-0.012", "-0.010", "-0.009", "-0.007",
            "-0.005", "-0.004", "-0.003", "-0.002", "-0.001", "0.000",
            "0.001", "0.002", "0.003", "0.004", "0.005", "0.007",
            "0.009", "0.010", "0.012", "0.015", "0.018", "0.020",
        ]
        return [
            {
                "n": i,
                "applied": applied,
                "close": applied * (Decimal("1") + Decimal(move)),
                "move": Decimal(move),
            }
            for i, move in enumerate(moves, 1)
        ]

    def test_quantile_grid_widens(self):
        samples = self.samples()
        first = c._v41_stress_band(samples, 1)
        last = c._v41_stress_band(samples, 8)
        self.assertGreaterEqual(first["low_move"], last["low_move"])
        self.assertLessEqual(first["high_move"], last["high_move"])

    def test_proposed_plan_survives_declared_stress_closes(self):
        pr = {"px": Decimal("231.02"), "raw": {}}
        samples = self.samples()
        for copy_no in range(1, 9):
            plan = c.dense_v41_plan_copy(pr, copy_no, samples)
            self.assertGreaterEqual(plan["long_qty"], plan["short_qty"])
            self.assertGreaterEqual(plan["short_qty"], Decimal("0.10"))
            for close in plan["stress_closes"]:
                sim = c._v41_simulate_pair(
                    plan["low"],
                    plan["high"],
                    plan["long_qty"],
                    plan["short_qty"],
                    close,
                )
                self.assertTrue(sim["long_settled"], (copy_no, close, sim))
                self.assertTrue(sim["short_settled"], (copy_no, close, sim))

    def test_first_copy_is_more_aggressive_than_full_range_copy(self):
        pr = {"px": Decimal("231.02"), "raw": {}}
        samples = self.samples()
        first = c.dense_v41_plan_copy(pr, 1, samples)
        last = c.dense_v41_plan_copy(pr, 8, samples)
        self.assertGreaterEqual(first["long_qty"], last["long_qty"])
        self.assertGreaterEqual(first["short_qty"], last["short_qty"])

    def test_pair_can_keep_long_when_short_voids(self):
        sim = c._v41_simulate_pair(
            Decimal("219.47"),
            Decimal("233.34"),
            Decimal("42.00"),
            Decimal("60.00"),
            Decimal("231.00"),
        )
        self.assertTrue(sim["long_settled"])
        self.assertFalse(sim["short_settled"])

    def test_current_v4_and_v41_backtest_are_both_reported(self):
        pr = {"px": Decimal("231.02"), "raw": {}}
        report = c.dense_v41_backtest(pr, self.samples())
        self.assertIn("current_v4", report)
        self.assertIn("proposed_v41", report)
        self.assertEqual(report["current_v4"]["samples"], 24)
        self.assertEqual(report["proposed_v41"]["samples"], 24)


if __name__ == "__main__":
    unittest.main()
