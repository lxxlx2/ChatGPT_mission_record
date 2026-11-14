#!/usr/bin/env python3
"""BSC P4: read-only competing pool liquidity at first positive V2/WBNB block.

Frozen denominator: 19 major CAs, 171 alternative factory reads, 22 returned
preexisting V2/USDT or V3 fee pools. Active historical liquidity by itself
does not establish first global tradability, tax/sellability or copy alpha.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
BASE="crypto-300-profit-mission/research/"
PRESENCE=("bsc-meme-address-model-v1-p4-19ca-competing171-presence-2026-10-14.json",
          "b5ae3b0f1d3d48f7b5398554b47f4748eb32ef89")
SOURCES=(
    ("bsc-meme-address-model-v1-p4-competing22-liquidity-precommit-2026-10-14.json",
     "2cc89a63db6d070ac3e5706e8d5bda198b8feee6"),
    ("bsc-meme-address-model-v1-p4-competing22-liquidity-part1-2026-10-14.json",
     "87d5f1f2c7a42cf306b69bdaa435b2d64f2109c6"),
    ("bsc-meme-address-model-v1-p4-competing22-liquidity-part2-2026-10-14.json",
     "c0c142a32a63f6275e572626798e89455181838d"),
    ("bsc-meme-address-model-v1-p4-competing22-liquidity-part3-2026-10-14.json",
     "93454d587bbf474ac52cb931b9adfcf8847224de"),
)
SCOPE=("22 nonzero competing factory pools at source V2 initial liquidity block. "
       "Active in-range Uniswap V3 liquidity() and slot0 sqrtPrice>0 or V2 both reserves>0. "
       "Does NOT prove first liquidity was before V2, liquid swap quote for any size, taxes, "
       "sellability, or profitable missed trades.")


def check(ok: bool, msg: str) -> None:
    if not ok:
        raise ValueError(msg)


def blob_sha(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def pin(root: Path, record: tuple[str,str]) -> dict:
    name,sha=record
    b=(root/name).read_bytes()
    check(blob_sha(b)==sha,"source Git SHA changed "+name)
    return json.loads(b)


def load(root: Path) -> tuple[dict,list[dict]]:
    return pin(root,PRESENCE),[pin(root,p) for p in SOURCES]


def build(presence: dict, sources: list[dict]) -> dict:
    check(presence["schema"]=="BSC_P4_FROZEN19_171_COMPETING_POOL_EXISTENCE_MATRIX"
          and presence["summary"]["historical_factory_reads"]==171
          and presence["summary"]["reads_successful"]==171
          and presence["summary"]["nonzero_preexisting_alternative_slots"]==22
          and presence["summary"]["production"]=="NO_GO",
          "historical 171-query denominator changed")
    check(len(sources)==4 and len(presence["rows"])==19,
          "wrong 19-CA source coverage")
    pre,*parts=sources
    check(pre["schema"]=="BSC_P4_FROZEN22_COMPETING_V2V3_LIQUIDITY_PRECOMMIT"
          and pre["source"]["blob_sha"]==PRESENCE[1]
          and pre["production"]=="NO_GO"
          and len(pre["cases"])==19,
          "liquidity input not source-precommitted")
    rows=[]
    for i,(part,bounds) in enumerate(zip(parts,((0,6),(7,12),(13,18))),1):
        check(part["schema"]=="BSC_P4_COMPETING22_HISTORICAL_POOL_LIQUIDITY"
              and part["part"]==i
              and part["range"]==list(bounds)
              and part["source_precommit_sha"]==SOURCES[0][1]
              and part["production"]=="NO_GO"
              and len(part["rows"])==bounds[1]-bounds[0]+1,
              "partial/reordered multicall result")
        rows.extend(part["rows"])
    check(len(rows)==19, "all 19 source rows required")
    classified=[]
    for i,(row,baseline,p) in enumerate(zip(rows,pre["cases"],presence["rows"])):
        check(row["CA"]==baseline["CA"]==p["CA"]
              and row["token"]==baseline["token"]==p["token"]
              and row["at_block"]==baseline["at_block"]==p["at_block"]
              and len(row["pools"])==len(baseline["pools"])==p["found"],
              "wrong token or altered pool universe at "+str(i))
        check(row["rpc"]==("NOT_NEEDED" if not row["pools"] else "MULTICALL3_COMPLETE"),
              "historical pool read missing")
        for pool,req in zip(row["pools"],baseline["pools"]):
            check(pool["pool"]==req["pool"] and pool["protocol"]==req["protocol"]
                  and pool["quote"]==req["quote"] and pool["fee_pips"]==req["fee_pips"]
                  and pool["query_state"]=="COMPLETE",
                  "historical candidate/source failure")
            readings=pool["reads"]
            check(len(readings)==(1 if pool["protocol"]=="V2" else 2)
                  and all(x["pool"]==pool["pool"] and x["read"]["success"]
                          for x in readings),
                  "partial V2/V3 original onchain call")
            for x in readings:
                check(x["read"]["raw_hex"].startswith("0x")
                      and x["read"]["bytes"]==len(x["read"]["raw_hex"][2:])//2,
                      "truncated raw read")
            if pool["protocol"]=="V2":
                check(readings[0]["kind"]=="getReserves"
                      and readings[0]["selector"]=="0902f1ac",
                      "V2 wrong selector")
                raw=readings[0]["read"]["raw_hex"]
                check(len(raw)>=130,"V2 reserve bytes insufficient")
                r0=int(raw[2:66],16);r1=int(raw[66:130],16)
                check(pool["stats"]=={"reserve0":str(r0),"reserve1":str(r1)},
                      "V2 raw pool reserves inconsistent")
                expected=("V2_POSITIVE_RESERVES_AT_SNAPSHOT" if r0>0 and r1>0
                          else "V2_ZERO_OR_ONE_SIDED_AT_SNAPSHOT")
            else:
                v={x["kind"]:x for x in readings}
                check(set(v)=={"liquidity","slot0"}
                      and v["liquidity"]["selector"]=="1a686502"
                      and v["slot0"]["selector"]=="3850c7bd",
                      "wrong V3 active state selectors")
                lr=v["liquidity"]["read"]["raw_hex"]
                sr=v["slot0"]["read"]["raw_hex"]
                check(len(lr)==66 and len(sr)>=66,"V3 raw read truncated")
                L=int(lr,16);sqrt=int(sr[2:66],16)
                check(pool["stats"]=={"liquidity_raw":str(L),"sqrtPriceX96":str(sqrt)},
                      "V3 liquidity/price actual RPC bytes mismatch")
                expected=("V3_INITIALIZED_ACTIVE_LIQUIDITY_AT_SNAPSHOT" if
                          L>0 and sqrt>0 else "V3_NO_ACTIVE_LIQUIDITY_AT_SNAPSHOT")
            check(pool["classification"]==expected, "false liquidity classification")
            classified.append(expected)
    active=classified.count("V2_POSITIVE_RESERVES_AT_SNAPSHOT")+classified.count(
        "V3_INITIALIZED_ACTIVE_LIQUIDITY_AT_SNAPSHOT")
    check(len(classified)==22 and active==17
          and classified.count("V2_POSITIVE_RESERVES_AT_SNAPSHOT")==2
          and classified.count("V3_INITIALIZED_ACTIVE_LIQUIDITY_AT_SNAPSHOT")==15
          and classified.count("V3_NO_ACTIVE_LIQUIDITY_AT_SNAPSHOT")==5,
          "frozen 22 competing pool classifications drifted")
    return {
        "schema":"BSC_P4_FROZEN19_COMPETING22_ACTUAL_LIQUIDITY_SNAPSHOT",
        "network":"bnb-mainnet",
        "scope":SCOPE,
        "source_manifest":[{"path":BASE+n,"git_blob_sha":sha} for n,sha in SOURCES],
        "summary":{
            "major_CAs":19,"source_competing_slots":22,
            "provider_reads_complete":22,
            "V2_USDT_with_positive_reserves":2,
            "V3_active_initialized_at_V2_baseline":15,
            "V3_no_active_liquidity_at_baseline":5,
            "total_active_competing_pool_snapshots":17,
            "earlier_first_positive_proven":0,
            "qualified_misses_proven":0,
            "production":"NO_GO",
        },
        "rows":[{**r,
                 "earlier_than_V2_liquidity":"UNRESOLVED",
                 "first_executable_quote_size":"UNRESOLVED",
                 "wallet_miss_qualification":"UNRESOLVED"} for r in rows],
    }


def main() -> None:
    p=argparse.ArgumentParser(description="Offline exact 22 alternate pool liquidity snapshot auditor")
    p.add_argument("--source-dir",type=Path,default=ROOT)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    result=build(*load(args.source_dir))
    args.output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",
                           encoding="utf-8")


if __name__=="__main__":
    main()
