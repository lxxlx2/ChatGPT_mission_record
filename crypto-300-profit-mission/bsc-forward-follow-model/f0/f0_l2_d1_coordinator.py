#!/usr/bin/env python3
"""D1 OFFLINE three-slot bounded concurrent FAKE HTTP coordinator.

No real network client, live entrypoint, wallet signer or permit activation.
Requires an exact type FakeSource and creates only in-memory JSON-RPC frames.
Uses real monotonic scheduling and threads to measure ACTUAL fake send starts.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
import hashlib
import json
import os
from pathlib import Path
import threading
import time

from f0_l1_http_wire import parse_http_response, valid_rpc_payload
from f0_l2_d1_https import _exchange_with_factory
from f0_l1_three_slot_offline import _synthetic_hash
from f0_rpc_adapter import block_candidates, hexb

ENDPOINT = "https://bsc-dataseed.bnbchain.org"
SCHEMA = "bsc-f0-d1-three-slot-fake-concurrent-v1"
METHODS = ("eth_chainId", "eth_blockNumber", "eth_getBlockByNumber")


def need(yes, code):
    if not yes:
        raise ValueError(code)


class ExclusiveEvidence:
    """Single coordinator-writer fsyncs UNKNOWN before fake workers start."""

    def __init__(self, root):
        need(isinstance(root, Path) and root.is_absolute() and root.is_dir()
             and not root.is_symlink() and root.stat().st_mode & 0o077 == 0,
             "D1_EVIDENCE_ROOT_NOT_PRIVATE")
        self.root = root
        self.raw_dir = root / "raw_responses"
        need(not self.raw_dir.exists() and not self.raw_dir.is_symlink(),
             "D1_RAW_DIRECTORY_ALREADY_EXISTS")
        self.raw_dir.mkdir(mode=0o700)
        fd = os.open(root / "attempts.jsonl",
                     os.O_CREAT | os.O_EXCL | os.O_WRONLY |
                     getattr(os, "O_NOFOLLOW", 0), 0o600)
        self.writer = os.fdopen(fd, "w", encoding="utf-8")
        self._fsync_directory(root)

    @staticmethod
    def _fsync_directory(path):
        fd = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(fd)
        finally:
            os.close(fd)

    def add(self, event):
        self.writer.write(json.dumps(event, sort_keys=True,
                                     separators=(",", ":")) + "\n")
        self.writer.flush()
        os.fsync(self.writer.fileno())

    def settle(self, rid, event, frame):
        # Raw response archive must be durable BEFORE a SETTLE entry.
        if frame is not None:
            status, headers, body = frame
            need(type(body) is bytes and len(body) <= 2_000_000,
                 "D1_RAW_BODY_NOT_ARCHIVABLE")
            name = "%03d.body" % rid
            path = self.raw_dir / name
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY |
                         getattr(os, "O_NOFOLLOW", 0), 0o600)
            with os.fdopen(fd, "wb") as out:
                out.write(body)
                out.flush()
                os.fsync(out.fileno())
            self._fsync_directory(self.raw_dir)
            event["raw_sha256"] = hashlib.sha256(body).hexdigest()
            event["raw_name"] = name
            event["http_status"] = status
            event["response_content_type"] = headers.get("content-type")
        self.add(event)

    def close(self):
        self.writer.close()


class FakeSource:
    """No network escape hatch. Only deterministic fake JSON-RPC responses."""

    def __init__(self, *, first_head=1000, growth_bps=5.0,
                 delay_ms=280, fail_heights=(), parent_fault_heights=(),
                 timeout_heights=(), wrong_ids=(), fail_head_after=0,
                 bad_json_heights=(), block_delay_by_ordinal=None,
                 bad_parent_ordinal=0, bad_json_ordinal=0,
                 fail_block_ordinal=0):
        need(type(first_head) is int and first_head > 0
             and type(growth_bps) in (int, float) and 0 <= growth_bps <= 10
             and type(delay_ms) is int and 0 <= delay_ms <= 1000,
             "D1_FAKE_SOURCE_INVALID")
        self.first_head = first_head
        self.growth_bps = growth_bps
        self.delay_ms = delay_ms
        self.fail_heights = set(fail_heights)
        self.parent_fault_heights = set(parent_fault_heights)
        self.timeout_heights = set(timeout_heights)
        self.wrong_ids = set(wrong_ids)
        self.fail_head_after = fail_head_after
        self.bad_json_heights = set(bad_json_heights)
        need(block_delay_by_ordinal is None or
             (type(block_delay_by_ordinal) is dict and
              all(type(k) is int and k > 0 and type(v) is int
                  and 0 <= v <= 3000
                  for k,v in block_delay_by_ordinal.items())),
             "D1_FAKE_DELAYS_INVALID")
        self.block_delay_by_ordinal = block_delay_by_ordinal or {}
        self.bad_parent_ordinal = bad_parent_ordinal
        self.bad_json_ordinal = bad_json_ordinal
        self.fail_block_ordinal = fail_block_ordinal
        self.epoch = time.monotonic()
        self.block_count = 0
        self.head_count = 0
        self.lock = threading.Lock()

    def reply(self, request):
        """This method does NOT call a socket, and cannot accept a callback."""
        valid_rpc_payload(request)
        method, rid = request["method"], request["id"]
        ordinal = None
        if method == "eth_getBlockByNumber":
            with self.lock:
                self.block_count += 1
                ordinal = self.block_count
        delay_ms = self.block_delay_by_ordinal.get(ordinal, self.delay_ms)
        time.sleep(delay_ms / 1000)
        status = 200
        if method == "eth_chainId":
            result = "0x38"
        elif method == "eth_blockNumber":
            with self.lock:
                self.head_count += 1
                poll = self.head_count
            if self.fail_head_after and poll >= self.fail_head_after:
                status = 503
            h = self.first_head + int(self.growth_bps *
                                      (time.monotonic() - self.epoch))
            result = hex(h)
        else:
            height = int(request["params"][0], 16)
            if height in self.timeout_heights:
                raise TimeoutError("FAKE_SOURCE_TIMEOUT")
            if height in self.fail_heights or ordinal == self.fail_block_ordinal:
                status = 503
            if height in self.bad_json_heights or ordinal == self.bad_json_ordinal:
                return (200, {"content-type": "application/json"}, b"{")
            result = {
                "number": hex(height),
                "hash": "0x" + _synthetic_hash(height),
                "parentHash": ("0x" + "ab"*32 if (
                    height in self.parent_fault_heights or
                    ordinal == self.bad_parent_ordinal)
                               else "0x" + _synthetic_hash(height-1)),
                "transactions": [],
            }
        if rid in self.wrong_ids:
            rid += 100000
        return (status, {"content-type":"application/json"},
                json.dumps({"jsonrpc":"2.0", "id":rid, "result":result},
                           separators=(",", ":"), sort_keys=True).encode())


class _FakeHTTPSStartDenied(Exception):
    def __init__(self, state):
        self.state = state


class SealedMemoryHTTPSSource(FakeSource):
    """Only in-process HTTPS transcript; never a socket or external factory.

    All connection/request/response objects are constructed privately and
    there are no caller-injected transport callbacks. FakeSource generates
    the response body only AFTER the global gate authorizes the actual fake
    HTTP POST. This class has no live-capable counterpart.
    """
    def reply_over_memory_https(self, request, begin_fake_post, timeout_s):
        outer = self

        class MemoryResponse:
            def __init__(self, frame):
                self.status, headers, self.data = frame
                self.headers = list(headers.items())
            def getheaders(self):
                return self.headers
            def read(self, size):
                return self.data[:size]

        class MemoryConnection:
            def __init__(self):
                self.response = None
                self.closed = False
            def request(self, method, path, *, body, headers):
                need(not self.closed and self.response is None and
                     method == "POST" and path == "/" and
                     headers.get("Host") ==
                     "bsc-dataseed.bnbchain.org" and
                     headers.get("Accept-Encoding") == "identity",
                     "D1_MEMORY_HTTPS_REQUEST_SCOPE")
                parsed = json.loads(body)
                need(parsed == request, "D1_MEMORY_HTTPS_BODY_IDENTITY")
                # Records the actual fake HTTP POST start (not TLS setup
                # or a pre-SSL worker entry timestamp).
                begin_fake_post()
                self.response = MemoryResponse(FakeSource.reply(outer, parsed))
            def getresponse(self):
                need(not self.closed and self.response is not None,
                     "D1_MEMORY_HTTPS_RESPONSE_NOT_READY")
                return self.response
            def close(self):
                self.closed = True

        def factory(host, *, port, timeout, context):
            need(host == "bsc-dataseed.bnbchain.org" and port == 443 and
                 0 < timeout <= 5 and context.check_hostname and
                 context.verify_mode == __import__("ssl").CERT_REQUIRED,
                 "D1_MEMORY_HTTPS_ORIGIN_OR_TLS_INVALID")
            return MemoryConnection()
        return _exchange_with_factory(
            request, factory, timeout_s=timeout_s,
            max_bytes=2_000_000)


_STAGED_RESERVATION_TEST_SEAL = object()


class _StagedOnlyReservationGuard:
    """In-process TEST receipt minted after the coordinator fsyncs its RID.

    This is NOT a production key, permit, signature or sandbox capability.
    Exact type checking prevents accidental direct lower-gate dispatch with
    an arbitrary callback; Python code with module mutation is untrusted.
    """
    __slots__ = ("_rid", "_digest", "_guard")

    def __init__(self, request, guard, *, _seal=None):
        need(_seal is _STAGED_RESERVATION_TEST_SEAL and
             type(request) is dict and callable(guard),
             "D2_STAGED_RESERVATION_SEAL_REQUIRED")
        self._rid = request["id"]
        self._digest = hashlib.sha256(json.dumps(
            request, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        self._guard = guard

    def __call__(self, actual):
        need(type(actual) is dict and actual.get("id") == self._rid
             and hashlib.sha256(json.dumps(
                 actual, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
             == self._digest, "D2_STAGED_RESERVED_PAYLOAD_MISMATCH")
        self._guard(actual)


class GlobalStartGate:
    """One shared lock controls actual fake send start across every worker."""

    def __init__(self, spacing_ms):
        need(type(spacing_ms) is int and 250 <= spacing_ms <= 5000,
             "D1_GLOBAL_START_GAP_INVALID")
        self.gap = spacing_ms / 1000
        self.lock = threading.Lock()
        self.last = None
        self.starts = []

    def run(self, request, source, *, block_head_deadline, dispatch_deadline,
            timeout_ms, fake_post_utc_window=None, reservation_guard=None):
        from f0_l2_d2a_physical_admission import UnreleasedPhysicalHTTPSProposal
        if type(source) is UnreleasedPhysicalHTTPSProposal:
            # A direct lower-level gate call cannot dispatch a candidate.
            request_physical_source_admission(source)
        from f0_l2_d1_concrete_https import (SealedConcreteOfflineSource,
                                                     PatchedConstructorOfflineSource)
        from f0_l2_d2_physical_source_offline import StagedPhysicalHTTPSReadOnlySource
        from f0_l2_d1_physical_source_candidate import BoundedPhysicalReadOnlySource
        physical = type(source) is BoundedPhysicalReadOnlySource
        # This lower-level shared lock formerly accepted arbitrary duck-typed
        # objects via its fallback .reply(). Keep even direct invocations
        # restricted to the four reviewed, EXACT memory-only source types.
        need(type(source) in (FakeSource, SealedMemoryHTTPSSource,
                              SealedConcreteOfflineSource,
                              PatchedConstructorOfflineSource,
                              StagedPhysicalHTTPSReadOnlySource,
                              BoundedPhysicalReadOnlySource)
             and "reply" not in getattr(source, "__dict__", {})
             and "reply_over_memory_https" not in
                 getattr(source, "__dict__", {})
             and "reply_transport_evidence_offline" not in
                 getattr(source, "__dict__", {}),
             "D2A_GATE_NON_FAKE_SOURCE_REFUSED")
        if type(source) is StagedPhysicalHTTPSReadOnlySource or physical:
            # Every staged or physical candidate must have the original
            # coordinator's post-fsync RID, not a caller-injected callback.
            need(type(reservation_guard) is _StagedOnlyReservationGuard,
                 "D2_STAGED_DURABLE_RESERVATION_PROOF_REQUIRED")
            reservation_guard(request)
        if type(source) in (SealedMemoryHTTPSSource, SealedConcreteOfflineSource,
                            PatchedConstructorOfflineSource,
                            StagedPhysicalHTTPSReadOnlySource,
                            BoundedPhysicalReadOnlySource):
            # Prepare the TLS connection before acquiring the global
            # start lock. Gate the actual in-memory POST, not worker entry.
            began = [None]
            def begin_fake_post():
                with self.lock:
                    when = time.monotonic()
                    if self.last is not None and when < self.last + self.gap:
                        time.sleep(self.last + self.gap - when)
                    when = time.monotonic()
                    if when >= dispatch_deadline:
                        raise _FakeHTTPSStartDenied("PRESTART_WINDOW_EXPIRED")
                    if (block_head_deadline is not None and
                            when >= block_head_deadline):
                        raise _FakeHTTPSStartDenied("PRESTART_STALE_HEAD")
                    # LAST UTC check happens after fake TLS/context setup and
                    # the global spacing wait, directly at in-memory POST.
                    # An invalid/expired test permit never starts FakeSource.
                    if fake_post_utc_window is not None:
                        try:
                            fake_post_utc_window.check_at_fake_post(request)
                        except (ValueError, TypeError):
                            raise _FakeHTTPSStartDenied(
                                "PRESTART_OFFLINE_PERMIT_UTC_DENIED")
                    if physical:
                        try:
                            source.check_at_actual_post()
                        except (ValueError, TypeError):
                            raise _FakeHTTPSStartDenied(
                                "PRESTART_PHYSICAL_POST_UTC_DENIED")
                    when = time.monotonic()
                    if when >= dispatch_deadline or (
                        block_head_deadline is not None and
                        when >= block_head_deadline
                    ):
                        raise _FakeHTTPSStartDenied("PRESTART_WINDOW_EXPIRED")
                    self.last = when
                    self.starts.append((request["id"], request["method"], when))
                    began[0] = when
            try:
                transport = None
                if type(source) in (PatchedConstructorOfflineSource,
                                       StagedPhysicalHTTPSReadOnlySource,
                                       BoundedPhysicalReadOnlySource):
                    need(callable(reservation_guard),
                         "D1_PATCHED_CTOR_PRESEND_PROOF_REQUIRED")
                    if physical:
                        transport = source.reply_transport_evidence_physical_candidate(
                            request, begin_fake_post, timeout_ms / 1000,
                            reservation_guard=reservation_guard)
                    else:
                        transport = source.reply_transport_evidence_offline(
                            request, begin_fake_post, timeout_ms / 1000,
                            reservation_guard=reservation_guard)
                    frame = transport["frame"]
                else:
                    frame = source.reply_over_memory_https(
                        request, begin_fake_post, timeout_ms / 1000)
                completed = time.monotonic()
                if transport is not None and transport["state"] != "RAW":
                    # A complete rejected HTTP response may still have
                    # durable RAW bytes. Archive them in SETTLE before
                    # declaring RPC failure; never parse or COMMIT it.
                    return {
                        "state": ("TRANSPORT_REJECTED_RAW" if frame is not None
                                  else "TRANSPORT_FAILED_NO_RAW"),
                        "frame": frame, "start": began[0],
                        "completed_at": completed,
                        "error": transport["failure"],
                    }
                need(began[0] is not None,
                     "D1_MEMORY_HTTPS_POST_START_UNOBSERVED")
                if (completed - began[0]) * 1000 > timeout_ms:
                    return {"state":"FAKE_TIMEOUT_LATE_RESPONSE",
                            "frame":frame, "start":began[0],
                            "completed_at":completed}
                return {"state":"FRAME", "frame":frame,
                        "start":began[0], "completed_at":completed}
            except _FakeHTTPSStartDenied as exc:
                return {"state":exc.state, "frame":None, "start":None,
                        "completed_at":time.monotonic()}
            except Exception as exc:
                return {"state":"EXCEPTION", "frame":None,
                        "start":began[0], "completed_at":time.monotonic(),
                        "error":type(exc).__name__}
        with self.lock:
            when = time.monotonic()
            if self.last is not None and when < self.last + self.gap:
                time.sleep(self.last + self.gap - when)
            when = time.monotonic()
            if when >= dispatch_deadline:
                return {"state":"PRESTART_WINDOW_EXPIRED", "start":None,
                        "frame":None}
            if block_head_deadline is not None and when >= block_head_deadline:
                return {"state":"PRESTART_STALE_HEAD", "start":None,
                        "frame":None}
            self.last = when
            self.starts.append((request["id"], request["method"], when))
        try:
            frame = source.reply(request)
            completed_at = time.monotonic()
            # Only the worker knows when the response finished. The
            # coordinator/queue/fsync can be arbitrarily delayed afterward.
            if (completed_at - when) * 1000 > timeout_ms:
                return {"state":"FAKE_TIMEOUT_LATE_RESPONSE",
                        "frame":frame,"start":when,"completed_at":completed_at}
            return {"state":"FRAME", "frame":frame, "start":when,
                    "completed_at":completed_at}
        except Exception as exc:
            return {"state":"EXCEPTION", "frame":None, "start":when,
                    "completed_at":time.monotonic(),
                    "error":type(exc).__name__}


def request_physical_source_admission(source_proposal):
    """Future true source's ONLY coordinator admission seam: D2-A DENY.

    The old scheduler, RID journal and start gate are the intended owners,
    but they must never run a physical sender without independently pinned
    D2 and separately authenticated D3 authority. The structured proposal
    itself can be forged; not even exact type/shape is permission.
    Fail BEFORE evidence output, reservation, lease or HTTPS constructor.
    """
    from f0_l2_d2a_physical_admission import UnreleasedPhysicalHTTPSProposal
    need(type(source_proposal) is UnreleasedPhysicalHTTPSProposal,
         "D2A_PHYSICAL_SOURCE_EXACT_PROPOSAL_REQUIRED")
    raise ValueError("D2A_PHYSICAL_SOURCE_ADMISSION_BLOCKED_D2_D3")


def _run_single_shared_coordinator(source, output_root, *, max_total=32,
                        max_blocks=24, max_refreshes=6, spacing_ms=250,
                        slots=3, head_ttl_ms=4000, window_ms=60000,
                        max_block_response_ms=5000,
                        head_min_poll_age_ms=1000,
                        fake_post_utc_window=None,
                        anchor_initial_head=False,
                        _staged_physical_offline=False,
                        _physical_source_candidate=False,
                        _real_foreground_permit=None):
    """No permit or live network entry. Thread workers are fake only.

    Any invalid input is rejected; concurrent workers cannot allocate IDs,
    modify budgets, write the evidence log, or retry.
    """
    from f0_l2_d2a_physical_admission import UnreleasedPhysicalHTTPSProposal
    from f0_l2_d2_physical_source_offline import StagedPhysicalHTTPSReadOnlySource
    from f0_l2_d1_physical_source_candidate import BoundedPhysicalReadOnlySource
    from f0_l2_d1_concrete_https import (
        SealedConcreteOfflineSource, PatchedConstructorOfflineSource,
        _ORIGINAL_HTTPS_CONNECTION)
    import http.client
    from f0_l2_d1_grant import PINNED_LIVE_TRUST_ROOTS
    from f0_l2_d2b_signed_execution_offline import PRODUCTION_D2_D3_TRUST_ROOTS
    if type(source) is UnreleasedPhysicalHTTPSProposal:
        # Explicit early physical-source denial BEFORE the fake coordinator
        # starts its clock, creates evidence, or hands work to its pool.
        request_physical_source_admission(source)
    staged = type(source) is StagedPhysicalHTTPSReadOnlySource
    physical = type(source) is BoundedPhysicalReadOnlySource
    physical_live = physical and http.client.HTTPSConnection is _ORIGINAL_HTTPS_CONNECTION
    # REVIEWED FUTURE LIVE PATH: one original OS child can hold a consumed-once
    # owner/UID/PID/monotonic-bound permit; Python-private objects are NOT
    # authentication. The foreground CLI independently requires explicit
    # operator confirmation and fixed clean Git SHA before issuing this.
    if physical_live:
        from f0_l2_d1_physical_once import _LiveOnceChildPermit
        need(type(_real_foreground_permit) is _LiveOnceChildPermit
             and _real_foreground_permit.valid()
             and source._runtime_permit is _real_foreground_permit
             and _physical_source_candidate is True,
             "F0_REAL_FOREGROUND_OWNER_ONCE_PERMIT_REQUIRED")
    else:
        need(_real_foreground_permit is None and (
             (not physical and _physical_source_candidate is False)
             or (physical and _physical_source_candidate is True
                 and http.client.HTTPSConnection is not _ORIGINAL_HTTPS_CONNECTION)),
             "F0_REAL_FOREGROUND_PHYSICAL_SOURCE_NOT_RELEASED")
    # NEVER allow this private offline constructor-rehearsal source through
    # the public fake entry; nor permit the genuine physical constructor to
    # reach even a test coordinator when production identity is absent.
    need((not staged and _staged_physical_offline is False) or
         (staged and _staged_physical_offline is True and
          http.client.HTTPSConnection is not _ORIGINAL_HTTPS_CONNECTION and
          PINNED_LIVE_TRUST_ROOTS == {} and
          PRODUCTION_D2_D3_TRUST_ROOTS == {}),
         "D2_STAGED_SOURCE_CONSTRUCTOR_OR_AUTHORITY_DENIED")
    need(type(source) in (FakeSource, SealedMemoryHTTPSSource,
                          SealedConcreteOfflineSource,
                          PatchedConstructorOfflineSource)
         or staged or physical, "D1_SCOPE_INVALID")
    need("reply" not in getattr(source, "__dict__", {})
         and "reply_over_memory_https" not in getattr(source, "__dict__", {})
         and "reply_transport_evidence_offline" not in
             getattr(source, "__dict__", {})
         and "reply_transport_evidence_physical_candidate" not in
             getattr(source, "__dict__", {})
         and type(slots) is int and slots == 3
         and type(max_total) is int and 2 <= max_total <= 32
         and type(anchor_initial_head) is bool
         and (not anchor_initial_head or max_total >= 3)
         and type(max_blocks) is int and 1 <= max_blocks <= 24
         and type(max_refreshes) is int and 0 <= max_refreshes <= 6
         and type(head_ttl_ms) is int and 500 <= head_ttl_ms <= 4000
         and type(window_ms) is int and 1000 <= window_ms <= 60000
         and type(max_block_response_ms) is int and
         250 <= max_block_response_ms <= 5000
         and type(head_min_poll_age_ms) is int and
         250 <= head_min_poll_age_ms < head_ttl_ms
         and max_total <= max_blocks + max_refreshes + 2
             + (1 if anchor_initial_head else 0),
         "D1_SCOPE_INVALID")
    if fake_post_utc_window is not None:
        # Import only at run-time: post_utc consumes the bundle's strict
        # permit reader; module imports must remain free of cyclic imports.
        from f0_l2_d1_post_utc import OfflinePostUTCWindow
        need(type(source) in (SealedMemoryHTTPSSource,
                              SealedConcreteOfflineSource,
                              PatchedConstructorOfflineSource,
                              StagedPhysicalHTTPSReadOnlySource) and
             type(fake_post_utc_window) is OfflinePostUTCWindow,
             "D1_POST_UTC_FAKE_ONLY")
    begin = time.monotonic()
    dispatch_deadline = begin + window_ms / 1000
    gate = GlobalStartGate(spacing_ms)
    log = ExclusiveEvidence(output_root)
    pending = {}
    reservations, settles = [], []
    faults, parsed_blocks, commits = [], {}, []
    head = head_completed = next_height = next_commit = None
    last_committed_hash = None
    initial_anchor_started = False
    initial_anchor_ready = not anchor_initial_head
    initial_anchor_height = None
    initial_anchor_hash = None
    verified_initial_parent_links = 0
    verified_internal_parent_links = 0
    stop = None
    number_blocks = number_refreshes = 0
    chain_ok = False
    initial_head_started = False
    head_pending = False
    unique_id = 0
    peak_slots = 0
    bad_parent = None
    head_samples = []
    received_full = 0
    last_completed_sample = None

    def reserve(category, height=None):
        nonlocal unique_id, number_blocks, number_refreshes
        nonlocal head_pending, initial_head_started, next_height, peak_slots
        nonlocal initial_anchor_started
        need(len(pending) < 3 and unique_id < max_total,
             "D1_RESERVATION_OVER_BUDGET")
        method = ("eth_chainId" if category == "CHAIN" else
                  "eth_blockNumber" if category in ("HEAD", "INITIAL_HEAD") else
                  "eth_getBlockByNumber")
        unique_id += 1
        rid = unique_id
        payload = {"jsonrpc":"2.0", "id":rid, "method":method,
                   "params":[hex(height),True] if category in ("BLOCK","ANCHOR") else []}
        valid_rpc_payload(payload)
        if category in ("BLOCK","ANCHOR"):
            need(head is not None and height <= head and
                 time.monotonic() < head_completed + head_ttl_ms/1000,
                 "D1_HEAD_LIMIT_INVALID")
            if category == "ANCHOR":
                need(anchor_initial_head and not initial_anchor_started and
                     height == head and next_height == head + 1,
                     "D1_ANCHOR_SCOPE_INVALID")
                initial_anchor_started = True
            else:
                next_height += 1
                number_blocks += 1
        if category == "HEAD":
            number_refreshes += 1
        if category in ("HEAD", "INITIAL_HEAD"):
            head_pending = True
            initial_head_started = True
        entry = {
            "event":"RESERVE_UNKNOWN", "id":rid,
            "category":category, "method":method, "height":height,
            "confirmed_head":head,
        }
        # f-sync serially BEFORE handing task to any fake worker.
        log.add(entry)
        reservations.append(entry)
        # This coordinator-owned closure can only be minted after the journal
        # successfully flushes+fsyncs the exact RID. It is an OFFLINE test
        # ordering invariant, NOT a user or production network permit.
        def verified_reservation(actual, expected=payload, reserved_id=rid):
            need(actual == expected and actual.get("id") == reserved_id,
                 "D1_PATCHED_CTOR_RESERVED_REQUEST_MISMATCH")
        dead_head = (head_completed + head_ttl_ms/1000
                     if category in ("BLOCK","ANCHOR") else None)
        # Exactly the same durable RID closure; the staged physical-shaped
        # source additionally requires an internal post-fsync TEST receipt.
        # Never interpret this receipt as real D2/D3 production authority.
        reservation_proof = (
            _StagedOnlyReservationGuard(
                payload, verified_reservation,
                _seal=_STAGED_RESERVATION_TEST_SEAL)
            if staged or physical else verified_reservation)
        fut = executor.submit(gate.run, payload, source,
                              block_head_deadline=dead_head,
                              dispatch_deadline=dispatch_deadline,
                              timeout_ms=max_block_response_ms,
                              fake_post_utc_window=fake_post_utc_window,
                              reservation_guard=reservation_proof)
        pending[fut] = entry
        peak_slots = max(peak_slots, len(pending))

    def record_hard_stop(reason):
        nonlocal stop
        # The finite request budget can be reached before responses finish.
        # A later in-flight 503/bad JSON/chain integrity failure must remain
        # visible in the final stop reason and performance decision.
        if stop in (None,"BLOCK_BUDGET","HEAD_BUDGET","TOTAL_BUDGET",
                    "DISPATCH_TIME_CAP"):
            stop = reason

    def completion(future):
        nonlocal head, head_completed, next_height, next_commit, chain_ok
        nonlocal head_pending, received_full, last_committed_hash, stop
        nonlocal bad_parent, last_completed_sample, initial_anchor_ready
        nonlocal initial_anchor_height, initial_anchor_hash
        nonlocal verified_initial_parent_links, verified_internal_parent_links
        entry = pending.pop(future)
        rid, category, height = entry["id"], entry["category"], entry["height"]
        outcome = future.result()
        raw = outcome.get("frame")
        state = "RPC_RESPONSE"
        reason = None
        response = None
        if outcome["state"] != "FRAME":
            state = "FAILED"
            reason = outcome["state"] + (
                ":" + outcome.get("error","") if outcome.get("error") else "")
        else:
            try:
                req = {"jsonrpc":"2.0", "id":rid,
                       "method":entry["method"],
                       "params":[hex(height),True] if category in ("BLOCK","ANCHOR") else []}
                response = parse_http_response(raw[0],raw[1],raw[2],req)
                if category == "CHAIN":
                    need(response["result"] == "0x38", "D1_WRONG_CHAIN")
                elif category in ("HEAD", "INITIAL_HEAD"):
                    v = response["result"]
                    need(type(v) is str and v.startswith("0x") and
                         len(v) > 2 and
                         all(x in "0123456789abcdefABCDEF" for x in v[2:]),
                         "D1_BAD_HEAD")
                    h = int(v,16)
                    need(head is None or h >= head, "D1_HEAD_REWIND")
                else:
                    parsed = block_candidates(response,set(),set())
                    need(parsed["block_number"] == height, "D1_WRONG_HEIGHT")
                    parent = hexb(response["result"]["parentHash"],32)
            except (ValueError,TypeError,KeyError) as exc:
                state = "FAILED"
                reason = str(exc)[:110]
        settlement = {"event":"SETTLE", "id":rid,
                      "category":category, "height":height,
                      "state":state, "reason":reason,
                      "started":outcome.get("start") is not None}
        try:
            log.settle(rid,settlement,raw)
        except (OSError,ValueError) as exc:
            # If raw bytes cannot be persisted, do not claim success.
            record_hard_stop("RAW_OR_SETTLEMENT_FSYNC_FAILED")
            faults.append({"id":rid,"height":height,
                           "reason":"D1_ARCHIVE_NOT_DURABLE"})
            settles.append({"id":rid,"state":"UNKNOWN",
                            "height":height,"category":category})
            return
        settles.append(settlement)
        if state != "RPC_RESPONSE":
            faults.append({"id":rid, "height":height,
                           "reason":reason, "category":category})
            record_hard_stop("INITIAL_ANCHOR_FAILED" if category == "ANCHOR"
                             else "RPC_OR_HEAD_FAULT")
            if category in ("HEAD","INITIAL_HEAD"):
                head_pending = False
            return
        if category == "CHAIN":
            chain_ok = True
        elif category in ("HEAD","INITIAL_HEAD"):
            head = h
            head_completed = outcome["completed_at"]
            need(type(head_completed) is float and
                 head_completed <= time.monotonic(),
                 "D1_HEAD_RESPONSE_COMPLETION_UNRECORDED")
            head_pending = False
            if next_height is None:
                next_height = next_commit = head + 1
            head_samples.append({"sampled_head":head,
                                 "at_monotonic":head_completed,
                                 "accepted_at_monotonic":time.monotonic(),
                                 "clock_basis":"WORKER_RESPONSE_COMPLETED"})
        elif category == "ANCHOR":
            # Successful RAW must already be fsynced via log.settle.
            # Same source only; not independent canonical/finality proof.
            need(initial_anchor_started and not initial_anchor_ready and
                 height == head, "D1_ANCHOR_SETTLEMENT_INVALID")
            initial_anchor_height = height
            initial_anchor_hash = parsed["block_hash"]
            last_committed_hash = initial_anchor_hash
            initial_anchor_ready = True
        else:
            parsed_blocks[height] = (rid,parsed["block_hash"],parent)
            received_full += 1
            # Separate RPC settlement from block continuity. Original RID
            # remains attached to a buffered failure, never to the unlocker.
            while bad_parent is None and next_commit in parsed_blocks:
                owner, block_hash, ph = parsed_blocks[next_commit]
                if last_committed_hash is not None and ph != last_committed_hash:
                    bad_parent = next_commit
                    fault = {"id":owner,"height":next_commit,
                             "reason":"D1_CHAIN_PARENT_MISMATCH",
                             "kind":"CHAIN_INTEGRITY"}
                    faults.append(fault)
                    log.add({"event":"CHAIN_INTEGRITY_FAULT",**fault})
                    record_hard_stop("CHAIN_FAULT")
                    break
                if initial_anchor_ready and anchor_initial_head and (
                    next_commit == initial_anchor_height + 1):
                    verified_initial_parent_links += 1
                elif last_committed_hash is not None:
                    verified_internal_parent_links += 1
                del parsed_blocks[next_commit]
                log.add({"event":"COMMIT_CONTIGUOUS",
                         "height":next_commit,"id":owner})
                commits.append({"height":next_commit,"id":owner})
                next_commit += 1
                last_committed_hash = block_hash

    try:
        with ThreadPoolExecutor(max_workers=3) as executor:
            reserve("CHAIN")
            while True:
                if pending:
                    done, _ = wait(set(pending), timeout=0.015,
                                   return_when=FIRST_COMPLETED)
                    for f in done:
                        completion(f)
                if stop is None and time.monotonic() >= dispatch_deadline:
                    stop = "DISPATCH_TIME_CAP"
                if stop is None and not pending and not chain_ok:
                    stop = "INVALID_CHAIN_ID"
                if stop is None and chain_ok and head is None and not head_pending:
                    reserve("INITIAL_HEAD")
                    continue
                if stop is None and head is not None:
                    if anchor_initial_head and not initial_anchor_ready:
                        # No future block/HEAD refresh before the journaled
                        # initial HEAD full block has settled as valid RAW.
                        if not initial_anchor_started:
                            if len(reservations) >= max_total:
                                stop = "TOTAL_BUDGET"
                            elif time.monotonic() >= (
                                    head_completed + head_ttl_ms/1000):
                                stop = "INITIAL_ANCHOR_STALE_HEAD"
                            elif not pending:
                                reserve("ANCHOR", head)
                                continue
                        elif not pending:
                            stop = "INITIAL_ANCHOR_UNVERIFIED"
                    elif number_blocks >= max_blocks:
                        stop = "BLOCK_BUDGET"
                    elif len(reservations) >= max_total:
                        stop = "TOTAL_BUDGET"
                    elif len(pending) < 3:
                        now = time.monotonic()
                        age = now - head_completed
                        if (next_height <= head and age < head_ttl_ms/1000):
                            reserve("BLOCK", next_height)
                            continue
                        if not head_pending:
                            if number_refreshes >= max_refreshes:
                                stop = "HEAD_BUDGET"
                            elif age >= head_min_poll_age_ms/1000:
                                reserve("HEAD")
                                continue
                if stop is not None and not pending:
                    break
                if not pending:
                    time.sleep(0.008)
    finally:
        log.close()
    starts = gate.starts
    gaps = [(starts[i][2]-starts[i-1][2])*1000
            for i in range(1,len(starts))]
    need(not gaps or min(gaps) >= spacing_ms-1.5,
         "D1_ACTUAL_FAKE_START_GAP_FAILED")
    need(len(reservations) <= 32 and number_blocks <= 24
         and number_refreshes <= 6 and peak_slots <=3,
         "D1_SCOPE_LIMIT_EXCEEDED")
    mode = ("F0_ONCE_FOREGROUND_GENUINE_HTTPS_READ_ONLY"
            if physical_live else
            "F0_PHYSICAL_HTTPS_BRIDGE_PATCHED_NOT_RELEASED"
            if physical else
            "D2_STAGED_PHYSICAL_HTTPS_PATCHED_NO_SOCKET_TEST_ONLY"
            if staged else
            "D1_OFFLINE_CONCRETE_HTTPS_SEALED_NO_SOCKET"
            if type(source) is SealedConcreteOfflineSource else
            "D1_OFFLINE_PATCHED_HTTPS_CTOR_NO_SOCKET_TEST_ONLY"
            if type(source) is PatchedConstructorOfflineSource else
            "D1_OFFLINE_MEMORY_HTTPS_ONLY"
            if type(source) is SealedMemoryHTTPSSource else
            "D1_OFFLINE_FAKE_ONLY")
    return {
        "schema":SCHEMA, "mode":mode,
        "network_requests":len(starts) if physical_live else 0,
        "no_live_sender":not physical_live,
        "physical_bridge_code_tested":physical,
        "physical_source_released":physical_live,
        "fake_post_utc_checks":(fake_post_utc_window.checked_fake_posts
                                if fake_post_utc_window is not None else None),
        "real_user_grant_active":physical_live,
        "stop":stop,
        "reserved":len(reservations), "physically_started_fake":(
            None if physical_live else len(starts)),
        "physical_post_attempted_count":len(starts) if physical_live else 0,
        "settled":len(settles), "unknown_after_stop":
            len([x for x in settles if x["state"] == "UNKNOWN"]),
        "max_shared_slots":peak_slots, "head_refreshes":number_refreshes,
        "block_attempts":number_blocks,
        "min_actual_fake_start_gap_ms":round(min(gaps),3) if gaps else None,
        "parsed_full_blocks":received_full,
        "contiguous_commits":len(commits),
        "initial_anchor_requested":anchor_initial_head,
        "initial_anchor_attempts":int(initial_anchor_started),
        "initial_anchor_height":initial_anchor_height,
        "initial_anchor_hash":initial_anchor_hash,
        "initial_anchor_same_source_verified":(
            initial_anchor_height is not None),
        "verified_initial_parent_links":verified_initial_parent_links,
        "verified_internal_parent_links":verified_internal_parent_links,
        "first_parent_same_source_anchored":(
            verified_initial_parent_links == 1),
        "first_parent_independently_anchored":False,
        "faults":faults, "bad_parent_height":bad_parent,
        "sampled_head":head, "committed_end_height":(
            next_commit-1 if next_commit is not None else None),
        "sampled_head_minus_committed":(
            head-(next_commit-1) if head is not None and
            next_commit is not None else None),
        "known_unattempted":(
            max(0,head-(next_height-1)) if
            head is not None and next_height is not None else None),
        # The distinct physical HTTPS source has no synthetic head-growth
        # generator. Preserve the existing field for all four fake classes,
        # but explicitly mark it inapplicable for the staged test slot.
        "synthetic_source_growth_bps":(
            None if staged or physical else source.growth_bps),
        "full_ledger_filename":"attempts.jsonl",
        "start_records":[{"id":i,"method":m,"monotonic":t}
                         for i,m,t in starts],
        "source_head_samples":head_samples,
        "f0_status":"NOT_PASSED", "production":"NO_GO",
    }

# Single executor and RID writer live ONLY in _run_single_shared_coordinator.
# These two *entry* functions never create a second scheduler or worker pool.
# The public fake API continues to refuse exact staged physical sources.
def run_fake_concurrent(source, output_root, *, max_total=32,
                        max_blocks=24, max_refreshes=6, spacing_ms=250,
                        slots=3, head_ttl_ms=4000, window_ms=60000,
                        max_block_response_ms=5000,
                        head_min_poll_age_ms=1000,
                        fake_post_utc_window=None,
                        anchor_initial_head=False):
    """Original public API: exact FAKE-only entry, never live."""
    return _run_single_shared_coordinator(
        source, output_root, max_total=max_total, max_blocks=max_blocks,
        max_refreshes=max_refreshes, spacing_ms=spacing_ms,
        slots=slots, head_ttl_ms=head_ttl_ms, window_ms=window_ms,
        max_block_response_ms=max_block_response_ms,
        head_min_poll_age_ms=head_min_poll_age_ms,
        fake_post_utc_window=fake_post_utc_window,
        anchor_initial_head=anchor_initial_head,
        _staged_physical_offline=False)


def _run_staged_physical_patched_offline(source, output_root, **scope):
    """Same coordinator under a swapped stdlib constructor; test-only.

    The real HTTPSConnection identity is denied before output creation.
    A future production runner cannot use this test path because D2/D3
    production roots and one-use authorization are not enrolled here.
    """
    from f0_l2_d2_physical_source_offline import StagedPhysicalHTTPSReadOnlySource
    need(type(source) is StagedPhysicalHTTPSReadOnlySource,
         "D2_STAGED_SOURCE_EXACT_TYPE_REQUIRED")
    return _run_single_shared_coordinator(
        source, output_root, _staged_physical_offline=True, **scope)
