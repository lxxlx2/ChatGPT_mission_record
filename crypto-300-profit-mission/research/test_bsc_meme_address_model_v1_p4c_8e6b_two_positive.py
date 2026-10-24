import json
import unittest
from bsc_meme_address_model_v1_p4c_8e6b_two_positive import ROOT, build, load

class SourceVerifiedTwoMajorPositiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.docs = load(ROOT)

    def test_exact_frozen_replay(self):
        expected = json.loads((ROOT / "bsc-meme-address-model-v1-p4c-8e6b-hajimi-dragon-two-verified-native-positive-2026-10-15.json").read_text(encoding="utf-8"))
        self.assertEqual(build(self.docs), expected)

    def test_actual_signed_wbnb_gas_and_closed_inventory(self):
        result = build(self.docs)
        self.assertEqual(result["summary"]["source_proven_signed_positive_native_rounds"], 2)
        self.assertEqual(result["summary"]["original_full_success_tx_receipts"], 5)
        self.assertEqual(result["summary"]["source_proven_native_net_sum_wei"], "521893275237019248")
        self.assertEqual([x["actual_native_round_net_wei"] for x in result["rounds"]], ["268592992917629933", "253300282319389315"])
        self.assertTrue(all(x["residual_raw"] == "0" for x in result["rounds"]))

    def test_no_profit_rank_or_follower_promoted(self):
        result = build(self.docs)
        self.assertFalse(result["summary"]["profit_ranking_ready"])
        self.assertEqual(result["summary"]["qualified_observer_trades"], 0)
        self.assertEqual(result["summary"]["production"], "NO_GO")
        self.assertTrue(all(x["owner_observer_follower_1_5_15min"] == "UNRESOLVED" for x in result["rounds"]))

if __name__ == "__main__":
    unittest.main()
