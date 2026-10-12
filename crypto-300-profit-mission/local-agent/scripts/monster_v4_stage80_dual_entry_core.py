#!/usr/bin/env python3
"""Monster Stage80 pure D1 research candidate. NO production, network, orders or email."""
from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path

CONTRACT_SHA = "292e0cefe2089214dbde48ee50d6baf6cf590f8e"
CONTRACT_PATH = Path(__file__).resolve().parents[2] / "monster/evidence/monster_stage79_dual_entry_d1_frozen_contract_20261013.json"
MINUTE_MS = 60_000
RESEARCH_ONLY = True


def sha_blob(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def load_contract(path: Path = CONTRACT_PATH) -> dict:
    raw = path.read_bytes()
    if sha_blob(raw) != CONTRACT_SHA:
        raise ValueError("STAGE80_CONTRACT_SOURCE_NOT_FROZEN")
    obj = json.loads(raw)
    if obj["schema"] != "MONSTER_STAGE79_FROZEN_DUAL_ENTRY_D1_RESEARCH_CONTRACT_V1":
        raise ValueError("STAGE80_WRONG_CONTRACT_SCHEMA")
    if not obj["d0_unchanged"] or obj["deployment"] != "NO_GO" or obj["gmail"] != "OFF":
        raise ValueError("STAGE80_AUTHORITY_DRIFT")
    return obj


def decimal(x) -> Decimal:
    if x is None or isinstance(x, bool):
        raise ValueError("STAGE80_MISSING_OR_BAD_NUMBER")
    try:
        d = Decimal(str(x))
    except (InvalidOperation, ValueError):
        raise ValueError("STAGE80_INVALID_DECIMAL") from None
    if not d.is_finite():
        raise ValueError("STAGE80_NONFINITE_NUMBER")
    return d


def utc_ms(x: str) -> int:
    if not isinstance(x, str) or not x.endswith("Z"):
        raise ValueError("STAGE80_TIMESTAMP_MUST_BE_UTC")
    d = datetime.fromisoformat(x[:-1] + "+00:00")
    if d.second != 0 or d.microsecond != 0:
        raise ValueError("STAGE80_MINUTE_CLOCK_NOT_CLOSED")
    return int(d.timestamp() * 1000)


@dataclass(frozen=True)
class Features:
    ret60_pct: Decimal
    quote15_usdt: Decimal
    trade15: int
    quote15_relative45: Decimal | None
    closed_price: Decimal | None = None

    def validate(self) -> None:
        for d in (self.ret60_pct, self.quote15_usdt):
            if not d.is_finite():
                raise ValueError("STAGE80_NONFINITE_FEATURE")
        if self.quote15_usdt < 0 or not isinstance(self.trade15, int) or isinstance(self.trade15, bool) or self.trade15 < 0:
            raise ValueError("STAGE80_BAD_TRADE_COUNTS")
        if self.quote15_relative45 is not None and (not self.quote15_relative45.is_finite() or self.quote15_relative45 < 0):
            raise ValueError("STAGE80_BAD_RATIO")
        if self.closed_price is not None and (not self.closed_price.is_finite() or self.closed_price <= 0):
            raise ValueError("STAGE80_BAD_PRICE")


def from_archived_closed_bars(bars: list[tuple], at_ms: int) -> Features:
    """Exactly 61 completed bars ending at at_ms-60s. Future appended bars ignored."""
    prior = [row for row in bars if row[0] < at_ms]
    if len(prior) < 61:
        raise ValueError("STAGE80_INSUFFICIENT_COMPLETE_ASOF_BARS")
    recent = prior[-61:]
    if any(row[0] != at_ms - (61 - i) * MINUTE_MS for i, row in enumerate(recent)):
        raise ValueError("STAGE80_NON_CONTIGUOUS_CLOSED_MINUTE")
    if any(len(row) < 7 for row in recent):
        raise ValueError("STAGE80_INVALID_BAR_FORMAT")
    prices = [decimal(x[4]) for x in recent]
    quotes = [decimal(x[5]) for x in recent]
    trades = [x[6] for x in recent]
    if any(x <= 0 for x in prices) or any(q < 0 for q in quotes) or any(
        not isinstance(t, int) or isinstance(t, bool) or t < 0 for t in trades
    ):
        raise ValueError("STAGE80_CORRUPT_KLINE_VALUES")
    q15 = sum(quotes[-15:])
    q45 = sum(quotes[-60:-15])
    f = Features(
        ret60_pct=(prices[-1] / prices[0] - 1) * 100,
        quote15_usdt=q15, trade15=sum(trades[-15:]),
        quote15_relative45=(q15 * 3 / q45 if q45 else None),
        closed_price=prices[-1],
    )
    f.validate()
    return f


@dataclass(frozen=True)
class WatchState:
    venue: str
    symbol: str
    first_utc: str
    first_price: Decimal | None
    first_d1_utc: str | None = None
    first_d1_path: str | None = None


def gate(features: Features, first: bool, relative_pct: Decimal | None, contract: dict) -> bool:
    cfg = contract["entry_first"] if first else contract["entry_reignition"]
    if features.quote15_relative45 is None:
        return False
    if features.ret60_pct < decimal(cfg["ret60_pct_gte"]):
        return False
    if features.quote15_usdt < decimal(cfg["quote15_usdt_gte"]):
        return False
    if features.trade15 < cfg["trades15_gte"]:
        return False
    if features.quote15_relative45 < decimal(cfg["quote15_normalized_prev45_gte"]):
        return False
    return first or relative_pct is not None and relative_pct >= decimal(cfg["price_relative_first_pct_gte"])


def evaluate(state: WatchState | None, *, venue: str, symbol: str, at_utc: str,
             features: Features | None, is_first_d0: bool, contract: dict,
             relative_first_pct: Decimal | None = None,
             source_ok: bool = True) -> tuple[WatchState | None, str]:
    if not venue or not symbol:
        raise ValueError("STAGE80_IDENTITY_REQUIRED")
    now = utc_ms(at_utc)
    if now % (3 * MINUTE_MS):
        raise ValueError("STAGE80_NOT_ORIGINAL_3MIN_TICK")
    if state is not None and (state.venue != venue or state.symbol != symbol):
        raise ValueError("STAGE80_WRONG_EXISTING_ENTITY")
    if is_first_d0:
        if state is not None:
            raise ValueError("STAGE80_DUPLICATE_FIRST_D0")
        state = WatchState(venue, symbol, at_utc, features.closed_price if features else None)
    elif state is None:
        raise ValueError("STAGE80_UPGRADE_WITHOUT_D0")
    if now < utc_ms(state.first_utc):
        raise ValueError("STAGE80_EVENT_PRECEDES_D0")
    if state.first_d1_utc is not None:
        return state, "ALREADY_UPGRADED_RETAIN_D0"
    if now - utc_ms(state.first_utc) > contract["from_first_d0_expiration_hours"] * 3600_000:
        return state, "EXPIRED_RETAIN_D0"
    if not source_ok or features is None:
        return state, "SOURCE_UNKNOWN_RETAIN_D0"
    features.validate()
    if features.closed_price is not None and state.first_price is not None:
        computed = (features.closed_price / state.first_price - 1) * 100
        if relative_first_pct is not None and abs(computed-relative_first_pct) > Decimal("0.00001"):
            raise ValueError("STAGE80_RELATIVE_PRICE_SOURCE_MISMATCH")
        relative_first_pct = computed
    path = "DIRECT_AT_FIRST_D0" if is_first_d0 else "REIGNITION_AFTER_D0"
    if gate(features, is_first_d0, relative_first_pct, contract):
        return replace(state, first_d1_utc=at_utc, first_d1_path=path), path
    return state, "WATCH_RETAINED"


def selftest() -> None:
    c = load_contract()
    base_ms = utc_ms("2026-10-14T06:00:00Z")
    bars = [(base_ms+(i-70)*MINUTE_MS, Decimal(100), Decimal(101), Decimal(99),
             Decimal(100), Decimal(100_000), 1000) for i in range(70)]
    f = from_archived_closed_bars(bars, base_ms)
    assert f.ret60_pct == 0 and f.trade15 == 15000 and f.quote15_usdt == 1500000
    assert f.quote15_relative45 == 1
    fake = bars + [(base_ms, Decimal(999),Decimal(9999),Decimal(1),Decimal(999),
                   Decimal("1e20"),999999)]
    assert from_archived_closed_bars(fake, base_ms) == f
    bb = list(bars)
    bb[-1] = (bb[-1][0],bb[-1][1],bb[-1][2],bb[-1][3],Decimal(123),bb[-1][5],bb[-1][6])
    assert from_archived_closed_bars(bb, base_ms).closed_price != f.closed_price
    f = Features(Decimal("9"), Decimal("1200000"), 16000, Decimal("1.5"), Decimal("100"))
    s,x = evaluate(None, venue="USDM",symbol="AUSDT",at_utc="2026-10-14T06:00:00Z",
                   features=f,is_first_d0=True,contract=c)
    assert x == "DIRECT_AT_FIRST_D0" and s.first_d1_utc is not None
    s2,x2 = evaluate(s,venue="USDM",symbol="AUSDT",at_utc="2026-10-14T06:03:00Z",
                     features=f,is_first_d0=False,contract=c)
    assert x2 == "ALREADY_UPGRADED_RETAIN_D0" and s2 == s
    below=Features(Decimal("2"), Decimal(100_000), 100, Decimal(1), Decimal("100"))
    s,x=evaluate(None,venue="USDM",symbol="BUSDT",at_utc="2026-10-14T06:00:00Z",
                 features=below,is_first_d0=True,contract=c)
    assert x=="WATCH_RETAINED" and s.first_d1_utc is None
    rev=Features(Decimal("6"),Decimal("1500000"),14000,Decimal("1.6"),Decimal("108"))
    s,x=evaluate(s,venue="USDM",symbol="BUSDT",at_utc="2026-10-14T06:03:00Z",
                 features=rev,is_first_d0=False,contract=c)
    assert x=="REIGNITION_AFTER_D0"
    bad=Features(Decimal(6),Decimal(1400000),12000,Decimal("1.5"),Decimal("110"))
    try:
        evaluate(WatchState("USDM","BUSDT","2026-10-14T06:00:00Z",Decimal(100)),
                 venue="USDM",symbol="BUSDT",at_utc="2026-10-14T06:03:00Z",
                 features=bad,is_first_d0=False,contract=c,relative_first_pct=Decimal(4))
    except ValueError as e:
        assert "RELATIVE_PRICE_SOURCE_MISMATCH" in str(e)
    else:
        raise AssertionError("STAGE80_MUST_REJECT_FALSE_RELATIVE_RETURN")
    print("STAGE80_DUAL_ENTRY_PURE_CAUSAL_SELFTEST_PASS")


if __name__=="__main__":
    selftest()
