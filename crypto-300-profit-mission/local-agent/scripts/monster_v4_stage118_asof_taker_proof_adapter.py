#!/usr/bin/env python3
"""Stage118 exact as-of official 1m taker proof for original Stage116 replay.

Re-fetch verified original Binance USD-M official archive only when replay
contains a true D0. Compare the actual SHA of same minute ZIP to the
already verified Stage91 original 9-day source; compare ALL 61 OHLC-derived
close, quote-volume and trade-counts against Stage91's same source. This is
offline source validation, not a live Binance monitor or broker.
"""
from __future__ import annotations

from datetime import datetime,timedelta,timezone

try:
    import monster_v4_stage118_first_d0_dual_lane_flow_core as model
    import monster_v4_stage56_usdm_asof_taker_and_tradecount_source_audit as taker
    import monster_v4_stage80_dual_entry_core as base
except ImportError:
    from scripts import monster_v4_stage118_first_d0_dual_lane_flow_core as model
    from scripts import monster_v4_stage56_usdm_asof_taker_and_tradecount_source_audit as taker
    from scripts import monster_v4_stage80_dual_entry_core as base

MIN=60_000
SCHEMA="MONSTER_STAGE118_ASOF_61M_TAKER_OFFICIAL_DAILY_SHA_FORWARD_REPLAY_V1"


def proof(*,venue,symbol,first_d0_utc,original_bars,
          original_nine_day_SHA_receipts,fetch=None):
    if fetch is None:
        fetch=taker.read_verified_day
    if venue!="USDM" or not symbol.endswith("USDT"):
        raise ValueError("STAGE118_INCOMPATIBLE_VENUE_OR_SYMBOL")
    if not isinstance(original_nine_day_SHA_receipts,list) or len(original_nine_day_SHA_receipts)!=9:
        raise ValueError("STAGE118_NINE_PUBLISHER_SHA_DAYS_REQUIRED")
    prior={r["date"]:r["zip_sha256"] for r in original_nine_day_SHA_receipts}
    if len(prior)!=9 or any(
        r.get("verified_official_publisher_SHA256") is not True
        or len(r.get("zip_sha256",""))!=64
        or r.get("bars")!=1440
        for r in original_nine_day_SHA_receipts):
        raise ValueError("STAGE118_PRIOR_9_SOURCE_DAYS_NOT_VERIFIED")
    ms=base.utc_ms(first_d0_utc)
    if ms%(3*MIN):
        raise ValueError("STAGE118_NOT_ORIGINAL_3M_D0_TICK")
    stamps=[ms-i*MIN for i in range(61,0,-1)]
    existing={r[0]:r for r in original_bars if stamps[0]<=r[0]<=stamps[-1]}
    if len(existing)!=61 or any(k not in existing for k in stamps):
        raise ValueError("STAGE118_PRIOR_STAGED_1M_DATA_NOT_CONTIGUOUS")
    days=sorted({datetime.fromtimestamp(t/1000,timezone.utc).date()
                 for t in stamps})
    raw={};verified=[]
    try:
        for day in days:
            ticks,receipt=fetch(symbol,day)
            if (receipt.get("date")!=day.isoformat()
                or receipt.get("checksum_verified") is not True
                or receipt.get("official_zip_sha256")!=prior.get(day.isoformat())):
                raise ValueError("STAGE118_TAKER_SOURCE_SHA_MISMATCH_WITH_ORIGINAL_1M")
            if set(raw).intersection(ticks):
                raise ValueError("STAGE118_DUPLICATE_TAKER_DAY_MINUTES")
            raw.update(ticks)
            verified.append({"date":receipt["date"],
                             "zip_sha256":receipt["official_zip_sha256"],
                             "independently_matches_stage91_original_pub_sha":True})
    except FileNotFoundError as exc:
        unknown=model.evaluate_first_d0(
            venue=venue,symbol=symbol,first_d0_utc=first_d0_utc,
            asof=None,source_ok=False)
        return {
            "schema":SCHEMA,
            "source_status":"SOURCE_UNAVAILABLE_AFTER_ORIGINAL_PUBLISHER_1M",
            "source_error_type":type(exc).__name__,
            "no_synthetic_order_flow":True,
            "verified_days":verified,
            "frozen_decision":unknown,
        }
    if any(k not in raw for k in stamps):
        raise ValueError("STAGE118_INCOMPLETE_TAKER_61M_AFTER_PUBLISHER_ZIP")
    for t in stamps:
        previous=existing[t]
        newer=raw[t]
        if (len(previous)!=7 or
            previous[4]!=newer[0] or previous[5]!=newer[1] or
            previous[6]!=newer[3]):
            raise ValueError("STAGE118_ORIGINAL_1M_OHLC_QUOTE_TRADE_PARITY_FAIL")
    new=model.from_closed_minute_taker(
        venue=venue,symbol=symbol,first_d0_utc=first_d0_utc,
        source_ticks=raw)
    return {
        "schema":SCHEMA,
        "source_status":"COMPLETE_OFFICIAL_ASOF_61M_TAKER_WITH_ORIGINAL_SHA_PARITY",
        "verified_days":verified,
        "no_future_minute_in_admission":True,
        "frozen_decision":new,
        "real_executable_net":"UNKNOWN","deployment":"NO_GO",
    }


