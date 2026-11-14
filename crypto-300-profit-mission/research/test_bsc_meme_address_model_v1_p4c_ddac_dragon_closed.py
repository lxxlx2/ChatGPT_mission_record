#!/usr/bin/env python3
"""P4-C DDAC original 龙虾 fully closed signed trade negative-economic-control tests."""
import copy
import json
import unittest
from bsc_meme_address_model_v1_p4c_ddac_dragon_closed import ROOT,build,load

class DragonClosedOriginalNativeNegativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d=load(ROOT)

    def test_exact_original_git_economic_source_replay(self):
        got=build(self.d)
        expected=json.loads((ROOT/"bsc-meme-address-model-v1-p4c-dragon-ddac-closed-native-loss-2026-10-15.json").read_text(encoding="utf-8"))
        self.assertEqual(got,expected)

    def test_actual_signed_sale_and_original_token_close(self):
        a=build(self.d)
        f=a["round"]
        self.assertEqual(f["entry_token_amount_raw"],f["exit_token_amount_raw"])
        self.assertEqual(f["residual_token_raw"],"0")
        self.assertEqual(f["elapsed_blocks"],24)
        self.assertEqual(f["exit_venue_verified_successful"],"FOUR_MEME_TOKENSALE")
        self.assertEqual(a["summary"]["actual_negative_native_owner_rounds"],1)
        self.assertEqual(a["summary"]["actual_positive_native_owner_rounds"],0)

    def test_wallet_native_loss_and_exact_approval_sale_gas(self):
        f=build(self.d)["round"]
        self.assertEqual(f["native_buy_block_debit_wei"],"809007576999999996")
        self.assertEqual(f["native_exit_block_credit_after_gas_wei"],"716837961485385724")
        self.assertEqual(f["exit_block_total_signed_gas_wei"],"30978840000000")
        self.assertEqual(f["native_closed_owner_round_net_wei"],"-92169615514614272")
        self.assertEqual(f["native_closed_owner_round_roi_bps_trunc"],-1139)
        self.assertEqual(f["exit_event_implied_prepay_credit_wei"],f["exit_native_balance_plus_gas_wei"])
        self.assertEqual(f["native_closed_owner_round_classification"],"REALIZED_NEGATIVE_BNB_WINDOW")

    def test_no_wider_profit_ranking_or_followability_promoted(self):
        a=build(self.d)
        self.assertEqual((a["summary"]["frozen_wallets"],a["summary"]["frozen_major_CAs"]), (23,19))
        self.assertEqual(a["summary"]["remaining_wallet_CAs_not_audited_for_economic_closure"],436)
        self.assertEqual(a["summary"]["market_U_fully_qualified"],0)
        self.assertEqual(a["summary"]["live_production"],"NO_GO")
        self.assertEqual(a["round"]["buyer_follower_entry_after_1_5_15min"],"UNRESOLVED")
        self.assertEqual(a["round"]["global_first_executable_market_U"],"UNRESOLVED")

    def test_forged_sale_account_or_amount_rejected(self):
        d=copy.deepcopy(self.d)
        sale=next(x["receipt"] for x in d[4]["rows"] if len(x["receipt"]["logs"])==7)
        event=next(z for z in sale["logs"] if z["topics"][0].startswith("0x0a5575b3"))
        old=event["data"]
        event["data"]=old[:2+64]+("0"*64)+old[2+128:]
        with self.assertRaises(ValueError):build(d)
        d=copy.deepcopy(self.d)
        sale=next(x["receipt"] for x in d[4]["rows"] if len(x["receipt"]["logs"])==7)
        event=next(z for z in sale["logs"] if z["topics"][0].startswith("0x0a5575b3"))
        old=event["data"]
        event["data"]=old[:2+64*3]+("0"*64)+old[2+64*4:]
        with self.assertRaises(ValueError):build(d)

    def test_wrong_original_signed_gas_rejected(self):
        d=copy.deepcopy(self.d)
        sale=next(x["receipt"] for x in d[4]["rows"] if len(x["receipt"]["logs"])==7)
        sale["gasUsed"]="0x0"
        with self.assertRaises(ValueError):build(d)

    def test_balance_ledger_cannot_fabricate_positive_pnl(self):
        d=copy.deepcopy(self.d)
        d[2]["balances"][3]["balance_wei"]="999999999999999999999"
        with self.assertRaises(ValueError):build(d)

    def test_extra_signed_outbound_changes_denominator(self):
        d=copy.deepcopy(self.d)
        d[2]["owner_external_source_activity"][1]["transfers"].append(copy.deepcopy(d[2]["owner_external_source_activity"][1]["transfers"][0]))
        with self.assertRaises(ValueError):build(d)

    def test_missing_actual_four_manager_sale_event_rejected(self):
        d=copy.deepcopy(self.d)
        sale=next(x["receipt"] for x in d[4]["rows"] if len(x["receipt"]["logs"])==7)
        sale["logs"]=[z for z in sale["logs"] if not z["topics"][0].startswith("0x0a5575b3")]
        with self.assertRaises(ValueError):build(d)

    def test_external_native_inflow_not_hidden(self):
        d=copy.deepcopy(self.d)
        d[3]["external_inbound"][1]["pageKey"]="nonempty"
        with self.assertRaises(ValueError):build(d)

    def test_unreviewed_wallets_still_not_labeled_negative(self):
        d=copy.deepcopy(self.d)
        d[5]["summary"]["wallets"]=22
        with self.assertRaises(ValueError):build(d)

if __name__=="__main__":
    unittest.main()
