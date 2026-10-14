#!/usr/bin/env python3
"""Stage117 one-shot first-D0 fast attention candidate; pure and time-causal.

No trading, scheduled runner, real notification, identity certification,
notional assumption or implicit buying; reproduces frozen Stage79 first gate.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib

try:
    import monster_v4_stage80_dual_entry_core as earlier
except ImportError:
    from scripts import monster_v4_stage80_dual_entry_core as earlier

SCHEMA="MONSTER_STAGE117_FIRST_D0_EARLY_ATTENTION_FROZEN_V1"
EVENT_NAMESPACE="MONSTER_STAGE117_FIRST_D0_V1"
DECISION_NAMES={"EARLY_ATTENTION_CANDIDATE","D0_RAW_WATCH_ONLY",
                "SOURCE_UNKNOWN_RETAIN_D0"}
MIN=60_000


def evaluate_first_d0(*,venue:str,symbol:str,first_d0_utc:str,
                      feature:earlier.Features|None,
                      source_ok:bool=True,
                      frozen_contract:dict|None=None)->dict:
    """Use ONLY the first D0 event and 61 already closed 1m bars.

    Stage79 exact FIRST gate is reused, not optimized on the Stage83 GT labels.
    """
    if venue!="USDM" or not isinstance(symbol,str) or not symbol.endswith("USDT"):
        raise ValueError("STAGE117_USDM_SYMBOL_VENUE_REQUIRED")
    ms=earlier.utc_ms(first_d0_utc)
    if ms % (3*MIN):
        raise ValueError("STAGE117_FIRST_D0_NOT_3MIN_POLL")
    contract=frozen_contract or earlier.load_contract()
    if (contract["from_first_d0_expiration_hours"]!=48
        or contract["entry_first"]!=earlier.load_contract()["entry_first"]):
        raise ValueError("STAGE117_STAGE79_FIRST_GATE_DRIFT")
    event_key=f"{EVENT_NAMESPACE}|{venue}|{symbol}|{first_d0_utc}"
    event_id=hashlib.sha256(event_key.encode("ascii")).hexdigest()
    out={
        "schema":SCHEMA,
        "venue":venue,
        "symbol":symbol,
        "first_D0_UTC":first_d0_utc,
        "event_id":event_id,
        "event_key":event_key,
        "candidate_decision_UTC":first_d0_utc,
        "raw_D0_WATCH_retained":True,
        "model_decision":"SOURCE_UNKNOWN_RETAIN_D0",
        "next_entry_price":"UNKNOWN_REQUIRES_REAL_BID_ASK",
        "crypto_identity":"UNKNOWN_REQUIRES_INDEPENDENT_ASOF_PROOF",
        "real_execution_profit":"UNKNOWN",
        "user_notional_quote":"UNSPECIFIED",
        "monitored":False,
        "gmail":"OFF",
        "monster_deployment":"NO_GO",
        "real_trading":"NO_GO",
    }
    if not source_ok or feature is None:
        return out
    feature.validate()
    base=contract["entry_first"]
    # This is the ORIGINAL Stage79 first gate; no second-chance waiting.
    is_candidate=earlier.gate(feature, True, None, contract)
    out.update(
        model_decision=("EARLY_ATTENTION_CANDIDATE" if is_candidate
                        else "D0_RAW_WATCH_ONLY"),
        asof_ret60_pct=str(feature.ret60_pct),
        asof_quote15_USDT=str(feature.quote15_usdt),
        asof_trade15=feature.trade15,
        asof_quote15_normalized_prev45=(
            str(feature.quote15_relative45)
            if feature.quote15_relative45 is not None else None),
        gate_frozen_Stage79={
            "ret60_pct_gte":base["ret60_pct_gte"],
            "quote15_usdt_gte":base["quote15_usdt_gte"],
            "trades15_gte":base["trades15_gte"],
            "quote15_normalized_prev45_gte":
                base["quote15_normalized_prev45_gte"],
        },
    )
    return out


def from_closed_minutes(*,venue:str,symbol:str,first_d0_utc:str,
                        minute_bars:list,source_ok:bool=True)->dict:
    """The same function used by prospective official Binance minute replay."""
    ms=earlier.utc_ms(first_d0_utc)
    closed=[r for r in minute_bars if r[0]<ms]
    feature=(earlier.from_archived_closed_bars(closed,ms)
             if source_ok else None)
    return evaluate_first_d0(venue=venue,symbol=symbol,
                             first_d0_utc=first_d0_utc,
                             feature=feature,source_ok=source_ok)


def selftest():
    from decimal import Decimal as D
    t="2026-10-14T06:03:00Z"
    base=earlier.utc_ms(t)
    minute=[(base+(i-61)*MIN,D(100),D(101),D(99),D(100),
             D(150_000) if i>=46 else D(100_000),1000)
            for i in range(61)]
    # >=1M quote15, >=10k trades15, ratio 1.3.
    # 60m ret must be 8%; set the t-60 close accordingly.
    changed=list(minute)
    at60=list(changed[0]); at60[4]=D(90);changed[0]=tuple(at60)
    early=from_closed_minutes(venue="USDM",symbol="AAAUSDT",
                              first_d0_utc=t,minute_bars=changed)
    assert early["model_decision"]=="EARLY_ATTENTION_CANDIDATE"
    assert early["raw_D0_WATCH_retained"] is True
    assert early["real_trading"]=="NO_GO"
    assert from_closed_minutes(venue="USDM",symbol="AAAUSDT",first_d0_utc=t,
         minute_bars=changed+[(base,D(999),D(10000),D(0),D(999),
                               D(10_000_000),1_000_000)])==early
    other=evaluate_first_d0(venue="USDM",symbol="BBBUSDT",first_d0_utc=t,
                            feature=earlier.Features(D(1),D(100),500,D(1)))
    assert other["model_decision"]=="D0_RAW_WATCH_ONLY"
    assert other["event_id"]!=early["event_id"]
    missing=evaluate_first_d0(venue="USDM",symbol="AAAUSDT",
                              first_d0_utc=t,feature=None)
    assert missing["model_decision"]=="SOURCE_UNKNOWN_RETAIN_D0"
    assert earlier.load_contract()["entry_first"]["ret60_pct_gte"]=="8"
    print("STAGE117_FIRST_D0_ASOF_PAST_ONLY_LABEL_FREE_FROZEN_GATE_TEST_PASS")


if __name__=="__main__":
    selftest()
