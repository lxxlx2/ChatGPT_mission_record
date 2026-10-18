#!/usr/bin/env python3
"""Same February source: original WATCH vs D1 SETUP descriptive price-proxy value.

Not a strategy optimizer or causally identified treatment effect. A SETUP
arises AFTER its WATCH, so selecting WATCHs by later SETUP is an oracle cohort.
No network, no execution, no historical PIT exchange/book reconstruction.
"""
import argparse
from collections import Counter, defaultdict
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import statistics

import monster_v4_original120_setup_price_economics as previous
import monster_v4_shared_445_one_db_from_shards as archives
import monster_v4_shared_445_official_source_shards as sources

SCHEMA = "MONSTER_WATCH_VS_SETUP_SAME445_ORIGINAL_SOURCE_DESCRIPTIVE_V1"
EVENT_SHA = "c30c8b6467b0017b36efc33fadfa2c7853f29f9c7e32993249774269ba4e2ae2"
PREVIOUS_SCRIPT_BLOB = "b02dbaa153d75beecc4a24c8af6b1e28484c14f5"
MINUTE = 60_000
DAY_MS = 1_440 * MINUTE


def git_blob(raw):
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\x00" + raw).hexdigest()


def load_events(source):
    raw = source.read_bytes()
    if hashlib.sha256(raw).hexdigest() != EVENT_SHA:
        raise ValueError("MONSTER_MAINLINE_AB_SOURCE_SHA256_MISMATCH")
    j = json.loads(raw)
    all_events = j["raw_alternative_events"]
    watch = [r for r in all_events if r["event_type"] == "WATCH_EARLY"]
    setup = [r for r in all_events if r["event_type"] == "SETUP_ACTIVE"]
    queue = j["raw_alternative_queue"]
    if (len(watch) != 269 or len(setup) != 120 or len(queue) != 269
        or len({r["event_id"] for r in watch + setup}) != 389
        or len({r["id"] for r in queue}) != 269
        or j["setup_event_id_baseline"] != 120
        or j["setup_event_id_alternative"] != 120
        or j["setup_new_ids"] or j["setup_lost_ids"]
        or j["not_independent_OOS"] is not True
        or j["G4"] != "UNKNOWN" or j["G6"] != "NO_GO"):
        raise ValueError("MONSTER_MAINLINE_EXPOSED_WATCH_SETUP_POPULATION_DRIFT")
    source_watch_keys = {(r["symbol"], r["observed_ms"]) for r in watch}
    queue_keys = {(r["symbol"], r["first_seen_ms"]) for r in queue}
    if len(source_watch_keys) != 269 or source_watch_keys != queue_keys:
        raise ValueError("MONSTER_MAINLINE_WATCH_QUEUE_UNIQUE_IDENTITY_DRIFT")
    for row in watch + setup:
        if (row["venue"] != "spot" or type(row["observed_ms"]) is not int
            or row["observed_ms"] % (3 * MINUTE) != 0):
            raise ValueError("MONSTER_MAINLINE_EVENT_TIME_OR_VENUE_DRIFT")
    if len({r["symbol"] for r in setup}) != 56:
        raise ValueError("MONSTER_MAINLINE_SETUP_56_SYMBOLS_DRIFT")
    if git_blob(Path(previous.__file__).read_bytes()) != PREVIOUS_SCRIPT_BLOB:
        raise ValueError("MONSTER_MAINLINE_FROZEN_ECONOMICS_FORMULA_BLOB_DRIFT")
    return (sorted(watch, key=lambda x:(x["observed_ms"],x["event_id"])),
            sorted(setup, key=lambda x:(x["observed_ms"],x["event_id"])),queue)


def source_bars(source_dir, target_symbols):
    shards = archives.verified_shard_paths(source_dir)
    if len(shards) != 28 or sum(len(sources.members(i)) for i,_,_ in shards) != 445:
        raise ValueError("MONSTER_MAINLINE_SHARD_28_FULL445_PROOF_DRIFT")
    result = {}
    proof_shas = []
    for idx, archive_path, proof in shards:
        proof_shas.append({"shard":idx,"zip_sha256":proof["sha256_zip"]})
        if not target_symbols.intersection(sources.members(idx)):
            continue
        for symbol, bars, receipts, metadata in sources.read_archive(
                archive_path, proof=proof, expected_shard=idx):
            if symbol not in target_symbols:
                continue
            if (symbol in result
                or metadata.get("source_origin_verified_at_collection") is not True):
                raise ValueError("MONSTER_MAINLINE_DUPLICATE_OR_UNATTESTED_SYMBOL")
            previous.verify_minute_rows(bars)
            result[symbol] = bars
    if set(result) != target_symbols:
        raise ValueError("MONSTER_MAINLINE_ARCHIVE_SYMBOL_SOURCE_MISSING")
    return result, proof_shas


