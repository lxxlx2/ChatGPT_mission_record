"""Isolated durable research episodes for preregistered ADR-005 D1.

This consumes immutable original-core WATCH_EARLY events and two feeds of six
already closed 5m bars. Its queue is NOT the original candidate_queue and
its event type is NOT original SETUP_ACTIVE. Never changes production D0/D1,
opens network, starts a monitor, emits BUY, mails or trades.
"""
from pathlib import Path
import hashlib
import json
import sqlite3

import monster_v4_shadow as original
from monster_v4_d1_rbtc15_last5_research import FIVE_MS, evaluate_research_candidate

RESEARCH_SCHEMA = "MONSTER_ADR005_ISOLATED_EPISODE_LEDGER_V1"
TICK_MS = 180_000
MAX_SERVICE = 8
FINAL = frozenset({"RESEARCH_SETUP", "NO_SETUP", "SOURCE_UNSCORED", "LATE_UNSCORED"})


def _db(db):
    db.row_factory = sqlite3.Row
    return db


def _schema(db):
    db.executescript("""
    CREATE TABLE metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL);
    CREATE TABLE episode(
        watch_event_id TEXT PRIMARY KEY, venue TEXT NOT NULL, symbol TEXT NOT NULL,
        first_seen_ms INTEGER NOT NULL, deadline_ms INTEGER NOT NULL,
        status TEXT NOT NULL DEFAULT 'PENDING',
        retry_after_ms INTEGER NOT NULL, last_reviewed_open_ms INTEGER,
        attempts INTEGER NOT NULL DEFAULT 0, source_censored_count INTEGER NOT NULL DEFAULT 0
    );
    CREATE UNIQUE INDEX one_research_pending_per_spot_symbol
      ON episode(venue,symbol) WHERE status='PENDING';
    CREATE TABLE research_setup(
        event_id TEXT PRIMARY KEY, watch_event_id TEXT UNIQUE NOT NULL,
        symbol TEXT NOT NULL, observed_ms INTEGER NOT NULL, payload TEXT NOT NULL,
        FOREIGN KEY(watch_event_id) REFERENCES episode(watch_event_id)
    );
    """)
    with db:
        db.execute("INSERT INTO metadata VALUES(?,?)",("schema",RESEARCH_SCHEMA))


def create_ledger(path):
    """Create a separate research file, refusing all existing files/symlinks."""
    dest=Path(path)
    if dest.exists() or dest.is_symlink():
        raise ValueError("RESEARCH_LEDGER_REFUSE_EXISTING_OUTPUT")
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("xb"):
        pass
    db=_db(sqlite3.connect(str(dest)))
    db.execute("PRAGMA foreign_keys=ON")
    _schema(db)
    return db


def reopen_ledger(path):
    dest=Path(path)
    if not dest.is_file() or dest.is_symlink():
        raise ValueError("RESEARCH_LEDGER_MISSING_OR_SYMLINK")
    db=_db(sqlite3.connect(str(dest)))
    db.execute("PRAGMA foreign_keys=ON")
    if dict(db.execute("SELECT key,value FROM metadata")).get("schema")!=RESEARCH_SCHEMA:
        db.close()
        raise ValueError("RESEARCH_LEDGER_SCHEMA_INVALID")
    return db


