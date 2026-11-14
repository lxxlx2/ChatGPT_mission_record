#!/usr/bin/env python3
"""P3 frozen BSC 23-wallet recent signer evidence and false-positive gates."""
from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from bsc_meme_address_model_v1_p3 import (
    DIRECTORY, EvidenceError, build_overlay, git_blob_sha, load_pinned,
)

COMMITTED = DIRECTORY / "bsc-meme-address-model-v1-p3-signer-evidence-overlay-2026-10-13.json"


class P3EvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.docs, cls.refs = load_pinned(DIRECTORY)

    def build(self, docs=None):
        return build_overlay(self.docs if docs is None else docs, self.refs)

    def test_git_blob_hash_and_pinned_sources(self):
        self.assertEqual(git_blob_sha(b"hello"), "b6fc4c620b67d95f953a5c1c1230aaab5db5a1b0")
        self.assertEqual(len(self.refs), 5)
        self.assertTrue(all(r["path"].startswith("crypto-300-profit-mission/research/")
                            for r in self.refs))

    def test_committed_overlay_exact_regeneration(self):
        expected = json.loads(COMMITTED.read_text(encoding="utf-8"))
        self.assertEqual(self.build(), expected)

    def test_p3_23wallet_coverage_and_known_incomplete_gate(self):
        overlay = self.build()
        s = overlay["summary"]
        self.assertEqual((s["wallets"], s["exact_CA"], s["fully_paginated_queries"],
                          s["erc20_transfer_events"], s["wallets_transfer_present"],
                          s["wallets_transfer_absent"]), (23, 19, 46, 89, 8, 15))
        self.assertEqual((s["candidate_wallet_transaction_pairs"], s["distinct_original_hashes"],
                          s["original_hashes_read"], s["original_hashes_pending"]), (75, 71, 16, 55))
        self.assertEqual((s["confirmed_owner_original_wallet_tx_pairs"],
                          s["confirmed_third_party_original_wallet_tx_pairs"],
                          s["unread_wallet_tx_pairs"]), (10, 7, 58))
        self.assertEqual(s["confirmed_owner_market_swaps"], 0)
        self.assertEqual(s["production"], "NO_GO")

    def test_all_wallets_preserve_ambiguous_market_swap_and_profit(self):
        for row in self.build()["wallets"]:
            self.assertEqual(row["recent_30d_true_owner_market_swap"], "UNRESOLVED")
            self.assertEqual(row["realized_profit"], "UNRESOLVED")
            self.assertTrue(row["not_proven_inactive"])
            self.assertEqual(row["owner_original_reads"] +
                             row["third_party_original_reads"] +
                             row["original_unread_or_unreadable"],
                             row["frozen_original_candidates"])
            for tx in row["original_transactions"]:
                self.assertEqual(tx["receipt_success"], "UNRESOLVED")
                self.assertFalse(tx["market_swap_confirmed"])
                if tx["owner_signed_original"] is False:
                    self.assertNotEqual(tx["tx_from"], row["wallet"])

    def test_frozen_30d_window_not_midnight_substitution(self):
        output = self.build()
        self.assertEqual(output["strict_window_start_UTC"], "2026-09-13T08:37:36Z")
        self.assertEqual(output["as_of_snapshot_UTC"], "2026-10-13T08:37:36Z")
        d = copy.deepcopy(self.docs)
        d[1]["exact_cutoff_block_UTC"] = "2026-09-13T00:00:00Z"
        with self.assertRaises(EvidenceError):
            self.build(d)

    def test_reject_third_party_misclassification_source_forgery(self):
        d = copy.deepcopy(self.docs)
        d[4]["records"][6]["wallets"] = ["0x1234123412341234123412341234123412341234"]
        with self.assertRaises(EvidenceError):
            self.build(d)

    def test_reject_duplicate_or_unfrozen_candidate(self):
        d = copy.deepcopy(self.docs)
        d[2]["original_candidates"].append(copy.deepcopy(d[2]["original_candidates"][0]))
        with self.assertRaises(EvidenceError):
            self.build(d)
        d = copy.deepcopy(self.docs)
        d[2]["original_candidates"][0]["token_CAs"] = ["0x0000000000000000000000000000000000000000"]
        with self.assertRaises(EvidenceError):
            self.build(d)

    def test_reject_partial_or_mismatched_signer_original(self):
        d = copy.deepcopy(self.docs)
        row = d[3]["records"][0]
        row["block"] = row["block"] + 1
        with self.assertRaises(EvidenceError):
            self.build(d)

    def test_reject_transfer_census_drift(self):
        d = copy.deepcopy(self.docs)
        d[1]["summary"]["fully_paginated_directions"] = 45
        with self.assertRaises(EvidenceError):
            self.build(d)

    def test_all_15_transfer_absent_wallets_are_not_labeled_inactive(self):
        rows = self.build()["wallets"]
        missing = [w for w in rows if w["exact19_30d_transfer_evidence_state"] ==
                   "ABSENT_IN_FROZEN_19_CA"]
        self.assertEqual(len(missing), 15)
        self.assertTrue(all(w["not_proven_inactive"] for w in missing))



