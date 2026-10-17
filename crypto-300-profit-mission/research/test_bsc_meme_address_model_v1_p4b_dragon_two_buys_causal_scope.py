#!/usr/bin/env python3
"""Adversarial scope tests: actual post-owner signed trades != externally replicable profit."""
import copy
import shutil
import tempfile
import unittest
from pathlib import Path
import bsc_meme_address_model_v1_p4b_dragon_two_buys_causal_scope as gate

class Dragon2026CausalScopeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.good=gate.load()

    def should_fail(self,edit,reason):
        d=copy.deepcopy(self.good)
        edit(d)
        with self.assertRaisesRegex(ValueError,reason):
            gate.build(d)

    def test_two_signed_real_trade_windows_not_follower(self):
        a=gate.build(self.good)
        self.assertEqual(a["selected_four_blocks_sum_native_delta_wei"],"61218026868859435")
        self.assertEqual(
          [x["owner_to_actual_buy_block_timestamp_ms"] for x in a["rows"]],
          [100800,138600])
        self.assertEqual(
          [x["owner_to_actual_sell_block_timestamp_ms"] for x in a["rows"]],
          [108900,143100])
        self.assertEqual(
          [x["real_buyer_hold_timestamp_ms"] for x in a["rows"]],
          [8100,4500])
        self.assertEqual(
          [a["cutoffs_after_DDAC_original_buy_seconds"][str(s)]["D503_buy_and_subsequent_exit_both_inside_cutoff"] for s in (60,300,900)],
          [0,2,2])
        self.assertTrue(all(x["actual_follower_ROI"]=="UNRESOLVED" for x in a["rows"]))
        self.assertEqual(a["verified_causal_external_follower_entries"],0)
        self.assertEqual(a["P5"],"BLOCKED")

    def test_wrong_actual_first_signed_buy(self):
        self.should_fail(lambda d:d["probe"]["results"][0].update(
          tx="0x"+"a"*64),"ORIGINAL_SIGNED_ACTUAL_BUY_IDENTITY")

    def test_original_market_CA_switch_rejected(self):
        self.should_fail(lambda d:d["freeze"].update(
          exact_CA="0x"+"0"*40),"FROZEN_EXACT_CA_AND_BUYERS")

    def test_clipped_receipt_cannot_be_rebranded_complete(self):
        self.should_fail(lambda d:d["probe"]["results"][1]["ethGetTransactionReceipt"].update(
          complete_parseable_JSON=True),"PROVIDER_CLIPPED_OR_DENIED_NOT_PROFIT")

    def test_paid_trace_unavailable_is_not_successful_trace(self):
        self.should_fail(lambda d:d["probe"]["results"][0]["debugTraceTransaction"].update(
          call_trace="COMPLETE"),"PROVIDER_CLIPPED_OR_DENIED_NOT_PROFIT")

    def test_full_follow_PnL_faked(self):
        self.should_fail(lambda d:d["probe"]["gates"].update(
          follower_net_return_1_5_15_min="CONFIRMED"),"FALSIFIED_OBSERVER_PROFIT_GATE")

    def test_earlier_profit_disappears_if_wrong_native_credit(self):
        self.should_fail(lambda d:d["native"]["movements"][1].update(
          block_native_delta_wei="0"),"NATIVE_SELECTED_BLOCK_DIRECTIONS")

    def test_wrong_sell_inventory_does_not_pass(self):
        self.should_fail(lambda d:d["inventory"]["samples"][3].update(
          token_raw="1000000000000000000000"),"EXACT_TOKEN_INVENTORY_CLOSED")

    def test_holdout_control_never_converted_to_loss(self):
        self.should_fail(lambda d:d["inventory"]["samples"][-1].update(
          token_raw="0"),"FROZEN_E11B_NO_CURVE_EXIT_STILL_UNKNOWN_NOT_LOSS")

    def test_immutable_source_bytes_checked(self):
        with tempfile.TemporaryDirectory() as td:
            dst=Path(td)
            for fn,_ in gate.SOURCES.values():
                shutil.copyfile(gate.ROOT/fn,dst/fn)
            self.assertEqual(gate.build(gate.load(dst))["P4_B"],"PARTIAL")
            with (dst/gate.SOURCES["signed"][0]).open("ab") as f:
                f.write(b" ")
            with self.assertRaisesRegex(ValueError,"SOURCE_SHA_DRIFT_signed"):
                gate.load(dst)

if __name__=="__main__":
    unittest.main()
