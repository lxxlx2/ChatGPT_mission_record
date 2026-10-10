#!/usr/bin/env python3
"""Read-only zero-RPC instruction investigation for one Frank TWEETCRAFT BUY lead.

Uses *only* the existing finalized 173-root transaction cache, validated by
unchanged context. Does not classify a BUY as confirmed from net flows alone.
No network, new monitoring, email, trading, or production DB writes.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from mission_agent.meme.fomo_crosschain import FOMO_COSIGNER, SOL_ROUTERS, USDC
from scripts import audit_frank_native_resume as audit
from scripts.audit_frank_partial_trace import detail
from scripts.inspect_frank_solana_root_window import inspect_tx

BUY_SIGNATURE = "4sP6iSpctgnnbKsLcGRn1YvaPB7TF9EGc1A6KL4G7gGwLKdP1Jm6LfEH3fs9UhQLMFNPwJ6tmS4FaEAaGT9XCC9S"
TWEETCRAFT_MINT = "HzYCHqAN2uoHGRnL9v2ChCfFQX3bvJuJd5zu2Hd5MZQy"
EXPECTED_USDC_OUT_RAW = -6715734492
EXPECTED_TWEETCRAFT_IN_RAW = 4732220716414


def summarize(tx, signature=BUY_SIGNATURE):
    if signature != BUY_SIGNATURE:
        raise audit.ScanBlocked("NOT_PINNED_BUY_CANDIDATE")
    if not isinstance(tx, dict) or type(tx.get("slot")) is not int or type(tx.get("blockTime")) is not int:
        raise audit.ScanBlocked("BUY_TX_IDENTITY_INVALID")
    if not audit.START <= tx["blockTime"] <= audit.END:
        raise audit.ScanBlocked("BUY_TX_OUTSIDE_FIXED_WINDOW")
    if not isinstance(tx.get("meta"), dict) or tx["meta"].get("err") is not None:
        raise audit.ScanBlocked("BUY_TX_FAILED_OR_MISSING_META")
    item=inspect_tx(signature, tx, audit.WALLET)
    observed={x["mint"]:int(x["raw"]) for x in item["owned_token_deltas"]}
    if (item["category"] != "SWAP_CANDIDATE"
            or not item["wallet_signed"] or not item["fomo_cosigned"]
            or observed.get(USDC) != EXPECTED_USDC_OUT_RAW
            or observed.get(TWEETCRAFT_MINT) != EXPECTED_TWEETCRAFT_IN_RAW):
        raise audit.ScanBlocked("BUY_TX_EVIDENCE_DIFFERS_FROM_PRIOR_ROOT_AUDIT")
    raw=detail(tx)
    if not raw["tx_succeeded"] or not raw["frank_root_signed"] or not raw["fomo_cosigned"]:
        raise audit.ScanBlocked("BUY_TX_SIGNER_EVIDENCE_INVALID")
    instr=raw["instruction_sample"]
    routers=sorted(set(raw["program_ids"]).intersection(SOL_ROUTERS))
    instructions_with_token_flows=[
        x for x in instr if x.get("instruction_type") in
        ("transfer","transferChecked","mintTo","burn","closeAccount")
    ]
    raw_logs=tx["meta"].get("logMessages") or []
    if not isinstance(raw_logs, list):
        raise audit.ScanBlocked("BUY_TX_LOGS_INVALID")
    log_matches=[
        x[:250] for x in raw_logs
        if isinstance(x,str) and
        ("Instruction: Swap" in x or "Instruction: Buy" in x
         or "Instruction: Sell" in x or "Program log:" in x)
    ]
    return {
        "status":"ROOT_SIGNED_TWEETCRAFT_BUY_CANDIDATE_INSTRUCTION_REVIEW",
        "signature":signature,"slot":tx["slot"],
        "block_time":tx["blockTime"],
        "transaction_sha256":audit.digest(tx),
        "mint":TWEETCRAFT_MINT,
        "symbol_offchain_label":"TWEETCRAFT",
        "frank_signed":True,"fomo_cosigned":True,
        "fee_payer":raw["fee_payer"],
        "usdc_out_raw":str(EXPECTED_USDC_OUT_RAW),
        "tweetcraft_in_raw":str(EXPECTED_TWEETCRAFT_IN_RAW),
        "routers_detected":routers,
        "all_program_ids":raw["program_ids"],
        "instruction_count":raw["instruction_count"],
        "instruction_details_truncated":raw["instruction_details_truncated"],
        "instructions":instr,
        "token_transfer_instruction_subset":instructions_with_token_flows[:40],
        "token_transfer_instruction_subset_truncated":len(instructions_with_token_flows)>40,
        "log_matches_sample":log_matches[:35],
        "logs_truncated":len(log_matches)>35,
        "token_balance_changes":raw["token_balance_changes"],
        "token_balance_changes_truncated":raw["token_balance_changes_truncated"],
        "executable_buy_confirmed":False,
        "reason":"DEX_INSTRUCTION_OPCODE_AND_EXECUTABLE_CONSIDERATION_UNCONFIRMED",
        "rpc_attempts":0,"production_db_writes":0,
        "signals_changed":False,"emails_sent":0,
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--source-report",type=Path,default=Path.home()/"Documents/ChatGPT/frank-fomo-fixed-20261009-054846.json")
    parser.add_argument("--cache-dir",type=Path,default=Path.home()/"Documents/ChatGPT/frank-fomo-rpc-cache")
    parser.add_argument("--db",type=Path,default=Path.home()/"Documents/ChatGPT/crypto-monitor-frank-only-evidence-20261003/live-v1/forward.sqlite")
    args=parser.parse_args()
    try:
        context,root_sigs,_=audit.offline_context(args.source_report,args.cache_dir,args.db)
        if BUY_SIGNATURE not in root_sigs:
            raise audit.ScanBlocked("PINNED_BUY_NOT_IN_ROOT_WINDOW")
        records=audit.cached_root(args.cache_dir,audit.WALLET,audit.START,audit.END,len(root_sigs))
        if set(records)!=root_sigs:
            raise audit.ScanBlocked("ROOT_CACHE_SIGNATURE_MISMATCH")
        result=summarize(records[BUY_SIGNATURE])
        result["root_tx_sha256"]=context["root_tx_sha256"]
        result["source_sha256"]=context["source_sha256"]
        print(json.dumps(result,ensure_ascii=False,indent=2))
        return 0
    except Exception as exc:
        import re
        msg=str(exc)
        code=msg if re.fullmatch("[A-Z][A-Z0-9_]{3,80}",msg) else "TWEETCRAFT_OFFLINE_REVIEW_BLOCKED"
        print(json.dumps({"status":"UNVERIFIED","reason":code,
                          "rpc_attempts":0,"executable_buy_confirmed":False},ensure_ascii=False))
        return 2


if __name__=="__main__":
    raise SystemExit(main())
