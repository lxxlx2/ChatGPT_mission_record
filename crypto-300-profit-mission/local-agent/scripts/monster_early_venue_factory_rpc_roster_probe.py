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
    "bsc-v3": {
        "chain_id": 56,
        "rpc": "https://bsc-rpc.publicnode.com",
        "factory": "0x0BFbCF9fa4f9C56B0F40a671Ad40E0805A091865",
        "topic": "0x783cca1c0412dd0d695e784568c96da2e9c22ff989357a2e8b1d9b2b4e6b7118",
        "bases": ("0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c",
                  "0x55d398326f99059fF775485246999027B3197955"),
        "event": "PoolCreated",
    },
    "bsc-v2": {
        "chain_id": 56,
        "rpc": "https://bsc-rpc.publicnode.com",
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
        self.source_tag = sha(endpoint.encode("utf-8"))
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


def historical_v2_count(rpc, block):
    """Historical allPairsLength() proves expected factory PairCreated event count."""
    factory = CHAINS["bsc-v2"]["factory"]
    result, _ = rpc.request("eth_call", [{"to": factory, "data": "0x574f2ba3"}, hex(block)])
    return as_int(result)


def reconcile_v2_factory_counter(rpc, first, last, logs):
    before = historical_v2_count(rpc, first - 1)
    after = historical_v2_count(rpc, last)
    ordered = sorted(logs, key=lambda row: (
        as_int(row["blockNumber"]), as_int(row["transactionIndex"]),
        as_int(row["logIndex"])))
    if before + len(ordered) != after:
        raise SourceError("HISTORICAL_V2_FACTORY_EVENT_COUNT_MISMATCH")
    for seq, row in enumerate(ordered, before + 1):
        data = row.get("data", "")
        if not isinstance(data, str) or not re.fullmatch(r"0x[0-9a-fA-F]{128}", data):
            raise SourceError("HISTORICAL_V2_PAIR_CREATED_DATA_MALFORMED")
        emitted_number = as_int("0x" + data[66:130])
        if emitted_number != seq:
            raise SourceError("HISTORICAL_V2_FACTORY_SEQUENCE_MISMATCH")
    return {"status": "COUNTER_MATCHES_EVENTS", "pairs_before": before,
            "pairs_after": after, "created_events": len(ordered)}


def historical_v2_address(rpc, contract, call_data, block):
    """Decode only the 32-byte ABI address return, retaining raw provider bytes."""
    val, raw = rpc.request("eth_call", [{"to": contract, "data": call_data}, hex(block)])
    if not isinstance(val, str) or not re.fullmatch(r"0x[0-9a-fA-F]{64}", val):
        raise SourceError("BSC_V2_ADDRESS_ABI_INVALID")
    address = "0x" + val[-40:].lower()
    if address == "0x" + "0" * 40:
        raise SourceError("BSC_V2_FACTORY_ZERO_OR_MISSING_PAIR")
    return address, raw


def enumerate_bsc_v2(rpc, first, last, *, limit, out_dir):
    """Append-only historical factory index pilot; does not prove buy/sell or T_entry."""
    if first <= 0:
        raise SourceError("BSC_V2_INVALID_FIRST_BLOCK")
    before = historical_v2_count(rpc, first - 1)
    after = historical_v2_count(rpc, last)
    if after < before:
        raise SourceError("BSC_V2_NONMONOTONIC_FACTORY_COUNT")
    root = out_dir / "v2_historical_index_raw"
    root.mkdir(parents=True, exist_ok=True)
    selected, seen = [], set()
    attempted = 0
    cfg = CHAINS["bsc-v2"]
    bases = {a.lower() for a in cfg["bases"]}
    for index in range(before, min(after, before + limit)):
        pair_file = root / (str(index) + ".json")
        if pair_file.exists():
            row = json.loads(pair_file.read_bytes())
            if (row.get("factory_index") != index or row.get("block") != last
                or row.get("rpc_source_sha256") != rpc.source_tag
                or row.get("chain") != "bsc-v2"
                or row.get("factory") != cfg["factory"].lower()):
                raise SourceError("HISTORICAL_V2_RESUME_SOURCE_DRIFT")
            for name in ("pair", "token0", "token1"):
                if not re.fullmatch(r"0x[0-9a-f]{40}", row.get(name, "")):
                    raise SourceError("HISTORICAL_V2_SAVED_ADDRESS_MALFORMED")
            raws = row.get("raw_abi_response_records")
            if not isinstance(raws, list) or len(raws) != 3:
                raise SourceError("HISTORICAL_V2_SAVED_RAW_MISSING")
            if any(sha(x["raw_json"].encode("utf-8")) != x["sha256"]
                   for x in raws):
                raise SourceError("HISTORICAL_V2_SAVED_RAW_SHA_MISMATCH")
        else:
            pair, raw_pair = historical_v2_address(
                rpc, cfg["factory"], "0x1e3dd18b" + format(index, "064x"), last)
            token0, raw0 = historical_v2_address(rpc, pair, "0x0dfe1681", last)
            token1, raw1 = historical_v2_address(rpc, pair, "0xd21220a7", last)
            if not token0 < token1:
                raise SourceError("HISTORICAL_V2_INVALID_TOKEN_ORDER")
            raw_records = []
            for method, raw in (("allPairs", raw_pair), ("token0", raw0), ("token1", raw1)):
                raw_records.append({"method": method, "raw_json": raw.decode("utf-8"),
                                    "sha256": sha(raw)})
            row = {"chain": "bsc-v2", "factory": cfg["factory"].lower(),
                   "block": last, "factory_index": index,
                   "rpc_source_sha256": rpc.source_tag,
                   "pair": pair, "token0": token0, "token1": token1,
                   "raw_abi_response_records": raw_records}
            safe_file(pair_file, plain_json(row).encode("utf-8"))
        attempted += 1
        a, b = row["token0"], row["token1"]
        if (a in bases) == (b in bases):
            continue
        token = b if a in bases else a
        if token in seen:
            continue
        seen.add(token)
        selected.append({"factory_index": index, "pair": row["pair"],
                         "token_ca": token,
                         "quote_asset": a if a in bases else b,
                         "historical_identity_only": True,
                         "original_paircreated_tx_hash": None,
                         "t_entry": None,
                         "actual_two_sided_sellability": "NOT_SCORABLE"})
        if len(selected) >= 30:
            break
    return {
        "schema": "MONSTER_BSC_V2_FACTORY_HISTORICAL_IDENTITY_PILOT_V1",
        "status": ("CHRONOLOGICAL_FIRST30_V2_POOL_IDENTITIES_ONLY"
                   if len(selected) == 30 else "PARTIAL_NOT_30_ELIGIBLE_OR_LIMIT"),
        "factory": cfg["factory"].lower(), "factory_count_before_day": before,
        "factory_count_at_day_end": after, "factory_new_pools_in_day": after - before,
        "factory_index_rows_checked": attempted, "identity_candidates_found": len(selected),
        "sample_complete_first30_by_factory_order": len(selected) == 30,
        "sample": selected,
        "source_identity": "HISTORICAL_ONCHAIN_FACTORY_STORAGE_AND_PAIR_IMMUTABLE_TOKENS",
        "first_real_swap": "NOT_SCORABLE", "actual_executable_pnl": "UNKNOWN",
        "source_raw_archive_dir": str(root), "contains_current_token_list": False
    }


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
    if CHAINS[chain]["event"] == "PoolCreated" and len(topics) != 4:
        raise SourceError("V3_FEE_TOPIC_MISSING")
    if CHAINS[chain]["event"] == "PairCreated" and len(topics) != 3:
        raise SourceError("V2_UNEXPECTED_TOPIC_LAYOUT")
    pool = "0x" + data[2:66][-40:].lower() if CHAINS[chain]["event"] == "PairCreated" else "0x" + data[66:130][-40:].lower()
    if pool == "0x" + "0" * 40 or a[0] == a[1]:
        raise SourceError("ZERO_POOL_OR_DUPLICATE_TOKEN")
    return {
        "token0": a[0], "token1": a[1], "pool": pool,
        "block_number": as_int(row["blockNumber"]),
        "transaction_index": as_int(row["transactionIndex"]),
        "log_index": as_int(row["logIndex"]),
        "tx_hash": row["transactionHash"].lower(),
    }


def read_saved(directory, low, high, chain, endpoint_host, endpoint_sha=None):
    """Require every persisted segment to match this frozen chain, range and factory."""
    rows = []
    cursor = low
    for receipt_path in sorted(directory.glob("*.receipt.json"), key=lambda p: int(p.name.split("-")[0])):
        receipt = json.loads(receipt_path.read_text())
        if (receipt.get("chain") != chain or receipt.get("rpc_host") != endpoint_host or
            (endpoint_sha is not None and receipt.get("rpc_source_sha256") != endpoint_sha) or
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



def bootstrap_bsc_v2_saved_roster(rpc, first, last, out_dir, limit, start_rank=1):
    """Bounded historical PairCreated + same-tx Mint/Sync verification for prior frozen identities."""
    if not 1 <= start_rank <= 30 or not 1 <= limit <= 5:
        raise SourceError("BOOTSTRAP_INVALID_FROZEN_RANK_WINDOW")
    source_path = out_dir / "v2_factory_enum_status.json"
    if not source_path.is_file():
        raise SourceError("RUN_ENUMERATE_MODE_BEFORE_BOOTSTRAP")
    source = json.loads(source_path.read_text())
    if (source.get("chain") != "bsc-v2" or source.get("day_blocks") != [first, last]
            or source.get("rpc_source_sha256") != rpc.source_tag
            or source.get("sample_complete_first30_by_factory_order") is not True
            or len(source.get("sample", [])) != 30):
        raise SourceError("BOOTSTRAP_FROZEN_ROSTER_MISMATCH")
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from mission_agent.early.bsc_v2_pit import (PITInvalid, SWAP, first_creation_block,
                                                 first_later_reserve_update, verify_bootstrap,
                                                 verify_delayed_mint_sync)
    folder = out_dir / "v2_bootstrap_raw"
    folder.mkdir(parents=True, exist_ok=True)
    cache = {}
    def count_at(block):
        if block not in cache:
            cache[block] = historical_v2_count(rpc, block)
        return cache[block]
    records = []
    for item in source["sample"][start_rank - 1:start_rank - 1 + limit]:
        index = item["factory_index"]
        pair = item["pair"].lower()
        identity = json.loads((out_dir / "v2_historical_index_raw" /
                               (str(index) + ".json")).read_text())
        if (identity.get("factory_index") != index or
                identity.get("pair") != pair or
                identity.get("block") != last or
                identity.get("rpc_source_sha256") != rpc.source_tag):
            raise SourceError("BOOTSTRAP_RAW_FACTORY_IDENTITY_DRIFT")
        record = {"factory_index": index, "pair": pair, "token_ca": item["token_ca"],
                  "status": "UNRESOLVED", "source": "HISTORICAL_CHAIN_REPLAY_NOT_LIVE_OBSERVER"}
        try:
            creation = first_creation_block(index, first, last, count_at)
            factory_logs, raw_factory = fetch_logs(rpc, "bsc-v2", creation, creation)
            pool_filter = {"address": pair, "fromBlock": hex(creation),
                           "toBlock": hex(min(last, creation + 9))}
            pool_logs, raw_pair = rpc.request("eth_getLogs", [pool_filter])
            if not isinstance(pool_logs, list):
                raise SourceError("BOOTSTRAP_POOL_LOGS_NOT_ARRAY")
            for log in pool_logs:
                if (str(log.get("address", "")).lower() != pair
                        or not creation <= as_int(log.get("blockNumber")) <= min(last, creation + 9)
                        or log.get("removed") is True):
                    raise SourceError("BOOTSTRAP_POOL_LOG_WRONG_SOURCE_OR_RANGE")
            result = verify_bootstrap(
                factory=CHAINS["bsc-v2"]["factory"], factory_index=index,
                creation_block=creation, pool=pair, token0=identity["token0"],
                token1=identity["token1"], factory_logs=factory_logs,
                pool_logs=pool_logs)
            for tag, raw in (("factory", raw_factory), ("pool", raw_pair)):
                safe_file(folder / (str(index) + "." + tag + ".rpc.json"), raw)
                record[tag + "_response_sha256"] = sha(raw)
            record.update(result)
            record["first_swap_observed_within_10_blocks"] = any(
                str(x["topics"][0]).lower() == SWAP
                for x in pool_logs if x.get("topics"))
            start_time = (timestamp_for_block(rpc, creation)
                          if result.get("initial_quote_liquidity_proven") is True else 0)
            time_cache = {}
            def pool_update_at(block):
                if block not in time_cache:
                    val, raw = rpc.request("eth_call", [
                        {"to": pair, "data": "0x0902f1ac"}, hex(block)])
                    if not isinstance(val, str) or not re.fullmatch(
                            r"0x[0-9a-fA-F]{192}", val):
                        raise SourceError("POOL_RESERVE_TIMESTAMP_ABI_INVALID")
                    time_cache[block] = as_int("0x" + val[130:194])
                return time_cache[block]
            later_block = first_later_reserve_update(
                creation, last, start_time, pool_update_at)
            record["first_later_pool_reserve_update_block"] = later_block
            record["first_later_pool_reserve_update_is_not_first_swap_proof"] = True
            if later_block is not None:
                later, later_raw = rpc.request("eth_getLogs", [{
                    "address": pair, "fromBlock": hex(later_block),
                    "toBlock": hex(later_block)}])
                if not isinstance(later, list) or any(
                        str(x.get("address", "")).lower() != pair or
                        as_int(x.get("blockNumber")) != later_block or
                        x.get("removed") is True for x in later):
                    raise SourceError("FIRST_LATER_POOL_LOG_SOURCE_MISMATCH")
                safe_file(folder / (str(index) + ".later.rpc.json"), later_raw)
                record["later_response_sha256"] = sha(later_raw)
                if result.get("initial_quote_liquidity_proven") is not True:
                    delayed = verify_delayed_mint_sync(
                        pool=pair, creation_block=creation,
                        update_block=later_block, pool_logs=later)
                    record["delayed_liquidity"] = delayed
                record["first_later_reserve_update_has_swap"] = any(
                    str(x["topics"][0]).lower() == SWAP
                    for x in later if x.get("topics"))
                record["first_later_reserve_update_utc"] = (
                    dt.datetime.fromtimestamp(pool_update_at(later_block),
                                              tz=dt.timezone.utc).isoformat())
        except (SourceError, PITInvalid, ValueError, OSError, KeyError) as exc:
            record["status"] = "BOOTSTRAP_SOURCE_OR_IDENTITY_UNRESOLVED"
            record["reason"] = str(exc)[:180]
        record["sell_path"] = "UNKNOWN"
        record["t_entry"] = None
        records.append(record)
    return {"schema": "MONSTER_BSC_V2_HISTORICAL_BOOTSTRAP_BATCH_V1",
            "status": "BOUNDED_FIRST_N_PIT_CREATION_ONLY_NOT_EXECUTABLE",
            "verified_delayed_first_mint": sum(
                r.get("delayed_liquidity", {}).get("delayed_initial_liquidity_proven")
                is True for r in records),
            "verified_creation_and_first_mint": sum(
                r.get("initial_quote_liquidity_proven") is True for r in records),
            "records": records, "start_rank": start_rank,
            "requested_count": len(records),
            "source_day_blocks": [first, last],
            "source_rpc_fingerprint": rpc.source_tag,
            "real_executable_pnl": "UNKNOWN",
            "not_24_30_or_18_30_gate_pass": True}


def probe_frozen_bsc_v2_runtime_code(rpc, out_dir, evidence_path, start_rank, limit):
    """Bounded manual historical code checks over the original frozen 30 only.

    Each fetched eth_getCode JSON-RPC response is saved byte-for-byte with its
    audit-time SHA. No token deployment transaction or public observation time
    is inferred from a nonempty post-block code snapshot.
    """
    if not 1 <= start_rank <= 30 or not 1 <= limit <= 5:
        raise SourceError("DEPLOY_CODE_INVALID_FROZEN_RANK_RANGE")
    original = json.loads(Path(evidence_path).read_text(encoding="utf-8"))
    hist = original["historical_bsc_v2_append_only_factory_enumeration"]
    sample = hist["chronological_quoted_unique_first30"]
    cases = hist["creation_liquidity_source_spotchecks"]["cases"]
    baseline = json.loads((out_dir / "v2_factory_enum_status.json").read_text())
    if (len(sample) != 30 or len(cases) != 30
            or baseline.get("chain") != "bsc-v2"
            or baseline.get("sample_complete_first30_by_factory_order") is not True
            or baseline.get("day_blocks") != hist["july1_2025_utc"]
            or len(baseline.get("sample", [])) != 30):
        raise SourceError("DEPLOY_CODE_FROZEN_SOURCE_OR_DAY_MISMATCH")
    from mission_agent.early.bsc_v2_pit import (
        PITInvalid, locate_first_runtime_code_block)
    first_day = hist["july1_2025_utc"][0]
    archive = out_dir / "v2_runtime_code_raw" / rpc.source_tag
    archive.mkdir(parents=True, exist_ok=True)
    results = []
    for rank in range(start_rank, min(30, start_rank + limit - 1) + 1):
        row, case, frozen = sample[rank - 1], cases[rank - 1], baseline["sample"][rank - 1]
        if (row["cohort_rank"] != rank or case["rank"] != rank
                or case["index"] != row["factory_index"]
                or frozen["factory_index"] != row["factory_index"]
                or case["pair"].lower() != row["pool"].lower()
                or frozen["pair"].lower() != row["pool"].lower()
                or frozen["token_ca"].lower() != row["token_ca"].lower()
                or not first_day <= case["creation_block"] <= hist["july1_2025_utc"][1]):
            raise SourceError("DEPLOY_CODE_RANK_OR_IDENTITY_DRIFT")
        token = row["token_ca"].lower()
        index = case["index"]
        cache, records = {}, []
        def has_code(block):
            if block in cache:
                return cache[block]
            stem = archive / (str(index) + "." + str(block))
            bodyfile = Path(str(stem) + ".rpc.json")
            hashfile = Path(str(stem) + ".sha256")
            if bodyfile.exists() != hashfile.exists():
                raise SourceError("DEPLOY_CODE_INCOMPLETE_RAW_SHA_PAIR")
            if bodyfile.exists():
                raw = bodyfile.read_bytes()
                if sha(raw) != hashfile.read_text(encoding="utf-8").strip():
                    raise SourceError("DEPLOY_CODE_ARCHIVE_HASH_DRIFT")
                body = json.loads(raw)
                if not isinstance(body, dict) or body.get("error") or "result" not in body:
                    raise SourceError("DEPLOY_CODE_ARCHIVED_RPC_RESULT_INVALID")
                value = body["result"]
                src = "SAVED_SAME_RPC_FINGERPRINT_ARCHIVE"
            else:
                value, raw = rpc.request("eth_getCode", [token, hex(block)])
                safe_file(bodyfile, raw)
                safe_file(hashfile, (sha(raw) + "\n").encode("utf-8"))
                src = "FRESH_HISTORICAL_RPC"
            if not isinstance(value, str) or not re.fullmatch(r"0x(?:[0-9a-fA-F]{2})*", value):
                raise SourceError("DEPLOY_CODE_BYTECODE_RESULT_INVALID")
            exists = len(value) > 2
            cache[block] = exists
            records.append({"block": block, "source": src,
                            "response_sha256": sha(raw),
                            "runtime_code_present": exists})
            return exists
        answer = {
            "rank": rank, "factory_index": index,
            "creation_block": case["creation_block"],
            "at_creation_quote_floor_pass": case["initial_quote_floor_reached"],
            "source_state": "NOT_SCORABLE",
        }
        try:
            verified = locate_first_runtime_code_block(
                first_day, case["creation_block"], has_code)
            answer.update(verified)
            answer["source_state"] = "BOUNDED_HISTORICAL_CODE_STATE_ONLY"
        except (SourceError, PITInvalid, OSError, ValueError, TypeError) as exc:
            answer["source_state"] = "SOURCE_BLOCKED_UNRESOLVED"
            answer["reason"] = type(exc).__name__ + ":" + str(exc)[:180]
        answer["archived_snapshots_this_run"] = records
        results.append(answer)
        if answer["source_state"] == "SOURCE_BLOCKED_UNRESOLVED":
            break
    return {
        "schema": "MONSTER_BSC_V2_FIRST_RUNTIME_CODE_BATCH_V1",
        "status": ("BOUNDED_CODE_STATE_REPLAY_PASS_NOT_DEPLOY_TX"
                   if len(results) == min(limit, 31 - start_rank)
                   and all(x["source_state"] == "BOUNDED_HISTORICAL_CODE_STATE_ONLY"
                           for x in results)
                   else "SOURCE_PARTIAL_CODE_STATE_NOT_SCORABLE"),
        "chain": "bsc-v2", "day": "2025-07-01",
        "source_rpc_fingerprint": rpc.source_tag,
        "baseline_source_same_rpc": baseline["rpc_source_sha256"] == rpc.source_tag,
        "rank_results": results,
        "requested_start_rank": start_rank,
        "requested_count": len(results),
        "requests_this_invocation": rpc.calls,
        "archive_sha_calculated_at_read_not_original_independent_receipt": True,
        "deployment_tx_proven": False,
        "complete_24_of_30_pit_gate": "NOT_SCORABLE",
        "public_available_at": "UNVERIFIED",
        "no_trade": True,
    }


def audit_saved_bsc_v2_p0(out_dir, evidence_path):
    """Offline archive replay of the fixed 30, without RPC or private URLs.

    Hashes of the saved raw JSON are audit-time baselines only. This does not
    establish independent-provider fidelity, public T_entry, or sellability.
    """
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from mission_agent.early.bsc_v2_pit import (PITInvalid, verify_bootstrap,
                                               summarize_v2_archived_swap_windows)

    frozen = json.loads(Path(evidence_path).read_text(encoding="utf-8"))
    history = frozen["historical_bsc_v2_append_only_factory_enumeration"]
    expected = history["chronological_quoted_unique_first30"]
    cases = history["creation_liquidity_source_spotchecks"]["cases"]
    identities = {r["factory_index_zero_based"]: r for r in history["first36"]}
    source = json.loads((out_dir / "v2_factory_enum_status.json").read_text())
    roster = source.get("sample", [])
    if (len(expected) != 30 or len(cases) != 30 or len(roster) != 30
            or source.get("chain") != "bsc-v2"
            or source.get("day_blocks") != history["july1_2025_utc"]
            or not source.get("sample_complete_first30_by_factory_order")):
        raise SourceError("OFFLINE_AUDIT_FROZEN_ROSTER_OR_DATE_MISMATCH")
    if len({x["factory_index"] for x in roster}) != 30:
        raise SourceError("OFFLINE_AUDIT_DUPLICATE_FACTORY_INDEX")
    if source.get("rpc_source_sha256") is None:
        raise SourceError("OFFLINE_AUDIT_MISSING_SOURCE_FINGERPRINT")

    original_files = []
    results = []
    def original_json_file(path):
        raw = path.read_bytes()
        payload = json.loads(raw)
        if not isinstance(payload, dict) or "result" not in payload:
            raise SourceError("OFFLINE_AUDIT_RAW_JSONRPC_RESULT_MISSING")
        original_files.append({
            "relative_file": str(path.relative_to(out_dir)),
            "bytes": len(raw), "sha256_at_audit": sha(raw),
            "prior_independent_response_sha256": None,
        })
        return payload["result"]

    for rank, (member, case, item) in enumerate(zip(roster, cases, expected), 1):
        index = member["factory_index"]
        answer = {"rank": rank, "factory_index": index,
                  "status": "SOURCE_NOT_SCORABLE"}
        try:
            if (case["rank"] != rank or item["cohort_rank"] != rank
                    or index != case["index"] or index != item["factory_index"]
                    or member["pair"].lower() != case["pair"].lower()
                    ):
                raise SourceError("OFFLINE_AUDIT_IDENTITY_ORDER_DRIFT")
            if (member["token_ca"].lower() != item["token_ca"].lower()
                    or member["quote_asset"].lower() != item["quote_asset"].lower()
                    or member["pair"].lower() != item["pool"].lower()):
                raise SourceError("OFFLINE_AUDIT_TOKEN_POOL_OR_QUOTE_DRIFT")
            row = json.loads((out_dir / "v2_historical_index_raw" /
                              (str(index) + ".json")).read_text())
            key = identities[index]
            if (row.get("factory_index") != index or
                    row.get("pair", "").lower() != member["pair"].lower() or
                    row.get("rpc_source_sha256") != source["rpc_source_sha256"] or
                    row.get("block") != source["day_blocks"][1] or
                    row.get("token0") != key["token0"] or
                    row.get("token1") != key["token1"]):
                raise SourceError("OFFLINE_AUDIT_INDEX_DATA_DRIFT")
            abis = row.get("raw_abi_response_records", [])
            expected_abi = [("allPairs", row["pair"]),
                            ("token0", row["token0"]),
                            ("token1", row["token1"])]
            if len(abis) != 3:
                raise SourceError("OFFLINE_AUDIT_ABI_RAW_MISSING")
            for entry, (method, addr) in zip(abis, expected_abi):
                raw = entry["raw_json"].encode("utf-8")
                decoded = json.loads(raw)
                if (entry["method"] != method or sha(raw) != entry["sha256"]
                        or not isinstance(decoded, dict)
                        or decoded.get("result", "").lower() !=
                        "0x" + "0" * 24 + addr.lower()[2:]):
                    raise SourceError("OFFLINE_AUDIT_ABI_RESPONSE_SHA_OR_VALUE_MISMATCH")
            p = out_dir / "v2_bootstrap_raw" / str(index)
            factory_logs = original_json_file(Path(str(p) + ".factory.rpc.json"))
            pool_logs = original_json_file(Path(str(p) + ".pool.rpc.json"))
            if not isinstance(factory_logs, list) or not isinstance(pool_logs, list):
                raise SourceError("OFFLINE_AUDIT_EVENT_RESULT_NOT_ARRAY")
            for log in pool_logs:
                if (log.get("address", "").lower() != case["pair"].lower()
                        or not case["creation_block"] <= as_int(log.get("blockNumber"))
                        <= min(source["day_blocks"][1], case["creation_block"] + 9)
                        or log.get("removed") is True):
                    raise SourceError("OFFLINE_AUDIT_POOL_LOG_SCOPE_MISMATCH")
            proof = verify_bootstrap(
                factory=CHAINS["bsc-v2"]["factory"], factory_index=index,
                creation_block=case["creation_block"], pool=case["pair"],
                token0=row["token0"], token1=row["token1"],
                factory_logs=factory_logs, pool_logs=pool_logs)
            if (proof["creation_tx"] != case["creation_tx_hash"].lower()
                    or proof["initial_quote_liquidity_proven"] is not
                    case["same_tx_erc20_lp_transfer_sync_mint"]):
                raise SourceError("OFFLINE_AUDIT_MINT_OR_CREATION_CONFLICT")
            if proof["initial_quote_liquidity_proven"]:
                if (proof["reserve0_raw"] != case["initial_reserve0_raw"]
                        or proof["reserve1_raw"] != case["initial_reserve1_raw"]):
                    raise SourceError("OFFLINE_AUDIT_LP_RESERVES_DRIFT")
            archived_swap_windows = [{"name": "CREATION_BLOCK_TO_PLUS_9",
                                      "logs": pool_logs}]
            later = Path(str(p) + ".later.rpc.json")
            if later.is_file():
                later_events = original_json_file(later)
                if not isinstance(later_events, list) or any(
                        log.get("address", "").lower() != case["pair"].lower()
                        or log.get("removed") is True for log in later_events):
                    raise SourceError("OFFLINE_AUDIT_LATER_POOL_LOG_SCOPE_MISMATCH")
                archived_swap_windows.append({
                    "name": "FIRST_LATER_POOL_RESERVE_UPDATE_BLOCK",
                    "logs": later_events})
            quote = item["quote_asset"].lower()
            known_bases = tuple(x.lower() for x in CHAINS["bsc-v2"]["bases"])
            if quote not in known_bases:
                raise SourceError("OFFLINE_AUDIT_UNKNOWN_BSC_QUOTE")
            frozen_quote_depth_floor = (
                2 * 10**18 if quote == known_bases[0] else 1000 * 10**18)
            answer["archived_pair_swap_evidence"] = summarize_v2_archived_swap_windows(
                pool=case["pair"], token0=row["token0"], token1=row["token1"],
                quote_asset=item["quote_asset"], windows=archived_swap_windows,
                quote_reserve_floor_raw=frozen_quote_depth_floor)
            answer["observed_pool_depth_at_swap_is_not_public_t_entry"] = True
            answer["status"] = "CREATION_MINT_SYNC_CONFIRMED" if (
                proof["initial_quote_liquidity_proven"]
                ) else "CREATION_CONFIRMED_NO_SAME_TX_MINT_SYNC"
            answer["creation_tx"] = proof["creation_tx"]
            answer["initial_lp_same_creation_tx"] = proof["initial_quote_liquidity_proven"]
            answer["sellable_at_notional"] = "UNVERIFIED"
        except (SourceError, PITInvalid, OSError, ValueError, TypeError, KeyError, IndexError) as exc:
            answer["status"] = "SOURCE_NOT_SCORABLE"
            answer["reason"] = type(exc).__name__ + ":" + str(exc)[:150]
        results.append(answer)
    good = [r for r in results if r["status"] != "SOURCE_NOT_SCORABLE"]
    creation_lp = sum(r.get("initial_lp_same_creation_tx") is True for r in good)
    no_creation_lp = sum(r.get("initial_lp_same_creation_tx") is False for r in good)
    complete = len(good) == 30 and creation_lp == 25 and no_creation_lp == 5
    observed_sells = [x["rank"] for x in good if
                      x["archived_pair_swap_evidence"]["observed_token_to_quote_with_sync"] > 0]
    observed_buys = [x["rank"] for x in good if
                     x["archived_pair_swap_evidence"]["observed_quote_to_token_with_sync"] > 0]
    absent_later = [x["rank"] for x in good if
                    len(x["archived_pair_swap_evidence"]["archived_windows"]) == 1]
    buy_above = [x["rank"] for x in good if
                 x["archived_pair_swap_evidence"]["observed_buy_at_or_above_frozen_quote_depth"]]
    sell_above = [x["rank"] for x in good if
                  x["archived_pair_swap_evidence"]["observed_sell_at_or_above_frozen_quote_depth"]]
    buy_below = [x["rank"] for x in good if
                 x["archived_pair_swap_evidence"]["observed_buy_below_frozen_quote_depth"]]
    sell_below = [x["rank"] for x in good if
                  x["archived_pair_swap_evidence"]["observed_sell_below_frozen_quote_depth"]]
    reserve_unknown = [x["rank"] for x in good if
                       x["archived_pair_swap_evidence"]["observed_swaps_without_proven_preswap_depth"]]
    buy_first_above_floor_same_tx_first_sync = [x["rank"] for x in good if
        x["archived_pair_swap_evidence"]["first_above_floor_buy_public_reaction_status"]
        == "SAME_TX_NOT_PUBLICLY_REACTABLE_AFTER_SYNC"]
    buy_first_above_floor_same_tx_first_mint = [x["rank"] for x in good if
        x["archived_pair_swap_evidence"]["first_above_floor_buy_prior_mint_same_tx"]]
    observed_transaction_activity = [{
        "rank": x["rank"],
        "buy_swap_events": x["archived_pair_swap_evidence"]["observed_buy_swap_events"],
        "buy_distinct_txs": x["archived_pair_swap_evidence"]["observed_buy_distinct_transactions"],
        "above_floor_buy_swap_events": (
            x["archived_pair_swap_evidence"]["observed_above_floor_buy_swap_events"]),
        "above_floor_buy_distinct_txs": (
            x["archived_pair_swap_evidence"]["observed_above_floor_buy_distinct_transactions"]),
        "sell_swap_events": x["archived_pair_swap_evidence"]["observed_sell_swap_events"],
        "sell_distinct_txs": x["archived_pair_swap_evidence"]["observed_sell_distinct_transactions"],
        "above_floor_sell_distinct_txs": (
            x["archived_pair_swap_evidence"]["observed_above_floor_sell_distinct_transactions"]),
        "first_qualified_buy_public_reaction_status": (
            x["archived_pair_swap_evidence"]["first_above_floor_buy_public_reaction_status"]),
        "qualified_buy_later_block_distinct_txs": (
            x["archived_pair_swap_evidence"]["observed_qualified_buy_distinct_tx_count_later_block"]),
        } for x in good]
    return {
        "schema": "MONSTER_BSC_V2_P0_LOCAL_ORIGINAL_RPC_OFFLINE_REPLAY_V1",
        "status": ("LOCAL_FROZEN_30_CREATION_REPLAY_PASS" if complete
                   else "PARTIAL_OR_SOURCE_INCONSISTENT_NOT_SCORABLE"),
        "scope": "PANCAKE_V2_BSC_FIRST30_2025_07_01_ONLY",
        "archive_source_fingerprint": source["rpc_source_sha256"],
        "all_30_roster_matched": len(roster) == 30,
        "fully_replayed_creation_count": len(good),
        "same_tx_initial_lp_count": creation_lp,
        "created_without_same_tx_initial_lp": no_creation_lp,
        "unknown_ranks": [r["rank"] for r in results
                          if r["status"] == "SOURCE_NOT_SCORABLE"],
        "original_response_files_audited": len(original_files),
        "original_response_manifest": original_files,
        "rank_results": results,
        "observed_token_to_quote_swap_with_same_tx_sync_ranks": observed_sells,
        "observed_quote_to_token_swap_with_same_tx_sync_ranks": observed_buys,
        "later_update_source_window_not_archived_ranks": absent_later,
        "observed_buy_with_proven_preswap_quote_floor_ranks": buy_above,
        "observed_sell_with_proven_preswap_quote_floor_ranks": sell_above,
        "observed_buy_below_preswap_quote_floor_ranks": buy_below,
        "observed_sell_below_preswap_quote_floor_ranks": sell_below,
        "observed_swap_preswap_depth_unresolved_ranks": reserve_unknown,
        "observed_swap_activity_distinct_transactions_by_rank": observed_transaction_activity,
        "observed_swap_transactions_not_same_as_distinct_buyers": True,
        "first_above_floor_buy_same_tx_as_first_above_floor_sync_ranks":
            buy_first_above_floor_same_tx_first_sync,
        "first_above_floor_buy_with_prior_mint_in_same_tx_ranks":
            buy_first_above_floor_same_tx_first_mint,
        "same_tx_first_qualified_buy_not_public_reaction": True,
        "quote_depth_floor_is_research_eligibility_not_purchase_notional": True,
        "archive_swap_window_observation_scope":
            "FIRST_TEN_CREATION_BLOCKS_PLUS_ONE_LATER_UPDATE_BLOCK_IF_SAVED; NONCONTIGUOUS",
        "observed_sells_are_not_same_notional_user_sellability": True,
        "raw_sha256_scope": "RECALCULATED_FROM_LOCAL_BYTES_AT_AUDIT_NO_PRIOR_INDEPENDENT_SHA",
        "response_headers_captured": False,
        "independent_provider_verified": False,
        "public_t_entry": "UNVERIFIED",
        "token_deployment_date": "UNVERIFIED",
        "historical_dynamic_buy_sell": "UNVERIFIED",
        "eighteen_of_thirty_sellable_gate": "NOT_SCORABLE",
        "twentyfour_of_thirty_complete_pit_gate": "NOT_SCORABLE",
        "no_network_no_trade": True,
    }


def frozen_depth_qualified_real_sell_targets(evidence):
    """An already identified source-only 18-rank set, never a P0 trading gate."""
    history = evidence["historical_bsc_v2_append_only_factory_enumeration"]
    cohort = history["chronological_quoted_unique_first30"]
    identities = {r["factory_index_zero_based"]: r for r in history["first36"]}
    main = evidence["bsc_v2_p0_uploaded20_actual_buy_and_indexed_real_sell_replay_20261020"]
    delayed = evidence["bsc_v2_p0_ranks16_17_post_atomic_distinct_buy_and_partial_sell_pilot_20261020"]
    if len(cohort) != 30 or len(main["case_results"]) != 20 or len(delayed["cases"]) != 2:
        raise SourceError("SELL_ARCHIVE_FROZEN_COHORT_DRIFT")
    selected = []
    for item in main["case_results"]:
        if item["sell_above_frozen_floor"]:
            selected.append((item["rank"], item["sell_tx"], item["sell_block"],
                             item["sell_pool_swap_token_in_raw"],
                             item["sell_pool_swap_quote_out_raw"],
                             item["sell_preswap_quote_reserve_raw"]))
    for item in delayed["cases"]:
        selected.append((item["rank"], item["real_sell_tx"],
                         item["real_first_indexed_sell_block"],
                         item["real_token_transfer_into_pool_raw"],
                         item["pool_quote_out_raw"],
                         item["sell_preswap_quote_reserve_raw"]))
    ranks = [row[0] for row in selected]
    if len(selected) != 18 or len(set(ranks)) != 18:
        raise SourceError("SELL_ARCHIVE_EXPECTED_18_UNIQUE_RANKS")
    targets = []
    for rank, tx, block, token_in, quote_out, pre_quote in sorted(selected):
        if type(rank) is not int or not 1 <= rank <= 30:
            raise SourceError("SELL_ARCHIVE_RANK_INVALID")
        orig = cohort[rank - 1]
        if orig["cohort_rank"] != rank:
            raise SourceError("SELL_ARCHIVE_RANK_IDENTITY_MISMATCH")
        pair = identities[orig["factory_index"]]
        quote = orig["quote_asset"].lower()
        quote_is_token0 = pair["token0"].lower() == quote
        if quote not in tuple(x.lower() for x in CHAINS["bsc-v2"]["bases"]):
            raise SourceError("SELL_ARCHIVE_UNKNOWN_QUOTE")
        if not quote_is_token0 and pair["token1"].lower() != quote:
            raise SourceError("SELL_ARCHIVE_QUOTE_NOT_IN_PAIR")
        token = pair["token1"] if quote_is_token0 else pair["token0"]
        if token.lower() != orig["token_ca"].lower():
            raise SourceError("SELL_ARCHIVE_TOKEN_NOT_IN_PAIR")
        floor = (2 if quote == CHAINS["bsc-v2"]["bases"][0].lower()
                 else 1000) * 10**18
        if (type(block) is not int or block <= 0 or
                not isinstance(tx, str) or not re.fullmatch("0x[0-9a-fA-F]{64}", tx) or
                any(not isinstance(a, str) or not a.isdecimal() or int(a) <= 0
                    for a in (token_in, quote_out, pre_quote)) or
                int(pre_quote) < floor):
            raise SourceError("SELL_ARCHIVE_INPUT_DEPTH_OR_ID_INVALID")
        targets.append({"rank": rank, "tx": tx.lower(), "block": block,
                        "pair": orig["pool"].lower(), "token": token.lower(),
                        "quote": quote, "quote_is_token0": quote_is_token0,
                        "token_in_raw": token_in, "quote_out_raw": quote_out,
                        "pre_quote_raw": pre_quote})
    return targets


def validate_frozen_real_sell_receipt(receipt, target):
    """Fail closed on transaction, pool reserves, transfers and raw sell amounts."""
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from mission_agent.early.bsc_v2_pit import SYNC, SWAP, words
    transfer_topic = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
    if (not isinstance(receipt, dict) or receipt.get("status") != "0x1" or
            str(receipt.get("transactionHash", "")).lower() != target["tx"] or
            as_int(receipt.get("blockNumber")) != target["block"] or
            not isinstance(receipt.get("logs"), list)):
        raise SourceError("SELL_RECEIPT_IDENTITY_OR_STATUS_MISMATCH")
    logs = receipt["logs"]
    for row in logs:
        if (not isinstance(row, dict) or
                str(row.get("transactionHash", "")).lower() != target["tx"] or
                as_int(row.get("blockNumber")) != target["block"] or
                not isinstance(row.get("topics"), list)):
            raise SourceError("SELL_RECEIPT_LOG_NOT_SAME_TX")
        as_int(row.get("logIndex"))
    pool_logs = [(as_int(x["logIndex"]), x) for x in logs
                 if x.get("address", "").lower() == target["pair"]]
    swaps = [(k, x) for k, x in pool_logs
             if x["topics"] and x["topics"][0].lower() == SWAP]
    verified = []
    for k, swap in swaps:
        amount0in, amount1in, amount0out, amount1out = words(swap["data"], 4)
        q_in, token_in = ((amount0in, amount1in) if target["quote_is_token0"]
                          else (amount1in, amount0in))
        q_out, token_out = ((amount0out, amount1out) if target["quote_is_token0"]
                            else (amount1out, amount0out))
        if q_in != 0 or token_out != 0 or token_in <= 0 or q_out <= 0:
            continue
        syncs = [(i, x) for i, x in pool_logs
                 if i < k and x["topics"] and x["topics"][0].lower() == SYNC]
        if not syncs:
            continue
        sync = max(syncs, key=lambda x: x[0])[1]
        r0, r1 = words(sync["data"])
        after_q, after_token = ((r0, r1) if target["quote_is_token0"]
                                else (r1, r0))
        pre_quote, pre_token = after_q - q_in + q_out, after_token - token_in + token_out
        if pre_quote <= 0 or pre_token <= 0:
            raise SourceError("SELL_RECEIPT_IMPOSSIBLE_PRE_RESERVES")
        token_paid = [x for x in logs
            if (x.get("address", "").lower() == target["token"]
                and len(x["topics"]) == 3 and x["topics"][0].lower() == transfer_topic
                and x["topics"][2][-40:].lower() == target["pair"][2:]
                and int(x["data"], 16) == token_in)]
        quote_received = [x for x in logs
            if (x.get("address", "").lower() == target["quote"]
                and len(x["topics"]) == 3 and x["topics"][0].lower() == transfer_topic
                and x["topics"][1][-40:].lower() == target["pair"][2:]
                and int(x["data"], 16) == q_out)]
        if (token_paid and quote_received and
                str(token_in) == target["token_in_raw"] and
                str(q_out) == target["quote_out_raw"] and
                str(pre_quote) == target["pre_quote_raw"]):
            verified.append({"swap_log_index": k, "token_in_raw": str(token_in),
                             "quote_out_raw": str(q_out),
                             "preswap_quote_raw": str(pre_quote),
                             "token_transfer_log_index": as_int(token_paid[0]["logIndex"]),
                             "quote_transfer_log_index": as_int(quote_received[0]["logIndex"])})
    if len(verified) != 1:
        raise SourceError("SELL_RECEIPT_SWAP_SYNC_TRANSFER_OR_RESERVE_NOT_PROVEN")
    gas_price = receipt.get("effectiveGasPrice")
    if gas_price is not None:
        as_int(gas_price)
    return {"rank": target["rank"], "tx": target["tx"],
            "block": target["block"], **verified[0],
            "receipt_status": "0x1", "historical_real_pool_sell": True,
            "gas_price_field": gas_price,
            "gas_cost_evidence": "UNVERIFIED_ZERO_REPORTED" if gas_price == "0x0"
                                 else "RPC_RECEIPT_ONLY_NOT_INDEPENDENTLY_VERIFIED",
            "uniform_notional_sellability": "NOT_SCORABLE",
            "public_available_at": "UNVERIFIED"}


def replay_frozen_sell_receipts(directory, evidence_path, rpc=None):
    """Exact 18 receipt calls on first run; saved raw bytes only thereafter."""
    evidence = json.loads(Path(evidence_path).read_text(encoding="utf-8"))
    targets = frozen_depth_qualified_real_sell_targets(evidence)
    manifest_path = directory / "v2_p0_real_sell_receipt_manifest.json"
    old = json.loads(manifest_path.read_text()) if manifest_path.exists() else None
    if old is not None and (old.get("rank_count") != 18 or
                            [x.get("rank") for x in old.get("rows", [])] !=
                            [x["rank"] for x in targets]):
        raise SourceError("SELL_ARCHIVE_EXISTING_MANIFEST_IDENTITY_DRIFT")
    if rpc is None and old is None:
        raise SourceError("SELL_ARCHIVE_NO_LOCAL_MANIFEST")
    if rpc is not None and old is not None and old.get("endpoint_sha256") != rpc.source_tag:
        raise SourceError("SELL_ARCHIVE_ENDPOINT_FINGERPRINT_CHANGED")
    source_tag = old["endpoint_sha256"] if rpc is None else rpc.source_tag
    rows = []
    for target in targets:
        filename = "rank_" + str(target["rank"]) + ".rpc.json"
        stored = directory / "v2_p0_real_sell_receipts" / source_tag / filename
        if stored.exists():
            raw = stored.read_bytes()
        else:
            if rpc is None:
                raise SourceError("SELL_ARCHIVE_MISSING_RAW_RANK_" + str(target["rank"]))
            _, raw = rpc.request("eth_getTransactionReceipt", [target["tx"]])
        try:
            envelope = json.loads(raw)
        except (ValueError, UnicodeDecodeError):
            raise SourceError("SELL_ARCHIVE_INVALID_RAW_JSON") from None
        if not isinstance(envelope, dict) or "result" not in envelope:
            raise SourceError("SELL_ARCHIVE_MISSING_RAW_RESULT")
        row = validate_frozen_real_sell_receipt(envelope["result"], target)
        if old is not None:
            prior = old["rows"][len(rows)]
            if (prior.get("rank") != target["rank"] or
                    prior.get("sha256") != sha(raw) or
                    prior.get("tx") != target["tx"]):
                raise SourceError("SELL_ARCHIVE_RAW_OR_TX_SHA_DRIFT")
        if not stored.exists():
            safe_file(stored, raw)
        rows.append({**row, "relative_raw_file": str(stored.relative_to(directory)),
                     "raw_bytes": len(raw), "sha256": sha(raw)})
    manifest = {
        "status": "HISTORICAL_18_REAL_SELL_RECEIPTS_ARCHIVED_AND_OFFLINE_REPLAYED",
        "chain": "bsc-v2", "day": "2025-07-01", "rank_count": 18,
        "endpoint_sha256": source_tag,
        "requests_this_invocation": 0 if rpc is None else rpc.calls,
        "source_is_independent_provider": "UNVERIFIED",
        "all_original_rpc_bodies_sha256_checked": True,
        "receipt_and_swap_transfer_sync_matches": 18,
        "research_frozen_quote_depth_not_user_order_notional": True,
        "public_T_entry": "UNVERIFIED",
        "notional_18_of_30_gate": "NOT_SCORABLE",
        "rows": rows,
    }
    if old is not None:
        if [(x["rank"], x["sha256"], x["tx"]) for x in rows] != [
                (x["rank"], x["sha256"], x["tx"]) for x in old["rows"]]:
            raise SourceError("SELL_ARCHIVE_MANIFEST_CHANGED")
    else:
        safe_file(manifest_path, plain_json(manifest).encode("utf-8"))
    return manifest


def run(args):
    if args.mode == "audit":
        if args.chain != "bsc-v2" or args.day != "2025-07-01":
            raise SourceError("OFFLINE_AUDIT_ONLY_FROZEN_BSC_V2_DAY")
        base = args.out_dir.resolve() / ("bsc-v2-" + args.day)
        evidence_path = (Path(__file__).resolve().parents[2] /
                         "monster/evidence/early/P0/P0_SOURCE_PROBE_20261019.json")
        result = audit_saved_bsc_v2_p0(base, evidence_path)
        safe_file(base / "v2_p0_offline_audit_status.json",
                  plain_json(result).encode("utf-8"))
        print(plain_json({k: result[k] for k in (
            "status", "fully_replayed_creation_count", "same_tx_initial_lp_count",
            "created_without_same_tx_initial_lp", "unknown_ranks",
            "original_response_files_audited",
            "observed_token_to_quote_swap_with_same_tx_sync_ranks",
            "observed_quote_to_token_swap_with_same_tx_sync_ranks",
            "later_update_source_window_not_archived_ranks",
            "observed_buy_with_proven_preswap_quote_floor_ranks",
            "observed_sell_with_proven_preswap_quote_floor_ranks",
            "observed_buy_below_preswap_quote_floor_ranks",
            "observed_sell_below_preswap_quote_floor_ranks",
            "observed_swap_preswap_depth_unresolved_ranks",
            "first_above_floor_buy_same_tx_as_first_above_floor_sync_ranks",
            "first_above_floor_buy_with_prior_mint_in_same_tx_ranks",
            "twentyfour_of_thirty_complete_pit_gate",
            "eighteen_of_thirty_sellable_gate")}).strip())
        if result["status"] != "LOCAL_FROZEN_30_CREATION_REPLAY_PASS":
            raise SystemExit(2)
        return
    if args.mode == "deployment":
        if args.chain != "bsc-v2" or args.day != "2025-07-01":
            raise SourceError("DEPLOY_CODE_ONLY_FROZEN_BSC_V2_DAY")
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        chain = CHAINS[args.chain]
        rpc = RPC(args.rpc or chain["rpc"], chain["chain_id"],
                  args.max_requests, args.delay)
        rpc.chain_check()
        directory = args.out_dir.resolve() / (args.chain + "-" + args.day)
        evidence_path = (Path(__file__).resolve().parents[2] /
                         "monster/evidence/early/P0/P0_SOURCE_PROBE_20261019.json")
        result = probe_frozen_bsc_v2_runtime_code(
            rpc, directory, evidence_path, args.bootstrap_start_rank,
            args.bootstrap_limit)
        last_rank = (args.bootstrap_start_rank + result["requested_count"] - 1)
        safe_file(directory / ("v2_deployment_rank_" + str(args.bootstrap_start_rank)
                              + "_" + str(last_rank) + ".json"),
                  plain_json(result).encode("utf-8"))
        print(plain_json({
            "status": result["status"],
            "requested_count": result["requested_count"],
            "requests_this_invocation": result["requests_this_invocation"],
            "rank_results": [{k: row.get(k) for k in
                             ("rank", "status", "first_code_block_in_day",
                              "source_state", "reason")}
                            for row in result["rank_results"]],
            "complete_24_of_30_pit_gate": result["complete_24_of_30_pit_gate"],
        }).strip())
        if result["status"] != "BOUNDED_CODE_STATE_REPLAY_PASS_NOT_DEPLOY_TX":
            raise SystemExit(2)
        return
    chain = CHAINS[args.chain]
    endpoint = args.rpc or chain["rpc"]
    rpc = RPC(endpoint, chain["chain_id"], args.max_requests, args.delay)
    rpc.chain_check()
    first, last = resolve_day(rpc, args.day)
    if args.mode == "enumerate":
        if args.chain != "bsc-v2":
            raise SourceError("FACTORY_STORAGE_ENUMERATION_ONLY_FOR_BSC_V2")
        out_dir = args.out_dir.resolve() / (args.chain + "-" + args.day)
        try:
            result = enumerate_bsc_v2(rpc, first, last, limit=args.limit, out_dir=out_dir)
        except SourceError as exc:
            result = {"status": "SOURCE_PARTIAL_OR_UNAVAILABLE", "reason": str(exc),
                      "sample_complete_first30_by_factory_order": False,
                      "first_real_swap": "NOT_SCORABLE"}
        result.update({"day": args.day, "chain": args.chain, "day_blocks": [first, last],
                       "provider_host": rpc.host, "rpc_source_sha256": rpc.source_tag,
                       "requests_this_invocation": rpc.calls,
                       "not_final_population_or_PIT_pass": True})
        safe_file(out_dir / "v2_factory_enum_status.json",
                  plain_json(result).encode("utf-8"))
        print(plain_json({k: result.get(k) for k in (
            "status", "factory_new_pools_in_day", "factory_index_rows_checked",
            "identity_candidates_found", "sample_complete_first30_by_factory_order",
            "requests_this_invocation", "reason")}).strip())
        if not result.get("sample_complete_first30_by_factory_order"):
            raise SystemExit(2)
        return
    if args.mode == "bootstrap":
        if args.chain != "bsc-v2":
            raise SourceError("BOOTSTRAP_REQUIRES_BSC_V2")
        out_dir = args.out_dir.resolve() / (args.chain + "-" + args.day)
        result = bootstrap_bsc_v2_saved_roster(
            rpc, first, last, out_dir, args.bootstrap_limit,
            start_rank=args.bootstrap_start_rank)
        result["requests_this_invocation"] = rpc.calls
        rank_first = args.bootstrap_start_rank
        rank_last = rank_first + result["requested_count"] - 1
        safe_file(out_dir / ("v2_bootstrap_rank_" + str(rank_first) + "_"
                             + str(rank_last) + ".json"),
                  plain_json(result).encode("utf-8"))
        safe_file(out_dir / "v2_bootstrap_status.json",
                  plain_json(result).encode("utf-8"))
        print(plain_json({k: result[k] for k in (
            "status", "verified_creation_and_first_mint", "requested_count",
            "requests_this_invocation")}).strip())
        return
    if args.mode == "probe":
        attempts = []
        for n in (2000, 10):
            end = min(last, first + n - 1)
            try:
                logs, raw = fetch_logs(rpc, args.chain, first, end)
                sample = {"range": [first, end], "status": "OK", "event_count": len(logs),
                          "raw_response_sha256": sha(raw)}
                if args.chain == "bsc-v2":
                    try:
                        sample["v2_factory_counter"] = reconcile_v2_factory_counter(
                            rpc, first, end, logs)
                    except SourceError as e:
                        sample["v2_factory_counter"] = {
                            "status": "UNVERIFIED_OR_MISMATCH", "reason": str(e)}
                attempts.append(sample)
            except SourceError as e:
                attempts.append({"range": [first, end], "status": "ERROR", "reason": str(e)})
        print(plain_json({"schema": "MONSTER_FACTORY_RPC_PROBE_V1", "mode": "READ_ONLY_PROBE",
              "chain": args.chain, "rpc_host": rpc.host,
              "rpc_source_sha256": rpc.source_tag, "day": args.day,
              "resolved_full_day_blocks": [first, last], "tests": attempts,
              "full_day_covered": False, "cohort_30": "NOT_SCORABLE",
              "requests": rpc.calls}).strip())
        return
    out_dir = args.out_dir.resolve() / (args.chain + "-" + args.day)
    directory = out_dir / "raw_rpc_segments"
    directory.mkdir(parents=True, exist_ok=True)
    state = {"schema": "MONSTER_FACTORY_RPC_COHORT_V1", "chain": args.chain,
             "factory": chain["factory"], "topic": chain["topic"],
             "rpc_host": rpc.host, "rpc_source_sha256": rpc.source_tag,
             "day": args.day, "blocks": [first, last],
             "mode": "OFFLINE_READ_ONLY_MANUAL", "has_real_swap_or_historical_depth": False}
    try:
        cursor, rows = read_saved(directory, first, last, args.chain, rpc.host, rpc.source_tag)
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
                       "rpc_host": rpc.host, "rpc_source_sha256": rpc.source_tag,
                       "start": cursor, "end": end,
                       "response_sha256": sha(raw), "log_count": len(new)}
            safe_file(directory / (str(cursor) + "-" + str(end) + ".raw.json"), raw)
            safe_file(directory / (str(cursor) + "-" + str(end) + ".receipt.json"),
                      plain_json(receipt).encode())
            rows.extend(new)
            cursor = end + 1
        counter_check = (reconcile_v2_factory_counter(rpc, first, last, rows)
                         if args.chain == "bsc-v2" else {"status": "NOT_AVAILABLE_FOR_THIS_FACTORY"})
        ordered, selection, eligible_total = build_roster(rows, args.chain)
        state.update({"status": "FULL_DAY_RPC_SEGMENTS_COLLECTED_ROSTER_ONLY",
                      "complete_contiguous_block_coverage": True,
                      "factory_events": len(ordered), "historical_counter_check": counter_check,
                      "unique_quote_paired_tokens": eligible_total,
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
    parser.add_argument("--mode", choices=("probe", "scan", "enumerate", "bootstrap", "audit", "deployment"), default="probe")
    parser.add_argument("--limit", type=int, default=45,
                        help="BSC V2 historical index identities to check, max 200 per invocation")
    parser.add_argument("--bootstrap-start-rank", type=int, default=1,
                        help="First 1-based frozen cohort rank to verify (1–30)")
    parser.add_argument("--bootstrap-limit", type=int, default=3,
                        help="Max frozen BSC V2 identities per manual initial-liquidity batch (1–5)")
    parser.add_argument("--rpc", default=None, help="Override only with a trusted HTTPS RPC with eth_getLogs")
    parser.add_argument("--out-dir", type=Path, default=Path.home() / "monster-pit-source-probe")
    parser.add_argument("--chunk", type=int, default=1000)
    parser.add_argument("--max-requests", type=int, default=250)
    parser.add_argument("--delay", type=float, default=0.3)
    args = parser.parse_args()
    if (args.chunk < 1 or args.chunk > 10000 or args.max_requests < 1
        or not 1 <= args.limit <= 200 or not 1 <= args.bootstrap_limit <= 5
        or not 1 <= args.bootstrap_start_rank <= 30
        or args.delay < 0):
        parser.error("invalid request budget / chunk / delay")
    try:
        run(args)
    except SourceError as e:
        print(plain_json({"status": "SOURCE_BLOCKED_CURRENT_RPC_NOT_MARKET_EMPTY",
                          "reason": str(e), "cohort_30": "NOT_SCORABLE"}).strip())
        raise SystemExit(2)


if __name__ == "__main__":
    main()