def valid_entry(bars, entry_tick):
    """Only point-in-time entry proxy inputs may control 24h capital locking."""
    row = previous.get_bar(bars, entry_tick)
    if row is None:
        return "CENSORED_ENTRY_BAR_NOT_AVAILABLE"
    try:
        price = Decimal(row[1])
        quote = Decimal(row[5])
    except (ValueError, ArithmeticError):
        return "CENSORED_ENTRY_INVALID_PRICE_OR_QUOTE"
    if (not price.is_finite() or not quote.is_finite() or price <= 0
        or quote < 0):
        return "CENSORED_ENTRY_INVALID_PRICE_OR_QUOTE"
    if row[6] <= 0 or quote <= 0:
        return "CENSORED_NO_ENTRY_TRADES"
    if quote < previous.MIN_QUOTE:
        return "CENSORED_ENTRY_QUOTE_BELOW_30_USDT"
    return "ENTRY_PROXY_ADMISSIBLE"


def per_arm(events, bars_by_symbol, *, causal_symbol_lock):
    locks = {}
    records = []
    for e in events:
        minute = e["observed_ms"] + 3 * MINUTE
        bars = bars_by_symbol[e["symbol"]]
        item = {"event_id":e["event_id"],"symbol":e["symbol"],
                "event_time_ms":e["observed_ms"],
                "proxy_entry_ms":minute,"delayed_entry_minutes":3}
        admission = valid_entry(bars, minute)
        item["source_entry_admission"] = admission
        # Lock is decided solely at entry. Future exit quality cannot unlock
        # an already admissible 24-hour occupied position.
        if causal_symbol_lock and e["observed_ms"] < locks.get(e["symbol"], -1):
            item["status"] = "SKIP_SAME_SYMBOL_24H_LOCKED_AT_ENTRY"
        elif admission != "ENTRY_PROXY_ADMISSIBLE":
            item["status"] = admission
        else:
            if causal_symbol_lock:
                locks[e["symbol"]] = minute + DAY_MS
            evaluation = previous.one_horizon(bars, minute, 1440)
            item["status"] = evaluation["status"]
            item["price_proxy"] = evaluation
        records.append(item)
    if len(records) != len(events):
        raise ValueError("MONSTER_MAINLINE_MISSING_EVENT_RESULT")
    return records


def arm_summary(records):
    types = Counter(r["status"] for r in records)
    prices = [(r["event_id"],r["symbol"],
            Decimal(r["price_proxy"]["net_percent_fee10_slip20bps_each"]))
              for r in records if r["status"] == "PRICE_PROXY_ONLY"]
    stress = [Decimal(r["price_proxy"]["net_percent_fee10_slip100bps_each"])
              for r in records if r["status"] == "PRICE_PROXY_ONLY"]
    wins = sum(x[2] > 0 for x in prices)
    losses = sum(x[2] < 0 for x in prices)
    size = len(prices)
    if sum(types.values()) != len(records) or size != types["PRICE_PROXY_ONLY"]:
        raise ValueError("MONSTER_MAINLINE_ARM_DENOMINATOR_DRIFT")
    x = [r[2] for r in prices]
    return {
        "original_total_signal_events":len(records),
        "price_proxy_valid":size,
        "unique_symbols_with_valid_price_proxy":len({r[1] for r in prices}),
        "wins":wins,"losses":losses,"flats":size-wins-losses,
        "status_counts":dict(sorted(types.items())),
        "median_return_20bps_each_percent":str(statistics.median(x)) if x else None,
        "mean_return_20bps_each_percent":str(sum(x)/size) if x else None,
        "median_return_100bps_each_percent":str(statistics.median(stress)) if stress else None,
        "hypothetical_independent_30usdt_total_pnl":str(sum(x)*Decimal(".3")) if x else None,
        "biggest_five_realized_price_proxy_rows":[{
            "event_id": eid,"symbol":sym,"net_percent":str(value)
        } for eid,sym,value in sorted(prices,key=lambda a:a[2],reverse=True)[:5]],
        "no_executable_fill_or_fixed_total_cash_assumed":True,
    }


