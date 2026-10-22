"""Compare fixed and budget-preserving wait HEAD policies, offline only."""
import ast
import json
from pathlib import Path
import sys
import tempfile
import unittest

F0 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(F0))
from f0_l1_three_slot_offline import simulate
from f0_l1_head_policy_compare import compare


def timings():
    return {
        "eth_chainId": [10.0],
        "eth_blockNumber": [10.0, 10.0, 5000.0],
        "eth_getBlockByNumber": [700.0],
    }


class HeadWaitPolicyTests(unittest.TestCase):
    def one(self, name, **kwargs):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "private"
            root.mkdir(mode=0o700)
            return simulate(timings(), root / (name + ".jsonl"), **kwargs)

    def test_old_default_and_explicit_checkpoint_trace_identical(self):
        a = self.one("a", head_values=[1000, 1100, 1200],
                     refresh_after=8, max_blocks=16)
        b = self.one("b", head_values=[1000, 1100, 1200],
                     refresh_after=8, max_blocks=16,
                     head_policy="checkpoint")
        self.assertEqual(a["trace"], b["trace"])
        self.assertEqual(a["head_samples"], b["head_samples"])
        self.assertEqual(a["requested_total"], b["requested_total"])
        self.assertEqual(a["blocks_committed_contiguous"],
                         b["blocks_committed_contiguous"])

    def test_wait_does_not_poll_immediately_when_no_confirmed_height(self):
        fast = {"eth_chainId": [10.0],
                "eth_blockNumber": [10.0],
                "eth_getBlockByNumber": [700.0]}
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "private"
            root.mkdir(mode=0o700)
            old = simulate(fast, root/"base.jsonl",
                           head_values=[1000,1000,1010],
                           max_blocks=10)
            new = simulate(fast, root/"wait.jsonl",
                           head_values=[1000,1000,1010],
                           max_blocks=10, head_policy="availability_wait",
                           prefetch_available_heights=0,
                           min_head_refresh_age_ms=2500)
        def refresh_age(r):
            i = next(row for row in r["trace"]
                     if row["event"] == "SETTLE"
                     and row["category"] == "INITIAL_HEAD")
            refresh = next(row for row in r["trace"]
                           if row["event"] == "RESERVE_UNKNOWN"
                           and row["category"] == "HEAD_REFRESH")
            return refresh["at_ms"] - i["at_ms"]
        self.assertLess(refresh_age(old), 2500)
        self.assertGreaterEqual(refresh_age(new), 2500)
        self.assertLessEqual(new["requested_total"], 32)

    def test_pending_slow_head_5000ms_still_cannot_dispatch_stale_blocks(self):
        r = self.one("slow", head_values=[1000,1100,1200],
                     refresh_after=8, max_blocks=16,
                     head_policy="availability_wait",
                     min_head_refresh_age_ms=2500)
        events = r["trace"]
        completed_head_time = None
        for row in events:
            if row["event"] == "SETTLE" and row["category"] in (
                    "INITIAL_HEAD", "HEAD_REFRESH"):
                completed_head_time = row["at_ms"]
            if row["event"] == "RESERVE_UNKNOWN" and row["category"] == "BLOCK":
                self.assertIsNotNone(completed_head_time)
                self.assertLess(row["at_ms"] - completed_head_time, 4000)
                self.assertLessEqual(row["height"], row["confirmed_head"])
        self.assertEqual(r["inflight_outcome_unknown_after_stop"], 0)
        self.assertLessEqual(r["max_observed_inflight"], 3)
        self.assertGreaterEqual(r["global_min_start_gap_ms"], 250)

    def test_policy_decision_cannot_peek_at_future_head_growth(self):
        kwargs = dict(head_values=[1000,1200,1300],
                      head_policy="availability_wait",
                      min_head_refresh_age_ms=2500, max_blocks=5)
        first = self.one("a", source_growth_bps=0.5, **kwargs)
        second = self.one("b", source_growth_bps=5.0, **kwargs)
        self.assertEqual(first["trace"], second["trace"])

    def test_fixed_budget_constraints_under_both_policies(self):
        for policy in ("checkpoint", "availability_wait"):
            for period in (4,8):
                with self.subTest(policy=policy, period=period):
                    r = self.one("run", head_policy=policy,
                                 refresh_after=period, slowdown=1.5,
                                 min_head_refresh_age_ms=3500)
                    self.assertEqual(r["actual_network_requests"], 0)
                    self.assertLessEqual(r["max_observed_inflight"], 3)
                    self.assertGreaterEqual(r["global_min_start_gap_ms"], 250)
                    self.assertLessEqual(r["requested_total"], 32)
                    self.assertLessEqual(r["head_refreshes_requested"], 6)
                    self.assertLessEqual(r["block_attempts"], 24)
                    self.assertEqual(r["inflight_outcome_unknown_after_stop"], 0)
                    self.assertLessEqual(r["blocks_committed_contiguous"],
                                         r["block_responses_received"])

    def test_comparison_is_aggregate_and_never_reuses_ledger(self):
        fast = {"eth_chainId": [350.0],
                "eth_blockNumber": [425.0],
                "eth_getBlockByNumber": [770.0]}
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)/"private"
            root.mkdir(mode=0o700)
            data = compare(fast, root)
            self.assertEqual(len(data["cases"]), 6)
            self.assertEqual(data["actual_network_requests"], 0)
            for case in data["cases"]:
                self.assertEqual(len(case["variants"]), 4)
                self.assertEqual(case["variants"][0]["policy"], "checkpoint")
                for row in case["variants"]:
                    self.assertLessEqual(row["total_attempts"], 32)
                    self.assertLessEqual(row["head_refresh_attempts"], 6)
                    self.assertLessEqual(row["full_block_attempts"], 24)
                    self.assertLessEqual(row["max_inflight"], 3)
                    self.assertLessEqual(row["committed_contiguous"],
                                         row["responses_received"])
            with self.assertRaisesRegex(ValueError, "LEDGER_NOT_PRIVATE_OR_FRESH"):
                compare(fast, root)

    def test_reject_invalid_wait_beyond_head_freshness(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/"private"
            root.mkdir(mode=0o700)
            with self.assertRaisesRegex(ValueError, "OFFLINE_SIMULATION_SCOPE_INVALID"):
                simulate(timings(), root/"bad.jsonl",
                         head_policy="availability_wait",
                         min_head_refresh_age_ms=4000)
            self.assertFalse((root/"bad.jsonl").exists())

    def test_no_network_or_os_process_modules_in_comparator(self):
        tree = ast.parse((F0/"f0_l1_head_policy_compare.py").read_text())
        imported=set()
        for n in ast.walk(tree):
            if isinstance(n, ast.Import):
                imported.update(x.name.split(".")[0] for x in n.names)
            elif isinstance(n, ast.ImportFrom) and n.module:
                imported.add(n.module.split(".")[0])
        self.assertFalse(imported.intersection({
            "socket", "requests", "urllib", "ssl", "http", "websocket",
            "subprocess", "aiohttp", "asyncio", "threading",
        }))


if __name__ == "__main__":
    unittest.main()
