#!/usr/bin/env python3
"""P4 first four source-frozen creation timing and risk gate tests."""
import copy
import json
import unittest

from bsc_meme_address_model_v1_p4_priority4_competitors import ROOT, load, build

class PriorityCompetitorsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.docs=load(ROOT)

    def test_exact_source_replay_matches_committed(self):
        actual=build(self.docs)
        expected=json.loads((ROOT/"bsc-meme-address-model-v1-p4-priority4-competitor-creation-verified-2026-10-14.json").read_text(encoding="utf-8"))
        self.assertEqual(actual,expected)

    def test_exact_four_blocks_three_active_one_out_of_range(self):
        d=build(self.docs)
        self.assertEqual([x["create_block"] for x in d["rows"]],
                         [116207845,116156658,115919188,112642885])
        self.assertEqual([x["creation_active"] for x in d["rows"]],
                         [True,True,False,True])
        self.assertEqual((d["summary"]["active_at_creation"],d["summary"]["inactive_at_creation"]),(3,1))
        self.assertTrue(all(x["create_block"]<x["baseline_v2_wbnb_block"] for x in d["rows"]))

    def test_deployed_pool_and_mint_does_not_mean_active_v3(self):
        d=build(self.docs)
        x=d["rows"][2]
        self.assertEqual(x["token"],"牛来")
        self.assertEqual(x["protocol"],"V3")
        self.assertEqual(x["fee_pips"],10000)
        self.assertEqual(x["v3_liquidity_at_creation_wei"],"0")
        self.assertIsNone(x["first_positive_in_this_pool_block"])
        self.assertEqual(x["earliest_global_tradability"],"UNRESOLVED")

    def test_no_false_global_entry_or_alpha(self):
        d=build(self.docs)
        self.assertEqual(d["summary"]["full_market_earliest_tradability"],0)
        self.assertEqual(d["summary"]["qualified_misses"],0)
        self.assertEqual(d["summary"]["production"],"NO_GO")
        self.assertTrue(all(r["sellability_and_tax"]=="UNRESOLVED"
                            and r["qualified_wallet_miss"]=="UNRESOLVED"
                            for r in d["rows"]))

    def test_wrong_creation_event_address_fails(self):
        d=copy.deepcopy(self.docs)
        d[2]["records"][0]["first_creator_event"]["address"]="0x"+"f"*40
        with self.assertRaises(ValueError):
            build(d)

    def test_fake_mint_different_transaction_fails(self):
        d=copy.deepcopy(self.docs)
        m=next(x for x in d[3]["records"][0]["pool_creation_block_events"]
               if x["topics"][0].startswith("0x7a53080b"))
        m["transactionHash"]="0x"+"1"*64
        with self.assertRaises(ValueError):
            build(d)

    def test_injected_liquidity_nonzero_at_zero_v3_fails(self):
        d=copy.deepcopy(self.docs)
        d[3]["records"][0]["pool_creation_state"]["liquidity"]="0x"+"0"*63+"1"
        with self.assertRaises(ValueError):
            build(d)

    def test_fake_creation_bound_fails(self):
        d=copy.deepcopy(self.docs)
        d[1]["to_bounds"][0]["hi"]+=1
        with self.assertRaises(ValueError):
            build(d)

if __name__=="__main__":
    unittest.main()
