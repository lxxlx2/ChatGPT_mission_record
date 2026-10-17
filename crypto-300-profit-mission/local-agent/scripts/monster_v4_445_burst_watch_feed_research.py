#!/usr/bin/env python3
"""Source-SHA-pinned historical WATCH feed projection; never an alert or trade.

Only fields inside WATCH_EARLY at observed_ms may enter preview.
Final queue status and SETUP event ID belong to a separate hindsight section.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path

SOURCE_SHA = "370c34fbe8c2e914de54d87068b329405fc94c9d2624f7e3d8701155b10d67cf"
SCHEMA = "MONSTER445_CAPACITY8_WATCH_GROUPS_HISTORICAL_RESEARCH_V1"
SLOTS = 8


def utc(ms):
    return datetime.fromtimestamp(ms/1000,timezone.utc).isoformat().replace("+00:00","Z")


def event_hash(venue,symbol,kind,anchor):
    return hashlib.sha256(
        f"MONSTER_V4|{venue}|{symbol}|{kind}|{anchor}".encode()).hexdigest()


def at_watch(e):
    if e.get("event_type")!="WATCH_EARLY":
        raise ValueError("MONSTER445_GROUP_NOT_WATCH")
    p=json.loads(e["payload"])
    t=e["observed_ms"]; venue=e["venue"]; sym=e["symbol"]
    if (venue!="spot" or not isinstance(t,int)
            or e["event_id"]!=event_hash(venue,sym,"WATCH_EARLY",t)
            or p.get("observed_ms")!=t or p.get("venue")!=venue
            or p.get("classification")!="RESEARCH_WATCH_NOT_BUY"
            or p.get("execution_verified") is not False):
        raise ValueError("MONSTER445_GROUP_WATCH_SOURCE_IDENTITY_DRIFT")
    try:
        proxy=Decimal(str(p["quote24_usdt"]))
    except (InvalidOperation,ValueError,KeyError,TypeError):
        raise ValueError("MONSTER445_GROUP_QUOTE_PROXY_INVALID") from None
    if not proxy.is_finite() or proxy<0:
        raise ValueError("MONSTER445_GROUP_QUOTE_PROXY_INVALID")
    flags=[k for k in ("trigger_3m_5pct","trigger_15m_8pct","trigger_60m_15pct")
           if p.get(k) is True]
    if not flags or not isinstance(p.get("return_snapshot_pct"),(int,float)):
        raise ValueError("MONSTER445_GROUP_NO_CAUSAL_WATCH_TRIGGER")
    return {
        "event_id":e["event_id"],"symbol":sym,"venue":venue,
        "first_observed_ms":t,"first_observed_utc":utc(t),
        "triggered_windows_at_WATCH":flags,
        "observed_snapshot_move_pct":p["return_snapshot_pct"],
        "historical_reconstructed_quote24_proxy_usdt":str(proxy),
        "proxy_is_real_historical_PIT_ticker":False,
        "label":"WATCH_NOT_BUY",
        "can_follow_now":"UNKNOWN_REQUIRES_LIVE_PRICE_AND_ORDER_BOOK",
    }


def project(full_bytes,summary):
    sha=hashlib.sha256(full_bytes).hexdigest()
    if sha!=SOURCE_SHA or summary.get("full_replay_json_sha256")!=sha:
        raise ValueError("MONSTER445_GROUP_IMMUTABLE_SOURCE_SHA_MISMATCH")
    src=json.loads(full_bytes)
    if (src.get("actually_complete_symbols")!=445
            or src.get("one_shared_sqlite_for_all_symbols") is not True
            or src.get("not_independent_OOS") is not True
            or src.get("not_real_PIT_listing") is not True
            or src.get("execution_counts",{}).get("polls")!=3360
            or src.get("D1_model_semantics")!="RESEARCH_V2_SOURCE_UNSUPPORTED_ZEROQUOTE"
            or src.get("all445_original_production_D1_completed") is not False
            or src.get("G6")!="NO_GO"):
        raise ValueError("MONSTER445_GROUP_SOURCE_COHORT_CONTRACT_DRIFT")
    watches=[at_watch(e) for e in src["events"] if e["event_type"]=="WATCH_EARLY"]
    queue=src["queue_rows"]
    if len(watches)!=269 or len(queue)!=269:
        raise ValueError("MONSTER445_GROUP_269_DENOMINATOR_DRIFT")
    identity={(q["venue"],q["symbol"],q["first_seen_ms"]):q for q in queue}
    if (len(identity)!=269 or len({v["event_id"] for v in watches})!=269
            or set(identity)!={(x["venue"],x["symbol"],x["first_observed_ms"])
                                for x in watches}):
        raise ValueError("MONSTER445_GROUP_WATCH_QUEUE_IDENTITY_DRIFT")
    tick=defaultdict(list)
    for x in watches:
        tick[(x["venue"],x["first_observed_ms"])].append(x)
    cards=[]; retrospective=[]
    setup_ids={e["event_id"] for e in src["events"] if e["event_type"]=="SETUP_ACTIVE"}
    for (venue,t),members in sorted(tick.items(),key=lambda p:(p[0][1],p[0][0])):
        members.sort(key=lambda x:(-Decimal(x["historical_reconstructed_quote24_proxy_usdt"]),
                                   x["symbol"],x["event_id"]))
        if len(members)<=SLOTS:
            cards.extend({"kind":"SINGLE_WATCH_NOT_BUY","event_id":v["event_id"],
                          "symbol":v["symbol"],"venue":venue,"first_observed_utc":utc(t)}
                         for v in members)
            continue
        gid=hashlib.sha256(f"MONSTER445_BURST|{venue}|{t}".encode()).hexdigest()[:20]
        cards.append({
            "kind":"MARKET_BURST_WATCH_NOT_BUY","group_id":gid,
            "venue":venue,"first_observed_utc":utc(t),"member_count":len(members),
            "all_watch_event_ids_preserved":[x["event_id"] for x in members],
            "preview_eight_symbols_sorted_by_historical_quote_proxy_NOT_BUY_RANK":
                [x["symbol"] for x in members[:SLOTS]],
            "ordering_is_not_profit_or_execution_priority":True,
        })
        statuses=Counter(identity[(venue,x["symbol"],t)]["status"] for x in members)
        setups=sum(event_hash(venue,x["symbol"],"SETUP_ACTIVE",
                              identity[(venue,x["symbol"],t)]["id"]) in setup_ids
                   for x in members)
        retrospective.append({
            "group_id":gid,"observed_utc":utc(t),
            "hindsight_final_D1_queue_status_counts":dict(sorted(statuses.items())),
            "hindsight_SETUP_count":setups,
            "NOT_AVAILABLE_AT_WATCH":True,
        })
    accounted=[eid for c in cards for eid in
               (c["all_watch_event_ids_preserved"] if
                c["kind"]=="MARKET_BURST_WATCH_NOT_BUY" else [c["event_id"]])]
    if Counter(accounted)!=Counter(x["event_id"] for x in watches):
        raise ValueError("MONSTER445_GROUP_CARD_LOST_OR_DUPLICATED_WATCH")
    all_events=sorted(watches,key=lambda x:(x["first_observed_ms"],x["symbol"]))
    group_cards=[c for c in cards if c["kind"]=="MARKET_BURST_WATCH_NOT_BUY"]
    return {
        "schema":SCHEMA,"full_replay_source_sha256":sha,
        "source_artifact_id":12044872933,
        "source_cohort":"POSTHOC_445_SOURCE_COMPLETE_OF_ORIGINAL_758",
        "censored_original_source_313":313,
        "slots_per_shared_D1_tick":SLOTS,
        "group_only_if_same_tick_WATCH_count_exceeds":SLOTS,
        "point_in_time_display_preview":{
            "at_WATCH_visible_rows_all_preserved":all_events,
            "cards_research_only_no_delivery":cards,
            "total_WATCH":len(watches),"unique_market_poll_ticks":len(tick),
            "market_burst_cards":len(group_cards),
            "burst_member_WATCH":sum(c["member_count"] for c in group_cards),
            "hypothetical_ungrouped_cards":len(watches),
            "hypothetical_grouped_cards":len(cards),
            "hypothetical_cards_reduced":len(watches)-len(cards),
            "emails_actually_sent":"NONE_RESEARCH_ONLY",
            "BUY":"FORBIDDEN","current_followability":"UNKNOWN",
        },
        "hindsight_diagnostic_not_for_live_display":{
            "market_bursts":retrospective,
            "full_queue_V2_status_counts":dict(sorted(Counter(q["status"]
                                                    for q in queue).items())),
            "not_independent_OOS":True,"not_real_PIT_listing":True,
            "executable_profit":"UNVERIFIED"
        },
        "G4":"UNKNOWN","G6":"NO_GO",
        "NO_MERGE":True,"NO_DEPLOY":True,"NO_GMAIL":True,"NO_TRADE":True
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--full",type=Path,required=True)
    p.add_argument("--summary",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    if a.out.exists() or a.out.is_symlink():
        raise ValueError("MONSTER445_GROUP_RESEARCH_OUTPUT_ALREADY_EXISTS")
    result=project(a.full.read_bytes(),json.loads(a.summary.read_text()))
    a.out.parent.mkdir(parents=True,exist_ok=True)
    with a.out.open("x",encoding="utf8") as f:
        json.dump(result,f,sort_keys=True,indent=2)
        f.write("\n")
    v=result["point_in_time_display_preview"]
    print("MONSTER445_445_SOURCE_PINNED_CAPACITY8_GROUP_RESEARCH",
          json.dumps({k:v[k] for k in
                     ("total_WATCH","unique_market_poll_ticks","market_burst_cards",
                      "burst_member_WATCH","hypothetical_grouped_cards",
                      "hypothetical_cards_reduced")},sort_keys=True))


if __name__=="__main__":
    main()
