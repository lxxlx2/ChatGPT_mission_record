#!/usr/bin/env python3
"""Monster V4 non-production full-universe shadow collector and durable WATCH queue.

Binance public data only. No trading, Gmail, daemon installation, or notification sends.
Research candidate thresholds are NOT validated as a profitable strategy.
"""
import argparse
import hashlib
import json
import math
import sqlite3
import statistics
import time
import urllib.error
import urllib.parse
import urllib.request
from decimal import Decimal, InvalidOperation
from pathlib import Path

INTERVAL_MS = 300_000
MAX_DELTA_MS = 600_000
MIN_DELTA_MS = 30_000
WATCH_COOLDOWN_MS = 6 * 3_600_000
QUEUE_DEADLINE_MS = 15 * 60_000
SCHEMA = """
CREATE TABLE IF NOT EXISTS snapshots (
 venue TEXT NOT NULL, symbol TEXT NOT NULL, observed_ms INTEGER NOT NULL,
 price TEXT NOT NULL, quote24 TEXT NOT NULL, PRIMARY KEY(venue,symbol)
);
CREATE TABLE IF NOT EXISTS watch_state (
 venue TEXT NOT NULL, symbol TEXT NOT NULL, last_watch_ms INTEGER NOT NULL,
 PRIMARY KEY(venue,symbol)
);
CREATE TABLE IF NOT EXISTS candidate_queue (
 id INTEGER PRIMARY KEY AUTOINCREMENT, venue TEXT NOT NULL, symbol TEXT NOT NULL,
 first_seen_ms INTEGER NOT NULL, last_seen_ms INTEGER NOT NULL,
 priority INTEGER NOT NULL, reason TEXT NOT NULL,
 status TEXT NOT NULL DEFAULT 'PENDING', attempts INTEGER NOT NULL DEFAULT 0,
 retry_after_ms INTEGER NOT NULL DEFAULT 0, deadline_ms INTEGER NOT NULL,
 last_error TEXT
);
CREATE UNIQUE INDEX IF NOT EXISTS queue_one_pending ON candidate_queue(venue,symbol)
 WHERE status='PENDING';
CREATE TABLE IF NOT EXISTS events (
 event_id TEXT PRIMARY KEY, venue TEXT NOT NULL, symbol TEXT NOT NULL,
 event_type TEXT NOT NULL, observed_ms INTEGER NOT NULL, payload TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS outbox (
 event_id TEXT PRIMARY KEY REFERENCES events(event_id),
 created_ms INTEGER NOT NULL, status TEXT NOT NULL DEFAULT 'DRY_RUN_ONLY'
);
CREATE TABLE IF NOT EXISTS polls (
 poll_id INTEGER PRIMARY KEY AUTOINCREMENT, venue TEXT NOT NULL,
 observed_ms INTEGER NOT NULL, source_total INTEGER NOT NULL,
 scanned INTEGER NOT NULL, invalid INTEGER NOT NULL, watch_new INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS failures (
 id INTEGER PRIMARY KEY AUTOINCREMENT, venue TEXT NOT NULL,
 observed_ms INTEGER NOT NULL, stage TEXT NOT NULL, error TEXT NOT NULL
);
"""

def open_store(path):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(str(p))
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA busy_timeout=5000")
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA foreign_keys=ON")
    db.executescript(SCHEMA)
    return db

def positive(value, name):
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError("INVALID_" + name) from exc
    if not result.is_finite() or result <= 0:
        raise ValueError("INVALID_" + name)
    return result

def event_key(venue, symbol, kind, anchor):
    return hashlib.sha256(
        f"MONSTER_V4|{venue}|{symbol}|{kind}|{anchor}".encode()
    ).hexdigest()

def record_event(db, venue, symbol, kind, observed_ms, anchor, payload):
    eid = event_key(venue, symbol, kind, anchor)
    db.execute(
        "INSERT OR IGNORE INTO events VALUES(?,?,?,?,?,?)",
        (eid, venue, symbol, kind, observed_ms, json.dumps(payload,sort_keys=True))
    )
    db.execute("INSERT OR IGNORE INTO outbox(event_id,created_ms) VALUES(?,?)",
               (eid, observed_ms))
    return eid

