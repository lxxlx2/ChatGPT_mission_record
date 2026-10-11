#!/usr/bin/env python3
"""Stage27: original Stage26 WATCH arrival stream, shared D1 capacity and cash ledger.

READ-ONLY research. Exactly the 36 SHA-gated Stage26 original archive ZIPs.
No strategy changes, no GT winner filtering and no real execution claims.

Shared queue simulation is deliberately OPTIMISTIC: one evaluation completes
each candidate. Real D1 can require repeat polls, retries and shared API latency.
Full/fractional USD ledger assumes historical 24h price proxy can execute;
unknown censored exits are reported with 0/100% hypothetical recovery bounds.
"""
import argparse
import collections
import heapq
import json
import math
import statistics
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

try:
    import monster_v4_stage26_aggregate as previous
except ImportError:
    from scripts import monster_v4_stage26_aggregate as previous

EVIDENCE=previous.EVIDENCE
PREREG=EVIDENCE/"monster_stage27_shared_queue_cash_budget_prereg_20261011.json"
SCHEMA="MONSTER_STAGE27_SHARED_D1_FIRST_EVALUATION_AND_FUNDED_CASH_V1"

def frozen():
    d=json.loads(PREREG.read_text(encoding="utf-8"))
    if d.get("schema")!="MONSTER_STAGE27_LOCKED_HISTORICAL_SHARED_D1_CAPACITY_AND_CASH_ACCOUNTING_V1":
        raise ValueError("STAGE27_FROZEN_SCHEMA_CHANGED")
    if (d["all_watches"],d["all_complete_symbol_dates"])!=(1132,2719):
        raise ValueError("STAGE27_ORIGINAL_WATCH_DENOMINATOR_CHANGED")
    c=d["shared_queue"]
    if (c["process_queue_limit_per_poll"],c["poll_spacing_minutes"],c["ttl_minutes"])!=(8,3,15):
        raise ValueError("STAGE27_D1_CAPACITY_CHANGED")
    a=d["ledger"]
    if (a["starting_balances"],a["max_positions"],a["full_lot_USDT"],a["slippage_bps_side"],a["censored_recovery_bounds"])!=([30,300],[1,10],30,[20,100],[0,100]):
        raise ValueError("STAGE27_FUNDED_LEDGER_CHANGED")
    return d

def original_cases(files):
    cfg=frozen()
    record=json.loads(previous.PROOF.read_text(encoding="utf-8"))
    originals={(a["date"],a["shard"]):a for a in record["artifacts"]}
    if len(files)!=36 or len(originals)!=36:
        raise ValueError("STAGE27_REQUIRE_ALL_36_ORIGINALS")
    seen=set()
    items=[]
    for path in files:
        with zipfile.ZipFile(path) as z:
            names=z.namelist()
        if len(names)!=1 or not names[0].startswith("monster_stage26_") or not names[0].endswith(".json"):
            raise ValueError("STAGE27_UNEXPECTED_ZIP_MEMBER")
        date,shard=(names[0].removeprefix("monster_stage26_")
                         .removesuffix(".json").split("_shard"))
        key=(date,int(shard))
        if key not in originals or key in seen:
            raise ValueError("STAGE27_DUPLICATE_OR_UNKNOWN_SOURCE")
        seen.add(key)
        data=previous.load_zip(path,originals[key])
        items.extend(data["cases"])
    if len(items)!=4548 or len(seen)!=36:
        raise ValueError("STAGE27_NOT_FULL_758_X_SIX")
    counts=collections.Counter(x["date"] for x in items)
    if any(v!=758 for v in counts.values()) or len(counts)!=6:
        raise ValueError("STAGE27_DATE_COHORT_MISMATCH")
    valid=[x for x in items if x["status"]=="COMPLETE_168H_CONTINUOUS_V4"]
    watches=sum(len(x["continuous"]["watch_utcs"]) for x in valid)
    if len(valid)!=cfg["all_complete_symbol_dates"] or watches!=cfg["all_watches"]:
        raise ValueError("STAGE27_SOURCE_DENOMINATORS_DO_NOT_MATCH")
    return valid

