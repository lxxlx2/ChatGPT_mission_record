#!/usr/bin/env python3
"""Aggregate exact original305 source-verified official 1m exit paths, no trades."""
from __future__ import annotations
import argparse
from collections import Counter
from decimal import Decimal
import json
from pathlib import Path
import statistics

try:
    import monster_v4_stage101_exit_minute_backtest as stage
    import monster_v4_stage88_d1_24h72h_official_paths as old
except ImportError:
    from scripts import monster_v4_stage101_exit_minute_backtest as stage
    from scripts import monster_v4_stage88_d1_24h72h_official_paths as old

SCHEMA="MONSTER_STAGE101_ALL305_ORIGINAL_D1_HISTORIC_REAL_MINUTE_EXIT_SUMMARY_V1"
STRATEGIES={
    "original_24h":"original_fixed_24h",
    "original_72h":"original_fixed_72h",
    "time_exit_6h":"fixed_6h_price_exit",
    "time_exit_12h":"fixed_12h_price_exit",
    "hard15_trail20_after25_72h":"hard15_trail20_after25_72h",
}


def rows_from_artifacts(folder: Path):
    files=sorted(folder.glob("monster-stage101-*.json"))
    if len(files)!=24:
        raise ValueError("STAGE101_EXPECTED_EXACT24_REAL_OFFICIAL_SHARDS")
    census,source=stage.frozen()
    originals={(x["date"],x["symbol"]):x for x in census}
    chosen=set()
    obtained=[]
    for f in files:
        p=json.loads(f.read_text())
        if p["schema"]!=stage.SCHEMA or (p["date"],p["shard"]) in chosen:
            raise ValueError("STAGE101_INVALID_OR_DUPLICATE_SHARD")
        key=(p["date"],p["shard"])
        if p["date"] not in old.DATES or p["shard"] not in range(4):
            raise ValueError("STAGE101_NONFROZEN_SHARD")
        chosen.add(key)
        expected=old.shard_rows(*key,census)
        keys={(x["date"],x["symbol"]) for x in expected}
        rows=p["rows"]
        if len(rows)!=p["original_case_count"] or keys!={(x["date"],x["symbol"]) for x in rows}:
            raise ValueError("STAGE101_SHARD_ORIGINAL_COIN_DATES_MISSING")
        obtained.extend(rows)
    if len(obtained)!=305 or len({(x["date"],x["symbol"]) for x in obtained})!=305:
        raise ValueError("STAGE101_ALL305_CORRUPTED")
    for row in obtained:
        oldrow=originals[(row["date"],row["symbol"])]
        archived=source[(row["date"],row["symbol"])]
        if (row["D0_FIRST_UTC"]!=oldrow["D0_FIRST_UTC"]
            or row["D1_FIRST_UTC"]!=oldrow["D1_FIRST_UTC"]
            or row["D1_PATH"]!=oldrow["D1_PATH"]
            or row["identity"]!=oldrow["identity"]
            or row["original_major_2x_early5_EVAL_ONLY"]!=oldrow[
                  "early5_gt2_evaluation_only"]
            or row["original_fixed_24h"]["gross_price_return_pct"]!=archived[
                  "h24"]["fixed_exit_gross_return_pct"]
            or row["original_fixed_72h"]["gross_price_return_pct"]!=archived[
                  "h72"]["fixed_exit_gross_return_pct"]):
            raise ValueError("STAGE101_305_DAY_OR_PRICE_NOT_STAGE85_STAGE88")
        for name,src in STRATEGIES.items():
            v=row[src]
            if not isinstance(v,dict):
                raise ValueError("STAGE101_STRATEGY_CASE_MISSING_"+name)
            d=Decimal(v["gross_price_return_pct"])
            if not d.is_finite():
                raise ValueError("STAGE101_NAN_PRICE_RETURN")
    return sorted(obtained,key=lambda x:(x["date"],x["symbol"]))


def median(values):
    if not values:return None
    return str(statistics.median(values))


