"""Offline PR228 ANCHOR RID/RAW recovery acceptance and tamper cases."""
from hashlib import sha256
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from f0_l2_d1_coordinator import FakeSource, run_fake_concurrent
from f0_l2_d1_recovery import reconcile_saved_attempts


class D1AnchorRecoveryTests(unittest.TestCase):
    def sample(self, *, source=None, total=8, blocks=3, refreshes=2, anchor=True):
        holder = tempfile.TemporaryDirectory()
        self.addCleanup(holder.cleanup)
        root = Path(holder.name).resolve() / "private"
        root.mkdir(mode=0o700)
        if source is None:
            source = FakeSource(first_head=1000, growth_bps=10.0,
                                delay_ms=5)
        with patch("http.client.HTTPSConnection",
                   side_effect=AssertionError("REAL_NETWORK_FORBIDDEN")) as ctor:
            report = run_fake_concurrent(
                source, root, max_total=total,
                max_blocks=blocks, max_refreshes=refreshes,
                head_min_poll_age_ms=250, spacing_ms=250, window_ms=8000,
                anchor_initial_head=anchor)
            ctor.assert_not_called()
        return root, report

    def events(self, root):
        return [json.loads(line) for line in
                (root/"attempts.jsonl").read_text().splitlines()]

    def save(self, root, rows):
        (root/"attempts.jsonl").write_text(
            "".join(json.dumps(e, sort_keys=True)+"\n" for e in rows))

    def rewrite_block_raw(self, root, rows, category, change):
        entry = next(e for e in rows if e["event"]=="SETTLE"
                     and e["category"]==category
                     and e["state"]=="RPC_RESPONSE")
        path=root/"raw_responses"/entry["raw_name"]
        data=json.loads(path.read_bytes())
        change(data)
        payload=json.dumps(data,sort_keys=True,separators=(",",":")).encode()
        path.write_bytes(payload)
        entry["raw_sha256"]=sha256(payload).hexdigest()
        self.save(root,rows)

    def test_complete_anchor_rid_raw_audited_and_continuous(self):
        root, report = self.sample()
        recovery = reconcile_saved_attempts(root)
        self.assertEqual(recovery["audit_status"],"OFFLINE_ACCOUNTED_NOT_LIVE")
        self.assertEqual(recovery["initial_anchor_attempts"],1)
        self.assertTrue(recovery["initial_anchor_raw_verified"])
        self.assertEqual(recovery["initial_anchor_height"],
                         report["initial_anchor_height"])
        self.assertEqual(recovery["verified_initial_parent_links"],1)
        self.assertEqual(recovery["verified_internal_parent_links"],
                         recovery["contiguous_commits"]-1)
        self.assertEqual(recovery["contiguous_commits"],3)
        self.assertTrue(recovery["first_parent_same_source_anchored"])
        self.assertFalse(recovery["first_parent_independently_anchored"])
        self.assertEqual(recovery["reserved"],report["reserved"])
        self.assertEqual(recovery["settled"],report["settled"])
        self.assertEqual(recovery["parsed_full_block_responses"],3)
        self.assertEqual(len(recovery["raw_frames_sha256"]),report["reserved"])
        self.assertEqual(recovery["network_retries"],0)
        self.assertFalse(recovery["automatic_recovery_permitted"])

    def test_three_attempt_anchor_only_is_accounted_but_not_performance_pass(self):
        root, r = self.sample(total=3,blocks=1,refreshes=0)
        rec=reconcile_saved_attempts(root)
        self.assertEqual(rec["reserved"],3)
        self.assertEqual(rec["settled"],3)
        self.assertEqual(rec["initial_anchor_attempts"],1)
        self.assertTrue(rec["initial_anchor_raw_verified"])
        self.assertEqual(rec["contiguous_commits"],0)
        self.assertFalse(rec["first_parent_same_source_anchored"])
        self.assertEqual(rec["audit_status"],"INVALID_FOR_PERFORMANCE_CLAIM")

    def test_failed_anchor_is_audited_as_failure_no_false_commit(self):
        root, r=self.sample(source=FakeSource(
            first_head=1000,growth_bps=10.0,delay_ms=5,fail_block_ordinal=1))
        rec=reconcile_saved_attempts(root)
        self.assertEqual(r["stop"],"INITIAL_ANCHOR_FAILED")
        self.assertEqual(rec["initial_anchor_attempts"],1)
        self.assertFalse(rec["initial_anchor_raw_verified"])
        self.assertEqual(rec["verified_initial_parent_links"],0)
        self.assertEqual(rec["contiguous_commits"],0)
        self.assertEqual(rec["audit_status"],"INVALID_FOR_PERFORMANCE_CLAIM")
        self.assertEqual(rec["unknown_request_ids"],[])

    def test_bad_initial_future_parent_recovered_as_integrity_failure(self):
        root, r=self.sample(source=FakeSource(
            first_head=1000,growth_bps=10,delay_ms=5,bad_parent_ordinal=2))
        rec=reconcile_saved_attempts(root)
        self.assertEqual(r["stop"],"CHAIN_FAULT")
        self.assertEqual(rec["invalid_parent_heights"],[1001])
        self.assertEqual(rec["contiguous_commits"],0)
        self.assertEqual(rec["verified_initial_parent_links"],0)
        self.assertEqual(rec["audit_status"],"INVALID_FOR_PERFORMANCE_CLAIM")

    def test_rewritten_anchor_raw_and_matching_sha_cannot_forge_parent(self):
        root, r=self.sample()
        rows=self.events(root)
        self.rewrite_block_raw(
            root,rows,"ANCHOR",
            lambda rpc:rpc["result"].update(hash="0x"+"a"*64))
        with self.assertRaisesRegex(ValueError,
                                    "D1_RECOVERY_ANCHORED_PARENT_MISMATCH"):
            reconcile_saved_attempts(root)

    def test_rewritten_first_child_parent_and_matching_sha_is_denied(self):
        root, r=self.sample()
        rows=self.events(root)
        self.rewrite_block_raw(
            root,rows,"BLOCK",
            lambda rpc:rpc["result"].update(parentHash="0x"+"a"*64))
        with self.assertRaisesRegex(ValueError,
                                    "D1_RECOVERY_ANCHORED_PARENT_MISMATCH"):
            reconcile_saved_attempts(root)

    def test_anchor_id_mismatch_and_wrong_height_are_rejected_even_rehashed(self):
        for mode in ("id","height"):
            with self.subTest(mode=mode):
                root,_=self.sample()
                rows=self.events(root)
                if mode=="id":
                    mutate=lambda rpc:rpc.update(id=901)
                else:
                    mutate=lambda rpc:rpc["result"].update(number="0x3ea")
                self.rewrite_block_raw(root,rows,"ANCHOR",mutate)
                with self.assertRaisesRegex(ValueError,
                                            "D1_RECOVERY_ANCHORED_RAW_INVALID"):
                    reconcile_saved_attempts(root)

    def test_second_anchor_and_missing_anchor_reservation_rejected(self):
        root,_=self.sample()
        events=self.events(root)
        anchor=next(e for e in events
                    if e["event"]=="RESERVE_UNKNOWN"
                    and e["category"]=="ANCHOR")
        another=dict(anchor,id=events[-1]["id"]+100)
        self.save(root,events+[another])
        with self.assertRaisesRegex(ValueError,
                                    "D1_RECOVERY_NONMONOTONIC_ID"):
            reconcile_saved_attempts(root)
        # A duplicated reservation with legal consecutive RID but no
        # previously issued REQUEST must also be invalid.
        another["id"]=max(e.get("id",0) for e in events)+1
        self.save(root,events+[another])
        with self.assertRaisesRegex(ValueError,
                                    "D1_RECOVERY_ANCHOR_RESERVATION_INVALID"):
            reconcile_saved_attempts(root)

    def test_missing_anchor_settle_cannot_promote_first_commit(self):
        root,_=self.sample()
        rows=self.events(root)
        self.save(root,[e for e in rows if not (
            e["event"]=="SETTLE" and e["category"]=="ANCHOR")])
        with self.assertRaisesRegex(ValueError,
                                    "D1_RECOVERY_UNVERIFIED_ANCHOR_COMMIT"):
            reconcile_saved_attempts(root)

    def test_truncated_first_child_commit_is_not_a_clean_pass(self):
        root,_=self.sample()
        rows=self.events(root)
        self.save(root,[e for e in rows if not (
            e["event"]=="COMMIT_CONTIGUOUS" and
            e["height"]==1003)])
        rec=reconcile_saved_attempts(root)
        self.assertEqual(rec["audit_status"],"INVALID_FOR_PERFORMANCE_CLAIM")
        self.assertEqual(rec["contiguous_commits"],2)

    def test_legacy_unanchored_journal_keeps_existing_semantics(self):
        root,report=self.sample(total=7,anchor=False)
        rec=reconcile_saved_attempts(root)
        self.assertEqual(rec["initial_anchor_attempts"],0)
        self.assertFalse(rec["first_parent_same_source_anchored"])
        self.assertFalse(rec["initial_anchor_raw_verified"])
        self.assertFalse(rec["first_parent_independently_anchored"])
        self.assertEqual(rec["audit_status"],"OFFLINE_ACCOUNTED_NOT_LIVE")


if __name__=="__main__":
    unittest.main()
