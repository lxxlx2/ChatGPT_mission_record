#!/usr/bin/env python3
"""Stage36: official Binance USD-M FUTURES historical archive prefix census.

This reads only public S3 directory listings and a frozen Spot historical cohort.
Archive directory != active/listed perpetual contract on any historical date.
This is not a model evaluation, trade, threshold change, Gmail or Mac runtime.
"""
import argparse,csv,hashlib,json,re,urllib.parse,urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime,timezone
from pathlib import Path

NS="{http://s3.amazonaws.com/doc/2006-03-01/}"
BUCKET="https://s3-ap-northeast-1.amazonaws.com/data.binance.vision"
PREFIXES=("data/futures/um/monthly/klines/","data/futures/um/daily/klines/")
EVIDENCE=Path(__file__).resolve().parents[2]/"monster"/"evidence"
CONTRACT=EVIDENCE/"monster_stage36_usdm_historical_archive_universe_prereg_20261012.json"
STAGE34=EVIDENCE/"monster_stage34_full18date_13644_coin_date_controls.csv"
SPOT_BLOB="f94f881e3ef13f8ac33e92aa68542d45a8069384"
SCHEMA="MONSTER_STAGE36_OFFICIAL_S3_USDM_SYMBOL_DIRECTORY_GAP_AUDIT_V1"

def git_blob(p):
    raw=p.read_bytes()
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()

def parser():
    frozen=json.loads(CONTRACT.read_text(encoding="utf-8"))
    if (frozen.get("schema")!="MONSTER_STAGE36_FUTURES_ARCHIVE_UNIVERSE_PREREG_V1"
        or tuple(frozen["archive_prefixes"])!=PREFIXES
        or frozen["spot_comparison"].split()[-1]!=SPOT_BLOB or git_blob(STAGE34)!=SPOT_BLOB):
        raise ValueError("STAGE36_FROZEN_SOURCE_OR_SPOT_COHORT_CHANGED")
    with STAGE34.open(encoding="utf-8",newline="") as handle:
        rows=list(csv.DictReader(handle))
    if len(rows)!=13644 or len({(r["date"],r["symbol"]) for r in rows})!=13644:
        raise ValueError("STAGE36_ORIGINAL_STAGE34_COUNT_DRIFT")
    spot={r["symbol"] for r in rows}
    if len(spot)!=758:raise ValueError("STAGE36_ORIGINAL_SPOT_758_CHANGED")
    return frozen,spot

def read_public(url):
    req=urllib.request.Request(url,headers={"User-Agent":"Monster-Stage36-Audit/1.0"})
    with urllib.request.urlopen(req,timeout=35) as res:
        raw=res.read(3_000_000)
    if len(raw)>2_000_000 or not raw:raise ValueError("STAGE36_INVALID_LISTING_BYTES")
    return raw

def list_prefix(prefix,read=read_public):
    found=set();page_receipts=[];token=None;seen=set()
    for page in range(30):
        query={"list-type":"2","prefix":prefix,"delimiter":"/","max-keys":"1000"}
        if token:query["continuation-token"]=token
        url=BUCKET+"?"+urllib.parse.urlencode(query)
        raw=read(url)
        doc=ET.fromstring(raw)
        if doc.tag!=NS+"ListBucketResult" or doc.findtext(NS+"Prefix")!=prefix:
            raise ValueError("STAGE36_WRONG_S3_LIST_RESPONSE")
        names=[]
        for node in doc.findall(NS+"CommonPrefixes"):
            p=node.findtext(NS+"Prefix","")
            if not p.startswith(prefix) or not p.endswith("/") or "/" in p[len(prefix):-1]:
                raise ValueError("STAGE36_UNEXPECTED_PREFIX")
            sym=p[len(prefix):-1]
            if not sym or any(ord(ch)<33 for ch in sym) or len(sym)>100:
                raise ValueError("STAGE36_BAD_ARCHIVE_SYMBOL_DIR")
            names.append(sym)
        if len(names)!=len(set(names)):raise ValueError("STAGE36_DUPLICATED_PAGE_DIR")
        if found.intersection(names):raise ValueError("STAGE36_REPEATED_DIR_ACROSS_PAGES")
        found.update(names)
        truncated=doc.findtext(NS+"IsTruncated")
        if truncated not in ("true","false"):raise ValueError("STAGE36_UNKNOWN_S3_PAGINATION_STATE")
        page_receipts.append({"page_index":page,"page_sha256":hashlib.sha256(raw).hexdigest(),
                              "dirs":len(names),"truncated":truncated=="true"})
        if truncated=="false":
            if not found:raise ValueError("STAGE36_EMPTY_ARCHIVE_LISTING")
            return found,page_receipts
        new_token=doc.findtext(NS+"NextContinuationToken")
        if not new_token or new_token in seen:raise ValueError("STAGE36_S3_LOOP_OR_MISSING_CURSOR")
        seen.add(new_token);token=new_token
    raise ValueError("STAGE36_S3_PAGE_LIMIT")

