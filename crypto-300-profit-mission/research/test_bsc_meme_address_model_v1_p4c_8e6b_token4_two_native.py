import copy,json,unittest
from bsc_meme_address_model_v1_p4c_8e6b_token4_two_native import ROOT,build,load

class Token4OriginalMixed19(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.source=load(ROOT)
    def test_replay_matches_byte_pinned_original_19(self):
        expected=json.loads((ROOT/"bsc-meme-address-model-v1-p4c-8e6b-token4-two-settled-source-audit-2026-10-15.json").read_text(encoding="utf-8"))
        self.assertEqual(build(self.source),expected)
    def test_both_original_signs_not_cherry_picked_and_no_followable_alpha(self):
        x=build(self.source)
        self.assertEqual([r["p2_index"] for r in x["rounds"]],[16,17])
        self.assertEqual([r["original_tx_count"] for r in x["rounds"]],[2,17])
        self.assertEqual([r["original_owner_native_net_wei"] for r in x["rounds"]],
                         ["-117977426190152496","13282964879793219111"])
        self.assertEqual([r["original_owner_economic_sign"] for r in x["rounds"]],["NEGATIVE","POSITIVE"])
        self.assertEqual(x["summary"]["independently_rechecked_full_transactions"],5)
        self.assertEqual(x["summary"]["original_owner_signed_successful_txs"],19)
        self.assertEqual(x["summary"]["new_followable_signals"],0)
        self.assertEqual(x["summary"]["production"],"NO_GO")
    def test_original_gas_and_route_residual_are_never_zeroed(self):
        x=build(self.source)
        self.assertTrue(all(int(r["paid_gas_wei"])>0 and int(r["route_residual_wei"])>0 for r in x["rounds"]))
        self.assertEqual(sum(len([s for s in x["original_transactions"] if s["p2_index"]==r["p2_index"]]) for r in x["rounds"]),19)
    def test_wrong_independent_live_native_balance_rejected(self):
        x=copy.deepcopy(self.source)
        x[1]["rows"][0]["native_delta_wei"]="0"
        with self.assertRaises(ValueError):build(x)
    def test_forged_live_owner_signer_rejected(self):
        x=copy.deepcopy(self.source)
        x[2]["rows"][0]["original_transaction"]["from"]="0x"+"0"*40
        with self.assertRaises(ValueError):build(x)
    def test_wrong_original_full_receipt_gas_rejected(self):
        x=copy.deepcopy(self.source)
        x[1]["rows"][0]["receipt_meta"]["gasUsed"]="0x1"
        with self.assertRaises(ValueError):build(x)
    def test_live_quote_paired_deposit_mismatch_rejected(self):
        x=copy.deepcopy(self.source)
        x[1]["rows"][0]["receipt_meta"]["selected_wbnb_logs"][0]["data"]="0x1"
        with self.assertRaises(ValueError):build(x)
    def test_old_fee_route_residual_spoof_rejected(self):
        x=copy.deepcopy(self.source)
        x[4]["rows"][2]["gross_minus_buy_gas_native_wei"]="0"
        with self.assertRaises(ValueError):build(x)
    def test_source_negative_round_must_remain(self):
        x=copy.deepcopy(self.source)
        x[0]["original_rounds"].pop(0)
        with self.assertRaises(ValueError):build(x)
    def test_source_second_sell_missing_rejected(self):
        x=copy.deepcopy(self.source)
        x[3]["first_major_4"]["rounds"][1]["transactions"].pop()
        with self.assertRaises((ValueError,IndexError)):build(x)
if __name__=="__main__":unittest.main()
