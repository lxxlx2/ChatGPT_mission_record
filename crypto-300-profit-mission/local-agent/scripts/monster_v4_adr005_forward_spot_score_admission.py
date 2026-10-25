#!/usr/bin/env python3
"""ADR005 November Spot 3-window D0/D1/G1/G2/G3 source-to-score admission.

Offline, no network, schedule, trade or model evaluation. Calls the approved
raw T0 gate and original-issuer 15-day census on their ORIGINAL INPUT BYTES.
Returns complete symbol attempt accounting, stage-by-stage readiness, and
explicit score vetoes. This is not a score and does not call USD-M Stage92.
"""
import argparse
from collections import Counter
from datetime import timedelta
import json
from pathlib import Path

import monster_v4_adr005_forward_spot_t0_gate as t0
import monster_v4_adr005_forward_spot_daily_gate as daily

SCHEMA="MONSTER_ADR005_SPOT_NOV_FORWARD_D0_D1_G1_G2_G3_SCORE_ADMISSION_V2"
BENCHMARK_SYMBOL="BTCUSDT"
BASELINE="BASELINE_24H"
OBSERVATION="D0_D1_OBSERVATION_7D"
FUTURE="FUTURE_2X_LABEL_7D"
COMPLETE="VERIFIED_1440_OFFICIAL_1M"
# Window/model rules are read-only references; never auto-promote old October
# historical results or the separate USD-M Stage91/92 preregistration.
RESEARCH_MODEL="D1_RBTC15_LAST5_V1"
MIN_INDEPENDENT_GT2X=20
MIN_WINDOWS_FOR_G1=3
G1_STRICT_MIN="0.90"
G1_5MIN_MIN="0.85"
G2_RETAIN_MIN="0.80"
G3_MEAN_MAX=5
G3_PEAK_MAX=12


def _valid_census(census):
    """Enforce cohort shape even for a directly called pure join function.

    A validated-looking dict still cannot cryptographically attest source
    origin; the top-level run() independently re-opens original issuer files.
    """
    if (not isinstance(census,dict)
        or census.get("schema")!=daily.SCHEMA
        or census.get("window_start_utc") not in t0.WINDOWS
        or type(census.get("baseline_symbol_population")) is not int
        or census["baseline_symbol_population"]<=0
        or census.get("days_per_original_symbol")!=15
        or census.get("expected_official_zip_checksum_pairs")!=
            15*census["baseline_symbol_population"]
        or census.get("source_publisher_archive_available_at_event_time")!="UNKNOWN"
        or census.get("dynamic_listing_changes_during_window")!="UNKNOWN"):
        raise ValueError("ADR005_SCORE_ADMISSION_UNVERIFIED_CENSUS_OR_PIT")
    calendar=daily.source_calendar(census["window_start_utc"])
    attempts=census.get("source_attempts")
    if not isinstance(attempts,list) or len(attempts)!=census["expected_official_zip_checksum_pairs"]:
        raise ValueError("ADR005_SCORE_ADMISSION_FULL_SYMBOL_DAY_CENSUS_REQUIRED")
    days={e["utc_day"]:e["segment"] for e in calendar}
    allowed={COMPLETE,"SOURCE_NOT_SUPPLIED","SOURCE_REJECTED_OR_INCOMPLETE",
             "UTC_DAY_NOT_YET_ENDED"}
    all_keys=set()
    symbols=set()
    counts=Counter()
    segment_counts={x:Counter() for x in daily.SEGMENTS}
    for item in attempts:
        if not isinstance(item,dict):
            raise ValueError("ADR005_SCORE_ADMISSION_INVALID_ATTEMPT")
        symbol=item.get("symbol")
        day=item.get("utc_day")
        status=item.get("source_status")
        if (not isinstance(symbol,str) or not t0.SYMBOL.fullmatch(symbol)
            or not symbol.endswith("USDT") or day not in days
            or item.get("segment")!=days[day]
            or status not in allowed or (symbol,day) in all_keys):
            raise ValueError("ADR005_SCORE_ADMISSION_ATTEMPT_ID_STATUS_OR_DAY_DRIFT")
        all_keys.add((symbol,day))
        symbols.add(symbol)
        counts[status]+=1
        segment_counts[days[day]][status]+=1
    if (len(symbols)!=census["baseline_symbol_population"]
        or any(sum((symbol,day) in all_keys for day in days)!=15 for symbol in symbols)
        or dict(sorted(counts.items()))!=census.get("actual_status_counts")
        or {k:dict(sorted(v.items())) for k,v in segment_counts.items()}
             !=census.get("segment_source_status_counts")
        or census.get("verified_complete_all_15days") !=
           (counts[COMPLETE]==len(attempts))):
        raise ValueError("ADR005_SCORE_ADMISSION_CENSUS_COMPLETENESS_MISMATCH")
    return attempts,symbols,calendar


