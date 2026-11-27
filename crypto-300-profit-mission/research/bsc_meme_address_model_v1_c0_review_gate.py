#!/usr/bin/env python3
"""C0 source-only audit gate: five/seven scope, 2025 wallet residual, UTC."""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parent
PINS=(
 ("bsc-meme-address-model-v1-p4c-23x19-five-native-rounds-mixed239e-2026-10-15.json","7ef825b5e56071687dadbf24d3b4327724e0d831"),
 ("bsc-meme-address-model-v1-p4c-23x19-seven-native-mixed4-2026-10-15.json","de5e62edd7e5b961ca6c8c3db20960a33016f4d4"),
 ("bsc-meme-address-model-v1-p4c-8e6b-token4-19tx-five-independent-source-reconciliation-2026-10-15.json","6c02e8623865b689300c776cc2774f13963f040d"),
 ("bsc-meme-address-model-v1-p4c-8e6b-token4-independent-five-part1-2026-10-15.json","75372f649a8ce75188d41b011df6febe33ecbe84"),
 ("bsc-meme-address-model-v1-p4c-8e6b-token4-independent-five-part2-2026-10-15.json","79a43a6c97085e8e796a8288fffdf175618d26f3"),
 ("bsc-meme-address-model-v1-p4c-8e6b-token4-2025-blocktime-header-2026-10-15.json","85bca313b5579fa4971478d81c9d2c5320299927"),
)
def ensure(ok,reason):
    if not ok:
        raise ValueError(reason)
def load(root=ROOT):
    result=[]
    for name,sha in PINS:
        raw=(root/name).read_bytes()
        digest=hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
        ensure(digest==sha,"source blob changed: "+name)
        result.append(json.loads(raw))
    return result
def epoch_utc(value):
    return datetime.fromtimestamp(value,timezone.utc).isoformat(timespec="milliseconds").replace("+00:00","Z")
def build(src):
    ensure(len(src)==6,"all frozen sources required")
    five,seven,recon,one,two,headers=src
    for d,n,c,remaining in ((five,5,4,433),(seven,7,5,432)):
        s=d["summary"]
        ensure((s["total_wallet_CA_cells"],s["source_verified_original_native_rounds"],
                s["reviewed_distinct_wallet_CA_cells"],s["not_economically_audited_cells"]) ==
               (437,n,c,remaining),"mixed source-scope denominator")
        ensure(s["production"]=="NO_GO" and s["public_observer_follower_qualified_signals"]==0,
               "invalid production / U upgrade")
    old=five["verified_economic_rounds"]
    newer=seven["verified_economic_rounds"]
    ensure(len(old)==5 and len(newer)==7 and newer[:5]==old,
           "old 5 rounds were changed or 2025 token4 was added twice")
    keys=[(r["wallet"],r["exact_CA"],r["economic_round_key"]) for r in newer]
    ensure(len(set(keys))==7 and
           [r["economic_round_key"] for r in newer[-2:]]==["P2_16","P2_17"] and
           len({(r["wallet"],r["exact_CA"]) for r in newer[-2:]})==1 and
           int(newer[-2]["net_wei"])<0<int(newer[-1]["net_wei"]),
           "same-CA token4 negative/positive round attribution drift")
    trades=[r for group in recon["rounds"] for r in group["original_trades"]]
    spots=one["rows"]+two["rows"]
    ensure(len(trades)==19 and len({x["hash"] for x in trades})==19 and
           len(spots)==len(recon["spot_checks"])==5 and
           len(recon["rounds"])==2 and all(t["original_signed_success"] for t in trades),
           "19 original sourced trades versus five historical spot reads confused")
    amount=sum(int(x["original_owner_native_block_net_wei"]) for x in trades)
    ensure(amount==int(recon["summary"]["original_total_native_wei"]) and
           amount==sum(int(x["net_wei"]) for x in newer[-2:]),
           "token4 cashflow mismatch")
    source_by_hash={r["hash"]:r for r in trades}
    for spot,declared in zip(spots,recon["spot_checks"]):
        h=spot["selected"]["hash"]
        ensure(h==declared["hash"] and h in source_by_hash and
               spot["receipt_status"]=="SUCCESS_FULL" and
               spot["original_eoa_signed_status"]=="OWNER_SIGNED_CHAIN56" and
               int(spot["native_after"])-int(spot["native_before"])==int(spot["native_delta_wei"])==
               int(source_by_hash[h]["original_owner_native_block_net_wei"]),
               "historical source receipt/balance mismatch")
    ensure(spots[0]["selected"]["block"]==min(x["block"] for x in trades) and
           spots[-1]["selected"]["block"]==max(x["block"] for x in trades),
           "boundary spots do not cover selected 19")
    wallet_delta=int(spots[-1]["native_after"])-int(spots[0]["native_before"])
    residual=wallet_delta-amount
    first_gap=int(spots[1]["native_before"])-int(spots[0]["native_after"])
    between_rounds=int(spots[2]["native_before"])-int(spots[1]["native_after"])
    ensure(residual!=0 and first_gap!=0 and between_rounds!=0,
           "incomplete owner wallet ledger falsely considered complete")
    ensure(len(headers["rows"])==2,"historical header bounds")
    for row in headers["rows"]:
        ensure(epoch_utc(row["timestamp_unix"])==row["UTC"] and
               int(row["timestamp_hex"],16)==row["timestamp_unix"] and
               row["UTC"].startswith("2025-"),"actual 2025 epoch UTC proof changed")
    return {
        "schema":"BSC_V1_C0_SOURCE_SCOPE_CORRECTION",
        "source_manifest":[{"path":"crypto-300-profit-mission/research/"+n,"git_blob_sha":s} for n,s in PINS],
        "five_baseline":{"selected_owner_rounds":5,"unique_wallet_CA_cells":4,"other_cells":433},
        "seven_expanded_review_pending":{"selected_owner_rounds":7,"unique_wallet_CA_cells":5,
                                         "other_cells":432,"already_contains":["P2_16","P2_17"],
                                         "review_verdict":"REQUEST_CHANGES"},
        "2025_token4":{
            "source_original_transactions":19,"new_prior_rpc_spot_reads":5,
            "selected_token_trades_native_cashflow_wei":str(amount),
            "whole_wallet_balance_change_first_to_last_spot_wei":str(wallet_delta),
            "unattributed_wallet_vs_selected_trade_residual_wei":str(residual),
            "unattributed_between_round1_buy_sell_wei":str(first_gap),
            "unattributed_between_rounds_wei":str(between_rounds),
            "cashflow_grade":"SELECTED_TRADES_ONLY_NOT_FINAL_WALLET_PNL",
            "unattributed_flows":"UNRESOLVED",
            "original_UTC":[r["UTC"] for r in headers["rows"]],
            "recent_2026_signal":False
        },
        "CI_source_verification":"OFFLINE_STATIC_REPLAY_NOT_LIVE_RPC",
        "P4_C":"PARTIAL","P4_B_U":"UNRESOLVED","P5":"BLOCKED","production":"NO_GO"
    }
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source-dir",type=Path,default=ROOT)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    a.output.write_text(json.dumps(build(load(a.source_dir)),ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
if __name__=="__main__":
    main()
