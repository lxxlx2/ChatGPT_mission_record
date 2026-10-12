#!/usr/bin/env python3
"""Stage35: original V4 first WATCH vs same-day ordinary coin-date controls.
Read only. Source SHA verified. Features only from closed 1m bars known at signal.
No BTC/trade return/24h holding, no future as feature, no strategy retuning.
"""
import argparse,concurrent.futures,csv,hashlib,json,statistics
from datetime import datetime,timedelta,timezone
from decimal import Decimal
from pathlib import Path
try:
    import monster_v4_archive_universe_replay as source
except ImportError:
    from scripts import monster_v4_archive_universe_replay as source

EVIDENCE=Path(__file__).resolve().parents[2]/"monster"/"evidence"
PREREG=EVIDENCE/"monster_stage35_18date_first_watch_causal_feature_census_prereg_20261012.json"
CENSUS=EVIDENCE/"monster_stage34_full18date_13644_coin_date_controls.csv"
SCHEMA="MONSTER_STAGE35_CAUSAL_FIRST_WATCH_EXPOSED18_DATE_FEATURE_V1"

def sha(v):return hashlib.sha256(v).hexdigest()
def blob(v):
    data=Path(v).read_bytes()
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()
def utc_ms(v):return int(datetime.fromisoformat(v.replace("Z","+00:00")).timestamp()*1000)

def freeze():
    p=json.loads(PREREG.read_text(encoding="utf-8"))
    if p.get("schema")!="MONSTER_STAGE35_FULL18_DATE_FIRST_WATCH_CAUSAL_FEATURE_CENSUS_PRE_SOURCE_V1" or blob(CENSUS)!=p["immutable_stage34_source"]["git_blob_sha1"]:
        raise ValueError("STAGE35_FROZEN_SOURCE_OR_PROTOCOL_DRIFT")
    with CENSUS.open(encoding="utf-8",newline="") as f:
        rows=list(csv.DictReader(f))
    dates=sorted({r["date"] for r in rows})
    if len(rows)!=13644 or len(dates)!=18 or len({(r["date"],r["symbol"]) for r in rows})!=13644:
        raise ValueError("STAGE35_INPUT_COVERAGE_DRIFT")
    if sum(r["joint_source_complete"]=="1" for r in rows)!=7776 or sum(r["joint_source_complete"]=="1" and int(r["watch_count_3m"])>0 for r in rows)!=1227:
        raise ValueError("STAGE35_COHORT_SOURCE_DRIFT")
    return p,rows,dates

def choose(rows,day):
    valid=[r for r in rows if r["date"]==day and r["joint_source_complete"]=="1"]
    watch=[r for r in valid if int(r["watch_count_3m"])>0]
    nonwatch=[r for r in valid if int(r["watch_count_3m"])==0]
    if not watch or len(nonwatch)<20:raise ValueError("STAGE35_NO_CONTROLS")
    clocks=sorted(x["first_watch_utc_3m"] for x in watch)
    controls=sorted(nonwatch,key=lambda r:(sha((day+"|"+r["symbol"]).encode()),r["symbol"]))[:20]
    cases=[{**r,"asof_utc":r["first_watch_utc_3m"],"cohort":"FIRST_WATCH"} for r in watch]
    for r in controls:
        index=int(sha((day+"|"+r["symbol"]).encode()),16)%len(clocks)
        cases.append({**r,"asof_utc":clocks[index],"cohort":"SAME_DATE_OTHER_WATCH_CLOCK_CONTROL"})
    if len({r["symbol"] for r in cases})!=len(cases):raise ValueError("STAGE35_DUPLICATE_CASE")
    return sorted(cases,key=lambda r:r["symbol"]),len(watch)

def features(ms,bars):
    previous={row[0]:row for row in bars if row[0]<ms}
    stamps=[ms-(i+1)*60000 for i in range(61)]
    if any(t not in previous for t in stamps):raise ValueError("STAGE35_MISSING_CLOSED_1M_SOURCE")
    xs=[previous[t] for t in stamps]
    if any(min(v[1],v[2],v[3],v[4])<=0 or v[5]<0 or v[6]<0 for v in xs):
        raise ValueError("STAGE35_INVALID_SOURCE_BAR")
    q=lambda seq:sum((v[5] for v in seq),Decimal(0))
    q1,q3,q15,q60=xs[0][5],q(xs[:3]),q(xs[:15]),q(xs[:60])
    prev45=q(xs[15:60])
    o,h,l,c=xs[0][1],xs[0][2],xs[0][3],xs[0][4]
    if h<max(o,c) or l>min(o,c) or h<l:raise ValueError("STAGE35_BAD_LAST_BAR")
    pct=lambda prior:round(float((c/prior-1)*100),6)
    return {
      "return_3m_pct":pct(xs[3][4]),"return_15m_pct":pct(xs[15][4]),"return_60m_pct":pct(xs[60][4]),
      "quote_1m_usdt":round(float(q1),5),"quote_3m_usdt":round(float(q3),5),
      "quote_15m_usdt":round(float(q15),5),"quote_60m_usdt":round(float(q60),5),
      "quote_15m_vs_prior45m_normalized":round(float(q15/(prev45/3)),6) if prev45>0 else None,
      "last1m_share_of_60m_quote":round(float(q1/q60),6) if q60>0 else None,
      "trades_1m":xs[0][6],"trades_15m":sum(v[6] for v in xs[:15]),
      "trades_60m":sum(v[6] for v in xs[:60]),
      "positive_trade_minutes_60m":sum(v[6]>0 for v in xs[:60]),
      "last_minute_upper_wick_fraction":round(float((h-max(o,c))/(h-l)),6) if h>l else None,
      "close_vs_last60m_high_pct":round(float((c/max(v[2] for v in xs[:60])-1)*100),6),
      "only_closed_bars":True
    }

