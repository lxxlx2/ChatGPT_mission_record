#!/usr/bin/env python3
"""Guard true historical signer exit clock vs unproven causal 1/5/15min follower entries."""
import copy
import shutil
import tempfile
import unittest
from pathlib import Path
import bsc_meme_address_model_v1_p4b_239e_4tx_real_clock as model

class Original239ERealSignedFourTxClockTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.orig=model.load()

    def bad(self,edit,reason):
        d=copy.deepcopy(self.orig)
        edit(d)
        with self.assertRaisesRegex(ValueError,reason):
            model.build(d)

    def test_two_actual_original_rounds_different_1_5_15min_exit_status(self):
        z=model.build(self.orig)
        self.assertEqual([x["duration_first_buy_to_final_sell_seconds"] for x in z["sampled_original_rounds"]],
                         [1550,634])
        self.assertEqual([[r["original_final_signed_sell_already_mined"] for r in x["cutoffs"]]
                          for x in z["sampled_original_rounds"]],
                         [[False,False,False],[False,False,True]])
        self.assertTrue(all(x["actual_copy_strategy_1_5_15_minute_return"]=="UNRESOLVED"
                            for x in z["sampled_original_rounds"]))
        self.assertEqual(z["first_public_tradable_U"],"UNRESOLVED")
        self.assertEqual(z["P5"],"BLOCKED")

    def test_original_buy_hash_not_replaceable(self):
        self.bad(lambda d:d["readback"]["selected_tx_records"][0].update(
                 transactionHash="0x"+"f"*64),"SIGNED_TX_BLOCK_AUTHOR_AND_VALUE")

    def test_original_sell_source_timestamp_not_relabelled(self):
        self.bad(lambda d:d["readback"]["selected_tx_records"][1].update(
                 raw_blockTimestamp_hex="0x69b14c67"),"SOURCE_TRANSACTION_BLOCK_TIME")

    def test_original_sell_at_15min_not_claimed_for_long_round(self):
        self.bad(lambda d:d["readback"]["derived_cases"][0]["cutoffs_from_original_first_buy_seconds"][2].update(
                 owner_final_sell_already_mined_by_this_timestamp=True),
                 "NO_INTERIM_CHAIN_BALANCE_OR_OBSERVER_CLAIM")

    def test_second_short_round_does_exit_before_15min(self):
        self.bad(lambda d:d["readback"]["derived_cases"][1]["cutoffs_from_original_first_buy_seconds"][2].update(
                 owner_final_sell_already_mined_by_this_timestamp=False),
                 "NO_INTERIM_CHAIN_BALANCE_OR_OBSERVER_CLAIM")

    def test_no_extra_broadened_3min_window(self):
        self.bad(lambda d:d["freeze"]["cutoffs_seconds_after_actual_owner_first_signed_buy"].append(180),
                 "FREEZE_FIELDS_AND_NO_PROFIT_PROMOTION")

    def test_original_real_profit_sign_no_edit(self):
        self.bad(lambda d:d["original"]["rounds"][1].update(
                 original_native_wallet_net_wei="-22647938898252522"),
                 "REAL_PROFIT_SIGN_VS_UNEXECUTED_MATH_SIGN")

    def test_tool_grade_cannot_invent_provider_capture(self):
        self.bad(lambda d:d["readback"].update(
                 tool_return_grade="FULL_ORIGINAL_NETWORK_REQUEST"),
                 "SOURCE_SCOPE_AND_TOOL_GRADE")

    def test_originating_wallet_is_not_external_follower(self):
        self.bad(lambda d:d["readback"]["selected_tx_records"][0].update(
                 raw_from="0x"+"f"*40),"SIGNED_TX_BLOCK_AUTHOR_AND_VALUE")

    def test_cannot_claim_p5_returns_from_exit_status(self):
        self.bad(lambda d:d["freeze"]["gates"].update(
                 follower_profit_at_1_5_15="PROVEN"),
                 "FREEZE_FIELDS_AND_NO_PROFIT_PROMOTION")

    def test_old_original_signed_transaction_source_mutation_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            folder=Path(td)
            for name,sha in model.SOURCES.values():
                shutil.copyfile(model.ROOT/name,folder/name)
            self.assertEqual(model.build(model.load(folder))["P5"],"BLOCKED")
            with (folder/model.SOURCES["original"][0]).open("ab") as f:
                f.write(b" ")
            with self.assertRaisesRegex(ValueError,"SOURCE_SHA_original"):
                model.load(folder)

if __name__=="__main__":
    unittest.main()
