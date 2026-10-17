#!/usr/bin/env python3
"""Tests: real 5E60 Dragon exit must never be rebranded as 1000 USDT profit."""
import copy
import shutil
import tempfile
import unittest
from pathlib import Path
import bsc_meme_address_model_v1_p4b_5e60_real_five_sell_liquidation as model

class TrueOriginalExternalSignedDragonSells(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.docs=model.load()
    def reject(self,fn,code):
        d=copy.deepcopy(self.docs)
        fn(d)
        with self.assertRaisesRegex(ValueError,code):
            model.build(d)
    def test_full_real_five_sell_exit_cash_receipts_and_cost_unknown(self):
        z=model.build(self.docs)
        self.assertEqual(len(z["first_five_real_signed_sales"]),5)
        self.assertEqual(len(z["later_three_signed_USDT_sales"]),3)
        self.assertEqual(z["first_five_all_Dragon_sold_raw"],"383628517870200760487354")
        self.assertEqual(z["first_five_actual_USDT_received_raw"],"8399620126582833083485")
        self.assertEqual(z["first_five_independent_USDT_wallet_balance_increase_raw"],"8399620126582833083485")
        self.assertEqual(z["first_five_actual_BNB_sell_gas_fee_wei"],"370354000000000")
        self.assertEqual(z["later_three_actual_USDT_received_raw"],"13540757456188781829802")
        self.assertTrue(z["first_five_true_zero_Dragon_wallet_balance_after_fifth"])
        self.assertEqual(z["legacy_335173_Dragon_purchase_cost_basis"],
                         "UNRESOLVED_PAGINATED_PRIOR_10_OR_MORE_RECEIPTS")
        self.assertEqual(z["PUBLIC_EXECUTABLE_U"],"UNRESOLVED")
        self.assertEqual(z["P5"],"BLOCKED")
    def test_cannot_fake_full_exit_by_changing_actual_dragon_post_balance(self):
        self.reject(lambda d:d["sells"]["checkpoints"].update(
               after_fifth_sell_Dragon_raw="1"),"FIRST_FIVE_FULL_REAL_LIQUIDATION_AND_USDT_WALLET_CREDIT")
    def test_cannot_replace_original_signer_of_sell(self):
        self.reject(lambda d:d["sells"]["rows"][0].update(
               signer="0x"+"f"*40),"ALL_EIGHT_SAME_REAL_SIGNED_ROUTER_SELL_PATH")
    def test_cannot_ignore_sixth_to_eighth_sells(self):
        self.reject(lambda d:d["sells"]["rows"].pop(),
               "FROZEN_SOURCE_QUERY_SCOPE")
    def test_wrong_token_in_router_path_rejected(self):
        self.reject(lambda d:d["sells"]["rows"][0]["signed_router_path"].__setitem__(
                0,"0x55d398326f99059ff775485246999027b3197955"),
                "ALL_EIGHT_SAME_REAL_SIGNED_ROUTER_SELL_PATH")
    def test_transfer_hash_must_match_signed_transaction(self):
        self.reject(lambda d:d["sells"]["rows"][1]["selected_full_USDT_Transfer"].update(
            transactionHash="0x"+"0"*64),"SAME_SIGNED_SELL_REAL_USDT_CREDIT_NOT_ROUTER_MIN_OUT")
    def test_token_outbound_amount_cannot_be_rewritten(self):
        self.reject(lambda d:d["out"]["transfers"][3].update(
            raw_uint256="1"),"ACTUAL_TRANSACTION_SUCCESS_GAS_AND_ERC20_SELL_QUANTITY")
    def test_actual_gas_used_not_signed_limit(self):
        self.reject(lambda d:d["fees"]["rows"][0].update(
            gasUsed_units="500000"),"ACTUAL_TRANSACTION_SUCCESS_GAS_AND_ERC20_SELL_QUANTITY")
    def test_one_actual_usdt_receipt_change_breaks_cash_reconciliation(self):
        self.reject(lambda d:d["sells"]["rows"][3].update(
            actual_USDT_received_raw="1"),"SAME_SIGNED_SELL_REAL_USDT_CREDIT_NOT_ROUTER_MIN_OUT")
    def test_separate_later_three_sells_cannot_be_counted_as_first_five(self):
        self.reject(lambda d:d["sells"]["rows"][5].update(
            rank=5),"ALL_EIGHT_SAME_REAL_SIGNED_ROUTER_SELL_PATH")
    def test_source_prior_acquisition_more_than_ten_must_not_be_called_complete(self):
        self.reject(lambda d:d["censored"].update(
            complete_full_window=True),"COST_BASIS_INCOMPLETE_MUST_NOT_BE_PROFIT")
    def test_source_prior_page_key_cannot_be_erased(self):
        self.reject(lambda d:d["censored"].update(
            pageKey_exists=False),"COST_BASIS_INCOMPLETE_MUST_NOT_BE_PROFIT")
    def test_history_original_1000_usdt_buy_involved_existing_stake(self):
        self.reject(lambda d:d["buy"]["external_wallet_dragon_state"].update(
            before_buy_raw="0"),"REAL_PREEXISTING_DRAGON_AND_1000_USDT_BUY")
    def test_p5_blocker_cannot_change_into_approve(self):
        self.reject(lambda d:d["sells"]["gates"].update(P5="APPROVED"),
            "NO_FALSE_CAUSAL_1000USDT_PROFIT")
    def test_pinned_eight_real_sells_source_immutable(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            for name,sha in model.SOURCES.values():
                shutil.copyfile(model.ROOT/name,root/name)
            self.assertEqual(model.build(model.load(root))["P5"],"BLOCKED")
            with (root/model.SOURCES["sells"][0]).open("ab") as fd:
                fd.write(b" ")
            with self.assertRaisesRegex(ValueError,"SOURCE_GIT_BLOB_sells"):
                model.load(root)
if __name__=="__main__":
    unittest.main()
