#!/usr/bin/env python3
"""Stage45: Stage43 date-locked full USD-M market unchanged V4 + sealed P1v02.

Source data: Stage44 ORIGINAL36 SHA-verified full900x6 monthly 1h truth,
plus 9 real daily official USD-M 1m SHA files per source-complete coin-date.
P1v02 compares ONLY original first WATCH time with already closed minute bars.
No future high/label is an input to P1; GT labeling is appended after decision.
Original D0 events remain intact when P1 is rejected or source unscorable.
No BTC signal, post-hoc v01 tuning, real BUY, email, Mac or Frank access.
"""
import argparse,bisect,collections,concurrent.futures,csv,json
from datetime import date,datetime,timezone
from decimal import Decimal
from pathlib import Path
try:
    import monster_v4_stage39_usdm_all900_sixday_original_1m as old
    import monster_v4_stage38_usdm_original_v4_1m_pilot as original
except ImportError:
    from scripts import monster_v4_stage39_usdm_all900_sixday_original_1m as old
    from scripts import monster_v4_stage38_usdm_original_v4_1m_pilot as original

EVIDENCE=Path(__file__).resolve().parents[2]/"monster"/"evidence"
INPUT=EVIDENCE/"monster_stage44_all5400_blind_dates_source_status_and_GT.csv"
STAGE44=EVIDENCE/"monster_stage44_original36_sha_six_blind_900x6_hourly_GT_summary.json"
FREEZE=EVIDENCE/"monster_stage44_six_blinddate_900_usdm_and_P1_v02_prereg_20261012.json"
DATES=("2025-01-09","2025-09-02","2026-01-26","2026-02-24","2026-03-28","2026-05-10")
SCHEMA="MONSTER_STAGE45_6_BLIND_DATES_ORIGINAL_V4_AND_FROZEN_IMMEDIATE_P1V02_FULL_MARKET_V1"
GOOD=old.COMPLETE
RET60=Decimal("8")
Q15=Decimal("1000000")
REL15=Decimal("1.5")
P1GOOD="P1_V02_UPGRADE_IMMEDIATE_FIRST_WATCH"

def freeze():
    p=json.loads(FREEZE.read_text(encoding="utf-8"))
    if (p.get("schema")!="MONSTER_STAGE44_SIX_DATE_STAGE43_AUDIT_LOCKED_900_USDM_BLIND_HOURLY_AND_P1V02_PROTOCOL_V1"
        or tuple(p["dates"])!=DATES or original.blob(INPUT)!="938747a010109e6fb99a0da2da1a46f67f0d8862"
        or original.blob(original.production.__file__)!=original.ORIGINAL_V4_GIT_BLOB):
        raise ValueError("STAGE45_ORIGINAL_HOURLY_OR_V4_SOURCE_DRIFT")
    rule=p["strategy_hypothesis_v02"]
    if (rule["ret60_closed_1m_percent_gte"]!=8 or
        rule["boolean_expression"]!="(RET60>=8) OR (QUOTE15>=1000000 AND QUOTE15/(QUOTE_PREVIOUS45/3)>=1.5)"):
        raise ValueError("STAGE45_FROZEN_P1_V02_CHANGED")
    totals=json.loads(STAGE44.read_text(encoding="utf-8"))
    if (totals["source_complete"],totals["gross2x_high"],totals["gross5x_high"],totals["gross10x_high"])!=(3484,41,6,3):
        raise ValueError("STAGE45_STAGE44_STRICT_BLIND_SHA_MISMATCH")
    with INPUT.open(newline="",encoding="utf-8") as f:rows=list(csv.DictReader(f))
    if len(rows)!=5400 or len({(r["date"],r["symbol"]) for r in rows})!=5400:
        raise ValueError("STAGE45_NOT_ALL900_6_DATES")
    for day in DATES:
        if sum(r["date"]==day for r in rows)!=900:raise ValueError("STAGE45_NOT900_PER_DATE")
    return rows

