"""Offline three-slot HTTP-envelope replay regression tests."""
import ast
import json
import sys
import tempfile
from pathlib import Path
import unittest

F0=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(F0))
from f0_l1_three_slot_offline import simulate
from f0_l1_three_slot_response_replay import fake_frames, replay


def timings():
    return {"eth_chainId":[350.0],
            "eth_blockNumber":[425.0, 430.0, 420.0],
            "eth_getBlockByNumber":[770.0, 850.0, 750.0]}


class ThreeSlotFrameReplayTests(unittest.TestCase):
    def scenario(self, **kw):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/"private"
            root.mkdir(mode=0o700)
            return simulate(timings(),root/"events.jsonl",
                            head_policy="availability_wait",
                            min_head_refresh_age_ms=1500, **kw)

    def block_ids(self, sim):
        return [(e["id"],e["height"]) for e in sim["trace"]
                if e["event"]=="RESERVE_UNKNOWN" and e["category"]=="BLOCK"]

    def test_valid_frames_match_contiguous_commit_and_budgets(self):
        sim=self.scenario()
        row=replay(sim,fake_frames(sim))
        self.assertTrue(row["overall_valid"],row["integrity_faults"])
        self.assertEqual(row["total_attempts"],sim["requested_total"])
        self.assertEqual(row["contiguous_committed_blocks"],
                         sim["blocks_committed_contiguous"])
        self.assertEqual(row["received_parsed_blocks"],sim["block_responses_received"])
        self.assertLessEqual(row["max_inflight_including_head"],3)
        self.assertFalse(row["live_sender_present"])
        self.assertEqual(row["actual_new_rpc_requests"],0)

    def test_bad_rpc_id_causes_missing_and_no_overclaimed_contiguity(self):
        sim=self.scenario()
        frames=fake_frames(sim)
        rid,h=self.block_ids(sim)[0]
        obj=json.loads(frames[rid][2])
        obj["id"] += 99
        frames[rid]=(200,frames[rid][1],json.dumps(obj).encode())
        row=replay(sim,frames)
        self.assertFalse(row["overall_valid"])
        self.assertIn(h,row["failed_attempted_heights"])
        self.assertEqual(row["contiguous_committed_blocks"],0)

    def test_block_height_mismatch_is_not_success(self):
        sim=self.scenario()
        frames=fake_frames(sim)
        rid,h=self.block_ids(sim)[0]
        obj=json.loads(frames[rid][2])
        obj["result"]["number"]="0xffff"
        frames[rid]=(200,frames[rid][1],json.dumps(obj).encode())
        row=replay(sim,frames)
        self.assertFalse(row["overall_valid"])
        self.assertIn("REPLAY_BLOCK_HEIGHT_MISMATCH",
                      [x["reason"] for x in row["integrity_faults"]])

    def test_wrong_parent_blocks_next_commit(self):
        sim=self.scenario()
        frames=fake_frames(sim)
        rid,h=self.block_ids(sim)[1]
        obj=json.loads(frames[rid][2])
        obj["result"]["parentHash"]="0x"+"ab"*32
        frames[rid]=(200,frames[rid][1],json.dumps(obj).encode())
        row=replay(sim,frames)
        self.assertFalse(row["overall_valid"])
        self.assertEqual(row["contiguous_committed_blocks"],1)
        self.assertIn("REPLAY_PARENT_MISMATCH",
                      [x["reason"] for x in row["integrity_faults"]])

    def test_missing_frame_and_http_failure_not_committed(self):
        sim=self.scenario()
        frames=fake_frames(sim)
        (a,ha),(b,hb)=self.block_ids(sim)[:2]
        del frames[a]
        status,headers,body=frames[b]
        frames[b]=(503,headers,body)
        row=replay(sim,frames)
        self.assertFalse(row["overall_valid"])
        self.assertEqual(row["contiguous_committed_blocks"],0)
        self.assertEqual(row["failed_attempted_heights"],[ha,hb])

    def test_duplicate_settlement_no_new_attempts(self):
        sim=self.scenario(duplicate_heights={1002})
        row=replay(sim,fake_frames(sim))
        self.assertTrue(row["overall_valid"])
        self.assertEqual(row["total_attempts"],sim["requested_total"])

    def test_head_mismatch_is_not_silent_success(self):
        sim=self.scenario()
        frames=fake_frames(sim)
        rid=next(e["id"] for e in sim["trace"] if e["event"]=="RESERVE_UNKNOWN"
                 and e["category"]=="INITIAL_HEAD")
        frames[rid]=(200,frames[rid][1],
                     json.dumps({"jsonrpc":"2.0","id":rid,"result":"0xf4240"}).encode())
        with self.assertRaisesRegex(ValueError,"REPLAY_DISPATCH_WITHOUT_FRESH_HEAD"):
            replay(sim,frames)

    def test_no_network_import_in_module(self):
        tree=ast.parse((F0/"f0_l1_three_slot_response_replay.py").read_text())
        roots=set()
        for node in ast.walk(tree):
            if isinstance(node,ast.Import):
                roots.update(x.name.split(".")[0] for x in node.names)
            elif isinstance(node,ast.ImportFrom) and node.module:
                roots.add(node.module.split(".")[0])
        self.assertFalse(roots.intersection({
            "socket","requests","urllib","http","ssl",
            "aiohttp","websocket","subprocess","asyncio","threading"}))


if __name__=="__main__":
    unittest.main()
