#!/usr/bin/env python3
"""Monster Stage70: offline-only research WATCH projection into isolated SQLite.

Source verified Stage68+69 event ledgers. This is NOT a production service,
BUY engine, live quote, email sender, or Mac deployment. One ACID transaction;
strict journal idempotence and no silent loss when research cap is exhausted.
"""
from __future__ import annotations
import argparse,collections,hashlib,json,sqlite3
from datetime import datetime,timezone
from pathlib import Path

BASE=Path(__file__).resolve().parents[2]/"monster"
E=BASE/"evidence"
FIRST=E/"monster_stage68_original2700_all252_D0_P1_watch_and_research_urgency_states.jsonl"
SECOND=E/"monster_stage69_older6_all685_WATCH_P1_replayed_budget_events.jsonl"
DESIGN=BASE/"MONSTER_STAGE70_WATCH_NEVER_DROPPED_SQLITE_PROJECTION_TECH_DESIGN_20261012.md"
PINS={
 FIRST.name:"8e5d3247aaf04ffd00e44d1ef214e4939d75fa6b",
 SECOND.name:"d34ff59b559023af0b0db67c818fb9b2649c0363",
 DESIGN.name:"2cf1588cfb7f6bce935b5be528aaa6e57daedbc1",
}
SCHEMA="MONSTER_STAGE70_ISOLATED_SQLITE_HISTORIC_FIRST_D0_AND_P1_READ_MODEL_V1"

DDL=(
 "CREATE TABLE IF NOT EXISTS monster_research_journal "
 "(event_id TEXT PRIMARY KEY, window_date TEXT NOT NULL, symbol TEXT NOT NULL, "
 "at_utc TEXT NOT NULL, event_kind TEXT NOT NULL, payload_sha256 TEXT NOT NULL, "
 "payload_json TEXT NOT NULL)",
 "CREATE TABLE IF NOT EXISTS monster_research_watch "
 "(window_date TEXT NOT NULL, symbol TEXT NOT NULL, first_d0_utc TEXT NOT NULL, "
 "first_p1_utc TEXT, last_update_utc TEXT NOT NULL, stage TEXT NOT NULL, "
 "historical_only INTEGER NOT NULL CHECK(historical_only=1), "
 "execution_status TEXT NOT NULL CHECK(execution_status='UNVERIFIED'), "
 "order_notional_status TEXT NOT NULL CHECK(order_notional_status='UNSPECIFIED'), "
 "PRIMARY KEY(window_date,symbol))",
 "CREATE INDEX IF NOT EXISTS monster_research_watch_time "
 "ON monster_research_watch(last_update_utc DESC,symbol ASC)"
)
STAGES=("WATCH","URGENT_RESEARCH","CAP_DEFERRED_RESEARCH")
WATCH="FIRST_D0_WATCH"
P1="P1_FIRST_ASOF_ELIGIBLE"


def blob(path):
    raw=path.read_bytes()
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()


def source():
    for path in (FIRST,SECOND,DESIGN):
        if blob(path)!=PINS[path.name]:
            raise ValueError("STAGE70_ORIGINAL_EVIDENCE_OR_PRECODE_DESIGN_CHANGED "+path.name)
    a=[json.loads(line) for line in FIRST.read_text(encoding="utf-8").splitlines() if line]
    b=[json.loads(line) for line in SECOND.read_text(encoding="utf-8").splitlines() if line]
    if (len(a),len(b))!=(252,685):
        raise ValueError("STAGE70_EXPOSED_BOTH_SOURCE_EVENT_LEDGER_INCOMPLETE")
    return a+b


