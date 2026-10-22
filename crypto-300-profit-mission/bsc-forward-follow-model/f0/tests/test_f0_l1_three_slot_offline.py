"""Deterministic, network-free three-slot coordinator acceptance tests."""
import ast
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

F0 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(F0))
import f0_l1_three_slot_offline as mod


def latency_fixture():
    return {
        "eth_chainId": [350.0],
        "eth_blockNumber": [425.0, 430.0, 410.0],
        "eth_getBlockByNumber": [750.0, 850.0, 770.0, 800.0],
    }


class ThreeSlotOfflineTests(unittest.TestCase):
    def run_case(self, **kwargs):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "evidence"
            root.mkdir(mode=0o700)
            report = mod.simulate(latency_fixture(), root / "events.jsonl", **kwargs)
            raw_rows = [json.loads(line) for line in
                        (root / "events.jsonl").read_text().splitlines()]
            return report, raw_rows

    def test_import_path_has_no_transport_or_shell(self):
        tree = ast.parse((F0 / "f0_l1_three_slot_offline.py").read_text())
        names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names.update(x.name.split(".")[0] for x in node.names)
            if isinstance(node, ast.ImportFrom) and node.module:
                names.add(node.module.split(".")[0])
        self.assertFalse(names.intersection({
            "requests", "urllib", "ssl", "socket", "http", "aiohttp",
            "websocket", "subprocess", "concurrent", "threading",
            "asyncio",
        }))

    def test_identity_head_and_global_three_slot_rate_and_budget(self):
        result, journal = self.run_case()
        self.assertEqual(result["actual_network_requests"], 0)
        self.assertLessEqual(result["max_observed_inflight"], 3)
        self.assertLessEqual(result["requested_total"], 32)
        self.assertLessEqual(result["head_refreshes_requested"], 6)
        self.assertLessEqual(result["block_attempts"], 24)
        self.assertGreaterEqual(result["global_min_start_gap_ms"], 250)
        self.assertEqual(result["method_counts"]["eth_chainId"], 1)
        self.assertEqual(result["inflight_outcome_unknown_after_stop"], 0)
        reserves = [e for e in journal if e["event"] == "RESERVE_UNKNOWN"]
        self.assertEqual(len(reserves), result["requested_total"])
        self.assertEqual(reserves[0]["method"], "eth_chainId")
        self.assertEqual(reserves[1]["category"], "INITIAL_HEAD")
        for e in reserves[2:]:
            if e["category"] == "BLOCK":
                self.assertLessEqual(e["height"], e["confirmed_head"])
        self.assertEqual([e["id"] for e in reserves],
                         list(range(1, result["requested_total"] + 1)))
        self.assertGreater(result["head_refreshes_requested"], 0)

    def test_journal_reservation_precedes_settlement_and_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "private"
            root.mkdir(mode=0o700)
            ledger = root / "events.jsonl"
            doc = mod.simulate(latency_fixture(), ledger)
            records = [json.loads(s) for s in ledger.read_text().splitlines()]
            seen = set()
            for item in records:
                if item["event"] == "RESERVE_UNKNOWN":
                    self.assertNotIn(item["id"], seen)
                    seen.add(item["id"])
                if item["event"] == "SETTLE":
                    self.assertIn(item["id"], seen)
            original = ledger.read_bytes()
            with self.assertRaisesRegex(ValueError, "LEDGER_NOT_PRIVATE_OR_FRESH"):
                mod.simulate(latency_fixture(), ledger)
            self.assertEqual(original, ledger.read_bytes())
            self.assertEqual(len(seen), doc["requested_total"])

    def test_out_of_order_completion_never_counts_as_contiguous(self):
        normal, _ = self.run_case()
        delayed, _ = self.run_case(slow_heights={1002: 8})
        self.assertLessEqual(delayed["blocks_committed_contiguous"],
                             delayed["block_responses_received"])
        self.assertGreaterEqual(delayed["reorder_buffer_peak"], 1)
        self.assertGreaterEqual(normal["blocks_committed_contiguous"], 1)
        self.assertTrue(all(e["event"] != "COMMIT" or e["height"] >= 1001
                            for e in delayed["trace"]))

    def test_timeout_and_duplicate_do_not_hide_hole_or_spend_extra_budget(self):
        res, events = self.run_case(failed_heights={1002},
                                    duplicate_heights={1003})
        self.assertIn(1002, res["attempted_missing_heights"])
        self.assertLess(res["blocks_committed_contiguous"],
                        res["block_responses_received"])
        self.assertIn(1003, res["reorder_buffer_uncommitted_after_stop"])
        self.assertEqual(res["duplicate_receipts_ignored"], 1)
        self.assertEqual(res["method_counts"]["eth_chainId"], 1)
        self.assertLessEqual(res["requested_total"], 32)

    def test_parent_mismatch_blocks_contiguous_commit(self):
        res, _ = self.run_case(bad_parent_heights={1002})
        self.assertEqual(res["stop_state"], "PARENT_HASH_MISMATCH")
        self.assertEqual(res["blocks_committed_contiguous"], 1)
        self.assertIn(1002, res["parent_mismatch_heights"])
        self.assertEqual(res["inflight_outcome_unknown_after_stop"], 0)

    def test_head_regression_stops_without_retry(self):
        res, _ = self.run_case(head_values=[1001, 1000])
        self.assertEqual(res["stop_state"], "HEAD_REGRESSED_UNVERIFIED")
        self.assertEqual(res["head_refreshes_requested"], 1)
        self.assertEqual(res["inflight_outcome_unknown_after_stop"], 0)

    def test_global_capacity_honours_slower_source_and_expiry(self):
        normal, _ = self.run_case()
        slow, _ = self.run_case(slowdown=2.0)
        self.assertLessEqual(slow["max_observed_inflight"], 3)
        self.assertGreaterEqual(slow["virtual_elapsed_ms"],
                                normal["virtual_elapsed_ms"])
        self.assertLessEqual(slow["requested_total"], 32)
        expired, _ = self.run_case(max_duration_ms=1000)
        self.assertEqual(expired["stop_state"], "VIRTUAL_DURATION_CAP_EXPIRED")
        self.assertEqual(expired["inflight_outcome_unknown_after_stop"], 0)

    def test_simulated_abrupt_crash_leaves_unknown_reserved_no_retry(self):
        res, ledger = self.run_case(crash_after_reservations=4)
        self.assertEqual(res["stop_state"],
                         "SIMULATED_PROCESS_CRASH_OUTCOME_UNKNOWN")
        self.assertEqual(res["requested_total"], 4)
        self.assertGreater(res["inflight_outcome_unknown_after_stop"], 0)
        reserved = [x["id"] for x in ledger if x["event"] == "RESERVE_UNKNOWN"]
        settled = [x["id"] for x in ledger if x["event"] == "SETTLE"]
        self.assertTrue(set(settled).issubset(set(reserved)))
        self.assertGreater(len(reserved), len(settled))

    def test_head_and_block_share_inflight_slots_and_finish_counts(self):
        result, _ = self.run_case(head_freshness_ms=800,
                                  refresh_after=8)
        self.assertLessEqual(result["max_observed_inflight"], 3)
        self.assertLessEqual(result["head_refreshes_requested"], 6)
        self.assertEqual(result["requested_total"],
                         sum(result["method_counts"].values()))
        self.assertEqual(result["requested_total"],
                         result["method_counts"]["eth_chainId"] +
                         result["method_counts"]["eth_blockNumber"] +
                         result["method_counts"]["eth_getBlockByNumber"])

    def test_bad_request_ids_count_as_failed_not_received(self):
        res, _ = self.run_case(wrong_id_heights={1002})
        self.assertIn(1002, res["attempted_missing_heights"])
        self.assertGreater(res["block_failures"], 0)
        self.assertLess(res["blocks_committed_contiguous"],
                        res["block_responses_received"])


if __name__ == "__main__":
    unittest.main()
