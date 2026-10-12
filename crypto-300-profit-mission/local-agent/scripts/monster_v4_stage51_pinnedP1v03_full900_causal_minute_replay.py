#!/usr/bin/env python3
"""Monster Stage51: unchanged original V4 D0, frozen P1v03 continual 3m re-evaluation.

Full 900 historic symbols x6 pre-sealed dates, official Binance USD-M daily 1m
publisher SHA, future 2x HIGH used only as a post-signal evaluation label.
No threshold calibration, no global delivery claim (Stage52), no actual BUY.
"""
import argparse,collections,concurrent.futures,json
from decimal import Decimal
from pathlib import Path
try:
    import monster_v4_stage38_usdm_original_v4_1m_pilot as src
    import monster_v4_stage39_usdm_all900_sixday_original_1m as originalV4
except ImportError:
    from scripts import monster_v4_stage38_usdm_original_v4_1m_pilot as src
    from scripts import monster_v4_stage39_usdm_all900_sixday_original_1m as originalV4

E=Path(__file__).resolve().parents[2]/"monster"/"evidence"
DATA=E/"monster_stage50_full5400_blind_source_publisher_hourly_SHA.jsonl"
SUMMARY=E/"monster_stage50_original36_sha_six_blind_900x6_hourly_GT_summary.json"
FREEZE=E/"monster_stage49_v03_second_ignition_strategy_and_holdout_prereg_20261012.json"
DATES=("2025-01-30","2025-06-02","2025-08-01","2025-10-02","2026-06-21","2026-07-28")
SCHEMA="MONSTER_STAGE51_NEW_SIX_DATE_ALL5400_ORIGINAL_V4_ASOF_3M_P1V03_REIGNITION_UNBUDGETED_V1"
D=Decimal;ONE=60000
GOOD="COMPLETE_REAL_USDM_1M_SHA_CAUSAL_V4"

def frozen():
    p=json.loads(FREEZE.read_text())
    gt=json.loads(SUMMARY.read_text())
    if (src.blob(FREEZE)!="c3c3d2f1b587a0c0202cba54f9889174c29ecdb7" or
        src.blob(DATA)!="040f7a8425f313a99ef484067baff34245fcb0c8" or
        src.blob(SUMMARY)!="05dfa401de9dbd33f8ae60d9dc84034d9b0469ca" or
        src.blob(src.production.__file__)!=src.ORIGINAL_V4_GIT_BLOB or
        p["schema"]!="MONSTER_STAGE49_V03_SECOND_IGNITION_PRIOR_TO_NEW_USDM_MARKET_PRICE_PREREG_V1" or
        tuple(p["dates"])!=DATES or
        p["priority_hypothesis"]["initial_urgent_gate"]!="At FIRST original D0 WATCH only: ret60_pct >=14 AND quote15_USDT >=3000000 AND quote15_normalized_prev45 >=1.5" or
        p["priority_hypothesis"]["reignition_gate"]!="At any later closed 3-minute polling clock following first D0: close_relative_first_watch_close_pct >=15 AND ret60_pct >=8 AND quote15_USDT >=2000000 AND quote15_normalized_prev45 >=1.5"):
        raise ValueError("STAGE51_FROZEN_P1V03_HOURLY_SOURCE_OR_PRODUCTION_V4_CHANGED")
    if (gt["attempted"],gt["source_complete"],gt["gross2x_high"],gt["gross5x_high"],gt["gross10x_high"])!=(5400,3456,30,3,2):
        raise ValueError("STAGE51_STAGE50_GT_COUNTER_DRIFT")
    rows=[json.loads(x) for x in DATA.read_text().splitlines() if x]
    if len(rows)!=5400 or len({(r["date"],r["symbol"]) for r in rows})!=5400:
        raise ValueError("STAGE51_ALL5400_SOURCE_DRIFT")
    return rows

def at(bars,pref,t,first_price):
    if t%ONE:raise ValueError("STAGE51_NOT_MINUTE_BOUNDARY")
    i=(t-bars[0][0])//ONE-1
    if i<60 or i>=len(bars) or bars[i][0]!=t-ONE:
        raise ValueError("STAGE51_NOT_REAL_CLOSED_MINUTE")
    price,prior=bars[i][4],bars[i-60][4]
    if min(price,prior,first_price)<=0:raise ValueError("STAGE51_BAD_PRICE")
    q15=pref[i+1]-pref[i-14]
    q45=pref[i-14]-pref[i-59]
    if min(q15,q45)<0:raise ValueError("STAGE51_BAD_QUOTE")
    ratio=D(3)*q15/q45 if q45>0 else None
    return {"ret60_pct":(price/prior-1)*100,
      "quote15_USDT":q15,"quote_prior45_USDT":q45,
      "quote15_normalized_prev45":ratio,
      "ret_from_first_D0_pct":(price/first_price-1)*100,
      "last_closed_price":price}

