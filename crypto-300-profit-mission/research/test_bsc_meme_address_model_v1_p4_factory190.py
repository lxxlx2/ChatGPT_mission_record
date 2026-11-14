#!/usr/bin/env python3
"""Frozen 190 BSC onchain factory read reproducibility and no-tradability inference."""
import copy
import json
import unittest

from bsc_meme_address_model_v1_p4_factory190 import (
    HERE, PRECOMMIT, PRECOMMIT_SHA, PINS, PREFIX,
    build, parse_pinned,
)


class P4Factory190Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = parse_pinned(HERE, PRECOMMIT, PRECOMMIT_SHA)
        cls.sources = [parse_pinned(HERE, PREFIX+f"part{i+1}-2026-10-13.json",s)
                       for i,s in enumerate(PINS)]

    def test_exact_committed_19ca_artifact(self):
        got = build(self.plan,self.sources)
        expected = json.loads((HERE / "bsc-meme-address-model-v1-p4-19ca-factory190-discovery-2026-10-13.json").read_text())
        self.assertEqual(got, expected)

    def test_190_contiguous_fixed_snapshots_preserve_all_19_major_tokens(self):
        x = build(self.plan,self.sources)
        s = x["summary"]
        self.assertEqual((s["major_exact_CAs"],s["required_factory_calls"],
                          s["parsed_factory_calls"],s["failed_factory_calls"],
                          s["factory_nonzero_slots"],s["factory_zero_slots"]), (19,190,190,0,161,29))
        self.assertEqual(len(x["source_manifest"]), 16)
        self.assertEqual([r["token"] for r in x["rows"]],
                         [self.plan["queries"][i*10]["token"] for i in range(19)])
        self.assertEqual(sum(len(r["matched_pools"]) for r in x["rows"]), 190)
        self.assertEqual(sum(r["nonzero_factory_pools"] for r in x["rows"]), 161)

    def test_unknown_liquidity_and_g5_no_alpha_promotion(self):
        x = build(self.plan,self.sources)
        self.assertEqual(x["summary"]["code_verified_for_nonzero_pools"], 0)
        self.assertEqual(x["summary"]["first_executable_timestamp_confirmed"], 0)
        self.assertEqual(x["summary"]["qualified_profitable_misses"], 0)
        self.assertEqual(x["summary"]["production"], "NO_GO")
        self.assertTrue(x["wallet_universe_23_untouched"])
        self.assertEqual(x["profit_from_pool_discovery"], "UNRESOLVED")
        self.assertTrue(all(r["qualified_miss"] == r["first_executable_pool"] == "UNRESOLVED"
                            for r in x["rows"]))
        self.assertTrue(all(slot["tradable_at_launch"] == slot["liquidity_BNB_at_launch"] == "UNRESOLVED"
                            for row in x["rows"] for slot in row["matched_pools"]))

    def test_missing_result_row_fails_closed(self):
        src=copy.deepcopy(self.sources)
        src[0]["records"].pop()
        with self.assertRaises(ValueError):
            build(self.plan,src)

    def test_fabricated_factory_address_fails_evm_consistency(self):
        src=copy.deepcopy(self.sources)
        src[0]["records"][0]["pool"]="0x"+"f"*40
        with self.assertRaises(ValueError):
            build(self.plan,src)

    def test_duplicate_address_from_distinct_fee_slots_fails(self):
        src=copy.deepcopy(self.sources)
        first=src[0]["records"][0]
        second=src[0]["records"][1]
        second["raw"]=first["raw"]
        second["pool"]=first["pool"]
        with self.assertRaises(ValueError):
            build(self.plan,src)


if __name__ == "__main__":
    unittest.main()
