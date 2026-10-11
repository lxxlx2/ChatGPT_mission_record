#!/usr/bin/env python3
"""Stage22 frozen 65 D1 pre-signal Binance Spot aggTrades; no trading."""
import argparse
import concurrent.futures
import csv
import hashlib
import io
import json
import re
import statistics
import urllib.error
import urllib.request
import zipfile
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal as D
from pathlib import Path

try:
    import monster_v4_stage21_aggregate as stage21
except ImportError:
    from scripts import monster_v4_stage21_aggregate as stage21

EVIDENCE=stage21.ROOT
PREREG=EVIDENCE/"monster_stage22_aggressor_flow_stop_rootcause_prereg_20261011.json"
PROOF=EVIDENCE/"monster_stage21_real_10date_ci_artifact_proof_20261011.json"
BASE="https://data.binance.vision/data/spot/daily/aggTrades"
MAX_ZIP=120_000_000
MAX_UNCOMPRESSED=1_200_000_000
MAX_ROWS=10_000_000

def utc_ms(iso):
    return int(datetime.fromisoformat(iso.replace("Z","+00:00")).timestamp()*1000)

def frozen_cohort(day,artifact):
    frozen=json.loads(PREREG.read_text(encoding="utf-8"))
    proof=json.loads(PROOF.read_text(encoding="utf-8"))
    if frozen.get("schema")!="MONSTER_STAGE22_POST_ENTRY_STOP_CAUSAL_AGGTRADES_FROZEN_DIAGNOSTIC_V1":
        raise ValueError("STAGE22_MANIFEST_BAD_SCHEMA")
    entries={x["date"]:x for x in proof["artifacts"]}
    if len(entries)!=10 or day not in entries or day not in frozen["frozen_cohort"]["ten_dates"]:
        raise ValueError("STAGE22_DATE_NOT_FROZEN")
    doc=stage21.read_zip(artifact,entries[day])
    cases=[]
    for c in doc["cases"]:
        if c["status"]!="COMPLETE_60H" or not c.get("quality",{}).get("quality_pass"):
            continue
        proxy=c["arm_proxies"]["D_QUALITY_D1_BOUNDED_6H_20BPS"]
        if proxy is None:
            raise ValueError("STAGE22_QUALIFIED_D1_WITHOUT_PROXY")
        cases.append({"date":day,"symbol":c["symbol"],"setup_utc":c["first_v4_d1_utc"],
          "exit_label":proxy.get("exit_reason") if proxy["status"]=="PRICE_PROXY_ONLY" else "CENSORED",
          "exit_status":proxy["status"],"exit_utc":proxy.get("exit_utc"),
          "original_net_pct":proxy.get("net_pct"),"original_quality":c["quality"]})
    cases.sort(key=lambda x:(x["date"],x["symbol"],x["setup_utc"]))
    if len(cases)!=doc["summary"]["quality_accepted"]:
        raise ValueError("STAGE22_QUALITY_DENOMINATOR_MISMATCH")
    return cases

def source_url(symbol,day):
    if not re.fullmatch(r"[A-Z0-9]+USDT",symbol) or not re.fullmatch(r"20\d\d-\d\d-\d\d",day):
        raise ValueError("STAGE22_UNSAFE_SYMBOL_OR_DATE")
    return f"{BASE}/{symbol}/{symbol}-aggTrades-{day}.zip"

def download(url,limit):
    req=urllib.request.Request(url,headers={"User-Agent":"MonsterStage22Research/1.0"})
    with urllib.request.urlopen(req,timeout=45) as response:
        if response.headers.get("Content-Length") and int(response.headers["Content-Length"])>limit:
            raise ValueError("STAGE22_ARCHIVE_TOO_LARGE")
        data=response.read(limit+1)
    if not data or len(data)>limit:
        raise ValueError("STAGE22_ARCHIVE_TOO_LARGE_OR_EMPTY")
    return data

