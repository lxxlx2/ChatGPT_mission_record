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
        self.assertEqual(row["sampled_block_83636000_distinct_signed_dragon_sells"], 3)
        self.assertEqual(row["observer_first_public_execution_U"], "UNRESOLVED")
        self.assertEqual(row["follower_lag_1_5_15min_PnL"], "UNRESOLVED")
        self.assertEqual((row["P5"],row["production"]), ("BLOCKED","NO_GO"))
        self.assertEqual(len(PINS),3)
        self.assertEqual(row["sale_signers_in_frozen_23"],2)
        self.assertEqual(row["sale_signers_outside_frozen_23"],1)
        self.assertEqual(row["sampled_block_total_manager_sales_all_CAs"],4)
        self.assertEqual(row["sampled_block_dragon_manager_outgoing_transfers"],2)
        self.assertEqual(row["observed_buy_to_sale_block_timestamp_diff_milliseconds"],"100800")
        self.assertEqual(row["DDAC_initial_buy_unattributed_value_residual_wei"],"8000000000000004")

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

    def test_one_frozen_seller_must_not_be_labeled_external(self):
        changed=copy.deepcopy(self.source)
        changed[2]["seller_frozen_sample_membership"][0]["member_of_frozen_23"]=False
        with self.assertRaises(ValueError):
            classify(changed)

    def test_earliest_observed_owner_cannot_be_same_as_market_seller(self):
        changed=copy.deepcopy(self.source)
        changed[2]["seller_frozen_sample_membership"][0]["wallet"]=OWNER
        with self.assertRaises(ValueError):
            classify(changed)

    def test_timestamp_milliseconds_are_source_verified(self):
        changed=copy.deepcopy(self.source)
        changed[2]["block_headers_selected_RPC_fields"][0]["milliTimestamp"]="0x1"
        with self.assertRaises(ValueError):
            classify(changed)

    def test_fabricated_100p8_second_elapsed_rejected(self):
        changed=copy.deepcopy(self.source)
        changed[2]["block_time_math"]["interval_in_milliseconds"]="100000"
        with self.assertRaises(ValueError):
            classify(changed)

    def test_sampled_block_other_ca_sale_not_deleted(self):
        changed=copy.deepcopy(self.source)
        changed[2]["sampled_block_exact_83636000"]["manager_all_TokenSale_logs"].pop()
        with self.assertRaises(ValueError):
            classify(changed)

    def test_sampled_block_buy_side_token_transfer_not_deleted(self):
        changed=copy.deepcopy(self.source)
        changed[2]["sampled_block_exact_83636000"]["dragon_all_ERC20_Transfer_logs"].pop(0)
        with self.assertRaises(ValueError):
            classify(changed)

    def test_receipt_status_downgrade_rejected(self):
        changed=copy.deepcopy(self.source)
        changed[2]["sampled_block_exact_83636000"]["three_sale_receipt_excerpt"][0]["status"]="0x0"
        with self.assertRaises(ValueError):
            classify(changed)

    def test_ddac_native_residual_cannot_be_relabelled_as_closed(self):
        changed=copy.deepcopy(self.source)
        changed[2]["DDAC_initial_0p8_BNB_payment"]["attribution"]="ROUTER_FEE_CONFIRMED"
        with self.assertRaises(ValueError):
            classify(changed)

    def test_disabled_buy_requires_revert_payload(self):
        changed=copy.deepcopy(self.source)
        changed[2]["migration_disabled_probe"]["revert_payload"]="0x"
        with self.assertRaises(ValueError):
            classify(changed)

    def test_hidden_sample_membership_claim_rejected(self):
        changed=copy.deepcopy(self.source)
        changed[2]["seller_frozen_sample_membership"][1]["source_wallet_index"]=None
        with self.assertRaises(ValueError):
            classify(changed)

    def test_premature_follow_profit_claim_rejected_by_correction(self):
        changed=copy.deepcopy(self.source)
        changed[2]["gate"]["follower_1_5_15_min_profit"]="PROFIT"
        with self.assertRaises(ValueError):
            classify(changed)

if __name__ == "__main__":
    unittest.main()
