#!/usr/bin/env python3
"""Paired 1m vs3m original V4 on five ALREADY KNOWN Stage31 2x/5x outcomes.

Diagnostic only. Rehash all 18 original Stage30 ZIP/JSON source shards and each
target's official 1h/10x1m publisher SHA via Stage32 standard. Counts cannot
be treated as out-of-sample market early-recall or trade profitability.
"""
import argparse
import json
from pathlib import Path
try:
    import monster_v4_stage31_five_case_causal_trace as stage31
    import monster_v4_stage32_paired_1m_vs3m as trial
except ImportError:
    from scripts import monster_v4_stage31_five_case_causal_trace as stage31
    from scripts import monster_v4_stage32_paired_1m_vs3m as trial

def run(zips):
    trial.frozen()
    targets=stage31.original_five_cases(zips)
    findings=[]
    for cfg,row in targets:
        r=trial.compare_one(cfg["symbol"],trial.date.fromisoformat(cfg["day"]))
        if r["status"]!="COMPLETE_BOTH_168H":
            raise ValueError("STAGE32A_REAL_KNOWN_COIN_NOW_MISSING_VERIFIED_ARCHIVES")
        if (r["monthly_GT_official_publisher_SHA256"]!=row["hourly_GT_monthly_SHA256"] or
            r["ten_daily_1m_publisher_sha256"]!=row["official_source_SHA256_days"]):
            raise ValueError("STAGE32A_REPLAY_CHANGED_KNOWN_BINANCE_PUBLISHER_SOURCE_SHA")
        if r["V4_original3m"]["watch_utcs"]!=row["continuous"]["watch_utcs"] or (
              r["V4_original3m"]["setup_utcs"]!=row["continuous"]["setup_utcs"]):
            raise ValueError("STAGE32A_ORIGINAL_V4_D0_D1_PARITY_WITH_STAGE30_NOT_SAME")
        target=str(cfg["target_m"])+"x"
        ctrl=r["labels_original3m"][target]
        fast=r["labels_candidate1m"][target]
        if ctrl["cross_1m_high_UTC"]!=cfg["cross"] or fast["cross_1m_high_UTC"]!=cfg["cross"]:
            raise ValueError("STAGE32A_GT_CROSS_MISMATCH")
        findings.append({"symbol":cfg["symbol"],"date":cfg["day"],"multiple":cfg["target_m"],
           "cross_high_utc":cfg["cross"],"original_3min":{"gt":ctrl,
               "WATCH":r["V4_original3m"]["watch_count"],
               "D1":r["V4_original3m"]["setups"],
               "all_watch":r["V4_original3m"]["watch_utcs"]},
           "candidate_1min":{"gt":fast,
               "WATCH":r["V4_candidate1m"]["watch_count"],
               "D1":r["V4_candidate1m"]["setups"],
               "all_watch":r["V4_candidate1m"]["watch_utcs"]},
           "frozen_source_SHA_same_original":True})
        print("STAGE32A_PAIRED_CASE "+json.dumps({
          "symbol":cfg["symbol"],"original":ctrl["classification"],"candidate":fast["classification"],
          "original_first":ctrl["first_watch_UTC"],"candidate_first":fast["first_watch_UTC"],
          "before_original_nearest_min":ctrl["nearest_pre_cross_lead_min"],
          "before_candidate_nearest_min":fast["nearest_pre_cross_lead_min"],
          "WATCH_old":r["V4_original3m"]["watch_count"],
          "WATCH_new":r["V4_candidate1m"]["watch_count"]},sort_keys=True),flush=True)
    return {"schema":"MONSTER_STAGE32A_POSTHOC_FIVE_KNOWN_COIN_DIAGNOSTIC_1M_VS3M_V1",
        "original18_artifact_ZIP_JSON_sha_verified":True,
        "all_5_verified_monthly_daily_Binance_SHA_same_as_Stage30":True,
        "original_V4_D0_D1_full_168h_event_parity":True,
        "only_cadence_changed_and_original_production_called":True,
        "five_cases":findings,
        "posthoc_exposed_NOT_a_market_profit_validation":True,
        "no_real_fills_or_L2":True,
        "real_mail":"OFF","trading":"NO_GO","deployment":"NO_GO","frank":"UNCHANGED",
        "other_ai_review":"NOT_DONE"}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--original-stage30-zips",nargs=18,required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    a=p.parse_args()
    r=run(a.original_stage30_zips)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(r,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("STAGE32A_DONE_REAL_SHA_PARITY "+json.dumps({"n":len(r["five_cases"]),"source":r["all_5_verified_monthly_daily_Binance_SHA_same_as_Stage30"]}),flush=True)
if __name__=="__main__":main()
