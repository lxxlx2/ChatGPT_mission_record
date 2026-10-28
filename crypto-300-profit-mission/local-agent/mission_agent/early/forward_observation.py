"""Manual, bounded, read-only BSC V2 Factory forward clock evidence pilot.

Two snapshots in one foreground invocation. Never a daemon, trading bot,
complete BSC census, profitable-entry claim, or historical PIT retrofit.
"""
import argparse
import datetime as dt
import hashlib
import http.client
import json
import os
from pathlib import Path
import re
import signal
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

from mission_agent.early.fourmeme_index_source_probe import JsonRPC

CHAIN = 56
FACTORY = "0xca143ce32fe78f1f7019d7d551a6402fc5350c73"
COUNT_SELECTOR = "0x574f2ba3"  # allPairsLength()
PAIRS_SELECTOR = "0x1e3dd18b"  # allPairs(uint256)
TOKEN0_SELECTOR = "0x0dfe1681"  # token0()
TOKEN1_SELECTOR = "0xd21220a7"  # token1()
MAX_NEW_PAIRS = 3
MAX_CALLS = 20
MAX_BOUNDED_CALLS = 180
MAX_BOUNDED_SECONDS = 180
BOUNDED_POLL_SECONDS = 5
MAX_BOUNDED_IDENTITIES = 12
MAX_BOUNDED_PAIR_PER_INTERVAL = 3
MAX_BOUNDED_ANCESTOR_BLOCKS = 24
MAX_RESPONSE_BYTES = 262144
REQUEST_TIMEOUT_SECONDS = 20
MAX_SNAPSHOT_INTERVAL_NS = 3_000_000_000
CLOCK_DRIFT_TOLERANCE_NS = 1_000_000_000
READ_METHODS = frozenset(("eth_chainId", "eth_blockNumber", "eth_getBlockByNumber", "eth_call"))
HEX = re.compile(r"^0x[0-9a-fA-F]+$")
ADDRESS = re.compile(r"^0x[0-9a-fA-F]{40}$")
HASH = re.compile(r"^0x[0-9a-fA-F]{64}$")


class ForwardProbeError(ValueError):
    pass


class ForwardRPC(JsonRPC):
    """Foreground-only transport; keep historical Four.meme behavior unchanged."""

    def __init__(self, endpoint, *, min_interval=0.25, max_requests=MAX_CALLS, opener=None):
        if type(max_requests) is not int or not 0 <= max_requests <= MAX_BOUNDED_CALLS:
            raise ForwardProbeError("RPC_CALL_LIMIT")
        # Four.meme's shared transport constructor is capped at 50. Keep
        # that module untouched; this subclass enforces its own fixed <=180
        # allowance, and the bounded observer checks the same attempt budget.
        super().__init__(endpoint, min_interval=min_interval,
                         max_requests=min(max_requests, 50), opener=opener)
        self.max_requests = max_requests

    def request(self, method, params):
        if method not in READ_METHODS:
            raise ForwardProbeError("DISALLOWED_RPC_METHOD")
        if self.calls >= self.max_requests:
            raise ForwardProbeError("RPC_CALL_LIMIT")
        if (threading.current_thread() is not threading.main_thread()
                or signal.getitimer(signal.ITIMER_REAL) != (0.0, 0.0)):
            raise ForwardProbeError("FOREGROUND_WITHOUT_EXISTING_ALARM_REQUIRED")

        def expired(*_):
            raise ForwardProbeError("RPC_TOTAL_DEADLINE_EXCEEDED")

        previous = signal.signal(signal.SIGALRM, expired)
        signal.setitimer(signal.ITIMER_REAL, REQUEST_TIMEOUT_SECONDS)
        try:
            remain = self.min_interval - (time.monotonic() - self.last)
            if remain > 0:
                time.sleep(remain)
            self.last = time.monotonic()
            self.calls += 1
            payload = json.dumps({"jsonrpc": "2.0", "id": self.calls,
                                  "method": method, "params": params}).encode()
            req = urllib.request.Request(self.url, data=payload, method="POST",
                headers={"Content-Type": "application/json",
                         "User-Agent": "MonsterForwardReadonly/1"})
            with self.opener.open(req, timeout=REQUEST_TIMEOUT_SECONDS) as response:
                if response.status != 200:
                    raise ForwardProbeError("RPC_HTTP_STATUS_NOT_200")
                lengths = response.headers.get_all("Content-Length", [])
                if (len(lengths) > 1 or (lengths and not lengths[0].isdigit())
                        or (lengths and int(lengths[0]) > MAX_RESPONSE_BYTES)
                        or (lengths and response.headers.get("Transfer-Encoding"))):
                    raise ForwardProbeError("RPC_HTTP_FRAMING_INVALID")
                raw = response.read(MAX_RESPONSE_BYTES + 1)
                if lengths and len(raw) != int(lengths[0]):
                    raise ForwardProbeError("RPC_HTTP_BODY_TRUNCATED")
            if len(raw) > MAX_RESPONSE_BYTES:
                raise ForwardProbeError("RPC_RESPONSE_TOO_LARGE")
            parsed = json.loads(raw)
            # A provider may echo credentials in arbitrary extra response fields.
            endpoint = urllib.parse.urlsplit(self.url)
            markers = [self.url, urllib.parse.unquote(self.url)]
            markers += [v for _, v in urllib.parse.parse_qsl(endpoint.query) if v]
            markers += [urllib.parse.unquote(v) for v in endpoint.path.split("/")
                        if v and v.lower() not in ("v1", "v2", "v3", "rpc", "bsc", "mainnet")]
            decoded = json.dumps(parsed, ensure_ascii=False)
            if any(v in decoded or v.encode() in raw for v in markers):
                raise ForwardProbeError("RPC_SECRET_ECHO_REJECTED")
            if (not isinstance(parsed, dict) or parsed.get("jsonrpc") != "2.0"
                    or type(parsed.get("id")) is not int or parsed["id"] != self.calls
                    or "result" not in parsed or "error" in parsed):
                raise ForwardProbeError("RPC_ENVELOPE_INVALID")
            return parsed["result"], raw
        except urllib.error.HTTPError as exc:
            status = int(exc.code)
            exc.close()
            raise ForwardProbeError("RPC_HTTP_" + str(status)) from None
        except (urllib.error.URLError, TimeoutError, OSError, http.client.HTTPException):
            raise ForwardProbeError("RPC_NETWORK_UNAVAILABLE") from None
        except (ValueError, UnicodeDecodeError) as exc:
            if isinstance(exc, ForwardProbeError):
                raise
            raise ForwardProbeError("RPC_INVALID_JSON") from None
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, previous)


