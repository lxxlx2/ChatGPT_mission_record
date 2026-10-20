"""Strictly offline injected sender tests for bounded L1 capture and journal."""
import copy
import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from f0_l1_injected_capture import capture_injected_blocks
MANIFEST = (ROOT / "F0_COHORT_PRESELECTION.json").read_bytes()
ROUTERS = (ROOT / "F0_ROUTER_SOURCE_CANDIDATES.json").read_bytes()
FIX = json.loads((ROOT / "fixtures/l1_contiguous_replay.json").read_text())
FAKE = json.loads((ROOT / "fixtures/l1_fake_cohort.json").read_text())
COHORT = json.loads(MANIFEST)
PRIMARY = [w["wallet"] for w in COHORT["preliminary_wallets"] if w["role"] == "PRIMARY"]
FIRST_ROUTER = json.loads(ROUTERS)["routers"][0]["address"]


class Clock:
    def __init__(self):
        self.step = 0
        self.start = datetime(2026, 10, 20, tzinfo=timezone.utc)

    def utc(self):
        self.step += 1
        return (self.start + timedelta(milliseconds=20*self.step)).isoformat(
            timespec="milliseconds").replace("+00:00", "Z")

    def mono(self):
        self.step += 1
        return self.step*20


def fake_full_blocks():
    data = {}
    old_a = FAKE["preliminary_wallets"][0]["wallet"]
    old_b = FAKE["preliminary_wallets"][15]["wallet"]
    old_router = FIX["synthetic_routers"][0]
    for row in FIX["block_attempts"]:
        if row["result"] != "RECEIVED":
            continue
        block = copy.deepcopy(row["rpc"])
        for tx in block["result"]["transactions"]:
            if tx["from"].lower() == old_a.lower():
                tx["from"] = PRIMARY[0]
            if tx["from"].lower() == old_b.lower():
                tx["from"] = PRIMARY[10]
            if tx["to"] == old_router:
                tx["to"] = FIRST_ROUTER
        data[row["height"]] = block
    return data


