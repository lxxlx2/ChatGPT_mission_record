"""Unit tests for immutable real-summary sample capacity gate; zero network."""
from __future__ import annotations

import ast
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from f0_l1_saved_source_rate_gate import (  # noqa: E402
    INPUT_BLOB_SHA1, SUMMARY_FILE, assess_public_fields,
    evaluate_pinned_summary, git_blob_sha1, parse_pinned_summary,
)


def fields():
    return parse_pinned_summary(SUMMARY_FILE.read_bytes())


class SavedSourceRateGateTests(unittest.TestCase):
    def test_real_public_summary_git_blob_pinned_and_offline(self):
        raw = SUMMARY_FILE.read_bytes()
        self.assertEqual(git_blob_sha1(raw), INPUT_BLOB_SHA1)
        out = evaluate_pinned_summary(raw)
        self.assertEqual(out["input_git_blob_sha1"], INPUT_BLOB_SHA1)
        self.assertEqual(out["network_requests_by_analysis"], 0)
        self.assertEqual(out["raw_responses_reported_verified"], 62)
        self.assertEqual(out["raw_response_sha256_recomputed_by_this_tool"], 0)

    def test_rates_use_fifty_nine_intervals_not_sixty(self):
        out = evaluate_pinned_summary(SUMMARY_FILE.read_bytes())
        self.assertEqual(out["block_heights"], 60)
        self.assertEqual(out["height_interval_count"], 59)
        self.assertAlmostEqual(
            out["sample_header_progress_blocks_per_s"], 59 / 26, places=4)
        self.assertAlmostEqual(
            out["sample_response_progress_blocks_per_s"],
            59 / 58.979, places=4)
        self.assertAlmostEqual(
            out["sample_progress_rate_ratio_header_over_response"],
            58.979 / 26, places=4)
        self.assertEqual(out["serial_sample_rate_gate"],
                         "FAIL_OBSERVED_SAMPLE_ONLY")
        self.assertFalse(out["independent_live_chain_head_lag_proven"])
        self.assertFalse(
            out["improved_three_slot_or_alternate_provider_capacity_proven"])

    def test_insufficient_events_and_parent_gate_fail_closed(self):
        out = evaluate_pinned_summary(SUMMARY_FILE.read_bytes())
        self.assertEqual(out["wallet_signer_candidates_observed"], 0)
        self.assertEqual(out["router_address_selector_candidates"], 40)
        self.assertFalse(out["all_blocks_parent_anchored"])
        self.assertFalse(out["router_swap_causality_proven"])
        self.assertFalse(out["randomized_control_eligible"])
        self.assertFalse(out["actual_follow_profitability_proven"])
        self.assertEqual(out["actual_executable_quotes"], 0)
        self.assertEqual(out["f0_status"], "F0_NOT_PASSED")
        self.assertEqual(out["research_evidence_decision"],
                         "L1_INSUFFICIENT_FEASIBILITY_EVIDENCE")

    def test_public_summary_any_byte_mutation_fails_git_blob(self):
        raw = SUMMARY_FILE.read_bytes()
        with self.assertRaisesRegex(ValueError, "PUBLIC_SUMMARY_GIT_BLOB_MISMATCH"):
            evaluate_pinned_summary(raw + b" ")
        with self.assertRaisesRegex(ValueError, "PUBLIC_SUMMARY_GIT_BLOB_MISMATCH"):
            evaluate_pinned_summary(raw.replace(b"5940", b"5941"))

    def test_fake_parent_anchor_claim_rejected(self):
        x = fields()
        x["parent_hash_first_block_unanchored"] = False
        with self.assertRaisesRegex(ValueError, "PARENT_PROOF_MISMATCH"):
            assess_public_fields(x)

    def test_old_independent_request_changes_cannot_be_rewritten(self):
        x = fields()
        x["audit_review_status"] = "APPROVED"
        with self.assertRaisesRegex(ValueError, "HISTORICAL_P1_STATUS_CHANGED"):
            assess_public_fields(x)

    def test_selector_counts_not_equivalent_to_swap_or_controls(self):
        x = fields()
        x["router_selector_address_match_distribution"]["0x3593564c"] = 39
        with self.assertRaisesRegex(ValueError, "SELECTOR_COUNT_MISMATCH"):
            assess_public_fields(x)
        x = fields()
        x["control_eligible"] = True
        with self.assertRaisesRegex(ValueError, "UNPROVEN_OUTCOME_PROMOTION"):
            assess_public_fields(x)
        x = fields()
        x["quoted_actual_count"] = 1
        with self.assertRaisesRegex(ValueError, "UNPROVEN_OUTCOME_PROMOTION"):
            assess_public_fields(x)

    def test_boolean_and_nan_are_not_valid_numeric_evidence(self):
        x = fields()
        x["blocks"] = True
        with self.assertRaisesRegex(ValueError, "INVALID_INT:blocks"):
            assess_public_fields(x)
        x = fields()
        x["local_receipt_span_s"] = float("nan")
        with self.assertRaisesRegex(ValueError, "INVALID_NUMBER:local_receipt_span_s"):
            assess_public_fields(x)

    def test_missing_or_changed_heights_and_raw_denominators_fail(self):
        x = fields()
        x["height_last"] += 1
        with self.assertRaisesRegex(ValueError, "NONCONSECUTIVE_HEIGHT_RANGE"):
            assess_public_fields(x)
        x = fields()
        x["raw_responses_verified_sha256"] -= 1
        with self.assertRaisesRegex(ValueError, "RAW_RESPONSE_COUNT_INCONSISTENT"):
            assess_public_fields(x)

    def test_no_source_provenance_promotion_and_stale_metrics(self):
        x = fields()
        x["network_requests_by_analysis"] = 1
        with self.assertRaisesRegex(ValueError, "PROVENANCE_INVALID"):
            assess_public_fields(x)
        x = fields()
        x["mean_chain_interval_s_from_header_ts"] = 0.2
        with self.assertRaisesRegex(ValueError, "HEADER_INTERVAL_INCOHERENT"):
            assess_public_fields(x)

    def test_faster_hypothetical_sample_cannot_prove_live_success(self):
        x = fields()
        x["local_receipt_span_s"] = 20.0
        out = assess_public_fields(x)
        self.assertEqual(out["serial_sample_rate_gate"],
                         "NOT_FAILED_IN_OBSERVED_SAMPLE_ONLY")
        self.assertEqual(out["f0_status"], "F0_NOT_PASSED")
        self.assertFalse(out["independent_live_chain_head_lag_proven"])
        self.assertFalse(out["actual_follow_profitability_proven"])

    def test_import_tree_has_no_rpc_network_or_side_effect_transport(self):
        tree = ast.parse((ROOT / "f0_l1_saved_source_rate_gate.py").read_text())
        blocked = {
            "socket", "urllib", "requests", "http", "httpx", "aiohttp",
            "ssl", "websocket", "subprocess", "asyncio", "threading",
            "f0_l1_live_short", "f0_l2_d1_concrete_https",
        }
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(x.name.split(".")[0] for x in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        self.assertFalse(imports.intersection(blocked))
        funcs = {n.name for n in ast.walk(tree)
                 if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
        self.assertFalse({"send_live", "request", "execute_live"} & funcs)


if __name__ == "__main__":
    unittest.main()
