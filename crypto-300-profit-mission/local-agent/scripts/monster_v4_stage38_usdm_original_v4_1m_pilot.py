#!/usr/bin/env python3
"""Monster Stage38 original production V4 USD-M real 1m causal discovery pilot.

Historical retrospective 52 full-source GT2x + 20 label-blind non-2x/date,
all 6 preregistered dates. NO BTC, trade profit, holding assumption, live task,
model fitting, threshold change, email send, cross-symbol queue claim or deployment.
Official Binance futures daily 1m ZIP and publisher .CHECKSUM are mandatory.
"""
import argparse,bisect,concurrent.futures,csv,hashlib,io,json,re,statistics,tempfile,time,urllib.error,urllib.request,zipfile
from collections import Counter
from datetime import date,datetime,timedelta,timezone
from decimal import Decimal
from pathlib import Path

try:
    import monster_v4_shadow as production
    import monster_v4_historical_replay as replay
except ImportError:
    from scripts import monster_v4_shadow as production
    from scripts import monster_v4_historical_replay as replay

EVIDENCE=Path(__file__).resolve().parents[2]/"monster"/"evidence"
PREREG=EVIDENCE/"monster_stage38_futures_original_v4_causal_pilot_prereg_20261012.json"
STAGE37=EVIDENCE/"monster_stage37_sixdate_all5400_usdm_source_and_GT.csv"
SCHEMA="MONSTER_STAGE38_REAL_BINANCE_UM_1M_ORIGINAL_V4_FUTURES_CAUSAL_PILOT_V1"
ORIGINAL_V4_GIT_BLOB="bc958b3d90a8a52afa51515cb53f7e5fafaffaaa"
BASE="https://data.binance.vision/data/futures/um/daily/klines/"
MINUTE_MS=60000
WARMUP=1440
ACTIVE=10080
BARS=11520
MAX_ZIP=15_000_000

def blob(path):
    b=Path(path).read_bytes()
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
def sha(b):return hashlib.sha256(b).hexdigest()
def stamp(ms):return datetime.fromtimestamp(ms/1000,timezone.utc).isoformat().replace("+00:00","Z")
def msutc(text):return int(datetime.fromisoformat(text.replace("Z","+00:00")).timestamp()*1000)

def lock():
    spec=json.loads(PREREG.read_text(encoding="utf-8"))
    if (spec.get("schema")!="MONSTER_STAGE38_FROZEN_USDM_52_GT2X_PLUS_120_BLIND_NON2X_CAUSAL_V4_PILOT_V1" or
        blob(STAGE37)!=spec["original_stage37_source"]["git_blob_sha1"] or
        blob(production.__file__)!=ORIGINAL_V4_GIT_BLOB or
        spec["original_52_positives_plus_120_controls_expected"]!=172):
        raise ValueError("STAGE38_SOURCE_PRODUCTION_OR_FROZEN_COHORT_DRIFT")
    with STAGE37.open(encoding="utf-8",newline="") as f:
        records=list(csv.DictReader(f))
    if len(records)!=5400 or len({(r["date"],r["symbol"]) for r in records})!=5400:
        raise ValueError("STAGE38_BAD_ORIGINAL5400_SOURCE")
    complete=[r for r in records if r["status"]=="COMPLETE_168H_PUBLISHER_SHA"]
    if len(complete)!=3333 or sum(r["gt2x"]=="True" for r in complete)!=52:
        raise ValueError("STAGE38_FROZEN_GT_DRIFT")
    dates=spec["frozen_dates"]
    if len(dates)!=6 or any(sum(r["date"]==d for r in records)!=900 for d in dates):
        raise ValueError("STAGE38_SIX_DATE_900_WRONG")
    return spec,complete

def select(day,all_rows):
    full=[r for r in all_rows if r["date"]==day]
    winners=sorted((r for r in full if r["gt2x"]=="True"),key=lambda r:r["symbol"])
    normal=sorted((r for r in full if r["gt2x"]=="False"),
                  key=lambda r:(sha((day+"|"+r["symbol"]).encode()),r["symbol"]))[:20]
    assert len(normal)==20 and not any(r in winners for r in normal)
    return [dict(r,cohort=("FROZEN_GT_2X_CASE" if r in winners else "LABEL_BLIND_HASH_CONTROL")) for r in
            sorted(winners+normal,key=lambda r:r["symbol"])],len(winners)

def url(symbol,day):
    if not re.fullmatch(r"[A-Z0-9]+USDT",symbol):raise ValueError("STAGE38_BAD_USDM_SYMBOL")
    return BASE+symbol+"/1m/"+symbol+"-1m-"+day.isoformat()+".zip"