class InjectedBoundedCaptureTests(unittest.TestCase):
    def capture(self, root, sender, max_calls=5, fail_streak_limit=3, **kwargs):
        clock = Clock()
        return capture_injected_blocks(
            sender, MANIFEST, ROUTERS,
            start_height=100, end_height=104, max_calls=max_calls,
            journal_path=root/"journal.json", report_path=root/"report.json",
            clock_utc=clock.utc, clock_monotonic_ms=clock.mono,
            fail_streak_limit=fail_streak_limit, **kwargs)

    def test_saved_full_blocks_share_frozen_watch_and_router_candidate_stream(self):
        blocks = fake_full_blocks()
        presend = []
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            def sender(payload):
                journal = json.loads((root/"journal.json").read_text())
                presend.append(journal["attempts"][-1]["state"])
                height = int(payload["params"][0], 16)
                if height in blocks:
                    block = copy.deepcopy(blocks[height])
                    block["id"] = payload["id"]
                    return block
                raise TimeoutError("fake endpoint timed out - never goes on chain")
            report = self.capture(root, sender)
            ledger = json.loads((root/"journal.json").read_text())
            self.assertEqual(presend, ["ATTEMPTED_OUTCOME_UNKNOWN"]*5)
            self.assertEqual(len(ledger["attempts"]), 5)
            self.assertEqual([x["index"] for x in ledger["attempts"]], [1,2,3,4,5])
            self.assertEqual(report["metrics"]["blocks_received"],3)
            self.assertEqual(report["metrics"]["blocks_failed"],2)
            self.assertEqual(report["metrics"]["watch_signer_tx_in_received_blocks"],3)
            self.assertEqual(report["metrics"]["router_control_candidates_in_received_blocks"],3)
            self.assertTrue(all(not x["control_eligible"] for x in report["candidate_rows"]))
            self.assertEqual(report["capture_stop_state"],"INJECTED_WINDOW_COMPLETED")
            self.assertEqual(report["actual_rpc_calls"],0)
            self.assertEqual(report["first_seen_source"],"INJECTED_CLOCK_NOT_REAL")
            self.assertEqual(report["cohort"]["primary_count"],20)
            self.assertEqual(len([x for x in ledger["attempts"] if x["state"]=="FAILED"]),2)

    def test_budget_truncation_has_unattempted_height_denominator(self):
        blocks = fake_full_blocks()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            def sender(payload):
                h = int(payload["params"][0], 16)
                if h not in blocks:
                    raise TimeoutError()
                value = copy.deepcopy(blocks[h])
                value["id"] = payload["id"]
                return value
            report = self.capture(root, sender, max_calls=3)
            self.assertEqual(report["attempted_calls"],3)
            self.assertEqual(report["nonattempted_heights"],2)
            self.assertEqual(report["capture_stop_state"],"INJECTED_BUDGET_EXHAUSTED")
            self.assertEqual(report["metrics"]["missing_heights"],[101,102,103,104])
            self.assertEqual(len(json.loads((root/"journal.json").read_text())["attempts"]),3)

    def test_wrong_rpc_id_is_failed_saved_attempt_not_free(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            def sender(payload):
                return {"jsonrpc":"2.0", "id":payload["id"]+1,
                        "result":{"message":"fake-private-token"}}
            report = self.capture(root, sender, fail_streak_limit=2)
            ledger = json.loads((root/"journal.json").read_text())
            self.assertEqual(report["attempted_calls"],2)
            self.assertEqual(report["failed_attempts"],2)
            self.assertEqual(report["capture_stop_state"],
                             "INJECTED_CONSECUTIVE_SOURCE_FAILURES")
            self.assertTrue(all(x["failure_code"]=="INVALID_RPC_IDENTITY"
                                for x in ledger["attempts"]))
            self.assertNotIn("fake-private-token",json.dumps(report)+json.dumps(ledger))

    def test_interrupt_preserves_presend_outcome_unknown_without_retry(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            def sender(payload):
                journal = json.loads((root/"journal.json").read_text())
                self.assertEqual(journal["attempts"][0]["state"],
                                 "ATTEMPTED_OUTCOME_UNKNOWN")
                raise KeyboardInterrupt()
            with self.assertRaises(KeyboardInterrupt):
                self.capture(root,sender)
            ledger = json.loads((root/"journal.json").read_text())
            self.assertEqual(ledger["attempted_calls"],1)
            self.assertEqual(ledger["attempts"][0]["state"],"ATTEMPTED_OUTCOME_UNKNOWN")
            self.assertFalse((root/"report.json").exists())

    def test_path_collision_rejected_before_any_sender_calls(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            calls = []
            clock = Clock()
            with self.assertRaisesRegex(ValueError,"JOURNAL_REPORT_PATH_OR_EXISTENCE_CONFLICT"):
                capture_injected_blocks(
                    lambda request:calls.append(request),MANIFEST,ROUTERS,
                    start_height=100,end_height=104,max_calls=5,
                    journal_path=root/"journal.json",report_path=root/"journal.json",
                    clock_utc=clock.utc,clock_monotonic_ms=clock.mono)
            self.assertEqual(calls,[])
            self.assertFalse((root/"journal.json").exists())

    def test_mutated_router_registry_rejected_before_sender_and_journal(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            calls = []
            clock = Clock()
            with self.assertRaisesRegex(ValueError,"FROZEN_ROUTER_REGISTRY_REQUIRED"):
                capture_injected_blocks(
                    lambda request:calls.append(request),MANIFEST,
                    ROUTERS.replace(b"v3_universal",b"xx_universal",1),
                    start_height=100,end_height=104,max_calls=5,
                    journal_path=root/"journal.json",report_path=root/"report.json",
                    clock_utc=clock.utc,clock_monotonic_ms=clock.mono)
            self.assertEqual(calls,[])
            self.assertFalse((root/"journal.json").exists())


if __name__ == "__main__":
    unittest.main()
