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
import socket
import subprocess
import sys
import tempfile
import time

from f0_l2_d1_grant import GRANT_ID, HEX64, OfflineGrantRegistry, PRIVATE_FIXED_REGISTRY
from f0_l2_d1_recovery import reconcile_saved_attempts

SCHEMA = "bsc-f0-d1-hard-stop-offline-once-v1"
_SCENARIOS = ("complete", "hang_after_reserve")
_MAX_TEST_SECONDS = 15.0


def send_live(*_args, **_kwargs):
    raise ValueError("D1_HARD_STOP_LIVE_NOT_AUTHORIZED")


def _private_test_dir(path):
    if (type(path) is not Path or not path.is_absolute() or path.is_symlink()
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


def run_bounded_offline_once(registry: Path, evidence: Path, *,
                             grant_id: str, permit_sha256: str,
                             scenario: str = "complete",
                             hard_seconds: float = 8.0):
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
    # Durable, one-use TEST grant must be spent before even creating a child.
    lease = OfflineGrantRegistry(reg).consume(grant_id, permit_sha256)
    cmd = (sys.executable, "-B", str(Path(__file__).resolve()),
           "--offline-child", str(out), str(reg), grant_id,
           permit_sha256, scenario)
    start = time.monotonic()
    proc = subprocess.Popen(
        cmd, stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, close_fds=True)
    timed_out = False
    try:
        stdout, stderr = proc.communicate(timeout=hard_seconds)
    except subprocess.TimeoutExpired:
        timed_out = True
        # Subprocess creates no grandchildren. SIGKILL bounds the whole
        # OS child regardless of blocked Python threads or socket timeouts.
        proc.kill()
        stdout, stderr = proc.communicate()
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
        "audit": audit,
        "offline_child": parsed if completed else None,
        "live_network_requests": 0,
        "no_automatic_retry": True, "real_d2_approved": False,
        "real_d3_approved": False, "production": "NO_GO",
    }


def _offline_child(evidence: Path, registry: Path, grant_id: str,
                   digest: str, scenario: str):
    """Private subprocess fixture; never a real socket/production runner."""
    from f0_l2_d1_concrete_https import PatchedConstructorOfflineSource
    from f0_l2_d1_coordinator import FakeSource, run_fake_concurrent
    if scenario not in _SCENARIOS:
        raise ValueError("D1_HARD_STOP_BAD_SCENARIO")
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
            source, evidence, max_total=6, max_blocks=3, max_refreshes=1,
            spacing_ms=250, slots=3, window_ms=5000,
            head_min_poll_age_ms=250)
    finally:
        http.client.HTTPSConnection = original_ctor
        socket.create_connection = original_socket
    return result


def _main(argv):
    # This entry exists solely to run a supervised synthetic child.
    if len(argv) != 7 or argv[1] != "--offline-child":
        raise ValueError("D1_HARD_STOP_NO_PUBLIC_LIVE_CLI")
    evidence = Path(argv[2])
    registry = Path(argv[3])
    result = _offline_child(evidence, registry, argv[4], argv[5], argv[6])
    print(json.dumps(result, sort_keys=True), flush=True)


if __name__ == "__main__":
    _main(sys.argv)
