"""New actual-once source probe: OFFLINE adversarial tests, ZERO real TCP/DNS."""
import json
import io
import http.client
from datetime import datetime, timezone, timedelta
from pathlib import Path
import socket
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from f0_l1_5m_source_once import (
    SCHEMA, ENDPOINT, METHODS, MAX_BODY, validate_scope, run_probe, Sender, Capture,
    now_utc, main)
from f0_l1_window import load_frozen_cohort,cohort_watchlist
from f0_l1_preflight import official_router_addresses

SHA="a"*40


def permit():
    n=now_utc()
    return dict(
        schema=SCHEMA,user_authorized=True,independent_review_required=True,
        endpoint=ENDPOINT,chain_id=56,methods=METHODS,free_only=True,
        read_only=True,no_retries=True,no_ws=True,no_proxy=True,
        no_redirects=True,background=False,
        approved_commit_sha=SHA,approved_script_sha256="b"*64,
        run_nonce="c"*64,storage_root="/tmp/f0-source-once-TEST",
        window_start_utc=(n-timedelta(seconds=2)).isoformat().replace("+00:00","Z"),
        window_end_utc=(n+timedelta(seconds=301)).isoformat().replace("+00:00","Z"),
        max_total_attempts=770,max_block_reads=730,max_head_polls=31,
        duration_ms=300000,head_poll_interval_ms=10000,slots=3,
        spacing_ms=250,timeout_ms=5000,max_response_bytes=MAX_BODY)


def valid_rpc(req):
    return json.dumps({"jsonrpc":"2.0","id":req["id"],
                       "result":"0x38" if req["method"]=="eth_chainId"
                       else "0x64" if req["method"]=="eth_blockNumber"
                       else {"number":req["params"][0],
                             "hash":hex(int(req["params"][0],16))[2:].zfill(64),
                             "parentHash":"0x"+format(
                                 int(req["params"][0],16)-1,"064x"),
                             "transactions":[]}}).encode()


class MemorySource:
    def __init__(self):
        self.calls=[]
        self.anchor=100
    def send(self,encoded):
        req=json.loads(encoded)
        self.calls.append(req)
        time.sleep(0.001)
        if req["method"]=="eth_blockNumber":
            self.anchor+=6
            value=hex(self.anchor)
        elif req["method"]=="eth_chainId":
            value="0x38"
        else:
            h=int(req["params"][0],16)
            value={"number":hex(h),"hash":"0x"+format(h,"064x"),
                   "parentHash":"0x"+format(h-1,"064x"),
                   "transactions":[]}
        data=json.dumps({"jsonrpc":"2.0","id":req["id"],"result":value}).encode()
        return {"state":"RAW","status":200,
                "headers":{"Content-Type":"application/json"},
                "raw":data,"post_ns":time.monotonic_ns(),
                "end_ns":time.monotonic_ns()}


