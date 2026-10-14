#!/usr/bin/env python3
"""Reproduce P4 first active liquidity for the four preselected competitor pools.

Read only, immutable Git blob inputs. Scoped V2/USDT and V3/USDT evidence
does not establish first tradable market, token sellability, entry eligibility
or profitable delayed copy trading.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PREFIX = "crypto-300-profit-mission/research/"
SOURCES = (
 ("bsc-meme-address-model-v1-p4-priority4-competition-initial-pool-states-2026-10-14.json",
  "e0e91dd1a19fc7b3e56eedc95d800d0d8c0cdd72"),
 ("bsc-meme-address-model-v1-p4-niulai-v3-10000-delayed-active-proof-2026-10-14.json",
  "7a5e74b5fa653b7e2a51f1f86e2200510c8a5c88"),
 ("bsc-meme-address-model-v1-p4-19ca-v2-wbnb-first-positive-liquidity-2026-10-14.json",
  "9fbc8bdaeb9df342a4d200fefb0ebd48b746b903"),
)
SUMMARY = {
 "frozen_competitor_pools": 4, "creation_events_confirmed": 4,
 "first_active_block_evidence": 4, "positive_at_creation": 3,
 "delayed_in_range_active": 1, "delayed_NIULAI_V3_10000_blocks": 17,
 "verified_before_V2_WBNB_baseline": 4, "qualified_misses": 0,
 "production": "NO_GO",
}
SCHEMA = "BSC_P4_PRIORITY4_COMPETING_FIRST_ACTIVE_POOL_LIQUIDITY_MATRIX"
SCOPE = ("Four pre-frozen MARSCOIN/牛来 V2 USDT/V3 USDT competitor pools only. "
 "Positive V3 liquidity is in-range active liquidity, NOT full-venue tradability, "
 "adequate depth, executed swap viability or profitable opportunity.")
TOPIC_V2 = "0x0d3648bd0f6ba80134a33ba9275ac585d9d315f0ad8355cddefde31afa28d0e9"
TOPIC_V3 = "0x783cca1c0412dd0d695e784568c96da2e9c22ff989357a2e8b1d9b2b4e6b7118"
TOPIC_SYNC = "0x1c411e9a96e071241c2f21f7726b17ae89e3cab4c78be50e062b03a9fffbbad1"
TOPIC_MINT_V2 = "0x4c209b5fc8ad50758f13e2e1088ba56a560dff690a1c6fef26394f4c03821c4f"
TOPIC_INIT_V3 = "0x98636036cb66a9c19a37435efc1e90142190214e8abeb821bdba3f2990dd4c95"
TOPIC_MINT_V3 = "0x7a53080ba414158be7ec69b987b5fb7d07dee101fe85488f0853ae16239d0bde"
TOPIC_MINT_EVENT = "0x19b47279256b2a23a1665c810c8d55a1758940ee09377d4f8d26497a3577dc83"
USDT = "0x55d398326f99059ff775485246999027b3197955"
CASES = (
 ("牛来", "V2", None, 116207845, 116207845),
 ("牛来", "V3", 2500, 116156658, 116156658),
 ("牛来", "V3", 10000, 115919188, 115919205),
 ("MARSCOIN", "V3", 10000, 112642885, 112642885),
)


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def blob_sha(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def load(root: Path) -> list[dict]:
    out=[]
    for filename,pin in SOURCES:
        data=(root/filename).read_bytes()
        require(blob_sha(data)==pin, "source drift: "+filename)
        out.append(json.loads(data))
    return out


def utc_event(event: dict) -> str:
    return datetime.fromtimestamp(
        int(event["blockTimestamp"],16),tz=timezone.utc
    ).isoformat(timespec="milliseconds").replace("+00:00","Z")


def rawword(data: str, index: int) -> int:
    require(data.startswith("0x") and len(data)>=2+(index+1)*64, "event missing uint256")
    return int(data[2+64*index:2+64*(index+1)],16)


def verify_delayed(witness: dict, expected_creation: int, pool: str) -> None:
    require(witness["schema"]=="BSC_P4_NIULAI_V3_USDT_10000_FIRST_ACTIVE_LIQUIDITY_PROOF"
            and witness["pool"]==pool
            and witness["pool_creation_block"]==expected_creation
            and witness["first_active_block"]==expected_creation+17
            and witness["delay_blocks"]==17
            and witness["production"]=="NO_GO"
            and len(witness["windows"])==10
            and witness["earlier_pool_logs_in_window"]==0,
            "delayed in-range source incomplete")
    all_events=[]
    for i,page in enumerate(witness["windows"]):
        require(page["index"]==i and page["state"]=="COMPLETE"
                and page["lo"]==expected_creation+1+10*i
                and page["hi"]==expected_creation+10+10*i, "unscanned or overlapped historic interval")
        all_events.extend(page["logs"])
    require(len(all_events)==5
            and all_events[0]["topics"][0]==TOPIC_MINT_EVENT
            and int(all_events[0]["blockNumber"],16)==expected_creation+17
            and all(e["topics"][0]==TOPIC_MINT_EVENT for e in all_events),
            "earlier pool event or missing first Mint")
    require(all_events[0]==witness["first_mint_event"], "first mint not same source")
    states=witness["historical_state"]
    require([x["block"] for x in states]==[
        expected_creation,expected_creation+16,expected_creation+17
    ], "missing boundary historical state")
    require(int(states[0]["liquidity_raw"],16)==int(states[1]["liquidity_raw"],16)==0
            and int(states[2]["liquidity_raw"],16)>0,
            "first in-range liquidity not demonstrated")
    require(all(rawword(s["slot0_raw"],0)>0 for s in states),
            "historical V3 slot0 uninitialized")


def build(docs: list[dict]) -> dict:
    require(len(docs)==3,"expected frozen sources")
    source,delayed,baseline=docs
    require(source["schema"]=="BSC_P4_PRIORITY4_COMPETING_INITIAL_POOL_STATES"
            and source["production"]=="NO_GO"
            and len(source["records"])==4,
            "source scope changed")
    require(baseline["summary"]["exact_major_CAs"]==19
            and baseline["summary"]["production"]=="NO_GO",
            "baseline 19 changed")
    baseline_by_ca={x["exact_CA"]:x for x in baseline["rows"]}
    require(len(baseline_by_ca)==19,"duplicate 19-CA baseline")
    rows=[]
    seen=set()
    for rec,(token,protocol,fee,creation,first) in zip(source["records"],CASES):
        identity=(rec["CA"],rec["pool"])
        require(identity not in seen, "duplicate competitor pool")
        seen.add(identity)
        require(rec["token"]==token and rec["protocol"]==protocol
                and rec["fee_pips"]==fee
                and rec["created_block"]==creation
                and rec["quote"]=="USDT"
                and rec["pool"].startswith("0x")
                and len(rec["pool"])==42
                and rec["read_status"]=="COMPLETE",
                "wrong frozen competitor")
        event=rec["event"]
        require(int(event["blockNumber"],16)==creation
                and event["data"][-40:].lower()==rec["pool"][2:]
                and len(event["topics"])==(3 if protocol=="V2" else 4)
                and event["topics"][0]==(TOPIC_V2 if protocol=="V2" else TOPIC_V3)
                and {t[-40:].lower() for t in event["topics"][1:3]}=={rec["CA"][2:],USDT[2:]},
                "pool creation factory event invalid")
        if protocol=="V3":
            require(int(event["topics"][3],16)==fee,"Pancake V3 fee mismatch")
        logs=rec["creation_block_logs"]
        require(all(x["address"].lower()==rec["pool"] and
                    int(x["blockNumber"],16)==creation for x in logs),
                "creation pool event belongs to different pool/block")
        creation_tx=[x for x in logs if x["transactionHash"]==event["transactionHash"]]
        topics={x["topics"][0] for x in creation_tx}
        if protocol=="V2":
            require(TOPIC_SYNC in topics and TOPIC_MINT_V2 in topics
                    and len(rec["raw_read_hex"]["getReserves"])>=130,
                    "V2 no source Mint/Sync")
            sync=next(x for x in creation_tx if x["topics"][0]==TOPIC_SYNC)
            mint=next(x for x in creation_tx if x["topics"][0]==TOPIC_MINT_V2)
            r0,r1=rawword(sync["data"],0),rawword(sync["data"],1)
            require(int(sync["logIndex"],16)<int(mint["logIndex"],16)
                    and r0==rawword(mint["data"],0)
                    and r1==rawword(mint["data"],1)
                    and min(r0,r1)>0
                    and rec["creation_block_state"]=={"reserve0_raw":str(r0),"reserve1_raw":str(r1)},
                    "V2 positive first deposit not proven")
            check=rec["raw_read_hex"]["getReserves"]
            require(rawword(check,0)>0 and rawword(check,1)>0,
                    "V2 creation-block reserves zero")
            active=True
        else:
            require({TOPIC_INIT_V3,TOPIC_MINT_V3}.issubset(topics),
                    "V3 no Initialize and Mint in creation block")
            init=next(x for x in creation_tx if x["topics"][0]==TOPIC_INIT_V3)
            mint=next(x for x in creation_tx if x["topics"][0]==TOPIC_MINT_V3)
            require(int(init["logIndex"],16)<int(mint["logIndex"],16),
                    "V3 Initialize after Mint")
            liq=int(rec["raw_read_hex"]["liquidity"],16)
            sqrt=rawword(rec["raw_read_hex"]["slot0"],0)
            require(str(liq)==rec["creation_block_state"]["liquidity_raw"]
                    and str(sqrt)==rec["creation_block_state"]["sqrtPriceX96"]
                    and sqrt>0, "V3 historical snapshot mismatch")
            active=liq>0
        require(active==(first==creation),"first active inconsistent with creation state")
        baseline_row=baseline_by_ca[rec["CA"]]
        require(baseline_row["token"]==token
                and baseline_row["first_positive_reserves_block"]==rec["baseline_first_V2_liquidity_block"]
                and first<rec["baseline_first_V2_liquidity_block"],
                "wrong causal earliest known reference")
        if first>creation:
            require(rec["token"]=="牛来" and protocol=="V3" and fee==10000,
                    "unexpected delayed candidate")
            verify_delayed(delayed,creation,rec["pool"])
            at=utc_event(delayed["first_mint_event"])
            kind="V3_FIRST_IN_RANGE_MINT_AFTER_CREATION"
        else:
            at=utc_event(event)
            kind=("V2_SYNC_MINT_SAME_PAIRCREATED_TX" if protocol=="V2"
                  else "V3_INITIALIZE_MINT_SAME_POOLCREATED_TX")
        rows.append({
            "token":token,"CA":rec["CA"],"protocol":protocol,"quote":rec["quote"],
            "fee_pips":fee,"pool":rec["pool"],"pool_creation_block":creation,
            "creation_UTC":utc_event(event),"first_active_liquidity_block":first,
            "first_active_liquidity_UTC":at,"delay_blocks":first-creation,
            "source_event_kind":kind,
            "precedes_known_V2_WBNB_first_reserve_by_blocks":
                rec["baseline_first_V2_liquidity_block"]-first,
            "raw_initial_pool_state":rec["creation_block_state"],
            "at_creation_active":active,
            "first_globally_tradable":"UNRESOLVED",
            "gas_slippage_and_token_selling":"UNRESOLVED",
            "qualifying_missed_trade":"UNRESOLVED",
            "follower_alpha":"UNRESOLVED",
        })
    require(len(rows)==4 and sum(x["delay_blocks"]==17 for x in rows)==1
            and sum(x["at_creation_active"] for x in rows)==3,
            "wrong historical evidence totals")
    return {"schema":SCHEMA,"scope":SCOPE,
            "source_manifest":[{"path":PREFIX+n,"git_blob_sha":sha} for n,sha in SOURCES],
            "summary":SUMMARY,"rows":rows}


def main() -> None:
    p=argparse.ArgumentParser(description="Offline pinned BSC P4 4 competing pools validator")
    p.add_argument("--source-dir",type=Path,default=ROOT)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    a.output.write_text(json.dumps(build(load(a.source_dir)),ensure_ascii=False,indent=2)+"\n",
                        encoding="utf-8")


if __name__=="__main__":
    main()