def _write_private(path, raw):
    with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "wb") as fd:
        fd.write(raw)


def utc_now():
    return dt.datetime.now(dt.timezone.utc)


def iso(t):
    if t.tzinfo is None or t.utcoffset() is None:
        raise ForwardProbeError("CLOCK_NOT_UTC_AWARE")
    return t.astimezone(dt.timezone.utc).isoformat(timespec="microseconds")


def hex_int(v):
    if not isinstance(v, str) or not HEX.fullmatch(v):
        raise ForwardProbeError("INVALID_RPC_HEX")
    return int(v, 16)


def word_address(v):
    if not isinstance(v, str) or not re.fullmatch(r"0x[0-9a-fA-F]{64}", v):
        raise ForwardProbeError("BAD_ETH_CALL_ADDRESS_WORD")
    if int(v[2:26], 16) != 0:
        raise ForwardProbeError("BAD_ETH_CALL_ADDRESS_PADDING")
    out = "0x" + v[-40:].lower()
    if int(out, 16) == 0:
        raise ForwardProbeError("ZERO_PAIR_OR_TOKEN_ADDRESS")
    return out


def _validate_header(v, number):
    if not isinstance(v, dict) or hex_int(v.get("number")) != number:
        raise ForwardProbeError("BLOCK_NUMBER_MISMATCH")
    if not HASH.fullmatch(str(v.get("hash"))) or not HASH.fullmatch(str(v.get("parentHash"))):
        raise ForwardProbeError("BLOCK_HASH_INVALID")
    return {"number": number, "hash": v["hash"].lower(),
            "parent_hash": v["parentHash"].lower(),
            "chain_timestamp_seconds": hex_int(v.get("timestamp"))}


