import unittest
from quote_capacity import (
    QuoteCapacityError, max_input_for_average_impact,
    historical_v2_snapshot_capacity,
)


class CapacityTests(unittest.TestCase):
    def test_snapshot_historical_2_point_5_wbnb(self):
        r = historical_v2_snapshot_capacity(
            block_number=52440325,
            quote_reserve_raw=2500000000000000000,
            token_reserve_raw=1000000000000000000000,
            max_total_impact_bps=100)
        self.assertEqual(r["max_quote_in_raw_at_snapshot"], "18986861092124250")
        self.assertEqual(r["evidence_grade"], "AMM_MATH_ONLY")
        self.assertFalse(r["p0_gate_passed"])
        self.assertEqual(r["real_sell_path"], "UNKNOWN")

    def test_10k_usdt_snapshot(self):
        n = max_input_for_average_impact(10**22, 1600 * 10**18, 100)
        self.assertEqual(n, 75947444368497000075)

    def test_no_arbitrary_trade_size(self):
        r = historical_v2_snapshot_capacity(
            block_number=1, quote_reserve_raw=10000,
            token_reserve_raw=50000, max_total_impact_bps=50)
        self.assertEqual(r["uniform_notional_sellability"], "NOT_SCORABLE")
        self.assertEqual(r["historical_public_available_at"], "UNKNOWN")
        self.assertEqual(r["max_quote_in_raw_at_snapshot"], "25")

    def test_fee_budget_is_not_a_zero_tradeability_claim(self):
        self.assertEqual(max_input_for_average_impact(10**18, 100, 25), 0)
        self.assertEqual(max_input_for_average_impact(10**18, 100, 10), 0)

    def test_exact_integer_boundary(self):
        q = 10**18
        cap = max_input_for_average_impact(q, 10**20, 100)
        fee = 25
        def meets(n):
            # gamma * q / (q + gamma*n) >= 0.99, cross-multiplied
            return (10000-fee)*q*10000 >= (10000-100)*(10000*q+(10000-fee)*n)
        self.assertTrue(meets(cap))
        self.assertFalse(meets(cap+1))

    def test_invalid_types_bounds_and_negative_reserve(self):
        for inval in [True, 0, -1, 1.1, "1000"]:
            with self.subTest(inval=inval), self.assertRaises(QuoteCapacityError):
                max_input_for_average_impact(inval, 100, 100)
        for inval in [False, 0, 10000, "100"]:
            with self.subTest(impact=inval), self.assertRaises(QuoteCapacityError):
                max_input_for_average_impact(100, 200, inval)
        for inval in [True, -1, 10000, 1.2]:
            with self.subTest(fee=inval), self.assertRaises(QuoteCapacityError):
                max_input_for_average_impact(100, 200, 100, swap_fee_bps=inval)
        with self.assertRaises(QuoteCapacityError):
            historical_v2_snapshot_capacity(block_number=-1, quote_reserve_raw=1,
                                             token_reserve_raw=1, max_total_impact_bps=100)


if __name__ == "__main__":
    unittest.main()
