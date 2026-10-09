#!/usr/bin/env python3
"""One-time public RPC observation of additional frozen Frank accumulation mints.

Historical owner-token-account signature coverage only; no passive==trade.
Fail closed on RPC HTTP 429, no retry/endpoint rotation. Never trades or alerts.
"""
import json
import argparse
import time
import urllib.request
from pathlib import Path

ROOT="498g1rVnFcnjBjpfw1xyqA1WvgQXUU8RWuELjxkjAayQ"
USDC="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
SOURCE=Path(__file__).resolve().parents[2]/"meme/evidence/frank-trade-coverage-sol-usdt-complex-2026-10-04.json"
API="https://api.mainnet-beta.solana.com"
SELECTED=(
  "MukLDtJ8Cx9DxLbeyLRSWPSposTMWuwHANbuaudpump",
  "6GmAFSYs4gk3FDao5FzzySQpPZaWsa4rUJHacpMpUNgx",
  "HcRLc9VDgjLeK154xDawfb1dmVJ98DoSqcwTHGqiDeJR",
  "8K5X85PAJHAAVSvYaAzgVPPAPsqqHmvx16ZyBiscYF8L",
  "E4Ap4icMLwKot8rkkTbq5JkS5kZxt5XCE3yfxbzYBjHx",
  "4MMQY9bwkxxTtsK3W227Q5ABT6yFY8Pmn9Ze7wmAXKY8",
  "PerPsCe2SJ7Q25CN4R5TTX4fmBdmknE2hQmqCt96fHL",
  "CbyTNf7UPzvewHh4Zp6umogM2RWahhmGRJWLJnPwpump",
)

class BoundRpc:
    def __init__(self,budget=34,spacing=2.5):
        self.budget,self.spacing=budget,spacing
        self.count=0;self.last=0
    def query(self,method,params):
        if self.count>=self.budget:raise RuntimeError("RPC_FIXED_BUDGET_REACHED")
        if self.last:
            delay=self.spacing-(time.monotonic()-self.last)
            if delay>0:time.sleep(delay)
        self.last=time.monotonic();self.count+=1
        body=json.dumps({"jsonrpc":"2.0","id":self.count,
                         "method":method,"params":params}).encode()
        req=urllib.request.Request(API,headers={"Content-Type":"application/json"},data=body)
        with urllib.request.urlopen(req,timeout=18) as fd:r=json.load(fd)
        if "error" in r:raise RuntimeError("RPC_RESPONSE_ERROR_"+str(r["error"])[:100])
        return r.get("result")

