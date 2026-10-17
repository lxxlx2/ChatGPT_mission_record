#!/usr/bin/env python3
"""Original signed Flap quote ERC20 path tests: intermediate Portal payment, not owner PnL."""
import copy
import shutil
import tempfile
import unittest
from pathlib import Path
import bsc_meme_address_model_v1_p4b_flap_original_quote_portal as gate

class FlapPortalActualQuoteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original=gate.load()

    def rejected(self,change,expected):
        docs=copy.deepcopy(self.original)
        change(docs)
        with self.assertRaisesRegex(ValueError,expected):
            gate.replay(docs)

    def test_actual_original_transactions_have_two_cost_matches(self):
        out=gate.replay(self.original)
        self.assertEqual(out["summary"]["actual_original_tx_quote_to_portal_matches"],2)
        self.assertEqual(out["summary"]["follower_public_executable_U"],0)
        self.assertEqual(out["source_grading"],"TOOL_PARSED_FILTERED_FIELDS_NOT_FULL_RPC_RAW_LOG_PINNED")
        self.assertEqual([x["one_block_nonmatching_other_transfer_count"] for x in out["rows"]],[0,1])
        self.assertTrue(all(x["actual_signed_EOA_input_currency_and_funding"]=="UNRESOLVED" and
                            x["same_wallet_realized_follower_profit"]=="UNRESOLVED"
                            for x in out["rows"]))

    def test_unrelated_same_block_mars_tx_cannot_be_chosen(self):
        def change(d):
            e=d["result"]["rows"][1]
            e["to_portal_transfers"][0]["tx"]=e["to_portal_transfers"][1]["tx"]
        self.rejected(change,"REAL_ORIGINAL_TX_MATCH_ONLY")

    def test_quote_payment_amount_does_not_include_separate_fee(self):
        def change(d):
            e=d["result"]["rows"][0]
            v=int(e["source_Original_TokenBought_cost_raw"])+int(e["source_Original_TokenBought_fee_raw"])
            e["to_portal_transfers"][0]["raw_value_hex"]="0x"+format(v,"064x")
        self.rejected(change,"MATCHED_INTERMEDIARY_QUOTE_COST_NOT_GROSS_COST_PLUS_FEE")

    def test_outbound_original_signer_forged(self):
        self.rejected(lambda d:d["result"]["rows"][0].update(
            from_signer_quote_ERC20_Transfer_count_in_N=1),
            "FILTERED_QUERY_STATUS_OR_COUNT")

    def test_quote_contract_replaced(self):
        self.rejected(lambda d:d["result"]["rows"][0].update(
            quote_ca="0x000000000000000000000000000000000000dead"),
            "TOKEN_QUOTE_CA_ID")

    def test_portal_not_token_receiver(self):
        self.rejected(lambda d:d["result"]["rows"][1]["to_portal_transfers"][0].update(
            to="0x000000000000000000000000000000000000dead"),
            "PORTAL_TRANSFER_DIRECTION_AND_UNIQUENESS")

    def test_intermediate_cannot_be_original_eoa(self):
        def change(d):
            e=d["result"]["rows"][1]
            e["to_portal_transfers"][0]["from"]=e["original_signed_eoa"]
        self.rejected(change,"PORTAL_TRANSFER_DIRECTION_AND_UNIQUENESS")

    def test_original_buy_signer_must_match(self):
        self.rejected(lambda d:d["result"]["rows"][0].update(
            original_signed_eoa="0x000000000000000000000000000000000000dead"),
            "SOURCE_ORIGINAL_TX_AND_SIGNER")

    def test_false_original_pnl_on_source_fails(self):
        self.rejected(lambda d:d["original"]["rows"][0].update(causal_profit="CONFIRMED"),
                      "EXTERNAL_ORIGINAL_BUYER_PNL_UPGRADE")

    def test_false_public_U_fails(self):
        self.rejected(lambda d:d["result"]["gates"].update(
            public_first_executable_U="CONFIRMED"),
            "PREMATURE_FUNDING_OR_U")

    def test_marscoin_original_native_value_required(self):
        self.rejected(lambda d:d["result"]["rows"][1].update(
            original_signed_tx_native_value_wei="0"),
            "ORIGINAL_NATIVE_VALUE_AND_TX_RECIPIENT")

    def test_original_native_tx_receiver_must_match_source(self):
        self.rejected(lambda d:d["result"]["rows"][1].update(
            original_signed_tx_to="0x000000000000000000000000000000000000dead"),
            "ORIGINAL_NATIVE_VALUE_AND_TX_RECIPIENT")

    def test_mars_quote_payer_identity_not_claimed_if_wrong(self):
        self.rejected(lambda d:d["result"]["rows"][1].update(
            original_signed_tx_to_matches_portal_quote_payer=False),
            "ORIGINAL_NATIVE_VALUE_AND_TX_RECIPIENT")

    def test_quote_source_grade_cannot_be_promoted_to_full_rpc(self):
        self.rejected(lambda d:d["result"].update(
            evidence_grade="RAW_RPC_IMMUTABLE_FULL"),
            "SOURCE_GRADE_OR_CHRONOLOGY_UNSUPPORTED")

    def test_from_empty_filter_chronology_not_retroactively_proven(self):
        self.rejected(lambda d:d["result"].update(
            query_chronology_grade="RAW_FROM_FILTER_PRECOMMIT_PROVEN"),
            "SOURCE_GRADE_OR_CHRONOLOGY_UNSUPPORTED")

    def test_mutating_pinned_original_result_byte_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            for filename,_ in gate.SOURCES.values():
                shutil.copyfile(gate.ROOT/filename,root/filename)
            self.assertEqual(gate.replay(gate.load(root))["summary"]["selected_markets"],2)
            with (root/gate.SOURCES["result"][0]).open("ab") as f:
                f.write(b" ")
            with self.assertRaisesRegex(ValueError,"SOURCE_BLOB_DRIFT_result"):
                gate.load(root)

if __name__=="__main__":
    unittest.main()
