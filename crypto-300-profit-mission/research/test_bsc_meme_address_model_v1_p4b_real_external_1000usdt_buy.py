#!/usr/bin/env python3
"""Regression: one true 1000 USDT funded external buy is not a proven profitable copy."""
import copy
import shutil
import tempfile
import unittest
from pathlib import Path
import bsc_meme_address_model_v1_p4b_real_external_1000usdt_buy as study

class External1000USDTRealBuy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.good=study.load()
    def rejects(self,edit,reason):
        x=copy.deepcopy(self.good)
        edit(x)
        with self.assertRaisesRegex(ValueError,reason):
            study.build(x)
    def test_signed_buyer_paid_1000_USDT_and_received_actual_tokens_with_gas(self):
        z=study.build(self.good)
        self.assertEqual(z["actual_wallet_USDT_spent_raw"],"1000000000000000000000")
        self.assertEqual(z["actual_pair_intermediate_WBNB_in_wei"],"1562236003910333182")
        self.assertEqual(z["actual_dragon_token_received_raw"],"48454704178311452125501")
        self.assertEqual(z["wallet_dragon_preexisting_before_real_buy_raw"],"335173813691889308361853")
        self.assertEqual(z["wallet_dragon_end_owner_source_exit_raw"],"383628517870200760487354")
        self.assertEqual(z["receipt_gasUsed_units"],"156632")
        self.assertEqual(z["receipt_actual_fee_BNB_wei"],"78316000000000")
        self.assertEqual(z["classification"],"ACTUAL_SIGNED_BUY_ALREADY_HAD_TOKENS_EXIT_NOT_PROVEN")
        self.assertEqual(z["actual_realized_external_wallet_sell_or_PnL"],"UNRESOLVED")
        self.assertEqual(z["fixed_delay_follow_profit_1_5_15minute"],"UNRESOLVED")
        self.assertEqual(z["P5"],"BLOCKED")

    def test_cannot_switch_source_WBNB_into_original_USDT(self):
        self.rejects(lambda x:x["route"]["decoded"]["path"].__setitem__(
            0,"0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c"),
            "SIGNED_USDT_WBNB_DRAGON_ORIGINAL_ROUTE")

    def test_amount_in_1000_USDT_must_be_in_signed_calldata(self):
        self.rejects(lambda x:x["route"]["decoded"].update(
            amountIn_raw="1500000000000000000000"),
            "SIGNED_USDT_WBNB_DRAGON_ORIGINAL_ROUTE")

    def test_real_wallet_USDT_debit_not_quoted_pair_amount(self):
        self.rejects(lambda x:x["usdt"]["USDT_wallet_balances"][0].update(
            decimal_raw="10946711670407384671181"),"REAL_SIGNER_1000_USDT_BALANCE_DEBIT")

    def test_actual_USDT_transfer_must_belong_to_same_signed_tx(self):
        self.rejects(lambda x:x["usdt"]["USDT_transfer_from_signer"].update(
            transactionHash="0x"+"1"*64),"SIGNED_REAL_USDT_FUNDING_TRANSFER")

    def test_dragon_transferred_cannot_be_just_swap_without_wallet_receipt(self):
        self.rejects(lambda x:x["dragon"]["transfer_to_buyer_logs"]["logs"][0].update(
            data="0x"+("0"*63)+"1"),
            "EXTERNAL_FULL_DELIVERY_TRANSFER_NOT_ONLY_PAIR_QUOTE")

    def test_preexisting_token_holding_is_not_falsified_as_new_user(self):
        self.rejects(lambda x:x["dragon"]["balanceOf_rows"][0].update(
            parsed_owner_token_balance_raw="0"),
            "REAL_ALREADY_OWNED_DRAGON_PLUS_RECEIVED_MORE_AND_NO_CONFIRMED_SELL")

    def test_intermediate_WBNB_pair_volume_is_not_spent_from_signer_wallet(self):
        self.rejects(lambda x:x["wbnb"]["transfer_from_wallet_event"].update(total=1),
            "PAIR_WBNB_NOT_SIGNER_DIRECT_WBNB_DEBIT")

    def test_receipt_actual_gas_not_gas_limit(self):
        self.rejects(lambda x:x["usdt"]["receipt"].update(
            gasUsed="0x7a120"),"REAL_SUCCESS_RECEIPT_GAS_USED_AND_NO_FAKE_RAW")

    def test_actual_gas_fee_is_separate_from_USDT_principal(self):
        self.rejects(lambda x:x["usdt"]["receipt"].update(
            computed_buy_fee_wei="0"),"REAL_SUCCESS_RECEIPT_GAS_USED_AND_NO_FAKE_RAW")

    def test_cannot_promote_real_buy_into_realized_profit(self):
        self.rejects(lambda x:x["usdt"]["verification"].update(
            actual_follower_net_return="PROVEN_POSITIVE"),
            "CANNOT_REBRAND_EXISTING_HOLDER_AS_PROFITABLE_CAUSAL_FOLLOWER")

    def test_source_blob_changed_then_fail_before_replay(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            for filename,pin in study.SOURCES.values():
                shutil.copyfile(study.ROOT/filename,root/filename)
            self.assertEqual(study.build(study.load(root))["P5"],"BLOCKED")
            with (root/study.SOURCES["usdt"][0]).open("ab") as fp:
                fp.write(b" ")
            with self.assertRaisesRegex(ValueError,"SOURCE_PIN_usdt"):
                study.load(root)

if __name__=="__main__":
    unittest.main()
