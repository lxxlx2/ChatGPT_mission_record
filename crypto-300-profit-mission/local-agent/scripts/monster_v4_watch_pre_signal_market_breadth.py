#!/usr/bin/env python3
"""Offline as-of pre-WATCH market breadth, using original 445 source-complete Spot symbols.

Strictly a descriptive, already-exposed historical association, NOT an
economic regime model or a buy/sell recommendation.
"""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import statistics

import monster_v4_shared_445_one_db_from_shards as archive
import monster_v4_shared_445_official_source_shards as shards
import monster_v4_watch_vs_setup_incremental_value as economics

SCHEMA = "MONSTER_ORIGINAL269_WATCH_PRE_SIGNAL_445_BREADTH_DESCRIPTIVE_V1"
EVENT_SHA = "c30c8b6467b0017b36efc33fadfa2c7853f29f9c7e32993249774269ba4e2ae2"
ECON_BLOB = "62241ce57d5d275da289aa602bfde32070b0b4f2"
ONE_MINUTE = 60_000
START_LOOKBACK_MS = 63 * ONE_MINUTE
END_LOOKBACK_MS = 3 * ONE_MINUTE
MIN_VALID = 400
POSITIVE_BREADTH = Decimal("0.60")
NEGATIVE_BREADTH = Decimal("0.40")


def git_blob(raw):
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def load_fixed_inputs(ab, econ):
    if hashlib.sha256(ab.read_bytes()).hexdigest() != EVENT_SHA:
        raise ValueError("MONSTER_BREADTH_STAGE162_AB_SOURCE_SHA_DRIFT")
    raw = econ.read_bytes()
    if git_blob(raw) != ECON_BLOB:
        raise ValueError("MONSTER_BREADTH_ECONOMIC_269_SOURCE_BLOB_DRIFT")
    j = json.loads(ab.read_bytes())
    e = json.loads(raw)
    watches = sorted(
        (x for x in j["raw_alternative_events"] if x["event_type"] == "WATCH_EARLY"),
        key=lambda x:(x["observed_ms"],x["event_id"]))
    reported = e["WATCH"]["independent_signals"]
    locked = e["WATCH"]["causal_at_entry_same_symbol_24h_lock"]
    if (len(watches) != 269 or j["not_independent_OOS"] is not True
        or reported["original_total_signal_events"] != 269
        or locked["original_total_signal_events"] != 269
        or e["event_counts"] != {"WATCH":269,"SETUP":120}
        or len(e["WATCH"]["full_original_event_rows_no_lock"]) != 269
        or len(e["WATCH"]["full_original_event_rows_entry_time_lock"]) != 269
        or e["G4"] != "UNKNOWN" or e["G6"] != "NO_GO"):
        raise ValueError("MONSTER_BREADTH_FROZEN_WATCH_COHORT_DRIFT")
    expected = {x["event_id"]:x for x in watches}
    joined = {}
    for x in e["WATCH"]["full_original_event_rows_no_lock"]:
        aid = x["event_id"]
        if (aid not in expected or aid in joined
            or x["symbol"] != expected[aid]["symbol"]
            or x["event_time_ms"] != expected[aid]["observed_ms"]):
            raise ValueError("MONSTER_BREADTH_WATCH_EVENT_PRICE_IDENTITY_DRIFT")
        joined[aid] = x
    if set(joined) != set(expected):
        raise ValueError("MONSTER_BREADTH_EVENT_IDS_INCOMPLETE")
    return watches, joined


def prior_60m_percent(bars, t):
    """At WATCH=T, only exact CLOSED 1m candles open at T-63m and T-3m."""
    if not bars:
        return None
    base=bars[0][0]
    start=t-START_LOOKBACK_MS-base
    end=t-END_LOOKBACK_MS-base
    if start < 0 or end < 0 or start%ONE_MINUTE or end%ONE_MINUTE:
        return None
    ix,iy=start//ONE_MINUTE,end//ONE_MINUTE
    if iy>=len(bars) or bars[ix][0]!=t-START_LOOKBACK_MS or bars[iy][0]!=t-END_LOOKBACK_MS:
        return None
    try:
        p=Decimal(str(bars[ix][4]))
        q=Decimal(str(bars[iy][4]))
    except ArithmeticError:
        return None
    if not p.is_finite() or not q.is_finite() or p<=0 or q<=0:
        return None
    return (q/p-1)*100


