"""Explicit one-shot, read-only Four.meme July-2025 source enumeration.

No training, signal emission, wallet signing, trades, subscription or scheduling.
Save original JSON-RPC HTTP response bytes losslessly via base64 JSONL locally.
The 538 historical _tokens(index) slots are a scope-limited launchpad pilot,
NOT complete BSC coverage or evidence of contemporaneous public available_at.
"""
import argparse
import base64
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import time
import urllib.error
import urllib.parse
import urllib.request

CHAIN = 56
MANAGER = "0x5c952063c7fc8610ffdb798152d69f0b9550762b"
SELECTOR = "0xed70554d"
CREATE_TOPIC = "0x396d5e902b675b032348d3d2e9517ee8f0c4a926603fbc075d3d282ff00cad20"
PRE_BLOCK = 52440286
FIRST_BLOCK = 52440287
LAST_BLOCK = 52555482
START_INDEX = 247596
END_INDEX_EXCLUSIVE = 248134
ANCHORS = ((START_INDEX, 52440331, "0x1e395d5edb51e7e7c6b1203912d0d0b6f87f4444"),
           (END_INDEX_EXCLUSIVE - 1, 52554568,
            "0xc4be692236dba677f3db2d2cdb38f998d2f54444"))
MAX_REQUESTS = 550
ADDRESS = re.compile(r"^0x[0-9a-f]{40}$")
HEX_WORD = re.compile(r"^0x[0-9a-fA-F]{64}$")


class ProbeError(Exception):
    pass


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def parse_word(value):
    if not isinstance(value, str) or not HEX_WORD.fullmatch(value):
        raise ProbeError("FOURMEME_BAD_ETH_CALL_WORD")
    return "0x" + value[-40:].lower()


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


class JsonRPC:
    """Caller-supplied archive HTTPS RPC; neither log nor persist its URL."""

    def __init__(self, endpoint, *, min_interval=0.25, max_requests=MAX_REQUESTS,
                 opener=None):
        if not isinstance(endpoint, str):
            raise ProbeError("FOURMEME_RPC_ENV_REQUIRED")
        parsed = urllib.parse.urlsplit(endpoint)
        if (parsed.scheme != "https" or not parsed.hostname or
                parsed.username or parsed.password or parsed.fragment or
                "\r" in endpoint or "\n" in endpoint):
            raise ProbeError("FOURMEME_RPC_MUST_BE_HTTPS")
        if not 0 <= min_interval <= 10 or max_requests > MAX_REQUESTS:
            raise ProbeError("FOURMEME_UNSAFE_REQUEST_BUDGET")
        self.url = endpoint
        self.source_sha256 = sha256(endpoint.encode("utf-8"))
        self.secret_marker = parsed.path.rsplit("/", 1)[-1].encode()
        if len(self.secret_marker) < 12:
            self.secret_marker = b""
        self.opener = opener or urllib.request.build_opener(NoRedirect())
        self.max_requests = max_requests
        self.min_interval = min_interval
        self.calls = 0
        self.last = 0.0

    def request(self, method, params):
        if self.calls >= self.max_requests:
            raise ProbeError("FOURMEME_REQUEST_BUDGET_EXHAUSTED")
        remain = self.min_interval - (time.monotonic() - self.last)
        if remain > 0:
            time.sleep(remain)
        self.last = time.monotonic()
        self.calls += 1
        payload = json.dumps({"jsonrpc": "2.0", "id": self.calls,
                              "method": method, "params": params},
                             separators=(",", ":")).encode()
        req = urllib.request.Request(self.url, data=payload, method="POST",
                                     headers={"Content-Type": "application/json",
                                              "User-Agent": "MonsterP0FourmemeReadonly/1"})
        try:
            with self.opener.open(req, timeout=20) as response:
                raw = response.read(262145)
        except urllib.error.HTTPError as exc:
            code = int(exc.code)
            exc.close()
            raise ProbeError("FOURMEME_RPC_HTTP_" + str(code)) from None
        except (urllib.error.URLError, TimeoutError, OSError):
            raise ProbeError("FOURMEME_RPC_NETWORK_UNAVAILABLE") from None
        if len(raw) > 262144 or (self.secret_marker and self.secret_marker in raw):
            raise ProbeError("FOURMEME_RESPONSE_OVERSIZE_OR_SECRET_ECHO")
        try:
            parsed = json.loads(raw)
        except (ValueError, UnicodeDecodeError):
            raise ProbeError("FOURMEME_INVALID_RPC_JSON") from None
        if (not isinstance(parsed, dict) or "result" not in parsed or
                parsed.get("error") or parsed.get("id") != self.calls):
            raise ProbeError("FOURMEME_RPC_MISSING_RESULT_OR_ERROR")
        return parsed["result"], raw


