#!/usr/bin/env python3
"""Stage16: frozen-universe independent 7-day raw price-extreme labels.

READ ONLY. Official Binance monthly Spot 1h archive ZIP+CHECKSUM. Labels are
future outcomes, never used for V4 D0/D1 feature computation; raw 1h highs are
NOT executable prices, success, or an entry/exit PnL.
"""
import argparse
import concurrent.futures
import csv
import hashlib
import io
import json
import re
import statistics
import sys
import urllib.error
import urllib.request
import zipfile
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

try:
    import monster_v4_stage15_archive_only as stage15
except ImportError:
    from scripts import monster_v4_stage15_archive_only as stage15

EVIDENCE = stage15.archive.source.EVIDENCE
STAGE15_PROOF = EVIDENCE / "monster_stage15_archive_only_5date_actual_ci_20261011.json"
BASE = "https://data.binance.vision/data/spot/monthly/klines/"
DATES = stage15.FROZEN_DATES
HOURS = 168
WORKERS = 8
MAX_ZIP = 5_000_000

def frozen_symbols(inventory_fetch=stage15.inventory):
    proof = json.loads(STAGE15_PROOF.read_text(encoding="utf-8"))
    inventory = inventory_fetch()
    if (inventory["archive_only_sha256"] != proof["archive_only_compatible_sha256"]
            or inventory["replay_eligible_archive_only_count"] != 254
            or inventory["frozen_current_count"] != 504):
        raise ValueError("STAGE16_UNIVERSE_DRIFT")
    current = stage15.frozen_current504()
    symbols = sorted(current | set(inventory["archive_only_symbols"]))
    if len(symbols) != 758:
        raise ValueError("STAGE16_INCOMPLETE_UNION")
    return symbols, inventory

def url(symbol, day):
    if not re.fullmatch(r"[A-Z0-9]+USDT", symbol):
        raise ValueError("STAGE16_UNSUPPORTED_SYMBOL")
    month = day.strftime("%Y-%m")
    filename = symbol + "-1h-" + month + ".zip"
    return BASE + symbol + "/1h/" + filename

def read_zip(url, limit=MAX_ZIP):
    request = urllib.request.Request(url, headers={"User-Agent":"MonsterResearchGT/1.0"})
    with urllib.request.urlopen(request, timeout=35) as response:
        data = response.read(limit + 1)
    if not data or len(data)>limit:
        raise ValueError("EMPTY_OR_OVERSIZE_MONTHLY_ARCHIVE")
    return data

def verified_hourly_month(symbol, day, download=read_zip):
    source = url(symbol,day)
    content=download(source)
    published=download(source+".CHECKSUM",2048)
    fields=published.decode("utf-8").strip().split()
    if not fields or not re.fullmatch(r"[a-fA-F0-9]{64}", fields[0]):
        raise ValueError("INVALID_PUBLISHED_SHA256")
    digest=hashlib.sha256(content).hexdigest()
    if digest!=fields[0].lower():
        raise ValueError("PUBLISHED_MONTHLY_SHA256_MISMATCH")
    csv_name=symbol+"-1h-"+day.strftime("%Y-%m")+".csv"
    with zipfile.ZipFile(io.BytesIO(content)) as z:
        if z.namelist()!=[csv_name] or z.getinfo(csv_name).file_size>20_000_000:
            raise ValueError("MONTHLY_UNSAFE_CSV_MEMBERS")
        with z.open(csv_name) as stream:
            rows=list(csv.reader(io.TextIOWrapper(stream,encoding="utf-8")))
    observations={}
    for r in rows:
        if len(r)<9 or not r[0].isdigit():
            raise ValueError("MALFORMED_MONTHLY_BAR")
        stamp=int(r[0])
        if stamp>=10**15:
            if stamp%1000:
                raise ValueError("NON_HOURLY_MICROSECOND_TIMESTAMP")
            stamp//=1000
        if stamp<10**12 or stamp%(3600*1000):
            raise ValueError("INVALID_HOURLY_TIMESTAMP")
        opening,high,close,quote=(Decimal(r[i]) for i in (1,2,4,7))
        if min(opening,high,close)<=0 or quote<0 or high<max(opening,close):
            raise ValueError("INVALID_HOURLY_PRICES")
        if stamp in observations:
            raise ValueError("DUPLICATE_HOURLY_TIMESTAMP")
        observations[stamp]=(opening,high,close,quote)
    return observations,digest

