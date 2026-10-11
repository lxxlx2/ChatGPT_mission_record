#!/usr/bin/env python3
"""Stage28: ACTUAL production process_queue in one shared SQLite per date.

Feeds ALL 1132 original Stage26 timestamped WATCHs into the exact V4 queue.
Production evaluate_closed_5m uses freshly downloaded official Binance
Spot daily 5m CSV ZIPs, SHA256 checked against Binance .CHECKSUM publisher.
Not a complete global D0 scanner: upstream historical WATCH timestamps came
from individually replayed Stage26 models; D0 invalidations are not injected.
"""
import argparse
import bisect
import collections
import csv
import hashlib
import io
import json
import re
import tempfile
import urllib.error
import zipfile
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

try:
    import monster_v4_stage27_shared_queue_cash_ledger as original
    import monster_v4_shadow as production
    import monster_v4_archive_crosscheck as official
except ImportError:
    from scripts import monster_v4_stage27_shared_queue_cash_ledger as original
    from scripts import monster_v4_shadow as production
    from scripts import monster_v4_archive_crosscheck as official

ROOT=original.EVIDENCE
CONTRACT=ROOT/"monster_stage28_exact_shared_d1_production_queue_prereg_20261011.json"
UTC=timezone.utc

def git_blob_sha(path):
    b=Path(path).read_bytes()
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()

def frozen():
    x=json.loads(CONTRACT.read_text(encoding="utf-8"))
    if x.get("schema")!="MONSTER_STAGE28_ORIGINAL_SHARED_SQLITE_D1_EXACT_PROCESS_QUEUE_PRE_REGISTERED_V1":
        raise ValueError("STAGE28_FROZEN_SCHEMA_CHANGED")
    if git_blob_sha(production.__file__)!=x["production_source_blob_sha1"]:
        raise ValueError("STAGE28_ORIGINAL_PRODUCTION_V4_CHANGED")
    if x["shared_queue_contract"]["process_queue_limit"]!=8 or x["shared_queue_contract"]["ttl_mins"]!=15:
        raise ValueError("STAGE28_QUEUE_LIMIT_DRIFT")
    return x

def normalize_ts(value):
    i=int(value)
    if i>=10**15:
        if i%1000:raise ValueError("STAGE28_NON_MILLISECOND_ALIGNED_MICRO_TIMESTAMP")
        return i//1000
    if i<10**12:raise ValueError("STAGE28_UNKNOWN_OFFICIAL_TIMESTAMP_UNIT")
    return i

def extract_5m_zip(data, checksum, symbol, day):
    token=checksum.decode("utf-8").split()
    if len(token)<1 or not re.fullmatch("[0-9a-fA-F]{64}",token[0]):
        raise ValueError("STAGE28_NO_PUBLISHER_SHA")
    digest=hashlib.sha256(data).hexdigest()
    if digest!=token[0].lower():raise ValueError("STAGE28_PUBLISHER_SHA_MISMATCH")
    member=f"{symbol}-5m-{day.isoformat()}.csv"
    if len(data)>4_000_000:raise ValueError("STAGE28_5M_ZIP_OVERSIZE")
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        if z.namelist()!=[member] or z.getinfo(member).file_size>8_000_000:
            raise ValueError("STAGE28_5M_MEMBER_MISMATCH")
        with z.open(member) as handle:
            candles=[]
            for row in csv.reader(io.TextIOWrapper(handle,encoding="utf-8")):
                if len(row)<9:raise ValueError("STAGE28_SHORT_CANDLE")
                ms=normalize_ts(row[0])
                # historical exchange timestamps are microseconds after 2025.
                candle=[ms,row[1],row[2],row[3],row[4],row[5],ms+299_999,row[7]]
                candles.append(candle)
    first=int(datetime(day.year,day.month,day.day,tzinfo=UTC).timestamp()*1000)
    if len(candles)!=288 or any(int(c[0])!=first+300000*i for i,c in enumerate(candles)):
        raise ValueError("STAGE28_BAD_DAILY_5M_CONTINUITY")
    return candles,{"symbol":symbol,"date":day.isoformat(),"sha256":digest,
                    "publisher_verified":True,"rows":len(candles)}

