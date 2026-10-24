"""Offline-only review of one shared coordinator using concrete real TLS source.

The *actual* http.client.HTTPSConnection constructor is patched on every
review-source invocation, and tests assert the disposable consumed marker
and the fsynced RESERVE_UNKNOWN already exist BEFORE mocked TLS connect.
"""
import json
import sys
import tempfile
import threading
from pathlib import Path
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from f0_l2_d1_coordinator import (
    FakeSource, run_fake_concurrent, _review_unreleased_real_concurrent,
)
from f0_l2_d1_grant import OfflineGrantRegistry
from f0_l2_d1_recovery import reconcile_saved_attempts
from f0_l2_d1_unreleased_real_source import (
    UnreleasedRealHTTPSCodeSource,
    _D1_OFFLINE_UNRELEASED_TRANSPORT_TICKET as REVIEW_TICKET,
    send_live,
)


class MockedNetworkReviewTests(unittest.TestCase):
    def setUp(self):
        d=tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        self.root=Path(d.name).resolve()
        self.evidence=self.root/"evidence"
        self.registry=self.root/"registrar"
        self.evidence.mkdir(mode=0o700)
        self.registry.mkdir(mode=0o700)
        self.frames=FakeSource(delay_ms=0,growth_bps=10.0)
        self.methods=[]
        self.connects=[]
        self.lock=threading.Lock()
        self.block_status=None
        self.head_status=None
        self.write_timeout=False
        self.mark=None

    def factory(self, host, *, port, timeout, context):
        self.assertEqual((host,port),
                         ("bsc-dataseed.bnbchain.org",443))
        self.assertTrue(context.check_hostname)
        self.assertGreater(timeout,0)
        self.assertLessEqual(timeout,5)
        case=self
        class R:
            def __init__(self,frame):
                self.status,self.header_dict,self.body=frame
            def getheaders(self):
                return list(self.header_dict.items())
            def read(self,size):
                return self.body[:size]

        class M:
            sock=None
            frame=None
            closed=False
            def connect(self):
                self.sock=object()
                contents=(case.evidence/"attempts.jsonl").read_bytes()
                self_id=len(case.connects)+1
                self_reserved=b'"event":"RESERVE_UNKNOWN"' in contents
                case.assertTrue(self_reserved, "TLS connect before durable journal")
                if case.mark:
                    case.assertTrue(case.mark.exists(),
                                    "TLS connect before one-use marker")
                with case.lock:
                    case.connects.append(self_id)
            def request(self, method, path, *,body,headers):
                case.assertEqual((method,path),("POST","/"))
                request=json.loads(body)
                with case.lock:
                    case.methods.append(request["method"])
                if case.write_timeout and request["method"]=="eth_blockNumber":
                    raise TimeoutError("MOCK_POST_WRITE_UNKNOWN")
                frame=case.frames.reply(request)
                if case.head_status and request["method"]=="eth_blockNumber":
                    frame=(case.head_status,frame[1],frame[2])
                if case.block_status and request["method"]=="eth_getBlockByNumber":
                    frame=(case.block_status,frame[1],frame[2])
                self.frame=R(frame)
            def getresponse(self):
                return self.frame
            def close(self):
                self.closed=True
                self.sock=None
        return M()

    def reviewed(self, *, max_total=8, max_blocks=3, max_refreshes=3,
                 marker=True):
        if marker:
            consume=OfflineGrantRegistry(self.registry).consume(
                "single-run-f0-test", "a"*64)
            self.assertEqual(consume["status"],
                             "CONSUMED_NOT_A_NETWORK_AUTHORIZATION")
            self.mark=next(self.registry.iterdir())
        source=UnreleasedRealHTTPSCodeSource(
            _offline_review_ticket=REVIEW_TICKET)
        with patch("http.client.HTTPSConnection",side_effect=self.factory) as ctor:
            result=_review_unreleased_real_concurrent(
                source, self.evidence,
                _offline_review_ticket=REVIEW_TICKET,
                max_total=max_total,max_blocks=max_blocks,
                max_refreshes=max_refreshes,slots=3,spacing_ms=250,
                window_ms=6000,head_ttl_ms=4000)
        return result,ctor

    def test_shared_one_coordinator_with_durable_preconnect_and_ledger(self):
        result,ctor=self.reviewed()
        self.assertGreater(ctor.call_count,0)
        self.assertGreater(len(self.connects),0)
        self.assertLessEqual(result["max_shared_slots"],3)
        self.assertLessEqual(result["reserved"],8)
        self.assertEqual(result["reserved"],result["settled"])
        self.assertGreaterEqual(result["min_actual_fake_start_gap_ms"],248.5)
        self.assertEqual(result["mode"],
                         "D1_REAL_HTTP_CODE_UNRELEASED_NO_AUTHORITY")
        self.assertTrue(result["unreleased_transport_review_only"])
        self.assertIsNone(result["network_requests"],
                          "Never claim 0 real calls for real transport code")
        self.assertIsNone(result["synthetic_source_growth_bps"])
        self.assertEqual(result["production"],"NO_GO")
        audit=reconcile_saved_attempts(self.evidence)
        self.assertIn(audit["audit_status"],
                      ("OFFLINE_ACCOUNTED_NOT_LIVE",
                       "INVALID_FOR_PERFORMANCE_CLAIM"))
        self.assertEqual(set(self.methods)-{
            "eth_chainId","eth_blockNumber","eth_getBlockByNumber"},set())

    def test_503_on_real_transport_code_preserves_raw_no_retry(self):
        self.head_status=503
        result,ctor=self.reviewed()
        self.assertEqual(result["stop"],"RPC_OR_HEAD_FAULT")
        self.assertEqual(result["contiguous_commits"],0)
        self.assertEqual(result["reserved"],result["settled"])
        self.assertEqual(self.methods.count("eth_blockNumber"),1)
        self.assertGreaterEqual(ctor.call_count,2)
        bodies=list((self.evidence/"raw_responses").glob("*.body"))
        self.assertTrue(bodies)
        self.assertEqual(result["production"],"NO_GO")

    def test_post_write_unknown_keeps_stop_without_retry(self):
        self.write_timeout=True
        result,ctor=self.reviewed()
        self.assertEqual(result["stop"],"RPC_OR_HEAD_FAULT")
        self.assertEqual(result["contiguous_commits"],0)
        self.assertEqual(self.methods.count("eth_blockNumber"),1)
        self.assertEqual(result["reserved"],result["settled"])
        self.assertTrue(result["faults"])
        self.assertGreaterEqual(ctor.call_count,2)

    def test_old_fake_entry_never_accepts_real_source(self):
        source=UnreleasedRealHTTPSCodeSource(
            _offline_review_ticket=REVIEW_TICKET)
        with patch("http.client.HTTPSConnection",
                   side_effect=AssertionError("NETWORK")) as network:
            with self.assertRaisesRegex(ValueError,"SCOPE_INVALID"):
                run_fake_concurrent(source,self.evidence)
            with self.assertRaisesRegex(ValueError,"CODE_REVIEW_DENIED"):
                _review_unreleased_real_concurrent(
                    source,self.evidence)
            with self.assertRaisesRegex(ValueError,
                                        "D2_D3_NOT_AUTHORIZED"):
                send_live(execute_live=True)
            network.assert_not_called()
        self.assertFalse(list(self.evidence.iterdir()))

    def test_one_use_fake_registry_cannot_be_refunded_with_new_output(self):
        self.reviewed()
        with self.assertRaisesRegex(ValueError,"GRANT_ALREADY_CONSUMED"):
            OfflineGrantRegistry(self.registry).consume(
                "single-run-f0-test","a"*64)
        newout=self.root/"different-evidence"
        newout.mkdir(mode=0o700)
        with self.assertRaisesRegex(ValueError,"GRANT_ALREADY_CONSUMED"):
            OfflineGrantRegistry(self.registry).consume(
                "single-run-f0-test","b"*64)
        self.assertFalse(list(newout.iterdir()))


if __name__=="__main__":
    unittest.main()
