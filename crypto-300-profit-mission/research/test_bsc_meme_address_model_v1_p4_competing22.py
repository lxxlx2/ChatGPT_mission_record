#!/usr/bin/env python3
"""P4 171 competing factory reads and 22 exact historical V2/V3 liquidity tests."""
import copy
import json
import unittest

from bsc_meme_address_model_v1_p4_competing22 import ROOT, load, build, SOURCES, PRESENCE


class P4Competing22Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.presence,cls.parts=load(ROOT)

    def test_complete_source_pinned_22_pool_model_equals_committed(self):
        expected=json.loads((ROOT/"bsc-meme-address-model-v1-p4-19ca-competing22-liquidity-snapshot-2026-10-14.json").read_text(encoding="utf-8"))
        self.assertEqual(build(self.presence,self.parts),expected)

    def test_all_19_CAs_171_reads_then_22_source_snapshots(self):
        d=build(self.presence,self.parts)
        s=d["summary"]
        self.assertEqual((s["major_CAs"],s["source_competing_slots"],s["provider_reads_complete"]), (19,22,22))
        self.assertEqual((s["V2_USDT_with_positive_reserves"],
                          s["V3_active_initialized_at_V2_baseline"],
                          s["V3_no_active_liquidity_at_baseline"],
                          s["total_active_competing_pool_snapshots"]), (2,15,5,17))
        self.assertEqual(len(d["source_manifest"]),len(SOURCES))
        self.assertEqual(self.presence["summary"]["historical_factory_reads"],171)
        self.assertEqual(self.parts[0]["source"]["blob_sha"],PRESENCE[1])

    def test_zero_snapshots_do_not_imply_never_liquid(self):
        d=build(self.presence,self.parts)
        self.assertTrue(all(r["earlier_than_V2_liquidity"]=="UNRESOLVED"
                            and r["first_executable_quote_size"]=="UNRESOLVED"
                            and r["wallet_miss_qualification"]=="UNRESOLVED"
                            for r in d["rows"]))
        self.assertEqual((d["summary"]["earlier_first_positive_proven"],
                          d["summary"]["qualified_misses_proven"]), (0,0))
        self.assertEqual(d["summary"]["production"],"NO_GO")
        self.assertTrue("Does NOT prove first liquidity was before V2" in d["scope"])

    def test_raw_v3_liquidity_tampering_rejected(self):
        parts=copy.deepcopy(self.parts)
        pool=parts[1]["rows"][0]["pools"][0]
        original=next(x for x in pool["reads"] if x["kind"]=="liquidity")
        original["read"]["raw_hex"]="0x"+"0"*64
        with self.assertRaises(ValueError):
            build(self.presence,parts)

    def test_duplicated_pool_or_wrong_original_scope_rejected(self):
        parts=copy.deepcopy(self.parts)
        parts[2]["rows"][0]["CA"]="0x"+"f"*40
        with self.assertRaises(ValueError):
            build(self.presence,parts)

    def test_fake_v2_usdt_profit_signal_rejected(self):
        parts=copy.deepcopy(self.parts)
        target=next(x for row in parts[1]["rows"] for x in row["pools"]
                    if x["protocol"]=="V2")
        target["classification"]="V3_INITIALIZED_ACTIVE_LIQUIDITY_AT_SNAPSHOT"
        with self.assertRaises(ValueError):
            build(self.presence,parts)

    def test_one_failed_original_rpc_cannot_be_labelled_liquid(self):
        parts=copy.deepcopy(self.parts)
        parts[1]["rows"][0]["pools"][0]["reads"][0]["read"]["success"]=False
        with self.assertRaises(ValueError):
            build(self.presence,parts)


if __name__=="__main__":
    unittest.main()
