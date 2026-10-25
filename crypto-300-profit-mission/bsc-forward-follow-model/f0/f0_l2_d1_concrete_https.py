#!/usr/bin/env python3
"""D1 concrete HTTPS client code for OFFLINE injected-socket review only.

There is intentionally NO public network-capable entrypoint. send_live()
always denies, and this private review function is NOT a production grant
gate. Tests replace http.client.HTTPSConnection before every invocation.
A later D2 review must bind the concrete sender to a trustworthy fixed
runtime, audited identity, permanently consumed grant and global scheduler.
"""
from __future__ import annotations

import hashlib
import json
import http.client
import ssl
import time

from f0_l1_http_wire import MAX_BODY_BYTES, json_body, parse_http_response, valid_rpc_payload
from f0_l2_d1_coordinator import FakeSource
from f0_l2_d1_https import HOST, PORT

MAX_REQUEST_BYTES = 2000
# Bound response metadata as well as the already bounded response body. The
# complete raw header list is collected by http.client; never trust metadata
# size or announced body length without explicit validation.
MAX_RESPONSE_HEADERS = 40
MAX_RESPONSE_HEADER_BYTES = 8192

# Private module-local test barrier. NOT cryptographic or production auth.
_REVIEW_TEST_ONLY_CAPABILITY = object()


def send_live(*_args, **_kwargs):
    raise ValueError("D1_CONCRETE_HTTPS_LIVE_DISABLED_REQUIRES_D2")


