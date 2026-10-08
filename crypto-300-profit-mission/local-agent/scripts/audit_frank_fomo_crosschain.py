#!/usr/bin/env python3
"""Read-only FOMO person-wide Solana/Robinhood Chain evidence audit.

Independent of live Frank Ledger, follow policy, notifications and wallet signing.
Requires complete RPC windows to claim a chain was scanned. Unverified third-party
Frank address attribution makes ALL results OBSERVE_ONLY.
Usage: python -B scripts/audit_frank_fomo_crosschain.py --hours 6
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error
from collections import Counter
from pathlib import Path

from mission_agent.meme.fomo_crosschain import (
    FOMO_EIP7702_CODE, RH_CANDIDATE_WALLET, RH_CHAIN_ID, RH_ENTRYPOINT,
    SOL_CANDIDATE_WALLET, SOL_CASH_WALLET, TOPIC_TRANSFER, TOPIC_USEROP,
    robinhood_buy_fills, robinhood_user_operations, pair_orders, solana_events,
)

DEFAULT_RH_RPC = "https://rpc.mainnet.chain.robinhood.com"
MAX_SOL_PAGES = 15
MAX_SOL_TRANSACTIONS_PER_WALLET = 1000
MAX_EVM_LOGS = 3000
MAX_EVM_REQUESTS = 600


class IncompleteWindow(RuntimeError):
    pass


class RPC:
    def __init__(self, url: str):
        if not isinstance(url, str) or not url.startswith("https://"):
            raise ValueError("HTTPS_RPC_REQUIRED")
        self.url = url
        self.calls = 0

    def call(self, method: str, params: list):
        self.calls += 1
        body = json.dumps({"jsonrpc":"2.0","id":self.calls,"method":method,"params":params}).encode()
        request = urllib.request.Request(
            self.url, data=body, method="POST",
            headers={"Content-Type":"application/json","Accept":"application/json"},
        )
        with urllib.request.urlopen(request, timeout=18) as response:
            reply = json.load(response)
        if not isinstance(reply, dict) or reply.get("error") or "result" not in reply:
            raise IncompleteWindow("RPC_RESPONSE_INCOMPLETE:" + method)
        return reply["result"]


def configured_solana_endpoints(path: Path) -> list[str]:
    if not path.is_file() or path.stat().st_mode & 0o077:
        raise IncompleteWindow("RPC_CONFIG_MISSING_OR_PERMISSIONS")
    text = path.read_text().strip()
    endpoints = [x.strip() for x in text.split(",") if x.strip()]
    if not endpoints or len(endpoints) > 10 or any(not x.startswith("https://") for x in endpoints):
        raise IncompleteWindow("RPC_CONFIG_INVALID")
    return endpoints


def solana_signatures(rpc: RPC, wallet: str, cutoff: int, until: int) -> list[dict]:
    results = []
    before = None
    seen = set()
    for _ in range(MAX_SOL_PAGES):
        options = {"limit":1000,"commitment":"finalized"}
        if before:
            options["before"] = before
        page = rpc.call("getSignaturesForAddress", [wallet, options])
        if not isinstance(page, list):
            raise IncompleteWindow("SOL_SIGNATURES_NOT_ARRAY")
        if not page:
            return results
        for sig in page:
            if not isinstance(sig, dict) or not sig.get("signature") or sig.get("blockTime") is None:
                raise IncompleteWindow("SOL_TIMESTAMP_MISSING")
            if sig["signature"] in seen:
                continue
            seen.add(sig["signature"])
            stamp = int(sig["blockTime"])
            if stamp < cutoff:
                return results
            if stamp <= until:
                results.append(sig)
            if len(results) > MAX_SOL_TRANSACTIONS_PER_WALLET:
                raise IncompleteWindow("SOL_WALLET_TRANSACTION_BUDGET_EXCEEDED")
        if len(page) < 1000:
            return results
        next_before = page[-1]["signature"]
        if before == next_before:
            raise IncompleteWindow("SOL_RPC_CURSOR_STALLED")
        before = next_before
    raise IncompleteWindow("SOL_MAX_PAGES_REACHED")


def scan_solana(rpc: RPC, wallet: str, cutoff: int, until: int) -> dict:
    signatures = solana_signatures(rpc, wallet, cutoff, until)
    rows = []
    for item in signatures:
        sig = item["signature"]
        tx = rpc.call("getTransaction", [sig, {
            "encoding":"jsonParsed", "commitment":"finalized", "maxSupportedTransactionVersion":0,
        }])
        if not tx:
            raise IncompleteWindow("SOL_FINALIZED_TRANSACTION_UNAVAILABLE")
        if tx.get("slot") != item.get("slot"):
            raise IncompleteWindow("SOL_SIGNATURE_SLOT_MISMATCH")
        rows.extend(solana_events(sig, tx, wallet))
    return {
        "chain":"SOL", "wallet":wallet, "status":"COMPLETE",
        "signatures_scanned":len(signatures), "rpc_calls":rpc.calls,
        "legs":rows,
    }


def rh_block_number(rpc: RPC, cutoff: int, until: int) -> tuple[int,int]:
    newest = int(rpc.call("eth_blockNumber", []), 16)
    if newest < 1:
        raise IncompleteWindow("RH_HEIGHT_INVALID")
    last = rpc.call("eth_getBlockByNumber", [hex(newest),False])
    if not last or int(last["timestamp"],16) < cutoff:
        raise IncompleteWindow("RH_HEAD_OLDER_THAN_WINDOW")
    def first_block_at_or_after(timestamp: int) -> int:
        lo,hi = 0,newest
        while lo < hi:
            mid=(lo+hi)//2
            block=rpc.call("eth_getBlockByNumber",[hex(mid),False])
            if not block or block.get("timestamp") is None:
                raise IncompleteWindow("RH_BLOCK_TIMESTAMP_MISSING")
            if int(block["timestamp"],16)<timestamp:
                lo=mid+1
            else:
                hi=mid
        return lo
    first = first_block_at_or_after(cutoff)
    # Upper bound is inclusive; exclude the first block beyond the window.
    last_block = first_block_at_or_after(until+1)-1 if int(last["timestamp"],16)>until else newest
    return first, max(first-1, last_block)


def rh_getlogs(rpc: RPC, first: int, last: int, topics: list) -> list[dict]:
    # Public RPC providers vary in permissible eth_getLogs range; subdivide as
    # needed, but NEVER call a partial window COMPLETE.
    stack=[(first,last)]
    result=[]
    calls=0
    while stack:
        a,b=stack.pop()
        calls+=1
        if calls>MAX_EVM_REQUESTS:
            raise IncompleteWindow("RH_RPC_REQUEST_BUDGET_EXCEEDED")
        try:
            logs=rpc.call("eth_getLogs",[{"fromBlock":hex(a),"toBlock":hex(b),"topics":topics}])
            if not isinstance(logs,list):
                raise ValueError("RH_LOGS_NOT_ARRAY")
        except (ValueError, urllib.error.URLError, IncompleteWindow, TimeoutError):
            if a>=b:
                raise IncompleteWindow("RH_LOGS_UNAVAILABLE")
            mid=(a+b)//2
            stack.extend(((mid+1,b),(a,mid)))
            continue
        result+=logs
        if len(result)>MAX_EVM_LOGS:
            raise IncompleteWindow("RH_LOG_RESULT_BUDGET_EXCEEDED")
    unique={}
    for log in result:
        key=(log.get("transactionHash"),log.get("logIndex"))
        unique[key]=log
    return sorted(unique.values(),key=lambda log: (int(log["blockNumber"],16),int(log["logIndex"],16)))


def pad_evm_wallet(wallet: str) -> str:
    return "0x" + "0"*24 + wallet.removeprefix("0x").lower()


def scan_robinhood(rpc: RPC, wallet: str, cutoff: int, until: int) -> dict:
    chain=int(rpc.call("eth_chainId",[]),16)
    if chain!=RH_CHAIN_ID:
        raise IncompleteWindow("RH_CHAIN_ID_MISMATCH")
    code=(rpc.call("eth_getCode",[wallet,"latest"]) or "").lower()
    if code!=FOMO_EIP7702_CODE:
        raise IncompleteWindow("RH_CANDIDATE_NOT_EIP7702_FOMO_ACCOUNT")
    first,last=rh_block_number(rpc,cutoff,until)
    if last < first:
        return {"chain":"RH", "wallet":wallet, "status":"COMPLETE",
                "first_block":first,"last_block":last,"userop_tx_count":0,
                "inbound_transfer_tx_count":0,"eip7702_delegation_confirmed":True,
                "rpc_calls":rpc.calls,"legs":[]}
    padded=pad_evm_wallet(wallet)
    ops=rh_getlogs(rpc,first,last,[TOPIC_USEROP,None,padded])
    # Receipts must contain ALL sibling UserOps for correct per-operation scope.
    inbound=rh_getlogs(rpc,first,last,[TOPIC_TRANSFER,None,padded])
    op_hashes={log["transactionHash"] for log in ops}
    transfer_hashes={log["transactionHash"] for log in inbound}
    found=[]
    for hash_value in sorted(op_hashes|transfer_hashes):
        receipt=rpc.call("eth_getTransactionReceipt",[hash_value])
        if not receipt or receipt.get("status")!="0x1":
            continue
        if hash_value in op_hashes:
            found+=robinhood_user_operations(receipt,wallet)
        if hash_value in transfer_hashes:
            tx=rpc.call("eth_getTransactionByHash",[hash_value])
            if tx:
                found+=robinhood_buy_fills(tx,receipt,wallet)
    return {
        "chain":"RH", "wallet":wallet, "status":"COMPLETE",
        "first_block":first,"last_block":last,"userop_tx_count":len(op_hashes),
        "inbound_transfer_tx_count":len(transfer_hashes),
        "eip7702_delegation_confirmed":True,"rpc_calls":rpc.calls,"legs":found,
    }


def audit(hours: int, solana_urls: list[str], rh_url: str, audited_at: int | None = None) -> dict:
    until=int(time.time()) if audited_at is None else int(audited_at)
    if until > int(time.time()) or until <= hours*3600:
        raise ValueError("INVALID_AUDIT_END_TIME")
    since=until-hours*3600
    report={
        "status":"PARTIAL", "window_hours":hours, "cutoff_epoch":since,
        "audited_at_epoch":until,"person":"frankdegods",
        "identity_attribution":"THIRD_PARTY_UNVERIFIED",
        "source_identity":"hoodwatch.dev/trader/frankdegods;hoodwatch.dev/trader/A5SEXYJY4jTEi6sjMLfZs5KAP8SVFvLDPDV67GgSSZSk",
        "promotion_to_follow_signals":"FORBIDDEN","gmail_sent":0,
        "production_db_writes":0,"automatic_trading":"NO_GO",
        "chains":[], "counts":{}, "paired":[],
    }
    legs=[]
    for wallet in (SOL_CASH_WALLET,SOL_CANDIDATE_WALLET):
        failures=[]
        for endpoint in solana_urls:
            try:
                value=scan_solana(RPC(endpoint),wallet,since,until)
                break
            except (IncompleteWindow, ValueError, KeyError, TypeError, urllib.error.URLError, TimeoutError) as exc:
                # Never output private RPC URL or credentials.
                failures.append(type(exc).__name__)
        else:
            value={"chain":"SOL","wallet":wallet,"status":"INCOMPLETE",
                   "error":"SOL_RPC_WINDOW_UNAVAILABLE_OR_BUDGET","trials":len(failures),"legs":[]}
        legs+=value.pop("legs")
        report["chains"].append(value)
    try:
        value=scan_robinhood(RPC(rh_url),RH_CANDIDATE_WALLET,since,until)
    except (IncompleteWindow, ValueError, KeyError, TypeError, urllib.error.URLError, TimeoutError):
        value={"chain":"RH","wallet":RH_CANDIDATE_WALLET,"status":"INCOMPLETE",
               "error":"RH_RPC_WINDOW_OR_IDENTITY_UNAVAILABLE","legs":[]}
    legs+=value.pop("legs")
    report["chains"].append(value)
    report["counts"]=dict(Counter(x["kind"] for x in legs))
    report["paired"]=pair_orders(legs)
    report["paired_counts"]=dict(Counter(x["kind"] for x in report["paired"]))
    report["evidence"]=sorted(legs,key=lambda x:(x.get("block_time") or 0,x["tx_id"]))
    if all(x["status"]=="COMPLETE" for x in report["chains"]):
        report["status"]="RPC_WINDOW_COMPLETE_IDENTITY_UNVERIFIED"
    report["interpretation"]="Evidence legs and possible Relay order joins only; no confirmed person attribution, trade PNL, or email eligibility."
    return report


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--hours",type=int,default=6,choices=(1,6,24))
    parser.add_argument("--solana-rpc-file",type=Path,
                        default=Path.home()/"Library/Application Support/FrankMeme/solana_rpc_urls")
    parser.add_argument("--robinhood-rpc",default=os.environ.get("ROBINHOOD_RPC_URL",DEFAULT_RH_RPC))
    parser.add_argument("--output",type=Path,help="Optional research JSON report; never a production DB")
    parser.add_argument("--as-of-epoch",type=int,
                        help="Reproduce a fixed UTC time window; end timestamp inclusive")
    args=parser.parse_args()
    try:
        endpoints=configured_solana_endpoints(args.solana_rpc_file)
        result=audit(args.hours,endpoints,args.robinhood_rpc,args.as_of_epoch)
    except (IncompleteWindow, ValueError):
        print('{"status":"PRECHECK_FAILED","production_db_writes":0,"gmail_sent":0}')
        return 2
    payload=json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True)+"\n"
    if args.output:
        parent=args.output.parent.resolve(strict=True)
        if args.output.exists() or args.output.is_symlink():
            raise SystemExit("OUTPUT_EXISTS_FAIL_CLOSED")
        if "FrankMeme" in str(parent) or "crypto-monitor-frank-only" in str(parent):
            raise SystemExit("OUTPUT_MUST_BE_SEPARATE_FROM_LIVE_RUNTIME")
        args.output.write_text(payload,encoding="utf-8")
        os.chmod(args.output,0o600)
    else:
        print(payload)
    return 0 if result["status"]=="RPC_WINDOW_COMPLETE_IDENTITY_UNVERIFIED" else 3


if __name__=="__main__":
    try:
        raise SystemExit(main())
    except Exception:
        print('{"status":"AUDIT_FAILED","production_db_writes":0,"gmail_sent":0}',file=sys.stderr)
        raise SystemExit(4)
