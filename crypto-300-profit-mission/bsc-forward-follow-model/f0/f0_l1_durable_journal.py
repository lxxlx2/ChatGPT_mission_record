#!/usr/bin/env python3
"""Network-free, audit-first JSON-RPC request journal shared by offline and live callers.

The *caller* owns the sender and approval. This module imports no socket,
urllib, ssl, subprocess, login, scheduler or wallet tools. It cannot determine
whether a caller-supplied post callback is authorized or actually uses network.
"""
from __future__ import annotations

from datetime import datetime
import hashlib
import json
import os
from pathlib import Path

from f0_l1_http_wire import ENDPOINT, MAX_BODY_BYTES, json_body, parse_http_response

SCHEMA = "bsc-f0-l1-short-http-single-use-v1"


def require(ok, code):
    if not ok:
        raise ValueError(code)


def iso(now: datetime) -> str:
    return now.isoformat(timespec="milliseconds").replace("+00:00", "Z")


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def fsync_directory(directory: Path) -> None:
    """Persist directory entries for journal/raw evidence."""
    fd = os.open(directory, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def atomic_json(out: Path, data: dict) -> None:
    """Atomic 0600 JSON write, file fsync + parent-directory fsync."""
    require(not out.is_symlink(), "OUTPUT_SYMLINK_FORBIDDEN")
    temp = out.with_name(out.name + ".tmp." + str(os.getpid()))
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(temp, flags, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as dest:
            json.dump(data, dest, sort_keys=True, indent=2)
            dest.write("\n")
            dest.flush()
            os.fsync(dest.fileno())
        os.replace(temp, out)
        fsync_directory(out.parent)
    finally:
        if temp.exists():
            temp.unlink()


class Journal:
    """Permanently charges a request attempt *before* invoking its sender.

    Same external constructor/request contract and on-disk schema as the
    original f0_l1_live_short.Journal. No retry or network implementation.
    """

    timeout_seconds = 5.0
    response_cap = MAX_BODY_BYTES

    def __init__(self, path, *, limit, clock, mono, sleep, interval_ms,
                 deadline, raw_dir):
        self.path, self.limit, self.clock, self.mono, self.sleep = (
            path, limit, clock, mono, sleep)
        self.interval_ms, self.deadline, self.raw_dir = interval_ms, deadline, raw_dir
        # A new session must never reset a durable attempt count or UNKNOWN state.
        # Do not silently resume a consumed/partially used one-use permit.
        require(not path.exists() and not path.is_symlink(),
                "CAPTURE_JOURNAL_ALREADY_EXISTS")
        self.rows = []
        self.last_attempt_mono = None
        self.raw_dir.mkdir(mode=0o700)
        fsync_directory(self.raw_dir.parent)
        self.persist()

    def persist(self):
        atomic_json(self.path, {"schema": SCHEMA, "attempted_calls": len(self.rows),
                               "attempts": self.rows, "provider_billed": "UNVERIFIED"})

    def request(self, method, params, category, post):
        require(len(self.rows) < self.limit, "CAPTURE_CALL_CAP_REACHED")
        if self.last_attempt_mono is not None:
            delta = self.interval_ms/1000 - (self.mono()-self.last_attempt_mono)
            if delta > 0:
                self.sleep(delta)
        require(self.clock() <= self.deadline, "CAPTURE_DEADLINE_EXPIRED")
        idx = len(self.rows) + 1
        payload = {"jsonrpc": "2.0", "id": idx, "method": method, "params": params}
        encoded = json_body(payload)
        before = self.clock()
        start_mono = self.mono()
        item = {
            "index": idx, "method": method, "params": params, "category": category,
            "requested_utc": iso(before),
            "requested_monotonic_ns": int(start_mono*1e9),
            "state": "ATTEMPTED_OUTCOME_UNKNOWN",
        }
        self.rows.append(item)
        self.last_attempt_mono = start_mono
        self.persist()  # fsync must complete before any caller-provided post.
        require(self.clock() <= self.deadline, "CAPTURE_DEADLINE_EXPIRED")
        result, failure, raw = None, None, None
        try:
            status, headers, raw = post(ENDPOINT, encoded,
                                        self.timeout_seconds, self.response_cap)
            result = parse_http_response(status, headers, raw, payload,
                                         max_bytes=self.response_cap)
        except Exception as exc:
            # urllib.error.HTTPError/URLError subclass OSError, without importing
            # the production HTTP module into this transport-free journal.
            if isinstance(exc, TimeoutError):
                failure = "NETWORK_TIMEOUT"
            elif isinstance(exc, (ConnectionError, OSError)):
                failure = "NETWORK_ERROR_OR_HTTP_ERROR"
            elif isinstance(exc, ValueError):
                failure = "INVALID_HTTP_OR_RPC_RESPONSE"
            else:
                failure = "SOURCE_EXCEPTION"
        # BaseException/KeyboardInterrupt leaves already-durable UNKNOWN state.
        finished = self.clock()
        item.update(
            completed_utc=iso(finished),
            completed_monotonic_ns=int(self.mono()*1e9),
            state="RPC_RESPONSE" if result is not None else "FAILED",
            response_sha256=sha(raw) if type(raw) is bytes else None,
            failure_code=failure,
        )
        if raw is not None and type(raw) is bytes:
            artifact = self.raw_dir / ("%03d.response.json" % idx)
            with artifact.open("xb") as output:
                os.chmod(artifact, 0o600)
                output.write(raw)
                output.flush()
                os.fsync(output.fileno())
            fsync_directory(self.raw_dir)
            item["local_raw_response_file"] = artifact.name
        self.persist()
        return result, failure, item