def join_census(census):
    """One immutable row per T0 symbol and one cohort-wide source readiness.

    This adapter may be called with a synthetic test dict but MUST NOT be
    regarded as independent authenticated T0 or model execution evidence.
    """
    rows,symbols,calendar=_valid_census(census)
    grouping={s:{seg:Counter() for seg in daily.SEGMENTS} for s in symbols}
    for item in rows:
        grouping[item["symbol"]][item["segment"]][item["source_status"]]+=1
    # RBTC15 requires the benchmark's first 24h/7d observations independent
    # of the candidate's own bars. BTC is never itself a Monster target.
    btc_in_census=BENCHMARK_SYMBOL in symbols
    btc_counts=grouping[BENCHMARK_SYMBOL] if btc_in_census else None
    btc_baseline=bool(btc_counts and btc_counts[BASELINE][COMPLETE]==1)
    btc_observation=bool(btc_counts and btc_counts[OBSERVATION][COMPLETE]==7)
    btc_ready=btc_baseline and btc_observation
    out=[]
    stage_counts=Counter()
    for symbol in sorted(symbols):
        counts=grouping[symbol]
        baseline=counts[BASELINE][COMPLETE]==1
        observation=counts[OBSERVATION][COMPLETE]==7
        labels=counts[FUTURE][COMPLETE]==7
        is_target=symbol!=BENCHMARK_SYMBOL
        d0_ready=is_target and baseline and observation
        research_d1_ready=d0_ready and btc_ready
        d0_gt_ready=d0_ready and labels
        d1_gt_ready=research_d1_ready and labels
        blockers=[]
        if not baseline: blockers.append("BASELINE_24H_MISSING_OR_INVALID")
        if not observation: blockers.append("OBSERVATION_7D_MISSING_OR_INVALID")
        if not labels: blockers.append("FUTURE_2X_LABEL_7D_MISSING_OR_INVALID")
        if is_target and d0_ready:
            if not btc_in_census:
                blockers.append("BTC_BENCHMARK_NOT_IN_T0_SOURCE_CENSUS")
            else:
                if not btc_baseline:
                    blockers.append("BTC_BASELINE_24H_MISSING_OR_INVALID")
                if not btc_observation:
                    blockers.append("BTC_OBSERVATION_7D_MISSING_OR_INVALID")
        if not is_target:
            # BTC remains in the complete source population and can supply
            # benchmark data; it never becomes a Monster research D1 candidate.
            stage=("BTC_BENCHMARK_SOURCE_COMPLETE" if baseline and observation and labels
                   else "BTC_BENCHMARK_SOURCE_INCOMPLETE")
        elif not d0_ready:
            stage="D0_D1_SOURCE_BLOCKED"
        elif not research_d1_ready:
            stage="D0_SOURCE_READY_RBTC_D1_BLOCKED"
        elif not labels:
            stage="D0_D1_SOURCE_READY_GT_LABELS_BLOCKED"
        else:
            stage="SOURCE_COMPLETE_OFFLINE_REPLAY_ONLY"
        stage_counts[stage]+=1
        out.append({
            "symbol":symbol,
            "research_d1_target":is_target,
            "t0_listing_and_crypto_identity_independently_proven":False,
            "baseline_24h_source_verified":baseline,
            "candidate_own_observation_7d_source_verified":observation,
            "future_gt2x_7d_source_verified":labels,
            "btc_benchmark_in_t0_source_census":btc_in_census,
            "btc_benchmark_baseline_24h_source_verified":btc_baseline,
            "btc_benchmark_observation_7d_source_verified":btc_observation,
            "btc_benchmark_research_d1_source_ready":btc_ready,
            "technically_eligible_for_offline_original_d0_source_replay":d0_ready,
            "technically_eligible_for_offline_rbtc_d1_source_replay":research_d1_ready,
            "technically_eligible_for_offline_d0_d1_source_replay":research_d1_ready,
            "technically_eligible_for_original_d0_gt2x_label_sources":d0_gt_ready,
            "technically_eligible_for_retrospective_gt_labels":d1_gt_ready,
            "status":stage,
            "source_blockers":blockers,
            "original_d0_watch_event_id":None,
            "original_d1_research_event_id":None,
            "gt2x_label_event_id":None,
            "original_d0_core_executed":False,
            "research_d1_core_executed":False,
            "gt2x_label_evaluated":False,
            "actual_signal_sent_to_user":False,
            "actual_trading_or_exit_proven":False,
            "G4":"UNKNOWN",
        })
    if len(out)!=census["baseline_symbol_population"] or sum(stage_counts.values())!=len(out):
        raise RuntimeError("ADR005_SCORE_ADMISSION_ORIGINAL_MARKET_COHORT_LOSS")
    return {
        "schema":SCHEMA,
        "window_start_utc":census["window_start_utc"],
        "window_end_exclusive_utc":(
            (t0.EPOCH+timedelta(
                microseconds=t0.frozen_window(census["window_start_utc"])+
                t0.WINDOW_MS*1000)).isoformat().replace("+00:00","Z")),
        "source_from_admitted_t0_archive_sha256":census.get("t0_archive_sha256"),
        "original_market_census_venue":"BINANCE_SPOT",
        "original_t0_symbols_total":len(out),
        "btc_benchmark_symbol":BENCHMARK_SYMBOL,
        "btc_benchmark_in_t0_source_census":btc_in_census,
        "btc_benchmark_baseline_24h_source_verified":btc_baseline,
        "btc_benchmark_observation_7d_source_verified":btc_observation,
        "btc_benchmark_research_d1_source_ready":btc_ready,
        "frozen_source_days_per_symbol":len(calendar),
        "source_stage_status_counts":dict(sorted(stage_counts.items())),
        "actual_market_source_is_exchange_signed":False,
        "t0_issuer_identity_and_dynamic_listing_complete":False,
        "technical_original_d0_source_complete_symbols":
            sum(r["technically_eligible_for_offline_original_d0_source_replay"] for r in out),
        "technical_rbtc_d1_source_complete_symbols":
            sum(r["technically_eligible_for_offline_rbtc_d1_source_replay"] for r in out),
        "technical_offline_replay_source_complete_symbols":
            sum(r["technically_eligible_for_offline_d0_d1_source_replay"] for r in out),
        "technical_original_d0_gt_label_source_complete_symbols":
            sum(r["technically_eligible_for_original_d0_gt2x_label_sources"] for r in out),
        "technical_future_label_source_complete_symbols":
            sum(r["technically_eligible_for_retrospective_gt_labels"] for r in out),
        "all_source_15days_complete":census["verified_complete_all_15days"],
        "preregistered_research_D1_model":RESEARCH_MODEL,
        "G1_min_independent_gt2x":MIN_INDEPENDENT_GT2X,
        "G1_min_windows":MIN_WINDOWS_FOR_G1,
        "G1_strict_advance_min":G1_STRICT_MIN,
        "G1_advance_5m_min":G1_5MIN_MIN,
        "G2_retain_min":G2_RETAIN_MIN,
        "G3_avg_per_day_max":G3_MEAN_MAX,
        "G3_peak_per_day_max":G3_PEAK_MAX,
        "replay_engine_executed":False,
        "metrics_from_future_labels_computed":False,
        "ready_for_full_market_point_in_time_OOS":False,
        "point_in_time_http_origin_attested":False,
        "G0":"PARTIAL_DYNAMIC_LISTINGS_AND_CRYPTO_IDENTITY_UNKNOWN",
        "G1":"NOT_SCORABLE",
        "G2":"UNKNOWN",
        "G3":"NOT_SCORABLE",
        "G4":"UNKNOWN",
        "G5":"NEW_SCORE_ADMISSION_REVIEW_PENDING",
        "G6":"NO_GO",
        "NO_MERGE":True,"NO_DEPLOY":True,"NO_AUTOMATIONS":True,
        "NO_GMAIL":True,"NO_TRADES":True,"NO_NEW_RPC":True,
        "symbols":out,
    }


