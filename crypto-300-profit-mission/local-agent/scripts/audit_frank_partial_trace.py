#!/usr/bin/env python3
"""Read-only, hash-attested detail trace for the THREE saved Frank USDC samples.

Not a trade classifier. Never modifies the live DB, wallet, signals or email.
Prior decoded receipts must exist. Each RPC call is explicit, single-attempt and
at least 5s apart. Reruns reuse immutable trace receipts with ZERO new RPCs.
"""
from __future__ import annotations

import argparse
import fcntl
import json
import os
from pathlib import Path
import time

from scripts import audit_frank_native_resume as audit
from mission_agent.meme.fomo_crosschain import FOMO_COSIGNER, SOL_RELAY_SOLVER

DEFAULT_ACCOUNT="6kD22oUQrV8tVpE2hkQzkoobwCQAy2iiZcipWn8AD5jF"
MAX_TRACE=3
MIN_SPACING=5.0


def instruction_rows(tx, names):
    instructions=list((tx["transaction"]["message"].get("instructions") or []))
    for group in (tx["meta"].get("innerInstructions") or []):
        if not isinstance(group,dict):
            raise audit.ScanBlocked("TRACE_INSTRUCTIONS_INVALID")
        instructions.extend(group.get("instructions") or [])
    rows=[]
    for ix in instructions:
        if not isinstance(ix,dict):
            raise audit.ScanBlocked("TRACE_INSTRUCTIONS_INVALID")
        program=ix.get("programId")
        if program is None and type(ix.get("programIdIndex")) is int:
            index=ix["programIdIndex"]
            program=names[index] if 0<=index<len(names) else None
        if not isinstance(program,str):
            raise audit.ScanBlocked("TRACE_INSTRUCTIONS_INVALID")
        parsed=ix.get("parsed")
        kind=(parsed.get("type") if isinstance(parsed,dict) else None)
        info=(parsed.get("info") if isinstance(parsed,dict) else None)
        allowed=("source","destination","authority","owner","mint","amount",
                 "tokenAmount","lamports","account","wallet","signer")
        details={k:v for k,v in info.items() if k in allowed
                 and isinstance(v,(str,int,dict))} if isinstance(info,dict) else {}
        memo=(parsed if isinstance(parsed,str) else
              info.get("memo") if isinstance(info,dict) else None)
        rows.append({"program":program,"instruction_type":kind,
                     "parsed_fields":details,
                     "memo":memo[:256] if isinstance(memo,str) else None})
    return {
        "instruction_count":len(rows),
        "program_ids":sorted({x["program"] for x in rows}),
        "instruction_sample":rows[:60],
        "instruction_details_truncated":len(rows)>60,
    }


def balance_changes(tx,names):
    meta=tx["meta"]
    vectors={}
    for phase in ("preTokenBalances","postTokenBalances"):
        rows=meta.get(phase)
        if not isinstance(rows,list):
            raise audit.ScanBlocked("TRACE_TOKEN_BALANCES_MISSING")
        for row in rows:
            if not isinstance(row,dict) or type(row.get("accountIndex")) is not int:
                raise audit.ScanBlocked("TRACE_BALANCE_ROW_INVALID")
            idx=row["accountIndex"]
            if not 0<=idx<len(names):
                raise audit.ScanBlocked("TRACE_BALANCE_ROW_INVALID")
            mint,owner=row.get("mint"),row.get("owner")
            info=row.get("uiTokenAmount") or {}
            if not isinstance(mint,str) or not isinstance(info,dict):
                raise audit.ScanBlocked("TRACE_BALANCE_ROW_INVALID")
            try:
                amount=int(info["amount"]);decimals=int(info["decimals"])
            except (ValueError,KeyError,TypeError):
                raise audit.ScanBlocked("TRACE_BALANCE_ROW_INVALID") from None
            if amount<0 or decimals<0 or decimals>18:
                raise audit.ScanBlocked("TRACE_BALANCE_ROW_INVALID")
            key=(idx,mint,owner,decimals)
            target=vectors.setdefault(key,{})
            if phase in target:
                raise audit.ScanBlocked("TRACE_BALANCE_DUPLICATE")
            target[phase]=amount
    result=[]
    for (idx,mint,owner,decimals),phases in sorted(vectors.items(),key=lambda x:(x[0][1],x[0][0])):
        change=phases.get("postTokenBalances",0)-phases.get("preTokenBalances",0)
        if change:
            result.append({
                "token_account":names[idx],"mint":mint,"owner":owner,
                "owner_is_frank":owner==audit.WALLET,
                "change_raw":str(change),"decimals":decimals,
            })
    return {
        "token_balance_change_count":len(result),
        "token_balance_changes":result[:80],
        "token_balance_changes_truncated":len(result)>80,
    }


def detail(tx):
    names=audit.account_keys(tx)
    signers=[k["pubkey"] for k in tx["transaction"]["message"]["accountKeys"]
             if k.get("signer") is True]
    result={
        "slot":tx["slot"],"block_time":tx["blockTime"],
        "tx_succeeded":tx["meta"].get("err") is None,
        "fee_payer":names[0] if names else None,
        "frank_root_in_account_keys":audit.WALLET in names,
        "frank_root_signed":audit.WALLET in signers,
        "fomo_cosigned":FOMO_COSIGNER in signers,
        "relay_solver_signed":SOL_RELAY_SOLVER in signers,
        "signers":signers[:20],
        "signers_truncated":len(signers)>20,
    }
    result.update(balance_changes(tx,names))
    result.update(instruction_rows(tx,names))
    result["finding"]="INSTRUCTION_EVIDENCE_ONLY_NOT_PROVEN_FRANK_TRADE"
    return result


