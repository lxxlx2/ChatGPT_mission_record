#!/usr/bin/env python3
"""Zero-RPC evidence-first review of Frank's signed Solana token buys and Relay PAY.

Reads the immutable 173-signature fixed-window root cache and local readonly
ledger. Strictly historical research; NO production alerts, signals or trades.
Unlike the FOMO third-party distribution samples, this focuses on root-authorized
USDC outflows and same-transaction target-token receipts.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import sys

from mission_agent.meme.fomo_crosschain import USDC, solana_events
from scripts import audit_frank_native_resume as audit
from scripts.inspect_frank_solana_root_window import inspect_tx

QUOTE_MINTS={
    USDC,
    "So11111111111111111111111111111111111111112",
    "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB",
}
FOCUS_CATEGORIES={"RELAY_PAY","RELAY_PAYOUT",
                  "SWAP_CANDIDATE","OPPOSING_FLOW_UNVERIFIED"}
SAMPLE_LIMIT=25
KNOWN_RELAY_PAY="KTW6qm2yw8PJC1cqUVejnG9yfYo3UQN5Y6dJJrwXeZQfbxL2ZvbtB4aymTPbPYr9BkhJrrhtswMGUytgqF5othS"


def account_signs(tx,root):
    message=(tx.get("transaction") or {}).get("message") or {}
    keys=message.get("accountKeys")
    if not isinstance(keys,list):
        raise audit.ScanBlocked("ROOT_FOCUS_ACCOUNT_KEYS_INVALID")
    return any(isinstance(x,dict) and
               x.get("pubkey")==root and x.get("signer") is True for x in keys)


def summarize(txs,root):
    counts=Counter()
    focus=[]
    root_signed_count=0
    relay_seen=False
    for signature,tx in sorted(txs.items(),key=lambda p:(p[1]["blockTime"],p[0])):
        rec=inspect_tx(signature,tx,root)
        counts[rec["category"]]+=1
        signed=account_signs(tx,root)
        root_signed_count+=bool(signed)
        deltas=rec["owned_token_deltas"]
        usdc=[x for x in deltas if x["mint"]==USDC]
        usdc_out_raw=sum(int(x["raw"]) for x in usdc if int(x["raw"])<0)
        target_in=[x for x in deltas
                   if x["mint"] not in QUOTE_MINTS and int(x["raw"])>0]
        events=solana_events(signature,tx,root) if rec["category"] in FOCUS_CATEGORIES else []
        is_focus=(rec["category"] in FOCUS_CATEGORIES or
                  (signed and (usdc_out_raw<0 or target_in)))
        if not is_focus:
            continue
        relay_seen|=signature==KNOWN_RELAY_PAY
        focus.append({
            "signature":signature,
            "block_time":tx["blockTime"],
            "slot":tx["slot"],
            "category":rec["category"],
            "root_signed":signed,
            "fomo_cosigned":rec["fomo_cosigned"],
            "usdc_out_raw":str(usdc_out_raw),
            "usdc_out_decimals":6,
            "target_in_mints":[{"mint":x["mint"],"raw":x["raw"],
                                "decimals":x["decimals"]} for x in target_in],
            "owned_token_deltas":deltas[:20],
            "owned_deltas_truncated":len(deltas)>20,
            "relay_or_swap_events":[{
                "kind":x.get("kind"),
                "order_id":x.get("order_id"),
                "asset":x.get("asset"),
                "amount_raw":x.get("amount_raw"),
                "reason":x.get("reason"),
            } for x in events][:15],
            "trade_confirmed":False,
            "needs_instruction_level_attribution":True,
        })
    return {
        "status":"ROOT_EXECUTION_EVIDENCE_OFFLINE",
        "root_count":len(txs),
        "root_signed_count":root_signed_count,
        "category_counts":dict(sorted(counts.items())),
        "candidate_count":len(focus),
        "known_relay_pay_present":relay_seen,
        "known_relay_pay_detail":next((x for x in focus if x["signature"]==KNOWN_RELAY_PAY),None),
        "candidate_sample":focus[:SAMPLE_LIMIT],
        "candidate_sample_truncated":len(focus)>SAMPLE_LIMIT,
        "rpc_attempts":0,
        "classification":"RESEARCH_CANDIDATE_ONLY",
        "trade_coverage_complete":False,
        "production_db_writes":0,
        "signals_changed":False,
        "emails_sent":0,
    }


def main():
    parser=argparse.ArgumentParser(description="Frank 173-root zero-RPC paid-trade lead report")
    parser.add_argument("--source-report",type=Path,
                        default=Path.home()/"Documents/ChatGPT/frank-fomo-fixed-20261009-054846.json")
    parser.add_argument("--cache-dir",type=Path,
                        default=Path.home()/"Documents/ChatGPT/frank-fomo-rpc-cache")
    parser.add_argument("--db",type=Path,
                        default=Path.home()/"Documents/ChatGPT/crypto-monitor-frank-only-evidence-20261003/live-v1/forward.sqlite")
    args=parser.parse_args()
    try:
        ctx,root_sigs,local_trades=audit.offline_context(
            args.source_report,args.cache_dir,args.db)
        txs=audit.cached_root(
            args.cache_dir,audit.WALLET,audit.START,audit.END,len(root_sigs))
        if set(txs)!=root_sigs:
            raise audit.ScanBlocked("ROOT_CACHE_SIGNATURE_MISMATCH")
        output=summarize(txs,audit.WALLET)
        output["source_sha256"]=ctx["source_sha256"]
        output["root_tx_sha256"]=ctx["root_tx_sha256"]
        output["local_classified_count"]=len(local_trades)
        print(json.dumps(output,ensure_ascii=False,indent=2))
        return 0
    except (audit.ScanBlocked,Exception) as exc:
        # Never leak local filesystem paths or private RPC endpoint strings.
        code=str(exc)
        import re
        if not re.fullmatch(r"[A-Z][A-Z0-9_]{3,80}",code):
            code="ROOT_FOCUS_OFFLINE_BLOCKED"
        print(json.dumps({"status":"UNVERIFIED","reason":code,"rpc_attempts":0}))
        return 2


if __name__=="__main__":
    sys.exit(main())
