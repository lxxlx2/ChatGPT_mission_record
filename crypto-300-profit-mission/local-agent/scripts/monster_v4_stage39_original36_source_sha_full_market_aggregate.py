#!/usr/bin/env python3
"""Rehash Stage39 original36 source ZIPs and compare every Stage38 pilot case.

Compute full 5400 mixed USD-M archived-symbol historical market denominator.
Publisher verified data only; censored cases NOT recoded negative/no WATCH.
No strategy fitting, reward claims, BTC model, order books or production.
"""
import argparse,collections,csv,hashlib,json,statistics,zipfile
from pathlib import Path

EVIDENCE=Path(__file__).resolve().parents[2]/"monster"/"evidence"
DAYS=("2025-01-19","2025-04-19","2025-07-19","2025-10-19","2026-04-19","2026-07-19")
ORIGINAL="MONSTER_STAGE39_USDM_900x6_ORIGINAL_V4_FULL168H_SHA_GROSS_2x5x10x_V1"
SCHEMA="MONSTER_STAGE39_ORIGINAL36_SHA_5400_USDM_FUTURES_FULL_CAUSAL_DISCOVERY_CENSUS_V1"
STAGE37=EVIDENCE/"monster_stage37_sixdate_all5400_usdm_source_and_GT.csv"
STAGE38=EVIDENCE/"monster_stage38_original12_full172_futures_causal_cases.jsonl"
STAGE36=EVIDENCE/"monster_stage36_official_usdm_archive_vs_spot758.json"
GOOD="COMPLETE_REAL_USDM_1M_SHA_CAUSAL_V4"
ACCEPTED={"CENSORED_STAGE37_HOURLY_SOURCE","CENSORED_DAILY_1M_404",
 "CENSORED_DAILY_1M_GAP","CENSORED_PUBLISHER_VERIFIED_1H_VS_1M_PRICE_CONFLICT",GOOD}

def sha(b):return hashlib.sha256(b).hexdigest()

def read_originals(m,folder):
    if m.get("run_id")!=38208358036 or len(m.get("artifacts",[]))!=36:
        raise ValueError("STAGE39_NOT_FIXED_ORIGINAL36_SOURCE_PROOF")
    output=[];receipts=[]
    for a in m["artifacts"]:
        day=a["date"];shard=int(a["shard"]);aid=int(a["artifact_id"])
        if day not in DAYS or shard not in range(6) or any(r["date"]==day and r["shard"]==shard for r in receipts):
            raise ValueError("STAGE39_ORIGINAL_SHARD_ID_WRONG_OR_DUPLICATE")
        zbytes=(Path(folder)/(str(aid)+".zip")).read_bytes()
        if sha(zbytes)!=a["zip_sha256"]:raise ValueError("STAGE39_ORIGINAL_ZIP_SHA_MISMATCH")
        member=f"monster_stage39_{day}_shard{shard}.json"
        with zipfile.ZipFile(Path(folder)/(str(aid)+".zip")) as z:
            if z.namelist()!=[member]:raise ValueError("STAGE39_EXPECT_SINGLE_ORIGINAL_MEMBER")
            raw=z.read(member)
        j=json.loads(raw)
        if j["schema"]!=ORIGINAL or j["date"]!=day or j["shard"]!=shard or (
           len(j["rows"])!=150 or j["source_cases"]!=150 or not j["all900_per_date_and150_per_shard"]):
            raise ValueError("STAGE39_ORIGINAL_FULL_SOURCE_INCOMPLETE")
        hist=collections.Counter(r["source_status"] for r in j["rows"])
        if dict(hist)!=j["status_counts"] or any(s not in ACCEPTED for s in hist):
            raise ValueError("STAGE39_ORIGINAL_SOURCE_STATUS_NOT_AUDITABLE")
        if any(r["date"]!=day for r in j["rows"]):raise ValueError("STAGE39_CROSSDATE_RESULT")
        for r in j["rows"]:
            if r["source_status"]==GOOD:
                if (r["polls"]!=3360 or len(r["verified_9_daily_1m_publisher_sha256"])!=9 or
                    len(r["verified_original_1h_publisher_sha256"])!=64 or not r["unchanged_V4_original_futures"]):
                    raise ValueError("STAGE39_ORIGINAL_V4_OR_PUBLISHER_SOURCE_DRIFT")
                if not all(p["verified_official_publisher_SHA256"] and len(p["zip_sha256"])==64 and p["bars"]==1440
                           for p in r["verified_9_daily_1m_publisher_sha256"]):
                    raise ValueError("STAGE39_OFFICIAL_1M_SOURCE_SHA_FAIL")
            if r["source_status"]=="CENSORED_PUBLISHER_VERIFIED_1H_VS_1M_PRICE_CONFLICT" and (
                    len(r.get("verified_9_daily_1m_publisher_sha256",[]))!=9 or
                    "actual_1h_anchor_open" not in r or "actual_1m_anchor_open" not in r):
                raise ValueError("STAGE39_OFFICIAL_PRICE_CONFLICT_PROOF_MISSING")
        output.extend(j["rows"])
        receipts.append({"date":day,"shard":shard,"artifact_id":aid,
                         "original_zip_sha256":sha(zbytes),"original_internal_JSON_sha256":sha(raw),
                         "shard_source_complete":j["source_verified_good"],"source_status":dict(hist)})
    if {(x["date"],x["shard"]) for x in receipts}!={(d,s) for d in DAYS for s in range(6)}:
        raise ValueError("STAGE39_ORIGINAL36_MISSING")
    return sorted(output,key=lambda r:(r["date"],r["symbol"])),sorted(receipts,key=lambda r:(r["date"],r["shard"]))

