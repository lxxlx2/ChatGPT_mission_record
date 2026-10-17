#!/usr/bin/env python3
"""Negative controls: N+1 two view calls are not a stateful historical follower trade."""
import copy
import shutil
import tempfile
import unittest
from pathlib import Path
import bsc_meme_address_model_v1_p4b_flap_nplus1_two_sided_quotes as gate

class Flap2026TwoSidedMathOnlyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.good=gate.load()

    def fails(self, mutation,reason):
        docs=copy.deepcopy(self.good)
        mutation(docs)
        with self.assertRaisesRegex(ValueError,reason):
            gate.build(docs)

    def test_replay_two_markets_two_direction_math_only(self):
        a=gate.build(self.good)
        self.assertEqual(a["summary"]["scoped_tokens"],2)
        self.assertEqual(a["summary"]["quote_calls"],4)
        self.assertEqual(a["summary"]["verified_public_executable_U"],0)
        self.assertEqual(a["summary"]["P5"],"BLOCKED")
        self.assertEqual({x["token"] for x in a["rows"]},{"牛来","MARSCOIN"})
        self.assertTrue(all(x["actual_post_witness_follower_buy_then_sell"]=="UNRESOLVED"
                            and x["actual_post_hypothetical_purchase_market_state"]=="NOT_SIMULATED"
                            for x in a["rows"]))

    def test_source_only_signed_buy_after_N_block_wrong(self):
        self.fails(lambda d:d["freeze"]["cases"][0].update(read_block_Nplus1=115628774),
                   "POST_WITNESS_READ_BLOCK")

    def test_bought_token_CA_swapped(self):
        self.fails(lambda d:d["readback"]["rows"][0].update(
            exact_CA=d["freeze"]["cases"][1]["CA"]),"TOKEN_CA_CORRESPONDENCE")

    def test_original_quote_CA_modified(self):
        self.fails(lambda d:d["readback"]["rows"][0].update(
            quote_CA="0x000000000000000000000000000000000000dead"),"QUOTE_ASSET_AND_DECIMALS")

    def test_view_caller_faked_actual_buy(self):
        self.fails(lambda d:d["readback"]["rows"][0].update(signed_actual_buy=True),
                   "MATH_MISLABELLED_ACTUAL_TRADE")

    def test_view_caller_faked_actual_sell(self):
        self.fails(lambda d:d["readback"]["rows"][1].update(signed_actual_sell=True),
                   "MATH_MISLABELLED_ACTUAL_TRADE")

    def test_mutated_reverse_input_sell_amount(self):
        self.fails(lambda d:d["readback"]["rows"][0]["reverse"].update(input_token_raw="1"),
                   "INVERSE_QUOTE_SAME_HISTORIC_STATE")

    def test_switched_reverse_token_direction_fails(self):
        self.fails(lambda d:d["readback"]["rows"][1]["reverse"].update(
            rpc_calldata=d["readback"]["rows"][1]["buy"]["rpc_calldata"]),
            "INVERSE_QUOTE_SAME_HISTORIC_STATE")

    def test_mutated_buy_output_fails(self):
        self.fails(lambda d:d["readback"]["rows"][1]["buy"].update(decoded_token_raw="1"),
                   "BUY_ETHCALL_INPUT_OUTPUT")

    def test_unverified_2026_tax_promoted(self):
        self.fails(lambda d:d["readback"]["rows"][0].update(
            gas_tax_slippage_historical_settlement="CONFIRMED"),
            "MATH_MISLABELLED_ACTUAL_TRADE")

    def test_global_qualified_U_faked(self):
        self.fails(lambda d:d["readback"]["gates"].update(
            global_public_executable_U="CONFIRMED"),"PREMATURE_REALIZED_OR_PRODUCTION")

    def test_static_gap_is_not_free_money(self):
        self.fails(lambda d:d["readback"]["rows"][0].update(
            static_two_read_difference_quote_raw="-1000"),
            "MATH_PRICE_DIFFERENCE_DOES_NOT_PROVE_PROFIT")

    def test_four_causal_calls_limit_enforced(self):
        self.fails(lambda d:d["readback"].update(read_count=5),
                   "SCOPE_OR_ABI_DRIFT")

    def test_original_early_owner_must_be_signed(self):
        self.fails(lambda d:d["first_signed"]["rows"][0].update(
            original_first_purchase_event_match="UNRESOLVED"),
            "EARLY_ACTUAL_SIGNED_OWNER_EVIDENCE")

    def test_original_historical_quote_decimals_changed(self):
        self.fails(lambda d:d["first_signed"]["rows"][1].update(
            historical_quote_decimals=6),
            "QUOTE_ASSET_AND_DECIMALS")

    def test_original_historical_buy_tax_cannot_change(self):
        self.fails(lambda d:d["first_signed"]["rows"][1].update(
            buy_tax_bps=0),"EARLY_PREBUY_OR_TAX_SOURCE")

    def test_source_pinned_byte_tamper(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            for filename,_ in gate.SOURCES.values():
                shutil.copyfile(gate.ROOT/filename,root/filename)
            self.assertEqual(gate.build(gate.load(root))["summary"]["scoped_tokens"],2)
            with (root/gate.SOURCES["readback"][0]).open("ab") as file:
                file.write(b" ")
            with self.assertRaisesRegex(ValueError,"SOURCE_BLOB_DRIFT_readback"):
                gate.load(root)

if __name__=="__main__":
    unittest.main()
