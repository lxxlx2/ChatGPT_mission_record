#!/usr/bin/env python3
"""Monster Stage42 Stage40-frozen P1 candidate, read-only pure causal evaluator.

Runs ONLY on original V4 D0 WATCH observations. DOES NOT modify original V4,
Frank, Gmail, an actual outbox, live monitoring or trades. Data is publisher
SHA-backed closed 1m bars. A research score is NEVER BUY authorization.
"""
from datetime import datetime,timezone,timedelta
from decimal import Decimal, InvalidOperation
import hashlib,json
from pathlib import Path

V01_SCHEMA="MONSTER_STAGE42_ORIGINAL_D0_PRIORITY_CANDIDATE_V01_CAUSAL_ONLY"
THRESHOLD_RET_60=Decimal("8.0")
THRESHOLD_QUOTE15=Decimal("250000")
THRESHOLD_Q15_VS_PRIOR45=Decimal("1.5")
BAR_MS=60000
AFTER_POLL_3M_MS=3*BAR_MS
AFTER_POLL_6M_MS=6*BAR_MS

def utc(ms):
    return datetime.fromtimestamp(ms/1000,timezone.utc).isoformat().replace("+00:00","Z")

def parse_utc(value):
    if not isinstance(value,str):raise ValueError("P1_INVALID_UTC_VALUE")
    d=datetime.fromisoformat(value.replace("Z","+00:00"))
    if d.tzinfo is None or d.utcoffset()!=timedelta(0):
        raise ValueError("P1_REQUIRES_EXPLICIT_UTC")
    ms=int(d.timestamp()*1000)
    if ms<=0 or ms%BAR_MS:raise ValueError("P1_WATCH_NOT_MINUTE_BOUNDARY")
    return ms

def amount(value,positive=False):
    try:result=Decimal(str(value))
    except (InvalidOperation,ValueError,TypeError) as ex:raise ValueError("P1_NONNUMERIC_OHLCV") from ex
    if not result.is_finite() or (result<=0 if positive else result<0):
        raise ValueError("P1_INVALID_PRICE_OR_QUOTE")
    return result

def calculate(venue,symbol,watch_utc,bar_sequence,original_v4_watch_event_id=""):
    """Score first WATCH once, as of exact second following 3-minute confirmation.

    bar_sequence uses original official minute bar tuples:
      (UTC start ms, open, high, low, close, quote_volume, trade_count).
    Clock watch_utc represents the original 3m closed-bar poll instant.
    Need all minute rows from watch UTC -61m through watch UTC +5m inclusive.
    No HIGH or trade exit is used in this eligibility calculation.
    """
    if venue not in ("spot","futures") or not isinstance(symbol,str) or not symbol.endswith("USDT"):
        raise ValueError("P1_INVALID_VENUE_SYMBOL")
    watch_ms=parse_utc(watch_utc)
    if not isinstance(original_v4_watch_event_id,str):
        raise ValueError("P1_BAD_D0_EVENT_ID")
    event_id=hashlib.sha256(("MONSTER_STAGE41|"+venue+"|"+symbol+"|"+
         original_v4_watch_event_id+"|P1_V01").encode()).hexdigest()
    bars={}
    for row in bar_sequence:
        if len(row)<7:raise ValueError("P1_BAR_MISSING_FIELDS")
        t=int(row[0])
        if t<=0 or t%BAR_MS or t in bars:raise ValueError("P1_DUP_OR_BAD_1M_TIME")
        o,h,l,c=map(lambda x:amount(x,True),row[1:5])
        q=amount(row[5])
        trades=int(row[6])
        if h<max(o,c) or l>min(o,c) or h<l or trades<0:
            raise ValueError("P1_BAD_OFFICIAL_1M_BAR")
        bars[t]=(o,h,l,c,q,trades)
    requested=[watch_ms+i*BAR_MS for i in range(-61,6)]
    missing=[k for k in requested if k not in bars]
    if missing:
        return {"schema":V01_SCHEMA,"venue":venue,"symbol":symbol,"D0_WATCH_UTC":watch_utc,
          "research_event_id":event_id,"status":"UNSCORABLE_SOURCE",
          "reason":"MISSING_CLOSED_OFFICIAL_1M_BARS","missing_bars":len(missing),
          "P1_escalation_UTC":None,"no_buy":True}
    close0=bars[watch_ms-BAR_MS][3]
    close_minus60=bars[watch_ms-61*BAR_MS][3]
    c3=bars[watch_ms+2*BAR_MS][3]
    c6=bars[watch_ms+5*BAR_MS][3]
    ret60=(close0/close_minus60-Decimal(1))*100
    last60=[bars[watch_ms+AFTER_POLL_6M_MS-(i+1)*BAR_MS] for i in range(60)]
    quote15=sum((b[4] for b in last60[:15]),Decimal(0))
    previous45=sum((b[4] for b in last60[15:60]),Decimal(0))
    quote_ratio=(quote15/(previous45/3)) if previous45>0 else None
    valid=(ret60>=THRESHOLD_RET_60 and c3>=close0 and c6>=close0
           and quote15>=THRESHOLD_QUOTE15 and quote_ratio is not None
           and quote_ratio>=THRESHOLD_Q15_VS_PRIOR45)
    return {"schema":V01_SCHEMA,"venue":venue,"symbol":symbol,"D0_WATCH_UTC":watch_utc,
      "research_event_id":event_id,"decision_asof_UTC":utc(watch_ms+AFTER_POLL_6M_MS),
      "P1_escalation_UTC":utc(watch_ms+AFTER_POLL_6M_MS) if valid else None,
      "status":"P1_RESEARCH_ELIGIBLE" if valid else "P1_NOT_ESCALATED",
      "first_D0_close":str(close0),"confirm_closed_plus3m":str(c3),
      "confirm_closed_plus6m":str(c6),"return_60m_at_D0_pct":str(ret60),
      "quote_15m_usdt_asof_decision":str(quote15),
      "quote_prior45m_usdt_asof_decision":str(previous45),
      "quote15_vs_previous45_per_minute":str(quote_ratio) if quote_ratio is not None else None,
      "no_buy":True,"Frank":"UNCHANGED","mail":"OFF"}