def minute(s):
    t=datetime.fromisoformat(s.replace("Z","+00:00"))
    if t.utcoffset()!=timezone.utc.utcoffset(t) or t.second or t.microsecond:
        raise ValueError("STAGE70_INVALID_SOURCE_EVENT_UTC_MINUTE")
    return int(t.timestamp()//60)


def signature(e):
    raw=json.dumps(e,sort_keys=True,separators=(",",":"),ensure_ascii=False)
    return raw,hashlib.sha256(raw.encode("utf-8")).hexdigest()


def validate(e):
    for field in ("event_id","date","symbol","at_UTC","kind","state_after","budget_action"):
        if not isinstance(e.get(field),str) or not e[field]:
            raise ValueError("STAGE70_MISSING_SOURCE_EVENT_FIELD "+field)
    if e["kind"] not in (WATCH,P1):
        raise ValueError("STAGE70_UNRECOGNIZED_REAL_EVENT")
    if e["source_venue"]!="BINANCE_USDM_FUTURES_HISTORICAL_ONLY":
        raise ValueError("STAGE70_SOURCE_MUST_NOT_IMPERSONATE_SPOT")
    if not e["NO_HISTORIC_EXECUTABLE_SPOT_PROOF"] or not e["NO_GMAIL_NO_TRADE"] or not e["ORDER_NOTIONAL_UNSPECIFIED"]:
        raise ValueError("STAGE70_SOURCE_EMBEDDED_REAL_TRADE_CLAIM")
    if e["event_id"]!="monster68:"+e["date"]+":"+e["symbol"]+":"+e["kind"]:
        raise ValueError("STAGE70_BAD_IMMUTABLE_EVENT_ID")
    stamp=minute(e["at_UTC"])
    anchor=minute(e["date"]+"T06:00:00Z")
    if not anchor<=stamp<anchor+7*1440 or (stamp-anchor)%3:
        raise ValueError("STAGE70_ORIGINAL_7DAY_EVENT_CLOCK_INVALID")
    if e["kind"]==WATCH:
        if e["state_after"]!="WATCH" or e["budget_action"]!="D0_WATCH_UNCAPPED_NO_EMAIL":
            raise ValueError("STAGE70_FIRST_WATCH_WRONGLY_BUDGETED")
    else:
        if e["state_after"] not in STAGES[1:]:
            raise ValueError("STAGE70_P1_STATE_MUST_BE_URGENT_OR_DEFERRED")
        expected=("RESEARCH_URGENT_P2_CAP_CONSUMED" if e["state_after"]=="URGENT_RESEARCH"
                  else "P1_READY_BUT_CAP_RESERVED_OR_FULL_WATCH_RETAINED")
        if e["budget_action"]!=expected:
            raise ValueError("STAGE70_P1_BUDGET_DECISION_CONTRADICTS_STAGE")


def setup(conn):
    for sql in DDL:conn.execute(sql)


def ingest(conn,rows):
    # Canonical sorting independent of shard/input arrival order.
    ordered=sorted(rows,key=lambda e:(minute(e["at_UTC"]),0 if e["kind"]==WATCH else 1,
                                      e["date"],e["symbol"],e["event_id"]))
    try:
        conn.execute("BEGIN IMMEDIATE")
        inserted=0
        for e in ordered:
            validate(e)
            raw,sha=signature(e)
            old=conn.execute(
                "SELECT payload_sha256 FROM monster_research_journal WHERE event_id=?",
                (e["event_id"],)).fetchone()
            if old:
                if old[0]!=sha:
                    raise ValueError("STAGE70_DUPLICATE_ID_WITH_DIFFERENT_IMMUTABLE_PAYLOAD")
                continue
            key=(e["date"],e["symbol"])
            record=conn.execute(
                "SELECT first_d0_utc,first_p1_utc,stage FROM monster_research_watch "
                "WHERE window_date=? AND symbol=?",key).fetchone()
            if e["kind"]==WATCH:
                if record:raise ValueError("STAGE70_DUPLICATE_FIRST_D0_WATCH")
                conn.execute(
                    "INSERT INTO monster_research_watch "
                    "(window_date,symbol,first_d0_utc,first_p1_utc,last_update_utc,stage,"
                    "historical_only,execution_status,order_notional_status) "
                    "VALUES (?,?,?,NULL,?,'WATCH',1,'UNVERIFIED','UNSPECIFIED')",
                    (e["date"],e["symbol"],e["at_UTC"],e["at_UTC"]))
            else:
                if not record or record[1] is not None or minute(e["at_UTC"])<minute(record[0]):
                    raise ValueError("STAGE70_P1_WITHOUT_CAUSAL_AND_UNIQUE_FIRST_D0")
                conn.execute(
                    "UPDATE monster_research_watch SET first_p1_utc=?,last_update_utc=?,stage=? "
                    "WHERE window_date=? AND symbol=?",
                    (e["at_UTC"],e["at_UTC"],e["state_after"],*key))
            conn.execute(
                "INSERT INTO monster_research_journal "
                "(event_id,window_date,symbol,at_utc,event_kind,payload_sha256,payload_json) "
                "VALUES (?,?,?,?,?,?,?)",
                (e["event_id"],e["date"],e["symbol"],e["at_UTC"],e["kind"],sha,raw))
            inserted+=1
        conn.commit()
        return inserted
    except Exception:
        conn.rollback()
        raise


def snapshot(conn):
    cur=conn.execute(
        "SELECT window_date,symbol,first_d0_utc,first_p1_utc,last_update_utc,stage,"
        "historical_only,execution_status,order_notional_status "
        "FROM monster_research_watch ORDER BY last_update_utc DESC,window_date,symbol")
    fields=[v[0] for v in cur.description]
    return [dict(zip(fields,row)) for row in cur]


def counts(conn):
    journal=conn.execute("SELECT COUNT(*) FROM monster_research_journal").fetchone()[0]
    by=dict(conn.execute(
        "SELECT stage, COUNT(*) FROM monster_research_watch GROUP BY stage"))
    p1=conn.execute("SELECT COUNT(*) FROM monster_research_watch WHERE first_p1_utc IS NOT NULL").fetchone()[0]
    return {"journal_events":journal,"unique_first_D0_watch":sum(by.values()),
            "P1_upgraded":p1,"stage_counts":by}


def test():
    from tempfile import TemporaryDirectory
    def rec(symbol,kind,time,stage,decision):
        return {
            "event_id":"monster68:2025-03-30:"+symbol+":"+kind,
            "date":"2025-03-30","symbol":symbol,"at_UTC":time,
            "kind":kind,"state_after":stage,"budget_action":decision,
            "source_venue":"BINANCE_USDM_FUTURES_HISTORICAL_ONLY",
            "NO_HISTORIC_EXECUTABLE_SPOT_PROOF":True,
            "NO_GMAIL_NO_TRADE":True,"ORDER_NOTIONAL_UNSPECIFIED":True,
        }
    a=rec("AUSDT",WATCH,"2025-03-30T06:00:00Z","WATCH","D0_WATCH_UNCAPPED_NO_EMAIL")
    b=rec("AUSDT",P1,"2025-03-30T06:03:00Z","CAP_DEFERRED_RESEARCH",
          "P1_READY_BUT_CAP_RESERVED_OR_FULL_WATCH_RETAINED")
    wrong=rec("AUSDT",P1,"2025-03-30T06:03:00Z","URGENT_RESEARCH",
              "RESEARCH_URGENT_P2_CAP_CONSUMED")
    with TemporaryDirectory() as dir:
        db=Path(dir)/"isolated-monster-stage70.sqlite3"
        with sqlite3.connect(db,isolation_level=None) as conn:
            setup(conn)
            assert ingest(conn,[b,a])==2
            assert ingest(conn,[a,b])==0
            assert counts(conn)["stage_counts"]=={"CAP_DEFERRED_RESEARCH":1}
            state=snapshot(conn)
        with sqlite3.connect(db,isolation_level=None) as conn:
            setup(conn)
            assert snapshot(conn)==state
            try:ingest(conn,[a,wrong])
            except ValueError as e:assert "DIFFERENT_IMMUTABLE" in str(e)
            else:raise AssertionError("STAGE70_FAILED_TO_REJECT_CONFLICT")
            assert snapshot(conn)==state and counts(conn)["journal_events"]==2
            try:ingest(conn,[rec("ZUSDT",P1,"2025-03-30T06:09:00Z",
                  "URGENT_RESEARCH","RESEARCH_URGENT_P2_CAP_CONSUMED")])
            except ValueError as e:assert "WITHOUT_CAUSAL" in str(e)
            else:raise AssertionError("STAGE70_P1_WITHOUT_WATCH_ALLOWED")
            assert counts(conn)["journal_events"]==2
    print("STAGE70_SQLITE_ACID_WATCH_IDEMPOTENT_RESTART_AND_SOURCE_PROVENANCE_TEST_PASS")


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--selftest",action="store_true")
    ap.add_argument("--db",type=Path)
    ap.add_argument("--out",type=Path)
    args=ap.parse_args()
    if args.selftest:test();return
    if args.db is None or args.out is None or str(args.db)==":memory:":
        ap.error("--db path and --out required, no production defaults")
    if not args.db.parent.is_dir():ap.error("database directory must exist")
    data=source()
    with sqlite3.connect(args.db,isolation_level=None) as conn:
        setup(conn)
        n=ingest(conn,data)
        audit=counts(conn)
        first=snapshot(conn)
    with sqlite3.connect(args.db,isolation_level=None) as conn:
        setup(conn)
        if ingest(conn,list(reversed(data)))!=0:
            raise ValueError("STAGE70_REPLAY_RESTART_NOT_IDEMPOTENT")
        if counts(conn)!=audit or snapshot(conn)!=first:
            raise ValueError("STAGE70_RESTART_PROJECTION_DIGEST_CHANGED")
    if (n,audit["journal_events"],audit["unique_first_D0_watch"],
        audit["P1_upgraded"])!=(937,937,715,222):
        raise ValueError("STAGE70_INPUT_EVENTS_OR_WATCH_DROPPED")
    if audit["stage_counts"]!={"WATCH":493,"URGENT_RESEARCH":161,"CAP_DEFERRED_RESEARCH":61}:
        raise ValueError("STAGE70_P2_HISTORIC_RESEARCH_BUDGET_STATES_DRIFT")
    args.out.mkdir(parents=True,exist_ok=True)
    (args.out/"monster_stage70_offline_sqlite_watch_projection_summary.json").write_text(
        json.dumps({"schema":SCHEMA,"input_git_blobs":PINS,**audit,
                    "reimported_937_idempotent":True,"sqlite_restart_exact_snapshot_parity":True,
                    "HISTORICAL_RESEARCH_ONLY":True,"source_censored_were_not_declared_negative":True,
                    "EXECUTION_AND_REAL_NOTIONAL":"UNKNOWN",
                    "OTHER_AI_REVIEW":"NOT_DONE","MONSTER_DEPLOY":"NO_GO",
                    "GMAIL":"OFF","AUTOTRADE":"NO_GO"},sort_keys=True,indent=2)+"\n",encoding="utf-8")
    (args.out/"monster_stage70_offline_readonly_715_watch_items.jsonl").write_text(
        "".join(json.dumps(x,sort_keys=True,ensure_ascii=False)+"\n" for x in first),encoding="utf-8")
    print("STAGE70_EXACT_715_WATCH_937_EVENTS_NO_LOSS_RESTART "+
          json.dumps(audit,sort_keys=True))


if __name__=="__main__":
    main()