def matches(watch, setup, queues, bars):
    watches = {(r["symbol"],r["observed_ms"]):r for r in watch}
    queues_by_symbol=defaultdict(list)
    for q in queues:
        queues_by_symbol[q["symbol"]].append(q)
    pairs=[]
    counts=Counter()
    for event in setup:
        candidates=[q for q in queues_by_symbol[event["symbol"]]
                    if q["first_seen_ms"] <= event["observed_ms"] <= q["deadline_ms"]]
        if len(candidates)!=1:
            counts["AMBIGUOUS" if len(candidates)>1 else "UNMATCHED"] += 1
            pairs.append({"setup_event_id":event["event_id"],"symbol":event["symbol"],
                          "source_join_status":"AMBIGUOUS" if len(candidates)>1 else "UNMATCHED",
                          "candidate_queue_ids":[q["id"] for q in candidates]})
            continue
        q=candidates[0]
        origin=watches.get((event["symbol"],q["first_seen_ms"]))
        if origin is None:
            raise ValueError("MONSTER_MAINLINE_PAIR_WATCH_EVENT_ABSENT")
        watch_entry=origin["observed_ms"]+3*MINUTE
        setup_entry=event["observed_ms"]+3*MINUTE
        if not (watch_entry<=setup_entry and 0 <= event["observed_ms"]-origin["observed_ms"] <= 15*MINUTE):
            raise ValueError("MONSTER_MAINLINE_PAIR_TIME_OR_DEADLINE_DRIFT")
        sym_bars=bars[event["symbol"]]
        ready_w=valid_entry(sym_bars,watch_entry)
        ready_s=valid_entry(sym_bars,setup_entry)
        row={
            "source_join_status":"UNIQUE",
            "candidate_id":q["id"],"symbol":event["symbol"],
            "watch_event_id":origin["event_id"],"setup_event_id":event["event_id"],
            "watch_observed_ms":origin["observed_ms"],
            "setup_observed_ms":event["observed_ms"],
            "setup_delay_after_watch_minutes":(event["observed_ms"]-origin["observed_ms"])//MINUTE,
            "watch_entry_ms":watch_entry,"setup_entry_ms":setup_entry,
            "watch_entry_status":ready_w,"setup_entry_status":ready_s
        }
        if ready_w == ready_s == "ENTRY_PROXY_ADMISSIBLE":
            price_w=Decimal(previous.get_bar(sym_bars,watch_entry)[1])
            price_s=Decimal(previous.get_bar(sym_bars,setup_entry)[1])
            row["setup_entry_price_change_vs_watch_entry_percent"]=str(
                (price_s/price_w-1)*100)
            pw=previous.one_horizon(sym_bars,watch_entry,1440)
            ps=previous.one_horizon(sym_bars,setup_entry,1440)
            row["watch_24h_status"]=pw["status"]
            row["setup_24h_status"]=ps["status"]
            if pw["status"]==ps["status"]=="PRICE_PROXY_ONLY":
                rw=Decimal(pw["net_percent_fee10_slip20bps_each"])
                rs=Decimal(ps["net_percent_fee10_slip20bps_each"])
                row["watch_24h_net_percent"]=str(rw)
                row["setup_24h_net_percent"]=str(rs)
                row["paired_setup_minus_watch_net_percentage_points"]=str(rs-rw)
        pairs.append(row)
        counts["UNIQUE"] += 1
    if len(pairs)!=len(setup) or sum(counts.values())!=len(setup):
        raise ValueError("MONSTER_MAINLINE_PAIR_IDENTITY_DENOMINATOR_DRIFT")
    values=[Decimal(p["setup_entry_price_change_vs_watch_entry_percent"])
            for p in pairs if "setup_entry_price_change_vs_watch_entry_percent" in p]
    paired=[Decimal(p["paired_setup_minus_watch_net_percentage_points"])
            for p in pairs if "paired_setup_minus_watch_net_percentage_points" in p]
    return pairs,{
        "source_join_counts":dict(sorted(counts.items())),
        "entry_both_admissible":len(values),
        "median_setup_entry_price_change_vs_watch_percent":str(statistics.median(values)) if values else None,
        "setup_entry_price_higher_count":sum(x>0 for x in values),
        "setup_entry_price_lower_count":sum(x<0 for x in values),
        "setup_entry_price_equal_count":sum(x==0 for x in values),
        "both_24h_price_proxies_valid":len(paired),
        "median_setup_minus_watch_24h_return_percentage_points":str(statistics.median(paired)) if paired else None,
        "setup_24h_better_count":sum(x>0 for x in paired),
        "watch_24h_better_count":sum(x<0 for x in paired),
        "same_24h_return_count":sum(x==0 for x in paired),
        "historically_knowing_future_setup_at_watch_is_oracle_only":True
    }