def observe_snapshot(db, venue, observed_ms, rows, min_quote24=Decimal("100000")):
    """Complete-time snapshots; rolling 24h turnover is CONTEXT, not 3m volume.

    The initial snapshot establishes a baseline and cannot trigger a 3m momentum
    signal. Reused, nonmonotonic, and stale (>10m) symbol baselines do not alert.
    """
    if venue not in ("spot","futures") or not isinstance(observed_ms,int) or observed_ms<=0:
        raise ValueError("INVALID_POLL")
    if not isinstance(rows,list) or not rows:
        raise ValueError("EMPTY_FULL_MARKET_SNAPSHOT")
    symbols=set()
    valid=[]
    invalid=0
    for row in rows:
        try:
            sym=row["symbol"]
            if not isinstance(sym,str) or not sym.endswith("USDT") or not sym.isascii():
                raise ValueError("BAD_SYMBOL")
            if sym in symbols:
                raise ValueError("DUPLICATE_SYMBOL")
            symbols.add(sym)
            p=positive(row["lastPrice"],"PRICE")
            q=positive(row["quoteVolume"],"QUOTE24")
            valid.append((sym,p,q))
        except (KeyError,ValueError,TypeError):
            invalid+=1
    if not valid:
        raise ValueError("NO_VALID_MARKET_SYMBOLS")
    watch_new=0
    with db:
        last=db.execute("SELECT MAX(observed_ms) AS t FROM polls WHERE venue=?",
                        (venue,)).fetchone()["t"]
        if last is not None and observed_ms<=last:
            raise ValueError("NON_MONOTONIC_MARKET_POLL")
        for symbol,price,quote in valid:
            prev=db.execute(
                "SELECT observed_ms,price FROM snapshots WHERE venue=? AND symbol=?",
                (venue,symbol)).fetchone()
            ret=None
            if prev is not None and MIN_DELTA_MS<=observed_ms-prev["observed_ms"]<=MAX_DELTA_MS:
                ret=price/Decimal(prev["price"])-Decimal(1)
            db.execute("""INSERT INTO snapshots VALUES(?,?,?,?,?)
                ON CONFLICT(venue,symbol) DO UPDATE SET
                observed_ms=excluded.observed_ms,price=excluded.price,
                quote24=excluded.quote24""",
                (venue,symbol,observed_ms,str(price),str(quote)))
            if ret is None or ret<Decimal("0.05") or quote<min_quote24:
                continue
            reason="FAST_3M_PRICE_PLUS_24H_LIQUIDITY_CONTEXT"
            priority=min(100,int(ret*1000))
            db.execute("""INSERT INTO candidate_queue
                (venue,symbol,first_seen_ms,last_seen_ms,priority,reason,deadline_ms)
                VALUES(?,?,?,?,?,?,?)
                ON CONFLICT(venue,symbol) WHERE status='PENDING'
                DO UPDATE SET last_seen_ms=excluded.last_seen_ms,
                 priority=MAX(candidate_queue.priority,excluded.priority)""",
                (venue,symbol,observed_ms,observed_ms,priority,reason,
                 observed_ms+QUEUE_DEADLINE_MS))
            prev_watch=db.execute(
                "SELECT last_watch_ms FROM watch_state WHERE venue=? AND symbol=?",
                (venue,symbol)).fetchone()
            if prev_watch is not None and observed_ms-prev_watch["last_watch_ms"]<WATCH_COOLDOWN_MS:
                continue
            db.execute("""INSERT INTO watch_state VALUES(?,?,?)
                ON CONFLICT(venue,symbol) DO UPDATE SET last_watch_ms=excluded.last_watch_ms""",
                (venue,symbol,observed_ms))
            record_event(db,venue,symbol,"WATCH_EARLY",observed_ms,observed_ms,
                {"observed_ms":observed_ms,"return_snapshot_pct":round(float(ret*100),4),
                 "snapshot_lag_ms":observed_ms-prev["observed_ms"],
                 "quote24_usdt":str(quote),"venue":venue,
                 "classification":"RESEARCH_WATCH_NOT_BUY",
                 "execution_verified":False})
            watch_new+=1
        db.execute("""INSERT INTO polls
            (venue,observed_ms,source_total,scanned,invalid,watch_new)
            VALUES(?,?,?,?,?,?)""",
            (venue,observed_ms,len(rows),len(valid),invalid,watch_new))
    return {"venue":venue,"source_total":len(rows),"valid":len(valid),
            "invalid":invalid,"watch_new":watch_new}

