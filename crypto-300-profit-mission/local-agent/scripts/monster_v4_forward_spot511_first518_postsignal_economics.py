#!/usr/bin/env python3
"""Pre-registered all 8 WATCH/all 8 SETUP subsequent open-to-open price proxies.

Only same archived issuer bytes and frozen signal artifact. No live prices,
historical real PIT / depth / fills, trading, default notional or notifications.
"""
from __future__ import annotations
import argparse
from collections import Counter
from datetime import datetime,timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import statistics

import monster_v4_forward_spot511_first518_fifo8_bridge as bridge

SOURCE_SHA="d51ce0faa70609dfa24659eed29958cef167c068838ad3986c6a8a0e297b0c2d"
SOURCE_REL="monster_forward_spot511_first518_official_minute_causal_fifo8_actual_v1.json"
SCHEMA="MONSTER_FORWARD_SPOT511_FIRST518_ALL8_WATCH_SETUP_FIXED_PRICE_HORIZON_V1"
HORIZONS=(15,60,360,1440)
FEE=Decimal("0.001")
SLIP=Decimal("0.002")
MIN_MS=60_000

def event_inventory():
    raw=(bridge.EVIDENCE/SOURCE_REL).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=SOURCE_SHA:
        raise ValueError("MONSTER518_FIXED_8_WATCH_SETUP_SOURCE_SHA_MISMATCH")
    source=json.loads(raw)
    watches=source["WATCH_event_identity"]
    setups=source["SETUP_event_identity"]
    if (source["schema"]!=bridge.SCHEMA or len(watches)!=8 or len(setups)!=8
            or source["event_type_counts"]!={"SETUP_ACTIVE":8,"WATCH_EARLY":8}
            or source["strict_3m_global_polls"]!=518):
        raise ValueError("MONSTER518_FIXED_ORIGINAL_EVENT_POPULATION_DRIFT")
    all_events=watches+setups
    if (len({x["event_id"] for x in all_events})!=16
            or len({x["symbol"] for x in watches})!=8
            or {x["symbol"] for x in watches}!={x["symbol"] for x in setups}):
        raise ValueError("MONSTER518_EIGHT_PAIR_EVENTS_IDENTITY_INVALID")
    return watches,setups

def minute_at(bars,tick):
    if tick%MIN_MS:
        raise ValueError("MONSTER518_NONMINUTE_SIGNAL_OR_ENTRY")
    idx=(tick-bars[0][0])//MIN_MS
    if idx<0 or idx>=len(bars) or bars[idx][0]!=tick:
        return None
    return idx

def evaluate(bars,observed_ms,hold_minutes):
    """Never test entry or exit minute completed volume before its OPEN."""
    if hold_minutes not in HORIZONS:
        raise ValueError("MONSTER518_UNFROZEN_HOLD_HORIZON")
    at=observed_ms+3*MIN_MS
    idx=minute_at(bars,at)
    if idx is None or idx==0:
        return {"status":"CENSORED_ENTRY_PRICE_SOURCE_NOT_AVAILABLE"}
    prev=bars[idx-1]
    if prev[5]<=0 or prev[6]<=0:
        return {"status":"CENSORED_PREENTRY_ZERO_TRADES_OR_QUOTE"}
    exit_ms=at+hold_minutes*MIN_MS
    ei=minute_at(bars,exit_ms)
    if ei is None or ei==0:
        return {"status":"CENSORED_EXIT_SOURCE_NOT_AVAILABLE"}
    prior=bars[ei-1]
    if prior[5]<=0 or prior[6]<=0:
        return {"status":"CENSORED_PREEXIT_ZERO_TRADES_OR_QUOTE"}
    price=bars[idx][1]; exit_price=bars[ei][1]
    if price<=0 or exit_price<=0:
        return {"status":"CENSORED_NO_POSITIVE_OPEN_PRICE"}
    ratio=exit_price/price
    net=ratio*(Decimal(1)-SLIP)/(Decimal(1)+SLIP)*(Decimal(1)-FEE)**2
    return {
        "status":"OFFICIAL_1M_PRICE_PROXY_ONLY",
        "entry_utc":datetime.fromtimestamp(at/1000,timezone.utc).isoformat(),
        "exit_utc":datetime.fromtimestamp(exit_ms/1000,timezone.utc).isoformat(),
        "gross_pct":str((ratio-1)*100),
        "net_price_proxy_pct":str((net-1)*100),
        "fee_per_side_assumption_bps":10,
        "slippage_per_side_assumption_bps":20,
        "real_ask_bid_or_fill_verified":False,
    }

