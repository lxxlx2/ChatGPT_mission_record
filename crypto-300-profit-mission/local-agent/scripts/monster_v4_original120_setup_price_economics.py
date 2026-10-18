#!/usr/bin/env python3
"""Monster mainline: original 120 SETUP_ACTIVEs vs real archived 1m price paths.

Historical exposed February 2026 sources only. This code cannot claim PIT
listing, real order-book liquidity, trade fills, G4, or actual profitability.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import statistics

import monster_v4_shared_445_one_db_from_shards as archive
import monster_v4_shared_445_official_source_shards as shards

SCHEMA = "MONSTER_ORIGINAL120_SETUP_POST_SIGNAL_EXPOSED_PRICE_ECONOMICS_V1"
AB_SHA = "c30c8b6467b0017b36efc33fadfa2c7853f29f9c7e32993249774269ba4e2ae2"
HORIZONS = (15, 60, 360, 1440)
MIN = 60_000
ENTRY_DELAY_MIN = 3
FEE = Decimal("0.001")
BASE_SLIP = Decimal("0.002")
STRESS_SLIP = Decimal("0.01")
MIN_QUOTE = Decimal("30")


def percent_net(entry, exit_price, slippage):
    ratio = exit_price / entry
    return (ratio*(1-slippage)/(1+slippage)*(1-FEE)**2-1)*100


def load_immutable_setups(path):
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != AB_SHA:
        raise ValueError("MONSTER_SETUP120_STAGE162_AB_SHA_DRIFT")
    j = json.loads(raw)
    events = j["raw_alternative_events"]
    setups = [e for e in events if e["event_type"] == "SETUP_ACTIVE"]
    watches = [e for e in events if e["event_type"] == "WATCH_EARLY"]
    if (len(setups)!=120 or len(watches)!=269
        or len({e["event_id"] for e in setups})!=120
        or len({e["symbol"] for e in setups})!=56
        or j["setup_event_id_alternative"] != 120
        or j["setup_event_id_baseline"] != 120
        or j["setup_new_ids"] or j["setup_lost_ids"]
        or j["not_independent_OOS"] is not True
        or j["G6"] != "NO_GO"):
        raise ValueError("MONSTER_SETUP120_EVENT_SOURCE_DRIFT")
    for e in setups:
        if e["venue"] != "spot" or json.loads(e["payload"]).get("setup_candidate") is not True:
            raise ValueError("MONSTER_SETUP120_NOT_SOURCE_D1_SETUP")
        if type(e["observed_ms"]) is not int or e["observed_ms"] % (3*MIN):
            raise ValueError("MONSTER_SETUP120_TICK_NOT_THREE_MINUTES")
    return sorted(setups,key=lambda r:(r["observed_ms"],r["event_id"]))


def verify_minute_rows(bars):
    if len(bars)!=12_960:
        raise ValueError("MONSTER_SETUP120_ARCHIVE_NOT_12960_1M")
    last=None
    for r in bars:
        if len(r)!=7 or type(r[0]) is not int or type(r[6]) is not int:
            raise ValueError("MONSTER_SETUP120_ROW_FIELDS_INVALID")
        if last is not None and r[0]-last!=MIN:
            raise ValueError("MONSTER_SETUP120_MINUTE_GAP")
        last=r[0]
    return True


def get_bar(bars, tick_ms):
    first=bars[0][0]
    delta=tick_ms-first
    if delta < 0 or delta%MIN:
        return None
    idx=delta//MIN
    if idx>=len(bars):
        return None
    r=bars[idx]
    if r[0]!=tick_ms:
        raise ValueError("MONSTER_SETUP120_MINUTE_CLOCK_DRIFT")
    return r


def one_horizon(bars, entry_tick, hold_minutes):
    entry=get_bar(bars,entry_tick)
    exit_tick=entry_tick+hold_minutes*MIN
    exitbar=get_bar(bars,exit_tick)
    if entry is None or exitbar is None:
        return {"status":"CENSORED_NO_COMPLETE_EXIT", "exit_tick_ms":exit_tick}
    ent_price=Decimal(entry[1])
    out_price=Decimal(exitbar[1])
    if ent_price <= 0 or out_price <= 0:
        return {"status":"CENSORED_BAD_OPEN_PRICE","exit_tick_ms":exit_tick}
    if entry[6]<=0 or Decimal(entry[5])<=0:
        return {"status":"CENSORED_NO_ENTRY_TRADES","exit_tick_ms":exit_tick}
    if exitbar[6]<=0 or Decimal(exitbar[5])<=0:
        return {"status":"CENSORED_NO_EXIT_TRADES","exit_tick_ms":exit_tick}
    if Decimal(entry[5])<MIN_QUOTE or Decimal(exitbar[5])<MIN_QUOTE:
        return {"status":"CENSORED_ENTRY_OR_EXIT_MINUTE_QUOTE_LT_30","exit_tick_ms":exit_tick}
    idx=(exit_tick-bars[0][0])//MIN
    if any(b[6]<=0 or Decimal(b[5])<=0 for b in bars[max(0,idx-5):idx+1]):
        return {"status":"CENSORED_ZERO_TRADE_NEAR_EXIT","exit_tick_ms":exit_tick}
    base=percent_net(ent_price,out_price,BASE_SLIP)
    stress=percent_net(ent_price,out_price,STRESS_SLIP)
    return {
        "status":"PRICE_PROXY_ONLY",
        "exit_tick_ms":exit_tick,
        "entry_open":str(ent_price),
        "exit_open":str(out_price),
        "entry_quote":str(entry[5]),
        "exit_quote":str(exitbar[5]),
        "net_percent_fee10_slip20bps_each":str(base),
        "net_percent_fee10_slip100bps_each":str(stress),
        "gain_or_loss":"WIN" if base>0 else "LOSS" if base<0 else "FLAT",
        "real_orderbook_entry_ask_bid":"NOT_ARCHIVED",
        "actual_execution":"UNVERIFIED"
    }


def result_for_events(events, symbol_bars):
    locked_until={}  # per symbol; only accepted 24h proxy positions occupy a slot
    rows=[]
    for e in events:
        symbol=e["symbol"]
        observed=e["observed_ms"]
        entry_tick=observed+ENTRY_DELAY_MIN*MIN
        bars=symbol_bars.get(symbol)
        if bars is None:
            raise ValueError("MONSTER_SETUP120_SOURCE_SYMBOL_ABSENT")
        output={"event_id":e["event_id"],"symbol":symbol,"venue":"spot",
                "setup_observed_ms":observed,"proxy_entry_tick_ms":entry_tick,
                "proxy_entry_delay_minutes":ENTRY_DELAY_MIN}
        if observed<locked_until.get(symbol,0):
            output["primary_24h_status"]="SKIP_SAME_SYMBOL_24H_CAPITAL_OCCUPIED"
            output["horizons"]={}
        else:
            horizons={str(h):one_horizon(bars,entry_tick,h) for h in HORIZONS}
            output["horizons"]=horizons
            output["primary_24h_status"]=horizons["1440"]["status"]
            if horizons["1440"]["status"]=="PRICE_PROXY_ONLY":
                locked_until[symbol]=entry_tick+1440*MIN
        rows.append(output)
    if len(rows)!=len(events):
        raise ValueError("MONSTER_SETUP120_OUTPUT_ROW_COUNT_DRIFT")
    return rows


def median_or_none(vals):
    return str(statistics.median(vals)) if vals else None


def summarize(rows):
    grouped={}
    for hold in HORIZONS:
        key=str(hold)
        status=Counter()
        vals=[]
        stress=[]
        for r in rows:
            if r["primary_24h_status"]=="SKIP_SAME_SYMBOL_24H_CAPITAL_OCCUPIED":
                status["SKIP_SAME_SYMBOL_24H_CAPITAL_OCCUPIED"]+=1
                continue
            h=r["horizons"][key]
            status[h["status"]]+=1
            if h["status"]=="PRICE_PROXY_ONLY":
                vals.append((r["event_id"],r["symbol"],
                             Decimal(h["net_percent_fee10_slip20bps_each"])))
                stress.append(Decimal(h["net_percent_fee10_slip100bps_each"]))
        win=sum(x[2]>0 for x in vals)
        loss=sum(x[2]<0 for x in vals)
        flat=len(vals)-win-loss
        v=[x[2] for x in vals]
        biggest=sorted(vals,key=lambda x:x[2],reverse=True)
        worst=sorted(vals,key=lambda x:x[2])
        grouped[key]={
            "status_counts":dict(sorted(status.items())),
            "price_proxy_valid":len(vals),
            "win_count":win,"loss_count":loss,"flat_count":flat,
            "median_net_20bps_each_percent":median_or_none(v),
            "mean_net_20bps_each_percent":str(sum(v)/len(v)) if v else None,
            "median_net_100bps_each_percent":median_or_none(stress),
            "top_five_historical_net_percent_contributions":[{
                "event_id":eid,"symbol":symbol,"net_percent":str(pct)}
                for eid,symbol,pct in biggest[:5]],
            "worst_five_historical_net_percent":[{
                "event_id":eid,"symbol":symbol,"net_percent":str(pct)}
                for eid,symbol,pct in worst[:5]],
            "sum_independent_30usdt_price_proxy_pnl_usdt":(
                str(sum(v)*Decimal("0.3")) if v else None),
            "historical_30usdt_is_not_user_order_authorization":True
        }
        if sum(status.values())!=len(rows):
            raise ValueError("MONSTER_SETUP120_HORIZON_DENOMINATOR_DRIFT")
    return grouped


def audit(full_ab, source_dir):
    events=load_immutable_setups(full_ab)
    targets={e["symbol"] for e in events}
    archives=archive.verified_shard_paths(source_dir)
    if len(archives)!=28 or sum(len(shards.members(i)) for i,_,_ in archives)!=445:
        raise ValueError("MONSTER_SETUP120_ORIGINAL_445_SOURCE_CENSUS_DRIFT")
    sym_bars={}
    read_zip_sha=[]
    for shard_id,path,proof in archives:
        read_zip_sha.append({"shard":shard_id, "zip_sha256":proof["sha256_zip"]})
        if not targets.intersection(shards.members(shard_id)):
            continue
        for symbol,bars,receipts,meta in shards.read_archive(
                path,proof=proof,expected_shard=shard_id):
            if symbol not in targets:
                continue
            if symbol in sym_bars or meta.get("source_origin_verified_at_collection") is not True:
                raise ValueError("MONSTER_SETUP120_DUPLICATE_OR_UNATTESTED_SOURCE")
            verify_minute_rows(bars)
            sym_bars[symbol]=bars
    if set(sym_bars)!=targets:
        raise ValueError("MONSTER_SETUP120_56_SOURCE_SYMBOLS_NOT_ALL_FOUND")
    rows=result_for_events(events,sym_bars)
    summary=summarize(rows)
    return {
        "schema":SCHEMA,
        "stage162_original_full_sha256":AB_SHA,
        "source_venue":"Binance Spot",
        "research_cohort":"EXPOSED_FEBRUARY_2026_ORIGINAL_445_OF_758_WITH_313_CENSORED",
        "original_source_shard_zip_sha256":read_zip_sha,
        "source_445_verified_archive_shards":28,
        "setup_event_ids_total":len(events),
        "unique_setup_symbols":len(targets),
        "original_d0_watch_event_count":269,
        "original_D1_setups_baseline_and_fair8":120,
        "entry_rule":"1M_OPEN_EXACT_SETUP_PLUS_3MIN",
        "exit_horizons_minutes":list(HORIZONS),
        "fee_bps_per_side_assumed":10,
        "base_slippage_bps_per_side_assumed":20,
        "stress_slippage_bps_per_side_assumed":100,
        "primary_horizon_minutes":1440,
        "horizon_results":summary,
        "event_level_actual_source_rows":rows,
        "not_historical_true_pit_listing":True,
        "not_independent_OOS":True,
        "historical_orderbook": "NOT_ARCHIVED",
        "real_executable_net_profit":"UNKNOWN",
        "G4":"UNKNOWN","G6":"NO_GO",
        "NO_MERGE":True,"NO_DEPLOY":True,"NO_GMAIL":True,"NO_TRADE":True
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--stage162-full",type=Path,required=True)
    p.add_argument("--original28-source-dir",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    if a.out.exists() or a.out.is_symlink():
        raise ValueError("MONSTER_SETUP120_OUTPUT_EXISTS_REFUSE_REWRITE")
    j=audit(a.stage162_full,a.original28_source_dir)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    with a.out.open("x",encoding="utf-8") as fd:
        json.dump(j,fd,ensure_ascii=False,sort_keys=True,indent=2)
        fd.write("\n")
    print("MONSTER_ORIGINAL120_POST_SETUP_PRIMARY_PRICE_ECONOMICS",
          json.dumps({
            "setups":j["setup_event_ids_total"],
            "unique_symbols":j["unique_setup_symbols"],
            "primary_24h":j["horizon_results"]["1440"],
            "G4":j["G4"],"G6":j["G6"]
          },sort_keys=True))


if __name__=="__main__":
    main()
