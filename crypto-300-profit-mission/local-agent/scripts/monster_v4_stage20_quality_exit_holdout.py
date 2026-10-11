#!/usr/bin/env python3
"""Stage20: fixed unused-calendar V4 D1 quality+exit experiment, research-only.

All 758 source-attempted Spot pairs, unchanged V4 observe_snapshot/process_queue
and publisher SHA256 verified Binance 1m, including BTC benchmark. All quality
decisions depend ONLY on closes and volume known by D1 SETUP time.

Pre-committed manifest rules, four arms and cost scenarios. No optimization,
not point-in-time exchangeInfo, not historical orderbook, not executable fills.
"""
import argparse
import concurrent.futures
import json
import statistics
import sys
import urllib.error
from collections import Counter
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

try:
    import monster_v4_archive_universe_replay as archive
    import monster_v4_historical_replay as replay
    import monster_v4_stage15_archive_only as stage15
except ImportError:
    from scripts import monster_v4_archive_universe_replay as archive
    from scripts import monster_v4_historical_replay as replay
    from scripts import monster_v4_stage15_archive_only as stage15

MANIFEST = archive.source.EVIDENCE / "monster_stage20_quality_exit_holdout_prereg_20261011.json"
EXPECTED_DATES = ("2025-12-13","2026-01-13","2026-04-13","2026-07-13")
ARMS = ("A_ALL_D1_FIXED_24H_20BPS","B_ALL_D1_BOUNDED_6H_20BPS",
        "C_QUALITY_D1_FIXED_24H_20BPS",
        "D_QUALITY_D1_BOUNDED_6H_20BPS",
        "E_QUALITY_D1_BOUNDED_6H_100BPS")
WORKERS = 8
D = Decimal

def frozen_manifest():
    cfg=json.loads(MANIFEST.read_text(encoding="utf-8"))
    if cfg.get("schema")!="MONSTER_STAGE20_FROZEN_HOLDOUT_QUALITY_EXIT_COMPARISON_V1":
        raise ValueError("STAGE20_MANIFEST_NOT_FROZEN")
    if tuple(cfg.get("holdout_dates_utc",[]))!=EXPECTED_DATES or cfg.get("expected_symbols")!=758:
        raise ValueError("STAGE20_HOLDOUT_OR_UNIVERSE_CHANGED")
    q=cfg["quality_gate"]
    if (q["last_15m_quote_ratio_against_prior_45m_normalized_min"],
        q["last_1m_quote_min_usdt"],
        q["last_close_vs_previous_60m_high_drawdown_max_pct"],
        q["relative_60m_return_minus_btc_60m_min_percentage_points"],
        q["max_symbol_60m_return_pct"])!=(1.5,30,8,4,70):
        raise ValueError("STAGE20_QUALITY_RULE_CHANGED")
    risk=cfg["risk_exit"]
    if (risk["stop_loss_pct"],risk["take_profit_pct"],
        risk["timeout_min"],risk["execution_scenarios_bps_per_side"])!=(8,18,360,[20,100]):
        raise ValueError("STAGE20_RISK_EXIT_RULE_CHANGED")
    if tuple(cfg.get("arms",[]))!=ARMS:
        raise ValueError("STAGE20_ARMS_CHANGED")
    if cfg["baseline"]!={"trigger":"V4 production SETUP_ACTIVE from full calendar replay",
                          "entry_lag_min":3,"exit_fixed_min":1440,
                          "fee_bps_per_side":10,"slippage_bps_per_side":20,
                          "capital_usdt":30}:
        raise ValueError("STAGE20_BASELINE_CHANGED")
    return cfg

def universe(cfg, inventory_get=stage15.inventory):
    inv=inventory_get()
    if (inv["archive_only_sha256"]!=cfg["archive_only_sha256"] or
        len(inv["archive_only_symbols"])!=254 or
        len(stage15.frozen_current504())!=504):
        raise ValueError("STAGE20_ARCHIVE_UNIVERSE_DRIFT")
    syms=sorted(stage15.frozen_current504() | set(inv["archive_only_symbols"]))
    if len(syms)!=758:
        raise ValueError("STAGE20_MERGED_UNIVERSE_NOT_758")
    return syms,inv

