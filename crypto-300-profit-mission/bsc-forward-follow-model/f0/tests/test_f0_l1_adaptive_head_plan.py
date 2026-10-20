"""Offline adaptive head scheduler tests; no socket, callback or RPC."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from f0_l1_adaptive_head_plan import (
    init_plan, next_action, apply_head_result, apply_block_result,
    summarize, throughput_scenarios,
)


class AdaptiveHeadOfflineTests(unittest.TestCase):
    def test_never_reads_future_height_before_new_confirmed_head(self):
        s=init_plan(initial_head=100,max_head_polls=2,max_block_reads=3,
                    head_poll_interval_ms=500)
        self.assertEqual(next_action(s,now_ms=0)["action"],"WAIT")
        self.assertEqual(next_action(s,now_ms=499)["action"],"WAIT")
        self.assertEqual(next_action(s,now_ms=500)["action"],"READ_HEAD")
        s=apply_head_result(s,now_ms=500,observed_head=103)
        self.assertEqual(next_action(s,now_ms=500)["action"],"WAIT")
        self.assertEqual(next_action(s,now_ms=750)["height"],101)
        self.assertEqual(next_action(s,now_ms=750)["params"],["0x65",True])
        self.assertEqual(summarize(s)["actual_rpc_calls_by_this_module"],0)

    def test_head_checkpoint_preserves_contiguous_next_heights(self):
        s=init_plan(initial_head=100,max_head_polls=3,max_block_reads=4,
                    refresh_after_blocks=2,head_poll_interval_ms=500)
        s=apply_head_result(s,now_ms=500,observed_head=102)
        s=apply_block_result(s,now_ms=750,received=True)
        s=apply_block_result(s,now_ms=1000,received=True)
        self.assertEqual(next_action(s,now_ms=1250)["action"],"READ_HEAD")
        s=apply_head_result(s,now_ms=1250,observed_head=104)
        self.assertEqual(next_action(s,now_ms=1500)["height"],103)
        s=apply_block_result(s,now_ms=1500,received=True)
        self.assertEqual(next_action(s,now_ms=1750)["height"],104)
        s=apply_block_result(s,now_ms=1750,received=True)
        self.assertEqual(next_action(s,now_ms=2000)["reason"],"BLOCK_ATTEMPT_BUDGET_COMPLETE")
        out=summarize(s)
        self.assertEqual(out["block_reads_attempted"],4)
        self.assertEqual(out["block_reads_received"],4)
        self.assertEqual(out["head_polls_attempted_after_initial"],2)
        self.assertEqual(out["next_unattempted_height"],105)
        self.assertFalse(out["live_head_lag_verified"])

    def test_head_poll_budget_exhaustion_does_not_guess_future_head(self):
        s=init_plan(initial_head=100,max_head_polls=1,max_block_reads=5)
        s=apply_head_result(s,now_ms=500,observed_head=101)
        s=apply_block_result(s,now_ms=750,received=True)
        action=next_action(s,now_ms=1000)
        self.assertEqual(action,{"action":"STOP","reason":"HEAD_POLL_BUDGET_EXHAUSTED"})
        self.assertEqual(s["next_height"],102)

    def test_missing_full_block_is_accounted_and_not_retried(self):
        s=init_plan(initial_head=100,max_head_polls=2,max_block_reads=2)
        s=apply_head_result(s,now_ms=500,observed_head=102)
        s=apply_block_result(s,now_ms=750,received=False)
        self.assertEqual(next_action(s,now_ms=1000)["height"],102)
        s=apply_block_result(s,now_ms=1000,received=True)
        result=summarize(s)
        self.assertEqual(result["explicit_missing_heights"],[101])
        self.assertEqual((result["block_reads_attempted"],result["block_reads_received"],
                          result["block_reads_failed"]),(2,1,1))

    def test_failed_head_consumes_budget_without_auto_retry(self):
        s=init_plan(initial_head=100,max_head_polls=4,max_block_reads=3)
        s=apply_head_result(s,now_ms=500,observed_head=None)
        self.assertEqual(s["head_polls_attempted"],1)
        self.assertTrue(s["head_poll_failure"])
        self.assertEqual(next_action(s,now_ms=1000),
                         {"action":"STOP","reason":"HEAD_SOURCE_FAILED_NO_RETRY"})

    def test_regressed_head_source_does_not_trigger_old_block_reads(self):
        s=init_plan(initial_head=100,max_head_polls=2,max_block_reads=3)
        s=apply_head_result(s,now_ms=500,observed_head=99)
        self.assertEqual(next_action(s,now_ms=1000)["reason"],"HEAD_REGRESSED_UNVERIFIED")
        self.assertEqual(s["confirmed_head"],100)
        self.assertEqual(s["block_reads_attempted"],0)

    def test_limit_blocks_even_if_head_reports_far_ahead(self):
        s=init_plan(initial_head=100,max_head_polls=2,max_block_reads=1)
        s=apply_head_result(s,now_ms=500,observed_head=10000)
        s=apply_block_result(s,now_ms=750,received=True)
        self.assertEqual(next_action(s,now_ms=1000)["reason"],"BLOCK_ATTEMPT_BUDGET_COMPLETE")
        self.assertEqual(s["next_height"],102)

    def test_interval_and_monotonic_sanity(self):
        s=init_plan(initial_head=100,max_head_polls=3,max_block_reads=2)
        with self.assertRaisesRegex(ValueError,"ADAPTIVE_INVALID_CLOCK_OR_STATE"):
            next_action(s,now_ms=-1)
        s=apply_head_result(s,now_ms=500,observed_head=103)
        with self.assertRaisesRegex(ValueError,"ADAPTIVE_INVALID_CLOCK_OR_STATE"):
            next_action(s,now_ms=499)
        self.assertEqual(next_action(s,now_ms=600)["wait_ms"],150)
        s=apply_block_result(s,now_ms=750,received=True)
        with self.assertRaisesRegex(ValueError,"ADAPTIVE_CLOCK_REGRESSION"):
            next_action(s,now_ms=600)

    def test_historical_60_block_rate_projection_does_not_promise_catch_up(self):
        p=throughput_scenarios(saved_blocks=60,header_span_s=26,
                               local_receipt_span_s=58.979,
                               recorded_block_request_median_ms=766.309,
                               candidate_interval_ms=250)
        self.assertEqual(p["observed_block_interval_mean_ms"],440.678)
        self.assertEqual(p["observed_local_receipt_pace_ms"],999.644)
        self.assertEqual(p["observed_elapsed_minus_header_span_s"],32.979)
        self.assertEqual(p["optimistic_sequential_no_fixed_wait_pace_ms"],766.309)
        self.assertEqual(p["projected_sequential_gap_growth_over_same_intervals_s"],19.212)
        self.assertFalse(p["sequential_median_alone_can_keep_up"])
        self.assertEqual(p["decision"],"ADAPTIVE_WAIT_REMOVAL_ALONE_INSUFFICIENT")
        self.assertIn("LIVE_HEAD_LAG",p["not_measured"])

    def test_possible_faster_scenario_does_not_become_live_assertion(self):
        p=throughput_scenarios(saved_blocks=60,header_span_s=26,
                               local_receipt_span_s=58.979,
                               recorded_block_request_median_ms=300)
        self.assertEqual(p["decision"],"SEQUENTIAL_POSSIBLY_FAST_ENOUGH_NOT_YET_PROVEN")
        self.assertTrue(p["scenario_only"])


if __name__=="__main__":
    unittest.main()
