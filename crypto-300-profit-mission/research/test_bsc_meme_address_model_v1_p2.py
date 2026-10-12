#!/usr/bin/env python3
"""P2 cross-wallet economic import regression using frozen P1 and curated source evidence.

Runs without RPC/API keys, GMGN, installed dependencies or trading.
"""
from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from bsc_meme_address_model_v1_p2 import EvidenceError, build_economic_comparison

HERE = Path(__file__).resolve().parent


def fixtures():
    return (
        json.loads((HERE / "bsc-meme-address-model-v1-baseline-2026-10-13.json").read_text(encoding="utf-8")),
        json.loads((HERE / "bsc-meme-address-model-v1-p2-evidence-ledger-2026-10-13.json").read_text(encoding="utf-8")),
    )


class EconomicCrossWalletP2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.baseline, cls.ledger = fixtures()

    def build(self, baseline=None, ledger=None):
        return build_economic_comparison(
            copy.deepcopy(self.baseline) if baseline is None else baseline,
            copy.deepcopy(self.ledger) if ledger is None else ledger,
        )

    def test_full_23_wallets_and_no_profit_rank(self):
        r = self.build()
        self.assertEqual(r["summary"]["wallets_included"], 23)
        self.assertEqual(len(r["wallets"]), 23)
        self.assertFalse(r["summary"]["any_ranked_wallet"])
        for w in r["wallets"]:
            self.assertFalse(w["can_rank_by_profit"])
            self.assertIsNone(w["realized_profit_rank"])
            self.assertEqual(w["completed_full_wallet_all_CA_PnL"], "UNRESOLVED")
            self.assertEqual(w["recent_30d_signed_meme_swap"], "UNRESOLVED")
            self.assertFalse(w["followable_alpha_approved"])

    def test_curated_positive_and_negative_cases_preserved(self):
        s = self.build()["summary"]
        self.assertEqual(s["signed_closed_episodes_imported"], 32)
        self.assertEqual(s["selected_positive_episodes"], 21)
        self.assertEqual(s["selected_negative_episodes"], 11)
        self.assertEqual(s["wallets_with_curated_evidence"], 5)
        self.assertEqual(s["wallets_not_yet_economically_curated"], 18)

    def test_18_uncurated_wallets_are_not_zero_profit(self):
        for w in self.build()["wallets"]:
            if w["source_episodes_imported"] == 0:
                self.assertIsNone(w["native_only_event_block_scope_sum_wei"])
                self.assertIsNone(w["native_only_scope_excluding_largest_positive_wei"])
                self.assertEqual(w["economic_evidence_grade"],
                                 "NO_CURATED_P2_EPISODES_NOT_ZERO_PROFIT")

    def test_a83b_broccoli_negative_retained(self):
        w = next(w for w in self.build()["wallets"] if w["wallet"].startswith("0xa83b"))
        self.assertEqual((w["source_episodes_imported"], w["selected_negative_episode_count"]), (1, 1))
        self.assertEqual(w["native_only_event_block_scope_sum_wei"], "-239887492433116024")
        self.assertIsNone(w["native_only_largest_positive_episode_wei"])

    def test_ddac_with_ifml_losses_and_MARS_earnings(self):
        w = next(w for w in self.build()["wallets"] if w["wallet"].startswith("0xddac"))
        self.assertEqual((w["selected_positive_episode_count"],
                          w["selected_negative_episode_count"]), (5, 1))
        self.assertEqual(w["selected_positive_distinct_major_CAs_count"], 2)
        self.assertEqual(w["source_episodes_imported"], 6)
        self.assertIsNone(w["mixed_quote_actual_USDT_delta_sum_raw"])

    def test_8e6b_largest_win_concentration_and_real_USDT(self):
        w = next(w for w in self.build()["wallets"] if w["wallet"].startswith("0x8e6b"))
        self.assertEqual((w["source_episodes_imported"], w["selected_positive_episode_count"],
                          w["selected_negative_episode_count"]), (17, 10, 7))
        self.assertEqual(w["mixed_source_episodes"], 2)
        self.assertEqual(w["mixed_quote_actual_USDT_delta_sum_raw"], "4061629806775951927704")
        self.assertEqual(w["native_only_scope_excluding_largest_positive_wei"],
                         "10619003074952465592")
        self.assertFalse(w["can_rank_by_profit"])

    def test_2adf_small_proven_BOB_not_equated_to_other_unknown_token_profit(self):
        w = next(w for w in self.build()["wallets"] if w["wallet"].startswith("0x2adf"))
        self.assertEqual(w["source_episodes_imported"], 1)
        self.assertEqual(w["native_only_event_block_scope_sum_wei"], "9515610472872943")
        self.assertIsNone(w["mixed_quote_actual_BNB_delta_sum_wei"])

    def test_provenance_mismatch_rejected(self):
        b, d = fixtures()
        d["episodes"][0]["provenance"]["source_git_blob_sha"] = "b" * 40
        with self.assertRaisesRegex(EvidenceError, "source Git SHA"):
            self.build(b, d)

    def test_baseline_freeze_mismatch_rejected(self):
        b, d = fixtures()
        d["frozen_source_sha"] = "f" * 40
        with self.assertRaisesRegex(EvidenceError, "sha mismatch"):
            self.build(b, d)

    def test_duplicate_episode_rejected(self):
        b, d = fixtures()
        d["episodes"].append(copy.deepcopy(d["episodes"][0]))
        with self.assertRaisesRegex(EvidenceError, "double-count"):
            self.build(b, d)

    def test_false_wallet_token_source_rejected(self):
        b, d = fixtures()
        d["episodes"][0]["exact_ca"] = "0x" + "f" * 40
        with self.assertRaisesRegex(EvidenceError, "missing/absent exact CA"):
            self.build(b, d)

    def test_unverified_native_USDT_not_zero_faked(self):
        b, d = fixtures()
        x = next(e for e in d["episodes"]
                 if e["evidence_grade"] == "SIGNED_NATIVE_BLOCK_SCOPE")
        x["actual_USDT_delta_raw"] = "0"
        with self.assertRaisesRegex(EvidenceError, "must remain NULL"):
            self.build(b, d)

    def test_mixed_mark_missing_rejected(self):
        b, d = fixtures()
        x = next(e for e in d["episodes"] if e["evidence_grade"] == "MIXED_BNB_USDT_SPOT_REFERENCE")
        x["mark_USDT_equivalent_spot_reference_raw"] = None
        with self.assertRaisesRegex(EvidenceError, "historical quote"):
            self.build(b, d)

    def test_mixed_mark_fake_sign_rejected(self):
        b, d = fixtures()
        x = next(e for e in d["episodes"] if e["evidence_grade"] == "MIXED_BNB_USDT_SPOT_REFERENCE")
        x["net_classification"] = "NEGATIVE_QUOTE_MARK"
        with self.assertRaisesRegex(EvidenceError, "mixed quote sign"):
            self.build(b, d)

    def test_bad_owner_signature_rejected(self):
        b, d = fixtures()
        d["episodes"][0]["owner_signed_success_source_record"] = False
        with self.assertRaisesRegex(EvidenceError, "uncorroborated"):
            self.build(b, d)

    def test_pnl_or_live_trade_authorization_rejected(self):
        b, d = fixtures()
        d["episodes"][0]["is_full_wallet_PnL"] = True
        with self.assertRaisesRegex(EvidenceError, "improper PnL"):
            self.build(b, d)

    def test_trade_window_inversion_rejected(self):
        b, d = fixtures()
        d["episodes"][0]["first_block"] = 900
        d["episodes"][0]["last_block"] = 800
        with self.assertRaisesRegex(EvidenceError, "inverted"):
            self.build(b, d)

    def test_239e_new_cross_major_positive_and_negative_controls(self):
        w = next(w for w in self.build()["wallets"] if w["wallet"].startswith("0x239e"))
        self.assertEqual(w["source_episodes_imported"], 7)
        self.assertEqual(w["selected_positive_episode_count"], 5)
        self.assertEqual(w["selected_negative_episode_count"], 2)
        self.assertEqual(w["selected_positive_distinct_major_CAs_count"], 2)
        self.assertEqual(w["native_only_event_block_scope_sum_wei"], "296492314017711706")
        self.assertEqual(w["native_only_scope_excluding_largest_positive_wei"],
                         "100318745376932943")
        self.assertEqual(w["mixed_source_episodes"], 0)
        self.assertIsNone(w["realized_profit_rank"])
        self.assertEqual(w["recent_30d_signed_meme_swap"], "UNRESOLVED")

    def test_239e_27_signer_receipts_match_raw_closed_quantity_and_native_episodes(self):
        p = HERE
        tx = json.loads((p / "BSC_MEME_239E_TWO_MAJOR_FULL_SIGNED_FLOW_SOURCE_2026-10-11.json").read_text(encoding="utf-8"))
        rounds = json.loads((p / "BSC_MEME_239E_ORIGINAL_LATE_EPISODE_NATIVE_CASHFLOW_CHECK_2026-10-11.json").read_text(encoding="utf-8"))
        ifml = json.loads((p / "BSC_MEME_239E_IFML_ORIGINAL_TX_RECEIPT_PROVENANCE_2026-10-11.json").read_text(encoding="utf-8"))
        lobster = json.loads((p / "BSC_MEME_239E_LOBSTER_21_ORIGINAL_SIGNER_RECEIPT_AUDIT_2026-10-11.json").read_text(encoding="utf-8"))
        wallet = rounds["wallet"]
        self.assertEqual(sum(len(t["rows"]) for t in tx["tokens"][0]["scopes"]) +
                         sum(len(t["rows"]) for t in tx["tokens"][1]["scopes"]), 27)
        self.assertEqual((ifml["self_signed_count"], ifml["receipt_success_count"]), (6, 6))
        self.assertEqual((lobster["self_signed"], lobster["success"]), (21, 21))
        for c in rounds["cohorts"]:
            source = next(t for t in tx["tokens"] if t["token"] == c["token"])
            self.assertTrue(source["summary"]["complete"])
            self.assertEqual(source["summary"]["diff_raw"], "0")
            proof = lobster["rows"] if c["token"] == "龙虾" else ifml["rows"]
            by_hash = {t["hash"]: t for t in proof}
            self.assertEqual(len(by_hash), source["summary"]["unique_tx"])
            movements = sorted(
                [(t["block"], t["hash"], int(t["raw"], 16) * (1 if s["direction"] == "in" else -1))
                 for s in source["scopes"] for t in s["rows"]],
                key=lambda x: x[0],
            )
            inventory = 0
            pending = []
            closed = []
            for block, h, delta in movements:
                self.assertEqual(by_hash[h]["signer"], wallet)
                self.assertEqual(by_hash[h]["receipt_status"], "0x1")
                inventory += delta
                self.assertGreaterEqual(inventory, 0)
                pending.append((block, h))
                if inventory == 0:
                    ep = c["original_episodes"][len(closed)]
                    self.assertTrue(ep["closed"])
                    self.assertEqual((ep["first_block"], ep["last_block"], ep["tx_count"]),
                                     (pending[0][0], pending[-1][0], len(pending)))
                    current_net = (
                        sum(int(by_hash[h]["block_native_delta_wei"]) for _, h in pending)
                        if c["token"] == "龙虾"
                        else sum(int(x["delta_wei"]) for x in ep["native_wei_ledger"])
                    )
                    self.assertEqual(current_net, int(ep["block_native_delta_wei"]))
                    closed.append(ep)
                    pending = []
            self.assertEqual(inventory, 0)
            self.assertEqual(len(pending), 0)
            self.assertEqual(len(closed), len(c["original_episodes"]))


if __name__ == "__main__":
    unittest.main()
