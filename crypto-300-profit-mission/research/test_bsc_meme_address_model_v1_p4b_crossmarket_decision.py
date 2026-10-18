"""Source-backed P4-B cross-market negative and positive research controls."""
import copy
import shutil
import tempfile
import unittest
from pathlib import Path

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


    def test_ddac_and_hajimi_unattributed_flows_remain_unknown(self):
        out = self.replay()
        tiers = {row["case"]: row["evidence_tier"] for row in out["selected_owner_rounds"]}
        self.assertEqual(tiers["DDAC_DRAGON"], "OWNER_NATIVE_WINDOW_UNATTRIBUTED_BUY_AND_EXIT_FLOWS")
        self.assertEqual(tiers["8E6B_HAJIMI"], "OWNER_NATIVE_POSITIVE_WITH_UNATTRIBUTED_BUY_ROUTING")
        gaps = out["unattributed_native_fund_flow_disclosures"]
        self.assertEqual(gaps["DDAC_DRAGON"]["native_buy_block_gap_wei"], "17007577000000000")
        self.assertEqual(gaps["DDAC_DRAGON"]["exit_expected_single_event_fee_gap_wei"], "7314989186993731")
        self.assertEqual(gaps["DDAC_DRAGON"]["owner_signed_exit_block_tx_count"], 2)
        self.assertEqual(gaps["8E6B_HAJIMI"]["signed_native_to_pool_WBNB_gap_wei"], "50000000000000000")
        self.assertIn("UNRESOLVED", gaps["DDAC_DRAGON"]["causal_fee_or_transfer_semantics"])

    def test_five_e60_all_frozen_pages_recomputed(self):
        out = self.replay()["outside_cohort_5e60"]
        self.assertTrue(out["in_out_from_source_pages_recomputed"])
        sums = model.reconstructed_5e60_erc20_pages(self.sources, out["wallet"])
        self.assertEqual((sums["inbound_count"], sums["outbound_count"]), (33, 17))
        self.assertEqual(sums["inbound_raw"], "2096771771412964976312348")
        self.assertEqual(sums["outbound_raw"], "2728013687115437116815271")

    def test_consistently_fake_aggregate_and_final_balance_fails_line_replay(self):
        def tamper(s):
            tr = s["5e60_inventory"]["fixed_window_transfers"]
            tr["inbound_raw"] = str(int(tr["inbound_raw"]) + 10 ** 18)
            s["5e60_inventory"]["observations"][1]["rawDecimal"] = str(
                int(s["5e60_inventory"]["observations"][1]["rawDecimal"]) + 10 ** 18)
        with self.assertRaisesRegex(ValueError, "EXTERNAL_PAGE_ROWS_VS_AGGREGATE_MISMATCH"):
            self.replay(tamper)

    def test_fake_original_transfer_row_amount_fails(self):
        def tamper(s):
            row = s["5e60_page2"]["results"]["INBOUND_PAGE2"]["rows"][0]
            row["raw_amount_uint"] = str(int(row["raw_amount_uint"]) + 1)
            row["raw_amount_hex"] = hex(int(row["raw_amount_uint"]))
        with self.assertRaisesRegex(ValueError, "EXTERNAL_PAGE_ROWS_VS_AGGREGATE_MISMATCH"):
            self.replay(tamper)

    def test_missing_last_page_fails(self):
        with self.assertRaisesRegex(ValueError, "EXTERNAL_PAGE_COMPLETENESS_DRIFT"):
            self.replay(lambda s: s["5e60_page4"].update(remaining_pageKey="fake-cursor"))

    def test_duplicated_original_hash_fails(self):
        def tamper(s):
            s["5e60_page2"]["results"]["INBOUND_PAGE2"]["rows"][0]["hash"] = s["5e60_in1"]["rows"][0]["hash"]
        with self.assertRaisesRegex(ValueError, "EXTERNAL_PAGE_DUPLICATE_HASH"):
            self.replay(tamper)

    def test_original_cohort_not_hardcoded(self):
        with self.assertRaisesRegex(ValueError, "FROZEN_23X19_SOURCE_DENOMINATOR_DRIFT"):
            self.replay(lambda s: s["frozen_grid"]["wallets"].pop())

    def test_original_cohort_market_membership(self):
        with self.assertRaisesRegex(ValueError, "FROZEN_SELECTED_OWNER_NOT_IN_23X19"):
            self.replay(lambda s: s["ddac"]["round"].update(exact_CA="0x" + "0" * 40))

    def test_source_file_bytes_modified_in_temporary_copy_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name, _sha in model.SOURCES.values():
                shutil.copyfile(model.RESEARCH / name, root / name)
            file_path = root / model.SOURCES["5e60_page3"][0]
            file_path.write_bytes(file_path.read_bytes() + b" ")
            with self.assertRaisesRegex(ValueError, "SOURCE_BLOB_SHA_MISMATCH:5e60_page3"):
                model.read_all(root)

    def test_unexplained_ddac_source_gap_must_not_be_zeroed(self):
        with self.assertRaisesRegex(ValueError, "UNATTRIBUTED_NATIVE_SOURCE_GAP_DRIFT"):
            self.replay(lambda s: s["ddac"]["round"].update(native_buy_block_debit_wei="791999999999999996"))

    def test_unexplained_hajimi_50milli_bnb_must_not_be_hidden(self):
        with self.assertRaisesRegex(ValueError, "UNATTRIBUTED_NATIVE_SOURCE_GAP_DRIFT"):
            self.replay(lambda s: s["8e6b"]["rounds"][0]["buy"][0].update(WBNB_route_to_pool_wei="5000000000000000000"))


if __name__ == "__main__":
    unittest.main()
