#!/usr/bin/env python3
"""Monster Stage68: immutable, causal D0 WATCH + P1 research urgency engine.

Mechanism-only exposed 3x900 replay, not holdout / predictive ranking approval.
No automatic trading, order sizing, Gmail, Frank edits or production deployment.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

BASE=Path(__file__).resolve().parents[2]/"monster"
E=BASE/"evidence"
DATA=E/"monster_stage66_full2700_originalV4_D0_and_P1v03_source_SHA.jsonl"
FATES=E/"monster_stage66_firstD0_first5_full2700_vs_oldP1_urgent_fates.jsonl"
SUMMARY=E/"monster_stage66_new3_full2700_global_cap5_firstD0_vs_P1v03_summary.json"
PROTOCOL=BASE/"MONSTER_STAGE68_P2_EARLY_WATCH_P1_HALF_DAY_CAP_PREDECLARED_DESIGN_20261012.md"
PIN={
  DATA.name:"9eb19c22ae8d34d030ccabd7176c3cd4d2e2e3f8",
  FATES.name:"9b4b64f133853f0effc7e47d8b1b8c35cb6d5d81",
  SUMMARY.name:"5305f0cbe482691a01575a6bb368dbe8422035e8",
  PROTOCOL.name:"7d3d0b90e2987df6fec02bdf0dc65d7c130f5301",
}
SCHEMA="MONSTER_STAGE68_P2_IMMEDIATE_WATCH_P1_FIRST_HALF2_DAY5_CAUSAL_LEDGER_V1"
VALID="COMPLETE_REAL_USDM_1M_SHA_CAUSAL_V4"
DAY=24*60
HALF=12*60
DATES=("2025-03-30","2025-06-30","2025-11-27")
DEC=Decimal

def gitblob(p):
    raw=p.read_bytes()
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()

def stamp(s):
    t=datetime.fromisoformat(s.replace("Z","+00:00"))
    if t.utcoffset().total_seconds()!=0 or t.second or t.microsecond:
        raise ValueError("STAGE68_TIME_MUST_BE_UTC_MINUTE")
    return int(t.timestamp()//60)

def relative_day(date,t):
    tick=stamp(t)-stamp(date+"T06:00:00Z")
    if not 0<=tick<7*DAY or tick%3:
        raise ValueError("STAGE68_ORIGINAL_UTC06_7DAY_3MIN_CLOCK_INVALID")
    return tick//DAY, tick%DAY

def load():
    for p in (DATA,FATES,SUMMARY,PROTOCOL):
        if gitblob(p)!=PIN[p.name]:
            raise ValueError("STAGE68_IMMUTABLE_EXPOSED_OR_PRIOR_RULE_CHANGED "+p.name)
    rows=[json.loads(t) for t in DATA.read_text(encoding="utf-8").splitlines() if t]
    old=[json.loads(t) for t in FATES.read_text(encoding="utf-8").splitlines() if t]
    meta=json.loads(SUMMARY.read_text(encoding="utf-8"))
    if len(rows)!=2700 or len(old)!=252:
        raise ValueError("STAGE68_2700_ORIGINAL2700_AND252_FATES_INCOMPLETE")
    if len({(r["date"],r["symbol"]) for r in rows})!=2700:
        raise ValueError("STAGE68_DUPLICATE_MARKET_COIN")
    if (meta["original_1m_and_1h_source_valid"],
        meta["new_first5_candidate_count"],
        meta["old_P1v03_candidate_count"])!=(1497,196,56):
        raise ValueError("STAGE68_PRIOR_ORIGINAL_WATCH_COUNTS_CHANGED")
    for d in DATES:
        if sum(r["date"]==d for r in rows)!=900:
            raise ValueError("STAGE68_MISSING_ORIGINAL_ARCHIVED900")
    return rows,old,meta

def validated_events(rows):
    events=[];counts=collections.Counter()
    for r in rows:
        key=(r["date"],r["symbol"])
        if r["minute_source_status"]!=VALID:
            if r.get("original_D0_first_UTC") or r.get("P1v03_original_unbudgeted_candidate"):
                raise ValueError("STAGE68_CENSORED_CANNOT_BECOME_KNOWN_NEGATIVE")
            counts["SOURCE_CENSORED"]+=1
            continue
        counts["SOURCE_VALID"]+=1
        d0=r["original_D0_first_UTC"]
        p1=r["P1v03_original_unbudgeted_candidate"]
        if (d0 is None)!=(not r["original_D0_all_WATCH_UTC"]):
            raise ValueError("STAGE68_ORIGINAL_V4_WATCH_LIST_MISMATCH")
        if p1 and not d0:
            raise ValueError("STAGE68_P1_MUST_FOLLOW_REAL_D0")
        if d0:
            if d0!=r["original_D0_all_WATCH_UTC"][0]:
                raise ValueError("STAGE68_ORIGINAL_FIRST_WATCH_CLOCK_CHANGED")
            relative_day(r["date"],d0)
            quote=r["D0_first_quote15_USDM_asof"]
            if quote is None or DEC(quote)<0:
                raise ValueError("STAGE68_WATCH_HAS_NO_CLOSED_MINUTE_SOURCE")
            counts["D0"]+=1
            events.append({
                "date":r["date"],"symbol":r["symbol"],"at_UTC":d0,
                "kind":"FIRST_D0_WATCH","asof_quote15":quote,
                "future_GT2x_EVALUATION_ONLY":bool(r["hourly_gt2x_EVALUATION_ONLY"]),
                "first_2x_HIGH_EVALUATION_ONLY":r["original_GT2x_first_real_1m_HIGH_UTC"],
            })
        if p1:
            if p1["first_D0_watch_UTC"]!=d0 or stamp(p1["at_UTC"])<stamp(d0):
                raise ValueError("STAGE68_P1_QUALIFIED_BEFORE_FIRST_WATCH")
            relative_day(r["date"],p1["at_UTC"])
            if not p1["publisher_verified_asof_no_future_source"]:
                raise ValueError("STAGE68_P1_SOURCE_USES_FUTURE")
            value=p1["features"]["quote15_USDT"]
            if value is None or DEC(value)<0:
                raise ValueError("STAGE68_P1_ASOF_QUOTE15_MISSING")
            counts["P1"]+=1
            events.append({
                "date":r["date"],"symbol":r["symbol"],"at_UTC":p1["at_UTC"],
                "kind":"P1_FIRST_ASOF_ELIGIBLE","asof_quote15":value,
                "future_GT2x_EVALUATION_ONLY":bool(r["hourly_gt2x_EVALUATION_ONLY"]),
                "first_2x_HIGH_EVALUATION_ONLY":r["original_GT2x_first_real_1m_HIGH_UTC"],
            })
    if (counts["SOURCE_VALID"],counts["SOURCE_CENSORED"],counts["D0"],counts["P1"])!=(1497,1203,196,56):
        raise ValueError("STAGE68_ORIGINAL_ALL_MARKET_CONSISTENCY_FAILED "+str(dict(counts)))
    return events,counts

def simulate(events):
    """Pure prefix-causal; output stable on unordered input with same-tick quote tie."""
    if len({(e["date"],e["symbol"],e["kind"]) for e in events})!=len(events):
        raise ValueError("STAGE68_DUPLICATE_WATCH_OR_UPGRADE")
    ordered=sorted(events,key=lambda e:(
        stamp(e["at_UTC"]), 0 if e["kind"]=="FIRST_D0_WATCH" else 1,
        -DEC(e["asof_quote15"]),e["symbol"]))
    state={}
    counts=collections.Counter()
    firsthalf=collections.Counter()
    ledger=[]
    for ev in ordered:
        date,symbol,kind,at=ev["date"],ev["symbol"],ev["kind"],ev["at_UTC"]
        if kind not in ("FIRST_D0_WATCH","P1_FIRST_ASOF_ELIGIBLE"):
            raise ValueError("STAGE68_UNKNOWN_EVENT_KIND")
        day,within=relative_day(date,at)
        key=(date,symbol)
        slot=(date,day)
        # Counts only positive decisions, and decisions never go backwards.
        if kind=="FIRST_D0_WATCH":
            if key in state:
                raise ValueError("STAGE68_REPEATED_OR_OUT_OF_ORDER_WATCH")
            state[key]={"stage":"WATCH","watch_UTC":at,"p1_UTC":None,"urgent":False}
            phase="WATCH"
            decision="D0_WATCH_UNCAPPED_NO_EMAIL"
        else:
            if key not in state or state[key]["p1_UTC"] is not None or stamp(at)<stamp(state[key]["watch_UTC"]):
                raise ValueError("STAGE68_P1_WITHOUT_UNIQUE_CAUSAL_FIRST_WATCH")
            if within<HALF:
                reserve_open=firsthalf[slot]<2 and counts[slot]<5
            else:
                reserve_open=counts[slot]<5
            state[key]["p1_UTC"]=at
            state[key]["urgent"]=reserve_open
            state[key]["stage"]="URGENT_RESEARCH" if reserve_open else "CAP_DEFERRED_RESEARCH"
            if reserve_open:
                counts[slot]+=1
                if within<HALF:firsthalf[slot]+=1
                decision="RESEARCH_URGENT_P2_CAP_CONSUMED"
            else:
                decision="P1_READY_BUT_CAP_RESERVED_OR_FULL_WATCH_RETAINED"
            phase=state[key]["stage"]
        if counts[slot]>5 or firsthalf[slot]>2:
            raise ValueError("STAGE68_RESEARCH_BUDGET_CAP_EXCEEDED")
        ledger.append({
            "event_id":"monster68:"+date+":"+symbol+":"+kind,
            "date":date,"symbol":symbol,"at_UTC":at,
            "kind":kind,
            "state_after":phase,
            "budget_action":decision,
            "slot_UTC06_day":day,
            "slot_half":"FIRST_12H" if within<HALF else "LAST_12H",
            "source_asof_quote15_USDM":ev["asof_quote15"],
            "source_venue":"BINANCE_USDM_FUTURES_HISTORICAL_ONLY",
            "NO_HISTORIC_EXECUTABLE_SPOT_PROOF":True,
            "ORDER_NOTIONAL_UNSPECIFIED":True,
            "NO_GMAIL_NO_TRADE":True,
        })
    return ledger,state,counts,firsthalf

def compare(original,old_fates,events,ledger,state,counts,firsthalf):
    prev=[x for x in old_fates if x["allocation"]=="OLD_P1V03"]
    previous={(x["date"],x["symbol"]):x for x in prev}
    orig_p1={(e["date"],e["symbol"]):e for e in events if e["kind"]=="P1_FIRST_ASOF_ELIGIBLE"}
    if len(previous)!=56 or set(previous)!=set(orig_p1):
        raise ValueError("STAGE68_OLD_P1_ASOF_CANDIDATE_SET_DIFFERENT")
    for key,e in orig_p1.items():
        old=previous[key]
        if e["at_UTC"]!=old["time_UTC"] or DEC(e["asof_quote15"])!=DEC(old["asof_quote15_USDM_for_same_tick_ranking"]):
            raise ValueError("STAGE68_ORIGINAL_P1_ASOF_TIME_QUOTE_DRIFT")
    selected={(k[0],k[1]) for k,s in state.items() if s["urgent"]}
    if len(selected)!=sum(counts.values()):
        raise ValueError("STAGE68_RESELECTED_DUPLICATED_OR_URGENT_STATUS_WRONG")
    if len(ledger)!=252 or sum(e["kind"]=="FIRST_D0_WATCH" for e in ledger)!=196:
        raise ValueError("STAGE68_D0_WATCH_MISSING")
    if sum(e["kind"]=="P1_FIRST_ASOF_ELIGIBLE" for e in ledger)!=56:
        raise ValueError("STAGE68_P1_EVENT_MISSING")
    if any(v>2 for v in firsthalf.values()) or any(v>5 for v in counts.values()):
        raise ValueError("STAGE68_CAP_LIMIT_FAILED")
    winners=[r for r in original if r["minute_source_status"]==VALID and r["hourly_gt2x_EVALUATION_ONLY"]]
    if len(winners)!=5:
        raise ValueError("STAGE68_FROZEN_FIVE_REAL_2X_EVENTS_CHANGED")
    cases=[];capture=0;old_capture=0
    for w in sorted(winners,key=lambda r:(r["date"],r["symbol"])):
        key=w["date"],w["symbol"]
        candidate=orig_p1.get(key)
        proposed=state.get(key)
        high=w["original_GT2x_first_real_1m_HIGH_UTC"]
        if not high:raise ValueError("STAGE68_GT2X_HIGH_TIMESTAMP_MISSING")
        diff=(stamp(high)-stamp(candidate["at_UTC"])) if candidate else None
        newbool=bool(candidate and proposed["urgent"] and diff>=5)
        old=previous.get(key)
        oldbool=bool(old and old["urgent_under_cap_research"] and stamp(high)-stamp(old["time_UTC"])>=5)
        capture+=int(newbool);old_capture+=int(oldbool)
        cases.append({
            "date":w["date"],"symbol":w["symbol"],
            "2x_HISTORIC_MINUTE_HIGH_UTC_NOT_A_FILL":high,
            "D0_first_UTC":w["original_D0_first_UTC"],
            "P1_UTC":candidate["at_UTC"] if candidate else None,
            "P1_to_first2x_lead_minutes":diff,
            "P2_12h_paced_research_urgent":proposed["urgent"] if proposed else False,
            "P2_12h_paced_early5min_2x":newbool,
            "old_P1_uncapped_halfday_research_urgent":old["urgent_under_cap_research"] if old else False,
            "old_P1_early5min_2x":oldbool,
        })
    if old_capture!=2:
        raise ValueError("STAGE68_ORIGINAL_P1_HISTORIC2X_CAPTURE_COUNT_CHANGED")
    bydate={}
    for date in DATES:
        date_events=[e for e in ledger if e["date"]==date]
        bydate[date]={
            "watch_events":sum(e["kind"]=="FIRST_D0_WATCH" for e in date_events),
            "P1_upgrade_candidates":sum(e["kind"]=="P1_FIRST_ASOF_ELIGIBLE" for e in date_events),
            "P2_research_urgent":sum(e["budget_action"]=="RESEARCH_URGENT_P2_CAP_CONSUMED" for e in date_events),
            "P1_queued_or_cap_deferred":sum(e["budget_action"]=="P1_READY_BUT_CAP_RESERVED_OR_FULL_WATCH_RETAINED" for e in date_events),
            "old_P1_urgent":sum(x["urgent_under_cap_research"] for x in prev if x["date"]==date),
            "per_slot":[{"utc06_slot":i,"P2_total":counts[(date,i)],"P2_first_half":firsthalf[(date,i)]} for i in range(7)],
        }
    gates={
        "min_20_true_future2x":len(winners)>=20,
        "P2_urgent_2x_retain_80pct_original_first_D0_5m_early":capture*100>=80*5,
        "no_research_urgent_over5_or_first_half_over2":all(n<=5 for n in counts.values()) and all(n<=2 for n in firsthalf.values()),
        "no_fabricated_buy_or_notional":True,
        "sample_still_exposed":True,
    }
    verdict=("EXPOSED_MECHANISM_REJECTED_AND_UNDERPOWERED" if not gates["P2_urgent_2x_retain_80pct_original_first_D0_5m_early"]
             else "EXPOSED_MECHANISM_UNDERPOWERED_NOT_VALIDATED")
    return {
        "schema":SCHEMA,
        "source_blobs":PIN,
        "full_market_universe":2700,
        "valid_original_futures_minute_cases":1497,
        "censored_not_mislabeled_negative":1203,
        "raw_D0_WATCH_preserved":196,
        "old_P1_candidates_all_preserved":56,
        "old_P1_urgent_cap5":sum(x["urgent_under_cap_research"] for x in prev),
        "P2_urgent_half_day_paced":len(selected),
        "old_P1_2x_early5min_count":old_capture,
        "P2_2x_early5min_count":capture,
        "real_original_2x_events":len(winners),
        "by_date":bydate,
        "five_2x_event_outcomes":cases,
        "gates":gates,
        "verdict":verdict,
        "NEW_INDEPENDENT_DATE_VALIDATION":"NOT_STARTED",
        "REAL_SPOT_ALPHA_DEX_EXECUTION":"UNVERIFIED",
        "NO_REALIZED_NET_PROFIT_OR_ORDER_NOTIONAL":True,
        "NO_OTHER_AI_REVIEW_DONE":True,
        "NO_DEPLOY_OR_TRADE":True,
        "P1_V03":"REJECTED",
        "D0_FIRST5":"REJECTED",
        "MONSTER":"NO_GO",
    }

def test():
    date="2025-03-30"
    def clock(offset):
        from datetime import datetime,timedelta
        return (datetime.fromisoformat(date+"T06:00:00+00:00")+timedelta(minutes=offset)).isoformat().replace("+00:00","Z")
    def e(symbol,kind,offset,quote):
        return {"date":date,"symbol":symbol,"kind":kind,"at_UTC":clock(offset),
                "asof_quote15":str(quote)}
    a=[]
    for i,m in enumerate((0,3,6,9,12,15,18)):
        symbol="X"+str(i)+"USDT"
        a.extend([e(symbol,"FIRST_D0_WATCH",m,100+i),e(symbol,"P1_FIRST_ASOF_ELIGIBLE",m,100+i)])
    # first 2 use the early window; no further urgent allowed until hour12
    for i,m in enumerate((HALF,HALF+3,HALF+6,HALF+9)):
        symbol="L"+str(i)+"USDT"
        a.extend([e(symbol,"FIRST_D0_WATCH",m,100+i),e(symbol,"P1_FIRST_ASOF_ELIGIBLE",m,100+i)])
    log,s,c,h=simulate(a[::-1])
    assert len(log)==len(a)
    assert c[(date,0)]==5 and h[(date,0)]==2
    assert sum(x["budget_action"]=="RESEARCH_URGENT_P2_CAP_CONSUMED" for x in log)==5
    assert all(s[k]["watch_UTC"] for k in s)
    for i in range(len(a)+1):
        prefix=[x for x in a if stamp(x["at_UTC"])<=stamp(clock(i*3-3))]
        ref,_,_,_=simulate(prefix)
        assert ref == [x for x in log if stamp(x["at_UTC"])<=stamp(clock(i*3-3))]
    assert simulate(a)[0]==log
    # Failed/delayed P1 cannot appear unless first D0 exists.
    try:
        simulate([e("BADUSDT","P1_FIRST_ASOF_ELIGIBLE",3,50)])
    except ValueError as err:
        assert "WITHOUT_UNIQUE" in str(err)
    else:raise AssertionError("STAGE68_FUTURE_P1_ALLOWED")
    print("STAGE68_P2_PREFIX_CAUSAL_2_THEN5_SAME_UTC_WATCH_AND_NO_FUTURE_SELFTEST_PASS")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--selftest",action="store_true")
    ap.add_argument("--out",type=Path)
    opts=ap.parse_args()
    if opts.selftest:test();return
    if opts.out is None:ap.error("--out required")
    old,oldfates,prior=load()
    events,counts=validated_events(old)
    ledger,state,tally,halftally=simulate(events)
    report=compare(old,oldfates,events,ledger,state,tally,halftally)
    opts.out.mkdir(parents=True,exist_ok=True)
    (opts.out/"monster_stage68_original2700_all252_D0_P1_watch_and_research_urgency_states.jsonl").write_text(
        "".join(json.dumps(x,sort_keys=True,ensure_ascii=False)+"\n" for x in ledger),encoding="utf-8")
    (opts.out/"monster_stage68_original3x900_p2_halfday_reserve_vs_p1_summary.json").write_text(
        json.dumps(report,sort_keys=True,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("STAGE68_EXPOSED_CAUSAL_MECHANISM "+
          json.dumps({k:report[k] for k in ("raw_D0_WATCH_preserved","old_P1_candidates_all_preserved",
            "old_P1_urgent_cap5","P2_urgent_half_day_paced","old_P1_2x_early5min_count",
            "P2_2x_early5min_count","verdict")},sort_keys=True))

if __name__=="__main__":
    main()
