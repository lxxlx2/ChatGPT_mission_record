#!/usr/bin/env python3
"""Stage118 frozen first-D0 price OR taker-flow pure research attention core.

One event / D0, original Stage117 price lane untouched; second lane uses
true Binance USD-M taker-buy 1m verified columns, only earlier closed bars.
No side effects, orders, notional, Gmail or production monitoring.
"""
from __future__ import annotations

from decimal import Decimal
import hashlib

try:
    import monster_v4_stage117_first_d0_fast_attention_core as price
    import monster_v4_stage80_dual_entry_core as d1
    import monster_v4_stage64_all519_first_d0_asof61m_official_taker as source
except ImportError:
    from scripts import monster_v4_stage117_first_d0_fast_attention_core as price
    from scripts import monster_v4_stage80_dual_entry_core as d1
    from scripts import monster_v4_stage64_all519_first_d0_asof61m_official_taker as source

SCHEMA="MONSTER_STAGE118_FROZEN_FIRST_D0_PRICE_OR_TAKER_FLOW_V1"
PRICE_FIRST_RULE_BLOB="292e0cefe2089214dbde48ee50d6baf6cf590f8e"
MIN=60_000
BUY15=Decimal("0.55")
BUY_DELTA=Decimal("0.03")
FLOW_SOURCE_FIELDS=(
    "ret60_pct","quote15_USDT","quote60_USDT",
    "quote15_normalized_prev45","taker_buy_quote15_USDT",
    "taker_buy_quote60_USDT","taker_buy_share15","taker_buy_share60",
    "trade_count15","trade_count60","minutes_with_positive_quote60",
    "historical_usdm_executed_trades60",
)


def numeric(x,label):
    if x is None:
        return None
    try:
        z=Decimal(str(x))
    except (ArithmeticError,ValueError,TypeError):
        raise ValueError("STAGE118_BAD_FINITE_INPUT_"+label)
    if not z.is_finite():
        raise ValueError("STAGE118_NONFINITE_"+label)
    return z


def frozen_original_rule():
    c=d1.load_contract()
    if d1.CONTRACT_SHA!=PRICE_FIRST_RULE_BLOB:
        raise ValueError("STAGE118_STAGE79_PRICE_GATE_BLOB_DRIFT")
    orig=c["entry_first"]
    if (orig["ret60_pct_gte"]!="8"
        or orig["quote15_usdt_gte"]!="1000000"
        or orig["trades15_gte"]!=10000
        or orig["quote15_normalized_prev45_gte"]!="1.3"):
        raise ValueError("STAGE118_ORIGINAL_FIRST_GATE_MOVED")
    return c


def check(raw):
    if not isinstance(raw,dict):
        raise ValueError("STAGE118_NEEDS_OFFICIAL_ASOF_FEATURE_DICT")
    if any(k not in raw for k in FLOW_SOURCE_FIELDS):
        raise ValueError("STAGE118_INCOMPLETE_ASOF_TAKER_FEATURES")
    if (not isinstance(raw["historical_usdm_executed_trades60"],bool)
        or raw["historical_usdm_executed_trades60"] is not True):
        raise ValueError("STAGE118_REAL_ASOF_TRADE_EVIDENCE_REQUIRED")
    for k in ("trade_count15","trade_count60","minutes_with_positive_quote60"):
        if isinstance(raw[k],bool) or not isinstance(raw[k],int) or raw[k]<0:
            raise ValueError("STAGE118_TRADE_COUNT_INCONSISTENT")
    if (raw["trade_count15"]>raw["trade_count60"]
        or raw["minutes_with_positive_quote60"]>60):
        raise ValueError("STAGE118_TRADES_15_GREATER_THAN_60")
    values={k:numeric(raw[k],k) for k in (
        "ret60_pct","quote15_USDT","quote60_USDT",
        "quote15_normalized_prev45","taker_buy_quote15_USDT",
        "taker_buy_quote60_USDT","taker_buy_share15","taker_buy_share60")}
    q15,q60=values["quote15_USDT"],values["quote60_USDT"]
    b15,b60=values["taker_buy_quote15_USDT"],values["taker_buy_quote60_USDT"]
    sh15,sh60=values["taker_buy_share15"],values["taker_buy_share60"]
    if q15 is None or q60 is None or b15 is None or b60 is None:
        raise ValueError("STAGE118_MISSING_TAKER_TURNOVER")
    if not (Decimal(0)<=b15<=q15<=q60 and b15<=b60<=q60):
        raise ValueError("STAGE118_TAKER_QUOTES_IMPOSSIBLE")
    for name,sh,q,b in (("15",sh15,q15,b15),("60",sh60,q60,b60)):
        if q>0:
            if sh is None or not (Decimal(0)<=sh<=Decimal(1)):
                raise ValueError("STAGE118_MISSING_POSITIVE_BUY_SHARE_"+name)
            if abs(sh-b/q)>Decimal("0.000000001"):
                raise ValueError("STAGE118_TAKER_SHARE_NOT_FROM_ACTUAL_QUOTES_"+name)
        elif sh is not None:
            raise ValueError("STAGE118_ZERO_QUOTE_WITH_SHARE_"+name)
    if values["quote15_normalized_prev45"] is not None:
        ratio=values["quote15_normalized_prev45"]
        if ratio<0:
            raise ValueError("STAGE118_INVALID_QUOTE_RATIO")
        if q60<=q15 or abs(ratio-3*q15/(q60-q15))>Decimal("0.000000001"):
            raise ValueError("STAGE118_VOLUME_RATIO_RECALC_DRIFT")
    return values