def get(uri,limit):
    request=urllib.request.Request(uri,headers={"User-Agent":"Monster-V4-Stage38-Publisher-SHA/1.0"})
    with urllib.request.urlopen(request,timeout=32) as r:
        b=r.read(limit+1)
    if not b or len(b)>limit:raise ValueError("STAGE38_EMPTY_OR_OVERSIZE_BINANCE")
    return b

def verified_1m_day(symbol,day,reader=get):
    source=url(symbol,day)
    payload=None;receipt=None
    for attempt in range(3):
        try:
            payload=reader(source,MAX_ZIP)
            receipt=reader(source+".CHECKSUM",2048)
            break
        except urllib.error.HTTPError as e:
            if e.code==404:raise FileNotFoundError("ORIGINAL_FUTURES_1M_DAILY_ZIP_404 "+day.isoformat()) from e
            if attempt==2:raise
        except (urllib.error.URLError,ConnectionError,TimeoutError,OSError):
            if attempt==2:raise
        time.sleep(1+attempt)
    spec=receipt.decode("utf-8","strict").strip().split()
    if not spec or not re.fullmatch(r"[A-Fa-f0-9]{64}",spec[0]):
        raise ValueError("STAGE38_MISSING_PUBLISHER_CHECKSUM")
    checksum=sha(payload)
    if checksum!=spec[0].lower():
        raise ValueError("STAGE38_OFFICIAL_ZIP_HASH_NOT_MATCH_PUBLISHER")
    member=f"{symbol}-1m-{day.isoformat()}.csv"
    with zipfile.ZipFile(io.BytesIO(payload)) as z:
        if z.namelist()!=[member] or z.getinfo(member).file_size>25_000_000:
            raise ValueError("STAGE38_WRONG_MEMBER_OR_UNCOMPRESSED_BOMB")
        raw=z.read(member)
    data=[]
    for idx,row in enumerate(csv.reader(io.StringIO(raw.decode("utf-8-sig")))):
        if idx==0 and len(row)>=9 and row[0].strip().lower() in ("open_time","open time","opentime"):
            continue
        if len(row)<9 or not row[0].isdigit():raise ValueError("STAGE38_INVALID_USDM_1M_CSV_LINE")
        timestamp=int(row[0])
        if timestamp>=10**15:
            if timestamp%1000:raise ValueError("STAGE38_INVALID_MICROSECONDS")
            timestamp//=1000
        if timestamp<10**12 or timestamp%60000:
            raise ValueError("STAGE38_NOT_FULL_MINUTE")
        o,h,l,c,q=(Decimal(row[k]) for k in (1,2,3,4,7))
        n=int(row[8])
        if min(o,h,l,c)<=0 or q<0 or n<0 or h<max(o,c) or l>min(o,c) or h<l:
            raise ValueError("STAGE38_INVALID_OHLC_OR_TRADES")
        data.append((timestamp,o,h,l,c,q,n))
    start=msutc(day.isoformat()+"T00:00:00Z")
    if len(data)!=1440 or any(r[0]!=start+i*MINUTE_MS for i,r in enumerate(data)):
        raise ValueError("STAGE38_GAPPED_DAILY_1M")
    return data,{"date":day.isoformat(),"zip_sha256":checksum,
                 "verified_official_publisher_SHA256":True,"bars":len(data)}

def minute_source(symbol,day,reader=verified_1m_day):
    begin=msutc(day+"T06:00:00Z")-24*3600000
    raw=[];proof=[]
    for n in range(-1,8):
        curr=date.fromisoformat(day)+timedelta(days=n)
        bars,p=reader(symbol,curr)
        raw+=bars;proof.append(p)
    offset=6*60
    bars=raw[offset:offset+BARS]
    if len(bars)!=BARS or any(x[0]!=begin+i*MINUTE_MS for i,x in enumerate(bars)):
        raise ValueError("STAGE38_INCOMPLETE_FULL192H_OR_WRONG_UTC")
    if len(proof)!=9:raise ValueError("STAGE38_NOT_ALL9_SOURCE_DAYS")
    return bars,proof

