"""Source-backed P4-B cross-market negative and positive research controls."""
import copy
import unittest

import bsc_meme_address_model_v1_p4b_crossmarket_decision as model


class CrossMarketDecisionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources = model.read_all()

    def replay(self, changes=None):
        s = copy.deepcopy(self.sources)
        if changes:
            changes(s)
        return model.build(s)

    def test_frozen_four_markets_five_wallets_six_rounds(self):
        out = self.replay()
        self.assertEqual((out["original_cohort_wallets"], out["original_exact_ca_count"], out["original_cells"]), (23, 19, 437))
        self.assertEqual((len(out["selected_owner_rounds"]), out["selected_wallets"], out["selected_CAs"]), (6, 5, 4))
        self.assertEqual([r["case"] for r in out["selected_owner_rounds"]], [
            "DDAC_DRAGON", "239E_DRAGON_R1", "239E_DRAGON_R2",
            "8E6B_HAJIMI", "A83B_NIULAI", "877AF_MARSCOIN",
        ])

    def test_actual_owner_signs_without_follower_promotion(self):
        out = self.replay()
        self.assertEqual([r["selected_sign"] for r in out["selected_owner_rounds"]],
                         ["NEGATIVE", "NEGATIVE", "POSITIVE", "POSITIVE", "NEGATIVE", "NEGATIVE"])
        for row in out["selected_owner_rounds"]:
            self.assertEqual(row["public_executable_U"], "UNRESOLVED")
            self.assertEqual(row["follower_1_5_15min_net_pnl"], "UNRESOLVED")
            self.assertEqual(row["production"], "NO_GO")
            self.assertEqual(row["wallet_lifetime_pnl"], "UNRESOLVED")
        self.assertTrue(out["no_strategy_success_rate"])

    def test_confirmed_ddac_early_exit_is_not_followable_win(self):
        self.assertEqual(self.replay()["historical_stale_control"]["actual_owner_balance_raw"], "0")
        def mutate(s):
            next(x for x in s["balances"]["historical_exact_CA_and_owner_balance_rows"]
                 if x["wallet"] == s["ddac"]["round"]["owner"] and x["block"] == 83636000)["observed_raw_balance"] = "1"
        with self.assertRaisesRegex(ValueError, "STALE_OWNER_SIGNAL"):
            self.replay(mutate)

    def test_old_inventory_disallows_fake_seven_thousand_profit(self):
        c = self.replay()["outside_cohort_5e60"]
        self.assertNotEqual(c["prior_inventory_open_raw"], "0")
        self.assertEqual(c["realized_net_profit"], "UNRESOLVED_PREEXISTING_COST_BASIS")
        self.assertEqual(c["five_signed_sells_actual_USDT_receipt_raw"], "8399620126582833083485")
        self.assertEqual(c["follower_239e_causality"], "UNRESOLVED")

    def test_cannot_zero_prior_inventory(self):
        with self.assertRaisesRegex(ValueError, "EXTERNAL_TOKEN_INVENTORY_NOT_CLOSED"):
            self.replay(lambda s: s["5e60_inventory"]["observations"][0].update(rawDecimal="0"))

    def test_cannot_change_cash_receipt(self):
        with self.assertRaisesRegex(ValueError, "EXTERNAL_USDT_CASH_RECEIPT"):
            self.replay(lambda s: s["5e60_exit"]["first_five"].update(USDT_received_raw="8399620126582833083486"))

    def test_cannot_invent_token_exit(self):
        with self.assertRaisesRegex(ValueError, "EXTERNAL_FIRST_FIVE_SELL"):
            self.replay(lambda s: s["5e60_exit"]["first_five"].update(Dragon_sold_raw="1"))

    def test_no_hidden_negative_round_to_positive(self):
        with self.assertRaisesRegex(ValueError, "NEGATIVE_CONTROL_SOURCE_DRIFT"):
            self.replay(lambda s: s["negatives"]["rounds"][0].update(economic_sign="POSITIVE_NATIVE_SCOPE"))

    def test_no_cohort_source_switch(self):
        with self.assertRaisesRegex(ValueError, "239E_ROUND_OR_CA_DRIFT"):
            self.replay(lambda s: s["239e"]["rounds"][1].update(exact_CA="0x" + "0" * 40))


if __name__ == "__main__":
    unittest.main()
