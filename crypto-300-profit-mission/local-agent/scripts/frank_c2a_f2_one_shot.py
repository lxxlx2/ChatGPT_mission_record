"""Frank Dashboard-only one-shot cutover adapter. No CLI, no import-time effects.

LIVE invocation is a separate, explicitly approved integration step. This module
contains real bounded OS I/O and filesystem operations; tests MUST use fake
lifecycle/probes/scratch paths. Never pass a production plan from CI.
"""
from __future__ import annotations

import base64
import fcntl
import hashlib
import json
import os
import plistlib
import re
import selectors
import signal
import stat
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Protocol

APPROVED_SOURCE = "296f35a8b6dffe1b2384f77b8768aa799a68ed0d"
OLD_SOURCE = "914e9e47fed2e60bc24690fcb083413a64d4e681"
CAP = 8192
COMMAND_DEADLINE = 20.0
READ_CHUNK = 4096
FIRST_ATTEMPT_RECORD = "first-dashboard-bootstrap.json"
_HASH64 = re.compile(r"[0-9a-f]{64}\Z")


class GateError(RuntimeError):
    pass


@dataclass(frozen=True)
class Captured:
    status: str  # COMPLETE / TIMEOUT / INTERRUPTED / SPAWN_FAILED / INCOMPLETE
    returncode: int | None
    stdout: bytes
    stderr: bytes
    stdout_total: int
    stderr_total: int
    stdout_sha256: str  # empty when stream was not opened
    stderr_sha256: str
    stdout_eof: bool
    stderr_eof: bool
    stdout_truncated: bool
    stderr_truncated: bool

    @property
    def ok(self) -> bool:
        return self.status == "COMPLETE" and self.returncode == 0


def _kill_group(proc: subprocess.Popen) -> None:
    # A new session is created for every command. Kill the group so descendant
    # holders of stdout/stderr cannot leave our reader waiting forever.
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    except PermissionError:
        proc.kill()


def bounded_command(argv: tuple[str, ...], *, timeout: float = COMMAND_DEADLINE) -> Captured:
    """Real OS command, strictly bounded stdout/stderr *storage* and deadline.

    Streams are drained into hashes/counters in fixed chunks; retained memory
    is at most CAP bytes per stream. Timeout kills the whole process group.
    Outputs may contain secrets: NEVER copy Captured into public logs.
    """
    if os.name != "posix" or not argv or not all(type(a) is str and a for a in argv):
        raise GateError("INVALID_OS_OR_ARGV")
    if not (0 < timeout <= 30):
        raise GateError("INVALID_COMMAND_DEADLINE")
    p = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, close_fds=True, start_new_session=True)
    sel = None
    buffers = {"stdout": bytearray(), "stderr": bytearray()}
    counters = {"stdout": 0, "stderr": 0}
    digests = {"stdout": hashlib.sha256(), "stderr": hashlib.sha256()}
    eof = {"stdout": False, "stderr": False}
    timed_out = False
    try:
        sel = selectors.DefaultSelector()
        for name, pipe in (("stdout", p.stdout), ("stderr", p.stderr)):
            os.set_blocking(pipe.fileno(), False)
            sel.register(pipe, selectors.EVENT_READ, name)
        deadline = time.monotonic() + timeout
        while sel.get_map() or p.poll() is None:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                timed_out = True
                break
            for key, _ in sel.select(min(0.1, remaining)):
                name = key.data
                try:
                    chunk = os.read(key.fileobj.fileno(), READ_CHUNK)
                except BlockingIOError:
                    continue
                if not chunk:
                    eof[name] = True
                    sel.unregister(key.fileobj)
                    continue
                counters[name] += len(chunk)
                digests[name].update(chunk)
                space = CAP - len(buffers[name])
                if space > 0:
                    buffers[name].extend(chunk[:space])
        if timed_out:
            _kill_group(p)
        # A timeout is never reported as complete even if exit arrives during cleanup.
        if timed_out:
            cutoff = time.monotonic() + 0.4
            while sel.get_map() and time.monotonic() < cutoff:
                for key, _ in sel.select(0.05):
                    name = key.data
                    chunk = os.read(key.fileobj.fileno(), READ_CHUNK)
                    if not chunk:
                        eof[name] = True
                        sel.unregister(key.fileobj)
                    else:
                        counters[name] += len(chunk)
                        digests[name].update(chunk)
                        buffers[name].extend(chunk[:max(0, CAP - len(buffers[name]))])
        try:
            rc = p.wait(timeout=1)
        except subprocess.TimeoutExpired:
            _kill_group(p)
            rc = p.wait(timeout=1)
        status = "TIMEOUT" if timed_out else ("COMPLETE" if all(eof.values()) else "INCOMPLETE")
        return Captured(status, None if timed_out else rc, bytes(buffers["stdout"]), bytes(buffers["stderr"]),
                        counters["stdout"], counters["stderr"],
                        digests["stdout"].hexdigest(), digests["stderr"].hexdigest(),
                        eof["stdout"], eof["stderr"],
                        counters["stdout"] > CAP, counters["stderr"] > CAP)
    except BaseException:
        _kill_group(p)
        try:
            p.wait(timeout=1)
        except (subprocess.TimeoutExpired, OSError):
            pass
        raise
    finally:
        if sel is not None:
            sel.close()
        p.stdout.close()
        p.stderr.close()