def _review_concrete_https_once(request, *, final_post_guard,
                                pre_connect_guard=None,
                                _test_capability=None, timeout_s=5.0,
                                max_bytes=MAX_BODY_BYTES,
                                _sealed_offline_factory=None):
    """Review concrete connection lifecycle with constructor PATCHED in tests.

    This PRIVATE primitive, like any low-level network library, is callable by
    arbitrary Python code. It is NOT an authorization mechanism and must NOT
    be invoked with a real constructor while D2 is blocked.

    TLS connect can already send packets BEFORE final_post_guard. A
    post_attempted_at timestamp is the Python conn.request() call boundary,
    NOT proven physical HTTPS byte emission. All attempted POSTs are
    irrevocably uncertain on write/read exceptions and NEVER retryable.
    """
    if _test_capability is not _REVIEW_TEST_ONLY_CAPABILITY:
        raise ValueError("D1_CONCRETE_HTTP_REVIEW_CAPABILITY_REQUIRED")
    if (_sealed_offline_factory is not None and
            type(_sealed_offline_factory) is not _SealedMemoryTLSFactory):
        raise ValueError("D1_CONCRETE_HTTP_UNREVIEWED_FACTORY")
    if (not callable(final_post_guard) or
            (pre_connect_guard is not None and not callable(pre_connect_guard)) or
            type(timeout_s) not in (int, float) or isinstance(timeout_s, bool) or
            not 0 < timeout_s <= 5 or type(max_bytes) is not int or
            not 0 < max_bytes <= MAX_BODY_BYTES):
        raise ValueError("D1_CONCRETE_HTTP_CONFIG_INVALID")
    body = json_body(request)
    if len(body) > MAX_REQUEST_BYTES:
        raise ValueError("D1_CONCRETE_HTTP_BODY_TOO_LARGE")

    context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    if not context.check_hostname or context.verify_mode != ssl.CERT_REQUIRED:
        raise ValueError("D1_CONCRETE_HTTP_TLS_VERIFY_REQUIRED")

    conn = None
    phase = "BEFORE_CONNECT"
    connect_attempted_at = None
    connected_at = None
    post_attempted_at = None
    completed_at = None
    raw_frame = None
    failure = None
    raw_prefix_sha256 = None
    try:
        phase = "PRECONNECT_RESERVATION_GUARD"
        if pre_connect_guard is not None:
            pre_connect_guard(request)
        # The ONLY concrete constructor. No URL, arbitrary host, proxy,
        # tunnel, credential, environment-based routing or HTTP redirect.
        ctor = (http.client.HTTPSConnection if _sealed_offline_factory is None
                else _sealed_offline_factory)
        conn = ctor(HOST, port=PORT, timeout=float(timeout_s), context=context)
        # One-coordinator proof is generated only after pre-send journal fsync.
        # In production the reviewed release must also bind the one-use marker
        # and exact D2/D3 user permission *before this constructor*.
        phase = "CONNECT_ATTEMPTED"
        connect_attempted_at = time.monotonic()
        conn.connect()
        if getattr(conn, "sock", None) is None:
            raise ValueError("D1_CONCRETE_HTTP_NO_TLS_SOCKET")
        connected_at = time.monotonic()
        phase = "CONNECTED"
        # A true production guard must be immutable, independently
        # authenticated and shared with the coordinator. D1 lacks it.
        final_post_guard(request)
        post_attempted_at = time.monotonic()
        phase = "POST_ATTEMPTED"
        conn.request("POST", "/", body=body, headers={
            "Host": HOST,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Accept-Encoding": "identity",
            "Connection": "close",
        })
        response = conn.getresponse()
        status = response.status
        hdrs = response.getheaders()
        if (type(status) is not int or status < 100 or status > 599
                or type(hdrs) is not list
                or not all(type(k) is str and type(v) is str for k, v in hdrs)):
            raise ValueError("D1_CONCRETE_HTTP_RESPONSE_METADATA_INVALID")
        if (len(hdrs) > MAX_RESPONSE_HEADERS or
                any(not k or any(ord(ch) < 33 or ord(ch) > 126
                                 or ch == ":" for ch in k)
                    or any(ord(ch) < 32 and ch != "\t" or ord(ch) == 127
                           for ch in v) for k, v in hdrs) or
                sum(len(k.encode("utf-8")) + len(v.encode("utf-8")) + 4
                    for k, v in hdrs) > MAX_RESPONSE_HEADER_BYTES):
            raise ValueError("D1_CONCRETE_HTTP_HEADERS_NOT_BOUNDED")
        header_names = [name.lower() for name, _ in hdrs]
        if len(header_names) != len(set(header_names)):
            raise ValueError("D1_CONCRETE_HTTP_DUPLICATE_HEADER")
        headers = {name.lower(): value for name, value in hdrs}
        content_length = headers.get("content-length")
        if content_length is not None:
            if (not content_length.isascii()
                    or not content_length.isdecimal()
                    or len(content_length) > 7
                    or int(content_length) > max_bytes):
                # Declared oversize/malformed payload is never read or
                # fabricated into a complete RAW response.
                raise ValueError("D1_CONCRETE_HTTP_LENGTH_DECLARATION_INVALID")
        # Status 503 or 302 must preserve the RAW frame for audit, but
        # parsing a successful RPC is a SEPARATE later decision.
        data = response.read(max_bytes + 1)
        completed_at = time.monotonic()
        if type(data) is not bytes or len(data) > max_bytes:
            if type(data) is bytes:
                raw_prefix_sha256 = hashlib.sha256(data).hexdigest()
            raise ValueError("D1_CONCRETE_HTTP_OVERSIZED_OR_INVALID_RAW")
        if content_length is not None and len(data) != int(content_length):
            # A short response or inconsistent declared length cannot be
            # archived as if it were a complete, authenticated RPC frame.
            raw_prefix_sha256 = hashlib.sha256(data).hexdigest()
            raise ValueError("D1_CONCRETE_HTTP_BODY_LENGTH_MISMATCH")
        raw_frame = (status, headers, data)
        phase = "RAW_RECEIVED"
        if 300 <= status < 400:
            failure = "D1_CONCRETE_HTTP_REDIRECT_REFUSED"
        elif headers.get("content-encoding", "identity").lower() != "identity":
            failure = "D1_CONCRETE_HTTP_COMPRESSED_REFUSED"
        elif "transfer-encoding" in headers:
            # Do not let content transfer/framing transformations silently
            # become RPC success; complete bounded original RAW is retained
            # for FAILED settlement, with no retry or COMMIT.
            failure = "D1_CONCRETE_HTTP_TRANSFER_ENCODING_REFUSED"
    except Exception as exc:
        if phase == "CONNECTED":
            failure = "D1_CONCRETE_HTTP_PREPOST_GUARD_DENIED"
        elif isinstance(exc, ValueError) and str(exc).startswith(
                "D1_CONCRETE_HTTP_"):
            failure = str(exc)
        else:
            failure = "D1_CONCRETE_HTTP_" + phase + "_UNCERTAIN"
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                if failure is None:
                    failure = "D1_CONCRETE_HTTP_CLOSE_UNCERTAIN"

    return {
        "mode": "D1_CONCRETE_SOURCE_CODE_OFFLINE_REVIEW_ONLY",
        "state": "RAW" if failure is None else "FAILED",
        "failure": failure,
        "phase": phase,
        "connect_attempted_at": connect_attempted_at,
        "connected_at": connected_at,
        "post_attempted_at": post_attempted_at,
        "response_completed_at": completed_at,
        "raw_frame": raw_frame,
        "raw_prefix_sha256": raw_prefix_sha256,
        "retry_allowed": False,
        "trusted_prepost_guard": False,
        "trusted_user_or_reviewer": False,
        "real_production_grant_available": False,
        "physical_socket_send_time_proven": False,
        "production": "NO_GO",
    }


