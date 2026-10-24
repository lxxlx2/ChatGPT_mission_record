#!/usr/bin/env python3
"""P4 evidence: creation, Initialize/Mint, active liquidity, Swap on four frozen
competition pools. Never infer global first tradability or follower profit.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DIR = "crypto-300-profit-mission/research/"
SOURCES = (
    ("bsc-meme-address-model-v1-p4-competing17-firstfactory-precommit-2026-10-14.json", "b1c2395c949ba664c2424c8b8da84924c967ab90"),
    ("bsc-meme-address-model-v1-p4-priority4-competition-bisect-stage7-2026-10-14.json", "a028afbefba965d12ea648dbf491aa6be41a7af0"),
    ("bsc-meme-address-model-v1-p4-competing4-creation-evidence-part1-2026-10-14.json", "5bc9aa443e345694d6cb067c82d173ce8351ab50"),
    ("bsc-meme-address-model-v1-p4-competing4-creation-evidence-part2-2026-10-14.json", "5f80f2341c351925a2f450fdcd4ab238284bdf5d"),
    ("bsc-meme-address-model-v1-p4-competing4-creation-swaps-2026-10-14.json", "4690fd28867e831559a7d78d79b5343724ed6539"),
    ("bsc-meme-address-model-v1-p4-19ca-v2-wbnb-first-positive-liquidity-2026-10-14.json", "9fbc8bdaeb9df342a4d200fefb0ebd48b746b903"),
)
TOPIC = {
    "V2_Create": "0x0d3648bd0f6ba80134a33ba9275ac585d9d315f0ad8355cddefde31afa28d0e9",
    "V3_Create": "0x783cca1c0412dd0d695e784568c96da2e9c22ff989357a2e8b1d9b2b4e6b7118",
    "V2_Init": "0x1c411e9a96e071241c2f21f7726b17ae89e3cab4c78be50e062b03a9fffbbad1",
    "V3_Init": "0x98636036cb66a9c19a37435efc1e90142190214e8abeb821bdba3f2990dd4c95",
    "V2_Mint": "0x4c209b5fc8ad50758f13e2e1088ba56a560dff690a1c6fef26394f4c03821c4f",
    "V3_Mint": "0x7a53080ba414158be7ec69b987b5fb7d07dee101fe85488f0853ae16239d0bde",
    "V2_Swap": "0xd78ad95fa46c994b6551d0da85fc275fe613ce37657fb8d5e3d130840159d822",
    "V3_Swap": "0x19b47279256b2a23a1665c810c8d55a1758940ee09377d4f8d26497a3577dc83",
}
QUOTES = {"WBNB":"0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c",
          "USDT":"0x55d398326f99059ff775485246999027b3197955"}
INDICES = (12, 13, 14, 15)


def require(cond, message):
    if not cond:
        raise ValueError(message)


def blob(raw):
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def load(root):
    docs=[]
    for name,sha in SOURCES:
        raw=(root/name).read_bytes()
        require(blob(raw)==sha, "frozen source changed: "+name)
        docs.append(json.loads(raw))
    return docs


def pairs(data):
    require(isinstance(data,str) and data.startswith("0x") and len(data)>=130,
            "invalid two-word event")
    return int(data[2:66],16),int(data[66:130],16)


def validate(docs):
    pre,bounds,part1,part2,swaps,baseline=docs
    require(pre["production"]==bounds["production"]=="NO_GO"
            and bounds["selected_indices"]==list(INDICES)
            and bounds["source_precommit_sha"]==SOURCES[0][1]
            and len(bounds["to_bounds"])==4
            and part1["range"]==[0,1] and part2["range"]==[2,3]
            and part1["precommit_blob"]==part2["precommit_blob"]==SOURCES[0][1]
            and part1["exact_bounds_blob"]==part2["exact_bounds_blob"]==SOURCES[1][1]
            and part1["production"]==part2["production"]==swaps["production"]=="NO_GO",
            "frozen four-pool provenance invalid")
    raw=part1["records"]+part2["records"]
    require(len(raw)==len(swaps["records"])==4
            and pre["status"]=="FROZEN_BEFORE_BINSEARCH"
            and baseline["summary"]["exact_major_CAs"]==19,
            "missing frozen research denominator")
    bmap={r["exact_CA"]:r for r in baseline["rows"]}
    output=[]
    for j,(record,s) in enumerate(zip(raw,swaps["records"])):
        idx=INDICES[j]
        q=pre["active_at_baseline"][idx]
        low,high=bounds["to_bounds"][j]["lo"],bounds["to_bounds"][j]["hi"]
        require(high-low==1 and record["index"]==idx and
                record["created_block"]==high and
                record["source_status"]=="CONFIRMED_ALL_EVENTS_SAME_TX"
                and record["CA"]==q["CA"] and record["token"]==q["token"]
                and record["pool"]==q["pool"]==s["pool"]
                and record["factory"]==q["factory"]
                and record["protocol"]==q["protocol"]==s["protocol"]
                and record["quote"]==q["quote"]
                and record["fee_pips"]==q["fee_pips"]
                and s["status"]=="COMPLETE_BOUND_ONE_BLOCK"
                and s["block"]==high,
                "unmatched source pool/creation boundary")
        create=record["created_event"]
        init=record["pool_event_at_creation"]
        mint=record["mint_event_at_creation"]
        token0,token1=sorted((q["CA"],QUOTES[q["quote"]]))
        require(create["address"].lower()==q["factory"]
                and create["topics"][0]==TOPIC[q["protocol"]+"_Create"]
                and create["topics"][1]=="0x"+token0[2:].rjust(64,"0")
                and create["topics"][2]=="0x"+token1[2:].rjust(64,"0")
                and int(create["blockNumber"],16)==high
                and init["address"].lower()==mint["address"].lower()==q["pool"]
                and create["transactionHash"]==init["transactionHash"]==mint["transactionHash"]
                and int(create["logIndex"],16)<int(init["logIndex"],16)
                <int(mint["logIndex"],16),
                "factory creation/init/mint chain inconsistent")
        if q["protocol"]=="V2":
            require(create["data"][26:66]=="".join((q["pool"][2:],))
                    and init["topics"][0]==TOPIC["V2_Init"]
                    and mint["topics"][0]==TOPIC["V2_Mint"],"V2 event identity invalid")
            r0,r1=pairs(init["data"])
            require((r0,r1)==pairs(mint["data"]) and r0>0 and r1>0,
                    "V2 mint/reserves invalid")
            a0,a1=pairs(record["raw_creation_state"])
            require((r0>0 and r1>0) and (a0>0 and a1>0),
                    "V2 creation state has no positive reserves")
            state="V2_FIRST_CREATION_TX_POSITIVE_RESERVES"
            liquidity=str(r0)+"|"+str(r1)
        else:
            require(len(create["topics"])==4
                    and int(create["topics"][3],16)==q["fee_pips"]
                    and create["data"][-40:]==q["pool"][2:]
                    and init["topics"][0]==TOPIC["V3_Init"]
                    and mint["topics"][0]==TOPIC["V3_Mint"]
                    and int(init["data"][2:66],16)>0
                    and int(mint["data"][66:130],16)>0,
                    "V3 initialized/minted event invalid")
            L=int(record["raw_creation_state"],16)
            state="V3_CREATION_MINT_ACTIVE_LIQUIDITY" if L>0 else "V3_CREATION_MINT_ZERO_ACTIVE_LIQUIDITY"
            liquidity=str(L)
        # Same-block Swap logs are an observational check, never a follower fill.
        require(all(e["address"].lower()==q["pool"]
                    and e["topics"][0]==TOPIC[q["protocol"]+"_Swap"]
                    and int(e["blockNumber"],16)==high
                    for e in s["events"]),
                "wrong-source Swap promoted")
        timestamp=int(create["blockTimestamp"],16)
        baseline_block=bmap[q["CA"]]["first_positive_reserves_block"]
        require(baseline_block>high,"creation must precede V2 WBNB baseline")
        output.append({
            "index":idx,"token":q["token"],"CA":q["CA"],
            "pool":q["pool"],"venue":q["protocol"],"quote":q["quote"],"fee_pips":q["fee_pips"],
            "creation_block":high,
            "creation_UTC":datetime.fromtimestamp(timestamp,timezone.utc).isoformat(timespec="milliseconds").replace("+00:00","Z"),
            "blocks_before_v2_wbnb_baseline":baseline_block-high,
            "creation_mint_tx":mint["transactionHash"],
            "creation_state":state,
            "creation_liquidity_or_reserves_raw":liquidity,
            "same_block_swap_count":len(s["events"]),
            "first_active_liquidity_at_any_venue":"UNRESOLVED",
            "historical_tax_sellability":"UNRESOLVED",
            "qualified_wallet_miss":"UNRESOLVED",
            "follower_PnL":"UNRESOLVED",
        })
    require([r["creation_state"] for r in output]==[
        "V2_FIRST_CREATION_TX_POSITIVE_RESERVES",
        "V3_CREATION_MINT_ACTIVE_LIQUIDITY",
        "V3_CREATION_MINT_ZERO_ACTIVE_LIQUIDITY",
        "V3_CREATION_MINT_ACTIVE_LIQUIDITY",
    ] and [r["same_block_swap_count"] for r in output]==[1,0,0,1],
        "four-pool frozen classification changed")
    return {
        "schema":"BSC_P4_4_PRIORITY_COMPETING_ORIGIN_POSITIVE_AND_NEGATIVE",
        "source_manifest":[{"path":DIR+n,"git_blob_sha":sha} for n,sha in SOURCES],
        "scope":"Four frozen MARSCOIN/牛来 competitors of 17; factory creation + initial same-tx Mint state, two creation-block Swap hits. Later trading, other pools and exact eligible follower entry remain unresolved.",
        "summary":{"preexisting_competitors_total":17,
                   "fully_creation_checked":4,"remaining_untested_competitors":13,
                   "creation_positive_liquidity":3,"creation_zero_active_liquidity":1,
                   "creation_block_with_swap":2,
                   "confirmed_global_first_tradable":0,
                   "confirmed_followable_profitable_misses":0,"production":"NO_GO"},
        "rows":output,
    }


def main():
    p=argparse.ArgumentParser(description="offline BSC P4 competitor creation & initial liquidity proof")
    p.add_argument("--source-dir",type=Path,default=ROOT)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    a.output.write_text(json.dumps(validate(load(a.source_dir)),ensure_ascii=False,indent=2)+"\n",encoding="utf-8")


if __name__=="__main__":
    main()
