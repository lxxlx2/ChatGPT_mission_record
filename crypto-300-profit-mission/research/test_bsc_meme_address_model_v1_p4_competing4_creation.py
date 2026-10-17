#!/usr/bin/env python3
"""Offline frozen four competing early pools and original 17-pool negative controls."""
import copy
import unittest

from bsc_meme_address_model_v1_p4_competing4_creation import ROOT, load, build


class CompetingFourCreationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d=load(ROOT)

    def test_four_bounded_creations_and_seventeen_universe_kept(self):
        r=build(self.d)
        self.assertEqual((r["summary"]["precommitted_competing_pools"],
                          r["summary"]["creation_event_audited"],
                          r["summary"]["unexamined_other_active_competitors"],
                          r["summary"]["inactive_at_reference_retained"]), (17,4,13,5))
        self.assertEqual([x["creation_block"] for x in r["rows"]],
                         [116207845,116156658,115919188,112642885])

    def test_initial_unchanged_usdt_mint_and_v3_active_negative(self):
        rows=build(self.d)["rows"]
        self.assertEqual([x["creation_initial_USDT"] for x in rows],
                         ["20","538.70512342330123571","0","13.18055194816814023"])
        self.assertEqual([x["active_at_creation"] for x in rows],[True,True,False,True])
        self.assertEqual(rows[2]["state"],"MINT_OUT_OF_RANGE_ZERO_ACTIVE_LIQUIDITY_AT_CREATION")
        self.assertGreater(rows[1]["active_liquidity_raw"],"0")
        self.assertEqual(rows[2]["active_liquidity_raw"],"0")

    def test_created_before_v2_is_only_venue_not_alpha(self):
        r=build(self.d)
        self.assertEqual((r["summary"]["positive_active_at_creation"],
                          r["summary"]["initial_mint_but_zero_active"],
                          r["summary"]["earliest_global_executable_trades"],
                          r["summary"]["qualified_wallet_misses"]), (3,1,0,0))
        self.assertEqual(r["summary"]["production"],"NO_GO")
        self.assertTrue(all(x["before_V2_first_reserves_by_blocks"]>0 and
                            x["earliest_whole_market_tradability"]=="UNRESOLVED" and
                            x["transfer_tax_sellability"]=="UNRESOLVED" and
                            x["eligible_missed_opportunity"]=="UNRESOLVED" and
                            x["follower_PnL"]=="UNRESOLVED"
                            for x in r["rows"]))

    def test_fabricated_factory_boundary_rejected(self):
        d=copy.deepcopy(self.d)
        d[8]["to_bounds"][0]["hi"]+=1
        with self.assertRaises(ValueError):
            build(d)

    def test_edited_mint_funding_rejected(self):
        d=copy.deepcopy(self.d)
        row=d[-1]["rows"][1]
        ev=next(x for x in row["creation_pool_logs"]
                if x["topics"][0].startswith("0x7a53080b"))
        ev["data"]="0x"+"0"*256
        with self.assertRaises(ValueError):
            build(d)

    def test_out_of_range_pool_cannot_be_declared_active(self):
        d=copy.deepcopy(self.d)
        q=d[-1]["rows"][2]
        q["state_at_creation"][0]["data"]="0x"+format(10,"064x")
        with self.assertRaises(ValueError):
            build(d)

    def test_scope_not_reduced_to_only_winning_three(self):
        d=copy.deepcopy(self.d)
        d[0]["excluded_from_immediate_early_check_but_still_in_market_universe"].pop()
        with self.assertRaises(ValueError):
            build(d)

    def test_wrong_token_topics_rejected(self):
        d=copy.deepcopy(self.d)
        d[-1]["rows"][3]["creation_event"]["topics"][1]="0x"+"f"*64
        with self.assertRaises(ValueError):
            build(d)


if __name__=="__main__":
    unittest.main()