def compute_prior_breadth(source_dir, ticks):
    archives=archive.verified_shard_paths(source_dir)
    if len(archives)!=28 or sum(len(shards.members(i)) for i,_,_ in archives)!=445:
        raise ValueError("MONSTER_BREADTH_FROZEN_445_ARCHIVE_CENSUS_DRIFT")
    all_ticks=sorted(set(ticks))
    metrics={t:{"sample":[],"up":0,"down":0,"flat":0,"btc":None} for t in all_ticks}
    seen=set()
    proofs=[]
    for ix,path,proof in archives:
        proofs.append({"shard":ix,"zip_sha256":proof["sha256_zip"]})
        for symbol,bars,receipts,metadata in shards.read_archive(
                path,proof=proof,expected_shard=ix):
            if symbol in seen or metadata.get("source_origin_verified_at_collection") is not True:
                raise ValueError("MONSTER_BREADTH_DUPLICATED_OR_UNATTESTED_SOURCE")
            seen.add(symbol)
            if len(bars)!=shards.MINUTE_ROWS:
                raise ValueError("MONSTER_BREADTH_SYMBOL_MINUTE_SOURCE_INCOMPLETE")
            for t in all_ticks:
                change=prior_60m_percent(bars,t)
                if change is None:
                    continue
                m=metrics[t]
                m["sample"].append(change)
                if change>0:m["up"]+=1
                elif change<0:m["down"]+=1
                else:m["flat"]+=1
                if symbol=="BTCUSDT":
                    m["btc"]=change
    if seen!=set(shards.roster()) or len(seen)!=445:
        raise ValueError("MONSTER_BREADTH_SOURCE_ALL445_IDENTITIES_MISSING")
    rows={}
    for t in all_ticks:
        m=metrics[t]
        n=len(m["sample"])
        if n!=m["up"]+m["down"]+m["flat"]:
            raise ValueError("MONSTER_BREADTH_CROSS_SECTION_COUNT_DRIFT")
        coverage=(Decimal(n)/Decimal(445))
        breadth=(Decimal(m["up"])/Decimal(n)) if n else None
        if n<MIN_VALID:
            label="UNOBSERVABLE"
        elif breadth >= POSITIVE_BREADTH:
            label="UP_BREADTH_GE_60PCT"
        elif breadth <= NEGATIVE_BREADTH:
            label="DOWN_BREADTH_LE_40PCT"
        else:
            label="MIXED_40_TO_60"
        rows[t]={
            "watch_observed_ms":t,
            "prior_60m_end_candle_open_ms":t-END_LOOKBACK_MS,
            "prior_60m_start_candle_open_ms":t-START_LOOKBACK_MS,
            "valid_symbols_out_of_445":n,
            "coverage":str(coverage),
            "positive_count":m["up"],"negative_count":m["down"],"flat_count":m["flat"],
            "positive_fraction":str(breadth) if breadth is not None else None,
            "median_prior_60m_return_percent":str(statistics.median(m["sample"])) if n else None,
            "btc_prior_60m_return_percent":str(m["btc"]) if m["btc"] is not None else "UNAVAILABLE",
            "pre_signal_breadth_class":label,
            "source_was_already_observable_before_watch":n>=MIN_VALID
        }
    return rows,proofs


def summarize_cohort(records):
    valid=[x for x in records if x["proxy_status"]=="PRICE_PROXY_ONLY"]
    vals=[Decimal(x["net_24h_percent"]) for x in valid]
    tick_counts=Counter(x["watch_observed_ms"] for x in records)
    dates=Counter(datetime.fromtimestamp(x["watch_observed_ms"]/1000,timezone.utc).date().isoformat()
                  for x in records)
    status=Counter(x["proxy_status"] for x in records)
    return {
        "original_event_count":len(records),
        "unique_watch_ticks":len(tick_counts),
        "distinct_utc_watch_days":len(dates),
        "watch_count_by_date_utc":dict(sorted(dates.items())),
        "largest_simultaneous_burst_event_count":max(tick_counts.values(),default=0),
        "source_proxy_status_counts":dict(sorted(status.items())),
        "evaluable_24h_price_proxies":len(valid),
        "wins":sum(v>0 for v in vals),
        "losses":sum(v<0 for v in vals),
        "median_24h_net_price_proxy_percent":str(statistics.median(vals)) if vals else None,
        "mean_24h_net_price_proxy_percent":str(sum(vals)/len(vals)) if vals else None,
        "distinct_evaluable_utc_days":len({datetime.fromtimestamp(x["watch_observed_ms"]/1000,timezone.utc).date()
                                            for x in valid}),
        "not_independent_event_sample":True
    }


