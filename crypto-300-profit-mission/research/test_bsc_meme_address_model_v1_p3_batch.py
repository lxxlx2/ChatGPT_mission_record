#!/usr/bin/env python3
"""P3 BSC 37-batch deterministic owner/receipt/token/pool/Swap proof tests."""
from __future__ import annotations

import copy
import unittest

from bsc_meme_address_model_v1_p3 import DIRECTORY, EvidenceError, build_overlay, load_pinned
from bsc_meme_address_model_v1_p3_swap import load_witness, promote_verified_witness
from bsc_meme_address_model_v1_p3_batch import (LATEST_NAME, LATEST_BLOB_SHA, attach_latest_verified_swap_utc, build_evidence, load_evidence, load_source)


class P3FrozenBatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        docs, refs = load_pinned(DIRECTORY, include_full=True)
        cls.refs = refs
        cls.overlay = build_overlay(docs, refs)
        cls.previous = promote_verified_witness(cls.overlay, load_witness(DIRECTORY))
        cls.evidence, cls.batch_refs = load_evidence(DIRECTORY)

    def build(self, evidence=None):
        return build_evidence(self.overlay, copy.deepcopy(evidence or self.evidence),
                              self.previous, self.refs + self.batch_refs)

    def test_37_denominator_and_20_total_true_swaps_with_gates(self):
        x = self.build()
        s = x["summary"]
        self.assertEqual((s["wallets"], s["candidate_owner_tx_excluding_prior"],
                          s["new_confirmed_owner_swap_txs"], s["prior_confirmed_owner_swap_txs"],
                          s["total_confirmed_owner_swap_txs"]), (23,37,19,1,20))
        self.assertEqual((s["pool_swap_seen_but_receipt_status_unverified"],
                          s["direct_pool_swap_not_found_routing_unknown"],
                          s["historical_verified_pools"]), (4,14,11))
        self.assertEqual((s["wallets_with_confirmed_frozen_CA_recent_swap"],
                          s["wallets_without_confirmed_swap_still_unknown"]), (7,16))
        self.assertEqual((s["PnL"], s["reproducible_follow"], s["production"]),
                         ("UNRESOLVED","UNRESOLVED","NO_GO"))
        self.assertTrue(all(w["lifetime_pnl"] == w["follower_alpha"] == "UNRESOLVED"
                            for w in x["wallets"]))

    def test_pooled_swaps_19_verified_4_pending_14_unknown(self):
        x = self.build()
        proven = [r for r in x["candidates"]
                  if r["status"] == "VERIFIED_OWNER_SIGNED_POOL_SWAP"]
        self.assertEqual(len(proven), 19)
        self.assertTrue(all(r["receipt_status_header"] == "0x1" and r["matching_pool"] is not None
                            for r in proven))
        pending = [r for r in x["candidates"]
                   if r["status"] == "POOL_SWAP_SEEN_RECEIPT_STATUS_UNRESOLVED"]
        self.assertEqual(len(pending), 4)
        self.assertTrue(all(r["receipt_status_header"] is None for r in pending))
        no_pool = [r for r in x["candidates"]
                   if r["status"] == "NO_DIRECT_POOL_SWAP_SEEN_ROUTING_UNRESOLVED"]
        self.assertEqual(len(no_pool),14)
        self.assertTrue(all(r["matching_pool"] is None for r in no_pool))
        self.assertEqual(len({r["hash"] for r in x["candidates"]}), 37)

    def test_owner_signature_cannot_be_manufactured(self):
        tampered = copy.deepcopy(self.overlay)
        tx = self.evidence["pre"][
            "bsc-meme-address-model-v1-p3-owner37-receipt-pool-precommit-2026-10-13.json"
        ]["candidates"][0]
        row = next(w for w in tampered["wallets"] if w["wallet"] == tx["wallet"])
        item = next(v for v in row["original_transactions"] if v["hash"] == tx["hash"])
        item["owner_signed_original"] = False
        with self.assertRaises(EvidenceError):
            build_evidence(tampered, self.evidence, self.previous, self.refs + self.batch_refs)

    def test_receipt_header_without_success_does_not_allow_promotion(self):
        tampered = copy.deepcopy(self.evidence)
        needle = next(i for i,r in enumerate(self.build()["candidates"])
                      if r["status"] == "VERIFIED_OWNER_SIGNED_POOL_SWAP")
        offset = needle // 7
        idx = needle % 7
        tampered["rows"]["receipt"][offset]["records"][idx]["status_header"] = "0x0"
        with self.assertRaises(EvidenceError):
            self.build(tampered)

    def test_swapped_pool_identity_is_blocker(self):
        tampered = copy.deepcopy(self.evidence)
        tampered["rows"]["pool-historical"][0]["records"][0]["call_values"]["token1"] = (
            "0x0000000000000000000000000000000000000000"
        )
        with self.assertRaises(EvidenceError):
            self.build(tampered)

    def test_missing_venue_log_cannot_preserve_replay(self):
        tampered = copy.deepcopy(self.evidence)
        chunk = tampered["rows"]["venue-swap-log"][0]
        x = next(r for r in chunk["records"] if r["events"])
        x["events"].clear()
        with self.assertRaises(EvidenceError):
            self.build(tampered)

    def test_latest_verified_utc_for_seven_eligible_wallets_only(self):
        source = load_source(DIRECTORY, LATEST_NAME, LATEST_BLOB_SHA)
        x = attach_latest_verified_swap_utc(self.build(), source)
        ready = [w for w in x["wallets"] if w["latest_verified_swap_UTC"] is not None]
        self.assertEqual(len(ready), 7)
        self.assertEqual(len(x["source_manifest"]), len(self.refs) + len(self.batch_refs) + 1)
        a83b = next(w for w in ready if w["wallet"].startswith("0xa83b"))
        self.assertEqual(a83b["latest_verified_swap_UTC"], "2026-10-12T07:57:23.000Z")
        unknown = [w for w in x["wallets"] if w["latest_verified_swap_UTC"] is None]
        self.assertEqual(len(unknown), 16)
        self.assertTrue(all(w["latest_verified_swap_hash"] is None for w in unknown))

    def test_latest_timestamp_spoof_is_rejected(self):
        source = load_source(DIRECTORY, LATEST_NAME, LATEST_BLOB_SHA)
        source["wallets"][0]["blockTimestampHex"] = "0x1234"
        with self.assertRaises(EvidenceError):
            attach_latest_verified_swap_utc(self.build(), source)

    def test_standard_v3_negative_control_is_not_inactivity(self):
        x = self.build()
        self.assertEqual(len([r for r in x["candidates"]
                              if r["status"] == "NO_DIRECT_POOL_SWAP_SEEN_ROUTING_UNRESOLVED"]),14)
        self.assertEqual(len([w for w in x["wallets"]
                              if w["recent_true_swap_state"] == "UNRESOLVED"]),16)
        self.assertTrue(all(w["verified_recent_swap_last_block"] is None
                            for w in x["wallets"] if w["recent_true_swap_state"] == "UNRESOLVED"))


if __name__ == "__main__":
    unittest.main()
