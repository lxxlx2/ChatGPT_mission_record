#!/usr/bin/env python3
"""Stage37: six-date, all900 USD-M archived plain-USDT futures raw 1h GT.

Source is publisher-SHA-verified historical kline ZIP; future HIGH is not a fill.
No model decision, WATCH, claimed tradability, profit or deployment.
"""
import argparse,concurrent.futures,csv,hashlib,io,json,re,time,urllib.error,urllib.request,zipfile
from collections import Counter
from datetime import datetime,date,timezone
from decimal import Decimal
from pathlib import Path

EVIDENCE=Path(__file__).resolve().parents[2]/"monster"/"evidence"
INV=EVIDENCE/"monster_stage36_official_usdm_archive_vs_spot758.json"
FREEZE=EVIDENCE/"monster_stage37_all900_usdm_sixdate_7d_GT_prereg_20261012.json"
BLOB="91b0f99ef85adb48494c5be5c7cc13a7cedcb686"
BASE="https://data.binance.vision/data/futures/um/monthly/klines/"
DAYS=("2025-01-19","2025-04-19","2025-07-19","2025-10-19","2026-04-19","2026-07-19")
SCHEMA="MONSTER_STAGE37_USDM_PUBLISHER_SHA_FULL900_SIX_DATE_168H_GT_V1"

def blob(path):
    b=path.read_bytes()
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()

def frozen():
    p=json.loads(FREEZE.read_text(encoding="utf-8"))
    if (p["schema"]!="MONSTER_STAGE37_FROZEN_FULL900_USDM_6_DATE_FUTURE_7D_HOURLY_HIGH_GT_V1"
        or tuple(p["dates_utc_start_06"])!=DAYS or p["all_universe_at_every_date"]!=True
        or p["attempts"]!=5400 or p["frozen_stage36_inventory"]["git_blob_sha1"]!=BLOB
        or blob(INV)!=BLOB):
        raise ValueError("STAGE37_UNFROZEN_SOURCE_OR_DATES_CHANGED")
    inv=json.loads(INV.read_text(encoding="utf-8"))
    plain=sorted(x["symbol"] for x in inv["source_rows"] if x["archive_symbol_class"]=="EXACT_PLAIN_USDT_ARCHIVED")
    if len(plain)!=900 or len(set(plain))!=900 or not all(re.fullmatch(r"[A-Z0-9]+USDT",x) for x in plain):
        raise ValueError("STAGE37_FROZEN_900_UNIVERSE_DRIFT")
    return plain

def read_public(uri,max_bytes=3_000_000):
    r=urllib.request.Request(uri,headers={"User-Agent":"Monster-Stage37-Verified-USD-M/1.0"})
    with urllib.request.urlopen(r,timeout=32) as f:b=f.read(max_bytes+1)
    if not b or len(b)>max_bytes:raise ValueError("STAGE37_EMPTY_OR_TOO_LARGE_SOURCE")
    return b

def monthly_source(symbol,month,fetch=read_public):
    uri=f"{BASE}{symbol}/1h/{symbol}-1h-{month}.zip"
    last=None
    for i in range(3):
        try:
            raw=fetch(uri)
            receipt=fetch(uri+".CHECKSUM",2048)
            break
        except urllib.error.HTTPError as e:
            if e.code==404:return None,"SOURCE_404_MONTHLY_1H_NOT_OBSERVABLE"
            last=e
        except (urllib.error.URLError,ConnectionError,TimeoutError,OSError) as e:
            last=e
        if i<2:time.sleep(1+i)
    else:raise RuntimeError("STAGE37_PUBLIC_SOURCE_NETWORK_FAILURE "+repr(last))
    text=receipt.decode("utf-8","strict").strip().split()
    if not text or not re.fullmatch(r"[0-9a-fA-F]{64}",text[0]):
        raise ValueError("STAGE37_MISSING_OR_INVALID_PUBLISHER_SHA256")
    digest=hashlib.sha256(raw).hexdigest()
    if digest!=text[0].lower():raise ValueError("STAGE37_ORIGINAL_ZIP_PUBLISHER_SHA256_MISMATCH")
    member=f"{symbol}-1h-{month}.csv"
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        if z.namelist()!=[member] or z.getinfo(member).file_size>16_000_000:
            raise ValueError("STAGE37_WRONG_OR_OVERSIZED_ARCHIVE")
        rows=list(csv.reader(io.TextIOWrapper(z.open(member),encoding="utf-8")))
    bars={}
    for r in rows:
        if len(r)<9 or not r[0].isdigit():raise ValueError("STAGE37_BAD_CSV_ROW")
        stamp=int(r[0])
        if stamp>=10**15:
            if stamp%1000:raise ValueError("STAGE37_BAD_MICRO_TIMESTAMP")
            stamp//=1000
        if stamp<10**12 or stamp%3600000:raise ValueError("STAGE37_BAD_UTC_HOUR_ALIGNMENT")
        price,high,close,quote=map(Decimal,(r[1],r[2],r[4],r[7]))
        if min(price,high,close)<=0 or high<max(price,close) or quote<0 or stamp in bars:
            raise ValueError("STAGE37_INVALID_PRICE_QUOTE_DUPLICATE")
        bars[stamp]=(price,high,close,quote)
    return {"publisher_zip_sha256":digest,"bars":bars},None

