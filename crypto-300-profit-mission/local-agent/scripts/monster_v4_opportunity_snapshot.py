#!/usr/bin/env python3
"""Read-only, non-production Monster D0/D1/D2 opportunity snapshot.

Reads the existing Monster SQLite contract. Never sends, trades, scans, or
uses network access. A historical SETUP is not an actionable BUY.
"""
import argparse
import hashlib
import json
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path

MAX_SOURCE_LAG_MS = 6 * 60_000
QUEUE_VALID_MS = 15 * 60_000
REQUIRED = {"candidate_queue", "events", "d2_reviews", "polls", "source_state", "snapshots"}


def event_id(venue, symbol, event_type, anchor):
    return hashlib.sha256(
        f"MONSTER_V4|{venue}|{symbol}|{event_type}|{anchor}".encode("utf-8")
    ).hexdigest()


def utc_time(ms):
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def _get(db, sql, params):
    row = db.execute(sql, params).fetchone()
    return dict(row) if row is not None else None


def read_snapshot(db_path, now_ms, limit=25, window_hours=24):
    """Inspect already stored state as read-only; never reconstruct past state."""
    if not isinstance(now_ms, int) or now_ms <= 0 or not 1 <= limit <= 200 or not 1 <= window_hours <= 168:
        raise ValueError("INVALID_SNAPSHOT_ARGUMENT")
    path = Path(db_path)
    if not path.is_file():
        raise FileNotFoundError("MONSTER_DB_NOT_FOUND")
    with sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True) as db:
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA query_only=ON")
        present = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if REQUIRED - present:
            raise ValueError("MONSTER_SCHEMA_INCOMPLETE:" + ",".join(sorted(REQUIRED - present)))
        sources = {}
        for venue in ("spot", "futures"):
            poll = _get(db, """SELECT observed_ms,source_total,scanned,invalid
                FROM polls WHERE venue=? AND observed_ms<=?
                ORDER BY observed_ms DESC,poll_id DESC LIMIT 1""", (venue, now_ms))
            health = _get(db, "SELECT degraded_since_ms,last_ok_ms FROM source_state WHERE venue=?", (venue,))
            source_age = now_ms - poll["observed_ms"] if poll else None
            healthy = bool(poll and source_age <= MAX_SOURCE_LAG_MS
                           and poll["invalid"] == 0 and poll["scanned"] == poll["source_total"]
                           and not (health and health["degraded_since_ms"] is not None))
            sources[venue] = {
                "state": "RECENT_STORED_POLL" if healthy else "STALE_OR_DEGRADED",
                "last_poll_utc": utc_time(poll["observed_ms"]) if poll else None,
                "age_seconds": source_age // 1000 if source_age is not None else None,
                "scanned": poll["scanned"] if poll else None,
                "source_total": poll["source_total"] if poll else None,
                "degraded_since_utc": utc_time(health["degraded_since_ms"])
                if health and health["degraded_since_ms"] is not None else None,
            }
        rows = db.execute("""SELECT * FROM candidate_queue
            WHERE first_seen_ms BETWEEN ? AND ?
            ORDER BY first_seen_ms DESC,id DESC LIMIT ?""",
            (now_ms - window_hours * 3_600_000, now_ms, limit)).fetchall()
        entries = []
        for r in rows:
            q = dict(r)
            venue, symbol, first = q["venue"], q["symbol"], q["first_seen_ms"]
            watch = _get(db, "SELECT observed_ms,payload FROM events WHERE event_id=? AND observed_ms<=?",
                         (event_id(venue, symbol, "WATCH_EARLY", first), now_ms))
            setup_key = event_id(venue, symbol, "SETUP_ACTIVE", q["id"])
            setup = _get(db, "SELECT observed_ms FROM events WHERE event_id=? AND observed_ms<=?",
                         (setup_key, now_ms))
            d2 = _get(db, """SELECT status,observed_ms,attempts,last_error
                FROM d2_reviews WHERE source_event_id=?""", (setup_key,)) if setup else None
            d2_event = _get(db, "SELECT observed_ms,payload FROM events WHERE event_id=? AND observed_ms<=?",
                            (event_id(venue, symbol, "D2_LIQUIDITY", setup_key), now_ms)) if d2 else None
            quote = _get(db, """SELECT observed_ms,price,quote24 FROM snapshots
                WHERE venue=? AND symbol=? AND observed_ms<=?""", (venue, symbol, now_ms))
            try:
                why = json.loads(watch["payload"]) if watch is not None else {}
                if not isinstance(why, dict):
                    why = {}
            except (ValueError, TypeError):
                why = {}
            expired = now_ms > q["deadline_ms"] or now_ms - first > QUEUE_VALID_MS
            source_ok = sources.get(venue, {}).get("state") == "RECENT_STORED_POLL"
            if q["status"] == "INVALIDATED":
                state = "INVALIDATED"
            elif q["status"] == "LATE":
                state = "MISSED_D1_DEADLINE"
            elif expired:
                state = "EXPIRED"
            elif not source_ok:
                state = "SOURCE_STALE"
            elif not watch:
                state = "MISSING_WATCH_EVIDENCE"
            elif setup:
                state = "SETUP_RESEARCH_ONLY" if venue == "spot" else "FUTURES_ONLY_SETUP"
            elif q["status"] == "PENDING":
                state = "WATCH_RESEARCH_ONLY"
            else:
                state = "CLOSED_WITHOUT_SETUP"
            depth = None
            if d2_event is not None:
                try:
                    payload = json.loads(d2_event["payload"])
                    depth = payload.get("depth")
                except (ValueError, TypeError):
                    depth = None
            entries.append({
                "venue": venue, "symbol": symbol,
                "first_watch_utc": utc_time(first),
                "watch_evidence_present": watch is not None,
                "watch_reason": q["reason"], "watch_priority_research_only": q["priority"],
                "watch_observed_move_pct": why.get("return_snapshot_pct"),
                "watch_lookback_window_ms": why.get("research_window_ms"),
                "watch_quote24_at_trigger": why.get("quote24_usdt"),
                "watch_classification": why.get("classification"),
                "d1_last_error": q["last_error"],
                "latest_quote_utc": utc_time(quote["observed_ms"]) if quote else None,
                "last_stored_price": quote["price"] if quote else None,
                "last_stored_quote24": quote["quote24"] if quote else None,
                "queue_status": q["status"], "deadline_utc": utc_time(q["deadline_ms"]),
                "signal": state, "setup_utc": utc_time(setup["observed_ms"]) if setup else None,
                "d2_status": d2["status"] if d2 else "NOT_CAPTURED",
                "d2_observed_utc": utc_time(d2_event["observed_ms"]) if d2_event else None,
                "d2_research_liquidity_gate": depth.get("research_liquidity_gate")
                    if isinstance(depth, dict) else None,
                "d2_fee_source": depth.get("fee_source") if isinstance(depth, dict) else None,
                "d2_spread_bps": depth.get("spread_bps") if isinstance(depth, dict) else None,
                "d2_instant_roundtrip_cost_bps":
                    depth.get("instant_roundtrip_cost_bps") if isinstance(depth, dict) else None,
                "d2_depth_fully_filled":
                    depth.get("depth_fully_filled") if isinstance(depth, dict) else None,
                "d2_assumed_budget_usdt": depth.get("budget_usdt")
                    if isinstance(depth, dict) else None,
                "g4_real_execution": "UNKNOWN",
                "recommendation": "RESEARCH_REVIEW_ONLY_NO_BUY",
            })
        return {
            "schema": "MONSTER_V4_OPERATOR_RESEARCH_SNAPSHOT_V1",
            "asof_utc": utc_time(now_ms), "mode": "OFFLINE_SQLITE_READ_ONLY",
            "historical_asof_reconstruction": False,
            "production": "NO_GO", "trading": "NO_GO", "g4_real_profit": "UNKNOWN",
            "data_window_hours": window_hours, "limited_to": limit,
            "sources": sources, "opportunities": entries,
            "displayed": len(entries),
            "note": "No historical PIT reconstruction or live market quote; no trading or mail.",
        }


