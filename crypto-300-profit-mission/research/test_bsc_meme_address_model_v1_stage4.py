#!/usr/bin/env python3
"""Stage4 independently selected 2026 wallet negative controls, read-only stdlib tests."""
import json
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load(name):
    return json.loads((HERE / name).read_text(encoding="utf-8"))


def count_rounds(ins, outs):
    events = []
    for rows, direction in ((ins, 1), (outs, -1)):
        for x in rows:
            events.append((int(x.get("blockNum", x.get("block")), 16),
                           int(x.get("uniqueId", x.get("id")).split(":")[-1]),
                           x["hash"], int(x["raw"], 16) * direction))
    events.sort(key=lambda a: (a[0], a[1]))
    balance = 0
    txs = []
    rounds = []
    for block, log, tx, delta in events:
        balance += delta
        if balance < 0:
            raise AssertionError("Negative raw token inventory")
        txs.append(tx)
        if balance == 0:
            rounds.append(list(dict.fromkeys(txs)))
            txs = []
    return rounds, balance, len(events), len(txs)


class ModelStage4Tests(unittest.TestCase):
    def test_precommitted_selection_replayed_without_economic_lookahead(self):
        plan = load("bsc-meme-address-model-v1-p2-stage4-precommitted-2026-10-13.json")
        cases = {
            "A83B_NIULAI": (
                load("BSC_MEME_A83B_NIULAI_INBOUND_CURSOR_A_2026-10-12.json")["events"],
                load("BSC_MEME_A83B_NIULAI_OUTBOUND_CURSOR_A_2026-10-12.json")["events"],
                12, 0, 158),
            "877AF_MARSCOIN": (
                load("BSC_MEME_877AF_MARS_FULL_ERC20_RECONCILED_CENSUS_2026-10-12.json")["all_events_by_direction"]["in"],
                load("BSC_MEME_877AF_MARS_FULL_ERC20_RECONCILED_CENSUS_2026-10-12.json")["all_events_by_direction"]["out"],
                21, 68700271596483656647, 170),
        }
        for case in plan["selected"]:
            ins, outs, n, remainder, total = cases[case["scope"]]
            cycles, bal, logs, open_events = count_rounds(ins, outs)
            self.assertEqual((len(cycles), bal, logs), (n, remainder, total))
            pick = next((i, x) for i, x in enumerate(cycles, 1)
                        if i > 1 and len(x) <= 3)
            self.assertEqual(pick[0], case["original_episode_index"])
            self.assertEqual(pick[1], case["transaction_hashes"])
            self.assertEqual(len(pick[1]), 3)
            self.assertEqual(open_events, 0 if not remainder else 2)

    def test_exact_original_signers_status_and_native_balance_unique_blocks(self):
        proof = load("bsc-meme-address-model-v1-p2-stage4-two-negative-2026-signed-rounds-2026-10-13.json")
        plan = load("bsc-meme-address-model-v1-p2-stage4-precommitted-2026-10-13.json")
        self.assertTrue(proof["selection_was_frozen_before_RPC"])
        self.assertEqual(proof["summary"]["original_owner_successful_txs"], 6)
        self.assertEqual(proof["summary"]["unique_native_account_blocks"], 5)
        self.assertEqual(proof["summary"]["negative_native_scope_rounds"], 2)
        for expect, row in zip(plan["selected"], proof["rounds"]):
            self.assertEqual(expect["transaction_hashes"],
                             [t["hash"] for t in row["original_transactions"]])
            self.assertEqual((expect["wallet"], expect["exact_ca"], expect["original_episode_index"]),
                             (row["wallet"], row["exact_ca"], row["inventory_zero_round_index"]))
            self.assertEqual(len({t["block"] for t in row["original_transactions"]}),
                             len(row["unique_block_native_account_scopes"]))
            self.assertEqual(int(row["native_wallet_block_scope_wei"]),
                             sum(int(b["historical_native_N_minus_1_to_N_wei"])
                                 for b in row["unique_block_native_account_scopes"]))
            self.assertTrue(all(t["EOA_self_signed"] and t["original_receipt_status"] == "0x1"
                                for t in row["original_transactions"]))
            self.assertEqual(row["economic_sign"], "NEGATIVE_NATIVE_SCOPE")
            self.assertFalse(row["fully_exhaustive_CA_PnL"])

    def test_same_block_two_buy_transactions_do_not_duplicate_bnb_delta(self):
        p = load("bsc-meme-address-model-v1-p2-stage4-two-negative-2026-signed-rounds-2026-10-13.json")
        w = next(x for x in p["rounds"] if x["scope"] == "A83B_NIULAI")
        self.assertEqual([r["block"] for r in w["original_transactions"]],
                         [116113193, 116113193, 116113197])
        self.assertEqual([x["number_of_selected_owner_txs_in_block"]
                          for x in w["unique_block_native_account_scopes"]], [2, 1])
        self.assertEqual(w["original_transaction_value_inputs_wei"], "2800000000000000000")
        self.assertEqual(w["native_wallet_block_scope_wei"], "-213598956812665039")
        wrong_double_counted = 2 * -2896673890000000000 + 2683074933187334961
        self.assertNotEqual(int(w["native_wallet_block_scope_wei"]), wrong_double_counted)

    def test_blockers_apply_at_episode_not_entire_ca(self):
        block = load("bsc-meme-address-model-v1-p2-2026-eligibility-blocker-queue-2026-10-13.json")
        ledger = load("bsc-meme-address-model-v1-p2-evidence-ledger-2026-10-13.json")
        self.assertEqual(len(block["items"]), 8)
        self.assertTrue(block["previous_absolute_CA_exclusion_policy_is_invalid"])
        for item in block["items"]:
            admitted = {e["episode_index"] for e in ledger["episodes"]
                        if e["wallet"] == item["wallet"] and e["exact_ca"] == item["ca"]}
            self.assertEqual(admitted, set(item["audited_closed_episode_indices"]))
            self.assertTrue(admitted.isdisjoint(item["blocked_specific_episode_indices"]))
            self.assertEqual(item["entire_CA_profit_pnl_state"], "UNRESOLVED")
        a = next(x for x in block["items"] if x["wallet"].startswith("0xa83b"))
        b = next(x for x in block["items"] if x["wallet"].startswith("0x877a"))
        self.assertEqual((a["audited_closed_episode_indices"],
                          len(a["blocked_specific_episode_indices"])), ([2], 11))
        self.assertEqual((b["audited_closed_episode_indices"],
                          len(b["blocked_specific_episode_indices"])), ([4, 5, 6, 10], 17))

    def test_two_negative_rounds_in_23_wallet_comparison_no_profit_ranking(self):
        comparison = load("bsc-meme-address-model-v1-p2-economic-comparison-2026-10-13.json")
        s = comparison["summary"]
        self.assertEqual((s["wallets_included"], s["wallets_with_curated_evidence"],
                          s["signed_closed_episodes_imported"]), (23, 7, 50))
        self.assertEqual((s["selected_positive_episodes"], s["selected_negative_episodes"]),
                         (32, 18))
        a = next(x for x in comparison["wallets"] if x["wallet"].startswith("0xa83b"))
        b = next(x for x in comparison["wallets"] if x["wallet"].startswith("0x877a"))
        self.assertEqual((a["selected_positive_episode_count"],
                          a["selected_negative_episode_count"]), (0, 4))
        self.assertEqual(b["native_only_event_block_scope_sum_wei"], "215047351526192606")
        for wallet in comparison["wallets"]:
            self.assertIsNone(wallet["realized_profit_rank"])
            self.assertFalse(wallet["can_rank_by_profit"])
            self.assertEqual(wallet["recent_30d_signed_meme_swap"], "UNRESOLVED")


if __name__ == "__main__":
    unittest.main()
