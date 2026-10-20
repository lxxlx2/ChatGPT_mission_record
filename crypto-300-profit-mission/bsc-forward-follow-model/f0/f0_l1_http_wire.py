#!/usr/bin/env python3
"""Pure offline BSC JSON-RPC HTTP wire adapter and prospective height plan.

NO urllib/socket implementation, no CLI, permit or automatic network. All
HTTP traffic is supplied by an injected callback, and this file is not proof
that any arbitrary callback was safe or unauthorised networking impossible.
"""
from __future__ import annotations

import json
from typing import Callable

SCHEMA = "bsc-f0-l1-offline-http-wire-v1"
ENDPOINT = "https://bsc-dataseed.bnbchain.org"
METHODS = ("eth_chainId", "eth_blockNumber", "eth_getBlockByNumber")
MAX_BODY_BYTES = 2_000_000
MAX_WINDOW_BLOCKS = 512


def require(ok: bool, code: str) -> None:
    if not ok:
        raise ValueError(code)


def valid_rpc_payload(payload: dict) -> dict:
    require(isinstance(payload, dict) and set(payload) == {"jsonrpc", "id", "method", "params"}
            and payload["jsonrpc"] == "2.0" and type(payload["id"]) is int
            and payload["id"] > 0 and payload["method"] in METHODS
            and isinstance(payload["params"], list), "HTTP_RPC_REQUEST_INVALID")
    method, params = payload["method"], payload["params"]
    if method in ("eth_chainId", "eth_blockNumber"):
        require(params == [], "HTTP_RPC_PARAMS_INVALID")
    else:
        require(len(params) == 2 and type(params[0]) is str
                and params[0].startswith("0x") and params[0] == params[0].lower()
                and len(params[0]) > 2 and params[0][2] != "0"
                and all(c in "0123456789abcdef" for c in params[0][2:])
                and type(params[1]) is bool and params[1] is True,
                "HTTP_RPC_FULL_BLOCK_PARAMS_REQUIRED")
        require(int(params[0], 16) > 0, "HTTP_RPC_BLOCK_HEIGHT_INVALID")
    return payload


def json_body(payload: dict) -> bytes:
    valid_rpc_payload(payload)
    return json.dumps(payload, separators=(",", ":"), sort_keys=True,
                      ensure_ascii=True).encode("utf-8")


def parse_http_response(status: int, headers: dict, body: bytes, request: dict,
                        *, max_bytes: int = MAX_BODY_BYTES) -> dict:
    valid_rpc_payload(request)
    require(type(max_bytes) is int and 0 < max_bytes <= MAX_BODY_BYTES,
            "HTTP_RESPONSE_CAP_INVALID")
    require(type(status) is int and status == 200, "HTTP_STATUS_NOT_OK_NO_REDIRECT")
    require(isinstance(headers, dict) and all(isinstance(k, str) and isinstance(v, str)
                                             for k,v in headers.items()),
            "HTTP_HEADERS_INVALID")
    lowercase_headers = {k.lower(): v.strip().lower() for k,v in headers.items()}
    require(lowercase_headers.get("content-type", "").split(";", 1)[0].strip() ==
            "application/json", "HTTP_JSON_CONTENT_TYPE_REQUIRED")
    require(lowercase_headers.get("content-encoding", "identity") == "identity",
            "HTTP_COMPRESSED_RESPONSE_REJECTED")
    require(type(body) is bytes and 0 < len(body) <= max_bytes,
            "HTTP_BODY_SIZE_INVALID")
    try:
        result = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("HTTP_INVALID_JSON_RESPONSE") from exc
    require(isinstance(result, dict) and result.get("jsonrpc") == "2.0" and
            type(result.get("id")) is int and result["id"] == request["id"],
            "HTTP_RPC_IDENTITY_MISMATCH")
    has_result = "result" in result
    has_error = "error" in result and result["error"] is not None
    require(has_result != has_error, "HTTP_RPC_RESULT_ERROR_AMBIGUOUS")
    if has_error:
        err = result["error"]
        require(isinstance(err, dict) and type(err.get("code")) is int,
                "HTTP_RPC_ERROR_INVALID")
    return result


def make_injected_http_sender(
    post_bytes: Callable[[str, bytes, float, int], tuple[int, dict, bytes]],
    *, max_response_bytes: int = MAX_BODY_BYTES, timeout_s: float = 4.0,
) -> Callable[[dict], dict]:
    """Bridge injected byte-level HTTP transport to L1 injected block sender.

    The callback MUST be a fake for offline tests. This constructor does not
    make it safe to plug in a real network opener without new approved permit.
    """
    require(callable(post_bytes) and type(max_response_bytes) is int and
            0 < max_response_bytes <= MAX_BODY_BYTES and
            type(timeout_s) in (int,float) and 0 < timeout_s <= 10,
            "HTTP_TRANSPORT_CONFIG_INVALID")

    def sender(payload: dict) -> dict:
        body = json_body(payload)
        status, headers, response_bytes = post_bytes(
            ENDPOINT, body, float(timeout_s), max_response_bytes)
        return parse_http_response(status, headers, response_bytes, payload,
                                   max_bytes=max_response_bytes)
    return sender


def _parse_quantity(rpc: dict, expected_method: str, expected_id: int) -> int:
    require(isinstance(rpc, dict) and rpc.get("jsonrpc") == "2.0" and
            rpc.get("id") == expected_id and "error" not in rpc,
            "HTTP_SOURCE_IDENTITY_UNVERIFIED")
    v = rpc.get("result")
    require(isinstance(v, str) and len(v) >= 3 and v.startswith("0x") and
            all(ch in "0123456789abcdefABCDEF" for ch in v[2:]),
            "HTTP_SOURCE_QUANTITY_INVALID")
    n = int(v,16)
    require(n > 0, "HTTP_SOURCE_QUANTITY_INVALID")
    if expected_method == "eth_chainId":
        require(n == 56, "HTTP_SOURCE_WRONG_CHAIN")
    return n


def plan_prospective_heights(chain_rpc: dict, head_rpc: dict, *,
                             chain_request_id: int, head_request_id: int,
                             max_block_reads: int) -> dict:
    """Plan FUTURE heights following a head; never label them already observed.

    Pure computation. Actual chain/head HTTP requests also require presend
    journal and new user authorisation in a separate reviewed live runner.
    """
    require(type(chain_request_id) is int and type(head_request_id) is int and
            chain_request_id > 0 and head_request_id > 0 and
            chain_request_id != head_request_id and
            type(max_block_reads) is int and 1 <= max_block_reads <= MAX_WINDOW_BLOCKS,
            "HTTP_PROSPECTIVE_PLAN_INVALID")
    chain = _parse_quantity(chain_rpc, "eth_chainId", chain_request_id)
    head = _parse_quantity(head_rpc, "eth_blockNumber", head_request_id)
    return {"schema": SCHEMA, "plan_kind": "FUTURE_HEIGHTS_ONLY_NOT_A_LIVE_CAPTURE",
            "chain_id": chain, "observed_head": head,
            "start_height": head + 1, "end_height": head + max_block_reads,
            "planned_heights": max_block_reads,
            "identity_reads_not_in_block_budget": 2,
            "requires_fresh_live_permission": True,
            "endpoint": ENDPOINT, "actual_rpc_calls": 0}