def extract(r,getday=source.get_day):
    ms=utc_ms(r["asof_utc"])
    if ms%60000:raise ValueError("STAGE35_NOT_ALIGNED_MINUTE")
    now=datetime.fromtimestamp(ms/1000,timezone.utc).date()
    start=int(datetime(now.year,now.month,now.day,tzinfo=timezone.utc).timestamp()*1000)
    days=([now-timedelta(days=1),now] if ms-61*60000<start else [now])
    rows=[];publisher=[]
    for day in days:
        k,proof=getday(r["symbol"],day)
        if len(k)!=1440 or not proof.get("verified_published_sha256") or len(proof["sha256"])!=64:
            raise ValueError("STAGE35_UNVERIFIED_OR_GAPPED_OFFICIAL_ARCHIVE")
        rows.extend(k)
        publisher.append({"date":day.isoformat(),"sha256":proof["sha256"]})
    return {"date":r["date"],"symbol":r["symbol"],"stage":int(r["stage"]),"cohort":r["cohort"],
            "asof_utc":r["asof_utc"],"label_future_calendar_2x":int(r["future_2x_high"]),
            "label_future_calendar_5x":int(r["future_5x_high"]),
            "label_future_calendar_10x":int(r["future_10x_high"]),
            "first_2x_watch_class":r["first_2x_watch_class"],
            "first_2x_cross_utc":r["first_2x_high_cross_utc"],
            "original_watch_count":int(r["watch_count_3m"]),"publisher_sha256":publisher,
            **features(ms,rows)}

def run_date(day,workers=4):
    _,rows,dates=freeze()
    if day not in dates or workers not in range(1,5):raise ValueError("STAGE35_NONFROZEN_DATE_OR_WORKERS")
    cases,nw=choose(rows,day)
    result=[];failures=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        jobs={pool.submit(extract,r):r for r in cases}
        for job in concurrent.futures.as_completed(jobs):
            r=jobs[job]
            try:result.append(job.result())
            except Exception as e:failures.append({"symbol":r["symbol"],"type":type(e).__name__,"reason":str(e)[:160]})
            if (len(result)+len(failures))%30==0:
                print("STAGE35_PROGRESS "+json.dumps({"date":day,"done":len(result),"failed":len(failures),"total":len(cases)}),flush=True)
    report={"schema":SCHEMA,"date":day,"expected_watch":nw,"expected_controls":20,
            "complete_features":len(result),"source_errors":failures,"rows":sorted(result,key=lambda r:r["symbol"]),
            "model_trained":False,"other_ai_review":"NOT_DONE","deployment":"NO_GO","gmail":"OFF","trading":"NO_GO"}
    if failures or len(result)!=len(cases):
        raise RuntimeError("STAGE35_FAILED_SOURCE_NOT_ZERO "+json.dumps(failures[:6]))
    return report

def selftest():
    ms=1704070800000
    bars=[(ms-(i+1)*60000,Decimal(100),Decimal(101),Decimal(99),Decimal(100),Decimal(10),2) for i in range(61)]
    f=features(ms,bars)
    assert f["return_60m_pct"]==0 and f["quote_60m_usdt"]==600 and f["trades_60m"]==120
    assert f["quote_15m_vs_prior45m_normalized"]==1 and f["positive_trade_minutes_60m"]==60
    try:features(ms,bars[:-1])
    except ValueError as e:assert "MISSING_CLOSED" in str(e)
    else:raise AssertionError("STAGE35_FORBID_SHORT_SOURCE")
    try:features(ms,bars+[ (ms+60000,Decimal(100),Decimal(200),Decimal(1),Decimal(150),Decimal(0),0) ])
    except ValueError:raise AssertionError("FUTURE_BAR_UNNECESSARILY_INCLUDED")
    print("STAGE35_FEATURE_NO_LOOKAHEAD_SELFTEST_PASS")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--selftest",action="store_true")
    p.add_argument("--date")
    p.add_argument("--output",type=Path)
    p.add_argument("--workers",type=int,default=4)
    a=p.parse_args()
    if a.selftest:selftest();return
    if not a.date or not a.output:p.error("--date and --output required")
    r=run_date(a.date,a.workers)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(r,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print("STAGE35_REAL_OFFICIAL_SHA_COMPLETE "+json.dumps({"date":a.date,"watch":r["expected_watch"],"control":20}))
if __name__=="__main__":main()
