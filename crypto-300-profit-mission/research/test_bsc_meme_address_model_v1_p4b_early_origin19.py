#!/usr/bin/env python3
"""All 19 major CA early-history denominator and protocol uncertainty guards."""
import copy
import json
import unittest
from bsc_meme_address_model_v1_p4b_early_origin19 import ROOT,build,load

class AllMajorPreDexOriginTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d=load(ROOT)

    def test_exact_source_to_frozen_replay(self):
        actual=build(self.d)
        frozen=json.loads((ROOT/"bsc-meme-address-model-v1-p4b-19ca-early-launch-origin-2026-10-14.json").read_text(encoding="utf-8"))
        self.assertEqual(actual,frozen)

    def test_19_all_early_transfer_no_fake_trade(self):
        result=build(self.d)
        self.assertEqual(len(result["rows"]),19)
        self.assertEqual((result["summary"]["canonical_fourmeme_v2_at_pre_scoped_dex"],result["summary"]["unknown_or_empty_helper"]),(12,7))
        self.assertEqual(result["summary"]["token_transfer_initial_block_precedes_scoped_dex"],19)
        self.assertEqual(result["summary"]["actually_proven_first_market_U"],0)
        self.assertTrue(all(r["actual_first_launchpad_token_purchase"]=="UNRESOLVED"
                            and r["first_global_buy_and_sell_U"]=="UNRESOLVED"
                            and r["follower_pnl"]=="UNRESOLVED" for r in result["rows"]))

    def test_2026_three_token_negative_unknowns(self):
        rows=build(self.d)["rows"]
        self.assertEqual(next(r for r in rows if r["token"]=="龙虾")["pre_dex_helper_status"],"FOUR_MEME_V2_CANONICAL")
        self.assertEqual(next(r for r in rows if r["token"]=="牛来")["pre_dex_helper_status"],"NO_RECOGNIZED_HELPER_MANAGER_AT_PROBE")
        self.assertEqual(next(r for r in rows if r["token"]=="MARSCOIN")["pre_dex_helper_status"],"NO_RECOGNIZED_HELPER_MANAGER_AT_PROBE")

    def test_dont_drop_one_original_CA(self):
        d=copy.deepcopy(self.d)
        d[10]["rows"].pop()
        with self.assertRaises(ValueError):build(d)

    def test_early_transfer_later_than_selected_liquidity_rejected(self):
        d=copy.deepcopy(self.d)
        d[8]["rows"][0]["transfers"][0]["blockNum"]="0xffffffffffffffff"
        with self.assertRaises(ValueError):build(d)

    def test_conflicting_helper_source_provenance_rejected(self):
        d=copy.deepcopy(self.d)
        d[2]["rows"][0]["helper_read_block"]+=1
        with self.assertRaises(ValueError):build(d)

    def test_wrong_token_contract_transfer_rejected(self):
        d=copy.deepcopy(self.d)
        d[8]["rows"][0]["transfers"][0]["rawContract"]["address"]="0x"+"f"*40
        with self.assertRaises(ValueError):build(d)

    def test_first_ten_is_never_all_trades(self):
        a=build(self.d)["rows"]
        self.assertTrue(any(x["source_page_has_more"] for x in a))
        self.assertTrue(all(x["source_transfer_page_count"]<=10 for x in a))

if __name__=="__main__":
    unittest.main()
