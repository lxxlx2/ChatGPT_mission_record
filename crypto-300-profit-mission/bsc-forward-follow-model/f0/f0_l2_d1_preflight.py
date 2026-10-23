#!/usr/bin/env python3
"""F0 D1 preflight contracts. Pure offline; no network or executable grants.

This module checks bytes and a scoped UTC contract but NEVER authenticates a
human. Signed, independently enrolled production trust roots remain a D2 gate.
"""
from __future__ import annotations
from datetime import datetime, timezone, timedelta
from hashlib import sha256
from pathlib import Path
import re
import subprocess

HEX40 = re.compile(r"[0-9a-f]{40}\Z")
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
ISO_UTC = re.compile(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d{1,6})?Z\Z")
RPC = ("eth_chainId", "eth_blockNumber", "eth_getBlockByNumber")
ENDPOINT = "https://bsc-dataseed.bnbchain.org"


def require(value, error):
    if not value:
        raise ValueError(error)


def parse_utc_timestamp(value):
    require(type(value) is str and bool(ISO_UTC.fullmatch(value)),
            "D1_UTC_REQUIRED")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise ValueError("D1_UTC_INVALID") from exc
    return parsed


def validate_window_contract(permit, now):
    """Inspect OFFLINE permit scope, not user/reviewer signature or approval."""
    require(type(permit) is dict and type(now) is datetime
            and now.tzinfo is not None and now.utcoffset() == timedelta(0),
            "D1_UTC_CONTRACT_INVALID")
    start = parse_utc_timestamp(permit.get("window_start_utc"))
    end = parse_utc_timestamp(permit.get("window_end_utc"))
    require(timedelta(0) < end - start <= timedelta(minutes=10)
            and start <= now <= end, "D1_UTC_WINDOW_INACTIVE")
    require(permit.get("endpoint") == ENDPOINT
            and permit.get("chain_id") == 56
            and permit.get("methods") == list(RPC)
            and permit.get("read_only") is True
            and permit.get("no_ws") is True
            and permit.get("no_retries") is True
            and permit.get("free_only") is True
            and permit.get("background") is False
            and permit.get("no_proxy") is True
            and permit.get("no_redirects") is True,
            "D1_UTC_TRANSPORT_SCOPE_INVALID")
    ranges = (
        ("max_total_attempts", 2, 32),
        ("max_block_reads", 1, 24),
        ("max_head_refreshes", 0, 6),
        ("max_inflight", 3, 3),
        ("min_start_gap_ms", 250, 5000),
        ("head_ttl_ms", 500, 4000),
        ("request_timeout_ms", 250, 5000),
        ("max_response_bytes", 1, 2_000_000),
        ("max_dispatch_seconds", 1, 60),
    )
    for field, low, high in ranges:
        value = permit.get(field)
        require(type(value) is int and low <= value <= high,
                "D1_UTC_RESOURCE_SCOPE_INVALID:" + field)
    require(permit["max_total_attempts"] <= (
        permit["max_block_reads"] + permit["max_head_refreshes"] + 2),
        "D1_UTC_TOTAL_BUDGET_CONFLICT")
    require(type(permit.get("approved_commit_sha")) is str and
            bool(HEX40.fullmatch(permit["approved_commit_sha"])),
            "D1_UTC_SHA_REQUIRED")
    # Explicitly label this NON-AUTHORIZING result.  Authentication is a
    # separate D2 prerequisite; even a valid UTC window never grants access.
    return {"validated_for": "OFFLINE_SCOPE_ONLY_NO_LIVE_PERMISSION",
            "approved_commit_sha": permit["approved_commit_sha"],
            "deadline_utc": end.isoformat(), "dispatch_seconds_cap":
            permit["max_dispatch_seconds"]}


def _git(root, *args):
    try:
        p = subprocess.run(["git", "-C", str(root), *args],
                           check=False, capture_output=True, timeout=6)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ValueError("D1_GIT_VERIFICATION_UNAVAILABLE") from exc
    require(p.returncode == 0, "D1_GIT_VERIFICATION_FAILED")
    return p.stdout


def verify_fixed_checkout_offline(root, reviewed_sha, reviewed_files):
    """Compare clean, exact Git HEAD and explicitly listed source file bytes.

    Reviewed files map {relative_path: sha256}, from a SEPARATELY trusted
    reviewer manifest. Caller-supplied hashes are not an authority by
    themselves; a real runner must freeze/attest the complete file list.
    """
    require(isinstance(root, Path) and root.is_absolute() and root.is_dir()
            and not root.is_symlink() and type(reviewed_sha) is str
            and bool(HEX40.fullmatch(reviewed_sha))
            and type(reviewed_files) is dict and bool(reviewed_files),
            "D1_CHECKOUT_ARGUMENT_INVALID")
    actual_root = Path(_git(root, "rev-parse", "--show-toplevel").decode().strip())
    require(actual_root == root and actual_root.resolve() == root,
            "D1_CHECKOUT_ROOT_MISMATCH")
    actual_sha = _git(root, "rev-parse", "HEAD").decode().strip()
    require(actual_sha == reviewed_sha, "D1_CHECKOUT_HEAD_MISMATCH")
    require(not _git(root, "status", "--porcelain", "--untracked-files=all"),
            "D1_CHECKOUT_DIRTY")
    for relative, digest in reviewed_files.items():
        require(type(relative) is str and not relative.startswith("/")
                and "\\" not in relative and
                all(x not in ("", ".", "..") for x in relative.split("/"))
                and type(digest) is str and bool(HEX64.fullmatch(digest)),
                "D1_MANIFEST_INVALID")
        path = root / relative
        # Rejected for every component, not just final filename.
        cursor = root
        for piece in relative.split("/"):
            cursor = cursor / piece
            require(not cursor.is_symlink(),
                    "D1_CHECKOUT_SYMLINK_DISALLOWED")
        require(path.is_file(), "D1_CHECKOUT_FILE_MISSING")
        from_git = _git(root, "show", "HEAD:" + relative)
        from_disk = path.read_bytes()
        require(from_git == from_disk and sha256(from_disk).hexdigest() == digest,
                "D1_CHECKOUT_BYTE_MISMATCH")
    return {"validated_for": "OFFLINE_CHECKOUT_ONLY_NO_LIVE_PERMISSION",
            "head_sha": actual_sha, "verified_files": len(reviewed_files)}