def capture(rpc, out_dir, *, pause_seconds=1.0, clock=utc_now,
            monotonic_ns=time.monotonic_ns, sleep=time.sleep):
    """Save raw RPC response bytes + local completion timestamps (not network-wide first seen).

    Caller must supply an empty/new directory. RPC must implement existing
    fourmeme_index_source_probe.JsonRPC.request(method, params) returning result/raw.
    """
    if not 0 <= pause_seconds <= 3:
        raise ForwardProbeError("PAUSE_OUT_OF_BOUNDS")
    directory = Path(out_dir)
    if directory.exists():
        raise ForwardProbeError("OUTPUT_DIRECTORY_MUST_NOT_EXIST")
    if not hasattr(rpc, "request") or not isinstance(getattr(rpc, "source_sha256", None), str):
        raise ForwardProbeError("RPC_SOURCE_ID_REQUIRED")
    directory.mkdir(mode=0o700, parents=True, exist_ok=False)
    calls = []
    run_start, run_mono = clock(), monotonic_ns()
    last_clock, last_mono = run_start, run_mono
    attempts = 0

    def checkpoint():
        nonlocal last_clock, last_mono
        now, mono = clock(), monotonic_ns()
        iso(now)
        if now < last_clock or mono < last_mono:
            raise ForwardProbeError("LOCAL_CLOCK_REVERSED")
        utc_ns = int((now - run_start).total_seconds() * 1_000_000_000)
        if abs(utc_ns - (mono - run_mono)) > CLOCK_DRIFT_TOLERANCE_NS:
            raise ForwardProbeError("LOCAL_CLOCK_MONOTONIC_DISAGREEMENT")
        last_clock, last_mono = now, mono
        return now, mono

    def ask(method, params):
        nonlocal attempts
        if method not in READ_METHODS:
            raise ForwardProbeError("DISALLOWED_RPC_METHOD")
        if attempts >= MAX_CALLS:
            raise ForwardProbeError("RPC_CALL_LIMIT")
        start, m_start = checkpoint()
        attempts += 1
        value, raw = rpc.request(method, params)
        recv, m_end = checkpoint()
        if type(raw) is not bytes or len(raw) > 262144:
            raise ForwardProbeError("ORIGINAL_RPC_BYTES_INVALID")
        try:
            envelope = json.loads(raw)
        except (ValueError, UnicodeDecodeError):
            raise ForwardProbeError("ORIGINAL_RPC_JSON_INVALID") from None
        if not isinstance(envelope, dict) or envelope.get("result") != value or envelope.get("error"):
            raise ForwardProbeError("ORIGINAL_RPC_RESULT_NOT_VERIFIED")
        file = f"rpc-{len(calls)+1:02d}.json"
        _write_private(directory / file, raw)
        row = {"ordinal": len(calls)+1, "method": method, "params": params,
               "raw_file": file, "raw_sha256": hashlib.sha256(raw).hexdigest(),
               "raw_bytes": len(raw), "call_invoked_at_utc": iso(start),
               "local_response_completed_at_utc": iso(recv),
               "elapsed_monotonic_ns": m_end - m_start,
               "response_completed_monotonic_offset_ns": m_end - run_mono}
        calls.append(row)
        return value, row

    def call(to, data, height):
        return ask("eth_call", [{"to": to, "data": data}, hex(height)])

    try:
        chain, _ = ask("eth_chainId", [])
        if hex_int(chain) != CHAIN:
            raise ForwardProbeError("NOT_BSC_MAINNET_CHAIN_56")
        observations = []
        for iteration in range(2):
            if iteration:
                sleep(pause_seconds)
            height_raw, _ = ask("eth_blockNumber", [])
            height = hex_int(height_raw)
            header_raw, _ = ask("eth_getBlockByNumber", [hex(height), False])
            header = _validate_header(header_raw, height)
            count_raw, count_receipt = call(FACTORY, COUNT_SELECTOR, height)
            count = hex_int(count_raw)
            if not re.fullmatch(r"0x[0-9a-fA-F]{64}", count_raw):
                raise ForwardProbeError("FACTORY_COUNT_NOT_ABI_WORD")
            header_check_raw, _ = ask("eth_getBlockByNumber", [hex(height), False])
            if _validate_header(header_check_raw, height) != header:
                raise ForwardProbeError("BLOCK_REORG_DURING_OBSERVATION")
            observations.append({"block": header, "all_pairs_length": count,
                "count_observed_at_utc": count_receipt["local_response_completed_at_utc"],
                "count_response_monotonic_offset_ns": count_receipt["response_completed_monotonic_offset_ns"]})
        a, b = observations
        actual_interval = b["count_response_monotonic_offset_ns"] - a["count_response_monotonic_offset_ns"]
        if actual_interval > MAX_SNAPSHOT_INTERVAL_NS:
            raise ForwardProbeError("ACTUAL_SNAPSHOT_INTERVAL_EXCEEDS_3_SECONDS")
        if b["block"]["number"] < a["block"]["number"]:
            raise ForwardProbeError("HEAD_MOVED_BACKWARDS")
        if b["all_pairs_length"] < a["all_pairs_length"]:
            raise ForwardProbeError("FACTORY_COUNTER_DECREASED")
        if (a["block"]["number"] == b["block"]["number"]
                and (a["all_pairs_length"] != b["all_pairs_length"]
                     or a["block"] != b["block"])):
            raise ForwardProbeError("SAME_HEIGHT_INCONSISTENT_STATE")
        if (b["block"]["number"] == a["block"]["number"] + 1
                and b["block"]["parent_hash"] != a["block"]["hash"]):
            raise ForwardProbeError("NONCONTIGUOUS_PARENT_HASH")
        # A same-epoch block that got reorganized after our first read cannot
        # be evidence of a verified contiguous interval.
        anchor_raw, _ = ask("eth_getBlockByNumber", [hex(a["block"]["number"]), False])
        if _validate_header(anchor_raw, a["block"]["number"]) != a["block"]:
            raise ForwardProbeError("FIRST_ANCHOR_CHANGED")
        # Verify every skipped parent within the same 20-call budget, before
        # spending the remaining budget on identities. No implied gap coverage.
        parent = b["block"]["parent_hash"]
        intermediate = []
        for height in range(b["block"]["number"] - 1, a["block"]["number"], -1):
            if len(calls) >= MAX_CALLS - 1:
                raise ForwardProbeError("ANCESTRY_EXCEEDS_RPC_BUDGET")
            raw, _ = ask("eth_getBlockByNumber", [hex(height), False])
            header = _validate_header(raw, height)
            if header["hash"] != parent:
                raise ForwardProbeError("NONCONTIGUOUS_PARENT_HASH")
            intermediate.append(header)
            parent = header["parent_hash"]
        if b["block"]["number"] > a["block"]["number"] and parent != a["block"]["hash"]:
            raise ForwardProbeError("NONCONTIGUOUS_PARENT_HASH")
        delta = b["all_pairs_length"] - a["all_pairs_length"]
        new_pairs = []
        identity_limit = min(delta, MAX_NEW_PAIRS, (MAX_CALLS - len(calls) - 1) // 3)
        for index in range(a["all_pairs_length"], a["all_pairs_length"] + identity_limit):
            word = "0x" + format(index, "064x")
            pair_raw, pair_time = call(FACTORY, PAIRS_SELECTOR + word[2:], b["block"]["number"])
            pair = word_address(pair_raw)
            token0_raw, token0_time = call(pair, TOKEN0_SELECTOR, b["block"]["number"])
            token1_raw, token1_time = call(pair, TOKEN1_SELECTOR, b["block"]["number"])
            token0, token1 = word_address(token0_raw), word_address(token1_raw)
            if token0 == token1:
                raise ForwardProbeError("POOL_IDENTICAL_TOKEN_ADDRESSES")
            if int(token0, 16) > int(token1, 16):
                raise ForwardProbeError("POOL_TOKEN_ORDER_INVALID")
            if any(p["pool"] == pair or (p["token0"], p["token1"]) == (token0, token1)
                   for p in new_pairs):
                raise ForwardProbeError("DUPLICATE_FACTORY_POOL_IDENTITY")
            new_pairs.append({"factory_index": index, "pool": pair,
                "token0": token0, "token1": token1,
                "last_identity_response_completed_at_utc": token1_time["local_response_completed_at_utc"],
                "pair_response_completed_at_utc": pair_time["local_response_completed_at_utc"],
                "token0_response_completed_at_utc": token0_time["local_response_completed_at_utc"]})
        # Detect late reorg or changed block identity after reading pool state.
        final_header_raw, _ = ask("eth_getBlockByNumber", [hex(b["block"]["number"]), False])
        if _validate_header(final_header_raw, b["block"]["number"]) != b["block"]:
            raise ForwardProbeError("SECOND_ANCHOR_CHANGED")
        finished, finished_mono = checkpoint()
        manifest = {"schema": "MONSTER_FORWARD_BSC_V2_ONE_SHOT_OBSERVER_V1",
            "network_chain_id": CHAIN, "provider_url_sha256_only": rpc.source_sha256,
            "factory": FACTORY, "snapshots": observations,
            "new_factory_pair_index_count": delta, "new_pairs_read": new_pairs,
            "unread_new_pair_count": delta - len(new_pairs),
            "observation_complete_for_two_factory_counts": True,
            "factory_index_identity_coverage": "PARTIAL" if delta > len(new_pairs) else "WITHIN_OBSERVED_PAIR_COUNT_DELTA",
            "verified_intermediate_headers": intermediate,
            "pause_seconds_requested": pause_seconds,
            "count_response_interval_monotonic_ns": actual_interval,
            "capture_started_at_utc": iso(run_start),
            "capture_completed_at_utc": iso(finished),
            "capture_elapsed_monotonic_ns": finished_mono - run_mono,
            "capture_duration_scope": "RPC_AND_VALIDATION_BEFORE_MANIFEST_WRITE",
            "clock_attestation": "LOCAL_SYSTEM_CLOCK_NOT_EXTERNALLY_ATTESTED",
            "rpc_attempt_count": attempts,
            "time_basis": "LOCAL_RESPONSE_COMPLETED_UTC_UPPER_BOUND_NOT_FIRST_PUBLIC_AVAILABLE_AT",
            "provenance_scope": "ONE_PROVIDER_LIVE_READ_NOT_INDEPENDENT_AUTHENTICATION",
            "reorg_finality": "NOT_PROVEN_FINALIZED",
            "trade_execution_or_liquidity": "NOT_TESTED",
            "interval_no_new_pair_is_not_full_market_zero": True,
            "p0_historical_2025_available_at": "UNKNOWN_NOT_RETROACTIVELY_RECONSTRUCTED",
            "p1_gate_passed": False, "trading_authorized": False,
            "rpc_requests": calls}
        _write_private(directory / "manifest.json", (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode())
        return manifest
    except Exception as exc:
        # Preserve the exact prior raw bytes and mark this run unusable.
        code = str(exc) if isinstance(exc, ForwardProbeError) else type(exc).__name__
        _write_private(directory / "failure.json", (json.dumps({"status": "UNUSABLE_NOT_PIT_EVIDENCE", "reason": code,
                   "rpc_attempt_count": attempts, "completed_rpc_responses": calls}, indent=2, sort_keys=True) + "\n").encode())
        raise



def capture_bounded(rpc, out_dir, *, duration_seconds=MAX_BOUNDED_SECONDS,
                    poll_seconds=BOUNDED_POLL_SECONDS, rpc_budget=MAX_BOUNDED_CALLS,
                    clock=utc_now, monotonic_ns=time.monotonic_ns, sleep=time.sleep):
    """One foreground finite V2 Factory observation, not a live trading/PIT approval.

    Default contract: <=180s maximum target, <=180 read-only RPC calls,
    <=12 pair identities, interval ancestry <=24 blocks. Typical ~0.45s BSC
    blocks require ~5s polling, not 12s. Budget may stop observation
    before the 180s ceiling; only actually verified intervals are covered.
    An in-flight HTTP
    request may extend completion by the existing 20-second request timeout.
    """
    if (type(duration_seconds) is not int or not 12 <= duration_seconds <= MAX_BOUNDED_SECONDS
            or type(poll_seconds) is not int or not 1 <= poll_seconds <= BOUNDED_POLL_SECONDS
            or type(rpc_budget) is not int or not 40 <= rpc_budget <= MAX_BOUNDED_CALLS):
        raise ForwardProbeError("BOUNDED_CONTRACT_OUT_OF_RANGE")
    if (not hasattr(rpc, "request") or not isinstance(getattr(rpc, "source_sha256", None), str)):
        raise ForwardProbeError("RPC_SOURCE_ID_REQUIRED")
    directory = Path(out_dir)
    if directory.exists():
        raise ForwardProbeError("OUTPUT_DIRECTORY_MUST_NOT_EXIST")
    directory.mkdir(mode=0o700, parents=True, exist_ok=False)
    start_clock, start_mono = clock(), monotonic_ns()
    last_clock, last_mono = start_clock, start_mono
    end_mono = start_mono + duration_seconds * 1_000_000_000
    calls, snapshots, intervals, new_pairs = [], [], [], []
    attempted = 0

    def checkpoint():
        nonlocal last_clock, last_mono
        now, mono = clock(), monotonic_ns()
        iso(now)
        if now < last_clock or mono < last_mono:
            raise ForwardProbeError("LOCAL_CLOCK_REVERSED")
        delta_wall_ns = int((now - start_clock).total_seconds() * 1_000_000_000)
        if abs(delta_wall_ns - (mono - start_mono)) > CLOCK_DRIFT_TOLERANCE_NS:
            raise ForwardProbeError("LOCAL_CLOCK_MONOTONIC_DISAGREEMENT")
        last_clock, last_mono = now, mono
        return now, mono

    def ask(method, params):
        nonlocal attempted
        if method not in READ_METHODS:
            raise ForwardProbeError("DISALLOWED_RPC_METHOD")
        if attempted >= rpc_budget:
            raise ForwardProbeError("BOUNDED_RPC_LIMIT")
        begin, m_begin = checkpoint()
        attempted += 1
        value, raw = rpc.request(method, params)
        recv, m_end = checkpoint()
        if type(raw) is not bytes or len(raw) > MAX_RESPONSE_BYTES:
            raise ForwardProbeError("ORIGINAL_RPC_BYTES_INVALID")
        try:
            parsed = json.loads(raw)
        except (ValueError, UnicodeDecodeError):
            raise ForwardProbeError("ORIGINAL_RPC_JSON_INVALID") from None
        if (not isinstance(parsed, dict) or parsed.get("result") != value
                or parsed.get("error") or parsed.get("jsonrpc") != "2.0"
                or parsed.get("id") != attempted or type(parsed.get("id")) is not int):
            raise ForwardProbeError("ORIGINAL_RPC_RESULT_NOT_VERIFIED")
        name = f"rpc-{len(calls)+1:03d}.json"
        _write_private(directory / name, raw)
        row = {"ordinal": len(calls)+1, "method": method, "params": params,
               "raw_file": name, "raw_sha256": hashlib.sha256(raw).hexdigest(),
               "raw_bytes": len(raw), "call_invoked_at_utc": iso(begin),
               "local_response_completed_at_utc": iso(recv),
               "elapsed_monotonic_ns": m_end-m_begin,
               "response_completed_monotonic_offset_ns": m_end-start_mono}
        calls.append(row)
        return value, row

    def call(to, data, height):
        return ask("eth_call", [{"to": to, "data": data}, hex(height)])

    def pinned_snapshot():
        height_raw, _ = ask("eth_blockNumber", [])
        height = hex_int(height_raw)
        header_raw, _ = ask("eth_getBlockByNumber", [hex(height), False])
        header = _validate_header(header_raw, height)
        count_raw, count_row = call(FACTORY, COUNT_SELECTOR, height)
        if not isinstance(count_raw, str) or not re.fullmatch(r"0x[0-9a-fA-F]{64}", count_raw):
            raise ForwardProbeError("FACTORY_COUNT_NOT_ABI_WORD")
        count = hex_int(count_raw)
        again, _ = ask("eth_getBlockByNumber", [hex(height), False])
        if _validate_header(again, height) != header:
            raise ForwardProbeError("BLOCK_REORG_DURING_OBSERVATION")
        result = {"block": header, "all_pairs_length": count,
                  "count_observed_at_utc": count_row["local_response_completed_at_utc"],
                  "count_response_monotonic_offset_ns":
                      count_row["response_completed_monotonic_offset_ns"]}
        return result

    try:
        chain, _ = ask("eth_chainId", [])
        if hex_int(chain) != CHAIN:
            raise ForwardProbeError("NOT_BSC_MAINNET_CHAIN_56")
        a = pinned_snapshot()
        snapshots.append(a)
        stop_reason = "DURATION_LIMIT"
        while True:
            _, now_mono = checkpoint()
            if now_mono >= end_mono:
                break
            # Reserve enough calls to prove one entire short gap and a head
            # recheck. Never capture an unverified segment merely to use budget.
            if rpc_budget - attempted < 32:
                stop_reason = "RPC_BUDGET_SAFETY_RESERVE"
                break
            remaining = (end_mono - now_mono) / 1_000_000_000
            sleep(min(float(poll_seconds), remaining))
            _, now_mono = checkpoint()
            if now_mono >= end_mono:
                break
            b = pinned_snapshot()
            if b["block"]["number"] < a["block"]["number"]:
                raise ForwardProbeError("HEAD_MOVED_BACKWARDS")
            if b["all_pairs_length"] < a["all_pairs_length"]:
                raise ForwardProbeError("FACTORY_COUNTER_DECREASED")
            if (b["block"]["number"] == a["block"]["number"]
                    and b["block"] != a["block"]):
                raise ForwardProbeError("SAME_HEIGHT_REORG")
            if (b["block"]["number"] == a["block"]["number"]
                    and b["all_pairs_length"] != a["all_pairs_length"]):
                raise ForwardProbeError("SAME_HEIGHT_INCONSISTENT_STATE")
            gap = b["block"]["number"] - a["block"]["number"]
            if gap > MAX_BOUNDED_ANCESTOR_BLOCKS:
                raise ForwardProbeError("ANCESTRY_EXCEEDS_BOUNDED_DEPTH")
            if rpc_budget - attempted < gap + 2:
                raise ForwardProbeError("ANCESTRY_EXCEEDS_RPC_BUDGET")
            anchor, _ = ask("eth_getBlockByNumber", [hex(a["block"]["number"]), False])
            if _validate_header(anchor, a["block"]["number"]) != a["block"]:
                raise ForwardProbeError("FIRST_ANCHOR_CHANGED")
            parent = b["block"]["parent_hash"]
            ancestors = []
            for height in range(b["block"]["number"]-1, a["block"]["number"], -1):
                raw, _ = ask("eth_getBlockByNumber", [hex(height), False])
                hdr = _validate_header(raw, height)
                if hdr["hash"] != parent:
                    raise ForwardProbeError("NONCONTIGUOUS_PARENT_HASH")
                ancestors.append(hdr)
                parent = hdr["parent_hash"]
            if gap > 0 and parent != a["block"]["hash"]:
                raise ForwardProbeError("NONCONTIGUOUS_PARENT_HASH")
            delta = b["all_pairs_length"] - a["all_pairs_length"]
            read = []
            capacity = min(delta, MAX_BOUNDED_PAIR_PER_INTERVAL,
                           MAX_BOUNDED_IDENTITIES-len(new_pairs),
                           max(0, (rpc_budget-attempted-2)//3))
            for index in range(a["all_pairs_length"], a["all_pairs_length"]+capacity):
                index_word = format(index, "064x")
                pair_raw, t_pair = call(FACTORY, PAIRS_SELECTOR+index_word, b["block"]["number"])
                pool = word_address(pair_raw)
                t0_raw, t0 = call(pool, TOKEN0_SELECTOR, b["block"]["number"])
                t1_raw, t1 = call(pool, TOKEN1_SELECTOR, b["block"]["number"])
                token0, token1 = word_address(t0_raw), word_address(t1_raw)
                if token0 == token1 or int(token0, 16) > int(token1, 16):
                    raise ForwardProbeError("POOL_INVALID_TOKEN_ORDER_OR_IDENTITY")
                if any(p["pool"] == pool or (p["token0"], p["token1"]) == (token0, token1)
                       for p in new_pairs):
                    raise ForwardProbeError("DUPLICATE_FACTORY_POOL_IDENTITY")
                row = {"factory_index": index, "pool": pool,
                       "token0": token0, "token1": token1,
                       "pair_response_completed_at_utc": t_pair["local_response_completed_at_utc"],
                       "token0_response_completed_at_utc": t0["local_response_completed_at_utc"],
                       "token1_response_completed_at_utc": t1["local_response_completed_at_utc"],
                       "identity_evidence_is_at_block": b["block"]["number"]}
                new_pairs.append(row)
                read.append(index)
            latest, _ = ask("eth_getBlockByNumber", [hex(b["block"]["number"]), False])
            if _validate_header(latest, b["block"]["number"]) != b["block"]:
                raise ForwardProbeError("SECOND_ANCHOR_CHANGED")
            intervals.append({
                "from_block": a["block"]["number"], "to_block": b["block"]["number"],
                "verified_intermediate_headers": ancestors,
                "factory_index_before": a["all_pairs_length"],
                "factory_index_after": b["all_pairs_length"],
                "new_factory_pair_index_count": delta,
                "identities_read_indices": read,
                "unread_factory_index_start": a["all_pairs_length"]+len(read),
                "unread_factory_index_end_exclusive": b["all_pairs_length"],
                "unread_count": delta-len(read),
                "source_scope": "BSC_PANCAKE_V2_FACTORY_ONLY",
                "interval_contiguous_headers_verified": True})
            snapshots.append(b)
            a = b
        finish, finish_mono = checkpoint()
        first, last = snapshots[0], snapshots[-1]
        if not intervals:
            raise ForwardProbeError("BOUNDED_NO_VALID_INTERVAL")
        unread = sum(s["unread_count"] for s in intervals)
        result = {
            "schema": "MONSTER_FORWARD_BSC_V2_MANUAL_BOUNDED_V1",
            "network_chain_id": CHAIN, "factory": FACTORY,
            "provider_url_sha256_only": rpc.source_sha256,
            "requested_duration_seconds": duration_seconds,
            "poll_seconds_requested": poll_seconds,
            "max_rpc_attempts": rpc_budget,
            "stop_reason": stop_reason,
            "snapshots": snapshots, "verified_intervals": intervals,
            "new_factory_pair_index_count": last["all_pairs_length"]-first["all_pairs_length"],
            "new_pairs_read": new_pairs,
            "unread_new_pair_count": unread,
            "factory_index_identity_coverage":
                "PARTIAL" if unread else "WITHIN_OBSERVED_FACTORY_COUNTER_DELTA_ONLY",
            "capture_started_at_utc": iso(start_clock),
            "capture_completed_at_utc": iso(finish),
            "elapsed_monotonic_ns": finish_mono-start_mono,
            "rpc_attempt_count": attempted, "rpc_requests": calls,
            "time_basis": "LOCAL_RESPONSE_COMPLETED_UTC_NOT_FIRST_PUBLIC_AVAILABLE_AT",
            "clock_attestation": "LOCAL_SYSTEM_CLOCK_NOT_EXTERNALLY_ATTESTED",
            "source_scope": "SINGLE_PROVIDER_PANCAKE_V2_ONLY",
            "reorg_finality": "NOT_PROVEN_FINALIZED",
            "zero_delta_does_not_imply_whole_market_zero": True,
            "trade_execution_or_liquidity": "NOT_TESTED",
            "p0_historical_2025_available_at": "UNKNOWN_NOT_RETROACTIVELY_RECONSTRUCTED",
            "p1_gate_passed": False, "trading_authorized": False,
        }
        _write_private(directory/"manifest.json",
                       (json.dumps(result, indent=2, sort_keys=True)+"\n").encode())
        return result
    except Exception as exc:
        code = str(exc) if isinstance(exc, ForwardProbeError) else type(exc).__name__
        _write_private(directory/"failure.json",
                       (json.dumps({"status": "UNUSABLE_NOT_PIT_EVIDENCE", "reason": code,
                                    "rpc_attempt_count": attempted,
                                    "completed_rpc_responses": calls},
                                   indent=2, sort_keys=True)+"\n").encode())
        raise


def main():
    parser = argparse.ArgumentParser(description="Monster bounded manual BSC V2 forward-only receipt pilot")
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--manual-once", action="store_true")
    modes.add_argument("--manual-bounded", action="store_true")
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--pause-ms", type=int, default=1000)
    args = parser.parse_args()
    if args.manual_bounded:
        if args.pause_ms != 1000:
            parser.error("--pause-ms is only valid with --manual-once")
        rpc = ForwardRPC(os.getenv("MONSTER_BSC_ARCHIVE_RPC_URL"),
                         max_requests=MAX_BOUNDED_CALLS)
        result = capture_bounded(rpc, args.out_dir)
        print(json.dumps({"status": "READ_ONLY_BOUNDED_OBSERVED",
            "manifest_path": str(args.out_dir / "manifest.json"),
            "snapshots": len(result["snapshots"]),
            "pair_count_delta": result["new_factory_pair_index_count"],
            "listed_pairs": len(result["new_pairs_read"]),
            "unread_new_pairs": result["unread_new_pair_count"],
            "stop_reason": result["stop_reason"],
            "p0_gate": "UNCHANGED", "p1_gate": "BLOCKED"}, sort_keys=True))
    else:
        if not 0 <= args.pause_ms <= 3000:
            parser.error("--manual-once and --pause-ms from 0 to 3000 required")
        rpc = ForwardRPC(os.getenv("MONSTER_BSC_ARCHIVE_RPC_URL"), max_requests=MAX_CALLS)
        result = capture(rpc, args.out_dir, pause_seconds=args.pause_ms / 1000)
        print(json.dumps({"status": "READ_ONLY_PILOT_OBSERVED",
            "manifest_path": str(args.out_dir / "manifest.json"),
            "snapshots": len(result["snapshots"]),
            "pair_count_delta": result["new_factory_pair_index_count"],
            "listed_pairs": len(result["new_pairs_read"]),
            "p0_gate": "UNCHANGED", "p1_gate": "BLOCKED"}, sort_keys=True))


if __name__ == "__main__":
    main()