def _private_dir(path: Path) -> int:
    if path.is_symlink():
        raise GateError("EVIDENCE_SYMLINK_DIR")
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(path, flags)
    st = os.fstat(fd)
    if not stat.S_ISDIR(st.st_mode) or st.st_uid != os.getuid() or stat.S_IMODE(st.st_mode) != 0o700:
        os.close(fd)
        raise GateError("EVIDENCE_DIR_NOT_PRIVATE")
    return fd


def _write_private_once(directory: Path, name: str, body: bytes) -> None:
    if not re.fullmatch(r"[a-z0-9-]+\.json|[a-z0-9-]+\.bin", name):
        raise GateError("EVIDENCE_BAD_NAME")
    dfd = _private_dir(directory)
    tmp = f".temp-{os.getpid()}-{os.urandom(8).hex()}"
    try:
        fd = os.open(tmp, os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_NOFOLLOW", 0),
                     0o600, dir_fd=dfd)
        try:
            with os.fdopen(fd, "wb", closefd=False) as out:
                out.write(body)
                out.flush()
                os.fsync(fd)
        finally:
            os.close(fd)
        os.link(tmp, name, src_dir_fd=dfd, dst_dir_fd=dfd, follow_symlinks=False)
        os.fsync(dfd)
        os.unlink(tmp, dir_fd=dfd)
        os.fsync(dfd)
        check_fd = os.open(name, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0), dir_fd=dfd)
        try:
            st = os.fstat(check_fd)
            if st.st_uid != os.getuid() or stat.S_IMODE(st.st_mode) != 0o600:
                raise GateError("EVIDENCE_BAD_MODE")
            with os.fdopen(check_fd, "rb", closefd=False) as inp:
                if inp.read() != body:
                    raise GateError("EVIDENCE_READBACK_MISMATCH")
        finally:
            os.close(check_fd)
    finally:
        try:
            os.unlink(tmp, dir_fd=dfd)
        except FileNotFoundError:
            pass
        os.close(dfd)


def _stream_details(data: bytes, total: int, digest: str, eof: bool, truncated: bool) -> dict:
    return {"bytes_observed": total, "sha256_observed": digest,
            "captured_base64": base64.b64encode(data).decode("ascii"),
            "captured_bytes": len(data), "eof_seen": eof, "truncated": truncated}


