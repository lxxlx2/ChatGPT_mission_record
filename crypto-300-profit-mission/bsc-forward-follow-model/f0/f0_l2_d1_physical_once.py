#!/usr/bin/env python3
"""One operator-triggered, bounded, read-only physical BSC foreground experiment.

No cron, trading, auto retry, background process, alternative sender, API key,
or multi-party signature. This module is NOT permission to execute an RPC:
the owner must explicitly invoke --execute-live with exact reviewed SHA and
the scope SHA256 confirmation after independent review. Import is inert.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import select
import stat
import subprocess
import sys
import threading
import time

from f0_l2_d1_physical_foreground_scope import check_physical_foreground_scope
from f0_l2_d1_grant import _consume_once_using_open_dirfd
from f0_l2_d1_recovery import reconcile_saved_attempts
from f0_l2_d1_preflight import _git

_ROOT = Path(__file__).resolve().parents[3]
_APP = ("Library", "Application Support", "MissionEvidence", "f0-physical-once")
_CHILD_MARKER = "child-started.once"
_LAUNCH_PREFIX = "I-AUTHORIZE-ONE-BSC-READ-ONLY-RUN:"
_MAX_SCOPE_BYTES = 4096


def _same_reviewed_checkout(reviewed_sha: str):
    if sys.platform != "darwin":
        raise ValueError("F0_PHYSICAL_MAC_FOREGROUND_ONLY")
    actual = _git(_ROOT, "rev-parse", "HEAD").decode().strip()
    if actual != reviewed_sha or _git(_ROOT, "status", "--porcelain",
                                      "--untracked-files=all"):
        raise ValueError("F0_PHYSICAL_UNREVIEWED_OR_DIRTY_CHECKOUT")
    if Path(_git(_ROOT, "rev-parse", "--show-toplevel").decode().strip()).resolve() != _ROOT:
        raise ValueError("F0_PHYSICAL_CHECKOUT_ROOT_MISMATCH")
    return actual


def _private_root():
    base = Path.home().resolve()
    if not base.is_dir() or base.stat().st_uid != os.getuid():
        raise ValueError("F0_PHYSICAL_OS_HOME_OWNER_INVALID")
    p = base
    for part in _APP:
        p = p / part
        if p.is_symlink():
            raise ValueError("F0_PHYSICAL_PRIVATE_ROOT_SYMLINK")
        if not p.exists():
            p.mkdir(mode=0o700)
        if not p.is_dir() or p.stat().st_uid != os.getuid():
            raise ValueError("F0_PHYSICAL_ROOT_OWNER_INVALID")
    # Existing root must be owner-only even if created in an older run.
    if p.stat().st_mode & 0o077:
        raise ValueError("F0_PHYSICAL_ROOT_NOT_PRIVATE")
    return p


def _new_private_dir(p: Path):
    p.mkdir(mode=0o700)
    if p.is_symlink() or p.stat().st_uid != os.getuid() or p.stat().st_mode & 0o077:
        raise ValueError("F0_PHYSICAL_EVIDENCE_OWNER_OR_MODE_INVALID")
    return p


def _open_private_dir(p):
    if p.is_symlink() or p.stat().st_uid != os.getuid() or p.stat().st_mode & 0o077:
        raise ValueError("F0_PHYSICAL_PRIVATE_DIR_INVALID")
    fd = os.open(p, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) |
                 getattr(os, "O_NOFOLLOW", 0))
    if not stat.S_ISDIR(os.fstat(fd).st_mode):
        os.close(fd)
        raise ValueError("F0_PHYSICAL_PRIVATE_DIR_NOT_DIRECTORY")
    return fd


def _sync_exclusive_marker(directory, name, data: bytes):
    fd_dir = _open_private_dir(directory)
    try:
        fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL |
                     getattr(os, "O_NOFOLLOW", 0), 0o600, dir_fd=fd_dir)
        with os.fdopen(fd, "wb") as out:
            out.write(data)
            out.flush()
            os.fsync(out.fileno())
        os.fsync(fd_dir)
    finally:
        os.close(fd_dir)


class _LiveOnceChildPermit:
    """Process-local guard, not authentication or operator consent."""

    __slots__ = ("_pid", "_uid", "_deadline", "_marker", "_grant_sha")

    def __init__(self, marker: Path, grant_sha: str, deadline: float):
        self._pid = os.getpid()
        self._uid = os.getuid()
        self._deadline = deadline
        self._marker = marker
        self._grant_sha = grant_sha

    def valid(self):
        try:
            p = self._marker
            return (os.getpid() == self._pid and os.getuid() == self._uid
                    and time.monotonic() < self._deadline
                    and not p.is_symlink() and p.is_file()
                    and p.stat().st_uid == self._uid
                    and p.stat().st_mode & 0o077 == 0
                    and json.loads(p.read_text())["grant_id_sha256"]
                    == self._grant_sha)
        except (OSError, ValueError, KeyError, TypeError):
            return False


def _guardian(pipefd: int, deadline: float, output: Path):
    """Kill entire child on parent pipe EOF or hard deadline, no restart."""
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            reason = "CHILD_HARD_DEADLINE"
        else:
            try:
                ready, _, _ = select.select([pipefd], [], [], min(remaining, 1.0))
                if not ready:
                    continue
                reason = ("PARENT_PIPE_CLOSED" if os.read(pipefd, 1) == b""
                          else "UNEXPECTED_PARENT_PIPE_DATA")
            except (OSError, ValueError):
                reason = "PARENT_LIVENESS_UNCERTAIN"
        try:
            _sync_exclusive_marker(output, "child_termination.json",
                                   (json.dumps({"reason": reason,
                                                "genuine_https_may_have_started": True})
                                    + "\n").encode())
        except (OSError, ValueError):
            pass
        os._exit(90)


def _child(root: Path, evidence: Path, raw: bytes, reviewed_sha: str,
           grant_sha: str, parent_pipe: int, deadline: float):
    if (parent_pipe < 3 or not stat.S_ISFIFO(os.fstat(parent_pipe).st_mode)
            or deadline <= time.monotonic()
            or deadline - time.monotonic() > 76):
        raise ValueError("F0_PHYSICAL_CHILD_LIFETIME_INVALID")
    _same_reviewed_checkout(reviewed_sha)
    fixed = _private_root()
    if root != fixed or evidence != fixed / "evidence" / grant_sha:
        raise ValueError("F0_PHYSICAL_CHILD_FIXED_OWNER_ROOT_MISMATCH")
    for private in (fixed / "registry", fixed / "evidence", evidence):
        fd = _open_private_dir(private)
        os.close(fd)
    verified = check_physical_foreground_scope(
        raw, independently_reviewed_sha=reviewed_sha)
    doc = json.loads(raw)
    if verified["grant_id_sha256"] != grant_sha:
        raise ValueError("F0_PHYSICAL_CHILD_SCOPE_IDENTITY_CHANGED")
    registry = root / "registry"
    output = evidence
    marker = registry / (grant_sha + ".consumed.json")
    if (not marker.is_file() or marker.is_symlink()
            or marker.stat().st_uid != os.getuid()
            or marker.stat().st_mode & 0o077):
        raise ValueError("F0_PHYSICAL_CHILD_ONCE_MARKER_MISSING")
    saved = json.loads(marker.read_bytes())
    if saved.get("permit_sha256") != verified["scope_sha256"] or (
            saved.get("outcome") != "CONSUMED_OR_UNKNOWN"):
        raise ValueError("F0_PHYSICAL_CHILD_ONCE_MARKER_MISMATCH")
    _sync_exclusive_marker(
        output, _CHILD_MARKER,
        (json.dumps({"grant_id_sha256": grant_sha,
                     "scope_sha256": verified["scope_sha256"],
                     "reviewed_sha": reviewed_sha,
                     "owner_uid": os.getuid()},
                    sort_keys=True) + "\n").encode())
    watcher = threading.Thread(
        target=_guardian, args=(parent_pipe, deadline, output),
        name="f0-physical-once-parent-watch", daemon=True)
    watcher.start()

    from f0_l2_d1_coordinator import _run_single_shared_coordinator
    from f0_l2_d1_physical_source_candidate import (
        BoundedPhysicalReadOnlySource, _UNRELEASED_SOURCE_CODE_SEAL)
    grant = _LiveOnceChildPermit(marker, grant_sha, deadline)
    if not grant.valid():
        raise ValueError("F0_PHYSICAL_CHILD_PERMIT_NOT_LIVE")
    source = BoundedPhysicalReadOnlySource(
        doc["window_start_utc"], doc["window_end_utc"],
        _unreleased_review_seal=_UNRELEASED_SOURCE_CODE_SEAL,
        _runtime_permit=grant)
    result = _run_single_shared_coordinator(
        source, output,
        max_total=doc["max_total"],
        max_blocks=doc["max_blocks"],
        max_refreshes=doc["max_refreshes"],
        spacing_ms=doc["spacing_ms"], slots=3,
        head_ttl_ms=doc["head_ttl_ms"],
        head_min_poll_age_ms=doc["head_min_poll_age_ms"],
        window_ms=doc["window_ms"],
        max_block_response_ms=doc["timeout_ms"],
        anchor_initial_head=True,
        _physical_source_candidate=True,
        _real_foreground_permit=grant)
    result["physical_source_run_scoped"] = True
    result["production"] = "NO_GO"
    result["f0_status"] = "NOT_PASSED"
    return result


def run_owner_approved_once(scope_path: Path, reviewed_sha: str,
                            confirmation: str):
    """One genuine read-only OS child, ONLY from explicit Mac CLI invocation."""
    if not isinstance(scope_path, Path) or not scope_path.is_absolute():
        raise ValueError("F0_PHYSICAL_OWNER_SCOPE_PATH_ABSOLUTE_REQUIRED")
    if scope_path.is_symlink() or not scope_path.is_file():
        raise ValueError("F0_PHYSICAL_OWNER_SCOPE_FILE_INVALID")
    if (scope_path.stat().st_uid != os.getuid()
            or scope_path.stat().st_mode & 0o077):
        raise ValueError("F0_PHYSICAL_OWNER_SCOPE_NOT_PRIVATE")
    raw = scope_path.read_bytes()
    if len(raw) > _MAX_SCOPE_BYTES:
        raise ValueError("F0_PHYSICAL_OWNER_SCOPE_OVERSIZE")
    _same_reviewed_checkout(reviewed_sha)
    v = check_physical_foreground_scope(
        raw, independently_reviewed_sha=reviewed_sha)
    expected = _LAUNCH_PREFIX + reviewed_sha + ":" + v["scope_sha256"]
    if confirmation != expected:
        raise ValueError("F0_PHYSICAL_EXPLICIT_ONE_RUN_CONFIRMATION_REQUIRED")
    doc = json.loads(raw)
    if (doc["window_ms"] + doc["timeout_ms"] + 2000 >
            doc["hard_seconds"] * 1000):
        raise ValueError("F0_PHYSICAL_LIFETIME_OUT_OF_SCOPE")

    root = _private_root()
    registry = root / "registry"
    if not registry.exists():
        _new_private_dir(registry)
    fd = _open_private_dir(registry)
    try:
        # O_EXCL consumed and fsynced BEFORE child, socket, DNS and TLS.
        consumed = _consume_once_using_open_dirfd(
            fd, doc["grant_id"], v["scope_sha256"])
    finally:
        os.close(fd)
    evidence_base = root / "evidence"
    if not evidence_base.exists():
        _new_private_dir(evidence_base)
    evidence_fd = _open_private_dir(evidence_base)
    os.close(evidence_fd)
    evidence = _new_private_dir(evidence_base / v["grant_id_sha256"])
    read_fd, write_fd = os.pipe()
    start = time.monotonic()
    deadline = start + doc["hard_seconds"]
    cmd = [sys.executable, "-B", str(Path(__file__).resolve()),
           "--child", str(root), str(evidence), raw.hex(), reviewed_sha,
           v["grant_id_sha256"], str(read_fd), repr(deadline)]
    try:
        proc = subprocess.Popen(
            cmd, stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            close_fds=True, pass_fds=(read_fd,), text=True)
    except Exception:
        # The O_EXCL marker remains permanently spent; never retry.
        os.close(write_fd)
        raise
    finally:
        os.close(read_fd)
    timed_out = False
    try:
        try:
            stdout, stderr = proc.communicate(
                timeout=max(0.01, deadline-time.monotonic()))
        except subprocess.TimeoutExpired:
            timed_out = True
            proc.kill()
            stdout, stderr = proc.communicate()
    finally:
        os.close(write_fd)
    try:
        audit = reconcile_saved_attempts(evidence)
    except (ValueError, OSError):
        audit = {"audit_status": "INVALID_OR_MISSING_NO_RETRY"}
    parsed = None
    if proc.returncode == 0 and not timed_out:
        try:
            parsed = json.loads(stdout)
        except (TypeError, ValueError):
            pass
    summary = {
        "state": ("PHYSICAL_ONCE_CHILD_EXITED" if parsed is not None
                  else "PHYSICAL_ONCE_FAILED_OR_UNKNOWN_NO_RETRY"),
        "schema": "bsc-f0-physical-once-foreground-v1",
        "reviewed_sha": reviewed_sha,
        "scope_sha256": v["scope_sha256"],
        "grant_id_sha256": v["grant_id_sha256"],
        "owner_uid": os.getuid(),
        "once_status": consumed["status"],
        "child_exit_code": proc.returncode,
        "child_timed_out": timed_out,
        "child": parsed,
        "audit": audit,
        "evidence_directory": str(evidence),
        "no_automatic_retry": True,
        "f0_status": "NOT_PASSED", "production": "NO_GO",
    }
    return summary


def main(argv):
    if (len(argv) == 5 and argv[1] == "--execute-live"):
        # Not invoked by any CI or ChatGPT workflow. Requires owner action
        # after separate exact SHA/code/run review and fresh authorization.
        result = run_owner_approved_once(
            Path(argv[2]), argv[3], argv[4])
    elif len(argv) == 9 and argv[1] == "--child":
        root, evidence = Path(argv[2]), Path(argv[3])
        result = _child(root, evidence, bytes.fromhex(argv[4]),
                        argv[5], argv[6], int(argv[7]), float(argv[8]))
    else:
        raise ValueError("F0_PHYSICAL_NO_IMPLICIT_LIVE_ENTRY")
    print(json.dumps(result, sort_keys=True), flush=True)


if __name__ == "__main__":
    main(sys.argv)
