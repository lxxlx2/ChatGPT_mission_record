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


class GlobalStartGate:
    """One shared lock controls actual fake send start across every worker."""

    def __init__(self, spacing_ms):
        need(type(spacing_ms) is int and 250 <= spacing_ms <= 5000,
             "D1_GLOBAL_START_GAP_INVALID")
        self.gap = spacing_ms / 1000
        self.lock = threading.Lock()
        self.last = None
        self.starts = []

    def run(self, request, source, *, block_head_deadline, dispatch_deadline):
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
            return {"state":"FRAME", "frame":frame, "start":when}
        except Exception as exc:
            return {"state":"EXCEPTION", "frame":None, "start":when,
                    "error":type(exc).__name__}


def run_fake_concurrent(source, output_root, *, max_total=32,
                        max_blocks=24, max_refreshes=6, spacing_ms=250,
                        slots=3, head_ttl_ms=4000, window_ms=60000,
                        max_block_response_ms=5000,
                        head_min_poll_age_ms=1000):
    """No permit or live network entry. Thread workers are fake only.

    Any invalid input is rejected; concurrent workers cannot allocate IDs,
    modify budgets, write the evidence log, or retry.
    """
    need(type(source) is FakeSource and type(slots) is int and slots == 3
         and type(max_total) is int and 2 <= max_total <= 32
         and type(max_blocks) is int and 1 <= max_blocks <= 24
         and type(max_refreshes) is int and 0 <= max_refreshes <= 6
         and type(head_ttl_ms) is int and 500 <= head_ttl_ms <= 4000
         and type(window_ms) is int and 1000 <= window_ms <= 60000
         and type(max_block_response_ms) is int and
         250 <= max_block_response_ms <= 5000
         and type(head_min_poll_age_ms) is int and
         250 <= head_min_poll_age_ms < head_ttl_ms
         and max_total <= max_blocks + max_refreshes + 2,
         "D1_SCOPE_INVALID")
    begin = time.monotonic()
    dispatch_deadline = begin + window_ms / 1000
    gate = GlobalStartGate(spacing_ms)
    log = ExclusiveEvidence(output_root)
    pending = {}
    reservations, settles = [], []
    faults, parsed_blocks, commits = [], {}, []
    head = head_completed = next_height = next_commit = None
    last_committed_hash = None
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
        need(len(pending) < 3 and unique_id < max_total,
             "D1_RESERVATION_OVER_BUDGET")
        method = ("eth_chainId" if category == "CHAIN" else
                  "eth_blockNumber" if category in ("HEAD", "INITIAL_HEAD") else
                  "eth_getBlockByNumber")
        unique_id += 1
        rid = unique_id
        payload = {"jsonrpc":"2.0", "id":rid, "method":method,
                   "params":[hex(height),True] if category == "BLOCK" else []}
        valid_rpc_payload(payload)
        if category == "BLOCK":
            need(head is not None and height <= head and
                 time.monotonic() < head_completed + head_ttl_ms/1000,
                 "D1_HEAD_LIMIT_INVALID")
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
        dead_head = head_completed + head_ttl_ms/1000 if category == "BLOCK" else None
        fut = executor.submit(gate.run, payload, source,
                              block_head_deadline=dead_head,
                              dispatch_deadline=dispatch_deadline)
        pending[fut] = entry
        peak_slots = max(peak_slots, len(pending))

    def completion(future):
        nonlocal head, head_completed, next_height, next_commit, chain_ok
        nonlocal head_pending, received_full, last_committed_hash, stop
        nonlocal bad_parent, last_completed_sample
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
                       "params":[hex(height),True] if category == "BLOCK" else []}
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
            stop = stop or "RAW_OR_SETTLEMENT_FSYNC_FAILED"
            faults.append({"id":rid,"height":height,
                           "reason":"D1_ARCHIVE_NOT_DURABLE"})
            settles.append({"id":rid,"state":"UNKNOWN",
                            "height":height,"category":category})
            return
        settles.append(settlement)
        if state != "RPC_RESPONSE":
            faults.append({"id":rid, "height":height,
                           "reason":reason, "category":category})
            stop = stop or "RPC_OR_HEAD_FAULT"
            if category in ("HEAD","INITIAL_HEAD"):
                head_pending = False
            return
        if category == "CHAIN":
            chain_ok = True
        elif category in ("HEAD","INITIAL_HEAD"):
            head = h
            head_completed = time.monotonic()
            head_pending = False
            if next_height is None:
                next_height = next_commit = head + 1
            head_samples.append({"sampled_head":head,
                                 "at_monotonic":head_completed})
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
                    stop = stop or "CHAIN_FAULT"
                    break
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
                    if number_blocks >= max_blocks:
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
    return {
        "schema":SCHEMA, "mode":"D1_OFFLINE_FAKE_ONLY",
        "network_requests":0, "no_live_sender":True,
        "real_user_grant_active":False,
        "stop":stop,
        "reserved":len(reservations), "physically_started_fake":len(starts),
        "settled":len(settles), "unknown_after_stop":
            len([x for x in settles if x["state"] == "UNKNOWN"]),
        "max_shared_slots":peak_slots, "head_refreshes":number_refreshes,
        "block_attempts":number_blocks,
        "min_actual_fake_start_gap_ms":round(min(gaps),3) if gaps else None,
        "parsed_full_blocks":received_full,
        "contiguous_commits":len(commits),
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
        "synthetic_source_growth_bps":source.growth_bps,
        "full_ledger_filename":"attempts.jsonl",
        "start_records":[{"id":i,"method":m,"monotonic":t}
                         for i,m,t in starts],
        "source_head_samples":head_samples,
        "f0_status":"NOT_PASSED", "production":"NO_GO",
    }