def label(symbol, day, *, month_fetch=verified_hourly_month):
    try:
        bars,digest=month_fetch(symbol,day)
    except urllib.error.HTTPError as error:
        return {"symbol":symbol,"status":"MONTH_ARCHIVE_MISSING_404" if error.code==404
                  else "SOURCE_HTTP_FAILED_"+str(error.code)}
    except (urllib.error.URLError,TimeoutError,OSError) as error:
        return {"symbol":symbol,"status":"SOURCE_NETWORK_FAILED_"+type(error).__name__}
    except ValueError as error:
        return {"symbol":symbol,"status":"SOURCE_INTEGRITY_REJECTED","reason":str(error)}
    start=int(datetime(day.year,day.month,day.day,6,tzinfo=timezone.utc).timestamp()*1000)
    stamps=[start+k*3600000 for k in range(HOURS)]
    if any(stamp not in bars for stamp in stamps):
        return {"symbol":symbol,"status":"CENSORED_7D_HOURLY_GAP",
                "archive_sha256":digest,
                "available_hour_count":sum(stamp in bars for stamp in stamps)}
    selected=[bars[x] for x in stamps]
    first=selected[0][0]
    high_multiple=max(row[1] for row in selected)/first
    close_multiple=max(row[2] for row in selected)/first
    result={"symbol":symbol,"status":"VERIFIED_COMPLETE_168H",
            "archive_sha256":digest,
            "baseline_utc":datetime.fromtimestamp(start/1000,timezone.utc).isoformat(),
            "baseline_1h_open":str(first),
            "maximum_high_multiple":str(high_multiple),
            "maximum_close_multiple":str(close_multiple),
            "quote_volume_first_hour":str(selected[0][3]),
            "raw_high_not_a_fill":True}
    for threshold in (2,5,10):
        result["gross_high_ge_"+str(threshold)+"x"]=high_multiple>=threshold
        result["gross_close_ge_"+str(threshold)+"x"]=close_multiple>=threshold
        first_high=next((i for i,row in enumerate(selected) if row[1]>=first*threshold),None)
        if first_high is not None:
            result["first_high_"+str(threshold)+"x_hour_index"]=first_high
    return result

def run(date_str, *, get_symbols=frozen_symbols, evaluator=label, workers=WORKERS):
    if date_str not in DATES:
        raise ValueError("STAGE16_NON_FROZEN_DATE")
    symbols,inv=get_symbols()
    if len(symbols)!=len(set(symbols)) or len(symbols)!=758:
        raise ValueError("STAGE16_UNIVERSE_SIZE_CHANGED")
    if not 1<=workers<=WORKERS:
        raise ValueError("STAGE16_INVALID_CONCURRENCY")
    day=date.fromisoformat(date_str)
    output=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        jobs={pool.submit(evaluator,s,day):s for s in symbols}
        for f in concurrent.futures.as_completed(jobs):
            row=f.result()
            if row.get("symbol")!=jobs[f]:
                raise ValueError("STAGE16_RESULT_ID_MISMATCH")
            output.append(row)
            if len(output)%100==0:
                print("STAGE16_PROGRESS "+json.dumps({"day":date_str,"done":len(output),"target":len(symbols)}),file=sys.stderr,flush=True)
    output.sort(key=lambda x:x["symbol"])
    statuses=Counter(x["status"] for x in output)
    valid=[x for x in output if x["status"]=="VERIFIED_COMPLETE_168H"]
    summary={"attempted":len(output),"status_counts":dict(statuses),"complete_168h":len(valid)}
    for n in (2,5,10):
        summary["gross_high_ge_"+str(n)+"x"]=sum(x["gross_high_ge_"+str(n)+"x"] for x in valid)
        summary["gross_close_ge_"+str(n)+"x"]=sum(x["gross_close_ge_"+str(n)+"x"] for x in valid)
        summary["symbols_gross_high_ge_"+str(n)+"x"]=[x["symbol"] for x in valid if x["gross_high_ge_"+str(n)+"x"]]
    return {"schema":"MONSTER_STAGE16_FROZEN_FIVE_DATE_7D_HOURLY_GT_V1",
            "source":"BINANCE_OFFICIAL_MONTHLY_SPOT_1H_SHA256_VERIFIED",
            "date":date_str,"universe_sha256":inv["archive_only_sha256"],
            "historical_truth_not_model_input":True,
            "not_true_point_in_time_exchangeinfo":True,
            "baseline":"UTC_06_00_FIRST_1H_OPEN",
            "horizon_hours":168,
            "max_1h_high_not_executable":True,
            "summary":summary,"cases":output,
            "deployment":"NO_GO","trading_enabled":False,"other_ai_review_done":False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--date",required=True,choices=DATES)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    result=run(a.date)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("STAGE16_RESULT_JSON "+json.dumps(result["summary"],sort_keys=True),flush=True)
    statuses=result["summary"]["status_counts"]
    if any("NETWORK_FAILED" in k or "SOURCE_HTTP_FAILED" in k or "SOURCE_INTEGRITY_REJECTED" in k for k in statuses):
        raise SystemExit("STAGE16_SOURCE_FAILURE")
    if result["summary"]["complete_168h"]<100:
        raise SystemExit("STAGE16_TOO_FEW_VALID_HISTORICAL_SYMBOLS")

if __name__=="__main__":
    main()