def official_60h(symbol, day, get_day=archive.get_day):
    raw=[];proof=[]
    for offset in (-1,0,1):
        date_part=day+timedelta(days=offset)
        bar,detail=get_day(symbol,date_part)
        raw.extend(bar)
        proof.append({"date":date_part.isoformat(),"sha256":detail["sha256"]})
    bars=raw[360:3960]
    expected=replay.parse_ms(day.isoformat()+"T12:00:00Z")-30*3600000
    if len(bars)!=3600 or any(b[0]!=expected+i*60000 for i,b in enumerate(bars)):
        raise ValueError("STAGE20_GAPPED_OR_INCOMPLETE_60H")
    return bars,proof

def _causal_features(symbol_bars,btc_bars,setup_ms):
    if len(symbol_bars)!=3600 or len(btc_bars)!=3600:
        raise ValueError("STAGE20_INVALID_BARS")
    start=symbol_bars[0][0]
    if btc_bars[0][0]!=start:
        raise ValueError("STAGE20_BTC_TIME_MISMATCH")
    # Latest 1m bar that has FULLY CLOSED at D1 evaluation time.
    idx=(setup_ms-start)//60000-1
    if idx<1450 or idx>=2168:
        raise ValueError("STAGE20_SETUP_OUTSIDE_STUDY")
    sym=symbol_bars
    btc=btc_bars
    if sym[idx][0]>=setup_ms or btc[idx][0]>=setup_ms:
        raise ValueError("STAGE20_CAUSAL_BAR_IN_FUTURE")
    close=sym[idx][4]
    prev=sym[idx-60][4]
    bclose=btc[idx][4]
    bprev=btc[idx-60][4]
    if min(close,prev,bclose,bprev)<=0:
        raise ValueError("STAGE20_NONPOSITIVE_PRICE")
    recent=sum((x[5] for x in sym[idx-14:idx+1]),D(0))
    older=sum((x[5] for x in sym[idx-59:idx-14]),D(0))
    ratio=recent*3/older if older>0 else None
    highest=max(b[2] for b in sym[idx-59:idx+1])
    drawdown_pct=(1-close/highest)*100
    sym_60_pct=(close/prev-1)*100
    btc_60_pct=(bclose/bprev-1)*100
    relative_pct=sym_60_pct-btc_60_pct
    positives=all(x[6]>0 and x[5]>0 for x in sym[idx-5:idx+1])
    flags={
        "last_1m_quote_gte_30":sym[idx][5]>=30,
        "last_6m_traded":positives,
        "volume_ratio_15m_to_earlier_normalized45m_gte_1_5":
            ratio is not None and ratio>=D("1.5"),
        "within_8pct_60m_high":drawdown_pct<=8,
        "btc_relative_60m_gte_4_percentage_points":relative_pct>=4,
        "symbol_60m_return_lte_70pct":sym_60_pct<=70,
    }
    return {"feature_asof_utc":replay.utc(sym[idx][0]+60000),
        "last_1m_quote_usdt":str(sym[idx][5]),
        "quote_ratio_recent15_to_prior45":round(float(ratio),6) if ratio is not None else None,
        "highest_60m_drawdown_pct":round(float(drawdown_pct),6),
        "symbol_60m_return_pct":round(float(sym_60_pct),6),
        "btc_60m_return_pct":round(float(btc_60_pct),6),
        "relative_60m_return_pp":round(float(relative_pct),6),
        "flags":flags,
        "quality_pass":all(flags.values())}

def _exit_check(bars,entry_idx,exit_idx):
    if bars[exit_idx][6]<=0 or bars[exit_idx][5]<=0:
        return "CENSORED_ZERO_VOLUME_EXIT"
    if bars[exit_idx][5]<30:
        return "CENSORED_MINUTE_QUOTE_LT_30_USDT"
    if any(b[6]==0 for b in bars[max(entry_idx,exit_idx-5):exit_idx+1]):
        return "CENSORED_ZERO_VOLUME_NEAR_EXIT"
    return None

