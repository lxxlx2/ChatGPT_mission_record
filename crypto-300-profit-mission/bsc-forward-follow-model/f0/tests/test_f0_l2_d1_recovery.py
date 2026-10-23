"""Journal crash/replay/identity checks. No network or live grant."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from f0_l2_d1_recovery import reconcile_saved_attempts

class D1RecoveryTests(unittest.TestCase):
    def fixture(self, pending=False):
        tmp=tempfile.TemporaryDirectory()
        root=Path(tmp.name)/"private"
        root.mkdir(mode=0o700)
        raw=root/"raw_responses"
        raw.mkdir(mode=0o700)
        body=b'{"jsonrpc":"2.0","id":1,"result":{}}'
        (raw/"001.body").write_bytes(body)
        (raw/"001.body").chmod(0o600)
        reserve={"event":"RESERVE_UNKNOWN","id":1,"category":"BLOCK",
                 "method":"eth_getBlockByNumber","height":1004}
        settle={"event":"SETTLE","id":1,"category":"BLOCK","height":1004,
                "state":"RPC_RESPONSE","raw_name":"001.body",
                "raw_sha256":hashlib.sha256(body).hexdigest()}
        commit={"event":"COMMIT_CONTIGUOUS","id":1,"height":1004}
        events=[reserve,settle,commit]
        if pending:
            events.append({"event":"RESERVE_UNKNOWN","id":2,"category":"BLOCK",
                           "method":"eth_getBlockByNumber","height":1005})
        self.save(root,events)
        return tmp,root,events

    def save(self,root,events):
        path=root/"attempts.jsonl"
        path.write_text("".join(json.dumps(x)+"\n" for x in events))
        path.chmod(0o600)

    def test_full_offline_ledger_audited_no_live_claim(self):
        holder,root,_=self.fixture()
        with holder:
            r=reconcile_saved_attempts(root)
            self.assertEqual(r["reserved"],1)
            self.assertEqual(r["settled"],1)
            self.assertEqual(r["contiguous_commits"],1)
            self.assertEqual(r["audit_status"],"OFFLINE_ACCOUNTED_NOT_LIVE")
            self.assertFalse(r["automatic_recovery_permitted"])

    def test_crash_preserves_unknown_and_never_auto_retries(self):
        holder,root,_=self.fixture(pending=True)
        with holder:
            r=reconcile_saved_attempts(root)
            self.assertEqual(r["unknown_request_ids"],[2])
            self.assertEqual(r["network_retries"],0)
            self.assertEqual(r["audit_status"],"INVALID_FOR_PERFORMANCE_CLAIM")

    def test_duplicate_settle_and_orphan_settle_rejected(self):
        holder,root,events=self.fixture()
        with holder:
            self.save(root,events+[events[1]])
            with self.assertRaisesRegex(ValueError,"DUPLICATE_OR_ORPHAN"):
                reconcile_saved_attempts(root)
            self.save(root,events+[dict(events[1],id=99)])
            with self.assertRaisesRegex(ValueError,"DUPLICATE_OR_ORPHAN"):
                reconcile_saved_attempts(root)

    def test_parent_fault_owner_and_no_cross_gap(self):
        holder,root,events=self.fixture(pending=True)
        with holder:
            # Simulate second valid RPC response, but invalid parent.
            raw=root/"raw_responses"/"002.body"
            body=b'{"jsonrpc":"2.0","id":2,"result":{}}'
            raw.write_bytes(body)
            raw.chmod(0o600)
            settle2={"event":"SETTLE","id":2,"category":"BLOCK",
                     "height":1005,"state":"RPC_RESPONSE",
                     "raw_name":"002.body",
                     "raw_sha256":hashlib.sha256(body).hexdigest()}
            fault={"event":"CHAIN_INTEGRITY_FAULT","id":2,"height":1005}
            self.save(root,events+[settle2,fault])
            r=reconcile_saved_attempts(root)
            self.assertEqual(r["invalid_parent_heights"],[1005])
            self.assertEqual(r["unknown_request_ids"],[])
            self.assertEqual(r["contiguous_commits"],1)
            self.save(root,events+[settle2,fault,fault])
            with self.assertRaisesRegex(ValueError,"WRONG_FAULT_OWNER_OR_DUPLICATE"):
                reconcile_saved_attempts(root)
            self.save(root,events+[settle2,dict(fault,id=1)])
            with self.assertRaisesRegex(ValueError,"WRONG_FAULT_OWNER_OR_DUPLICATE"):
                reconcile_saved_attempts(root)
            self.save(root,events+[settle2,fault,
                                  {"event":"COMMIT_CONTIGUOUS",
                                   "id":2,"height":1005}])
            with self.assertRaisesRegex(ValueError,"COMMIT_ACROSS_BAD_PARENT"):
                reconcile_saved_attempts(root)

    def test_raw_mutation_and_truncated_jsonl_rejected(self):
        holder,root,events=self.fixture()
        with holder:
            (root/"raw_responses"/"001.body").write_bytes(b"tampered")
            with self.assertRaisesRegex(ValueError,"RAW_HASH_MISMATCH"):
                reconcile_saved_attempts(root)
            self.save(root,events)
            (root/"attempts.jsonl").write_bytes(b'{"event":"RESERVE_UNKNOWN"')
            with self.assertRaisesRegex(ValueError,"TRUNCATED_LOG"):
                reconcile_saved_attempts(root)

    def test_failed_rpc_settlement_is_not_valid_performance_sample(self):
        holder,root,events=self.fixture()
        with holder:
            bad=[events[0],dict(events[1],state="FAILED")]
            self.save(root,bad)
            result=reconcile_saved_attempts(root)
            self.assertEqual(result["unknown_request_ids"],[])
            self.assertEqual(result["failed_request_ids"],[1])
            self.assertEqual(result["audit_status"],
                             "INVALID_FOR_PERFORMANCE_CLAIM")
            self.assertEqual(result["network_retries"],0)


    def test_real_fake_coordinator_first_commit_deletion_is_denied(self):
        """P1: mutate a genuine coordinator journal, not a hand-built success."""
        from f0_l2_d1_coordinator import FakeSource,run_fake_concurrent
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/"private"
            root.mkdir(mode=0o700)
            fake=FakeSource(delay_ms=25,growth_bps=10.0)
            original=run_fake_concurrent(
                fake,root,max_total=11,max_blocks=3,max_refreshes=6,
                window_ms=10000,head_min_poll_age_ms=250)
            self.assertGreaterEqual(original["contiguous_commits"],2)
            events=[json.loads(line) for line in
                    (root/"attempts.jsonl").read_text().splitlines()]
            block_reservations=[x for x in events
                                if x["event"]=="RESERVE_UNKNOWN"
                                and x["category"]=="BLOCK"]
            commits=[x for x in events if x["event"]=="COMMIT_CONTIGUOUS"]
            self.assertEqual(commits[0]["height"],
                             block_reservations[0]["height"])
            self.assertEqual(commits[1]["height"],commits[0]["height"]+1)
            valid=reconcile_saved_attempts(root)
            self.assertEqual(valid["expected_first_block_height"],
                             commits[0]["height"])
            self.assertEqual(valid["audit_status"],"OFFLINE_ACCOUNTED_NOT_LIVE")
            # Keep every RESERVE, SETTLE and exact raw response byte/hash.
            mutated=[x for x in events if x is not commits[0]]
            self.save(root,mutated)
            with self.assertRaisesRegex(ValueError,
                                        "D1_RECOVERY_FIRST_COMMIT_START_GAP"):
                reconcile_saved_attempts(root)
            # Removing ALL COMMIT records must not be a clean 0-block audit.
            self.save(root,[x for x in events
                            if x["event"]!="COMMIT_CONTIGUOUS"])
            empty=reconcile_saved_attempts(root)
            self.assertEqual(empty["audit_status"],
                             "INVALID_FOR_PERFORMANCE_CLAIM")
            self.assertTrue(empty["first_commit_missing"])
            self.assertEqual(empty["expected_first_block_height"],
                             commits[0]["height"])

    def test_initial_head_and_block_reservation_must_share_start(self):
        holder,root,events=self.fixture()
        with holder:
            body=b'{"jsonrpc":"2.0","id":1,"result":"0x3ea"}'
            raw=root/"raw_responses"/"001.body"
            raw.write_bytes(body)
            initial={"event":"RESERVE_UNKNOWN","id":1,
                     "category":"INITIAL_HEAD","method":"eth_blockNumber",
                     "height":None}
            headsettle={"event":"SETTLE","id":1,"category":"INITIAL_HEAD",
                        "height":None,"state":"RPC_RESPONSE",
                        "raw_name":"001.body",
                        "raw_sha256":hashlib.sha256(body).hexdigest()}
            reserve=dict(events[0],id=2,height=1004)
            payload=b'{"jsonrpc":"2.0","id":2,"result":{}}'
            raw2=root/"raw_responses"/"002.body"
            raw2.write_bytes(payload)
            raw2.chmod(0o600)
            settlement=dict(events[1],id=2,height=1004,
                            raw_name="002.body",
                            raw_sha256=hashlib.sha256(payload).hexdigest())
            commit=dict(events[2],id=2,height=1004)
            # 0x3ea=1002, therefore expected first block is 1003, not 1004.
            self.save(root,[initial,headsettle,reserve,settlement,commit])
            with self.assertRaisesRegex(ValueError,
                                        "D1_RECOVERY_INITIAL_HEAD_START_MISMATCH"):
                reconcile_saved_attempts(root)

    def test_missing_raw_and_dirty_mode_denied(self):
        holder,root,events=self.fixture()
        with holder:
            (root/"raw_responses"/"001.body").unlink()
            with self.assertRaisesRegex(ValueError,"RAW_NOT_PRIVATE"):
                reconcile_saved_attempts(root)
            (root/"attempts.jsonl").chmod(0o644)
            with self.assertRaisesRegex(ValueError,"FILES_NOT_PRIVATE"):
                reconcile_saved_attempts(root)

if __name__=="__main__":
    unittest.main()
