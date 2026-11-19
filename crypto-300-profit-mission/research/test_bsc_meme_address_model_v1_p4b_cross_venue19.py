#!/usr/bin/env python3
"""Prevent premature market-U qualification in P4-B 19-CA cross-venue model."""
import copy
import json
import unittest
from bsc_meme_address_model_v1_p4b_cross_venue19 import ROOT,build,load

class CrossVenue19Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d=load(ROOT)

    def test_exact_frozen_replay(self):
        fresh=build(self.d)
        frozen=json.loads((ROOT/"bsc-meme-address-model-v1-p4b-19ca-cross-venue-candidate-u-2026-10-14.json").read_text(encoding="utf-8"))
        self.assertEqual(fresh,frozen)

    def test_complete_19_plus_all_negative_controls(self):
        a=build(self.d)
        self.assertEqual(len(a["rows"]),19)
        self.assertEqual([x["index"] for x in a["rows"]],list(range(19)))
        s=a["summary"]
        self.assertEqual((s["scoped_active_pools"],s["earlier_competitor_pools"],s["CA_with_scoped_alt_earlier"]),(36,17,12))
        self.assertEqual((s["CAs_where_V2_is_earliest_proven_scoped"],s["other_inactive_at_reference_unknown"]),(7,5))
        self.assertEqual(s["actual_market_U_qualified"],0)
        self.assertEqual(s["production"],"NO_GO")

    def test_scoped_market_is_never_global_or_profitable_signal(self):
        a=build(self.d)
        for w in a["rows"]:
            self.assertEqual(w["globally_first_executable_venue"],"UNRESOLVED")
            self.assertEqual(w["pre_v2_launchpad_market"],"UNRESOLVED")
            self.assertEqual(w["fixed_size_buy_sell_tax_slippage"],"UNRESOLVED")
            self.assertEqual(w["wallet_eligible_opportunity"],"UNRESOLVED")
            self.assertEqual(w["follower_executable_pnl"],"UNRESOLVED")

    def test_two_delayed_pool_timestamps_dont_claim_creation_time(self):
        r=build(self.d)["rows"]
        b=next(x for x in r if x["token"]=="BULLA")
        n=next(x for x in r if x["token"]=="牛来")
        self.assertEqual(next(z for z in b["pools_scoped_first_active"] if z.get("delay_blocks")==10)["first_active_UTC"],"2025-06-06T09:44:17.000Z")
        self.assertEqual(next(z for z in n["pools_scoped_first_active"] if z.get("delay_blocks")==17)["first_active_UTC"],"2026-08-14T16:18:43.000Z")

    def test_missing_alt_pool_rejected(self):
        d=copy.deepcopy(self.d)
        d[1]["rows"].pop(0)
        with self.assertRaises(ValueError):build(d)

    def test_partial_swap_source_not_upgraded_to_full(self):
        d=copy.deepcopy(self.d)
        d[3]["rows"][0]["scan_coverage"]="FULL_FIRST_TEN_BLOCKS"
        with self.assertRaises(AssertionError):self.assertEqual(build(d),json.loads((ROOT/"bsc-meme-address-model-v1-p4b-19ca-cross-venue-candidate-u-2026-10-14.json").read_text(encoding="utf-8")))

    def test_unexplained_earlier_market_not_from_snapshot(self):
        d=copy.deepcopy(self.d)
        d[2]["rows"][0]["pools"].pop()
        with self.assertRaises(ValueError):build(d)

if __name__=="__main__":
    unittest.main()
