"""F0 3-slot offline closed-loop fake source validation; zero network."""
import ast
import json
from pathlib import Path
import sys
import tempfile
import unittest

F0 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(F0))
from f0_l1_closed_loop_fake import SyntheticBscOracle, run_closed_loop


def timing():
    return {"eth_chainId":[350.0], "eth_blockNumber":[425.0, 420.0, 500.0],
            "eth_getBlockByNumber":[770.0, 850.0, 750.0, 790.0]}


class ThreeSlotClosedLoopFakeTests(unittest.TestCase):
    def one(self, oracle=None, **kw):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)/"private"
            root.mkdir(mode=0o700)
            report = run_closed_loop(timing(), root/"ledger.jsonl",
                                     oracle=oracle or SyntheticBscOracle(), **kw)
            rows = [json.loads(x) for x in (root/"ledger.jsonl").read_text().splitlines()]
            return report, rows

    @staticmethod
    def initial_height(report):
        return report["head_samples"][0]["head"] + 1

    def test_three_slots_total_fsync_before_fake_completion_and_budgets(self):
        r,rows=self.one()
        self.assertEqual(r["actual_network_requests"],0)
        self.assertFalse(r["network_sender_exists"])
        self.assertLessEqual(r["max_inflight_including_head"],3)
        self.assertLessEqual(r["attempts"],32)
        self.assertLessEqual(r["head_refreshes"],6)
        self.assertLessEqual(r["block_attempts"],24)
        self.assertGreaterEqual(r["min_global_start_gap_ms"],250)
        self.assertEqual(r["pending_after_stop"],0)
        self.assertEqual(r["contiguous_parent_verified_blocks"],
                         r["block_responses_accepted"])
        ids=set()
        for row in rows:
            if row["event"]=="RESERVE_UNKNOWN":
                self.assertNotIn(row["id"],ids)
                ids.add(row["id"])
            if row["event"]=="SETTLE":
                self.assertIn(row["id"],ids)
        self.assertEqual(len(ids),r["attempts"])
        self.assertEqual(sum(r["method_attempt_counts"].values()),r["attempts"])

    def test_head_updates_affect_future_reservations_no_oracle_peeking(self):
        r,rows=self.one()
        samples=r["head_samples"]
        self.assertGreaterEqual(len(samples),2)
        for reserve in (x for x in r["trace"] if x["event"]=="RESERVE_UNKNOWN"
                        and x["category"]=="BLOCK"):
            prior=[s for s in samples if s["at_ms"]<=reserve["at_ms"]]
            self.assertTrue(prior)
            self.assertLessEqual(reserve["height"],prior[-1]["head"])
            self.assertLess(reserve["at_ms"]-prior[-1]["at_ms"],4000)
        self.assertGreaterEqual(r["synthetic_oracle_tip_at_exit_not_real_network"],
                                r["last_confirmed_synthetic_head"])

    def test_block_http503_changes_dispatch_and_leaves_explicit_gap(self):
        baseline,_=self.one()
        first=self.initial_height(baseline)
        fault,_=self.one(SyntheticBscOracle(fail_blocks=[first]))
        self.assertEqual(fault["stop_state"],"BLOCK_FAULT_STOP_NO_RETRY")
        self.assertIn(first,fault["attempted_missing_heights"])
        self.assertEqual(fault["contiguous_parent_verified_blocks"],0)
        self.assertLess(fault["attempts"],baseline["attempts"])
        self.assertEqual(fault["pending_after_stop"],0)

    def test_bad_id_changes_future_dispatch_not_a_posthoc_warning(self):
        baseline,_=self.one()
        first=self.initial_height(baseline)
        result,_=self.one(SyntheticBscOracle(bad_id_blocks=[first]))
        self.assertEqual(result["stop_state"],"BLOCK_FAULT_STOP_NO_RETRY")
        self.assertTrue(any("HTTP_RPC_IDENTITY_MISMATCH" in x["reason"]
                            for x in result["faults"]))
        self.assertEqual(result["contiguous_parent_verified_blocks"],0)

    def test_timeout_consumes_budget_without_retry_and_drains_inflight(self):
        normal,_=self.one()
        first=self.initial_height(normal)
        report,ledger=self.one(SyntheticBscOracle(timeout_blocks=[first]))
        self.assertEqual(report["stop_state"],"BLOCK_FAULT_STOP_NO_RETRY")
        self.assertIn(first,report["attempted_missing_heights"])
        self.assertEqual(report["pending_after_stop"],0)
        self.assertEqual(len([x for x in ledger
                              if x["event"]=="RESERVE_UNKNOWN"]),
                         report["attempts"])

    def test_parent_mismatch_closes_dispatch_and_never_jumps_hole(self):
        normal,_=self.one()
        first=self.initial_height(normal)
        result,_=self.one(SyntheticBscOracle(bad_parent_blocks=[first+1]))
        self.assertEqual(result["stop_state"],"BLOCK_FAULT_STOP_NO_RETRY")
        self.assertEqual(result["contiguous_parent_verified_blocks"],1)
        self.assertLess(result["block_responses_accepted"],
                        normal["block_responses_accepted"])

    def test_head_refresh_failure_no_longer_dispatches_new_blocks(self):
        initial,_=self.one()
        fail,_=self.one(SyntheticBscOracle(head_fail_refreshes=[1]))
        self.assertEqual(fail["stop_state"],"SOURCE_IDENTITY_OR_HEAD_FAULT_STOP")
        self.assertLess(fail["attempts"],initial["attempts"])
        self.assertEqual(fail["pending_after_stop"],0)
        self.assertEqual(fail["head_refreshes"],1)

    def test_bad_block_body_hash_only_wrong_height_malformed_are_terminal(self):
        normal,_=self.one()
        first=self.initial_height(normal)
        for kw in ({"hash_only_blocks":[first]},
                   {"bad_height_blocks":[first]},
                   {"malformed_blocks":[first]}):
            with self.subTest(kw=kw):
                out,_=self.one(SyntheticBscOracle(**kw))
                self.assertEqual(out["stop_state"],"BLOCK_FAULT_STOP_NO_RETRY")
                self.assertIn(first,out["attempted_missing_heights"])
                self.assertEqual(out["contiguous_parent_verified_blocks"],0)

    def test_slow_head_does_not_let_stale_block_dispatch(self):
        slow = {"eth_chainId":[10.0],
                "eth_blockNumber":[10.0,10.0,5000.0],
                "eth_getBlockByNumber":[700.0]}
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/"private"
            root.mkdir(mode=0o700)
            report=run_closed_loop(
                slow,root/"ledger.jsonl",
                oracle=SyntheticBscOracle(growth_bps=5),
                policy="checkpoint", refresh_after_blocks=8)
        self.assertEqual(report["pending_after_stop"],0)
        for reservation in (x for x in report["trace"]
                            if x["event"]=="RESERVE_UNKNOWN"
                            and x["category"]=="BLOCK"):
            heads=[h for h in report["head_samples"]
                   if h["at_ms"] <= reservation["at_ms"]]
            self.assertLess(reservation["at_ms"]-heads[-1]["at_ms"],4000)

    def test_old_30_call_scope_not_increased_with_long_simulated_backlog(self):
        for speed in (0.5,1.0,2.178,5.0):
            for factor in (1.0,2.0):
                with self.subTest(speed=speed,factor=factor):
                    report,_=self.one(SyntheticBscOracle(growth_bps=speed),
                                      slowdown=factor)
                    self.assertLessEqual(report["attempts"],32)
                    self.assertLessEqual(report["block_attempts"],24)
                    self.assertLessEqual(report["head_refreshes"],6)
                    self.assertGreaterEqual(report["synthetic_oracle_tip_at_exit_not_real_network"],
                                            report["last_confirmed_synthetic_head"])
                    self.assertEqual(report["pending_after_stop"],0)

    def test_legacy_parent_and_new_closed_loop_are_separate(self):
        src=(F0/"f0_l1_closed_loop_fake.py").read_text()
        tree=ast.parse(src)
        imports=set()
        for node in ast.walk(tree):
            if isinstance(node,ast.Import):
                imports.update(x.name.split(".")[0] for x in node.names)
            elif isinstance(node,ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        self.assertFalse(imports.intersection({
            "socket","ssl","http","urllib","requests","aiohttp","websocket",
            "subprocess","threading","asyncio","concurrent"}))
        self.assertNotIn("def post",src)
        self.assertNotIn("--execute-live",src)

    def test_stop_then_drain_outstanding_does_not_forge_success(self):
        baseline,_=self.one()
        first=self.initial_height(baseline)
        faulty,_=self.one(SyntheticBscOracle(fail_blocks=[first+1]))
        self.assertEqual(faulty["pending_after_stop"],0)
        self.assertEqual(len([x for x in faulty["trace"] if x["event"]=="SETTLE"]),
                         faulty["attempts"])
        self.assertEqual(faulty["contiguous_parent_verified_blocks"],1)


if __name__=="__main__":
    unittest.main()
