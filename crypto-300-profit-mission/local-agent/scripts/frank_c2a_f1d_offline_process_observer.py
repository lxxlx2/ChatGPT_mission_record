"""F1d inert, bounded bootstrap observation simulator. NEVER runs a command.

Consumes preconstructed synthetic pipe/exit events. This is NOT a subprocess
supervisor, launchctl wrapper, Dashboard launcher or authenticated OS probe.
Limits bound memory retained *after each input event*, not upstream pipe I/O.
Only fully observed (both EOF + exit, no truncation) failures may be translated
to the approved F1 offline evidence format; all other states must stay unknown.
"""
from __future__ import annotations

import subprocess
from dataclasses import dataclass
from typing import Iterable

PHASE = "DASHBOARD_BOOTSTRAP"
MAX_EVENT_BYTES = 4096
MAX_STREAM_BYTES = 8192
MAX_EVENTS = 256
DEADLINE_MS = 30_000


@dataclass(frozen=True)
class PipeData:
    at_ms: int
    stream: str  # stdout | stderr
    data: bytes


@dataclass(frozen=True)
class PipeEOF:
    at_ms: int
    stream: str  # stdout | stderr


@dataclass(frozen=True)
class ChildExit:
    at_ms: int
    returncode: int  # signed subprocess code, 0 is success


@dataclass(frozen=True)
class DeadlineReached:
    at_ms: int


@dataclass(frozen=True)
class Interrupted:
    at_ms: int


Event = PipeData | PipeEOF | ChildExit | DeadlineReached | Interrupted


@dataclass(frozen=True)
class Observed:
    status: str
    returncode: int | None
    stdout: bytes
    stderr: bytes
    stdout_eof: bool
    stderr_eof: bool
    events_seen: int
    elapsed_ms: int
    # Raw streams can contain private data. Never log/serialize this object.


def observe_synthetic_stream(events: Iterable[Event]) -> Observed:
    """Process only inert fixture events in fixed bounded space.

    Consumes at most MAX_EVENTS+1 events, counts only strictly typed inputs,
    enforces non-decreasing fixture monotonic milliseconds and never hashes
    an unknown/uncaptured remainder as if it were a complete stream.
    This CANNOT bound a blocking generator or a real child process.
    """
    out = bytearray()
    err = bytearray()
    stdout_eof = False
    stderr_eof = False
    rc = None
    seen = 0
    clock = 0
    final = False

    def receipt(status: str) -> Observed:
        return Observed(
            status=status, returncode=rc,
            stdout=bytes(out), stderr=bytes(err),
            stdout_eof=stdout_eof, stderr_eof=stderr_eof,
            events_seen=seen, elapsed_ms=clock,
        )

    for event in events:
        seen += 1
        if seen > MAX_EVENTS:
            return receipt("EVENT_BUDGET_EXCEEDED")
        if type(event) not in (PipeData, PipeEOF, ChildExit, DeadlineReached, Interrupted):
            return receipt("INVALID_EVENT")
        at = event.at_ms
        if type(at) is not int or at < clock or at < 0:
            return receipt("INVALID_EVENT_CLOCK")
        clock = at
        if clock > DEADLINE_MS:
            return receipt("DEADLINE_EXCEEDED")
        if final:
            return receipt("INVALID_TRAILING_EVENT")
        if type(event) is PipeData:
            if event.stream not in ("stdout", "stderr") or type(event.data) is not bytes:
                return receipt("INVALID_PIPE_DATA")
            if len(event.data) > MAX_EVENT_BYTES:
                return receipt("CHUNK_BUDGET_EXCEEDED")
            target = out if event.stream == "stdout" else err
            if (stdout_eof if event.stream == "stdout" else stderr_eof):
                return receipt("DATA_AFTER_EOF")
            remaining = MAX_STREAM_BYTES - len(target)
            if len(event.data) > remaining:
                target.extend(event.data[:remaining])
                return receipt("STREAM_BUDGET_EXCEEDED")
            target.extend(event.data)
        elif type(event) is PipeEOF:
            if event.stream not in ("stdout", "stderr"):
                return receipt("INVALID_PIPE_EOF")
            if event.stream == "stdout":
                if stdout_eof:
                    return receipt("DUPLICATE_EOF")
                stdout_eof = True
            else:
                if stderr_eof:
                    return receipt("DUPLICATE_EOF")
                stderr_eof = True
        elif type(event) is ChildExit:
            if type(event.returncode) is not int or rc is not None:
                return receipt("INVALID_CHILD_EXIT")
            rc = event.returncode
        elif type(event) is DeadlineReached:
            return receipt("DEADLINE_REACHED")
        else:
            return receipt("INTERRUPTED")
        final = rc is not None and stdout_eof and stderr_eof

    if rc is None:
        return receipt("MISSING_EXIT")
    if not (stdout_eof and stderr_eof):
        return receipt("INCOMPLETE_PIPE_CAPTURE")
    return receipt("COMPLETE_SUCCESS" if rc == 0 else "COMPLETE_FAILURE")


def to_f1_failed_result(observed: Observed) -> subprocess.CompletedProcess:
    """Translate ONLY complete failed synthetic pipe capture to F1 input.

    A truncated/missing pipe or an event budget/timeout is not proof that
    the stream was captured completely. Never create a fake failed returncode
    or pass only a prefix to F1 as if it were a complete stream.
    """
    if type(observed) is not Observed or (
        observed.status != "COMPLETE_FAILURE"
        or type(observed.returncode) is not int
        or observed.returncode == 0
        or observed.stdout_eof is not True
        or observed.stderr_eof is not True
    ):
        raise ValueError("F1D_COMPLETE_FAILURE_REQUIRED")
    return subprocess.CompletedProcess(
        args=["SYNTHETIC_DASHBOARD_BOOTSTRAP_ONLY"],
        returncode=observed.returncode,
        stdout=observed.stdout,
        stderr=observed.stderr,
    )


def safe_status(observed: Observed) -> dict[str, str | int | bool]:
    """Safe administrative status without argv, paths or unredacted bytes."""
    if type(observed) is not Observed:
        raise ValueError("F1D_OBSERVATION_REQUIRED")
    return {
        "phase": PHASE,
        "status": observed.status,
        "returncode_known": observed.returncode is not None,
        "stdout_eof": observed.stdout_eof,
        "stderr_eof": observed.stderr_eof,
        "events_seen": observed.events_seen,
        "elapsed_ms": observed.elapsed_ms,
        "output_bytes_published": False,
        "production_probe": False,
    }
