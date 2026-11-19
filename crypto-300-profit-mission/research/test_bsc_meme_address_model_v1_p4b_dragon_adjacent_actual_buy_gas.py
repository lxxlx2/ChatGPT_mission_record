#!/usr/bin/env python3
"""Prove adjacent cumulative receipt gasUsed, not EOA residual guessed gas or follower PnL."""
import copy
import shutil
import tempfile
import unittest
from pathlib import Path
import bsc_meme_address_model_v1_p4b_dragon_adjacent_actual_buy_gas as model

class ActualAdjacentD503BuyGasTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=model.load()

    def must_fail(self,change,expected):
        d=copy.deepcopy(self.data)
        change(d)
        with self.assertRaisesRegex(ValueError,expected):
            model.build(d)

    def test_two_actual_buy_gas_and_fee_from_adjacent_receipts(self):
        result=model.build(self.data)
        self.assertEqual([x["gasUsed_actual_units_from_adjacent_cumulative"]
                          for x in result["true_signed_D503_buy_gas"]],
                         ["290567","290567"])
        self.assertEqual([x["derived_actual_buy_gas_fee_BNB_wei"]
                          for x in result["true_signed_D503_buy_gas"]],
                         ["871701000000000","2033969000000000"])
        self.assertEqual([x["unattributed_residual_wei"]
                          for x in result["true_signed_D503_buy_gas"]],
                         ["-4","-18"])
        self.assertTrue(result["E11B_unknown_gas_and_exit"])
        self.assertFalse(result["actual_complete_target_receipt_archived"])
        self.assertEqual(result["P5"],"BLOCKED")

    def test_previous_transaction_index_not_any_old_transaction(self):
        self.must_fail(lambda d:d["readback"]["rows"][1].update(
            previous_transaction_index=53),"CHAIN_TX_ADJACENCY_OR_TARGET_IDENTITY")

    def test_source_target_cumulative_cannot_be_relabelled(self):
        self.must_fail(lambda d:d["readback"]["rows"][0].update(
            target_cumulativeGasUsed_hex="0x4fa40"),
            "ORIGINAL_PINNED_TOOL_VISIBLE_TARGET_CUMULATIVE")

    def test_previous_receipt_must_be_same_block_and_index(self):
        self.must_fail(lambda d:d["readback"]["rows"][1].update(
            previous_receipt_index_hex="0x35"),
            "REAL_IMMEDIATELY_PRECEDING_TX_RECEIPT")

    def test_incorrect_previous_cumulative_fails_derived_gas(self):
        self.must_fail(lambda d:d["readback"]["rows"][1].update(
            previous_cumulativeGasUsed_hex="0x1a7d74d"),
            "ONCHAIN_CUMULATIVE_DELTA_IS_TRANSACTION_GASUSED")

    def test_signed_target_gas_price_cannot_change(self):
        self.must_fail(lambda d:d["real_five_signed_tx"]["results"][2]["returned"].update(
            gasPrice="0x1"),"CHAIN_TX_ADJACENCY_OR_TARGET_IDENTITY")

    def test_fee_cannot_ignore_actual_gas_price(self):
        self.must_fail(lambda d:d["readback"]["rows"][1].update(
            derived_legacy_tx_fee_wei="871701000000000"),
            "SIGNED_GAS_PRICE_MULTIPLY_DERIVED_GAS")

    def test_wallet_native_balance_debit_was_gas_inclusive(self):
        self.must_fail(lambda d:d["readback"]["rows"][0].update(
            observed_actual_buy_block_native_debit_wei="190000000000000000"),
            "ALREADY_GAS_INCLUSIVE_NATIVE_WALLET_BLOCK_DELTA")

    def test_4_and_18_wei_nonzero_residual_cannot_be_changed_to_zero(self):
        self.must_fail(lambda d:d["readback"]["rows"][1].update(
            native_block_debit_minus_signed_value_plus_calculated_fee_wei="0"),
            "ALREADY_GAS_INCLUSIVE_NATIVE_WALLET_BLOCK_DELTA")

    def test_E11B_gas_and_exit_not_falsely_claimed(self):
        self.must_fail(lambda d:d["readback"]["rows"][2].update(
            derived_target_gasUsed_units="290567"),
            "E11B_UNKNOWN_GAS_AND_EXIT_MUST_REMAIN_UNKNOWN")

    def test_no_broadening_queries_after_source_freeze(self):
        self.must_fail(lambda d:d["readback"]["call_budget"].update(
            total_calls_executed=8),"PRECOMMIT_AND_NO_EXTRA_QUERIES")

    def test_old_partial_receipt_prefix_must_keep_its_actual_cumulative(self):
        self.must_fail(lambda d:d["prior_partial_buy_receipts"]["results"][0]
            ["ethGetTransactionReceipt"].update(visible_cumulativeGasUsed="0x1"),
            "ORIGINAL_PINNED_TOOL_VISIBLE_TARGET_CUMULATIVE")

    def test_byte_change_in_new_result_fails_sha_pin(self):
        with tempfile.TemporaryDirectory() as td:
            tmp=Path(td)
            for filename,sha in model.FILES.values():
                shutil.copyfile(model.ROOT/filename,tmp/filename)
            self.assertEqual(model.build(model.load(tmp))["P5"],"BLOCKED")
            with (tmp/model.FILES["readback"][0]).open("ab") as f:
                f.write(b" ")
            with self.assertRaisesRegex(ValueError,"PINNED_BLOB_DRIFT_readback"):
                model.load(tmp)
if __name__=="__main__":
    unittest.main()