def collect(out_dir, rpc):
    """A fresh directory only. Incomplete archives stay incomplete, never PASS."""
    out_dir = Path(out_dir)
    if out_dir.exists() and any(out_dir.iterdir()):
        raise ProbeError("FOURMEME_OUTPUT_DIRECTORY_NOT_EMPTY")
    out_dir.mkdir(parents=True, exist_ok=True)
    raw_path = out_dir / "raw_rpc_responses_base64.jsonl"
    report_path = out_dir / "manifest.json"

    with raw_path.open("xb") as archive:
        response_count = 0

        def request(method, params):
            nonlocal response_count
            result, raw = rpc.request(method, params)
            response_count += 1
            archive.write((json.dumps({
                "sequence": response_count, "method": method,
                "params": params, "original_response_sha256": sha256(raw),
                "raw_http_json_rpc_base64": base64.b64encode(raw).decode("ascii")
            }, separators=(",", ":")) + "\n").encode("utf-8"))
            archive.flush()
            return result

        if request("eth_chainId", []) != "0x38":
            raise ProbeError("FOURMEME_NOT_BNB_MAINNET")

        def token(index, block):
            data = SELECTOR + format(index, "064x")
            value = request("eth_call", [{"to": MANAGER, "data": data}, hex(block)])
            return parse_word(value)

        empty = "0x" + "0" * 40
        boundary = {
            "old_last": token(START_INDEX - 1, PRE_BLOCK),
            "old_first_missing": token(START_INDEX, PRE_BLOCK),
            "new_last_missing_old": token(END_INDEX_EXCLUSIVE - 1, PRE_BLOCK),
            "new_first": token(START_INDEX, LAST_BLOCK),
            "new_last": token(END_INDEX_EXCLUSIVE - 1, LAST_BLOCK),
            "new_after_last": token(END_INDEX_EXCLUSIVE, LAST_BLOCK),
        }
        if (boundary["old_last"] == empty or
                boundary["old_first_missing"] != empty or
                boundary["new_last_missing_old"] != empty or
                boundary["new_first"] != ANCHORS[0][2] or
                boundary["new_last"] != ANCHORS[1][2] or
                boundary["new_after_last"] != empty):
            raise ProbeError("FOURMEME_FROZEN_BOUNDARY_NOT_REPRODUCED")

        tokens = []
        unique = set()
        for index in range(START_INDEX, END_INDEX_EXCLUSIVE):
            addr = token(index, LAST_BLOCK)
            if addr == empty:
                raise ProbeError("FOURMEME_HOLE_IN_FROZEN_INDEX_RANGE")
            if not ADDRESS.fullmatch(addr) or addr in unique:
                raise ProbeError("FOURMEME_INVALID_OR_DUPLICATE_TOKEN_CA")
            unique.add(addr)
            tokens.append({"index": index, "token_ca": addr})

        for index, block, expected in ANCHORS:
            logs = request("eth_getLogs", [{
                "fromBlock": hex(block), "toBlock": hex(block),
                "address": MANAGER, "topics": [CREATE_TOPIC]
            }])
            if not isinstance(logs, list):
                raise ProbeError("FOURMEME_BAD_TOKENCREATE_LOGS")
            matched = []
            for event in logs:
                if not isinstance(event, dict):
                    raise ProbeError("FOURMEME_MALFORMED_LOG")
                data = event.get("data", "")
                if (event.get("address", "").lower() != MANAGER or
                        event.get("topics", [None])[0] != CREATE_TOPIC or
                        not isinstance(data, str) or not data.startswith("0x") or
                        len(data) < 2 + 128):
                    raise ProbeError("FOURMEME_INVALID_FACTORY_EVENT")
                event_ca = "0x" + data[2 + 64 + 24:2 + 128].lower()
                if event_ca == expected:
                    matched.append(event)
            if len(matched) != 1 or tokens[index - START_INDEX]["token_ca"] != expected:
                raise ProbeError("FOURMEME_ANCHOR_NOT_UNIQUE_OR_MISMATCH")
            event = matched[0]
            if event.get("blockNumber") != hex(block) or event.get("removed"):
                raise ProbeError("FOURMEME_LOG_BLOCK_OR_REORG_INVALID")
            txhash = event.get("transactionHash")
            if not isinstance(txhash, str) or not re.fullmatch(r"0x[0-9a-fA-F]{64}", txhash):
                raise ProbeError("FOURMEME_LOG_MISSING_TX")
            receipt = request("eth_getTransactionReceipt", [txhash])
            if not isinstance(receipt, dict) or receipt.get("status") != "0x1":
                raise ProbeError("FOURMEME_ANCHOR_RECEIPT_NOT_SUCCESS")

    manifest = {
        "schema": "MONSTER_P0_FOURMEME_FROZEN_DAY_ONESHOT_LOCAL_RAW_ARCHIVE_V1",
        "status": "538_UNIQUE_INDEXED_ADDRESSES_CROSSCHECKED_TWO_CREATION_EVENTS",
        "chain_id": CHAIN, "manager": MANAGER, "date_utc": "2025-07-01",
        "source_uri_sha256": getattr(rpc, "source_sha256", "FAKE_SOURCE"),
        "pre_day_block": PRE_BLOCK, "end_day_block": LAST_BLOCK,
        "range_start": START_INDEX, "range_end_exclusive": END_INDEX_EXCLUSIVE,
        "address_count": len(tokens), "rpc_response_count": response_count,
        "raw_archive_sha256": sha256(raw_path.read_bytes()),
        "raw_archive_bytes": raw_path.stat().st_size,
        "indexed_token_addresses": tokens,
        "observation_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "limitations": [
            "FROZEN_ONE_DAY_ONE_MANAGER_ONLY_NOT_ALL_LAUNCHPADS",
            "INDEX_RANGE_UNIQUENESS_NOT_COMPLETE_LOG_ENUMERATION",
            "NO_2025_CONTEMPORANEOUS_PUBLIC_AVAILABLE_AT",
            "NO_SAME_NOTIONAL_BUY_SELL_OR_MODEL_VALIDATION",
            "NEEDS_INDEPENDENT_CHAIN_SOURCE_CROSSCHECK",
            "RAW_HTTP_RESPONSE_BYTES_SAVED_AS_BASE64_NOT_THE_NETWORK_HEADERS"
        ],
    }
    with report_path.open("xb") as out:
        out.write((json.dumps(manifest, ensure_ascii=False, sort_keys=True,
                              indent=2) + "\n").encode())
    return manifest


def main():
    parser = argparse.ArgumentParser(description="Manual read-only Four.meme frozen-day index audit")
    parser.add_argument("--live-frozen-2025-07-01", action="store_true")
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args()
    if not args.live_frozen_2025_07_01:
        parser.error("explicit --live-frozen-2025-07-01 is required")
    try:
        rpc = JsonRPC(os.getenv("MONSTER_BSC_ARCHIVE_RPC_URL"))
        result = collect(args.out_dir, rpc)
    except ProbeError as exc:
        parser.exit(2, str(exc) + "\n")
    print(json.dumps({k: v for k, v in result.items()
                      if k != "indexed_token_addresses"}, sort_keys=True))


if __name__ == "__main__":
    main()
