from decimal import Decimal
import unittest

import close_call_fleet as c


class RealizeRedeployLabTests(unittest.TestCase):
    def test_fee_per_qty_matches_clawback_direction(self):
        self.assertEqual(
            c._redeploy_fee_per_qty("buy", Decimal("216.95"), Decimal("228.49")),
            Decimal("11.54"),
        )
        self.assertEqual(
            c._redeploy_fee_per_qty("sell", Decimal("239.77"), Decimal("228.49")),
            Decimal("11.28"),
        )

    def test_close_long_then_open_short_uses_released_flat_cash(self):
        account = {
            "account": "L",
            "pair_id": "p",
            "side": "long",
            "qty": Decimal("40"),
            "entry": Decimal("220"),
            "opening_fee": Decimal("100"),
            "cash": Decimal("1100"),
        }
        sim = c._redeploy_simulate(
            account,
            close=Decimal("230"),
            lower_limit=Decimal("218.50"),
            upper_limit=Decimal("241.50"),
        )
        self.assertTrue(sim["close_feasible"])
        self.assertTrue(sim["open_feasible"])
        self.assertEqual(sim["to_side"], "short")
        self.assertGreater(sim["flat_cash"], Decimal("10000"))
        self.assertGreater(sim["new_qty"], Decimal("0"))

    def test_close_short_then_open_long_can_fail_first_leg(self):
        account = {
            "account": "S",
            "pair_id": "p",
            "side": "short",
            "qty": Decimal("43"),
            "entry": Decimal("240"),
            "opening_fee": Decimal("100"),
            "cash": Decimal("50"),
        }
        sim = c._redeploy_simulate(
            account,
            close=Decimal("228.49"),
            lower_limit=Decimal("216.95"),
            upper_limit=Decimal("239.77"),
        )
        self.assertFalse(sim["close_feasible"])
        self.assertEqual(sim["to_side"], "long")

    def test_redeploy_line_has_expected_direction(self):
        sim = {
            "close_feasible": True,
            "open_feasible": True,
            "score_slope": Decimal("-40"),
            "score_intercept": Decimal("9500"),
        }
        self.assertGreater(
            c._redeploy_line_score(sim, Decimal("220")),
            c._redeploy_line_score(sim, Decimal("230")),
        )

    def test_qty_from_cash_rounds_down_to_cents(self):
        q = c._redeploy_qty_from_cash(
            Decimal("10000"),
            Decimal("220"),
            Decimal("10"),
        )
        self.assertEqual(q, Decimal("43.47"))


if __name__ == "__main__":
    unittest.main()
