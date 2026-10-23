#!/usr/bin/env python3
"""D1 sealed HTTPS code. NO live run entry, approvals or production trust roots.

send_live unconditionally rejects. The underlying implementation accepts an
explicit fake-only factory for test coverage. No default network factory.
"""
import ssl
from f0_l1_http_wire import MAX_BODY_BYTES, json_body, parse_http_response

HOST = "bsc-dataseed.bnbchain.org"
PORT = 443
LIVE_TRANSPORT_ENABLED = False

def require(ok, reason):
    if not ok:
        raise ValueError(reason)

def send_live(_request, _permit=None):
    raise ValueError("D1_LIVE_TRANSPORT_DISABLED_REQUIRES_D2_REVIEW")

def _exchange_with_factory(request, factory, *, timeout_s=5.0,
                           max_bytes=MAX_BODY_BYTES):
    """Fixed HTTPS host, no proxies/redirects, exactly one fake POST."""
    require(callable(factory) and type(timeout_s) in (int,float) and
            0 < timeout_s <= 5 and type(max_bytes) is int and
            0 < max_bytes <= MAX_BODY_BYTES,
            "D1_HTTPS_TRANSPORT_CONFIG_INVALID")
    body=json_body(request)
    require(len(body) <= 2000, "D1_HTTPS_REQUEST_TOO_LARGE")
    context=ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH)
    require(context.check_hostname and context.verify_mode == ssl.CERT_REQUIRED,
            "D1_HTTPS_TLS_VERIFICATION_REQUIRED")
    conn=factory(HOST,port=PORT,timeout=float(timeout_s),context=context)
    require(conn is not None,"D1_HTTPS_CONNECTION_UNAVAILABLE")
    try:
        conn.request("POST","/",body=body,headers={
            "Host":HOST, "Content-Type":"application/json",
            "Accept":"application/json","Accept-Encoding":"identity",
            "Connection":"close"})
        response=conn.getresponse()
        status=response.status
        headers={key.lower():value for key,value in response.getheaders()}
        require(type(status) is int and not 300 <= status < 400,
                "D1_HTTPS_REDIRECT_FORBIDDEN")
        require(headers.get("content-encoding","identity").lower()=="identity",
                "D1_HTTPS_COMPRESSED_RESPONSE_FORBIDDEN")
        raw=response.read(max_bytes+1)
        require(type(raw) is bytes and len(raw) <= max_bytes,
                "D1_HTTPS_RESPONSE_SIZE_LIMIT")
        # Non-200 frames are returned for archive, not retried or parsed OK.
        return status,headers,raw
    finally:
        conn.close()

def _parse_reviewed_fake_frame(frame,request):
    require(type(frame) is tuple and len(frame)==3,
            "D1_FAKE_FRAME_INVALID")
    return parse_http_response(frame[0],frame[1],frame[2],request)
