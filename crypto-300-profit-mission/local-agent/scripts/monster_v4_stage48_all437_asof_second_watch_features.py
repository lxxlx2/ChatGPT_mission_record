#!/usr/bin/env python3
"""Monster Stage48 - original D0 936 observations, genuine SHA-verified asof minute features.

All previously source-complete USD-M first-and-repeat WATCH events in six
exposed, previously date-audited windows, plus explicit normal/no-watch/censored
denominators. This is exploratory data analysis NOT a fitted new P1 strategy.
Absolutely no post-event price in feature extraction: only t-61 .. t-1 open-time
minute bars at original WATCH time t. Bind each re-fetched daily ZIP to exact
source-stage45 already-verified official publisher SHA256, fail closed.
"""
from __future__ import annotations
import argparse,collections,concurrent.futures,datetime as dt,hashlib,json
from decimal import Decimal
from pathlib import Path

try:import monster_v4_stage38_usdm_original_v4_1m_pilot as orig
except ImportError:from scripts import monster_v4_stage38_usdm_original_v4_1m_pilot as orig

BASE=Path(__file__).resolve().parents[2]/"monster"/"evidence"
PRE=BASE/"monster_stage48_all437_watch_minute_feature_observations_prereg_20261012.json"
SRC=BASE/"monster_stage45_blind_all5400_originalV4_P1v02_cases.jsonl"
SUMMARY=BASE/"monster_stage45_blind_900x6_SHA_P1v02_metrics_and_gates.json"
PRIOR=BASE/"monster_stage47_all_market_first_and_repeated_D0_watch_vs_real2x_audit.json"
DATES=("2025-01-09","2025-09-02","2026-01-26","2026-02-24","2026-03-28","2026-05-10")
GOOD="COMPLETE_REAL_USDM_1M_SHA_CAUSAL_V4"
SCHEMA="MONSTER_STAGE48_ALL437_FIRST_REPEAT_936_EVENT_REAL_BINANCE_USDM_ASOF_1M_SHA_V1"
ONE=60000
D=Decimal
UTC=dt.timezone.utc

def fixed():
    p=json.loads(PRE.read_text(encoding="utf-8"))
    if (p["schema"]!="MONSTER_STAGE48_ALL437_SOURCE_VERIFIED_WATCH_COIN_DATES_936_ACTUAL_EVENT_ASOF_1M_FEATURE_AUDIT_PREREG_V1" or
        tuple(p["dates"])!=DATES or
        orig.blob(SRC)!=p["prior_original_git_sha45"] or
        orig.blob(SUMMARY)!=p["prior_summary_git_sha45"] or
        orig.blob(PRIOR)!=p["prior_stage47_git_sha"]):
        raise ValueError("STAGE48_FROZEN_SOURCE_OR_PREREG_CHANGED")
    summary=json.loads(SUMMARY.read_text(encoding="utf-8"))
    if summary.get("source_complete")!=3465 or summary.get("D0_WATCH_distinct_coin_dates")!=437 or summary.get("D0_WATCH_event_total")!=936:
        raise ValueError("STAGE48_EARLIER_VERIFIED_COUNTS_DRIFT")
    rows=[json.loads(line) for line in SRC.read_text(encoding="utf-8").splitlines() if line]
    if len(rows)!=5400 or len({(r["date"],r["symbol"]) for r in rows})!=5400:
        raise ValueError("STAGE48_STAGE45_FULL5400_CHANGED")
    for d in DATES:
        if len([r for r in rows if r["date"]==d])!=900:
            raise ValueError("STAGE48_DATE_NOT_FULL900")
    full=[r for r in rows if r["source_status"]==GOOD]
    if len(full)!=3465 or sum(bool(r["WATCH_UTC"]) for r in full)!=437 or sum(len(r["WATCH_UTC"]) for r in full)!=936:
        raise ValueError("STAGE48_WATCH_COHORT_DRIFT")
    return rows

def daily_at_original_sha(row,day,reader=orig.verified_1m_day):
    proofs={x["date"]:x for x in row["verified_9_daily_publisher_sha256"]}
    if len(proofs)!=9 or day.isoformat() not in proofs:
        raise ValueError("STAGE48_PROOF_DATE_NOT_PRESENT_IN_STAGE45")
    bars,now=reader(row["symbol"],day)
    prior=proofs[day.isoformat()]
    if (now["zip_sha256"]!=prior["zip_sha256"] or
        now["date"]!=prior["date"] or
        now["bars"]!=1440 or not now["verified_official_publisher_SHA256"] or
        len(bars)!=1440):
        raise ValueError("STAGE48_REFETCHED_OFFICIAL_PUBLISHER_SHA_VS_STAGE45_MISMATCH")
    return bars,now

