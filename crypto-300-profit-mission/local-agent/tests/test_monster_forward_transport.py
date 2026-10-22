"""Offline transport regressions: in-memory responses and 127.0.0.1 only.

No public RPC, credentials, chain sampling, services or background observers.
The loopback server exists only for a test and is shut down before it returns.
"""
import contextlib
from email.message import Message
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import signal
import threading
import time
import unittest
from unittest import mock

from mission_agent.early import forward_observation as m


ENDPOINT = "https://offline.invalid/rpc"


def envelope(request_id=1, **extra):
    value = {"jsonrpc": "2.0", "id": request_id, "result": "0x38"}
    value.update(extra)
    return json.dumps(value, separators=(",", ":")).encode()


class MemoryResponse:
    def __init__(self, body, headers=None):
        self.status = 200
        self.body = body
        self.headers = Message()
        for key, value in headers or [("Content-Length", str(len(body)))]:
            self.headers.add_header(key, value)

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def read(self, size):
        return self.body[:size]


@contextlib.contextmanager
def loopback_server(*, body=None, length_delta=0, duplicate_length=False,
                    delay_per_byte=0, redirect=False):
    """Exercise urllib's real response reader without reaching an external host."""
    seen = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            seen.append(self.path)
            request = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            data = envelope(request["id"]) if body is None else body
            if redirect:
                self.send_response(302)
                self.send_header("Location", base + "/redirect-target")
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            self.send_response(200)
            self.send_header("Content-Length", str(len(data) + length_delta))
            if duplicate_length:
                self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            try:
                if delay_per_byte:
                    for byte in data:
                        self.wfile.write(bytes([byte]))
                        self.wfile.flush()
                        time.sleep(delay_per_byte)
                else:
                    self.wfile.write(data)
                    self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                pass
            self.close_connection = True

        def do_GET(self):
            seen.append(self.path)
            self.send_response(200)
            self.send_header("Content-Length", "0")
            self.end_headers()

        def log_message(self, *_):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    base = "http://127.0.0.1:" + str(server.server_address[1])
    thread = threading.Thread(target=lambda: server.serve_forever(poll_interval=0.01),
                              daemon=True)
    thread.start()
    rpc = m.ForwardRPC(ENDPOINT, min_interval=0, max_requests=m.MAX_CALLS)
    # Constructor production HTTPS validation remains unchanged. Tests replace
    # only this instance's URL with their own local HTTP server.
    rpc.url = base + "/rpc"
    try:
        yield rpc, seen
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=1)