def arrivals_for_day(rows,day):
    records=[]
    for r in rows:
        if r["date"]!=day:continue
        for t in r["continuous"]["watch_utcs"]:
            records.append((previous.utc(t),r["symbol"]))
    records.sort(key=lambda r:(r[0],r[1]))
    if len(records)!=len(set(records)):
        raise ValueError("STAGE27_DUPLICATE_WATCH_TIMESTAMP_SYMBOL")
    return records

def shared_first_eval_queue(arrivals,limit=8,poll_mins=3,ttl_mins=15):
    """Max eight *first* evaluations/poll; actual D1 recurrent work is worse."""
    if not arrivals:
        return {"arrivals":0,"first_evaluated_before_deadline":0,
                "unserved_expired":0,"max_backlog_after_arrivals":0,
                "max_wait_minutes":None,"median_first_wait_minutes":None,
                "first_wait_gt_6min":0,"per_poll_peak":0,"most_crowded_poll_utc":None}
    queue=collections.deque()
    tick=arrivals[0][0]
    n=0;expired=0;first=[];peak=0;poll_peak=0;most_crowded=None
    entered=collections.Counter()
    last=arrivals[-1][0]+timedelta(minutes=ttl_mins+poll_mins)
    idx=0
    while tick<=last:
        at_tick=[]
        while idx<len(arrivals) and arrivals[idx][0]<=tick:
            watch,symbol=arrivals[idx]
            if (tick-watch).total_seconds()>0:
                raise ValueError("STAGE27_WATCH_TIMING_NOT_THREE_MIN_GRID")
            queue.append((watch,symbol))
            at_tick.append(symbol)
            idx+=1;n+=1
        if len(at_tick)>poll_peak:
            poll_peak=len(at_tick);most_crowded=tick.isoformat()
        peak=max(peak,len(queue))
        while queue and (tick-queue[0][0]).total_seconds()>ttl_mins*60:
            queue.popleft();expired+=1
        for _ in range(limit):
            if not queue:break
            when,symbol=queue.popleft()
            if tick>when+timedelta(minutes=ttl_mins):
                expired+=1
            else:
                first.append((tick-when).total_seconds()/60)
        if idx==len(arrivals) and not queue:
            break
        tick+=timedelta(minutes=poll_mins)
    if n!=len(arrivals) or n!=expired+len(first):
        raise ValueError("STAGE27_D1_FIRST_EVAL_ACCOUNTING_BROKEN")
    return {"arrivals":n,"first_evaluated_before_deadline":len(first),
      "unserved_expired":expired,"max_backlog_after_arrivals":peak,
      "max_wait_minutes":max(first) if first else None,
      "median_first_wait_minutes":round(statistics.median(first),6) if first else None,
      "first_wait_gt_6min":sum(v>6 for v in first),
      "per_poll_peak":poll_peak,"most_crowded_poll_utc":most_crowded,
      "one_eval_model_optimistic":True}

def candidate_entries(rows,slippage=20):
    name="proxy_"+str(slippage)+"bps"
    source=[]
    skipped_same=0
    for r in rows:
        for t in r["continuous"]["trade_proxies"]:
            p=t[name]
            if p is None or p.get("status")=="SKIP_SAME_SYMBOL_24H_CAPITAL_OCCUPIED":
                skipped_same+=1
                continue
            if p["status"]!="PRICE_PROXY_ONLY" and not p["status"].startswith("CENSORED_"):
                raise ValueError("STAGE27_BAD_TRADE_PROXY_STATUS")
            source.append({"date":r["date"],"symbol":r["symbol"],
                "watch_utc":t["watch_utc"],"proxy_status":p["status"],
                "net_pct":p.get("net_pct")})
    source.sort(key=lambda x:(x["watch_utc"],x["date"],x["symbol"]))
    return source,skipped_same

