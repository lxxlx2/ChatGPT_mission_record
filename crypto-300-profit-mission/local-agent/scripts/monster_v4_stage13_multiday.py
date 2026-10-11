#!/usr/bin/env python3
"""Stage13: preregistered calendar-day full 504-symbol Binance V4 D0/D1 replay.

The score, OHLCV source validation, censoring, fee/slippage hypothesis and
execution model are reused unchanged from Stage12. Each CI job gets one date.
Not historically delisted point-in-time universe, independent OOS or real PNL.
"""
import argparse
import json
from datetime import date
from pathlib import Path

try:
    import monster_v4_archive_universe_replay as full
except ImportError:
    from scripts import monster_v4_archive_universe_replay as full

PREREG = full.source.EVIDENCE / "monster_stage13_fixed_calendar4_preregistration_20261011.json"


def frozen_dates(path=PREREG):
    meta=json.loads(Path(path).read_text(encoding="utf-8"))
    if meta.get("schema")!="MONSTER_STAGE13_PRE_REGISTERED_MULTIDATE_CURRENT504_V1":
        raise ValueError("UNRECOGNIZED_STAGE13_MANIFEST")
    original=meta.get("frozen_dates_utc")
    expected=["2025-11-17","2026-02-17","2026-05-17","2026-08-17"]
    if original!=expected or not meta.get("frozen_before_stage13_source_fetch"):
        raise ValueError("STAGE13_CALENDAR_MODIFIED")
    if meta.get("symbol_count")!=504 or meta.get("source_symbol_registry")!=full.REGISTRY.name:
        raise ValueError("UNIVERSE_REGISTRY_CHANGED")
    return [date.fromisoformat(x) for x in original]


def run_day(date_value, *, symbols=None, worker=None, max_workers=full.MAX_WORKERS):
    if not isinstance(date_value,date) or date_value not in frozen_dates():
        raise ValueError("DATE_OUTSIDE_FROZEN_PREREGISTRATION")
    anchor=date_value.isoformat()+"T12:00:00Z"
    if worker is None:
        def worker(symbol):
            return full.run_symbol(symbol,calendar_day=date_value,calendar_anchor=anchor)
    report=full.run(symbols=symbols,worker=worker,max_workers=max_workers)
    report["schema"]="MONSTER_STAGE13_FROZEN_MULTIDAY_V4_HISTORICAL_REPLAY_V1"
    report["anchor"]=anchor
    report["source"]="OFFICIAL_BINANCE_PUBLIC_DAILY_1M_ZIP_PUBLISHED_SHA256"
    report["cohort_type"]="CURRENT_20261011_LISTING_SURVIVOR_UNIVERSE"
    report["frozen_prereg_date"]=date_value.isoformat()
    report["selection_basis"]="CALENDAR_DAY_17TH_EVERY_3_MONTHS"
    report["research_only"]=True
    report["has_historical_depth_or_actual_fills"]=False
    report["independent_out_of_sample"]=False
    report["deployment"]="NO_GO"
    report["real_mail_sent"]=False
    report["actual_trading_enabled"]=False
    return report


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--date",required=True,choices=[d.isoformat() for d in frozen_dates()])
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--limit",type=int,default=0,help="0=all504; positive means smoke only")
    args=parser.parse_args()
    if args.limit < 0 or args.limit>504:
        raise SystemExit("INVALID_SAMPLE_LIMIT")
    d=date.fromisoformat(args.date)
    manifest=json.loads(full.REGISTRY.read_text(encoding="utf-8"))
    universe=full.validate_manifest(manifest)
    selected=universe[:args.limit] if args.limit else None
    report=run_day(d,symbols=selected)
    report["classification"]="SMOKE_ONLY" if args.limit else "ALL_CURRENT504_SPOT_SINGLE_FROZEN_CALENDAR_DAY"
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    summary=report["summary"]
    important={
        "status":"STAGE13_REAL_HISTORICAL_REPLAY_COMPLETED",
        "date":args.date,
        "source_status_counts":summary["source_status_counts"],
        "complete":summary["full_60h_data_cases"],
        "attempted":summary["case_count_executed"],
        "observations":summary["observed_3m_ticker_proxy_poll_count"],
        "WATCH":summary["watch_episodes"],
        "D1":summary["setup_episodes"],
        "watch_symbols":[x["symbol"] for x in report["cases"]
                         if x.get("watch_events",0)>0],
        "watch_30usd_median":summary["assumed_20bps_per_side_net_return_median_pct"],
        "watch_30usd_proxy_count":summary["assumed_30usdt_24h_trade_proxy_cases"],
        "D1_30usd_median":summary["d1_confirmed_20bps_net_median_pct"],
        "D1_30usd_proxy_count":summary["d1_confirmed_30usdt_24h_proxy_cases"],
        "D1_positive":summary["d1_confirmed_20bps_net_positive"],
        "D1_negative":summary["d1_confirmed_20bps_net_negative"],
        "D1_censored":summary["d1_confirmed_censored_24h_proxy_statuses"],
        "full_log_artifact":str(args.output),
        "not_proven":"ACTUAL_EXECUTION_OR_TRUE_POSITIVE_RATE",
    }
    print("STAGE13_RESULT_JSON "+json.dumps(important,sort_keys=True),flush=True)
    if summary["source_status_counts"].get("SOURCE_INTEGRITY_REJECTED",0)>0:
        raise SystemExit("CHECKSUM_INTEGRITY_FAILURE")
    if not args.limit and summary["full_60h_data_cases"]<150:
        raise SystemExit("REPLAY_TOO_FEW_HISTORICALLY_ACTIVE_SYMBOLS")


if __name__=="__main__":
    main()
