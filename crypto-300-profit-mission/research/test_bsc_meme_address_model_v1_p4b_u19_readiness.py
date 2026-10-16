#!/usr/bin/env python3
"""Adversarial tests for the P4-B 19-market source-only actionable-U gate."""
import copy
import unittest
import bsc_meme_address_model_v1_p4b_u19_readiness as gate

class P4BU19ReadinessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = gate.load()

    def checked(self, edit):
        src = copy.deepcopy(self.source)
        edit(src)
        with self.assertRaises(ValueError):
            gate.census(src)

    def test_all_19_and_23x19_retained(self):
        out = gate.census(self.source)
        self.assertEqual(len(out["rows"]), 19)
        self.assertEqual(out["summary"]["wallet_CA_cells"], 437)
        self.assertEqual(out["summary"]["original_wallets"], 23)
        self.assertEqual(len({r["exact_CA"] for r in out["rows"]}), 19)

    def test_witnesses_not_mislabeled_as_19_executable_U(self):
        out = gate.census(self.source)
        self.assertEqual(out["summary"]["early_owner_signed_witnesses_inside_cohort"], 1)
        self.assertEqual(out["summary"]["early_owner_signed_witnesses_external_controls"], 2)
        self.assertEqual(out["summary"]["verified_global_public_executable_U"], 0)
        self.assertEqual(out["summary"]["verified_follower_lag_returns"], 0)
        self.assertEqual(out["summary"]["PRODUCTION"], "NO_GO")
        self.assertTrue(all(x["qualified_global_first_executable_U"] == "UNRESOLVED"
                            for x in out["rows"]))
        self.assertTrue(all(x["historical_V2_math_quote_block_NOT_SAME_AS_EARLIEST"] >
                            x["earliest_proven_scoped_pool_block_NOT_GLOBAL_U"]
                            for x in out["rows"]))

    def test_delete_CA_rejected(self):
        self.checked(lambda d: d["pools"]["rows"].pop())

    def test_duplicate_CA_rejected(self):
        self.checked(lambda d: d["market"]["rows"][0].update(
            exact_CA=d["market"]["rows"][1]["exact_CA"]))

    def test_delete_wallet_rejected(self):
        self.checked(lambda d: d["wallet_grid"]["wallets"].pop())

    def test_drop_wallet_cell_rejected(self):
        self.checked(lambda d: d["wallet_grid"]["wallets"][0]
                     ["early_owner_trade_statuses"].pop())

    def test_fake_math_quote_same_time_as_early_pool_rejected(self):
        self.checked(lambda d: d["quotes"]["rows"][0].update(
            historical_read_block=d["pools"]["rows"][0]["scoped_first_active_block"]))

    def test_source_promoted_to_U_rejected(self):
        self.checked(lambda d: d["market"]["rows"][0].update(
            actual_global_observer_market_U="CONFIRMED"))

    def test_native_transfer_as_early_signed_purchase_rejected(self):
        self.checked(lambda d: d["market"]["rows"][0].update(
            earlier_actual_signed_purchase_evidence="FOUR_MEME_SIGNED_EARLY_BUY"))

    def test_forged_external_signer_cohort_membership_rejected(self):
        self.checked(lambda d: d["market"]["rows"][15].update(
            selected_signer_is_in_original_23=True))

    def test_false_historical_trade_profit_rejected(self):
        self.checked(lambda d: d["market"]["rows"][14].update(
            historical_signed_roundtrip_PnL="CONFIRMED_POSITIVE"))

    def test_mixed_CA_token_identity_rejected(self):
        self.checked(lambda d: d["quotes"]["rows"][14].update(token="MARSCOIN"))

    def test_dragon_read_only_probe_called_real_fill_rejected(self):
        self.checked(lambda d: d["dragon_probe"]["historical_pre_sell_buy_quotes"][0].update(
            real_fill=True))

    def test_later_real_sales_called_follower_roundtrip_rejected(self):
        self.checked(lambda d: d["dragon_sells"]["gate"].update(
            same_wallet_buy_then_sell_actual_follower_roundtrip="CONFIRMED"))

    def test_read_source_is_byte_pinned(self):
        self.assertEqual(len(gate.SOURCES), 7)
        self.assertEqual(gate.census(gate.load())["summary"]["exact_CAs"], 19)

if __name__ == "__main__":
    unittest.main()