class FiveMinuteSourceTests(unittest.TestCase):
    def test_exact_valid_maximum_scope_and_no_permission(self):
        p=permit()
        self.assertIs(validate_scope(p),p)
        self.assertFalse(hasattr(validate_scope,"execute_live"))

    def test_late_and_method_and_budget_scope_denied(self):
        for key,value in (
            ("methods",METHODS+["eth_sendRawTransaction"]),
            ("endpoint","https://evil.com"),
            ("slots",True),("max_total_attempts",801),
            ("max_block_reads",741),("max_head_polls",32),
            ("head_poll_interval_ms",2000),
            ("duration_ms",300001),
            ("user_authorized",1),
            ("approved_commit_sha","z"*40),
        ):
            with self.subTest(key=key):
                q=permit()
                q[key]=value
                with self.assertRaisesRegex(ValueError,"ONCE_SCOPE_"):
                    validate_scope(q)

    def test_incoherent_reservation_rejected_before_network(self):
        q=permit()
        q["max_total_attempts"]=731
        with patch("socket.getaddrinfo",
                   side_effect=AssertionError("DNS_FORBIDDEN")) as dns:
            with self.assertRaisesRegex(ValueError,"INCOHERENT"):
                validate_scope(q)
            dns.assert_not_called()

    def test_no_implicit_live_entry(self):
        with (patch.object(sys,"argv",["runner"]),
              patch("socket.create_connection",
                    side_effect=AssertionError("REAL_TCP_FORBIDDEN")) as tcp,
              patch("socket.getaddrinfo",
                    side_effect=AssertionError("REAL_DNS_FORBIDDEN")) as dns):
            with self.assertRaises(SystemExit):
                main()
            tcp.assert_not_called()
            dns.assert_not_called()

    def test_fake_source_three_slot_and_durable_raw_no_real_network(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp).resolve()
            q=permit()
            q.update(max_total_attempts=48,max_block_reads=32,
                     max_head_polls=10,duration_ms=1200,
                     head_poll_interval_ms=100)
            source=MemorySource()
            cohort_raw=(ROOT/"F0_COHORT_PRESELECTION.json").read_bytes()
            watches,_=cohort_watchlist(load_frozen_cohort(cohort_raw))
            registry=json.loads((ROOT/"F0_ROUTER_SOURCE_CANDIDATES.json").read_bytes())
            routers=set(official_router_addresses(registry))
            with (patch("socket.getaddrinfo",
                        side_effect=AssertionError("REAL_DNS_FORBIDDEN")) as dns,
                  patch("socket.create_connection",
                        side_effect=AssertionError("REAL_TCP_FORBIDDEN")) as tcp):
                result=run_probe(q,watches,routers,path,sender=source)
                tcp.assert_not_called()
                dns.assert_not_called()
            self.assertGreater(result["heads_requested"],1)
            self.assertGreater(result["blocks_requested"],1)
            self.assertGreater(result["last_contiguous_height"],106)
            self.assertEqual(result["failed"],0)
            self.assertEqual(result["attempts"],len(source.calls))
            self.assertEqual(result["post_started"],len(source.calls))
            self.assertLessEqual(result["max_inflight"],3)
            self.assertIsNone(result["buy_confirmed"])
            rows=[json.loads(x) for x in (path/"attempts.jsonl").read_text().splitlines()]
            self.assertEqual(len(rows),2*len(source.calls))
            first={}
            settled={}
            for index,row in enumerate(rows):
                if row["event"]=="RESERVE_UNKNOWN":
                    first[row["rid"]]=index
                elif row["event"]=="SETTLE":
                    settled[row["rid"]]=index
                    self.assertLess(first[row["rid"]],index)
                    raw=(path/"raw_responses"/row["raw_file"]).read_bytes()
                    import hashlib
                    self.assertEqual(row["response_sha256"],
                                     hashlib.sha256(raw).hexdigest())
            self.assertEqual(set(first),set(settled))
            self.assertGreaterEqual(result["contiguous_full_blocks_post_anchor"],1)
            self.assertGreaterEqual(result["contiguous_rate_blocks_per_s"],0)
            self.assertGreater(len(result["head_samples"]),1)

    def test_orphan_parent_block_does_not_count_wallet_signed_transactions(self):
        cohort_raw=(ROOT/"F0_COHORT_PRESELECTION.json").read_bytes()
        watched,_=cohort_watchlist(load_frozen_cohort(cohort_raw))
        router_raw=(ROOT/"F0_ROUTER_SOURCE_CANDIDATES.json").read_bytes()
        routers=set(official_router_addresses(json.loads(router_raw)))
        w=sorted(watched)[0]
        target=sorted(routers)[0]
        def rpc(height,parent,txs):
            return {"jsonrpc":"2.0","id":1,
                    "result":{"number":hex(height),
                              "hash":"0x"+format(height,"064x"),
                              "parentHash":"0x"+format(parent,"064x"),
                              "transactions":txs}}
        with tempfile.TemporaryDirectory() as td:
            cp=Capture(Path(td),permit(),sender=None)
            try:
                cp.ingest("ANCHOR",100,rpc(100,99,[]),None,
                          {"post_ns":1,"end_ns":2},watched,routers)
                tx={"hash":"0x"+format(987654,"064x"),
                    "from":w,"to":target,"value":"0x0",
                    "blockNumber":hex(101)}
                cp.ingest("BLOCK",101,rpc(101,55,[tx]),None,
                          {"post_ns":1,"end_ns":2},watched,routers)
                self.assertEqual(cp.stop_reason,"BLOCK_IDENTITY_OR_PARENT_INVALID")
                self.assertEqual(cp.watch_signed,0)
                self.assertEqual(cp.router_candidates,0)
                self.assertEqual(cp.last_contiguous,100)
            finally:
                cp.finish()

    def test_sender_tls_pacing_post_response_and_full_are_distinct(self):
        # No TCP/DNS: distinct fake connect, throttle wait and body read.
        class Response:
            status=200
            chunked=False
            length=40
            will_close=False
            closed=False
            def getheaders(self):
                return [("Content-Type","application/json"),
                        ("Content-Length","40")]
            def read1(self,n):
                time.sleep(0.003)
                if self.closed:
                    return b""
                self.closed=True
                return b'{"jsonrpc":"2.0","id":1,"result":"0x38"}'
            def isclosed(self):
                return self.closed

        class FakeConnection:
            def __init__(self,*args,**kwargs):
                pass
            def connect(self):
                time.sleep(0.005)
            def request(self,*args,**kwargs):
                pass
            def getresponse(self):
                return Response()
            def close(self):
                pass

        sender=Sender(end_utc=now_utc()+timedelta(seconds=10),
                      stop_mono=time.monotonic()+10,
                      timeout_s=1,spacing_s=0.06,
                      post_factory=FakeConnection)
        with (patch("socket.create_connection",
                    side_effect=AssertionError("TCP_FORBIDDEN")) as tcp,
              patch("socket.getaddrinfo",
                    side_effect=AssertionError("DNS_FORBIDDEN")) as dns):
            first=sender.send(b"{}")
            second=sender.send(b"{}")
            tcp.assert_not_called()
            dns.assert_not_called()
        for result in (first,second):
            self.assertEqual(result["state"],"RAW")
            self.assertGreaterEqual(result["tls_connect_ms"],4.0)
            self.assertGreaterEqual(result["post_to_response_ms"],2.0)
            self.assertGreater(result["full_attempt_ms"],
                               result["tls_connect_ms"])
            self.assertGreaterEqual(result["pacing_wait_ms"],0.0)
            # Four observed segments are never presented as the same latency.
            # Full attempt also includes HTTPS constructor and SSL context
            # setup; it is NOT identical to the three narrower intervals.
            self.assertGreaterEqual(
                result["full_attempt_ms"]+0.1,
                result["tls_connect_ms"]+result["pacing_wait_ms"]+
                result["post_to_response_ms"])
            self.assertNotIn("connect_ms",result)
        self.assertGreater(second["pacing_wait_ms"],25)
        self.assertLess(second["tls_connect_ms"],
                        second["pacing_wait_ms"])
        self.assertGreater(second["full_attempt_ms"],
                           second["post_to_response_ms"])

    def test_fake_report_has_defined_timing_population_and_missing_samples(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td).resolve()
            doc=permit()
            doc.update(max_total_attempts=48,max_block_reads=32,
                       max_head_polls=10,duration_ms=1200,
                       head_poll_interval_ms=100)
            raw=(ROOT/"F0_COHORT_PRESELECTION.json").read_bytes()
            watches,_=cohort_watchlist(load_frozen_cohort(raw))
            routers=set(official_router_addresses(json.loads(
                (ROOT/"F0_ROUTER_SOURCE_CANDIDATES.json").read_bytes())))
            result=run_probe(doc,watches,routers,root,sender=MemorySource())
            self.assertEqual(result["tls_connect_sample_count"],0)
            self.assertIsNone(result["tls_connect_p50_ms"])
            self.assertEqual(result["pacing_wait_sample_count"],0)
            self.assertEqual(result["full_attempt_sample_count"],0)
            self.assertGreater(result["post_to_response_sample_count"],0)
            self.assertIsNotNone(result["post_to_response_p95_ms"])
            self.assertNotIn("block_response_p50_ms",result)
            self.assertIn("global lock",result["timing_definition"]["pacing_wait"])

    def _run_wire(self, wire: bytes, *, timeout=1.0, latency=0,
                  slow_headers=0, slow_body=0):
        class SlowRaw(io.RawIOBase):
            def __init__(self, payload):
                self.buffer=io.BytesIO(payload)
                self.body_at=payload.find(b"\\r\\n\\r\\n")+4
            def readable(self):
                return True
            def readinto(self, b):
                n=min(len(b),1)
                index=self.buffer.tell()
                data=self.buffer.read(n)
                if data:
                    delay=slow_headers if index<self.body_at else slow_body
                    if delay:
                        time.sleep(delay)
                b[:len(data)]=data
                return len(data)

        class FakeSocket:
            def __init__(self, content):
                self.content=content
            def makefile(self,*args,**kwargs):
                if slow_headers or slow_body:
                    return io.BufferedReader(SlowRaw(self.content),
                                             buffer_size=1)
                return io.BytesIO(self.content)

        class RealHTTPResponseConnection:
            def __init__(self,*args,**kwargs):
                self.sock=None
            def connect(self):
                pass
            def request(self,*args,**kwargs):
                pass
            def getresponse(self):
                response=http.client.HTTPResponse(FakeSocket(wire))
                response.begin()
                if latency:
                    time.sleep(latency)
                return response
            def close(self):
                pass

        sender=Sender(end_utc=now_utc()+timedelta(seconds=10),
                      stop_mono=time.monotonic()+10,
                      timeout_s=timeout,spacing_s=0.25,
                      post_factory=RealHTTPResponseConnection)
        with (patch("socket.create_connection",
                    side_effect=AssertionError("REAL_TCP_FORBIDDEN")) as tcp,
              patch("socket.getaddrinfo",
                    side_effect=AssertionError("REAL_DNS_FORBIDDEN")) as dns):
            result=sender.send(b"{}")
            dns.assert_not_called()
            tcp.assert_not_called()
        return result

    def test_stdlib_httpresponse_declared_length_truncation_partial_is_failed(self):
        valid=b'{"jsonrpc":"2.0","id":1,"result":"0x38"}'
        wire=(b"HTTP/1.1 200 OK\\r\\nContent-Type: application/json\\r\\n"
              +b"Content-Length: "+str(len(valid)+100).encode()
              +b"\\r\\nConnection: close\\r\\n\\r\\n"+valid)
        out=self._run_wire(wire)
        self.assertEqual(out["state"],"HTTP_TRUNCATED_CONTENT_LENGTH")
        self.assertEqual(out["raw"],valid)
        self.assertFalse(out["framing_valid"])

    def test_stdlib_httpresponse_conflicting_duplicate_cl_is_failed(self):
        valid=b'{"jsonrpc":"2.0","id":1,"result":"0x38"}'
        wire=(b"HTTP/1.1 200 OK\\r\\nContent-Type: application/json\\r\\n"
              +b"Content-Length: "+str(len(valid)+100).encode()
              +b"\\r\\nContent-Length: "+str(len(valid)).encode()
              +b"\\r\\nConnection: close\\r\\n\\r\\n"+valid)
        out=self._run_wire(wire)
        self.assertEqual(out["state"],"HTTP_DUPLICATE_FRAMING_HEADER")
        self.assertNotEqual(out["state"],"RAW")

    def test_stdlib_chunked_complete_and_truncated(self):
        valid=b'{"jsonrpc":"2.0","id":1,"result":"0x38"}'
        prefix=b"HTTP/1.1 200 OK\\r\\nTransfer-Encoding: chunked\\r\\nContent-Type: application/json\\r\\nConnection: close\\r\\n\\r\\n"
        body=("%x"%len(valid)).encode()+b"\\r\\n"+valid+b"\\r\\n"
        accepted=self._run_wire(prefix+body+b"0\\r\\n\\r\\n")
        self.assertEqual(accepted["state"],"RAW")
        self.assertEqual(accepted["raw"],valid)
        trunc=self._run_wire(prefix+body)
        self.assertNotEqual(trunc["state"],"RAW")
        self.assertTrue(trunc["state"].startswith("HTTP_"))

    def test_stdlib_valid_content_length_success(self):
        valid=b'{"jsonrpc":"2.0","id":1,"result":"0x38"}'
        out=self._run_wire(
            b"HTTP/1.1 200 OK\\r\\nContent-Type: application/json\\r\\n"
            +b"Content-Length: "+str(len(valid)).encode()+b"\\r\\n"
            +b"Connection: close\\r\\n\\r\\n"+valid)
        self.assertEqual(out["state"],"RAW")
        self.assertEqual(out["raw"],valid)

    def test_header_latency_counts_against_one_request_deadline(self):
        valid=b'{"jsonrpc":"2.0","id":1,"result":"0x38"}'
        wire=(b"HTTP/1.1 200 OK\\r\\nContent-Type: application/json\\r\\n"
              +b"Content-Length: "+str(len(valid)).encode()
              +b"\\r\\nConnection: close\\r\\n\\r\\n"+valid)
        result=self._run_wire(wire,timeout=0.06,slow_headers=0.0015)
        self.assertEqual(result["state"],"REQUEST_DEADLINE_EXCEEDED")
        self.assertNotEqual(result["state"],"RAW")

    def test_trickle_body_stream_deadline_preserves_partial_bytes(self):
        valid=b'{"jsonrpc":"2.0","id":1,"result":"0x38"}'
        wire=(b"HTTP/1.1 200 OK\\r\\nContent-Type: application/json\\r\\n"
              +b"Content-Length: "+str(len(valid)).encode()
              +b"\\r\\nConnection: close\\r\\n\\r\\n"+valid)
        out=self._run_wire(wire,timeout=0.26,slow_body=0.02)
        self.assertEqual(out["state"],"REQUEST_DEADLINE_EXCEEDED")
        self.assertTrue(valid.startswith(out["raw"]))
        self.assertLess(len(out["raw"]),len(valid))

    def test_header_and_body_cumulative_request_deadline(self):
        valid=b'{"jsonrpc":"2.0","id":1,"result":"0x38"}'
        wire=(b"HTTP/1.1 200 OK\\r\\nContent-Type: application/json\\r\\n"
              +b"Content-Length: "+str(len(valid)).encode()
              +b"\\r\\nConnection: close\\r\\n\\r\\n"+valid)
        out=self._run_wire(wire,timeout=0.22,
                           slow_headers=0.0012,slow_body=0.01)
        self.assertEqual(out["state"],"REQUEST_DEADLINE_EXCEEDED")
        self.assertNotEqual(out["state"],"RAW")

    def test_slow_stream_elapsed_over_deadline_rejected_even_if_json_valid(self):
        valid=b'{"jsonrpc":"2.0","id":1,"result":"0x38"}'
        wire=(b"HTTP/1.1 200 OK\\r\\nContent-Type: application/json\\r\\n"
              +b"Content-Length: "+str(len(valid)).encode()
              +b"\\r\\nConnection: close\\r\\n\\r\\n"+valid)
        result=self._run_wire(wire,timeout=0.06,latency=0.09)
        self.assertEqual(result["state"],"REQUEST_DEADLINE_EXCEEDED")
        self.assertNotEqual(result["state"],"RAW")

    def test_real_sender_post_clock_denied_after_fake_tls_connection(self):
        calls=[]
        class FakeConnection:
            def __init__(self,*args,**kwargs):
                calls.append("ctor")
            def connect(self):
                calls.append("connect")
            def request(self,*args,**kwargs):
                calls.append("POST")
            def close(self):
                calls.append("close")
        sender=Sender(end_utc=now_utc()-timedelta(seconds=1),
                      stop_mono=time.monotonic()+1,
                      timeout_s=1,spacing_s=0.25,
                      post_factory=FakeConnection)
        with (patch("socket.getaddrinfo",
                    side_effect=AssertionError("REAL_DNS_FORBIDDEN")) as dns,
              patch("socket.create_connection",
                    side_effect=AssertionError("REAL_TCP_FORBIDDEN")) as tcp):
            result=sender.send(b"{}")
            dns.assert_not_called()
            tcp.assert_not_called()
        self.assertEqual(result["state"],"PRE_POST_WINDOW_DENIED")
        self.assertEqual(calls,["ctor","connect","close"])


if __name__=="__main__":
    unittest.main()