def money_ledger(trades,starting,slots,lot_policy,slippage,censored_recovery):
    if starting not in (30,300) or slots not in (1,10):
        raise ValueError("STAGE27_UNFROZEN_ACCOUNT")
    if lot_policy not in ("FIXED_30U","UP_TO_30U_FRACTIONAL"):
        raise ValueError("STAGE27_UNFROZEN_LOT_POLICY")
    if censored_recovery not in (0,100) or slippage not in (20,100):
        raise ValueError("STAGE27_UNFROZEN_STRESS")
    cash=float(starting)
    heap=[];ordnum=0
    count=collections.Counter()
    realized=0.0;max_nav=float(starting);min_nav=float(starting)
    paid=0.0;received=0.0;gross_entry=0.0
    selected=[]
    def nav():
        return cash+sum(item[2] for item in heap)
    def mark():
        nonlocal max_nav,min_nav
        current=nav()
        max_nav=max(max_nav,current)
        min_nav=min(min_nav,current)
    def settle_until(ts):
        nonlocal cash,received,realized
        while heap and heap[0][0]<=ts:
            _,_,entry,payback,known=heapq.heappop(heap)
            cash+=payback
            received+=payback
            realized+=payback-entry
            count["settled"]+=1
            if not known:count["censored_settled"]+=1
            mark()
    for t in trades:
        entry_time=previous.utc(t["watch_utc"])+timedelta(minutes=3)
        settle_until(entry_time)
        if len(heap)>=slots:
            count["skip_slots_busy"]+=1
            continue
        if lot_policy=="FIXED_30U":
            if cash+1e-9<30:
                count["skip_insufficient_cash_30u"]+=1
                continue
            amount=30.0
        else:
            if cash+1e-9<1:
                count["skip_insufficient_cash_1u"]+=1
                continue
            amount=min(30.0,cash)
        cash-=amount
        if cash < -1e-8:
            raise ValueError("STAGE27_CASH_OVERDRAFT")
        if cash<0:cash=0.0
        gross_entry+=amount
        p=t["net_pct"]
        known=t["proxy_status"]=="PRICE_PROXY_ONLY"
        if known:
            if p is None or not isinstance(p,(int,float)) or p < -100:
                raise ValueError("STAGE27_BAD_OR_UNKNOWN_ACTUAL_PROXY_RETURN")
            payoff=amount*(1+p/100.0)
            count["selected_evaluable"]+=1
            count["winning"]+=int(p>0)
            count["losing"]+=int(p<0)
        else:
            payoff=amount*censored_recovery/100.0
            count["selected_censored"]+=1
        ordnum+=1
        heapq.heappush(heap,(entry_time+timedelta(hours=24),ordnum,amount,payoff,known))
        count["selected"]+=1
        selected.append({"date":t["date"],"symbol":t["symbol"],
                "watch_utc":t["watch_utc"],"entry_USDT":round(amount,6),
                "source_status":t["proxy_status"],
                "assumed_exit_USDT":round(payoff,6)})
        mark()
    settle_until(datetime.max.replace(tzinfo=timezone.utc))
    if heap or cash<0 or abs((cash-starting)-realized)>1e-6:
        raise ValueError("STAGE27_LEDGER_NONCONSERVATION")
    return {"initial_cash_USDT":starting,"max_positions":slots,
       "lot_policy":lot_policy,"slippage_bps_side":slippage,
       "censored_principal_recovery_pct_UNVERIFIED":censored_recovery,
       "final_cash_USDT":round(cash,6),
       "realized_proxy_profit_USDT":round(realized,6),
       "lowest_realized_book_NAV_USDT":round(min_nav,6),
       "peak_realized_book_NAV_USDT":round(max_nav,6),
       "gross_lot_entries_USDT":round(gross_entry,6),
       "gross_settlements_USDT":round(received,6),
       "cash_overdrawn":False,
       "counts":dict(count),
       "selected_cases":selected,
       "not_real_wallet_execution":True}

