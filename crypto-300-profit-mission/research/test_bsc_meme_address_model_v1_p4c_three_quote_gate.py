import copy
import json
import unittest
from bsc_meme_address_model_v1_p4c_three_quote_gate import ROOT,build,load

class ThreeFixedSourceQuoteClosureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=load(ROOT)

    def test_deterministic_frozen_exact_economic_gate(self):
        got=build(self.source)
        target=json.loads((ROOT/"bsc-meme-address-model-v1-p4c-three-unclosed-owner-token-quote-gate-2026-10-15.json").read_text(encoding="utf-8"))
        self.assertEqual(got,target)

    def test_all_canonical_owner_inventory_closed_but_quote_causality_open(self):
        out=build(self.source)
        self.assertEqual((out["summary"]["fixed_rounds"],out["summary"]["fixed_original_owner_signed_txs"]),(3,7))
        self.assertEqual(out["summary"]["source_canonical_token_inventory_closed"],3)
        self.assertEqual(out["summary"]["new_settled_native_profitable_rounds"],0)
        self.assertEqual(out["summary"]["new_settled_native_unprofitable_rounds"],0)
        self.assertTrue(all(x["original_token_in_raw"]==x["original_token_out_raw"] and x["original_token_residual_raw"]=="0" for x in out["rounds"]))
        self.assertFalse(out["summary"]["positive_profit_rank_approved"])
        self.assertEqual(out["summary"]["production"],"NO_GO")

    def test_non_native_Q3B_not_wbnb_and_other_owners_excluded(self):
        out=build(self.source)
        self.assertEqual([x["quote_asset_source"] for x in out["rounds"]],["WBNB","Q3B","Q3B"])
        self.assertEqual(out["summary"]["unrelated_same_block_Q3B_outflows_excluded"],1)
        self.assertEqual(out["excluded_unrelated_quote_events"][0]["block"],116113193)
        self.assertEqual([x["native_owner_block_sign"] for x in out["rounds"]],
                         ["POSITIVE_NATIVE_BLOCK_SCOPE","POSITIVE_NATIVE_BLOCK_SCOPE","NEGATIVE_NATIVE_BLOCK_SCOPE"])

    def test_original_non_owner_quote_transfer_cannot_be_added(self):
        d=copy.deepcopy(self.source)
        raw=d[6]["rows"][1]["logs"][0]
        raw["transactionHash"]=d[0]["selected"][2]["txs"][0][0]
        with self.assertRaises(ValueError):
            build(d)

    def test_forged_token_sold_amount_not_full_inventory(self):
        d=copy.deepcopy(self.source)
        d[3]["rows"][3]["logs"][0]["data"]="0x1"
        with self.assertRaises(ValueError):
            build(d)

    def test_wrong_quote_asset_recipient_rejected(self):
        d=copy.deepcopy(self.source)
        d[6]["rows"][1]["logs"][0]["topics"][2]="0x"+"0"*64
        with self.assertRaises(ValueError):
            build(d)

    def test_missing_tax_reconciliation_rejected(self):
        d=copy.deepcopy(self.source)
        d[4]["rows"][3]["logs"][0]["data"]="0x1"
        with self.assertRaises(ValueError):
            build(d)

    def test_duplicate_original_events_rejected_even_if_inventory_balances(self):
        d=copy.deepcopy(self.source)
        for row in d[1]["res"]:
            row["logs"] *= 2
        with self.assertRaisesRegex(ValueError,"duplicate"):
            build(d)

    def test_removed_reorged_event_rejected(self):
        d=copy.deepcopy(self.source)
        d[1]["res"][0]["logs"][0]["removed"]=True
        with self.assertRaisesRegex(ValueError,"removed"):
            build(d)

    def test_mismatched_eth_log_block_rejected(self):
        d=copy.deepcopy(self.source)
        d[1]["res"][0]["logs"][0]["blockNumber"]="0x1"
        with self.assertRaisesRegex(ValueError,"block mismatch"):
            build(d)

    def test_rpc_row_error_not_masked_by_status(self):
        d=copy.deepcopy(self.source)
        d[1]["res"][0]["error"]={"code":-32000,"message":"provider failure"}
        with self.assertRaisesRegex(ValueError,"provider error"):
            build(d)

    def test_duplicate_quote_event_rejected(self):
        d=copy.deepcopy(self.source)
        d[6]["rows"][1]["logs"] *= 2
        with self.assertRaisesRegex(ValueError,"duplicate"):
            build(d)

    def test_provenance_correction_is_append_only_pinned(self):
        from bsc_meme_address_model_v1_p4c_three_quote_gate import (
            PROVENANCE_BLOB, PROVENANCE_FILE, PINS, sha, verify_legacy_provenance
        )
        b=(ROOT/PROVENANCE_FILE).read_bytes()
        self.assertEqual(sha(b),PROVENANCE_BLOB)
        proof=json.loads(b)
        verify_legacy_provenance(proof)
        self.assertEqual(proof["historical_source_git_blob_sha"],PINS[1][1])
        self.assertEqual(proof["actual_precommit_git_blob_sha"],PINS[0][1])
        mutated=copy.deepcopy(proof)
        mutated["actual_precommit_git_blob_sha"]="0"*40
        with self.assertRaisesRegex(ValueError,"provenance"):
            verify_legacy_provenance(mutated)

if __name__=="__main__":
    unittest.main()
