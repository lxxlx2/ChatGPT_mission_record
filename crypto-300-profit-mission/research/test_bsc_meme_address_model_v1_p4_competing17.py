#!/usr/bin/env python3
"""Adversarial acceptance for 17 P4 original pool source receipts and false alpha guards."""
import copy
import unittest
from bsc_meme_address_model_v1_p4_competing17 import ROOT, build, load, V3_MINT

class FrozenSeventeenTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=load(ROOT)

    def test_seventeen_event_proof_and_original_scope(self):
        x=build(self.source)
        self.assertEqual([r["index"] for r in x["rows"]],list(range(17)))
        self.assertEqual(len({r["pool"] for r in x["rows"]}),17)
        self.assertEqual(x["summary"]["competitor_first_active_proven"],17)
        self.assertEqual((x["summary"]["creation_block_active"],x["summary"]["delayed_first_active"]),(15,2))
        self.assertEqual(x["summary"]["other_inactive_at_reference_still_unresolved"],5)
        self.assertEqual(x["summary"]["production"],"NO_GO")
        self.assertEqual(len(x["source_manifest"]),7)

    def test_delayed_are_actual_swaps_and_retain_unknown_market(self):
        x=build(self.source)
        late=[r for r in x["rows"] if r["delay_blocks"]>0]
        self.assertEqual([(r["token"],r["delay_blocks"]) for r in late],[("BULLA",10),("牛来",17)])
        self.assertTrue(all("SWAP" in r["activation_event_kind"] for r in late))
        self.assertTrue(all(r["first_global_trade"]==r["sellability_tax_impact"]==
                            r["wallet_qualified_miss"]==r["follower_profit"]=="UNRESOLVED" for r in x["rows"]))

    def test_factory_token_mismatch_rejected(self):
        d=copy.deepcopy(self.source)
        d[1]["events"][0]["original_factory_event"]["topics"][1]="0x"+"f"*64
        with self.assertRaises(ValueError):build(d)

    def test_missing_competing_pool_kept_not_silently_dropped(self):
        d=copy.deepcopy(self.source)
        d[3]["records"].pop()
        with self.assertRaises(ValueError):build(d)

    def test_fake_init_or_mint_rejected(self):
        d=copy.deepcopy(self.source)
        d[3]["records"][0]["original_same_creation_tx_events"][0]["topics"][0]="0x"+"f"*64
        with self.assertRaises(ValueError):build(d)

    def test_zero_active_creation_cannot_be_promoted(self):
        d=copy.deepcopy(self.source)
        d[4]["records"][2]["state_hex_at_creation"]="0x"+format(1,"064x")
        with self.assertRaises(ValueError):build(d)

    def test_bulla_first_event_is_swap_not_mint(self):
        d=copy.deepcopy(self.source)
        d[5]["full_unfiltered_event_window"]["events"][0]["topics"][0]=V3_MINT
        with self.assertRaises(ValueError):build(d)

    def test_bulla_first_event_liquidity_must_close(self):
        d=copy.deepcopy(self.source)
        d[5]["liquidity_raw_states"][2]["result"]="0x1"
        with self.assertRaises(ValueError):build(d)

    def test_niulai_already_saved_mislabeled_mint_is_swap(self):
        d=copy.deepcopy(self.source)
        d[6]["first_mint_event"]["topics"][0]=V3_MINT
        with self.assertRaises(ValueError):build(d)

    def test_no_mutated_four_pool_history_accepted(self):
        d=copy.deepcopy(self.source)
        d[0]["rows"][2]["first_active_liquidity_block"]+=1
        with self.assertRaises(ValueError):build(d)

if __name__=="__main__":
    unittest.main()
