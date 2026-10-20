"""Transport-free Journal refactor contracts; no live HTTP or RPC."""
import ast
import hashlib
import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from f0_l1_durable_journal import Journal, SCHEMA, sha
from f0_l1_http_wire import ENDPOINT


class Clock:
    def __init__(self):
        self.ms=0
        self.zero=datetime(2026,10,20,tzinfo=timezone.utc)

    def utc(self):
        return self.zero+timedelta(milliseconds=self.ms)

    def mono(self):
        return self.ms/1000

    def sleep(self,seconds):
        self.ms+=max(1,round(seconds*1000))


def new_journal(root,clock,limit=3):
    return Journal(root/"journal.json", limit=limit,
                   clock=clock.utc, mono=clock.mono, sleep=clock.sleep,
                   interval_ms=250, deadline=clock.utc()+timedelta(minutes=1),
                   raw_dir=root/"raw_responses")


class TransportFreeJournalTests(unittest.TestCase):
    def test_raw_codec_closure_and_fake_replay_do_not_import_network_runner(self):
        for name in ["f0_l1_durable_journal.py","f0_l1_http_wire.py",
                     "f0_l1_adaptive_journal_replay.py"]:
            text=(ROOT/name).read_text()
            tree=ast.parse(text)
            roots=set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    roots.update(a.name.split(".")[0] for a in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    roots.add(node.module.split(".")[0])
            forbidden={"f0_l1_live_short","urllib","socket","ssl",
                       "http","requests","websocket","subprocess","asyncio"}
            self.assertFalse(roots & forbidden, (name,roots & forbidden))
        self.assertEqual(SCHEMA,"bsc-f0-l1-short-http-single-use-v1")

    def test_live_runner_imports_shared_journal_not_second_copy(self):
        import f0_l1_live_short
        self.assertIs(f0_l1_live_short.Journal,Journal)
        self.assertNotIn("class Journal:",(ROOT/"f0_l1_live_short.py").read_text())
        self.assertIn('"f0_l1_durable_journal.py"',
                      (ROOT/"f0_l1_live_short.py").read_text())

    def test_presend_unknown_persists_before_fake_post(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);clock=Clock();j=new_journal(root,clock)
            def fake(url,raw,timeout,cap):
                disk=json.loads((root/"journal.json").read_text())
                self.assertEqual(disk["attempted_calls"],1)
                self.assertEqual(disk["attempts"][0]["state"],
                                 "ATTEMPTED_OUTCOME_UNKNOWN")
                self.assertEqual(url,ENDPOINT)
                payload=json.loads(raw)
                return (200,{"Content-Type":"application/json"},
                        json.dumps({"jsonrpc":"2.0","id":payload["id"],
                                    "result":"0x38"}).encode())
            result,failure,item=j.request("eth_chainId",[],"CHAIN_ID",fake)
            self.assertIsNone(failure)
            self.assertEqual(result["result"],"0x38")
            self.assertEqual(item["state"],"RPC_RESPONSE")
            self.assertEqual(item["index"],1)
            self.assertEqual(len(list((root/"raw_responses").glob("*.json"))),1)
            raw=(root/"raw_responses"/"001.response.json").read_bytes()
            self.assertEqual(sha(raw),item["response_sha256"])
            self.assertEqual(json.loads((root/"journal.json").read_text())["schema"],SCHEMA)

    def test_interrupt_still_leaves_durable_unknown_without_retry(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);j=new_journal(root,Clock())
            calls=[]
            def stop(*args):
                calls.append(True)
                raise KeyboardInterrupt()
            with self.assertRaises(KeyboardInterrupt):
                j.request("eth_chainId",[],"CHAIN_ID",stop)
            disk=json.loads((root/"journal.json").read_text())
            self.assertEqual(calls,[True])
            self.assertEqual(disk["attempted_calls"],1)
            self.assertEqual(disk["attempts"][0]["state"],
                             "ATTEMPTED_OUTCOME_UNKNOWN")

    def test_failure_classifications_retained_without_urllib_dependency(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);clock=Clock();j=new_journal(root,clock)
            def fail(*args):
                raise OSError("private token 987")
            _,reason,item=j.request("eth_chainId",[],"CHAIN_ID",fail)
            self.assertEqual(reason,"NETWORK_ERROR_OR_HTTP_ERROR")
            self.assertEqual(item["state"],"FAILED")
            self.assertNotIn("private token 987",(root/"journal.json").read_text())

    def test_budget_exhaustion_prevents_second_fake_post(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);clock=Clock();j=new_journal(root,clock,limit=1)
            calls=[]
            def fake(url,body,timeout,cap):
                calls.append(True)
                return 200,{"Content-Type":"application/json"},json.dumps({
                    "jsonrpc":"2.0","id":1,"result":"0x38"}).encode()
            j.request("eth_chainId",[],"CHAIN_ID",fake)
            with self.assertRaisesRegex(ValueError,"CAPTURE_CALL_CAP_REACHED"):
                j.request("eth_blockNumber",[],"HEAD",fake)
            self.assertEqual(len(calls),1)
            self.assertEqual(json.loads((root/"journal.json").read_text())["attempted_calls"],1)


if __name__=="__main__":
    unittest.main()
