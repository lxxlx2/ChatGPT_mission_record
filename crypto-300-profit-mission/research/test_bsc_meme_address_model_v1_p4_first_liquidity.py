#!/usr/bin/env python3
"""P4 four V2/WBNB creation-transaction first positive reserve evidence tests."""
from __future__ import annotations

import copy
import unittest

from bsc_meme_address_model_v1_p4_first_liquidity import ROOT, SRC_NAME, SRC_BLOB, build, load, git_blob


class P4FirstPoolLiquidityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src = load(ROOT)

    def test_pinned_git_blob_still_matches_creation_events(self):
        self.assertEqual(git_blob((ROOT / SRC_NAME).read_bytes()), SRC_BLOB)

    def test_four_created_with_initial_mint_same_transaction(self):
        d = build(self.src)
        s = d["summary"]
        self.assertEqual((s["priority_wallets"], s["source_confirmed_V2_WBNB_pair_creations"],
                          s["initial_Mint_and_Sync_same_creation_tx"],
                          s["positive_initial_WBNB_reserves"],
                          s["same_block_swap_confirmed_pools"]), (4,4,4,4,2))
        self.assertEqual(len(d["rows"]), 4)
        self.assertEqual(len(d["source_manifest"]), 3)
        self.assertEqual(d["rows"][0]["creation_block"], 83636128)
        self.assertEqual(d["rows"][1]["creation_block"], 63454407)
        self.assertEqual(d["rows"][2]["creation_block"], 112668701)
        self.assertEqual(d["rows"][3]["creation_block"], 116314917)

    def test_precise_initial_wbnb_reserves_and_tradability_not_conflated(self):
        d = build(self.src)
        observed = {r["token"]:r["first_positive_WBNB_reserve_BNB"] for r in d["rows"]}
        self.assertEqual(observed, {
            "龙虾": "17.639999998157599996",
            "币安人生": "17.639999998157599996",
            "MARSCOIN": "0.00103",
            "牛来": "0.1",
        })
        self.assertEqual(d["summary"]["qualified_follower_entry_proven"], 0)
        self.assertEqual(d["summary"]["profit_proven"], 0)
        self.assertFalse(d["summary"]["full_19CA_venue_launch_universe_validated"])
        self.assertEqual(d["summary"]["production"], "NO_GO")
        self.assertTrue(all(r["first_qualified_trade_entry"] == "UNRESOLVED" and
                            r["attributable_realized_profit"] == "UNRESOLVED" and
                            r["earliest_any_pool_liquidity"] == "UNRESOLVED"
                            for r in d["rows"]))

    def test_reject_fabricated_mint_not_in_creation_transaction(self):
        src = copy.deepcopy(self.src)
        src["records"][0]["initial_mint_event"]["transactionHash"] = "0x" + "a"*64
        with self.assertRaises(ValueError):
            build(src)

    def test_reject_quote_reserve_manipulation(self):
        src = copy.deepcopy(self.src)
        src["records"][2]["first_initial_mint_reserves_raw"][0] = "0"
        with self.assertRaises(ValueError):
            build(src)

    def test_reject_broken_factory_boundary(self):
        src = copy.deepcopy(self.src)
        src["records"][1]["factory_getPair_before"] = src["records"][1]["factory_getPair_at"]
        with self.assertRaises(ValueError):
            build(src)

    def test_reject_fake_swap_or_profit_promotion(self):
        src = copy.deepcopy(self.src)
        src["records"][0]["confirmed_execution_same_block"] = True
        with self.assertRaises(ValueError):
            build(src)
        src2 = copy.deepcopy(self.src)
        src2["records"][0]["final_trade_profit"] = "GAIN"
        with self.assertRaises(ValueError):
            build(src2)


if __name__ == "__main__":
    unittest.main()
