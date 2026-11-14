import copy,json,unittest
from bsc_meme_address_model_v1_p4c_seven_rounds23x19 import ROOT,build,load,MIXED,NOT_AUDITED

class SevenHistoricalNativeOutcomesFiveWalletCACells(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.docs=load(ROOT)
    def test_replay_matches_pinned_source(self):
        expected=json.loads((ROOT/"bsc-meme-address-model-v1-p4c-23x19-seven-native-mixed4-2026-10-15.json").read_text(encoding="utf-8"))
        self.assertEqual(build(self.docs),expected)
    def test_rounds_are_not_distinct_wallet_CA_or_alpha(self):
        s=build(self.docs)["summary"]
        self.assertEqual((s["total_wallet_CA_cells"],s["source_verified_original_native_rounds"],s["reviewed_distinct_wallet_CA_cells"],s["not_economically_audited_cells"]),(437,7,5,432))
        self.assertEqual((s["verified_native_positive_original_rounds"],s["verified_native_negative_original_rounds"]),(4,3))
        self.assertEqual(s["wallets_with_positive_original_rounds"],2)
        self.assertEqual(s["wallets_with_both_positive_and_negative_original_rounds"],2)
        self.assertEqual(s["wallets_with_profitable_original_rounds_in_three_distinct_major_CA"],1)
        self.assertEqual(s["source_2025_token4_original_mixed_rounds"],2)
        self.assertEqual(s["source_2026_token4_followable_signals"],0)
        self.assertEqual(s["public_observer_follower_qualified_signals"],0)
        self.assertFalse(s["profit_rank_ready"])
        self.assertEqual(s["production"],"NO_GO")
    def test_original_8e6b_token4_one_wallet_CA_mixed(self):
        a=build(self.docs)
        w=next(x for x in a["wallets"] if x["wallet"]=="0x8e6b3c9c72ca592bbab470f761fa869c174e9ea0")
        self.assertEqual(w["closed_native_round_flags"].count(MIXED),1)
        self.assertEqual(w["closed_native_round_flags"].count(NOT_AUDITED),16)
        self.assertEqual([r["net_wei"] for r in a["verified_economic_rounds"][-2:]],["-117977426190152496","13282964879793219111"])
        self.assertEqual(len(a["unresolved_economic_controls"]),2)
    def test_forbid_losing_token4_round_removed(self):
        d=copy.deepcopy(self.docs)
        d[1]["rounds"].pop(0)
        with self.assertRaises(ValueError):build(d)
    def test_no_double_existing_wallet_CA_flag(self):
        d=copy.deepcopy(self.docs)
        d[0]["wallets"][0]["closed_native_round_flags"][10]=MIXED
        with self.assertRaises(ValueError):build(d)
    def test_no_forged_token4_positive_profit(self):
        d=copy.deepcopy(self.docs)
        d[1]["rounds"][0]["original_owner_native_net_wei"]="10000"
        with self.assertRaises(ValueError):build(d)
    def test_unclosed_wallet_CA_denominator_rejected(self):
        d=copy.deepcopy(self.docs)
        d[0]["summary"]["not_economically_audited_cells"]=432
        with self.assertRaises(ValueError):build(d)
if __name__=="__main__":unittest.main()
