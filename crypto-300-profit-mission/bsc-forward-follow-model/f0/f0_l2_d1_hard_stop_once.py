#!/usr/bin/env python3
"""D1 bounded one-shot OS-process supervision, TEST transport ONLY.

Reuses the PR190 physical HTTPS constructor *call site* with an in-process
fake, the existing three-slot coordinator, and the already reviewed
OfflineGrantRegistry. This module intentionally cannot call the public BSC
network, enroll a production authorization, or claim a real throughput sample.

The parent permanently consumes a TEST marker BEFORE launching the child.
On hard timeout, kill/reap the entire single child. Journal reservations that
survive remain UNKNOWN; never resume or retry with this grant.
"""
from __future__ import annotations

import hashlib
import http.client
import json
import os
from pathlib import Path
import select
import socket
import stat
import threading
import subprocess
import sys
import tempfile
import time

from f0_l2_d1_grant import GRANT_ID, HEX64, OfflineGrantRegistry, PRIVATE_FIXED_REGISTRY
from f0_l2_d1_recovery import reconcile_saved_attempts

SCHEMA = "bsc-f0-d1-hard-stop-offline-once-v1"
_SCENARIOS = ("complete", "hang_after_reserve")
_MAX_TEST_SECONDS = 15.0

# Caps on synthetic replay. A supplied D3 candidate may only reduce these.
_OFFLINE_SCOPE_KEYS = frozenset({
    "max_total", "max_blocks", "max_refreshes", "spacing_ms",
    "slots", "head_ttl_ms", "window_ms", "timeout_ms",
})
_DEFAULT_OFFLINE_SCOPE = {
    "max_total": 6, "max_blocks": 3, "max_refreshes": 1,
    "spacing_ms": 250, "slots": 3, "head_ttl_ms": 4000,
    "window_ms": 5000, "timeout_ms": 5000,
}


def _validate_offline_scope(candidate):
    """Validate before any test marker, then repeat in isolated child."""
    if candidate is None:
        return dict(_DEFAULT_OFFLINE_SCOPE)
    if type(candidate) is not dict or set(candidate) != _OFFLINE_SCOPE_KEYS:
        raise ValueError("D1_CHILD_OFFLINE_SCOPE_FIELDS_INVALID")
    cap = _DEFAULT_OFFLINE_SCOPE
    for name, value in candidate.items():
        low = 0 if name == "max_refreshes" else 1
        if (type(value) is not int or value < low or
                (name not in ("spacing_ms",) and value > cap[name])):
            raise ValueError("D1_CHILD_OFFLINE_SCOPE_BUDGET_INVALID:" + name)
    if (not 2 <= candidate["max_total"] <=
            candidate["max_blocks"] + candidate["max_refreshes"] + 2
            or candidate["max_blocks"] < 1
            or candidate["slots"] != 3
            or not 250 <= candidate["spacing_ms"] <= 5000
            or not 500 <= candidate["head_ttl_ms"] <= 4000
            or not 1000 <= candidate["window_ms"] <= 5000
            or not 250 <= candidate["timeout_ms"] <= 5000):
        raise ValueError("D1_CHILD_OFFLINE_SCOPE_INCOHERENT")
    return dict(candidate)


def send_live(*_args, **_kwargs):
    raise ValueError("D1_HARD_STOP_LIVE_NOT_AUTHORIZED")


def _private_test_dir(path):
    if (not isinstance(path, Path) or not path.is_absolute() or path.is_symlink()
            or not path.is_dir() or path.stat().st_mode & 0o077):
        raise ValueError("D1_HARD_STOP_TEST_ROOT_NOT_PRIVATE")
    # The disposable test registry must have no possible overlap with the
    # permanent OS-user-bound production registry, including /var aliases.
    real = path.resolve()
    prod = PRIVATE_FIXED_REGISTRY.resolve()
    tmp = Path(tempfile.gettempdir()).resolve()
    if (not real.is_relative_to(tmp) or real == prod or
            real in prod.parents or prod in real.parents):
        raise ValueError("D1_HARD_STOP_TEST_ROOT_NOT_DISPOSABLE")
    return real