def admit_original_watch(db, event):
    """Idempotently import exact original WATCH event, never synthesize D0."""
    if not isinstance(event,dict) or event.get("venue")!="spot" or event.get("event_type")!="WATCH_EARLY":
        raise ValueError("ORIGINAL_SPOT_WATCH_EVENT_REQUIRED")
    venue,symbol,ms=event["venue"],event.get("symbol"),event.get("observed_ms")
    if (not isinstance(symbol,str) or not symbol.endswith("USDT") or symbol=="BTCUSDT"
            or type(ms) is not int or ms%TICK_MS):
        raise ValueError("ORIGINAL_WATCH_IDENTITY_OR_UTC_TICK_INVALID")
    expected=original.event_key(venue,symbol,"WATCH_EARLY",ms)
    if event.get("event_id")!=expected:
        raise ValueError("ORIGINAL_WATCH_ID_MISMATCH")
    old=db.execute("SELECT * FROM episode WHERE watch_event_id=?",(expected,)).fetchone()
    if old is not None:
        if old["symbol"]!=symbol or old["first_seen_ms"]!=ms:
            raise ValueError("ORIGINAL_WATCH_REUSE_DRIFT")
        return False
    with db:
        overlapping=db.execute("""SELECT watch_event_id FROM episode
             WHERE venue=? AND symbol=? AND status='PENDING'""",(venue,symbol)).fetchone()
        if overlapping:
            raise ValueError("SECOND_ORIGINAL_WATCH_WHILE_RESEARCH_PENDING")
        db.execute("""INSERT INTO episode(
          watch_event_id,venue,symbol,first_seen_ms,deadline_ms,retry_after_ms)
          VALUES(?,?,?,?,?,?)""",(expected,venue,symbol,ms,ms+original.QUEUE_DEADLINE_MS,ms))
    return True


