#!/usr/bin/env python3
"""Stage31 original V4 D0/D1 causal forensics on five precommitted 2x/5x coins.

All 18 original Stage30 date-shard ZIPs SHA reverified; ten actual publisher-SHA
daily 1m sources per target must equal Stage30 source. Reuse exact original
observe_snapshot/process_queue for ALL 3360 polling moments, do not rewrite
signal. Separately inspect causal prior D0 predicates BEFORE production observes
current tick. 1m HIGH future crossing is label-only, never input to D0.
No model change, no trading, no BUY.
"""
import argparse
import bisect
import collections
import json
import tempfile
from datetime import date
from decimal import Decimal
from pathlib import Path

try:
    import monster_v4_stage30_aggregate as original
    import monster_v4_stage26_continuous168h as v4
    import monster_v4_stage16_seven_day_labels as gt
    import monster_v4_historical_replay as replay
    import monster_v4_shadow as live
except ImportError:
    from scripts import monster_v4_stage30_aggregate as original
    from scripts import monster_v4_stage26_continuous168h as v4
    from scripts import monster_v4_stage16_seven_day_labels as gt
    from scripts import monster_v4_historical_replay as replay
    from scripts import monster_v4_shadow as live

EVIDENCE=original.EVIDENCE
CFG=EVIDENCE/"monster_stage31_five_meme_case_causal_d0_missed_winner_prereg_20261011.json"
LABEL_SCHEMA="MONSTER_STAGE31_FIVE_ORIGINAL_V4_168H_CAUSAL_SIGNAL_MISS_V1"
MARKET_DATES=("2025-01-19","2025-04-19","2025-07-19")
SHARDS=6

def contract():
    o=json.loads(CFG.read_text(encoding="utf-8"))
    if o.get("schema")!="MONSTER_STAGE31_FROZEN_FIVE_ST30_MISSED_LATE_VS_5X_WINNER_CAUSAL_TRACE_V1":
        raise ValueError("STAGE31_CONTRACT_DRIFT")
    if (len(o["frozen_cases"])!=5 or {x["symbol"] for x in o["frozen_cases"]}!=
        {"VTHOUSDT","PENGUUSDT","CETUSUSDT","ALPACAUSDT","SPKUSDT"}):
        raise ValueError("STAGE31_FIVE_COHORT_CHANGED")
    if v4.git_sha(live.__file__)!=o["locked_original_sha"]["v4"] or (
       v4.git_sha(v4.__file__)!=o["locked_original_sha"]["historical_replay"]):
        raise ValueError("STAGE31_UNCHANGED_ORIGINAL_V4_BLOB_MISMATCH")
    if (o["controls"]["quote24_usdt"],o["controls"]["returns_3m_pct"],
        o["controls"]["returns_15m_pct"],o["controls"]["returns_60m_pct"],
        o["controls"]["watch_cooldown_hours"])!=(100000,5,8,15,6):
        raise ValueError("STAGE31_V4_THRESHOLD_MISMATCH")
    return o

def original_five_cases(paths):
    m=contract()
    proof=json.loads(original.ARTS.read_text(encoding="utf-8"))
    index={(x["date"],x["shard"]):x for x in proof["artifacts"]}
    if len(paths)!=18:raise ValueError("STAGE31_REQUIRE_ALL18_ORIGINAL_SHARDS")
    got={};symbols_by_day={}
    for path in paths:
        import zipfile
        with zipfile.ZipFile(path) as z:
            names=z.namelist()
        if len(names)!=1 or not names[0].startswith("monster_stage30_") or "_shard" not in names[0]:
            raise ValueError("STAGE31_NOT_STAGE30_ZIP")
        day,shard=names[0].removeprefix("monster_stage30_").removesuffix(".json").split("_shard")
        key=(day,int(shard))
        if key not in index or day not in MARKET_DATES or key in got:
            raise ValueError("STAGE31_INVALID_OR_DUPLICATE_SOURCE_SHARD")
        decoded=original.decode(path,index[key])
        got[key]=decoded
        ss=symbols_by_day.setdefault(day,set())
        if ss.intersection(r["symbol"] for r in decoded["cases"]):
            raise ValueError("STAGE31_REPEATED_SYMBOL_ACROSS_SHARDS")
        ss.update(r["symbol"] for r in decoded["cases"])
    if set(got)!={(d,s) for d in MARKET_DATES for s in range(SHARDS)}:
        raise ValueError("STAGE31_MISSING_18_SHA_VERIFIED_SHARDS")
    if any(len(x)!=758 for x in symbols_by_day.values()):
        raise ValueError("STAGE31_NOT_ENTIRE_758_ORIGINAL_SOURCE")
    out=[]
    for cfg in m["frozen_cases"]:
        matches=[r for (d,_),data in got.items() if d==cfg["day"]
                 for r in data["cases"] if r["symbol"]==cfg["symbol"]]
        if len(matches)!=1:raise ValueError("STAGE31_MISSING_TARGET_IN_ORIGINAL")
        row=matches[0]
        if row["status"]!="COMPLETE_168H_CONTINUOUS_V4":
            raise ValueError("STAGE31_TARGET_NOT_ORIGINAL_FULL_SOURCE")
        label=row["labels"][str(cfg["target_m"])+"x"]
        if label["classification"]!=cfg["expected_class"] or (
             label["real_1m_cross_utc"]!=cfg["cross"]):
            raise ValueError("STAGE31_ORIGINAL_CROSS_OR_LABEL_CHANGED")
        out.append((cfg,row))
    return out