def closed_window(watch_timestamp,lookup):
    """Only exactly t-61 through t-1 closed minute bars; never later."""
    t=orig.msutc(watch_timestamp)
    if t%ONE:raise ValueError("STAGE48_NOT_UTC_MINUTE_BOUNDARY")
    out=[]
    for i in range(61,0,-1):
        ms=t-i*ONE
        item=lookup(ms)
        if item is None or item[0]!=ms:raise ValueError("STAGE48_ASOF_61_MINUTE_SOURCE_GAP")
        out.append(item)
    if out[0][0]!=t-61*ONE or out[-1][0]!=t-ONE:
        raise ValueError("STAGE48_TIME_TRAVEL")
    return out

def features(window):
    if len(window)!=61 or any(window[i][0]!=window[0][0]+i*ONE for i in range(61)):
        raise ValueError("STAGE48_FEATURES_NOT_FULL_61_CLOSED_MINUTES")
    first,last=window[0],window[-1]
    if first[4]<=0 or last[4]<=0:raise ValueError("STAGE48_INVALID_CLOSE")
    pct=(last[4]/first[4]-1)*D(100)
    quote15=sum((x[5] for x in window[-15:]),D(0))
    prior45=sum((x[5] for x in window[1:46]),D(0))
    relative=D(3)*quote15/prior45 if prior45>0 else None
    trade15=sum(x[6] for x in window[-15:])
    if min(quote15,prior45)<0 or trade15<0:raise ValueError("STAGE48_INVALID_QUOTE_VOLUME_OR_TRADES")
    return {"ret60_pct":str(pct),
            "quote15_USDT":str(quote15),
            "quote_prev45_USDT":str(prior45),
            "normalized_quote15_vs_prior45":str(relative) if relative is not None else None,
            "trades15":trade15,"last_closed_close":str(last[4])}

def read_one(row,reader=orig.verified_1m_day):
    """Never uses a future outcome label before building all original WATCH facts."""
    d={"date":row["date"],"symbol":row["symbol"],"source_status":row["source_status"],
       "frozen_original_D0_watch_count":len(row.get("WATCH_UTC",[])),"events":[]}
    if row["source_status"]!=GOOD:return d
    times=row["WATCH_UTC"]
    if not times:return d
    if times!=sorted(set(times)) or len(times)!=row["watch_count"]:
        raise ValueError("STAGE48_OLD_WATCH_SEQUENCE_INVALID")
    sources={}
    def get(ms):
        day=dt.datetime.fromtimestamp(ms/1000,UTC).date()
        if day not in sources:
            bars,p=daily_at_original_sha(row,day,reader=reader)
            sources[day]=(bars,p)
        daily=sources[day][0]
        at=orig.msutc(day.isoformat()+"T00:00:00Z")
        ix=(ms-at)//ONE
        if ix<0 or ix>=len(daily):return None
        return daily[ix]
    first_close=None;previous_ms=None
    for index,now in enumerate(times):
        sample=closed_window(now,get)
        feats=features(sample)
        observed=orig.msutc(now)
        current=D(feats["last_closed_close"])
        if first_close is None:first_close=current
        feats.update({"asof_D0_WATCH_UTC":now,"watch_ordinal":index+1,
          "is_repeated_original_watch":index>0,
          "minutes_since_previous_D0":int((observed-previous_ms)/ONE) if previous_ms is not None else None,
          "ret_from_first_WATCH_last_close_pct":str((current/first_close-1)*D(100)),
          "actual_1m_official_source_closes_before_D0_utc":True})
        # Never use the known future 2x label in any feature or sample selection.
        d["events"].append(feats)
        previous_ms=observed
    d["official_refetched_daily_publisher_sha_receipts"]=[
       sources[day][1] for day in sorted(sources)]
    # Future GT truth is attached ONLY after the last feature has been extracted.
    crossed=orig.msutc(row["first_true_2x_HIGH_minute_UTC"]) if row.get("first_true_2x_HIGH_minute_UTC") else None
    d["historical_gt2x_at_frozen_anchor"]=row["original_GT2x_1h"]=="True"
    d["first_true_2x_HIGH_minute_UTC"]=row["first_true_2x_HIGH_minute_UTC"]
    d["gt5x"]=row["original_GT5x_1h"]=="True"
    d["gt10x"]=row["original_GT10x_1h"]=="True"
    for event in d["events"]:
        ms=orig.msutc(event["asof_D0_WATCH_UTC"])
        event["label_only_strictly_before_first_2x_utc"]=crossed is not None and ms<crossed
        event["label_only_after_or_at_first_2x_utc"]=crossed is not None and ms>=crossed
    return d

