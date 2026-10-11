#!/usr/bin/env python3
"""Stage14: pre-registered D1-confirmed 31-event exit horizon investigation.

Research on known historical V4-selected D1 signals, deliberately in-sample.
Re-download Binance official daily ZIP + .CHECKSUM, use same V4 D0/D1 replay,
same fee/slip/lower-liquidity censor, varying ONLY hold_minutes.
No real trading, Gmail, historical L2 claims, or Monster deployment.
"""
import argparse
import concurrent.futures
import json
import statistics
import sys
from collections import Counter
from datetime import date,timedelta
from pathlib import Path

try:
    import monster_v4_archive_universe_replay as archive
    import monster_v4_historical_replay as historical
except ImportError:
    from scripts import monster_v4_archive_universe_replay as archive
    from scripts import monster_v4_historical_replay as historical

CONFIG = archive.source.EVIDENCE / "monster_stage14_frozen_31d1_horizon_study_20261011.json"
STAGE13 = archive.source.EVIDENCE / "monster_stage13_four_dates_actual_504spot_ci_consolidated_20261011.json"


def frozen_cases():
    cfg=json.loads(CONFIG.read_text(encoding="utf-8"))
    if cfg.get("schema")!="MONSTER_STAGE14_PRE_REGISTERED_D1_HOLD_HORIZONS_V1":
        raise ValueError("INVALID_STAGE14_FROZEN_MANIFEST")
    if cfg.get("horizons_minutes")!=[30,120,360,720,1440]:
        raise ValueError("CHANGED_PREDECLARED_EXIT_WINDOWS")
    if (cfg.get("capital_usdt"),cfg.get("assumed_fee_bps_per_side"),
        cfg.get("assumed_slippage_bps_per_side"))!=(30,10,20):
        raise ValueError("CHANGED_FEE_OR_CAPITAL_ASSUMPTIONS")
    cases=[(date.fromisoformat(day),symbol)
           for day,symbols in cfg["date_symbols"].items() for symbol in symbols]
    if (len(cases)!=31 or len(set(cases))!=31 or
        cfg["expected_d1_cases"]!=31):
        raise ValueError("NOT_ALL_FROZEN_D1_CASES")
    if any(not sym.endswith("USDT") for _,sym in cases):
        raise ValueError("INVALID_FROZEN_SYMBOL")
    return cases,cfg["horizons_minutes"]


def expected_24h():
    cfg=json.loads(STAGE13.read_text(encoding="utf-8"))
    ans={}
    for item in cfg["outcomes"]:
        day=item["date_utc"]
        for sym,ret in item["signal_d1_24h_net_pct"]:
            # Some WATCH-only signals have no D1; filter using the precommit.
            ans[(day,sym)]=ret
    last=cfg["with_prior_sep_stage12"]["baseline"]
    for sym,ret in last["price_proxy_30usd_net_return_pct_by_symbol"]:
        ans[(last["date"],sym)]=ret
    return ans


def run_case(day,symbol, horizon_minutes, get_archive=archive.get_day):
    days=[day+timedelta(days=i) for i in (-1,0,1)]
    all_bars=[]; proof=[]
    for d in days:
        bars,detail=get_archive(symbol,d)
        all_bars.extend(bars); proof.append(detail["sha256"])
    anchor=day.isoformat()+"T12:00:00Z"
    first=historical.parse_ms(anchor)-30*3600_000
    bars=all_bars[360:3960]
    if len(bars)!=3600 or any(v[0]!=first+60000*i for i,v in enumerate(bars)):
        raise ValueError("STAGE14_GAPPED_OFFICIAL_1M_SOURCE")
    case=historical.replay_case({"symbol":symbol,"venue":"spot",
        "cohort":"STAGE14_FROZEN_D1","old_watch_utc":anchor},
        bars,include_zero_trade_ticks=True)
    if len(case["setup_events"])!=1:
        raise ValueError("STAGE14_D1_COUNT_CHANGED_"+str(len(case["setup_events"])))
    setup=historical.parse_ms(case["setup_events"][0]["utc"])
    outcomes={}
    for minutes in horizon_minutes:
        outcomes[str(minutes)]=historical._proxy_trade(
            bars,bars[0][0],setup,180_000,20,hold_minutes=minutes)
    expected=expected_24h().get((day.isoformat(),symbol),"NO_EXPECTED_VALUE")
    observed=outcomes["1440"]
    if expected=="NO_EXPECTED_VALUE":
        raise ValueError("STAGE14_NOT_IN_FROZEN_PREVIOUS_RESULTS")
    if expected is None and observed["status"]=="PRICE_PROXY_ONLY":
        raise ValueError("STAGE14_24H_CENSORING_CONFLICT")
    if expected is not None and (
        observed["status"]!="PRICE_PROXY_ONLY" or
        abs(observed["net_pct"]-expected)>0.000001):
        raise ValueError("STAGE14_24H_REPRODUCIBILITY_MISMATCH")
    return {"day":day.isoformat(),"symbol":symbol,
            "setup_utc":case["setup_events"][0]["utc"],
            "official_archive_zip_sha256":proof,
            "source_verified_contiguous_minutes":len(bars),
            "historical_depth_available":False,
            "horizon_minutes_to_24h_net_price_proxy":outcomes}


