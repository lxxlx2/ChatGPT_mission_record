#!/usr/bin/env python3
"""Frank root-window evidence summary, strictly offline.

Uses a previously completed fixed-window root audit, finalized transaction
cache and a read-only Mission ledger. Never initializes RPC or sends network
requests. Does not equate balanced net token flows with executed trades.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import sys

from mission_agent.meme.fomo_crosschain import SOL_CASH_WALLET as WALLET, USDC
from scripts.audit_frank_native_owner_coverage import (
    START, END, EvidenceGap, build_seed_inventory, local_snapshot,
    flows, read_report,
)
from scripts.inspect_frank_solana_root_window import EvidenceError

SIG = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{64,100}$")
MAX_CACHED_TX_BYTES = 8_000_000
MAX_ROOT_CACHE_FILES = 4000


def cached_root(cache_dir: Path, wallet: str, start: int, end: int, expected: int):
    directory=cache_dir / wallet
    if cache_dir.is_symlink() or directory.is_symlink() or not directory.is_dir():
        raise EvidenceGap("ROOT_CACHE_DIRECTORY_MISSING_OR_UNSAFE")
    files=list(directory.iterdir())
    if len(files)>MAX_ROOT_CACHE_FILES:
        raise EvidenceGap("ROOT_CACHE_FILE_BUDGET_EXCEEDED")
    result={}
    for file in files:
        if file.suffix!=".json":
            continue
        if file.is_symlink() or not file.is_file():
            raise EvidenceGap("ROOT_CACHE_ENTRY_UNSAFE")
        if not SIG.fullmatch(file.stem):
            raise EvidenceGap("ROOT_CACHE_FILENAME_INVALID")
        fs=file.stat()
        if fs.st_mode & 0o077 or fs.st_size>MAX_CACHED_TX_BYTES:
            raise EvidenceGap("ROOT_CACHE_ENTRY_PERMISSIONS_OR_SIZE")
        try:
            obj=json.loads(file.read_text(encoding="utf-8"))
        except (OSError,ValueError,UnicodeError):
            raise EvidenceGap("ROOT_CACHE_ENTRY_INVALID") from None
        sig=obj.get("signature") if isinstance(obj,dict) else None
        slot=obj.get("slot") if isinstance(obj,dict) else None
        tx=obj.get("tx") if isinstance(obj,dict) else None
        if sig!=file.stem or type(slot) is not int or not isinstance(tx,dict):
            raise EvidenceGap("ROOT_CACHE_IDENTITY_MISMATCH")
        if tx.get("slot")!=slot or type(tx.get("blockTime")) is not int:
            raise EvidenceGap("ROOT_CACHE_TRANSACTION_INVALID")
        if not isinstance((tx.get("transaction") or {}).get("message"),dict):
            raise EvidenceGap("ROOT_CACHE_MESSAGE_MISSING")
        at=tx["blockTime"]
        if start<=at<=end:
            if sig in result:
                raise EvidenceGap("ROOT_CACHE_DUPLICATE_SIGNATURE")
            result[sig]=tx
    if len(result)!=expected:
        raise EvidenceGap("ROOT_CACHE_WINDOW_COUNT_MISMATCH")
    return result


def build_offline_report(source_report, cache_dir, db_path, start, end):
    source_count,source_hash=read_report(source_report,WALLET,start,end)
    transactions=cached_root(cache_dir,WALLET,start,end,source_count)
    local_root,local_trades=local_snapshot(db_path,WALLET,start,end)
    inventory,baseline=build_seed_inventory(transactions,WALLET)
    candidate_rows=[]
    for signature,tx in transactions.items():
        evidence=flows(tx,WALLET)
        if evidence["opposing_net_token_quote"]:
            candidate_rows.append({
                "signature":signature,
                "slot":tx["slot"],"block_time":tx["blockTime"],
                "signed_by_root":evidence["signed_by_root"],
                "fomo_cosigned":evidence["fomo_cosigned"],
                "has_known_router":evidence["has_known_router"],
                "target_mints":evidence["target_mints"],
                "quote_mints":evidence["quote_mints"],
                "already_classified_by_mission":signature in local_trades,
                "trade_confirmed":False,
            })
    candidate_rows.sort(key=lambda x:(x["block_time"],x["slot"],x["signature"]))
    mint_to_accounts=Counter(inventory.values())
    return {
        "status":"OFFLINE_ROOT_CACHE_RECONCILED_SCOPE_LIMITED",
        "wallet":WALLET,"start":start,"end":end,
        "source_report_sha256":source_hash,
        "cached_root_transaction_count":len(transactions),
        "source_report_completed_root_count":source_count,
        "local_root_signature_count":len(local_root),
        "cached_root_not_in_local_ledger":sorted(set(transactions)-local_root),
        "local_ledger_not_in_cached_root":sorted(local_root-set(transactions)),
        "local_classified_signature_count":len(local_trades),
        "owned_accounts_observed_in_cached_root":len(inventory),
        "observed_accounts_by_mint":dict(sorted(mint_to_accounts.items())),
        "baseline_net_flow_groups":{
            f"{a}:{b}":v for (a,b),v in sorted(baseline.items())
        },
        "root_opposing_flow_candidate_count":len(candidate_rows),
        "root_opposing_flow_candidates":candidate_rows,
        "token_account_signature_coverage_checked":False,
        "historical_unreferenced_accounts_checked":False,
        "can_conclude_complete_frank_trades":False,
        "rpc_requests":0,
        "external_indexer_requests":0,
        "signals_changed":False,"production_db_writes":0,"emails_sent":0,
        "warning":"Verified only a count-matched local cache against the earlier root report; no new RPC attestation, token-account history, economic trade confirmation or complete Frank trading coverage. All opposing net flows remain investigation candidates.",
    }


def main():
    parser=argparse.ArgumentParser(description="Read only cached Frank onchain evidence with ZERO RPC")
    parser.add_argument("--source-report",type=Path,default=Path.home()/"Documents/ChatGPT/frank-fomo-fixed-20261009-054846.json")
    parser.add_argument("--cache-dir",type=Path,default=Path.home()/"Documents/ChatGPT/frank-fomo-rpc-cache")
    parser.add_argument("--db",type=Path,default=Path.home()/"Documents/ChatGPT/crypto-monitor-frank-only-evidence-20261003/live-v1/forward.sqlite")
    parser.add_argument("--output-dir",type=Path,default=Path.home()/"Documents/ChatGPT/frank-fomo-research")
    args=parser.parse_args()
    try:
        body=build_offline_report(args.source_report,args.cache_dir,args.db,START,END)
        out=args.output_dir.expanduser()
        if out.is_symlink() or "live-v1" in str(out) or "FrankMeme" in str(out):
            raise EvidenceGap("OUTPUT_DIRECTORY_UNSAFE")
        out.mkdir(parents=True,mode=0o700,exist_ok=True)
        if out.stat().st_mode & 0o077:
            raise EvidenceGap("OUTPUT_DIRECTORY_PERMISSIONS")
        path=out/("frank-root-offline-"+datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")+".json")
        fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        with os.fdopen(fd,"w",encoding="utf-8") as writer:
            json.dump(body,writer,indent=2,ensure_ascii=False)
        output={k:v for k,v in body.items() if k not in ("root_opposing_flow_candidates","observed_accounts_by_mint")}
        output["candidate_sample"]=body["root_opposing_flow_candidates"][:25]
        output["account_mints"]=body["observed_accounts_by_mint"]
        output["full_report"]=str(path)
        print(json.dumps(output,ensure_ascii=False,indent=2))
        return 0
    except (EvidenceGap,EvidenceError,OSError,TypeError,ValueError,KeyError) as exc:
        code=str(exc)
        if not re.fullmatch(r"[A-Z][A-Z0-9_]{3,80}",code):
            code="OFFLINE_EVIDENCE_UNAVAILABLE"
        print(json.dumps({"status":"UNVERIFIED","reason":code,
            "rpc_requests":0,"production_db_writes":0,"emails_sent":0},ensure_ascii=False))
        return 2


if __name__=="__main__":
    sys.exit(main())
