import copy
import json
import unittest
from bsc_meme_address_model_v1_p4c_8e6b_token4_19tx import ROOT,build,load

class Token4Original19TwoOpposingNativeOutcomes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=load(ROOT)

    def test_exact_source_immutable_result_replay(self):
        got=build(self.source)
        expected=json.loads((ROOT/"bsc-meme-address-model-v1-p4c-8e6b-token4-19tx-five-independent-source-reconciliation-2026-10-15.json").read_text(encoding="utf-8"))
        self.assertEqual(got,expected)

    def test_two_opposite_rounds_original_19_transactions(self):
        x=build(self.source)
        self.assertEqual((x["summary"]["original_signer_success_source_records"],x["summary"]["independent_live_spot_tx_count"]),(19,5))
        self.assertEqual((x["summary"]["original_negative_native_rounds"],x["summary"]["original_positive_native_rounds"]),(1,1))
        self.assertEqual([r["original_wallet_native_net_wei"] for r in x["rounds"]],["-117977426190152496","13282964879793219111"])
        self.assertEqual(x["summary"]["original_total_native_wei"],"13164987453603066615")
        self.assertEqual([r["trade_count"] for r in x["rounds"]],[2,17])
        self.assertTrue(all(r["original_inventory_closed_raw"]=="0" for r in x["rounds"]))
        self.assertEqual(x["summary"]["lagged_1_5_15_min_follower_signal_count"],0)
        self.assertEqual(x["summary"]["production"],"NO_GO")
        self.assertFalse(x["summary"]["independent_reviewer_approved_this_sha"])

    def test_buy_wbnb_actual_mint_differs_from_original_native_input(self):
        x=build(self.source)
        self.assertEqual([r["buy_native_input_minus_WBNB_deposit_wei"] for r in x["spot_checks"] if r["action"]=="BUY"],
                         ["5000000000000000","3000000000000000"])
        self.assertTrue(all(r["original_chain56_signer_confirmed"] and r["full_success_receipt_confirmed"] for r in x["spot_checks"]))

    def test_actual_token4_historic_window_2025_not_2026(self):
        from bsc_meme_address_model_v1_p4c_8e6b_token4_19tx import git_blob
        raw=(ROOT/"bsc-meme-address-model-v1-p4c-8e6b-token4-2025-blocktime-header-2026-10-15.json").read_bytes()
        self.assertEqual(git_blob(raw),"85bca313b5579fa4971478d81c9d2c5320299927")
        evidence=json.loads(raw)
        self.assertEqual([r["block"] for r in evidence["rows"]],[63056884,64458294])
        self.assertEqual([r["UTC"] for r in evidence["rows"]],
                         ["2025-10-01T04:08:45.000Z","2025-10-13T08:13:21.000Z"])
        self.assertTrue(all(r["RPC_FULL_BLOCK_BODY"]=="TRUNCATED_TOOL_OUTPUT_HEADER_FIELDS_ONLY"
                            for r in evidence["rows"]))

    def test_missing_negative_case_fails(self):
        d=copy.deepcopy(self.source)
        d[3]["first_major_4"]["rounds"].pop(0)
        with self.assertRaises(ValueError):build(d)

    def test_positive_incomplete_sell_inventory_fails(self):
        d=copy.deepcopy(self.source)
        d[3]["first_major_4"]["rounds"][1]["transactions"][-1]["token_delta_raw"]="-1"
        with self.assertRaises(ValueError):build(d)

    def test_native_bnb_not_equal_original_wallet_receipt_fails(self):
        d=copy.deepcopy(self.source)
        d[2]["rows"][1]["native_delta_wei"]="1"
        with self.assertRaises(ValueError):build(d)

    def test_forged_gas_must_not_reclassify_roi(self):
        d=copy.deepcopy(self.source)
        d[1]["rows"][0]["receipt_meta"]["gasUsed"]="0x1"
        with self.assertRaises(ValueError):build(d)

    def test_forged_wbnb_mint_original_buy_rejected(self):
        d=copy.deepcopy(self.source)
        d[1]["rows"][0]["receipt_meta"]["selected_wbnb_logs"][0]["data"]="0x1"
        with self.assertRaises(ValueError):build(d)

    def test_missing_signed_historic_tx_from_source_rejected(self):
        d=copy.deepcopy(self.source)
        d[4]["rows"].pop(0)
        with self.assertRaises(ValueError):build(d)

    def test_wrong_ca_or_owner_source_identity_rejected(self):
        d=copy.deepcopy(self.source)
        d[0]["major_exact_CA"]="0x"+"0"*40
        with self.assertRaises(ValueError):build(d)

if __name__=="__main__":
    unittest.main()