def save_first_attempt(directory: Path, result: Captured | None, *, phase: str) -> None:
    if phase not in ("BOOTSTRAP_RESULT", "BOOTSTRAP_INTERRUPTED", "BOOTSTRAP_EXCEPTION"):
        raise GateError("EVIDENCE_PHASE_INVALID")
    record = {"version": 1, "phase": phase, "candidate_source": APPROVED_SOURCE,
              "observed_at_unix": time.time(), "command_arguments_saved": False}
    if result is None:
        record.update({"status": "UNOBSERVED", "returncode": None,
                       "stdout": {"state": "NOT_CAPTURED"}, "stderr": {"state": "NOT_CAPTURED"}})
    else:
        record.update({"status": result.status, "returncode": result.returncode,
                       "stdout": _stream_details(result.stdout, result.stdout_total,
                                                result.stdout_sha256, result.stdout_eof,
                                                result.stdout_truncated),
                       "stderr": _stream_details(result.stderr, result.stderr_total,
                                                result.stderr_sha256, result.stderr_eof,
                                                result.stderr_truncated)})
    _write_private_once(directory, FIRST_ATTEMPT_RECORD,
                        (json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n").encode())


def _runner_bytes(path: Path) -> tuple[bytes, int]:
    st = path.lstat()
    if not stat.S_ISREG(st.st_mode) or st.st_uid != os.getuid():
        raise GateError("RUNNER_NOT_OWNED_REGULAR_FILE")
    return path.read_bytes(), stat.S_IMODE(st.st_mode)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _one_line_change(old: bytes, new: bytes) -> bool:
    a, b = old.splitlines(keepends=True), new.splitlines(keepends=True)
    if len(a) != len(b):
        return False
    delta = [(x, y) for x, y in zip(a, b) if x != y]
    return len(delta) == 1 and delta[0][0].startswith(b"LOCAL_AGENT=") and delta[0][1].startswith(b"LOCAL_AGENT=")


def atomic_runner(path: Path, expected_old: bytes, new: bytes, mode: int, arm: Callable[[], None]) -> None:
    """arm BEFORE os.replace: fsync after replace may throw with NEW still live."""
    data, original_mode = _runner_bytes(path)
    if data != expected_old or original_mode != mode:
        raise GateError("RUNNER_CONCURRENT_DRIFT")
    tmp_name = None
    try:
        fd, tmp_name = tempfile.mkstemp(prefix=".frank-f2-", dir=path.parent)
        os.fchmod(fd, mode)
        with os.fdopen(fd, "wb") as out:
            out.write(new)
            out.flush()
            os.fsync(out.fileno())
        # Future rollback must treat any exception from here as changed/unknown.
        arm()
        os.replace(tmp_name, path)
        tmp_name = None
        dfd = os.open(path.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(dfd)
        finally:
            os.close(dfd)
    finally:
        if tmp_name is not None:
            try:
                os.unlink(tmp_name)
            except FileNotFoundError:
                pass


@dataclass(frozen=True)
class Identity:
    source_sha: str
    runner_sha256: str
    dashboard_label: str
    listener: str
    dashboard_healthy: bool
    protected_fingerprint: str


@dataclass(frozen=True)
class Plan:
    runner: Path
    plist: Path
    label: str
    evidence_dir: Path
    approved_new_runner: bytes
    old_runner_sha256: str
    new_runner_sha256: str
    approved_source_sha: str = APPROVED_SOURCE
    old_source_sha: str = OLD_SOURCE


@dataclass(frozen=True)
class Verdict:
    status: str
    bootstrap_status: str
    first_attempt_evidence: str
    rollback_attempts: int
    rollback_verified: bool
    # Never include paths, process argv or raw stderr/stdout.


class Lifecycle(Protocol):
    def bootout(self) -> Captured: ...
    def bootstrap(self) -> Captured: ...


class MacDashboardLifecycle:
    """Real, bounded launchctl calls for a future separately authorized caller.

    Constructing the object or importing the module performs NO subprocess.
    No broad installer, no kickstart, no Loop/V1 commands.
    """
    def __init__(self, plan: Plan):
        if os.uname().sysname != "Darwin":
            raise GateError("DARWIN_ONLY")
        if not re.fullmatch(r"com\.[A-Za-z0-9_.-]+\.frank-meme\.dashboard", plan.label):
            raise GateError("LABEL_NOT_DASHBOARD")
        if plan.plist.is_symlink() or not plan.plist.is_file():
            raise GateError("DASHBOARD_PLIST_UNAVAILABLE")
        if plan.plist.name != plan.label + ".plist":
            raise GateError("PLIST_LABEL_FILENAME_MISMATCH")
        payload = plistlib.loads(plan.plist.read_bytes())
        if payload.get("Label") != plan.label:
            raise GateError("PLIST_LABEL_MISMATCH")
        self.domain = f"gui/{os.getuid()}"
        self.plist = str(plan.plist)

    def bootout(self) -> Captured:
        return bounded_command(("/bin/launchctl", "bootout", self.domain, self.plist))

    def bootstrap(self) -> Captured:
        return bounded_command(("/bin/launchctl", "bootstrap", self.domain, self.plist))


def _valid_plan(plan: Plan) -> None:
    if plan.approved_source_sha != APPROVED_SOURCE or plan.old_source_sha != OLD_SOURCE:
        raise GateError("SOURCE_SHA_UNAPPROVED")
    if not all(isinstance(v, str) and _HASH64.fullmatch(v) for v in
               (plan.old_runner_sha256, plan.new_runner_sha256)):
        raise GateError("RUNNER_HASH_BAD")
    if not re.fullmatch(r"com\.[A-Za-z0-9_.-]+\.frank-meme\.dashboard", plan.label):
        raise GateError("LABEL_BAD")
    if plan.plist.is_symlink() or plan.runner.is_symlink():
        raise GateError("LIVE_PATH_SYMLINK")
    if plan.runner.parent != plan.runner.resolve().parent:
        raise GateError("RUNNER_PARENT_DRIFT")
    if plan.evidence_dir.resolve() == plan.runner.parent.resolve():
        raise GateError("EVIDENCE_IN_PRODUCTION_RUNNER_DIR")


def _same_identity(observed: Identity, source: str, runner_digest: str,
                   label: str, protected: str) -> bool:
    return bool(isinstance(observed, Identity) and observed.source_sha == source
                and observed.runner_sha256 == runner_digest
                and observed.dashboard_label == label
                and observed.listener == "127.0.0.1:8766"
                and observed.dashboard_healthy is True
                and observed.protected_fingerprint == protected and protected)


def _execute_locked(plan: Plan, lifecycle: Lifecycle,
                 probe: Callable[[], Identity], *, authorized: bool = False) -> Verdict:
    """Real one-shot control flow; default DENY. Future Mac authorization required.

    The external probe must independently attest process/port/plist/interpreter,
    protected Loop/V1/D2/notifier state and live source/runner identity. This
    code does not invent those proofs. Never call in CI with authorized=True on
    live paths. A bool is NOT a permission system; owner approval is external.
    """
    if authorized is not True:
        raise GateError("LIVE_CUTOVER_NOT_AUTHORIZED")
    _valid_plan(plan)
    dfd = _private_dir(plan.evidence_dir)
    os.close(dfd)
    old, mode = _runner_bytes(plan.runner)
    if _sha(old) != plan.old_runner_sha256 or _sha(plan.approved_new_runner) != plan.new_runner_sha256:
        raise GateError("PINNED_RUNNER_BYTES_MISMATCH")
    if not _one_line_change(old, plan.approved_new_runner):
        raise GateError("RUNNER_NOT_SINGLE_LOCAL_AGENT_LINE")
    baseline = probe()
    if not _same_identity(baseline, OLD_SOURCE, plan.old_runner_sha256,
                          plan.label, baseline.protected_fingerprint):
        raise GateError("LIVE_BASELINE_NOT_VERIFIED")
    # Fail before any service operation if durable old-runner proof cannot be saved.
    _write_private_once(plan.evidence_dir, "old-dashboard-runner.bin", old)
    dirty = False
    evidence_status = "NOT_ATTEMPTED"
    bootstrap_status = "NOT_ATTEMPTED"
    risk = False
    attempt = 0

    def arm() -> None:
        nonlocal dirty
        dirty = True

    try:
        # After this point, the old Dashboard may be down, even if bootout
        # itself raises. All catchable exceptions require one rollback attempt.
        risk = True
        stop = lifecycle.bootout()
        if not isinstance(stop, Captured) or not stop.ok:
            raise GateError("BOOTOUT_FAILED_OR_UNVERIFIED")
        atomic_runner(plan.runner, old, plan.approved_new_runner, mode, arm)
        try:
            first = lifecycle.bootstrap()
        except BaseException as exc:
            bootstrap_status = "INTERRUPTED" if isinstance(exc, (KeyboardInterrupt, SystemExit)) else "EXCEPTION"
            try:
                save_first_attempt(plan.evidence_dir, None,
                                   phase="BOOTSTRAP_INTERRUPTED" if bootstrap_status == "INTERRUPTED" else "BOOTSTRAP_EXCEPTION")
                evidence_status = "RECORDED_MISSING_RESULT"
            except BaseException:
                evidence_status = "PERSIST_FAILED"
            raise
        bootstrap_status = first.status if isinstance(first, Captured) else "INVALID_CAPTURE"
        try:
            save_first_attempt(plan.evidence_dir, first if isinstance(first, Captured) else None,
                               phase="BOOTSTRAP_RESULT")
            evidence_status = "RECORDED"
        except BaseException:
            evidence_status = "PERSIST_FAILED"
            raise GateError("FIRST_ATTEMPT_EVIDENCE_UNAVAILABLE")
        if not isinstance(first, Captured) or not first.ok:
            raise GateError("BOOTSTRAP_FAILED_OR_INCOMPLETE")
        # Even a true rc=0 requires an independent real process/GET+protected
        # re-probe. A fake/old health response is NOT release success.
        after = probe()
        if not _same_identity(after, APPROVED_SOURCE, plan.new_runner_sha256,
                              plan.label, baseline.protected_fingerprint):
            raise GateError("AFTER_BOOTSTRAP_G3_OR_PROTECTED_DRIFT")
        # G4 is a second, independent protection observation after G3.
        final = probe()
        if not _same_identity(final, APPROVED_SOURCE, plan.new_runner_sha256,
                              plan.label, baseline.protected_fingerprint):
            raise GateError("AFTER_BOOTSTRAP_G4_LATE_DRIFT")
        return Verdict("CUTOVER_PROBE_PASS_NOT_DEPLOY_AUTH", bootstrap_status,
                       evidence_status, attempt, False)
    except BaseException:
        if not risk:
            raise
        attempt = 1
        # One restoration attempt, regardless of interrupted evidence/FSYNC.
        try:
            # Rewriting old bytes is safe even if replace failed before rename;
            # never rely on the "dirty" flag alone to decide restoration.
            current, current_mode = _runner_bytes(plan.runner)
            if current_mode != mode or _sha(current) not in (plan.old_runner_sha256, plan.new_runner_sha256):
                raise GateError("ROLLBACK_RUNNER_CONCURRENT_DRIFT")
            # A rc=0 candidate may still be registered when G3/G4 fails.
            # Remove only this Dashboard before restoring its runner. The stop
            # can be nonzero if the failed candidate never registered; it cannot
            # establish recovery success. Require the subsequent old bootstrap
            # AND the independent old identity/protected probe in either case.
            cleanup = lifecycle.bootout()
            if not isinstance(cleanup, Captured):
                raise GateError("ROLLBACK_STOP_UNOBSERVED")
            atomic_runner(plan.runner, current, old, mode, lambda: None)
            result = lifecycle.bootstrap()
            if not isinstance(result, Captured) or not result.ok:
                return Verdict("ROLLBACK_FAILED_STOP", bootstrap_status, evidence_status, attempt, False)
        except BaseException:
            return Verdict("ROLLBACK_FAILED_STOP", bootstrap_status, evidence_status, attempt, False)
        try:
            restored = probe()
            verified = _same_identity(restored, OLD_SOURCE, plan.old_runner_sha256,
                                      plan.label, baseline.protected_fingerprint)
            if not verified:
                return Verdict("ROLLBACK_UNVERIFIED_STOP", bootstrap_status, evidence_status, attempt, False)
            return Verdict("ROLLED_BACK_STOP", bootstrap_status, evidence_status, attempt, True)
        except BaseException:
            return Verdict("ROLLBACK_UNVERIFIED_STOP", bootstrap_status, evidence_status, attempt, False)


def execute_once(plan: Plan, lifecycle: Lifecycle,
                 probe: Callable[[], Identity], *, authorized: bool = False) -> Verdict:
    """Serialize cooperating callers across runner renames, without a lockfile.

    Lock the existing canonical parent directory, not the replaceable runner
    inode or a caller-selected evidence directory. This does not protect against
    malicious/noncooperating same-UID writers; live integration must exclude them.
    """
    if authorized is not True:
        raise GateError("LIVE_CUTOVER_NOT_AUTHORIZED")
    _valid_plan(plan)
    fd = os.open(plan.runner.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        if os.fstat(fd).st_uid != os.getuid():
            raise GateError("RUNNER_PARENT_NOT_OWNED")
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise GateError("ONE_SHOT_ALREADY_RUNNING") from exc
        return _execute_locked(plan, lifecycle, probe, authorized=authorized)
    finally:
        # close releases the advisory lock even on a caught interruption.
        os.close(fd)