def bounded_exit(bars,setup_ms,slip_bps=20):
    """Conservative 1m OHLC stop-first 8%/18%, 6h time cap, no fill claim."""
    if slip_bps not in (20,100):
        raise ValueError("STAGE20_UNKNOWN_SLIPPAGE")
    start=bars[0][0]
    entry_idx=(setup_ms+180000-start)//60000
    end_idx=entry_idx+360
    if entry_idx<0 or end_idx>=len(bars):
        return {"status":"CENSORED_NO_COMPLETE_EXIT"}
    entry=bars[entry_idx][1]
    if entry<=0:
        return {"status":"SOURCE_INVALID_ENTRY_PRICE"}
    if bars[entry_idx][6]<=0 or bars[entry_idx][5]<=0:
        return {"status":"CENSORED_NO_ENTRY_TRADES"}
    if bars[entry_idx][5]<30:
        return {"status":"CENSORED_MINUTE_QUOTE_LT_30_USDT"}
    stop=entry*D("0.92")
    take=entry*D("1.18")
    j=end_idx;price=bars[j][1];reason="TIMEOUT_6H";both=False
    for k in range(entry_idx,end_idx):
        candle=bars[k]
        stop_hit=candle[3]<=stop
        take_hit=candle[2]>=take
        if stop_hit or take_hit:
            j=k
            both=stop_hit and take_hit
            if stop_hit:
                reason="STOP_FIRST_BOTH_IN_1M" if both else "STOP"
                price=min(stop,candle[1])
            else:
                reason="TAKE_PROFIT"
                price=take
            break
    censored=_exit_check(bars,entry_idx,j)
    if censored:
        return {"status":censored,"exit_reason":reason,
                "exit_utc":replay.utc(bars[j][0])}
    slip=D(slip_bps)/10000
    fee=D("0.001")
    pct=((price/entry)*(1-slip)/(1+slip)*(1-fee)**2-1)*100
    return {"status":"PRICE_PROXY_ONLY",
        "entry_utc":replay.utc(bars[entry_idx][0]),
        "exit_utc":replay.utc(bars[j][0]),
        "exit_reason":reason,"same_candle_both_stop_priority":both,
        "entry_price_1m_open":str(entry),"exit_price_conservative_1m_proxy":str(price),
        "net_pct":round(float(pct),6),"pnl_usdt_on_30":round(float(pct*D(".3")),6),
        "fee_bps_side":10,"slip_bps_side":slip_bps,
        "real_fill_verified":False,"historical_l2_available":False}

def run_symbol(symbol,day,btc_bars, get_bars=official_60h,
               v4_replay=replay.replay_case):
    try:
        if symbol=="BTCUSDT":
            bars=btc_bars
            proof=[{"reference":"BTCUSDT benchmark verified independently"}]
        else:
            bars,proof=get_bars(symbol,day)
        case=v4_replay({"venue":"spot","symbol":symbol,
            "cohort":"STAGE20_FROZEN_HOLDOUT_QUALITY_EXIT",
            "old_watch_utc":day.isoformat()+"T12:00:00Z"},
            bars,include_zero_trade_ticks=True)
        setups=case["setup_events"]
        result={"symbol":symbol,"status":"COMPLETE_60H",
             "archive_sha256":proof,
             "v4_watch":case["watch_count"],
             "v4_d1_episodes":len(setups),
             "first_v4_d1_utc":setups[0]["utc"] if setups else None}
        if setups:
            setup_ms=replay.parse_ms(setups[0]["utc"])
            features=_causal_features(bars,btc_bars,setup_ms)
            old=replay._proxy_trade(bars,bars[0][0],setup_ms,180000,20)
            bounded=bounded_exit(bars,setup_ms,20)
            expensive=bounded_exit(bars,setup_ms,100)
            result["quality"]=features
            result["arm_proxies"]={
                ARMS[0]:old,ARMS[1]:bounded,
                ARMS[2]:old if features["quality_pass"] else None,
                ARMS[3]:bounded if features["quality_pass"] else None,
                ARMS[4]:expensive if features["quality_pass"] else None}
        return result
    except ValueError as exc:
        reason=str(exc)
        if reason.startswith("SOURCE_NOT_HISTORICALLY_AVAILABLE_HTTP_"):
            status="SOURCE_MISSING"
        elif reason in ("GAPPED_ARCHIVE_DAY","INCOMPLETE_60H_REAL_ARCHIVE",
                        "STAGE20_GAPPED_OR_INCOMPLETE_60H"):
            status="SOURCE_PARTIAL_OR_NONCONTIGUOUS"
        else:
            status="SOURCE_INTEGRITY_REJECTED"
        return {"symbol":symbol,"status":status,"error":reason[:190]}
    except urllib.error.HTTPError as exc:
        return {"symbol":symbol,"status":"SOURCE_MISSING" if exc.code==404 else "SOURCE_HTTP_FAILURE","error":str(exc)[:140]}
    except (urllib.error.URLError,TimeoutError,OSError,ConnectionError) as exc:
        return {"symbol":symbol,"status":"SOURCE_NETWORK_FAILED","error":str(exc)[:140]}

