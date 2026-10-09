#!/usr/bin/env python3
"""Review-only resumable Frank owner-account audit. Default: OFFLINE PLAN.

This file does not run from launchd, touch production data, emit signals or send
notifications. Network access requires BOTH --phase signatures|decode and
--allow-network. It uses exactly the configured existing RPC, never GMGN.

Checkpoint contract: fixed report SHA + root decoded tx SHA + exact owner-account
inventory, wallet, time window, commitment and unchanged caps. Each successful
100-signature page and each decoded transaction receipt is atomic, 0600 and
content-hash verified. A 429 halts without automatic retries or cursor advance.
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

from mission_agent.meme.fomo_crosschain import SOL_CASH_WALLET as WALLET
from scripts.audit_frank_fomo_crosschain import (
    MAX_SOL_PAGES, MAX_SOL_TRANSACTIONS_PER_WALLET,
    configured_solana_endpoints, IncompleteWindow,
)
from scripts.audit_frank_native_owner_coverage import (
    START, END, MAX_ADDITIONAL_TRANSACTIONS,
    account_keys, build_seed_inventory, flows, local_snapshot,
)
from scripts.audit_frank_root_offline import cached_root
from scripts.inspect_frank_solana_root_window import read_report

VERSION = 1
PAGE_SIZE = 250
MAX_CALLS_PER_RUN = 8
MIN_REQUEST_INTERVAL_SECONDS = 1.0
SIGNATURE_RE = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{64,100}$")
ACCOUNT_RE = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$")
RESEARCH_DIR = Path.home() / "Documents/ChatGPT/frank-fomo-research"
CHECKPOINT_DIR = RESEARCH_DIR / "native-owner-resume-v1"


class ScanBlocked(Exception):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(",",":"),allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def valid_root(path):
    path=path.expanduser()
    if path.is_symlink() or "live-v1" in str(path) or "FrankMeme" in str(path):
        raise ScanBlocked("CHECKPOINT_ROOT_UNSAFE")
    return path


def offline_context(source, cache, db):
    count, source_sha=read_report(source,WALLET,START,END)
    txs=cached_root(cache,WALLET,START,END,count)
    root, local_trades=local_snapshot(db,WALLET,START,END)
    if set(txs)!=root:
        raise ScanBlocked("ROOT_LEDGER_NOT_RECONCILED")
    inventory,_=build_seed_inventory(txs,WALLET)
    root_tx_digest=digest([
        [s,tx["slot"],tx["blockTime"],digest(tx)]
        for s,tx in sorted(txs.items())
    ])
    context={
        "version":VERSION,"wallet":WALLET,"start":START,"end":END,
        "source_sha256":source_sha,"root_tx_sha256":root_tx_digest,
        "root_count":count,"commitment":"finalized",
        "page_size":PAGE_SIZE,"max_signatures":MAX_SOL_TRANSACTIONS_PER_WALLET,
        "max_pages":MAX_SOL_PAGES,
        "max_extra_decode":MAX_ADDITIONAL_TRANSACTIONS,
        "inventory":dict(sorted(inventory.items())),
    }
    return context,set(root),set(local_trades)


class Checkpoints:
    def __init__(self,root,context,create=False):
        self.root=valid_root(root)
        self.context=context
        self.key=digest(context)
        if create:
            self.root.mkdir(parents=True,exist_ok=True,mode=0o700)
        if self.root.exists():
            if not self.root.is_dir() or self.root.stat().st_mode & 0o077:
                raise ScanBlocked("CHECKPOINT_PERMISSIONS")
        self.manifest=self.root/"manifest.json"
        if create:
            existing=self._read(self.manifest)
            if existing is None:
                self._write(self.manifest,{"key":self.key,"context":context})
            elif existing.get("key")!=self.key or existing.get("context")!=context:
                raise ScanBlocked("CHECKPOINT_CONTEXT_MISMATCH")
        elif self.manifest.exists():
            existing=self._read(self.manifest)
            if existing.get("key")!=self.key or existing.get("context")!=context:
                raise ScanBlocked("CHECKPOINT_CONTEXT_MISMATCH")

    def _read(self,path):
        if path.is_symlink():
            raise ScanBlocked("CHECKPOINT_SYMLINK_UNSAFE")
        if not path.exists():
            return None
        if not path.is_file() or path.stat().st_mode & 0o077 or path.stat().st_size>2_000_000:
            raise ScanBlocked("CHECKPOINT_FILE_UNSAFE")
        try:
            obj=json.loads(path.read_bytes())
            if not isinstance(obj,dict) or not isinstance(obj.get("sha256"),str):
                raise ValueError
            payload={k:v for k,v in obj.items() if k!="sha256"}
            if digest(payload)!=obj["sha256"]:
                raise ScanBlocked("CHECKPOINT_HASH_MISMATCH")
            return payload
        except (ValueError,TypeError,UnicodeError):
            raise ScanBlocked("CHECKPOINT_INVALID_JSON") from None

    def _write(self,path,payload):
        if path.is_symlink():
            raise ScanBlocked("CHECKPOINT_SYMLINK_UNSAFE")
        obj={**payload,"sha256":digest(payload)}
        fd,name=tempfile.mkstemp(prefix=".checkpoint-",dir=self.root)
        try:
            with os.fdopen(fd,"wb") as out:
                os.fchmod(out.fileno(),0o600)
                out.write(canonical(obj))
                out.flush()
                os.fsync(out.fileno())
            os.replace(name,path)
        finally:
            if os.path.exists(name):
                os.unlink(name)

    def account(self,addr):
        if addr not in self.context["inventory"] or not ACCOUNT_RE.fullmatch(addr):
            raise ScanBlocked("UNEXPECTED_ACCOUNT")
        item=self._read(self.root/("account-"+addr+".json"))
        if item is None:
            return {
                "context":self.key,"account":addr,
                "mint":self.context["inventory"][addr],
                "status":"PENDING","before":None,"rows":[],"pages":0,
            }
        if (item.get("context")!=self.key or item.get("account")!=addr or
                item.get("mint")!=self.context["inventory"][addr]):
            raise ScanBlocked("ACCOUNT_IDENTITY_MISMATCH")
        if item.get("status") not in ("PENDING","ACTIVE","COMPLETE","CAPPED"):
            raise ScanBlocked("ACCOUNT_STATUS_INVALID")
        rows=item.get("rows")
        if not isinstance(rows,list) or len(rows)>MAX_SOL_TRANSACTIONS_PER_WALLET:
            raise ScanBlocked("ACCOUNT_SIGNATURE_BUDGET_BROKEN")
        if (item.get("before") is not None and
                (not isinstance(item.get("before"),str) or
                 not SIGNATURE_RE.fullmatch(item["before"]))):
            raise ScanBlocked("ACCOUNT_CURSOR_INVALID")
        if item.get("pages")!=0 and item.get("before") is None and item["status"]=="ACTIVE":
            raise ScanBlocked("ACCOUNT_CURSOR_MISSING")
        if any(not isinstance(r,dict) or
               not isinstance(r.get("signature"),str) or
               not SIGNATURE_RE.fullmatch(r["signature"]) or
               type(r.get("slot")) is not int or
               type(r.get("blockTime")) is not int or
               not START<=r["blockTime"]<=END for r in rows):
            raise ScanBlocked("ACCOUNT_ROWS_INVALID")
        if len({r["signature"] for r in rows})!=len(rows):
            raise ScanBlocked("ACCOUNT_DUPLICATE_SIGNATURE")
        if any(older["blockTime"]>newer["blockTime"]
               for newer,older in zip(rows,rows[1:])):
            raise ScanBlocked("ACCOUNT_HISTORY_ORDER_INVALID")
        if type(item.get("pages")) is not int or not 0<=item["pages"]<=MAX_SOL_PAGES:
            raise ScanBlocked("ACCOUNT_PAGE_LIMIT_BROKEN")
        if len(rows)>item["pages"]*PAGE_SIZE:
            raise ScanBlocked("ACCOUNT_ROWS_EXCEED_PAGES")
        if item["status"]=="PENDING" and (item["pages"] or rows or item["before"]):
            raise ScanBlocked("ACCOUNT_PENDING_HAS_PROGRESS")
        return item

    def save_account(self,item):
        self._write(self.root/("account-"+item["account"]+".json"),item)

    def receipt(self,sig):
        if not SIGNATURE_RE.fullmatch(sig):
            raise ScanBlocked("INVALID_RECEIPT_SIGNATURE")
        row=self._read(self.root/("receipt-"+sig+".json"))
        if row is not None and (row.get("context")!=self.key or row.get("signature")!=sig):
            raise ScanBlocked("RECEIPT_CONTEXT_MISMATCH")
        return row

    def save_receipt(self,sig,tx,evidence):
        self._write(self.root/("receipt-"+sig+".json"),{
            "context":self.key,"signature":sig,
            "slot":tx["slot"],"tx_sha256":digest(tx),
            **evidence,"trade_confirmed":False,
        })


def one_rpc(url,method,params):
    """Single HTTP attempt. The legacy RPC client retries 429; this must not."""
    if not isinstance(url,str) or not url.startswith("https://"):
        raise ScanBlocked("RPC_ENDPOINT_INVALID")
    request=urllib.request.Request(
        url,data=canonical({"jsonrpc":"2.0","id":1,"method":method,"params":params}),
        headers={"Content-Type":"application/json","Accept":"application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request,timeout=18) as resp:
            body=json.load(resp)
    except urllib.error.HTTPError as exc:
        if exc.code==429:
            raise ScanBlocked("RPC_HTTP_429") from None
        raise ScanBlocked("RPC_HTTP_"+str(exc.code)) from None
    except (urllib.error.URLError,TimeoutError,OSError,ValueError):
        raise ScanBlocked("RPC_TRANSPORT_OR_JSON_FAILURE") from None
    if not isinstance(body,dict):
        raise ScanBlocked("RPC_INVALID_REPLY")
    if body.get("error"):
        err=body["error"]
        code=err.get("code") if isinstance(err,dict) else None
        if code in (-32005,-32016):
            raise ScanBlocked("RPC_RATE_LIMIT")
        raise ScanBlocked("RPC_JSON_ERROR")
    if "result" not in body:
        raise ScanBlocked("RPC_RESULT_MISSING")
    return body["result"]


def scan_page(state,call):
    """Mutates a copy; caller commits only after the page fully validates."""
    if state["status"] in ("COMPLETE","CAPPED"):
        return state
    if state["pages"]>=MAX_SOL_PAGES:
        return {**state,"status":"CAPPED"}
    opts={"limit":PAGE_SIZE,"commitment":"finalized"}
    if state["before"]:
        opts["before"]=state["before"]
    page=call("getSignaturesForAddress",[state["account"],opts])
    if not isinstance(page,list) or len(page)>PAGE_SIZE:
        raise ScanBlocked("SIGNATURE_PAGE_INVALID")
    new={**state,"rows":list(state["rows"]),"pages":state["pages"]+1}
    seen={r["signature"] for r in new["rows"]}
    prev_time=state["rows"][-1]["blockTime"] if state["rows"] else None
    cutoff=False
    for row in page:
        if not isinstance(row,dict):
            raise ScanBlocked("SIGNATURE_ROW_INVALID")
        sig=row.get("signature")
        at=row.get("blockTime")
        slot=row.get("slot")
        if (not isinstance(sig,str) or not SIGNATURE_RE.fullmatch(sig)
                or type(at) is not int or type(slot) is not int):
            raise ScanBlocked("SIGNATURE_ROW_INVALID")
        if prev_time is not None and at>prev_time:
            raise ScanBlocked("SIGNATURE_TIME_ORDER_INVALID")
        prev_time=at
        if at<START:
            cutoff=True
            break
        if at<=END:
            if sig in seen:
                raise ScanBlocked("SIGNATURE_PAGE_DUPLICATE")
            seen.add(sig)
            new["rows"].append({"signature":sig,"slot":slot,"blockTime":at})
            if len(new["rows"])>MAX_SOL_TRANSACTIONS_PER_WALLET:
                raise ScanBlocked("ACCOUNT_SIGNATURE_BUDGET_BROKEN")
    if state["before"] and page and page[-1].get("signature")==state["before"]:
        raise ScanBlocked("SIGNATURE_CURSOR_STALLED")
    new["before"]=page[-1]["signature"] if page else state["before"]
    if cutoff or len(page)<PAGE_SIZE:
        new["status"]="COMPLETE"
    elif (len(new["rows"])>=MAX_SOL_TRANSACTIONS_PER_WALLET
          or new["pages"]>=MAX_SOL_PAGES):
        new["status"]="CAPPED"
    else:
        new["status"]="ACTIVE"
    return new


def decode_candidates(store,root_sigs):
    """Deduped signatures from ONLY fully scanned accounts; no missing=zero."""
    all_sigs={}
    for addr in sorted(store.context["inventory"]):
        row=store.account(addr)
        if row["status"]!="COMPLETE":
            continue
        for sig in row["rows"]:
            if sig["signature"] in root_sigs:
                continue
            other=all_sigs.get(sig["signature"])
            if other is not None and (
                other["slot"]!=sig["slot"] or
                other["blockTime"]!=sig["blockTime"]
            ):
                raise ScanBlocked("SIGNATURE_CONFLICT_ACROSS_ACCOUNTS")
            all_sigs[sig["signature"]]=sig
    ordered=sorted(all_sigs.values(),key=lambda r:(r["blockTime"],r["slot"],r["signature"]))
    return ordered[:MAX_ADDITIONAL_TRANSACTIONS],len(ordered[MAX_ADDITIONAL_TRANSACTIONS:])


def decode_tx(row,call):
    tx=call("getTransaction",[row["signature"],{
        "encoding":"jsonParsed","commitment":"finalized",
        "maxSupportedTransactionVersion":1,
    }])
    if (not isinstance(tx,dict) or tx.get("slot")!=row["slot"]
            or tx.get("blockTime")!=row["blockTime"]):
        raise ScanBlocked("DECODE_TRANSACTION_MISMATCH")
    if not isinstance(tx.get("meta"),dict) or not isinstance(tx.get("transaction"),dict):
        raise ScanBlocked("DECODE_TRANSACTION_INCOMPLETE")
    indicators=flows(tx,WALLET)
    return tx,{
        "root_referenced":WALLET in account_keys(tx),
        "opposing_flow":indicators["opposing_net_token_quote"],
        "fomo_cosigned":indicators["fomo_cosigned"],
        "target_mints":indicators["target_mints"],
        "quote_mints":indicators["quote_mints"],
    }


def do_run(store,root_sigs,phase,network,budget,endpoint=None,account=None):
    counts={"rpc_attempts":0,"new_signature_pages":0,"new_receipts":0}
    failure=None
    if phase=="plan":
        return counts,None
    if not network:
        raise ScanBlocked("EXPLICIT_NETWORK_PERMISSION_REQUIRED")
    if not 1<=budget<=MAX_CALLS_PER_RUN:
        raise ScanBlocked("REQUEST_BUDGET_INVALID")
    if account is not None and (
        not isinstance(account,str) or account not in store.context["inventory"]
    ):
        raise ScanBlocked("ACCOUNT_OUTSIDE_OBSERVED_INVENTORY")
    last_rpc_at=None
    def call(method,params):
        nonlocal last_rpc_at
        if counts["rpc_attempts"]>=budget:
            raise ScanBlocked("REQUEST_BUDGET_EXHAUSTED")
        if last_rpc_at is not None:
            delay=MIN_REQUEST_INTERVAL_SECONDS-(time.monotonic()-last_rpc_at)
            if delay>0:
                time.sleep(delay)
        last_rpc_at=time.monotonic()
        counts["rpc_attempts"]+=1
        return one_rpc(endpoint,method,params)
    if phase=="signatures":
        selected=[account] if account is not None else sorted(store.context["inventory"])
        for addr in selected:
            state=store.account(addr)
            while state["status"] not in ("COMPLETE","CAPPED"):
                if counts["rpc_attempts"]>=budget:
                    return counts,"REQUEST_BUDGET_EXHAUSTED"
                try:
                    updated=scan_page(state,call)
                except ScanBlocked as exc:
                    return counts,exc.code
                store.save_account(updated)
                state=updated
                counts["new_signature_pages"]+=1
    elif phase=="decode":
        candidates,_=decode_candidates(store,root_sigs)
        for row in candidates:
            if store.receipt(row["signature"]) is not None:
                continue
            if counts["rpc_attempts"]>=budget:
                return counts,"REQUEST_BUDGET_EXHAUSTED"
            try:
                tx,info=decode_tx(row,call)
            except ScanBlocked as exc:
                return counts,exc.code
            store.save_receipt(row["signature"],tx,info)
            counts["new_receipts"]+=1
    else:
        raise ScanBlocked("UNKNOWN_PHASE")
    return counts,failure


def report(store,root_sigs,local_trades,counts,stopped):
    states={addr:store.account(addr) for addr in sorted(store.context["inventory"])}
    candidates,deferred=decode_candidates(store,root_sigs)
    completed={addr:s for addr,s in states.items() if s["status"]=="COMPLETE"}
    capped={addr:{"mint":s["mint"],"observed_rows":len(s["rows"]),
                   "status":"INCOMPLETE_LIMIT"} for addr,s in states.items()
            if s["status"]=="CAPPED"}
    undecoded=[]
    decoded=[]
    for row in candidates:
        rcpt=store.receipt(row["signature"])
        if rcpt is None:
            undecoded.append(row["signature"])
        else:
            if (rcpt.get("slot")!=row["slot"] or
                    not isinstance(rcpt.get("tx_sha256"),str) or
                    not re.fullmatch(r"[0-9a-f]{64}",rcpt["tx_sha256"]) or
                    type(rcpt.get("opposing_flow")) is not bool or
                    type(rcpt.get("root_referenced")) is not bool or
                    type(rcpt.get("fomo_cosigned")) is not bool or
                    not isinstance(rcpt.get("target_mints"),list) or
                    not isinstance(rcpt.get("quote_mints"),list)):
                raise ScanBlocked("RECEIPT_EVIDENCE_INVALID")
            decoded.append(rcpt)
    full_observed=(len(completed)==len(states) and not deferred and not undecoded)
    return {
        "status":("OBSERVED_SCOPE_REVIEW_COMPLETE" if full_observed else
                  "OBSERVED_SCOPE_PARTIAL"),
        "wallet":WALLET,"start":START,"end":END,
        "source_sha256":store.context["source_sha256"],
        "context_sha256":store.key,
        "historical_root_count":len(root_sigs),
        "local_classified_count":len(local_trades),
        "accounts_total":len(states),
        "accounts_complete":len(completed),
        "accounts_capped":capped,
        "accounts_pending_or_active":[{
            "account":addr,"mint":state["mint"],"status":state["status"],
            "saved_pages":state["pages"],"saved_signatures":len(state["rows"])
        } for addr,state in states.items() if state["status"] in ("PENDING","ACTIVE")],
        "extra_signature_candidates_from_completed_accounts":len(candidates)+deferred,
        "decode_receipts_complete":len(decoded),
        "decode_receipts_pending":len(undecoded),
        "decode_deferred_by_original_budget":deferred,
        "decoded_opposing_flow_review_candidates":sum(bool(x["opposing_flow"]) for x in decoded),
        "decoded_receipt_sample":[{
            "signature":x["signature"],"slot":x["slot"],
            "root_referenced":x["root_referenced"],
            "opposing_flow":x["opposing_flow"],
            "fomo_cosigned":x["fomo_cosigned"],
            "target_mints":x["target_mints"],
            "quote_mints":x["quote_mints"],
        } for x in decoded][:20],
        "decoded_review_sample":[{
            "signature":x["signature"],"opposing_flow":x["opposing_flow"],
            "root_referenced":x["root_referenced"],"fomo_cosigned":x["fomo_cosigned"],
            "target_mints":x["target_mints"]
        } for x in decoded if x["opposing_flow"]][:20],
        "stop_reason":stopped,
        **counts,
        "trade_confirmed_by_audit":False,
        "full_person_trade_coverage":False,
        "unknown_never_root_referenced_accounts":True,
        "production_db_writes":0,"signals_changed":False,"emails_sent":0,
        "warning":"Even complete observed-account evidence does not establish full wallet/person trade coverage. Accounts never referenced by root remain unknown. No receipt is a confirmed executable fill or follow signal.",
    }


def main():
    cli=argparse.ArgumentParser(description="Frank durable checkpoint scanner (PLAN ONLY BY DEFAULT)")
    cli.add_argument("--phase",choices=("plan","signatures","decode"),default="plan")
    cli.add_argument("--allow-network",action="store_true")
    cli.add_argument("--max-rpc-calls",type=int,default=3)
    cli.add_argument("--account",default=None,help="Limit signature phase to one root-observed owned token account")
    cli.add_argument("--checkpoint-dir",type=Path,default=CHECKPOINT_DIR)
    cli.add_argument("--source-report",type=Path,
                     default=Path.home()/"Documents/ChatGPT/frank-fomo-fixed-20261009-054846.json")
    cli.add_argument("--cache-dir",type=Path,
                     default=Path.home()/"Documents/ChatGPT/frank-fomo-rpc-cache")
    cli.add_argument("--db",type=Path,
                     default=Path.home()/"Documents/ChatGPT/crypto-monitor-frank-only-evidence-20261003/live-v1/forward.sqlite")
    cli.add_argument("--rpc-file",type=Path,
                     default=Path.home()/"Library/Application Support/FrankMeme/solana_rpc_urls")
    args=cli.parse_args()
    try:
        if args.phase!="plan" and not args.allow_network:
            raise ScanBlocked("EXPLICIT_NETWORK_PERMISSION_REQUIRED")
        if args.phase!="plan" and not 1<=args.max_rpc_calls<=MAX_CALLS_PER_RUN:
            raise ScanBlocked("REQUEST_BUDGET_INVALID")
        if args.account and args.phase!="signatures":
            raise ScanBlocked("ACCOUNT_FILTER_REQUIRES_SIGNATURES_PHASE")
        ctx,root_sigs,local_trades=offline_context(args.source_report,args.cache_dir,args.db)
        store=Checkpoints(args.checkpoint_dir,ctx,create=args.phase!="plan")
        if args.account and args.account not in ctx["inventory"]:
            raise ScanBlocked("ACCOUNT_OUTSIDE_OBSERVED_INVENTORY")
        if args.phase=="plan":
            counts,reason=do_run(store,root_sigs,"plan",False,0)
        else:
            urls=configured_solana_endpoints(args.rpc_file)
            if not urls:
                raise ScanBlocked("RPC_CONFIG_EMPTY")
            # No key rotation, fallbacks, extra RPC apps or retries.
            lock=store.root/".run.lock"
            if lock.is_symlink():
                raise ScanBlocked("CHECKPOINT_LOCK_SYMLINK")
            fd=os.open(lock,os.O_CREAT|os.O_RDWR,0o600)
            try:
                fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
                counts,reason=do_run(store,root_sigs,args.phase,True,
                                     args.max_rpc_calls,urls[0],
                                     account=args.account)
            except BlockingIOError:
                raise ScanBlocked("CONCURRENT_RESEARCH_SCAN")
            finally:
                os.close(fd)
        output=report(store,root_sigs,local_trades,counts,reason)
        output["selected_account"]=args.account
        print(json.dumps(output,ensure_ascii=False,indent=2))
        return 0 if args.phase=="plan" or (
            not reason and output["status"]=="OBSERVED_SCOPE_REVIEW_COMPLETE"
        ) else 2
    except (ScanBlocked,IncompleteWindow,OSError,ValueError,TypeError,KeyError) as exc:
        msg=str(exc)
        if not re.fullmatch(r"[A-Z][A-Z0-9_]{3,80}",msg):
            msg="RESEARCH_AUDIT_BLOCKED"
        print(json.dumps({
            "status":"UNVERIFIED","reason":msg,
            "production_db_writes":0,"emails_sent":0,"rpc_requests_unverified":True,
        }))
        return 2


if __name__=="__main__":
    raise SystemExit(main())
