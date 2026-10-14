#!/usr/bin/env python3
"""P4-B replay security and coverage tests for historical 19 CA Swap observations."""
import copy
import json
import unittest
from bsc_meme_address_model_v1_p4b_v2_swaps19 import ROOT,load,build

class Swap19WitnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.docs=load(ROOT)

    def test_exact_immutable_output(self):
        fresh=build(self.docs)
        old=json.loads((ROOT/"bsc-meme-address-model-v1-p4b-v2-19ca-first10-swap-observations-2026-10-14.json").read_text(encoding="utf-8"))
        self.assertEqual(fresh,old)

    def test_all_nineteen_with_no_hindsight_qualification(self):
        d=build(self.docs)
        self.assertEqual(len(d["rows"]),19)
        self.assertEqual([x["index"] for x in d["rows"]],list(range(19)))
        s=d["summary"]
        self.assertEqual((s["complete_ten_block_windows"],s["first_block_only_fallbacks"]),(11,8))
        self.assertEqual((s["observed_v2_swap_events_in_verified_windows"],s["pools_with_observed_swap"]),(24,9))
        self.assertEqual((s["pools_with_observed_token_buy"],s["pools_with_observed_token_sell"]),(7,5))
        self.assertEqual(s["fully_qualified_U"],0)
        self.assertEqual(s["production"],"NO_GO")
        self.assertTrue(all(x["qualified_major_opportunity"]==x["tax_and_sellability"]==
                            x["follower_pnl"]=="UNRESOLVED" for x in d["rows"]))

    def test_first_block_scope_not_10_block_claim(self):
        result=build(self.docs)
        for row in result["rows"]:
            span=row["verified_swap_window_end"]-row["verified_swap_window_start"]
            self.assertIn(span,(0,9))
            self.assertEqual(span,0 if "FIRST_BLOCK_ONLY" in row["scan_coverage"] else 9)

    def test_no_transfer_promoted_without_real_swap(self):
        q=build(self.docs)
        for r in q["rows"]:
            self.assertEqual(sum(r[z] for z in ("pool_buy_token_events","pool_sell_token_events","complex_swap_events")),
                             r["swap_event_count"])
            self.assertEqual(len(r["event_witnesses"]),r["swap_event_count"])

    def test_removed_log_rejected(self):
        d=copy.deepcopy(self.docs)
        row=next(x for x in d[2]["rows"] if x["logs"])
        row["logs"][0]["removed"]=True
        with self.assertRaises(ValueError):build(d)

    def test_fake_topic_rejected(self):
        d=copy.deepcopy(self.docs)
        d[1]["rows"][2]["logs"][0]["topics"][0]="0x"+"0"*64
        with self.assertRaises(ValueError):build(d)

    def test_fake_pool_quote_contract_rejected(self):
        d=copy.deepcopy(self.docs)
        d[0]["rows"][2]["pool"]="0x"+"f"*40
        with self.assertRaises(ValueError):build(d)

    def test_original_truncation_cannot_be_zero(self):
        d=copy.deepcopy(self.docs)
        d[1]["rows"][0]["query_status"]="COMPLETE"
        d[1]["rows"][0]["logs"]=[]
        with self.assertRaises(ValueError):build(d)

    def test_fallback_must_not_cover_nine_unread_blocks(self):
        d=copy.deepcopy(self.docs)
        d[7]["rows"][0]["block"]+=1
        with self.assertRaises(ValueError):build(d)

    def test_drop_critical_loss_witness_rejected(self):
        d=copy.deepcopy(self.docs)
        d[2]["rows"][2]["logs"]=[]
        with self.assertRaises(ValueError):build(d)

if __name__=="__main__":
    unittest.main()
