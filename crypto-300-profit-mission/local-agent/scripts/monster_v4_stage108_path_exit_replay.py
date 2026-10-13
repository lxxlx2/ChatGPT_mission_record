#!/usr/bin/env python3
"""Stage108: frozen dual-entry path-specific exit research on exact 305 original D1.

NO live feeds, trading, notifications, orders, launchd or Frank access.
Outcomes are observed historical OHLC *price proxies*, NOT actual fills/net PnL.
The 12h/24h rule was preregistered before this program was added to Git.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
import statistics

BASE = Path(__file__).resolve().parents[2]
SOURCE = (BASE / "monster" / "evidence" /
          "monster_stage101_all305_real1m_historic_exit_paths.jsonl")
PIN_BLOB = "19dfc89ab10aaf23f068bee924cddc85d5bcc3e1"
DATE_SET = (
    "2025-01-30", "2025-06-02", "2025-08-01",
    "2025-10-02", "2026-06-21", "2026-07-28",
)
DIRECT = "DIRECT_AT_FIRST_D0"
REIGNITION = "REIGNITION_AFTER_D0"
SCHEMA = "MONSTER_STAGE108_D1_DUAL_ENTRY_PATH_EXIT_305_PRICE_ONLY_V1"
CANDIDATE = "DIRECT_24H_REIGNITION_12H"
BENCHMARK = "ALL_24H"
CONTROL = "ALL_12H"
DAY_MS = 86400000
FEE_BPS_PER_SIDE = (20, 100)


def git_blob(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\x00" + raw).hexdigest()


def decimal(value) -> Decimal:
    if isinstance(value, bool) or value is None:
        raise ValueError("STAGE108_MISSING_NUMERIC_SOURCE")
    try:
        v = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError("STAGE108_BAD_DECIMAL") from None
    if not v.is_finite():
        raise ValueError("STAGE108_NONFINITE_DECIMAL")
    return v


def read_rows(path: Path = SOURCE) -> list[dict]:
    raw = path.read_bytes()
    if git_blob(raw) != PIN_BLOB:
        raise ValueError("STAGE108_SOURCE_305_GIT_BLOB_CHANGED")
    rows = [json.loads(s) for s in raw.splitlines() if s.strip()]
    if len(rows) != 305:
        raise ValueError("STAGE108_305_FROZEN_ROWS_MISSING")
    keys = [(x["date"], x["symbol"]) for x in rows]
    if len(set(keys)) != 305:
        raise ValueError("STAGE108_REPEATED_COIN_DATE")
    if set(x["date"] for x in rows) != set(DATE_SET):
        raise ValueError("STAGE108_SOURCE_DATES_CHANGED")
    types = Counter(x["D1_PATH"] for x in rows)
    if types != {DIRECT: 164, REIGNITION: 141}:
        raise ValueError("STAGE108_FROZEN_TWO_PATH_CENSUS_MISMATCH")
    if sum(x["original_major_2x_early5_EVAL_ONLY"] for x in rows) != 27:
        raise ValueError("STAGE108_MAJOR_2X_EARLY_CENSUS_CHANGED")
    for x in rows:
        d = datetime.fromisoformat(x["D1_FIRST_UTC"].replace("Z", "+00:00"))
        start = datetime.fromisoformat(x["date"] + "T06:00:00+00:00")
        if d.tzinfo is None or not start <= d < start.replace(
                year=start.year) + __import__("datetime").timedelta(days=7):
            raise ValueError("STAGE108_OUTSIDE_FROZEN_SEVEN_DAYS")
        if x["original_fixed_24h"].get("elapsed_minutes") != 1440:
            raise ValueError("STAGE108_BASELINE_EXIT_NOT_24H")
        if x["fixed_12h_price_exit"].get("elapsed_minutes") != 720:
            raise ValueError("STAGE108_PATH_EXIT_NOT_12H")
        if x["original_fixed_72h"].get("elapsed_minutes") != 4320:
            raise ValueError("STAGE108_FUTURE_TAIL_DATA_MISSING")
        if decimal(x["entry_price_proxy"]) <= 0:
            raise ValueError("STAGE108_INVALID_DELAYED_ENTRY")
        if not x["verified_official_publisher_1m_sha"] or not all(
            v["verified_official_publisher_SHA256"]
            for v in x["verified_official_publisher_1m_sha"]
        ):
            raise ValueError("STAGE108_PUBLISHER_SHA_NOT_VERIFIED")
        for field in ("original_fixed_24h", "fixed_12h_price_exit",
                      "original_fixed_72h"):
            v = x[field]
            p = decimal(v["exit_price"])
            if p <= 0:
                raise ValueError("STAGE108_INVALID_EXIT_PRICE")
            gross = (p / decimal(x["entry_price_proxy"]) - 1) * 100
            if abs(gross - decimal(v["gross_price_return_pct"])) > Decimal("1e-18"):
                raise ValueError("STAGE108_FROZEN_REAL_1M_EXIT_PCT_MISMATCH")
    return sorted(rows, key=lambda x: (x["date"], x["D1_FIRST_UTC"], x["symbol"]))


def policy(r: dict, strategy: str) -> tuple[Decimal, int]:
    if strategy == BENCHMARK:
        return decimal(r["original_fixed_24h"]["gross_price_return_pct"]), 1440
    if strategy == CONTROL:
        return decimal(r["fixed_12h_price_exit"]["gross_price_return_pct"]), 720
    if strategy == CANDIDATE:
        key = ("fixed_12h_price_exit" if r["D1_PATH"] == REIGNITION
               else "original_fixed_24h")
        return decimal(r[key]["gross_price_return_pct"]), (720 if key == "fixed_12h_price_exit" else 1440)
    raise ValueError("STAGE108_POLICY_MUST_BE_PREREGISTERED")


def fee_scenario(gross: Decimal, each_side_bps: int) -> Decimal:
    f = Decimal(each_side_bps) / Decimal(10000)
    return ((1 + gross / 100) * (1-f)/(1+f) - 1)*100


def summarize(rows: list[dict], strategy: str) -> dict:
    returns = [policy(r, strategy)[0] for r in rows]
    result = {
        "n": len(returns),
        "median_gross_pct": str(statistics.median(returns)) if returns else None,
        "gross_positive": sum(v>0 for v in returns),
        "gross_gain_ge50": sum(v>=50 for v in returns),
        "gross_gain_ge100": sum(v>=100 for v in returns),
        "gross_loss_le_minus20": sum(v<=-20 for v in returns),
        "major2x_early5_eval_only": sum(r["original_major_2x_early5_EVAL_ONLY"] for r in rows),
        "mean_gross_pct_not_portfolio": str(sum(returns)/len(returns)) if returns else None,
    }
    for fee in FEE_BPS_PER_SIDE:
        scenario = [fee_scenario(v, fee) for v in returns]
        result[f"assumed_{fee}bps_each_side_median_pct_PRICE_ONLY"] = (
            str(statistics.median(scenario)) if scenario else None)
        result[f"assumed_{fee}bps_each_side_gross_after_assumptions_positive"] = (
            sum(v>0 for v in scenario))
    return result


def daily_load(rows: list[dict]) -> dict:
    bins = Counter()
    for r in rows:
        start = datetime.fromisoformat(r["date"]+"T06:00:00+00:00")
        at = datetime.fromisoformat(r["D1_FIRST_UTC"].replace("Z","+00:00"))
        day = int((at-start).total_seconds())//86400
        if day not in range(7):
            raise ValueError("STAGE108_INVALID_UTC06_DAY")
        bins[(r["date"], day)] += 1
    full = [{"date":date, "day_index_utc06":i, "d1_count":bins[(date,i)]}
            for date in DATE_SET for i in range(7)]
    return {
        "all_original_D1_untouched":len(rows),
        "complete_utc06_days":len(full),
        "mean_original_D1_per_day":str(Decimal(len(rows))/len(full)),
        "peak_original_D1_per_day":max(r["d1_count"] for r in full),
        "G3_gates_pass":len(rows) <= 5*len(full) and max(
            r["d1_count"] for r in full) <= 12,
        "daily":full
    }


def evaluate(rows: list[dict]) -> dict:
    if len(rows) != 305:
        raise ValueError("STAGE108_NOT_ALL_305")
    by_strategy = {
        strategy: summarize(rows, strategy)
        for strategy in (BENCHMARK, CONTROL, CANDIDATE)
    }
    paths = {name:{
        strategy:summarize([r for r in rows if r["D1_PATH"] == name], strategy)
        for strategy in (BENCHMARK, CONTROL, CANDIDATE)
    } for name in (DIRECT, REIGNITION)}
    dates = {date:{
        strategy:summarize([r for r in rows if r["date"] == date], strategy)
        for strategy in (BENCHMARK, CANDIDATE)
    } for date in DATE_SET}
    nbase = by_strategy[BENCHMARK]["gross_gain_ge100"]
    ncand = by_strategy[CANDIDATE]["gross_gain_ge100"]
    unchanged_2x = by_strategy[CANDIDATE]["major2x_early5_eval_only"]
    load=daily_load(rows)
    reasons = []
    if decimal(by_strategy[CANDIDATE]["median_gross_pct"]) <= 0:
        reasons.append("PATH_EXIT_GROSS_PRICE_MEDIAN_NOT_POSITIVE")
    if not nbase or ncand * 100 < 80 * nbase:
        reasons.append("PATH_EXIT_LOSES_MORE_THAN_20PCT_OF_BASELINE_100PCT_RIGHT_TAIL")
    if unchanged_2x * 100 < 80 * 27:
        reasons.append("FROZEN_D1_MAJOR_2X_G2_BELOW_80PCT")
    if not load["G3_gates_pass"]:
        reasons.append("UNCHANGED_D1_G3_ALERT_LOAD_FAILS")
    result = {
        "schema":SCHEMA,
        "preregistration":"MONSTER_STAGE108_DUAL_PATH_EXIT_AND_G3_BASELINE_PREREG_20261013.md",
        "source_git_blob":PIN_BLOB,
        "source_original305":305,
        "path_census":{DIRECT:164,REIGNITION:141},
        "original_D0_D1_model_changed":False,
        "strategies":by_strategy,
        "by_path":paths,
        "by_date":dates,
        "chronologically_later_four_dates":{
            "dates":list(DATE_SET[2:]),
            "benchmark":summarize([r for r in rows if r["date"] in DATE_SET[2:]], BENCHMARK),
            "candidate":summarize([r for r in rows if r["date"] in DATE_SET[2:]], CANDIDATE),
            "already_exposed_not_new_OOS":True,
        },
        "unchanged_D1_attention_load":load,
        "right_tail_gross100_candidate_retention":str(
            Decimal(ncand)/nbase) if nbase else None,
        "major2x_early5_all_preserved_by_exit_only":unchanged_2x==27,
        "candidate_decision":("REJECTED_HISTORICAL_PRICE_OR_RIGHT_TAIL_OR_G3"
                              if reasons else "PASSES_EXPOSED_HISTORY_ONLY_NO_OOS"),
        "rejection_reasons":reasons,
        "complete_305_case_results":[{
            "date":r["date"],"symbol":r["symbol"],
            "D1_PATH":r["D1_PATH"],"D1_FIRST_UTC":r["D1_FIRST_UTC"],
            "original_major2x_early5_EVAL_ONLY":r["original_major_2x_early5_EVAL_ONLY"],
            "benchmark_24h_gross_price_pct":str(policy(r,BENCHMARK)[0]),
            "candidate_gross_price_pct":str(policy(r,CANDIDATE)[0]),
            "candidate_exit_horizon_min":policy(r,CANDIDATE)[1],
            "original_72h_gross_pct_reference_only":r["original_fixed_72h"]["gross_price_return_pct"],
        } for r in rows],
        "real_fill_and_executable_profit":"UNKNOWN",
        "forward_independent_oos":"NOT_DONE",
        "independent_ai_review_of_new_model":"NOT_DONE",
        "model_deployment":"NO_GO","gmail":"OFF","auto_trade":"NO_GO",
        "frank":"UNCHANGED",
    }
    return result


def selftest() -> None:
    fake = {
        "D1_PATH":DIRECT,
        "original_fixed_24h":{"gross_price_return_pct":"10"},
        "fixed_12h_price_exit":{"gross_price_return_pct":"50"},
        "original_major_2x_early5_EVAL_ONLY":True,
    }
    assert policy(fake,CANDIDATE) == (Decimal("10"),1440)
    fake["D1_PATH"] = REIGNITION
    assert policy(fake,CANDIDATE) == (Decimal("50"),720)
    assert fee_scenario(Decimal("0"),20)<0
    assert decimal("0") == 0
    for bad in ["NaN","Infinity"]:
        try:decimal(bad)
        except ValueError:pass
        else:raise AssertionError("NONFINITE_ACCEPTED")
    print("STAGE108_FROZEN_PATH_DISJOINT_AND_FEE_SCENARIO_SELFTEST_PASS")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--backtest", action="store_true")
    parser.add_argument("--out",type=Path)
    args=parser.parse_args()
    if args.selftest:
        selftest()
        return
    if not args.backtest or not args.out:
        parser.error("use --backtest --out")
    result=evaluate(read_rows())
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+"\n")
    print("STAGE108_REAL305_PATH_EXIT_REPLAY "+json.dumps({
        "source_git_blob":PIN_BLOB,
        "n":result["source_original305"],
        "baseline":result["strategies"][BENCHMARK],
        "candidate":result["strategies"][CANDIDATE],
        "daily":{k:v for k,v in result["unchanged_D1_attention_load"].items() if k!="daily"},
        "decision":result["candidate_decision"],
        "reasons":result["rejection_reasons"],
        "recorded_out":str(args.out),
    },sort_keys=True))


if __name__=="__main__":
    main()
