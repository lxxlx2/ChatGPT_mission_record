from decimal import Decimal
import unittest

import close_call_fleet as c


class LeaderPivotSolverTests(unittest.TestCase):
    def price_row(self, sweep="957", applied="230", close="229"):
        applied = Decimal(applied)
        return {
            "sweep": int(sweep),
            "applied": applied,
            "close": Decimal(close),
            "lower_limit": (applied * Decimal("0.95")).quantize(Decimal("0.01")),
            "upper_limit": (applied * Decimal("1.05")).quantize(Decimal("0.01")),
        }

    def test_buyer_fee_matches_base_or_clawback(self):
        qty = Decimal("10")
        self.assertEqual(
            c._leader_buyer_fee(qty, Decimal("230"), Decimal("231")),
            Decimal("23.00"),
        )
        self.assertEqual(
            c._leader_buyer_fee(qty, Decimal("210"), Decimal("230")),
            Decimal("200"),
        )

    def test_open_long_candidate_includes_fee_in_required_carry(self):
        row = self.price_row(applied="223.01", close="228.85")
        result = c._leader_open_long_candidate(
            row,
            target_score=Decimal("790.87"),
            target_mark=Decimal("228.85"),
            target_qty=Decimal("46.07"),
        )
        naive = (
            Decimal("790.87")
            - Decimal("46.07") * (Decimal("228.85") - row["lower_limit"])
        )
        self.assertGreater(result["locked_carry_required_before_open"], naive)
        self.assertGreater(result["buyer_fee"], Decimal("0"))

    def test_direct_flip_value_change_is_clawback_limited(self):
        row = self.price_row(applied="230", close="229")
        pre = {
            "score": Decimal("749.24"),
            "mark": Decimal("229.07"),
            "position": Decimal("-43.57"),
            "position_evidence": "consecutive_pnl_slope",
        }
        target = {
            "score": Decimal("790.87"),
            "mark": Decimal("228.85"),
            "position": Decimal("46.07"),
            "position_evidence": "published_position",
        }
        result = c._leader_direct_flip_candidate(row, pre, target)
        self.assertIsNotNone(result)
        self.assertEqual(result["buy_qty"], Decimal("89.64"))
        self.assertGreater(result["cash_required_before_flip"], Decimal("0"))
        self.assertEqual(result["pre_position_evidence"], "consecutive_pnl_slope")

    def test_two_step_requires_open_after_close(self):
        pre = {
            "score": Decimal("749.24"),
            "mark": Decimal("229.07"),
            "position": Decimal("-43.57"),
            "position_evidence": "consecutive_pnl_slope",
        }
        target = {
            "score": Decimal("790.87"),
            "mark": Decimal("228.85"),
            "position": Decimal("46.07"),
            "position_evidence": "published_position",
        }
        row = self.price_row(sweep="957")
        self.assertIsNone(
            c._leader_two_step_pivot_candidate(row, row, pre, target)
        )

    def test_two_step_returns_observed_gap(self):
        pre = {
            "score": Decimal("749.24"),
            "mark": Decimal("229.07"),
            "position": Decimal("-43.57"),
            "position_evidence": "consecutive_pnl_slope",
        }
        target = {
            "score": Decimal("790.87"),
            "mark": Decimal("228.85"),
            "position": Decimal("46.07"),
            "position_evidence": "published_position",
        }
        close_row = self.price_row(sweep="957", applied="230", close="229")
        open_row = self.price_row(sweep="958", applied="229", close="228.80")
        result = c._leader_two_step_pivot_candidate(
            close_row, open_row, pre, target
        )
        self.assertIsNotNone(result)
        self.assertIn("observed_minus_modeled", result)
        self.assertGreaterEqual(result["absolute_gap"], Decimal("0"))
        self.assertEqual(result["close_sweep"], 957)
        self.assertEqual(result["open_sweep"], 958)


if __name__ == "__main__":
    unittest.main()
