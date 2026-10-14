#!/usr/bin/env python3
"""Project-wide original 23x19 economic-reconciliation overlay, P4-C read-only.

Only a fully validated original signed buy/sell round with actual wallet
quote-denominated cost and settlement can promote a cell to a net result.
One DDAC 龙虾 REALIZED_NEGATIVE_BNB is supported; everything else
NOT_ECONOMICALLY_AUDITED is not a missed opportunity, zero, or profit.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
PREFIX="crypto-300-profit-mission/research/"
PINS=(("bsc-meme-address-model-v1-p4b-23x19-early-opportunity-ledger-2026-10-14.json","f88ed9abfcb0f321ec31e98a029303aca48a8623"),("bsc-meme-address-model-v1-p4c-dragon-ddac-closed-native-loss-2026-10-15.json","4e76eea4d7ab001360af82f15de5eefc8509c501"))
KNOWN="REALIZED_NEGATIVE_BNB_CLOSED_OWNER_ROUND"
OTHER="NOT_ECONOMICALLY_AUDITED"

def require(v,msg):
    if not v: raise ValueError(msg)

def blob_sha(raw):
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()

def load(root=ROOT):
    docs=[]
    for path,sha in PINS:
        raw=(root/path).read_bytes()
        require(blob_sha(raw)==sha,"source Git blob drift: "+path)
        docs.append(json.loads(raw))
    return docs

def build(d):
    require(len(d)==2,"expected exactly previous 23x19 and settled DDAC proof")
    early,settled=d
    s=early["summary"]
    f=settled["round"]
    r=settled["summary"]
    require(early["schema"]=="BSC_P4B_23WALLET_X19CA_EARLY_TRADE_EVIDENCE_OVERLAY"
            and (s["wallets"],s["major_exact_CAs"],s["implicit_wallet_CA_cells"])==(23,19,437)
            and s["one_source_proven_owner_signed_pre_dex_buy"]==1
            and s["remaining_not_audited_owner_early_trade_cells"]==436
            and s["existing_recent_major_signed_swap_wallets"]==7
            and settled["schema"]=="BSC_P4C_DDAC_DRAGON_SIGNED_CLOSED_NATIVE_LOSS_ROUND"
            and r["original_signed_owner_buys_economically_closed"]==1
            and r["actual_negative_native_owner_rounds"]==1
            and r["actual_positive_native_owner_rounds"]==0
            and int(f["native_closed_owner_round_net_wei"])<0
            and f["native_closed_owner_round_classification"]=="REALIZED_NEGATIVE_BNB_WINDOW"
            and f["exit_venue_verified_successful"]=="FOUR_MEME_TOKENSALE"
            and f["entry_token_amount_raw"]==f["exit_token_amount_raw"]
            and f["residual_token_raw"]=="0"
            and f["buyer_follower_entry_after_1_5_15min"]=="UNRESOLVED"
            and s["production"]==r["live_production"]=="NO_GO",
            "original 23x19 denominator or source-close economic gate altered")
    mi=[i for i,m in enumerate(early["markets"]) if m["ca"].lower()==f["exact_CA"].lower()]
    wi=[i for i,w in enumerate(early["wallets"]) if w["wallet"].lower()==f["owner"].lower()]
    require(len(mi)==len(wi)==1,"original closed owner/CA not unique in frozen cohort")
    mi,wi=mi[0],wi[0]
    require(early["wallets"][wi]["early_owner_trade_statuses"][mi]=="SIGNED_PRE_DEX_BUY_CONFIRMED"
            and len(early["markets"])==19 and len(early["wallets"])==23
            and [x["i"] for x in early["markets"]]==list(range(19)),
            "previous wallet early trade source does not match original closed native round")
    markets=[{"i":m["i"],"token":m["token"],"exact_CA":m["ca"],
              "first_scoped_dex_liquidity_block":m["first_scoped_dex_block"]}
             for m in early["markets"]]
    wallets=[]
    for i,w in enumerate(early["wallets"]):
        require(len(w["early_owner_trade_statuses"])==19,
                "source early evidence grid lost wallet-CA combinations")
        wallets.append({
            "wallet":w["wallet"],
            "existing_2026_recent_major_swap":w["recent_owner_19CA_swap"],
            "prior_source_P2_positive_episodes_are_not_full_PnL":w["selected_positive_rounds_not_net_PnL"],
            "prior_source_P2_negative_episodes_are_not_full_PnL":w["selected_negative_rounds_not_net_PnL"],
            "existing_early_buy_flags":w["early_owner_trade_statuses"],
            "closed_native_round_flags":[KNOWN if i==wi and k==mi else OTHER for k in range(19)]
        })
    cell=[x for w in wallets for x in w["closed_native_round_flags"]]
    require((len(cell),cell.count(KNOWN),cell.count(OTHER))==(437,1,436),
            "actual economic result inferred for nonreviewed wallet/CA")
    return {
        "schema":"BSC_P4C_ORIGINAL_23WALLET_19MAJOR_REALIZED_ECONOMIC_EVIDENCE_GRID",
        "scope":"23 frozen candidate wallets x 19 original major exact CAs. Only one DDAC original Dragon signed buy+TokenSale has fully source-verified negative native BNB round across historical wallet balance; other 436 cells have not undergone equivalent closure audit. Earlier P2 direction episodes and P3 signed activity are preserved but NOT promoted to actual net profit or eligible missed opportunities. Foreign Flap original buyers remain out of cohort.",
        "source_manifest":[{"path":PREFIX+name,"git_blob_sha":sha} for name,sha in PINS],
        "summary":{
            "frozen_wallet_candidates":23,
            "frozen_major_exact_CAs":19,
            "implicit_wallet_CAs":437,
            "source_closed_signed_native_rounds":1,
            "verified_native_negative_rounds":1,
            "verified_native_positive_rounds":0,
            "not_economically_audited_cells":436,
            "prior_2026_recent_signed_swap_wallets":7,
            "qualified_public_entry_follower_signals":0,
            "profit_rank_ready":False,
            "production":"NO_GO"
        },
        "markets":markets,"wallets":wallets,
        "verified_closed_rounds":[{
            "owner":f["owner"],"exact_CA":f["exact_CA"],"token":f["token"],
            "original_buy_tx":f["entry_tx"],
            "original_sale_tx":f["exit_tx"],
            "original_verified_sale_venue":f["exit_venue_verified_successful"],
            "net_wei":f["native_closed_owner_round_net_wei"],
            "quote":"BNB_NATIVE",
            "return_bps_trunc":f["native_closed_owner_round_roi_bps_trunc"],
            "classification":KNOWN
        }]
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source-dir",type=Path,default=ROOT)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    a.output.write_text(json.dumps(build(load(a.source_dir)),ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
if __name__=="__main__":
    main()
