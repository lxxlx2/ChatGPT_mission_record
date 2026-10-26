"""F1 OFFLINE-ONLY failure evidence gate; deliberately does NOT execute a command.

Accept only a pre-existing subprocess.CompletedProcess-like result (synthetic tests).
This module is NOT wired into Dashboard, launchd, install/release code or production.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
import stat
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

CAPTURE_LIMIT = 8192
RECORD_FILENAME = "first-bootstrap-attempt.json"
_ALLOWED_PHASES = frozenset({"DASHBOARD_BOOTSTRAP"})


class EvidenceGateError(RuntimeError):
    pass


def _require_private_dir(directory: Path) -> int:
    p = Path(directory)
    if p.is_symlink():
        raise EvidenceGateError("EVIDENCE_DIR_SYMLINK")
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(p, flags)
    except OSError as exc:
        raise EvidenceGateError("EVIDENCE_DIR_UNAVAILABLE") from exc
    info = os.fstat(fd)
    if not stat.S_ISDIR(info.st_mode) or stat.S_IMODE(info.st_mode) != 0o700 or info.st_uid != os.getuid():
        os.close(fd)
        raise EvidenceGateError("EVIDENCE_DIR_NOT_PRIVATE")
    return fd


def _bytes(value: bytes | str | None) -> bytes:
    if value is None:
        return b""
    if isinstance(value, bytes):
        return value
    if isinstance(value, str):
        return value.encode("utf-8", errors="surrogateescape")
    raise EvidenceGateError("EVIDENCE_STREAM_INVALID")


def _stream_record(value: bytes | str | None) -> dict:
    raw = _bytes(value)
    return {
        "total_bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "captured_bytes": min(len(raw), CAPTURE_LIMIT),
        "truncated": len(raw) > CAPTURE_LIMIT,
        "captured_base64": base64.b64encode(raw[:CAPTURE_LIMIT]).decode("ascii"),
    }


def persist_failed_bootstrap(
    private_dir: Path,
    result: subprocess.CompletedProcess,
    *,
    phase: str = "DASHBOARD_BOOTSTRAP",
    recorded_at_utc: datetime | None = None,
) -> Path:
    """Durably write one private result, never argv, never overwrite old evidence.

    File is 0600 inside pre-existing owner-owned 0700 directory. Atomic hard link
    publishes only after a private temp file is fsynced; directory fsync completes
    before this returns. The original stdout/stderr are retained *up to* 8192
    bytes each, with whole-stream SHA, size and explicit truncation indicators.
    Do not upload this file or the raw streams to GitHub.
    """
    if phase not in _ALLOWED_PHASES:
        raise EvidenceGateError("EVIDENCE_PHASE_NOT_ALLOWED")
    if type(result.returncode) is not int or result.returncode == 0:
        raise EvidenceGateError("EVIDENCE_REQUIRES_FAILED_PROCESS")
    observed = recorded_at_utc or datetime.now(timezone.utc)
    if observed.tzinfo is None or observed.utcoffset() != timezone.utc.utcoffset(observed):
        raise EvidenceGateError("EVIDENCE_TIMESTAMP_NOT_UTC")
    record = {
        "schema": "FRANK_C2A_F1_OFFLINE_FAILURE_V1",
        "phase": phase,
        "observed_at_utc": observed.isoformat(),
        "returncode": result.returncode,
        "stdout": _stream_record(result.stdout),
        "stderr": _stream_record(result.stderr),
        "argv_saved": False,
        "origin": "INJECTED_COMPLETED_PROCESS_ONLY",
    }
    payload = (json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    directory_fd = _require_private_dir(private_dir)
    temp_name = ".bootstrap-attempt." + secrets.token_hex(12) + ".tmp"
    fd = None
    try:
        # No accidental replacement, even across concurrent retry attempts.
        try:
            os.stat(RECORD_FILENAME, dir_fd=directory_fd, follow_symlinks=False)
        except FileNotFoundError:
            pass
        else:
            raise EvidenceGateError("EVIDENCE_ALREADY_EXISTS")
        fd = os.open(temp_name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o600, dir_fd=directory_fd)
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "wb", closefd=False) as out:
            out.write(payload)
            out.flush()
            os.fsync(fd)
        # Atomic no-replace publication: filesystem-level link fails if final exists.
        try:
            os.link(temp_name, RECORD_FILENAME, src_dir_fd=directory_fd, dst_dir_fd=directory_fd, follow_symlinks=False)
        except FileExistsError as exc:
            raise EvidenceGateError("EVIDENCE_ALREADY_EXISTS") from exc
        os.fsync(directory_fd)
        os.unlink(temp_name, dir_fd=directory_fd)
        os.fsync(directory_fd)
        # Verify complete published bytes, private mode, and checksum before release.
        read_fd = os.open(RECORD_FILENAME, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0), dir_fd=directory_fd)
        try:
            info = os.fstat(read_fd)
            with os.fdopen(read_fd, "rb", closefd=False) as inp:
                check = inp.read()
            if (not stat.S_ISREG(info.st_mode) or stat.S_IMODE(info.st_mode) != 0o600
                    or info.st_uid != os.getuid() or check != payload):
                raise EvidenceGateError("EVIDENCE_READBACK_MISMATCH")
        finally:
            os.close(read_fd)
        return Path(private_dir) / RECORD_FILENAME
    except OSError as exc:
        raise EvidenceGateError("EVIDENCE_PERSIST_FAILED") from exc
    finally:
        if fd is not None:
            os.close(fd)
        try:
            os.unlink(temp_name, dir_fd=directory_fd)
        except FileNotFoundError:
            pass
        os.close(directory_fd)


def checkpoint_then_simulate_rollback(
    private_dir: Path,
    result: subprocess.CompletedProcess,
    simulated_rollback: Callable[[Path], None],
    *,
    recorded_at_utc: datetime | None = None,
) -> Path | None:
    """Synthetic ordering check only. Callback MUST be a test spy, not launchctl.

    Deliberately no subprocess.run, launchctl call, shell or production code path.
    """
    if type(result.returncode) is not int:
        raise EvidenceGateError("EVIDENCE_RETURN_CODE_INVALID")
    if result.returncode == 0:
        return None
    evidence = persist_failed_bootstrap(private_dir, result, recorded_at_utc=recorded_at_utc)
    simulated_rollback(evidence)
    return evidence
