#!/usr/bin/env python3
"""P4B 2026 Flap early pool opportunity: causal original signer vs intermediary tests."""
import copy
import json
import unittest
from bsc_meme_address_model_v1_p4b_flap_major2 import ROOT,load,build

class FlapMajorTwoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d=load(ROOT)

    def test_immutable_source_to_output_replay(self):
        exact=json.loads((ROOT/"bsc-meme-address-model-v1-p4b-flap-major2-original-buys-and-quotes-2026-10-14.json").read_text(encoding="utf-8"))
        self.assertEqual(build(self.d),exact)

    def test_two_real_original_signers_not_routers_and_not_candidate_wallets(self):
        rows=build(self.d)["rows"]
        self.assertEqual([r["token"] for r in rows],["牛来","MARSCOIN"])
        self.assertEqual(rows[0]["original_EOA_signer"],"0xb0d0c4c1ee4ba9fac874db4ede587718ad9484d9")
        self.assertEqual(rows[1]["original_EOA_signer"],"0x504ba7b11be98c66a379a3e5de91dc5ab2dde3ea")
        self.assertTrue(all(r["original_EOA_signer"]!=r["portal_TokenBought_intermediate_buyer"]
                            and r["original_EOA_signer"]==r["final_ERC20_recipient"]
                            and r["buyer_in_frozen_23"]=="NO"
                            and r["original_first_purchase_event_match"]=="CONFIRMED" for r in rows))

    def test_distinct_quote_currency_never_combined_into_bnb_or_usd(self):
        rows=build(self.d)["rows"]
        self.assertEqual(rows[0]["actual_quote_CA"],"0x205812cdbed920aff76c6580abd681a46d11efc7")
        self.assertEqual(rows[1]["actual_quote_CA"],"0xbe9d156892e55e7154bcd3cb0fea677f9d3103e1")
        self.assertEqual([r["historical_quote_decimals"] for r in rows],[18,18])
        self.assertEqual([r["buy_tax_bps"] for r in rows],[100,300])
        self.assertEqual([r["sell_tax_bps"] for r in rows],[100,300])
        self.assertTrue(all(r["quote_symbol_is_not_assumed_USD"] for r in rows))

    def test_price_estimate_and_actual_selling_are_not_profit(self):
        result=build(self.d)
        s=result["summary"]
        self.assertEqual((s["tokens"],s["source_original_signed_purchases"],s["postbuy_reverse_math_quote_returns"]),(2,2,2))
        self.assertEqual((s["proven_historic_successful_sells"],s["closed_PnL"],s["qualified_first_market_U"]),(0,0,0))
        self.assertEqual(s["production"],"NO_GO")
        for x in result["rows"]:
            self.assertEqual(x["causal_profit"],"UNRESOLVED")
            self.assertEqual(x["net_fee_plus_quote_from_wallet"],"UNRESOLVED")
            self.assertEqual(x["first_global_U"],"UNRESOLVED")
            self.assertEqual(x["follower_entry_1_5_15min"],"UNRESOLVED")

    def test_sell_evidence_differing_windows_must_stay_distinct(self):
        rows=build(self.d)["rows"]
        self.assertEqual(rows[0]["observed_postbuy_sell_scope"],"COMPLETE_FIRST10_BLOCKS")
        self.assertEqual(rows[1]["observed_postbuy_sell_scope"],"COMPLETE_FIRST_BLOCK_ONLY_TEN_BLOCK_QUERY_TRUNCATED")
        self.assertEqual([x["observed_postbuy_sells_in_scope"] for x in rows],[0,0])

    def test_forged_non_causal_signer_fails(self):
        d=copy.deepcopy(self.d)
        d[1]["rows"][1]["transaction"]["from"]="0x"+"f"*40
        with self.assertRaises(ValueError):build(d)

    def test_forged_original_erc20_recipient_or_amount_fails(self):
        d=copy.deepcopy(self.d)
        rows=next(r for r in d[2]["rows"] if r["token"]=="牛来")["transfers"]
        row=next(x for x in rows if x["to"].lower()=="0xb0d0c4c1ee4ba9fac874db4ede587718ad9484d9")
        row["rawContract"]["value"]="0x123"
        with self.assertRaises(ValueError):build(d)

    def test_tax_or_quote_asset_from_different_CA_fails(self):
        d=copy.deepcopy(self.d)
        row=next(r for r in d[6]["rows"] if r["event"]=="FlapTokenAsymmetricTaxSet")
        log=row["original_creation_tx_events"][0]
        log["data"]=log["data"][:-64]+"0"*64
        with self.assertRaises(ValueError):build(d)

    def test_unsigned_token_or_wrong_topic_cannot_pass(self):
        d=copy.deepcopy(self.d)
        purchase=next(r for r in d[4]["rows"] if r["event"]=="TokenBought" and r["source_target_events"])
        purchase["source_target_events"][0]["topics"][0]="0x"+"0"*64
        with self.assertRaises(ValueError):build(d)

    def test_missing_full_sell_event_source_doesnt_mean_no_sale(self):
        d=copy.deepcopy(self.d)
        row=next(r for r in d[10]["rows"] if r["token"]=="MARSCOIN")
        row["sell_logs_full_window_status"]="COMPLETE"
        with self.assertRaises(ValueError):build(d)

    def test_candidate_membership_without_versioning_rejected(self):
        d=copy.deepcopy(self.d)
        d[12]["wallets"][0]["wallet"]="0xb0d0c4c1ee4ba9fac874db4ede587718ad9484d9"
        with self.assertRaises(ValueError):build(d)

if __name__=="__main__":
    unittest.main()