def selftest():
    from decimal import Decimal as D
    from datetime import date
    first="2026-10-14T06:03:00Z"
    now=base.utc_ms(first)
    # Build 61 original verified minute bars, fully closed and consistent
    # with the take-buy parser. t-61 00:00, t-1 06:02 61 one-minute bars.
    earlier={}
    rows=[]
    for i in range(61):
        t=now-(61-i)*MIN
        quote=D(200_000 if i>=46 else 100_000)
        buy=quote*D("0.65" if i>=46 else "0.50")
        earlier[t]=(D(100),quote,buy,1000)
        rows.append((t,D(100),D(101),D(99),D(100),quote,1000))
    day="2026-10-14"
    receipt={"date":day,"zip_sha256":"a"*64,
             "verified_official_publisher_SHA256":True,"bars":1440}
    expected=[{"date":(date.fromisoformat(day)+timedelta(days=i)).isoformat(),
               "zip_sha256":"a"*64,"verified_official_publisher_SHA256":True,
               "bars":1440} for i in range(-1,8)]
    def reader(symbol,actual_day):
        return earlier,{"date":actual_day.isoformat(),
                        "official_zip_sha256":"a"*64,
                        "checksum_verified":True}
    result=proof(venue="USDM",symbol="TESTUSDT",first_d0_utc=first,
                 original_bars=rows,
                 original_nine_day_SHA_receipts=expected,fetch=reader)
    assert result["frozen_decision"]["decision"]=="FLOW_ATTENTION_CANDIDATE"
    assert result["source_status"].startswith("COMPLETE")
    updated=rows+[(now,D(999),D(10000),D(1),D(999),D(999999),999999)]
    assert proof(venue="USDM",symbol="TESTUSDT",first_d0_utc=first,
                 original_bars=updated,
                 original_nine_day_SHA_receipts=expected,fetch=reader)==result
    def forgery(symbol,day):
        _,r=reader(symbol,day)
        return earlier,{**r,"official_zip_sha256":"b"*64}
    try:proof(venue="USDM",symbol="TESTUSDT",first_d0_utc=first,
              original_bars=rows,original_nine_day_SHA_receipts=expected,
              fetch=forgery)
    except ValueError as e:assert "SHA_MISMATCH" in str(e)
    else:raise AssertionError("STAGE118_SHA_FORGED_CANDIDATE_NOT_REJECTED")
    fake=list(rows)
    t,o,h,l,c,q,n=fake[0]
    fake[0]=(t,o,h,l,c,q+1,n)
    try:proof(venue="USDM",symbol="TESTUSDT",first_d0_utc=first,
              original_bars=fake,original_nine_day_SHA_receipts=expected,
              fetch=reader)
    except ValueError as e:assert "OHLC_QUOTE_TRADE" in str(e)
    else:raise AssertionError("STAGE118_DIVERGENT_MARKET_PRICE_SOURCE_ACCEPTED")
    def gone(symbol,day):
        raise FileNotFoundError("source unavailable")
    no=proof(venue="USDM",symbol="TESTUSDT",first_d0_utc=first,
             original_bars=rows,original_nine_day_SHA_receipts=expected,
             fetch=gone)
    assert no["frozen_decision"]["decision"]=="SOURCE_UNKNOWN_RETAIN_D0"
    assert no["source_status"].startswith("SOURCE_UNAVAILABLE")
    print("STAGE118_STAGE116_FULL_61M_SHA_PARITY_TAKER_ASOF_NO_LOOKAHEAD_SELFTEST_PASS")


if __name__=="__main__":
    selftest()
