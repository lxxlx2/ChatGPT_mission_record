#!/usr/bin/env python3
"""P4-C true 7 recently-signed owner wallets, 5 original rounds + 2 controls.

Only two fully source-reconciled native profitable WBNB + gas rounds may be
promoted. 3 sampled economic window deltas and 2 latest signed activity-only
wallets retain explicit unqualified grading. DDAC actual negative is preserved.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
PREFIX="crypto-300-profit-mission/research/"
PINS=(("bsc-meme-address-model-v1-p4c-sevenwallet-balanced-five-round-precommit-2026-10-15.json","85a39f4c5c9723e98180a1c018b9dd94588fe3b6"),("bsc-meme-address-model-v1-p4c-sevenwallet-owner-tx-part1-2026-10-15.json","a038983867c6cfbad35c1fcd4b070992eba3fe8f"),("bsc-meme-address-model-v1-p4c-sevenwallet-owner-tx-part2-2026-10-15.json","b1ceba18b696553ac902bbb25bbd68b7abe75187"),("bsc-meme-address-model-v1-p4c-sevenwallet-five-round-native-part1-2026-10-15.json","71d8c4549c176fcf9f78002f648d956aedc4a026"),("bsc-meme-address-model-v1-p4c-sevenwallet-five-round-native-part2-2026-10-15.json","ce70cd208676a449ee6b9f66264835c600423ba7"),("bsc-meme-address-model-v1-p4c-sevenwallet-original-receipt-part1-2026-10-15.json","0351062ea8b6290e465412e38d02a7790ae8f9a3"),("bsc-meme-address-model-v1-p4c-sevenwallet-original-receipt-part2-2026-10-15.json","a28c25a1ef16315777b4b59ab1d8126f8c10d11a"),("bsc-meme-address-model-v1-p4c-sevenwallet-original-receipt-part3-2026-10-15.json","b0a8ec20402523f78bc73e409a22b55a5afc8164"),("bsc-meme-address-model-v1-p4c-8e6b-hajimi-dragon-two-verified-native-positive-2026-10-15.json","dc144d9d259ef1392478d1e25d48f2f649744f20"),("bsc-meme-address-model-v1-p4c-dragon-ddac-closed-native-loss-2026-10-15.json","4e76eea4d7ab001360af82f15de5eefc8509c501"))
UNKNOWN="UNRESOLVED_ECONOMIC_CASHFLOW_OR_FULL_RECEIPTS"
WIN="SETTLED_OWNER_NATIVE_POSITIVE_WITH_WBNB_GAS"

def require(ok,msg):
    if not ok:raise ValueError(msg)
def sha(raw):
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
def load(root=ROOT):
    docs=[]
    for n,h in PINS:
        raw=(root/n).read_bytes()
        require(sha(raw)==h,"raw source changed "+n)
        docs.append(json.loads(raw))
    return docs
def build(d):
    require(len(d)==10,"original 7 wallet normalized source count must be ten")
    pre=d[0]
    owner=d[1]["rows"]+d[2]["rows"]
    native=d[3]["rows"]+d[4]["rows"]
    receipt=d[5]["rows"]+d[6]["rows"]+d[7]["rows"]
    winners=d[8]["rounds"]
    prior_negative=d[9]["round"]
    require(pre["schema"]=="BSC_P4C_SEVEN_RECENT_WALLET_BALANCED_SIGNED_ROUND_BATCH_FROZEN"
            and pre["status"]=="FROZEN_BEFORE_FRESH_RPC"
            and len(pre["seven_original_wallets"])==7
            and len(set(pre["seven_original_wallets"]))==7
            and len(pre["sample_rounds"])==5
            and len(pre["activity_only_controls"])==2
            and len(winners)==2 and len(owner)==len(receipt)==14
            and len(native)==11
            and all(x.get("production",x.get("summary",{}).get("production",x.get("summary",{}).get("live_production")))=="NO_GO" for x in d),
            "all original selected 7 active wallet sample evidence incomplete")
    require(d[1]["precommit_git_blob_sha"]==d[2]["precommit_git_blob_sha"]==PINS[0][1]
            and d[3]["precommit_sha"]==d[4]["precommit_sha"]
            and d[1]["part"]==d[3]["part"]==d[5]["part"]==1
            and d[2]["part"]==d[4]["part"]==d[6]["part"]==2
            and d[7]["part"]==3,
            "source parts silently mixed across frozen samples")
    status=[]
    for r in pre["sample_rounds"]:
        sigs=[x for x in owner if x["source"]["round"]==r["key"]]
        rcs=[x for x in receipt if x["source"]["round"]==r["key"]]
        bs=[x for x in native if x["round"]==r["key"]]
        require(len(sigs)==len(rcs)==len(r["transactions"])
                and len(bs)==len(set(t["block"] for t in r["transactions"]))
                and all(x["status"]=="OWNER_SIGNER_COMPLETE" and x["source"]["wallet"]==r["wallet"] for x in sigs)
                and all(x["before"]["status"]==x["after"]["status"]=="COMPLETE" and x["wallet"]==r["wallet"]
                        and x["delta_wei"]==str(int(x["after"]["balance_wei"])-int(x["before"]["balance_wei"]))
                        for x in bs),
                "non-original wallet or historical block balance mismatch")
        for selected in r["transactions"]:
            matches=[s for s in sigs if s["source"]["tx"]==selected["tx"] and s["source"]["block"]==selected["block"]]
            checks=[s for s in rcs if s["source"]["tx"]==selected["tx"] and s["source"]["block"]==selected["block"]]
            require(len(matches)==len(checks)==1,"original selected signed tx or receipt not preserved")
            require(checks[0]["status"] in ("SUCCESS_FULL_RECEIPT","TRUNCATED_NO_FULL_RECEIPT"),
                    "failed or unreadable transaction silently promoted")
        native_net=sum(int(x["delta_wei"]) for x in bs)
        win=next((x for x in winners if x["round_key"]==r["key"]),None)
        if win:
            require(win["owner"]==r["wallet"] and win["exact_CA"]==r["ca"]
                    and win["actual_native_round_net_wei"]==str(native_net)
                    and win["classification"]==WIN
                    and all(x["status"]=="SUCCESS_FULL_RECEIPT" for x in rcs),
                    "no original WBNB full-quantity success receipts for realized winner")
        status.append({
            "round_key":r["key"],"wallet":r["wallet"],"token":r["token"],
            "exact_CA":r["ca"],
            "selected_original_signed_transactions":len(sigs),
            "owner_signatures_rechecked":True,
            "unique_historical_account_blocks":len(bs),
            "all_BNB_archive_pre_post_complete":True,
            "native_account_selected_block_net_wei":str(native_net),
            "native_account_selected_block_direction":"POSITIVE_NATIVE_BLOCK_SCOPE" if native_net>0 else "NEGATIVE_NATIVE_BLOCK_SCOPE",
            "successful_complete_original_receipts":sum(x["status"]=="SUCCESS_FULL_RECEIPT" for x in rcs),
            "receipt_truncated_or_other_count":sum(x["status"]!="SUCCESS_FULL_RECEIPT" for x in rcs),
            "actual_settled_owner_native_round_status":WIN if win else UNKNOWN,
            "source_verified_owner_native_net_wei":win["actual_native_round_net_wei"] if win else None,
            "observer_1_5_15min":"UNRESOLVED",
            "production":"NO_GO"
        })
    controls=[]
    for c in pre["activity_only_controls"]:
        c_owner=next((s for s in owner if s["source"]["tx"]==c["tx"] and s["source"]["wallet"]==c["wallet"]),None)
        c_rc=next((s for s in receipt if s["source"]["tx"]==c["tx"]),None)
        require(c_owner is not None and c_owner["status"]=="OWNER_SIGNER_COMPLETE" and c_rc is not None
                and c_rc["status"] in ("SUCCESS_FULL_RECEIPT","TRUNCATED_NO_FULL_RECEIPT"),
                "actual P3 wallet activity not revalidated")
        controls.append({
            "wallet":c["wallet"],"source_recent_swap_tx":c["tx"],
            "block":c["block"],"EOA_signer_reverified":True,
            "success_receipt_complete":c_rc["status"]=="SUCCESS_FULL_RECEIPT",
            "actual_economic_buy_sell_round":"UNRESOLVED",
            "profit_status":"UNRESOLVED","production":"NO_GO"
        })
    wallets={r["wallet"] for r in status}|{x["wallet"] for x in controls}|{prior_negative["owner"]}
    require(len(wallets)==7 and wallets==set(pre["seven_original_wallets"])
            and int(prior_negative["native_closed_owner_round_net_wei"])<0
            and prior_negative["exit_venue_verified_successful"]=="FOUR_MEME_TOKENSALE"
            and prior_negative["token"]=="龙虾"
            and sum(x["actual_settled_owner_native_round_status"]==WIN for x in status)==2,
            "original active seven wallet economic population changed")
    s={
      "frozen_recent_active_wallets":7,"frozen_major_exact_CAs":19,
      "preselected_rounds_this_batch":5,"distinct_economic_batch_wallets":4,
      "source_owner_signature_reverified_transactions":len(owner),
      "unique_historical_native_balance_blocks":len(native),
      "full_original_receipt_success_recovered":sum(x["status"]=="SUCCESS_FULL_RECEIPT" for x in receipt),
      "origin_receipt_truncated":sum(x["status"]=="TRUNCATED_NO_FULL_RECEIPT" for x in receipt),
      "selected_native_positive_block_scope_rounds":sum(x["native_account_selected_block_direction"]=="POSITIVE_NATIVE_BLOCK_SCOPE" for x in status),
      "selected_native_negative_block_scope_rounds":sum(x["native_account_selected_block_direction"]=="NEGATIVE_NATIVE_BLOCK_SCOPE" for x in status),
      "independently_settled_native_positive_rounds":2,
      "prior_DDAC_native_negative_rounds_retained":1,
      "unclosed_positive_or_negative_scope_only":sum(x["actual_settled_owner_native_round_status"]==UNKNOWN for x in status),
      "control_wallets_without_round":len(controls),
      "verified_profitable_winner_wallets_in_original_7":1,
      "profit_rank_ready":False,"public_follower_1_5_15_eligible":False,"production":"NO_GO"
    }
    require((s["source_owner_signature_reverified_transactions"],
             s["unique_historical_native_balance_blocks"],
             s["full_original_receipt_success_recovered"],
             s["origin_receipt_truncated"],
             s["selected_native_positive_block_scope_rounds"],
             s["selected_native_negative_block_scope_rounds"],
             s["unclosed_positive_or_negative_scope_only"])==(14,11,6,8,4,1,3),
            "batch denominator/partial receipt statuses changed")
    return {
      "schema":"BSC_P4C_SEVEN_RECENT_WALLET_FROZEN_BALANCED_SOURCE_ECONOMIC_BATCH",
      "scope":"Original recent 7 owner-swap active wallets; original 5 precommitted signed candidate rounds 4 distinct wallets and 2 latest swap activity-only wallets, plus DDAC previously independent genuine negative. Fresh all 14 owner transactions re-read; 11 unique archived native block spans. Only 8E6B two 2026 majors independently closed positive with full receipts WBNB Gas. Other three candidate round signs are native-scope observations, not endorsed full quote PnL; 0ABB and 498 cannot be ranked.",
      "source_manifest":[{"path":PREFIX+n,"git_blob_sha":sha} for n,sha in PINS],
      "summary":s,"rounds":status,"activity_only_controls":controls,
      "preaudited_negative":{
        "owner":prior_negative["owner"],"token":prior_negative["token"],
        "CA":prior_negative["exact_CA"],
        "native_net_wei":prior_negative["native_closed_owner_round_net_wei"],
        "status":"SIGNED_TOKENSALE_NATIVE_NEGATIVE_WITH_GAS"
      }
    }
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source-dir",type=Path,default=ROOT)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    a.output.write_text(json.dumps(build(load(a.source_dir)),ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
if __name__=="__main__":main()