def ts_ms(raw):
    if not raw.isdecimal():
        raise ValueError("STAGE22_BAD_TIMESTAMP")
    n=int(raw)
    if n>=10**15:
        return n//1000
    if n>=10**12:
        return n
    raise ValueError("STAGE22_UNSUPPORTED_TIME_UNIT")

def analyze(symbol,day,setup_utc,fetch=download):
    url=source_url(symbol,day)
    content=fetch(url,MAX_ZIP)
    published=fetch(url+".CHECKSUM",2048).decode("utf-8").split()
    if not published or not re.fullmatch(r"[0-9a-fA-F]{64}",published[0]):
        raise ValueError("STAGE22_INVALID_PUBLISHER_SHA")
    sha=hashlib.sha256(content).hexdigest()
    if sha!=published[0].lower():
        raise ValueError("STAGE22_PUBLISHED_SHA_MISMATCH")
    end=utc_ms(setup_utc)
    if datetime.fromtimestamp(end/1000,timezone.utc).date().isoformat()!=day:
        raise ValueError("STAGE22_SETUP_DATE_MISMATCH")
    start=end-60*60000
    sums={n:{"buy":D(0),"sell":D(0),"buyn":0,"selln":0} for n in (5,15,60)}
    member=f"{symbol}-aggTrades-{day}.csv"
    count=0;inside=0;last=None
    with zipfile.ZipFile(io.BytesIO(content)) as z:
        if z.namelist()!=[member] or z.getinfo(member).file_size>MAX_UNCOMPRESSED:
            raise ValueError("STAGE22_ARCHIVE_MEMBER_OR_SIZE_REJECTED")
        with z.open(member) as stream:
            for line in csv.reader(io.TextIOWrapper(stream,encoding="utf-8-sig")):
                count+=1
                if count>MAX_ROWS:
                    raise ValueError("STAGE22_ROW_LIMIT")
                if len(line)!=8:
                    raise ValueError("STAGE22_BAD_AGGTRADES_CSV_COLUMNS")
                timestamp=ts_ms(line[5])
                if not start<=timestamp<end:
                    continue
                qty=D(line[2]);price=D(line[1])
                if min(qty,price)<=0:
                    raise ValueError("STAGE22_NONPOSITIVE_AGGTRADE")
                maker=line[6].strip().lower()
                if maker not in ("true","false"):
                    raise ValueError("STAGE22_UNKNOWN_BUYER_MAKER_FLAG")
                side="sell" if maker=="true" else "buy"
                quote=price*qty
                inside+=1
                last=timestamp if last is None else max(timestamp,last)
                for n in (5,15,60):
                    if timestamp>=end-n*60000:
                        m=sums[n]
                        m[side]+=quote
                        m[side+"n"]+=1
    if inside==0:
        return {"status":"CENSORED_NO_PRE_SIGNAL_AGGTRADES",
                "official_zip_sha256":sha,"archive_trade_rows":count}
    if last is None or last>=end:
        raise ValueError("STAGE22_NONCAUSAL_LAST_TRADE")
    result={"status":"VERIFIED_PRE_SIGNAL_AGGTRADES",
            "official_zip_sha256":sha,"archive_trade_rows":count,
            "pre_signal_60m_aggtrade_rows":inside,
            "last_trade_ms":last,"strictly_before_setup":True}
    for n in (5,15,60):
        s=sums[n];total=s["buy"]+s["sell"];c=s["buyn"]+s["selln"]
        key=f"prior_{n}m"
        result[key+"_quote_usdt"]=round(float(total),6)
        result[key+"_aggressor_buy_quote_share"]=round(float(s["buy"]/total),6) if total>0 else None
        result[key+"_aggressor_sell_trade_share"]=round(s["selln"]/c,6) if c else None
        result[key+"_net_buy_quote_usdt"]=round(float(s["buy"]-s["sell"]),6)
        result[key+"_aggtrade_rows"]=c
    older=sum(sums[60][k]-sums[15][k] for k in ("buy","sell"))
    current=sum(sums[15][k] for k in ("buy","sell"))
    result["prior_15m_vs_previous45m_quote_ratio"]=round(float(3*current/older),6) if older>0 else None
    return result

