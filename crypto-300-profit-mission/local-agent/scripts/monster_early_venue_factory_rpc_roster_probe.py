#!/usr/bin/env python3
"""One-shot, manual, read-only historical DEX factory coverage probe.

No wallet, signing, trading, automation, data-label inference or dependencies.
Use --mode probe first; --mode scan only after historical logs are supported.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

CHAINS = {
    "base-v3": {
        "chain_id": 8453,
        "rpc": "https://mainnet.base.org",
        "factory": "0x33128a8fC17869897dcE68Ed026d694621f6FDfD",
        "topic": "0x783cca1c0412dd0d695e784568c96da2e9c22ff989357a2e8b1d9b2b4e6b7118",
        "bases": ("0x4200000000000000000000000000000000000006",
                  "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913"),
        "event": "PoolCreated",
    },
    "bsc-v2": {
        "chain_id": 56,
        "rpc": "https://bsc-dataseed.bnbchain.org",
        "factory": "0xcA143Ce32Fe78f1f7019d7d551a6402fC5350c73",
        "topic": "0x0d3648bd0f6ba80134a33ba9275ac585d9d315f0ad8355cddefde31afa28d0e9",
        "bases": ("0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c",
                  "0x55d398326f99059fF775485246999027B3197955"),
        "event": "PairCreated",
    },
}

class SourceError(Exception):
    pass


def sha(blob):
    return hashlib.sha256(blob).hexdigest()


def plain_json(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def as_int(v):
    if not isinstance(v, str) or not re.fullmatch(r"0x[0-9a-fA-F]+", v):
        raise SourceError("BAD_RPC_HEX_NUMBER")
    return int(v, 16)


class RPC:
    def __init__(self, endpoint, chain, max_requests, delay):
        u = urllib.parse.urlsplit(endpoint)
        if u.scheme != "https" or not u.hostname or u.username or u.password or u.fragment:
            raise SourceError("RPC_MUST_BE_HTTPS_NO_EMBEDDED_CREDENTIALS")
        self.url = endpoint
        self.host = u.hostname
        self.chain = chain
        self.max_requests = max_requests
        self.delay = delay
        self.calls = 0
        self.last = 0.0

    def request(self, method, params):
        if self.calls >= self.max_requests:
            raise SourceError("REQUEST_BUDGET_EXHAUSTED_NO_COMPLETE_COHORT")
        remain = self.delay - (time.monotonic() - self.last)
        if remain > 0:
            time.sleep(remain)
        self.calls += 1
        self.last = time.monotonic()
        payload = json.dumps({"jsonrpc": "2.0", "id": self.calls,
                              "method": method, "params": params},
                             separators=(",", ":")).encode("utf-8")
        req = urllib.request.Request(self.url, data=payload,
                    headers={"Content-Type": "application/json", "User-Agent": "MonsterReadOnlyPITProbe/1.0"},
                    method="POST")
        try:
            with urllib.request.urlopen(req, timeout=20) as response:
                raw = response.read(16 * 1024 * 1024 + 1)
        except urllib.error.HTTPError as e:
            raise SourceError("RPC_HTTP_" + str(e.code)) from None
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            raise SourceError("RPC_NETWORK_UNAVAILABLE_" + type(e).__name__) from None
        if len(raw) > 16 * 1024 * 1024:
            raise SourceError("RPC_RESPONSE_EXCEEDS_16MB")
        try:
            body = json.loads(raw)
        except (ValueError, UnicodeDecodeError):
            raise SourceError("RPC_RESPONSE_INVALID_JSON") from None
        if not isinstance(body, dict):
            raise SourceError("RPC_RESULT_NOT_OBJECT")
        if body.get("error"):
            err = body["error"]
            code = err.get("code", "UNKNOWN") if isinstance(err, dict) else "UNKNOWN"
            msg = str(err.get("message", "")) if isinstance(err, dict) else str(err)
            raise SourceError("RPC_ERROR_" + str(code) + ":" + msg[:220])
        if "result" not in body:
            raise SourceError("RPC_RESULT_MISSING")
        return body["result"], raw

    def chain_check(self):
        found, _ = self.request("eth_chainId", [])
        if as_int(found) != self.chain:
            raise SourceError("RPC_WRONG_CHAIN_EXPECTED_" + str(self.chain))


def timestamp_for_block(rpc, number):
    block, _ = rpc.request("eth_getBlockByNumber", [hex(number), False])
    if not isinstance(block, dict) or as_int(block.get("number")) != number:
        raise SourceError("RPC_BLOCK_IDENTITY_MISMATCH")
    return as_int(block.get("timestamp"))


def first_block_at_or_after(rpc, unix_ts, tip):
    low, high = 0, tip + 1
    while low < high:
        mid = (low + high) // 2
        if timestamp_for_block(rpc, mid) < unix_ts:
            low = mid + 1
        else:
            high = mid
    if low > tip:
        raise SourceError("DAY_OUTSIDE_CHAIN_HISTORY")
    return low


def resolve_day(rpc, day):
    t0 = int(dt.datetime.strptime(day, "%Y-%m-%d").replace(tzinfo=dt.timezone.utc).timestamp())
    tiphex, _ = rpc.request("eth_blockNumber", [])
    tip = as_int(tiphex)
    first = first_block_at_or_after(rpc, t0, tip)
    after = first_block_at_or_after(rpc, t0 + 86400, tip)
    if first >= after:
        raise SourceError("NO_BLOCKS_IN_FROZEN_DAY")
    if timestamp_for_block(rpc, first) < t0 or timestamp_for_block(rpc, after - 1) >= t0 + 86400:
        raise SourceError("DAY_BLOCK_CLOCK_BOUNDARY_INCORRECT")
    return first, after - 1


def fetch_logs(rpc, chain, low, high):
    conf = CHAINS[chain]
    filters = {"fromBlock": hex(low), "toBlock": hex(high),
               "address": conf["factory"], "topics": [conf["topic"]]}
    data, raw = rpc.request("eth_getLogs", [filters])
    if not isinstance(data, list):
        raise SourceError("RPC_LOG_RESULT_NOT_ARRAY")
    for row in data:
        if not isinstance(row, dict) or str(row.get("address", "")).lower() != conf["factory"].lower():
            raise SourceError("RPC_LOG_ADDRESS_MISMATCH")
        topics = row.get("topics")
        if not isinstance(topics, list) or len(topics) < 3 or str(topics[0]).lower() != conf["topic"]:
            raise SourceError("RPC_LOG_TOPIC_MISMATCH")
        b = as_int(row.get("blockNumber"))
        if not low <= b <= high or row.get("removed") is True:
            raise SourceError("RPC_LOG_RANGE_OR_REMOVED_MISMATCH")
        for k in ("transactionIndex", "logIndex"):
            as_int(row.get(k))
        if not re.fullmatch("0x[0-9a-fA-F]{64}", str(row.get("transactionHash", ""))):
            raise SourceError("RPC_LOG_MISSING_TXHASH")
    return data, raw


def safe_file(path, raw):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".pending")
    with open(temp, "wb") as w:
        w.write(raw)
        w.flush()
        os.fsync(w.fileno())
    os.replace(temp, path)


def decode(row, chain):
    topics = row["topics"]
    a = ["0x" + item[-40:].lower() for item in topics[1:3]]
    for t in topics[1:3]:
        if not re.fullmatch(r"0x[0-9a-fA-F]{64}", t):
            raise SourceError("EVENT_TOKEN_TOPIC_NOT_32_BYTES")
    data = row.get("data", "")
    if not isinstance(data, str) or not re.fullmatch(r"0x[0-9a-fA-F]{128,}", data):
        raise SourceError("EVENT_DATA_MALFORMED")
    if chain == "base-v3" and len(topics) != 4:
        raise SourceError("V3_FEE_TOPIC_MISSING")
    if chain == "bsc-v2" and len(topics) != 3:
        raise SourceError("V2_UNEXPECTED_TOPIC_LAYOUT")
    pool = "0x" + data[2:66][-40:].lower() if chain == "bsc-v2" else "0x" + data[66:130][-40:].lower()
    if pool == "0x" + "0" * 40 or a[0] == a[1]:
        raise SourceError("ZERO_POOL_OR_DUPLICATE_TOKEN")
    return {
        "token0": a[0], "token1": a[1], "pool": pool,
        "block_number": as_int(row["blockNumber"]),
        "transaction_index": as_int(row["transactionIndex"]),
        "log_index": as_int(row["logIndex"]),
        "tx_hash": row["transactionHash"].lower(),
    }


def read_saved(directory, low, high, chain, endpoint_host):
    """Require every persisted segment to match this frozen chain, range and factory."""
    rows = []
    cursor = low
    for receipt_path in sorted(directory.glob("*.receipt.json"), key=lambda p: int(p.name.split("-")[0])):
        receipt = json.loads(receipt_path.read_text())
        if (receipt.get("chain") != chain or receipt.get("rpc_host") != endpoint_host or
            receipt.get("factory") != CHAINS[chain]["factory"].lower() or
            receipt.get("topic") != CHAINS[chain]["topic"]):
            raise SourceError("STORED_RECEIPT_WRONG_SOURCE_OR_SCOPE")
        start, end = receipt["start"], receipt["end"]
        if start != cursor or end < start or end > high:
            raise SourceError("STORED_SEGMENT_GAP_OVERLAP_OR_WRONG_BOUNDARY")
        raw_path = directory / (str(start) + "-" + str(end) + ".raw.json")
        raw = raw_path.read_bytes()
        if sha(raw) != receipt.get("response_sha256"):
            raise SourceError("STORED_RAW_SHA_MISMATCH")
        response = json.loads(raw)
        if not isinstance(response.get("result"), list):
            raise SourceError("STORED_RESPONSE_MALFORMED")
        for r in response["result"]:
            if str(r.get("address", "")).lower() != CHAINS[chain]["factory"].lower():
                raise SourceError("STORED_LOG_WRONG_FACTORY")
            ts = r.get("topics", [])
            if not ts or str(ts[0]).lower() != CHAINS[chain]["topic"]:
                raise SourceError("STORED_LOG_WRONG_TOPIC")
            if not start <= as_int(r.get("blockNumber")) <= end:
                raise SourceError("STORED_LOG_OUTSIDE_SEGMENT")
            rows.append(r)
        cursor = end + 1
    return cursor, rows


def build_roster(rows, chain):
    conf = CHAINS[chain]
    bases = {x.lower() for x in conf["bases"]}
    ordered = sorted([decode(x, chain) for x in rows], key=lambda x: (
        x["block_number"], x["transaction_index"], x["log_index"]))
    seen = set()
    cohort = []
    for entry in ordered:
        a, b = entry["token0"], entry["token1"]
        if (a in bases) == (b in bases):
            continue
        token = b if a in bases else a
        if token in bases or token in seen:
            continue
        seen.add(token)
        cohort.append({**entry, "token_ca": token, "pool_is_not_liquidity_or_swap_proof": True})
    return ordered, cohort[:30], len(cohort)


def run(args):
    chain = CHAINS[args.chain]
    endpoint = args.rpc or chain["rpc"]
    rpc = RPC(endpoint, chain["chain_id"], args.max_requests, args.delay)
    rpc.chain_check()
    first, last = resolve_day(rpc, args.day)
    if args.mode == "probe":
        attempts = []
        for n in (2000, 10):
            end = min(last, first + n - 1)
            try:
                logs, raw = fetch_logs(rpc, args.chain, first, end)
                attempts.append({"range": [first, end], "status": "OK", "event_count": len(logs),
                                 "raw_response_sha256": sha(raw)})
            except SourceError as e:
                attempts.append({"range": [first, end], "status": "ERROR", "reason": str(e)})
        print(plain_json({"schema": "MONSTER_FACTORY_RPC_PROBE_V1", "mode": "READ_ONLY_PROBE",
              "chain": args.chain, "rpc_host": rpc.host, "day": args.day,
              "resolved_full_day_blocks": [first, last], "tests": attempts,
              "full_day_covered": False, "cohort_30": "NOT_SCORABLE",
              "requests": rpc.calls}).strip())
        return
    out_dir = args.out_dir.resolve() / (args.chain + "-" + args.day)
    directory = out_dir / "raw_rpc_segments"
    directory.mkdir(parents=True, exist_ok=True)
    state = {"schema": "MONSTER_FACTORY_RPC_COHORT_V1", "chain": args.chain,
             "factory": chain["factory"], "topic": chain["topic"],
             "rpc_host": rpc.host, "day": args.day, "blocks": [first, last],
             "mode": "OFFLINE_READ_ONLY_MANUAL", "has_real_swap_or_historical_depth": False}
    try:
        cursor, rows = read_saved(directory, first, last, args.chain, rpc.host)
        width = args.chunk
        while cursor <= last:
            end = min(last, cursor + width - 1)
            try:
                new, raw = fetch_logs(rpc, args.chain, cursor, end)
            except SourceError as e:
                if ("limit" in str(e).lower() or "range" in str(e).lower() or
                    "too many" in str(e).lower() or "exceed" in str(e).lower()) and width > 1:
                    width = max(1, width // 2)
                    continue
                raise
            receipt = {"schema": "RPC_JSON_BYTES_SHA256_V1", "chain": args.chain,
                       "factory": chain["factory"].lower(), "topic": chain["topic"],
                       "rpc_host": rpc.host, "start": cursor, "end": end,
                       "response_sha256": sha(raw), "log_count": len(new)}
            safe_file(directory / (str(cursor) + "-" + str(end) + ".raw.json"), raw)
            safe_file(directory / (str(cursor) + "-" + str(end) + ".receipt.json"),
                      plain_json(receipt).encode())
            rows.extend(new)
            cursor = end + 1
        ordered, selection, eligible_total = build_roster(rows, args.chain)
        state.update({"status": "FULL_DAY_RPC_SEGMENTS_COLLECTED_ROSTER_ONLY",
                      "complete_contiguous_block_coverage": True,
                      "factory_events": len(ordered), "unique_quote_paired_tokens": eligible_total,
                      "cohort_created": len(selection) if len(selection) == 30 else 0,
                      "cohort_30_status": "FROZEN_UNVALIDATED_POOL_EVENTS_ONLY" if len(selection) == 30
                           else "NOT_SCORABLE_FEWER_THAN_30_ELIGIBLE",
                      "first_30_chronological_pools": selection,
                      "five_pit_fields_covered": "NOT_TESTED",
                      "real_executable_net_return": "UNKNOWN"})
    except (SourceError, ValueError, OSError) as e:
        state.update({"status": "PARTIAL_SOURCE_BLOCKED_NOT_ZERO_EVENTS",
                      "stop_reason": str(e), "complete_contiguous_block_coverage": False,
                      "cohort_created": 0, "cohort_30_status": "NOT_SCORABLE",
                      "real_executable_net_return": "UNKNOWN"})
    state["requests_this_invocation"] = rpc.calls
    safe_file(out_dir / "status.json", plain_json(state).encode())
    print(plain_json({"status": state["status"], "cohort": state["cohort_30_status"],
                      "out": str(out_dir / "status.json"), "calls": rpc.calls,
                      "stop_reason": state.get("stop_reason")}).strip())
    if not state["complete_contiguous_block_coverage"]:
        raise SystemExit(2)


def main():
    parser = argparse.ArgumentParser(description="Manual historical Factory RPC coverage; no transactions")
    parser.add_argument("--chain", choices=CHAINS, default="base-v3")
    parser.add_argument("--day", default="2025-07-01")
    parser.add_argument("--mode", choices=("probe", "scan"), default="probe")
    parser.add_argument("--rpc", default=None, help="Override only with a trusted HTTPS RPC with eth_getLogs")
    parser.add_argument("--out-dir", type=Path, default=Path.home() / "monster-pit-source-probe")
    parser.add_argument("--chunk", type=int, default=1000)
    parser.add_argument("--max-requests", type=int, default=250)
    parser.add_argument("--delay", type=float, default=0.3)
    args = parser.parse_args()
    if args.chunk < 1 or args.chunk > 10000 or args.max_requests < 1 or args.delay < 0:
        parser.error("invalid request budget / chunk / delay")
    try:
        run(args)
    except SourceError as e:
        print(plain_json({"status": "SOURCE_BLOCKED_CURRENT_RPC_NOT_MARKET_EMPTY",
                          "reason": str(e), "cohort_30": "NOT_SCORABLE"}).strip())
        raise SystemExit(2)


if __name__ == "__main__":
    main()