def evaluate_closed_5m(candles, observed_ms):
    """Feature check using only six fully closed contiguous 5m Binance candles."""
    if len(candles)<6:
        raise ValueError("INSUFFICIENT_CLOSED_5M")
    usable=[]
    for c in candles:
        if len(c)<8:
            raise ValueError("BAD_KLINE_SHAPE")
        t=int(c[0]); closed=int(c[6])
        if closed>=observed_ms or closed<t or closed-t>INTERVAL_MS:
            continue
        op=positive(c[1],"OPEN"); hi=positive(c[2],"HIGH")
        lo=positive(c[3],"LOW"); close=positive(c[4],"CLOSE")
        if not (lo<=op<=hi and lo<=close<=hi):
            raise ValueError("BAD_OHLC")
        q=positive(c[7],"CLOSED_QUOTE")
        usable.append((t,close,q))
    usable=usable[-6:]
    if len(usable)!=6 or any(usable[i+1][0]-usable[i][0]!=INTERVAL_MS for i in range(5)):
        raise ValueError("GAPPED_OR_OPEN_5M")
    closes=[x[1] for x in usable]
    quotes=[x[2] for x in usable]
    persistence=sum(closes[i]>closes[i-1] for i in (3,4,5))
    ratio=statistics.median(quotes[3:])/statistics.median(quotes[:3])
    setup=(persistence>=2 and ratio>=Decimal("1.5") and closes[-1]>=closes[2])
    return {"closed_5m":6,"positive_steps_last3":persistence,
            "recent_vs_earlier_15m_quote_ratio":round(float(ratio),4),
            "setup_candidate":setup,"bar_last_open_ms":usable[-1][0],
            "classification":"RESEARCH_ONLY_UNVALIDATED"}

def process_queue(db, now_ms, fetch_candles, limit=8):
    """Oldest first, never drop deferred entries; failures persist with retry.

    A stale candidate becomes a recorded late-review event, never a live BUY.
    """
    if limit<1:
        raise ValueError("BAD_PROCESS_LIMIT")
    completed=0; deferred=0; late=0
    pending=db.execute("""SELECT * FROM candidate_queue WHERE status='PENDING'
        AND retry_after_ms<=? ORDER BY first_seen_ms,id LIMIT ?""",
        (now_ms,limit)).fetchall()
    for item in pending:
        with db:
            if now_ms>item["deadline_ms"]:
                db.execute("UPDATE candidate_queue SET status='LATE' WHERE id=?",
                           (item["id"],))
                record_event(db,item["venue"],item["symbol"],"LATE_REVIEW",
                             now_ms,item["id"],{"first_seen_ms":item["first_seen_ms"],
                             "deadline_ms":item["deadline_ms"],
                             "classification":"STALE_NOT_ACTIONABLE"})
                late+=1
                continue
        try:
            details=evaluate_closed_5m(
                fetch_candles(item["venue"],item["symbol"],now_ms),now_ms)
        except (ValueError,TypeError,KeyError,OSError,urllib.error.URLError) as exc:
            with db:
                tries=item["attempts"]+1
                db.execute("""UPDATE candidate_queue SET attempts=?,
                    retry_after_ms=?,last_error=? WHERE id=?""",
                    (tries,now_ms+min(60_000*2**min(tries,5),600_000),
                     type(exc).__name__+":"+str(exc)[:160],item["id"]))
                db.execute("INSERT INTO failures(venue,observed_ms,stage,error) VALUES(?,?,?,?)",
                           (item["venue"],now_ms,"D1",type(exc).__name__))
            deferred+=1
            continue
        with db:
            db.execute("UPDATE candidate_queue SET status='EVALUATED' WHERE id=?",
                       (item["id"],))
            if details["setup_candidate"]:
                record_event(db,item["venue"],item["symbol"],"SETUP_ACTIVE",
                             now_ms,item["id"],details)
            completed+=1
    return {"completed":completed,"deferred":deferred,"late":late,
            "selected":len(pending)}

