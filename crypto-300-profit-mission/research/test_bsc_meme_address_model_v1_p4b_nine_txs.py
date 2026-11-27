#!/usr/bin/env python3
"""Nine first observed Swap original transaction provenance regression suite."""
import copy
import json
import unittest
from bsc_meme_address_model_v1_p4b_nine_txs import ROOT,build,load

class NineFirstSwapTransactions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d=load(ROOT)

    def test_frozen_json_replay(self):
        expected=json.loads((ROOT/"bsc-meme-address-model-v1-p4b-nine-firstswap-tx-provenance-2026-10-14.json").read_text(encoding="utf-8"))
        self.assertEqual(build(self.d),expected)

    def test_nine_signed_and_three_receipts_unresolved(self):
        s=build(self.d)["summary"]
        self.assertEqual((s["observed_pool_firstswap_transactions"],s["original_tx_senders_verified"],s["readback_receipt_success"],s["receipt_unresolved"]),(9,9,6,3))
        self.assertEqual((s["owner_realized_pnl_proven"],s["qualified_major_U_proven"]),(0,0))
        self.assertEqual(s["production"],"NO_GO")

    def test_original_sender_not_beneficial_trader(self):
        rows=build(self.d)["rows"]
        self.assertTrue(all(x["original_tx_confirmed"] and x["beneficial_owner_identity"]=="UNRESOLVED"
                            and x["owner_realized_pnl"]=="UNRESOLVED"
                            and x["fixed_size_follower_quote"]=="UNRESOLVED"
                            and x["eligible_missed_trade"]=="UNRESOLVED"
                            for x in rows))

    def test_partial_receipt_not_called_success(self):
        rows=build(self.d)["rows"]
        unknown=[x for x in rows if x["receipt_read_status"]!="COMPLETE"]
        self.assertEqual({x["token"] for x in unknown},{"TUT","BULLA","MARSCOIN"})
        self.assertTrue(all(x["receipt_status"]=="UNRESOLVED" and x["total_tx_gas_wei"] is None for x in unknown))

    def test_transaction_hash_mismatch_fails(self):
        d=copy.deepcopy(self.d)
        d[1]["rows"][0]["original_transaction"]["hash"]="0x"+"f"*64
        with self.assertRaises(ValueError):build(d)

    def test_receipt_status_cannot_be_fabricated(self):
        d=copy.deepcopy(self.d)
        d[1]["rows"][0]["original_receipt"]["status"]="0x0"
        with self.assertRaises(ValueError):build(d)

    def test_corrupt_scope_or_negative_case_rejected(self):
        d=copy.deepcopy(self.d)
        d[0]["targets"].pop()
        with self.assertRaises(ValueError):build(d)

if __name__=="__main__":
    unittest.main()
