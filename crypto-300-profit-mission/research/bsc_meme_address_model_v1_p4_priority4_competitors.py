#!/usr/bin/env python3
"""Offline BSC P4 four frozen competing pools, raw creation evidence audit.

No price hindsight, deployment, alerting, PnL or first GLOBAL tradability claims.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parent
PREFIX="crypto-300-profit-mission/research/"
SOURCES=[
 ("bsc-meme-address-model-v1-p4-competing17-firstfactory-precommit-2026-10-14.json","b1c2395c949ba664c2424c8b8da84924c967ab90"),
 ("bsc-meme-address-model-v1-p4-priority4-competition-bisect-stage7-2026-10-14.json","a028afbefba965d12ea648dbf491aa6be41a7af0"),
 ("bsc-meme-address-model-v1-p4-priority4-competitor-creation-part1-2026-10-14.json","c803a9a64d04ed64d701f78f3760688ead2203d1"),
 ("bsc-meme-address-model-v1-p4-priority4-competitor-creation-part2-2026-10-14.json","41bf38e4640e138d441a0b07ce0e4931ffc812ff"),
 ("bsc-meme-address-model-v1-p4-19ca-v2-wbnb-first-positive-liquidity-2026-10-14.json","9fbc8bdaeb9df342a4d200fefb0ebd48b746b903"),
]
POOL_TOPIC="0x783cca1c0412dd0d695e784568c96da2e9c22ff989357a2e8b1d9b2b4e6b7118"
PAIR_TOPIC="0x0d3648bd0f6ba80134a33ba9275ac585d9d315f0ad8355cddefde31afa28d0e9"
INIT_TOPIC="0x98636036cb66a9c19a37435efc1e90142190214e8abeb821bdba3f2990dd4c95"
MINT_V3_TOPIC="0x7a53080ba414158be7ec69b987b5fb7d07dee101fe85488f0853ae16239d0bde"
MINT_V2_TOPIC="0x4c209b5fc8ad50758f13e2e1088ba56a560dff690a1c6fef26394f4c03821c4f"
SYNC_TOPIC="0x1c411e9a96e071241c2f21f7726b17ae89e3cab4c78be50e062b03a9fffbbad1"
QUOTE={"WBNB":"0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c",
       "USDT":"0x55d398326f99059ff775485246999027b3197955"}
SCOPE=("Only four fixed V2/USDT and V3/USDT competing pools tied to original frozen 17; "
       "exact creation state, NOT first global opportunity nor follower PnL.")

def must(test: bool, what: str) -> None:
    if not test:
        raise ValueError(what)

def sha(raw: bytes) -> str:
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()

def load(directory: Path) -> list[dict]:
    items=[]
    for n,s in SOURCES:
        b=(directory/n).read_bytes()
        must(sha(b)==s, "source blob SHA mismatch "+n)
        items.append(json.loads(b))
    return items

def build(items: list[dict]) -> dict:
    must(len(items)==5,"all 5 sources required")
    pre,stage,p1,p2,base=items
    candidates=pre["active_at_baseline"]
    must(pre["schema"]=="BSC_P4_COMPETING17_FIRST_FACTORY_DEPLOYMENT_PRECOMMIT"
         and pre["status"]=="FROZEN_BEFORE_BINSEARCH"
         and pre["production"]=="NO_GO"
         and len(candidates)==17
         and stage["source_precommit_sha"]==SOURCES[0][1]
         and stage["rounds"]==[26,28]
         and stage["production"]=="NO_GO"
         and stage["selected_indices"]==[12,13,14,15]
         and len(stage["to_bounds"])==4
         and p1["indices"]==[12,13]
         and p2["indices"]==[14,15]
         and p1["source_precommit_sha"]==p2["source_precommit_sha"]==SOURCES[0][1]
         and p1["closed_binary_sha"]==p2["closed_binary_sha"]==SOURCES[1][1]
         and p1["production"]==p2["production"]=="NO_GO"
         and len(p1["records"])==len(p2["records"])==2
         and base["summary"]["exact_major_CAs"]==19,
         "frozen universe/binary source changed")
    baseline={r["exact_CA"]:r for r in base["rows"]}
    rows=[]
    for offset,r in enumerate(p1["records"]+p2["records"]):
        index=stage["selected_indices"][offset]
        q=candidates[index]
        bnd=stage["to_bounds"][offset]
        must(bnd["hi"]-bnd["lo"]==1
             and r["creation_block"]==bnd["hi"]
             and r["index"]==index
             and all(r[k]==q[k] for k in
                     ("token","CA","pool","protocol","quote","fee_pips","factory","baseline_block"))
             and r["factory_before"] in ("0x", "0x"+"0"*64)
             and r["factory_at"][-40:]==r["pool"][2:],
             "factory or pool mapping at boundary drifted")
        event=r["first_creator_event"]
        others=r["pool_creation_block_events"]
        token0,token1=sorted([q["CA"],QUOTE[q["quote"]]])
        must(event["address"].lower()==r["factory"]
             and int(event["blockNumber"],16)==r["creation_block"]
             and event["topics"][0]==(PAIR_TOPIC if q["protocol"]=="V2" else POOL_TOPIC)
             and event["topics"][1]=="0x"+token0[2:].rjust(64,"0")
             and event["topics"][2]=="0x"+token1[2:].rjust(64,"0"),
             "indexed exact token identity changed")
        if q["protocol"]=="V3":
            must(event["topics"][3]=="0x"+format(q["fee_pips"],"064x")
                 and event["data"][-40:]==q["pool"][2:]
                 and len(event["data"])==130, "invalid V3 pool event payload")
        else:
            must(event["data"][26:66]==q["pool"][2:]
                 and len(event["data"])==130, "invalid V2 pair event payload")
        mint_topic=MINT_V3_TOPIC if q["protocol"]=="V3" else MINT_V2_TOPIC
        mint=[x for x in others if x["topics"][0]==mint_topic]
        must(len(mint)==1
             and mint[0]["transactionHash"]==event["transactionHash"]
             and all(int(x["blockNumber"],16)==r["creation_block"] for x in others),
             "missing exactly one first creation tx Mint")
        state=r["pool_creation_state"]
        if q["protocol"]=="V3":
            init=[x for x in others if x["topics"][0]==INIT_TOPIC]
            must(len(init)==1
                 and init[0]["transactionHash"]==event["transactionHash"]
                 and int(init[0]["logIndex"],16)<int(mint[0]["logIndex"],16)
                 and int(mint[0]["logIndex"],16)>int(event["logIndex"],16),
                 "V3 initialize/mint event order differs")
            l=int(state["liquidity"],16)
            sqrt=int(state["slot0"][2:66],16)
            must(sqrt>0 and (l>0)==r["first_active_liquidity_proven"],
                 "V3 active liquidity misclassified")
            reserves=None
        else:
            sync=[x for x in others if x["topics"][0]==SYNC_TOPIC
                  and x["transactionHash"]==event["transactionHash"]]
            must(len(sync)==1
                 and int(sync[0]["logIndex"],16)<int(mint[0]["logIndex"],16)
                 and len(sync[0]["data"])==130
                 and sync[0]["data"]==mint[0]["data"], "V2 original mint/sync invalid")
            reserve=state["reserves"]
            reserves=(int(reserve[2:66],16),int(reserve[66:130],16))
            must(all(v>0 for v in reserves)
                 and r["first_active_liquidity_proven"], "V2 initial reserves invalid")
            l,sqrt=None,None
        ref=baseline.get(q["CA"])
        must(ref and ref["token"]==q["token"]
             and ref["first_positive_reserves_block"]==q["baseline_block"]
             and r["creation_block"]<q["baseline_block"], "causal earlier pool control failed")
        active=r["first_active_liquidity_proven"]
        rows.append({
            "index":index,"token":q["token"],"CA":q["CA"],
            "protocol":q["protocol"],"quote":q["quote"],"fee_pips":q["fee_pips"],
            "pool":q["pool"],"create_block":r["creation_block"],
            "create_utc":datetime.fromtimestamp(int(event["blockTimestamp"],16),
                                               tz=timezone.utc).isoformat(timespec="milliseconds").replace("+00:00","Z"),
            "baseline_v2_wbnb_block":q["baseline_block"],
            "earlier_than_baseline_blocks":q["baseline_block"]-r["creation_block"],
            "create_tx":event["transactionHash"],"create_mint_tx":mint[0]["transactionHash"],
            "creation_active":active,
            "first_positive_in_this_pool_block":r["creation_block"] if active else None,
            "v3_liquidity_at_creation_wei":str(l) if l is not None else None,
            "v3_sqrtPriceX96":str(sqrt) if sqrt is not None else None,
            "v2_end_block_reserves":[str(v) for v in reserves] if reserves else None,
            "earliest_global_tradability":"UNRESOLVED",
            "sellability_and_tax":"UNRESOLVED","qualified_wallet_miss":"UNRESOLVED",
        })
    must(len(rows)==4
         and sum(r["creation_active"] for r in rows)==3
         and rows[2]["creation_active"] is False
         and rows[3]["token"]=="MARSCOIN", "4 pool classification drifted")
    return {
        "schema":"BSC_P4_PRIORITY4_COMPETING_FIRST_CREATION_AND_ACTIVE_LIQUIDITY",
        "scope":SCOPE,
        "sources":[{"path":PREFIX+n,"git_blob_sha":s} for n,s in SOURCES],
        "summary":{
            "competing_pools":4,"creation_event_and_boundary":4,
            "create_transaction_mint":4,"active_at_creation":3,
            "inactive_at_creation":1,"full_market_earliest_tradability":0,
            "qualified_misses":0,"production":"NO_GO",
        },
        "rows":rows,
    }

def main() -> None:
    p=argparse.ArgumentParser()
    p.add_argument("--source-dir",type=Path,default=ROOT)
    p.add_argument("--output",required=True,type=Path)
    opts=p.parse_args()
    result=build(load(opts.source_dir))
    opts.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

if __name__=="__main__":
    main()
