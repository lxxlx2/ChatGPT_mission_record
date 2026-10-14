#!/usr/bin/env python3
"""Stage132 offline Stage130 publisher-verified 31 first-signal price-path proxy.

No buy recommendation, point-in-time crypto issuer proof, fill, fee, slippage,
live request, monitoring, order, Gmail or deployment.
"""
from __future__ import annotations
import argparse
import csv
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import io
import json
from pathlib import Path
import statistics
import zipfile

SOURCE_SHA = "a97037bff9d834f0f59fb3a0ae45942a9c28453dbfc0d01331fd78afa49b8f50"
HORIZONS = (15, 60, 360, 1440)
MIN = 60000
SCHEMA = "MONSTER_STAGE132_ARCHIVED31_DELAYED_ENTRY_FIXED_OPEN_PRICE_V1"


def epoch(iso):
    if not isinstance(iso, str) or not iso.endswith("Z"):
        raise ValueError("STAGE132_NOT_UTC_TIMESTAMP")
    return int(datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp() * 1000)


def utc(ms):
    return datetime.fromtimestamp(ms/1000, timezone.utc).isoformat().replace("+00:00", "Z")


def positive(v):
    x = Decimal(str(v))
    if not x.is_finite() or x <= 0:
        raise ValueError("STAGE132_INVALID_SOURCE_PRICE")
    return x


def paths(bars, first_signal):
    """At t+1m enter unfilled OPEN proxy, later exit unfilled OPEN at t+1m+h."""
    if not bars or any(bars[i][0]-bars[i-1][0] != MIN for i in range(1, len(bars))):
        raise ValueError("STAGE132_SOURCE_MINUTES_GAPPED")
    times = {b[0]: i for i, b in enumerate(bars)}
    entry = epoch(first_signal) + MIN
    if entry not in times:
        return {"status": "RIGHT_CENSORED_ENTRY",
                "horizons": {str(h): {"status": "RIGHT_CENSORED_SOURCE_END"} for h in HORIZONS}}
    start = times[entry]
    price = positive(bars[start][1])
    outcomes = {}
    for h in HORIZONS:
        exit_at = entry + h*MIN
        if exit_at not in times:
            outcomes[str(h)] = {"status": "RIGHT_CENSORED_SOURCE_END", "exit_utc": utc(exit_at)}
            continue
        last = times[exit_at]
        if last - start != h:
            raise ValueError("STAGE132_EXIT_HORIZON_NOT_CONTIGUOUS")
        series = bars[start:last]
        if not series:
            raise ValueError("STAGE132_EMPTY_ENTRY_TO_EXIT_PATH")
        low = min(x[3] for x in series)
        high = max(x[2] for x in series)
        exit_open = positive(bars[last][1])
        pct = lambda v: str((v/price-1)*100)
        outcomes[str(h)] = {"status": "VALID_GROSS_OPEN_TO_OPEN_PRICE_ONLY",
                            "exit_utc": utc(exit_at), "exit_open": str(exit_open),
                            "gross_return_pct": pct(exit_open),
                            "MAE_low_pct": pct(low), "MFE_high_pct": pct(high)}
    return {"status": "UNFILLED_ENTRY_OPEN_PROXY", "entry_utc": utc(entry),
            "entry_open": str(price), "horizons": outcomes}


def load_case(root, case):
    symbol = case["symbol"]
    bars = []
    for receipt in case["official_publisher_SHA256_daily_receipts"]:
        day = receipt["day"]
        prefix = root / "stage130_original_daily_zip_source" / symbol
        file = prefix / (day+".zip")
        raw = file.read_bytes()
        checksum = (prefix/(day+".zip.CHECKSUM")).read_text(encoding="ascii").split()[0].lower()
        digest = hashlib.sha256(raw).hexdigest()
        if (digest != checksum or digest != receipt["zip_sha256"] or
                receipt.get("publisher_sha256_verified") is not True):
            raise ValueError("STAGE132_PUBLISHER_SHA_OR_RECEIPT_CHANGED")
        name = f"{symbol}-1m-{day}.csv"
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            if z.namelist() != [name]:
                raise ValueError("STAGE132_WRONG_CSV_MEMBER")
            text = z.read(name).decode("utf-8-sig")
        daily = []
        for row in csv.reader(io.StringIO(text)):
            if row and row[0].strip().lower() in ("open_time", "open time", "opentime"):
                continue
            if len(row) < 9:
                raise ValueError("STAGE132_WRONG_PUBLISHER_BAR_COLS")
            raw_stamp = int(row[0])
            if raw_stamp >= 10**15:
                if raw_stamp % 1000:
                    raise ValueError("STAGE132_BAD_MICROSECOND_EPOCH")
                raw_stamp //= 1000
            if raw_stamp < 10**12 or raw_stamp % MIN:
                raise ValueError("STAGE132_BAD_MINUTE_EPOCH")
            op, hi, lo, cl = (positive(row[k]) for k in (1, 2, 3, 4))
            if hi < max(op, cl) or lo > min(op, cl):
                raise ValueError("STAGE132_INVALID_PUBLISHER_OHLC")
            daily.append((raw_stamp, op, hi, lo, cl))
        if len(daily) != receipt["bars"]:
            raise ValueError("STAGE132_PUBLISHER_DAILY_BARS_DRIFT")
        bars.extend(daily)
    start = epoch(case["anchor"]+"T06:00:00Z")
    end = start + 7*24*60*MIN
    bars = [r for r in bars if start <= r[0] < end]
    if len(bars) != case["minute_rows"]:
        raise ValueError("STAGE132_FULL_CASE_MINUTES_DRIFT")
    if any(bars[i][0]-bars[i-1][0] != MIN for i in range(1, len(bars))):
        raise ValueError("STAGE132_SOURCE_MINUTES_GAPPED")
    if (not bars or utc(bars[0][0]) != case["frozen_listing_first_observed_1m_open_utc"]
        or bars[0][1] != positive(case["first_1m_open"])):
        raise ValueError("STAGE132_FIRST_ORIGINAL_LISTING_MINUTE_DRIFT")
    return bars