def score_p1_first_watch(asof,bars):
    ms=original.msutc(asof)
    starts=[r[0] for r in bars]
    ix=bisect.bisect_left(starts,ms)-1
    if ix<60 or ix>=len(bars) or starts[ix]!=ms-60000:
        return {"p1_status":"P1_SOURCE_UNSCORABLE","p1_reason":"NO_CLOSED_BAR_AT_FIRST_D0"}
    use=bars[ix-60:ix+1]
    if len(use)!=61 or any(x[0]!=ms-(61-i)*60000 for i,x in enumerate(use)):
        return {"p1_status":"P1_SOURCE_UNSCORABLE","p1_reason":"MISSING_MINUTE_HISTORY"}
    if any(min(x[1],x[2],x[3],x[4])<=0 or x[5]<0 for x in use):
        return {"p1_status":"P1_SOURCE_UNSCORABLE","p1_reason":"BAD_MINUTE_OHLCV"}
    last=use[-1]
    pct=(last[4]/use[0][4]-1)*Decimal(100)
    # xs[-15:] are closed t-15..t; prior 45 are t-60..t-16.
    q15=sum((x[5] for x in use[-15:]),Decimal(0))
    q45=sum((x[5] for x in use[1:46]),Decimal(0))
    relative=(q15*Decimal(3)/q45 if q45>0 else None)
    eligible=(pct>=RET60 or (q15>=Q15 and relative is not None and relative>=REL15))
    return {"p1_status":P1GOOD if eligible else "P1_V02_NOT_UPGRADED_D0_PRESERVED",
            "p1_decision_UTC":asof,"p1_asof_no_future_bars":True,
            "p1_ret60_pct":str(pct),
            "p1_quote15_usdt":str(q15),"p1_quote_prev45_usdt":str(q45),
            "p1_q15_normalized_ratio":str(relative) if relative is not None else None,
            "p1_trigger_arm":("RET60" if pct>=RET60 else ("QUOTE" if eligible else "NONE"))}

def candidate(row,minute_get=original.minute_source,runner=original.production_scan):
    d={"date":row["date"],"symbol":row["symbol"],
       "hourly_source_status":row["source_status"],
       "original_GT2x_1h":row.get("gt2x",""),
       "original_GT5x_1h":row.get("gt5x",""),
       "original_GT10x_1h":row.get("gt10x",""),
       "source_status":"UNKNOWN","frozen_p1_rule":"STAGE44_P1_V02"},
    # remove accidental tuple: only dict must be passed downstream
    d=d[0]
    if row["source_status"]!="COMPLETE_168H_OFFICIAL_PUBLISHER_SHA":
        d["source_status"]="CENSORED_STAGE44_HOURLY_SOURCE";return d
    try:bars,proof=minute_get(row["symbol"],row["date"])
    except FileNotFoundError as e:
        d.update(source_status="CENSORED_DAILY_1M_404",reason=str(e)[:160]);return d
    except ValueError as e:
        if str(e) in ("STAGE38_GAPPED_DAILY_1M","STAGE38_INCOMPLETE_FULL192H_OR_WRONG_UTC"):
            d.update(source_status="CENSORED_DAILY_1M_GAP",reason=str(e));return d
        raise
    original_row={"date":row["date"],"symbol":row["symbol"],"status":"COMPLETE_168H_PUBLISHER_SHA",
         "baseline_1h_open":row["baseline_1h_open"],"max_high_multiple":row["max_high_multiple"],
         "gt2x":row["gt2x"],"gt5x":row["gt5x"],"gt10x":row["gt10x"],
         "publisher_1h_month_sha256":"x"*64}
    # Reuse EXACT Stage39 V4 true 2x/5x/10x timing and 1h-vs-1m parity.
    old_result=old.evaluate(original_row,minute_get=lambda s,t:(bars,proof),runner=runner)
    if old_result["source_status"]==old.CONFLICT:
        d.update(source_status=old.CONFLICT,
           original_1h_baseline_open=row["baseline_1h_open"],
           actual_1m_baseline_open=old_result["actual_1m_anchor_open"],
           original_1h_HIGH_multiple=row["max_high_multiple"],
           minute_high_vs_hour_multiple=old_result["reconstructed_1m_high_multiple_vs_hour_open"],
           verified_9_daily_publisher_sha256=proof)
        return d
    if old_result["source_status"]!=GOOD:raise ValueError("STAGE45_ORIGINAL_V4_INVALID_STATE")
    d.update(old_result)
    d["source_status"]=GOOD
    d["verified_9_daily_publisher_sha256"]=proof
    if old_result["WATCH_UTC"]:
        d.update(score_p1_first_watch(old_result["WATCH_UTC"][0],bars))
    else:
        d["p1_status"]="NO_D0_WATCH"
    if d["p1_status"]==P1GOOD:
        first=original.msutc(d["p1_decision_UTC"])
        for n in (2,5,10):
            crossing=d["first_true_2x_HIGH_minute_UTC"] if n==2 else d["first_real_1m_HIGH_gt"+str(n)+"x_UTC"]
            minute=original.msutc(crossing) if crossing else None
            d["P1_before_1m_high_"+str(n)+"x"]=minute is not None and first<minute
            d["P1_lead_gt"+str(n)+"x_minutes"]=(int((minute-first)/60000) if minute is not None else None)
    return d