def _child_watchdog_exit(evidence: Path, reason: str):
    """Write private diagnostic then stop this *mock-only* child immediately."""
    try:
        p = evidence / "child_watchdog_termination.json"
        fd = os.open(p, os.O_CREAT | os.O_EXCL | os.O_WRONLY |
                     getattr(os, "O_NOFOLLOW", 0), 0o600)
        with os.fdopen(fd, "wb") as f:
            f.write((json.dumps({"reason": reason, "real_network": False},
                                sort_keys=True) + "\n").encode("ascii"))
            f.flush()
            os.fsync(f.fileno())
        dfd = os.open(evidence, os.O_RDONLY |
                      getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(dfd)
        finally:
            os.close(dfd)
    except (OSError, ValueError):
        # Diagnostic may be absent on hardware/storage failure; do not
        # wait, resume workers, clear UNKNOWN or retry the grant.
        pass
    os._exit(90 if reason == "PARENT_PIPE_CLOSED" else 91)


def _child_lifetime_watch(read_fd: int, deadline: float, evidence: Path):
    """Parent-loss detection via inherited pipe; independent monotonic cap.

    A surviving parent owns the only write end. A crashed/KILLed parent
    closes that end in the kernel, waking this watcher even if the main
    child thread is wedged in a synchronous mock connect.
    """
    while True:
        remaining = deadline + 0.75 - time.monotonic()
        if remaining <= 0:
            _child_watchdog_exit(evidence, "CHILD_ABSOLUTE_DEADLINE")
        try:
            ready, _, _ = select.select([read_fd], [], [], remaining)
            if ready:
                if os.read(read_fd, 1) == b"":
                    _child_watchdog_exit(evidence, "PARENT_PIPE_CLOSED")
                _child_watchdog_exit(evidence, "UNEXPECTED_PARENT_PIPE_DATA")
        except (OSError, ValueError):
            _child_watchdog_exit(evidence, "PARENT_LIVENESS_UNCERTAIN")


def run_bounded_offline_once(registry: Path, evidence: Path, *,
                             grant_id: str, permit_sha256: str,
                             scenario: str = "complete",
                             hard_seconds: float = 8.0,
                             offline_scope=None):
    """Exactly one disposable OFFLINE process, no network or automatic retry.

    This is deliberately not a production entry: no user D2/D3 approval may
    be passed or synthesized. The roots MUST already exist privately under
    the OS temporary directory. Every attempt spends the same once ID even
    if child startup fails or is killed before sending a synthetic request.
    """
    reg = _private_test_dir(registry)
    out = _private_test_dir(evidence)
    if (reg == out or reg in out.parents or out in reg.parents):
        raise ValueError("D1_HARD_STOP_TEST_ROOTS_OVERLAP")
    if (type(grant_id) is not str or not GRANT_ID.fullmatch(grant_id)
            or type(permit_sha256) is not str
            or not HEX64.fullmatch(permit_sha256)
            or scenario not in _SCENARIOS
            or type(hard_seconds) not in (float, int)
            or not 0.2 <= hard_seconds <= _MAX_TEST_SECONDS
            or any((out / x).exists() for x in
                   ("attempts.jsonl", "raw_responses"))):
        raise ValueError("D1_HARD_STOP_SCOPE_INVALID")
    # Scope validation precedes durable once consumption and subprocess.
    scope = _validate_offline_scope(offline_scope)
    if (offline_scope is not None and
            scope["window_ms"] > int(hard_seconds * 1000)):
        raise ValueError("D1_CHILD_OFFLINE_SCOPE_OUTLIVES_HARD_STOP")
    # Durable, one-use TEST grant must be spent before even creating a child.
    lease = OfflineGrantRegistry(reg).consume(grant_id, permit_sha256)
    # The kernel pipe is a parent-lifetime lease, NOT a D2/D3 grant.
    # Pass only its read end into the mock child; its single write end stays
    # exclusively with the supervisor. Any parent SIGKILL closes it.
    read_fd, write_fd = os.pipe()
    start = time.monotonic()
    cmd = (sys.executable, "-B", str(Path(__file__).resolve()),
           "--offline-child", str(out), str(reg), grant_id,
           permit_sha256, scenario, str(read_fd),
           repr(start + hard_seconds),
           json.dumps(scope, sort_keys=True, separators=(",", ":")).encode().hex())
    try:
        proc = subprocess.Popen(
            cmd, stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, close_fds=True, pass_fds=(read_fd,))
    finally:
        os.close(read_fd)
    timed_out = False
    try:
        try:
            stdout, stderr = proc.communicate(timeout=hard_seconds)
        except subprocess.TimeoutExpired:
            timed_out = True
            # Child-side guardian remains active even if parent crashes.
            proc.kill()
            stdout, stderr = proc.communicate()
    finally:
        os.close(write_fd)
    elapsed = time.monotonic() - start
    if (out / "attempts.jsonl").exists():
        try:
            audit = reconcile_saved_attempts(out)
        except (ValueError, OSError):
            audit = {"audit_status": "INVALID_OR_TRUNCATED_NO_RETRY"}
    else:
        audit = {"audit_status": "NO_JOURNAL_MARKER_SPENT_NO_RETRY"}
    completed = proc.returncode == 0 and not timed_out
    parsed = None
    if completed:
        try:
            parsed = json.loads(stdout)
            if (parsed["network_requests"] != 0 or
                    parsed["no_live_sender"] is not True):
                completed = False
        except (ValueError, KeyError, TypeError):
            completed = False
    return {
        "schema": SCHEMA, "scenario": scenario,
        "state": ("OFFLINE_CHILD_EXITED_ACCOUNTED" if completed else
                  "HARD_STOP_KILLED_NO_RETRY" if timed_out else
                  "CHILD_FAILED_OR_UNKNOWN_NO_RETRY"),
        "elapsed_s": round(elapsed, 3),
        "child_exit_code": proc.returncode,
        "test_grant_id_sha256": hashlib.sha256(grant_id.encode()).hexdigest(),
        "lease": lease["status"],
        "effective_offline_scope": scope,
        "audit": audit,
        "offline_child": parsed if completed else None,
        "live_network_requests": 0,
        "no_automatic_retry": True, "real_d2_approved": False,
        "real_d3_approved": False, "production": "NO_GO",
    }


def _offline_child(evidence: Path, registry: Path, grant_id: str,
                   digest: str, scenario: str, scope=None):
    """Private subprocess fixture; never a real socket/production runner."""
    from f0_l2_d1_concrete_https import PatchedConstructorOfflineSource
    from f0_l2_d1_coordinator import FakeSource, run_fake_concurrent
    if scenario not in _SCENARIOS:
        raise ValueError("D1_HARD_STOP_BAD_SCENARIO")
    scope = _validate_offline_scope(scope)
    _private_test_dir(evidence)
    reg = _private_test_dir(registry)
    marker = reg / (hashlib.sha256(grant_id.encode()).hexdigest()
                    + ".consumed.json")
    if (not marker.is_file() or marker.is_symlink()
            or marker.stat().st_mode & 0o077):
        raise ValueError("D1_HARD_STOP_MISSING_TEST_LEASE")
    saved = json.loads(marker.read_text())
    if (saved.get("permit_sha256") != digest or
            saved.get("outcome") != "CONSUMED_OR_UNKNOWN"):
        raise ValueError("D1_HARD_STOP_TEST_LEASE_MISMATCH")

    def forbidden(*_args, **_kwargs):
        raise AssertionError("D1_HARD_STOP_REAL_SOCKET_FORBIDDEN")

    source = PatchedConstructorOfflineSource(delay_ms=15, growth_bps=10.0)
    class Response:
        def __init__(self, frame):
            self.status, headers, self.body = frame
            self.headers = list(headers.items())
        def getheaders(self):
            return self.headers
        def read(self, size):
            return self.body[:size]

    class Connection:
        def __init__(self, host, *, port, timeout, context):
            if (host != "bsc-dataseed.bnbchain.org" or port != 443
                    or not 0 < timeout <= 5
                    or not context.check_hostname):
                raise ValueError("D1_HARD_STOP_FIXED_TRANSPORT_SCOPE")
            self.sock = None
            self.request_json = None
        def connect(self):
            if scenario == "hang_after_reserve":
                time.sleep(30)
            self.sock = object()
        def request(self, method, path, *, body, headers):
            if (method != "POST" or path != "/"
                    or headers.get("Host") != "bsc-dataseed.bnbchain.org"):
                raise ValueError("D1_HARD_STOP_UNEXPECTED_HTTP_REQUEST")
            self.request_json = json.loads(body)
        def getresponse(self):
            return Response(FakeSource.reply(source, self.request_json))
        def close(self):
            self.sock = None

    # Source checks that HTTPSConnection is a patched constructor. Also
    # disable socket.create_connection to stop accidental real networking.
    original_ctor = http.client.HTTPSConnection
    original_socket = socket.create_connection
    try:
        http.client.HTTPSConnection = Connection
        socket.create_connection = forbidden
        result = run_fake_concurrent(
            source, evidence,
            max_total=scope["max_total"],
            max_blocks=scope["max_blocks"],
            max_refreshes=scope["max_refreshes"],
            spacing_ms=scope["spacing_ms"], slots=scope["slots"],
            head_ttl_ms=scope["head_ttl_ms"],
            window_ms=scope["window_ms"],
            max_block_response_ms=scope["timeout_ms"],
            head_min_poll_age_ms=250)
    finally:
        http.client.HTTPSConnection = original_ctor
        socket.create_connection = original_socket
    return result


def _main(argv):
    # This entry exists solely to run a supervised synthetic child.
    if len(argv) not in (9, 10) or argv[1] != "--offline-child":
        raise ValueError("D1_HARD_STOP_NO_PUBLIC_LIVE_CLI")
    evidence = Path(argv[2])
    registry = Path(argv[3])
    read_fd = int(argv[7])
    deadline = float(argv[8])
    # Reject absent/forged inherited descriptors before any coordinator
    # work. The pipe is intentionally a liveness proof, not a network grant.
    if (read_fd < 3 or not stat.S_ISFIFO(os.fstat(read_fd).st_mode)
            or deadline <= time.monotonic()
            or deadline - time.monotonic() > _MAX_TEST_SECONDS + 1):
        raise ValueError("D1_HARD_STOP_CHILD_GUARD_INVALID")
    _private_test_dir(evidence)
    if len(argv) == 10:
        try:
            scope = _validate_offline_scope(json.loads(bytes.fromhex(argv[9])))
        except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("D1_CHILD_SCOPE_SERIALIZATION_INVALID") from exc
    else:
        scope = _validate_offline_scope(None)
    if (len(argv) == 10 and
            scope["window_ms"] > int((deadline - time.monotonic()) * 1000) + 500):
        raise ValueError("D1_CHILD_SCOPE_DEADLINE_INVALID")
    guardian = threading.Thread(
        target=_child_lifetime_watch, args=(read_fd, deadline, evidence),
        daemon=True, name="d1-offline-parent-loss-watch")
    guardian.start()
    result = _offline_child(
        evidence, registry, argv[4], argv[5], argv[6], scope)
    print(json.dumps(result, sort_keys=True), flush=True)


if __name__ == "__main__":
    _main(sys.argv)
