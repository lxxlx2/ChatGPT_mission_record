#!/usr/bin/env python3
"""P4-B all 19 frozen market entrance evidence tests, no hidden profit or miss."""
import copy
import json
import unittest
from bsc_meme_address_model_v1_p4b_market19 import ROOT,build,load

class WholeNineteenMarketEntranceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src=load(ROOT)

    def test_deterministic_source_to_frozen(self):
        actual=build(self.src)
        saved=json.loads((ROOT/"bsc-meme-address-model-v1-p4b-19ca-unified-early-market-buy-evidence-2026-10-14.json").read_text(encoding="utf-8"))
        self.assertEqual(actual,saved)

    def test_19_exact_3_real_16_unresolved(self):
        a=build(self.src)
        s=a["summary"]
        self.assertEqual((s["frozen_major_exact_CAs"],s["original_23_EOA_candidates"],s["full_wallet_CA_denominator"]),(19,23,437))
        self.assertEqual((s["source_original_signed_early_buy_market_witnesses"],
                         s["earlier_signed_buy_witnesses_within_frozen_23"],
                         s["earlier_signed_buy_witnesses_outside_frozen_23"],
                         s["remaining_major_CAs_not_yet_signed_early_buy_audited"]),(3,1,2,16))
        self.assertEqual((s["global_actual_U_and_sell_capacity_fully_qualified"],s["actual_profit_ranks"]),(0,0))
        self.assertEqual(s["production"],"NO_GO")

    def test_market_witnesses_not_collapsed_into_one_quote_currency(self):
        rows=[r for r in build(self.src)["rows"] if r["selected_early_buy_signer"]]
        self.assertEqual({r["token"] for r in rows},{"龙虾","牛来","MARSCOIN"})
        self.assertEqual({r["observed_early_purchase_quote_label"] for r in rows},
                         {"BNB_NATIVE","Q3B (current metadata only)","S5B (current metadata only)"})
        self.assertEqual([r["selected_signer_is_in_original_23"] for r in rows].count(True),1)
        self.assertEqual([r["selected_signer_is_in_original_23"] for r in rows].count(False),2)

    def test_all_nineteen_market_opportunity_and_economic_profit_unresolved(self):
        rows=build(self.src)["rows"]
        self.assertTrue(all(r["actual_global_observer_market_U"]=="UNRESOLVED"
                            and r["historical_signed_roundtrip_PnL"]=="UNRESOLVED"
                            and r["qualified_23_wallet_missed_profitable_U"]=="UNRESOLVED"
                            and r["following_at_1_5_15min"]=="UNRESOLVED"
                            and r["production"]=="NO_GO" for r in rows))

    def test_missing_one_market_ca_rejected(self):
        d=copy.deepcopy(self.src)
        d[0]["rows"].pop(0)
        with self.assertRaises(ValueError):build(d)

    def test_wrong_23_candidate_source_rejected(self):
        d=copy.deepcopy(self.src)
        d[4]["summary"]["wallets"]=24
        with self.assertRaises(ValueError):build(d)

    def test_forged_flap_external_signer_part_of_wallet_set_rejected(self):
        d=copy.deepcopy(self.src)
        d[1]["rows"][0]["original_EOA_signer"]=d[4]["wallets"][0]["wallet"]
        with self.assertRaises(ValueError):build(d)

    def test_route_purchase_not_disconnected_from_token_receipt(self):
        d=copy.deepcopy(self.src)
        d[1]["rows"][0]["final_ERC20_recipient"]="0x"+"1"*40
        with self.assertRaises(ValueError):build(d)

    def test_dex_math_cannot_be_promoted_to_realized_fill(self):
        d=copy.deepcopy(self.src)
        d[3]["rows"][0]["historical_token_transfer_simulation"]="PERFORMED"
        with self.assertRaises(ValueError):build(d)

if __name__=="__main__":
    unittest.main()