def summarize(out, horizons):
    by_horizon={}
    for h in horizons:
        group=[x["horizon_minutes_to_24h_net_price_proxy"][str(h)] for x in out]
        trades=[t for t in group if t["status"]=="PRICE_PROXY_ONLY"]
        values=[v["net_pct"] for v in trades]
        censored=Counter(v["status"] for v in group
                         if v["status"]!="PRICE_PROXY_ONLY")
        by_horizon[str(h)]={
            "frozen_d1_events":len(out), "real_price_proxy_evaluable":len(values),
            "positive":sum(x>0 for x in values),
            "negative":sum(x<0 for x in values),
            "median_net_pct":round(statistics.median(values),6) if values else None,
            "mean_net_pct":round(statistics.mean(values),6) if values else None,
            "sum_independent_30usdt_pnl_proxy":round(sum(v["pnl_usdt_on_30"]
                                        for v in trades),6),
            "censored":dict(censored)}
    return by_horizon


def run(cases=None, worker=run_case, max_workers=4):
    fixed,horizons=frozen_cases()
    if cases is None:
        cases=fixed
    if len(set(cases))!=len(cases) or any(x not in fixed for x in cases):
        raise ValueError("NOT_A_FROZEN_SUBSET")
    if not 1<=max_workers<=4:
        raise ValueError("UNSAFE_CONCURRENCY")
    results=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
        f={pool.submit(worker,day,sym,horizons):(day,sym) for day,sym in cases}
        for job in concurrent.futures.as_completed(f):
            row=job.result()
            if (row["day"],row["symbol"])!=(
                    f[job][0].isoformat(),f[job][1]):
                raise ValueError("WORKER_CASE_IDENTITY_MISMATCH")
            results.append(row)
    results.sort(key=lambda row:(row["day"],row["symbol"]))
    return {"schema":"MONSTER_STAGE14_FROZEN_EXIT_HORIZON_ACTUAL_1M_V1",
            "not_out_of_sample":True,"historical_book_verified":False,
            "frozen_cases_expected":len(fixed),"cases_replayed":len(results),
            "price_basis":"1M_OPEN_AFTER_SETUP_PLUS_3MIN_AND_FIXED_HORIZON",
            "fee_bps_side":10,"slip_bps_side":20,
            "classification":"EXPOSED_EXIT_LENGTH_DIAGNOSTIC_NOT_VALIDATED_TRADING",
            "summary_by_horizon_minutes":summarize(results,horizons),
            "cases":results,"deploy_gate":"NO_GO",
            "mail_sent":False,"order_placed":False}


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--limit",type=int,default=0)
    x=p.parse_args()
    frozen,_=frozen_cases()
    if not 0<=x.limit<=len(frozen):
        raise SystemExit("INVALID_LIMIT")
    res=run(cases=frozen[:x.limit] if x.limit else None)
    x.output.parent.mkdir(parents=True,exist_ok=True)
    x.output.write_text(json.dumps(res,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("STAGE14_HORIZON_RESULT "+json.dumps({
        "cases":res["cases_replayed"],
        "horizons":res["summary_by_horizon_minutes"],
        "classification":res["classification"]},sort_keys=True),flush=True)
    if not x.limit and res["cases_replayed"]!=31:
        raise SystemExit("STAGE14_FULL_COHORT_INCOMPLETE")


if __name__=="__main__":
    main()
