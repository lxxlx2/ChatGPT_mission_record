"""Real thread scheduling, fake source only. Do not invoke network."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

F0=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(F0))
from f0_l2_d1_coordinator import FakeSource,run_fake_concurrent


class D1ConcurrentFakeTests(unittest.TestCase):
    def scenario(self, **kwargs):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/"private"
            root.mkdir(mode=0o700)
            s=kwargs.pop("source",FakeSource(delay_ms=40,growth_bps=10.0))
            rep=run_fake_concurrent(s,root,max_total=10,max_blocks=6,
                                    max_refreshes=2,window_ms=9000,
                                    head_min_poll_age_ms=250,**kwargs)
            log=[json.loads(line) for line in
                 (root/"attempts.jsonl").read_text().splitlines()]
            return rep,log

    def test_global_actual_fake_starts_share_250ms_and_slots_and_budget(self):
        r,rows=self.scenario()
        self.assertEqual(r["network_requests"],0)
        self.assertLessEqual(r["max_shared_slots"],3)
        self.assertLessEqual(r["reserved"],10)
        self.assertLessEqual(r["block_attempts"],6)
        self.assertLessEqual(r["head_refreshes"],2)
        self.assertGreaterEqual(r["min_actual_fake_start_gap_ms"],248.5)
        self.assertEqual(r["settled"],r["reserved"])
        self.assertEqual(r["unknown_after_stop"],0)
        seen=set()
        for x in rows:
            if x["event"]=="RESERVE_UNKNOWN":
                self.assertNotIn(x["id"],seen)
                seen.add(x["id"])
            if x["event"]=="SETTLE":
                self.assertIn(x["id"],seen)
        self.assertEqual(len(seen),r["reserved"])

    def test_http_503_stops_new_dispatch_and_charges_attempt(self):
        bad,_=self.scenario(source=FakeSource(
            growth_bps=10.0,delay_ms=40,fail_block_ordinal=1))
        self.assertIn(bad["stop"],("RPC_OR_HEAD_FAULT","CHAIN_FAULT"))
        self.assertTrue(bad["faults"])
        self.assertEqual(bad["settled"],bad["reserved"])
        self.assertEqual(bad["contiguous_commits"],0)

    def test_initial_head_http_error_does_not_dispatch_blocks(self):
        r,_=self.scenario(source=FakeSource(
            growth_bps=5.0,delay_ms=30,fail_head_after=1))
        self.assertEqual(r["block_attempts"],0)
        self.assertEqual(r["stop"],"RPC_OR_HEAD_FAULT")

    def test_bad_json_denies_parse_without_false_commit(self):
        r,_=self.scenario(source=FakeSource(
            growth_bps=10.0,delay_ms=40,bad_json_ordinal=1))
        self.assertEqual(r["contiguous_commits"],0)
        self.assertEqual(r["stop"],"RPC_OR_HEAD_FAULT")

    def test_journal_exclusive_and_raw_response_precedes_settlement(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/"private"
            root.mkdir(mode=0o700)
            rep=run_fake_concurrent(FakeSource(growth_bps=5.0,delay_ms=20),
                                    root,max_total=7,max_blocks=3,
                                    max_refreshes=2,window_ms=8000,
                                    head_min_poll_age_ms=250)
            self.assertEqual((root/"attempts.jsonl").stat().st_mode & 0o077,0)
            events=[json.loads(x) for x in
                    (root/"attempts.jsonl").read_text().splitlines()]
            first_index={}
            for i,row in enumerate(events):
                if row["event"]=="RESERVE_UNKNOWN":
                    first_index[row["id"]]=i
                elif row["event"]=="SETTLE":
                    self.assertLess(first_index[row["id"]],i)
                    if "raw_name" in row:
                        raw=root/"raw_responses"/row["raw_name"]
                        self.assertTrue(raw.is_file())
                        self.assertEqual(raw.stat().st_mode & 0o077,0)
            with self.assertRaises((OSError,ValueError)):
                run_fake_concurrent(FakeSource(),root,max_total=7,
                                    max_blocks=3,max_refreshes=2,
                                    head_min_poll_age_ms=250)

    def test_out_of_order_parent_fault_owned_by_bad_buffered_response(self):
        # Real workers: first block is slow, second bad-parent block arrives
        # earlier. Unlocking the first block must not become RPC FAILED.
        source=FakeSource(
            growth_bps=10.0, delay_ms=30,
            block_delay_by_ordinal={1:1400,2:30,3:60},
            bad_parent_ordinal=2)
        r,rows=self.scenario(source=source)
        # The bounded window may already hit BLOCK_BUDGET before a very
        # slow earlier block unlocks the buffered bad parent. The fault
        # must still be attributed correctly and never counted as commit.
        self.assertIn(r["stop"],("CHAIN_FAULT","BLOCK_BUDGET","HEAD_BUDGET"))
        broken=[x for x in rows if x["event"]=="CHAIN_INTEGRITY_FAULT"]
        self.assertEqual(len(broken),1)
        self.assertEqual(broken[0]["reason"],"D1_CHAIN_PARENT_MISMATCH")
        block_res=[x for x in rows if x["event"]=="RESERVE_UNKNOWN"
                   and x["category"]=="BLOCK"]
        self.assertGreaterEqual(len(block_res),3)
        first_id,second_id=block_res[0]["id"],block_res[1]["id"]
        self.assertEqual(broken[0]["id"],second_id)
        self.assertEqual(broken[0]["height"],block_res[1]["height"])
        responses={x["id"]:x for x in rows if x["event"]=="SETTLE"}
        self.assertEqual(responses[first_id]["state"],"RPC_RESPONSE")
        self.assertEqual(responses[second_id]["state"],"RPC_RESPONSE")
        self.assertIn(first_id,[x["id"] for x in rows
                                if x["event"]=="COMMIT_CONTIGUOUS"])
        self.assertNotIn(second_id,[x["id"] for x in rows
                                    if x["event"]=="COMMIT_CONTIGUOUS"])
        self.assertLess(r["contiguous_commits"],r["parsed_full_blocks"])
        self.assertEqual(r["settled"],r["reserved"])

    def test_global_gate_rejects_stale_head_at_actual_fake_send_time(self):
        # Three queued work items may wait for the global rate gate.
        # If HEAD goes stale while queued, no fake sender invocation starts.
        from f0_l2_d1_coordinator import GlobalStartGate
        import time
        gate=GlobalStartGate(250)
        source=FakeSource(delay_ms=0)
        req={"jsonrpc":"2.0","id":1,"method":"eth_getBlockByNumber",
             "params":["0x3ea", True]}
        outcome=gate.run(req,source,
                         block_head_deadline=time.monotonic()-1,
                         dispatch_deadline=time.monotonic()+2,
                         timeout_ms=5000)
        self.assertEqual(outcome["state"],"PRESTART_STALE_HEAD")
        self.assertEqual(len(gate.starts),0)
        self.assertEqual(source.block_count,0)

    def test_presend_fsync_exception_never_invokes_fake_source(self):
        from unittest.mock import patch
        from f0_l2_d1_coordinator import ExclusiveEvidence
        source=FakeSource(delay_ms=0)
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/"private"
            root.mkdir(mode=0o700)
            with patch.object(ExclusiveEvidence,"add",
                              side_effect=OSError("forced fsync failure")):
                with self.assertRaises(OSError):
                    run_fake_concurrent(source,root,max_total=6,max_blocks=2,
                                        max_refreshes=2,
                                        head_min_poll_age_ms=250)
        self.assertEqual(source.head_count,0)
        self.assertEqual(source.block_count,0)

    def test_late_fake_frame_is_archived_but_not_accepted(self):
        source=FakeSource(growth_bps=10.0,delay_ms=15,
                          block_delay_by_ordinal={1:450})
        r,rows=self.scenario(source=source,max_block_response_ms=250)
        self.assertEqual(r["stop"],"RPC_OR_HEAD_FAULT")
        failed=[e for e in rows if e["event"]=="SETTLE"
                and e.get("reason")=="FAKE_TIMEOUT_LATE_RESPONSE"]
        self.assertTrue(failed)
        self.assertTrue(all("raw_name" in e for e in failed))
        self.assertEqual(r["settled"],r["reserved"])
        self.assertLess(r["contiguous_commits"],r["block_attempts"])

    def test_no_arbitrary_real_sender_or_live_authorization(self):
        class AttemptedCallback:
            pass
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/"private"
            root.mkdir(mode=0o700)
            with self.assertRaisesRegex(ValueError,"D1_SCOPE_INVALID"):
                run_fake_concurrent(AttemptedCallback(),root,
                                    head_min_poll_age_ms=250)

if __name__=="__main__":
    unittest.main()
