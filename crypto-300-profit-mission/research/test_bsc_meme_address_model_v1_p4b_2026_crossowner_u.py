import copy
import unittest

from bsc_meme_address_model_v1_p4b_2026_crossowner_u import build, load, CASES, ROOT

class Frozen2026FiveWalletGate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources=load(ROOT)

    def test_all_wallets_and_observer_U_unresolved(self):
        r=build(self.sources)
        s=r["summary"]
        self.assertEqual((s["full_wallet_CA_denominator"],s["selected_wallets"],s["selected_major_CAs"]),(437,5,3))
        self.assertEqual(s["qualified_observer_executable_U"],0)
        self.assertEqual(s["qualified_follow_PnL"],0)
        self.assertEqual(s["P5"],"BLOCKED")
        self.assertEqual(s["production"],"NO_GO")
        self.assertTrue(all(x["first_observer_visible_executable_buy_and_sell_U"]=="UNRESOLVED" for x in r["cases"]))

    def test_positive_negative_and_unknown_not_lost(self):
        rows={r["wallet_label"]:r for r in build(self.sources)["cases"]}
        self.assertEqual((rows["239E"]["source_signed_native_positive"],rows["239E"]["source_signed_native_negative"]),(1,1))
        self.assertEqual(rows["877AF"]["source_signed_native_rounds"],0)
        self.assertEqual(rows["DDAC"]["early_sampled_buy_signer"],rows["DDAC"]["wallet"])
        self.assertNotEqual(rows["877AF"]["follower_1_5_15min_PnL"],0)

    def test_duplicate_owners_rejected(self):
        changed=list(CASES)
        changed[4]=changed[0]
        with self.assertRaises(ValueError):
            build(self.sources,tuple(changed))

    def test_made_up_public_U_rejected(self):
        changed=copy.deepcopy(self.sources)
        changed[2]["rows"][14]["actual_global_observer_market_U"]="QUALIFIED"
        with self.assertRaises(ValueError):
            build(changed)

    def test_made_up_follower_count_rejected(self):
        changed=copy.deepcopy(self.sources)
        changed[3]["summary"]["public_observer_follower_qualified_signals"]=1
        with self.assertRaises(ValueError):
            build(changed)

    def test_loser_deleted_rejected(self):
        changed=copy.deepcopy(self.sources)
        changed[3]["verified_economic_rounds"]=[
            x for x in changed[3]["verified_economic_rounds"]
            if not (x["wallet"].startswith("0x239e") and int(x["net_wei"])<0)]
        with self.assertRaises(ValueError):
            build(changed)

if __name__=="__main__":
    unittest.main()