def report(watches,source_by_id,tick_features,proofs):
    tick_counts=Counter(w["observed_ms"] for w in watches)
    episodes=[]
    for w in watches:
        feature=tick_features[w["observed_ms"]]
        price=source_by_id[w["event_id"]]
        row={
            "event_id":w["event_id"],"symbol":w["symbol"],
            "watch_observed_ms":w["observed_ms"],
            "pre_watch_class":feature["pre_signal_breadth_class"],
            "pre_watch_positive_fraction":feature["positive_fraction"],
            "pre_watch_median_60m_percent":feature["median_prior_60m_return_percent"],
            "proxy_status":price["status"],
            "net_24h_percent":(
                price["price_proxy"]["net_percent_fee10_slip20bps_each"]
                if price["status"]=="PRICE_PROXY_ONLY" else None),
            "simultaneous_watch_events_at_same_tick":tick_counts[w["observed_ms"]],
            "no_future_outcome_used_in_classification":True
        }
        episodes.append(row)
    byclass=defaultdict(list)
    for row in episodes:byclass[row["pre_watch_class"]].append(row)
    groups={k:summarize_cohort(byclass[k]) for k in
            ("UP_BREADTH_GE_60PCT","DOWN_BREADTH_LE_40PCT","MIXED_40_TO_60","UNOBSERVABLE")}
    tick_rows=[]
    per_tick=defaultdict(list)
    for e in episodes:per_tick[e["watch_observed_ms"]].append(e)
    for t,items in sorted(per_tick.items()):
        tick_rows.append({
            **tick_features[t],
            "watch_events":len(items),
            "evaluable_24h_proxies":sum(x["proxy_status"]=="PRICE_PROXY_ONLY" for x in items),
            "not_an_independent_strategy_trial":True
        })
    if len(episodes)!=269 or sum(g["original_event_count"] for g in groups.values())!=269:
        raise ValueError("MONSTER_BREADTH_COHORT_EVENT_COUNT_DRIFT")
    return {
        "schema":SCHEMA,
        "original_stage162_ab_sha256":EVENT_SHA,
        "previous_watch_economics_git_blob":ECON_BLOB,
        "original_445_source_shard_zip_sha256":proofs,
        "feature_definition":"ALL445_60MIN_CLOSED_1M_CLOSE_T_MINUS_63_AND_3",
        "pre_signal_breadth_thresholds":{"up_gte":"0.60","down_lte":"0.40","min_source_symbols":400},
        "watch_events":len(episodes),
        "unique_watch_ticks":len(tick_rows),
        "groups_by_preregistered_prior_breadth":groups,
        "full_269_watch_event_rows":episodes,
        "all_unique_tick_prior_breadth":tick_rows,
        "retrospective_market_regime_not_actionable_model":True,
        "original_758_missing_313_and_not_listing_PIT":True,
        "not_independent_OOS":True,"real_executable_positive_net_profit":"UNVERIFIED",
        "G4":"UNKNOWN","G6":"NO_GO","NO_MERGE":True,"NO_DEPLOY":True,
        "NO_GMAIL":True,"NO_TRADE":True
    }


def audit(ab,econ,source_dir):
    watches,byid=load_fixed_inputs(ab,econ)
    ticks=[x["observed_ms"] for x in watches]
    features,proofs=compute_prior_breadth(source_dir,ticks)
    return report(watches,byid,features,proofs)


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--stage162-full",required=True,type=Path)
    p.add_argument("--watch-setup-economics",required=True,type=Path)
    p.add_argument("--original28-source-dir",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    if a.out.exists() or a.out.is_symlink():
        raise ValueError("MONSTER_BREADTH_OUTPUT_EXISTS_REFUSE_OVERWRITE")
    r=audit(a.stage162_full,a.watch_setup_economics,a.original28_source_dir)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    with a.out.open("x",encoding="utf-8") as f:
        json.dump(r,f,indent=2,sort_keys=True,ensure_ascii=False)
        f.write("\n")
    print("MONSTER_PRIOR_ONLY_WATCH_445_MARKET_BREADTH_RESEARCH",
          json.dumps({"total":r["watch_events"],"ticks":r["unique_watch_ticks"],
                      "groups":r["groups_by_preregistered_prior_breadth"],
                      "G6":r["G6"]},sort_keys=True))


if __name__=="__main__":
    main()