def _parse_review_frame_offline(result, request):
    if (type(result) is not dict or result.get("state") != "RAW"
            or result.get("mode") !=
            "D1_CONCRETE_SOURCE_CODE_OFFLINE_REVIEW_ONLY"):
        raise ValueError("D1_CONCRETE_HTTP_NOT_SUCCESSFUL_FRAME")
    return parse_http_response(*result["raw_frame"], request)


class _SealedMemoryTLSFactory:
    """Exact private constructor; no transport callbacks or real sockets."""
    def __init__(self, source):
        if type(source) is not SealedConcreteOfflineSource:
            raise ValueError("D1_REVIEWED_TLS_NOT_SEALED_SOURCE")
        self.source = source

    def __call__(self, host, *, port, timeout, context):
        if (host != HOST or port != PORT or not 0 < timeout <= 5 or
                not context.check_hostname or
                context.verify_mode != ssl.CERT_REQUIRED):
            raise ValueError("D1_REVIEWED_TLS_DESTINATION_MISMATCH")
        source = self.source

        class MemoryResponse:
            def __init__(self, frame):
                self.status, hdr, self.body = frame
                self.headers = list(hdr.items())
            def getheaders(self):
                return self.headers
            def read(self, size):
                return self.body[:size]

        class MemoryTLSConnection:
            def __init__(self):
                self.sock = None
                self.frame = None
                self.closed = False
            def connect(self):
                if self.closed:
                    raise ValueError("D1_REVIEWED_TLS_CLOSED")
                self.sock = object()
            def request(self, method, path, *, body, headers):
                if (self.closed or self.sock is None or self.frame is not None
                        or method != "POST" or path != "/"
                        or headers.get("Host") != HOST
                        or headers.get("Accept-Encoding") != "identity"):
                    raise ValueError("D1_REVIEWED_TLS_REQUEST_SCOPE")
                rpc = json.loads(body)
                valid_rpc_payload(rpc)
                # Call the SAME request bytes only after shared gate permits.
                self.frame = MemoryResponse(FakeSource.reply(source, rpc))
            def getresponse(self):
                if self.frame is None or self.closed:
                    raise ValueError("D1_REVIEWED_TLS_RESPONSE_MISSING")
                return self.frame
            def close(self):
                self.closed = True
                self.sock = None

        return MemoryTLSConnection()


