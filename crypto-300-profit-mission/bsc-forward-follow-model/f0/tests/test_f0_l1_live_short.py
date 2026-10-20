"""Fake-HTTP-only checks of single-use BSC L1 runner. NEVER contacts chain."""
import copy
from datetime import datetime, timezone, timedelta
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import f0_l1_live_short as live

MANIFEST=(ROOT/"F0_COHORT_PRESELECTION.json").read_bytes()
REGISTRY=(ROOT/"F0_ROUTER_SOURCE_CANDIDATES.json").read_bytes()
SAVED=json.loads((ROOT/"fixtures/l1_contiguous_replay.json").read_text())
BLOCK=next(r["rpc"] for r in SAVED["block_attempts"] if r["height"]==100)


class Clock:
    def __init__(self):
        self.utc_value=datetime(2026,10,20,3,0,tzinfo=timezone.utc)
        self.mono_value=5000.0
    def utc(self):
        return self.utc_value
    def mono(self):
        return self.mono_value
    def sleep(self,seconds):
        self.utc_value+=timedelta(seconds=seconds)
        self.mono_value+=seconds


def permit(root,clock,blocks=1):
    return {"scope":live.SCHEMA,"user_authorized":True,
            "independent_review_required":True,"endpoint":live.ENDPOINT,
            "chain_id":56,"methods":["eth_chainId","eth_blockNumber",
                                       "eth_getBlockByNumber"],
            "free_only":True,"read_only":True,"no_retries":True,
            "no_ws":True,"no_proxy":True,"no_redirects":True,
            "background":False,"max_block_reads":blocks,
            "max_total_attempts":blocks+2,"min_interval_ms":250,
            "future_block_pace_ms":800,"max_response_bytes":2000000,
            "timeout_ms":5000,"fail_streak_limit":3,
            "window_start_utc":live.iso(clock.utc()-timedelta(seconds=1)),
            "window_end_utc":live.iso(clock.utc()+timedelta(minutes=8)),
            "approved_commit_sha":"a"*40,"approved_script_sha256":"b"*64,
            "run_nonce":"c"*64,"storage_root":str(root),
            "archive_raw_public_rpc":True}