def run(day,shard,workers):
    rows=freeze()
    if day not in DATES or shard not in range(6) or workers not in (1,2):
        raise ValueError("STAGE45_NOT_FROZEN_DATE_OR_SHARD")
    cohort=sorted((r for r in rows if r["date"]==day),key=lambda r:r["symbol"])
    selected=[r for i,r in enumerate(cohort) if i%6==shard]
    if len(selected)!=150:raise ValueError("STAGE45_NOT_FULL_UNIVERSE_SHARD")
    done=[];errors=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        jobs={pool.submit(candidate,r):r for r in selected}
        for job in concurrent.futures.as_completed(jobs):
            src=jobs[job]
            try:
                v=job.result()
                if v["symbol"]!=src["symbol"]:raise ValueError("STAGE45_CASE_IDENTITY_CHANGED")
                done.append(v)
            except Exception as e:
                errors.append({"symbol":src["symbol"],"error":type(e).__name__+":"+str(e)[:180]})
            if (len(done)+len(errors))%25==0:
                print("STAGE45_BLIND_MINUTE_PROGRESS "+json.dumps({"date":day,"shard":shard,"done":len(done),"hard_errors":len(errors),"total":150}),flush=True)
    if errors or len(done)!=150:raise RuntimeError("STAGE45_ORIGINAL_SHA_REPLAY_FAIL_CLOSED "+json.dumps(errors[:8]))
    valid=[r for r in done if r["source_status"]==GOOD]
    return {"schema":SCHEMA,"date":day,"shard":shard,"all900_original_frozen":True,"source_cases":len(done),
       "valid_source_with_V4":len(valid),"GT2x_valid":sum(r["original_GT2x_1h"]=="True" for r in valid),
       "GT5x_valid":sum(r["original_GT5x_1h"]=="True" for r in valid),
       "GT10x_valid":sum(r["original_GT10x_1h"]=="True" for r in valid),
       "D0_early_gt2x":sum(r["original_GT2x_1h"]=="True" and r["classification"]=="STRICTLY_EARLY_WATCH" for r in valid),
       "P1_upgrades":sum(r["p1_status"]==P1GOOD for r in valid),
       "source_status":dict(collections.Counter(r["source_status"] for r in done)),
       "rows":sorted(done,key=lambda x:x["symbol"]),"P1v02_changed_on_data":False,
       "other_AI_review":"NOT_DONE","Monster_deployment":"NO_GO","Gmail":"OFF","Frank":"UNCHANGED"}

def test():
    at=original.msutc("2025-01-01T08:00:00Z")
    bars=[(at-61*60000+i*60000,Decimal(100),Decimal(101),Decimal(99),Decimal(100),
           Decimal(10000),100) for i in range(61)]
    v=score_p1_first_watch(original.stamp(at),bars)
    assert v["p1_status"]=="P1_V02_NOT_UPGRADED_D0_PRESERVED"
    bars[-1]=(bars[-1][0],Decimal(100),Decimal(110),Decimal(100),Decimal(110),Decimal(10000),100)
    v=score_p1_first_watch(original.stamp(at),bars)
    assert v["p1_status"]==P1GOOD and v["p1_trigger_arm"]=="RET60"
    future=(at+60000,Decimal(1),Decimal(100000),Decimal(1),Decimal(10000),Decimal(100000000),1)
    assert score_p1_first_watch(original.stamp(at),bars+[future])==v
    assert score_p1_first_watch(original.stamp(at),bars[:-1])["p1_status"]=="P1_SOURCE_UNSCORABLE"
    print("STAGE45_P1_V02_IMMEDIATE_NO_FUTURE_ROLLING_SOURCE_CAUSAL_SELFTEST_PASS")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--selftest",action="store_true")
    p.add_argument("--date")
    p.add_argument("--shard",type=int)
    p.add_argument("--workers",type=int,default=2)
    p.add_argument("--output",type=Path)
    a=p.parse_args()
    if a.selftest:test();return
    if not a.date or a.shard is None or not a.output:p.error("--date --shard --output required")
    out=run(a.date,a.shard,a.workers)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(out,ensure_ascii=False,sort_keys=True,indent=2)+"\n")
    print("STAGE45_REAL_BLIND_ORIGINAL_V4_P1V02_SOURCE_SHA "+json.dumps({
        k:out[k] for k in ("date","shard","valid_source_with_V4","GT2x_valid","D0_early_gt2x","P1_upgrades")},sort_keys=True))
if __name__=="__main__":main()
