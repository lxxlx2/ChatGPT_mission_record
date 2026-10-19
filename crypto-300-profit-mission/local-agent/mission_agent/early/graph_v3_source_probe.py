"""One explicit, bounded PancakeSwap BSC V3 subgraph source check.

This only examines indexed coverage and a tiny pool-identity sample. It never
builds a cohort, infers PIT available_at, simulates trades, or paginates.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import urllib.error
import urllib.request

SUBGRAPH_ID = "Hv1GncLY5docZoGtXjo4kwbTvxm3MAhVZqBZE4sUT9eZ"
GATEWAY = f"https://gateway.thegraph.com/api/subgraphs/id/{SUBGRAPH_ID}"
FIRST_BLOCK = 52440287
LAST_BLOCK = 52555482
DAY = "2025-07-01"
QUERY = """query MonsterP0BoundedBscV3 {
  _meta { block { number hash } hasIndexingErrors deployment }
  pools(first: 5, orderBy: createdAtBlockNumber, orderDirection: asc,
        where: {createdAtBlockNumber_gte: "52440287",
                createdAtBlockNumber_lte: "52555482"}) {
    id createdAtBlockNumber createdAtTimestamp feeTier
    token0 { id } token1 { id }
  }
}"""
ADDRESS = re.compile(r"^0x[0-9a-fA-F]{40}$")


class ProbeError(Exception):
    pass


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def validate_body(raw):
    try:
        body = json.loads(raw)
    except (ValueError, UnicodeDecodeError) as exc:
        raise ProbeError("GRAPH_INVALID_JSON") from exc
    if not isinstance(body, dict) or body.get("errors"):
        raise ProbeError("GRAPH_ERRORS_OR_NON_OBJECT")
    data = body.get("data")
    if not isinstance(data, dict):
        raise ProbeError("GRAPH_DATA_MISSING")
    meta = data.get("_meta")
    if not isinstance(meta, dict) or not isinstance(meta.get("block"), dict):
        raise ProbeError("GRAPH_META_MISSING")
    number = meta["block"].get("number")
    if type(number) is not int or number < 0:
        raise ProbeError("GRAPH_META_BAD_BLOCK")
    if meta.get("hasIndexingErrors") is not False:
        raise ProbeError("GRAPH_INDEX_ERRORS_OR_UNKNOWN")
    pools = data.get("pools")
    if not isinstance(pools, list) or len(pools) > 5:
        raise ProbeError("GRAPH_POOL_SAMPLE_INVALID")
    seen = set()
    previous = FIRST_BLOCK
    samples = []
    for pool in pools:
        if not isinstance(pool, dict):
            raise ProbeError("GRAPH_POOL_MALFORMED")
        addr = pool.get("id")
        t0 = pool.get("token0")
        t1 = pool.get("token1")
        try:
            block = int(pool.get("createdAtBlockNumber"))
            timestamp = int(pool.get("createdAtTimestamp"))
            fee = int(pool.get("feeTier"))
        except (ValueError, TypeError):
            raise ProbeError("GRAPH_POOL_BAD_NUMERIC_FIELD") from None
        if (not isinstance(addr, str) or not ADDRESS.fullmatch(addr)
                or not isinstance(t0, dict) or not isinstance(t1, dict)
                or not isinstance(t0.get("id"), str) or not ADDRESS.fullmatch(t0["id"])
                or not isinstance(t1.get("id"), str) or not ADDRESS.fullmatch(t1["id"])
                or not FIRST_BLOCK <= block <= LAST_BLOCK or block < previous
                or not 0 < fee < 1000000 or not 0 < timestamp):
            raise ProbeError("GRAPH_POOL_IDENTITY_OR_BOUNDARY_INVALID")
        lower = addr.lower()
        if lower in seen:
            raise ProbeError("GRAPH_DUPLICATE_POOL")
        seen.add(lower)
        previous = block
        samples.append({"pool": lower, "created_block": block,
                        "created_timestamp": timestamp, "fee_tier": fee,
                        "token0": t0["id"].lower(), "token1": t1["id"].lower()})
    return number, samples


def probe_once(api_key, out_dir, *, opener=urllib.request.urlopen):
    if not isinstance(api_key, str) or not api_key.strip():
        raise ProbeError("GRAPH_API_KEY_REQUIRED")
    if "\n" in api_key or "\r" in api_key:
        raise ProbeError("GRAPH_API_KEY_INVALID")
    if not isinstance(out_dir, Path):
        out_dir = Path(out_dir)
    payload = json.dumps({"query": QUERY}, separators=(",", ":")).encode("utf-8")
    request = urllib.request.Request(
        GATEWAY, data=payload, method="POST",
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + api_key},
    )
    try:
        with opener(request, timeout=20) as response:
            raw = response.read(1048577)
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
        # Do not print provider body, exception URLs, headers, or credentials.
        raise ProbeError("GRAPH_NETWORK_OR_AUTH_FAILURE") from None
    if len(raw) > 1048576:
        raise ProbeError("GRAPH_RESPONSE_TOO_LARGE")
    tip, pools = validate_body(raw)
    result = {
        "status": "CANDIDATE_SAMPLE_ONLY_NOT_SOURCE_PASS" if tip >= LAST_BLOCK and pools
                  else "HISTORICAL_V3_COVERAGE_UNVERIFIED",
        "source_kind": "THIRD_PARTY_INDEX",
        "subgraph_id": SUBGRAPH_ID,
        "query_day_utc": DAY,
        "factory_day_first_block": FIRST_BLOCK,
        "factory_day_last_block": LAST_BLOCK,
        "indexed_tip": tip,
        "sample_size": len(pools),
        "sample": pools,
        "raw_response_sha256": sha256(raw),
        "query_sha256": sha256(payload),
        "ingested_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "limitations": ["SUBGRAPH_DEPLOYED_SCHEMA_UNCONFIRMED_BEFORE_SUCCESSFUL_QUERY",
                        "NO_CONTIGUOUS_OR_COMPLETE_DENOMINATOR_PROOF",
                        "NO_CHAIN_RECEIPT_CROSSCHECK",
                        "NO_CONTEMPORANEOUS_PUBLIC_AVAILABLE_AT",
                        "NO_V2_COVERAGE_OR_TRADE_EXECUTION_PROOF"],
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    body_path = out_dir / ("bsc_v3_graph_single_response_" + sha256(raw) + ".json")
    report_path = out_dir / ("bsc_v3_graph_single_result_" + sha256(raw) + ".json")
    for path, data in [(body_path, raw),
                       (report_path, (json.dumps(result, indent=2, sort_keys=True) + "\n").encode())]:
        with path.open("xb") as f:
            f.write(data)
    return result


def main():
    parser = argparse.ArgumentParser(description="Manual one-query The Graph BSC V3 source gate")
    parser.add_argument("--live-one-query", action="store_true", required=True)
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args()
    try:
        result = probe_once(os.getenv("GRAPH_API_KEY"), Path(args.out_dir))
    except ProbeError as exc:
        parser.exit(2, str(exc) + "\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
