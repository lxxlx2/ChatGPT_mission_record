#!/usr/bin/env python3
"""Bounded injection-only full-block L1 acquisition core (NO HTTP/WS/CLI).

A future network runner requires a separately approved code SHA, concrete
permit and fresh user consent. The caller supplies a fake sender and clocks;
all output is labelled offline, not public first-seen or a verified control.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from f0_l1_code_probe import atomic_json
from f0_l1_preflight import official_router_addresses
from f0_l1_window import (
    DOCUMENTED_ROUTER_MODE, FROZEN_ROUTER_REGISTRY_BLOB, MAX_WINDOW,
    SCHEMA as WINDOW_SCHEMA, git_blob_sha1, load_frozen_cohort,
    cohort_watchlist, offline_window, utc_ms,
)
from f0_rpc_adapter import block_candidates, digest

SCHEMA = "bsc-f0-l1-injected-presend-capture-v1"


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError(reason)


def _safe_error(exc: Exception) -> str:
    if isinstance(exc, TimeoutError):
        return "NETWORK_TIMEOUT"
    if isinstance(exc, ConnectionError):
        return "NETWORK_ERROR"
    return "INJECTED_SENDER_FAILURE"


def _validate_paths(journal_path: Path, report_path: Path) -> None:
    require(journal_path.name == "journal.json" and report_path.name == "report.json" and
            journal_path.parent.resolve() == report_path.parent.resolve() and
            journal_path.resolve(strict=False) != report_path.resolve(strict=False) and
            not journal_path.is_symlink() and not report_path.is_symlink() and
            not journal_path.exists() and not report_path.exists(),
            "JOURNAL_REPORT_PATH_OR_EXISTENCE_CONFLICT")
    require(journal_path.parent.is_dir(), "MISSING_PRIVATE_STORAGE_ROOT")


def capture_injected_blocks(
    sender: Callable[[dict], dict],
    cohort_raw: bytes,
    router_registry_raw: bytes,
    *,
    start_height: int,
    end_height: int,
    max_calls: int,
    journal_path: Path,
    report_path: Path,
    clock_utc: Callable[[], str],
    clock_monotonic_ms: Callable[[], int],
    fail_streak_limit: int = 3,
    control_modulo: int = 2,
) -> dict:
    """Collect fake/saved full blocks with the exact real-cohort parsing path.

    This API has no network sender, endpoint, permit, worker, sleep, loop over
    time or hidden retries. Any injected callable may perform arbitrary actions,
    so tests must use an explicitly non-network fake sender. This module makes
    ZERO network calls of its own, and never authorizes the caller's sender.
    """
    require(callable(sender) and callable(clock_utc) and callable(clock_monotonic_ms),
            "EXPLICIT_INJECTED_DEPENDENCIES_REQUIRED")
    require(type(start_height) is int and start_height >= 1 and
            type(end_height) is int and end_height >= start_height and
            1 <= end_height - start_height + 1 <= MAX_WINDOW and
            type(max_calls) is int and 1 <= max_calls <= MAX_WINDOW and
            type(fail_streak_limit) is int and fail_streak_limit >= 1 and
            type(control_modulo) is int and control_modulo >= 1,
            "INVALID_BOUNDED_CAPTURE_PLAN")
    _validate_paths(journal_path, report_path)

    # All provenance/registry rejection occurs BEFORE creating journal or send.
    cohort = load_frozen_cohort(cohort_raw)
    watched, _ = cohort_watchlist(cohort)
    require(git_blob_sha1(router_registry_raw) == FROZEN_ROUTER_REGISTRY_BLOB,
            "FROZEN_ROUTER_REGISTRY_REQUIRED")
    registry = json.loads(router_registry_raw)
    routers = set(official_router_addresses(registry))
    require(len(watched) == 20 and len(routers) == 2, "INVALID_FROZEN_INPUT_COUNTS")

    planned = end_height - start_height + 1
    attempts: list[dict] = []
    records: list[dict] = []
    failure_streak = 0
    stop = "INJECTED_WINDOW_COMPLETED"
    journal = {"schema": SCHEMA, "mode": "INJECTED_SENDER_NO_NETWORK_ENTRYPOINT",
               "attempted_calls": 0, "attempts": attempts,
               "provider_billed": "UNVERIFIED"}

    for height in range(start_height, end_height + 1):
        if len(attempts) >= max_calls:
            stop = "INJECTED_BUDGET_EXHAUSTED"
            break
        index = len(attempts) + 1
        requested_utc = clock_utc()
        requested_mono = clock_monotonic_ms()
        require(type(requested_mono) is int and requested_mono >= 0,
                "INVALID_REQUEST_MONOTONIC")
        utc_ms(requested_utc)
        payload = {"jsonrpc": "2.0", "id": index, "method": "eth_getBlockByNumber",
                   "params": [hex(height), True]}
        attempt = {"index": index, "height": height, "method": "eth_getBlockByNumber",
                   "params": payload["params"], "requested_utc": requested_utc,
                   "requested_monotonic_ms": requested_mono,
                   "state": "ATTEMPTED_OUTCOME_UNKNOWN"}
        attempts.append(attempt)
        journal["attempted_calls"] = len(attempts)
        atomic_json(journal_path, journal)  # always before invoking the sender

        # A BaseException/KeyboardInterrupt deliberately leaves the unknown
        # durable row instead of silently pretending no request was attempted.
        rpc = None
        error = None
        try:
            value = sender(payload)
        except Exception as exc:
            error = _safe_error(exc)
        else:
            if (not isinstance(value, dict) or value.get("jsonrpc") != "2.0" or
                    value.get("id") != index):
                error = "INVALID_RPC_IDENTITY"
            elif value.get("error") is not None:
                error = "RPC_ERROR"
            else:
                try:
                    parsed = block_candidates(value, watched, routers)
                    require(parsed["block_number"] == height, "BLOCK_HEIGHT_MISMATCH")
                    rpc = value
                except (ValueError, KeyError, TypeError):
                    error = "INVALID_FULL_BLOCK_RESPONSE"

        response_utc = clock_utc()
        response_mono = clock_monotonic_ms()
        require(type(response_mono) is int and response_mono >= requested_mono and
                utc_ms(response_utc) >= utc_ms(requested_utc),
                "INCONSISTENT_CAPTURE_CLOCKS")
        attempt.update(completed_utc=response_utc,
                       completed_monotonic_ms=response_mono,
                       state="RPC_RESPONSE" if rpc is not None else "FAILED",
                       response_sha256=digest(rpc) if rpc is not None else None,
                       failure_code=error)
        atomic_json(journal_path, journal)
        row = {"height": height, "ingest_path": "POLL",
               "request_utc": requested_utc,
               "response_utc": response_utc, "first_received_utc": response_utc,
               "request_monotonic_ms": requested_mono,
               "response_monotonic_ms": response_mono,
               "first_received_monotonic_ms": response_mono,
               "result": "RECEIVED" if rpc is not None else "FAILED"}
        if rpc is not None:
            row["rpc"] = rpc
            failure_streak = 0
        else:
            row["error_code"] = error
            failure_streak += 1
        records.append(row)
        if failure_streak >= fail_streak_limit:
            stop = "INJECTED_CONSECUTIVE_SOURCE_FAILURES"
            break

    fixture = {
        "schema": WINDOW_SCHEMA, "mode": "SYNTHETIC_SAVED_RPC_ONLY",
        "trial": True, "chain_id": 56,
        "cohort_source_kind": "FROZEN_PR116_GIT_BLOB",
        "router_allowlist_kind": DOCUMENTED_ROUTER_MODE,
        "start_height": start_height, "end_height": end_height,
        "max_rpc_calls": max_calls, "max_control_discovery_calls": max_calls,
        "control_modulo": control_modulo, "block_attempts": records,
    }
    try:
        report = offline_window(fixture, cohort, cohort_raw_bytes=cohort_raw,
                                router_registry_raw=router_registry_raw)
    except (ValueError, KeyError, TypeError) as exc:
        report = {"schema": SCHEMA, "mode": "OFFLINE_INJECTED_ONLY",
                  "stop_state": "INJECTED_SAVED_PARSER_REJECTED",
                  "error_code": type(exc).__name__,
                  "attempted_calls": len(attempts),
                  "first_seen_source": "INJECTED_CLOCK_NOT_REAL",
                  "actual_rpc_calls": 0}
        atomic_json(report_path, report)
        return report

    report.update(
        capture_schema=SCHEMA,
        capture_mode="OFFLINE_INJECTED_ONLY_NOT_LIVE_L1",
        capture_stop_state=stop,
        attempted_calls=len(attempts),
        planned_heights=planned,
        nonattempted_heights=planned-len(attempts),
        failed_attempts=sum(x["state"] == "FAILED" for x in attempts),
        presend_attempts_journaled=len(attempts),
        first_seen_source="INJECTED_CLOCK_NOT_REAL",
        actual_rpc_calls=0,
        provider_billed="UNVERIFIED",
    )
    atomic_json(report_path, report)
    return report
