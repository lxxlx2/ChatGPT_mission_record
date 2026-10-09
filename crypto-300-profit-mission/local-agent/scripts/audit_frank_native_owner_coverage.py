#!/usr/bin/env python3
"""Read-only historical Solana owner-account discovery from cached Frank root transactions.

Independent of paid GMGN API. Pinned fixed finalized historical window.
Find owner token accounts seen in those transactions, query each account's
onchain signatures, and highlight gaps without turning transfers into BUYs.
No production DB or services are modified. Cannot discover historical
accounts that never appeared in the root cache.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import sys

from mission_agent.meme.fomo_crosschain import (
    SOL_CASH_WALLET as WALLET, FOMO_COSIGNER, USDC, SOL_ROUTERS,
)
from scripts.audit_frank_fomo_crosschain import (
    RPC, SignatureCache, IncompleteWindow, configured_solana_endpoints, solana_signatures,
)
from scripts.inspect_frank_solana_root_window import owned_deltas, read_report

START = 1791386454
END = 1791472854
WSOL = "So11111111111111111111111111111111111111112"
USDT = "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB"
QUOTE = {USDC, WSOL, USDT}
MAX_OWNER_ACCOUNTS = 100
MAX_ADDITIONAL_TRANSACTIONS = 300
BASE58 = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$")


class EvidenceGap(Exception):
    pass


class AuditStageError(EvidenceGap):
    def __init__(self, stage, code, details=None):
        self.stage=stage
        self.code=code
        self.details=details or {}
        super().__init__(code)


def safe_failure_code(exc):
    raw=str(exc)
    if isinstance(exc,(EvidenceGap,IncompleteWindow,ValueError)) and re.fullmatch(
        r"[A-Z][A-Z0-9_]*(?::[0-9]+)?",raw
    ):
        return raw
    return "UNEXPECTED_" + type(exc).__name__.upper()


def stage_call(stage, action, *args):
    try:
        return action(*args)
    except AuditStageError:
        raise
    except (EvidenceGap,IncompleteWindow,OSError,ValueError,TypeError,KeyError,sqlite3.Error) as exc:
        raise AuditStageError(stage,safe_failure_code(exc)) from None


def account_keys(tx):
    m = (tx.get("transaction") or {}).get("message") or {}
    keys = m.get("accountKeys")
    if not isinstance(keys, list):
        raise EvidenceGap("TX_ACCOUNT_KEYS_MISSING")
    names = []
    for key in keys:
        name = key.get("pubkey") if isinstance(key, dict) else None
        if not isinstance(name, str):
            raise EvidenceGap("TX_JSON_PARSED_KEYS_REQUIRED")
        names.append(name)
    return names


def owned_accounts(tx, wallet):
    names = account_keys(tx)
    meta = tx.get("meta") or {}
    result = {}
    for column in ("preTokenBalances", "postTokenBalances"):
        rows = meta.get(column)
        if not isinstance(rows, list):
            raise EvidenceGap("TOKEN_BALANCE_VECTORS_MISSING")
        for row in rows:
            if row.get("owner") != wallet:
                continue
            idx = row.get("accountIndex")
            mint = row.get("mint")
            if type(idx) is not int or idx < 0 or idx >= len(names):
                raise EvidenceGap("TOKEN_ACCOUNT_INDEX_UNRESOLVED")
            if not isinstance(mint, str) or not BASE58.fullmatch(mint):
                raise EvidenceGap("MINT_MISSING")
            address = names[idx]
            if not BASE58.fullmatch(address):
                raise EvidenceGap("TOKEN_ACCOUNT_ADDRESS_INVALID")
            if address in result and result[address] != mint:
                raise EvidenceGap("TOKEN_ACCOUNT_MINT_CONFLICT")
            result[address] = mint
    return result


def flows(tx, wallet):
    deltas = owned_deltas(tx,wallet)
    tokens = [r for r in deltas if r["mint"] not in QUOTE and int(r["raw"])!=0]
    quotes = [r for r in deltas if r["mint"] in QUOTE and int(r["raw"])!=0]
    opposing = [(t,q) for t in tokens for q in quotes
                if int(t["raw"])*int(q["raw"])<0]
    signed = any(x.get("pubkey")==wallet and x.get("signer") is True
                 for x in (tx["transaction"]["message"].get("accountKeys") or []))
    cosigned = any(x.get("pubkey")==FOMO_COSIGNER and x.get("signer") is True
                   for x in (tx["transaction"]["message"].get("accountKeys") or []))
    instruction_ids = set()
    for ix in tx["transaction"]["message"].get("instructions") or []:
        if isinstance(ix, dict) and isinstance(ix.get("programId"),str):
            instruction_ids.add(ix["programId"])
    for group in (tx["meta"].get("innerInstructions") or []):
        for ix in group.get("instructions") or []:
            if isinstance(ix, dict) and isinstance(ix.get("programId"),str):
                instruction_ids.add(ix["programId"])
    return {
        "signed_by_root":signed,"fomo_cosigned":cosigned,
        "has_known_router":bool(instruction_ids & SOL_ROUTERS),
        "opposing_net_token_quote":bool(opposing),
        "target_mints":[r["mint"] for r in tokens],
        "quote_mints":[r["mint"] for r in quotes],
        "target_count":len(tokens),"quote_count":len(quotes),
        "no_observed_token_net":not (tokens or quotes),
        "trade_confirmed":False,
    }


def fetch_cached_root(source_rows, cache, wallet):
    raw_transactions={}
    found=set()
    for row in source_rows:
        signature,slot=row.get("signature"),row.get("slot")
        if not isinstance(signature,str) or type(slot) is not int:
            raise EvidenceGap("SOURCE_SIGNATURE_METADATA_INVALID")
        if signature in found:
            raise EvidenceGap("DUPLICATE_ROOT_SIGNATURE")
        found.add(signature)
        tx=cache.load(wallet,signature,slot)
        if tx is None:
            raise EvidenceGap("ROOT_CACHE_NOT_COMPLETE")
        raw_transactions[signature]=tx
    return raw_transactions


def build_seed_inventory(root_transactions,wallet):
    inventory={}
    error_rows=[]
    baseline=Counter()
    for sig,tx in root_transactions.items():
        try:
            discovered=owned_accounts(tx,wallet)
            for account,mint in discovered.items():
                if account in inventory and inventory[account]!=mint:
                    raise EvidenceGap("OWNER_ACCOUNT_MINT_CONFLICT")
                inventory[account]=mint
            f=flows(tx,wallet)
            key=("ROOT_SIGNED" if f["signed_by_root"] else "ROOT_NOT_SIGNER",
                 "OPPOSING" if f["opposing_net_token_quote"] else
                 "TARGET_ONLY" if f["target_count"] else
                 "QUOTE_ONLY" if f["quote_count"] else "NO_TOKEN_NET")
            baseline[key]+=1
        except (EvidenceGap,KeyError,ValueError,TypeError):
            error_rows.append(sig)
    if error_rows:
        raise EvidenceGap("ROOT_CACHE_ROWS_UNPARSABLE:"+str(len(error_rows)))
    if len(inventory)>MAX_OWNER_ACCOUNTS:
        raise EvidenceGap("OWNER_TOKEN_ACCOUNTS_OVER_CAP")
    return inventory,baseline


def local_snapshot(db_path, wallet, start, end):
    if db_path.is_symlink() or not db_path.is_file():
        raise EvidenceGap("LOCAL_LEDGER_NOT_FOUND")
    uri=db_path.resolve().as_uri()+"?mode=ro"
    try:
        db=sqlite3.connect(uri,uri=True)
        db.execute("PRAGMA query_only=ON")
        root={x[0] for x in db.execute(
            "SELECT signature FROM signatures WHERE person_id='frank' "
            "AND wallet=? AND block_time>=? AND block_time<=?",
            (wallet,start,end))}
        trades={x[0] for x in db.execute(
            "SELECT t.signature FROM trades t JOIN signatures s "
            "ON t.wallet=s.wallet AND t.signature=s.signature "
            "WHERE s.person_id='frank' AND s.wallet=? "
            "AND t.block_time>=? AND t.block_time<=?",
            (wallet,start,end))}
        db.close()
        return root,trades
    except sqlite3.DatabaseError:
        raise EvidenceGap("LOCAL_LEDGER_QUERY_FAILED") from None


def query_referenced_accounts(rpc,inventory,start,end,root_sigs,wallet):
    joined={}
    account_counts={}
    for addr in sorted(inventory):
        try:
            rows=solana_signatures(rpc,addr,start,end)
        except (IncompleteWindow,OSError,ValueError,TimeoutError) as exc:
            raise AuditStageError(
                "TOKEN_ACCOUNT_SIGNATURES",safe_failure_code(exc),
                {"accounts_completed":len(account_counts),"accounts_total":len(inventory)}
            ) from None
        account_counts[addr]=len(rows)
        for row in rows:
            sig=row["signature"]
            if sig not in root_sigs:
                if sig in joined and joined[sig]["slot"]!=row["slot"]:
                    raise EvidenceGap("EXTRA_SIGNATURE_SLOT_CONFLICT")
                joined[sig]=row
                if len(joined)>MAX_ADDITIONAL_TRANSACTIONS:
                    raise EvidenceGap("EXTRA_TRANSACTION_BUDGET_EXCEEDED")
    evidence=[]
    for sig,row in sorted(joined.items(),key=lambda p:(p[1]["slot"],p[0])):
        try:
            tx=rpc.call("getTransaction",[sig,{"encoding":"jsonParsed",
                "commitment":"finalized","maxSupportedTransactionVersion":1}])
            if not isinstance(tx,dict) or tx.get("slot")!=row["slot"]:
                raise EvidenceGap("EXTRA_TRANSACTION_UNAVAILABLE")
            if tx.get("meta") is None or tx.get("transaction") is None:
                raise EvidenceGap("EXTRA_TRANSACTION_METADATA_MISSING")
            f=flows(tx,wallet)
        except (EvidenceGap,IncompleteWindow,OSError,ValueError,TypeError,KeyError) as exc:
            raise AuditStageError(
                "EXTRA_TRANSACTION_DECODE",safe_failure_code(exc),
                {"extra_transactions_completed":len(evidence),"extra_transactions_total":len(joined)}
            ) from None
        evidence.append({
            "signature":sig,"slot":row["slot"],
            "block_time":row["blockTime"],
            "root_referenced":wallet in account_keys(tx),
            **f,
            "review_reason":(
                "OPPOSING_FLOW_REVIEW" if f["opposing_net_token_quote"] else
                "TOKEN_OR_QUOTE_ONLY" if not f["no_observed_token_net"] else
                "NO_OWNER_TOKEN_DELTA"),
        })
    return account_counts,evidence


def run(source_report,cache_dir,db_path,rpc_file,start,end):
    count,source_sha=stage_call("SOURCE_REPORT",read_report,source_report,WALLET,start,end)
    if cache_dir.is_symlink() or not cache_dir.is_dir():
        raise AuditStageError("ROOT_CACHE","CACHE_DIRECTORY_MISSING_OR_UNSAFE")
    local_root,local_trades=stage_call(
        "LOCAL_LEDGER",local_snapshot,db_path,WALLET,start,end
    )
    endpoints=stage_call("RPC_CONFIGURATION",configured_solana_endpoints,rpc_file)
    rpc=None
    source_rows=None
    endpoint_failures=[]
    for endpoint in endpoints:
        try:
            candidate=RPC(endpoint)
            found=solana_signatures(candidate,WALLET,start,end)
            if len(found)!=count:
                endpoint_failures.append("ROOT_SIGNATURE_COUNT_MISMATCH")
                continue
            rpc,source_rows=candidate,found
            break
        except (OSError,ValueError,TimeoutError,IncompleteWindow) as exc:
            endpoint_failures.append(safe_failure_code(exc))
    if rpc is None:
        raise AuditStageError(
            "ROOT_SIGNATURES",
            endpoint_failures[-1] if endpoint_failures else "ROOT_FINALIZED_WINDOW_UNVERIFIED",
            {"rpc_endpoints_attempted":len(endpoints)}
        )
    root_tx=stage_call(
        "ROOT_CACHE",fetch_cached_root,source_rows,SignatureCache(cache_dir),WALLET
    )
    inventory,baseline=stage_call(
        "ROOT_OWNER_INVENTORY",build_seed_inventory,root_tx,WALLET
    )
    root_sigs=set(root_tx)
    counts,extra=stage_call(
        "TOKEN_ACCOUNT_SIGNATURES",query_referenced_accounts,
        rpc,inventory,start,end,root_sigs,WALLET
    )
    return {
        "status":"OBSERVED_OWNER_ACCOUNT_WINDOW_RECONCILED",
        "wallet":WALLET,"start":start,"end":end,
        "source_report_sha256":source_sha,
        "root_rpc_signatures":len(root_sigs),
        "root_cache_decoded":len(root_tx),
        "local_root_signature_count":len(local_root),
        "root_signatures_missing_from_local":len(root_sigs-local_root),
        "local_classified_trade_signatures":len(local_trades),
        "baseline_flow_groups":{
            f"{a}:{b}":v for (a,b),v in sorted(baseline.items())},
        "observed_historical_owned_token_accounts":len(inventory),
        "current_owner_account_inventory_checked":False,
        "historical_accounts_never_mentioned_in_root_not_discoverable":True,
        "owned_account_signature_counts":counts,
        "owner_account_unique_extra_signatures":len(extra),
        "extra_opposing_flow_candidates":sum(x["opposing_net_token_quote"] for x in extra),
        "extra_transaction_details":extra,
        "raw_user_confirmed_additional_fills":0,
        "warning":"An owner token account touched in root transactions is discoverable even if since closed. Accounts never referenced by root in the window remain UNVERIFIED. Opposing net balances are only CANDIDATE evidence, not BUY/SELL; native SOL and gross transient routing need separate tx instruction review.",
        "production_db_writes":0,"emails_sent":0,"signals_changed":False,
    }


def main():
    p=argparse.ArgumentParser(description="Frank historical token-account coverage, SOL only")
    p.add_argument("--source-report",type=Path,default=Path.home()/"Documents/ChatGPT/frank-fomo-fixed-20261009-054846.json")
    p.add_argument("--cache-dir",type=Path,default=Path.home()/"Documents/ChatGPT/frank-fomo-rpc-cache")
    p.add_argument("--db",type=Path,default=Path.home()/"Documents/ChatGPT/crypto-monitor-frank-only-evidence-20261003/live-v1/forward.sqlite")
    p.add_argument("--rpc-file",type=Path,default=Path.home()/"Library/Application Support/FrankMeme/solana_rpc_urls")
    p.add_argument("--start",type=int,default=START)
    p.add_argument("--end",type=int,default=END)
    p.add_argument("--output-dir",type=Path,default=Path.home()/"Documents/ChatGPT/frank-fomo-research")
    args=p.parse_args()
    try:
        if args.start>=args.end or args.end>int(datetime.now(timezone.utc).timestamp()):
            raise AuditStageError("ARGUMENTS","WINDOW_INVALID")
        report=run(args.source_report,args.cache_dir,args.db,args.rpc_file,args.start,args.end)
        target=args.output_dir.expanduser()
        if target.is_symlink() or "live-v1" in str(target) or "FrankMeme" in str(target):
            raise EvidenceGap("OUTPUT_DIRECTORY_UNSAFE")
        target.mkdir(parents=True,exist_ok=True,mode=0o700)
        if target.stat().st_mode & 0o077:
            raise EvidenceGap("OUTPUT_PERMISSIONS_UNSAFE")
        filename="frank-native-account-gap-"+datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")+".json"
        output=target/filename
        fd=os.open(output,os.O_CREAT|os.O_WRONLY|os.O_EXCL,0o600)
        with os.fdopen(fd,"w",encoding="utf-8") as writer:
            json.dump(report,writer,indent=2,ensure_ascii=False)
        overview={key:value for key,value in report.items()
                  if key not in ("extra_transaction_details","owned_account_signature_counts")}
        overview["extra_review_sample"]=report["extra_transaction_details"][:20]
        overview["full_report"]=str(output)
        print(json.dumps(overview,ensure_ascii=False,indent=2))
        return 0
    except (EvidenceGap,IncompleteWindow,OSError,ValueError,TypeError) as exc:
        known=isinstance(exc,AuditStageError)
        stage=exc.stage if known else "REPORT_OUTPUT"
        reason=exc.code if known else safe_failure_code(exc)
        details=exc.details if known else {}
        print(json.dumps({"status":"UNVERIFIED","stage":stage,"reason":reason,
                          "diagnostics":details,
                          "production_db_writes":0,"emails_sent":0,"signals_changed":False}))
        return 2


if __name__=="__main__":
    sys.exit(main())