class Publisher5M:
    def __init__(self, downloader=official.read_url):
        self.download=downloader
        self.cache={}
        self.proofs={}
    def day(self,symbol,day):
        key=(symbol,day.isoformat())
        if key not in self.cache:
            if not re.fullmatch(r"[A-Z0-9]+USDT",symbol):
                raise ValueError("STAGE28_BAD_SYMBOL")
            fn=f"{symbol}-5m-{day.isoformat()}.zip"
            url=f"https://data.binance.vision/data/spot/daily/klines/{symbol}/5m/{fn}"
            # Read immutable official market data; never use live API ticker.
            data=self.download(url,4_000_000)
            checksum=self.download(url+".CHECKSUM",2048)
            candles,proof=extract_5m_zip(data,checksum,symbol,day)
            self.cache[key]=candles
            self.proofs[key]=proof
        return self.cache[key]
    def closed_before(self,venue,symbol,now_ms):
        if venue!="spot":raise ValueError("STAGE28_SPOT_ONLY")
        day=datetime.fromtimestamp(now_ms/1000,tz=UTC).date()
        today=self.day(symbol,day)
        previous=self.day(symbol,day-timedelta(days=1))
        combined=previous[-10:]+today
        ends=[c[6] for c in combined]
        i=bisect.bisect_left(ends,now_ms)
        return combined[max(0,i-8):i]
    def metadata(self):
        return sorted(self.proofs.values(),key=lambda x:(x["date"],x["symbol"]))

def inject_watch(db,now_ms,symbol):
    # D0 WATCH event is historical, originally emitted by actual observe_snapshot.
    # Exact global D0 priority/reason and invalidations were not archived,
    # but neither influences D1 FIFO ordering. Never invent future price inputs.
    with db:
        db.execute("""INSERT INTO candidate_queue
          (venue,symbol,first_seen_ms,last_seen_ms,priority,reason,deadline_ms)
          VALUES('spot',?,?,?,?,?,?)
          ON CONFLICT(venue,symbol) WHERE status='PENDING'
          DO UPDATE SET last_seen_ms=excluded.last_seen_ms,
            priority=MAX(candidate_queue.priority,excluded.priority)""",
          (symbol,now_ms,now_ms,100,"ORIGINAL_STAGE26_WATCH",now_ms+production.QUEUE_DEADLINE_MS))
        production.record_event(db,"spot",symbol,"WATCH_EARLY",now_ms,now_ms,
             {"source":"STAGE26_ORIGINAL_WATCH_TIMESTAMP",
              "injected_into_real_shared_D1_queue":True,
              "global_D0_replayed":False,"trading_enabled":False})

def timeline_for_date(rows,day):
    out=[]
    for row in rows:
        if row["date"]!=day:continue
        for iso in row["continuous"]["watch_utcs"]:
            t=original.previous.utc(iso)
            out.append((int(t.timestamp()*1000),row["symbol"]))
    out.sort(key=lambda x:(x[0],x[1]))
    if len(set(out))!=len(out):raise ValueError("STAGE28_DUPLICATE_WATCH_TIMESTAMP")
    return out

