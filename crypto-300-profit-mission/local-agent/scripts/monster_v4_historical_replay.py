#!/usr/bin/env python3
"""Causal Monster V4 replay using THE production observe_snapshot/process_queue.

Frozen official Binance 1m historical bars only. Reconstructs a rolling
1m-aggregate 24h quoteVolume as an explicitly labeled PROXY, never fabricates
historical exchangeInfo or historical L2 books. Entry/exit prices are NOT fills.
This research is not an independent holdout or proof of trading profitability.
"""
import argparse
import json
import statistics
import tempfile
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

try:
    import monster_v4_shadow as live
except ImportError:
    from scripts import monster_v4_shadow as live

EVIDENCE = Path(__file__).resolve().parents[2] / "monster/evidence"
INTERVAL_1M = 60_000
INTERVAL_5M = 300_000
STUDY_MS = 6 * 3600_000
ROLLING_24H_BARS = 1440
EXPECTED_BARS = 3600
SCENARIOS_BPS = (0, 20, 100)


def parse_ms(utc):
    return int(datetime.fromisoformat(utc.replace("Z", "+00:00")).timestamp() * 1000)


def utc(ms):
    return datetime.fromtimestamp(ms/1000, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def dec(x):
    x = Decimal(str(x))
    if not x.is_finite():
        raise ValueError("NONFINITE_SOURCE_BAR")
    return x


def load_case(path):
    src = json.loads(Path(path).read_text(encoding="utf-8"))
    if src.get("schema") != "MONSTER_V4_1M_REPLAY_BAR_V1":
        raise ValueError("WRONG_REPLAY_SCHEMA")
    rows = src.get("bars")
    if not isinstance(rows, list) or len(rows) != EXPECTED_BARS:
        raise ValueError("WRONG_BAR_COUNT")
    start = parse_ms(src["old_watch_utc"]) - 30*3600_000
    if src["first_bar_open_ms"] != start:
        raise ValueError("MISMATCHED_START")
    if src.get("data_integrity") != "CONTIGUOUS_3600" or src.get("anomalies"):
        raise ValueError("SOURCE_MARKED_INCOMPLETE")
    bars = []
    for i, row in enumerate(rows):
        if not isinstance(row, list) or len(row) != 7:
            raise ValueError("INVALID_COMPACT_BAR")
        ms = int(row[0])
        if ms != start + i * INTERVAL_1M:
            raise ValueError("GAPPED_OR_REORDERED_1M_HISTORY")
        o, h, lo, c, quote = map(dec, row[1:6])
        trade_count = int(row[6])
        if (min(o, h, lo, c) <= 0 or lo > min(o, c) or
                h < max(o, c) or lo > h or quote < 0 or trade_count < 0):
            raise ValueError("INVALID_OHLC_OR_VOLUME")
        bars.append((ms,o,h,lo,c,quote,trade_count))
    if src["venue"] not in ("spot", "futures"):
        raise ValueError("INVALID_VENUE")
    return src, bars


def make_closed_five_minute_bars(bars):
    """Construct Binance-compatible closed 5m rows from 1m raw OHLCV."""
    if len(bars) % 5:
        raise ValueError("UNCLOSED_5M_GROUP")
    result=[]
    for i in range(0,len(bars),5):
        group=bars[i:i+5]
        if group[0][0] % INTERVAL_5M:
            raise ValueError("NONALIGNED_5M")
        result.append([
            group[0][0],str(group[0][1]),
            str(max(v[2] for v in group)),
            str(min(v[3] for v in group)),
            str(group[-1][4]),"0",
            group[-1][0]+59999,
            str(sum((v[5] for v in group),Decimal(0)))
        ])
    return result


def round6(x):
    return round(float(x),6)


def _proxy_trade(bars, base_ms, watch_ms, delay_ms, slip_bps, hold_minutes=1440):
    # Observed WATCH uses already closed 1m, entry is first 1m OPEN
    # at/after the specified future latency (no future price in signal).
    entry_ms=watch_ms+delay_ms
    i=(entry_ms-base_ms)//INTERVAL_1M
    if not isinstance(hold_minutes,int) or hold_minutes<=0:
        raise ValueError("INVALID_REPLAY_HOLD_MINUTES")
    exit_i=i+hold_minutes
    if i < 0 or exit_i >= len(bars):
        return {"status":"CENSORED_NO_COMPLETE_EXIT"}
    entry=bars[i][1]; exit_price=bars[exit_i][1]
    if entry <= 0 or exit_price <= 0:
        return {"status":"NO_EXECUTABLE_PRICE"}
    # A fixed price from a zero-trade delisting bar is not an executable exit.
    if bars[i][6] == 0 or bars[i][5] == 0:
        return {"status":"CENSORED_NO_ENTRY_TRADES"}
    if bars[exit_i][6] == 0 or bars[exit_i][5] == 0:
        return {"status":"CENSORED_ZERO_VOLUME_EXIT"}
    if bars[i][5] < 30 or bars[exit_i][5] < 30:
        return {"status":"CENSORED_MINUTE_QUOTE_LT_30_USDT"}
    if any(v[6] == 0 for v in bars[max(i,exit_i-5):exit_i+1]):
        return {"status":"CENSORED_ZERO_VOLUME_NEAR_EXIT"}
    fee=Decimal("0.001")
    slippage=Decimal(slip_bps)/10000
    gross=(exit_price/entry-1)*100
    net=((exit_price/entry)*(1-slippage)/(1+slippage)*
         (1-fee)**2-1)*100
    min_low=min(b[3] for b in bars[i:exit_i+1])
    max_high=max(b[2] for b in bars[i:exit_i+1])
    return {"status":"PRICE_PROXY_ONLY",
            "entry_utc":utc(bars[i][0]), "exit_utc":utc(bars[exit_i][0]),
            "gross_pct":round6(gross),"net_pct":round6(net),
            "pnl_usdt_on_30":round6(Decimal(30)*net/100),
            "min_low_excursion_pct":round6((min_low/entry-1)*100),
            "max_high_excursion_pct":round6((max_high/entry-1)*100),
            "fee_per_side_bps_assumed":10,"slippage_per_side_bps_assumed":slip_bps,
            "historical_book_verified":False}


def replay_case(src, bars, include_zero_trade_ticks=False):
    """Default preserves Stage7 skip policy; opt-in models a ticker present
    even when the most recent closed minute bar has no actual trades. Both
    paths use the exact same production D0/D1 decision functions.
    """
    first=bars[0][0]
    anchor=parse_ms(src["old_watch_utc"])
    # Observe first 24h silently to create the known 24h volume window;
    # then start the actual same-code scanner at anchor-6h.
    quote_prefix=[Decimal(0)]
    for x in bars:
        quote_prefix.append(quote_prefix[-1]+x[5])
    candles=make_closed_five_minute_bars(bars)
    start_i=1442  # completed 24h plus a 3m-aligned first poll at 24h+3m
    # At 30h prior anchor and index 1442, observation starts ~6h before anchor.
    end_i=2160 # last poll at 6h after historical anchor
    if bars[start_i][0]%INTERVAL_1M != 0:
        raise ValueError("MISALIGNED_OBSERVATION")
    no_trade_minutes=0
    polls=0
    with tempfile.TemporaryDirectory(prefix="monster_v4_backtest_") as temp:
        db=live.open_store(Path(temp)/"replay.sqlite")
        try:
            def closed_5m(_venue,_symbol,now_ms):
                return [b for b in candles if b[0] + INTERVAL_5M <= now_ms][-8:]
            for i in range(start_i,end_i,3):
                ms=bars[i][0]+INTERVAL_1M # 1m closed; 3m pseudo-ticker poll
                # Binance exchangeInfo was not archived. Zero-trade bars must
                # not be treated as confirmed tradable live market ticks.
                if bars[i][6] == 0 or bars[i][5] == 0:
                    no_trade_minutes+=1
                    if not include_zero_trade_ticks:
                        continue
                rolling_quote=quote_prefix[i+1]-quote_prefix[i+1-ROLLING_24H_BARS]
                live.observe_snapshot(db,src["venue"],ms,[{
                    "symbol":src["symbol"],"lastPrice":str(bars[i][4]),
                    "quoteVolume":str(rolling_quote)}])
                live.process_queue(db,ms,closed_5m)
                polls+=1
            # Sweep unfinished D1 candidates through their expiry using the
            # next closed bars, without creating additional D0 observations.
            for extra in range(1,8):
                ms=bars[end_i][0]+extra*180000
                live.process_queue(db,ms,closed_5m)
            events=[dict(x) for x in db.execute(
                "SELECT event_id,event_type,observed_ms,payload FROM events ORDER BY observed_ms,event_id")]
            watches=[x for x in events if x["event_type"]=="WATCH_EARLY"]
            setups=[x for x in events if x["event_type"]=="SETUP_ACTIVE"]
            d1state={r["status"]:r["n"] for r in db.execute(
                "SELECT status,COUNT(*) n FROM candidate_queue GROUP BY status")}
            trade_proxies=[]
            last_entered_ms=None
            for watch in watches:
                by_scenario={}
                # Non-overlap is essential: a 24h position cannot be reopened
                # on the same symbol six hours later as if capital were free.
                overlap=(last_entered_ms is not None and
                         watch["observed_ms"]+180_000<last_entered_ms+24*3600_000)
                for slip in SCENARIOS_BPS:
                    by_scenario[str(slip)]=(
                        {"status":"OVERLAPPING_24H_HOLD_NO_NEW_POSITION"} if overlap else
                        _proxy_trade(bars,first,watch["observed_ms"],180000,slip))
                if not overlap and by_scenario["20"]["status"]=="PRICE_PROXY_ONLY":
                    last_entered_ms=watch["observed_ms"]+180_000
                trade_proxies.append({
                    "watch_utc":utc(watch["observed_ms"]),
                    "lead_hours_vs_old_anchor":round((anchor-watch["observed_ms"])/3600000,3),
                    "scenario_0_20_100bps":by_scenario})
            first_watch=watches[0]["observed_ms"] if watches else None
            results={
                "venue":src["venue"],"symbol":src["symbol"],"cohort":src["cohort"],
                "old_research_watch_utc":src["old_watch_utc"],"bars_verified":len(bars),
                "historical_spot_listing_status":"UNVERIFIED_AT_TIME",
                "ticker24":"1440_REAL_1M_QUOTE_SUM_PROXY_NOT_BINANCE_TICKER",
                "quote24_threshold_usdt":100000,
                "replay_start_utc":utc(bars[start_i][0]+INTERVAL_1M),
                "replay_end_utc":utc(bars[end_i-1][0]+INTERVAL_1M),
                "polls":polls,
                "polls_skipped_no_trade":(0 if include_zero_trade_ticks else no_trade_minutes),
                "polls_zero_trade_minute":no_trade_minutes,
                "ticker_zero_trade_policy":("INCLUDE_CLOSED_1M_LAST_PRICE_PROXY" if
                    include_zero_trade_ticks else "SKIP_ZERO_TRADE_POLL"),
                "watch_count":len(watches),"first_watch_utc":utc(first_watch) if first_watch else None,
                "first_watch_lead_hours_vs_old_anchor":(
                    round((anchor-first_watch)/3600000,3) if first_watch else None),
                "d1_setups":len(setups),"d1_queue":d1state,
                "watch_events":[{
                    "utc":utc(x["observed_ms"]), "evidence":json.loads(x["payload"])
                } for x in watches],
                "setup_events":[{
                    "utc":utc(x["observed_ms"]), "evidence":json.loads(x["payload"])
                } for x in setups],
                "historical_execution_verified":False,
                "trade_proxies":trade_proxies,
                "forward_out_of_sample":False,
                "production_trading":"NO_GO",
            }
            return results
        finally:
            db.close()


def summarize(results, skipped):
    cohorts={}
    for r in results:
        d=cohorts.setdefault(r["cohort"],{"n":0,"found_n":0,"setup_n":0,
                 "watch_events":0,"assumed_trades_with_exit":0,"proxy_net_pct_20bps":[]})
        d["n"]+=1
        d["found_n"]+=int(r["watch_count"]>0)
        d["setup_n"]+=int(r["d1_setups"]>0)
        d["watch_events"]+=r["watch_count"]
        for t in r["trade_proxies"]:
            x=t["scenario_0_20_100bps"]["20"]
            if x["status"]=="PRICE_PROXY_ONLY":
                d["assumed_trades_with_exit"]+=1
                d["proxy_net_pct_20bps"].append(x["net_pct"])
    for d in cohorts.values():
        returns=d.pop("proxy_net_pct_20bps")
        d["proxy_net_pct_20bps_median"]=(
            round(statistics.median(returns),4) if returns else None)
        d["proxy_net_pct_20bps_winners"]=sum(x>0 for x in returns)
        d["proxy_net_pct_20bps_losers"]=sum(x<0 for x in returns)
    return {"cases_replayed":len(results),"cases_skipped":len(skipped),
            "cohorts":cohorts,
            "caution":"RETROSPECTIVE_SELECTED_COHORTS_NOT_UNBIASED_UNIVERSE",
            "historical_orderbook":"UNAVAILABLE",
            "profitability_validated":False,
            "production_gate":"NO_GO"}


def run(paths):
    result=[];skipped=[]
    for path in paths:
        try:
            src,bars=load_case(path)
            result.append(replay_case(src,bars))
        except (ValueError, KeyError, TypeError) as exc:
            skipped.append({"file":Path(path).name,
                            "error":type(exc).__name__+":"+str(exc)[:120]})
    return {"study":"STAGE7_ACTUAL_SAME_CODE_V4_RETROSPECTIVE_REPLAY",
            "source":"OFFICIAL_BINANCE_1M_CANDLES_FROZEN_GIT",
            "version":"historical_replay_v1",
            "method":"PRODUCTION_D0_D1_FUNCTIONS_PLUS_TIME_CAUSAL_3M_1M_OHLC_PROXY",
            "summary":summarize(result,skipped),"skipped":skipped,"cases":result}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--pattern",default="monster_v4_replay_1m_*.json")
    parser.add_argument("--output",type=Path)
    args=parser.parse_args()
    report=run(sorted(EVIDENCE.glob(args.pattern)))
    text=json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(text+"\n",encoding="utf-8")
    print(text)
    if not report["summary"]["cases_replayed"]:
        raise SystemExit("NO_VALID_REPLAY_CASES")


if __name__=="__main__":
    main()