def summarize(rows):
    statuses=Counter(x["status"] for x in rows)
    good=[x for x in rows if x["status"]=="COMPLETE_60H"]
    setups=[x for x in good if "arm_proxies" in x]
    output={"attempted":len(rows),"source_status":dict(statuses),
            "valid_60h":len(good),
            "v4_watch_episodes":sum(x["v4_watch"] for x in good),
            "v4_d1_episodes":sum(x["v4_d1_episodes"] for x in good),
            "symbol_dates_with_d1":len(setups),
            "quality_accepted":sum(x["quality"]["quality_pass"] for x in setups),
            "quality_rejected_flags":dict(Counter(k for x in setups for k,v in x["quality"]["flags"].items() if not v))}
    for arm in ARMS:
        trades=[x["arm_proxies"][arm] for x in setups if x["arm_proxies"][arm] is not None]
        ok=[x for x in trades if x["status"]=="PRICE_PROXY_ONLY"]
        net=[x["net_pct"] for x in ok]
        output[arm]={
            "selected":len(trades),"evaluated":len(ok),
            "positive":sum(n>0 for n in net),"negative":sum(n<0 for n in net),
            "median_pct":round(statistics.median(net),6) if net else None,
            "mean_pct":round(statistics.mean(net),6) if net else None,
            "sum_independent_30usdt":round(sum(n*0.30 for n in net),6),
            "censored":dict(Counter(x["status"] for x in trades
                                   if x["status"]!="PRICE_PROXY_ONLY")),
            "exit_reason":dict(Counter(x["exit_reason"] for x in ok if "exit_reason" in x))}
    return output

def run_day(day_str, worker=run_symbol, fetch_bars=official_60h):
    cfg=frozen_manifest()
    if day_str not in EXPECTED_DATES:
        raise ValueError("STAGE20_DATE_NOT_PREDECLARED")
    syms,inv=universe(cfg)
    day=date.fromisoformat(day_str)
    btc,btc_proof=fetch_bars("BTCUSDT",day)
    rows=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as pool:
        jobs={pool.submit(worker,s,day,btc):s for s in syms}
        for future in concurrent.futures.as_completed(jobs):
            item=future.result()
            if item.get("symbol")!=jobs[future]:
                raise ValueError("STAGE20_FUTURE_IDENTITY_MISMATCH")
            rows.append(item)
            if len(rows)%100==0:
                print("STAGE20_PROGRESS "+json.dumps({"date":day_str,
                    "completed":len(rows),"total":len(syms)}),
                    file=sys.stderr,flush=True)
    rows.sort(key=lambda x:x["symbol"])
    return {"schema":"MONSTER_STAGE20_FOUR_FROZEN_HOLDOUT_D1_QUALITY_EXIT_V1",
        "date":day_str,"source":"BINANCE_OFFICIAL_DAILY_SPOT_1M_ZIP_PUBLISHER_SHA256",
        "frozen_prereg":MANIFEST.name,"frozen_universe_hash":inv["archive_only_sha256"],
        "btc_benchmark_archive_sha256":btc_proof,
        "no_historical_book":True,
        "no_new_watch_rules":True,"no_forward_unbiased_7d_GT":True,
        "holdout_relative_to_old_dates":True,
        "summary":summarize(rows),"cases":rows,
        "other_ai_review":"NOT_DONE","deployment":"NO_GO",
        "real_gmail":False,"trading":False}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--date",choices=EXPECTED_DATES,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    report=run_day(args.date)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("STAGE20_RESULT_JSON "+json.dumps(report["summary"],sort_keys=True),flush=True)
    statuses=report["summary"]["source_status"]
    if statuses.get("COMPLETE_60H",0)<120:
        raise SystemExit("STAGE20_INSUFFICIENT_ARCHIVE_COVERAGE")
    if any(k in statuses for k in ("SOURCE_NETWORK_FAILED","SOURCE_HTTP_FAILURE",
                                   "SOURCE_INTEGRITY_REJECTED")):
        raise SystemExit("STAGE20_SOURCE_ERROR_OR_INTEGRITY")

if __name__=="__main__":
    main()