def describe(rows):
    states=Counter(x["result"]["status"] for x in rows)
    good=[Decimal(x["result"]["net_price_proxy_pct"]) for x in rows
          if x["result"]["status"]=="OFFICIAL_1M_PRICE_PROXY_ONLY"]
    if sum(states.values())!=8:
        raise ValueError("MONSTER518_POSTSIGNAL_ALL8_DENOMINATOR_REQUIRED")
    return {
        "all_original_signals":8,
        "statuses":dict(sorted(states.items())),
        "evaluable_net_price_proxies":len(good),
        "winning_price_proxies":sum(x>0 for x in good),
        "losing_price_proxies":sum(x<0 for x in good),
        "zero_price_proxies":sum(x==0 for x in good),
        "median_net_price_proxy_pct":str(statistics.median(good)) if good else None,
        "mean_net_price_proxy_pct":str(sum(good)/len(good)) if good else None,
    }

def run(source_dirs):
    watches,setups=event_inventory()
    roster=bridge.admitted.frozen_roster()
    receipts=bridge.evidence_receipts(roster)
    zips,checksums=bridge.source_files(source_dirs)
    if len(zips)!=1533 or len(checksums)!=1533:
        raise ValueError("MONSTER518_POSTSIGNAL_1533_ARCHIVE_PAIRS_REQUIRED")
    symbols=sorted({r["symbol"] for r in watches+setups})
    expected={f"{sym}-1m-{day}.zip" for sym in roster for day in bridge.DAY_UTC}
    if set(zips)!=expected or set(checksums)!={name+".CHECKSUM" for name in expected}:
        raise ValueError("MONSTER518_SOURCE_ARCHIVE_NAME_POPULATION_DRIFT")
    valid={}
    independently_revalidated_symbol_days=0
    for sym in symbols:
        bars,proof=bridge.parse_symbol_three_days(sym,receipts,zips,checksums)
        if len(proof)!=len(bridge.DAY_UTC):
            raise ValueError("MONSTER518_EIGHT_SIGNAL_SOURCE_PROOF_INCOMPLETE")
        independently_revalidated_symbol_days+=len(proof)
        valid[sym]=bars
    if independently_revalidated_symbol_days!=8*len(bridge.DAY_UTC):
        raise ValueError("MONSTER518_EIGHT_SIGNAL_SHA_SCOPE_WRONG")
    result={}
    for kind,events in (("WATCH",watches),("SETUP",setups)):
        report={}
        for minutes in HORIZONS:
            rows=[{"event_id":event["event_id"],
                   "symbol":event["symbol"],
                   "observed_ms":event["observed_ms"],
                   "hold_minutes":minutes,
                   "result":evaluate(valid[event["symbol"]],
                                     event["observed_ms"],minutes)}
                  for event in events]
            report[str(minutes)]={"summary":describe(rows),"rows":rows}
        result[kind]=report
    look={x["symbol"]:x for x in watches}
    delay={x["symbol"]:(x["observed_ms"]-look[x["symbol"]]["observed_ms"])//MIN_MS
           for x in setups}
    return {
        "schema":SCHEMA,"source_first518_sha256":SOURCE_SHA,
        "source_immutable_watch_count":8,"source_immutable_setup_count":8,
        "producer_full_source_verification": {
            "producer_run_id":39226387610,
            "producer_original_report_sha256":SOURCE_SHA,
            "verified_original_symbol_days_in_producer":len(receipts),
            "this_economics_job_did_not_reverify_all_1533_bytes":True,
            "independent_other_AI_source_replay":"BLOCKED_NOT_PERFORMED"
        },
        "original_artifact_name_pairs_verified_here":len(expected),
        "signal_symbol_days_publisher_sha_reverified_here":independently_revalidated_symbol_days,
        "symbol_venue":"BINANCE_SPOT",
        "not_fresh_live_market_capture":True,
        "no_default_notional_or_cash_profit":True,
        "historical_1m_rolling_ticker24_proxy_not_real":True,
        "pre_registered_horizons_minutes":list(HORIZONS),
        "paired_SETUP_after_WATCH_delay_minutes":dict(sorted(delay.items())),
        "both_alternative_non_combined_signal_views":result,
        "independent_other_AI_review":"NOT_DONE",
        "true_7day_OOS":"NOT_DONE",
        "executable_net_pnl":"UNKNOWN",
        "G0":"PARTIAL","G4":"UNKNOWN","G6":"NO_GO",
        "NO_MERGE":True,"NO_DEPLOY":True,"NO_GMAIL":True,"NO_TRADE":True,
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--source-dir",type=Path,action="append",required=True)
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    if args.out.exists() or args.out.is_symlink():
        raise ValueError("MONSTER518_PRICE_PROXY_ALREADY_EXISTS")
    report=run(args.source_dir)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,indent=2,sort_keys=True,ensure_ascii=False)+"\n")
    print("MONSTER518_POSTSIGNAL_FIXED_8_WATCH_8_SETUP_PRICES",
          json.dumps({kind:{h:r["summary"] for h,r in d.items()}
                      for kind,d in report["both_alternative_non_combined_signal_views"].items()},
                     sort_keys=True),flush=True)

if __name__=="__main__":
    main()