def study(rows,receipts):
    if len(rows)!=5400 or len({(r["date"],r["symbol"]) for r in rows})!=5400:
        raise ValueError("STAGE39_FULL5400_PAIRS_MISSING_OR_DUPLICATE")
    expected=list(csv.DictReader(STAGE37.open(encoding="utf-8",newline="")))
    if len(expected)!=5400 or {(r["date"],r["symbol"]) for r in expected}!={(r["date"],r["symbol"]) for r in rows}:
        raise ValueError("STAGE39_GT_PRIOR_5400_PAIRS_NOT_EQUAL")
    prior={(r["date"],r["symbol"]):r for r in expected}
    for r in rows:
        p=prior[(r["date"],r["symbol"])]
        if p["status"]!=r["hourly_status"] or (p["status"]=="COMPLETE_168H_PUBLISHER_SHA" and
             (p["gt2x"]!=r["original_GT2x_1h"] or p["gt5x"]!=r["original_GT5x_1h"]
                or p["gt10x"]!=r["original_GT10x_1h"])):
            raise ValueError("STAGE39_ORIGINAL_GT_VS_SOURCE_FROZEN_CHANGED")
    old=[json.loads(s) for s in STAGE38.read_text(encoding="utf-8").splitlines() if s]
    if len(old)!=172:raise ValueError("STAGE39_ORIGINAL_STAGE38_PILOT_MISSING")
    current={(r["date"],r["symbol"]):r for r in rows}
    for prev in old:
        this=current[(prev["date"],prev["symbol"])]
        if prev["source_status"]!=this["source_status"]:
            raise ValueError("STAGE39_REAL_PRICE_SOURCE_PARITY_VS_STAGE38_CHANGED "+prev["symbol"])
        if this["source_status"]==GOOD and (prev["WATCH_UTC"]!=this["WATCH_UTC"] or
            prev["SETUP_UTC"]!=this["SETUP_UTC"] or prev["classification"]!=this["classification"]):
            raise ValueError("STAGE39_UNMODIFIED_V4_WATCH_SETUP_GT_CHANGED "+prev["symbol"])
    stage36=json.loads(STAGE36.read_text(encoding="utf-8"))
    extrasyms=set(stage36["plain_USDT_not_in_Spot_758_symbols"])
    if len(extrasyms)!=428:raise ValueError("STAGE39_FUTURES_ONLY_SYMBOL_COHORT_CHANGED")
    states=collections.Counter(r["source_status"] for r in rows)
    valid=[r for r in rows if r["source_status"]==GOOD]
    positive=[r for r in valid if r["original_GT2x_1h"]=="True"]
    negatives=[r for r in valid if r["original_GT2x_1h"]=="False"]
    gt5=[r for r in valid if r["gross_high_gt5x"]]
    gt10=[r for r in valid if r["gross_high_gt10x"]]
    watchpositives=[r for r in positive if r["classification"]=="STRICTLY_EARLY_WATCH"]
    lead=[r["nearest_strictly_earlier_WATCH_lead_min"] for r in watchpositives]
    watches=[r for r in valid if r["watch_count"]>0]
    daily=[]
    for day in DAYS:
        one=[r for r in rows if r["date"]==day]
        if len(one)!=900:raise ValueError("STAGE39_DATE_NOT_ALL900")
        full=[r for r in one if r["source_status"]==GOOD]
        w=[r for r in full if r["watch_count"]]
        daily.append({"date":day,"attempted":900,"official_full1m_and1h":len(full),
          "source_status":dict(collections.Counter(r["source_status"] for r in one)),
          "gt2x_verified_full1m":sum(r["original_GT2x_1h"]=="True" for r in full),
          "gt2x_strict_early":sum(r["classification"]=="STRICTLY_EARLY_WATCH" and r["original_GT2x_1h"]=="True" for r in full),
          "gt5x_verified_full1m":sum(r["gross_high_gt5x"] for r in full),
          "not_2x_but_anyWATCH_coin_dates":sum(r["original_GT2x_1h"]=="False" and r["watch_count"]>0 for r in full),
          "WATCH_events":sum(r["watch_count"] for r in full),
          "distinct_WATCH_coin_dates":len(w),
          "D1_setup_events_per_symbol_persistent":sum(r["setup_count"] for r in full)})
    pulses=collections.Counter((r["WATCH_UTC"][0]) for r in watches)
    burst=[{"UTC":t,"first_WATCH_coin_dates":n} for t,n in pulses.most_common(25) if n>=6]
    results={
      "schema":"MONSTER_STAGE39_ORIGINAL36_SHA_5400_USDM_MARKET_WATCH_AND_GT_FACTUAL_V1",
      "source_original_run_id":38208358036,
      "original_source_SHA_verified_36":True,"stage38_original_172_pilot_signal_parity_verified":True,
      "full_stage37_hourly_source_attempts":len(rows),"complete_stage37_1h_before_minutes":3333,
      "publisher_1m_and_1h_agree_full":len(valid),
      "source_censored_total":len(rows)-len(valid),
      "status_counts":dict(states),
      "gt2x_full_source":len(positive),"gt5x_full_source":len(gt5),"gt10x_full_source":len(gt10),
      "gt2x_early_strict":len(watchpositives),
      "gt2x_same_minute_not_early":sum(r["classification"]=="SAME_MINUTE_NOT_EARLY" for r in positive),
      "gt2x_late_watch":sum(r["classification"]=="WATCH_LATE" for r in positive),
      "gt2x_no_watch":sum(r["classification"]=="NO_WATCH" for r in positive),
      "gt5x_early_strict":sum(r["watch_vs_gt5x_class"]=="STRICTLY_EARLY_WATCH" for r in gt5),
      "gt10x_early_strict":sum(r["watch_vs_gt10x_class"]=="STRICTLY_EARLY_WATCH" for r in gt10),
      "nearest_strict_pre_cross_median_lead_min":statistics.median(lead) if lead else None,
      "nearest_strict_pre_cross_ge5_min":sum(x>=5 for x in lead),
      "nearest_strict_pre_cross_ge15_min":sum(x>=15 for x in lead),
      "nearest_strict_pre_cross_ge60_min":sum(x>=60 for x in lead),
      "full_NOT2x_source_complete":len(negatives),
      "full_NOT2x_with_WATCH_coin_dates":sum(x["watch_count"]>0 for x in negatives),
      "all_source_complete_with_any_WATCH_coin_dates":len(watches),
      "all_WATCH_events":sum(x["watch_count"] for x in valid),
      "all_D1_setups_from_isolated_per_symbol_replay":sum(x["setup_count"] for x in valid),
      "futures_not_in_frozen_spot758_2x_source_complete":sum(r["symbol"] in extrasyms for r in positive),
      "futures_not_in_frozen_spot758_2x_early":sum(r["symbol"] in extrasyms and r["classification"]=="STRICTLY_EARLY_WATCH" for r in positive),
      "futures_not_in_frozen_spot758_source_complete":sum(r["symbol"] in extrasyms for r in valid),
      "per_date":daily,"first_WATCH_same_minute_bursts_min6":burst,
      "original36_artifact_source_sha_receipts":receipts,
      "historical_replay_is_not_independent_forward_prediction":True,
      "historical_exchangeinfo_and_stock_RWA_types":"UNVERIFIED",
      "futures_1000x_symbol_underlying_mapping":"UNVERIFIED",
      "real_trade_fill_or_L2_orderbook":"UNVERIFIED",
      "cross_symbol_global_8_capacity_D1_queue":"NOT_REPLAYED",
      "model_threshold_changed":False,"independent_other_AI_review":"NOT_DONE",
      "Monster_deployment":"NO_GO","Gmail":"OFF","trading":"NO_GO","Frank":"UNCHANGED"}
    return results

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--manifest",type=Path,required=True)
    p.add_argument("--zip-dir",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    rows,receipts=read_originals(json.loads(a.manifest.read_text()),a.zip_dir)
    summary=study(rows,receipts)
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"monster_stage39_36original_SHA_all5400_futures_discovery_summary.json").write_text(
      json.dumps(summary,ensure_ascii=False,sort_keys=True,indent=2)+"\n")
    with (a.out/"monster_stage39_all5400_usdm_real1m_originalV4_cases.jsonl").open("w",encoding="utf-8") as f:
        for r in rows:f.write(json.dumps(r,ensure_ascii=False,sort_keys=True)+"\n")
    with (a.out/"monster_stage39_realminute_gt2x_event_registry.csv").open("w",encoding="utf-8",newline="") as f:
        cols=["date","symbol","source_status","first_true_2x_HIGH_minute_UTC","classification",
              "earliest_watch_lead_min","nearest_strictly_earlier_WATCH_lead_min","watch_count",
              "original_GT5x_1h","gross_high_gt5x","watch_vs_gt5x_class"]
        w=csv.DictWriter(f,fieldnames=cols,extrasaction="ignore",lineterminator="\n")
        w.writeheader()
        for r in rows:
            if r["original_GT2x_1h"]=="True":w.writerow(r)
    print("STAGE39_ORIGINAL36_SOURCE_SHA_STAGE38_PARITY_FULL5400_REPRODUCED "+json.dumps({
        x:summary[x] for x in ("publisher_1m_and_1h_agree_full","source_censored_total",
        "gt2x_full_source","gt2x_early_strict","full_NOT2x_with_WATCH_coin_dates","all_WATCH_events",
        "futures_not_in_frozen_spot758_2x_early")},sort_keys=True))
if __name__=="__main__":main()
