#!/usr/bin/env python3
"""Source-pinned P4 market pool discovery: frozen 19 exact CA × WBNB/USDT × V2/V3.

Pool factory() nonzero return establishes only a returned pool identifier for the
limited query scope. It does not establish bytecode at the block, nonzero liquidity,
first tradability, a qualified missed opportunity or follower alpha.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PREFIX = "bsc-meme-address-model-v1-p4-19ca-factory190-"
PRECOMMIT = "bsc-meme-address-model-v1-p4-19ca-factory190-precommit-2026-10-13.json"
ROOT = "crypto-300-profit-mission/research/"
PINS = (
    "1c58853dd5f6353daf5ec040de3c759737a48888",
    "ca6e076ec2e32987806705ceb3be89a230886528",
    "73bd623504ae75822c66d434b14543b8cdc8d940",
    "a96aafa6124424431ff6a7f2fba646eb7f1f0692",
    "382470149bb0617b1e3d551a0830291ae522d400",
    "c2872499b4dca661177c65c0686fbad367ab64cb",
    "2a62aa3bb3ebb6d7113b9c8277d6fc5eff499b51",
    "6d7b0e329ab320c3bca78a30a2e09db13d44eddf",
    "53349d1a151f6cd6672dea8af1f7afb7d3f3a540",
    "1454e193d7c55de6a0ca51e3ee05bde2f8806cc9",
    "6f9f8656a704e98a82a434c3d5f6d2d5e33de993",
    "fa1c5c1026dfa959d270935622848ef7ef444254",
    "491c614956cf71e6eae495fe7925d575b3e27272",
    "057268165710296bd0321861f5e5222eca6f89ef",
    "272373d50ab56e5805841808eb6daa436d3aafae",
)
PRECOMMIT_SHA = "c9b0be420a3e456e2927953288fdd17f6e78036d"
ZERO = "0x" + "0" * 40
SCOPE = ("PancakeSwap V2 + V3(100,500,2500,10000 pips) for WBNB or USDT only; "
         "no alt quote or alternative factory/pool discovery. Factory address "
         "at historical snapshot is neither code existence nor liquidity "
         "or first tradable proof.")


def require(condition: bool, why: str) -> None:
    if not condition:
        raise ValueError(why)


def sha(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def parse_pinned(root: Path, name: str, expected: str) -> dict:
    raw = (root / name).read_bytes()
    require(sha(raw) == expected, "Git source blob drift: " + name)
    return json.loads(raw)


def build(plan: dict, shards: list[dict]) -> dict:
    require(plan["schema"] == "BSC_MEME_ADDRESS_MODEL_V1_P4_19CA_FIXED_WBNB_USDT_POOL_FACTORY_QUERY_PLAN"
            and plan["summary"] == {
                "frozen_CA": 19, "quotes": 2, "protocol_fees_per_quote": 5,
                "total_factory_calls": 190}
            and plan["production"] == "NO_GO"
            and len(plan["queries"]) == 190, "19CA/190 fixed scope changed")
    require(len(shards) == 15, "missing source shards")
    all_rows = []
    index = 0
    for part, obj in enumerate(shards, 1):
        require(obj["schema"] == "BSC_P4_FACTORY190_QUERY_PART"
                and obj["part"] == part
                and obj["precommit_sha"] == PRECOMMIT_SHA
                and obj["production"] == "NO_GO"
                and obj["range"] == [index, index + len(obj["records"]) - 1],
                "source partition changed")
        for x in obj["records"]:
            require(x["index"] == index
                    and x["state"] == "DIRECT_HISTORICAL_FACTORY"
                    and isinstance(x["raw"], str)
                    and len(x["raw"]) == 66 and x["raw"].startswith("0x")
                    and x["pool"] == "0x" + x["raw"][-40:].lower(),
                    "invalid factory return at index " + str(index))
            all_rows.append(x)
            index += 1
    require(index == 190 and len({x["index"] for x in all_rows}) == 190,
            "incomplete/duplicate factory reads")
    rows = []
    found = set()
    for i in range(19):
        queries = plan["queries"][i*10:(i+1)*10]
        require(len(queries) == 10
                and len({q["token_CA"] for q in queries}) == 1
                and [(q["quote_symbol"],q["protocol"],q["fee_pips"]) for q in queries]
                == [(quote, protocol, fee)
                    for quote in ("WBNB","USDT")
                    for protocol,fee in (("V2",None),("V3",100),("V3",500),
                                         ("V3",2500),("V3",10000))], "changed token/fee coverage")
        slots = []
        for j,q in enumerate(queries):
            item = all_rows[i*10+j]
            is_pool = item["pool"] != ZERO
            if is_pool:
                require(item["pool"] not in found, "duplicate pool address across candidate slots")
                found.add(item["pool"])
            slots.append({
                "quote_symbol": q["quote_symbol"], "protocol": q["protocol"],
                "fee_pips": q["fee_pips"], "factory": q["factory"],
                "pool_address": item["pool"] if is_pool else None,
                "factory_pool_state": ("RETURNED_NONZERO" if is_pool else
                                       "FACTORY_ZERO_FOR_FIXED_PAIR_AT_SNAPSHOT"),
                "pool_exists_at_snapshot": "UNVERIFIED_CODE",
                "first_liquidity_UTC": "UNRESOLVED",
                "tradable_at_launch": "UNRESOLVED",
                "liquidity_BNB_at_launch": "UNRESOLVED",
            })
        rows.append({
            "token": queries[0]["token"], "exact_CA": queries[0]["token_CA"],
            "queries": 10, "nonzero_factory_pools": sum(bool(s["pool_address"]) for s in slots),
            "zero_factory_slots": sum(not s["pool_address"] for s in slots),
            "matched_pools": slots, "first_executable_pool": "UNRESOLVED",
            "qualified_miss": "UNRESOLVED",
        })
    require(len({x["exact_CA"] for x in rows}) == 19
            and len(found) == 161 and sum(x["zero_factory_slots"] for x in rows) == 29,
            "market pool matrix source-aggregate drift")
    return {
        "schema":"BSC_MEME_P4_FIXED_19CA_190_FACTORY_POOL_DISCOVERY_MATRIX",
        "network":"bnb-mainnet",
        "snapshot_block":plan["as_of_snapshot_block"],
        "snapshot_UTC":plan["as_of_snapshot_utc"],
        "scope":SCOPE,
        "source_manifest": ([{"path":ROOT+PRECOMMIT,"git_blob_sha":PRECOMMIT_SHA}] +
                            [{"path":ROOT+PREFIX+f"part{i+1}-2026-10-13.json",
                              "git_blob_sha":pin} for i,pin in enumerate(PINS)]),
        "summary":{"major_exact_CAs":19,"quoted_assets":2,"scope_slots_per_CA":10,
                   "required_factory_calls":190,"parsed_factory_calls":190,
                   "failed_factory_calls":0,"factory_nonzero_slots":161,
                   "factory_zero_slots":29,"unique_nonzero_pool_addresses":161,
                   "major_CA_with_at_least_one_nonzero_pool":19,
                   "code_verified_for_nonzero_pools":0,
                   "first_executable_timestamp_confirmed":0,
                   "qualified_profitable_misses":0,"production":"NO_GO"},
        "wallet_universe_23_untouched":True,
        "profit_from_pool_discovery":"UNRESOLVED",
        "rows":rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="offline P4 19CA factory190 deterministic audit")
    parser.add_argument("--source-dir",type=Path,default=HERE)
    parser.add_argument("--output",type=Path,required=True)
    a = parser.parse_args()
    plan = parse_pinned(a.source_dir,PRECOMMIT,PRECOMMIT_SHA)
    sources = [parse_pinned(a.source_dir,PREFIX+f"part{i+1}-2026-10-13.json",pin)
               for i,pin in enumerate(PINS)]
    a.output.write_text(json.dumps(build(plan,sources),ensure_ascii=False,indent=2)+"\n",
                        encoding="utf-8")


if __name__ == "__main__":
    main()
