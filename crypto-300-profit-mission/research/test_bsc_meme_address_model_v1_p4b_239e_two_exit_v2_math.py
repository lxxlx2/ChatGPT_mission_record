#!/usr/bin/env python3
"""Negative tests for 8 real historic V2 quotes; NEVER promote static math to copy profits."""
import copy
import shutil
import tempfile
import unittest
from pathlib import Path
import bsc_meme_address_model_v1_p4b_239e_two_exit_v2_math as model

class SignedOwnerVersusStaticV2MathTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.good=model.load()

    def reject(self,change,why):
        docs=copy.deepcopy(self.good)
        change(docs)
        with self.assertRaisesRegex(ValueError,why):
            model.build(docs)

    def test_two_actual_original_signed_rounds_and_eight_historical_quotes(self):
        result=model.build(self.good)
        self.assertEqual(len(result["samples"]),2)
        self.assertEqual([r["static_two_snapshot_gross_math_delta_wei"] for r in result["samples"]],
                         ["-842118233011701","933894786881619"])
        self.assertEqual([r["static_buy_dragon_token_out_raw"] for r in result["samples"]],
                         ["278350347316975449623","310011231296926372159"])
        self.assertEqual([r["static_reverse_WBNB_out_wei"] for r in result["samples"]],
                         ["9157881766988299","10933894786881619"])
        self.assertEqual([r["static_two_snapshot_gross_math_delta_bps_trunc"] for r in result["samples"]],
                         ["-842","933"])
        self.assertFalse(result["verified_executable_buy_sell_with_Gas_and_Tax"])
        self.assertFalse(result["observed_full_provider_wire_request_transcript"])
        self.assertEqual(result["PUBLIC_EXECUTABLE_U"],"UNRESOLVED")
        self.assertEqual(result["P5"],"BLOCKED")

    def test_negative_round_real_owner_loss_not_changed_positive(self):
        self.reject(lambda d:d["original_real"]["rounds"][0].update(
                     original_native_wallet_net_wei="15332805033002259"),
                    "REAL_OWNER_NEGATIVE_POSITIVE_EPISODE_IDENTITY")

    def test_positive_round_real_owner_profit_not_faked(self):
        self.reject(lambda d:d["original_real"]["rounds"][1].update(
                     original_native_wallet_net_wei="-22647938898252522"),
                    "REAL_OWNER_NEGATIVE_POSITIVE_EPISODE_IDENTITY")

    def test_buy_quote_uses_frozen_historical_block(self):
        self.reject(lambda d:d["readback"]["calls"][1]["tool_invoked_with"].update(
                     blockTag="latest"),"BOUNDED_ABI_REQUEST_SELF_CONSISTENCY_ONLY")

    def test_sell_quote_cannot_switch_market_address(self):
        self.reject(lambda d:d["readback"]["calls"][3]["tool_invoked_with"].update(
                     to="0x"+"0"*40),"BOUNDED_ABI_REQUEST_SELF_CONSISTENCY_ONLY")

    def test_reverse_sell_cannot_use_different_buy_amount(self):
        self.reject(lambda d:d["readback"]["calls"][3]["tool_invoked_with"].update(
                     calldata="0xd06ca61f"+"0"*320),
                    "BOUNDED_ABI_REQUEST_SELF_CONSISTENCY_ONLY")

    def test_uint256_malformed_buy_quote_return_rejected(self):
        self.reject(lambda d:d["readback"]["calls"][1].update(
                     tool_return_hex="0x12"),"BAD_ABI_ROUTER_DYNAMIC_ARRAY")

    def test_uint256_bad_offset_dynamic_reverse_rejected(self):
        def tamper(d):
            x=d["readback"]["calls"][7]
            x["tool_return_hex"]="0x"+("0"*64)+x["tool_return_hex"][66:]
        self.reject(tamper,"BAD_ROUTER_2_AMOUNTS_ABI")

    def test_changed_raw_router_buy_quote_cannot_pass_reserve_math(self):
        def tamper(d):
            row=d["readback"]["calls"][1]
            row["tool_return_hex"]=row["tool_return_hex"][:-2]+"18"
            d["readback"]["cases"][0]["buy_maths_quote_dragon_out_raw"]=str(
                int(d["readback"]["cases"][0]["buy_maths_quote_dragon_out_raw"])+1)
        self.reject(tamper,"TWO_QUOTE_AMOUNTS_AND_EXPLICIT_NOT_REALIZED")

    def test_pool_raw_reserve_mutation_breaks_unmodified_quote(self):
        def tamper(d):
            row=d["readback"]["calls"][0]
            h=row["tool_return_hex"]
            row["tool_return_hex"]=h[:65]+("1" if h[65]!="1" else "2")+h[66:]
        self.reject(tamper,"REAL_POOL_FEE_MATH_BOTH_END_BLOCKS")

    def test_fee_math_cannot_be_promoted_to_net_profit(self):
        self.reject(lambda d:d["readback"]["assertions"].update(
                      no_follow_profit_claim=False),"NO_FOLLOWER_ROI_PROMOTION")

    def test_explicit_provider_request_transcript_must_not_be_claimed(self):
        self.reject(lambda d:d["readback"]["calls"][0].update(
                      provider_full_wire_record=True),"PHASE_AND_PROVIDER_TRANSPORT_PROVENANCE")

    def test_original_frozen_router_cannot_be_changed(self):
        self.reject(lambda d:d["freeze"].update(
                      router="0x"+"f"*40),"ORIGINAL_V2_FIXED_MARKET")

    def test_size_must_remain_001_wbnb_not_scale_after_result(self):
        self.reject(lambda d:d["freeze"].update(
                     fixed_hypothetical_gross_WBNB_amount_in_wei="100000000000000000"),
                    "PRECOMMIT_SOURCES_OR_FIXED_001_WBNB")

    def test_raw_original_source_and_readback_byte_pin(self):
        with tempfile.TemporaryDirectory() as td:
            folder=Path(td)
            for filename,pin in model.SOURCES.values():
                shutil.copyfile(model.ROOT/filename,folder/filename)
            self.assertEqual(model.build(model.load(folder))["P5"],"BLOCKED")
            with (folder/model.SOURCES["readback"][0]).open("ab") as fp:
                fp.write(b" ")
            with self.assertRaisesRegex(ValueError,"PINNED_SOURCE_CHANGED_readback"):
                model.load(folder)

if __name__=="__main__":
    unittest.main()