def summarize(rows):
    result = {}
    for h in HORIZONS:
        checks = [x["post_signal_price_proxy"]["horizons"][str(h)] for x in rows if x["has_first_momentum"]]
        valid = [x for x in checks if x["status"] == "VALID_GROSS_OPEN_TO_OPEN_PRICE_ONLY"]
        vals = sorted(Decimal(x["gross_return_pct"]) for x in valid)
        maes = [Decimal(x["MAE_low_pct"]) for x in valid]
        info = {"valid": len(valid), "right_censored": len(checks)-len(valid),
                "no_signal": len(rows)-len(checks)}
        if vals:
            info.update({
                "positive": sum(v>0 for v in vals),
                "negative": sum(v<0 for v in vals),
                "flat": sum(v==0 for v in vals),
                "mean_pct": str(sum(vals)/len(vals)),
                "median_pct": str(statistics.median(vals)),
                "p25_pct": str(vals[(len(vals)-1)//4]),
                "p75_pct": str(vals[3*(len(vals)-1)//4]),
                "minimum_gross_pct": str(min(vals)),
                "max_gross_pct": str(max(vals)),
                "worst_MAE_pct": str(min(maes)),
            })
        result[str(h)] = info
    return result


def audit(source_root):
    root = Path(source_root)
    raw = (root/"stage130_real31.json").read_bytes()
    if hashlib.sha256(raw).hexdigest() != SOURCE_SHA:
        raise ValueError("STAGE132_FROZEN_ORIGINAL_STAGE130_JSON_CHANGED")
    stage130 = json.loads(raw)
    original = stage130.get("full31_source_results")
    if (not isinstance(original, list) or len(original) != 31
        or stage130.get("source_complete") != 31
        or stage130.get("research_momentum_first_triggers") != 19):
        raise ValueError("STAGE132_FROZEN_STAGE130_POPULATION_DRIFT")
    rows = []
    seen = set()
    for case in sorted(original, key=lambda x:(x["anchor"],x["symbol"])):
        key = (case["anchor"], case["symbol"])
        if key in seen:
            raise ValueError("STAGE132_DUPLICATE_CASE")
        seen.add(key)
        original_bars = load_case(root, case)
        signal = case["new_listing_research_momentum_first_utc"]
        if signal and (epoch(signal) < original_bars[0][0]+MIN or
                       epoch(signal) > original_bars[-1][0]+MIN):
            raise ValueError("STAGE132_SIGNAL_NOT_ORIGINALLY_OBSERVABLE")
        rows.append({
            "anchor":case["anchor"], "symbol":case["symbol"],
            "has_first_momentum":bool(signal), "first_signal_utc":signal,
            "historical_2x_high_posthoc":case["gross_first1m_2x_case_evaluation_only"],
            "minute_bars":len(original_bars),
            "source_publisher_zips":len(case["official_publisher_SHA256_daily_receipts"]),
            "issuer_point_in_time_verified":False,
            "actual_bid_ask_fills_fee_net":"UNKNOWN",
            "post_signal_price_proxy":paths(original_bars, signal) if signal else {
                "status":"NO_RESEARCH_FIRST_MOMENTUM_SIGNAL",
                "horizons":{str(h):{"status":"NO_SIGNAL"} for h in HORIZONS}},
        })
    if (sum(v["minute_bars"] for v in rows) != 159675
        or sum(v["source_publisher_zips"] for v in rows) != 147
        or sum(v["has_first_momentum"] for v in rows) != 19
        or sum(v["historical_2x_high_posthoc"] for v in rows) != 2):
        raise ValueError("STAGE132_ORIGINAL31_FULL_SOURCE_COUNTS_DRIFT")
    return {
        "schema":SCHEMA, "source_stage130_json_sha256":SOURCE_SHA,
        "full_original_attempts":31, "first_unique_momentum_signals":19,
        "no_momentum_signal_attempts":12,
        "frozen_stage130_publisher_zip_pairs_verified":147,
        "full_minute_bars_verified":159675,
        "historical_exposed_gross_2x_cases":2,
        "signal_emit_to_entry_proxy_delay_minutes":1,
        "assumptions":"UNFILLED_ENTRY_OPEN_T_PLUS_1M; EXIT_OPEN_AT_FIXED_HORIZON; ZERO_FEES_SPREAD_SLIPPAGE_EXECUTION",
        "horizon_stats":summarize(rows),
        "all_original_31_rows":rows,
        "G0":"PARTIAL", "G1_new_OOS":"NOT_SCORABLE", "G2_G3":"NOT_PASSED",
        "G4_actual_executable_net":"UNKNOWN", "Monster_deployment":"NO_GO",
        "independent_other_AI_review":"NOT_DONE", "Frank":"UNCHANGED",
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source-root",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    result=audit(a.source_root)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k!="all_original_31_rows"},ensure_ascii=False,sort_keys=True))


if __name__=="__main__":
    main()
