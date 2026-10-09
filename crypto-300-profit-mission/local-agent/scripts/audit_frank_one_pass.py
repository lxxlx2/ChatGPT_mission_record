#!/usr/bin/env python3
"""One-pass, research-only Frank Solana verification; saved checkpoints, no signals.

First validates the immutable 173-root cache and pinned TWEETCRAFT buy locally.
Then (only with --allow-network) walks ONLY its observed owner token account,
from newest signatures to the buy timestamp, and decodes newer transactions.
No cross-wallet discovery, retries, production DB writes, email, or trading.
A 429/budget limit saves partial results and cannot be read as a no-sale result.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import time

from scripts import audit_frank_native_resume as audit
from scripts import audit_frank_tweetcraft_execution_gate as buygate
from scripts import audit_frank_tweetcraft_instruction_offline as fixed
from scripts.audit_frank_partial_trace import detail

ROOT=audit.WALLET
TARGET=fixed.TWEETCRAFT_MINT
ATA=buygate.ROOT_TWEET_ATA
BUY_TIME=1791423976
BUY_SLOT=454400785
CAP_PAGES=4
CAP_SIGNATURES=1000
CAP_DECODE=60
MAX_CALLS=32
MIN_SPACING=5.0
WSOL="So11111111111111111111111111111111111111112"
ROOT_DIR=Path.home()/"Documents/ChatGPT/frank-fomo-research/tweetcraft-lifecycle-v1"


def initial_state(store):
    existing=store._read(store.root/"history.json")
    if existing is None:
        return {"context":store.key,"account":ATA,"buy_signature":fixed.BUY_SIGNATURE,
                "status":"PENDING","before":None,"pages":0,"signatures":[]}
    if (existing.get("context")!=store.key or
            existing.get("account")!=ATA or
            existing.get("buy_signature")!=fixed.BUY_SIGNATURE or
            existing.get("status") not in ("PENDING","ACTIVE","COMPLETE","CAPPED")):
        raise audit.ScanBlocked("LIFECYCLE_HISTORY_CONTEXT_INVALID")
    rows=existing.get("signatures")
    if (not isinstance(rows,list) or len(rows)>CAP_SIGNATURES or
            type(existing.get("pages")) is not int or
            not 0<=existing["pages"]<=CAP_PAGES or
            len(rows)>existing["pages"]*audit.PAGE_SIZE):
        raise audit.ScanBlocked("LIFECYCLE_HISTORY_BUDGET_INVALID")
    if any(not isinstance(r,dict) or
           not isinstance(r.get("signature"),str) or
           not audit.SIGNATURE_RE.fullmatch(r["signature"]) or
           type(r.get("blockTime")) is not int or
           type(r.get("slot")) is not int or
           r["blockTime"]<BUY_TIME for r in rows):
        raise audit.ScanBlocked("LIFECYCLE_HISTORY_ROWS_INVALID")
    if len({r["signature"] for r in rows})!=len(rows):
        raise audit.ScanBlocked("LIFECYCLE_HISTORY_DUPLICATES")
    if any(a["blockTime"]<b["blockTime"] for a,b in zip(rows,rows[1:])):
        raise audit.ScanBlocked("LIFECYCLE_HISTORY_ORDER_INVALID")
    if existing["pages"] and not existing.get("before"):
        raise audit.ScanBlocked("LIFECYCLE_CURSOR_MISSING")
    return existing


def advance(state,page):
    if not isinstance(page,list) or len(page)>audit.PAGE_SIZE:
        raise audit.ScanBlocked("LIFECYCLE_PAGE_INVALID")
    next_state={**state,"signatures":list(state["signatures"]),"pages":state["pages"]+1}
    seen={r["signature"] for r in state["signatures"]}
    prev=state.get("last_page_oldest_block_time")
    past_buy=False
    for item in page:
        if (not isinstance(item,dict) or
                not isinstance(item.get("signature"),str) or
                not audit.SIGNATURE_RE.fullmatch(item["signature"]) or
                type(item.get("blockTime")) is not int or
                type(item.get("slot")) is not int):
            raise audit.ScanBlocked("LIFECYCLE_PAGE_ROW_INVALID")
        if prev is not None and item["blockTime"]>prev:
            raise audit.ScanBlocked("LIFECYCLE_PAGE_TIME_REVERSED")
        prev=item["blockTime"]
        # Preserve later instructions in the same second but higher slots.
        if (item["blockTime"]<BUY_TIME or
                (item["blockTime"]==BUY_TIME and item["slot"]<=BUY_SLOT)):
            past_buy=True
            continue
        if item["signature"] in seen:
            raise audit.ScanBlocked("LIFECYCLE_DUPLICATE_SIGNATURE")
        seen.add(item["signature"])
        if len(next_state["signatures"])<CAP_SIGNATURES:
            next_state["signatures"].append({
                "signature":item["signature"],"slot":item["slot"],
                "blockTime":item["blockTime"]})
        else:
            next_state["status"]="CAPPED"
    if state.get("before") and page and page[-1]["signature"]==state["before"]:
        raise audit.ScanBlocked("LIFECYCLE_CURSOR_STALLED")
    next_state["before"]=page[-1]["signature"] if page else state.get("before")
    if page:
        next_state["last_page_oldest_block_time"]=page[-1]["blockTime"]
    if next_state.get("status")=="CAPPED":
        pass
    elif past_buy or len(page)<audit.PAGE_SIZE:
        next_state["status"]="COMPLETE"
    elif next_state["pages"]>=CAP_PAGES or len(next_state["signatures"])>=CAP_SIGNATURES:
        next_state["status"]="CAPPED"
    else:
        next_state["status"]="ACTIVE"
    return next_state


def classify(row,tx):
    if (not isinstance(tx,dict) or tx.get("slot")!=row["slot"]
            or tx.get("blockTime")!=row["blockTime"] or
            not isinstance(tx.get("meta"),dict)):
        raise audit.ScanBlocked("LIFECYCLE_TRANSACTION_INCONSISTENT")
    if (tx["meta"].get("err") is not None):
        return {"signature":row["signature"],"block_time":row["blockTime"],
                "status":"FAILED_ONCHAIN","token_delta_raw":"0",
                "usdc_delta_raw":"0","wsol_delta_raw":"0",
                "frank_signed":False,"fomo_cosigned":False,
                "classification":"NOT_AN_EXECUTED_TRADE"}
    raw=detail(tx)
    mint_totals={}
    for change in raw["token_balance_changes"]:
        if change["owner_is_frank"]:
            key=change["mint"]
            mint_totals[key]=mint_totals.get(key,0)+int(change["change_raw"])
    token=mint_totals.get(TARGET,0)
    usdc=mint_totals.get(buygate.USDC,0)
    wsol=mint_totals.get(WSOL,0)
    if token<0 and (usdc>0 or wsol>0):
        classification="OPPOSING_FLOW_SELL_CANDIDATE"
    elif token<0:
        classification="TOKEN_OUTFLOW_NOT_PROVEN_SELL"
    elif token>0 and (usdc<0 or wsol<0):
        classification="ADDITIONAL_BUY_CANDIDATE"
    elif token>0:
        classification="TOKEN_RECEIPT_COST_UNKNOWN"
    else:
        classification="NO_TARGET_NET_FLOW"
    return {"signature":row["signature"],"block_time":row["blockTime"],
            "slot":row["slot"],"status":"OBSERVED_SUCCESS",
            "token_delta_raw":str(token),
            "usdc_delta_raw":str(usdc),
            "wsol_delta_raw":str(wsol),
            "frank_signed":raw["frank_root_signed"],
            "fomo_cosigned":raw["fomo_cosigned"],
            "fee_payer":raw["fee_payer"],
            "program_ids":raw["program_ids"],
            "classification":classification,
            "trade_confirmed":False}


def run(network, budget, source, cache, db, rpc_file, checkpoint_root):
    ctx,root_sigs,_=audit.offline_context(source,cache,db)
    if fixed.BUY_SIGNATURE not in root_sigs:
        raise audit.ScanBlocked("PINNED_BUY_NOT_IN_ROOT_WINDOW")
    root_txs=audit.cached_root(cache,ROOT,audit.START,audit.END,len(root_sigs))
    if set(root_txs)!=root_sigs:
        raise audit.ScanBlocked("ROOT_CACHE_SET_MISMATCH")
    buy=buygate.gate(root_txs[fixed.BUY_SIGNATURE])
    if not buy["onchain_buy_evidence_confirmed"]:
        raise audit.ScanBlocked("PINNED_BUY_GATE_NOT_CONFIRMED")
    store=audit.Checkpoints(checkpoint_root,
         {"version":1,"mode":"TWEETCRAFT_AFTER_BUY","wallet":ROOT,
          "ata":ATA,"mint":TARGET,"buy_tx_sha256":buy["transaction_sha256"],
          "source_sha256":ctx["source_sha256"],
          "root_tx_sha256":ctx["root_tx_sha256"],
          "start":BUY_TIME,"pages_limit":CAP_PAGES,
          "tx_limit":CAP_DECODE,"signatures_limit":CAP_SIGNATURES},
         create=True)
    state=initial_state(store)
    endpoint=None
    if network:
        urls=audit.configured_solana_endpoints(rpc_file)
        if not urls:
            raise audit.ScanBlocked("RPC_CONFIG_EMPTY")
        endpoint=urls[0]
    used=0
    last=None
    stop=None
    def call(method,params):
        nonlocal used,last
        if not network:
            raise audit.ScanBlocked("EXPLICIT_NETWORK_PERMISSION_REQUIRED")
        if used>=budget:
            raise audit.ScanBlocked("REQUEST_BUDGET_EXHAUSTED")
        if last is not None:
            wait=MIN_SPACING-(time.monotonic()-last)
            if wait>0: time.sleep(wait)
        last=time.monotonic()
        used+=1
        return audit.one_rpc(endpoint,method,params)
    lockfile=store.root/".run.lock"
    if lockfile.is_symlink():
        raise audit.ScanBlocked("LIFECYCLE_LOCK_UNSAFE")
    fd=os.open(lockfile,os.O_CREAT|os.O_RDWR,0o600)
    try:
        fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        while state["status"] not in ("COMPLETE","CAPPED"):
            if not network:
                stop="OFFLINE_HISTORY_NOT_COMPLETE"
                break
            if used>=budget:
                stop="REQUEST_BUDGET_EXHAUSTED"
                break
            opts={"limit":audit.PAGE_SIZE,"commitment":"finalized"}
            if state["before"]: opts["before"]=state["before"]
            try:
                page=call("getSignaturesForAddress",[ATA,opts])
                state=advance(state,page)
                store._write(store.root/"history.json",state)
            except audit.ScanBlocked as exc:
                stop=exc.code
                break
        rows=[r for r in reversed(state["signatures"])
              if r["signature"]!=fixed.BUY_SIGNATURE]
        rows=rows[:CAP_DECODE]
        matches=[]
        for row in rows:
            path=store.root/("lifecycle-tx-"+row["signature"]+".json")
            cached=store._read(path)
            if cached:
                if (cached.get("context")!=store.key or
                    cached.get("signature")!=row["signature"] or
                    cached.get("slot")!=row["slot"]):
                    raise audit.ScanBlocked("LIFECYCLE_RECEIPT_MISMATCH")
                item=cached["finding"]
                matches.append(item)
                continue
            if not network:
                if stop is None: stop="OFFLINE_RECEIPTS_PENDING"
                break
            if used>=budget:
                stop="REQUEST_BUDGET_EXHAUSTED"
                break
            try:
                tx=call("getTransaction",[row["signature"],
                      {"encoding":"jsonParsed","commitment":"finalized",
                       "maxSupportedTransactionVersion":1}])
                item=classify(row,tx)
                store._write(path,{"context":store.key,"signature":row["signature"],
                                 "slot":row["slot"],"tx_sha256":audit.digest(tx),
                                 "finding":item})
                matches.append(item)
            except audit.ScanBlocked as exc:
                stop=exc.code
                break
    except BlockingIOError:
        raise audit.ScanBlocked("LIFECYCLE_CONCURRENT_RUN") from None
    finally:
        os.close(fd)
    fully=(state["status"]=="COMPLETE" and
            len(state["signatures"])<=CAP_DECODE and
            len(matches)==len([r for r in state["signatures"]
                               if r["signature"]!=fixed.BUY_SIGNATURE]))
    last_match=next((x for x in matches if int(x.get("token_delta_raw","0"))<0),None)
    return {
      "status":"HISTORICAL_ROOT_BUY_CONFIRMED_LIFECYCLE_REVIEW",
      "confirmed_buy":{
          "signature":fixed.BUY_SIGNATURE,
          "block_time":BUY_TIME,
          "mint":TARGET,"quantity_tokens":"4732220.716414",
          "total_owner_usdc_cost":"6715.734492",
          "largest_usdc_route_leg":"6686.529208",
          "other_usdc_outbound":"29.205284",
          "dex_buy_evidence_confirmed":True,
          "profit_verified":False},
      "lifecycle_account":ATA,
      "history_status":state["status"],"history_pages":state["pages"],
      "after_buy_signatures_observed":len(state["signatures"]),
      "after_buy_transactions_decoded":len(matches),
      "lifecycle_evidence_complete_for_this_account":fully,
      "historical_closed_other_accounts_unverified":True,
      "person_wallet_attribution_cryptographically_verified":False,
      "sell_or_outflow_candidates":[x for x in matches
                                   if x["classification"] in
                                   ("OPPOSING_FLOW_SELL_CANDIDATE",
                                    "TOKEN_OUTFLOW_NOT_PROVEN_SELL")][:20],
      "candidate_count":sum(x["classification"] in
                                   ("OPPOSING_FLOW_SELL_CANDIDATE",
                                    "TOKEN_OUTFLOW_NOT_PROVEN_SELL") for x in matches),
      "findings_sample":matches[:60],
      "realized_pnl":"UNVERIFIED",
      "person_pattern":"OBSERVE_ONLY",
      "production_trading":"NO_GO",
      "stop_reason":stop,
      "rpc_attempts":used,
      "rpc_max_budget":budget,
      "production_db_writes":0,"signals_changed":False,"emails_sent":0,
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--allow-network",action="store_true")
    p.add_argument("--max-rpc-calls",type=int,default=24)
    p.add_argument("--source-report",type=Path,default=Path.home()/"Documents/ChatGPT/frank-fomo-fixed-20261009-054846.json")
    p.add_argument("--cache-dir",type=Path,default=Path.home()/"Documents/ChatGPT/frank-fomo-rpc-cache")
    p.add_argument("--db",type=Path,default=Path.home()/"Documents/ChatGPT/crypto-monitor-frank-only-evidence-20261003/live-v1/forward.sqlite")
    p.add_argument("--rpc-file",type=Path,default=Path.home()/"Library/Application Support/FrankMeme/solana_rpc_urls")
    p.add_argument("--checkpoint-dir",type=Path,default=ROOT_DIR)
    args=p.parse_args()
    try:
        if type(args.max_rpc_calls) is not int or not 0<=args.max_rpc_calls<=MAX_CALLS:
            raise audit.ScanBlocked("ONE_PASS_RPC_BUDGET_INVALID")
        if args.allow_network and args.max_rpc_calls==0:
            raise audit.ScanBlocked("ONE_PASS_NETWORK_ZERO_BUDGET")
        result=run(args.allow_network,args.max_rpc_calls,args.source_report,
                   args.cache_dir,args.db,args.rpc_file,args.checkpoint_dir)
        print(json.dumps(result,ensure_ascii=False,indent=2))
        return 0 if result["lifecycle_evidence_complete_for_this_account"] else 2
    except (audit.ScanBlocked,OSError,ValueError,KeyError,TypeError) as e:
        import re
        reason=str(e)
        if not re.fullmatch("[A-Z][A-Z0-9_]{3,80}",reason):
            reason="ONE_PASS_RESEARCH_BLOCKED"
        print(json.dumps({"status":"UNVERIFIED","reason":reason,
                          "rpc_attempts":"UNKNOWN_IF_TRANSPORT_STOP",
                          "production_db_writes":0,"signals_changed":False,
                          "emails_sent":0,"person_pattern":"OBSERVE_ONLY"}))
        return 2


if __name__=="__main__":
    raise SystemExit(main())