def production_scan(symbol,day,bars):
    if len(bars)!=BARS:raise ValueError("STAGE38_NEED_ALL192H_SOURCE")
    anchor=msutc(day+"T06:00:00Z")
    start=anchor-24*3600000
    assert bars[0][0]==start and bars[WARMUP][0]==anchor
    prefix=[Decimal(0)]
    for b in bars:prefix.append(prefix[-1]+b[5])
    candles=replay.make_closed_five_minute_bars(bars)
    ends=[int(x[6]) for x in candles]
    polls=0
    with tempfile.TemporaryDirectory(prefix="monster38_futures_") as td:
        db=production.open_store(Path(td)/"isolated_actual_production.sqlite")
        try:
            def five_minute(_venue,_symbol,now_ms):
                k=bisect.bisect_left(ends,now_ms)
                return candles[max(0,k-8):k]
            for i in range(WARMUP+2,WARMUP+ACTIVE,3):
                ms=bars[i][0]+MINUTE_MS
                q=prefix[i+1]-prefix[i+1-1440]
                production.observe_snapshot(db,"futures",ms,[{
                    "symbol":symbol,"lastPrice":str(bars[i][4]),"quoteVolume":str(q)}])
                production.process_queue(db,ms,five_minute)
                polls+=1
            events=[dict(x) for x in db.execute(
                "SELECT event_type,observed_ms FROM events ORDER BY observed_ms,event_id")]
        finally:db.close()
    if polls!=3360:raise ValueError("STAGE38_WRONG_CAUSAL_POLL_COUNT")
    watch=[stamp(x["observed_ms"]) for x in events if x["event_type"]=="WATCH_EARLY"]
    setup=[stamp(x["observed_ms"]) for x in events if x["event_type"]=="SETUP_ACTIVE"]
    return {"polls":polls,"watch_count":len(watch),"WATCH_UTC":watch,"SETUP_UTC":setup,
            "setup_count":len(setup),"state":"ONE_SQLITE_PER_FUTURES_SYMBOL_ORIGINAL_V4_NO_GLOBAL_QUEUE"}

def score(row,bars,replay_result):
    first_open=bars[WARMUP][1]
    historical_open=Decimal(row["baseline_1h_open"])
    if first_open!=historical_open:
        raise ValueError("STAGE38_ORIGINAL_HOURLY_VS_1M_BASELINE_DIFFER")
    realized_max=max(x[2] for x in bars[WARMUP:WARMUP+ACTIVE])
    original_max=Decimal(row["max_high_multiple"])
    if realized_max/historical_open!=original_max:
        raise ValueError("STAGE38_MONTHLY_1H_HIGH_VS_DAILY_1M_MAX_MISMATCH")
    threshold=historical_open*2
    crossing=next((x[0] for x in bars[WARMUP:WARMUP+ACTIVE] if x[2]>=threshold),None)
    if (crossing is not None)!=(row["gt2x"]=="True"):
        raise ValueError("STAGE38_FROZEN_HOURLY_2X_VS_REAL_MINUTE_DISAGREE")
    watches=[msutc(w) for w in replay_result["WATCH_UTC"]]
    prior=[w for w in watches if crossing is not None and w<crossing]
    if crossing is None:classification="NO_CALENDAR_2X"
    elif prior:classification="STRICTLY_EARLY_WATCH"
    elif watches and min(watches)==crossing:classification="SAME_MINUTE_NOT_EARLY"
    elif watches:classification="WATCH_LATE"
    else:classification="NO_WATCH"
    return {"classification":classification,
            "first_true_2x_HIGH_minute_UTC":stamp(crossing) if crossing is not None else None,
            "earliest_watch_lead_min":round((crossing-watches[0])/60000,3) if crossing is not None and watches else None,
            "nearest_strictly_earlier_WATCH_lead_min":round((crossing-max(prior))/60000,3) if prior else None}

def analyze_case(row,minute_get=minute_source,scanner=production_scan):
    x={"date":row["date"],"symbol":row["symbol"],"cohort":row["cohort"],
       "original_1h_publisher_sha256":row["publisher_1h_month_sha256"],
       "frozen_GT2x":row["gt2x"]=="True","source_status":"UNKNOWN"}
    try:
        bars,proof=minute_get(row["symbol"],row["date"])
    except FileNotFoundError as e:
        x.update(source_status="CENSORED_DAILY_1M_404",source_reason=str(e)[:170])
        return x
    except ValueError as e:
        if str(e) in ("STAGE38_GAPPED_DAILY_1M","STAGE38_INCOMPLETE_FULL192H_OR_WRONG_UTC"):
            x.update(source_status="CENSORED_DAILY_1M_GAP",source_reason=str(e))
            return x
        raise
    actual=scanner(row["symbol"],row["date"],bars)
    label=score(row,bars,actual)
    x.update(source_status="COMPLETE_REAL_USDM_1M_SHA_CAUSAL_V4",
             official_9_daily_1m_publisher_SHA256=proof,
             unchanged_original_v4_futures=True,**actual,**label)
    return x

