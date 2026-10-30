#!/usr/bin/env python3
"""Offline proof QA for frozen 16 cross-wallet BSC-Meme candidate cycles.

Raw 2026-major token transfers are NOT economic trades.  Proof requires real
original EOA signature + receipt success + inventory close + native N-1/N wallet
balance per *unique* block.  No RPC, credentials, paid APIs or deployment.
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path
from collections import Counter

P = Path(__file__).resolve().parent


def data(name):
    return json.loads((P / name).read_text(encoding="utf-8"))


def read_rows(obj, field):
    if "all_events_by_direction" in obj:
        return obj["all_events_by_direction"][field]
    if "transfers" in obj:
        return obj["transfers"][field]
    if field in obj and isinstance(obj[field], dict):
        return obj[field]["events"]
    return obj["events"]


def original_cycles(ins, outs):
    entries = []
    for side, rows in (("in", ins), ("out", outs)):
        for e in rows:
            block = int(e.get("blockNum", e.get("block")), 16)
            uid = e.get("uniqueId", e.get("uid", e.get("id")))
            log_index = int(uid.split(":")[-1])
            value = int(e["raw"], 16) * (1 if side == "in" else -1)
            entries.append((block, log_index, e["hash"], value))
    entries.sort(key=lambda x: (x[0], x[1]))
    quantity, current, cycles = 0, [], []
    for block, log_index, h, value in entries:
        quantity += value
        assert quantity >= 0, "negative inventory or incorrect event order"
        current.append((block, h))
        if quantity == 0:
            cycles.append({
                "episode_index": len(cycles) + 1,
                "first_block": current[0][0],
                "last_block": block,
                "raw_transfer_log_count": len(current),
                "transaction_hashes": list(dict.fromkeys(h for _, h in current)),
            })
            current = []
    return cycles, quantity, len(entries), len(current)


def compiled():
    return (
        data("bsc-meme-address-model-v1-p2-bulk16-precommit-2026-10-13.json"),
        data("bsc-meme-address-model-v1-p2-bulk16-gate-decisions-2026-10-13.json"),
        data("bsc-meme-address-model-v1-p2-bulk16-verified-outcomes-2026-10-13.json"),
        data("bsc-meme-address-model-v1-p2-evidence-ledger-2026-10-13.json"),
    )


class Bulk16SourceProofTests(unittest.TestCase):
    def test_raw_7_ca_roster_and_precommit_replay_without_pnl_selection(self):
        p, _, _, _ = compiled()
        self.assertEqual((len(p["source_manifest"]), len(p["per_CA_census"]),
                          len(p["samples"])), (9, 7, 16))
        pairs = [
            ("A83B", "牛来", "BSC_MEME_A83B_NIULAI_INBOUND_CURSOR_A_2026-10-12.json",
             "BSC_MEME_A83B_NIULAI_OUTBOUND_CURSOR_A_2026-10-12.json"),
            ("877AF", "MARSCOIN", "BSC_MEME_877AF_MARS_FULL_ERC20_RECONCILED_CENSUS_2026-10-12.json", None),
            ("877AF", "牛来", "BSC_MEME_877AF_NIULAI_FULL_ERC20_RECONCILED_CENSUS_2026-10-12.json", None),
            ("ADFF", "我踏马来了", "BSC_MEME_ADFF_WOTAMALA_FULL_CURSOR_BALANCE_QA_2026-10-12.json", None),
            ("ADFF", "龙虾", "BSC_MEME_ADFF_LOBSTER_FULL_CURSOR_BALANCE_QA_2026-10-12.json", None),
            ("2ADF", "牛来", "BSC_MEME_2ADF_NIULAI_FULL_CURSOR_BALANCE_QA_2026-10-12.json", None),
            ("A83B", "龙虾", "BSC_MEME_A83B_LOBSTER_INBOUND_CURSOR_A_2026-10-12.json",
             "BSC_MEME_A83B_LOBSTER_OUTBOUND_CURSOR_A_2026-10-12.json"),
        ]
        reconstructed = []
        for (prefix, token, first, second), roster in zip(pairs, p["per_CA_census"]):
            src = data(first)
            in_rows = read_rows(src, "in")
            out_rows = read_rows(src, "out") if second is None else data(second)["events"]
            cycles, balance, event_count, pending = original_cycles(in_rows, out_rows)
            self.assertEqual((src["wallet"], src["ca"]), (roster["wallet"], roster["exact_ca"]))
            self.assertEqual((event_count, len(cycles), str(balance)),
                             (roster["source_raw_logs"], roster["source_zero_inventory_cycles"],
                              roster["source_final_inventory_raw"]))
            prior = set(roster["already_model_admitted_episodes"])
            shortlisted = [c for c in cycles
                           if c["episode_index"] not in prior
                           and len(c["transaction_hashes"]) <= 4][:3]
            self.assertEqual(len(shortlisted), roster["preselected_cycle_count"])
            for c in shortlisted:
                reconstructed.append((src["wallet"], token, src["ca"], c))
        self.assertEqual(len(reconstructed), 16)
        for computed, saved in zip(reconstructed, p["samples"]):
            w, token, ca, c = computed
            for key, expect in (("wallet", w), ("token", token), ("exact_ca", ca),
                                ("episode_index", c["episode_index"]),
                                ("first_block", c["first_block"]),
                                ("last_block", c["last_block"]),
                                ("raw_transfer_log_count", c["raw_transfer_log_count"]),
                                ("transaction_hashes", c["transaction_hashes"])):
                self.assertEqual(saved[key], expect)

    def test_all_39_original_transaction_hashes_and_success_gate(self):
        p, gate, outcome, ledger = compiled()
        wanted = [h for s in p["samples"] for h in s["transaction_hashes"]]
        original = [t for x in gate["cases"] for t in x["member_txs"]]
        self.assertEqual(len(wanted), 39)
        self.assertEqual(len(set(wanted)), 39)
        self.assertEqual(len(original), 39)
        self.assertEqual([t["hash"] for t in original], wanted)
        self.assertEqual(gate["gate_approved_sample_count"], 13)
        self.assertEqual(gate["gate_rejected_sample_count"], 3)
        self.assertEqual(gate["original_owner_signers"], 34)
        self.assertEqual(gate["receipt_success_statuses"], 38)
        self.assertEqual(gate["parse_failed_tx_records"], 1)

    def test_13_admitted_native_proofs_unique_blocks_and_explicit_loss(self):
        p, gate, proof, ledger = compiled()
        selected = [r for r in proof["rounds"] if r["owner_signed_eligible"]]
        self.assertEqual(len(selected), 13)
        self.assertEqual(sum(len(r["source_txs"]) for r in selected), 31)
        self.assertEqual(sum(len(r["source_native_block_deltas"]) for r in selected), 31)
        self.assertEqual(Counter(r["native_scope_sign"] for r in selected),
                         {"POSITIVE_NATIVE_SCOPE": 9, "NEGATIVE_NATIVE_SCOPE": 4})
        unique = set()
        for r in selected:
            self.assertTrue(r["earliest_block_UTC_verified"])
            self.assertIsNotNone(r["first_utc"])
            self.assertEqual([t["hash"] for t in r["source_txs"]],
                             p["samples"][r["selection_index"]]["transaction_hashes"])
            self.assertTrue(all(t["is_owner_signer"] and t["status"] == "0x1"
                                for t in r["source_txs"]))
            self.assertEqual({t["block"] for t in r["source_txs"]},
                             {b["block"] for b in r["source_native_block_deltas"]})
            tally = 0
            for row in r["source_native_block_deltas"]:
                key = r["wallet"], row["block"]
                self.assertNotIn(key, unique, "same wallet/block attributed to two selected episodes")
                unique.add(key)
                self.assertEqual(int(row["n_wei"]) - int(row["n_minus_1_wei"]),
                                 int(row["native_delta_wei"]))
                tally += int(row["native_delta_wei"])
            self.assertEqual(tally, int(r["native_scope_net_wei"]))
            self.assertFalse(r["followable_alpha"])
            self.assertEqual(r["quote_asset_gas_internal_causal_PnL"], "UNVERIFIED")
        self.assertEqual(len(unique), 31)

    def test_nonowner_and_oversized_original_source_are_never_imported(self):
        _, gate, proof, ledger = compiled()
        rejected = [r for r in proof["rounds"] if not r["owner_signed_eligible"]]
        self.assertEqual(len(rejected), 3)
        self.assertEqual({r["selection_index"] for r in rejected}, {0, 1, 15})
        self.assertEqual({r["gate_reason"] for r in rejected},
                         {"THIRD_PARTY_OR_NONOWNER_ORIGINAL_TX",
                          "TRUNCATED_RPC_ORIGINAL_SENDER_UNVERIFIED"})
        keyed = {(e["wallet"], e["exact_ca"], e["episode_index"]) for e in ledger["episodes"]}
        for r in rejected:
            self.assertIsNone(r["native_scope_net_wei"])
            self.assertNotIn((r["wallet"], r["exact_ca"], r["episode_index"]), keyed)

    def test_all_13_imported_provenance_and_no_full_wallet_pnl(self):
        _, gate, proof, ledger = compiled()
        imported = [e for e in ledger["episodes"]
                    if "bsc-meme-address-model-v1-p2-bulk16-verified-outcomes" in
                    e["provenance"]["source_path"]]
        self.assertEqual(len(imported), 13)
        for r in proof["rounds"]:
            matches = [e for e in imported if
                       (e["wallet"], e["exact_ca"], e["episode_index"]) ==
                       (r["wallet"], r["exact_ca"], r["episode_index"])]
            self.assertEqual(len(matches), int(r["owner_signed_eligible"]))
            if matches:
                e = matches[0]
                self.assertEqual(e["net_native_BNB_wallet_event_blocks_wei"],
                                 r["native_scope_net_wei"])
                self.assertEqual(e["net_classification"], r["native_scope_sign"])
                self.assertEqual(e["evidence_grade"], "SIGNED_NATIVE_BLOCK_SCOPE")
                self.assertFalse(e["is_full_wallet_PnL"])
                self.assertFalse(e["is_followable_alpha"])
                self.assertIsNone(e["actual_USDT_delta_raw"])

    def test_2025_signed_IFML_not_mislabeled_as_2026_activity(self):
        _, gate, proof, ledger = compiled()
        passed = [r for r in proof["rounds"] if r["owner_signed_eligible"]]
        self.assertEqual(sum(r["first_utc"].startswith("2025-") for r in passed), 3)
        self.assertEqual(sum(r["first_utc"].startswith("2026-") for r in passed), 10)
        self.assertEqual(proof["summary"]["eligible_2025_origin_cycles"], 3)
        self.assertEqual(proof["summary"]["eligible_2026_origin_cycles"], 10)

    def test_model_all_23_not_cherry_picked_profits(self):
        data_obj = data("bsc-meme-address-model-v1-p2-economic-comparison-2026-10-13.json")
        summary = data_obj["summary"]
        self.assertEqual((summary["wallets_included"], summary["signed_closed_episodes_imported"],
                          summary["wallets_with_curated_evidence"],
                          summary["wallets_not_yet_economically_curated"]), (23, 50, 7, 16))
        self.assertEqual((summary["selected_positive_episodes"],
                          summary["selected_negative_episodes"]), (32, 18))
        self.assertFalse(summary["any_ranked_wallet"])
        for wallet in data_obj["wallets"]:
            self.assertIsNone(wallet["realized_profit_rank"])
            self.assertEqual(wallet["completed_full_wallet_all_CA_PnL"], "UNRESOLVED")
            self.assertEqual(wallet["recent_30d_signed_meme_swap"], "UNRESOLVED")

    def test_877af_unverified_original_mars_cycles_stay_blocked(self):
        _, _, _, ledger = compiled()
        q = data("bsc-meme-address-model-v1-p2-2026-eligibility-blocker-queue-2026-10-13.json")
        rows = [e for e in ledger["episodes"]
                if e["wallet"].startswith("0x877a") and e["token"] == "MARSCOIN"]
        blocked = next(x for x in q["items"]
                       if x["wallet"].startswith("0x877a") and x["token"] == "MARSCOIN")
        self.assertEqual(len(rows), 4)
        self.assertEqual({e["episode_index"] for e in rows}, {4, 5, 6, 10})
        self.assertEqual(blocked["audited_closed_episode_indices"], [4, 5, 6, 10])
        self.assertEqual(len(blocked["blocked_specific_episode_indices"]), 17)
        self.assertTrue(set(blocked["blocked_specific_episode_indices"]).isdisjoint(
            blocked["audited_closed_episode_indices"]))
        self.assertEqual(blocked["entire_CA_profit_pnl_state"], "UNRESOLVED")

    def test_P3_one_recent_owner_meme_action_but_22_wallets_unverified(self):
        p3 = data("bsc-meme-address-model-v1-p3-recent-signer-positive-witness-2026-10-13.json")
        self.assertEqual(p3["frozen_wallet_count"], 23)
        self.assertEqual(p3["confirmed_signed_Meme_token_action_wallets"], 1)
        self.assertEqual(p3["unknown_wallets_not_full_window_scanned"], 22)
        self.assertEqual(p3["status"], "PARTIAL_POSITIVE_WITNESS_ONLY_NOT_COMPLETE_P3")
        v = p3["proven_2026_30d_owner_action"]
        self.assertTrue(v["original_owner_signed_and_successful"])
        self.assertTrue(v["original_EOA_token_in_and_out"])
        self.assertTrue(v["first_utc"].startswith("2026-09-14T"))
        self.assertEqual(v["quote_route_economics"], "UNRESOLVED")
        self.assertTrue(all(not w["proved_inactive"] for w in p3["wallets"]))
        self.assertEqual(sum(w["signed_Meme_token_action_verified"] ==
                             "AT_LEAST_ONE_TRUE_EOA_INITIATED_MEME_TOKEN_MOVEMENT"
                             for w in p3["wallets"]), 1)


if __name__ == "__main__":
    unittest.main()
