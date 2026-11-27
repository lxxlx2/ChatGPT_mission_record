#!/usr/bin/env python3
"""DDAC original signed early Dragon/龙虾 Four.meme purchase causal event gates."""
import copy
import json
import unittest
from bsc_meme_address_model_v1_p4b_dragon_ddac import ROOT,load,build

class DragonDDACLaunchpadTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.docs=load(ROOT)

    def test_exact_evidence_hashes_and_frozen_json(self):
        actual=build(self.docs)
        expected=json.loads((ROOT/"bsc-meme-address-model-v1-p4b-dragon-ddac-real-pre-dex-buy-2026-10-14.json").read_text(encoding="utf-8"))
        self.assertEqual(actual,expected)

    def test_buyer_signed_and_recipient_with_real_quote_amount(self):
        f=build(self.docs)["fact"]
        self.assertEqual(f["buyer_EOA"],"0xddac928a240bdace3994c2cc0783d4e29a002127")
        self.assertEqual(f["TokenPurchase_account"],f["buyer_EOA"])
        self.assertEqual(f["original_erc20_transfer_raw_amount"],f["TokenPurchase_amount_token_raw"])
        self.assertEqual(f["buyer_original_tx_value_wei"],"800000000000000000")
        self.assertEqual(f["TokenPurchase_cost_quote_wei"],"784158415841584155")
        self.assertEqual(f["TokenPurchase_protocol_fee_wei"],"7841584158415841")
        self.assertEqual(f["creation_to_purchase_delay_blocks"],6)
        self.assertEqual(f["launchTime_to_purchase_seconds"],4)
        self.assertEqual(f["DEX_liquidity_after_purchase_blocks"],352)

    def test_real_buy_not_realized_profit_or_followable_alpha(self):
        x=build(self.docs)
        self.assertEqual(x["summary"]["proven_realized_profit"],0)
        self.assertEqual(x["summary"]["qualified_first_global_U"],0)
        self.assertEqual(x["summary"]["production"],"NO_GO")
        for field in ["sell_status","gross_cashflow_after_sell","realized_net_PnL",
                      "third_party_follower_1_5_15m","first_global_any_venue_buy"]:
            self.assertEqual(x["fact"][field],"UNRESOLVED")
        self.assertEqual(x["fact"]["receipt_response_status"],"UNRESOLVED_TRUNCATED")

    def test_false_beneficiary_cannot_be_promoted(self):
        d=copy.deepcopy(self.docs)
        d[2]["rows"][1]["transaction"]["from"]="0x"+"1"*40
        with self.assertRaises(ValueError):build(d)

    def test_faked_token_transfer_amount_rejected(self):
        d=copy.deepcopy(self.docs)
        transfer=next(x for x in d[3]["rows"] if x["token"]=="龙虾")["transfers"][3]
        transfer["rawContract"]["value"]="0x1"
        with self.assertRaises(ValueError):build(d)

    def test_unrelated_tx_manager_purchase_rejected(self):
        d=copy.deepcopy(self.docs)
        d[1]["rows"][1]["original_target_events"][0]["transactionHash"]="0x"+"a"*64
        with self.assertRaises(ValueError):build(d)

    def test_fake_cost_higher_than_signed_value_rejected(self):
        d=copy.deepcopy(self.docs)
        d[2]["rows"][1]["transaction"]["value"]="0x1"
        with self.assertRaises(ValueError):build(d)

    def test_fabricated_early_dex_block_rejected(self):
        d=copy.deepcopy(self.docs)
        next(x for x in d[5]["rows"] if x["token"]=="龙虾")["first_scoped_dex_positive_block"]-=1000
        with self.assertRaises(ValueError):build(d)

if __name__=="__main__":
    unittest.main()