def _negative_fully_reviewed_through_deadline(row):
    """No known final-bar opportunity missed (no inference from an early negative).

    The last eligible closed 5m bar at the original 3m deadline has an open
    time strictly before floor(deadline / 5m). A stale earlier bar can never
    establish NO_SETUP, even if one or more earlier reviews were negative.
    """
    deadline=row["deadline_ms"]
    expected_open=(deadline//FIVE_MS)*FIVE_MS-FIVE_MS
    return row["last_reviewed_open_ms"] == expected_open


def _expiry_status(row, *, source_censored_count=None):
    censored=(row["source_censored_count"] if source_censored_count is None
              else source_censored_count)
    if censored:
        return "SOURCE_UNSCORED"
    return ("NO_SETUP" if _negative_fully_reviewed_through_deadline(row)
            else "LATE_UNSCORED")


def poll_episodes(db,tick_ms,closed5_by_symbol,*,limit=MAX_SERVICE):
    """Advance independent FIFO queue once at an exact 3m UTC poll.

    closed5_by_symbol(symbol, tick_ms) must return six closed 5m candles.
    Both coin and BTC must be present. Missing data is UNSCORED, never a
    fabricated failure or zero fill. No modification of original SQLite.
    """
    if type(tick_ms) is not int or tick_ms%TICK_MS or not 1<=limit<=MAX_SERVICE:
        raise ValueError("RESEARCH_BAD_POLL_OR_CAPACITY")
    if not callable(closed5_by_symbol):
        raise TypeError("RESEARCH_SOURCE_CALLBACK_REQUIRED")
    selected=db.execute("""SELECT * FROM episode WHERE status='PENDING'
              AND retry_after_ms<=? ORDER BY first_seen_ms,watch_event_id
              LIMIT ?""",(tick_ms,limit)).fetchall()
    outcomes=[]
    for row in selected:
        identity=row["watch_event_id"]
        if tick_ms>row["deadline_ms"]:
            # Do not certify a historical negative if the deadline's last
            # observable 5m bar was never assessed (e.g. scheduler outage).
            terminal=_expiry_status(row)
            with db:
                db.execute("UPDATE episode SET status=? WHERE watch_event_id=?",
                           (terminal,identity))
            outcomes.append((identity,terminal))
            continue
        try:
            coin=closed5_by_symbol(row["symbol"],tick_ms)
            btc=closed5_by_symbol("BTCUSDT",tick_ms)
            details=evaluate_research_candidate(
                symbol=row["symbol"],observed_ms=tick_ms,
                watch_ms=row["first_seen_ms"],deadline_ms=row["deadline_ms"],
                coin_closed5=coin,btc_closed5=btc,
                last_reviewed_open_ms=row["last_reviewed_open_ms"])
        except (ValueError, KeyError, TypeError, OSError) as exc:
            details={"state":"SOURCE_CENSORED","reason":type(exc).__name__,
                     "research_setup_candidate":None}
        state=details["state"]
        if state in ("SOURCE_CENSORED","WAIT_POST_WATCH_CLOSED_5M","SAME_BAR_NO_DUPLICATE"):
            # Closing poll may reuse the previous 5m bar. A prior valid
            # negative remains NO_SETUP, rather than being mislabelled LATE
            # at the next 3m tick. Missing evidence remains SOURCE_UNSCORED.
            censored = row["source_censored_count"] + int(state=="SOURCE_CENSORED")
            terminal = "PENDING"
            if tick_ms >= row["deadline_ms"]:
                terminal = _expiry_status(row,source_censored_count=censored)
            with db:
                db.execute("""UPDATE episode SET status=?,retry_after_ms=?,
                    attempts=attempts+1,source_censored_count=?
                    WHERE watch_event_id=?""",
                    (terminal,tick_ms+TICK_MS,censored,identity))
            outcomes.append((identity,terminal if terminal!="PENDING" else state))
            continue
        if state not in ("RESEARCH_SETUP","RESEARCH_NO_SETUP_YET"):
            raise RuntimeError("RESEARCH_UNEXPECTED_COMPARATOR_STATE")
        last_bar=details["latest_5m_open_ms"]
        # A valid negative at the deadline cannot retroactively prove
        # that an earlier source-censored evaluation was negative.
        # Censored opportunities remain unresolved without explicit backfill.
        # A later positive can still complete this episode as RESEARCH_SETUP.
        terminal=("RESEARCH_SETUP" if state=="RESEARCH_SETUP" else
                  ("SOURCE_UNSCORED" if row["source_censored_count"] else "NO_SETUP")
                  if tick_ms>=row["deadline_ms"] else "PENDING")
        with db:
            db.execute("""UPDATE episode SET status=?,retry_after_ms=?,
                last_reviewed_open_ms=?,attempts=attempts+1 WHERE watch_event_id=?""",
                (terminal,tick_ms+TICK_MS,last_bar,identity))
            if terminal=="RESEARCH_SETUP":
                eid=hashlib.sha256(("MONSTER_ADR005|spot|"+row["symbol"]+"|"+
                                    identity+"|RESEARCH_SETUP").encode()).hexdigest()
                db.execute("""INSERT INTO research_setup VALUES(?,?,?,?,?)""",
                    (eid,identity,row["symbol"],tick_ms,json.dumps(details,sort_keys=True)))
        outcomes.append((identity,terminal if terminal!="PENDING" else "RESEARCH_NO_SETUP_YET"))
    return outcomes


def summary(db):
    status=dict(db.execute("SELECT status,COUNT(*) FROM episode GROUP BY status"))
    original_count=sum(status.values())
    rows=[dict(row) for row in db.execute("""SELECT e.watch_event_id,e.symbol,e.first_seen_ms,
          e.deadline_ms,e.status,e.attempts,e.source_censored_count,
          e.last_reviewed_open_ms,
          r.event_id AS research_event_id,r.observed_ms AS research_observed_ms
          FROM episode e LEFT JOIN research_setup r
          ON r.watch_event_id=e.watch_event_id
          ORDER BY e.first_seen_ms,e.watch_event_id""")]
    if len(rows)!=original_count:
        raise RuntimeError("RESEARCH_EPISODE_LEDGER_DRIFT")
    return {"schema":RESEARCH_SCHEMA,"episodes":original_count,
            "status_counts":status,"rows":rows,
            "derived_from_original_D0_watch_only":True,
            "new_D1_full_market_integrated":False,
            "real_PIT_and_execution":"UNPROVEN",
            "G2":"UNKNOWN","G3":"UNKNOWN","G4":"UNKNOWN","G6":"NO_GO"}
