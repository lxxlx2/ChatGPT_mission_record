#!/usr/bin/env python3
"""Single foreground BSC read-only SOURCE CAPACITY measurement, 5 minutes only.

Physical networking occurs ONLY from a human-invoked --execute-live, with an
independently reviewed exact Git SHA/script hash + one-use fsynced nonce.
This is an engineering candidate, not standing permission to run it.

ONE coordinator owns the durable request log, three bounded workers may only
perform a preapproved CHAIN/HEAD/full-block request. HEAD/parent evidence
is from the SAME source; no global first-seen or BUY/SELL/ROI is claimed.

TIMEOUT CONTRACT: the main coordinator enforces a result acceptance deadline,
fsyncs FAILED/UNKNOWN on an expired Future, and NEVER waits for native DNS,
TCP or SSL calls to return. A Python thread cannot forcibly preempt such
native calls. After the summary is durably saved, the foreground CLI exits
the OS process with status 93 if an unjoined worker survives. The separate
whole-process watchdog exits status 92 on the global 310-second hard stop.
No response after its deadline is accepted; no second request is retried.
HTTP Connection: close EOF without CL/chunked framing is accepted as a
standard close-delimited response only when HTTPResponse.will_close is true.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
from datetime import datetime, timezone, timedelta
import hashlib
import http.client
import json
import os
from pathlib import Path
import shutil
import socket
import ssl
import subprocess
import threading
import time
import statistics

from f0_l1_live_short import verify_checkout, timestamp
from f0_l1_http_wire import ENDPOINT, json_body, parse_http_response, _parse_quantity
from f0_l1_window import (FROZEN_ROUTER_REGISTRY_BLOB, git_blob_sha1,
                          load_frozen_cohort, cohort_watchlist)
from f0_l1_preflight import official_router_addresses
from f0_l1_durable_journal import fsync_directory, atomic_json
from f0_rpc_adapter import block_candidates, hexb

SCHEMA = "bsc-f0-5m-real-source-once-v1"
HOST = "bsc-dataseed.bnbchain.org"
METHODS = ["eth_chainId", "eth_blockNumber", "eth_getBlockByNumber"]
MAX_TOTAL = 800
MAX_BLOCKS = 740
MAX_HEADS = 31  # initial HEAD included; 10-second interval
MAX_DURATION_MS = 300_000
MAX_BODY = 2_000_000
MIN_FREE_BYTES = 10 * 1024**3
MIN_REMAINING_BYTES = 5 * 1024**3
FIELDS = frozenset((
    "schema", "user_authorized", "independent_review_required",
    "endpoint", "chain_id", "methods", "free_only", "read_only",
    "no_retries", "no_ws", "no_proxy", "no_redirects", "background",
    "approved_commit_sha", "approved_script_sha256", "run_nonce",
    "storage_root", "window_start_utc", "window_end_utc",
    "max_total_attempts", "max_block_reads", "max_head_polls",
    "duration_ms", "head_poll_interval_ms", "slots", "spacing_ms",
    "timeout_ms", "max_response_bytes",
))


def require(test, code):
    if not test:
        raise ValueError(code)


def now_utc():
    return datetime.now(timezone.utc)


def fingerprint(raw):
    return hashlib.sha256(raw).hexdigest()


def validate_scope(doc, *, now=None):
    """Pure validation, never a permission. All budgets include errors/UNKNOWN."""
    require(type(doc) is dict and set(doc) == FIELDS, "ONCE_SCOPE_FIELDS")
    fixed = dict(schema=SCHEMA, endpoint=ENDPOINT, chain_id=56,
                 methods=METHODS, user_authorized=True,
                 independent_review_required=True, free_only=True,
                 read_only=True, no_retries=True, no_ws=True, no_proxy=True,
                 no_redirects=True, background=False, slots=3,
                 duration_ms=MAX_DURATION_MS)
    require(all(type(doc[k]) is type(v) and doc[k] == v
                for k, v in fixed.items()), "ONCE_SCOPE_IDENTITY")
    import re
    require(all(type(doc[k]) is str and re.fullmatch(pattern, doc[k])
                for k, pattern in (
                    ("approved_commit_sha", r"[0-9a-f]{40}"),
                    ("approved_script_sha256", r"[0-9a-f]{64}"),
                    ("run_nonce", r"[0-9a-f]{64}"))),
            "ONCE_SCOPE_CODE_IDENTITY")
    caps = (("max_total_attempts", 3, MAX_TOTAL),
            ("max_block_reads", 1, MAX_BLOCKS),
            ("max_head_polls", 2, MAX_HEADS),
            ("head_poll_interval_ms", 10000, 10000),
            ("spacing_ms", 250, 5000),
            ("timeout_ms", 1000, 5000),
            ("max_response_bytes", 1, MAX_BODY))
    require(all(type(doc[k]) is int and a <= doc[k] <= b
                for k, a, b in caps), "ONCE_SCOPE_BUDGET")
    require(doc["max_total_attempts"] >=
            doc["max_block_reads"] + doc["max_head_polls"] + 2,
            "ONCE_SCOPE_METHOD_BUDGET_INCOHERENT")
    require(type(doc["storage_root"]) is str and
            doc["storage_root"].startswith("/tmp/") and
            ".." not in Path(doc["storage_root"]).parts,
            "ONCE_SCOPE_STORAGE")
    start, end = timestamp(doc["window_start_utc"]), timestamp(doc["window_end_utc"])
    checked = now_utc() if now is None else now
    require(type(checked) is datetime and checked.tzinfo is not None
            and timedelta(0) < end - start <= timedelta(seconds=320)
            and start <= checked <= end - timedelta(seconds=1),
            "ONCE_SCOPE_UTC_WINDOW")
    return doc


def _append(fd, payload):
    b = (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode()
    if os.write(fd, b) != len(b):
        raise OSError("DURABLE_LEDGER_SHORT_WRITE")
    os.fsync(fd)


def _save_raw(rawdir, rid, body):
    dest = rawdir / ("%05d.response.bin" % rid)
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(dest, flags, 0o600)
    with os.fdopen(fd, "wb") as f:
        f.write(body)
        f.flush()
        os.fsync(f.fileno())
    fsync_directory(rawdir)
    return dest.name


class _FramingFailure(Exception):
    """Only complete HTTP framing may become a validated RPC response."""

    def __init__(self, code, partial=b""):
        super().__init__(code)
        self.code = code
        self.partial = partial[:MAX_BODY]


def _read_complete_http_body(response, headers, cap, deadline, timeout_event,
                             set_remaining_timeout):
    """Bounded read1 loop: enforce CL, chunk terminator, and total deadline.

    http.client.HTTPResponse.read(cap+1) is NOT sufficient: it may return
    short bytes for a declared Content-Length without raising IncompleteRead.
    read1 permits a monotonic check between bounded underlying reads.
    """
    framing = {}
    for key, value in headers:
        k = key.lower().strip()
        if k in ("content-length", "transfer-encoding",
                 "content-type", "content-encoding"):
            # Disallow duplicate security-relevant fields even if identical.
            if k in framing:
                raise _FramingFailure("HTTP_DUPLICATE_FRAMING_HEADER")
            framing[k] = value.strip()
    cl = framing.get("content-length")
    te = framing.get("transfer-encoding")
    if cl is not None and te is not None:
        raise _FramingFailure("HTTP_CL_TE_CONFLICT")
    if te is not None and te.lower() != "chunked":
        raise _FramingFailure("HTTP_TRANSFER_ENCODING_UNSUPPORTED")
    if te is not None and not response.chunked:
        raise _FramingFailure("HTTP_CHUNK_FRAMING_INVALID")
    if cl is not None:
        if not cl.isascii() or not cl.isdecimal() or len(cl) > 12:
            raise _FramingFailure("HTTP_CONTENT_LENGTH_INVALID")
        expected = int(cl)
        if expected > cap:
            raise _FramingFailure("RAW_OVERSIZE")
        if response.chunked:
            raise _FramingFailure("HTTP_CL_TE_CONFLICT")
        if response.length is not None and response.length != expected:
            raise _FramingFailure("HTTP_CONTENT_LENGTH_PARSER_MISMATCH")
    else:
        expected = None
        if te is None and not response.will_close:
            raise _FramingFailure("HTTP_UNBOUNDED_FRAMING_REJECTED")
    parts = []
    count = 0
    try:
        while True:
            if timeout_event.is_set() or time.monotonic() >= deadline:
                raise _FramingFailure("REQUEST_DEADLINE_EXCEEDED",
                                      b"".join(parts))
            if expected is not None and count == expected:
                if not response.isclosed():
                    raise _FramingFailure("HTTP_CONTENT_LENGTH_NOT_CLOSED",
                                          b"".join(parts))
                return b"".join(parts)
            remaining = cap + 1 - count
            if remaining <= 0:
                raise _FramingFailure("RAW_OVERSIZE", b"".join(parts))
            if expected is not None:
                remaining = min(remaining, expected-count)
            set_remaining_timeout()
            # read1 is deliberately used instead of read(amt): read(amt)
            # can obscure premature EOF and may block across many chunks.
            data = response.read1(min(8192, remaining))
            if data:
                parts.append(data)
                count += len(data)
            if timeout_event.is_set() or time.monotonic() >= deadline:
                raise _FramingFailure("REQUEST_DEADLINE_EXCEEDED",
                                      b"".join(parts))
            if not data:
                if expected is not None and count < expected:
                    raise _FramingFailure("HTTP_TRUNCATED_CONTENT_LENGTH",
                                          b"".join(parts))
                if not response.isclosed():
                    raise _FramingFailure("HTTP_MISSING_TERMINAL_EOF",
                                          b"".join(parts))
                return b"".join(parts)
            if count > cap:
                raise _FramingFailure("RAW_OVERSIZE", b"".join(parts)[:cap])
    except http.client.IncompleteRead as exc:
        raise _FramingFailure("HTTP_INCOMPLETE_CHUNKED_OR_FRAMING",
                              (b"".join(parts) + exc.partial)[:cap]) from exc
    except (OSError, TimeoutError) as exc:
        # Preserve earlier full chunks even when the next socket read fails.
        reason=("REQUEST_DEADLINE_EXCEEDED"
                if timeout_event.is_set() or time.monotonic() >= deadline
                else "HTTP_STREAM_INTERRUPTED")
        raise _FramingFailure(reason, b"".join(parts)[:cap]) from exc
    except (ValueError, http.client.HTTPException) as exc:
        # Invalid/missing chunk delimiters must never yield an accepted RPC.
        raise _FramingFailure("HTTP_INVALID_CHUNK_TERMINATION",
                              b"".join(parts)[:cap]) from exc


class Sender:
    """One real TLS connection/request; hard per-attempt monotonic deadline."""

    def __init__(self, *, end_utc, stop_mono, timeout_s, spacing_s,
                 response_cap=MAX_BODY, post_factory=None):
        self.end_utc, self.stop_mono = end_utc, stop_mono
        self.timeout_s, self.spacing_s = timeout_s, spacing_s
        self.response_cap = response_cap
        self.lock = threading.Lock()
        self.stop_event = threading.Event()
        self.last_start = None
        # Test-only injected connection factory; real CLI never supplies it.
        self._test_connection_factory = post_factory

    def send(self, encoded):
        conn = None
        live_socket = None
        started = None
        start_ns = time.monotonic_ns()
        deadline = time.monotonic() + self.timeout_s
        tls_connect_ms = None
        pacing_wait_ms = None
        timeout_event = threading.Event()
        completed_event = threading.Event()

        def expire():
            if completed_event.is_set():
                return
            timeout_event.set()
            # Shutdown the socket captured before HTTPResponse takes
            # ownership. Closing only conn.sock is insufficient because
            # http.client may set conn.sock=None after getresponse().
            sock = live_socket
            if sock is not None:
                try:
                    sock.shutdown(socket.SHUT_RDWR)
                except (OSError, AttributeError):
                    pass
                try:
                    sock.close()
                except OSError:
                    pass

        watcher = threading.Timer(self.timeout_s, expire)
        watcher.daemon = True
        watcher.start()

        def check_deadline(partial=b""):
            if self.stop_event.is_set():
                raise _FramingFailure("RUN_STOPPED_UNKNOWN_NO_RETRY", partial)
            if timeout_event.is_set() or time.monotonic() >= deadline:
                raise _FramingFailure("REQUEST_DEADLINE_EXCEEDED", partial)

        def remaining_io_timeout():
            check_deadline()
            if live_socket is not None:
                live_socket.settimeout(max(0.001, deadline-time.monotonic()))

        def finish(state, raw=None, **extra):
            end_ns = time.monotonic_ns()
            return {"state":state, "raw":raw, "post_ns":started,
                    "end_ns":end_ns,
                    "tls_connect_ms":tls_connect_ms,
                    "pacing_wait_ms":pacing_wait_ms,
                    "post_to_response_ms":(
                        round((end_ns-started)/1e6,3)
                        if started is not None else None),
                    "full_attempt_ms":round((end_ns-start_ns)/1e6,3),
                    **extra}
        try:
            ctor = self._test_connection_factory or http.client.HTTPSConnection
            check_deadline()
            conn = ctor(HOST, port=443,
                        timeout=max(0.001, deadline-time.monotonic()),
                        context=ssl.create_default_context())
            tls_start_ns = time.monotonic_ns()
            check_deadline()
            conn.connect()
            # A connected socket may be handed to the HTTPResponse object,
            # so retain a reference for the independent deadline watchdog.
            live_socket = getattr(conn, "sock", None)
            check_deadline()
            connected_ns = time.monotonic_ns()
            tls_connect_ms = round((connected_ns-tls_start_ns)/1e6,3)
            with self.lock:
                if self.last_start is not None:
                    delay = self.spacing_s-(time.monotonic()-self.last_start)
                    if delay > 0:
                        # A slow local scheduler is part of request deadline.
                        time.sleep(min(delay, max(0,deadline-time.monotonic())))
                check_deadline()
                if time.monotonic() >= self.stop_mono or now_utc() >= self.end_utc:
                    return finish("PRE_POST_WINDOW_DENIED")
                remaining_io_timeout()
                self.last_start = time.monotonic()
                started = time.monotonic_ns()
                pacing_wait_ms = round((started-connected_ns)/1e6,3)
                conn.request("POST", "/", body=encoded, headers={
                    "Host":HOST, "Content-Type":"application/json",
                    "Accept":"application/json", "Accept-Encoding":"identity",
                    "Connection":"close"})
            check_deadline()
            remaining_io_timeout()
            response = conn.getresponse()
            check_deadline()
            headers = response.getheaders()
            if len(headers) > 64 or sum(len(k)+len(v) for k,v in headers) > 32768:
                raise _FramingFailure("HEADERS_OVERSIZE")
            # Headers cannot be safely collapsed until duplicate framing is
            # rejected. Incomplete framing NEVER returns state RAW.
            body = _read_complete_http_body(
                response, headers, self.response_cap, deadline,
                timeout_event, remaining_io_timeout)
            check_deadline(body)
            return finish("RAW", raw=body, status=response.status,
                          headers=dict(headers))
        except _FramingFailure as exc:
            return finish(exc.code, raw=exc.partial,
                          framing_valid=False)
        except (OSError, TimeoutError, ValueError, ssl.SSLError,
                http.client.HTTPException) as exc:
            if timeout_event.is_set() or time.monotonic() >= deadline:
                return finish("REQUEST_DEADLINE_EXCEEDED",
                              exception_type=type(exc).__name__)
            return finish("NETWORK_OR_SOURCE_ERROR",
                          exception_type=type(exc).__name__)
        finally:
            completed_event.set()
            watcher.cancel()
            if conn is not None:
                conn.close()


class Capture:
    """Single-writer durable coordinator; workers NEVER write journal/RAW."""

    def __init__(self, root, scope, *, sender, mono=time.monotonic):
        self.scope, self.sender, self.mono = scope, sender, mono
        self.root, self.rawdir = root, root/"raw_responses"
        self.rawdir.mkdir(mode=0o700)
        fd = os.open(root/"attempts.jsonl",
                     os.O_CREAT|os.O_EXCL|os.O_WRONLY |
                     getattr(os,"O_NOFOLLOW",0),0o600)
        self.ledger_fd = fd
        fsync_directory(root)
        self.total, self.blocks, self.heads = 0,0,0
        self.post_attempts, self.errors = 0,0
        self.raw_bytes=0
        self.pending={}
        self.unjoined_futures=set()
        self.deadline_outcomes=0
        self.aborted_unknown_outcomes=0
        self.replies={}
        self.block_timings={k:[] for k in (
            "tls_connect", "pacing_wait", "post_to_response",
            "full_attempt")}
        self.watch_signed=0
        self.router_candidates=0
        self.last_contiguous=None
        self.last_hash=None
        self.next_needed=None
        self.head_samples=[]
        self.latest_head=None
        self.max_inflight=0
        self.initial_anchor_height=None
        self.initial_anchor_mono=None
        self.unresolved_heights=[]
        self.stop_reason=None
        self.started_mono=mono()

    def reserve(self, pool, method, params, category, height=None):
        cap=self.scope
        require(self.total < cap["max_total_attempts"],"ONCE_TOTAL_EXHAUSTED")
        if category=="BLOCK":
            require(self.blocks < cap["max_block_reads"],"ONCE_BLOCK_EXHAUSTED")
            self.blocks+=1
        if category in ("INITIAL_HEAD","HEAD"):
            require(self.heads < cap["max_head_polls"],"ONCE_HEAD_EXHAUSTED")
            self.heads+=1
        rid=self.total+1
        # The MAIN coordination thread owns a monotonic deadline. A blocked
        # DNS/connect worker cannot enforce its own completion deadline.
        deadline_ns=time.monotonic_ns()+self.scope["timeout_ms"]*1_000_000
        req={"jsonrpc":"2.0","id":rid,"method":method,"params":params}
        body=json_body(req)
        self.total=rid
        _append(self.ledger_fd,{"event":"RESERVE_UNKNOWN","rid":rid,
                                "method":method,"category":category,
                                "height":height,"UTC":now_utc().isoformat(),
                                "deadline_monotonic_ns":deadline_ns})
        fut=pool.submit(self.sender.send,body)
        self.pending[fut]=(req,category,height,deadline_ns)
        self.max_inflight=max(self.max_inflight,len(self.pending))
        return fut

    def drain(self, *, timeout=0.1, abort=False):
        """Never join a stalled connector; fail closed on the main thread.

        A Python worker blocked inside native DNS/TCP/SSL cannot be killed by
        Future.cancel() or socket.close() before connect() returns. Only the
        foreground process watchdog / operator-owned process exit can preempt
        that OS thread. The journal always settles its RID as FAILED/UNKNOWN,
        ignores any later worker result, and does not schedule another request.
        """
        if not self.pending:
            return []
        if not abort:
            nearest=min(item[3] for item in self.pending.values())
            remaining=max(0,(nearest-time.monotonic_ns())/1e9)
            wait(tuple(self.pending),timeout=min(timeout,remaining),
                 return_when=FIRST_COMPLETED)
        now_ns=time.monotonic_ns()
        rows=[]
        for future, (req,kind,height,deadline_ns) in tuple(self.pending.items()):
            completed=future.done()
            if not completed and not abort and now_ns<deadline_ns:
                continue
            del self.pending[future]
            if completed:
                try:
                    transport=future.result()
                except Exception:
                    transport={"state":"WORKER_UNHANDLED","raw":None,
                               "post_ns":None,"end_ns":time.monotonic_ns()}
                end_ns=transport.get("end_ns")
                # Even if a late RAW result is delivered immediately before
                # drain(), it CANNOT become a valid RPC after the reservation
                # deadline. Record UNKNOWN, never incorporate the late RAW.
                if (type(end_ns) is not int or
                        end_ns > deadline_ns):
                    transport={**transport,
                               "state":"REQUEST_DEADLINE_EXCEEDED",
                               "late_result_discarded":True}
            elif abort:
                future.cancel()
                self.unjoined_futures.add(future)
                self.aborted_unknown_outcomes+=1
                transport={"state":"ABORTED_UNKNOWN_NO_RETRY",
                           "raw":None,"post_ns":None,"end_ns":now_ns}
            else:
                future.cancel()
                self.unjoined_futures.add(future)
                transport={"state":"REQUEST_DEADLINE_EXCEEDED",
                           "raw":None,"post_ns":None,"end_ns":now_ns}
            if transport["state"]=="REQUEST_DEADLINE_EXCEEDED":
                self.deadline_outcomes+=1
            raw=transport.get("raw")
            rawpath=None
            if type(raw) is bytes and len(raw)<=self.scope["max_response_bytes"]:
                rawpath=_save_raw(self.rawdir,req["id"],raw)
                self.raw_bytes+=len(raw)
            result=None
            failure=None
            cap=self.scope["max_response_bytes"]
            if transport["state"]!="RAW" or type(raw) is not bytes or len(raw)>cap:
                failure=transport["state"] if len(raw or b"")<=cap else "RAW_OVERSIZE"
            else:
                try:
                    result=parse_http_response(transport["status"],transport["headers"],
                                               raw,req,max_bytes=cap)
                except (TypeError,KeyError,ValueError):
                    failure="INVALID_HTTP_OR_RPC"
            if transport.get("post_ns") is not None:
                self.post_attempts+=1
            if failure:
                self.errors+=1
            _append(self.ledger_fd,{"event":"SETTLE","rid":req["id"],
                   "category":kind, "height":height,
                   "state":"RPC_RESPONSE" if result is not None else "FAILED",
                   "failure":failure,
                   "outcome_unknown":(not completed or
                                      transport.get("late_result_discarded",False)),
                   "deadline_monotonic_ns":deadline_ns,
                   "post_monotonic_ns":transport.get("post_ns"),
                   "complete_monotonic_ns":transport.get("end_ns"),
                   "response_sha256":fingerprint(raw) if type(raw) is bytes else None,
                   "raw_file":rawpath,
                   "tls_connect_ms":transport.get("tls_connect_ms"),
                   "pacing_wait_ms":transport.get("pacing_wait_ms"),
                   "post_to_response_ms":transport.get("post_to_response_ms"),
                   "full_attempt_ms":transport.get("full_attempt_ms")})
            rows.append((kind,height,result,failure,transport))
        return rows

    def ingest(self, kind, height, result, failure, transport, watched, routers):
        if failure is not None or result is None:
            self.stop_reason=self.stop_reason or ("SOURCE_"+str(failure))
            if kind=="BLOCK":
                self.unresolved_heights.append(height)
            return
        if kind=="CHAIN":
            try:
                require(_parse_quantity(result,"eth_chainId",result["id"])==56,
                        "SOURCE_WRONG_CHAIN")
            except (TypeError,KeyError,ValueError):
                self.stop_reason="SOURCE_WRONG_CHAIN"
        elif kind in ("INITIAL_HEAD","HEAD"):
            try:
                h=_parse_quantity(result,"eth_blockNumber",result["id"])
                if self.latest_head is not None and h < self.latest_head:
                    raise ValueError("REGRESSED_HEAD")
                self.latest_head=h
                self.head_samples.append({"head":h,"contiguous":self.last_contiguous,
                      "completed_mono_ns":transport.get("end_ns"),
                      "backlog":None if self.last_contiguous is None
                      else h-self.last_contiguous})
            except (TypeError,KeyError,ValueError):
                self.stop_reason="HEAD_INVALID_OR_REGRESSED"
        elif kind in ("ANCHOR","BLOCK"):
            try:
                parsed=block_candidates(result,watched,routers)
                require(parsed["block_number"]==height,"BLOCK_WRONG_HEIGHT")
                obj=result["result"]
                bhash=hexb(obj["hash"],32)
                parent=hexb(obj["parentHash"],32)
                if kind=="ANCHOR":
                    self.initial_anchor_height=height
                    self.initial_anchor_mono=self.mono()
                    self.last_contiguous=height
                    self.last_hash=bhash
                    self.next_needed=height+1
                else:
                    watch_count=sum(c["group"]=="WATCHLIST"
                                    for c in parsed["candidates"])
                    control_count=sum(c["group"]=="CONTROL_CANDIDATE"
                                      for c in parsed["candidates"])
                    # Count ONLY parent-linked contiguous blocks; a syntactically
                    # parsed but orphaned block has NO valid wallet denominator.
                    self.replies[height]=(bhash,parent,watch_count,control_count)
                    post=transport.get("post_ns")
                    end=transport.get("end_ns")
                    if post is not None and end is not None:
                        value=transport.get("post_to_response_ms")
                        if value is None:
                            # Older injected test sources only have POST/end.
                            value=round((end-post)/1e6,3)
                        self.block_timings["post_to_response"].append(value)
                    for key in ("tls_connect","pacing_wait","full_attempt"):
                        value=transport.get(key+"_ms")
                        if type(value) in (int,float) and value >= 0:
                            self.block_timings[key].append(value)
                    while self.next_needed in self.replies:
                        chash,cparent,watch_count,control_count=(
                            self.replies.pop(self.next_needed))
                        require(cparent==self.last_hash,
                                "BLOCK_PARENT_MISMATCH")
                        self.watch_signed+=watch_count
                        self.router_candidates+=control_count
                        self.last_hash=chash
                        self.last_contiguous=self.next_needed
                        self.next_needed+=1
            except (KeyError,TypeError,ValueError):
                self.stop_reason="BLOCK_IDENTITY_OR_PARENT_INVALID"
                self.unresolved_heights.append(height)

    def finish(self):
        os.fsync(self.ledger_fd)
        os.close(self.ledger_fd)


def run_probe(scope, watched, routers, root, *, sender=None, clock=now_utc,
              mono=time.monotonic):
    """Main-thread single journal writer; must never be used as approval."""
    stop=mono()+scope["duration_ms"]/1000
    sender=sender or Sender(
        end_utc=timestamp(scope["window_end_utc"]),stop_mono=stop,
        timeout_s=scope["timeout_ms"]/1000,
        spacing_s=scope["spacing_ms"]/1000,
        response_cap=scope["max_response_bytes"])
    probe=Capture(root,scope,sender=sender,mono=mono)
    try:
        pool=ThreadPoolExecutor(max_workers=3,thread_name_prefix="f0-bsc-read")
        try:
            def single(method,params,kind,height=None):
                probe.reserve(pool,method,params,kind,height)
                while probe.pending and not probe.stop_reason:
                    for a in probe.drain(timeout=0.2):
                        probe.ingest(*a,watched,routers)
                return not probe.stop_reason

            if single("eth_chainId",[],"CHAIN") and single(
                    "eth_blockNumber",[],"INITIAL_HEAD"):
                first_head=probe.latest_head
                single("eth_getBlockByNumber",[hex(first_head),True],
                       "ANCHOR",first_head)
            next_height=None if probe.next_needed is None else probe.next_needed
            next_head_at=mono()+scope["head_poll_interval_ms"]/1000
            while (not probe.stop_reason and mono()<stop
                   and clock()<timestamp(scope["window_end_utc"])):
                if shutil.disk_usage(root).free < MIN_REMAINING_BYTES:
                    probe.stop_reason="DISK_FREE_BELOW_5GIB"
                    break
                for data in probe.drain(timeout=0.02):
                    probe.ingest(*data,watched,routers)
                if probe.stop_reason:
                    break
                if (mono()>=next_head_at and
                        probe.heads<scope["max_head_polls"] and
                        len(probe.pending)<3):
                    probe.reserve(pool,"eth_blockNumber",[],"HEAD")
                    next_head_at=mono()+scope["head_poll_interval_ms"]/1000
                elif (next_height is not None and probe.latest_head is not None
                      and next_height<=probe.latest_head
                      and len(probe.pending)<3
                      and probe.blocks<scope["max_block_reads"]):
                    probe.reserve(pool,"eth_getBlockByNumber",
                                  [hex(next_height),True],"BLOCK",next_height)
                    next_height+=1
                elif not probe.pending:
                    time.sleep(0.03)
                if probe.total>=scope["max_total_attempts"]:
                    probe.stop_reason="GLOBAL_ATTEMPT_LIMIT"
            # Once the coordinator stops, no worker still waiting for
            # connect() or the global POST lock may begin a NEW POST.
            if isinstance(sender,Sender):
                sender.stop_event.set()
            # Never wait indefinitely on native DNS/TCP/TLS. Completed
            # outcomes are recorded if timely; the rest become explicit
            # ABORTED_UNKNOWN_NO_RETRY and cannot be used for observations.
            for data in probe.drain(timeout=0):
                probe.ingest(*data,watched,routers)
            for data in probe.drain(abort=True):
                probe.ingest(*data,watched,routers)
            probe.stop_reason=probe.stop_reason or "FIVE_MINUTE_WINDOW_DONE"
        finally:
            # shutdown(wait=True) and a with-executor block BOTH join blocked
            # native connections. This probe is single-use, fail-closed; the
            # owner foreground CLI exits the OS process after fsync if any
            # unjoined worker survives this non-blocking shutdown.
            pool.shutdown(wait=False,cancel_futures=True)
    finally:
        probe.finish()
    elapsed=max(0.001,mono()-probe.started_mono)
    contiguous_added=(probe.last_contiguous-probe.initial_anchor_height
                      if probe.initial_anchor_height is not None and
                      probe.last_contiguous is not None else 0)
    def percentile(values, q):
        if not values:
            return None
        ordered=sorted(values)
        return round(ordered[min(len(ordered)-1,
                       int((len(ordered)-1)*q))],2)
    # These are successful, parent-linked eligible block responses only;
    # sample counts disclose missing/errored timing observations explicitly.
    timing_summary={}
    for field,values in probe.block_timings.items():
        timing_summary[field+"_sample_count"]=len(values)
        timing_summary[field+"_p50_ms"]=percentile(values,0.5)
        timing_summary[field+"_p95_ms"]=percentile(values,0.95)
    samples=probe.head_samples
    backlog_delta=(samples[-1]["backlog"]-samples[1]["backlog"]
                   if len(samples)>=3 and samples[-1]["backlog"] is not None
                   and samples[1]["backlog"] is not None else None)
    return {"schema":SCHEMA,"result":"UNVERIFIED_LIVE_SOURCE_FEASIBILITY",
            "stop":probe.stop_reason,"attempts":probe.total,
            "archived_raw_bytes":probe.raw_bytes,
            "post_started":probe.post_attempts,"blocks_requested":probe.blocks,
            "heads_requested":probe.heads,"failed":probe.errors,
            "per_request_deadline_outcomes":probe.deadline_outcomes,
            "aborted_unknown_outcomes":probe.aborted_unknown_outcomes,
            "unjoined_worker_count":sum(
                not f.done() for f in probe.unjoined_futures),
            "native_dns_or_tls_uninterruptible":True,
            "post_started_is_known_lower_bound_if_unknown":bool(
                probe.unjoined_futures or probe.aborted_unknown_outcomes),
            "timeout_contract":"main_thread_settles_expired_futures_as_UNKNOWN_without_join; successful_result_requires_completion_before_deadline; foreground_OS_exit_93_after_fsync_if_worker_unjoined; process_hard_stop_92",
            "last_contiguous_height":probe.last_contiguous,
            "latest_source_head":probe.latest_head,
            "source_backlog":None if probe.latest_head is None or
            probe.last_contiguous is None else probe.latest_head-probe.last_contiguous,
            "backlog_delta_same_source":backlog_delta,
            "head_samples":samples,
            "elapsed_seconds":round(elapsed,3),
            "contiguous_full_blocks_post_anchor":contiguous_added,
            "contiguous_rate_blocks_per_s":round(
                contiguous_added/max(0.001,elapsed),3),
            "timing_definition":{
                "tls_connect":"conn.connect() only; includes DNS/TCP/TLS",
                "pacing_wait":"after conn.connect() until POST starts; includes global lock wait and throttling sleep",
                "post_to_response":"POST starts through complete response body read, excludes TLS/pacing",
                "full_attempt":"sender entry through complete response body read, includes constructor/TLS/pacing/HTTP",
                "sample_population":"full BLOCK responses passing RPC and structural validation; excludes anchor/failures; not necessarily parent contiguous"},
            **timing_summary,
            "watch_signed_tx_candidates":probe.watch_signed,
            "router_to_candidates_unverified":probe.router_candidates,
            "buy_confirmed":None, "receipt_count":0,
            "control_randomized":False,"not_f0_passed":True,
            "max_inflight":probe.max_inflight,
            "raw_only_local":True,"automatic_retries":0}


def _hard_foreground_stop(root, deadline):
    """Last-resort same-process hard exit; durable pre-send UNKNOWN survives."""
    remaining=deadline-time.monotonic()
    if remaining>0:
        time.sleep(remaining)
    try:
        atomic_json(root/"hard_stop.json",{"status":"HARD_STOP_NO_RETRY",
                    "outstanding_rpc_outcomes":"UNKNOWN_IF_UNSETTLED"})
    finally:
        os._exit(92)


def main():
    parser=argparse.ArgumentParser(description="5m BSC source feasibility ONE SHOT")
    parser.add_argument("--execute-live",action="store_true")
    parser.add_argument("--permit",type=Path,required=True)
    parser.add_argument("--review-approval",type=Path,required=True)
    args=parser.parse_args()
    require(args.execute_live,"ONCE_EXPLICIT_EXECUTE_FLAG_REQUIRED")
    require(args.permit.is_file() and not args.permit.is_symlink() and
            args.permit.stat().st_mode & 0o077 == 0,
            "ONCE_PERMIT_PRIVATE_FILE_REQUIRED")
    raw=args.permit.read_bytes()
    require(0<len(raw)<=4096,"ONCE_PERMIT_BYTES")
    doc=validate_scope(json.loads(raw))
    script=Path(__file__).resolve()
    verify_checkout(script,doc)
    # verify_checkout() was written for the OLD main script and its DEPENDENCIES
    # list omits that script, which is NOW imported by this new entrypoint.
    # Verify this imported module and all tracked/untracked worktree paths too.
    repo=Path(subprocess.run(
        ["git","-C",str(script.parent),"rev-parse","--show-toplevel"],
        capture_output=True,text=True,check=True,timeout=5).stdout.strip()).resolve()
    legacy=script.parent/"f0_l1_live_short.py"
    rel=legacy.relative_to(repo).as_posix()
    reviewed=subprocess.run(["git","-C",str(repo),"show","HEAD:"+rel],
                            capture_output=True,check=True,timeout=5).stdout
    require(legacy.read_bytes()==reviewed,"ONCE_LEGACY_IMPORT_CHANGED")
    status=subprocess.run(["git","-C",str(repo),"status","--porcelain",
                           "--untracked-files=all"],
                          capture_output=True,text=True,check=True,timeout=5)
    require(not status.stdout.strip(),"ONCE_DIRTY_CHECKOUT")
    approval=args.review_approval
    require(approval.is_file() and not approval.is_symlink() and
            approval.stat().st_mode & 0o077 == 0 and
            approval.resolve()!=args.permit.resolve() and
            approval.read_text().strip()=="APPROVE_PERMIT "+fingerprint(raw),
            "ONCE_INDEPENDENT_PERMIT_REVIEW_REQUIRED")
    base=script.parent
    cohort_raw=(base/"F0_COHORT_PRESELECTION.json").read_bytes()
    router_raw=(base/"F0_ROUTER_SOURCE_CANDIDATES.json").read_bytes()
    watched,_=cohort_watchlist(load_frozen_cohort(cohort_raw))
    require(git_blob_sha1(router_raw)==FROZEN_ROUTER_REGISTRY_BLOB,
            "ONCE_ROUTER_SOURCE_BLOB_MISMATCH")
    routers=set(official_router_addresses(json.loads(router_raw)))
    require(len(watched)==20 and len(routers)==2,
            "ONCE_FROZEN_20_AND_2_REQUIRED")
    root=Path(doc["storage_root"])
    require(root.is_dir() and not root.is_symlink()
            and root.stat().st_uid==os.getuid()
            and root.stat().st_mode & 0o077 == 0
            and shutil.disk_usage(root).free>=MIN_FREE_BYTES
            and all(not (root/name).exists()
                    for name in ("attempts.jsonl","raw_responses","summary.json")),
            "ONCE_PRIVATE_FRESH_DISK_REQUIRED")
    # Irreversible O_EXCL nonce reservation before any HTTPS/DNS attempt.
    marker=root/(".f0_5m_nonce_"+fingerprint(doc["run_nonce"].encode())+".json")
    fd=os.open(marker,os.O_CREAT|os.O_EXCL|os.O_WRONLY |
               getattr(os,"O_NOFOLLOW",0),0o600)
    with os.fdopen(fd,"wb") as out:
        out.write((json.dumps({"permit_sha256":fingerprint(raw),
                               "nonce_sha256":fingerprint(
                                   doc["run_nonce"].encode())})+"\n").encode())
        out.flush()
        os.fsync(out.fileno())
    fsync_directory(root)
    # One foreground process; parent SIGKILL also kills ALL its worker
    # threads. A deadline daemon forces even stuck TLS reads to stop.
    deadline=time.monotonic()+min(310.0,
                (timestamp(doc["window_end_utc"])-now_utc()).total_seconds()+5)
    guard=threading.Thread(target=_hard_foreground_stop,
                           args=(root,deadline),daemon=True)
    guard.start()
    result=run_probe(doc,watched,routers,root)
    atomic_json(root/"summary.json",result)
    print(json.dumps({"stop":result["stop"],"attempts":result["attempts"],
                      "source_backlog":result["source_backlog"],
                      "watch_signed_tx_candidates":
                      result["watch_signed_tx_candidates"],
                      "unjoined_worker_count":result["unjoined_worker_count"],
                      "summary":str(root/"summary.json")},sort_keys=True),
          flush=True)
    if result["unjoined_worker_count"]:
        # The journal and summary are already fsynced, and no timed-out
        # worker response may be ingested. Exit the ENTIRE foreground process
        # instead of silently waiting for Python's non-daemon pool at exit.
        os._exit(93)


if __name__=="__main__":
    main()
