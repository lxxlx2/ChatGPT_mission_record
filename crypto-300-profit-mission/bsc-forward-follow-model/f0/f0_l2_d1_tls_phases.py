#!/usr/bin/env python3
"""D1 HTTPS socket lifecycle OFFLINE exercise, not an authorized sender.

There is no default connection factory, production signer, runnable CLI or
live flag. This isolates TLS connect vs actual POST for future J-06 review.
The caller's mock factory/gate have NO trusted identity. send_live() in the
separate reviewed module remains an unconditional rejection.
"""
from __future__ import annotations

import ssl
import time

from f0_l1_http_wire import MAX_BODY_BYTES, json_body, parse_http_response
from f0_l2_d1_https import HOST, PORT

MAX_REQUEST_BYTES=2000

def _valid(value, code):
    if not value:
        raise ValueError(code)


def _exercise_tls_post_with_mock(request, fake_factory, fake_prepost_guard,
                                 *, timeout_s=5.0, response_limit=MAX_BODY_BYTES):
    """Use only an explicitly injected fake TLS connection.

    A TLS CONNECT attempt is separately accountable from actual HTTP POST.
    It must happen only after the coordinator fsyncs RESERVE_UNKNOWN. Once
    connected, the FINAL UTC/HEAD/dispatch gate is evaluated immediately
    before HTTP request emission, not before TLS setup. A gate rejection
    closes TLS with NO POST. Connection errors never cause a retry.

    This is NOT callable via a real entrypoint and NEVER supplies its own
    HTTPSConnection factory. The caller could provide a network-capable
    factory; hence its result is explicitly offline/UNTRUSTED and cannot
    authorize live traffic. Only fake factories are used in tests.
    """
    _valid(callable(fake_factory) and callable(fake_prepost_guard) and
           type(timeout_s) in (float,int) and 0 < timeout_s <= 5 and
           type(response_limit) is int and 0 < response_limit <= MAX_BODY_BYTES,
           "D1_TLS_PHASE_CONFIG_INVALID")
    body=json_body(request)
    _valid(len(body)<=MAX_REQUEST_BYTES,"D1_TLS_PHASE_REQUEST_TOO_LARGE")
    context=ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH)
    _valid(context.check_hostname and context.verify_mode==ssl.CERT_REQUIRED,
           "D1_TLS_PHASE_CONTEXT_INVALID")

    conn=None
    phase="BEFORE_CONNECT"
    connected_at=None
    post_attempted_at=None
    response_completed_at=None
    frame=None
    failure=None
    try:
        conn=fake_factory(HOST,port=PORT,timeout=float(timeout_s),
                          context=context)
        _valid(conn is not None,"D1_TLS_PHASE_CONNECTION_MISSING")
        phase="CONNECT_ATTEMPTED"
        conn.connect()
        # A real http.client.HTTPSConnection must expose an established
        # TLS socket after connect(). A pre-connect "POST gate" cannot
        # establish actual POST time or prevent expired HEAD dispatch.
        _valid(getattr(conn,"sock",None) is not None,
               "D1_TLS_PHASE_NOT_CONNECTED")
        connected_at=time.monotonic()
        phase="CONNECTED"
        fake_prepost_guard(request)
        # This is the CALL-to-request boundary, not a measured wire-byte time.
        post_attempted_at=time.monotonic()
        phase="POST_ATTEMPTED"
        conn.request("POST","/",body=body,headers={
            "Host":HOST,"Content-Type":"application/json",
            "Accept":"application/json","Accept-Encoding":"identity",
            "Connection":"close"})
        response=conn.getresponse()
        status=response.status
        header_pairs=response.getheaders()
        _valid(type(status) is int and not (300<=status<400),
               "D1_TLS_PHASE_REDIRECT_FORBIDDEN")
        _valid(type(header_pairs) is list and all(
            type(k) is str and type(v) is str for k,v in header_pairs),
            "D1_TLS_PHASE_HEADERS_INVALID")
        headers={k.lower():v for k,v in header_pairs}
        _valid(headers.get("content-encoding","identity").lower()=="identity",
               "D1_TLS_PHASE_COMPRESSION_FORBIDDEN")
        raw=response.read(response_limit+1)
        _valid(type(raw) is bytes and len(raw)<=response_limit,
               "D1_TLS_PHASE_RESPONSE_TOO_LARGE")
        frame=(status,headers,raw)
        response_completed_at=time.monotonic()
        phase="RESPONSE_FRAME"
    except Exception as exc:
        # Never silently classify an uncertain POST as NOT SENT.
        failure=("D1_TLS_POST_GATE_DENIED" if
                 phase=="CONNECTED" else
                 "D1_TLS_" + phase + "_FAILED")
        if type(exc) is ValueError and str(exc).startswith("D1_TLS_PHASE_"):
            failure=str(exc)
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                # Close failure never permits retry or declares success.
                if failure is None:
                    failure="D1_TLS_CLOSE_UNCERTAIN"

    return {
        "mode":"OFFLINE_INJECTED_CONNECTION_ONLY_NOT_AUTHORIZED",
        "state":"FRAME" if failure is None else "FAILED",
        "failure":failure,
        "stage":phase,
        "connect_attempted":phase!="BEFORE_CONNECT",
        "connected_at_monotonic":connected_at,
        "post_attempted_at_monotonic":post_attempted_at,
        "response_completed_at_monotonic":response_completed_at,
        "post_attempted_or_unknown":post_attempted_at is not None,
        "frame":frame if failure is None else None,
        "retry_allowed":False,
        "live_authorized":False,
        "network_provenance":"UNVERIFIED_INJECTED_FAKE_FACTORY",
        "production":"NO_GO",
    }


def _validate_offline_tls_frame(outcome, request):
    _valid(type(outcome) is dict and outcome.get("state")=="FRAME"
           and outcome.get("mode")==
           "OFFLINE_INJECTED_CONNECTION_ONLY_NOT_AUTHORIZED",
           "D1_TLS_NO_VALID_FRAME")
    status,headers,raw=outcome["frame"]
    return parse_http_response(status,headers,raw,request)


def send_live(*_args, **_kwargs):
    raise ValueError("D1_REAL_TLS_SENDER_DISABLED_REQUIRES_D2")