def selftest():
    at=parse_utc("2025-04-19T09:00:00Z")
    seq=[]
    for i in range(-61,6):
        c=Decimal("1.20") if i>=-1 else Decimal("1.00")
        # Last15m 25k U/min and prior45 1000 U/min.
        q=Decimal("25000") if i>=-9 else Decimal("1000")
        seq.append((at+i*BAR_MS,c,c,c,c,q,4))
    d=calculate("futures","ABCUSDT","2025-04-19T09:00:00Z",seq,"original_v4_event")
    assert d["status"]=="P1_RESEARCH_ELIGIBLE" and d["decision_asof_UTC"]=="2025-04-19T09:06:00Z"
    assert d["P1_escalation_UTC"]!="2025-04-19T09:00:00Z" and d["no_buy"]
    assert calculate("futures","ABCUSDT","2025-04-19T09:00:00Z",seq[:-1],"original_v4_event")["status"]=="UNSCORABLE_SOURCE"
    # Modifying minute at +6m is FUTURE relative to decision, thus may not enter eligibility.
    modified=seq+[(at+6*BAR_MS,Decimal("1"),Decimal("1000"),Decimal("1"),Decimal("1000"),Decimal("999999"),9)]
    assert calculate("futures","ABCUSDT","2025-04-19T09:00:00Z",modified,"original_v4_event")["status"]=="P1_RESEARCH_ELIGIBLE"
    # A fall at the second confirmation invalidates P1.
    bad=list(seq)
    bad[-1]=(bad[-1][0],Decimal("1"),Decimal("1"),Decimal("1"),Decimal("1"),Decimal("25000"),4)
    assert calculate("futures","ABCUSDT","2025-04-19T09:00:00Z",bad,"original_v4_event")["status"]=="P1_NOT_ESCALATED"
    # Baseline first watch already barely has 60m return 0, so do not upgrade.
    flat=[]
    for s in seq:
        flat.append((s[0],Decimal("1"),Decimal("1"),Decimal("1"),Decimal("1"),s[5],s[6]))
    assert calculate("futures","ABCUSDT","2025-04-19T09:00:00Z",flat,"original_v4_event")["status"]=="P1_NOT_ESCALATED"
    assert d["research_event_id"]==calculate("futures","ABCUSDT","2025-04-19T09:00:00Z",seq,"original_v4_event")["research_event_id"]
    print("STAGE42_P1_CAUSAL_NO_FUTURE_CLOSE_AND_THRESHOLDS_SELFTEST_PASS")

def main():
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument("--selftest",action="store_true")
    args=parser.parse_args()
    if args.selftest:
        selftest()
    else:
        parser.error("Research import-only pure function; --selftest available")
if __name__=="__main__":main()