def shared_production_replay(watches,day,market=None,db_opener=production.open_store):
    if market is None:market=Publisher5M()
    anchor=int(datetime.fromisoformat(day+"T06:00:00+00:00").timestamp()*1000)
    end=anchor+168*3600_000
    if any(t<anchor or t>=end for t,_ in watches):
        raise ValueError("STAGE28_WATCH_OUTSIDE_FROZEN_168H")
    if watches!=sorted(watches,key=lambda x:(x[0],x[1])):
        raise ValueError("STAGE28_WATCH_ARRIVAL_ORDER_UNFROZEN")
    with tempfile.TemporaryDirectory(prefix="monster_stage28_shared_d1_") as td:
        db=db_opener(Path(td)/"all_symbols_same.sqlite")
        source_errors=[]
        def tracked_market_candles(venue,symbol,now_ms):
            try:
                return market.closed_before(venue,symbol,now_ms)
            except (ValueError,TypeError,OSError,urllib.error.URLError,urllib.error.HTTPError) as exc:
                source_errors.append(type(exc).__name__+":"+str(exc))
                raise
        try:
            ix=0
            peak_pending=0
            polls=0
            selected=0
            completed=0
            deferred=0
            late=0
            for tick in range(anchor+180000,end+21*60000,180000):
                while ix<len(watches) and watches[ix][0]<=tick:
                    tm,sym=watches[ix]
                    if tm!=tick:
                        raise ValueError("STAGE28_WATCH_NOT_ON_ORIGINAL_THREE_MINUTE_POLL")
                    inject_watch(db,tm,sym)
                    ix+=1
                pending=db.execute(
                    "SELECT COUNT(*) FROM candidate_queue WHERE status='PENDING'").fetchone()[0]
                peak_pending=max(peak_pending,pending)
                q=production.process_queue(db,tick,tracked_market_candles,limit=8)
                if source_errors:
                    raise RuntimeError("STAGE28_VERIFIED_5M_SOURCE_FAILED:"+source_errors[0][:190])
                polls+=1
                selected+=q["selected"];completed+=q["completed"]
                deferred+=q["deferred"];late+=q["late"]
                if ix==len(watches) and tick>=end+18*60000:
                    break
            if ix!=len(watches):
                raise ValueError("STAGE28_NOT_ALL_WATCH_INSERTED")
            events=[dict(x) for x in db.execute(
                "SELECT venue,symbol,event_type,observed_ms,payload FROM events ORDER BY observed_ms,event_id")]
            queue=[dict(x) for x in db.execute("""SELECT id,venue,symbol,first_seen_ms,
              last_seen_ms,status,attempts,deadline_ms,last_error,
              last_evaluated_bar_ms,retry_after_ms FROM candidate_queue
              ORDER BY first_seen_ms,id""")]
            stats=dict(collections.Counter(x["status"] for x in queue))
            types=dict(collections.Counter(x["event_type"] for x in events))
            setup=[{"symbol":x["symbol"],"utc":datetime.fromtimestamp(
                x["observed_ms"]/1000,tz=UTC).isoformat().replace("+00:00","Z")}
                for x in events if x["event_type"]=="SETUP_ACTIVE"]
            lateness=[{"symbol":x["symbol"],"observed_ms":x["observed_ms"],
                "payload":json.loads(x["payload"])}
                for x in events if x["event_type"]=="LATE_REVIEW"]
            unresolved=[q for q in queue if q["status"]=="PENDING"]
            return {"schema":"MONSTER_STAGE28_ACTUAL_PRODUCTION_SHARED_SQLITE_D1_WITH_FROZEN_WATCH_V1",
                "date":day,"watch_arrivals":len(watches),
                "queue_candidates":len(queue),"polls":polls,
                "production_processor_selected_total":selected,
                "production_processor_completed_total":completed,
                "production_processor_deferred_total":deferred,
                "production_processor_late_total":late,
                "max_pending_before_poll":peak_pending,
                "candidate_status_counts":stats,"event_counts":types,
                "actual_shared_sqlite_process_queue":True,
                "global_observe_snapshot_replayed":False,
                "D0_invalidation_event_injection":False,
                "setups":setup,"late_events":lateness,
                "queue_final":queue,
                "pending_at_end":len(unresolved),
                "source_5m_official_SHA256":market.metadata(),
                "actual_real_money_order_or_email":False}
        finally:
            db.close()

def stage28_day(day,original_files,market=None):
    cfg=frozen()
    if day not in cfg["source_dates"]:raise ValueError("STAGE28_UNREGISTERED_DAY")
    rows=original.original_cases(original_files)
    source=timeline_for_date(rows,day)
    if sum(len(timeline_for_date(rows,d)) for d in cfg["source_dates"])!=cfg["watch_events_expected"]:
        raise ValueError("STAGE28_ORIGINAL_1132_WATCHES_CHANGED")
    outcome=shared_production_replay(source,day,market=market)
    individual=sum(len(x["continuous"]["setup_utcs"]) for x in rows if x["date"]==day)
    outcome["original_stage26_individual_D1_setups"]=individual
    outcome["production_D1_vs_individual_difference"]=len(outcome["setups"])-individual
    outcome["source_original_36_sha_reverified"]=True
    outcome["independent_other_AI_review"]="NOT_DONE"
    outcome["deployment"]="NO_GO"
    outcome["frank"]="UNCHANGED"
    return outcome

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--day",required=True)
    ap.add_argument("--original-zips",nargs=36,type=Path,required=True)
    ap.add_argument("--output",required=True,type=Path)
    args=ap.parse_args()
    d=stage28_day(args.day,args.original_zips)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(d,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("STAGE28_RESULT_JSON "+json.dumps({
        k:v for k,v in d.items() if k not in
        ("setups","late_events","queue_final","source_5m_official_SHA256")
    },sort_keys=True),flush=True)

if __name__=="__main__":
    main()
