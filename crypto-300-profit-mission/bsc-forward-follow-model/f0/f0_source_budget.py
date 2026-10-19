#!/usr/bin/env python3
"""Offline BSC F0 request/CU planner. It cannot issue network requests.

Numbers are scenario estimates, not provider guarantees or live-run permission.
All quote/control discovery costs must be included explicitly.
"""
from __future__ import annotations

import argparse
import json
import math
from decimal import Decimal, InvalidOperation, ROUND_CEILING

SCHEMA = "bsc-f0-source-budget-preflight-v1"
CU_PER_CALL = {
    "eth_getBlockByNumber": 20,
    "eth_getTransactionReceipt": 20,
    "eth_call": 26,
    "eth_getCode": 20,
}
CU_PER_WS_BYTE = Decimal("0.04")


def nonnegative_int(value: str) -> int:
    number = int(value)
    if number < 0:
        raise argparse.ArgumentTypeError("negative value forbidden")
    return number


def positive_decimal(value: str) -> Decimal:
    try:
        amount = Decimal(value)
    except InvalidOperation as exc:
        raise argparse.ArgumentTypeError("invalid decimal") from exc
    if not amount.is_finite() or amount <= 0:
        raise argparse.ArgumentTypeError("positive finite decimal required")
    return amount


def ceil_ratio(numerator: Decimal, denominator: Decimal) -> int:
    return int((numerator / denominator).to_integral_value(rounding=ROUND_CEILING))


def estimate(*, hours: Decimal, block_seconds: Decimal, watch_receipts: int,
             control_receipts: int, eligible_entry_quotes: int,
             eligible_exit_quotes: int, audit_receipts: int,
             ws_bytes_per_block: int, eoa_checks: int,
             max_total_rpc_calls: int, max_control_discovery_calls: int,
             cu_budget: int) -> dict:
    if (hours <= 0 or block_seconds <= 0 or not hours.is_finite() or
            not block_seconds.is_finite()):
        raise ValueError("time inputs must be positive and finite")
    integers = (watch_receipts, control_receipts, eligible_entry_quotes,
                eligible_exit_quotes, audit_receipts, ws_bytes_per_block,
                eoa_checks, max_total_rpc_calls, max_control_discovery_calls,
                cu_budget)
    if any(type(i) is not int or i < 0 for i in integers):
        raise ValueError("all counts, caps and quota must be nonnegative integers")
    blocks = ceil_ratio(hours * Decimal(3600), block_seconds)
    methods = {
        "full_block_discovery": {"count": blocks, "method": "eth_getBlockByNumber"},
        "watchlist_receipts": {"count": watch_receipts, "method": "eth_getTransactionReceipt"},
        "control_receipts": {"count": control_receipts, "method": "eth_getTransactionReceipt"},
        "entry_quote_calls": {"count": eligible_entry_quotes * 3, "method": "eth_call"},
        "exit_quote_calls": {"count": eligible_exit_quotes * 3, "method": "eth_call"},
        "independent_audit_receipts": {"count": audit_receipts, "method": "eth_getTransactionReceipt"},
        "eoa_code_checks": {"count": eoa_checks, "method": "eth_getCode"},
    }
    for value in methods.values():
        value["estimated_cu"] = value["count"] * CU_PER_CALL[value["method"]]
    rpc_calls = sum(v["count"] for v in methods.values())
    control_discovery_calls = blocks + control_receipts
    ws_bytes = blocks * ws_bytes_per_block
    ws_cu = Decimal(ws_bytes) * CU_PER_WS_BYTE
    total_cu = sum(v["estimated_cu"] for v in methods.values()) + ws_cu
    cap_present = max_total_rpc_calls > 0 and max_control_discovery_calls > 0
    caps_ok = (cap_present and rpc_calls <= max_total_rpc_calls and
               control_discovery_calls <= max_control_discovery_calls)
    budget_ok = cu_budget > 0 and total_cu <= cu_budget
    return {
        "schema": SCHEMA,
        "mode": "OFFLINE_PLANNING_ONLY",
        "trial_run_authorized": False,
        "actual_rpc_calls": 0,
        "live_source_tested": False,
        "source_capabilities": "UNVERIFIED",
        "block_interval_seconds_scenario": str(block_seconds),
        "duration_hours_scenario": str(hours),
        "estimated_blocks": blocks,
        "rpc_breakdown": methods,
        "estimated_total_rpc_calls": rpc_calls,
        "estimated_control_discovery_calls": control_discovery_calls,
        "hypothetical_websocket_bytes": ws_bytes,
        "hypothetical_websocket_cu": str(ws_cu),
        "estimated_total_cu": str(total_cu),
        "cu_limit_scenario": cu_budget,
        "max_total_rpc_calls": max_total_rpc_calls,
        "max_control_discovery_calls": max_control_discovery_calls,
        "cap_evaluation": (
            "NEEDS_EXPLICIT_CAPS" if not cap_present
            else "WITHIN_SCENARIO_CAPS" if caps_ok else "OVER_SCENARIO_CAPS"
        ),
        "cu_evaluation": (
            "UNKNOWN_AVAILABLE_QUOTA" if cu_budget == 0
            else "WITHIN_HYPOTHETICAL_CU_LIMIT" if budget_ok else "OVER_HYPOTHETICAL_CU_LIMIT"
        ),
        "stop_state": "NO_RUN",
        "missing_live_evidence": [
            "provider_account_authorization", "method_support", "actual_free_quota_remaining",
            "actual_websocket_payload_bytes", "control_stream_event_rate",
            "matched_realtime_quotes", "independent_provider_or_method_denominator",
            "confirmed_finality_and_E2_policy", "per_method_latency",
        ],
        "notes": [
            "Assumes exactly one full-block RPC call per nominal block; not a verified capture method.",
            "Control discovery shares full-block calls; audit/receipt/quotes are additional calls.",
            "HTTP polling overhead, retries, gap repair, event payload variability and reconnects not included.",
            "CU pricing is a published Alchemy illustration, not proof of BSC method/billing support.",
            "No permission flag or network client exists: supplying nonzero caps cannot authorize any run.",
        ],
    }