def evaluate(case,fetch=download):
    out=case.copy()
    try:
        out["flow"]=analyze(case["symbol"],case["date"],case["setup_utc"],fetch)
    except urllib.error.HTTPError as err:
        out["flow"]={"status":"CENSORED_MISSING_AGGTRADES" if err.code in (403,404) else "SOURCE_HTTP_FAILURE","detail":str(err.code)}
    except (urllib.error.URLError,TimeoutError,OSError) as err:
        out["flow"]={"status":"SOURCE_NETWORK_FAILURE","detail":type(err).__name__}
    except (ValueError,zipfile.BadZipFile,UnicodeError,csv.Error) as err:
        reason=str(err)
        out["flow"]={"status":"CENSORED_OVERSIZE_ARCHIVE" if "TOO_LARGE" in reason or "ROW_LIMIT" in reason else "SOURCE_INTEGRITY_REJECTED","detail":reason[:160]}
    return out

def summary(cases):
    status=Counter(x["flow"]["status"] for x in cases)
    out={"attempted":len(cases),"flow_status":dict(status),
         "labels":dict(Counter(x["exit_label"] for x in cases)),
         "verified":status["VERIFIED_PRE_SIGNAL_AGGTRADES"]}
    for name in ("STOP","TAKE_PROFIT","TIMEOUT_6H","CENSORED"):
        filtered=[x for x in cases if x["exit_label"]==name]
        present=[x["flow"] for x in filtered if x["flow"]["status"]=="VERIFIED_PRE_SIGNAL_AGGTRADES"]
        features={}
        for feat in ("prior_5m_aggressor_buy_quote_share",
                "prior_15m_aggressor_buy_quote_share",
                "prior_60m_aggressor_buy_quote_share",
                "prior_15m_quote_usdt","prior_60m_quote_usdt",
                "prior_15m_vs_previous45m_quote_ratio"):
            nums=[x[feat] for x in present if x.get(feat) is not None]
            features[feat+"_median"]=round(statistics.median(nums),6) if nums else None
        out[name]={"n":len(filtered),"verified":len(present),
                "missing_or_unverified":len(filtered)-len(present),
                "metrics":features}
    return out

def run(day,artifact,fetch=download,workers=3):
    frozen=frozen_cohort(day,artifact)
    if not 1<=workers<=3:
        raise ValueError("STAGE22_UNSAFE_CONCURRENCY")
    output=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futures={pool.submit(evaluate,c,fetch):(c["symbol"],c["setup_utc"]) for c in frozen}
        for future in concurrent.futures.as_completed(futures):
            row=future.result()
            if (row["symbol"],row["setup_utc"])!=futures[future]:
                raise ValueError("STAGE22_FUTURE_IDENTITY_CHANGED")
            output.append(row)
    output.sort(key=lambda x:(x["date"],x["symbol"],x["setup_utc"]))
    return {"schema":"MONSTER_STAGE22_CAUSAL_65_D1_SPOT_AGGTRADES_V1",
        "date":day,"historical_results_exposed":True,
        "source":"OFFICIAL_BINANCE_SPOT_AGGTRADES_PUBLISHER_SHA256",
        "summary":summary(output),"cases":output,
        "new_rule_approved":False,"other_ai_review":"NOT_DONE",
        "deployment":"NO_GO","trading":False,"gmail":False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--date",required=True)
    p.add_argument("--source-artifact",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    result=run(a.date,a.source_artifact)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("STAGE22_RESULT_JSON "+json.dumps(result["summary"],sort_keys=True),flush=True)
    if any(result["summary"]["flow_status"].get(key,0) for key in
          ("SOURCE_NETWORK_FAILURE","SOURCE_HTTP_FAILURE","SOURCE_INTEGRITY_REJECTED")):
        raise SystemExit("STAGE22_SOURCE_FAILURE_OR_INTEGRITY")
if __name__=="__main__":
    main()