class LiveShortOfflineTests(unittest.TestCase):
    def test_permit_only_62_max_and_method_scope(self):
        with tempfile.TemporaryDirectory(prefix="f0fake-",dir="/tmp") as d:
            t=Clock()
            p=permit(Path(d),t,60)
            self.assertEqual(live.validate_permit(p,t.utc())[2],60)
            p["max_block_reads"]=61
            with self.assertRaisesRegex(ValueError,"CAPTURE_REQUEST_CAP_INVALID"):
                live.validate_permit(p,t.utc())
            p=permit(Path(d),t)
            p["methods"].append("eth_getLogs")
            with self.assertRaisesRegex(ValueError,"CAPTURE_AUTHORIZATION_INVALID"):
                live.validate_permit(p,t.utc())

    def test_full_one_future_block_and_unified_presend_journal(self):
        with tempfile.TemporaryDirectory(prefix="f0fake-",dir="/tmp") as d:
            root=Path(d)
            t=Clock()
            presend=[]
            def fake(url,body,timeout,cap):
                request=json.loads(body)
                j=json.loads((root/"journal.json").read_text())
                self.assertEqual(len(j["attempts"]),request["id"])
                self.assertEqual(j["attempts"][-1]["state"],"ATTEMPTED_OUTCOME_UNKNOWN")
                presend.append(request["method"])
                if request["method"]=="eth_chainId":
                    result="0x38"
                elif request["method"]=="eth_blockNumber":
                    result="0x63"
                else:
                    self.assertEqual(request["params"],["0x64",True])
                    result=BLOCK["result"]
                t.sleep(0.015)
                return (200,{"Content-Type":"application/json"},
                        json.dumps({"jsonrpc":"2.0","id":request["id"],
                                    "result":result}).encode())
            p=permit(root,t,1)
            result=live.capture_once(p,MANIFEST,REGISTRY,fake,
                                      clock=t.utc,mono=t.mono,sleep=t.sleep)
            self.assertEqual(result["actual_rpc_calls"],3)
            self.assertEqual(result["attempted_identity"],2)
            self.assertEqual(result["attempted_blocks"],1)
            self.assertEqual(result["observed_head"],99)
            self.assertEqual(result["start_height"],100)
            self.assertEqual(result["stop_state"],"CAPTURE_WINDOW_COMPLETED")
            self.assertEqual(result["first_seen_source"],
                             "LOCAL_HTTP_RESPONSE_RECEIPT_ONLY")
            self.assertEqual(presend,["eth_chainId","eth_blockNumber",
                                     "eth_getBlockByNumber"])
            journal=json.loads((root/"journal.json").read_text())
            self.assertEqual(len(journal["attempts"]),3)
            self.assertTrue(all(x["state"]=="RPC_RESPONSE" for x in journal["attempts"]))
            self.assertEqual(len(list((root/"raw_responses").glob("*.json"))),3)
            self.assertTrue((root/"report.json").exists())
            self.assertEqual(result["offline_block_analysis"]["actual_rpc_calls"],0)
            self.assertEqual(result["offline_block_analysis"]["metrics"]["blocks_received"],1)

    def test_future_height_null_result_is_failure_no_retry(self):
        with tempfile.TemporaryDirectory(prefix="f0fake-",dir="/tmp") as d:
            root=Path(d);t=Clock();count=[]
            def fake(url,body,timeout,cap):
                row=json.loads(body);count.append(row["method"])
                return 200,{"Content-Type":"application/json"},json.dumps({
                    "jsonrpc":"2.0","id":row["id"],"result":
                    "0x38" if row["id"]==1 else "0x63" if row["id"]==2
                    else None}).encode()
            report=live.capture_once(permit(root,t,2),MANIFEST,REGISTRY,fake,
                                     clock=t.utc,mono=t.mono,sleep=t.sleep)
            self.assertEqual(len(count),4)
            self.assertEqual(report["failed_block_attempts"],2)
            self.assertEqual(report["unattempted_blocks"],0)
            self.assertEqual(report["attempted_total"],4)
            self.assertEqual(report["stop_state"],"CAPTURE_WINDOW_COMPLETED")

    def test_wrong_chain_stops_after_one_accounted_request(self):
        with tempfile.TemporaryDirectory(prefix="f0fake-",dir="/tmp") as d:
            root=Path(d);t=Clock();calls=[]
            def fake(url,body,timeout,cap):
                row=json.loads(body);calls.append(row["id"])
                return 200,{"Content-Type":"application/json"},json.dumps({
                    "jsonrpc":"2.0","id":row["id"],"result":"0x1"}).encode()
            r=live.capture_once(permit(root,t,4),MANIFEST,REGISTRY,fake,
                                clock=t.utc,mono=t.mono,sleep=t.sleep)
            self.assertEqual(calls,[1])
            self.assertEqual(r["stop_state"],"CAPTURE_SOURCE_BLOCKED")
            self.assertEqual(r["attempted_total"],1)
            self.assertEqual(r["unattempted_blocks"],4)

    def test_timeout_keeps_failed_attempt_and_no_auto_retry(self):
        with tempfile.TemporaryDirectory(prefix="f0fake-",dir="/tmp") as d:
            root=Path(d);t=Clock();calls=[]
            def fake(url,body,timeout,cap):
                calls.append(json.loads(body)["id"])
                raise TimeoutError("fake secret should never enter journal")
            r=live.capture_once(permit(root,t,3),MANIFEST,REGISTRY,fake,
                                clock=t.utc,mono=t.mono,sleep=t.sleep)
            self.assertEqual(calls,[1])
            j=(root/"journal.json").read_text()
            self.assertIn("NETWORK_TIMEOUT",j)
            self.assertNotIn("fake secret",j)
            self.assertEqual(r["actual_rpc_calls"],1)

    def test_interrupt_preserves_unknown_attempt_and_no_report(self):
        with tempfile.TemporaryDirectory(prefix="f0fake-",dir="/tmp") as d:
            root=Path(d);t=Clock()
            def interrupt(*args):
                raise KeyboardInterrupt
            with self.assertRaises(KeyboardInterrupt):
                live.capture_once(permit(root,t,1),MANIFEST,REGISTRY,
                                  interrupt,clock=t.utc,mono=t.mono,sleep=t.sleep)
            j=json.loads((root/"journal.json").read_text())
            self.assertEqual(j["attempted_calls"],1)
            self.assertEqual(j["attempts"][0]["state"],"ATTEMPTED_OUTCOME_UNKNOWN")
            self.assertFalse((root/"report.json").exists())

    def test_existing_report_rejected_before_network(self):
        with tempfile.TemporaryDirectory(prefix="f0fake-",dir="/tmp") as d:
            root=Path(d);t=Clock();(root/"report.json").write_text("{}")
            calls=[]
            with self.assertRaisesRegex(ValueError,"CAPTURE_OUTPUTS_NOT_FRESH"):
                live.capture_once(permit(root,t,1),MANIFEST,REGISTRY,
                                  lambda *x:calls.append(x),clock=t.utc,
                                  mono=t.mono,sleep=t.sleep)
            self.assertEqual(calls,[])

    def test_mutated_manifest_rejected_before_network(self):
        with tempfile.TemporaryDirectory(prefix="f0fake-",dir="/tmp") as d:
            root=Path(d);t=Clock();calls=[]
            with self.assertRaisesRegex(ValueError,"FROZEN_COHORT_GIT_BLOB_MISMATCH"):
                live.capture_once(permit(root,t,1),MANIFEST+b"\n",REGISTRY,
                                  lambda *x:calls.append(x),clock=t.utc,
                                  mono=t.mono,sleep=t.sleep)
            self.assertEqual(calls,[])
            self.assertFalse((root/"journal.json").exists())

    def test_time_window_expired_before_network(self):
        with tempfile.TemporaryDirectory(prefix="f0fake-",dir="/tmp") as d:
            root=Path(d);t=Clock();p=permit(root,t,1)
            with self.assertRaisesRegex(ValueError,"CAPTURE_WINDOW_INVALID"):
                live.capture_once(p,MANIFEST,REGISTRY,lambda *args:None,
                                  clock=lambda:t.utc()+timedelta(minutes=11),
                                  mono=t.mono,sleep=t.sleep)

    def test_no_redirect_handler_permits_following(self):
        handler=live.DenyRedirect()
        with self.assertRaisesRegex(ValueError,"HTTP_REDIRECT_FORBIDDEN"):
            handler.redirect_request(None,None,302,"move",{},live.ENDPOINT+"/redirect")

if __name__=="__main__":
    unittest.main()