def run(day,shard,workers=2):
    rows=fixed()
    if day not in DATES or shard not in range(6) or workers not in (1,2,3,4):
        raise ValueError("STAGE48_NOT_FROZEN_DATE_SHARD")
    all_day=sorted((r for r in rows if r["date"]==day),key=lambda r:r["symbol"])
    selected=[r for i,r in enumerate(all_day) if i%6==shard]
    if len(selected)!=150:raise ValueError("STAGE48_NOT_150_SYMBOLS")
    # Only WATCH cases require source refetch. All 150 original row statuses
    # are retained; 0-WATCH and censored are not silently discarded.
    refs=[];errors=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        jobs={pool.submit(read_one,r):r for r in selected}
        for j in concurrent.futures.as_completed(jobs):
            r=jobs[j]
            try:
                x=j.result()
                if (x["date"],x["symbol"])!=(r["date"],r["symbol"]):
                    raise ValueError("STAGE48_RESULT_IDENTITY_CHANGED")
                refs.append(x)
            except Exception as e:
                errors.append({"symbol":r["symbol"],"error":type(e).__name__+":"+str(e)[:200]})
    if errors or len(refs)!=150:
        raise RuntimeError("STAGE48_OFFICIAL_SHA_OR_ASOF_FAIL_CLOSED "+json.dumps(errors[:6]))
    watch=[x for x in refs if x["events"]]
    return {"schema":SCHEMA,"date":day,"shard":shard,"original_full_universe":150,
        "actual_watch_coin_dates":len(watch),
        "real_original_D0_WATCH_events":sum(len(x["events"]) for x in refs),
        "all_150_original_date_symbol_source_status":collections.Counter(r["source_status"] for r in refs),
        "rows":sorted(refs,key=lambda r:r["symbol"]),
        "analysis_only_not_model_candidate":True,
        "future_price_used_to_decide_feature":False,
        "trade_execution":"UNVERIFIED","independent_other_AI_review":"NOT_DONE",
        "Monster_deploy":"NO_GO","Gmail":"OFF","Frank":"UNCHANGED"}

def selftest():
    t=orig.msutc("2026-01-29T05:42:00Z")
    raw=[(t-(61-i)*ONE,D("100"),D("110"),D("90"),D("100"),D("10000"),20) for i in range(61)]
    mapping={v[0]:v for v in raw}
    w=closed_window(orig.stamp(t),mapping.get)
    base=features(w)
    assert base["ret60_pct"]=="0"
    assert D(base["quote15_USDT"])==D("150000")
    assert D(base["quote_prev45_USDT"])==D("450000")
    assert D(base["normalized_quote15_vs_prior45"])==D("1")
    assert base["trades15"]==300
    future=(t,D("100"),D("999999"),D("1"),D("999"),D("1e12"),999)
    mapping[t]=future
    assert features(closed_window(orig.stamp(t),mapping.get))==base
    try:closed_window(orig.stamp(t),lambda ms: None if ms==t-5*ONE else mapping.get(ms))
    except ValueError as e:assert "GAP" in str(e)
    else:raise AssertionError("STAGE48_ASOF_SOURCE_GAP_FAIL_CLOSED_NOT_TRIGGERED")
    print("STAGE48_ORIGINAL_WATCH_CLOSED_1M_NO_FUTURE_FEATURE_SELFTEST_PASS")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--selftest",action="store_true")
    p.add_argument("--date");p.add_argument("--shard",type=int)
    p.add_argument("--workers",type=int,default=3);p.add_argument("--output",type=Path)
    a=p.parse_args()
    if a.selftest:selftest();return
    if not a.date or a.shard is None or not a.output:p.error("--date --shard --output required")
    report=run(a.date,a.shard,a.workers)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)+"\n")
    print("STAGE48_ALL_WATCH_ASOF_1M_SHA_FEATURES "+json.dumps({
        "date":report["date"],"shard":report["shard"],
        "watch_coin_dates":report["actual_watch_coin_dates"],
        "real_D0_events":report["real_original_D0_WATCH_events"]},sort_keys=True))
if __name__=="__main__":main()
