#!/usr/bin/env python3
"""Cross-owner original 23x19 native BNB proofs with explicit unreviewed cells."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
PREFIX="crypto-300-profit-mission/research/"
PINS=(("bsc-meme-address-model-v1-p4c-23x19-native-economic-evidence-grid-2026-10-15.json","ab624efd3dac43fa5508fbc09b3489d322097311"),("bsc-meme-address-model-v1-p4c-8e6b-hajimi-dragon-two-verified-native-positive-2026-10-15.json","dc144d9d259ef1392478d1e25d48f2f649744f20"))
NA="NOT_ECONOMICALLY_AUDITED"

def require(v,message):
    if not v:raise ValueError(message)
def blob_sha(raw):
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
def load(root=ROOT):
    res=[]
    for n,h in PINS:
        raw=(root/n).read_bytes()
        require(blob_sha(raw)==h,"source Git blob drift "+n)
        res.append(json.loads(raw))
    return res
def build(src):
    require(len(src)==2,"need original DDAC negative 23x19 and two independently settled positive source")
    old,wins=src
    require(old["schema"]=="BSC_P4C_ORIGINAL_23WALLET_19MAJOR_REALIZED_ECONOMIC_EVIDENCE_GRID"
            and old["summary"]["frozen_wallet_candidates"]==23
            and old["summary"]["frozen_major_exact_CAs"]==19
            and old["summary"]["implicit_wallet_CAs"]==437
            and old["summary"]["verified_native_negative_rounds"]==1
            and old["summary"]["verified_native_positive_rounds"]==0
            and len(old["verified_closed_rounds"])==1
            and wins["summary"]["source_proven_signed_positive_native_rounds"]==2
            and wins["summary"]["independent_major_CAs"]==2
            and wins["summary"]["original_full_success_tx_receipts"]==5
            and wins["summary"]["qualified_observer_trades"]==0
            and len(wins["rounds"])==2
            and old["summary"]["production"]==wins["summary"]["production"]=="NO_GO",
            "original income evidence or source denominator invalid")
    existing=old["verified_closed_rounds"][0]
    require(int(existing["net_wei"])<0
            and existing["classification"]=="REALIZED_NEGATIVE_BNB_CLOSED_OWNER_ROUND"
            and existing["quote"]=="BNB_NATIVE"
            and len(old["wallets"])==23 and len(old["markets"])==19,
            "original DDAC negative case changed")
    evidence=[{
        "wallet":existing["owner"],"exact_CA":existing["exact_CA"],
        "token":existing["token"],"quote":existing["quote"],
        "net_wei":existing["net_wei"],
        "classification":existing["classification"],
        "buy_tx":existing["original_buy_tx"],
        "sell_txs":[existing["original_sale_tx"]]
    }]
    for round in wins["rounds"]:
        require(round["source_closed_raw_quantity"] is True
                and round["source_original_EOA_all_signed"] is True
                and round["original_receipt_success_all"] is True
                and round["residual_raw"]=="0"
                and round["original_full_token_bought_raw"]==round["original_full_token_sold_raw"]
                and round["classification"]=="SETTLED_OWNER_NATIVE_POSITIVE_WITH_WBNB_GAS"
                and round["quote"]=="BNB_NATIVE_WITH_WBNB_SETTLEMENT"
                and round["first_executable_global_U"]=="UNRESOLVED"
                and round["owner_observer_follower_1_5_15min"]=="UNRESOLVED"
                and int(round["actual_native_round_net_wei"])>0,
                "positive wallet trade source not fully net-settled and signed")
        evidence.append({
            "wallet":round["owner"],"exact_CA":round["exact_CA"],
            "token":round["token"],"quote":round["quote"],
            "net_wei":round["actual_native_round_net_wei"],
            "classification":round["classification"],
            "buy_tx":round["buy"][0]["hash"],
            "sell_txs":[sale["hash"] for sale in round["sells"]]
        })
    lookup={(v["wallet"].lower(),v["exact_CA"].lower()):v for v in evidence}
    require(len(evidence)==len(lookup)==3,"original closed economics duplicated")
    roster={w["wallet"].lower() for w in old["wallets"]}
    ca={m["exact_CA"].lower() for m in old["markets"]}
    require(all(w in roster and c in ca for w,c in lookup),"not original fixed 23x19 universe")
    require(len({e["wallet"].lower() for e in evidence if int(e["net_wei"])>0})==1
            and len({e["exact_CA"].lower() for e in evidence if int(e["net_wei"])>0})==2,
            "multiple tokens true positive vs single wallet fixed sample changed")
    wallets=[]
    for oldwallet in old["wallets"]:
        flags=[lookup[(oldwallet["wallet"].lower(),m["exact_CA"].lower())]["classification"]
               if (oldwallet["wallet"].lower(),m["exact_CA"].lower()) in lookup else NA
               for m in old["markets"]]
        wallets.append({**oldwallet,"closed_native_round_flags":flags})
    allflags=[flag for w in wallets for flag in w["closed_native_round_flags"]]
    require((len(allflags),allflags.count(NA))==(437,434),
            "unreviewed original wallet denominator was silently dropped")
    summary={
      "frozen_wallet_candidates":23,"frozen_major_exact_CAs":19,
      "implicit_wallet_CAs":437,"source_closed_original_native_rounds":3,
      "verified_native_positive_rounds":2,"verified_native_negative_rounds":1,
      "not_economically_audited_cells":434,"wallets_with_positive_closed_major_rounds":1,
      "wallets_with_both_positive_and_negative_closed_rounds":0,
      "wallets_with_two_distinct_native_profitable_major_CAs":1,
      "prior_2026_recent_signed_swap_wallets":old["summary"]["prior_2026_recent_signed_swap_wallets"],
      "qualified_public_entry_follower_signals":0,
      "profit_rank_ready":False,"production":"NO_GO"
    }
    require(summary["prior_2026_recent_signed_swap_wallets"]==7,"P3 recent active original seven not preserved")
    return {
      "schema":"BSC_P4C_23WALLET_19MAJOR_NATIVE_SETTLED_CROSS_OWNER_ECONOMIC_SNAPSHOT",
      "scope":"Original frozen 23x19. Two freshly source-proven successful positive BNB-native owner rounds for 8E6B across HAJIMI and Dragon, one source-proven negative BNB-native owner round DDAC Dragon. No ranking: 434 other wallet-CA cells NOT_ECONOMICALLY_AUDITED, some with lesser-grade native scope positive/negative episodes. Historic copyable 1/5/15 minute market U NOT qualified.",
      "source_manifest":[{"path":PREFIX+n,"git_blob_sha":h} for n,h in PINS],
      "summary":summary,"markets":old["markets"],"wallets":wallets,
      "verified_economic_rounds":evidence
    }
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--source-dir",type=Path,default=ROOT)
    parser.add_argument("--output",type=Path,required=True)
    a=parser.parse_args()
    a.output.write_text(json.dumps(build(load(a.source_dir)),ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
if __name__=="__main__":main()
