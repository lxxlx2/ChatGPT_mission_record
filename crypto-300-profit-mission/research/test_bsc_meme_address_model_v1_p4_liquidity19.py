#!/usr/bin/env python3
"""P4 full 19-CA V2 WBNB first Mint/Sync evidence and conservative NO_GO regression."""
from __future__ import annotations
import copy
import json
import unittest

from bsc_meme_address_model_v1_p4_liquidity19 import ROOT, load, build, verify_giggle_raw, git_sha, GIGGLE_SHAS


class P4Liquidity19Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.docs=load(ROOT)

    def test_exact_git_artifact_from_all_pinned_sources(self):
        actual=build(self.docs,ROOT)
        expected=json.loads((ROOT/"bsc-meme-address-model-v1-p4-19ca-v2-wbnb-first-positive-liquidity-2026-10-14.json").read_text(encoding="utf-8"))
        self.assertEqual(actual,expected)

    def test_nineteen_distinct_fixed_CAs_and_eighteen_same_creation(self):
        d=build(self.docs,ROOT)
        self.assertEqual((d["summary"]["exact_major_CAs"],d["summary"]["v2_wbnb_pool_creation_verified"],
                          d["summary"]["first_positive_v2_wbnb_reserves_verified"],
                          d["summary"]["first_positive_same_creation_tx"],d["summary"]["delayed_first_liquidity"]),
                         (19,19,19,18,1))
        self.assertEqual(len(set(x["v2_wbnb_pool"] for x in d["rows"])),19)
        self.assertEqual(len(set(x["exact_CA"] for x in d["rows"])),19)

    def test_original_small_liquidity_and_cheems_giggle(self):
        rows={x["token"]:x for x in build(self.docs,ROOT)["rows"]}
        self.assertEqual(rows["MARSCOIN"]["first_positive_WBNB_BNB"],"0.00103")
        self.assertEqual(rows["SIREN"]["first_positive_WBNB_BNB"],"0.01312")
        self.assertEqual(rows["CHEEMS"]["first_positive_WBNB_BNB"],"240")
        self.assertEqual(rows["GIGGLE"]["first_positive_WBNB_BNB"],"2")
        self.assertEqual(rows["GIGGLE"]["liquidity_delay_blocks"],407)
        self.assertNotEqual(rows["GIGGLE"]["first_positive_reserves_block"],
                            rows["GIGGLE"]["pair_creation_block"])

    def test_exhaustive_41_windows_and_source_blob_pins(self):
        source=self.docs[9]
        verify_giggle_raw(ROOT,source)
        self.assertEqual(source["scan_blob_manifest"],list(GIGGLE_SHAS))
        self.assertEqual(source["scanned_block_windows"],41)
        self.assertEqual(len(GIGGLE_SHAS),6)
        for i,s in enumerate(GIGGLE_SHAS,1):
            f=ROOT/f"bsc-meme-address-model-v1-p4-giggle-sync-raw-part{i}-2026-10-14.json"
            self.assertEqual(git_sha(f.read_bytes()),s)

    def test_does_not_promote_first_pool_liquidity_to_profit_or_entry(self):
        x=build(self.docs,ROOT)
        self.assertEqual(x["summary"]["global_first_tradable_proven"],0)
        self.assertEqual(x["summary"]["qualified_misses_proven"],0)
        self.assertEqual(x["summary"]["follower_alpha_proven"],0)
        self.assertEqual(x["summary"]["production"],"NO_GO")
        self.assertTrue(all(y["full_venue_first_tradable"]=="UNRESOLVED" and
                            y["token_tax_sellability"]=="UNRESOLVED" and
                            y["qualified_wallet_misses"]=="UNRESOLVED" and
                            y["follower_alpha"]=="UNRESOLVED" for y in x["rows"]))

    def test_mint_amount_tamper_is_rejected(self):
        d=copy.deepcopy(self.docs)
        row=next(x for x in d[6]["records"] if x["token"]=="TST")
        m=next(x for x in row["all_events"] if x["topics"][0].startswith("0x4c209b5f"))
        m["data"]="0x"+"0"*128
        with self.assertRaises(ValueError):
            build(d,ROOT)

    def test_factory_created_pool_identity_tamper_is_rejected(self):
        d=copy.deepcopy(self.docs)
        d[1]["records"][0]["pool"]="0x"+"f"*40
        with self.assertRaises(ValueError):
            build(d,ROOT)

    def test_delayed_giggle_without_full_scan_is_rejected(self):
        d=copy.deepcopy(self.docs)
        d[9]["scanned_block_windows"]=40
        with self.assertRaises(ValueError):
            build(d,ROOT)

    def test_ignores_any_potential_rank_from_pool_counts(self):
        result=build(self.docs,ROOT)
        self.assertEqual(len(result["source_manifest"]),11)
        self.assertTrue(all("pnl" not in key.lower()
                            for row in result["rows"] for key in row.keys()))


if __name__=="__main__":
    unittest.main()