def classify(symbol):
    if re.fullmatch(r"[A-Z0-9]+USDT",symbol):return "EXACT_PLAIN_USDT_ARCHIVED"
    if re.fullmatch(r"[A-Z0-9]+USDT_[0-9]{6}",symbol):return "USDT_DATED_CONTRACT"
    return "OTHER_USDM_SYMBOL"

def inventory(read=read_public):
    _,spot=parser()
    monthly,monthly_proof=list_prefix(PREFIXES[0],read)
    daily,daily_proof=list_prefix(PREFIXES[1],read)
    symbols=sorted(monthly|daily)
    rows=[]
    for sym in symbols:
        kind=classify(sym)
        rows.append({"symbol":sym,"archive_symbol_class":kind,
                     "monthly_klines_directory":sym in monthly,
                     "daily_klines_directory":sym in daily,
                     "in_frozen_Spot_758":sym in spot,
                     "is_point_in_time_perpetual":"UNKNOWN"})
    plain={r["symbol"] for r in rows if r["archive_symbol_class"]=="EXACT_PLAIN_USDT_ARCHIVED"}
    extra=plain-spot
    return {"schema":SCHEMA,"source":"BINANCE_OFFICIAL_S3_PUBLIC_ARCHIVE_DIRECTORY",
       "observed_at_utc":datetime.now(timezone.utc).isoformat(),
       "original_stage34_spot_758_git_blob":SPOT_BLOB,
       "original_frozen_spot_count":len(spot),
       "source_monthly_pages":monthly_proof,"source_daily_pages":daily_proof,
       "monthly_directory_count":len(monthly),"daily_directory_count":len(daily),
       "total_distinct_um_archived_symbols":len(symbols),
       "class_counts":{k:sum(r["archive_symbol_class"]==k for r in rows) for k in
                        ("EXACT_PLAIN_USDT_ARCHIVED","USDT_DATED_CONTRACT","OTHER_USDM_SYMBOL")},
       "plain_USDT_archived_count":len(plain),
       "plain_USDT_overlap_frozen_spot_758":len(plain&spot),
       "plain_USDT_not_in_frozen_spot_758":len(extra),
       "plain_USDT_not_in_Spot_758_symbols":sorted(extra),
       "source_rows":rows,
       "warnings":["Archive prefix is not historical exchangeInfo", 
                   "Plain USDT naming does NOT itself prove every month was PERPETUAL or actually tradable",
                   "Some Futures-only symbols might have old Spot pairs with other quote assets",
                   "Directory prefix does NOT prove 1h historical publisher SHA completeness",
                   "No future winner label calculated or classifier fitted"],
       "actual_L2_or_fills":"UNVERIFIED","other_AI_review":"NOT_DONE",
       "production_deployment":"NO_GO","Frank":"UNCHANGED","Gmail":"OFF","trading":"NO_GO"}

def selftest():
    assert classify("BTCUSDT")=="EXACT_PLAIN_USDT_ARCHIVED"
    assert classify("BTCUSDT_210326")=="USDT_DATED_CONTRACT"
    assert classify("ETHUSDC")=="OTHER_USDM_SYMBOL"
    r=b"""<?xml version="1.0"?><ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/"><Prefix>data/futures/um/monthly/klines/</Prefix><IsTruncated>false</IsTruncated><CommonPrefixes><Prefix>data/futures/um/monthly/klines/BTCUSDT/</Prefix></CommonPrefixes></ListBucketResult>"""
    names,proof=list_prefix(PREFIXES[0],read=lambda _:r)
    assert names=={"BTCUSDT"} and len(proof)==1 and len(proof[0]["page_sha256"])==64
    print("STAGE36_S3_XML_PAGINATION_AND_CONTRACT_TYPE_SELFTEST_PASS")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--selftest",action="store_true")
    p.add_argument("--output",type=Path)
    a=p.parse_args()
    if a.selftest:selftest();return
    if a.output is None:p.error("--output required")
    result=inventory()
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2,ensure_ascii=False,sort_keys=True)+"\n",encoding="utf-8")
    print("STAGE36_OFFICIAL_USDM_ARCHIVE_INVENTORY "+json.dumps({
      k:v for k,v in result.items() if k in ("total_distinct_um_archived_symbols","monthly_directory_count","daily_directory_count","plain_USDT_archived_count","plain_USDT_not_in_frozen_spot_758")},sort_keys=True))
if __name__=="__main__":main()
