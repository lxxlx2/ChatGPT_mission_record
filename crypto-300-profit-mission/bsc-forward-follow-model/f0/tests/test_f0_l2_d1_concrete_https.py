"""D1 review actual HTTPSConnection source with ALL network constructors patched."""
import hashlib
import json
import ssl
import sys
from pathlib import Path
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from f0_l2_d1_concrete_https import (
    _review_concrete_https_once, _parse_review_frame_offline, send_live)
from f0_l2_d1_https import HOST, PORT


def rpc():
    return {"jsonrpc":"2.0","id":11,"method":"eth_blockNumber","params":[]}


class MemoryResponse:
    def __init__(self, status=200, headers=None, data=None):
        self.status=status
        self.headers=[("content-type","application/json")] if headers is None else headers
        self.data=(b'{"jsonrpc":"2.0","id":11,"result":"0x38"}'
                   if data is None else data)
        self.read_sizes=[]
    def getheaders(self):
        return self.headers
    def read(self, size):
        self.read_sizes.append(size)
        return self.data[:size]


class MockHTTPS:
    def __init__(self, response=None, *, fail_connect=False,
                 fail_post=False, fail_read=False):
        self.response=response if response is not None else MemoryResponse()
        self.fail_connect=fail_connect
        self.fail_post=fail_post
        self.fail_read=fail_read
        self.sock=None
        self.events=[]
    def connect(self):
        self.events.append("connect")
        if self.fail_connect:
            raise TimeoutError("TEST_CONNECT_TIMEOUT")
        self.sock=object()
    def request(self, method, path, *, body, headers):
        self.events.append("request")
        if self.fail_post:
            raise TimeoutError("TEST_SENDALL_UNKNOWN")
        if (method, path, headers["Host"]) != ("POST","/",HOST):
            raise AssertionError("BAD_FIXED_DESTINATION")
        if headers["Accept-Encoding"]!="identity" or "Authorization" in headers:
            raise AssertionError("UNEXPECTED_HEADERS")
        if json.loads(body)!=rpc():
            raise AssertionError("BAD_REQUEST_BODY")
    def getresponse(self):
        self.events.append("getresponse")
        if self.fail_read:
            raise TimeoutError("TEST_READ_TIMEOUT")
        return self.response
    def close(self):
        self.events.append("close")
        self.sock=None


