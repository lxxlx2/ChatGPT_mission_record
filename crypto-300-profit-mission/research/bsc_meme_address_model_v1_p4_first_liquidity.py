#!/usr/bin/env python3
"""BSC P4: independently replay four first-pool V2 WBNB Mint/Sync proofs.

Read-only offline: a same-block positive initial reserve is not evidence that
another DEX pool started later, the token is transferable/sellable, or that
the user could have copied the exact trade with real-world slippage/gas.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PATH_ROOT = "crypto-300-profit-mission/research/"
SRC_NAME = "bsc-meme-address-model-v1-p4-priority4-v2-first-mint-reserves-2026-10-13.json"
SRC_BLOB = "ae8a3843baab0941ca5dd3143dbdc82057b82ba3"
PRECOMMIT_BLOB = "fdaf91ec445a7b94c24508335ce9a6f017326c73"
BINARY_BLOB = "702784130e13c086b685caa0702e89fb0a36d7f3"
WBNB = "0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c"
FACTORY = "0xca143ce32fe78f1f7019d7d551a6402fc5350c73"
TOPICS = {
    "PairCreated": "0x0d3648bd0f6ba80134a33ba9275ac585d9d315f0ad8355cddefde31afa28d0e9",
    "Sync": "0x1c411e9a96e071241c2f21f7726b17ae89e3cab4c78be50e062b03a9fffbbad1",
    "Mint": "0x4c209b5fc8ad50758f13e2e1088ba56a560dff690a1c6fef26394f4c03821c4f",
    "Swap": "0xd78ad95fa46c994b6551d0da85fc275fe613ce37657fb8d5e3d130840159d822",
}


def require(condition: bool, detail: str) -> None:
    if not condition:
        raise ValueError(detail)


def git_blob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def load(root: Path) -> dict:
    blob = (root / SRC_NAME).read_bytes()
    require(git_blob(blob) == SRC_BLOB, "historical event Git SHA mismatch")
    return json.loads(blob)


def build(source: dict) -> dict:
    require(source["schema"] == "BSC_MEME_P4_PRIORITY4_V2_FIRST_MINT_RESERVE_WITNESS"
            and source["production"] == "NO_GO"
            and source["source_precommit_sha"] == PRECOMMIT_BLOB
            and source["binary_proof_git_blob_sha"] == BINARY_BLOB
            and source["summary"]["pools"] == 4
            and source["summary"]["initial_reserves_positive_WBNB"] == 4
            and len(source["records"]) == 4,
            "source freeze or coverage invalid")
    expected = [("龙虾", 83636128), ("币安人生", 63454407),
                ("MARSCOIN", 112668701), ("牛来", 116314917)]
    rows = []
    for record, (token, block) in zip(source["records"], expected):
        p, s, m = (record[k] for k in ("pair_created_event",
                                      "initial_sync_event", "initial_mint_event"))
        require(record["token"] == token and record["block"] == block
                and record["factory"] == FACTORY and record["quote_CA"] == WBNB,
                "wrong frozen target or protocol")
        t0, t1 = record["token0"], record["token1"]
        require(set((t0, t1)) == {record["ca"], WBNB} and t0 < t1,
                "pair token ordering/identity invalid")
        require(record["factory_getPair_before"] == "0x" + "0" * 64
                and record["factory_getPair_at"].endswith(record["pool"][2:]),
                "factory creation boundary missing")
        require(p["address"].lower() == FACTORY
                and s["address"].lower() == m["address"].lower() == record["pool"]
                and p["topics"][0] == TOPICS["PairCreated"]
                and s["topics"][0] == TOPICS["Sync"]
                and m["topics"][0] == TOPICS["Mint"],
                "unrelated events masquerading as initial Mint/Sync")
        require(p["topics"][1] == "0x" + t0[2:].rjust(64, "0")
                and p["topics"][2] == "0x" + t1[2:].rjust(64, "0")
                and p["data"][2:66][-40:] == record["pool"][2:]
                and p["transactionHash"] == s["transactionHash"] == m["transactionHash"],
                "creation and mint not in exact same transaction")
        require(int(p["blockNumber"], 16) == int(s["blockNumber"], 16)
                == int(m["blockNumber"], 16) == block
                and int(p["logIndex"], 16) < int(s["logIndex"], 16)
                < int(m["logIndex"], 16), "wrong event sequence")
        for item in (s, m):
            require(isinstance(item["data"], str)
                    and item["data"].startswith("0x")
                    and len(item["data"]) == 130, "event amount invalid")
        amounts = [int(s["data"][2:66],16), int(s["data"][66:130],16)]
        mint = [int(m["data"][2:66],16), int(m["data"][66:130],16)]
        require(amounts == mint
                and amounts == [int(x) for x in record["first_initial_mint_reserves_raw"]]
                and all(x > 0 for x in amounts), "initial reserves not proven")
        wbnb_wei = amounts[0 if t0 == WBNB else 1]
        displayed = format(Decimal(wbnb_wei) / Decimal(10**18), "f")
        require(str(wbnb_wei) == record["initial_wbnb_wei"]
                and Decimal(displayed) == Decimal(record["initial_wbnb_BNB"]),
                "quote amount mismatch")
        seconds = int(p["blockTimestamp"],16)
        from datetime import datetime, timezone
        iso = datetime.fromtimestamp(seconds, tz=timezone.utc).isoformat(timespec="milliseconds").replace("+00:00","Z")
        require(iso == record["creation_UTC"]
                and record["mint_same_tx"] is True
                and record["event_order_verified"] is True
                and record["first_positive_reserves_at_pair_creation_tx"] is True,
                "timestamp/frozen mint testimony inconsistent")
        swaps = record["creation_block_swaps"]
        require(record["confirmed_execution_same_block"] is bool(swaps)
                and all(e["topics"][0] == TOPICS["Swap"]
                        and e["address"].lower() == record["pool"]
                        and int(e["blockNumber"],16) == block
                        and int(e["logIndex"],16) > int(m["logIndex"],16)
                        for e in swaps),
                "wrong same-block swap evidence")
        require(record["final_trade_profit"] == "UNRESOLVED"
                and record["earliest_qualified_follower_entry"] == "UNRESOLVED",
                "prohibited profit/eligibility promotion")
        rows.append({
            "token":token,"major_CA":record["ca"],"linked_priority_wallet":record["wallet"],
            "v2_wbnb_pool":record["pool"],"creation_block":block,
            "first_positive_WBNB_reserve_wei":str(wbnb_wei),
            "first_positive_WBNB_reserve_BNB":displayed,
            "first_positive_sync_UTC":iso,
            "initial_mint_tx_hash":p["transactionHash"],
            "confirmed_same_block_swap_events":len(swaps),
            "earliest_any_pool_liquidity":"UNRESOLVED",
            "first_qualified_trade_entry":"UNRESOLVED",
            "attributable_realized_profit":"UNRESOLVED",
            "production":"NO_GO",
        })
    require(len({r["v2_wbnb_pool"] for r in rows}) == 4
            and sum(r["confirmed_same_block_swap_events"]>0 for r in rows) == 2,
            "duplicate pool or changed success count")
    return {
        "schema":"BSC_P4_PRIORITY4_V2_FIRST_POSITIVE_RESERVES_EVIDENCE_MATRIX",
        "source_manifest":[
            {"path":PATH_ROOT+SRC_NAME,"git_blob_sha":SRC_BLOB},
            {"path":PATH_ROOT+"bsc-meme-address-model-v1-p4-priority4-firstpair-precommit-2026-10-13.json","git_blob_sha":PRECOMMIT_BLOB},
            {"path":PATH_ROOT+"bsc-meme-address-model-v1-p4-priority4-firstpair-seven-stage-proof-2026-10-13.json","git_blob_sha":BINARY_BLOB},
        ],
        "summary":{"priority_wallets":4,"source_confirmed_V2_WBNB_pair_creations":4,
                   "initial_Mint_and_Sync_same_creation_tx":4,
                   "positive_initial_WBNB_reserves":4,
                   "same_block_swap_confirmed_pools":2,
                   "full_19CA_venue_launch_universe_validated":False,
                   "qualified_follower_entry_proven":0,"profit_proven":0,"production":"NO_GO"},
        "rows":rows,
    }


def main() -> None:
    a=argparse.ArgumentParser(description="offline frozen first V2 WBNB reserves audit")
    a.add_argument("--source-dir",type=Path,default=ROOT)
    a.add_argument("--output",type=Path,required=True)
    args=a.parse_args()
    result=build(load(args.source_dir))
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")


if __name__ == "__main__":
    main()