def evaluate_first_d0(*,venue:str,symbol:str,first_d0_utc:str,
                      asof:dict|None,source_ok:bool=True)->dict:
    """Identical pure rule for historical Stage64 and new Stage56 minutes."""
    frozen=frozen_original_rule()
    p=None
    if asof is not None and source_ok:
        v=check(asof)
        price_features=d1.Features(
            ret60_pct=v["ret60_pct"],
            quote15_usdt=v["quote15_USDT"],
            trade15=asof["trade_count15"],
            quote15_relative45=v["quote15_normalized_prev45"],
            closed_price=None,
        )
        p=price.evaluate_first_d0(
            venue=venue,symbol=symbol,first_d0_utc=first_d0_utc,
            feature=price_features,source_ok=True,frozen_contract=frozen)
    else:
        p=price.evaluate_first_d0(
            venue=venue,symbol=symbol,first_d0_utc=first_d0_utc,
            feature=None,source_ok=False,frozen_contract=frozen)
    allowed_flow=False
    buyer_delta=None
    if p["model_decision"]!="SOURCE_UNKNOWN_RETAIN_D0":
        assert asof is not None
        v=check(asof)
        sh15=v["taker_buy_share15"]
        sh60=v["taker_buy_share60"]
        buyer_delta=sh15-sh60 if sh15 is not None and sh60 is not None else None
        allowed_flow=bool(
            buyer_delta is not None
            and sh15>=BUY15 and buyer_delta>=BUY_DELTA
            and v["quote15_USDT"]>=Decimal("1000000")
            and asof["trade_count15"]>=10000
            and v["quote15_normalized_prev45"] is not None
            and v["quote15_normalized_prev45"]>=Decimal("1.3"))
    lane_price=p["model_decision"]=="EARLY_ATTENTION_CANDIDATE"
    if p["model_decision"]=="SOURCE_UNKNOWN_RETAIN_D0":
        final="SOURCE_UNKNOWN_RETAIN_D0"
    elif lane_price and allowed_flow:
        final="BOTH_ATTENTION_CANDIDATE"
    elif lane_price:
        final="PRICE_ATTENTION_CANDIDATE"
    elif allowed_flow:
        final="FLOW_ATTENTION_CANDIDATE"
    else:
        final="D0_RAW_WATCH_ONLY"
    if p["event_id"]!=hashlib.sha256(p["event_key"].encode()).hexdigest():
        raise ValueError("STAGE118_PRIOR_SCOPED_EVENT_ID_INVALID")
    key=f"STAGE118_V1|{venue}|{symbol}|{first_d0_utc}"
    return {
        "schema":SCHEMA,
        "venue":venue,"symbol":symbol,
        "first_D0_UTC":first_d0_utc,
        "idempotency_key":key,
        "event_id":hashlib.sha256(key.encode()).hexdigest(),
        "decision":final,
        "fast_attention":bool(lane_price or allowed_flow),
        "PRICE_unchanged_Stage117_lane":lane_price,
        "FLOW_new_taker_buy_lane":allowed_flow,
        "asof_15m_buy_quote_share":(
            str(numeric(asof["taker_buy_share15"],"buy15"))
            if asof is not None and source_ok
            and asof["taker_buy_share15"] is not None else None),
        "asof_buy15_minus_buy60_percentage_points":(
            str(buyer_delta*100) if buyer_delta is not None else None),
        "raw_D0_watch_retained":True,
        "source_contract":"STAGE64_OFFICIAL_PUBLISHER_SHA_ASOF_OR_STAGE56_SAME_SOURCE",
        "historical_2x_is_NEVER_an_input":True,
        "BUY":"NOT_AUTHORIZED",
        "identity_asof":"UNKNOWN_NOT_VERIFIED",
        "user_notional":"UNSPECIFIED",
        "real_net":"UNKNOWN",
        "gmail":"OFF","deployment":"NO_GO",
    }


