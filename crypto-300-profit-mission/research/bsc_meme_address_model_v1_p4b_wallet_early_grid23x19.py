#!/usr/bin/env python3
"""Compact 23-wallet x 19 major CA early trade evidence join; no winner ranking.

Historical manager recognition and token transfers are NOT eligible trade-U.
Only DDAC Dragon confirmed original signed purchase in this bounded new study;
NOT_AUDITED_THIS_STAGE is deliberately not NO_TRADE, missed or a losing trade.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
PREFIX="crypto-300-profit-mission/research/"
PINS=(("bsc-meme-address-model-v1-p4-p2p3-readiness-matrix-2026-10-13.json","3252e05c3ef1a4de14a5e10aed3e5ba80566154f"),("bsc-meme-address-model-v1-p4b-19ca-early-launch-origin-2026-10-14.json","847c83fb1e1c523ebebc152f6fddacdcf128a5b7"),("bsc-meme-address-model-v1-p4b-dragon-ddac-real-pre-dex-buy-2026-10-14.json","f89362368ad47f1cde2d8475f9e7b8a688093f83"))
DEFAULT="NOT_AUDITED_THIS_STAGE"
KNOWN="SIGNED_PRE_DEX_BUY_CONFIRMED"

def check(ok,msg):
    if not ok:
        raise ValueError(msg)

def git_sha(raw):
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()

def load(root=ROOT):
    out=[]
    for n,sha in PINS:
        raw=(root/n).read_bytes()
        check(git_sha(raw)==sha,"source digest changed "+n)
        out.append(json.loads(raw))
    return out

def build(d):
    check(len(d)==3,"missing 23x19 evidence source")
    old,early,dragon=d
    check(old["summary"]["wallets"]==23
          and old["summary"]["strict19CA_30day_owner_swap_verified_wallets"]==7
          and early["summary"]["exact_CAs"]==19
          and early["summary"]["complete_first10_transfer_index_reads"]==19
          and early["summary"]["canonical_fourmeme_v2_at_pre_scoped_dex"]==12
          and dragon["summary"]["original_signed_DDAC_buys_in_this_fixed_sample"]==1
          and dragon["summary"]["proven_realized_profit"]==0
          and dragon["fact"]["market_window_classification"]=="ACTUAL_SIGNED_PRE_DEX_LAUNCHPAD_BUY_OBSERVED"
          and all(s["production"]=="NO_GO" for s in (old["summary"],early["summary"],dragon["summary"]))
          and len(old["wallets"])==23 and len(early["rows"])==19,
          "original 23, 19 or DDAC user safety denominators invalid")
    purchase=dragon["fact"]
    buyer=purchase["buyer_EOA"].lower()
    bought=purchase["exact_CA"].lower()
    markets=[{
        "i":e["index"],"token":e["token"],"ca":e["exact_CA"],
        "first_transfer_block":e["first_observed_erc20_transfer_block"],
        "first_scoped_dex_block":e["first_scoped_dex_positive_block"],
        "helper":e["pre_dex_helper_status"],"market_U":"UNRESOLVED"
    } for e in early["rows"]]
    check([x["i"] for x in markets]==list(range(19))
          and len({x["ca"] for x in markets})==19
          and buyer in {w["wallet"].lower() for w in old["wallets"]}
          and bought in {x["ca"].lower() for x in markets},
          "source original opportunity and wallet identity mismatch")
    wallets=[{
        "wallet":w["wallet"],
        "recent_owner_19CA_swap":w["p3_verified_recent_19CA_swap"],
        "recent_swap_UTC":w["p3_latest_verified_swap_UTC"],
        "selected_positive_rounds_not_net_PnL":w["p2_selected_positive_episodes"],
        "selected_negative_rounds_not_net_PnL":w["p2_selected_negative_episodes"],
        "early_owner_trade_statuses":[KNOWN if w["wallet"].lower()==buyer and market["ca"].lower()==bought else DEFAULT for market in markets],
        "actual_PnL":"UNRESOLVED",
        "qualified_misses":"UNRESOLVED"
    } for w in old["wallets"]]
    flat=[x for w in wallets for x in w["early_owner_trade_statuses"]]
    summary={
        "wallets":len(wallets),"major_exact_CAs":len(markets),
        "implicit_wallet_CA_cells":len(flat),
        "one_source_proven_owner_signed_pre_dex_buy":flat.count(KNOWN),
        "remaining_not_audited_owner_early_trade_cells":flat.count(DEFAULT),
        "existing_recent_major_signed_swap_wallets":old["summary"]["strict19CA_30day_owner_swap_verified_wallets"],
        "market_U_qualified":0,"repeat_profit_ranks":0,"production":"NO_GO",
    }
    check((summary["wallets"],summary["major_exact_CAs"],summary["implicit_wallet_CA_cells"],
           summary["one_source_proven_owner_signed_pre_dex_buy"],
           summary["remaining_not_audited_owner_early_trade_cells"])==(23,19,437,1,436),
          "full cohort lost or invented new trade")
    return {
        "schema":"BSC_P4B_23WALLET_X19CA_EARLY_TRADE_EVIDENCE_OVERLAY",
        "scope":"Compact 23x19 indexed grid: markets[i] is the fixed CA, wallets[j].early_owner_trade_statuses[i] is one evidence cell. NOT_AUDITED_THIS_STAGE is unknown, never no trade, loss or eligible miss. One DDAC original purchase event is verified; P2 positive direction is not full PnL.",
        "source_manifest":[{"path":PREFIX+n,"git_blob_sha":sha} for n,sha in PINS],
        "summary":summary,"markets":markets,"wallets":wallets,
        "known_early_owner_trades":[{
            "wallet":buyer,"CA":bought,
            "tx":purchase["buyer_original_tx"],
            "block":purchase["buyer_original_tx_block"],
            "signer_equals_recipient":True,
            "exact_token_cost_wei":purchase["TokenPurchase_cost_quote_wei"],
            "fee_wei":purchase["TokenPurchase_protocol_fee_wei"],
            "status":KNOWN
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