def audit(ab_file, source_dir):
    watch,setup,queue=load_events(ab_file)
    targets={e["symbol"] for e in watch+setup}
    bars,proof_shas=source_bars(source_dir,targets)
    report={
        "schema":SCHEMA,
        "stage162_full_A_B_sha256":EVENT_SHA,
        "previous_exposed_setup_economics_code_blob":PREVIOUS_SCRIPT_BLOB,
        "read_only_original28_shard_zip_proofs":proof_shas,
        "source_population_original_445_of_758_313_censored":True,
        "event_counts":{"WATCH":len(watch),"SETUP":len(setup)},
        "same_symbol_holding_horizon_minutes":1440,
        "minute_open_entry_delay_after_each_signal_minutes":3,
        "fee_bps_each_side_assumed":10,
        "slippage_bps_each_side_base":20,
        "slippage_bps_each_side_stress":100,
        "entry_quote_minimum_usdt_for_source":30,
    }
    for label,evts in (("WATCH",watch),("SETUP",setup)):
        pure=per_arm(evts,bars,causal_symbol_lock=False)
        locked=per_arm(evts,bars,causal_symbol_lock=True)
        report[label]={
            "independent_signals":arm_summary(pure),
            "causal_at_entry_same_symbol_24h_lock":arm_summary(locked),
            "full_original_event_rows_no_lock":pure,
            "full_original_event_rows_entry_time_lock":locked
        }
    paired,ps=matches(watch,setup,queue,bars)
    report["descriptive_matched_later_setups"]={
        "summary":ps,"original_event_pairs":paired
    }
    report.update({
        "interpretation_scope":"HISTORICAL_EXPOSED_ASSOCIATION_NOT_CAUSAL_STRATEGY_GAIN",
        "not_independent_OOS":True,
        "true_historical_pit_listing_verified":False,
        "actual_executable_net_profit":"UNVERIFIED",
        "no_hindsight_setup_labels_are_buyable_at_watch":True,
        "G4":"UNKNOWN","G6":"NO_GO","NO_MERGE":True,"NO_DEPLOY":True,
        "NO_GMAIL":True,"NO_TRADE":True
    })
    return report


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--stage162-full",type=Path,required=True)
    p.add_argument("--original28-source-dir",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    if args.out.exists() or args.out.is_symlink():
        raise ValueError("MONSTER_MAINLINE_REFUSE_OVERWRITE")
    j=audit(args.stage162_full,args.original28_source_dir)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    with args.out.open("x",encoding="utf-8") as f:
        json.dump(j,f,sort_keys=True,indent=2,ensure_ascii=False)
        f.write("\n")
    def item(arm,locked):
        return j[arm][locked]
    print("MONSTER_WATCH_VS_SETUP_SAME_SOURCE_INCREMENTAL_VALUE",
          json.dumps({
            "WATCH_no_lock":item("WATCH","independent_signals"),
            "SETUP_no_lock":item("SETUP","independent_signals"),
            "WATCH_entry_lock":item("WATCH","causal_at_entry_same_symbol_24h_lock"),
            "SETUP_entry_lock":item("SETUP","causal_at_entry_same_symbol_24h_lock"),
            "paired":j["descriptive_matched_later_setups"]["summary"],
            "G4":j["G4"],"G6":j["G6"]},sort_keys=True))


if __name__=="__main__":
    main()
