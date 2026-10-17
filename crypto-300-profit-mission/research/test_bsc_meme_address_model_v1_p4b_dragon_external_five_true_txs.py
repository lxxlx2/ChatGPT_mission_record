#!/usr/bin/env python3
"""Negative controls: selected post-exit real trades do not establish profitable DDAC copy."""
import copy
import shutil
import tempfile
import unittest
from pathlib import Path
import bsc_meme_address_model_v1_p4b_dragon_external_five_true_txs as study

class DragonFiveActualExternalTxTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.docs=study.load()

    def fails(self,edit,error):
        d=copy.deepcopy(self.docs)
        edit(d)
        with self.assertRaisesRegex(ValueError,error):
            study.build(d)

    def test_existing_true_two_positive_closed_selected_eoa_and_one_exit_unknown(self):
        actual=study.build(self.docs)
        self.assertEqual(actual["cohort"]["old_cells"],437)
        self.assertEqual(actual["cohort"]["D503_actual_closed_rounds"],2)
        self.assertEqual(actual["cohort"]["E11B_selected_buy_only_exit_UNKNOWN"],1)
        self.assertEqual(actual["cohort"]["public_causal_follower_rounds_PROVEN"],0)
        self.assertEqual(actual["D503_two_selected_native_positive_BNB_delta_wei"],"61218026868859435")
        self.assertEqual([z["selected_two_block_EOA_BNB_delta_wei"] for z in
            actual["D503_real_selected_two_block_native_movements"]],
            ["24264878154473742","36953148714385693"])
        self.assertEqual(actual["D503_approve_plus_sell_verified_GAS_fee_wei_for_each_round"],
            ["516314000000000","516314000000000"])
        self.assertFalse(actual["D503_buy_receipt_gasUsed_verified"])
        self.assertTrue(actual["E11B_unresolved_exit_at_last_bounded_83636127"])
        self.assertTrue(actual["DDAC_original_closed_before_both_external_buyers"])
        self.assertFalse(actual["can_prove_causal_copy_of_DDAC"])
        self.assertEqual(actual["P5"],"BLOCKED")

    def test_real_first_D503_buy_has_higher_native_input_than_gas_limit(self):
        actual=study.build(self.docs)
        first=actual["observations"][0]
        self.assertEqual(first["signed_native_tx_value_wei"],"190000000000000000")
        self.assertEqual(first["signed_gas_price_wei_per_unit"],"3000000000")
        self.assertEqual(first["signed_gas_LIMIT_units"],"600000")
        self.assertEqual(first["actual_gasUsed_units"],"UNRESOLVED")

    def test_second_D503_buy_gas_price_changed_and_not_receipt_gas(self):
        result=study.build(self.docs)
        second=result["observations"][2]
        self.assertEqual(second["signed_native_tx_value_wei"],"220000000000000000")
        self.assertEqual(second["signed_gas_price_wei_per_unit"],"7000000000")
        self.assertEqual(second["actual_gasUsed_units"],"UNRESOLVED")

    def test_E11B_different_route_after_DDAC_exit_stays_exit_unknown(self):
        result=study.build(self.docs)
        e=result["observations"][-1]
        self.assertEqual(e["block"],83636000)
        self.assertEqual(e["signed_native_tx_value_wei"],"12000000000000000")
        self.assertEqual(e["signed_gas_price_wei_per_unit"],"57531543")
        self.assertTrue(result["E11B_unresolved_exit_at_last_bounded_83636127"])

    def test_cannot_make_truncated_buy_receipt_complete(self):
        self.fails(lambda d:d["readback"]["results"][0].update(
            receipt_gas_used="290567"),"SAME_FIVE_ORIGINAL_TX_IDENTITIES")

    def test_buy_gas_price_tampering_rejected(self):
        self.fails(lambda d:d["readback"]["results"][2]["returned"].update(
            gasPrice="0x1"),"ACTUAL_ROUTING_AND_REAL_GAS_PRICE_FIELDS")

    def test_stake_amount_cannot_switch_from_original_signed_source(self):
        self.fails(lambda d:d["readback"]["results"][0]["returned"].update(
            value="0x1"),"SAME_FIVE_ORIGINAL_TX_IDENTITIES")

    def test_swap_E11B_owner_to_D503_not_allowed(self):
        self.fails(lambda d:d["readback"]["results"][4]["returned"].update(
            **{"from":"0x"+"a"*40}),"SAME_FIVE_ORIGINAL_TX_IDENTITIES")

    def test_real_E11B_token_balance_holding_cannot_be_erased(self):
        self.fails(lambda d:d["original_inventory"]["samples"][-1].update(
            token_raw="0"),"FULL_HISTORIC_TOKEN_INVENTORY_AND_EXIT_UNKNOWN")

    def test_fake_DDAC_original_exit_after_D503_buy_rejected(self):
        self.fails(lambda d:d["old_ddac"]["round"].update(
            exit_block=83636001),"OLD_EARLY_OWNER_ALREADY_EXITED")

    def test_blockscout_denial_cannot_be_promoted_to_gas_proof(self):
        self.fails(lambda d:d["blockscout_denied"].update(
            gas_used="290567"),"INDEPENDENT_PROVIDER_ACCESS_DENIED_NOT_ZERO_GAS")

    def test_wallet_BNB_profit_cannot_be_increased(self):
        self.fails(lambda d:d["original_native"]["movements"][1].update(
            block_native_delta_wei="216136579154473738"),
            "SELECTED_EOA_NATIVE_DELTA_NOT_DDAC_FOLLOW_PROFIT")

    def test_original_blob_modified_is_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            for filename,pin in study.FILES.values():
                shutil.copyfile(study.ROOT/filename,root/filename)
            self.assertEqual(study.build(study.load(root))["P5"],"BLOCKED")
            with (root/study.FILES["readback"][0]).open("ab") as f:
                f.write(b" ")
            with self.assertRaisesRegex(ValueError,"GIT_BLOB_PIN_readback"):
                study.load(root)

if __name__=="__main__":
    unittest.main()
