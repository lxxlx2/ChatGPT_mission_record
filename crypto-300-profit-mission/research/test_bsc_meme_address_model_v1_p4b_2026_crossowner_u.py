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

    def test_source_unknown_stays_unresolved_not_false_inactive(self):
        rows={r["wallet_label"]:r for r in build(self.sources)["cases"]}
        for label in ("239E","877AF"):
            with self.subTest(wallet=label):
                row=rows[label]
                self.assertEqual(row["recent_signed_swap_state"],"UNRESOLVED")
                self.assertFalse(row["verified_recent_19CA_swap_found"])
                self.assertEqual(row["recent_swap_source_qualification"],"RECENT_SIGNED_SWAP_UNRESOLVED")
                self.assertIsNone(row["recent_swap_utc"])
                self.assertIsNone(row["recent_swap_tx_hash"])
                self.assertNotIn("recent_signed_swap",row)
                self.assertEqual(row["recent_swap_row_CA_attribution"],"NOT_CLAIMED_WALLET_UNIVERSE_ONLY")

    def test_three_confirmed_wallet_witnesses_are_scoped_and_dated(self):
        rows={r["wallet_label"]:r for r in build(self.sources)["cases"]}
        for label in ("DDAC","2ADF","A83B"):
            with self.subTest(wallet=label):
                row=rows[label]
                source=next(w for w in self.sources[0]["wallets"] if w["wallet"]==row["wallet"])
                self.assertEqual(row["recent_signed_swap_state"],"CONFIRMED_ACTIVE")
                self.assertTrue(row["verified_recent_19CA_swap_found"])
                self.assertEqual(row["recent_swap_utc"],source["p3_latest_verified_swap_UTC"])
                self.assertEqual(row["recent_swap_tx_hash"],source["p3_latest_verified_swap_hash"])
                self.assertEqual(row["recent_swap_frozen_window_UTC"],
                                 self.sources[0]["frozen_19CA_snapshot_window"])
                self.assertEqual(row["recent_swap_scope"],
                                 "WALLET_LEVEL_FROZEN_19_EXACT_CAS_NOT_DISPLAYED_ROW_CA")
                self.assertEqual(row["recent_swap_row_CA_attribution"],
                                 "NOT_CLAIMED_WALLET_UNIVERSE_ONLY")
        self.assertNotEqual(rows["A83B"]["recent_swap_tx_hash"],None)
        self.assertEqual(rows["A83B"]["token"],"牛来")
        self.assertNotIn("recent_swap_this_token_verified",rows["A83B"])

    def test_ambiguous_false_witness_missing_qualification_is_rejected(self):
        altered=copy.deepcopy(self.sources)
        row=next(w for w in altered[0]["wallets"] if w["wallet"].startswith("0x239e"))
        row["p4_research_qualification"]="CONFIRMED_NO_SWAP"
        with self.assertRaises(ValueError):
            build(altered)

    def test_false_witness_with_forged_hash_rejected(self):
        altered=copy.deepcopy(self.sources)
        row=next(w for w in altered[0]["wallets"] if w["wallet"].startswith("0x877a"))
        row["p3_latest_verified_swap_hash"]="0x"+"0"*64
        with self.assertRaises(ValueError):
            build(altered)

    def test_confirmed_witness_outside_freeze_rejected(self):
        altered=copy.deepcopy(self.sources)
        row=next(w for w in altered[0]["wallets"] if w["wallet"].startswith("0xa83b"))
        row["p3_latest_verified_swap_UTC"]="2026-10-14T08:37:36Z"
        with self.assertRaises(ValueError):
            build(altered)

    def test_original_frozen_window_required(self):
        altered=copy.deepcopy(self.sources)
        altered[0].pop("frozen_19CA_snapshot_window")
        with self.assertRaises((ValueError,KeyError)):
            build(altered)

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
