#!/usr/bin/env python3
"""One proven Pancake V3 owner-signed swap must not become a PnL ranking."""
from __future__ import annotations

import copy
import unittest

from bsc_meme_address_model_v1_p3 import DIRECTORY, EvidenceError, build_overlay, load_pinned
from bsc_meme_address_model_v1_p3_swap import (
    OWNER, TX, load_witness, promote_verified_witness,
)


class OwnerRealSwapWitnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        docs, refs = load_pinned(DIRECTORY, include_full=True)
        cls.overlay = build_overlay(docs, refs)
        cls.witness = load_witness(DIRECTORY)

    def check(self, proof=None, baseline=None):
        return promote_verified_witness(
            copy.deepcopy(self.overlay if baseline is None else baseline),
            copy.deepcopy(self.witness if proof is None else proof),
        )

    def test_exact_one_confirmed_swap_all_other_wallets_unknown(self):
        result = self.check()
        summary = result["summary"]
        self.assertEqual((summary["wallets"], summary["frozen_CAs"],
                          summary["wallets_with_verified_recent_true_swap"],
                          summary["verified_recent_true_swap_witnesses"],
                          summary["remaining_owner_original_pairs_without_full_swap_evidence"],
                          summary["wallets_unknown_recent_true_swap"]), (23, 19, 1, 1, 37, 22))
        self.assertEqual(len(result["source_manifest"]), 14)
        self.assertEqual(summary["production"], "NO_GO")
        self.assertFalse(summary["followable_alpha_proven"])
        self.assertFalse(summary["realized_PnL_rank_available"])
        active = [w for w in result["wallets"] if w["recent_true_owner_meme_swap_state"]
                  == "VERIFIED_ACTIVE_ON_FROZEN_19_CA"]
        self.assertEqual(len(active), 1)
        self.assertEqual(active[0]["wallet"], OWNER)
        self.assertEqual(active[0]["latest_verified_true_swap_hash"], TX)
        self.assertTrue(all(w["realized_PnL"] == w["follower_executability"] == "UNRESOLVED"
                            for w in result["wallets"]))
        self.assertTrue(all(w["recent_30d_all_Meme_activity_state"] == "UNRESOLVED"
                            for w in result["wallets"]))

    def test_reject_unsigned_external_wallet(self):
        proof = copy.deepcopy(self.witness)
        proof["tx"]["from"] = "0x0000000000000000000000000000000000000000"
        with self.assertRaises(EvidenceError):
            self.check(proof)

    def test_reject_bad_receipt_or_partial_receipt(self):
        for field, value in (("status", "0x0"), ("complete_body", False)):
            proof = copy.deepcopy(self.witness)
            proof["receipt"][field] = value
            with self.assertRaises(EvidenceError):
                self.check(proof)

    def test_reject_unlinked_pool_or_quote_or_swap(self):
        for target, field, value in (
            ("pool", "token0", "0x0000000000000000000000000000000000000000"),
            ("pool", "token1", "0x0000000000000000000000000000000000000000"),
            ("pool", "swap_topic0", "0xdeadbeef"),
            ("token_transfer", "to", "0x0000000000000000000000000000000000000000"),
            ("quote_transfer", "from", "0x0000000000000000000000000000000000000000"),
            ("swap_event", "contract", "0x0000000000000000000000000000000000000000"),
        ):
            proof = copy.deepcopy(self.witness)
            proof[target][field] = value
            with self.assertRaises(EvidenceError):
                self.check(proof)

    def test_reject_timestamps_outside_frozen_window(self):
        proof = copy.deepcopy(self.witness)
        proof["tx"]["block_UTC"] = "2026-09-12T00:00:00Z"
        with self.assertRaises(EvidenceError):
            self.check(proof)

    def test_reject_fake_profit_or_wallet_settlement_upgrade(self):
        for field, value in (
            ("quote_received_by_original_wallet", "CONFIRMED"),
            ("complete_realized_profit", "POSITIVE"),
            ("follower_executability", "CONFIRMED"),
            ("production", "GO"),
        ):
            proof = copy.deepcopy(self.witness)
            proof["gate"][field] = value
            with self.assertRaises(EvidenceError):
                self.check(proof)


if __name__ == "__main__":
    unittest.main()
