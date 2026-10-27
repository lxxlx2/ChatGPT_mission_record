"""Physical HTTPS source code bound to original 3-slot coordinator: offline only.

EVERY test patches the only HTTPS constructor and blocks actual sockets. There
is no real owner grant or physical run entry in this source-bridge commit.
"""
from datetime import datetime, timedelta, timezone
import http.client
import json
from pathlib import Path
import socket
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from f0_l2_d1_coordinator import (FakeSource, _run_single_shared_coordinator,
                                   run_fake_concurrent, GlobalStartGate)
from f0_l2_d1_concrete_https import _ORIGINAL_HTTPS_CONNECTION
from f0_l2_d1_physical_source_candidate import (
    BoundedPhysicalReadOnlySource, _UNRELEASED_SOURCE_CODE_SEAL, send_live)
from f0_l2_d1_recovery import reconcile_saved_attempts
from f0_l2_d1_https import HOST, PORT


def utc_window(offset_start=-10, offset_end=25):
    now=datetime.now(timezone.utc)
    return ((now+timedelta(seconds=offset_start)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            (now+timedelta(seconds=offset_end)).strftime("%Y-%m-%dT%H:%M:%SZ"))


def candidate(start=-10,end=25):
    a,b=utc_window(start,end)
    return BoundedPhysicalReadOnlySource(
        a,b,_unreleased_review_seal=_UNRELEASED_SOURCE_CODE_SEAL)


class PhysicalHTTPSBridgeTests(unittest.TestCase):
    def protected_run(self, *, source=None, status=200, fail_connect=False):
        source=source or candidate()
        fake=FakeSource(first_head=1000,growth_bps=10.0,delay_ms=0)
        events=[]
        with tempfile.TemporaryDirectory() as td:
            root=Path(td).resolve()/"private"
            root.mkdir(mode=0o700)

            class FakeResponse:
                def __init__(self,frame):
                    self.status,headers,self.body=frame
                    self.headers=list(headers.items())
                def getheaders(self):
                    return self.headers
                def read(self,limit):
                    return self.body[:limit]

            class FakeConnection:
                sock=None
                payload=None
                def connect(self):
                    if fail_connect:
                        raise TimeoutError("SIMULATED_CONNECT_FAILURE")
                    self.sock=object()
                    events.append(("connect",None))
                def request(self,method,path,*,body,headers):
                    self.payload=json.loads(body)
                    if (method!="POST" or path!="/"
                            or headers.get("Host")!=HOST
                            or headers.get("Accept-Encoding")!="identity"):
                        raise AssertionError("UNEXPECTED_RPC_WIRE")
                    rows=[json.loads(x) for x in
                          (root/"attempts.jsonl").read_text().splitlines()]
                    if not any(e["event"]=="RESERVE_UNKNOWN"
                               and e["id"]==self.payload["id"]
                               for e in rows):
                        raise AssertionError("POST_WITHOUT_DURABLE_RID")
                    events.append(("post",self.payload["method"]))
                def getresponse(self):
                    if self.payload is None:
                        raise AssertionError("RESPONSE_BEFORE_POST")
                    code,headers,raw=FakeSource.reply(fake,self.payload)
                    if status!=200:
                        code=status
                    return FakeResponse((code,headers,raw))
                def close(self):
                    self.sock=None

            def fake_ctor(host,*,port,timeout,context):
                if ((host,port)!=(HOST,PORT)
                        or not (0<timeout<=5)
                        or not context.check_hostname):
                    raise AssertionError("TLS_SCOPE_CHANGED")
                return FakeConnection()

            with (patch("http.client.HTTPSConnection",side_effect=fake_ctor),
                  patch.object(socket,"create_connection",
                               side_effect=AssertionError("REAL_SOCKET_FORBIDDEN"))):
                r=_run_single_shared_coordinator(
                    source,root,max_total=6,max_blocks=2,max_refreshes=1,
                    head_min_poll_age_ms=250,head_ttl_ms=4000,
                    window_ms=6000,max_block_response_ms=1500,
                    spacing_ms=250,anchor_initial_head=True,
                    _physical_source_candidate=True)
            records=[json.loads(l) for l in
                     (root/"attempts.jsonl").read_text().splitlines()]
            audit=reconcile_saved_attempts(root)
            return r,records,audit,events

    def test_existing_coordinator_real_transport_code_with_mocked_socket(self):
        r,rows,audit,events=self.protected_run()
        self.assertTrue(r["physical_bridge_code_tested"])
        self.assertFalse(r["physical_source_released"])
        self.assertEqual(r["mode"],
                         "F0_PHYSICAL_HTTPS_BRIDGE_PATCHED_NOT_RELEASED")
        self.assertEqual(r["network_requests"],0)
        self.assertTrue(r["no_live_sender"])
        self.assertEqual(r["initial_anchor_attempts"],1)
        self.assertTrue(r["first_parent_same_source_anchored"])
        self.assertEqual(audit["initial_anchor_attempts"],1)
        self.assertEqual(audit["verified_initial_parent_links"],1)
        self.assertGreaterEqual(r["contiguous_commits"],1)
        self.assertEqual(r["verified_internal_parent_links"],
                         r["contiguous_commits"]-1)
        self.assertFalse(r["first_parent_independently_anchored"])
        self.assertEqual(audit["contiguous_commits"],r["contiguous_commits"])
        self.assertLessEqual(r["reserved"],6)
        self.assertLessEqual(r["max_shared_slots"],3)
        self.assertGreaterEqual(r["min_actual_fake_start_gap_ms"],248.5)
        self.assertEqual(r["reserved"],r["settled"])
        self.assertTrue(any(x[1]=="eth_getBlockByNumber" for x in events))
        self.assertEqual(r["synthetic_source_growth_bps"],None)

    def test_public_fake_entry_denies_physical_before_journal_or_tls(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td).resolve()/"private"
            root.mkdir(mode=0o700)
            with patch("http.client.HTTPSConnection",
                       side_effect=AssertionError("NO_HTTPS_EXPECTED")) as ctor:
                with self.assertRaisesRegex(ValueError,
                                             "FOREGROUND_PHYSICAL_SOURCE_NOT_RELEASED"):
                    run_fake_concurrent(candidate(),root,anchor_initial_head=True)
                ctor.assert_not_called()
            self.assertEqual(list(root.iterdir()),[])

    def test_real_constructor_denied_even_private_candidate_entry(self):
        self.assertIs(http.client.HTTPSConnection,_ORIGINAL_HTTPS_CONNECTION)
        with tempfile.TemporaryDirectory() as td:
            root=Path(td).resolve()/"private"
            root.mkdir(mode=0o700)
            with patch.object(socket,"create_connection",
                              side_effect=AssertionError("REAL_SOCKET_FORBIDDEN")):
                with self.assertRaisesRegex(
                        ValueError,"FOREGROUND_PHYSICAL_SOURCE_NOT_RELEASED"):
                    _run_single_shared_coordinator(
                        candidate(),root,_physical_source_candidate=True,
                        anchor_initial_head=True)
            self.assertEqual(list(root.iterdir()),[])

    def test_expired_utc_rejected_at_final_post_before_http_request(self):
        r,rows,audit,events=self.protected_run(source=candidate(-35,-5))
        self.assertEqual(len([e for e in events if e[0]=="post"]),0)
        self.assertEqual(r["contiguous_commits"],0)
        self.assertFalse(r["first_parent_same_source_anchored"])
        self.assertEqual(r["stop"],"RPC_OR_HEAD_FAULT")
        self.assertEqual(audit["audit_status"],"INVALID_FOR_PERFORMANCE_CLAIM")
        self.assertEqual(audit["unknown_request_ids"],[])

    def test_http_503_keeps_raw_and_does_not_promote_anchor(self):
        r,rows,audit,events=self.protected_run(status=503)
        self.assertEqual(r["contiguous_commits"],0)
        self.assertEqual(audit["audit_status"],"INVALID_FOR_PERFORMANCE_CLAIM")
        self.assertFalse(audit["first_parent_same_source_anchored"])
        self.assertTrue(any(e.get("raw_name") for e in rows
                            if e["event"]=="SETTLE"))
        self.assertEqual(audit["unknown_request_ids"],[])

    def test_tls_connect_failure_is_accounted_without_retry(self):
        r,rows,audit,events=self.protected_run(fail_connect=True)
        self.assertEqual(r["reserved"],1)
        self.assertEqual(r["settled"],1)
        self.assertEqual(r["contiguous_commits"],0)
        self.assertEqual(r["initial_anchor_attempts"],0)
        self.assertEqual(audit["failed_request_ids"],[1])
        self.assertEqual(audit["network_retries"],0)
        self.assertFalse(audit["first_parent_same_source_anchored"])
        self.assertEqual(len([e for e in rows if e["event"]=="RESERVE_UNKNOWN"]),1)

    def test_direct_call_without_true_coordinator_guard_is_denied(self):
        src=candidate()
        rpc={"jsonrpc":"2.0","id":1,"method":"eth_chainId","params":[]}
        with patch("http.client.HTTPSConnection",
                   side_effect=AssertionError("NO_CONNECT_EXPECTED")) as ctor:
            with self.assertRaisesRegex(ValueError,"DURABLE_RID_REQUIRED"):
                src.reply_transport_evidence_physical_candidate(
                    rpc,lambda:None,2.0,reservation_guard=lambda _:None)
            ctor.assert_not_called()

    def test_public_candidate_release_and_bad_windows_are_denied(self):
        with self.assertRaisesRegex(ValueError,"NOT_RELEASED"):
            send_live()
        a,b=utc_window()
        with self.assertRaisesRegex(ValueError,"RELEASE_NOT_REVIEWED"):
            BoundedPhysicalReadOnlySource(a,b)
        for lo,hi in ((-120,20), (10,-10), (-5,-5)):
            with self.subTest(lo=lo,hi=hi):
                start,end=utc_window(lo,hi)
                with self.assertRaisesRegex(ValueError,"UTC_WINDOW_INVALID"):
                    BoundedPhysicalReadOnlySource(
                        start,end,_unreleased_review_seal=_UNRELEASED_SOURCE_CODE_SEAL)


if __name__=="__main__":
    unittest.main()
