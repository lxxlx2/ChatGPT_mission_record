#!/usr/bin/env python3
"""Validate DDAC owner-signed Four.meme Dragon original buy before earliest scoped DEX.

A real owner-signed buy event is not a closed profitable round or a 1/5/15m
followable public signal. Original receipt was too long for complete readback.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parent
PREFIX="crypto-300-profit-mission/research/"
PINS=(("bsc-meme-address-model-v1-p4b-dragon-fourmeme-first-events-precommit-2026-10-14.json","0d2951839e1f78b4a8a94f97218b6820bed5a98b"),("bsc-meme-address-model-v1-p4b-dragon-fourmeme-first-events-raw-2026-10-14.json","0ddf8b88ebf1bdc81439eb259a693a588ab770b7"),("bsc-meme-address-model-v1-p4b-2026-major3-first-txs-part1-2026-10-14.json","1bae5d79e34728f4e303f3ed03773ce78c49384c"),("bsc-meme-address-model-v1-p4b-first10-erc20-pre-dex-part4-2026-10-14.json","ed68cd1ae0245132ec1eafa8d7803d12c802d685"),("bsc-meme-address-model-v1-p4b-19ca-fourmeme-helper3-origin-2026-10-14.json","d9425bb3a9c5e8e23c737b7bfd00df41be6b940d"),("bsc-meme-address-model-v1-p4b-19ca-early-launch-origin-2026-10-14.json","847c83fb1e1c523ebebc152f6fddacdcf128a5b7"))
DDAC="0xddac928a240bdace3994c2cc0783d4e29a002127"
DRAGON="0xeccbb861c0dda7efd964010085488b69317e4444"
MANAGER="0x5c952063c7fc8610ffdb798152d69f0b9550762b"
TOKEN_CREATE="0x396d5e902b675b032348d3d2e9517ee8f0c4a926603fbc075d3d282ff00cad20"
TOKEN_PURCHASE="0x7db52723a3b2cdd6164364b3b766e65e540d7be48ffa89582956d8eaebe62942"

def check(ok,why):
    if not ok: raise ValueError(why)

def git_sha(raw):
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()

def load(root=ROOT):
    docs=[]
    for n,h in PINS:
        raw=(root/n).read_bytes()
        check(git_sha(raw)==h,"source blob drift: "+n)
        docs.append(json.loads(raw))
    return docs

def when(t):
    return datetime.fromtimestamp(t,tz=timezone.utc).isoformat(timespec="milliseconds").replace("+00:00","Z")

def build(d):
    check(len(d)==6,"source input count mismatch")
    pre,raw,txs,transfers,helpers,orig=d
    check(pre["schema"]=="BSC_P4B_2026_DRAGON_FOURMEME_MANAGER_CREATION_PURCHASE_EVENT_PRECOMMIT"
          and pre["source_selected_transactions_blob_sha"] in {
              "0", pre["source_selected_transactions_blob_sha"] # actual source manifest pinned below
          }
          and pre["token_CA"].lower()==DRAGON
          and pre["manager"]==MANAGER
          and [e["kind"] for e in pre["events"]]==["TokenCreate","TokenPurchase"]
          and pre["events"][0]["topic0"]==TOKEN_CREATE
          and pre["events"][1]["topic0"]==TOKEN_PURCHASE,
          "frozen Dragon manager witness changed")
    check(raw["schema"]=="BSC_P4B_DRAGON_FOURMEME_FIRST_MANAGER_EVENT_RAW"
          and raw["precommit_blob_sha"]==PINS[0][1]
          and raw["production"]=="NO_GO", "raw manager logs not from frozen precommit")
    events={}
    for witness in raw["rows"]:
        check(witness["status"]=="COMPLETE"
              and witness["target_txhash"]==next(p["txhash"] for p in pre["events"] if p["kind"]==witness["kind"])
              and len(witness["original_target_events"])==1
              and len([e for e in witness["all_same_block_topic_events"] if e["transactionHash"]==witness["target_txhash"]])==1,
              "manager logs not original one event")
        ev=witness["original_target_events"][0]
        check(ev["address"].lower()==MANAGER
              and ev["topics"][0] == next(p["topic0"] for p in pre["events"] if p["kind"]==witness["kind"])
              and int(ev["blockNumber"],16)==witness["block"]
              and ev["transactionHash"]==witness["target_txhash"]
              and ev.get("removed") is False,
              "manager event identity changed")
        events[witness["kind"]]=ev
    c,b=events["TokenCreate"],events["TokenPurchase"]
    # TokenCreate: creator, token, requestId, dynamic string offsets...
    check("0x"+c["data"][2+64+24:2+128].lower()==DRAGON
          and "0x"+b["data"][2+24:2+64].lower()==DRAGON
          and "0x"+b["data"][2+64+24:2+128].lower()==DDAC,
          "purchase/creation CA or recipient mismatch")
    check(len(b["data"])==2+64*8,"Four.meme purchase event wrong ABI shape")
    wr=[int(b["data"][2+64*i:2+64*(i+1)],16) for i in range(8)]
    buy_tx=next(x for x in txs["rows"] if x["selection"]["selected_role"]=="FIRST_DISTINCT_POST_MINT_TRANSFER_TX")
    signed=buy_tx["transaction"]
    check(buy_tx["tx_status"]=="COMPLETE"
          and buy_tx["receipt_status"]=="UNRESOLVED"
          and buy_tx["selection"]["selected_tx_hash"]==b["transactionHash"]
          and signed["hash"]==b["transactionHash"]
          and signed["from"].lower()==DDAC
          and int(signed["blockNumber"],16)==int(b["blockNumber"],16)
          and int(signed["value"],16)>=wr[4]+wr[5],
          "original DDAC signed funds and receipt grade incomplete")
    token=next(x for x in transfers["rows"] if x["token"]=="龙虾")
    matched=[t for t in token["transfers"] if t["hash"]==b["transactionHash"]
             and t["from"].lower()==MANAGER and t["to"].lower()==DDAC]
    check(len(matched)==1 and int(matched[0]["rawContract"]["value"],16)==wr[3]
          and matched[0]["rawContract"]["address"].lower()==DRAGON,
          "DDAC original onchain receipt token transfer missing")
    info=next(x for x in helpers["rows"] if x["token"]=="龙虾")
    earliest=next(x for x in orig["rows"] if x["token"]=="龙虾")
    launch=int(info["helper_launch_timestamp"])
    purchase_timestamp=int(b["blockTimestamp"],16)
    created_at=int(c["blockTimestamp"],16)
    db=int(earliest["first_scoped_dex_positive_block"])
    cp=int(c["blockNumber"],16)
    bp=int(b["blockNumber"],16)
    check(info["Four_meme_origin_classification"]=="FOUR_MEME_V2_CANONICAL"
          and info["helper_version"]==2
          and info["helper_token_manager"].lower()==MANAGER
          and earliest["pre_dex_helper_status"]=="FOUR_MEME_V2_CANONICAL"
          and cp<bp<db and launch<=created_at<=purchase_timestamp,
          "original market temporal precedence broken")
    fact={
        "token":"龙虾","exact_CA":DRAGON,"launchpad":"FOUR_MEME_V2_CANONICAL","manager":MANAGER,
        "original_launch_time_unix":launch,"original_launch_time_UTC":when(launch),
        "tokenCreate_block":cp,"tokenCreate_tx":c["transactionHash"],"tokenCreate_UTC":when(created_at),
        "buyer_EOA":DDAC,"buyer_original_tx":b["transactionHash"],
        "buyer_original_tx_block":bp,"buyer_original_tx_time_UTC":when(purchase_timestamp),
        "buyer_original_tx_value_wei":str(int(signed["value"],16)),
        "buyer_original_tx_to":signed["to"],
        "TokenPurchase_account":DDAC,"TokenPurchase_amount_token_raw":str(wr[3]),
        "TokenPurchase_cost_quote_wei":str(wr[4]),
        "TokenPurchase_protocol_fee_wei":str(wr[5]),
        "original_erc20_transfer_recipient":matched[0]["to"],
        "original_erc20_transfer_raw_amount":str(wr[3]),
        "creation_to_purchase_delay_blocks":bp-cp,
        "launchTime_to_purchase_seconds":purchase_timestamp-launch,
        "earliest_scoped_DEX_active_block":db,
        "DEX_liquidity_after_purchase_blocks":db-bp,
        "market_window_classification":"ACTUAL_SIGNED_PRE_DEX_LAUNCHPAD_BUY_OBSERVED",
        "receipt_response_status":"UNRESOLVED_TRUNCATED",
        "gas_fee":"UNRESOLVED",
        "cost_plus_fee_not_assumed_equal_tx_value":True,
        "sell_status":"UNRESOLVED",
        "gross_cashflow_after_sell":"UNRESOLVED",
        "realized_net_PnL":"UNRESOLVED",
        "third_party_follower_1_5_15m":"UNRESOLVED",
        "first_global_any_venue_buy":"UNRESOLVED",
        "production":"NO_GO"
    }
    return {
        "schema":"BSC_P4B_DRAGON_DDAC_EARLY_FOURMEME_OWNER_SIGNED_BUY",
        "scope":"One source-selected DDAC original signed buy of exact major CA 龙虾 on Four.meme TokenManager2 before known first liquid DEX, with actual original token purchase event and ERC20 transfer. Not proof earliest buy, profitable closed position, or outsider copy execution.",
        "source_manifest":[{"path":PREFIX+n,"git_blob_sha":h} for n,h in PINS],
        "summary":{
            "original_signed_DDAC_buys_in_this_fixed_sample":1,
            "pre_scoped_DEX_purchases_evidenced":1,
            "proven_realized_profit":0,
            "qualified_first_global_U":0,
            "production":"NO_GO"
        },
        "fact":fact,
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source-dir",type=Path,default=ROOT)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    a.output.write_text(json.dumps(build(load(a.source_dir)),ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
if __name__=="__main__":
    main()
