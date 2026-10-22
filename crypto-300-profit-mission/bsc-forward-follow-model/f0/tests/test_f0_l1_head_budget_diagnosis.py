"""Offline diagnosis tests: synthetic HEAD budget, no network or user permit."""
import ast
from pathlib import Path
import sys
import tempfile
import unittest

F0 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(F0))
from f0_l1_head_budget_diagnosis import diagnose
from f0_l1_three_slot_offline import simulate


def samples():
    return {"eth_chainId": [350.0],
            "eth_blockNumber": [425.0, 426.0, 430.0],
            "eth_getBlockByNumber": [750.0, 770.0, 840.0]}


class HeadBudgetDiagnosisTests(unittest.TestCase):
    def run_case(self, **kwargs):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d)/"private"
            path.mkdir(mode=0o700)
            scenario = simulate(samples(), path/"trace.jsonl", **kwargs)
            diagnostic = diagnose(
                scenario, refresh_after=kwargs.get("refresh_after", 4),
                head_freshness_ms=kwargs.get("head_freshness_ms", 4000),
                max_blocks=kwargs.get("max_blocks", 24),
                max_refreshes=kwargs.get("max_refreshes", 6))
            return scenario, diagnostic

    def test_all_six_baseline_synthetic_budget_counters_reconcile(self):
        for period in (4, 8):
            for slowdown in (1.0, 1.5, 2.0):
                with self.subTest(period=period, slowdown=slowdown):
                    report, d = self.run_case(refresh_after=period,
                                              slowdown=slowdown)
                    self.assertEqual(d["actual_network_requests"], 0)
                    self.assertEqual(d["head_refreshes_requested"],
                                     report["head_refreshes_requested"])
                    self.assertEqual(sum(d["primary_refresh_triggers"].values()),
                                     report["head_refreshes_requested"])
                    self.assertEqual(d["blocks_attempted"], report["block_attempts"])
                    self.assertEqual(d["contiguous_commits"],
                                     report["blocks_committed_contiguous"])
                    self.assertTrue(d["three_shared_slots_verified_by_trace"])
                    self.assertGreaterEqual(d["global_slot_occupancy_ratio_virtual"], 0)
                    self.assertLessEqual(d["global_slot_occupancy_ratio_virtual"], 1)
                    self.assertEqual(d["unspent_block_attempt_budget"],
                                     24 - report["block_attempts"])

    def test_budget_exhaustion_is_not_a_failed_block(self):
        report, d = self.run_case()
        if d["head_budget_exhausted"]:
            self.assertEqual(report["block_failures"], 0)
            self.assertGreater(d["unspent_block_attempt_budget"], 0)
            self.assertEqual(d["head_refreshes_requested"], 6)
        self.assertEqual(d["known_unattempted_height_count"],
                         len(report["known_unattempted_heights"]))
        self.assertIn("synthetic source tip", d["interpretation"])

    def test_when_head_expires_pending_refresh_do_not_dispatch(self):
        slow = {"eth_chainId": [10.0],
                "eth_blockNumber": [10.0, 10.0, 5000.0],
                "eth_getBlockByNumber": [700.0]}
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)/"private"
            root.mkdir(mode=0o700)
            report = simulate(slow, root/"trace.jsonl",
                              head_values=[1000, 1100, 1200],
                              head_freshness_ms=4000,
                              refresh_after=8, max_blocks=16)
        diag = diagnose(report, refresh_after=8, head_freshness_ms=4000,
                        max_blocks=16)
        self.assertLessEqual(diag["block_dispatches_while_refresh_inflight"],
                             diag["blocks_attempted"])
        self.assertEqual(diag["head_refreshes_requested"],
                         report["head_refreshes_requested"])

    def test_bad_trace_rejected_and_no_live_transport_imports(self):
        report, _ = self.run_case()
        report["trace"][0]["at_ms"] = 500000
        with self.assertRaisesRegex(ValueError, "EVENT_ORDER_INVALID"):
            diagnose(report, refresh_after=4)
        tree = ast.parse((F0/"f0_l1_head_budget_diagnosis.py").read_text())
        roots=set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                roots.update(x.name.split(".")[0] for x in node.names)
            if isinstance(node, ast.ImportFrom) and node.module:
                roots.add(node.module.split(".")[0])
        self.assertFalse(roots.intersection({
            "requests", "urllib", "ssl", "socket", "http", "aiohttp",
            "websocket", "subprocess", "threading", "asyncio",
        }))


if __name__ == "__main__":
    unittest.main()
