#!/usr/bin/env python3
"""One-shot adaptive BSC HTTP entrypoint. NO EXECUTION without fresh consent.

This module can issue real public BSC RPC requests ONLY through main() when the
operator explicitly supplies --execute-live, a SHA-bound single-use permit,
and an independently supplied exact permit approval. Imports do not start I/O.
No trading, wallet signing, WS, paid provider, daemon, or automatic retries.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import time

from f0_l1_adaptive_source_core import collect_adaptive_injected
from f0_l1_durable_journal import fsync_directory
from f0_l1_http_wire import ENDPOINT
from f0_l1_live_short import live_https_post

SCHEMA = "bsc-f0-adaptive-head-one-shot-permit-v1"
HEX40 = re.compile(r"[0-9a-f]{40}\Z")
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
DEPENDENCIES = (
    "f0_l1_adaptive_source_core.py",
    "f0_l1_adaptive_head_plan.py",
    "f0_l1_durable_journal.py",
    "f0_l1_http_wire.py",
    "f0_l1_live_short.py",
    "f0_l1_window.py",
    "f0_l1_preflight.py",
    "f0_l1_code_probe.py",
    "f0_l1_injected_capture.py",
    "f0_offline_collector.py",
    "f0_rpc_adapter.py",
    "f0_bounded_smoke.py",
    "F0_COHORT_PRESELECTION.json",
    "F0_ROUTER_SOURCE_CANDIDATES.json",
)
PERMIT_KEYS = frozenset((
    "scope", "user_authorized", "independent_review_required",
    "approved_commit_sha", "approved_script_sha256", "run_nonce",
    "window_start_utc", "window_end_utc", "storage_root",
    "endpoint", "chain_id", "methods", "free_only", "read_only",
    "no_retries", "no_ws", "no_proxy", "no_redirects", "background",
    "archive_raw_public_rpc", "cost_policy",
    "max_total_attempts", "max_block_reads", "max_head_polls",
    "duration_ms", "min_interval_ms", "head_poll_interval_ms",
    "max_stagnant_poll_wait_ms", "refresh_after_blocks",
    "max_response_bytes", "timeout_ms",
))


def require(ok, code):
    if not ok:
        raise ValueError(code)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def stamp(text):
    require(isinstance(text, str) and text.endswith("Z"), "ADAPTIVE_PERMIT_UTC_REQUIRED")
    try:
        return datetime.fromisoformat(text[:-1] + "+00:00")
    except ValueError as exc:
        raise ValueError("ADAPTIVE_PERMIT_BAD_UTC") from exc


def validate_permit(permit, now):
    """Structural validation only; NOT a permission grant or a network call."""
    require(isinstance(permit, dict) and set(permit) == PERMIT_KEYS,
            "ADAPTIVE_PERMIT_FIELDS_INVALID")
    require(permit["scope"] == SCHEMA and
            permit["user_authorized"] is True and
            permit["independent_review_required"] is True and
            permit["endpoint"] == ENDPOINT and
            permit["chain_id"] == 56 and
            permit["methods"] == [
                "eth_chainId", "eth_blockNumber", "eth_getBlockByNumber"] and
            all(permit[k] is True for k in
                ("free_only", "read_only", "no_retries", "no_ws",
                 "no_proxy", "no_redirects", "archive_raw_public_rpc")) and
            permit["background"] is False and
            permit["cost_policy"] == "FREE_ONLY_NO_AUTO_UPGRADE",
            "ADAPTIVE_PERMIT_SCOPE_INVALID")
    n, blocks, heads = (
        permit["max_total_attempts"], permit["max_block_reads"],
        permit["max_head_polls"])
    require(type(n) is int and type(blocks) is int and type(heads) is int
            and 1 <= blocks <= 24 and 1 <= heads <= 6
            and n == 2 + blocks + heads and n <= 32,
            "ADAPTIVE_PERMIT_TOTAL_BUDGET_INVALID")
    d, interval, poll = (permit["duration_ms"], permit["min_interval_ms"],
                         permit["head_poll_interval_ms"])
    require(type(d) is int and 1000 <= d <= 60000
            and type(interval) is int and 250 <= interval <= 1000
            and type(poll) is int and 500 <= poll <= 8000
            and type(permit["max_stagnant_poll_wait_ms"]) is int
            and poll <= permit["max_stagnant_poll_wait_ms"] <= 8000
            and type(permit["refresh_after_blocks"]) is int
            and 1 <= permit["refresh_after_blocks"] <= 8
            and type(permit["max_response_bytes"]) is int
            and 1 <= permit["max_response_bytes"] <= 2_000_000
            and type(permit["timeout_ms"]) is int
            and 1000 <= permit["timeout_ms"] <= 5000,
            "ADAPTIVE_PERMIT_LIMITS_INVALID")
    require(type(now) is datetime and now.tzinfo is not None,
            "ADAPTIVE_PERMIT_CLOCK_INVALID")
    start, end = stamp(permit["window_start_utc"]), stamp(permit["window_end_utc"])
    require(timedelta(0) < end - start <= timedelta(minutes=10)
            and start <= now and
            now + timedelta(milliseconds=d + permit["timeout_ms"]) <= end,
            "ADAPTIVE_PERMIT_WINDOW_INVALID")
    require(type(permit["approved_commit_sha"]) is str and
            HEX40.fullmatch(permit["approved_commit_sha"]) and
            type(permit["approved_script_sha256"]) is str and
            HEX64.fullmatch(permit["approved_script_sha256"]) and
            type(permit["run_nonce"]) is str and
            HEX64.fullmatch(permit["run_nonce"]),
            "ADAPTIVE_PERMIT_SHA_OR_NONCE_INVALID")
    raw_root = permit["storage_root"]
    require(type(raw_root) is str and Path(raw_root).is_absolute() and
            ".." not in Path(raw_root).parts, "ADAPTIVE_PERMIT_ROOT_INVALID")
    root = Path(raw_root)
    # On macOS the default tempfile directory is usually /var/folders/...,
    # not /tmp (/private/tmp). Constrain the resolved path to either the
    # resolved /tmp or this process's resolved default temp directory.
    resolved_root = root.resolve()
    temp_roots = (Path("/tmp").resolve(), Path(tempfile.gettempdir()).resolve())
    require(root.is_dir() and not root.is_symlink() and
            any(base in resolved_root.parents for base in temp_roots) and
            root.stat().st_mode & 0o077 == 0 and
            all(not (root / name).exists() and not (root / name).is_symlink()
                for name in ("journal.json", "report.json", "raw_responses")),
            "ADAPTIVE_PERMIT_OUTPUT_NOT_PRIVATE_OR_FRESH")
    return root


def verify_checkout(script, permit):
    """Pin this script and all imported transport/collector source bytes."""
    repo_raw = subprocess.run(
        ["git", "-C", str(script.parent), "rev-parse", "--show-toplevel"],
        check=True, capture_output=True, timeout=5).stdout
    repo = Path(repo_raw.decode().strip()).resolve(strict=True)
    head = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        check=True, capture_output=True, timeout=5).stdout.decode().strip()
    require(head == permit["approved_commit_sha"], "ADAPTIVE_UNREVIEWED_HEAD")
    require(digest(script.read_bytes()) == permit["approved_script_sha256"],
            "ADAPTIVE_UNREVIEWED_ENTRYPOINT")
    for name in DEPENDENCIES:
        target = (script.parent / name).resolve(strict=True)
        rel = target.relative_to(repo).as_posix()
        committed = subprocess.run(
            ["git", "-C", str(repo), "show", "HEAD:" + rel],
            check=True, capture_output=True, timeout=5).stdout
        require(target.read_bytes() == committed,
                "ADAPTIVE_UNREVIEWED_DEPENDENCY")
    return True


def consume_nonce(root, permit_raw, nonce):
    """One-use marker persisted BEFORE invoking any real transport callback."""
    target = root / (".f0_adaptive_nonce_" + digest(nonce.encode()) + ".json")
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(target, flags, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as output:
        json.dump({"permit_sha256": digest(permit_raw),
                   "nonce_sha256": digest(nonce.encode()),
                   "consumed_utc": datetime.now(timezone.utc).isoformat()},
                  output, sort_keys=True)
        output.flush()
        os.fsync(output.fileno())
    fsync_directory(root)
    return target


def main():
    parser = argparse.ArgumentParser(description="BSC adaptive one-use L1; live forbidden without new approval")
    parser.add_argument("--execute-live", action="store_true")
    parser.add_argument("--permit", required=True, type=Path)
    parser.add_argument("--review-approval", required=True, type=Path)
    args = parser.parse_args()
    require(args.execute_live, "ADAPTIVE_EXPLICIT_EXECUTE_FLAG_REQUIRED")
    permit_raw = args.permit.read_bytes()
    permit = json.loads(permit_raw)
    root = validate_permit(permit, datetime.now(timezone.utc))
    require(args.permit.resolve().parent != root and
            args.review_approval.resolve().parent != root and
            args.permit.resolve() != args.review_approval.resolve(),
            "ADAPTIVE_PERMIT_AND_REVIEW_MUST_BE_OUTSIDE_OUTPUT")
    require(args.review_approval.read_text(encoding="utf-8").strip() ==
            "APPROVE_PERMIT " + digest(permit_raw),
            "ADAPTIVE_INDEPENDENT_PERMIT_REVIEW_MISSING")
    verify_checkout(Path(__file__).resolve(), permit)
    consume_nonce(root, permit_raw, permit["run_nonce"])
    folder = Path(__file__).resolve().parent
    result = collect_adaptive_injected(
        post=live_https_post,
        clock=lambda: datetime.now(timezone.utc),
        mono=time.monotonic, sleep=time.sleep,
        output_root=root,
        cohort_raw=(folder / "F0_COHORT_PRESELECTION.json").read_bytes(),
        router_raw=(folder / "F0_ROUTER_SOURCE_CANDIDATES.json").read_bytes(),
        max_total_attempts=permit["max_total_attempts"],
        max_block_reads=permit["max_block_reads"],
        max_head_polls=permit["max_head_polls"],
        duration_ms=permit["duration_ms"],
        min_interval_ms=permit["min_interval_ms"],
        head_poll_interval_ms=permit["head_poll_interval_ms"],
        max_stagnant_poll_wait_ms=permit["max_stagnant_poll_wait_ms"],
        refresh_after_blocks=permit["refresh_after_blocks"],
        max_response_bytes=permit["max_response_bytes"],
        timeout_ms=permit["timeout_ms"],
    )
    print(json.dumps({
        "stop_state": result["stop_state"],
        "attempts_with_presend_persistence": result["total_attempts"],
        "actual_external_rpc_calls": "UNVERIFIED",
        "head_refreshes": result["head_refreshes"],
        "block_read_successes": result["block_read_successes"],
        "private_report": str(root / "report.json")
    }, sort_keys=True))


if __name__ == "__main__":
    main()