def study(rows):
    cfg=frozen()
    dates=sorted(set(x["date"] for x in rows))
    que={}
    peak=[]
    for day in dates:
        arrivals=arrivals_for_day(rows,day)
        q=shared_first_eval_queue(arrivals)
        que[day]=q
        peak.append((q["per_poll_peak"],day,q["most_crowded_poll_utc"]))
    all_watches=sum(q["arrivals"] for q in que.values())
    if all_watches!=cfg["all_watches"]:
        raise ValueError("STAGE27_QUEUE_EVENT_DENOMINATOR_BAD")
    original_candidate20,skipped=candidate_entries(rows,20)
    original_candidate100,skipped100=candidate_entries(rows,100)
    if (len(original_candidate20),skipped)!=(806,326) or len(original_candidate100)!=len(original_candidate20):
        raise ValueError("STAGE27_EXPECTED_ORIGINAL_NONOVERLAP_MISMATCH")
    if [(v["date"],v["symbol"],v["watch_utc"]) for v in original_candidate20]!=[
           (v["date"],v["symbol"],v["watch_utc"]) for v in original_candidate100]:
        raise ValueError("STAGE27_STRESS_20_100_DIFFERENT_SIGNAL_COHORTS")
    scenarios={}
    for initial,slots in ((30,1),(300,10)):
        for lot in ("FIXED_30U","UP_TO_30U_FRACTIONAL"):
            for slippage,trades in ((20,original_candidate20),(100,original_candidate100)):
                for recovery in (100,0):
                    name=f"{initial}USDT_{slots}SLOT_{lot}_{slippage}BPS_{recovery}PCT_CENSORED_RECOVERY"
                    scenarios[name]=money_ledger(trades,initial,slots,lot,slippage,recovery)
    qsum={
      "arrivals":all_watches,
      "optimistic_first_evaluations_within_15m":sum(v["first_evaluated_before_deadline"] for v in que.values()),
      "unserved_expired_even_under_optimistic_one_evaluation":sum(v["unserved_expired"] for v in que.values()),
      "single_3m_peak_poll_watches":max(peak)[0],
      "single_3m_peak_poll":sorted(peak,reverse=True)[0][2],
      "by_date":que}
    return {"schema":SCHEMA,"status":"RESEARCH_SHA_VERIFIED_ORIGINALS_ONLY",
       "historical_dates_exposed":True,
       "source_full_valid_168h_symbol_date":len(rows),
       "all_original_WATCH_event_count":all_watches,
       "source_original_36_artifact_sha_rechecked":True,
       "shared_D1_queue_capacity_upper_bound":qsum,
       "original_nonoverlapping_per_symbol_watch_candidates":len(original_candidate20),
       "original_per_symbol_24h_overlap_dropped":skipped,
       "funded_cash_accounting":scenarios,
       "censored_exit_real_liquidation":"UNKNOWN_TWO_SCENARIO_BOUND_ONLY",
       "live_global_D1_queue_exact_replay":"NOT_DONE_APPROX_FIRST_EVAL_UPPER_BOUND",
       "independent_other_ai_review":"NOT_DONE","mac_deployment":"NO_GO",
       "actual_Gmail":"OFF","trading":"NO_GO","frank":"UNCHANGED"}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--artifact-zips",required=True,nargs=36,type=Path)
    p.add_argument("--output",required=True,type=Path)
    a=p.parse_args()
    result=study(original_cases(a.artifact_zips))
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    show=result["shared_D1_queue_capacity_upper_bound"]
    selected={k:{j:v for j,v in d.items() if j!="selected_cases"}
       for k,d in result["funded_cash_accounting"].items()
       if "20BPS" in k and "100PCT_CENSORED_RECOVERY" in k}
    print("STAGE27_SUMMARY_JSON "+json.dumps({"queue":show,
      "cash_funded_opt_20bps":selected},sort_keys=True),flush=True)

if __name__=="__main__":
    main()
