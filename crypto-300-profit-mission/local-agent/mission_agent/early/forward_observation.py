"""Manual, bounded, read-only BSC V2 Factory forward clock evidence pilot.

Two snapshots in one foreground invocation. Never a daemon, trading bot,
complete BSC census, profitable-entry claim, or historical PIT retrofit.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import time

CHAIN = 56
FACTORY = "0xca143ce32fe78f1f7019d7d551a6402fc5350c73"
COUNT_SELECTOR = "0x574f2ba3"  # allPairsLength()
PAIRS_SELECTOR = "0x1e3dd18b"  # allPairs(uint256)
TOKEN0_SELECTOR = "0x0dfe1681"  # token0()
TOKEN1_SELECTOR = "0xd21220a7"  # token1()
MAX_NEW_PAIRS = 3
MAX_CALLS = 20
HEX = re.compile(r"^0x[0-9a-fA-F]+$")
ADDRESS = re.compile(r"^0x[0-9a-fA-F]{40}$")
HASH = re.compile(r"^0x[0-9a-fA-F]{64}$")


class ForwardProbeError(ValueError):
    pass


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
    directory.mkdir(parents=True, exist_ok=False)
    calls = []

    def ask(method, params):
        if method not in ("eth_chainId", "eth_blockNumber", "eth_getBlockByNumber", "eth_call"):
            raise ForwardProbeError("DISALLOWED_RPC_METHOD")
        if len(calls) >= MAX_CALLS:
            raise ForwardProbeError("RPC_CALL_LIMIT")
        start = clock()
        m_start = monotonic_ns()
        value, raw = rpc.request(method, params)
        m_end = monotonic_ns()
        recv = clock()
        if recv < start or m_end < m_start:
            raise ForwardProbeError("LOCAL_CLOCK_REVERSED")
        if type(raw) is not bytes or len(raw) > 262144:
            raise ForwardProbeError("ORIGINAL_RPC_BYTES_INVALID")
        try:
            envelope = json.loads(raw)
        except (ValueError, UnicodeDecodeError):
            raise ForwardProbeError("ORIGINAL_RPC_JSON_INVALID") from None
        if not isinstance(envelope, dict) or envelope.get("result") != value or envelope.get("error"):
            raise ForwardProbeError("ORIGINAL_RPC_RESULT_NOT_VERIFIED")
        file = f"rpc-{len(calls)+1:02d}.json"
        with (directory / file).open("xb") as fd:
            fd.write(raw)
        row = {"ordinal": len(calls)+1, "method": method, "params": params,
               "raw_file": file, "raw_sha256": hashlib.sha256(raw).hexdigest(),
               "raw_bytes": len(raw), "call_invoked_at_utc": iso(start),
               "local_response_completed_at_utc": iso(recv),
               "elapsed_monotonic_ns": m_end - m_start}
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
            header_check_raw, _ = ask("eth_getBlockByNumber", [hex(height), False])
            if _validate_header(header_check_raw, height) != header:
                raise ForwardProbeError("BLOCK_REORG_DURING_OBSERVATION")
            observations.append({"block": header, "all_pairs_length": count,
                "count_observed_at_utc": count_receipt["local_response_completed_at_utc"]})
        a, b = observations
        if b["block"]["number"] < a["block"]["number"]:
            raise ForwardProbeError("HEAD_MOVED_BACKWARDS")
        if b["all_pairs_length"] < a["all_pairs_length"]:
            raise ForwardProbeError("FACTORY_COUNTER_DECREASED")
        if (a["block"]["number"] == b["block"]["number"]
                and (a["all_pairs_length"] != b["all_pairs_length"]
                     or a["block"]["hash"] != b["block"]["hash"])):
            raise ForwardProbeError("SAME_HEIGHT_INCONSISTENT_STATE")
        if (b["block"]["number"] == a["block"]["number"] + 1
                and b["block"]["parent_hash"] != a["block"]["hash"]):
            raise ForwardProbeError("NONCONTIGUOUS_PARENT_HASH")
        # A same-epoch block that got reorganized after our first read cannot
        # be evidence of a verified contiguous interval.
        anchor_raw, _ = ask("eth_getBlockByNumber", [hex(a["block"]["number"]), False])
        if _validate_header(anchor_raw, a["block"]["number"]) != a["block"]:
            raise ForwardProbeError("FIRST_ANCHOR_CHANGED")
        delta = b["all_pairs_length"] - a["all_pairs_length"]
        new_pairs = []
        for index in range(a["all_pairs_length"], a["all_pairs_length"] + min(delta, MAX_NEW_PAIRS)):
            word = "0x" + format(index, "064x")
            pair_raw, pair_time = call(FACTORY, PAIRS_SELECTOR + word[2:], b["block"]["number"])
            pair = word_address(pair_raw)
            token0_raw, token0_time = call(pair, TOKEN0_SELECTOR, b["block"]["number"])
            token1_raw, token1_time = call(pair, TOKEN1_SELECTOR, b["block"]["number"])
            token0, token1 = word_address(token0_raw), word_address(token1_raw)
            if token0 == token1:
                raise ForwardProbeError("POOL_IDENTICAL_TOKEN_ADDRESSES")
            new_pairs.append({"factory_index": index, "pool": pair,
                "token0": token0, "token1": token1,
                "last_identity_response_completed_at_utc": token1_time["local_response_completed_at_utc"],
                "pair_response_completed_at_utc": pair_time["local_response_completed_at_utc"],
                "token0_response_completed_at_utc": token0_time["local_response_completed_at_utc"]})
        # Detect late reorg or changed block identity after reading pool state.
        final_header_raw, _ = ask("eth_getBlockByNumber", [hex(b["block"]["number"]), False])
        if _validate_header(final_header_raw, b["block"]["number"]) != b["block"]:
            raise ForwardProbeError("SECOND_ANCHOR_CHANGED")
        manifest = {"schema": "MONSTER_FORWARD_BSC_V2_ONE_SHOT_OBSERVER_V1",
            "network_chain_id": CHAIN, "provider_url_sha256_only": rpc.source_sha256,
            "factory": FACTORY, "snapshots": observations,
            "new_factory_pair_index_count": delta, "new_pairs_read": new_pairs,
            "unread_new_pair_count": delta - len(new_pairs),
            "observation_complete_for_two_factory_counts": True,
            "factory_index_identity_coverage": "PARTIAL" if delta > MAX_NEW_PAIRS else "WITHIN_OBSERVED_PAIR_COUNT_DELTA",
            "time_basis": "LOCAL_RESPONSE_COMPLETED_UTC_UPPER_BOUND_NOT_FIRST_PUBLIC_AVAILABLE_AT",
            "provenance_scope": "ONE_PROVIDER_LIVE_READ_NOT_INDEPENDENT_AUTHENTICATION",
            "reorg_finality": "NOT_PROVEN_FINALIZED",
            "trade_execution_or_liquidity": "NOT_TESTED",
            "interval_no_new_pair_is_not_full_market_zero": True,
            "p0_historical_2025_available_at": "UNKNOWN_NOT_RETROACTIVELY_RECONSTRUCTED",
            "p1_gate_passed": False, "trading_authorized": False,
            "rpc_requests": calls}
        with (directory / "manifest.json").open("xb") as fd:
            fd.write((json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode())
        return manifest
    except Exception as exc:
        # Preserve the exact prior raw bytes and mark this run unusable.
        code = str(exc) if isinstance(exc, ForwardProbeError) else type(exc).__name__
        with (directory / "failure.json").open("xb") as fd:
            fd.write((json.dumps({"status": "UNUSABLE_NOT_PIT_EVIDENCE", "reason": code,
                   "completed_rpc_responses": calls}, indent=2, sort_keys=True) + "\n").encode())
        raise


def main():
    parser = argparse.ArgumentParser(description="Monster bounded manual BSC V2 forward-only receipt pilot")
    parser.add_argument("--manual-once", action="store_true")
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--pause-ms", type=int, default=1000)
    args = parser.parse_args()
    if not args.manual_once or not 0 <= args.pause_ms <= 3000:
        parser.error("--manual-once and --pause-ms from 0 to 3000 required")
    from mission_agent.early.fourmeme_index_source_probe import JsonRPC
    rpc = JsonRPC(os.getenv("MONSTER_BSC_ARCHIVE_RPC_URL"), max_requests=MAX_CALLS)
    result = capture(rpc, args.out_dir, pause_seconds=args.pause_ms / 1000)
    print(json.dumps({"status": "READ_ONLY_PILOT_OBSERVED",
        "manifest_path": str(args.out_dir / "manifest.json"),
        "snapshots": len(result["snapshots"]),
        "pair_count_delta": result["new_factory_pair_index_count"],
        "listed_pairs": len(result["new_pairs_read"]),
        "p0_gate": "UNCHANGED", "p1_gate": "BLOCKED"}, sort_keys=True))


if __name__ == "__main__":
    main()