class ForwardTransportTests(unittest.TestCase):
    def rpc_for(self, body=None, headers=None, endpoint=ENDPOINT):
        opener = mock.Mock()
        opener.open.return_value = MemoryResponse(body or envelope(), headers)
        rpc = m.ForwardRPC(endpoint, min_interval=0, max_requests=m.MAX_CALLS,
                           opener=opener)
        return rpc, opener

    def assert_rejected(self, rpc, code):
        with self.assertRaisesRegex(m.ForwardProbeError, code):
            rpc.request("eth_chainId", [])

    def test_success_preserves_raw_body_and_uses_post(self):
        raw = envelope()
        rpc, opener = self.rpc_for(raw)
        result, actual = rpc.request("eth_chainId", [])
        self.assertEqual(result, "0x38")
        self.assertEqual(actual, raw)
        request = opener.open.call_args.args[0]
        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(json.loads(request.data)["method"], "eth_chainId")

    def test_slow_drip_exceeds_total_deadline_despite_frequent_socket_data(self):
        with loopback_server(delay_per_byte=0.02) as (rpc, _):
            with mock.patch.object(m, "REQUEST_TIMEOUT_SECONDS", 0.12):
                start = time.monotonic()
                self.assert_rejected(rpc, "RPC_TOTAL_DEADLINE_EXCEEDED")
                self.assertLess(time.monotonic() - start, 0.8)
        self.assertEqual(signal.getitimer(signal.ITIMER_REAL), (0.0, 0.0))

    def test_complete_json_inside_truncated_http_response_is_rejected(self):
        with loopback_server(length_delta=100) as (rpc, seen):
            self.assert_rejected(rpc, "RPC_HTTP_BODY_TRUNCATED")
            self.assertEqual(seen, ["/rpc"])

    def test_duplicate_content_length_is_rejected(self):
        with loopback_server(duplicate_length=True) as (rpc, _):
            self.assert_rejected(rpc, "RPC_HTTP_FRAMING_INVALID")

    def test_invalid_or_oversize_declared_content_length_is_rejected(self):
        for length in ("-1", "invalid", str(m.MAX_RESPONSE_BYTES + 1)):
            with self.subTest(length=length):
                rpc, _ = self.rpc_for(headers=[("Content-Length", length)])
                self.assert_rejected(rpc, "RPC_HTTP_FRAMING_INVALID")

    def test_content_length_with_transfer_encoding_is_rejected(self):
        rpc, _ = self.rpc_for(headers=[("Content-Length", str(len(envelope()))),
                                      ("Transfer-Encoding", "chunked")])
        self.assert_rejected(rpc, "RPC_HTTP_FRAMING_INVALID")

    def test_actual_body_size_cap_is_enforced_without_content_length(self):
        rpc, _ = self.rpc_for(body=b"x" * (m.MAX_RESPONSE_BYTES + 1),
                             headers=[("Content-Type", "application/json")])
        self.assert_rejected(rpc, "RPC_RESPONSE_TOO_LARGE")

    def test_redirect_is_rejected_without_followup_request(self):
        with loopback_server(redirect=True) as (rpc, seen):
            self.assert_rejected(rpc, "RPC_HTTP_302")
            self.assertEqual(seen, ["/rpc"])

    def test_query_key_echo_is_rejected_in_plain_or_unicode_escaped_json(self):
        key = "offline-demo-query-key"
        endpoint = ENDPOINT + "?apikey=" + key
        raw_plain = envelope(diagnostic=key)
        escaped = "".join("\\u%04x" % ord(char) for char in key)
        raw_escaped = ('{"jsonrpc":"2.0","id":1,"result":"0x38",'
                       '"diagnostic":"' + escaped + '"}').encode()
        for raw in (raw_plain, raw_escaped):
            with self.subTest(escaped=raw == raw_escaped):
                rpc, _ = self.rpc_for(raw, endpoint=endpoint)
                self.assert_rejected(rpc, "RPC_SECRET_ECHO_REJECTED")

    def test_path_secret_echo_is_rejected_in_plain_or_unicode_escaped_json(self):
        key = "offline-demo-path-key"
        endpoint = ENDPOINT + "/" + key
        escaped = "".join("\\u%04x" % ord(char) for char in key)
        for raw in (envelope(diagnostic=key),
                    ('{"jsonrpc":"2.0","id":1,"result":"0x38",'
                     '"diagnostic":"' + escaped + '"}').encode()):
            with self.subTest(raw_length=len(raw)):
                rpc, _ = self.rpc_for(raw, endpoint=endpoint)
                self.assert_rejected(rpc, "RPC_SECRET_ECHO_REJECTED")

    def test_entire_endpoint_echo_is_rejected(self):
        endpoint = ENDPOINT + "?apikey=offline-demo-query-key"
        rpc, _ = self.rpc_for(envelope(diagnostic=endpoint), endpoint=endpoint)
        self.assert_rejected(rpc, "RPC_SECRET_ECHO_REJECTED")

    def test_non_readonly_methods_never_reach_opener_or_consume_budget(self):
        for method in ("eth_sendRawTransaction", "eth_sendTransaction",
                       "personal_sign", "eth_sign", "wallet_sendCalls"):
            with self.subTest(method=method):
                rpc, opener = self.rpc_for()
                with self.assertRaisesRegex(m.ForwardProbeError, "DISALLOWED_RPC_METHOD"):
                    rpc.request(method, [])
                opener.open.assert_not_called()
                self.assertEqual(rpc.calls, 0)

    def test_twenty_requests_are_allowed_and_twenty_first_never_opens(self):
        rpc, opener = self.rpc_for()
        opener.open.side_effect = lambda request, **_: MemoryResponse(
            envelope(json.loads(request.data)["id"]))
        for _ in range(20):
            self.assertEqual(rpc.request("eth_chainId", [])[0], "0x38")
        self.assert_rejected(rpc, "RPC_CALL_LIMIT")
        self.assertEqual(opener.open.call_count, 20)
        self.assertEqual(rpc.calls, 20)

    def test_invalid_envelopes_cannot_be_successful_responses(self):
        invalid = [[], {"id": 1, "result": "0x38"},
                   {"jsonrpc": "1.0", "id": 1, "result": "0x38"},
                   {"jsonrpc": "2.0", "id": True, "result": "0x38"},
                   {"jsonrpc": "2.0", "id": 2, "result": "0x38"},
                   {"jsonrpc": "2.0", "id": 1},
                   {"jsonrpc": "2.0", "id": 1, "result": "0x38", "error": None}]
        for value in invalid:
            with self.subTest(value=value):
                rpc, _ = self.rpc_for(json.dumps(value).encode())
                self.assert_rejected(rpc, "RPC_ENVELOPE_INVALID")

    def test_malformed_json_is_rejected_with_safe_code(self):
        rpc, _ = self.rpc_for(b"not JSON")
        self.assert_rejected(rpc, "RPC_INVALID_JSON")

    def test_prior_alarm_handler_is_restored_on_success_and_failure(self):
        original = signal.getsignal(signal.SIGALRM)
        sentinel = lambda *_: None
        signal.signal(signal.SIGALRM, sentinel)
        try:
            for raw in (envelope(), b"not JSON"):
                rpc, _ = self.rpc_for(raw)
                if raw == envelope():
                    rpc.request("eth_chainId", [])
                else:
                    self.assert_rejected(rpc, "RPC_INVALID_JSON")
                self.assertIs(signal.getsignal(signal.SIGALRM), sentinel)
                self.assertEqual(signal.getitimer(signal.ITIMER_REAL), (0.0, 0.0))
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, original)

    def test_existing_alarm_is_preserved_and_request_is_refused(self):
        original = signal.getsignal(signal.SIGALRM)
        sentinel = lambda *_: None
        signal.signal(signal.SIGALRM, sentinel)
        signal.setitimer(signal.ITIMER_REAL, 10)
        try:
            rpc, opener = self.rpc_for()
            self.assert_rejected(rpc, "FOREGROUND_WITHOUT_EXISTING_ALARM_REQUIRED")
            self.assertIs(signal.getsignal(signal.SIGALRM), sentinel)
            remaining, interval = signal.getitimer(signal.ITIMER_REAL)
            self.assertGreater(remaining, 9)
            self.assertEqual(interval, 0)
            opener.open.assert_not_called()
            self.assertEqual(rpc.calls, 0)
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, original)

    def test_nonmain_thread_cannot_open_or_install_alarm(self):
        rpc, opener = self.rpc_for()
        errors = []

        def invoke():
            try:
                rpc.request("eth_chainId", [])
            except Exception as exc:
                errors.append(exc)

        thread = threading.Thread(target=invoke)
        thread.start()
        thread.join(timeout=1)
        self.assertFalse(thread.is_alive())
        self.assertEqual(len(errors), 1)
        self.assertIsInstance(errors[0], m.ForwardProbeError)
        self.assertEqual(str(errors[0]), "FOREGROUND_WITHOUT_EXISTING_ALARM_REQUIRED")
        opener.open.assert_not_called()
        self.assertEqual(rpc.calls, 0)
        self.assertEqual(signal.getitimer(signal.ITIMER_REAL), (0.0, 0.0))


if __name__ == "__main__":
    unittest.main()