def health(db, now_ms):
    counts={r["status"]:r["n"] for r in db.execute(
        "SELECT status,COUNT(*) AS n FROM candidate_queue GROUP BY status")}
    oldest=db.execute("SELECT MIN(first_seen_ms) AS t FROM candidate_queue WHERE status='PENDING'").fetchone()["t"]
    polls=[dict(r) for r in db.execute("""SELECT p.* FROM polls p
        JOIN (SELECT venue,MAX(poll_id) AS id FROM polls GROUP BY venue) v ON p.poll_id=v.id
        ORDER BY p.venue""")]
    return {"mode":"NON_PRODUCTION_SHADOW","production_trading":"NO_GO",
            "mail_sent":0,"outbox_dry_run":db.execute("SELECT COUNT(*) FROM outbox").fetchone()[0],
            "events":dict((r["event_type"],r["n"]) for r in db.execute(
                "SELECT event_type,COUNT(*) AS n FROM events GROUP BY event_type")),
            "queue":counts,"oldest_pending_age_sec":max(0,(now_ms-oldest)//1000) if oldest else None,
            "last_polls":polls,"source_failures":db.execute("SELECT COUNT(*) FROM failures").fetchone()[0]}

def binance_json(url,timeout=12):
    request=urllib.request.Request(url,headers={"User-Agent":"MonsterV4Shadow/0.1"})
    with urllib.request.urlopen(request,timeout=timeout) as resp:
        return json.loads(resp.read(20_000_000))

HOSTS={"spot":"https://api.binance.com","futures":"https://fapi.binance.com"}
ENDPOINTS={"spot":("/api/v3/exchangeInfo","/api/v3/ticker/24hr","/api/v3/klines"),
           "futures":("/fapi/v1/exchangeInfo","/fapi/v1/ticker/24hr","/fapi/v1/klines")}
def fetch_market(venue):
    base=HOSTS[venue]; info,ticker,_=ENDPOINTS[venue]
    listing=binance_json(base+info)["symbols"]
    tradable={s["symbol"] for s in listing
        if s.get("status")=="TRADING" and s["symbol"].endswith("USDT")
        and (venue=="spot" and s.get("isSpotTradingAllowed",True)
             or venue=="futures" and s.get("contractType")=="PERPETUAL")}
    snapshot=binance_json(base+ticker)
    if not isinstance(snapshot,list):
        raise ValueError("NO_ALL_MARKET_RESPONSE")
    return [x for x in snapshot if x.get("symbol") in tradable],len(tradable)

def fetch_5m(venue,symbol,now_ms):
    base=HOSTS[venue]; endpoint=ENDPOINTS[venue][2]
    url=base+endpoint+"?"+urllib.parse.urlencode(
        {"symbol":symbol,"interval":"5m","limit":8})
    return binance_json(url)

def scan_once(db,now_ms):
    reports=[]
    for venue in ("spot","futures"):
        try:
            rows,expected=fetch_market(venue)
            if not expected or len(rows)<expected:
                raise ValueError("PARTIAL_EXCHANGEINFO_TICKER_COVERAGE")
            reports.append(observe_snapshot(db,venue,now_ms,rows))
        except (ValueError,KeyError,TypeError,urllib.error.URLError,OSError) as exc:
            with db:
                db.execute("INSERT INTO failures(venue,observed_ms,stage,error) VALUES(?,?,?,?)",
                    (venue,now_ms,"D0",type(exc).__name__+":"+str(exc)[:160]))
            reports.append({"venue":venue,"error":type(exc).__name__})
    reports.append({"queue":process_queue(db,now_ms,fetch_5m)})
    return reports

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("command",choices=("scan-once","status"))
    parser.add_argument("--db",type=Path,required=True)
    opts=parser.parse_args()
    db=open_store(opts.db)
    now_ms=int(time.time()*1000)
    if opts.command=="scan-once":
        print(json.dumps(scan_once(db,now_ms),ensure_ascii=False))
    print(json.dumps(health(db,now_ms),ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