class SealedConcreteOfflineSource(FakeSource):
    """Fixed HTTPSConnection CODE path with an unchangeable memory-only socket.

    This source is allowed into the approved three-slot fake coordinator. It
    does NOT attach live HTTPS or permit the caller to inject a transport.
    """
    def reply_over_memory_https(self, request, begin_fake_post, timeout_s):
        if type(self) is not SealedConcreteOfflineSource:
            raise ValueError("D1_REVIEWED_TLS_SOURCE_NOT_EXACT")
        denial = [None]
        def final_guard(validated_request):
            if validated_request != request:
                raise ValueError("D1_REVIEWED_TLS_REQUEST_CHANGED")
            try:
                begin_fake_post()
            except Exception as exc:
                denial[0] = exc
                raise
        result = _review_concrete_https_once(
            request, final_post_guard=final_guard,
            _test_capability=_REVIEW_TEST_ONLY_CAPABILITY,
            timeout_s=timeout_s, max_bytes=MAX_BODY_BYTES,
            _sealed_offline_factory=_SealedMemoryTLSFactory(self))
        if denial[0] is not None:
            raise denial[0]
        if result["state"] != "RAW" or result["raw_frame"] is None:
            raise ValueError("D1_REVIEWED_TLS_FAILED_NO_AUTO_RETRY")
        return result["raw_frame"]


# This identity comparison blocks accidental direct use of the real constructor
# in the OFFLINE rehearsal. A Python monkeypatch is never a production grant.
_ORIGINAL_HTTPS_CONNECTION = http.client.HTTPSConnection


class PatchedConstructorOfflineSource(FakeSource):
    """Exercise the exact concrete HTTPSConnection call site under a test patch.

    No live entrypoint constructs this class. The original HTTPSConnection is
    forbidden, even if all request constraints happen to look correct. This
    is a constructor-level INTEGRATION TEST, never D2/D3 user authority.
    """

    def reply_transport_evidence_offline(
            self, request, begin_fake_post, timeout_s,
            *, reservation_guard=None):
        """Return bounded RAW even when its HTTP transport is rejected.

        A completed 302/compressed response has actual bytes, but MUST
        NEVER be parsed as a successful RPC or silently discarded.
        This is a mock-only transport result, NOT a live release.
        """
        if type(self) is not PatchedConstructorOfflineSource:
            raise ValueError("D1_PATCHED_CTOR_SOURCE_NOT_EXACT")
        if http.client.HTTPSConnection is _ORIGINAL_HTTPS_CONNECTION:
            raise ValueError("D1_PATCHED_CTOR_REQUIRED_NO_REAL_NETWORK")
        if not callable(reservation_guard):
            raise ValueError("D1_PATCHED_CTOR_COORDINATOR_RESERVATION_REQUIRED")
        denied = [None]

        def pre_connect_check(payload):
            if payload != request:
                raise ValueError("D1_PATCHED_CTOR_PRECONNECT_PAYLOAD_CHANGED")
            reservation_guard(payload)

        def final_post_guard(payload):
            if payload != request:
                raise ValueError("D1_PATCHED_CTOR_PAYLOAD_CHANGED")
            try:
                begin_fake_post()
            except Exception as exc:
                denied[0] = exc
                raise

        result = _review_concrete_https_once(
            request, final_post_guard=final_post_guard,
            pre_connect_guard=pre_connect_check,
            _test_capability=_REVIEW_TEST_ONLY_CAPABILITY,
            timeout_s=timeout_s, max_bytes=MAX_BODY_BYTES)
        if denied[0] is not None:
            # Preserve exact fake POST prestart denial as a denial, not as
            # an HTTP response or an attempted transport failure.
            raise denied[0]
        raw = result["raw_frame"]
        if result["state"] == "RAW":
            if raw is None:
                raise ValueError("D1_PATCHED_CTOR_SUCCESS_MISSING_RAW")
            return {"state": "RAW", "frame": raw, "failure": None}
        if raw is not None:
            return {"state": "REJECTED_RAW", "frame": raw,
                    "failure": result["failure"]}
        return {"state": "FAILED_NO_RAW", "frame": None,
                "failure": result["failure"]}

    def reply_over_memory_https(self, request, begin_fake_post, timeout_s,
                                *, reservation_guard=None):
        """Backwards compatible frame-only test API; never return bad RAW."""
        result = self.reply_transport_evidence_offline(
            request, begin_fake_post, timeout_s,
            reservation_guard=reservation_guard)
        if result["state"] != "RAW":
            raise ValueError("D1_PATCHED_CTOR_FAILED_NO_AUTO_RETRY")
        return result["frame"]
