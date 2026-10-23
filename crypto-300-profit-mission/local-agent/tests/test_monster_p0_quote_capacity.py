import unittest
from mission_agent.early.quote_capacity import (
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
        self.assertEqual(r["max_quote_in_raw_at_snapshot"], "18734335839598997")
        self.assertEqual(r["evidence_grade"], "AMM_MATH_ONLY")
        self.assertFalse(r["p0_gate_passed"])
        self.assertEqual(r["real_sell_path"], "UNKNOWN")

    def test_10k_usdt_snapshot(self):
        n = max_input_for_average_impact(10**22, 1600 * 10**18, 100)
        self.assertEqual(n, 74937343358395989974)

    def test_no_arbitrary_trade_size(self):
        r = historical_v2_snapshot_capacity(
            block_number=1, quote_reserve_raw=10000,
            token_reserve_raw=50000, max_total_impact_bps=50)
        self.assertEqual(r["uniform_notional_sellability"], "NOT_SCORABLE")
        self.assertEqual(r["historical_public_available_at"], "UNKNOWN")
        self.assertEqual(r["max_quote_in_raw_at_snapshot"], "24")

    def test_fee_budget_is_not_a_zero_tradeability_claim(self):
        self.assertEqual(max_input_for_average_impact(10**18, 100, 25), 0)
        self.assertEqual(max_input_for_average_impact(10**18, 100, 10), 0)

    def test_exact_integer_boundary(self):
        q = 10**18
        cap = max_input_for_average_impact(q, 10**20, 100)
        fee = 25
        def meets(n):
            # effective execution-price premium <= 100bps, exact fraction.
            return 10000 * (fee*q + (10000-fee)*n) <= 100 * (10000-fee)*q
        self.assertTrue(meets(cap))
        self.assertFalse(meets(cap+1))

    def test_same_price_premium_definition_as_entry_impact(self):
        from mission_agent.early.entry_impact import impact_microbps
        reserve = 10**18
        cap = max_input_for_average_impact(reserve, 10**24, 100)
        self.assertLessEqual(impact_microbps(str(cap), str(reserve)), 100*10**6)
        self.assertGreater(impact_microbps(str(cap+1), str(reserve)), 100*10**6)

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


class FrozenCohortCapacityTests(unittest.TestCase):
    def _fixture(self):
        identities = [dict(rank=i, token_ca="0x" + format(i, "040x"),
                           pool="0x" + format(i+100, "040x"),
                           quote_asset="0x" + "b"*40)
                      for i in range(1, 31)]
        reserve = dict(identities[0], first_confirmed_depth_block=10,
                       asof_end_block=11,
                       quote_reserve_raw_at_next_block_end=str(2 * 10**18),
                       token_reserve_raw_at_next_block_end=str(100 * 10**18),
                       token_reserve_positive=True)
        return {
            "bsc_v2_p0_current_frozen30_p0_gate_matrix_20261020": {"rows": identities},
            "bsc_v2_p0_all24_next_block_reserve_source_read_20261020": {"rows": [reserve]},
        }

    def test_identity_preserved_unknowns_never_become_zeros(self):
        from mission_agent.early.quote_capacity import frozen30_capacity_audit
        data = self._fixture()
        got = frozen30_capacity_audit(data, max_total_impact_bps=100)
        self.assertEqual((got["frozen_population"], got["available_end_block_snapshots"],
                          got["missing_reserve_snapshots"]), (30, 1, 29))
        self.assertEqual(got["rows"][0]["capacity_status"], "AMM_MATH_ONLY")
        self.assertIsNone(got["rows"][1]["max_quote_in_raw_at_snapshot"])
        self.assertEqual(got["rows"][1]["capacity_status"],
                         "NOT_SCORABLE_NO_HISTORIC_RESERVES")
        self.assertFalse(got["p0_gate_passed"])
        data["future_90d_outcomes"] = {"win": "10x"}
        self.assertEqual(got, frozen30_capacity_audit(data, max_total_impact_bps=100))

    def test_rejects_unmatched_pool_duplicate_rank_and_wrong_snapshot_block(self):
        from mission_agent.early.quote_capacity import (
            QuoteCapacityError, frozen30_capacity_audit)
        data = self._fixture()
        data["bsc_v2_p0_all24_next_block_reserve_source_read_20261020"]["rows"][0]["pool"] = "0x"+"f"*40
        with self.assertRaisesRegex(QuoteCapacityError, "IDENTITY_NOT_FROZEN"):
            frozen30_capacity_audit(data, max_total_impact_bps=100)
        data = self._fixture()
        reserves = data["bsc_v2_p0_all24_next_block_reserve_source_read_20261020"]["rows"]
        reserves.append(dict(reserves[0]))
        with self.assertRaisesRegex(QuoteCapacityError, "RANK_DUPLICATE"):
            frozen30_capacity_audit(data, max_total_impact_bps=100)
        data = self._fixture()
        data["bsc_v2_p0_all24_next_block_reserve_source_read_20261020"]["rows"][0]["asof_end_block"] = 9
        with self.assertRaisesRegex(QuoteCapacityError, "SNAPSHOT_SCOPE"):
            frozen30_capacity_audit(data, max_total_impact_bps=100)