def allowed(f,is_first):
    ratio=f["quote15_normalized_prev45"]
    if ratio is None or ratio<D("1.5"):return False
    if is_first:
        return f["ret60_pct"]>=14 and f["quote15_USDT"]>=3000000
    return (f["ret_from_first_D0_pct"]>=15 and f["ret60_pct"]>=8
            and f["quote15_USDT"]>=2000000)

def find_candidate(bars,watch_utc,day):
    if not watch_utc:return None
    begin=src.msutc(day+"T06:00:00Z")
    end=begin+168*3600000
    first=src.msutc(watch_utc[0])
    if first<begin or first>=end or (first-begin)%180000:
        raise ValueError("STAGE51_D0_NOT_IN_FROZEN_CAUSAL_SCAN")
    if any(src.msutc(w)<begin or src.msutc(w)>=end for w in watch_utc):
        raise ValueError("STAGE51_D0_WATCH_OUTSIDE_WINDOW")
    pref=[D(0)]
    for b in bars:pref.append(pref[-1]+b[5])
    first_i=(first-bars[0][0])//ONE-1
    if first_i<60 or bars[first_i][0]!=first-ONE:
        raise ValueError("STAGE51_FIRST_WATCH_MISSING_CLOSED_BAR")
    first_price=bars[first_i][4]
    for tick,t in enumerate(range(first,end,180000)):
        f=at(bars,pref,t,first_price)
        if allowed(f,is_first=(tick==0)):
            return {"at_UTC":src.stamp(t),
              "kind":"FIRST_D0_IMMEDIATE" if tick==0 else "ONGOING_3M_SECOND_IGNITION",
              "first_D0_watch_UTC":watch_utc[0],
              "polls_until_eligible":tick+1,
              "features":{k:(str(v) if v is not None else None) for k,v in f.items()},
              "publisher_verified_asof_no_future_source":True}
    return None

def case(row,loader=src.minute_source,scanner=src.production_scan):
    r={"date":row["date"],"symbol":row["symbol"],
       "hourly_status":row["source_status"],
       "hourly_gt2x":row.get("gt2x"),"hourly_gt5x":row.get("gt5x"),
       "hourly_gt10x":row.get("gt10x"),"source_status":"UNKNOWN",
       "p1v03_eligible_unbudgeted":None}
    if row["source_status"]!="COMPLETE_168H_OFFICIAL_PUBLISHER_SHA":
        r["source_status"]="CENSORED_STAGE50_HOURLY";return r
    try:bars,proof=loader(row["symbol"],row["date"])
    except FileNotFoundError as e:
        r.update(source_status="CENSORED_DAILY_1M_404",source_reason=str(e)[:160]);return r
    except ValueError as e:
        if str(e) in ("STAGE38_GAPPED_DAILY_1M","STAGE38_INCOMPLETE_FULL192H_OR_WRONG_UTC"):
            r.update(source_status="CENSORED_DAILY_1M_GAP",source_reason=str(e));return r
        raise
    original_input={"date":row["date"],"symbol":row["symbol"],
      "status":"COMPLETE_168H_PUBLISHER_SHA",
      "baseline_1h_open":row["baseline_1h_open"],
      "max_high_multiple":row["max_high_multiple"],
      "gt2x":str(row["gt2x"]),"gt5x":str(row["gt5x"]),"gt10x":str(row["gt10x"]),
      "publisher_1h_month_sha256":row["source_proofs"][0]["publisher_ZIP_sha256"]}
    baseline=originalV4.evaluate(original_input,minute_get=lambda symbol,day:(bars,proof),runner=scanner)
    if baseline["source_status"]==originalV4.CONFLICT:
        r.update(source_status=originalV4.CONFLICT,
          monthly_1h_publisher_SHAs=row["source_proofs"],
          daily_1m_publisher_SHAs=proof,
          hourly_start_price=row["baseline_1h_open"],
          minute_start_price=baseline["actual_1m_anchor_open"])
        return r
    if baseline["source_status"]!=GOOD:raise ValueError("STAGE51_ORIGINAL_V4_INVALID")
    r.update(baseline)
    r.update(source_status=GOOD,
      source_hourly_official_SHA=row["source_proofs"],
      source_daily_minute_official_SHA=proof,
      original_V4_unchanged=True,
      p1v03_eligible_unbudgeted=find_candidate(bars,baseline["WATCH_UTC"],row["date"]))
    return r