def from_closed_minute_taker(*,venue,symbol,first_d0_utc,source_ticks):
    t=d1.utc_ms(first_d0_utc)
    f=source.raw_features(t,source_ticks)
    return evaluate_first_d0(
        venue=venue,symbol=symbol,first_d0_utc=first_d0_utc,
        asof=f,source_ok=True)


def selftest():
    t="2026-10-14T06:03:00Z"
    ms=d1.utc_ms(t)
    # 61 already CLOSED 1m records. Prev45 turnover 100K/min 50% buy,
    # last15 turnover 200K/min 65% buy. No pre-price acceleration.
    bars={}
    for i in range(61):
        ts=ms-(61-i)*MIN
        recent=i>=46
        q=Decimal(200000 if recent else 100000)
        buy=q*Decimal("0.65" if recent else "0.5")
        bars[ts]=(Decimal(100),q,buy,1000)
    f=source.raw_features(ms,bars)
    a=evaluate_first_d0(venue="USDM",symbol="FAKEUSDT",
                        first_d0_utc=t,asof=f)
    assert a["decision"]=="FLOW_ATTENTION_CANDIDATE"
    assert a["PRICE_unchanged_Stage117_lane"] is False
    assert a["FLOW_new_taker_buy_lane"] is True
    assert from_closed_minute_taker(venue="USDM",symbol="FAKEUSDT",
                                  first_d0_utc=t,source_ticks=bars)==a
    future={**bars,ms:(Decimal(999),Decimal(10**12),
                       Decimal(10**12),10**9)}
    assert from_closed_minute_taker(venue="USDM",symbol="FAKEUSDT",
                                  first_d0_utc=t,source_ticks=future)==a
    weak=dict(f)
    weak["taker_buy_quote15_USDT"]=str(Decimal(f["quote15_USDT"])*Decimal("0.50"))
    weak["taker_buy_share15"]="0.50"
    weak["taker_buy_quote60_USDT"]=str(
        Decimal(weak["taker_buy_quote15_USDT"])+
        Decimal(f["quote60_USDT"])-Decimal(f["quote15_USDT"])*Decimal("0.5"))
    weak["taker_buy_share60"]=str(Decimal(weak["taker_buy_quote60_USDT"])/Decimal(f["quote60_USDT"]))
    b=evaluate_first_d0(venue="USDM",symbol="FAKEUSDT",first_d0_utc=t,asof=weak)
    assert b["decision"]=="D0_RAW_WATCH_ONLY"
    assert b["event_id"]==a["event_id"]
    null=evaluate_first_d0(venue="USDM",symbol="FAKEUSDT",
                           first_d0_utc=t,asof=None,source_ok=False)
    assert null["decision"]=="SOURCE_UNKNOWN_RETAIN_D0"
    assert null["event_id"]==a["event_id"]
    c=evaluate_first_d0(venue="USDM",symbol="DIFFERENTUSDT",
                        first_d0_utc=t,asof=f)
    assert c["event_id"]!=a["event_id"]
    print("STAGE118_VERIFIED_TAKER_BUY_ASOF_PRICE_AND_FLOW_LANES_CAUSAL_SELFTEST_PASS")


if __name__=="__main__":
    selftest()
