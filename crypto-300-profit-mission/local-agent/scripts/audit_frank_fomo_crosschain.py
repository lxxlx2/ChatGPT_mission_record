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
import re
import tempfile
import urllib.request
import urllib.error
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from mission_agent.meme.fomo_crosschain import (
    FOMO_EIP7702_CODE, RH_CANDIDATE_WALLET, RH_CHAIN_ID, RH_ENTRYPOINT,
    SOL_CANDIDATE_WALLET, SOL_CASH_WALLET, TOPIC_TRANSFER, TOPIC_USEROP,
    robinhood_buy_fills, robinhood_user_operations, pair_orders, solana_events,
)

DEFAULT_RH_RPCS = ("https://rpc.mainnet.chain.robinhood.com",
                   "https://robinhood-rpc.publicnode.com")
MAX_SOL_PAGES = 15
MAX_SOL_TRANSACTIONS_PER_WALLET = 1000
MAX_EVM_LOGS = 3000
MAX_EVM_REQUESTS = 2000
RPC_MIN_INTERVAL_SECONDS = 0.15
RPC_RETRY_DELAYS_SECONDS = (1.0, 2.0, 4.0)


class IncompleteWindow(RuntimeError):
    pass


class RPC:
    """Read-only JSON RPC with bounded backoff and credential-free diagnostics."""

    def __init__(self, url: str):
        if not isinstance(url, str) or not url.startswith("https://"):
            raise ValueError("HTTPS_RPC_REQUIRED")
        self.url = url
        self.calls = 0
        self.last_method = "NONE"
        self.scan_stage = "INIT"
        self.progress = {}
        self._last_request = 0.0

    def call(self, method: str, params: list):
        self.last_method = method
        body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method,
                           "params": params}).encode()
        request = urllib.request.Request(
            self.url, data=body, method="POST",
            headers={"Content-Type": "application/json", "Accept": "application/json"},
        )
        for attempt in range(len(RPC_RETRY_DELAYS_SECONDS) + 1):
            wait = RPC_MIN_INTERVAL_SECONDS - (time.monotonic() - self._last_request)
            if wait > 0:
                time.sleep(wait)
            self.calls += 1
            self._last_request = time.monotonic()
            try:
                with urllib.request.urlopen(request, timeout=18) as response:
                    reply = json.load(response)
                if not isinstance(reply, dict):
                    raise IncompleteWindow("RPC_NOT_JSON_OBJECT")
                error = reply.get("error")
                if error:
                    code = error.get("code") if isinstance(error, dict) else None
                    tag = "RPC_ERROR_" + str(code) if isinstance(code, int) else "RPC_ERROR_UNKNOWN"
                    # Some providers express rate limiting through JSON-RPC errors.
                    if code in (-32005, -32016) and attempt < len(RPC_RETRY_DELAYS_SECONDS):
                        time.sleep(RPC_RETRY_DELAYS_SECONDS[attempt])
                        continue
                    raise IncompleteWindow(tag)
                if "result" not in reply:
                    raise IncompleteWindow("RPC_RESULT_MISSING")
                return reply["result"]
            except urllib.error.HTTPError as exc:
                if exc.code in (408, 429, 500, 502, 503, 504) and attempt < len(RPC_RETRY_DELAYS_SECONDS):
                    time.sleep(RPC_RETRY_DELAYS_SECONDS[attempt])
                    continue
                raise IncompleteWindow("RPC_HTTP_" + str(exc.code)) from None
            except (TimeoutError, urllib.error.URLError, OSError):
                if attempt < len(RPC_RETRY_DELAYS_SECONDS):
                    time.sleep(RPC_RETRY_DELAYS_SECONDS[attempt])
                    continue
                raise IncompleteWindow("RPC_TRANSPORT_FAILURE") from None
            except (json.JSONDecodeError, UnicodeError):
                raise IncompleteWindow("RPC_JSON_PARSE_FAILURE") from None
        raise IncompleteWindow("RPC_RETRY_EXHAUSTED")


def safe_error(error: Exception) -> str:
    """Never disclose endpoint URLs or provider tokens in terminal diagnostics."""
    if isinstance(error, IncompleteWindow):
        code = str(error)
        if re.fullmatch(r"[A-Za-z0-9_:-]{1,90}", code):
            return code
    if isinstance(error, ValueError):
        code = str(error)
        if re.fullmatch(r"[A-Z_]{4,80}", code):
            return code
    return "UNEXPECTED_" + type(error).__name__.upper()


