#!/usr/bin/env python3
"""P4-B: 19 exact-CA cross-venue scoped first active liquidity and observed V2 swaps.

Do not promote liquidity to first executable global market, sellability, wallet
miss or follower alpha. Retain all 5 inactive-at-V2-reference pool unknowns.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parent
PREFIX="crypto-300-profit-mission/research/"
PINS=(
 ("bsc-meme-address-model-v1-p4-19ca-v2-wbnb-first-positive-liquidity-2026-10-14.json","9fbc8bdaeb9df342a4d200fefb0ebd48b746b903"),
 ("bsc-meme-address-model-v1-p4-competing17-first-active-unified-2026-10-14.json","fcc71a4ad6f35731224ed3de11c4e902fe3f5d3e"),
 ("bsc-meme-address-model-v1-p4-19ca-competing22-liquidity-snapshot-2026-10-14.json","a40e9c8ca741b08130e556c3fbed3908d6c05c0e"),
 ("bsc-meme-address-model-v1-p4b-v2-19ca-first10-swap-observations-2026-10-14.json","0000000000000000000000000000000000000000"),
 ("bsc-meme-address-model-v1-p4-bulla-v3-usdt-10000-delayed-active-proof-2026-10-14.json","41366fc5959d4bd227826aec8101229eb02e1bd1"),
 ("bsc-meme-address-model-v1-p4-niulai-v3-10000-delayed-active-proof-2026-10-14.json","7a5e74b5fa653b7e2a51f1f86e2200510c8a5c88"),
)
INACTIVE=("V3_NO_ACTIVE_LIQUIDITY_AT_SNAPSHOT","V2_NO_POSITIVE_RESERVES_AT_SNAPSHOT")

def require(value,message):
    if not value:
        raise ValueError(message)

def git_sha(raw):
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()

def load(root=ROOT):
    out=[]
    for name,sha in PINS:
        raw=(root/name).read_bytes()
        require(git_sha(raw)==sha, "source Git blob mismatch: "+name)
        out.append(json.loads(raw))
    return out

def utc(log):
    return datetime.fromtimestamp(int(log["blockTimestamp"],16),tz=timezone.utc).isoformat(
        timespec="milliseconds").replace("+00:00","Z")

def build(d):
    require(len(d)==len(PINS),"missing scope evidence")
    base,comp,snap,sw,bulla,niulai=d
    require(base["summary"]["exact_major_CAs"]==19
            and base["summary"]["first_positive_v2_wbnb_reserves_verified"]==19
            and comp["summary"]["competitor_first_active_proven"]==17
            and snap["summary"]["source_competing_slots"]==22
            and snap["summary"]["total_active_competing_pool_snapshots"]==17
            and sw["summary"]["exact_CAs"]==19
            and sw["summary"]["observed_v2_swap_events_in_verified_windows"]==24
            and all(q.get("production",q.get("summary",{}).get("production"))=="NO_GO"
                    for q in d), "frozen P4 evidence scope drift")
    require(len(base["rows"])==len(snap["rows"])==len(sw["rows"])==19
            and len(comp["rows"])==17,"original source rows omitted")
    byCA={}
    for x in comp["rows"]:
        byCA.setdefault(x["exact_CA"],[]).append(x)
    snapmap={x["CA"]:x for x in snap["rows"]}
    require(len(snapmap)==19,"duplicate source CA snapshot")
    times={bulla["pool"]:utc(bulla["first_active_event"]),
           niulai["pool"]:utc(niulai["first_mint_event"])}
    require(bulla["delay_blocks"]==10 and niulai["delay_blocks"]==17
            and bulla["production"]==niulai["production"]=="NO_GO",
            "delayed source origin changed")
    out=[]
    for i,(b,s) in enumerate(zip(base["rows"],sw["rows"])):
        ca=b["exact_CA"]
        require(ca==s["exact_CA"] and b["v2_wbnb_pool"]==s["pool"]
                and s["index"]==i and s["source_first_liquidity_block"]==
                b["first_positive_reserves_block"],"cross-dataset CA or V2 pool mismatch")
        reference=snapmap.get(ca)
        require(reference is not None and reference["at_block"]==
                b["first_positive_reserves_block"],"missing snapshot for historical reference")
        alternatives=byCA.get(ca,[])
        inactive=[]
        for z in reference["pools"]:
            if z["classification"] in INACTIVE:
                inactive.append({
                    "pool":z["pool"],"protocol":z["protocol"],"quote":z["quote"],
                    "fee_pips":z["fee_pips"],"reference_block":reference["at_block"],
                    "at_reference_state":z["classification"],"prior_trading":"UNRESOLVED",
                })
        alt_ids={(x["pool"],x["protocol"],x["quote"],x["fee_pips"]) for x in alternatives}
        snapshot_active={(x["pool"],x["protocol"],x["quote"],x["fee_pips"])
                         for x in reference["pools"] if x["classification"] not in INACTIVE}
        require(alt_ids==snapshot_active,"all 17 active snapshot pools not exact-matched")
        pools=[{"pool":b["v2_wbnb_pool"],"protocol":"V2","quote":"WBNB",
                "fee_pips":None,"first_active_block":b["first_positive_reserves_block"],
                "origin":"V2_WBNB_REFERENCE","first_active_UTC":b["first_positive_reserves_UTC"]}]
        for x in alternatives:
            delay=x["delay_blocks"]
            if delay:
                require(x["pool"] in times
                        and x["first_active_block"]>x["creation_block"],
                        "delayed positive block lacking actual event timestamp")
                at=times[x["pool"]]
            else:
                require(x["first_active_block"]==x["creation_block"],
                        "first active block without source")
                at=x["creation_UTC"]
            fields={"pool":x["pool"],"protocol":x["protocol"],"quote":x["quote"],
                    "fee_pips":x["fee_pips"],"first_active_block":x["first_active_block"],
                    "origin":"HISTORIC_COMPETITOR","first_active_UTC":at,
                    "delay_blocks":delay}
            pools.append(fields)
        pools.sort(key=lambda x:(x["first_active_block"],x["pool"]))
        first=pools[0]
        out.append({
            "index":i,"token":b["token"],"exact_CA":ca,
            "v2_reference_block":b["first_positive_reserves_block"],
            "scoped_first_active_pool":first["pool"],
            "scoped_first_active_block":first["first_active_block"],
            "scoped_first_active_protocol":first["protocol"],
            "scoped_first_active_quote":first["quote"],
            "scoped_first_active_origin":first["origin"],
            "earlier_competitors_proven":sum(x["first_active_block"]<b["first_positive_reserves_block"] for x in alternatives),
            "validated_liquidity_pool_count":len(pools),
            "pools_scoped_first_active":pools,
            "inactive_at_reference_historical_unknown_count":len(inactive),
            "inactive_at_reference_historical_unknown_pools":inactive,
            "v2_first10_scan_coverage":s["scan_coverage"],
            "observed_direct_V2_swaps_in_scope":s["swap_event_count"],
            "observed_direct_V2_token_buy_swaps_in_scope":s["pool_buy_token_events"],
            "observed_direct_V2_token_sell_swaps_in_scope":s["pool_sell_token_events"],
            "globally_first_executable_venue":"UNRESOLVED",
            "pre_v2_launchpad_market":"UNRESOLVED",
            "fixed_size_buy_sell_tax_slippage":"UNRESOLVED",
            "wallet_eligible_opportunity":"UNRESOLVED",
            "follower_executable_pnl":"UNRESOLVED",
        })
    summary={
        "exact_CAs":19,
        "scoped_active_pools":sum(x["validated_liquidity_pool_count"] for x in out),
        "earlier_competitor_pools":sum(x["earlier_competitors_proven"] for x in out),
        "CA_with_scoped_alt_earlier":sum(x["earlier_competitors_proven"]>0 for x in out),
        "CAs_where_V2_is_earliest_proven_scoped":sum(x["scoped_first_active_origin"]=="V2_WBNB_REFERENCE" for x in out),
        "other_inactive_at_reference_unknown":sum(x["inactive_at_reference_historical_unknown_count"] for x in out),
        "observed_first_window_v2_swaps":sw["summary"]["observed_v2_swap_events_in_verified_windows"],
        "actual_market_U_qualified":0,
        "production":"NO_GO",
    }
    require((summary["scoped_active_pools"],summary["earlier_competitor_pools"],
             summary["CA_with_scoped_alt_earlier"],summary["other_inactive_at_reference_unknown"])==
            (36,17,12,5),"historically active and excluded pool denominators drift")
    return {"schema":"BSC_P4B_19CA_CROSS_VENUE_FIRST_ACTIVE_CANDIDATE_U",
            "scope":"Only archived PancakeSwap V2 WBNB and 17 active competitor proofs. Excludes possible launchpad/other routes; five inactive-at-reference pools unresolved for earlier history; never counts tradable wallet opportunities.",
            "source_manifest":[{"path":PREFIX+n,"git_blob_sha":sha} for n,sha in PINS],
            "summary":summary,"rows":out}

def main():
    a=argparse.ArgumentParser()
    a.add_argument("--source-dir",type=Path,default=ROOT)
    a.add_argument("--output",type=Path,required=True)
    args=a.parse_args()
    args.output.write_text(json.dumps(build(load(args.source_dir)),ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
if __name__=="__main__":
    main()
