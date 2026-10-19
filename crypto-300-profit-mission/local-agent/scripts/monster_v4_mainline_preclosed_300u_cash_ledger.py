#!/usr/bin/env python3
"""Monster: original269 WATCH / 120 SETUP preclosed source, fully funded 300U ledger.

Historical exposed proxy experiment, not fill, true L2, PIT listing, or trade.
All source checks at each OPEN use only earlier CLOSED full one-minute candles.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import heapq
import json
from pathlib import Path
import statistics

import monster_v4_watch_vs_setup_incremental_value as old

SCHEMA="MONSTER_MAINLINE_ORIGINAL269_120_300U_PRE_ENTRY_CLOSED_1M_CASH_V1"
PREVIOUS_ECON_BLOB="62241ce57d5d275da289aa602bfde32070b0b4f2"
MIN=60_000
LOT=Decimal("30")
START_CASH=Decimal("300")
MAX_POSITIONS=10
HOLD=1440*MIN
RETURN_SLIP=Decimal("0.002")
RETURN_FEE=Decimal("0.001")
BURST_MS=int(datetime(2026,2,6,0,36,tzinfo=timezone.utc).timestamp()*1000)
EXPECTED= {"WATCH":269,"SETUP":120}


def blob_sha(raw):
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()


def original_inputs(ab_file, econ_file):
    raw=econ_file.read_bytes()
    if blob_sha(raw)!=PREVIOUS_ECON_BLOB:
        raise ValueError("MONSTER_300U_PREVIOUS_ECON_IMMUTABLE_BLOB_DRIFT")
    previous=json.loads(raw)
    watches,setups,queue=old.load_events(ab_file)
    if (previous["event_counts"]!=EXPECTED
        or previous["WATCH"]["independent_signals"]["original_total_signal_events"]!=269
        or previous["SETUP"]["independent_signals"]["original_total_signal_events"]!=120
        or previous["G4"]!="UNKNOWN" or previous["G6"]!="NO_GO"):
        raise ValueError("MONSTER_300U_PREVIOUS_UNIVERSE_DRIFT")
    for name,events in (("WATCH",watches),("SETUP",setups)):
        stored=previous[name]["full_original_event_rows_no_lock"]
        if len(stored)!=EXPECTED[name]:
            raise ValueError("MONSTER_300U_OLD_SOURCE_EVENT_COUNT_DRIFT")
        ids={(r["event_id"],r["event_time_ms"],r["symbol"]) for r in stored}
        expected={(r["event_id"],r["observed_ms"],r["symbol"]) for r in events}
        if ids!=expected or len(ids)!=EXPECTED[name]:
            raise ValueError("MONSTER_300U_OLD_ECONOMIC_EVENT_ID_DRIFT")
    return {"WATCH":watches,"SETUP":setups},previous


def candle(bars,tick_ms):
    return old.previous.get_bar(bars,tick_ms)


def finite_positive_open(row):
    try:
        n=Decimal(str(row[1]))
    except (ArithmeticError,TypeError,ValueError):
        return None
    return n if n.is_finite() and n>0 else None


def prior_closed_1m_eligible(bars,open_tick):
    """The whole entry minute is FUTURE at its OPEN; inspect only T-1m."""
    prior=candle(bars,open_tick-MIN)
    current=candle(bars,open_tick)
    if prior is None or current is None:
        return ("CENSORED_ENTRY_PRIOR_CLOSED_OR_OPEN_SOURCE_MISSING",None)
    current_open=finite_positive_open(current)
    if current_open is None:
        return ("CENSORED_ENTRY_OPEN_INVALID",None)
    try:
        q=Decimal(str(prior[5]))
        trades=prior[6]
    except (TypeError,ValueError,ArithmeticError):
        return ("CENSORED_ENTRY_PRIOR_CLOSED_INVALID",None)
    if not q.is_finite() or q<0 or type(trades) is not int or trades<0:
        return ("CENSORED_ENTRY_PRIOR_CLOSED_INVALID",None)
    if q<30 or trades<=0:
        return ("CENSORED_PRIOR_MINUTE_QUOTE_LT_30_OR_NO_TRADES",None)
    return ("ENTRY_PREVIOUS_CLOSED_MINUTE_SOURCE_OK",current_open)


def exit_only_preclosed_minute_source(bars,exit_tick):
    """Future outcome checked at exit; no EXIT minute quote/trades admitted."""
    out=candle(bars,exit_tick)
    if out is None:
        return ("CENSORED_EXIT_OPEN_NOT_ARCHIVED",None)
    px=finite_positive_open(out)
    if px is None:
        return ("CENSORED_EXIT_OPEN_INVALID",None)
    rows=[candle(bars,exit_tick-i*MIN) for i in range(1,6)]
    if any(r is None for r in rows):
        return ("CENSORED_EXIT_PRIOR5_MINUTES_INCOMPLETE",None)
    for r in rows:
        try:
            q=Decimal(str(r[5]))
            t=r[6]
        except (ArithmeticError,ValueError,TypeError):
            return ("CENSORED_EXIT_PRIOR5_INVALID",None)
        if not q.is_finite() or q<=0 or type(t) is not int or t<=0:
            return ("CENSORED_EXIT_PRIOR5_ZERO_VOLUME_OR_INVALID",None)
    if Decimal(str(rows[0][5]))<30:
        return ("CENSORED_EXIT_PRIOR_MINUTE_QUOTE_LT_30",None)
    return ("PRICE_PROXY_ONLY_PREVIOUS_CLOSED_SOURCE",px)


def net_percent(entry,exit,slip):
    return ((exit/entry)*(1-slip)/(1+slip)*(1-RETURN_FEE)**2-1)*Decimal(100)


def realize_proxy(bars,entry_tick,entry_open):
    outcome,price=exit_only_preclosed_minute_source(bars,entry_tick+HOLD)
    if outcome!="PRICE_PROXY_ONLY_PREVIOUS_CLOSED_SOURCE":
        return {"status":outcome,"24h_exit_tick_ms":entry_tick+HOLD,
                "true_exit_executable":False}
    base=net_percent(entry_open,price,RETURN_SLIP)
    pressure=net_percent(entry_open,price,Decimal(".01"))
    return {"status":outcome,"24h_exit_tick_ms":entry_tick+HOLD,
            "entry_1m_open":str(entry_open),"exit_1m_open":str(price),
            "net_return_pct_fee10_slip20_per_side":str(base),
            "net_return_pct_fee10_slip100_per_side":str(pressure),
            "source_times_strictly_preceded_respective_open":True,
            "true_entry_exit_ask_bid_unavailable":True}


def per_event_source(events,bars_by_symbol):
    rows=[]
    for e in events:
        entry=e["observed_ms"]+3*MIN
        b=bars_by_symbol[e["symbol"]]
        source,opening=prior_closed_1m_eligible(b,entry)
        r={"event_id":e["event_id"],"symbol":e["symbol"],
           "event_time_ms":e["observed_ms"],"entry_time_ms":entry,
           "source_entry_status":source,"source_exit":None}
        if source=="ENTRY_PREVIOUS_CLOSED_MINUTE_SOURCE_OK":
            r["source_exit"]=realize_proxy(b,entry,opening)
        rows.append(r)
    if len(rows)!=len(events) or len({x["event_id"] for x in rows})!=len(events):
        raise ValueError("MONSTER_300U_EVENT_ROWS_OR_IDS_DRIFT")
    return rows


def ordered_by_signal_time(events,mode):
    if mode not in ("SYMBOL_ASC","SYMBOL_DESC"):
        raise ValueError("MONSTER_300U_RANKING_UNFROZEN")
    time_groups={}
    for event in events:
        time_groups.setdefault(event["entry_time_ms"],[]).append(event)
    ordered=[]
    for tick in sorted(time_groups):
        ordered.extend(sorted(time_groups[tick],key=lambda e:(e["symbol"],e["event_id"]),
                              reverse=mode=="SYMBOL_DESC"))
    if len(ordered)!=len(events):
        raise ValueError("MONSTER_300U_SORT_LOST_EVENTS")
    return ordered


def cash_simulation(events, *,symbol_order,censored_principal_recovery):
    if censored_principal_recovery not in (0,100):
        raise ValueError("MONSTER_300U_CENSORED_RECOVERY_UNFROZEN")
    ordered=ordered_by_signal_time(events,symbol_order)
    cash=START_CASH
    heap=[]
    active_symbols=set()
    spent=Decimal(0)
    returned=Decimal(0)
    counts=Counter()
    max_used=0
    peak_book=START_CASH
    trough_book=START_CASH
    max_book_decline=Decimal(0)
    results=[]
    settlements=[]
    sequencer=0

    def mark_book():
        nonlocal peak_book,trough_book,max_book_decline
        nav=cash+LOT*len(heap)
        if nav>peak_book:peak_book=nav
        if nav<trough_book:trough_book=nav
        if peak_book-nav>max_book_decline:max_book_decline=peak_book-nav

    def settle_until(moment):
        nonlocal cash,returned
        while heap and heap[0][0]<=moment:
            t,number,sym,eid,redemption,source_status=heapq.heappop(heap)
            active_symbols.remove(sym)
            cash+=redemption
            returned+=redemption
            counts["settled_positions"]+=1
            settlements.append({"event_id":eid,"symbol":sym,"settle_time_ms":t,
                                "assumed_payback_usdt":str(redemption),
                                "source_outcome_status":source_status,
                                "assumed_only":True})
            mark_book()

    for e in ordered:
        entry=e["entry_time_ms"]
        settle_until(entry)
        if e["source_entry_status"]!="ENTRY_PREVIOUS_CLOSED_MINUTE_SOURCE_OK":
            status=e["source_entry_status"]
        elif e["symbol"] in active_symbols:
            status="SKIP_SAME_SYMBOL_ALREADY_FUNDED"
        elif len(heap)>=MAX_POSITIONS:
            status="SKIP_ALL_10_POSITIONS_BUSY"
        elif cash<LOT:
            status="SKIP_CASH_LT_30_USDT"
        else:
            status="SELECT_30_USDT"
            cash-=LOT
            spent+=LOT
            sequencer+=1
            exit_data=e["source_exit"]
            if exit_data["status"]=="PRICE_PROXY_ONLY_PREVIOUS_CLOSED_SOURCE":
                ret=Decimal(exit_data["net_return_pct_fee10_slip20_per_side"])
                redemption=LOT*(1+ret/Decimal(100))
                counts["selected_source_evaluable"]+=1
                counts["selected_24h_proxy_positive"]+=int(ret>0)
                counts["selected_24h_proxy_negative"]+=int(ret<0)
            else:
                redemption=LOT*Decimal(censored_principal_recovery)/Decimal(100)
                counts["selected_future_censored_proxy"]+=1
            if redemption<0 or cash<0:
                raise ValueError("MONSTER_300U_NEGATIVE_CASH_OR_REDEMPTION")
            heapq.heappush(heap,(entry+HOLD,sequencer,e["symbol"],e["event_id"],
                                 redemption,exit_data["status"]))
            active_symbols.add(e["symbol"])
            max_used=max(max_used,len(heap))
            mark_book()
        counts[status]+=1
        results.append({"event_id":e["event_id"],"symbol":e["symbol"],
                        "event_time_ms":e["event_time_ms"],
                        "entry_time_ms":entry,
                        "entry_source_status":e["source_entry_status"],
                        "selection_status":status,
                        "is_maximum_watch_burst":e["event_time_ms"]==BURST_MS,
                        "price_proxy_exit_status":e["source_exit"]["status"] if e["source_exit"] else None,
                        "executable_trade":"UNVERIFIED"})
    settle_until(10**30)
    if (active_symbols or heap or len(results)!=len(events)
        or abs(cash-(START_CASH-spent+returned))>Decimal("0.00000001")):
        raise ValueError("MONSTER_300U_CASH_CONSERVATION_OR_EVENT_COUNT_DRIFT")
    selected=[r for r in results if r["selection_status"]=="SELECT_30_USDT"]
    burst=[r for r in results if r["is_maximum_watch_burst"]]
    summary={
        "initial_cash_usdt":str(START_CASH),
        "max_simultaneous_30usdt_lots":MAX_POSITIONS,
        "signal_tie_selection":symbol_order,
        "censored_at_24h_principal_repayment_scenario_percent":censored_principal_recovery,
        "unverified_recovery_not_a_bound_on_true_execution":True,
        "total_signals":len(events),
        "selected_count":len(selected),
        "selected_source_evaluable":counts["selected_source_evaluable"],
        "selected_future_censored_proxy":counts["selected_future_censored_proxy"],
        "selected_price_proxy_winners":counts["selected_24h_proxy_positive"],
        "selected_price_proxy_losers":counts["selected_24h_proxy_negative"],
        "skipped_10_slots":counts["SKIP_ALL_10_POSITIONS_BUSY"],
        "skipped_cash":counts["SKIP_CASH_LT_30_USDT"],
        "skipped_same_symbol":counts["SKIP_SAME_SYMBOL_ALREADY_FUNDED"],
        "entry_source_rejected":len(events)-len(selected)-counts["SKIP_ALL_10_POSITIONS_BUSY"]-
                                counts["SKIP_CASH_LT_30_USDT"]-counts["SKIP_SAME_SYMBOL_ALREADY_FUNDED"],
        "maximum_concurrent_lots":max_used,
        "gross_assumed_entry_spend_usdt":str(spent),
        "gross_assumed_redemptions_usdt":str(returned),
        "final_cash_after_all_assumed_24h_settlements_usdt":str(cash),
        "assumed_cash_delta_usdt":str(cash-START_CASH),
        "minimum_cash_book_nav_usdt_not_mark_to_market":str(trough_book),
        "maximum_cash_book_drawdown_usdt_not_market_drawdown":str(max_book_decline),
        "largest_98_watch_burst":{
            "watch_observed_at_utc":"2026-02-06T00:36:00Z",
            "signals":len(burst),
            "selected_count":sum(x["selection_status"]=="SELECT_30_USDT" for x in burst),
            "selected_symbols":[x["symbol"] for x in burst if x["selection_status"]=="SELECT_30_USDT"],
            "skip_10_slots":sum(x["selection_status"]=="SKIP_ALL_10_POSITIONS_BUSY" for x in burst),
            "skip_insufficient_cash":sum(x["selection_status"]=="SKIP_CASH_LT_30_USDT" for x in burst),
            "entry_source_rejected":sum(x["selection_status"].startswith("CENSORED_") for x in burst),
            "selected_known_24h_price_proxy":sum(x["selection_status"]=="SELECT_30_USDT" and
                                x["price_proxy_exit_status"]=="PRICE_PROXY_ONLY_PREVIOUS_CLOSED_SOURCE"
                                for x in burst),
        },
        "capital_is_hypothetical_and_real_fill_unknown":True
    }
    if sum(v for k,v in counts.items() if k.startswith("SELECT_") or k.startswith("SKIP_")
           or k.startswith("CENSORED_"))!=len(events):
        raise ValueError("MONSTER_300U_EVENT_STATUS_COUNTER_INCOMPLETE")
    return {"summary":summary,"event_decisions":results,"assumed_settlements":settlements}


def audit(ab,econ,archives):
    eventgroups,prior=original_inputs(ab,econ)
    symbols={r["symbol"] for part in eventgroups.values() for r in part}
    minute_sources,shaproofs=old.source_bars(archives,symbols)
    report={
        "schema":SCHEMA,
        "old_269_120_economic_git_blob":PREVIOUS_ECON_BLOB,
        "original_stage162_sha256":old.EVENT_SHA,
        "original_source_proof_28_shards":shaproofs,
        "eligible_signal_groups":EXPECTED,
        "causal_minute_source_definition":"T_MINUS_1M_CLOSED_FOR_ENTRY_AND_EXIT_T_MINUS_5_TO_T_MINUS_1_CLOSED",
        "entry_rule":"SETUP_OR_WATCH_T_PLUS_3_MIN_1M_OPEN_PRICE_PROXY",
        "exit_rule":"ENTRY_PLUS_1440_MIN_1M_OPEN_PRICE_PROXY",
        "fee_bps_each_side_hypothetical":10,
        "slippage_bps_each_side_hypothetical":20,
        "stress_slippage_bps_each_side_hypothetical":100,
        "not_price_execution_orderbook_proven":True
    }
    for name,events in eventgroups.items():
        sources=per_event_source(events,minute_sources)
        scenarios={}
        for order in ("SYMBOL_ASC","SYMBOL_DESC"):
            for repayment in (0,100):
                key=f"{order}_CENSORED_REPAY_{repayment}PCT"
                scenarios[key]=cash_simulation(sources,symbol_order=order,
                                               censored_principal_recovery=repayment)
                if scenarios[key]["summary"]["total_signals"]!=EXPECTED[name]:
                    raise ValueError("MONSTER_300U_UNIVERSE_DENOMINATOR_MISMATCH")
        status=Counter(x["source_exit"]["status"] for x in sources if x["source_exit"])
        report[name]={
            "historical_signals_total":len(events),
            "at_entry_preclosed_source_admissible":sum(x["source_exit"] is not None for x in sources),
            "price_proxy_outcome_status_for_preclosed_entries":dict(sorted(status.items())),
            "all_original_events_new_preclosed_source":sources,
            "funded_300u_scenarios":scenarios
        }
    for key in ("WATCH","SETUP"):
        if len(report[key]["all_original_events_new_preclosed_source"])!=EXPECTED[key]:
            raise ValueError("MONSTER_300U_MISSING_FROZEN_EVENTS")
    report.update({
        "research_exposed_2026_feb_445_of_758_313_censored":True,
        "independent_oos":False,"historical_l2_ask_bid":"UNAVAILABLE",
        "real_executable_net_profit":"UNVERIFIED",
        "G4":"UNKNOWN","G6":"NO_GO",
        "NO_MERGE":True,"NO_DEPLOY":True,"NO_GMAIL":True,"NO_TRADE":True})
    return report


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--stage162-full",required=True,type=Path)
    p.add_argument("--old-watch-setup-economics",required=True,type=Path)
    p.add_argument("--original28-source-dir",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    args=p.parse_args()
    if args.out.exists() or args.out.is_symlink():
        raise ValueError("MONSTER_300U_OUTPUT_EXISTS_REFUSE_OVERWRITE")
    j=audit(args.stage162_full,args.old_watch_setup_economics,args.original28_source_dir)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    with args.out.open("x",encoding="utf-8") as dest:
        json.dump(j,dest,sort_keys=True,ensure_ascii=False,indent=2)
        dest.write("\n")
    summ={arm:{k:v["summary"] for k,v in j[arm]["funded_300u_scenarios"].items()}
          for arm in ("WATCH","SETUP")}
    print("MONSTER_300U_FINITE_CASH_PRE_CLOSED_SOURCE_NO_FILL",
          json.dumps({"cohort":summ,"G4":j["G4"],"G6":j["G6"]},sort_keys=True))


if __name__=="__main__":
    main()
