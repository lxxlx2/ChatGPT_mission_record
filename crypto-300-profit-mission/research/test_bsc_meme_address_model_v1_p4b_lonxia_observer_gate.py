import copy
import unittest

from bsc_meme_address_model_v1_p4b_lonxia_observer_gate import (
    ROOT, PINS, classify, load, OWNER, TOKEN
)

class OriginalOwnerObserverGate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = load(ROOT)

    def test_approved_source_n_plus_one_does_not_prove_follower_pnl(self):
        row = classify(self.source)
        self.assertEqual(row["source_owner"], OWNER)
        self.assertEqual(row["token"], TOKEN)
        self.assertEqual(row["post_owner_test_block"], 83635777)
        self.assertEqual(row["historical_buy_simulations_success"], 2)
        self.assertEqual(row["actual_subsequent_distinct_signed_market_sells"], 3)
        self.assertEqual(row["observer_first_public_execution_U"], "UNRESOLVED")
        self.assertEqual(row["follower_lag_1_5_15min_PnL"], "UNRESOLVED")
        self.assertEqual((row["P5"],row["production"]), ("BLOCKED","NO_GO"))
        self.assertEqual(len(PINS),2)

    def test_same_block_lookahead_rejected(self):
        changed = copy.deepcopy(self.source)
        changed[0]["token"]["post_owner_observer_test_block"] = 83635776
        with self.assertRaises(ValueError):
            classify(changed)

    def test_simulated_call_cannot_become_real_fill(self):
        changed = copy.deepcopy(self.source)
        changed[0]["historical_pre_sell_buy_quotes"][0]["real_fill"] = True
        with self.assertRaises(ValueError):
            classify(changed)

    def test_sell_transfer_must_be_original_signed_sell_amount(self):
        changed = copy.deepcopy(self.source)
        changed[1]["actual_token_market_sell_events"][1][
            "corresponding_token_erc20_transfer_log"]["data"] = "0x1"
        with self.assertRaises(ValueError):
            classify(changed)

    def test_sell_signer_must_match_original_tx(self):
        changed = copy.deepcopy(self.source)
        changed[1]["actual_token_market_sell_events"][2][
            "transaction_by_hash_raw"]["from"] = OWNER
        with self.assertRaises(ValueError):
            classify(changed)

    def test_missing_sell_must_not_prove_liquidity(self):
        changed = copy.deepcopy(self.source)
        changed[1]["actual_token_market_sell_events"].pop()
        with self.assertRaises(ValueError):
            classify(changed)

    def test_executable_U_or_PnL_promotion_rejected(self):
        for key in ("qualified_public_actionable_buy_AND_sell_U",
                    "follower_PnL_at_1_5_15min"):
            changed = copy.deepcopy(self.source)
            changed[0]["gate"][key] = "QUALIFIED"
            with self.subTest(key=key), self.assertRaises(ValueError):
                classify(changed)

    def test_after_migration_as_bonding_curve_rejected(self):
        changed = copy.deepcopy(self.source)
        changed[0]["historical_helper3_getTokenInfo"]["sampling"][2][
            "liquidityAdded"] = True
        with self.assertRaises(ValueError):
            classify(changed)

    def test_funding_assumption_requires_real_snapshot(self):
        changed = copy.deepcopy(self.source)
        changed[0]["hypothetical_external_caller"]["BNB_balance_wei_at_83635777"]="0"
        with self.assertRaises(ValueError):
            classify(changed)

if __name__ == "__main__":
    unittest.main()
