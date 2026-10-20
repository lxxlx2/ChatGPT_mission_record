"""Source-core integration using ONLY a scripted in-memory fake HTTP callback."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from f0_l1_adaptive_journal_replay import FakeClock
from f0_l1_adaptive_source_core import collect_adaptive_injected

COHORT=(ROOT/"F0_COHORT_PRESELECTION.json").read_bytes()
ROUTERS=(ROOT/"F0_ROUTER_SOURCE_CANDIDATES.json").read_bytes()


def chain():
    return {"method":"eth_chainId","params":[],"result":"0x38"}


def head(height):
    return {"method":"eth_blockNumber","params":[],"result":hex(height)}


def block(height, *, parent=None, latency_ms=15):
    return {"method":"eth_getBlockByNumber","params":[hex(height),True],
            "result":{"number":hex(height),"hash":"0x"+format(height,"064x"),
                      "parentHash":parent or "0x"+format(height-1,"064x"),
                      "transactions":[]},"latency_ms":latency_ms}


def null_block(height):
    return {"method":"eth_getBlockByNumber","params":[hex(height),True],
            "result":None}


class AdaptiveSourceCoreFakeTests(unittest.TestCase):
    def run_frames(self, root, frames, *, total=12, block_cap=4,
                   head_cap=4, refresh=4, duration=60000, cohort=COHORT,
                   routers=ROUTERS, interrupt_at=None):
        clock=FakeClock()
        calls=[]
        def post(endpoint, body, timeout, cap):
            request=json.loads(body)
            journal=json.loads((root/"journal.json").read_text())
            self.assertEqual(journal["attempts"][-1]["state"],
                             "ATTEMPTED_OUTCOME_UNKNOWN")
            self.assertEqual(journal["attempted_calls"],request["id"])
            if interrupt_at == request["id"]:
                raise KeyboardInterrupt()
            index=len(calls)
            self.assertLess(index,len(frames),"unplanned extra fake request")
            expected=frames[index]
            self.assertEqual(request["method"],expected["method"])
            self.assertEqual(request["params"],expected["params"])
            calls.append(request)
            latency=expected.get("latency_ms",15)
            if latency:
                clock.sleep(latency/1000)
            payload={"jsonrpc":"2.0","id":request["id"]}
            payload["result" if "result" in expected else "error"]=(
                expected["result"] if "result" in expected else expected["error"])
            return 200,{"Content-Type":"application/json"},json.dumps(payload).encode()
        report=collect_adaptive_injected(
            post=post,clock=clock.utc,mono=clock.mono,sleep=clock.sleep,
            output_root=root,cohort_raw=cohort,router_raw=routers,
            max_total_attempts=total,max_block_reads=block_cap,
            max_head_polls=head_cap,refresh_after_blocks=refresh,
            duration_ms=duration)
        return report,calls

    def test_two_identity_one_head_two_blocks_are_five_persisted_attempts(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            report,calls=self.run_frames(
                root,[chain(),head(100),head(102),block(101),block(102)],
                total=5,head_cap=1,block_cap=2)
            self.assertEqual(len(calls),5)
            self.assertEqual(report["total_attempts"],5)
            self.assertEqual(report["category_counts"],
                             {"CHAIN_ID":1,"INITIAL_HEAD":1,"READ_BLOCK":2,"READ_HEAD":1})
            self.assertEqual(report["block_read_successes"],2)
            self.assertEqual(report["block_read_failures"],0)
            self.assertEqual(report["verified_internal_parent_links"],1)
            self.assertFalse(report["initial_saved_block_parent_anchored"])
            self.assertEqual(report["head_samples"][1]["sampled_head_minus_last_attempted_height"],2)
            self.assertEqual(report["source_attestation"],"UNVERIFIED_CALLER_CALLBACK")
            self.assertEqual(report["external_real_rpc_calls"],"UNVERIFIED")
            self.assertFalse(report["candidate_control_eligible"])
            self.assertEqual(report["private_raw_archives"],5)
            self.assertEqual(json.loads((root/"journal.json").read_text())["attempted_calls"],5)

    def test_total_cap_counts_head_polls_and_never_invokes_extra_source(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            r,calls=self.run_frames(root,[chain(),head(100),head(102),block(101)],
                                    total=4,head_cap=2,block_cap=2)
            self.assertEqual(r["stop_state"],"TOTAL_ATTEMPT_BUDGET_EXHAUSTED")
            self.assertEqual(len(calls),4)
            self.assertEqual(r["block_read_attempts"],1)
            self.assertEqual(r["unattempted_block_budget"],1)
            self.assertEqual(r["journal_attempts"],4)
            self.assertTrue(r["method_counts_reconcile"])

    def test_sampled_backlog_grows_while_slow_block_receipts_arrive(self):
        frames=[chain(),head(100),head(104),block(101,latency_ms=800),
                block(102,latency_ms=800),head(110),block(103,latency_ms=800),
                block(104,latency_ms=800)]
        with tempfile.TemporaryDirectory() as d:
            r,calls=self.run_frames(Path(d),frames,total=8,head_cap=2,
                                    block_cap=4,refresh=2)
            self.assertEqual(r["block_read_successes"],4)
            self.assertEqual(r["verified_internal_parent_links"],3)
            refreshed=[x for x in r["head_samples"] if x["type"]=="HEAD_REFRESH"]
            self.assertEqual([x["sampled_head_minus_last_attempted_height"]
                              for x in refreshed],[4,8])
            self.assertEqual(r["head_lag_interpretation"],
                             "LAST_SOURCE_SAMPLED_HEAD_ONLY_NOT_INDEPENDENT_NETWORK_HEAD")
            self.assertEqual(r["external_real_rpc_calls"],"UNVERIFIED")
            self.assertEqual(len(calls),8)

    def test_stagnant_head_backoff_is_virtual_time_not_free_head_calls(self):
        frames=[chain(),head(100),head(100),head(100),head(101),block(101)]
        with tempfile.TemporaryDirectory() as d:
            r,calls=self.run_frames(Path(d),frames,total=6,
                                    head_cap=3,block_cap=1)
            self.assertEqual(r["block_read_successes"],1)
            self.assertEqual(r["head_refreshes"],3)
            self.assertEqual(len(calls),6)
            self.assertEqual([x["sampled_head"] for x in r["head_samples"]],
                             [100,100,100,101])
            self.assertEqual(r["scheduler"]["head_stagnation_streak"],0)

    def test_null_block_has_explicit_missing_height_and_no_retry(self):
        frames=[chain(),head(100),head(102),null_block(101),block(102)]
        with tempfile.TemporaryDirectory() as d:
            r,calls=self.run_frames(Path(d),frames,total=5,head_cap=1,block_cap=2)
            self.assertEqual(r["block_read_failures"],1)
            self.assertEqual(r["block_read_successes"],1)
            self.assertEqual(r["attempted_missing_heights"],[101])
            self.assertEqual(len(calls),5)

    def test_wrong_chain_blocks_initial_head_send(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            wrong={"method":"eth_chainId","params":[],"result":"0x1"}
            r,calls=self.run_frames(root,[wrong],total=4)
            self.assertEqual(r["stop_state"],"CHAIN_ID_NOT_BSC")
            self.assertEqual(len(calls),1)
            self.assertEqual(r["total_attempts"],1)
            self.assertEqual(r["head_samples"],[])

    def test_second_block_bad_parent_stops_without_fabricating_link(self):
        frames=[chain(),head(100),head(102),block(101),
                block(102,parent="0x"+"f"*64)]
        with tempfile.TemporaryDirectory() as d:
            r,calls=self.run_frames(Path(d),frames,total=5,head_cap=1,block_cap=2)
            self.assertEqual(r["stop_state"],"CONSECUTIVE_BLOCK_PARENT_MISMATCH")
            self.assertEqual(r["block_read_successes"],1)
            self.assertEqual(r["block_read_failures"],1)
            self.assertEqual(r["verified_internal_parent_links"],0)
            self.assertEqual(r["attempted_missing_heights"],[102])
            self.assertEqual(len(calls),5)

    def test_interrupted_sender_preserves_unknown_without_completed_report(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            with self.assertRaises(KeyboardInterrupt):
                self.run_frames(root,[chain()],interrupt_at=1)
            journal=json.loads((root/"journal.json").read_text())
            self.assertEqual(journal["attempted_calls"],1)
            self.assertEqual(journal["attempts"][0]["state"],
                             "ATTEMPTED_OUTCOME_UNKNOWN")
            self.assertFalse((root/"report.json").exists())

    def test_mutated_registry_rejected_before_any_source_and_journal(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            with self.assertRaises(ValueError):
                self.run_frames(root,[],routers=ROUTERS+b"\n")
            self.assertFalse((root/"journal.json").exists())
            self.assertFalse((root/"raw_responses").exists())

if __name__=="__main__":
    unittest.main()