class SignatureCache:
    """Atomic immutable finalized-tx JSON cache outside any live Frank storage."""

    def __init__(self, root: Path | None):
        self.root = root
        self.hits = 0
        self.writes = 0

    def _filename(self, wallet: str, signature: str) -> Path | None:
        # No untrusted RPC response may become an arbitrary path.
        if (not re.fullmatch(r"[1-9A-HJ-NP-Za-km-z]{32,64}", wallet)
                or not re.fullmatch(r"[1-9A-HJ-NP-Za-km-z]{64,100}", signature)
                or self.root is None):
            return None
        return self.root / wallet / (signature + ".json")

    def load(self, wallet: str, signature: str, slot: int) -> dict | None:
        file = self._filename(wallet, signature)
        if not file or not file.is_file() or file.is_symlink():
            return None
        try:
            with file.open(encoding="utf-8") as handle:
                data = json.load(handle)
            if (not isinstance(data, dict)
                    or data.get("signature") != signature
                    or data.get("slot") != slot
                    or not isinstance(data.get("tx"), dict)
                    or data["tx"].get("slot") != slot):
                return None
            self.hits += 1
            return data["tx"]
        except (OSError, ValueError, TypeError):
            return None

    def save(self, wallet: str, signature: str, slot: int, tx: dict):
        path = self._filename(wallet, signature)
        if not path:
            return
        parent = path.parent
        parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        if parent.is_symlink() or self.root.is_symlink():
            raise IncompleteWindow("CACHE_SYMLINK_UNSAFE")
        fd, temporary = tempfile.mkstemp(prefix=".partial-", dir=parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as out:
                os.fchmod(out.fileno(), 0o600)
                json.dump({"signature": signature, "slot": slot, "tx": tx}, out)
                out.flush()
                os.fsync(out.fileno())
            os.replace(temporary, path)
            self.writes += 1
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)


def configured_solana_endpoints(path: Path) -> list[str]:
    if not path.is_file() or path.stat().st_mode & 0o077:
        raise IncompleteWindow("RPC_CONFIG_MISSING_OR_PERMISSIONS")
    text = path.read_text().strip()
    endpoints = [x.strip() for x in text.split(",") if x.strip()]
    if not endpoints or len(endpoints) > 10 or any(not x.startswith("https://") for x in endpoints):
        raise IncompleteWindow("RPC_CONFIG_INVALID")
    return endpoints


def derive_robinhood_alchemy_rpcs(solana_endpoints: list[str]) -> list[str]:
    """Reuse an Alchemy *app* key only across Alchemy's known mainnet hosts.

    No generic host substitution; never send existing Solana RPC credentials to
    arbitrary RH/public endpoints. The live scanner still checks chain ID 4663.
    """
    urls: list[str] = []
    for raw in solana_endpoints:
        if not isinstance(raw, str):
            continue
        parsed = urlsplit(raw)
        if (parsed.scheme != "https" or parsed.hostname != "solana-mainnet.g.alchemy.com"
                or parsed.port is not None or parsed.username or parsed.password
                or parsed.query or parsed.fragment):
            continue
        if not re.fullmatch(r"/v2/[A-Za-z0-9_-]{8,256}", parsed.path):
            continue
        target = urlunsplit(("https", "robinhood-mainnet.g.alchemy.com",
                            parsed.path, "", ""))
        if target not in urls:
            urls.append(target)
    return urls


def configured_robinhood_rpc_file(path: Path) -> list[str]:
    """Optional user-managed 0600 file, unlike public unauthenticated RPCs."""
    if path.is_symlink():
        raise IncompleteWindow("RH_RPC_FILE_SYMLINK_UNSAFE")
    if not path.exists():
        return []
    if not path.is_file() or path.stat().st_mode & 0o077:
        raise IncompleteWindow("RH_RPC_FILE_PERMISSIONS_UNSAFE")
    entries = [part.strip() for part in path.read_text(encoding="utf-8").split(",")
               if part.strip()]
    if len(entries) > 8 or any(not url.startswith("https://") for url in entries):
        raise IncompleteWindow("RH_RPC_FILE_CONFIG_INVALID")
    return entries


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


