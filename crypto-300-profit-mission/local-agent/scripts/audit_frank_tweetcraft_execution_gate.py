#!/usr/bin/env python3
"""Historical zero-RPC, per-program DEX-execution evidence for Frank TWEETCRAFT.

Pin one root-signed finalized tx. Compare actual token instructions, onchain
balance changes, Solana nested program-invocation logs and official Meteora
DLMM Swap2 Anchor discriminator. Fail closed for executable trade upgrade.
No online calls, notification, wallet actions or production database writes.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from scripts import audit_frank_native_resume as audit
from scripts import audit_frank_tweetcraft_instruction_offline as previous
from mission_agent.meme.fomo_crosschain import b58decode, USDC
from scripts.audit_frank_partial_trace import detail

DLMM="LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo"
DFLOW="DF1ow4tspfHX9JwWJsAb9epbkA8hmpSEAtxXy1V27QBH"
BISONFI="BiSoNHVpsVZW2F7rx2eQ59yQwKxzU5NvBcmKshCSUypi"
ROOT_USDC_ATA="6kD22oUQrV8tVpE2hkQzkoobwCQAy2iiZcipWn8AD5jF"
ROOT_TWEET_ATA="7qujRSPgfbgiwMhBSc1znjaQoHM9jt6HQVw6TgxnLAsG"
SWAP2_DISCRIMINATOR=bytes([65,75,63,76,235,91,91,136])
INVOKE=re.compile(r"^Program ([1-9A-HJ-NP-Za-km-z]{32,44}) invoke \[(\d+)\]$")
COMPLETE=re.compile(r"^Program ([1-9A-HJ-NP-Za-km-z]{32,44}) (?:success|failed:.*)$")
LOG_INSTRUCTION=re.compile(r"^Program log: Instruction: (.+)$")


def invocation_evidence(tx):
    logs=tx.get("meta",{}).get("logMessages")
    if not isinstance(logs,list):
        return {"status":"LOGS_MISSING","malformed":True,
                "bindings":[],"seen_invoke":False}
    stack=[]
    events=[]
    invalid=False
    invokes=0
    for line in logs:
        if not isinstance(line,str):
            invalid=True
            continue
        m=INVOKE.fullmatch(line)
        if m:
            depth=int(m.group(2))
            if depth!=len(stack)+1:
                invalid=True
            stack.append(m.group(1))
            invokes+=1
            continue
        m=LOG_INSTRUCTION.fullmatch(line)
        if m and m.group(1) in ("Buy","Swap","Swap2"):
            events.append({"instruction":m.group(1),
                           "program":stack[-1] if stack else None,
                           "stack_depth":len(stack)})
            continue
        m=COMPLETE.fullmatch(line)
        if m:
            if not stack or stack[-1]!=m.group(1):
                invalid=True
            else:
                stack.pop()
            if "failed:" in line:
                invalid=True
    if stack:
        invalid=True
    return {"status":"VALID" if invokes>0 and not invalid else "UNBOUND_OR_INVALID",
            "malformed":invalid,
            "seen_invoke":invokes>0,
            "bindings":events}


def _ix_program(ix,names):
    p=ix.get("programId")
    if p is None and type(ix.get("programIdIndex")) is int:
        idx=ix["programIdIndex"]
        return names[idx] if 0<=idx<len(names) else None
    return p


def discriminator_evidence(tx):
    names=audit.account_keys(tx)
    groups=[("outer",tx["transaction"]["message"].get("instructions") or [])]
    for idx,group in enumerate(tx["meta"].get("innerInstructions") or []):
        if not isinstance(group,dict):
            raise audit.ScanBlocked("TWEET_INNER_INSTRUCTIONS_INVALID")
        groups.append(("inner:"+str(group.get("index",idx)),group.get("instructions") or []))
    matches=[]
    candidates=0
    for location,rows in groups:
        for ix in rows:
            if not isinstance(ix,dict):
                raise audit.ScanBlocked("TWEET_INSTRUCTIONS_INVALID")
            if _ix_program(ix,names)!=DLMM:
                continue
            candidates+=1
            raw=ix.get("data")
            if not isinstance(raw,str):
                continue
            try:
                data=b58decode(raw)
            except (ValueError,TypeError):
                continue
            if data[:8]==SWAP2_DISCRIMINATOR:
                matches.append({"instruction_location":location,
                                "data_length":len(data),
                                "discriminator_hex":data[:8].hex()})
    return {"dlmm_instruction_count":candidates,
            "swap2_discriminator_matched":len(matches)>0,
            "swap2_matching_instructions":matches[:8],
            "swap2_matching_instructions_truncated":len(matches)>8}


def direct_wallet_transfers(tx):
    rows=detail(tx)["instruction_sample"]
    usdc_out=[]
    target_in=[]
    for row in rows:
        p=row.get("parsed_fields") or {}
        ix=row.get("instruction_type")
        if ix not in ("transfer","transferChecked"):
            continue
        amount=(p.get("tokenAmount") or {}).get("amount") if ix=="transferChecked" else p.get("amount")
        if not isinstance(amount,str) or not amount.isdigit():
            continue
        raw=int(amount)
        if (p.get("source")==ROOT_USDC_ATA and
                p.get("authority")==audit.WALLET and
                (ix=="transfer" or p.get("mint")==USDC)):
            usdc_out.append({"destination":p.get("destination"),"raw":str(raw),
                             "decimals":6})
        if (p.get("destination")==ROOT_TWEET_ATA and
                p.get("mint")==previous.TWEETCRAFT_MINT):
            target_in.append({"source":p.get("source"),"raw":str(raw),
                              "decimals":6})
    gross=sum(int(x["raw"]) for x in usdc_out)
    acquired=sum(int(x["raw"]) for x in target_in)
    expected_out=-previous.EXPECTED_USDC_OUT_RAW
    expected_in=previous.EXPECTED_TWEETCRAFT_IN_RAW
    split=sorted(usdc_out,key=lambda z:int(z["raw"]),reverse=True)
    return {
        "usdc_outbound_instructions":split,
        "usdc_outbound_raw_total":str(gross),
        "usdc_outbound_equals_owner_delta":gross==expected_out,
        "target_inbound_instructions":target_in,
        "target_inbound_raw_total":str(acquired),
        "target_inbound_equals_owner_delta":acquired==expected_in,
        "largest_outbound_usdc_raw":split[0]["raw"] if split else None,
        "other_outbound_usdc_raw":str(sum(int(z["raw"]) for z in split[1:])),
        "other_outbound_role":"UNKNOWN_MAY_INCLUDE_FEES_NOT_PROVEN",
        "amounts_reconciled":gross==expected_out and acquired==expected_in,
        "caution":"Internal WSOL transfers are not independent Frank net purchases or spending."
    }


def gate(tx):
    prev=previous.summarize(tx)
    logs=invocation_evidence(tx)
    code=discriminator_evidence(tx)
    moves=direct_wallet_transfers(tx)
    log_swap2=any(r["program"]==DLMM and r["instruction"]=="Swap2"
                  for r in logs["bindings"])
    log_buy=any(r["instruction"]=="Buy" and r["program"] is not None
                for r in logs["bindings"])
    matched=(logs["status"]=="VALID" and log_swap2 and
             code["swap2_discriminator_matched"] and moves["amounts_reconciled"])
    result={
        "status":"CONFIRMED_ROOT_AUTHORIZED_DEX_BUY_EVIDENCE" if matched
                 else "EXECUTION_BINDING_INCOMPLETE",
        "reason":"EXACT_PROGRAM_SWAP2_AND_FUNDS_RECONCILED" if matched
                 else "NEED_LOG_PROGRAM_BINDING_OR_SWAP2_DISCRIMINATOR",
        "signature":previous.BUY_SIGNATURE,
        "transaction_sha256":audit.digest(tx),
        "block_time":tx["blockTime"],
        "mint":previous.TWEETCRAFT_MINT,
        "wallet_signed":True,"fomo_cosigned":True,
        "log_program_bindings":logs,
        "dlmm_discriminator":code,
        "buy_log_bound_to_program":log_buy,
        "meteora_swap2_log_bound":log_swap2,
        **moves,
        "onchain_buy_evidence_confirmed":matched,
        "execution_buy_not_person_pattern":True,
        "solana_mint_only":True,
        "persona_offchain_identity_verified":False,
        "trade_pnl_known":False,
        "rpc_attempts":0,"production_db_writes":0,
        "signals_changed":False,"emails_sent":0,
    }
    return result


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source-report",type=Path,default=Path.home()/"Documents/ChatGPT/frank-fomo-fixed-20261009-054846.json")
    p.add_argument("--cache-dir",type=Path,default=Path.home()/"Documents/ChatGPT/frank-fomo-rpc-cache")
    p.add_argument("--db",type=Path,default=Path.home()/"Documents/ChatGPT/crypto-monitor-frank-only-evidence-20261003/live-v1/forward.sqlite")
    args=p.parse_args()
    try:
        ctx,root_sigs,_=audit.offline_context(args.source_report,args.cache_dir,args.db)
        if previous.BUY_SIGNATURE not in root_sigs:
            raise audit.ScanBlocked("PINNED_BUY_NOT_IN_ROOT_WINDOW")
        txs=audit.cached_root(args.cache_dir,audit.WALLET,audit.START,audit.END,len(root_sigs))
        if set(txs)!=root_sigs:
            raise audit.ScanBlocked("ROOT_CACHE_SIGNATURE_MISMATCH")
        result=gate(txs[previous.BUY_SIGNATURE])
        result["root_tx_sha256"]=ctx["root_tx_sha256"]
        result["source_sha256"]=ctx["source_sha256"]
        print(json.dumps(result,ensure_ascii=False,indent=2))
        return 0 if result["onchain_buy_evidence_confirmed"] else 2
    except Exception as exc:
        msg=str(exc)
        reason=msg if re.fullmatch(r"[A-Z][A-Z0-9_]{3,80}",msg) else "ROOT_TWEET_SWAP2_GATE_BLOCKED"
        print(json.dumps({"status":"UNVERIFIED","reason":reason,
                          "rpc_attempts":0,"onchain_buy_evidence_confirmed":False}))
        return 2


if __name__=="__main__":
    raise SystemExit(main())
