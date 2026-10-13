#!/usr/bin/env python3
"""Monster Stage91: read-only future cohort intake and same-core D0/D1 causal replay.

No scheduler, monitoring, Gmail, trading, background process or production mutation.
A hash of user-supplied raw JSON proves byte consistency, NOT exchange authenticity.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

try:
    import monster_v4_stage38_usdm_original_v4_1m_pilot as v4
    import monster_v4_stage80_dual_entry_core as d1
except ImportError:
    from scripts import monster_v4_stage38_usdm_original_v4_1m_pilot as v4
    from scripts import monster_v4_stage80_dual_entry_core as d1

SCHEMA = "MONSTER_STAGE91_FROZEN_FORWARD_USDM_FULL_POPULATION_REPLAY_V1"
WINDOWS = (
    "2026-10-14T06:00:00Z",
    "2026-10-28T06:00:00Z",
    "2026-11-11T06:00:00Z",
)
EXCHANGE_INFO_URL = "https://fapi.binance.com/fapi/v1/exchangeInfo"
WINDOW_MS = 7 * 24 * 3600_000
MIN = 60_000
FRESH_MAX_MS = 15 * MIN
MODEL_SOURCE_V4 = v4.ORIGINAL_V4_GIT_BLOB
D1_SOURCE_CONTRACT = d1.CONTRACT_SHA


def num(x):
    if not isinstance(x, int) or isinstance(x, bool):
        raise ValueError("STAGE91_INT_TIMESTAMP_REQUIRED")
    return x


def sha256_raw(raw: str) -> str:
    if not isinstance(raw, str):
        raise ValueError("STAGE91_EXCHANGE_INFO_RAW_REQUIRED")
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def verify_window(utc: str) -> int:
    if utc not in WINDOWS:
        raise ValueError("STAGE91_NOT_ONE_OF_THE_THREE_FROZEN_FORWARD_DATES")
    return d1.utc_ms(utc)


def freeze_universe(packet: dict) -> dict:
    """Validate only the archived bytes/clock. No claim of live official origin."""
    if not isinstance(packet, dict) or packet.get("schema") != SCHEMA:
        raise ValueError("STAGE91_WRONG_MARKET_SNAPSHOT_SCHEMA")
    start = verify_window(packet.get("window_start_utc"))
    if packet.get("venue") != "BINANCE_USDM" or packet.get("source_url") != EXCHANGE_INFO_URL:
        raise ValueError("STAGE91_WRONG_EXCHANGE_OR_SOURCE_URL")
    cap = num(packet.get("capture_ms"))
    if not start - FRESH_MAX_MS <= cap <= start:
        raise ValueError("STAGE91_UNIVERSE_NOT_CAPTURED_BEFORE_FIXED_START")
    raw = packet.get("raw_exchangeInfo_json")
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError("STAGE91_EMPTY_OFFICIAL_POPULATION")
    if sha256_raw(raw) != packet.get("raw_sha256"):
        raise ValueError("STAGE91_UNIVERSE_RAW_BYTE_TAMPER")
    try:
        payload = json.loads(raw)
    except (ValueError, json.JSONDecodeError):
        raise ValueError("STAGE91_MALFORMED_EXCHANGE_INFO") from None
    if not isinstance(payload, dict) or not isinstance(payload.get("symbols"), list):
        raise ValueError("STAGE91_EXCHANGE_INFO_MISSING_SYMBOLS")
    if not payload["symbols"]:
        raise ValueError("STAGE91_EMPTY_MARKET_POPULATION")
    # Binance's USD-M exchangeInfo official docs explicitly say to IGNORE its
    # serverTime for clock verification; use a separately fetched /fapi/v1/time
    # HTTP body in the Stage97 authenticated capture validator instead.
    server_time = payload.get("serverTime")
    if server_time is not None:
        num(server_time)
    seen, rows = set(), []
    for item in payload["symbols"]:
        if not isinstance(item, dict):
            raise ValueError("STAGE91_NONOBJECT_MARKET_ROW")
        symbol = item.get("symbol")
        # USD-M exchangeInfo can include dated delivery contracts with "_".
        # Preserve *all* contracts in the population and choose PERPETUAL
        # separately. Do not use Unicode isalnum() as a venue symbol validator.
        if (not isinstance(symbol, str)
            or not re.fullmatch(r"[A-Z0-9]+(?:_[A-Z0-9]+)*",symbol)
            or symbol in seen):
            raise ValueError("STAGE91_MARKET_SYMBOL_DUPLICATE_OR_INVALID")
        seen.add(symbol)
        status = item.get("status")
        contract_type = item.get("contractType")
        quote_asset = item.get("quoteAsset")
        base_asset = item.get("baseAsset")
        if (not isinstance(status,str) or not status
            or not isinstance(contract_type,str) or not contract_type
            or not isinstance(quote_asset,str) or not quote_asset
            or not isinstance(base_asset,str) or not base_asset):
            raise ValueError("STAGE91_INCOMPLETE_OFFICIAL_MARKET_ROW")
        onboard = item.get("onboardDate")
        if onboard is not None:
            num(onboard)
        active_at_capture = (
            status == "TRADING" and contract_type == "PERPETUAL"
            and quote_asset == "USDT" and bool(base_asset)
            and (onboard is None or onboard <= cap)
        )
        rows.append({
            "symbol": symbol, "status_asof_capture": status,
            "contract_type":contract_type, "quote_asset":quote_asset,
            "base_asset":base_asset,
            "onboard_ms":onboard,
            "candidate_for_raw_USDM_attempt":active_at_capture,
            "crypto_identity":"UNKNOWN_NEEDS_INDEPENDENT_PROOF",
            "mapping":"UNKNOWN_UNTIL_INDEPENDENT_UNITS_VERIFIED",
        })
    candidates=[x for x in rows if x["candidate_for_raw_USDM_attempt"]]
    if not candidates:
        raise ValueError("STAGE91_NO_USDT_PERPETUAL_IN_UNIVERSE")
    return {
        "schema":SCHEMA,
        "window_start_utc":packet["window_start_utc"],
        "window_end_utc":v4.stamp(start+WINDOW_MS),
        "raw_sha256":packet["raw_sha256"],
        "capture_ms":cap,
        "population_all_exchange_symbols":len(rows),
        "usd_m_usdt_perpetual_asof_candidates":len(candidates),
        "rows":rows,
        "market_population_archive_consistency":"PASS_UNTRUSTED_ORIGIN",
        "source_authenticity":"UNVERIFIED_EXTERNAL_CAPTURE",
        "exchangeInfo_serverTime_clock_authority":"NONE_OFFICIAL_DOCS_SAY_IGNORE",
        "historical_or_forward_replay":"NOT_RUN",
        "G0_point_in_time_crypto_only":"NOT_DONE",
        "OOS":"NOT_DONE",
        "Gmail":"OFF","Monster_deployment":"NO_GO",
    }


def source_ready(symbol: str, start_utc: str, bars: list, receipts: list) -> bool:
    anchor=verify_window(start_utc)
    if len(bars)!=v4.BARS or len(receipts)!=9:
        raise ValueError("STAGE91_NINE_DAYS_OFFICIAL_SOURCE_REQUIRED")
    base=anchor - 24*3600_000
    if any(row[0]!=base+i*MIN or len(row)!=7 for i,row in enumerate(bars)):
        raise ValueError("STAGE91_NONCAUSAL_OR_INCOMPLETE_SOURCE_MINUTES")
    expected=[(date.fromisoformat(start_utc[:10]).toordinal()+n) for n in range(-1,8)]
    got=[date.fromisoformat(p["date"]).toordinal() for p in receipts]
    if got!=expected:
        raise ValueError("STAGE91_WRONG_NINE_OFFICIAL_CALENDAR_DATES")
    if any(not p.get("verified_official_publisher_SHA256")
           or not isinstance(p.get("zip_sha256"),str)
           or len(p["zip_sha256"])!=64 or
           not all(ch in "0123456789abcdef" for ch in p["zip_sha256"])
           or p.get("bars")!=1440 for p in receipts):
        raise ValueError("STAGE91_PUBLISHER_SHA_RECEIPTS_NOT_VERIFIED")
    if not symbol or not symbol.endswith("USDT"):
        raise ValueError("STAGE91_USDM_SYMBOL_REQUIRED")
    return True


def early5(event: int | None, high: int | None) -> bool:
    return event is not None and high is not None and event + 5*MIN <= high


def first_cross(bars: list, multiplier: int) -> int | None:
    if multiplier not in (2,5,10):
        raise ValueError("STAGE91_BAD_LABEL_MULTIPLE")
    # This future label is only calculated after a complete 168h archive exists.
    anchor=bars[v4.WARMUP][1]
    return next((x[0] for x in bars[v4.WARMUP:v4.WARMUP+v4.ACTIVE]
                 if x[2]>=anchor*multiplier),None)


def replay_raw_symbol(symbol: str, start_utc: str, bars: list, receipts: list,
                      *, runner=v4.production_scan,
                      d1_core=d1.evaluate) -> dict:
    """Original V4 first WATCH + frozen Stage79 D1 exactly every 3m, all normal cases."""
    source_ready(symbol,start_utc,bars,receipts)
    if v4.blob(v4.production.__file__) != v4.ORIGINAL_V4_GIT_BLOB:
        raise ValueError("STAGE91_ORIGINAL_D0_PRODUCTION_BLOB_NOT_LOCKED")
    d1.load_contract()
    anchor=verify_window(start_utc)
    scan=runner(symbol,start_utc,bars)
    if scan["polls"]!=3360:
        raise ValueError("STAGE91_NOT_ORIGINAL_3M_SCANNING_SCHEDULE")
    watch_times=[d1.utc_ms(x) for x in scan["WATCH_UTC"]]
    if (len(watch_times)!=scan["watch_count"]
        or watch_times != sorted(set(watch_times))
        or any(w<anchor or w>=anchor+WINDOW_MS or w%(3*MIN)!=0
               for w in watch_times)):
        raise ValueError("STAGE91_INVALID_ORIGINAL_D0_WATCH_CLOCK")
    first_d0=watch_times[0] if watch_times else None
    first_d1=None
    first_d1_path=None
    if first_d0 is not None:
        contract=d1.load_contract()
        expiry=min(first_d0+contract["from_first_d0_expiration_hours"]*3600_000,
                   anchor+WINDOW_MS)
        state=None
        t=first_d0
        while t<expiry:
            i=(t-bars[0][0])//MIN
            f=d1.from_archived_closed_bars(bars[i-61:i],t)
            state, outcome=d1_core(
                state, venue="USDM",symbol=symbol,at_utc=v4.stamp(t),
                features=f,is_first_d0=(t==first_d0),contract=contract)
            if outcome in ("DIRECT_AT_FIRST_D0","REIGNITION_AFTER_D0"):
                first_d1=t
                first_d1_path=outcome
                break
            t+=3*MIN
        if state is None or d1.utc_ms(state.first_utc)!=first_d0:
            raise ValueError("STAGE91_D0_LOST_IN_D1")
    cross={n:first_cross(bars,n) for n in (2,5,10)}
    score={}
    for n in (2,5,10):
        tc=cross[n]
        score[f"first_GT{n}x_HIGH_UTC_EVALUATION_ONLY"]=v4.stamp(tc) if tc is not None else None
        score[f"D0_first_pre_GT{n}x_strict"]=first_d0 is not None and tc is not None and first_d0<tc
        score[f"D0_first_pre_GT{n}x_5m"]=early5(first_d0,tc)
        score[f"D1_first_pre_GT{n}x_5m"]=early5(first_d1,tc)
    return {
        "date":start_utc[:10], "symbol":symbol, "venue":"BINANCE_USDM",
        "source_status":"COMPLETE_REAL_1M_PUBLISHER_SHA_MODEL_REPLAY",
        "observed_windows":3360, "D0_WATCH_COUNT":len(watch_times),
        "D0_first_UTC":v4.stamp(first_d0) if first_d0 is not None else None,
        "D1_first_UTC":v4.stamp(first_d1) if first_d1 is not None else None,
        "D1_entry_path":first_d1_path,
        "source_9_days_SHA256":receipts,
        "Crypto_identity":"UNKNOWN_NEEDS_INDEPENDENT_ASOF_PROOF",
        "D2_execution":"UNKNOWN",
        "gross_future_labels_not_real_profit":score,
        "true_independent_OOS":"PENDING_POPULATION_AND_COMPLETE_DATES",
    }


def gate_cohort(window_groups: dict[str,list[dict]], frozen_universes: dict):
    """Summary never passes when venue, population, crypto identity or OOS are unknown."""
    if set(window_groups)!=set(WINDOWS):
        return {"OOS":"BLOCKED_MISSING_FIXED_WINDOW",
                "missing":[d for d in WINDOWS if d not in window_groups]}
    rows=[]
    for win in WINDOWS:
        universe=frozen_universes.get(win)
        if not universe or universe.get("source_authenticity")!="ATTESTED_OFFICIAL_CAPTURE":
            return {"OOS":"BLOCKED_POINT_IN_TIME_POPULATION_NOT_AUTHENTICATED",
                    "window":win}
        eligible={r["symbol"] for r in universe["rows"] if r["candidate_for_raw_USDM_attempt"]}
        actual=[r["symbol"] for r in window_groups[win]]
        if len(actual)!=len(set(actual)) or set(actual)!=eligible:
            return {"OOS":"BLOCKED_MISSING_OR_EXTRA_SYMBOL_ATTEMPTS","window":win}
        rows+=window_groups[win]
    if any(x["source_status"]!="COMPLETE_REAL_1M_PUBLISHER_SHA_MODEL_REPLAY"
           for x in rows):
        return {"OOS":"BLOCKED_CENSORED_OR_UNVERIFIED_SOURCE"}
    # The raw venue census retains verified out-of-scope securities and
    # non-crypto rows for audit. Score only certified Crypto; unknown is blocked.
    recognized={"VERIFIED_CRYPTO_ASOF","CONFIRMED_NONCRYPTO_OUT_OF_SCOPE"}
    if any(x["Crypto_identity"] not in recognized for x in rows):
        return {"OOS":"BLOCKED_CRYPTO_IDENTITY_NOT_VERIFIED"}
    if any(x["D2_execution"]!="VERIFIED_2_SIDED_REAL_FILLS" for x in rows):
        return {"OOS":"BLOCKED_EXECUTION_EVIDENCE_INCOMPLETE"}
    # This is still not a full scoring engine; refuse to invent forward-pass stats
    # without separately pinned review of D0/G1/G2/G3.
    return {"OOS":"BLOCKED_G1_G2_G3_FULL_METRIC_SCORING_NOT_IMPLEMENTED"}


def selftest():
    assert len(WINDOWS)==3 and len(set(WINDOWS))==3
    t=verify_window(WINDOWS[0])
    raw=json.dumps({"serverTime":t-2000,"symbols":[
      {"symbol":"CATUSDT","status":"TRADING","contractType":"PERPETUAL",
       "quoteAsset":"USDT","baseAsset":"CAT","onboardDate":t-3600_000},
      {"symbol":"LRCXUSDT","status":"TRADING","contractType":"PERPETUAL",
       "quoteAsset":"USDT","baseAsset":"LRCX","onboardDate":t-3600_000},
      {"symbol":"OLDUSDT","status":"BREAK","contractType":"PERPETUAL",
       "quoteAsset":"USDT","baseAsset":"OLD","onboardDate":t-3600_000},
    ]},separators=(",",":"))
    template={"schema":SCHEMA,"window_start_utc":WINDOWS[0],
              "venue":"BINANCE_USDM","source_url":EXCHANGE_INFO_URL,
              "capture_ms":t-1000,"raw_exchangeInfo_json":raw,"raw_sha256":sha256_raw(raw)}
    result=freeze_universe(template)
    assert result["population_all_exchange_symbols"]==3
    assert result["usd_m_usdt_perpetual_asof_candidates"]==2
    assert result["rows"][1]["crypto_identity"].startswith("UNKNOWN")
    # Real Binance exchangeInfo.serverTime may be stale by design.
    stale_server=json.dumps({"serverTime":t-86_400_000,
         "symbols":json.loads(raw)["symbols"]},separators=(",",":"))
    dated=dict(template,raw_exchangeInfo_json=stale_server,
               raw_sha256=sha256_raw(stale_server))
    assert freeze_universe(dated)["source_authenticity"]=="UNVERIFIED_EXTERNAL_CAPTURE"
    assert result["OOS"]=="NOT_DONE"
    changed=dict(template,window_start_utc="2025-01-30T06:00:00Z")
    try:freeze_universe(changed)
    except ValueError as e: assert "NOT_ONE_OF" in str(e)
    else:raise AssertionError("STAGE91_MUST_REJECT_EXPOSED_2025_DATE")
    future=dict(template,capture_ms=t+1000)
    try:freeze_universe(future)
    except ValueError as e: assert "NOT_CAPTURED_BEFORE" in str(e)
    else:raise AssertionError("STAGE91_MUST_REJECT_FUTURE_EXCHANGEINFO")
    tamper=dict(template,raw_response="wrong",raw_exchangeInfo_json=raw+" ")
    try:freeze_universe(tamper)
    except ValueError as e: assert "TAMPER" in str(e)
    else:raise AssertionError("STAGE91_MUST_REJECT_RAW_JSON_TAMPERING")
    dup=json.dumps({"symbols":[json.loads(raw)["symbols"][0],
                                json.loads(raw)["symbols"][0]]})
    try:freeze_universe(dict(template,raw_exchangeInfo_json=dup,raw_sha256=sha256_raw(dup)))
    except ValueError as e: assert "DUPLICATE" in str(e)
    else:raise AssertionError("STAGE91_MUST_REJECT_DUPLICATE_SYMBOL")
    # A dated delivery contract is retained in the census, never a perp candidate.
    dated_delivery=dict(json.loads(raw)["symbols"][0])
    dated_delivery.update(symbol="BTCUSDT_261225",
                          baseAsset="BTC",contractType="CURRENT_QUARTER")
    mix=json.dumps({"symbols":json.loads(raw)["symbols"]+[dated_delivery]})
    asof=freeze_universe(dict(template,raw_exchangeInfo_json=mix,raw_sha256=sha256_raw(mix)))
    assert asof["population_all_exchange_symbols"]==4
    assert asof["usd_m_usdt_perpetual_asof_candidates"]==2
    assert asof["rows"][-1]["candidate_for_raw_USDM_attempt"] is False
    incomplete=dict(json.loads(raw)["symbols"][0])
    del incomplete["status"]
    wrong=json.dumps({"symbols":[incomplete]})
    try:freeze_universe(dict(template,raw_exchangeInfo_json=wrong,raw_sha256=sha256_raw(wrong)))
    except ValueError as e:assert "INCOMPLETE_OFFICIAL" in str(e)
    else:raise AssertionError("STAGE103_INCOMPLETE_MARKET_ROW_MUST_FAIL")
    assert gate_cohort({}, {})["OOS"]=="BLOCKED_MISSING_FIXED_WINDOW"
    assert gate_cohort({x:[] for x in WINDOWS},{})["OOS"]=="BLOCKED_POINT_IN_TIME_POPULATION_NOT_AUTHENTICATED"
    assert early5(t,t+5*MIN) and not early5(t,t+4*MIN)
    assert not early5(None,t+8*MIN)
    assert MODEL_SOURCE_V4 and D1_SOURCE_CONTRACT
    assert v4.blob(v4.production.__file__)==v4.ORIGINAL_V4_GIT_BLOB
    from decimal import Decimal
    zero=Decimal("100")
    anchor=verify_window(WINDOWS[0])
    begin=anchor-24*3600_000
    ticks=[]
    for i in range(v4.BARS):
        q=Decimal("100000") if v4.WARMUP-12<=i<=v4.WARMUP+2 else Decimal("60000")
        close=Decimal("110") if v4.WARMUP-12<=i<=v4.WARMUP+2 else zero
        high=Decimal("210") if i==v4.WARMUP+300 else max(zero,close)
        ticks.append((begin+i*MIN,zero,high,zero,close,q,1000))
    receipts=[
        {"date":date.fromordinal(date.fromisoformat(WINDOWS[0][:10]).toordinal()+n).isoformat(),
         "zip_sha256":"a"*64,"verified_official_publisher_SHA256":True,"bars":1440}
        for n in range(-1,8)
    ]
    first=v4.stamp(anchor+3*MIN)
    def fake_original_scanner(_symbol,_date,_bars):
        return {"polls":3360,"WATCH_UTC":[first],"watch_count":1}
    score1=replay_raw_symbol("CATUSDT",WINDOWS[0],ticks,receipts,
                             runner=fake_original_scanner)
    assert score1["D0_first_UTC"]==first
    assert score1["D1_first_UTC"]==first
    assert score1["D1_entry_path"]=="DIRECT_AT_FIRST_D0"
    assert score1["gross_future_labels_not_real_profit"]["D0_first_pre_GT2x_5m"]
    future=list(ticks)
    future[v4.WARMUP+300]=(future[v4.WARMUP+300][0],
                             zero,zero,zero,zero,Decimal("60000"),1000)
    future[v4.WARMUP+400]=(future[v4.WARMUP+400][0],
                             zero,Decimal("210"),zero,zero,Decimal("60000"),1000)
    score2=replay_raw_symbol("CATUSDT",WINDOWS[0],future,receipts,
                             runner=fake_original_scanner)
    assert score2["D1_first_UTC"]==score1["D1_first_UTC"]
    assert (score2["gross_future_labels_not_real_profit"]["first_GT2x_HIGH_UTC_EVALUATION_ONLY"]
            !=score1["gross_future_labels_not_real_profit"]["first_GT2x_HIGH_UTC_EVALUATION_ONLY"])
    print("STAGE91_FROZEN_POPULATION_AND_SYNTHETIC_SAME_CORE_CAUSAL_REPLAY_SELFTEST_PASS")


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--selftest",action="store_true")
    parser.add_argument("--validate-market-packet",type=Path)
    parser.add_argument("--out",type=Path)
    args=parser.parse_args()
    if args.selftest:
        selftest()
        return
    if args.validate_market_packet:
        packet=json.loads(args.validate_market_packet.read_text(encoding="utf-8"))
        data=freeze_universe(packet)
        content=json.dumps(data,ensure_ascii=False,sort_keys=True,indent=2)+"\n"
        if args.out:
            args.out.parent.mkdir(parents=True,exist_ok=True)
            args.out.write_text(content,encoding="utf-8")
        print("STAGE91_MARKET_PACKET_INTEGRITY_ONLY "+json.dumps(
            {k:data[k] for k in ("window_start_utc","population_all_exchange_symbols",
                 "usd_m_usdt_perpetual_asof_candidates","source_authenticity","OOS")},
             ensure_ascii=False,sort_keys=True))
        return
    parser.error("no action: supply --selftest or --validate-market-packet")


if __name__=="__main__":
    main()