def main() -> None:
    p = argparse.ArgumentParser(description="OFFLINE F0 capacity planning; NEVER network or running")
    p.add_argument("--hours", type=positive_decimal, default=Decimal("24"))
    p.add_argument("--block-seconds", type=positive_decimal, default=Decimal("0.45"))
    p.add_argument("--watch-receipts", type=nonnegative_int, default=0)
    p.add_argument("--control-receipts", type=nonnegative_int, default=0)
    p.add_argument("--entry-events", type=nonnegative_int, default=0)
    p.add_argument("--exit-events", type=nonnegative_int, default=0)
    p.add_argument("--audit-receipts", type=nonnegative_int, default=0)
    p.add_argument("--eoa-checks", type=nonnegative_int, default=0)
    p.add_argument("--ws-bytes-per-block", type=nonnegative_int, default=0)
    p.add_argument("--cu-budget", type=nonnegative_int, default=0)
    p.add_argument("--max-total-rpc-calls", type=nonnegative_int, default=0)
    p.add_argument("--max-control-discovery-calls", type=nonnegative_int, default=0)
    a = p.parse_args()
    result = estimate(
        hours=a.hours, block_seconds=a.block_seconds,
        watch_receipts=a.watch_receipts, control_receipts=a.control_receipts,
        eligible_entry_quotes=a.entry_events, eligible_exit_quotes=a.exit_events,
        audit_receipts=a.audit_receipts, ws_bytes_per_block=a.ws_bytes_per_block,
        eoa_checks=a.eoa_checks, max_total_rpc_calls=a.max_total_rpc_calls,
        max_control_discovery_calls=a.max_control_discovery_calls, cu_budget=a.cu_budget,
    )
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))


if __name__ == "__main__":
    main()
