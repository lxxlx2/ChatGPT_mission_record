#!/usr/bin/env python3
"""V1 23-wallet x 19-major CA actual native BNB economic evidence guards."""
import copy
import json
import unittest
from bsc_meme_address_model_v1_p4c_closed_grid23x19 import ROOT,build,load

class FrozenEconomicScope23x19(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src=load(ROOT)

    def test_exact_source_pinned_replay(self):
        actual=build(self.src)
        frozen=json.loads((ROOT/"bsc-meme-address-model-v1-p4c-23x19-native-economic-evidence-grid-2026-10-15.json").read_text(encoding="utf-8"))
        self.assertEqual(actual,frozen)

    def test_only_one_real_negative_other_cells_unaudited(self):
        a=build(self.src)
        s=a["summary"]
        self.assertEqual((s["frozen_wallet_candidates"],s["frozen_major_exact_CAs"],s["implicit_wallet_CAs"]),(23,19,437))
        self.assertEqual((s["verified_native_negative_rounds"],s["verified_native_positive_rounds"],s["not_economically_audited_cells"]),(1,0,436))
        self.assertEqual(s["prior_2026_recent_signed_swap_wallets"],7)
        self.assertFalse(s["profit_rank_ready"])
        self.assertEqual(s["qualified_public_entry_follower_signals"],0)
        self.assertEqual(s["production"],"NO_GO")

    def test_negative_result_is_ddac_dragon_only(self):
        a=build(self.src)
        r=a["verified_closed_rounds"]
        self.assertEqual(len(r),1)
        self.assertEqual(r[0]["owner"],"0xddac928a240bdace3994c2cc0783d4e29a002127")
        self.assertEqual(r[0]["token"],"龙虾")
        self.assertEqual(r[0]["net_wei"],"-92169615514614272")
        self.assertEqual(r[0]["return_bps_trunc"],-1139)
        idx=next(x["i"] for x in a["markets"] if x["token"]=="龙虾")
        dd=next(x for x in a["wallets"] if x["wallet"]==r[0]["owner"])
        self.assertEqual(dd["closed_native_round_flags"][idx],"REALIZED_NEGATIVE_BNB_CLOSED_OWNER_ROUND")
        self.assertEqual(sum(flag=="REALIZED_NEGATIVE_BNB_CLOSED_OWNER_ROUND"
                             for w in a["wallets"] for flag in w["closed_native_round_flags"]),1)

    def test_p2_p3_activity_not_formal_profit(self):
        a=build(self.src)
        self.assertTrue(all(len(w["closed_native_round_flags"])==19 for w in a["wallets"]))
        self.assertEqual(sum(x["existing_2026_recent_major_swap"] for x in a["wallets"]),7)
        self.assertEqual(sum(flag=="NOT_ECONOMICALLY_AUDITED"
                             for w in a["wallets"] for flag in w["closed_native_round_flags"]),436)

    def test_forged_native_profit_rejected(self):
        d=copy.deepcopy(self.src)
        d[1]["round"]["native_closed_owner_round_net_wei"]="1"
        with self.assertRaises(ValueError):build(d)

    def test_false_tge_followability_rejected(self):
        d=copy.deepcopy(self.src)
        d[1]["round"]["buyer_follower_entry_after_1_5_15min"]="PROVEN"
        with self.assertRaises(ValueError):build(d)

    def test_missing_original_wallet_rejected(self):
        d=copy.deepcopy(self.src)
        d[0]["wallets"].pop(0)
        with self.assertRaises(ValueError):build(d)

    def test_early_owner_original_trade_not_audited_now_rejected(self):
        d=copy.deepcopy(self.src)
        dd=next(w for w in d[0]["wallets"] if w["wallet"]=="0xddac928a240bdace3994c2cc0783d4e29a002127")
        idx=next(m["i"] for m in d[0]["markets"] if m["token"]=="龙虾")
        dd["early_owner_trade_statuses"][idx]="NOT_AUDITED_THIS_STAGE"
        with self.assertRaises(ValueError):build(d)

if __name__=="__main__":
    unittest.main()
