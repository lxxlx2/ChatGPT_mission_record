#!/usr/bin/env python3
"""Read-only source-difference investigation: root signatures vs owned token-account signatures.

This is a narrowly scoped historical evidence audit, not a new signal scanner.
It is specifically designed to explain why token-account transaction history and
GMGN historical activity may disagree with a root-address-only local ledger.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys

from scripts.audit_frank_fomo_crosschain import (
    RPC, IncompleteWindow, configured_solana_endpoints, solana_signatures,
)
from scripts.inspect_frank_solana_root_window import owned_deltas

ROOT = "498g1rVnFcnjBjpfw1xyqA1WvgQXUU8RWuELjxkjAayQ"
MINT = "HzYCHqAN2uoHGRnL9v2ChCfFQX3bvJuJd5zu2Hd5MZQy"
COSIGNER = "AgmLJBMDCqWynYnQiPCuj9ewsNNsBJXyzoUhD9LJzN51"
QUOTE_MINTS = {
    "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v": "USDC",
    "So11111111111111111111111111111111111111112": "WSOL",
    "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB": "USDT",
}
MINT_TOKEN_ACCOUNT_CAP = 30
TOKEN_ACCOUNT_TX_CAP = 400


def discover_current_token_accounts(rpc, wallet, mint):
    response=rpc.call("getTokenAccountsByOwner",[
        wallet, {"mint":mint}, {"encoding":"jsonParsed","commitment":"finalized"}])
    value=(response or {}).get("value")
    if not isinstance(value,list):
        raise IncompleteWindow("MINT_TOKEN_ACCOUNTS_UNAVAILABLE")
    accounts=[]
    for row in value:
        info=((((row.get("account") or {}).get("data") or {}).get("parsed") or {}).get("info") or {})
        if info.get("mint")==mint and info.get("owner")==wallet and isinstance(row.get("pubkey"),str):
            accounts.append(row["pubkey"])
    if len(accounts)>MINT_TOKEN_ACCOUNT_CAP:
        raise IncompleteWindow("MINT_TOKEN_ACCOUNT_CAP_EXCEEDED")
    return sorted(set(accounts))


def delta_evidence(tx, wallet, mint, signature, root_indexed, owner_accounts):
    meta=tx.get("meta") or {}
    message=((tx.get("transaction") or {}).get("message") or {})
    keys=message.get("accountKeys") or []
    if any(not isinstance(x,dict) or not isinstance(x.get("pubkey"),str) for x in keys):
        raise IncompleteWindow("TX_KEYS_NOT_JSON_PARSED")
    signers={x["pubkey"] for x in keys if x.get("signer") is True}
    delta_rows=owned_deltas(tx,wallet)
    target=[x for x in delta_rows if x["mint"]==mint]
    quote=[x for x in delta_rows if x["mint"] in QUOTE_MINTS]
    target_raw=sum(int(x["raw"]) for x in target)
    quote_rows=[{"asset":QUOTE_MINTS[x["mint"]],"raw":x["raw"],"decimals":x["decimals"]} for x in quote]
    signed=wallet in signers
    opposite=any(target_raw*int(x["raw"])<0 for x in quote)
    return {
        "signature":signature, "slot":tx.get("slot"),"block_time":tx.get("blockTime"),
        "root_indexed":root_indexed,
        "root_referenced":wallet in {x["pubkey"] for x in keys},
        "root_signed":signed,"fomo_cosigned":COSIGNER in signers,
        "mint_token_account_referenced":bool({x["pubkey"] for x in keys}&set(owner_accounts)),
        "success":meta.get("err") is None,
        "mint_net_raw":str(target_raw),
        "mint_decimals":target[0]["decimals"] if target else None,
        "owner_quote_net":quote_rows,
        "opposing_owned_asset_flows":opposite,
        "review_status":(
            "FAILED" if meta.get("err") is not None else
            "OPPOSING_FLOWS_REVIEW_REQUIRED" if opposite else
            "TOKEN_CHANGE_WITHOUT_OWNED_QUOTE" if target_raw else
            "NO_OWNER_MINT_DELTA"
        ),
        "trade_confirmed":False,
        "url":"https://solscan.io/tx/"+signature,
    }


def audit(rpc, wallet, mint, since, until):
    root=solana_signatures(rpc,wallet,since,until)
    root_signatures={x["signature"] for x in root}
    accounts=discover_current_token_accounts(rpc,wallet,mint)
    per_account={}
    joined={}
    for account in accounts:
        rows=solana_signatures(rpc,account,since,until)
        if len(rows)>TOKEN_ACCOUNT_TX_CAP:
            raise IncompleteWindow("MINT_ACCOUNT_SIGNATURES_EXCEED_CAP")
        per_account[account]=len(rows)
        for item in rows:
            signature=item["signature"]
            existing=joined.get(signature)
            if existing is not None and existing.get("slot") != item.get("slot"):
                raise IncompleteWindow("SIGNATURE_SLOT_CONFLICT")
            joined[signature]=item
    evidence=[]
    for sig,item in sorted(joined.items(),key=lambda x:(x[1]["slot"],x[0])):
        tx=rpc.call("getTransaction",[sig,{
            "encoding":"jsonParsed","commitment":"finalized",
            "maxSupportedTransactionVersion":1
        }])
        if not tx or tx.get("slot")!=item["slot"]:
            raise IncompleteWindow("MINT_ACCOUNT_TX_MISSING")
        evidence.append(delta_evidence(tx,wallet,mint,sig,sig in root_signatures,accounts))
    extra=[x for x in evidence if not x["root_indexed"]]
    return {
        "status":"CURRENT_TOKEN_ACCOUNT_WINDOW_RECONCILED",
        "wallet":wallet,"mint":mint,
        "start_epoch":since,"end_epoch":until,
        "root_signatures_in_window":len(root),
        "current_token_accounts":accounts,
        "historical_closed_accounts_covered":False,
        "account_signature_counts":per_account,
        "mint_account_unique_signatures":len(evidence),
        "mint_account_signatures_not_in_root_index":len(extra),
        "candidate_extra_sigs":[x["signature"] for x in extra],
        "classifications":dict(Counter(x["review_status"] for x in evidence)),
        "mint_account_transactions":evidence,
        "gmgn_independent_feed_checked":False,
        "confirmed_frank_buy_count":None,
        "warning":"This checks only CURRENT owned mint accounts. A transaction may touch a token account without an attributable swap. Never equate account-only signatures, passive receipts, or balance changes with BUY. No historical closed account coverage or GMGN activity matched.",
        "production_db_writes":0,"gmail_sent":0,"signals_changed":False,
    }


def main():
    p=argparse.ArgumentParser(description="Frank owned mint token-account window comparison (READ ONLY)")
    p.add_argument("--wallet",default=ROOT)
    p.add_argument("--mint",default=MINT)
    p.add_argument("--start",type=int,default=1791386454)
    p.add_argument("--end",type=int,default=1791472854)
    p.add_argument("--rpc-file",type=Path,default=Path.home()/"Library/Application Support/FrankMeme/solana_rpc_urls")
    p.add_argument("--output-dir",type=Path,default=Path.home()/"Documents/ChatGPT/frank-fomo-research")
    args=p.parse_args()
    try:
        if args.start>=args.end or args.end>int(datetime.now(timezone.utc).timestamp()):
            raise IncompleteWindow("INVALID_TIME_WINDOW")
        endpoints=configured_solana_endpoints(args.rpc_file)
        report=None
        for url in endpoints:
            try:
                report=audit(RPC(url),args.wallet,args.mint,args.start,args.end)
                break
            except (IncompleteWindow, OSError, TimeoutError, ValueError):
                continue
        if report is None:
            raise IncompleteWindow("SOLANA_PROVIDER_WINDOW_INCOMPLETE")
        out=args.output_dir.expanduser()
        if out.is_symlink() or "FrankMeme" in str(out) or "mission-control" in str(out):
            raise IncompleteWindow("OUTPUT_DIR_UNSAFE")
        out.mkdir(parents=True,exist_ok=True,mode=0o700)
        if out.stat().st_mode & 0o077:
            raise IncompleteWindow("OUTPUT_DIR_PERMISSIONS")
        name="frank-mint-account-compare-"+datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")+".json"
        path=out/name
        fd=os.open(path,os.O_EXCL|os.O_WRONLY|os.O_CREAT,0o600)
        with os.fdopen(fd,"w",encoding="utf-8") as f:
            json.dump(report,f,ensure_ascii=False,indent=2)
        display={k:report[k] for k in ("status","wallet","mint","root_signatures_in_window","current_token_accounts","historical_closed_accounts_covered","mint_account_unique_signatures","mint_account_signatures_not_in_root_index","classifications")}
        display["transactions"]=report["mint_account_transactions"][:25]
        display["report"]=str(path)
        print(json.dumps(display,ensure_ascii=False,indent=2))
        return 0
    except (IncompleteWindow, OSError,ValueError,TypeError) as exc:
        msg=str(exc)
        if msg not in {
            "INVALID_TIME_WINDOW","SOLANA_PROVIDER_WINDOW_INCOMPLETE",
            "OUTPUT_DIR_UNSAFE","OUTPUT_DIR_PERMISSIONS",
        }:msg="RECONCILIATION_BLOCKED"
        print(json.dumps({"status":"UNVERIFIED","reason":msg,
            "production_db_writes":0,"gmail_sent":0}))
        return 2


if __name__=="__main__":
    sys.exit(main())
