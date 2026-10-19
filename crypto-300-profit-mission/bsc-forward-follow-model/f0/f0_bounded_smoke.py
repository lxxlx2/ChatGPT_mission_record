#!/usr/bin/env python3
"""Explicitly gated, bounded BSC public HTTP smoke. No execution by default.

Offline fixture path makes ZERO network requests. Live path is unusable without
an externally approved, short-lived local permit. No WS, quotes, signing, or
background jobs exist. A smoke pass does not demonstrate E1/E2/E3 or coverage.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable

ENDPOINT = "https://bsc-dataseed.bnbchain.org"
METHODS = ("eth_chainId", "eth_blockNumber", "eth_getBlockByNumber", "eth_getTransactionReceipt")
SCOPE = "ONE_TIME_BSC_PUBLIC_HTTP_SOURCE_SMOKE_ONLY"
MAX_CALLS = 4
MAX_DISCOVERY = 1
MAX_RESPONSE_BYTES = 2_000_000


def require(condition: bool, code: str) -> None:
    if not condition:
        raise ValueError(code)


def utc(value: str) -> datetime:
    require(isinstance(value, str) and value.endswith("Z"), "INVALID_UTC")
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("INVALID_UTC") from exc
    require(result.tzinfo is not None, "INVALID_UTC")
    return result


def validate_permit(permit: dict, now: datetime) -> None:
    """Do not infer approval from data alone: user must explicitly approve scope in chat."""
    require(isinstance(permit, dict), "PERMIT_REQUIRED")
    require(permit.get("scope") == SCOPE and permit.get("user_authorized") is True,
            "EXPLICIT_USER_AUTHORIZATION_REQUIRED")
    require(permit.get("approved_endpoint") == ENDPOINT, "ENDPOINT_NOT_APPROVED")
    require(permit.get("methods") == list(METHODS), "UNAPPROVED_METHODS")
    require(permit.get("cost_policy") == "FREE_ONLY_NO_PAYMENT", "NONFREE_COST_RISK")
    require(permit.get("local_environment") == "USER_MAC_LOCAL_ONLY", "ENVIRONMENT_NOT_APPROVED")
    require(type(permit.get("max_total_rpc_calls")) is int and
            permit["max_total_rpc_calls"] == MAX_CALLS, "RPC_CAP_MUST_BE_FOUR")
    require(type(permit.get("max_control_discovery_calls")) is int and
            permit["max_control_discovery_calls"] == MAX_DISCOVERY,
            "CONTROL_CAP_MUST_BE_ONE")
    require(type(permit.get("max_response_bytes")) is int and
            0 < permit["max_response_bytes"] <= MAX_RESPONSE_BYTES, "RESPONSE_CAP_INVALID")
    require(permit.get("no_retries") is True and permit.get("no_ws") is True,
            "RETRIES_OR_WS_FORBIDDEN")
    require(permit.get("store_raw_payloads") is False, "RAW_PAYLOAD_PERSISTENCE_FORBIDDEN")
    require(type(permit.get("retention_hours")) is int and
            1 <= permit["retention_hours"] <= 24, "RETENTION_OUT_OF_SCOPE")
    require(isinstance(permit.get("storage_root"), str) and
            permit["storage_root"].startswith("/tmp/") and
            ".." not in Path(permit["storage_root"]).parts, "STORAGE_NOT_APPROVED")
    start, end = utc(permit.get("window_start_utc")), utc(permit.get("window_end_utc"))
    require(timedelta(0) < end - start <= timedelta(minutes=10), "WINDOW_TOO_WIDE")
    require(start <= now <= end, "OUTSIDE_APPROVED_WINDOW")


def digest(obj: object) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=False).encode()).hexdigest()


def rpc_hex(value: str, expected_bytes: int | None = None) -> int:
    require(isinstance(value, str) and value.startswith("0x") and
            len(value) > 2 and all(v in "0123456789abcdefABCDEF" for v in value[2:]),
            "INVALID_HEX_RESPONSE")
    if expected_bytes is not None:
        require(len(value) == expected_bytes * 2 + 2, "WRONG_HEX_SIZE")
    return int(value, 16)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("REDIRECT_FORBIDDEN")


def https_sender(endpoint: str, payload: dict, response_cap: int) -> dict:
    """Only this function opens a connection, and only after permit validation."""
    require(endpoint == ENDPOINT, "ENDPOINT_NOT_APPROVED")
    data = json.dumps(payload, separators=(",", ":")).encode()
    request = urllib.request.Request(endpoint, data=data, method="POST",
                                     headers={"Content-Type": "application/json"})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect)
    with opener.open(request, timeout=4) as response:
        require(response.status == 200, "HTTP_NOT_OK")
        raw = response.read(response_cap + 1)
    require(len(raw) <= response_cap, "RESPONSE_TOO_LARGE")
    try:
        item = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("INVALID_JSON_RESPONSE") from exc
    require(isinstance(item, dict), "INVALID_JSON_RESPONSE")
    return item


class LimitedRPC:
    def __init__(self, sender: Callable, endpoint: str, response_cap: int, max_calls: int = MAX_CALLS):
        self.sender, self.endpoint, self.response_cap = sender, endpoint, response_cap
        self.max_calls, self.attempts, self.discovery_attempts = max_calls, 0, 0

    def call(self, method: str, params: list, discovery: bool = False) -> tuple[object, str]:
        require(method in METHODS, "METHOD_NOT_APPROVED")
        require(self.attempts < self.max_calls, "RPC_CALL_CAP_REACHED")
        if discovery:
            require(method == "eth_getBlockByNumber" and
                    self.discovery_attempts < MAX_DISCOVERY, "CONTROL_DISCOVERY_CAP_REACHED")
        self.attempts += 1  # failed calls count, no retries
        if discovery:
            self.discovery_attempts += 1
        row = {"jsonrpc": "2.0", "id": self.attempts, "method": method, "params": params}
        received = self.sender(self.endpoint, row, self.response_cap)
        require(isinstance(received, dict) and received.get("jsonrpc") == "2.0" and
                received.get("id") == row["id"] and
                received.get("error") is None and "result" in received,
                "RPC_ERROR_OR_BAD_ENVELOPE")
        return received["result"], digest(received)


def smoke(sender: Callable, cap: int = MAX_RESPONSE_BYTES) -> dict:
    """Maximum four nontransactional JSON-RPC reads; no loop/stream/poll."""
    rpc = LimitedRPC(sender, ENDPOINT, cap)
    chain, chain_sha = rpc.call("eth_chainId", [])
    require(rpc_hex(chain) == 56, "WRONG_CHAIN_ID")
    height_hex, head_sha = rpc.call("eth_blockNumber", [])
    height = rpc_hex(height_hex)
    require(height >= 1, "NO_BLOCK_HEIGHT")
    block, block_sha = rpc.call("eth_getBlockByNumber", [height_hex, True], discovery=True)
    require(isinstance(block, dict) and rpc_hex(block.get("number")) == height,
            "BLOCK_NUMBER_MISMATCH")
    rpc_hex(block.get("hash"), 32)
    transactions = block.get("transactions")
    require(isinstance(transactions, list) and all(isinstance(x, dict) for x in transactions),
            "FULL_BLOCK_TRANSACTIONS_UNAVAILABLE")
    receipt_state = "NOT_TESTED_EMPTY_BLOCK"
    receipt_sha = None
    if transactions:
        tx = transactions[0]
        txhash = tx.get("hash")
        rpc_hex(txhash, 32)
        receipt, receipt_sha = rpc.call("eth_getTransactionReceipt", [txhash])
        if receipt is None:
            receipt_state = "NOT_YET_AVAILABLE"
        else:
            require(isinstance(receipt, dict) and receipt.get("transactionHash", "").lower() == txhash.lower(),
                    "RECEIPT_IDENTITY_MISMATCH")
            require(receipt.get("blockHash", "").lower() == block["hash"].lower(),
                    "RECEIPT_BLOCK_MISMATCH")
            require(rpc_hex(receipt.get("blockNumber")) == height, "RECEIPT_HEIGHT_MISMATCH")
            receipt_state = "IDENTITY_VALIDATED_NOT_FINALITY"
    return {
        "schema": "bsc-f0-bounded-smoke-v1",
        "mode": "READ_ONLY_TRANSPORT_SMOKE_NOT_E3",
        "chain_id": 56, "height": height,
        "full_block_transaction_count": len(transactions),
        "receipt_state": receipt_state,
        "attempted_rpc_calls": rpc.attempts,
        "attempted_control_discovery_calls": rpc.discovery_attempts,
        "raw_rpc_sha256": {"chain_id": chain_sha, "head": head_sha,
                           "block": block_sha, "receipt": receipt_sha},
        "control_random_coverage": "NOT_MEASURED",
        "first_public_observed_latency": "NOT_MEASURED",
        "e1_finality": "UNRESOLVED_F1_POLICY",
        "e2_attested": False, "e3_actual_count": 0,
        "quoted_actual_count": 0, "paper_profit_labels": 0,
        "stop_state": "SMOKE_COMPLETE_NOT_F0_PASS",
    }


def fixture_sender(fixture: dict) -> Callable:
    """Deterministic in-memory sequence, never touches urllib."""
    require(fixture.get("mode") == "OFFLINE_ONLY" and fixture.get("trial") is True,
            "UNMARKED_FIXTURE_FORBIDDEN")
    rows = list(fixture["responses"])
    position = 0
    def send(endpoint: str, payload: dict, cap: int) -> dict:
        nonlocal position
        require(endpoint == ENDPOINT and position < len(rows), "OFFLINE_FIXTURE_EXHAUSTED")
        expected = rows[position]
        position += 1
        require(expected["method"] == payload["method"] and
                expected["params"] == payload["params"], "FIXTURE_REQUEST_MISMATCH")
        result = {"jsonrpc": "2.0", "id": payload["id"], "result": expected["result"]}
        require(len(json.dumps(result).encode()) <= cap, "RESPONSE_TOO_LARGE")
        return result
    return send


def main() -> None:
    parser = argparse.ArgumentParser(description="BSC transport smoke (offline by default; live requires explicit approval)")
    parser.add_argument("--fixture", type=Path, help="Run only saved offline JSON")
    parser.add_argument("--execute-live", action="store_true", help="ONLY after separate user approval")
    parser.add_argument("--permit", type=Path, help="Local ephemeral authorization file; never commit")
    parser.add_argument("--report", type=Path, help="Optional report, under authorized /tmp storage for live")
    args = parser.parse_args()
    require(bool(args.fixture) != bool(args.execute_live), "EXACTLY_ONE_MODE_REQUIRED")
    if args.fixture:
        require(args.permit is None, "PERMIT_NOT_USED_IN_OFFLINE_MODE")
        sender = fixture_sender(json.loads(args.fixture.read_text()))
        result = smoke(sender)
        result["mode"] = "OFFLINE_FIXTURE_ONLY_NO_NETWORK"
        result["actual_rpc_calls"] = 0
    else:
        require(args.permit is not None and args.report is not None,
                "EXPLICIT_PERMIT_AND_REPORT_REQUIRED")
        permit = json.loads(args.permit.read_text())
        validate_permit(permit, datetime.now(timezone.utc))
        out = args.report.resolve()
        allowed_root = Path(permit["storage_root"]).resolve()
        require(out.parent == allowed_root, "REPORT_OUTSIDE_APPROVED_STORAGE")
        result = smoke(https_sender, cap=permit["max_response_bytes"])
        result["mode"] = "AUTHORIZED_PUBLIC_HTTP_SMOKE_NOT_FULL_F0"
        result["actual_rpc_calls"] = result["attempted_rpc_calls"]
    text = json.dumps(result, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(text, encoding="utf-8")
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