def trace(store, root_sigs, account, endpoint, budget):
    candidates=audit.partial_decode_sample(store,root_sigs,account)
    output=[]
    count=0
    last=None
    for row in candidates:
        old=store.receipt(row["signature"])
        if not old:
            raise audit.ScanBlocked("TRACE_REQUIRES_EXISTING_DECODE_RECEIPT")
        trace_path=store.root/("trace-"+row["signature"]+".json")
        cached=store._read(trace_path)
        if cached is not None:
            if (cached.get("context")!=store.key
                    or cached.get("signature")!=row["signature"]
                    or cached.get("tx_sha256")!=old.get("tx_sha256")):
                raise audit.ScanBlocked("TRACE_CACHE_CONTEXT_MISMATCH")
            output.append(cached)
            continue
        if count>=budget:
            break
        if last is not None:
            delay=MIN_SPACING-(time.monotonic()-last)
            if delay>0:
                time.sleep(delay)
        last=time.monotonic()
        count+=1
        tx=audit.one_rpc(endpoint,"getTransaction",[
            row["signature"],{"encoding":"jsonParsed","commitment":"finalized",
                               "maxSupportedTransactionVersion":1}])
        if (not isinstance(tx,dict) or tx.get("slot")!=row["slot"]
                or tx.get("blockTime")!=row["blockTime"]):
            raise audit.ScanBlocked("TRACE_TRANSACTION_MISMATCH")
        if audit.digest(tx)!=old.get("tx_sha256"):
            raise audit.ScanBlocked("TRACE_TRANSACTION_HASH_MISMATCH")
        summary={
            "context":store.key,"signature":row["signature"],
            "tx_sha256":old["tx_sha256"],
            **detail(tx),
        }
        store._write(trace_path,summary)
        output.append(summary)
    return {"status":"TRACE_REVIEW_ONLY",
            "rpc_attempts":count,
            "sample_candidates":len(candidates),
            "sample_traces_saved_or_reused":len(output),
            "all_sample_traces_complete":len(output)==len(candidates),
            "traces":output,
            "production_db_writes":0,"emails_sent":0,
            "signals_changed":False,"trade_confirmed":False}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--allow-network",action="store_true")
    parser.add_argument("--account",default=DEFAULT_ACCOUNT)
    parser.add_argument("--max-rpc-calls",type=int,default=3)
    parser.add_argument("--checkpoint-dir",type=Path,default=audit.CHECKPOINT_DIR)
    parser.add_argument("--source-report",type=Path,
                        default=Path.home()/"Documents/ChatGPT/frank-fomo-fixed-20261009-054846.json")
    parser.add_argument("--cache-dir",type=Path,
                        default=Path.home()/"Documents/ChatGPT/frank-fomo-rpc-cache")
    parser.add_argument("--db",type=Path,
                        default=Path.home()/"Documents/ChatGPT/crypto-monitor-frank-only-evidence-20261003/live-v1/forward.sqlite")
    parser.add_argument("--rpc-file",type=Path,
                        default=Path.home()/"Library/Application Support/FrankMeme/solana_rpc_urls")
    args=parser.parse_args()
    try:
        if not args.allow_network:
            raise audit.ScanBlocked("EXPLICIT_NETWORK_PERMISSION_REQUIRED")
        if args.account!=DEFAULT_ACCOUNT:
            raise audit.ScanBlocked("TRACE_ONLY_FROZEN_USDC_ACCOUNT")
        if not 1<=args.max_rpc_calls<=MAX_TRACE:
            raise audit.ScanBlocked("TRACE_RPC_BUDGET_INVALID")
        ctx,roots,_=audit.offline_context(args.source_report,args.cache_dir,args.db)
        store=audit.Checkpoints(args.checkpoint_dir,ctx,create=False)
        if not store.manifest.is_file():
            raise audit.ScanBlocked("TRACE_EXISTING_CHECKPOINT_REQUIRED")
        urls=audit.configured_solana_endpoints(args.rpc_file)
        if not urls:
            raise audit.ScanBlocked("RPC_CONFIG_EMPTY")
        lock=store.root/".run.lock"
        if lock.is_symlink():
            raise audit.ScanBlocked("CHECKPOINT_LOCK_SYMLINK")
        fd=os.open(lock,os.O_CREAT|os.O_RDWR,0o600)
        try:
            fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
            output=trace(store,roots,args.account,urls[0],args.max_rpc_calls)
        except BlockingIOError:
            raise audit.ScanBlocked("CONCURRENT_RESEARCH_SCAN") from None
        finally:
            os.close(fd)
        print(json.dumps(output,ensure_ascii=False,indent=2))
        return 0 if output["all_sample_traces_complete"] else 2
    except (audit.ScanBlocked,OSError,KeyError,ValueError,TypeError) as exc:
        raw=str(exc)
        import re
        code=raw if re.fullmatch("[A-Z][A-Z0-9_]{3,80}",raw) else "TRACE_RESEARCH_BLOCKED"
        print(json.dumps({"status":"UNVERIFIED","reason":code,
                          "rpc_attempts":"UNKNOWN_ON_ERROR",
                          "production_db_writes":0,"trade_confirmed":False}))
        return 2


if __name__=="__main__":
    raise SystemExit(main())