def diagnostic_predicates(db,symbol,now_ms,price,quote):
    """Inspect same exact historical windows as production BEFORE this poll.

    Mirror gating for EXPLANATION only. The actual signal comes exclusively
    from original V4 observe_snapshot; cross-event labels are not accessible.
    """
    last=db.execute("SELECT observed_ms,price FROM snapshots WHERE venue='spot' AND symbol=?",
                    (symbol,)).fetchone()
    prior=db.execute("""SELECT last_watch_ms,last_watch_price,invalidated FROM watch_state
                         WHERE venue='spot' AND symbol=?""",(symbol,)).fetchone()
    ret3=None
    if last is not None and live.MIN_DELTA_MS<=now_ms-last["observed_ms"]<=live.MAX_DELTA_MS:
        ret3=price/Decimal(last["price"])-1
    ret15=live.historical_return(db,"spot",symbol,now_ms,price,15*60000,3*60000)
    ret60=live.historical_return(db,"spot",symbol,now_ms,price,60*60000,6*60000)
    hit3=ret3 is not None and ret3>=Decimal("0.05")
    hit15=ret15 is not None and ret15["return"]>=Decimal("0.08")
    hit60=ret60 is not None and ret60["return"]>=Decimal("0.15")
    has_move=hit3 or hit15 or hit60
    sufficient_quote=quote>=Decimal("100000")
    invalidated_by_drop=(prior is not None and not prior["invalidated"] and
          price<=Decimal(prior["last_watch_price"])*Decimal("0.85"))
    cooldown=(prior is not None and not prior["invalidated"] and
          not invalidated_by_drop and
          now_ms-prior["last_watch_ms"]<live.WATCH_COOLDOWN_MS)
    reason=("NO_3M_15M_60M_THRESHOLD" if not has_move else
            "QUOTE24_LT_100K" if not sufficient_quote else
            "ALREADY_WATCHED_6H_COOLDOWN" if cooldown else "ELIGIBLE_FOR_ORIGINAL_WATCH")
    return {"snapshot_asof_utc":replay.utc(now_ms),"price_last_closed_1m":str(price),
        "quote24_usdt_prior_1440_closed_minutes":str(quote),
        "return_3m_pct":round(float(ret3*100),6) if ret3 is not None else None,
        "return_15m_pct":round(float(ret15["return"]*100),6) if ret15 is not None else None,
        "return_60m_pct":round(float(ret60["return"]*100),6) if ret60 is not None else None,
        "hit_3m5":bool(hit3),"hit_15m8":bool(hit15),"hit_60m15":bool(hit60),
        "quote24_pass_100k":bool(sufficient_quote),
        "cooldown_from_prior_watch":bool(cooldown),
        "prior_watch_invalidated_by_15pct_drop":bool(invalidated_by_drop),
        "D0_gate_explanation":reason}

