#!/usr/bin/env python3
"""BSC JSON-RPC response parsing only, strictly offline; never performs requests.

All inputs are saved JSON-RPC envelopes. Nothing here certifies public first-seen,
E2 causal swaps, E3, live quotes, finalized receipts or paper PnL.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

SCHEMA = "bsc-f0-rpc-fixture-adapter-v1"
TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
HEX = re.compile(r"^0x[0-9a-fA-F]+$")


def need(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError(reason)


def hexnum(value: str) -> int:
    need(isinstance(value, str) and HEX.fullmatch(value) is not None, "INVALID_HEX_QUANTITY")
    return int(value, 16)


def hexb(value: str, size: int) -> str:
    need(isinstance(value, str) and len(value) == size * 2 + 2 and HEX.fullmatch(value) is not None,
         f"INVALID_HEX_{size}_BYTES")
    return value.lower()


def address(value: str) -> str:
    return hexb(value, 20)


def digest(item: object) -> str:
    return hashlib.sha256(json.dumps(item, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=False).encode()).hexdigest()


def envelope(row: dict) -> object:
    need(isinstance(row, dict) and row.get("jsonrpc") == "2.0" and "id" in row,
         "INVALID_JSONRPC_ENVELOPE")
    need("error" not in row or row["error"] is None, "RPC_ERROR")
    need("result" in row, "MISSING_RPC_RESULT")
    return row["result"]


def block_candidates(rpc: dict, watched: set[str], routers: set[str]) -> dict:
    """Enumerate from full block objects; this is NOT a free/public stream claim."""
    block = envelope(rpc)
    need(isinstance(block, dict), "MISSING_BLOCK")
    height, bhash = hexnum(block["number"]), hexb(block["hash"], 32)
    txs = block.get("transactions")
    need(isinstance(txs, list), "MISSING_FULL_TRANSACTIONS")
    watching = {address(w) for w in watched}
    router_set = {address(r) for r in routers}
    observed = []
    seen = set()
    for row in txs:
        need(isinstance(row, dict), "HASH_ONLY_BLOCK_NOT_SUPPORTED")
        txhash = hexb(row["hash"], 32)
        wallet = address(row["from"])
        to = None if row.get("to") is None else address(row["to"])
        need(txhash not in seen, "DUPLICATE_TRANSACTION_IN_BLOCK")
        seen.add(txhash)
        need(hexnum(row.get("blockNumber", block["number"])) == height,
             "TX_BLOCK_NUMBER_MISMATCH")
        need(hexb(row.get("blockHash", bhash), 32) == bhash, "TX_BLOCK_HASH_MISMATCH")
        group = "WATCHLIST" if wallet in watching else "CONTROL_CANDIDATE"
        if group == "WATCHLIST" or to in router_set:
            observed.append({"wallet": wallet, "tx_hash": txhash, "to": to,
                             "value_wei": str(hexnum(row["value"])), "group": group,
                             "router_eligible": to in router_set,
                             "block_number": height, "block_hash": bhash,
                             "direction": "UNKNOWN", "ca": None,
                             "actionable_time": "UNRESOLVED",
                             "evidence": "TX_OBJECT_ONLY_NO_TRADE_ATTESTATION"})
    return {"mode": "OFFLINE_RPC_FIXTURE_ONLY", "source_method": "eth_getBlockByNumber",
            "block_number": height, "block_hash": bhash,
            "full_block_tx_count": len(txs), "candidates": observed,
            "raw_rpc_sha256": digest(rpc), "e3_actual_count": 0}


def transfer_log(log: dict) -> dict | None:
    topics = log.get("topics")
    if not isinstance(topics, list) or not topics:
        return None
    if not isinstance(topics[0], str) or topics[0].lower() != TRANSFER_TOPIC:
        return None
    need(len(topics) == 3, "MALFORMED_TRANSFER_TOPICS")
    t0, t1 = hexb(topics[1], 32), hexb(topics[2], 32)
    need(t0[2:26] == "0" * 24 and t1[2:26] == "0" * 24, "NON_ADDRESS_TOPIC")
    raw = hexb(log["data"], 32)
    return {"token_ca": address(log["address"]),
            "from": address("0x" + t0[-40:]), "to": address("0x" + t1[-40:]),
            "amount_raw": str(int(raw, 16)),
            "log_index": hexnum(log["logIndex"])}


def receipt_observation(rpc: dict, tx: dict, tip_number: int,
                        quote_assets: set[str], routers: set[str]) -> dict:
    """Preliminary BUY/SELL flow hints, never causal E2; no finalized decision."""
    receipt = envelope(rpc)
    need(isinstance(receipt, dict), "MISSING_RECEIPT")
    wallet, txhash = address(tx["wallet"]), hexb(tx["tx_hash"], 32)
    bhash, number = hexb(receipt["blockHash"], 32), hexnum(receipt["blockNumber"])
    need(hexb(receipt["transactionHash"], 32) == txhash, "RECEIPT_TX_MISMATCH")
    need(bhash == hexb(tx["block_hash"], 32) and number == tx["block_number"],
         "RECEIPT_BLOCK_IDENTITY_MISMATCH_REORG_OR_BAD_INPUT")
    need(isinstance(tip_number, int) and tip_number >= number, "INVALID_TIP")
    status = hexnum(receipt["status"])
    need(status in (0, 1), "INVALID_RECEIPT_STATUS")
    logs = receipt.get("logs")
    need(isinstance(logs, list), "MISSING_RECEIPT_LOGS")
    transfers = [x for x in (transfer_log(v) for v in logs) if x is not None]
    indexes = [r["log_index"] for r in transfers]
    need(len(indexes) == len(set(indexes)), "DUPLICATE_LOG_INDEX")
    quote_set = {address(x) for x in quote_assets}
    router_set = {address(x) for x in routers}
    quote_paid = [r for r in transfers if r["token_ca"] in quote_set and r["from"] == wallet]
    quote_received = [r for r in transfers if r["token_ca"] in quote_set and r["to"] == wallet]
    nonquote = [r for r in transfers if r["token_ca"] not in quote_set]
    token_in = [r for r in nonquote if r["to"] == wallet]
    token_out = [r for r in nonquote if r["from"] == wallet]
    eligible = tx.get("router_eligible") is True and tx.get("to") in router_set
    if status != 1 or not eligible:
        side, ca, reason = "UNKNOWN", None, "RECEIPT_FAILED_OR_ROUTER_NOT_ALLOWED"
    elif len({x["token_ca"] for x in token_in}) == 1 and quote_paid and not token_out:
        side, ca, reason = "BUY_CANDIDATE", token_in[0]["token_ca"], "UNVERIFIED_SWAP_ROUTE"
    elif len({x["token_ca"] for x in token_out}) == 1 and quote_received and not token_in:
        side, ca, reason = "SELL_CANDIDATE", token_out[0]["token_ca"], "UNVERIFIED_SWAP_ROUTE"
    else:
        side, ca, reason = "UNKNOWN", None, "QUOTE_OR_TOKEN_PATH_UNRESOLVED"
    return {"mode": "OFFLINE_RPC_FIXTURE_ONLY", "tx_hash": txhash,
            "wallet": wallet, "side_hint": side, "ca_hint": ca,
            "reason": reason, "receipt_success": status == 1,
            "confirmations_seen": tip_number - number + 1,
            "finality": "UNRESOLVED_F1_POLICY", "E2_attested": False,
            "transfers": transfers, "raw_rpc_sha256": digest(rpc),
            "e3_actual_count": 0}


def decode_get_amounts_out(rpc: dict, expected_path_length: int) -> dict:
    """Decode ABI uint256[] returned by Router getAmountsOut (saved eth_call)."""
    try:
        data = envelope(rpc)
        need(isinstance(data, str) and data.startswith("0x") and
             len(data[2:]) % 64 == 0 and all(ch in "0123456789abcdefABCDEF" for ch in data[2:]),
             "INVALID_ABI_HEX")
        words = [int(data[i:i + 64], 16) for i in range(2, len(data), 64)]
        need(len(words) >= 4 and words[0] == 32, "INVALID_ABI_OFFSET")
        count = words[1]
        need(isinstance(expected_path_length, int) and 2 <= expected_path_length <= 8,
             "INVALID_EXPECTED_PATH_LENGTH")
        need(count == expected_path_length and len(words) == count + 2,
             "INVALID_ABI_LENGTH")
        need(all(v > 0 for v in words[2:]), "NONPOSITIVE_QUOTE_AMOUNT")
        return {"mode": "OFFLINE_RPC_FIXTURE_ONLY", "status": "SIMULATED_ARCHIVE_QUOTE",
                "amount_out_raw": str(words[-1]), "path_amounts_raw": [str(v) for v in words[2:]],
                "raw_rpc_sha256": digest(rpc), "quoted_actual_count": 0}
    except (ValueError, TypeError, KeyError) as exc:
        return {"mode": "OFFLINE_RPC_FIXTURE_ONLY", "status": "NO_QUOTE",
                "failure_reason": str(exc), "raw_rpc_sha256": digest(rpc),
                "quoted_actual_count": 0}


def main() -> None:
    parser = argparse.ArgumentParser(description="OFFLINE ONLY: parse saved JSON-RPC fixtures")
    parser.add_argument("--fixture", required=True, type=Path)
    args = parser.parse_args()
    data = json.loads(args.fixture.read_text(encoding="utf-8"))
    need(data.get("mode") == "OFFLINE_RPC_FIXTURE_ONLY" and data.get("trial") is True,
         "LIVE_OR_UNMARKED_FIXTURE_FORBIDDEN")
    txs = block_candidates(data["block"], set(data["watchlist"]), set(data["routers"]))
    row = txs["candidates"][0]
    receipt = receipt_observation(data["receipt"], row, data["tip_number"],
                                  set(data["quote_assets"]), set(data["routers"]))
    quote = decode_get_amounts_out(data["quote"], data["path_length"])
    print(json.dumps({"schema": SCHEMA, "trial": True, "block": txs,
                      "receipt": receipt, "quote": quote, "actual_rpc_calls": 0,
                      "e3_actual_count": 0, "quoted_actual_count": 0,
                      "paper_profit_labels": 0}, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()