#!/usr/bin/env python3
"""P4 audited creation and first in-range liquidity for 4 of 17 competing pools.

Strictly source-pinned historical onchain originals; remains offline/research only.
A factory PoolCreated event, Initialize or Mint alone is NOT evidence of
in-range tradability, tax compliance, sale feasibility or follower profit.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parent
BASE="crypto-300-profit-mission/research/"
PINS=(
 ("bsc-meme-address-model-v1-p4-competing17-firstfactory-precommit-2026-10-14.json","b1c2395c949ba664c2424c8b8da84924c967ab90"),
 ("bsc-meme-address-model-v1-p4-competing17-firstfactory-round1-2026-10-14.json","2aa6f2145d6837d7f23eb6a2347f20dcb8731c45"),
 ("bsc-meme-address-model-v1-p4-priority4-competition-bisect-stage1-2026-10-14.json","325c4ef95d94265748bbb6147ab2200777a46aa2"),
 ("bsc-meme-address-model-v1-p4-priority4-competition-bisect-stage2-2026-10-14.json","6bbf715ab817a7ec6418a08de9d8493a9a604c1e"),
 ("bsc-meme-address-model-v1-p4-priority4-competition-bisect-stage3-2026-10-14.json","b2fae0a3389cf5d0f2c5496969e5d3c31a0c827c"),
 ("bsc-meme-address-model-v1-p4-priority4-competition-bisect-stage4-2026-10-14.json","cdfe57254bc2f86e388f90710889a7dcc0915d30"),
 ("bsc-meme-address-model-v1-p4-priority4-competition-bisect-stage5-2026-10-14.json","75aa7893559c1be0fc85ccb90de77033fcdb9729"),
 ("bsc-meme-address-model-v1-p4-priority4-competition-bisect-stage6-2026-10-14.json","6990a03157147bfc6d4aa184632ff6cbe27a6c99"),
 ("bsc-meme-address-model-v1-p4-priority4-competition-bisect-stage7-2026-10-14.json","a028afbefba965d12ea648dbf491aa6be41a7af0"),
 ("bsc-meme-address-model-v1-p4-priority4-competition-created-state-2026-10-14.json","85c05fdb07a14fd73edd7c603cc268b458d185b7"),
)
V2_CREATED="0x0d3648bd0f6ba80134a33ba9275ac585d9d315f0ad8355cddefde31afa28d0e9"
V3_CREATED="0x783cca1c0412dd0d695e784568c96da2e9c22ff989357a2e8b1d9b2b4e6b7118"
V2_SYNC="0x1c411e9a96e071241c2f21f7726b17ae89e3cab4c78be50e062b03a9fffbbad1"
V2_MINT="0x4c209b5fc8ad50758f13e2e1088ba56a560dff690a1c6fef26394f4c03821c4f"
V3_INIT="0x98636036cb66a9c19a37435efc1e90142190214e8abeb821bdba3f2990dd4c95"
V3_MINT="0x7a53080ba414158be7ec69b987b5fb7d07dee101fe85488f0853ae16239d0bde"
USDT="0x55d398326f99059ff775485246999027b3197955"


def require(ok: bool,why: str) -> None:
    if not ok:
        raise ValueError(why)


def git_blob(raw: bytes) -> str:
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()


def load(root: Path) -> list[dict]:
    out=[]
    for name,sha in PINS:
        data=(root/name).read_bytes()
        require(git_blob(data)==sha,"source Git SHA drift: "+name)
        out.append(json.loads(data))
    return out


def wei_decimal(value: int) -> str:
    whole,rem=divmod(value,10**18)
    decimal=str(rem).zfill(18).rstrip("0")
    return str(whole)+("."+decimal if decimal else "")


def read_word(s: str,i: int) -> int:
    require(s.startswith("0x") and len(s)>=2+(i+1)*64,"short ABI word")
    return int(s[2+i*64:2+(i+1)*64],16)


def creation_datetime(log: dict) -> str:
    return datetime.fromtimestamp(int(log["blockTimestamp"],16),tz=timezone.utc).isoformat(
        timespec="milliseconds").replace("+00:00","Z")


def validate_chain(d: list[dict]) -> tuple[list[dict],list[int]]:
    pre,first,*rest=d
    stages=rest[:7]
    require(pre["schema"]=="BSC_P4_COMPETING17_FIRST_FACTORY_DEPLOYMENT_PRECOMMIT"
            and pre["production"]=="NO_GO"
            and len(pre["active_at_baseline"])==17
            and len(pre["excluded_from_immediate_early_check_but_still_in_market_universe"])==5,
            "17 active / five negative source scope drift")
    targets=pre["active_at_baseline"]
    selected=[i for i,x in enumerate(targets) if x["token"] in ("牛来","MARSCOIN")]
    require(selected==[12,13,14,15],"priority selection drift")
    require(first["source_precommit_sha"]==PINS[0][1]
            and first["round"]==1
            and len(first["probes"])==17
            and len(first["bounds"])==17
            and first["production"]=="NO_GO", "first all-17 probe missing")
    bounds=[dict(first["bounds"][i]) for i in selected]
    for k,stage in enumerate(stages,1):
        a,b=[(2,5),(6,9),(10,13),(14,17),(18,21),(22,25),(26,28)][k-1]
        require(stage["schema"]=="BSC_P4_PRIORITY4_COMPETING_FACTORY_BISECTION"
                and stage["stage"]==k and stage["rounds"]==[a,b]
                and stage["selected_indices"]==selected
                and stage["source_precommit_sha"]==PINS[0][1]
                and stage["production"]=="NO_GO"
                and stage["from_bounds"]==bounds
                and len(stage["probes"])==4*(b-a+1),
                "binary stage chain gap / source drift")
        for round_id in range(a,b+1):
            entries=[p for p in stage["probes"] if p["round"]==round_id]
            require(len(entries)==4 and [z["index"] for z in entries]==selected,
                    "incomplete/unordered binary round")
            for j,entry in enumerate(entries):
                q=targets[selected[j]]
                if bounds[j]["hi"]-bounds[j]["lo"]<=1:
                    require(entry["block"] is None and entry["exists"] is None,"bad finished sentinel")
                    continue
                mid=(bounds[j]["lo"]+bounds[j]["hi"])//2
                require(entry["block"]==mid
                        and entry["value"] in ("0x"+"0"*40,q["pool"])
                        and entry["exists"]==(entry["value"]==q["pool"]),
                        "historical factory binary trace inconsistent")
                bounds[j]["hi" if entry["exists"] else "lo"]=mid
        require(bounds==stage["to_bounds"],"binary endpoint not derived from actual probes")
    require(all(z["hi"]-z["lo"]==1 for z in bounds),"four creation blocks not exact")
    return targets,selected


def build(d: list[dict]) -> dict:
    require(len(d)==len(PINS),"missing provenance")
    targets,selected=validate_chain(d)
    created=d[-1]
    require(created["schema"]=="BSC_P4_PRIORITY4_COMPETING_POOL_CREATED_EVENT_AND_CREATION_STATE"
            and created["precommit_sha"]==PINS[0][1]
            and created["bisect_stage7_sha"]==PINS[8][1]
            and created["production"]=="NO_GO"
            and len(created["rows"])==4, "created-state batch altered")
    bounds=d[8]["to_bounds"]
    rows=[]
    for j,(i,w) in enumerate(zip(selected,created["rows"])):
        q=targets[i]
        block=bounds[j]["hi"]
        log=w["creation_event"]
        require(all(w[key]==q[key] for key in
                    ("token","CA","protocol","quote","pool","factory","fee_pips"))
                and w["index"]==i and w["creation_block"]==block
                and int(log["blockNumber"],16)==block
                and log["address"].lower()==q["factory"]
                and w["read_status"]=="DIRECT_CHAIN",
                "creation event not original frozen pool")
        token0,token1=sorted((q["CA"],USDT))
        require(q["quote"]=="USDT"
                and log["topics"][1]=="0x"+token0[2:].rjust(64,"0")
                and log["topics"][2]=="0x"+token1[2:].rjust(64,"0"),
                "PoolCreated indexed exact token identity fails")
        if q["protocol"]=="V2":
            require(log["topics"][0]==V2_CREATED
                    and "0x"+log["data"][26:66]==q["pool"], "wrong V2 PairCreated")
        else:
            require(log["topics"][0]==V3_CREATED
                    and int(log["topics"][3],16)==q["fee_pips"]
                    and "0x"+log["data"][-40:]==q["pool"],"wrong V3 PoolCreated")
        event_list=w["creation_pool_logs"]
        require(all(e["address"].lower()==q["pool"]
                    and int(e["blockNumber"],16)==block for e in event_list),
                "different block pool event")
        created_tx=log["transactionHash"]
        by_tx=[e for e in event_list if e["transactionHash"]==created_tx]
        mark=(V2_MINT if q["protocol"]=="V2" else V3_MINT)
        mints=[e for e in by_tx if e["topics"][0]==mark]
        require(len(mints)==1,"first Mint not original creation transaction")
        mint=mints[0]
        initial_liquidity=0
        active_at_creation=False
        init_quote=0
        if q["protocol"]=="V2":
            syncs=[e for e in by_tx if e["topics"][0]==V2_SYNC]
            require(len(syncs)==1
                    and int(log["logIndex"],16)<int(syncs[0]["logIndex"],16)
                    <int(mint["logIndex"],16)
                    and mint["data"]==syncs[0]["data"],
                    "V2 creation Sync and Mint not same reserves")
            r0,r1=read_word(syncs[0]["data"],0),read_word(syncs[0]["data"],1)
            require(r0>0 and r1>0,"V2 initial reserves not bilateral")
            init_quote=r0 if token0==USDT else r1
            raw_state=w["state_at_creation"]
            require(len(raw_state)==1 and raw_state[0]["key"]=="reserves"
                    and read_word(raw_state[0]["data"],0)>0
                    and read_word(raw_state[0]["data"],1)>0, "V2 creation block no closing reserves")
            active_at_creation=True
            status="FIRST_POSITIVE_V2_USDT_CREATION_MINT"
        else:
            inits=[e for e in by_tx if e["topics"][0]==V3_INIT]
            require(len(inits)==1
                    and int(log["logIndex"],16)<int(inits[0]["logIndex"],16)
                    <int(mint["logIndex"],16),
                    "V3 creation lacks ordered Initialize/Mint")
            require(len(w["state_at_creation"])==2
                    and [x["key"] for x in w["state_at_creation"]]==["liquidity","slot0"],
                    "V3 liquidity or slot0 evidence missing")
            activeL=int(w["state_at_creation"][0]["data"],16)
            sqrt=read_word(w["state_at_creation"][1]["data"],0)
            require(sqrt>0 and read_word(inits[0]["data"],0)==sqrt,
                    "V3 not initialized at original creation")
            liquidity_minted=read_word(mint["data"],1)
            init_quote=read_word(mint["data"],2 if token0==USDT else 3)
            require(liquidity_minted>0, "V3 Mint not real")
            active_at_creation=activeL>0
            initial_liquidity=activeL
            status=("FIRST_ACTIVE_V3_LIQUIDITY_CREATION_TX" if active_at_creation
                    else "MINT_OUT_OF_RANGE_ZERO_ACTIVE_LIQUIDITY_AT_CREATION")
            if not active_at_creation:
                require(init_quote==0,"unexpected quote amount in out-of-range original Mint")
        require((q["token"],q["protocol"],q["fee_pips"]) !=
                ("牛来","V3",10000) or not active_at_creation,
                "out-of-range negative control unexpectedly promoted")
        require(w["first_effective_liquidity"]=="UNRESOLVED"
                and w["qualified_entry"]=="UNRESOLVED",
                "forbidden income inference in direct original evidence")
        rows.append({
            "token":q["token"],"exact_CA":q["CA"],"protocol":q["protocol"],
            "quote":"USDT","fee_pips":q["fee_pips"],"pool":q["pool"],
            "creation_block":block,"creation_UTC":creation_datetime(log),
            "before_V2_first_reserves_by_blocks":q["baseline_block"]-block,
            "creation_tx":created_tx,
            "creation_same_tx_mint":True,
            "creation_initial_USDT_raw_18":str(init_quote),
            "creation_initial_USDT":wei_decimal(init_quote),
            "active_liquidity_raw":str(initial_liquidity) if q["protocol"]=="V3" else None,
            "active_at_creation":active_at_creation,
            "state":status,
            "earliest_whole_market_tradability":"UNRESOLVED",
            "transfer_tax_sellability":"UNRESOLVED",
            "eligible_missed_opportunity":"UNRESOLVED",
            "follower_PnL":"UNRESOLVED",
        })
    require(len(rows)==4
            and sum(x["active_at_creation"] for x in rows)==3
            and sum(x["state"]=="MINT_OUT_OF_RANGE_ZERO_ACTIVE_LIQUIDITY_AT_CREATION"
                    for x in rows)==1, "four priority pool history differs")
    return {
        "schema":"BSC_P4_PRIORITY4_COMPETITOR_CREATION_AND_LIQUIDITY_AUDIT",
        "scope":"4 explicitly tracked competitor pools out of frozen 17; 13 still require creation replay. A same-creation active liquidity is a venue observation only; no global first trade / tax / account qualification.",
        "source_manifest":[{"path":BASE+n,"git_blob_sha":s} for n,s in PINS],
        "summary":{"precommitted_competing_pools":17,"creation_event_audited":4,
                   "unexamined_other_active_competitors":13,
                   "inactive_at_reference_retained":5,
                   "positive_active_at_creation":3,"initial_mint_but_zero_active":1,
                   "earliest_global_executable_trades":0,
                   "qualified_wallet_misses":0,"production":"NO_GO"},
        "rows":rows,
    }


def main() -> None:
    p=argparse.ArgumentParser(description="Offline pinned P4 four competing pool creation proof")
    p.add_argument("--source-dir",type=Path,default=ROOT)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    a.output.write_text(json.dumps(build(load(a.source_dir)),ensure_ascii=False,indent=2)+"\n",
                        encoding="utf-8")


if __name__=="__main__":
    main()
