from decimal import Decimal
import unittest

import close_call_fleet as c


class CounterpartyRedeployTests(unittest.TestCase):
    def account(self, name, side, qty, entry, fee, cash):
        return {
            "pair_id": name.rsplit("-", 1)[0],
            "account": name,
            "side": side,
            "qty": Decimal(qty),
            "entry": Decimal(entry),
            "opening_fee": Decimal(fee),
            "cash": Decimal(cash),
            "evidence_mode": "visible_settled",
            "source": "reserve",
        }

    def trio(self):
        target = self.account(
            "DENSE-V3-01619-L", "long", "41.28", "216.87",
            "459.8592", "587.7472",
        )
        donor_a = self.account(
            "DENSE-V3-01620-S", "short", "41.28", "232.84",
            "199.3824", "188.9824",
        )
        donor_b = self.account(
            "DENSE-V3-01621-S", "short", "41.28", "232.84",
            "199.3824", "188.9824",
        )
        return target, donor_a, donor_b

    def test_reconstructed_state_matches_baseline_score(self):
        target, _a, _b = self.trio()
        state = c._cp_state_from_account(target)
        for s in (Decimal("220"), Decimal("230"), Decimal("245")):
            self.assertEqual(
                c._cp_score(state, s),
                c._redeploy_baseline_score(target, s),
            )

    def test_exact_visible_trio_settles_both_legs(self):
        target, donor_a, donor_b = self.trio()
        sim = c._cp_simulate_trio(
            target,
            donor_a,
            donor_b,
            close=Decimal("233.81"),
            upper_limit=Decimal("242.11"),
        )
        self.assertTrue(sim["leg1_settled"])
        self.assertTrue(sim["leg2_settled"])
        self.assertEqual(sim["leg2_qty"], Decimal("40.89"))
        self.assertEqual(c._cp_position(sim["target"]), Decimal("-40.89"))
        self.assertEqual(c._cp_position(sim["donor_a"]), Decimal("0"))
        self.assertEqual(c._cp_position(sim["donor_b"]), Decimal("-0.39"))
        self.assertEqual(sim["target_flat_score"], Decimal("239.4240"))

    def test_leg_one_uses_both_accounts_pre_apply_cash(self):
        target, donor_a, _donor_b = self.trio()
        maker = c._cp_state_from_account(target)
        taker = c._cp_state_from_account(donor_a)
        trade = c._cp_sell_trade(
            maker,
            taker,
            Decimal("41.28"),
            Decimal("242.11"),
            Decimal("233.81"),
        )
        self.assertTrue(trade["settled"])
        self.assertEqual(trade["maker_fee"], Decimal("342.6240"))
        self.assertEqual(trade["taker_fee"], Decimal("99.943008"))
        self.assertLessEqual(trade["maker_need"], Decimal("587.7472"))
        self.assertLessEqual(trade["taker_need"], Decimal("188.9824"))

    def test_failed_first_leg_preserves_all_original_positions(self):
        target, donor_a, donor_b = self.trio()
        donor_a["cash"] = Decimal("1")
        sim = c._cp_simulate_trio(
            target,
            donor_a,
            donor_b,
            close=Decimal("233.81"),
            upper_limit=Decimal("242.11"),
        )
        self.assertFalse(sim["leg1_settled"])
        self.assertFalse(sim["leg2_settled"])
        self.assertEqual(c._cp_position(sim["target"]), Decimal("41.28"))
        self.assertEqual(c._cp_position(sim["donor_a"]), Decimal("-41.28"))
        self.assertEqual(c._cp_position(sim["donor_b"]), Decimal("-41.28"))

    def test_second_leg_never_forces_donor_b_long(self):
        target, donor_a, donor_b = self.trio()
        sim = c._cp_simulate_trio(
            target,
            donor_a,
            donor_b,
            close=Decimal("233.81"),
            upper_limit=Decimal("242.11"),
        )
        self.assertLessEqual(sim["leg2_qty"], Decimal("41.28"))
        self.assertLessEqual(c._cp_position(sim["donor_b"]), Decimal("0"))

    def test_second_leg_respects_donor_fee_cash(self):
        target, donor_a, donor_b = self.trio()
        donor_b["cash"] = Decimal("10")
        sim = c._cp_simulate_trio(
            target,
            donor_a,
            donor_b,
            close=Decimal("233.81"),
            upper_limit=Decimal("242.11"),
        )
        self.assertTrue(sim["leg1_settled"])
        self.assertTrue(sim["leg2_settled"])
        # Buyer fee is 1% * 242.11 = 2.4211 per contract.
        self.assertEqual(sim["leg2_qty"], Decimal("4.13"))


if __name__ == "__main__":
    unittest.main()