def run(day,shard,workers=2):
    rows=frozen()
    if day not in DATES or shard not in range(6) or workers not in (1,2,3):
        raise ValueError("STAGE51_INVALID_DATE_SHARD")
    group=sorted([r for r in rows if r["date"]==day],key=lambda r:r["symbol"])
    group=[r for i,r in enumerate(group) if i%6==shard]
    if len(group)!=150:raise ValueError("STAGE51_NOT_ALL900")
    rowsout=[];errors=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futures={pool.submit(case,r):r for r in group}
        for f in concurrent.futures.as_completed(futures):
            rr=futures[f]
            try:
                x=f.result()
                if x["date"]!=rr["date"] or x["symbol"]!=rr["symbol"]:
                    raise ValueError("STAGE51_WRONG_COIN_RETURN")
                rowsout.append(x)
            except Exception as e:
                errors.append({"symbol":rr["symbol"],"error":type(e).__name__+":"+str(e)[:180]})
            if (len(errors)+len(rowsout))%30==0:
                print("STAGE51_PROGRESS "+json.dumps({"date":day,"shard":shard,"seen":len(errors)+len(rowsout),"errors":len(errors)}),flush=True)
    if errors or len(rowsout)!=150:
        raise RuntimeError("STAGE51_REAL_OFFICIAL_SOURCE_OR_MODEL_FAIL_CLOSED "+json.dumps(errors[:7]))
    valid=[r for r in rowsout if r["source_status"]==GOOD]
    return {"schema":SCHEMA,"date":day,"shard":shard,"original_symbol_count":150,
      "source_complete":len(valid),
      "gt2x_valid":sum(x["hourly_gt2x"] for x in valid),
      "p1v03_unbudgeted":sum(bool(x["p1v03_eligible_unbudgeted"]) for x in valid),
      "original_status":dict(collections.Counter(x["source_status"] for x in rowsout)),
      "rows":sorted(rowsout,key=lambda x:x["symbol"]),
      "do_not_treat_as_delivered_alert":True,"no_mac_deploy":True,"Frank":"UNCHANGED"}

def test():
    start=src.msutc("2025-01-30T06:00:00Z")-24*3600000
    bars=[(start+i*ONE,D(100),D(101),D(99),D(100),D(100000),1) for i in range(1000)]
    pref=[D(0)]
    for b in bars:pref.append(pref[-1]+b[5])
    t=start+200*ONE
    x=at(bars,pref,t,D(100))
    assert x["ret60_pct"]==0 and x["quote15_USDT"]==1500000
    assert not allowed(x,True) and not allowed(x,False)
    index=(t-start)//ONE
    bars[index]=(bars[index][0],D(100),D(999999),D(1),D(12345),D("1e12"),2)
    assert at(bars,pref,t,D(100))==x
    y=dict(x,ret60_pct=D(15),quote15_USDT=D(3500000),quote15_normalized_prev45=D(2))
    assert allowed(y,True)
    z=dict(x,ret60_pct=D(9),quote15_USDT=D(2500000),ret_from_first_D0_pct=D(20),quote15_normalized_prev45=D(2))
    assert allowed(z,False) and not allowed(z,True)
    z["ret_from_first_D0_pct"]=D(14)
    assert not allowed(z,False)
    print("STAGE51_TRUE_CLOSED_MINUTE_ORIGINAL_V4_SECOND_IGNITION_ASOF_TEST_PASS")

def main():
    p=argparse.ArgumentParser();p.add_argument("--selftest",action="store_true")
    p.add_argument("--date");p.add_argument("--shard",type=int)
    p.add_argument("--workers",type=int,default=2);p.add_argument("--out",type=Path)
    a=p.parse_args()
    if a.selftest:test();return
    if not a.date or a.shard is None or not a.out:p.error("--date --shard --out required")
    result=run(a.date,a.shard,a.workers)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+"\n")
    print("STAGE51_TRUE_MINUTE_SHA_FROZEN_V03_NOT_BUDGETED "+json.dumps({
      k:result[k] for k in ("date","shard","source_complete","gt2x_valid","p1v03_unbudgeted")},sort_keys=True))
if __name__=="__main__":main()
