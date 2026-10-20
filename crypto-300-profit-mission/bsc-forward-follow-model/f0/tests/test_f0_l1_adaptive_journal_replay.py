"""Full fake-only adaptive scheduler+durable-Journal integration tests."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from f0_l1_adaptive_journal_replay import replay_fake_head_and_blocks

COHORT = (ROOT / "F0_COHORT_PRESELECTION.json").read_bytes()
ROUTERS = (ROOT / "F0_ROUTER_SOURCE_CANDIDATES.json").read_bytes()


def chain():
    return {"method": "eth_chainId", "params": [], "result": "0x38"}


def head(n):
    return {"method": "eth_blockNumber", "params": [], "result": hex(n)}


def block(n):
    return {
        "method": "eth_getBlockByNumber", "params": [hex(n), True],
        "result": {
            "number": hex(n), "hash": "0x" + format(n, "064x"),
            "parentHash": "0x" + format(n - 1, "064x"),
            "transactions": [],
        },
    }


class AdaptiveJournalFakeTests(unittest.TestCase):
    def replay(self, directory, frames, *, total=12, head_cap=4,
               block_cap=4, refresh=4, **kwargs):
        return replay_fake_head_and_blocks(
            frames=frames, cohort_raw=COHORT, router_raw=ROUTERS,
            output_root=Path(directory), max_total_attempts=total,
            max_head_polls=head_cap, max_block_reads=block_cap,
            refresh_after_blocks=refresh, **kwargs)

    def test_initial_identity_checkpoint_then_two_blocks_in_one_persisted_budget(self):
        frames=[chain(), head(100), head(102), block(101), block(102)]
        with tempfile.TemporaryDirectory() as temp:
            with patch("f0_l1_live_short.live_https_post",
                       side_effect=AssertionError("REAL_HTTP_FORBIDDEN")):
                r=self.replay(temp,frames,total=5,head_cap=1,block_cap=2)
            self.assertEqual(r["stop_state"],"BLOCK_ATTEMPT_BUDGET_COMPLETE")
            self.assertEqual(r["simulated_attempts_persisted"],5)
            self.assertEqual(r["identity_and_initial_head_attempts"],2)
            self.assertEqual(r["periodic_head_polls_attempted"],1)
            self.assertEqual(r["full_block_attempts"],2)
            self.assertEqual(r["actual_rpc_calls"],0)
            self.assertEqual(r["scheduler"]["block_reads_received"],2)
            self.assertEqual(r["scheduler"]["latest_sampled_head"],102)
            self.assertFalse(r["control_eligible"])
            self.assertEqual(r["private_raw_responses_recorded"],5)
            j=json.loads((Path(temp)/"journal.json").read_text())
            self.assertEqual(j["attempted_calls"],5)
            self.assertEqual([x["index"] for x in j["attempts"]],[1,2,3,4,5])
            self.assertEqual([x["method"] for x in j["attempts"]],
                             ["eth_chainId","eth_blockNumber","eth_blockNumber",
                              "eth_getBlockByNumber","eth_getBlockByNumber"])
            self.assertTrue(all(x["state"]=="RPC_RESPONSE" for x in j["attempts"]))
            self.assertEqual(len(list((Path(temp)/"raw_responses").glob("*.json"))),5)

    def test_stagnant_head_exponential_backoff_then_new_head_and_block(self):
        frames=[chain(),head(100),head(100),head(100),head(101),block(101)]
        with tempfile.TemporaryDirectory() as temp:
            r=self.replay(temp,frames,total=6,head_cap=3,block_cap=1)
            self.assertEqual(r["simulated_attempts_persisted"],6)
            self.assertEqual(r["periodic_head_polls_attempted"],3)
            self.assertEqual(r["full_block_attempts"],1)
            self.assertEqual(r["scheduler"]["head_stagnation_streak"],0)
            snaps=r["head_snapshots"]
            self.assertEqual([s["sampled_head"] for s in snaps],[100,100,100,101])
            self.assertGreaterEqual(snaps[2]["virtual_monotonic_ms"] -
                                    snaps[1]["virtual_monotonic_ms"],1000)
            self.assertGreaterEqual(snaps[3]["virtual_monotonic_ms"] -
                                    snaps[2]["virtual_monotonic_ms"],2000)

    def test_total_budget_includes_identity_and_repeated_head(self):
        frames=[chain(),head(100),head(102),block(101),block(102)]
        with tempfile.TemporaryDirectory() as temp:
            r=self.replay(temp,frames,total=4,head_cap=2,block_cap=2)
            self.assertEqual(r["stop_state"],"TOTAL_ATTEMPT_BUDGET_EXHAUSTED")
            self.assertEqual(r["simulated_attempts_persisted"],4)
            self.assertEqual(r["identity_and_initial_head_attempts"],2)
            self.assertEqual(r["periodic_head_polls_attempted"],1)
            self.assertEqual(r["full_block_attempts"],1)
            self.assertEqual(r["scheduler"]["next_unattempted_height"],102)
            self.assertEqual(r["pending_fixture_frames"],1)

    def test_invalid_chain_stops_before_initial_head_without_extra_send(self):
        frames=[{"method":"eth_chainId","params":[],"result":"0x1"},head(100)]
        with tempfile.TemporaryDirectory() as temp:
            r=self.replay(temp,frames)
            self.assertEqual(r["stop_state"],"FAKE_WRONG_CHAIN")
            self.assertEqual(r["simulated_attempts_persisted"],1)
            self.assertEqual(r["pending_fixture_frames"],1)
            self.assertIsNone(r["scheduler"])

    def test_failed_refresh_head_consumes_attempt_without_retry(self):
        frames=[chain(),head(100),{
            "method":"eth_blockNumber","params":[],
            "error":{"code":-32000,"message":"private-text-in-fake-error"}}]
        with tempfile.TemporaryDirectory() as temp:
            r=self.replay(temp,frames)
            self.assertEqual(r["stop_state"],"HEAD_SOURCE_FAILED_NO_RETRY")
            self.assertEqual(r["periodic_head_polls_attempted"],1)
            self.assertEqual(r["full_block_attempts"],0)
            self.assertEqual(r["scheduler"]["head_polls_attempted_after_initial"],1)
            self.assertNotIn("private-text-in-fake-error",
                             json.dumps(r)+(Path(temp)/"journal.json").read_text())

    def test_missing_exact_block_is_counted_not_retried(self):
        frames=[chain(),head(100),head(102),{
            "method":"eth_getBlockByNumber","params":["0x65",True],
            "result":None},block(102)]
        with tempfile.TemporaryDirectory() as temp:
            r=self.replay(temp,frames,total=5,head_cap=2,block_cap=2)
            self.assertEqual(r["scheduler"]["block_reads_attempted"],2)
            self.assertEqual(r["scheduler"]["block_reads_received"],1)
            self.assertEqual(r["scheduler"]["block_reads_failed"],1)
            self.assertEqual(r["scheduler"]["explicit_missing_heights"],[101])
            self.assertEqual(r["simulated_attempts_persisted"],5)

    def test_regressed_head_stops_with_no_block(self):
        frames=[chain(),head(100),head(99)]
        with tempfile.TemporaryDirectory() as temp:
            r=self.replay(temp,frames)
            self.assertEqual(r["stop_state"],"HEAD_REGRESSED_UNVERIFIED")
            self.assertEqual(r["simulated_attempts_persisted"],3)
            self.assertEqual(r["full_block_attempts"],0)

    def test_source_mutation_rejected_before_journal(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(ValueError):
                replay_fake_head_and_blocks(
                    frames=[chain()],cohort_raw=COHORT+b"\n",router_raw=ROUTERS,
                    output_root=Path(temp),max_total_attempts=3,
                    max_head_polls=1,max_block_reads=1)
            self.assertFalse((Path(temp)/"journal.json").exists())

    def test_stale_head_source_wait_cap_does_not_burn_remaining_requests(self):
        frames=[chain(),head(100),head(100),head(100),head(100)]
        with tempfile.TemporaryDirectory() as temp:
            r=self.replay(temp,frames,total=8,head_cap=8,block_cap=1,
                          max_simulated_duration_ms=2000)
            self.assertEqual(r["stop_state"],"VIRTUAL_TIME_CAP_REACHED")
            self.assertLess(r["periodic_head_polls_attempted"],4)
            self.assertLess(r["simulated_attempts_persisted"],8)

    def test_no_fixture_replay_on_same_output_directory(self):
        frames=[chain(),head(100),head(101),block(101)]
        with tempfile.TemporaryDirectory() as temp:
            self.replay(temp,frames,total=4,head_cap=1,block_cap=1)
            with self.assertRaisesRegex(ValueError,"FAKE_OUTPUTS_NOT_FRESH"):
                self.replay(temp,frames,total=4,head_cap=1,block_cap=1)


if __name__ == "__main__":
    unittest.main()
