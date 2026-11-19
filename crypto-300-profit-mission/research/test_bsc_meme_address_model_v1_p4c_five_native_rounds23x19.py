import copy,json,unittest
from bsc_meme_address_model_v1_p4c_five_native_rounds23x19 import ROOT,build,load,MIXED,NA

class P4CFiveRoundsDistinctCells(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.src=load(ROOT)
    def test_replay(self):
        target=json.loads((ROOT/"bsc-meme-address-model-v1-p4c-23x19-five-native-rounds-mixed239e-2026-10-15.json").read_text(encoding="utf-8"))
        self.assertEqual(build(self.src),target)
    def test_3_true_wins_2_losses_but_only_four_wallet_CA_cells(self):
        a=build(self.src);s=a["summary"]
        self.assertEqual((s["frozen_wallets"],s["frozen_major_exact_CAs"],s["total_wallet_CA_cells"]),(23,19,437))
        self.assertEqual((s["source_verified_original_native_rounds"],s["verified_native_positive_original_rounds"],s["verified_native_negative_original_rounds"]),(5,3,2))
        self.assertEqual((s["reviewed_distinct_wallet_CA_cells"],s["not_economically_audited_cells"]),(4,433))
        self.assertEqual((s["wallets_with_positive_original_rounds"],s["wallets_with_both_positive_and_negative_original_rounds"]),(2,1))
        self.assertEqual(s["wallets_with_profitable_original_rounds_in_two_distinct_major_CA"],1)
        self.assertEqual(s["original_MARSCOIN_inventory_closed_but_profit_unknown_rounds"],2)
        self.assertEqual(s["public_observer_follower_qualified_signals"],0)
        self.assertFalse(s["profit_rank_ready"])
        self.assertEqual(s["production"],"NO_GO")
    def test_239e_same_CA_mixed_not_two_unique_winners(self):
        a=build(self.src)
        w=next(w for w in a["wallets"] if w["wallet"]=="0x239e74bfbd02d71cdc70fecc2d505dc13acfb337")
        self.assertEqual(w["closed_native_round_flags"].count(MIXED),1)
        self.assertEqual(w["closed_native_round_flags"].count(NA),18)
        self.assertEqual([x["net_wei"] for x in a["verified_economic_rounds"][-2:]],["-15332805033002259","22647938898252522"])
    def test_marscoin_quote_unknown_not_promoted(self):
        a=build(self.src)
        self.assertEqual(len(a["unresolved_economic_controls"]),2)
        self.assertTrue(all(x["status"]=="OWNER_TOKEN_CLOSE_BUT_NONNATIVE_QUOTE_GAS_UNRESOLVED" for x in a["unresolved_economic_controls"]))
    def test_false_marscoin_profit_fails(self):
        d=copy.deepcopy(self.src)
        d[2]["rounds"][0]["qualified_realized_net_profit"]=True
        with self.assertRaises(ValueError):build(d)
    def test_239e_removed_negative_round_fails(self):
        d=copy.deepcopy(self.src)
        d[1]["rounds"].pop(0)
        with self.assertRaises(ValueError):build(d)
if __name__=="__main__":unittest.main()
