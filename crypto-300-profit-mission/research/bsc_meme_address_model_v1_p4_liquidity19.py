#!/usr/bin/env python3
"""Frozen 19 exact BSC Meme CAs: first positive Pancake V2 WBNB pool reserves.

All original evidence is SHA pinned and complete, including 41 source RPC
windows for GIGGLE where creation had no Mint or Sync. First V2 liquidity
does NOT imply earliest global venue, transfer taxes, buy/sell executability,
trader PnL, qualified misses, or follower alpha. Read-only and offline.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PREFIX = "crypto-300-profit-mission/research/"
SOURCE = [
    ("bsc-meme-address-model-v1-p4-19ca-factory190-discovery-2026-10-13.json", "2c8682c0ddd14f3c8f0683e970d0523177a7602e"),
    ("bsc-meme-address-model-v1-p4-remaining15-paircreated-part1-2026-10-14.json", "9fc16c6d24263d102202d8727d174d65ab0a766e"),
    ("bsc-meme-address-model-v1-p4-remaining15-paircreated-group2a-2026-10-14.json", "c6b79a09ef41d177ee6459ef424dd235c1fbb2ae"),
    ("bsc-meme-address-model-v1-p4-remaining15-paircreated-group2b-2026-10-14.json", "13ecd41bdedef5f5bd402b1b144d3d3060bdb100"),
    ("bsc-meme-address-model-v1-p4-remaining15-paircreated-group3a-2026-10-14.json", "f0ac9abf5fccbe5e162cf225f4cefd4c00f3b699"),
    ("bsc-meme-address-model-v1-p4-remaining15-paircreated-group3b-2026-10-14.json", "8f0ab0c3be4157b0ca3734f8c4707968d304ca32"),
    ("bsc-meme-address-model-v1-p4-remaining15-initial-mint-group1-2026-10-14.json", "a37473c360b9fcdc1c03e1c98658bf266c702770"),
    ("bsc-meme-address-model-v1-p4-remaining15-initial-mint-group2-2026-10-14.json", "926941e5a61a4036224972e39a849e1ab810887b"),
    ("bsc-meme-address-model-v1-p4-remaining15-initial-mint-group3-2026-10-14.json", "20c7ac7779714a120a604962ff94c4c883ec5220"),
    ("bsc-meme-address-model-v1-p4-giggle-delayed-first-liquidity-2026-10-14.json", "f88ce5f2227a61318c27b9504c95467a8696d872"),
    ("bsc-meme-address-model-v1-p4-priority4-v2-first-mint-reserves-2026-10-13.json", "ae8a3843baab0941ca5dd3143dbdc82057b82ba3"),
]
GIGGLE_SHAS = (
    "9ffb7e76e6b26709f4809b8a07b355b19ab83a77",
    "ac261831db0e43e28f3258d7d337c42197363ed0",
    "7d3955ece2ce8aceb2a7197740d22f3e0462f02b",
    "aa2122384ece5831ecf6145c6bc853d77ceca0bd",
    "5085b2040c9f41eda368d81bf81f528a20ecbaf2",
    "bad0e673a15142bf447da04b8183736e493d822c",
)
QUOTE = "0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c"
FACTORY = "0xca143ce32fe78f1f7019d7d551a6402fc5350c73"
PAIR = "0x0d3648bd0f6ba80134a33ba9275ac585d9d315f0ad8355cddefde31afa28d0e9"
SYNC = "0x1c411e9a96e071241c2f21f7726b17ae89e3cab4c78be50e062b03a9fffbbad1"
MINT = "0x4c209b5fc8ad50758f13e2e1088ba56a560dff690a1c6fef26394f4c03821c4f"
SCHEMA = "BSC_P4_FROZEN19_V2_WBNB_FIRST_POSITIVE_LIQUIDITY_MATRIX"
SCOPE = ("Exact 19 major CAs PancakeSwap V2 WBNB pool only, PairCreated plus first positive pool Sync/Mint; "
         "not global first tradability among V3/USDT/other DEX, not profitable entry")


def verify(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def git_sha(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def pinned(root: Path, name: str, expected: str) -> dict:
    raw = (root / name).read_bytes()
    verify(git_sha(raw) == expected, "source SHA drift " + name)
    return json.loads(raw)


def load(root: Path) -> list[dict]:
    return [pinned(root, *item) for item in SOURCE]


def iso(event: dict) -> str:
    verify(event.get("blockTimestamp") is not None, "missing original block timestamp")
    return datetime.fromtimestamp(int(event["blockTimestamp"],16),tz=timezone.utc).isoformat(
        timespec="milliseconds").replace("+00:00","Z")


def amount_wei(event: dict) -> tuple[int,int]:
    s = event["data"]
    verify(s.startswith("0x") and len(s) == 130, "expected exact V2 Sync/Mint two uint112/uint256 amounts")
    return int(s[2:66],16),int(s[66:130],16)


def decimal_18(wei: int) -> str:
    x, y = divmod(wei,10**18)
    suffix = str(y).zfill(18).rstrip("0")
    return str(x)+("."+suffix if suffix else "")


def verify_giggle_raw(root: Path, witness: dict) -> None:
    verify(witness["scan_blob_manifest"] == list(GIGGLE_SHAS)
           and witness["scanned_block_windows"] == 41
           and witness["all_prior_sync_events"] == 0
           and witness["creation_block"] == 61963318
           and witness["positive_liquidity_block"] == 61963725
           and witness["production"] == "NO_GO", "GIGGLE 407-block interval evidence changed")
    windows = []
    for i, sha in enumerate(GIGGLE_SHAS,1):
        name = f"bsc-meme-address-model-v1-p4-giggle-sync-raw-part{i}-2026-10-14.json"
        obj = pinned(root,name,sha)
        verify(obj["production"] == "NO_GO"
               and obj["pool"] == witness["pool"], "GIGGLE wrong source pool")
        for row in obj.get("windows",obj.get("pages",[])):
            windows.append((row.get("part",row.get("idx")),
                            row.get("fromBlock",row.get("lo")),
                            row.get("toBlock",row.get("hi")),
                            row.get("events",row.get("logs",[]))))
    windows.sort()
    verify(len(windows)==41, "missing Sync range")
    events = []
    for index,(i,lo,hi,logs) in enumerate(windows):
        verify(index==i and lo==61963318+index*10
               and hi==min(61963725,lo+9), "Sync range gap/overlap")
        events.extend(logs)
    verify(len(events)==1
           and events[0]["block"]==61963725
           and events[0]["hash"]==witness["first_positive_sync_event"]["hash"]
           and events[0]["data"]==witness["first_positive_sync_event"]["data"],
           "early Sync exists or final Sync not proven")
    verify(witness["zero_to_positive_boundary"]["before_reserves_raw"] == ["0","0"]
           and all(int(x)>0 for x in witness["zero_to_positive_boundary"]["after_reserves_raw"]),
           "GIGGLE first-positive source lacks reserves")


def build(d: list[dict], root: Path) -> dict:
    verify(len(d)==len(SOURCE), "source array incomplete")
    base, *rest = d
    verify(base["summary"]["major_exact_CAs"]==19
           and base["summary"]["required_factory_calls"]==190
           and base["summary"]["production"]=="NO_GO"
           and len(base["rows"])==19, "frozen exact 19CA universe changed")
    pair_rows = [r for obj in d[1:6] for r in obj.get("records",obj.get("entries",[]))]
    mint_rows = [r for obj in d[6:9] for r in obj["records"]]
    pair = {x.get("CA",x.get("ca")):x for x in pair_rows}
    mint = {x["index"]:x for x in mint_rows}
    gig, priority = d[9],{x["ca"]:x for x in d[10]["records"]}
    verify(len(pair)==len(mint)==15 and len(priority)==4
           and {x["index"] for x in pair_rows}==set(range(15))
           and {x["index"] for x in mint_rows}==set(range(15)),
           "missing or duplicated original fifteen pools")
    verify_giggle_raw(root,gig)
    output = []
    for token in base["rows"]:
        ca=token["exact_CA"]
        historical=priority.get(ca)
        discovery=pair.get(ca)
        verify((historical is None) != (discovery is None), "unknown/duplicate CA")
        expected=next(q["pool_address"] for q in token["matched_pools"]
                      if q["protocol"]=="V2" and q["quote_symbol"]=="WBNB")
        if historical:
            pool=historical["pool"]
            created=historical["block"]
            positive=created
            event=historical["pair_created_event"]
            sync=historical["initial_sync_event"]
            minted=historical["initial_mint_event"]
            first_tx=minted["transactionHash"]
            created_at=historical["creation_UTC"]
            positive_at=created_at
            same_tx=True
            state="CREATION_TX_INITIAL_POSITIVE_V2_RESERVES"
            verify(first_tx==event["transactionHash"]==sync["transactionHash"]
                   and historical["mint_same_tx"] is True, "priority mint not source-signed")
        else:
            pool=discovery["pool"]
            created=discovery.get("candidate_creation_block",discovery.get("block"))
            event=discovery.get("pair_created_event",discovery.get("event"))
            created_at=iso(event)
            trace=mint[discovery["index"]]
            verify(trace["pool"]==pool and trace["block"]==created
                   and trace["query_status"]=="COMPLETE", "wrong scope or incomplete pool logs")
            if token["token"] == "GIGGLE":
                verify(pool==gig["pool"]
                       and created==gig["creation_block"]
                       and trace["classification"]=="INITIAL_RESERVE_NOT_PROVEN"
                       and len(trace["all_events"])==0, "GIGGLE must have no creation Mint")
                positive=gig["positive_liquidity_block"]
                minted=gig["first_positive_mint_event"]
                sync_data=gig["first_positive_sync_event"]
                verify(sync_data["hash"]==minted["transactionHash"]
                       and sync_data["data"]==minted["data"]
                       and minted["topics"][0]==MINT
                       and int(sync_data["logIndex"],16)<int(minted["logIndex"],16),
                       "GIGGLE first mint not linked to first Sync")
                sync={"data":sync_data["data"],"topics":[SYNC],
                      "transactionHash":sync_data["hash"]}
                positive_at=iso(minted)
                first_tx=minted["transactionHash"]
                same_tx=False
                state="DELAYED_FIRST_POSITIVE_V2_RESERVES_ALL_SYNC_SCANNED"
                verify(amount_wei(sync)==tuple(int(x) for x in
                       gig["zero_to_positive_boundary"]["after_reserves_raw"]),
                       "GIGGLE onchain exact after-reserve drift")
            else:
                matches=[x for x in trace["all_events"]
                         if x["transactionHash"]==event["transactionHash"]]
                syncs=[x for x in matches if x["topics"][0]==SYNC]
                mints=[x for x in matches if x["topics"][0]==MINT]
                verify(len(syncs)==len(mints)==1
                       and trace["classification"]=="INITIAL_POSITIVE_RESERVE_SAME_TX",
                       "initial liquidity not same creation tx")
                sync,minted=syncs[0],mints[0]
                positive=created
                positive_at=created_at
                first_tx=event["transactionHash"]
                same_tx=True
                state="CREATION_TX_INITIAL_POSITIVE_V2_RESERVES"
                verify(trace["same_tx_reserves"]==list(map(str,amount_wei(sync))),
                       "creation Sync changed from original snapshot")
        verify(pool==expected and event["address"].lower()==FACTORY
               and event["topics"][0]==PAIR
               and "0x"+event["data"][26:66].lower()==pool
               and int(event["blockNumber"],16)==created,
               "onchain PairCreated proof invalid")
        t0,t1=sorted((ca,QUOTE))
        verify(event["topics"][1]=="0x"+t0[2:].rjust(64,"0")
               and event["topics"][2]=="0x"+t1[2:].rjust(64,"0"), "wrong pool token0/token1")
        reserves=amount_wei(sync)
        verify(all(x>0 for x in reserves)
               and amount_wei(minted)==reserves
               and minted["topics"][0]==MINT
               and sync["topics"][0]==SYNC
               and minted["transactionHash"]==first_tx
               and sync["transactionHash"]==first_tx,
               "not proven same transaction first positive reserves")
        if same_tx:
            verify(int(event["logIndex"],16)<int(sync["logIndex"],16)
                   <int(minted["logIndex"],16), "incorrect factory Mint event ordering")
        quote_wei=reserves[0 if t0==QUOTE else 1]
        output.append({
            "token":token["token"],"exact_CA":ca,"v2_wbnb_pool":pool,
            "pair_creation_block":created,"pair_creation_UTC":created_at,
            "first_positive_reserves_block":positive,
            "first_positive_reserves_UTC":positive_at,
            "liquidity_delay_blocks":positive-created,
            "first_positive_WBNB_wei":str(quote_wei),
            "first_positive_WBNB_BNB":decimal_18(quote_wei),
            "first_positive_sync_tx_hash":first_tx,
            "first_liquidity_evidence_state":state,
            "same_creation_tx_positive_liquidity":same_tx,
            "full_venue_first_tradable":"UNRESOLVED",
            "token_tax_sellability":"UNRESOLVED",
            "qualified_wallet_misses":"UNRESOLVED",
            "follower_alpha":"UNRESOLVED",
        })
    verify(len(output)==19
           and len({x["exact_CA"] for x in output})==19
           and len({x["v2_wbnb_pool"] for x in output})==19
           and sum(x["same_creation_tx_positive_liquidity"] for x in output)==18
           and sum(x["liquidity_delay_blocks"]>0 for x in output)==1
           and next(x for x in output if x["token"]=="GIGGLE")["liquidity_delay_blocks"]==407,
           "incorrect universe or first-liquidity classification")
    return {
        "schema":SCHEMA,"scope":SCOPE,
        "source_manifest":[{"path":PREFIX+n,"git_blob_sha":sha} for n,sha in SOURCE],
        "summary":{
            "exact_major_CAs":19,
            "v2_wbnb_pool_creation_verified":19,
            "first_positive_v2_wbnb_reserves_verified":19,
            "first_positive_same_creation_tx":18,
            "delayed_first_liquidity":1,
            "delayed_giggle_blocks":407,
            "global_first_tradable_proven":0,
            "qualified_misses_proven":0,
            "follower_alpha_proven":0,
            "production":"NO_GO",
        },
        "rows":output,
    }


def main() -> None:
    p=argparse.ArgumentParser(description="BSC P4 offline 19 major V2 first liquidity evidence")
    p.add_argument("--source-dir",type=Path,default=ROOT)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    result=build(load(args.source_dir),args.source_dir)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")


if __name__ == "__main__":
    main()
