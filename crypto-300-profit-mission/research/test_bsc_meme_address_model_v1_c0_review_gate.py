import copy
import unittest
from bsc_meme_address_model_v1_c0_review_gate import build,load,ROOT,epoch_utc

class C0SourceScopeIntegrity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=load(ROOT)

    def test_five_seven_are_versions_not_additive(self):
        output=build(self.source)
        self.assertEqual((output["five_baseline"]["selected_owner_rounds"],
                          output["five_baseline"]["other_cells"]),(5,433))
        self.assertEqual((output["seven_expanded_review_pending"]["selected_owner_rounds"],
                          output["seven_expanded_review_pending"]["other_cells"]),(7,432))
        self.assertEqual(output["seven_expanded_review_pending"]["already_contains"],["P2_16","P2_17"])
        self.assertEqual(output["production"],"NO_GO")

    def test_wallet_balance_and_token_cashflow_differ(self):
        item=build(self.source)["2025_token4"]
        self.assertEqual(item["selected_token_trades_native_cashflow_wei"],"13164987453603066615")
        self.assertNotEqual(item["whole_wallet_balance_change_first_to_last_spot_wei"],
                            item["selected_token_trades_native_cashflow_wei"])
        self.assertNotEqual(item["unattributed_between_round1_buy_sell_wei"],"0")
        self.assertNotEqual(item["unattributed_between_rounds_wei"],"0")
        self.assertEqual(item["unattributed_flows"],"UNRESOLVED")

    def test_duplicate_round_rejected(self):
        d=copy.deepcopy(self.source)
        d[1]["verified_economic_rounds"][5]["economic_round_key"]="P2_17"
        with self.assertRaises(ValueError):build(d)

    def test_removal_of_loss_rejected(self):
        d=copy.deepcopy(self.source)
        d[1]["verified_economic_rounds"].pop(-2)
        with self.assertRaises(ValueError):build(d)

    def test_forged_native_balance_rejected(self):
        d=copy.deepcopy(self.source)
        d[3]["rows"][1]["native_before"]=str(int(d[3]["rows"][1]["native_before"])+1)
        with self.assertRaises(ValueError):build(d)

    def test_epoch_utc_derived_from_timestamp(self):
        self.assertEqual(epoch_utc(1759291725),"2025-10-01T04:08:45.000Z")
        d=copy.deepcopy(self.source)
        d[5]["rows"][0]["timestamp_unix"]+=100
        with self.assertRaises(ValueError):build(d)

if __name__=="__main__":
    unittest.main()
