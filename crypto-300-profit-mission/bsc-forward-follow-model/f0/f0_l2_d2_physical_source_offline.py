"""D2 code-only physical HTTPS source slot, constructible but NEVER live.

Unlike FakeSource, this exact slot has no synthetic reply generator and no
caller-supplied host or transport factory. It uses the existing, reviewed
stdlib HTTPSConnection code when ALL network constructors are substituted
by a test fixture. With the genuine constructor installed, it denies before
TLS construction. A later audited release needs separate real D2/D3 human
identity, OS-user-fixed grant consumption and a fresh source review.
"""
from __future__ import annotations

import http.client

from f0_l1_http_wire import MAX_BODY_BYTES
from f0_l2_d1_concrete_https import (
    _ORIGINAL_HTTPS_CONNECTION, _REVIEW_TEST_ONLY_CAPABILITY,
    _review_concrete_https_once,
)

class StagedPhysicalHTTPSReadOnlySource:
    """Exact zero-field offline source; not FakeSource or a production grant."""
    __slots__ = ()

    def reply_transport_evidence_offline(
            self, request, begin_offline_post, timeout_s,
            *, reservation_guard=None):
        if type(self) is not StagedPhysicalHTTPSReadOnlySource:
            raise ValueError("D2_STAGED_SOURCE_EXACT_TYPE_REQUIRED")
        # This is a *test-only* code path; no real TLS constructor allowed.
        # Check before the existing transport's TLS context/constructor.
        if http.client.HTTPSConnection is _ORIGINAL_HTTPS_CONNECTION:
            raise ValueError("D2_STAGED_SOURCE_REAL_NETWORK_FORBIDDEN")
        if not callable(reservation_guard) or not callable(begin_offline_post):
            raise ValueError("D2_STAGED_SOURCE_COORDINATOR_PROOF_REQUIRED")
        denied = [None]

        def pre_connect(payload):
            if payload != request:
                raise ValueError("D2_STAGED_SOURCE_RESERVED_PAYLOAD_MISMATCH")
            reservation_guard(payload)

        def pre_post(payload):
            if payload != request:
                raise ValueError("D2_STAGED_SOURCE_POST_PAYLOAD_MISMATCH")
            try:
                begin_offline_post()
            except Exception as exc:
                denied[0] = exc
                raise

        result = _review_concrete_https_once(
            request, final_post_guard=pre_post,
            pre_connect_guard=pre_connect,
            _test_capability=_REVIEW_TEST_ONLY_CAPABILITY,
            timeout_s=timeout_s, max_bytes=MAX_BODY_BYTES)
        if denied[0] is not None:
            raise denied[0]
        raw = result["raw_frame"]
        if result["state"] == "RAW":
            if raw is None:
                raise ValueError("D2_STAGED_SOURCE_SUCCESS_MISSING_RAW")
            return {"state": "RAW", "frame": raw, "failure": None}
        if raw is not None:
            return {"state": "REJECTED_RAW", "frame": raw,
                    "failure": result["failure"]}
        return {"state": "FAILED_NO_RAW", "frame": None,
                "failure": result["failure"]}


def send_live(*_args, **_kwargs):
    raise ValueError("D2_STAGED_PHYSICAL_SOURCE_NOT_RELEASED_D2_D3_REQUIRED")