def scan_solana(rpc: RPC, wallet: str, cutoff: int, until: int,
                cache: SignatureCache | None = None) -> dict:
    rpc.scan_stage = "SOL_GET_SIGNATURES"
    signatures = solana_signatures(rpc, wallet, cutoff, until)
    rpc.progress = {"signatures_in_window": len(signatures),
                    "transactions_decoded": 0}
    rows = []
    for item in signatures:
        sig = item["signature"]
        rpc.scan_stage = "SOL_GET_TRANSACTION"
        slot = item.get("slot")
        tx = cache.load(wallet, sig, slot) if cache else None
        if tx is None:
            tx = rpc.call("getTransaction", [sig, {
                "encoding":"jsonParsed", "commitment":"finalized", "maxSupportedTransactionVersion":1,
            }])
            if not tx:
                raise IncompleteWindow("SOL_FINALIZED_TRANSACTION_UNAVAILABLE")
            if tx.get("slot") != slot:
                raise IncompleteWindow("SOL_SIGNATURE_SLOT_MISMATCH")
            if cache:
                cache.save(wallet, sig, slot, tx)
        rpc.scan_stage = "SOL_DECODE_TRANSACTION"
        rows.extend(solana_events(sig, tx, wallet))
        rpc.progress["transactions_decoded"] += 1
    return {
        "chain":"SOL", "wallet":wallet, "status":"COMPLETE",
        "signatures_scanned":len(signatures),
        "cache_hits":cache.hits if cache else 0,
        "rpc_calls":rpc.calls, "legs":rows,
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
            rpc.progress["log_chunks_attempted"] = calls
            logs=rpc.call("eth_getLogs",[{"fromBlock":hex(a),"toBlock":hex(b),"topics":topics}])
            if not isinstance(logs,list):
                raise ValueError("RH_LOGS_NOT_ARRAY")
        except (ValueError, urllib.error.URLError, IncompleteWindow, TimeoutError) as exc:
            # Splitting cannot fix auth errors, 429, transport failure or an
            # unsupported RPC method. Preserve the actual failure stage.
            reason = safe_error(exc)
            if (reason in {"RPC_HTTP_429", "RPC_HTTP_401", "RPC_HTTP_403",
                           "RPC_TRANSPORT_FAILURE", "RPC_JSON_PARSE_FAILURE",
                           "RPC_ERROR_-32601", "RPC_ERROR_-32602",
                           "RPC_ERROR_-32016"} or
                    reason.startswith("RPC_HTTP_5")):
                raise IncompleteWindow(reason) from None
            if a >= b:
                raise IncompleteWindow("RH_LOGS_UNAVAILABLE_" + reason) from None
            mid=(a+b)//2
            stack.extend(((mid+1,b),(a,mid)))
            continue
        result+=logs
        rpc.progress["log_chunks_completed"] = rpc.progress.get("log_chunks_completed", 0) + 1
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
    rpc.scan_stage = "RH_CHAIN_ID"
    chain=int(rpc.call("eth_chainId",[]),16)
    if chain!=RH_CHAIN_ID:
        raise IncompleteWindow("RH_CHAIN_ID_MISMATCH")
    rpc.scan_stage = "RH_GET_WALLET_CODE"
    code=(rpc.call("eth_getCode",[wallet,"latest"]) or "").lower()
    delegation_confirmed = code == FOMO_EIP7702_CODE
    # A Hoodwatch association is only a candidate. Do not suppress evidence
    # collection because its chain code is EOA / changed / unknown; mark it.
    wallet_code_status = ("FOMO_EIP7702_CONFIRMED" if delegation_confirmed else
                          "EOA" if code == "0x" else
                          "OTHER_DELEGATION" if code.startswith("0xef0100") else
                          "CONTRACT_OR_UNKNOWN")
    rpc.scan_stage = "RH_FIND_BLOCK_RANGE"
    first,last=rh_block_number(rpc,cutoff,until)
    if last < first:
        return {"chain":"RH", "wallet":wallet, "status":"COMPLETE",
                "first_block":first,"last_block":last,"userop_tx_count":0,
                "inbound_transfer_tx_count":0,"eip7702_delegation_confirmed":delegation_confirmed,
                "wallet_code_status":wallet_code_status,
                "rpc_calls":rpc.calls,"legs":[]}
    padded=pad_evm_wallet(wallet)
    rpc.scan_stage = "RH_USEROP_LOGS"
    ops=rh_getlogs(rpc,first,last,[TOPIC_USEROP,None,padded])
    rpc.progress["userop_log_count"] = len(ops)
    # Receipts must contain ALL sibling UserOps for correct per-operation scope.
    rpc.scan_stage = "RH_INBOUND_ERC20_LOGS"
    inbound=rh_getlogs(rpc,first,last,[TOPIC_TRANSFER,None,padded])
    rpc.progress["inbound_log_count"] = len(inbound)
    op_hashes={log["transactionHash"] for log in ops}
    transfer_hashes={log["transactionHash"] for log in inbound}
    found=[]
    rpc.progress["candidate_tx_count"] = len(op_hashes | transfer_hashes)
    rpc.progress["receipt_count"] = 0
    for hash_value in sorted(op_hashes|transfer_hashes):
        rpc.scan_stage = "RH_GET_RECEIPT"
        receipt=rpc.call("eth_getTransactionReceipt",[hash_value])
        rpc.progress["receipt_count"] += 1
        if not receipt or receipt.get("status")!="0x1":
            continue
        if hash_value in op_hashes:
            found+=robinhood_user_operations(receipt,wallet)
        if hash_value in transfer_hashes:
            rpc.scan_stage = "RH_GET_TRANSACTION"
            tx=rpc.call("eth_getTransactionByHash",[hash_value])
            if tx:
                found+=robinhood_buy_fills(tx,receipt,wallet)
    return {
        "chain":"RH", "wallet":wallet, "status":"COMPLETE",
        "first_block":first,"last_block":last,"userop_tx_count":len(op_hashes),
        "inbound_transfer_tx_count":len(transfer_hashes),
        "eip7702_delegation_confirmed":delegation_confirmed,
        "wallet_code_status":wallet_code_status,
        "rpc_calls":rpc.calls,"legs":found,
    }


def audit(hours: int, solana_urls: list[str], rh_url: str | None,
          audited_at: int | None = None, cache_dir: Path | None = None,
          rh_extra_urls: list[str] | None = None) -> dict:
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
    cache=SignatureCache(cache_dir)
    for wallet in (SOL_CASH_WALLET,SOL_CANDIDATE_WALLET):
        failures=[]
        for endpoint in solana_urls:
            rpc=RPC(endpoint)
            try:
                value=scan_solana(rpc,wallet,since,until,cache=cache)
                break
            except (IncompleteWindow, ValueError, KeyError, TypeError, urllib.error.URLError, TimeoutError) as exc:
                # Never output private RPC URL, token or exception trace.
                failures.append({
                    "reason":safe_error(exc), "stage":rpc.scan_stage,
                    "method":rpc.last_method, "rpc_calls":rpc.calls,
                    **rpc.progress,
                })
        else:
            value={"chain":"SOL","wallet":wallet,"status":"INCOMPLETE",
                   "error":"SOL_SCAN_INCOMPLETE",
                   "endpoint_trials":len(failures),
                   "diagnostics":failures,"cache_hits":cache.hits,"legs":[]}
        legs+=value.pop("legs")
        report["chains"].append(value)
    # Prefer supplied authenticated RPCs over public endpoints (which returned
    # 403 on Mac). An alternate MUST pass eth_chainId 4663 to be accepted.
    rh_endpoints = []
    for endpoint in ([rh_url] if rh_url else []) + list(rh_extra_urls or []) + list(DEFAULT_RH_RPCS):
        if isinstance(endpoint, str) and endpoint.startswith("https://") and endpoint not in rh_endpoints:
            rh_endpoints.append(endpoint)
    rh_failures = []
    for endpoint in rh_endpoints:
        rh_rpc = RPC(endpoint)
        try:
            value=scan_robinhood(rh_rpc,RH_CANDIDATE_WALLET,since,until)
            break
        except (IncompleteWindow, ValueError, KeyError, TypeError, urllib.error.URLError, TimeoutError) as exc:
            rh_failures.append({
                "reason":safe_error(exc), "stage":rh_rpc.scan_stage,
                "method":rh_rpc.last_method, "rpc_calls":rh_rpc.calls,
                **rh_rpc.progress,
            })
    else:
        value={"chain":"RH","wallet":RH_CANDIDATE_WALLET,"status":"INCOMPLETE",
               "error":"RH_SCAN_INCOMPLETE","endpoint_trials":len(rh_failures),
               "diagnostics":rh_failures,"legs":[]}
    legs+=value.pop("legs")
    report["chains"].append(value)
    report["cache"]={"hits":cache.hits,"writes":cache.writes,
                     "enabled":cache_dir is not None}
    report["rh_provider_diagnostics"]={
        "authenticated_candidate_count":len(rh_extra_urls or []) + (1 if rh_url else 0),
        "total_providers_checked":len(rh_endpoints) if value["status"]!="COMPLETE" else None,
        "authenticated_provider_configured":bool(rh_extra_urls or rh_url),
        "configure_hint":("AUTHENTICATED_RH_RPC_RECOMMENDED"
                          if value["status"]!="COMPLETE" else None),
    }
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
    parser.add_argument("--robinhood-rpc",default=os.environ.get("ROBINHOOD_RPC_URL"),
                        help="Optional private Robinhood Mainnet RPC URL (never printed)")
    parser.add_argument("--robinhood-rpc-file",type=Path,
                        default=Path.home()/"Library/Application Support/FrankMeme/robinhood_rpc_urls",
                        help="Optional private 0600 HTTPS Robinhood RPC list; never printed")
    parser.add_argument("--no-reuse-solana-alchemy",action="store_true",
                        help="Do not derive Robinhood Alchemy endpoint from a configured Solana Alchemy app key")
    parser.add_argument("--output",type=Path,help="Optional research JSON report; never a production DB")
    parser.add_argument("--cache-dir",type=Path,
                        default=Path.home()/"Documents/ChatGPT/frank-fomo-rpc-cache",
                        help="Separate resumable finalized Solana transaction cache")
    parser.add_argument("--as-of-epoch",type=int,
                        help="Reproduce a fixed UTC time window; end timestamp inclusive")
    args=parser.parse_args()
    try:
        endpoints=configured_solana_endpoints(args.solana_rpc_file)
        if args.cache_dir.is_symlink():
            raise IncompleteWindow("CACHE_DIR_SYMLINK_UNSAFE")
        cache_dir=args.cache_dir.resolve()
        if (cache_dir.is_symlink() or
            "FrankMeme" in str(cache_dir) or
            "crypto-monitor-frank-only" in str(cache_dir) or
            "mission-control" in str(cache_dir)):
            raise IncompleteWindow("CACHE_DIR_UNSAFE")
        private_rh=configured_robinhood_rpc_file(args.robinhood_rpc_file)
        if not args.no_reuse_solana_alchemy:
            private_rh += derive_robinhood_alchemy_rpcs(endpoints)
        # De-duplicate credentials without ever printing them.
        private_rh = list(dict.fromkeys(private_rh))
        result=audit(args.hours,endpoints,args.robinhood_rpc,args.as_of_epoch,
                     cache_dir=cache_dir,rh_extra_urls=private_rh)
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
    # Keep the terminal readable; exact chain evidence remains in --output JSON.
    summary={
        "status":result["status"],"window_hours":result["window_hours"],
        "cutoff_epoch":result["cutoff_epoch"],
        "window_end_epoch":result["audited_at_epoch"],
        "identity_attribution":result["identity_attribution"],
        "chain_coverage":[
            {k:v for k,v in chain.items() if k in (
                "chain","wallet","status","error","signatures_scanned",
                "userop_tx_count","inbound_transfer_tx_count",
                "eip7702_delegation_confirmed","wallet_code_status",
                "diagnostics","cache_hits")}
            for chain in result["chains"]
        ],
        "leg_counts":result["counts"],"order_counts":result["paired_counts"],
        "paired_preview":result["paired"][:15],
        "evidence_rows_total":len(result["evidence"]),
        "rpc_cache":result["cache"],
        "rh_provider_diagnostics":result.get("rh_provider_diagnostics", {}),
        "full_evidence_file":str(args.output) if args.output else None,
        "production_db_writes":0,"gmail_sent":0,"follow_signals_changed":False,
    }
    print(json.dumps(summary,ensure_ascii=False,indent=2,sort_keys=True))
    return 0 if result["status"]=="RPC_WINDOW_COMPLETE_IDENTITY_UNVERIFIED" else 3


if __name__=="__main__":
    try:
        raise SystemExit(main())
    except Exception:
        print('{"status":"AUDIT_FAILED","production_db_writes":0,"gmail_sent":0}',file=sys.stderr)
        raise SystemExit(4)