def run(start,asof,source_zip=None,receipts=None,official_dir=None):
    if (source_zip is None)!=(receipts is None):
        raise ValueError("ADR005_SCORE_ADMISSION_T0_ZIP_AND_RECEIPT_PAIR_REQUIRED")
    if source_zip is None:
        if official_dir is not None:
            raise ValueError("ADR005_SCORE_ADMISSION_NO_OFFICIAL_SOURCE_WITHOUT_T0")
        window=t0.preflight(start,asof)
        calendar=daily.planned_source_readiness(start,asof)
        return {
            "schema":SCHEMA,"window_start_utc":start,
            "source_status":window["source_ready_state"],
            "publisher_day_states":calendar["calendar"],
            "original_t0_symbols_total":None,
            "btc_benchmark_symbol":BENCHMARK_SYMBOL,
            "btc_benchmark_in_t0_source_census":None,
            "btc_benchmark_research_d1_source_ready":None,
            "technical_original_d0_source_complete_symbols":None,
            "technical_rbtc_d1_source_complete_symbols":None,
            "technical_offline_replay_source_complete_symbols":None,
            "technical_original_d0_gt_label_source_complete_symbols":None,
            "technical_future_label_source_complete_symbols":None,
            "replay_engine_executed":False,
            "metrics_from_future_labels_computed":False,
            "G0":"POPULATION_UNKNOWN","G1":"NOT_SCORABLE",
            "G2":"UNKNOWN","G3":"NOT_SCORABLE","G4":"UNKNOWN",
            "G5":"NEW_SCORE_ADMISSION_REVIEW_PENDING",
            "G6":"NO_GO","NO_AUTOMATIONS":True,"NO_TRADES":True,
        }
    if official_dir is None:
        raise ValueError("ADR005_SCORE_ADMISSION_OFFICIAL_15DAY_SOURCE_DIR_REQUIRED")
    admitted=t0.preflight(start,asof,source_zip,receipts)
    census=daily.census(admitted,official_dir,asof)
    result=join_census(census)
    if (result["source_from_admitted_t0_archive_sha256"]!=admitted["archive_sha256"]
        or result["original_t0_symbols_total"]!=admitted["t0_spot_usdt_candidates"]):
        raise ValueError("ADR005_SCORE_ADMISSION_T0_SOURCE_CENSUS_DRIFT")
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--window-start-utc",required=True,choices=t0.WINDOWS)
    p.add_argument("--asof-utc",required=True)
    p.add_argument("--source-zip",type=Path)
    p.add_argument("--source-receipts",type=Path)
    p.add_argument("--publisher-root",type=Path)
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    report=run(a.window_start_utc,a.asof_utc,a.source_zip,a.source_receipts,a.publisher_root)
    if a.out is not None:
        if a.out.exists() or a.out.is_symlink():
            raise ValueError("ADR005_SCORE_ADMISSION_REFUSE_EXISTING_OUTPUT")
        a.out.parent.mkdir(parents=True,exist_ok=True)
        with a.out.open("x",encoding="utf-8") as f:
            json.dump(report,f,sort_keys=True,ensure_ascii=False,indent=2)
            f.write("\n")
    print("ADR005_NOVEMBER_SPOT_OFFLINE_REPLAY_AND_SCORE_SOURCE_ADMISSION",
          json.dumps({k:v for k,v in report.items() if k not in ("symbols","publisher_day_states")},
                     sort_keys=True))


if __name__=="__main__":
    main()
