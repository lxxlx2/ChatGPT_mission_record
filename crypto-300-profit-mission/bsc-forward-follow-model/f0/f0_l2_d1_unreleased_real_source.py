#!/usr/bin/env python3
"""Unreleased fixed HTTPS transport adapter for D1 OFFLINE CODE AUDIT ONLY.

This contains a concrete standard-library HTTPSConnection path. It is NOT a
permissioned entry and must never be invoked with an unpatched constructor.
All user-facing live entries still fail closed. A separate user-approved D2
scope and separately approved D3 run are prerequisites for any actual call.

The module-private review ticket is deliberately NOT real authentication:
Python callers can import it. It exists to identify this never-to-be-released
source in the single coordinator during OFFLINE TESTS only.
"""
from __future__ import annotations

import http.client
from f0_l2_d1_coordinator import FakeSource
from f0_l2_d1_concrete_https import (
    _REVIEW_TEST_ONLY_CAPABILITY, _review_concrete_https_once,
)

_D1_OFFLINE_UNRELEASED_TRANSPORT_TICKET = object()
_UNPATCHED_HTTPS_CONNECTION = http.client.HTTPSConnection


def _require_intercepted_http_for_offline_review():
    # The private code-review route cannot reach unpatched HTTPSConnection,
    # even if someone imports the test ticket. This is NOT a production
    # authorization mechanism or a general network sandbox.
    if http.client.HTTPSConnection is _UNPATCHED_HTTPS_CONNECTION:
        raise ValueError("D1_REVIEW_REAL_HTTPS_CONSTRUCTOR_NOT_INTERCEPTED")


class UnreleasedRealHTTPSCodeSource(FakeSource):
    """Specific real HTTPS connection code, never a public executable sender."""

    def __init__(self, *, _offline_review_ticket=None):
        if _offline_review_ticket is not _D1_OFFLINE_UNRELEASED_TRANSPORT_TICKET:
            raise ValueError("D1_REAL_SOURCE_NOT_RELEASED_FOR_NETWORK")
        super().__init__(first_head=1000, growth_bps=5.0)

    def reply_over_unreleased_real_https(self, request, begin_post_attempt,
                                        timeout_s):
        if type(self) is not UnreleasedRealHTTPSCodeSource:
            raise ValueError("D1_REAL_SOURCE_EXACT_CLASS_ONLY")
        if not callable(begin_post_attempt):
            raise ValueError("D1_REAL_SOURCE_MISSING_SHARED_POST_GATE")
        denied = [None]

        def guarded_post(given):
            if given != request:
                raise ValueError("D1_REAL_SOURCE_REQUEST_ID_CHANGED")
            try:
                begin_post_attempt()
            except Exception as exc:
                denied[0] = exc
                raise

        # Code under review: no injected constructor here. In tests the
        # *actual stdlib HTTPSConnection symbol* is patched BEFORE invocation.
        _require_intercepted_http_for_offline_review()
        result = _review_concrete_https_once(
            request, final_post_guard=guarded_post,
            _test_capability=_REVIEW_TEST_ONLY_CAPABILITY,
            timeout_s=timeout_s,
        )
        if denied[0] is not None:
            raise denied[0]
        if result["state"] != "RAW" or result["raw_frame"] is None:
            # Once connect/request was ATTEMPTED, UNKNOWN is safer than
            # implying no network packet was transmitted. Never retry.
            raise ValueError("D1_UNRELEASED_REAL_TRANSPORT_UNKNOWN_STOP")
        return result["raw_frame"]


def send_live(*_args, **_kwargs):
    raise ValueError("D1_REAL_SOURCE_D2_D3_NOT_AUTHORIZED")
