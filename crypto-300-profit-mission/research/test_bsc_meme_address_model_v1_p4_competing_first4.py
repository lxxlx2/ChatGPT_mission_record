#!/usr/bin/env python3
"""P4 historical four alternative market pools: no selective alpha promotion."""
import copy
import json
import unittest

from bsc_meme_address_model_v1_p4_competing_first4 import ROOT, build, load, CASES


class P4FirstFourCompetingPoolsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.docs=load(ROOT)

    def test_replay_matches_immutable_git_matrix(self):
        actual=build(self.docs)
        expected=json.loads((ROOT/"bsc-meme-address-model-v1-p4-priority4-competing-first-active-2026-10-14.json").read_text(encoding="utf-8"))
        self.assertEqual(actual,expected)

    def test_all_four_competing_pools_have_an_exact_first_active_block(self):
        x=build(self.docs)
        s=x["summary"]
        self.assertEqual((s["frozen_competitor_pools"],s["first_active_block_evidence"],
                          s["positive_at_creation"],s["delayed_in_range_active"]), (4,4,3,1))
        self.assertEqual(len(x["rows"]),len(CASES))
        self.assertEqual(len(x["source_manifest"]),3)
        self.assertEqual(
            [(r["token"],r["first_active_liquidity_block"]) for r in x["rows"]],
            [("牛来",116207845),("牛来",116156658),("牛来",115919205),("MARSCOIN",112642885)])

    def test_delayed_niulai_has_no_earlier_pool_event_and_17_block_gap(self):
        x=build(self.docs)
        r=next(r for r in x["rows"] if r["delay_blocks"]==17)
        self.assertEqual(r["pool_creation_block"],115919188)
        self.assertEqual(r["source_event_kind"],"V3_FIRST_IN_RANGE_MINT_AFTER_CREATION")
        proof=self.docs[1]
        self.assertEqual(len(proof["windows"]),10)
        self.assertEqual(sum(len(p["logs"]) for p in proof["windows"]),5)
        self.assertEqual(proof["first_active_block"],115919205)

    def test_preexisting_liquidity_does_not_claim_globally_first_buy_or_profit(self):
        x=build(self.docs)
        self.assertEqual(x["summary"]["qualified_misses"],0)
        self.assertEqual(x["summary"]["production"],"NO_GO")
        self.assertTrue(all(
            r["first_globally_tradable"]=="UNRESOLVED"
            and r["gas_slippage_and_token_selling"]=="UNRESOLVED"
            and r["qualifying_missed_trade"]=="UNRESOLVED"
            and r["follower_alpha"]=="UNRESOLVED"
            and r["precedes_known_V2_WBNB_first_reserve_by_blocks"]>0
            for r in x["rows"]))

    def test_fake_factory_identity_rejected(self):
        d=copy.deepcopy(self.docs)
        d[0]["records"][0]["event"]["data"]="0x"+"0"*128
        with self.assertRaises(ValueError):
            build(d)

    def test_missing_first_in_range_coverage_rejected(self):
        d=copy.deepcopy(self.docs)
        d[1]["windows"].pop(0)
        with self.assertRaises(ValueError):
            build(d)

    def test_fake_positive_on_creation_rejected(self):
        d=copy.deepcopy(self.docs)
        d[0]["records"][2]["creation_block_state"]["liquidity_raw"]="1"
        with self.assertRaises(ValueError):
            build(d)

    def test_wrong_delayed_active_liquidity_block_rejected(self):
        d=copy.deepcopy(self.docs)
        d[1]["first_active_block"]+=1
        with self.assertRaises(ValueError):
            build(d)


if __name__ == "__main__":
    unittest.main()