def run(day,shard,workers=2):
    p,valid=lock()
    if day not in p["frozen_dates"] or shard not in (0,1) or workers not in (1,2):
        raise ValueError("STAGE38_INVALID_DAY_SHARD_WORKERS")
    selected,nw=select(day,valid)
    chosen=[r for i,r in enumerate(selected) if i%2==shard]
    items=[];errors=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        jobs={pool.submit(analyze_case,r):r for r in chosen}
        for job in concurrent.futures.as_completed(jobs):
            r=jobs[job]
            try:
                x=job.result()
                if x["symbol"]!=r["symbol"]:raise ValueError("STAGE38_WRONG_JOB_SYMBOL")
                items.append(x)
            except Exception as e:
                errors.append({"symbol":r["symbol"],"error":type(e).__name__+":"+str(e)[:180]})
            if (len(items)+len(errors))%8==0:
                print("STAGE38_PROGRESS "+json.dumps({"date":day,"shard":shard,"seen":len(items),"hard_errors":len(errors),"expected":len(chosen)}),flush=True)
    if errors or len(items)!=len(chosen):
        raise RuntimeError("STAGE38_ORIGINAL_SOURCE_FAIL_CLOSED "+json.dumps(errors[:6]))
    complete=[x for x in items if x["source_status"]=="COMPLETE_REAL_USDM_1M_SHA_CAUSAL_V4"]
    return {"schema":SCHEMA,"date":day,"shard":shard,"original_expected":len(chosen),
            "original_date_GT2x":nw,"result":sorted(items,key=lambda x:x["symbol"]),
            "complete_replay":len(complete),"source_censored":len(items)-len(complete),
            "complete_gt2x":sum(x["frozen_GT2x"] for x in complete),
            "strictly_early_gt2x":sum(x["classification"]=="STRICTLY_EARLY_WATCH" and x["frozen_GT2x"] for x in complete),
            "source_errors":errors,"model_untouched":True,"BTC":"NOT_USED",
            "other_AI_review":"NOT_DONE","deployment":"NO_GO","Frank":"UNCHANGED","Gmail":"OFF","trading":"NO_GO"}

def selftest():
    at=msutc("2025-01-19T06:00:00Z")
    row={"date":"2025-01-19","symbol":"ABCUSDT","gt2x":"True",
         "baseline_1h_open":"1","max_high_multiple":"2"}
    raw=[(at-24*3600000+i*60000,Decimal(1),Decimal(1),Decimal(1),Decimal(1),Decimal(1),10) for i in range(BARS)]
    values=list(raw)
    high_i=WARMUP+200
    values[high_i]=(values[high_i][0],Decimal(1),Decimal(2),Decimal(1),Decimal(1),Decimal(1),10)
    early=score(row,values,{"WATCH_UTC":[stamp(at+198*60000)]})
    assert early["classification"]=="STRICTLY_EARLY_WATCH" and early["nearest_strictly_earlier_WATCH_lead_min"]==2
    same=score(row,values,{"WATCH_UTC":[stamp(at+200*60000)]})
    assert same["classification"]=="SAME_MINUTE_NOT_EARLY"
    after=score(row,values,{"WATCH_UTC":[stamp(at+201*60000)]})
    assert after["classification"]=="WATCH_LATE"
    assert score(row,values,{"WATCH_UTC":[]})["classification"]=="NO_WATCH"
    row_bad=dict(row,max_high_multiple="3")
    try:score(row_bad,values,{"WATCH_UTC":[]})
    except ValueError as e:assert "MISMATCH" in str(e)
    else:raise AssertionError("FAILED_1H_MINUTE_PARITY_GUARD")
    print("STAGE38_NO_FUTURE_SCAN_GROSS_1M_LABEL_AND_SOURCE_PARITY_SELFTEST_PASS")

def main():
    a=argparse.ArgumentParser()
    a.add_argument("--selftest",action="store_true")
    a.add_argument("--date")
    a.add_argument("--shard",type=int)
    a.add_argument("--workers",type=int,default=2)
    a.add_argument("--output",type=Path)
    x=a.parse_args()
    if x.selftest:selftest();return
    if not x.date or x.shard is None or not x.output:a.error("--date, --shard, --output required")
    r=run(x.date,x.shard,x.workers)
    x.output.parent.mkdir(parents=True,exist_ok=True)
    x.output.write_text(json.dumps(r,indent=2,ensure_ascii=False,sort_keys=True)+"\n",encoding="utf-8")
    print("STAGE38_REAL_USDM_CAUSAL_RESULT "+json.dumps({k:r[k] for k in
      ("date","shard","original_expected","complete_replay","source_censored","complete_gt2x","strictly_early_gt2x")},sort_keys=True))
if __name__=="__main__":main()
