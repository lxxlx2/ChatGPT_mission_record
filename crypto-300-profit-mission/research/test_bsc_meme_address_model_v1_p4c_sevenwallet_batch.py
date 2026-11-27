import json
import unittest
from bsc_meme_address_model_v1_p4c_sevenwallet_batch import ROOT,build,load

class FrozenSevenWalletBatchTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.docs=load(ROOT)

    def test_exact_source_ledger(self):
        a=build(self.docs)
        b=json.loads((ROOT/"bsc-meme-address-model-v1-p4c-sevenwallet-balanced-signers-native-outcome-2026-10-15.json").read_text(encoding="utf-8"))
        self.assertEqual(a,b)

    def test_original_seven_wallets_and_economic_qualifications(self):
        a=build(self.docs)
        s=a["summary"]
        self.assertEqual((s["frozen_recent_active_wallets"],s["preselected_rounds_this_batch"],s["distinct_economic_batch_wallets"]),(7,5,4))
        self.assertEqual((s["source_owner_signature_reverified_transactions"],s["unique_historical_native_balance_blocks"]),(14,11))
        self.assertEqual((s["full_original_receipt_success_recovered"],s["origin_receipt_truncated"]),(6,8))
        self.assertEqual((s["selected_native_positive_block_scope_rounds"],s["selected_native_negative_block_scope_rounds"]),(4,1))
        self.assertEqual((s["independently_settled_native_positive_rounds"],s["prior_DDAC_native_negative_rounds_retained"]),(2,1))
        self.assertEqual((s["unclosed_positive_or_negative_scope_only"],s["control_wallets_without_round"]),(3,2))
        self.assertFalse(s["public_follower_1_5_15_eligible"])
        self.assertFalse(s["profit_rank_ready"])
        self.assertEqual(s["production"],"NO_GO")

    def test_no_qualification_from_only_signed_recent_activity(self):
        a=build(self.docs)
        self.assertEqual(len(a["activity_only_controls"]),2)
        self.assertTrue(all(v["profit_status"]=="UNRESOLVED" for v in a["activity_only_controls"]))
        self.assertEqual(sum(x["actual_settled_owner_native_round_status"]=="UNRESOLVED_ECONOMIC_CASHFLOW_OR_FULL_RECEIPTS" for x in a["rounds"]),3)

if __name__=="__main__":
    unittest.main()
