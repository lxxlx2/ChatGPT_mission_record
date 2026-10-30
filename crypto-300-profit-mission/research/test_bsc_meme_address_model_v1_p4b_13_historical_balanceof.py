#!/usr/bin/env python3
"""Adversarial archival tests for true historical ERC20 owner state, no follower ROI."""
import copy
import shutil
import tempfile
import unittest
from pathlib import Path
import bsc_meme_address_model_v1_p4b_13_historical_balanceof as verifier

class HistoricalActualOwnerBalance13Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.docs=verifier.load()

    def fail(self,change,reason):
        d=copy.deepcopy(self.docs)
        change(d)
        with self.assertRaisesRegex(ValueError,reason):
            verifier.build(d)

    def test_all_13_actual_historical_balance_matches_without_fake_follow(self):
        d=verifier.build(self.docs)
        self.assertEqual(d["counts"]["historical_balance_successes"],13)
        self.assertEqual(d["counts"]["full_onchain_ERC20_balances_equal_selected_signed_flows"],13)
        self.assertEqual(d["counts"]["unique_wallets"],3)
        self.assertEqual(d["counts"]["unique_CAs"],2)
        self.assertEqual(d["counts"]["causal_follower_transactions_verified"],0)
        self.assertEqual(d["counts"]["present_2026_10_18_live_balance_queries"],0)
        self.assertEqual(d["PUBLIC_EXECUTABLE_U"],"UNRESOLVED")
        self.assertEqual(d["P5"],"BLOCKED")
        self.assertTrue(d["ddac_zero_at_actual_d503_buy_block"])
        self.assertTrue(d["239e_genuinely_zero_between_signed_rounds"])
        self.assertTrue(d["hajimi_nonzero_after_first_partial_sell"])

    def test_ddac_really_zero_when_d503_was_buying(self):
        d=verifier.build(self.docs)
        balance=next(r["historical_block_end_balanceOf_uint256_raw"] for r in d["historical_rows"]
                     if r["case"]=="DDAC_DRAGON" and r["block"]==83636000)
        self.assertEqual(balance,"0")

    def test_original_239e_reentry_nonzero_after_prior_zero(self):
        d=verifier.build(self.docs)
        r={x["block"]:x["historical_block_end_balanceOf_uint256_raw"]
           for x in d["historical_rows"] if x["case"]=="239E_DRAGON"}
        self.assertEqual(r[85959960],"0")
        self.assertEqual(r[85959961],"9324059273385582494656")
        self.assertEqual(r[85961371],"0")

    def test_original_hajimi_partial_remains_nonzero(self):
        d=verifier.build(self.docs)
        r={x["block"]:x["historical_block_end_balanceOf_uint256_raw"]
           for x in d["historical_rows"] if x["case"]=="8E6B_HAJIMI"}
        self.assertEqual(r[74741573],"64629048195327088600524")
        self.assertEqual(r[74741587],"0")

    def test_wrong_d503_owner_balance_is_rejected(self):
        self.fail(lambda d:d["readback"]["historical_exact_CA_and_owner_balance_rows"][2].update(
             observed_raw_balance="1"),"ONCHAIN_UINT256_32BYTE_RETURN")

    def test_same_tampered_hex_and_decimal_even_if_self_consistent_is_rejected(self):
        def edit(d):
            row=d["readback"]["historical_exact_CA_and_owner_balance_rows"][2]
            row["tool_return_hex"]="0x"+("0"*63)+"1"
            row["observed_raw_balance"]="1"
        self.fail(edit,"REAL_CHAIN_BALANCE_VS_SIGNED_TOKENS")

    def test_wrong_historical_blocktag_rejected(self):
        self.fail(lambda d:d["readback"]["historical_exact_CA_and_owner_balance_rows"][2].update(
             eth_call_blockTag="latest"),"HISTORICAL_RPC_PARAMETERS_ONLY_NO_FULL_PROVIDER_CAPTURE")

    def test_wrong_token_ca_on_one_market_rejected(self):
        self.fail(lambda d:d["readback"]["historical_exact_CA_and_owner_balance_rows"][10].update(
             token_CA="0x"+"a"*40),"CHECKPOINT_IDENTITY")

    def test_wrong_original_owner_signed_event_rejected(self):
        self.fail(lambda d:d["e239"]["rounds"][0]["txs"][1].update(
             wallet_signed_token_delta_raw="1000000"),"239E_SIGNED_DELTA_INVENTORY")

    def test_bad_historical_balance_grade_not_upgrade_to_original_provider(self):
        self.fail(lambda d:d["readback"]["historical_exact_CA_and_owner_balance_rows"][0].update(
             source_grade="PROVIDER_FULL_PACKET"),"HISTORICAL_RPC_PARAMETERS_ONLY_NO_FULL_PROVIDER_CAPTURE")

    def test_public_follower_u_still_not_claimed(self):
        self.fail(lambda d:d["readback"]["gates"].update(
             public_executable_U="PROVEN"),"NO_REALTIME_OR_FOLLOWER_OVERCLAIM")

    def test_freeze_scope_not_widened_after_tool_results(self):
        self.fail(lambda d:d["freeze"].update(frozen_rpc_calls=14),
                  "RPC_SCOPE_OR_PROVENANCE")

    def test_original_source_bytes_mutation_fails_before_parsing(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            for file,sha in verifier.SOURCES.values():
                shutil.copyfile(verifier.ROOT/file,root/file)
            self.assertEqual(verifier.build(verifier.load(root))["P5"],"BLOCKED")
            with (root/verifier.SOURCES["readback"][0]).open("ab") as f:
                f.write(b" ")
            with self.assertRaisesRegex(ValueError,"SOURCE_GIT_BLOB_CHANGED_readback"):
                verifier.load(root)

if __name__=="__main__":
    unittest.main()