def observed(tx,mint):
    if not isinstance(tx,dict):raise ValueError("TX_NOT_AVAILABLE")
    meta=tx["meta"]
    accounts=tx["transaction"]["message"]["accountKeys"]
    keys=[x["pubkey"] for x in accounts]
    signers={x["pubkey"] for x in accounts if x.get("signer") is True}
    flows={};owned_accounts=set()
    for tag,sign in (("preTokenBalances",-1),("postTokenBalances",1)):
        for row in meta.get(tag) or []:
            if row.get("owner")!=ROOT:continue
            code=row["mint"]
            flows[code]=flows.get(code,0)+sign*int(row["uiTokenAmount"]["amount"])
            if code==mint:
                owned_accounts.add(keys[row["accountIndex"]])
    return {"at":tx["blockTime"],"slot":tx["slot"],
      "succeeded":meta.get("err") is None,"root_signed":ROOT in signers,
      "usdc_delta_raw":str(flows.get(USDC,0)),
      "token_delta_raw":str(flows.get(mint,0)),
      "owned_token_accounts":sorted(owned_accounts)}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--max-rpc",type=int,default=34)
    ap.add_argument("--output",type=Path)
    a=ap.parse_args()
    if not 2<=a.max_rpc<=34:raise SystemExit("RPC_BUDGET_INVALID")
    src=json.loads(SOURCE.read_text())
    assert src["history"]["raw_hash_verified"]==6874
    signals=src["models"]["M3"]["signals"]
    rpc=BoundRpc(a.max_rpc)
    by={}
    for x in signals:
        if x.get("signal_type")!="FRANK_ACCUMULATION_SIGNAL":continue
        if x["mint"] not in SELECTED:continue
        if x["mint"] not in by or x["triggered_at"]<by[x["mint"]]["triggered_at"]:
            by[x["mint"]]=x
    assert len(by)==len(SELECTED)
    reports=[]
    stop=None
    for mint in SELECTED:
        s=by[mint];case={"mint":mint,"trigger_time":s["triggered_at"],
                        "signal_signature":s["triggering_signature"],
                        "signal_type":"ACCUMULATION_PRECONFIRM",
                        "episode_position_raw":s["position"]["current_token_position"],
                        "episode_quote_spent":s["position"]["gross_quote_spent"],
                        "status":"UNVERIFIED"}
        try:
            tx=rpc.query("getTransaction",[case["signal_signature"],
               {"encoding":"jsonParsed","commitment":"finalized",
                "maxSupportedTransactionVersion":1}])
            base=observed(tx,mint)
            case["trigger_tx"]=base
            if not base["succeeded"] or not base["root_signed"]:
                case["status"]="ROOT_TX_NOT_CONFIRMED"
            elif len(base["owned_token_accounts"])!=1:
                case["status"]="ATA_UNIQUE_NOT_CONFIRMED"
            else:
                ata=base["owned_token_accounts"][0]
                rows=rpc.query("getSignaturesForAddress",[ata,{
                   "limit":1000,"commitment":"finalized"}])
                if not isinstance(rows,list):raise ValueError("ATA_LIST_MISSING")
                newer=[r for r in rows if r.get("blockTime") and (
                     r["blockTime"]>base["at"] or
                     r["blockTime"]==base["at"] and r["slot"]>base["slot"])]
                covered=(len(rows)<1000 or any(r.get("blockTime") and
                          r["blockTime"]<base["at"] for r in rows))
                case.update({"token_account":ata,"account_page_size":len(rows),
                   "after_trigger_signatures":len(newer),
                   "account_history_page_reached_trigger":covered})
                if len(newer)<=5:
                    todecode=list(reversed(newer))
                    sampled=False
                else:
                    # Time-spaced samples; incomplete evidence no PnL attribution.
                    newest=list(reversed(newer))
                    todecode=[newest[i] for i in sorted({0,len(newest)//2,len(newest)-1})]
                    sampled=True
                items=[]
                for row in todecode:
                    received=rpc.query("getTransaction",[
                      row["signature"],{"encoding":"jsonParsed",
                      "commitment":"finalized","maxSupportedTransactionVersion":1}])
                    obj=observed(received,mint)
                    obj["signature"]=row["signature"]
                    items.append(obj)
                case["decoded_transactions"]=items
                case["decoded_all_after_trigger"]=len(items)==len(newer) and covered
                case["status"]="FULL_AT_A_SINGLE_KNOWN_ATA_ONLY" if (
                       len(items)==len(newer) and covered) else "INCOMPLETE_SAMPLED_ATA"
                out=[x for x in items if int(x["token_delta_raw"])<0]
                case["root_signed_outflow_count"]=sum(x["root_signed"] for x in out)
                case["owner_exits_observed"]=[{
                    "signature":x["signature"],"at":x["at"],
                    "root_signed":x["root_signed"],
                    "token_delta_raw":x["token_delta_raw"],
                    "usdc_delta_raw":x["usdc_delta_raw"]} for x in out]
                # A qualifying "closed" is conditional if all after-trigger
                # rows decoded and no further target tokens came back.
                initial=int(case["episode_position_raw"])
                token_net=sum(int(x["token_delta_raw"]) for x in items)
                case["lot_quantity_exit_matches_signal_inventory"]=(case["decoded_all_after_trigger"]
                           and token_net==-initial and initial>0)
        except Exception as exc:
            case["error_class"]=type(exc).__name__
            case["status"]="STOP_PUBLIC_RPC_"+type(exc).__name__
            stop={"mint":mint,"kind":type(exc).__name__,"message":str(exc)[:100]}
            reports.append(case)
            print("CASE_JSON:",json.dumps(case,separators=(",",":")),flush=True)
            break
        reports.append(case)
        print("CASE_JSON:",json.dumps(case,separators=(",",":")),flush=True)
    output={"population":len(SELECTED),"attempted":len(reports),
            "complete_single_ata":sum(r["status"]=="FULL_AT_A_SINGLE_KNOWN_ATA_ONLY" for r in reports),
            "rpc_attempts":rpc.count,"stop":stop,
            "root_wallet_binding_third_party":True,
            "other_token_accounts_or_historical_closed_accounts_unverified":True,
            "no_person_pnl_or_signal_generated":True,
            "results":reports}
    print("SUMMARY_JSON:",json.dumps({k:v for k,v in output.items() if k!="results"},
                       separators=(",",":")),flush=True)
    if a.output:a.output.write_text(json.dumps(output,indent=2)+"\n")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
