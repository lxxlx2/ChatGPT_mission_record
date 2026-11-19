#!/usr/bin/env python3
"""P4-B source-pinned original tx, signer, gas and receipt for nine observed pool Swaps.

Original tx sender is not established token-beneficial-owner. Unreadable receipt
remains UNKNOWN even if canonical pool Swap log itself is present.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
PREFIX="crypto-300-profit-mission/research/"
PINS=(
 ("bsc-meme-address-model-v1-p4b-nine-firstswap-original-tx-precommit-2026-10-14.json","0f56c5859c3e596fc29e1db98679ff7d8268d0d2"),
 ("bsc-meme-address-model-v1-p4b-nine-firstswap-tx-receipt-part1-2026-10-14.json","5dc57d74e40457c767f02205a14336093579a8b5"),
 ("bsc-meme-address-model-v1-p4b-nine-firstswap-tx-receipt-part2-2026-10-14.json","4f2cc8f230dbee4acf3b1a976646e51dfa04b1ef"),
 ("bsc-meme-address-model-v1-p4b-nine-firstswap-tx-receipt-part3-2026-10-14.json","c91efe3b25643386f21090e1dc21803ae8852094"),
 ("bsc-meme-address-model-v1-p4b-v2-19ca-first10-swap-observations-2026-10-14.json","646732ca70fa06dff798b30b2a91236135f4ecbb"),
)

def require(value,message):
    if not value:
        raise ValueError(message)
def git_sha(raw):
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
def load(root=ROOT):
    out=[]
    for name,sha in PINS:
        raw=(root/name).read_bytes()
        require(git_sha(raw)==sha, "source SHA mismatch "+name)
        out.append(json.loads(raw))
    return out

def build(d):
    require(len(d)==len(PINS),"missing raw source")
    pre,p1,p2,p3,sw=d
    require(pre["schema"]=="BSC_P4B_FIRST_OBSERVED_SWAP_OWNER_RECEIPT_9_PRECOMMIT"
            and pre["origin_source_blob_sha"]==PINS[4][1]
            and len(pre["targets"])==9 and pre["production"]=="NO_GO"
            and sw["summary"]["observed_v2_swap_events_in_verified_windows"]==24,
            "nine original transaction scope mismatch")
    docs=(p1,p2,p3)
    rows=[]
    for k,p in enumerate(docs,1):
        require(p["schema"]=="BSC_P4B_NINE_FIRSTSWAP_OWNER_TX_RECEIPT_RAW"
                and p["part"]==k
                and p["target_indices"]==[t["index"] for t in pre["targets"][3*(k-1):3*k]]
                and p["precommit_git_blob_sha"]==PINS[0][1]
                and p["production"]=="NO_GO"
                and len(p["rows"])==3,"raw source segment corrupted")
        rows.extend(p["rows"])
    require([w["target"]["index"] for w in rows]==[t["index"] for t in pre["targets"]],
            "nine original selected pools changed")
    observed=[z for z in sw["rows"] if z["swap_event_count"]>0]
    require(len(observed)==9
            and [x["index"] for x in observed]==[x["index"] for x in pre["targets"]],
            "selection not full nine observed pool windows")
    out=[]
    for witness,sel,pool in zip(rows,pre["targets"],observed):
        tx,receipt=witness["original_transaction"],witness["original_receipt"]
        first=pool["event_witnesses"][0]
        require(witness["target"]==sel
                and sel["txhash"].lower()==tx["hash"].lower()==first["txhash"].lower()
                and sel["first_observed_swap_block"]==first["block"]==int(tx["blockNumber"],16)
                and sel["pool"]==pool["pool"]
                and sel["CA"]==pool["exact_CA"]
                and sel["first_event_log_index"]==first["log_index"]
                and sel["first_event_direction"]==first["swap_type"]
                and sel["scope"]==pool["scan_coverage"]
                and witness["transaction_read_status"]=="COMPLETE",
                "original signed source/hash/block mismatch")
        full=witness["receipt_read_status"]=="COMPLETE"
        if full:
            require(receipt["transactionHash"].lower()==tx["hash"].lower()
                    and receipt["status"]=="0x1"
                    and receipt["blockNumber"]==tx["blockNumber"],
                    "receipt signer/tx/header status mismatch")
        else:
            require(receipt.get("ERROR")=="UNPARSEABLE_OR_TRUNCATED",
                    "partial receipt falsely promoted")
        used=int(receipt["gasUsed"],16) if full and receipt.get("gasUsed") else None
        price=int(receipt["effectiveGasPrice"],16) if full and receipt.get("effectiveGasPrice") else None
        out.append({
            "index":sel["index"],"token":sel["token"],"exact_CA":sel["CA"],"pool":sel["pool"],
            "observed_pool_swap_tx":sel["txhash"],
            "observed_swap_block":sel["first_observed_swap_block"],
            "observed_pool_swap_direction":first["swap_type"],
            "observed_wbnb_into_pool_wei":first["wbnb_in_wei"],
            "observed_wbnb_out_of_pool_wei":first["wbnb_out_wei"],
            "original_tx_from":tx["from"],"original_tx_to":tx["to"],
            "original_tx_value_wei":str(int(tx.get("value","0x0"),16)),
            "original_tx_input_selector":tx.get("input","")[:10] or "UNRESOLVED",
            "source_swap_window_coverage":pool["scan_coverage"],
            "original_tx_confirmed":True,
            "receipt_status":receipt["status"] if full else "UNRESOLVED",
            "receipt_read_status":witness["receipt_read_status"],
            "receipt_gas_used":str(used) if used is not None else None,
            "receipt_effective_gas_price_wei":str(price) if price is not None else None,
            "total_tx_gas_wei":str(used*price) if used is not None and price is not None else None,
            "beneficial_owner_identity":"UNRESOLVED","owner_realized_pnl":"UNRESOLVED",
            "fixed_size_follower_quote":"UNRESOLVED","eligible_missed_trade":"UNRESOLVED",
        })
    summary={
        "observed_pool_firstswap_transactions":9,
        "original_tx_senders_verified":len(out),
        "readback_receipt_success":sum(x["receipt_status"]=="0x1" for x in out),
        "receipt_unresolved":sum(x["receipt_status"]=="UNRESOLVED" for x in out),
        "owner_realized_pnl_proven":0,
        "qualified_major_U_proven":0,
        "production":"NO_GO",
    }
    require((summary["readback_receipt_success"],summary["receipt_unresolved"])==(6,3),
            "receipt evidence grade drift")
    return {"schema":"BSC_P4B_NINE_FIRSTSWAP_TX_PROVENANCE_GATE",
            "scope":"One fixed earliest-observed V2 pool Swap original transaction for each of 9 frozen 19 CA pools with a witnessed Swap; no beneficial trader identity, no user return or whole-market entry conclusion",
            "source_manifest":[{"path":PREFIX+n,"git_blob_sha":sha} for n,sha in PINS],
            "summary":summary,"rows":out}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--source-dir",type=Path,default=ROOT)
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    args.output.write_text(json.dumps(build(load(args.source_dir)),ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
if __name__=="__main__":
    main()