def evaluate(symbol,day,source=monthly_source):
    month=day[:7]
    data,missing=source(symbol,month)
    row={"symbol":symbol,"date":day,"venue":"BINANCE_USDM_FUTURES_ARCHIVED_SYMBOL",
         "true_historical_perpetual_contract_type":"UNKNOWN",
         "real_fill_or_historical_L2_verified":False}
    if missing:
        row["status"]=missing
        return row
    start=int(datetime.fromisoformat(day+"T06:00:00+00:00").timestamp()*1000)
    hours=[start+i*3600000 for i in range(168)]
    source_bars=data["bars"]
    if any(h not in source_bars for h in hours):
        row.update(status="CENSORED_NOT_168_CONTIGUOUS_HOURS",
                   available_hour_count=sum(h in source_bars for h in hours),
                   publisher_1h_month_sha256=data["publisher_zip_sha256"])
        return row
    series=[source_bars[h] for h in hours]
    baseline=series[0][0]
    max_high=max(h[1] for h in series)
    row.update(status="COMPLETE_168H_PUBLISHER_SHA",
               publisher_1h_month_sha256=data["publisher_zip_sha256"],
               baseline_utc=day+"T06:00:00Z",baseline_1h_open=str(baseline),
               max_high_multiple=str(max_high/baseline))
    for n in (2,5,10):
        threshold=baseline*n
        first=next((i for i,h in enumerate(series) if h[1]>=threshold),None)
        row[f"gt{n}x"]=first is not None
        row[f"first_{n}x_high_hour_utc"]=(
            datetime.fromtimestamp(hours[first]/1000,timezone.utc).isoformat().replace("+00:00","Z")
            if first is not None else None)
    return row

def run(day,shard,workers=4):
    symbols=frozen()
    if day not in DAYS or shard not in range(6) or workers not in (1,2,3,4):
        raise ValueError("STAGE37_NOT_FROZEN_DATE_SHARD_OR_WORKERS")
    chosen=[s for i,s in enumerate(symbols) if i%6==shard]
    if len(chosen)!=150:raise ValueError("STAGE37_SHARD_NOT_150")
    result=[];errors=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        jobs={pool.submit(evaluate,s,day):s for s in chosen}
        for f in concurrent.futures.as_completed(jobs):
            symbol=jobs[f]
            try:
                r=f.result()
                if r["symbol"]!=symbol:raise ValueError("STAGE37_JOB_IDENTITY_MISMATCH")
                result.append(r)
            except Exception as e:
                errors.append({"symbol":symbol,"error":type(e).__name__+":"+str(e)[:180]})
            if (len(result)+len(errors))%30==0:
                print("STAGE37_PROGRESS "+json.dumps({"date":day,"shard":shard,"done":len(result),"source_errors":len(errors)}),flush=True)
    if errors or len(result)!=150:
        raise RuntimeError("STAGE37_SOURCE_OR_INTEGRITY_FAILURE "+json.dumps(errors[:5]))
    result.sort(key=lambda r:r["symbol"])
    statuses=Counter(r["status"] for r in result)
    good=[r for r in result if r["status"]=="COMPLETE_168H_PUBLISHER_SHA"]
    return {"schema":SCHEMA,"date":day,"shard":shard,"frozen_source_inventory_git_blob":BLOB,
            "full_frozen900_universe_attempted":True,"valid":len(good),
            "status_counts":dict(statuses),
            "positive_high_gt2x":sum(r["gt2x"] for r in good),
            "positive_high_gt5x":sum(r["gt5x"] for r in good),
            "positive_high_gt10x":sum(r["gt10x"] for r in good),
            "rows":result,"no_future_GTs_used_to_select_symbols":True,
            "review":"NOT_DONE","trade":"NO_GO","gmail":"OFF","deployment":"NO_GO","Frank":"UNCHANGED"}

def selftest():
    m={}
    start=int(datetime.fromisoformat("2025-01-19T06:00:00+00:00").timestamp()*1000)
    for i in range(168):m[start+i*3600000]=(Decimal(1),Decimal(3 if i==90 else 1),Decimal(1),Decimal(100))
    r=evaluate("MUSDT","2025-01-19",source=lambda *args:({"publisher_zip_sha256":"a"*64,"bars":m},None))
    assert r["status"]=="COMPLETE_168H_PUBLISHER_SHA" and r["gt2x"] and not r["gt5x"]
    assert r["first_2x_high_hour_utc"]=="2025-01-23T00:00:00Z"
    m.pop(start+3600000)
    r=evaluate("MUSDT","2025-01-19",source=lambda *args:({"publisher_zip_sha256":"a"*64,"bars":m},None))
    assert r["status"]=="CENSORED_NOT_168_CONTIGUOUS_HOURS"
    r=evaluate("MUSDT","2025-01-19",source=lambda *args:(None,"SOURCE_404_MONTHLY_1H_NOT_OBSERVABLE"))
    assert "gt2x" not in r
    print("STAGE37_HOURLY_GT_AND_MISSING_SOURCE_SELFTEST_PASS")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--selftest",action="store_true")
    p.add_argument("--date")
    p.add_argument("--shard",type=int)
    p.add_argument("--workers",type=int,default=4)
    p.add_argument("--output",type=Path)
    a=p.parse_args()
    if a.selftest:selftest();return
    if not a.date or a.shard is None or not a.output:p.error("--date --shard --output required")
    res=run(a.date,a.shard,a.workers)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(res,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("STAGE37_REAL_OFFICIAL_GT_SHA "+json.dumps({k:res[k] for k in
        ("date","shard","valid","positive_high_gt2x","positive_high_gt5x","positive_high_gt10x","status_counts")},sort_keys=True))
if __name__=="__main__":
    main()
