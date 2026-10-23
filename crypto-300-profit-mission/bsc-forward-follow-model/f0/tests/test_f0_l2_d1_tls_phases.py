"""D1 mock HTTPS connection lifecycle, zero real socket calls."""
import json
from pathlib import Path
import ssl
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from f0_l2_d1_tls_phases import (_exercise_tls_post_with_mock,
                                 _validate_offline_tls_frame,send_live)
from f0_l2_d1_https import HOST, PORT


def request():
    return {"jsonrpc":"2.0","id":2,"method":"eth_blockNumber","params":[]}


class MemoryResponse:
    def __init__(self, status=200, headers=None, raw=None):
        self.status=status
        self.headers=([("content-type","application/json")] if headers is None
                      else headers)
        self.raw=(b'{"jsonrpc":"2.0","id":2,"result":"0x38"}'
                  if raw is None else raw)
        self.read_sizes=[]
    def getheaders(self):
        return self.headers
    def read(self,n):
        self.read_sizes.append(n)
        return self.raw[:n]


class FakeTLSSocket:
    def __init__(self, reply=None, *, fail_connect=False, fail_post=False):
        self.reply=reply or MemoryResponse()
        self.fail_connect=fail_connect
        self.fail_post=fail_post
        self.actions=[]
        self.sock=None
        self.closed=False
    def connect(self):
        self.actions.append("connect")
        if self.fail_connect:
            raise OSError("TEST_CONNECT_FAILURE")
        self.sock=object()
    def request(self,verb,path,*,body,headers):
        self.actions.append("request")
        if self.fail_post:
            raise TimeoutError("TEST_SOCKET_WRITE_UNKNOWN")
        if verb!="POST" or path!="/" or headers["Host"]!=HOST:
            raise AssertionError("BAD_POST")
        if headers["Accept-Encoding"]!="identity":
            raise AssertionError("COMPRESSED_POST")
        if json.loads(body)!=request():
            raise AssertionError("BODY_CHANGED")
    def getresponse(self):
        self.actions.append("getresponse")
        return self.reply
    def close(self):
        self.actions.append("close")
        self.closed=True
        self.sock=None


class D1TLSPhaseTests(unittest.TestCase):
    def invoke(self,session=None,guard=None,**kwargs):
        self.conn=session if session is not None else FakeTLSSocket()
        self.observed=[]
        def factory(host,*,port,timeout,context):
            self.assertEqual((host,port),(HOST,PORT))
            self.assertTrue(0<timeout<=5)
            self.assertTrue(context.check_hostname)
            self.assertEqual(context.verify_mode,ssl.CERT_REQUIRED)
            self.observed.append("factory")
            return self.conn
        def prepost(payload):
            self.observed.append("prepost")
            self.assertEqual(self.conn.actions,["connect"])
            if guard is not None:
                return guard(payload)
        with patch("http.client.HTTPSConnection",
                   side_effect=AssertionError("REAL_SOCKET_FORBIDDEN")):
            outcome=_exercise_tls_post_with_mock(
                request(),factory,prepost,**kwargs)
        return outcome

    def test_connect_then_gate_then_exactly_one_post_and_raw_frame(self):
        result=self.invoke()
        self.assertEqual(result["state"],"FRAME")
        self.assertEqual(self.observed,["factory","prepost"])
        self.assertEqual(self.conn.actions,
                         ["connect","request","getresponse","close"])
        self.assertTrue(self.conn.closed)
        self.assertTrue(result["connect_attempted"])
        self.assertTrue(result["post_attempted_or_unknown"])
        self.assertIsNotNone(result["connected_at_monotonic"])
        self.assertGreaterEqual(result["post_attempted_at_monotonic"],
                                result["connected_at_monotonic"])
        self.assertEqual(
            _validate_offline_tls_frame(result,request())["id"],2)
        self.assertFalse(result["retry_allowed"])
        self.assertFalse(result["live_authorized"])
        self.assertEqual(result["network_provenance"],
                         "UNVERIFIED_INJECTED_FAKE_FACTORY")

    def test_signed_window_gate_denial_after_tls_has_no_http_post(self):
        def denied(_):
            raise ValueError("EXPIRED_UTC_TEST")
        result=self.invoke(guard=denied)
        self.assertEqual(result["state"],"FAILED")
        self.assertEqual(result["failure"],"D1_TLS_POST_GATE_DENIED")
        self.assertEqual(self.conn.actions,["connect","close"])
        self.assertIsNotNone(result["connected_at_monotonic"])
        self.assertIsNone(result["post_attempted_at_monotonic"])
        self.assertFalse(result["post_attempted_or_unknown"])
        with self.assertRaisesRegex(ValueError,"NO_VALID_FRAME"):
            _validate_offline_tls_frame(result,request())

    def test_tls_connect_failure_keeps_network_start_uncertain_and_no_post(self):
        result=self.invoke(FakeTLSSocket(fail_connect=True))
        self.assertEqual(result["state"],"FAILED")
        self.assertEqual(result["stage"],"CONNECT_ATTEMPTED")
        self.assertTrue(result["connect_attempted"])
        self.assertFalse(result["post_attempted_or_unknown"])
        self.assertEqual(self.conn.actions,["connect","close"])
        self.assertFalse(result["retry_allowed"])

    def test_post_write_timeout_never_retries_or_falsely_settles(self):
        result=self.invoke(FakeTLSSocket(fail_post=True))
        self.assertEqual(result["state"],"FAILED")
        self.assertEqual(result["stage"],"POST_ATTEMPTED")
        self.assertTrue(result["post_attempted_or_unknown"])
        self.assertIsNone(result["frame"])
        self.assertEqual(self.conn.actions,["connect","request","close"])
        self.assertFalse(result["retry_allowed"])

    def test_503_raw_kept_with_no_automatic_retry(self):
        resp=MemoryResponse(status=503,raw=b'{"error":"rate limit"}')
        result=self.invoke(FakeTLSSocket(reply=resp))
        self.assertEqual(result["frame"][0],503)
        self.assertEqual(result["frame"][2],b'{"error":"rate limit"}')
        self.assertEqual(self.conn.actions.count("request"),1)
        with self.assertRaisesRegex(ValueError,"HTTP_STATUS_NOT_OK"):
            _validate_offline_tls_frame(result,request())

    def test_redirect_and_compression_fail_closed(self):
        for reply in (
            MemoryResponse(status=302,headers=[("location","https://evil.invalid")]),
            MemoryResponse(headers=[("content-encoding","gzip")]),
        ):
            with self.subTest(status=reply.status,headers=reply.headers):
                result=self.invoke(FakeTLSSocket(reply=reply))
                self.assertEqual(result["state"],"FAILED")
                self.assertIsNone(result["frame"])
                self.assertTrue(self.conn.closed)
                self.assertFalse(result["retry_allowed"])

    def test_response_limit_and_no_default_socket(self):
        big=MemoryResponse(raw=b"x"*128)
        result=self.invoke(FakeTLSSocket(reply=big),response_limit=64)
        self.assertEqual(big.read_sizes,[65])
        self.assertEqual(result["failure"],"D1_TLS_PHASE_RESPONSE_TOO_LARGE")
        self.assertTrue(self.conn.closed)
        with self.assertRaisesRegex(ValueError,"CONFIG_INVALID"):
            self.invoke(timeout_s=10)
        with self.assertRaisesRegex(ValueError,"CONFIG_INVALID"):
            self.invoke(response_limit=2_000_001)
        with self.assertRaisesRegex(ValueError,"D1_REAL_TLS_SENDER_DISABLED"):
            send_live(request())


if __name__=="__main__":
    unittest.main()