def summarize(rows):
    data={"attempted_original_D1_cases":len(rows),
          "has_verified_daily_official_sha":len(rows),
          "major2x_early5":sum(x["original_major_2x_early5_EVAL_ONLY"]
                             for x in rows)}
    for name,src in STRATEGIES.items():
        returns=[Decimal(x[src]["gross_price_return_pct"]) for x in rows]
        count=len(returns)
        reasons=Counter(x[src].get("exit_reason","FIXED_HORIZON")
                        for x in rows)
        data[name]={
          "source_valid":count,
          "positive_gross_proxy":sum(x>0 for x in returns),
          "positive_rate":str(Decimal(sum(x>0 for x in returns))/count) if count else None,
          "median_gross_pct":median(returns),
          "arithmetic_mean_gross_pct_not_portfolio":(
              str(sum(returns)/count) if count else None),
          "loss_at_least_20pct":sum(x<=-20 for x in returns),
          "gross_gain_ge50pct":sum(x>=50 for x in returns),
          "gross_gain_ge100pct":sum(x>=100 for x in returns),
          "exit_reasons":dict(reasons),
          "no_real_bid_ask_commission_or_execution":True,
          "exit_with_zero_trades_bar_count":sum(
              x[src]["exit_bar_trade_count"]<=0 for x in rows),
        }
    if (len(rows)==305 and (
        data["original_24h"]["positive_gross_proxy"]!=133
        or data["original_72h"]["positive_gross_proxy"]!=103
        or data["original_72h"]["gross_gain_ge100pct"]!=5)):
        raise ValueError("STAGE101_ORIGINAL_STAGE88_CROSS_CHECK_WRONG")
    return data


def audit(rows):
    grouped={"all305":rows}
    for d in old.DATES:
        grouped["date_"+d]=[x for x in rows if x["date"]==d]
    for path in ("DIRECT_AT_FIRST_D0","REIGNITION_AFTER_D0"):
        grouped["entry_"+path]=[x for x in rows if x["D1_PATH"]==path]
    answer={
      "schema":SCHEMA,
      "source_stage88_git_blob":stage.PIN,
      "frozen_dates":list(old.DATES),
      "source_scope":"MIXED_BINANCE_USDM_EXPOSED_HISTORICAL_ALL305",
      "parameters_predeclared":{
        "hard_stop_from_entry_pct":"-15",
        "trail_armed_when_previous_completed_high_at_least_pct":"+25",
        "trail_retains_fraction_of_previous_peak":"0.80",
        "hard_and_trail_max_elapsed_minutes":4320,
        "gap_open_worse_than_stop":"EXIT_AT_OBSERVED_MINUTE_OPEN_PRICE_ONLY",
        "intrabar_time_order":"STOP_FIRST_AND_RECOMPUTE_TRAIL_NEXT_MINUTE",
        "fixed_exits_at_minutes":[360,720,1440,4320],
      },
      "groups":{name:summarize(part) for name,part in grouped.items()},
      "real_executable_net_pnl":"UNKNOWN",
      "not_complete_crypto_identity":"TRUE",
      "historical_price_proxy_only":True,
      "not_forward_independent_oos":True,
      "D1_original_G3":"REJECTED",
      "D0_D1_rules_unchanged":True,
      "other_AI_review":"NOT_DONE",
      "deployment":"NO_GO","gmail":"OFF","autotrade":"NO_GO","frank":"UNCHANGED",
    }
    return answer


def selftest():
    assert len(STRATEGIES)==5
    assert len(old.DATES)==6
    assert Decimal(median([Decimal("3"),Decimal("-1")]))==1
    print("STAGE101_AGGREGATION_ALL305_SOURCE_CLOSED_TEST_PASS")


def main():
    a=argparse.ArgumentParser()
    a.add_argument("--selftest",action="store_true")
    a.add_argument("--artifact-dir",type=Path)
    a.add_argument("--out",type=Path)
    args=a.parse_args()
    if args.selftest:selftest();return
    if not args.artifact_dir or not args.out:
        a.error("--artifact-dir --out required")
    rows=rows_from_artifacts(args.artifact_dir)
    result=audit(rows)
    args.out.mkdir(parents=True,exist_ok=True)
    (args.out/"monster_stage101_all305_real1m_historic_exit_paths.jsonl").write_text(
       "".join(json.dumps(x,sort_keys=True,ensure_ascii=False)+"\n" for x in rows))
    (args.out/"monster_stage101_real305_exit_time_stop_comparison.json").write_text(
       json.dumps(result,sort_keys=True,ensure_ascii=False,indent=2)+"\n")
    full=result["groups"]["all305"]
    print("STAGE101_OFFICIAL_FULL305_EXIT_STRATEGY_TEST "+json.dumps({
      k:{"gross_median":full[k]["median_gross_pct"],
         "positive":full[k]["positive_gross_proxy"],
         "gain100":full[k]["gross_gain_ge100pct"],
         "loss20":full[k]["loss_at_least_20pct"]}
      for k in STRATEGIES},sort_keys=True))


if __name__=="__main__":
    main()
