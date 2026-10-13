#!/usr/bin/env python3
"""P4 conservative all-wallet recent Swap × sampled economic evidence tests."""
from __future__ import annotations

import copy
import json
import unittest

from bsc_meme_address_model_v1_p3 import DIRECTORY, EvidenceError, git_blob_sha
from bsc_meme_address_model_v1_p3_batch import load_evidence
from bsc_meme_address_model_v1_p4 import build_matrix, load_checked


class P4ReadinessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p2, cls.p3 = load_checked(DIRECTORY)

    def test_exact_committed_json_regeneration(self):
        expected = json.loads((
            DIRECTORY / "bsc-meme-address-model-v1-p4-p2p3-readiness-matrix-2026-10-13.json"
        ).read_text(encoding="utf-8"))
        self.assertEqual(build_matrix(self.p2, self.p3), expected)

    def test_all_23_preserved_and_no_fake_rank(self):
        x = build_matrix(self.p2, self.p3)
        s = x["summary"]
        self.assertEqual((s["wallets"], s["strict19CA_30day_owner_swap_verified_wallets"],
                          s["sampled_two_plus_major_positive_with_recent_activity"],
                          s["recent_active_but_economics_incomplete"],
                          s["recent_swap_unknown_wallets"]), (23, 7, 4, 3, 16))
        self.assertEqual((s["full_2026_economic_PnL_proven_wallets"],
                          s["qualified_major_misses_proven"]), (0, 0))
        self.assertFalse(s["executable_follower_alpha_proven"])
        self.assertTrue(all(w["profit_rank"] is None
                            and w["p2_full_wallet_PnL"] == "UNRESOLVED"
                            and w["p4_funding_and_pool_eligibility"] == "UNRESOLVED"
                            and w["p5_follower_1_5_15m"] == "UNRESOLVED"
                            for w in x["wallets"]))

    def test_priority_is_four_samples_never_realized_profitable(self):
        x = build_matrix(self.p2, self.p3)
        priority = [w for w in x["wallets"] if w["p4_research_qualification"].startswith("PRIORITY_")]
        self.assertEqual({w["wallet"] for w in priority}, {
            "0x2adf961b40951736bcff3b36b7fb1cd5775475ba",
            "0x8e6b3c9c72ca592bbab470f761fa869c174e9ea0",
            "0xadffbebbd2d9141cff80f8a905846ba8f9e3946d",
            "0xddac928a240bdace3994c2cc0783d4e29a002127",
        })
        self.assertTrue(all(w["p2_positive_distinct_major_CAs_count"] >= 2
                            and w["p3_verified_recent_19CA_swap"] for w in priority))
        self.assertTrue(all(w["p2_full_wallet_PnL"] == "UNRESOLVED" for w in priority))

    def test_fake_full_pnl_rejected(self):
        p2 = copy.deepcopy(self.p2)
        p2["wallets"][0]["completed_full_wallet_all_CA_PnL"] = "POSITIVE"
        with self.assertRaises(EvidenceError):
            build_matrix(p2, self.p3)

    def test_missing_recent_wallet_does_not_turn_into_no_trade(self):
        p3 = copy.deepcopy(self.p3)
        p3["wallets"].pop()
        with self.assertRaises(EvidenceError):
            build_matrix(self.p2, p3)

    def test_non_native_pool_quote_metadata_is_real_historical_ABI(self):
        name = "bsc-meme-address-model-v1-p4-nonnative-quote-token-identities-2026-10-13.json"
        blob = (DIRECTORY / name).read_bytes()
        self.assertEqual(git_blob_sha(blob), "9cced46fcf5dc805ffa6fd051d0a2555a15987ff")
        q = json.loads(blob)
        self.assertEqual(q["production"], "NO_GO")
        self.assertEqual([x["symbol"] for x in q["quote_token_checks"]],
                         ["QQQB", "SPCXB", "USDT"])
        evidence, _ = load_evidence(DIRECTORY)
        pools = {row["pool"]: row for part in evidence["rows"]["pool-historical"]
                 for row in part["records"]}
        for item in q["quote_token_checks"]:
            raw = item["symbol_return"]
            self.assertEqual(int(raw[66:130], 16), len(item["symbol"]))
            self.assertEqual(bytes.fromhex(raw[130:130+len(item["symbol"])*2]).decode("ascii"),
                             item["symbol"])
            self.assertEqual(len(item["decimals_return"]), 66)
            self.assertEqual(int(item["decimals_return"], 16), item["decimals"])
            self.assertEqual(item["decimals"], 18)
            proof = pools[item["pool"]]
            self.assertEqual(proof["earliest_block"], item["block"])
            self.assertIn(item["quote_ca"], [proof["call_values"]["token0"],
                                              proof["call_values"]["token1"]])
            self.assertNotEqual(item["quote_ca"], proof["target_CA"])

    def test_quote_metadata_cannot_be_used_as_realized_pnl_mark(self):
        data = json.loads((DIRECTORY /
            "bsc-meme-address-model-v1-p4-nonnative-quote-token-identities-2026-10-13.json"
        ).read_text(encoding="utf-8"))
        self.assertTrue(all(data["guardrails"].values()))
        self.assertEqual(build_matrix(self.p2, self.p3)["summary"][
            "full_2026_economic_PnL_proven_wallets"], 0)

    def test_wrong_window_must_fail(self):
        p3 = copy.deepcopy(self.p3)
        p3["window"]["start"] = "2026-09-14T00:00:00Z"
        with self.assertRaises(EvidenceError):
            build_matrix(self.p2, p3)


if __name__ == "__main__":
    unittest.main()