def main():
    p = argparse.ArgumentParser(description="Offline Monster shadow signal inspector")
    p.add_argument("--db", type=Path, required=True)
    p.add_argument("--limit", type=int, default=25)
    p.add_argument("--window-hours", type=int, default=24)
    p.add_argument("--asof-ms", type=int, default=None, help="Evaluation clock; not a historical replay")
    p.add_argument("--format", choices=("json", "text"), default="text")
    a = p.parse_args()
    result = read_snapshot(a.db, a.asof_ms if a.asof_ms is not None else int(time.time() * 1000),
                           a.limit, a.window_hours)
    if a.format == "json":
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    else:
        print("MONSTER RESEARCH ONLY | G4 UNKNOWN | G6 NO_GO | " + result["asof_utc"])
        for venue, source in result["sources"].items():
            print(venue + ": " + source["state"] + " | " + str(source["last_poll_utc"]))
        for r in result["opportunities"]:
            print(r["first_watch_utc"] + " " + r["venue"] + "/" + r["symbol"]
                  + " " + r["signal"] + " | D2=" + r["d2_status"]
                  + " | WHY=" + str(r["watch_reason"])
                  + " | MOVE=" + str(r["watch_observed_move_pct"])
                  + " | PRICE_STORED=" + str(r["last_stored_price"])
                  + " | COST_BPS_STORED=" + str(r["d2_instant_roundtrip_cost_bps"])
                  + " | NO_BUY")
        print("Shown " + str(result["displayed"]) + "; research records, not current orders.")


if __name__ == "__main__":
    main()