def trace_case(cfg,row,market_get=v4.read_complete_216h,hourly_get=gt.label):
    day=date.fromisoformat(cfg["day"])
    bars,publisher_proof=market_get(cfg["symbol"],day)
    if publisher_proof!=row["official_source_SHA256_days"]:
        raise ValueError("STAGE31_OFFICIAL_10_DAILY_1M_SOURCE_SHA_OR_DATES_CHANGED")
    hr=hourly_get(cfg["symbol"],day)
    if hr.get("status")!="VERIFIED_COMPLETE_168H" or (
       hr.get("archive_sha256")!=row["hourly_GT_monthly_SHA256"]):
        raise ValueError("STAGE31_ORIGINAL_MONTHLY_1H_GT_SOURCE_SHA_CHANGED")
    crossing=v4.first_real_1m_cross(day,bars,hr["baseline_1h_open"],cfg["target_m"])
    cross_ms=replay.parse_ms(cfg["cross"])
    if crossing!=cross_ms:
        raise ValueError("STAGE31_REAL_1M_HIGH_CROSS_CHANGED")
    base=replay.parse_ms(cfg["day"]+"T06:00:00Z")-v4.WARMUP_MINUTES*60000
    if bars[0][0]!=base or len(bars)!=v4.EXPECTED_MINUTES:
        raise ValueError("STAGE31_BAD_ACTUAL_216H_MARKET_SOURCE")
    prefix=[Decimal(0)]
    for bar in bars:prefix.append(prefix[-1]+bar[5])
    candles=replay.make_closed_five_minute_bars(bars)
    ends=[int(c[6]) for c in candles]
    first=v4.WARMUP_MINUTES+2
    last=v4.WARMUP_MINUTES+v4.ACTIVE_MINUTES
    raw_trace=[];gates=collections.Counter();gates_before=collections.Counter()
    watch_utc=[];zero_trade_poll=0;predicted_yes=0;observed_yes=0
    with tempfile.TemporaryDirectory(prefix="monster_stage31_original_v4_d0_") as td:
        db=live.open_store(Path(td)/"one_coin_original.sqlite")
        try:
            def closed_5m(_venue,_symbol,observed_ms):
                i=bisect.bisect_left(ends,observed_ms)
                return candles[max(0,i-8):i]
            for i in range(first,last,3):
                now=bars[i][0]+60000
                p=Decimal(str(bars[i][4]))
                q=prefix[i+1]-prefix[i+1-replay.ROLLING_24H_BARS]
                if not bars[i][5] or not bars[i][6]:zero_trade_poll+=1
                feature=diagnostic_predicates(db,cfg["symbol"],now,p,q)
                reason=feature["D0_gate_explanation"]
                gates[reason]+=1
                if cross_ms-6*3600000<=now<=cross_ms:
                    gates_before[reason]+=1
                original_observation=live.observe_snapshot(db,"spot",now,[{
                    "symbol":cfg["symbol"],"lastPrice":str(p),"quoteVolume":str(q)}])
                live.process_queue(db,now,closed_5m)
                actual_watch=original_observation["watch_new"]==1
                predicted_watch=(reason=="ELIGIBLE_FOR_ORIGINAL_WATCH")
                if predicted_watch:predicted_yes+=1
                if actual_watch:observed_yes+=1;watch_utc.append(replay.utc(now))
                if actual_watch!=predicted_watch:
                    raise ValueError("STAGE31_MIRRORED_CAUSAL_GATE_DIFFERS_FROM_UNCHANGED_V4_D0")
                if cross_ms-6*3600000<=now<=cross_ms+2*3600000 or actual_watch:
                    feature["actual_V4_WATCH_EARLY"]=actual_watch
                    feature["relative_to_first_intraminute_HIGH_cross_min"]=round((now-cross_ms)/60000,3)
                    raw_trace.append(feature)
            for extra in range(1,8):
                now=replay.parse_ms(cfg["day"]+"T06:00:00Z")+v4.ACTIVE_MINUTES*60000+extra*180000
                live.process_queue(db,now,closed_5m)
            events=[dict(x) for x in db.execute(
                "SELECT event_type,observed_ms,payload FROM events ORDER BY observed_ms,event_id")]
        finally:
            db.close()
    watch_actual=[replay.utc(e["observed_ms"]) for e in events if e["event_type"]=="WATCH_EARLY"]
    setup_actual=[replay.utc(e["observed_ms"]) for e in events if e["event_type"]=="SETUP_ACTIVE"]
    if watch_actual!=row["continuous"]["watch_utcs"] or setup_actual!=row["continuous"]["setup_utcs"]:
        raise ValueError("STAGE31_ACTUAL_ORIGINAL_WATCH_OR_SETUP_TIMES_DIFFER_FROM_STAGE30")
    if watch_actual!=watch_utc or predicted_yes!=observed_yes:
        raise ValueError("STAGE31_D0_WATCH_GATE_NOT_REPRODUCIBLE")
    crossbar=bars[(cross_ms-base)//60000]
    threshold=Decimal(str(hr["baseline_1h_open"]))*Decimal(cfg["target_m"])
    if crossbar[2]<threshold:
        raise ValueError("STAGE31_FALSE_CROSS")
    around=[x for x in raw_trace if cross_ms-6*3600000<=replay.parse_ms(x["snapshot_asof_utc"])<=cross_ms+2*3600000]
    prior=[x for x in around if replay.parse_ms(x["snapshot_asof_utc"])<=cross_ms]
    after=[x for x in around if replay.parse_ms(x["snapshot_asof_utc"])>cross_ms]
    events2=[{"event_type":e["event_type"],
              "UTC":replay.utc(e["observed_ms"]),
              "payload":json.loads(e["payload"])}
              for e in events if e["event_type"] in ("WATCH_EARLY","SETUP_ACTIVE","INVALIDATED","LATE_REVIEW")]
    return {
        "date":cfg["day"],"symbol":cfg["symbol"],"multiple":cfg["target_m"],
        "original_stage30_GT_classification":cfg["expected_class"],
        "first_original_1m_high_cross_UTC":cfg["cross"],
        "cross_minute_open":str(crossbar[1]),"cross_minute_high":str(crossbar[2]),
        "cross_minute_close":str(crossbar[4]),
        "cross_minute_close_reaches_multiple":bool(crossbar[4]>=threshold),
        "GT_baseline_UTC_06_first_hour_open":hr["baseline_utc"],
        "GT_baseline_open":hr["baseline_1h_open"],
        "GT_threshold_high_price":str(threshold),
        "hourly_GT_source_SHA256":hr["archive_sha256"],
        "original_10_publisher_daily_1m_SHA256":publisher_proof,
        "original_V4_3m_polls":sum(gates.values()),"nontraded_minute_poll_count":zero_trade_poll,
        "diagnostic_gate_total":dict(gates),
        "gate_before_first_true_HIGH_cross_last_6h":dict(gates_before),
        "D0_directly_eligible_polls":predicted_yes,
        "original_V4_WATCH_total":len(watch_actual),
        "original_V4_SETUP_total":len(setup_actual),
        "all_original_V4_event_UTC_and_payload":events2,
        "last_poll_not_later_than_high_cross":prior[-1] if prior else None,
        "first_poll_after_high_cross":after[0] if after else None,
        "trace_near_cross_6h_before_2h_after_plus_original_early_watches":raw_trace,
        "original_Stage30_watch_proxy_20bps":[{"watch_utc":x["watch_utc"],
                   "status":x["proxy_20bps"]["status"],
                   "net_pct":x["proxy_20bps"].get("net_pct")}
               for x in row["continuous"]["trade_proxies"]],
        "no_GT_or_future_candle_fed_into_original_D0":True,
        "original_blobs_SHA_validated":True,"original_168h_SCAN_original_functions_unchanged":True,
        "real_exchange_execution_proven":False,"no_buy_recommendation":True}

def run(source_paths):
    contract()
    originals=original_five_cases(source_paths)
    done=[]
    for cfg,row in originals:
        done.append(trace_case(cfg,row))
        print("STAGE31_CASE "+json.dumps({
            "symbol":cfg["symbol"],"day":cfg["day"],"UTC_cross":cfg["cross"],
            "WATCH":done[-1]["original_V4_WATCH_total"],
            "SETUP":done[-1]["original_V4_SETUP_total"],
            "gates_6h":done[-1]["gate_before_first_true_HIGH_cross_last_6h"],
            "cross_candle_close_ge_target":done[-1]["cross_minute_close_reaches_multiple"],
            "last_poll":done[-1]["last_poll_not_later_than_high_cross"]},sort_keys=True),flush=True)
    return {"schema":LABEL_SCHEMA,"original_stage30_18_ZIP_JSON_SHA_verified":True,
         "original_stage30_758_per_target_day_all_source_cases":True,
         "all_five_cases":done,
         "independent_new_profit_strategy_validation":False,
         "source_official_1h_plus_10_days_1m_SHA_reverified_and_parity_original":True,
         "new_runtime_filter_or_threshold_added":False,
         "independent_other_AI_review":"NOT_DONE",
         "real_gmail":"OFF","trading":"NO_GO","monster_deployment":"NO_GO","frank":"UNCHANGED"}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--stage30-source-zips",type=Path,nargs=18,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    result=run(a.stage30_source_zips)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("STAGE31_ALL_FIVE_VERIFIED "+json.dumps({
        "cases":len(result["all_five_cases"]),
        "symbols":[x["symbol"] for x in result["all_five_cases"]],
        "all_original_sha":result["source_official_1h_plus_10_days_1m_SHA_reverified_and_parity_original"],
        "no_deployment":result["monster_deployment"]},sort_keys=True),flush=True)
if __name__=="__main__":main()