class P3FullSignerCensusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.docs, cls.refs = load_pinned(DIRECTORY, include_full=True)

    def build(self, docs=None):
        return build_overlay(self.docs if docs is None else docs, self.refs)

    def test_every_frozen_hash_has_original_read_attempt_and_no_new_pnl(self):
        x = self.build()
        s = x["summary"]
        self.assertEqual(len(x["source_manifest"]), 13)
        self.assertEqual((s["wallets"], s["exact_CA"], s["distinct_original_hashes"],
                          s["original_hashes_read"], s["original_hashes_pending"]), (23, 19, 71, 71, 0))
        self.assertEqual((s["original_hashes_parsed"], s["original_hashes_unreadable"]), (70, 1))
        self.assertEqual((s["confirmed_owner_original_wallet_tx_pairs"],
                          s["confirmed_third_party_original_wallet_tx_pairs"],
                          s["unread_wallet_tx_pairs"]), (38, 36, 1))
        self.assertEqual(s["confirmed_owner_market_swaps"], 0)
        self.assertEqual(s["production"], "NO_GO")
        self.assertEqual(sum(w["frozen_original_candidates"] for w in x["wallets"]), 75)
        self.assertTrue(all(w["realized_profit"] == "UNRESOLVED" and
                            w["recent_30d_true_owner_market_swap"] == "UNRESOLVED"
                            for w in x["wallets"]))

    def test_full_signer_source_partitions_no_gaps(self):
        parts = self.docs[3:]
        self.assertEqual([p["part"] for p in parts], list(range(1, 11)))
        self.assertEqual([p["range"] for p in parts],
                         [[0, 7], [8, 15], [16, 22], [23, 29], [30, 36],
                          [37, 43], [44, 50], [51, 57], [58, 64], [65, 70]])
        self.assertTrue(all(p["precommit_sha"] == self.refs[2]["git_blob_sha"] for p in parts))

    def test_reject_one_missing_original_hash_even_if_other_rows_unmodified(self):
        docs = copy.deepcopy(self.docs)
        docs[-1]["records"].pop()
        with self.assertRaises(EvidenceError):
            self.build(docs)

    def test_cannot_turn_nonowner_transfer_into_wallet_buy(self):
        x = self.build()
        nonowner = [tx for w in x["wallets"] for tx in w["original_transactions"]
                    if tx["owner_signed_original"] is False]
        self.assertEqual(len(nonowner), 36)
        self.assertTrue(all(tx["market_swap_confirmed"] is False for tx in nonowner))
        self.assertTrue(all(tx["receipt_success"] == "UNRESOLVED" for tx in nonowner))



if __name__ == "__main__":
    unittest.main()