class D1ConcreteHTTPSReviewTests(unittest.TestCase):
    def run_review(self, conn=None, guard=None, **opts):
        self.session=MockHTTPS() if conn is None else conn
        self.calls=[]
        def new_connection(host, *, port, timeout, context):
            self.calls.append("constructor")
            self.assertEqual((host,port),(HOST,PORT))
            self.assertGreater(timeout,0)
            self.assertLessEqual(timeout,5)
            self.assertEqual(context.verify_mode,ssl.CERT_REQUIRED)
            self.assertTrue(context.check_hostname)
            return self.session
        def prepost(payload):
            self.calls.append("guard")
            self.assertEqual(payload, rpc())
            self.assertEqual(self.session.events,["connect"])
            if guard is not None:
                guard(payload)
        with patch("http.client.HTTPSConnection",side_effect=new_connection) as ctor:
            result=_review_concrete_https_once(
                rpc(),final_post_guard=prepost,**opts)
        self.assertEqual(ctor.call_count,1)
        return result

    def test_fixed_host_verified_tls_guard_then_one_post_and_close(self):
        out=self.run_review()
        self.assertEqual(self.calls,["constructor","guard"])
        self.assertEqual(self.session.events,
                         ["connect","request","getresponse","close"])
        self.assertEqual(out["state"],"RAW")
        self.assertEqual(out["raw_frame"][0],200)
        self.assertEqual(_parse_review_frame_offline(out,rpc())["result"],"0x38")
        self.assertIsNotNone(out["connect_attempted_at"])
        self.assertGreaterEqual(out["post_attempted_at"],
                                out["connected_at"])
        self.assertFalse(out["physical_socket_send_time_proven"])
        self.assertFalse(out["retry_allowed"])
        self.assertEqual(out["production"],"NO_GO")

    def test_live_entry_denied_before_any_http_constructor(self):
        with patch("http.client.HTTPSConnection",
                   side_effect=AssertionError("NETWORK_FORBIDDEN")) as ctor:
            with self.assertRaisesRegex(ValueError,
                                        "LIVE_DISABLED_REQUIRES_D2"):
                send_live(rpc())
            ctor.assert_not_called()

    def test_final_guard_denial_after_tls_never_calls_post(self):
        def deny(_):
            raise ValueError("TEST_UTC_EXPIRED")
        out=self.run_review(guard=deny)
        self.assertEqual(out["state"],"FAILED")
        self.assertEqual(out["failure"],
                         "D1_CONCRETE_HTTP_PREPOST_GUARD_DENIED")
        self.assertEqual(self.session.events,["connect","close"])
        self.assertIsNone(out["post_attempted_at"])
        self.assertIsNotNone(out["connect_attempted_at"])
        with self.assertRaisesRegex(ValueError,"NOT_SUCCESSFUL_FRAME"):
            _parse_review_frame_offline(out,rpc())

    def test_tls_connect_timeout_retains_connection_attempt_no_retry(self):
        out=self.run_review(MockHTTPS(fail_connect=True))
        self.assertEqual(out["phase"],"CONNECT_ATTEMPTED")
        self.assertIsNotNone(out["connect_attempted_at"])
        self.assertIsNone(out["post_attempted_at"])
        self.assertEqual(self.session.events,["connect","close"])
        self.assertFalse(out["retry_allowed"])

    def test_post_write_or_read_timeout_is_uncertain_never_retry(self):
        for attrs, events in (
            ({"fail_post":True},["connect","request","close"]),
            ({"fail_read":True},["connect","request","getresponse","close"]),
        ):
            with self.subTest(attrs=attrs):
                out=self.run_review(MockHTTPS(**attrs))
                self.assertEqual(out["state"],"FAILED")
                self.assertEqual(out["phase"],"POST_ATTEMPTED")
                self.assertIsNotNone(out["post_attempted_at"])
                self.assertEqual(self.session.events,events)
                self.assertFalse(out["retry_allowed"])
                self.assertIsNone(out["raw_frame"])

    def test_http_503_raw_is_preserved_not_parsed_as_success(self):
        response=MemoryResponse(503,data=b'{"error":"rate limit"}')
        out=self.run_review(MockHTTPS(response))
        self.assertEqual(out["state"],"RAW")
        self.assertEqual(out["raw_frame"][0],503)
        self.assertEqual(out["raw_frame"][2],b'{"error":"rate limit"}')
        with self.assertRaisesRegex(ValueError,"HTTP_STATUS_NOT_OK"):
            _parse_review_frame_offline(out,rpc())
        self.assertEqual(self.session.events.count("request"),1)

    def test_redirect_compression_and_duplicate_headers_fail_closed(self):
        cases=[
            (MemoryResponse(302,headers=[("location","https://evil.invalid")]),
             "REDIRECT_REFUSED"),
            (MemoryResponse(headers=[("content-encoding","gzip")]),
             "COMPRESSED_REFUSED"),
            (MemoryResponse(headers=[("content-type","application/json"),
                                     ("CONTENT-TYPE","text/plain")]),
             "DUPLICATE_HEADER"),
        ]
        for response,error in cases:
            with self.subTest(error=error):
                out=self.run_review(MockHTTPS(response))
                self.assertEqual(out["state"],"FAILED")
                self.assertIn(error,out["failure"])
                self.assertEqual(self.session.events[-1],"close")
                self.assertFalse(out["retry_allowed"])

    def test_response_bound_and_invalid_limits_fail_closed(self):
        response=MemoryResponse(data=b"x"*130)
        out=self.run_review(MockHTTPS(response),max_bytes=64)
        self.assertEqual(response.read_sizes,[65])
        self.assertEqual(out["state"],"FAILED")
        self.assertEqual(out["failure"],
                         "D1_CONCRETE_HTTP_OVERSIZED_OR_INVALID_RAW")
        self.assertEqual(out["raw_prefix_sha256"],
                         hashlib.sha256(b"x"*65).hexdigest())
        self.assertIsNone(out["raw_frame"])
        with self.assertRaisesRegex(ValueError,"CONFIG_INVALID"):
            _review_concrete_https_once(rpc(),
                final_post_guard=lambda _:None, timeout_s=8)
        with self.assertRaisesRegex(ValueError,"CONFIG_INVALID"):
            _review_concrete_https_once(rpc(),
                final_post_guard=lambda _:None, max_bytes=2_000_001)

    def test_tls_certificate_verification_must_be_enabled(self):
        class InsecureContext:
            check_hostname=False
            verify_mode=ssl.CERT_NONE
        with patch("ssl.create_default_context",return_value=InsecureContext()):
            with patch("http.client.HTTPSConnection",
                       side_effect=AssertionError("NO_NETWORK")) as ctor:
                with self.assertRaisesRegex(ValueError,"TLS_VERIFY_REQUIRED"):
                    _review_concrete_https_once(
                        rpc(),final_post_guard=lambda _:None)
                ctor.assert_not_called()

if __name__=="__main__":
    unittest.main()
