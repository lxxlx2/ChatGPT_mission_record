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
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

MAX_SOURCE_LAG_MS = 6 * 60_000
QUEUE_VALID_MS = 15 * 60_000
MAX_WINDOW_EPISODES = 50_000
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
    # Explicit close: sqlite3 connection context manager alone does not close.
    # SQLite may still create WAL/SHM sidecars when opening an existing WAL DB.
    with closing(sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)) as db:
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
            # source_state is mutable current state, not an as-of history.
            # Durable transition events preserve outages even after recovery.
            transition = _get(db, """SELECT observed_ms,event_type FROM events
                WHERE venue=? AND symbol='FULL_UNIVERSE'
                AND event_type IN ('SOURCE_DEGRADED','SOURCE_RECOVERED')
                AND observed_ms<=? ORDER BY observed_ms DESC,event_id DESC LIMIT 1""",
                (venue, now_ms))
            degraded_at_asof = bool(transition and transition["event_type"] == "SOURCE_DEGRADED")
            source_age = now_ms - poll["observed_ms"] if poll else None
            healthy = bool(poll and source_age <= MAX_SOURCE_LAG_MS
                           and poll["invalid"] == 0 and poll["scanned"] == poll["source_total"]
                           and not degraded_at_asof)
            sources[venue] = {
                "state": "RECENT_STORED_POLL" if healthy else "STALE_OR_DEGRADED",
                "last_poll_utc": utc_time(poll["observed_ms"]) if poll else None,
                "age_seconds": source_age // 1000 if source_age is not None else None,
                "scanned": poll["scanned"] if poll else None,
                "source_total": poll["source_total"] if poll else None,
                "degraded_since_utc": utc_time(transition["observed_ms"])
                if degraded_at_asof else None,
                "health_origin": "PERSISTED_SOURCE_TRANSITION_EVENTS_ASOF",
            }
        # Materialize the entire requested research window *before* display
        # truncation: recent invalidated/expired episodes must not hide an
        # older, still-current WATCH or SETUP.
        rows = db.execute("""SELECT * FROM candidate_queue
            WHERE first_seen_ms BETWEEN ? AND ?
            ORDER BY first_seen_ms DESC,id DESC LIMIT ?""",
            (now_ms - window_hours * 3_600_000, now_ms,
             MAX_WINDOW_EPISODES + 1)).fetchall()
        if len(rows) > MAX_WINDOW_EPISODES:
            raise ValueError("MONSTER_OPERATOR_WINDOW_EXCEEDS_SAFE_EPISODE_LIMIT")
        entries = []
        for r in rows:
            q = dict(r)
            venue, symbol, first = q["venue"], q["symbol"], q["first_seen_ms"]
            watch = _get(db, "SELECT observed_ms,payload FROM events WHERE event_id=? AND observed_ms<=?",
                         (event_id(venue, symbol, "WATCH_EARLY", first), now_ms))
            setup_key = event_id(venue, symbol, "SETUP_ACTIVE", q["id"])
            setup = _get(db, "SELECT observed_ms FROM events WHERE event_id=? AND observed_ms<=?",
                         (setup_key, now_ms))
            # An evaluated D1 row is not rewritten by the production invalidation
            # handler. The WATCH-anchored event is the episode's source of truth.
            invalidation = _get(db, """SELECT observed_ms FROM events
                WHERE event_id=? AND observed_ms BETWEEN ? AND ?""",
                (event_id(venue, symbol, "INVALIDATED", first), first, now_ms))
            # D2 review status is mutable: CHECKED could have happened after
            # --asof-ms. Only terminal events with observed_ms<=asof are valid.
            d2_event = _get(db, """SELECT observed_ms,event_type,payload FROM events
                WHERE event_id IN (?,?,?) AND observed_ms<=?
                ORDER BY observed_ms DESC,event_id DESC LIMIT 1""",
                (event_id(venue, symbol, "D2_LIQUIDITY", setup_key),
                 event_id(venue, symbol, "D2_NOT_SPOT", setup_key),
                 event_id(venue, symbol, "D2_LATE", setup_key), now_ms)) if setup else None
            d2_status = {"D2_LIQUIDITY": "CHECKED",
                         "D2_NOT_SPOT": "FUTURES_ONLY",
                         "D2_LATE": "LATE"}.get(d2_event["event_type"], "NOT_CAPTURED") if d2_event else "NOT_CAPTURED"
            late_event = _get(db, """SELECT observed_ms FROM events
                WHERE event_id=? AND observed_ms<=?""",
                (event_id(venue, symbol, "LATE_REVIEW", q["id"]), now_ms))
            quote = _get(db, """SELECT observed_ms,price,quote24 FROM snapshots
                WHERE venue=? AND symbol=? AND observed_ms<=?""", (venue, symbol, now_ms))
            try:
                why = json.loads(watch["payload"]) if watch is not None else {}
                if not isinstance(why, dict):
                    why = {}
            except (ValueError, TypeError):
                why = {}
            expired = now_ms > q["deadline_ms"] or now_ms - first > QUEUE_VALID_MS
            venue_source = sources.get(venue, {})
            source_ok = venue_source.get("state") == "RECENT_STORED_POLL"
            quote_age_ms = now_ms - quote["observed_ms"] if quote else None
            last_poll_utc = venue_source.get("last_poll_utc")
            # Poll time is stored on every symbol actually included by D0;
            # a healthy venue poll never proves that an omitted symbol is fresh.
            seen_in_latest_poll = bool(quote and last_poll_utc
                and utc_time(quote["observed_ms"]) == last_poll_utc)
            if quote is None:
                quote_state = "MISSING"
            elif quote_age_ms > MAX_SOURCE_LAG_MS:
                quote_state = "STALE"
            elif not seen_in_latest_poll:
                quote_state = "NOT_SEEN_IN_LATEST_POLL"
            else:
                quote_state = "PRESENT_IN_LATEST_POLL"
            if invalidation is not None:
                state = "INVALIDATED"
            elif late_event is not None:
                state = "MISSED_D1_DEADLINE"
            elif expired:
                state = "EXPIRED"
            elif not source_ok:
                state = "SOURCE_STALE"
            elif quote_state != "PRESENT_IN_LATEST_POLL":
                state = "SYMBOL_QUOTE_" + quote_state
            elif not watch:
                state = "MISSING_WATCH_EVIDENCE"
            elif setup:
                state = "SETUP_RESEARCH_ONLY" if venue == "spot" else "FUTURES_ONLY_SETUP"
            else:
                # Current queue.status can be EVALUATED/LATE/INVALIDATED from a
                # *future* transition. No timestamped as-of closure event was
                # captured; retain WATCH, never fabricate a historical closure.
                state = "WATCH_RESEARCH_ONLY"
            depth = None
            if d2_status == "CHECKED":
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
                "symbol_quote_state": quote_state,
                "symbol_quote_age_seconds": quote_age_ms // 1000 if quote_age_ms is not None else None,
                "symbol_seen_in_latest_poll": seen_in_latest_poll,
                "invalidation_utc": utc_time(invalidation["observed_ms"]) if invalidation else None,
                "last_stored_price": quote["price"] if quote else None,
                "last_stored_quote24": quote["quote24"] if quote else None,
                # Derived from timestamped events/deadline, not current
                # mutable candidate_queue.status (which may reflect the future).
                "queue_status": ("INVALIDATED" if invalidation else
                                 "LATE" if late_event else
                                 "EVALUATED" if setup else
                                 "EXPIRED" if expired else "UNRESOLVED_ASOF"),
                "queue_status_origin": "ASOF_EVENTS_AND_DEADLINE_NOT_MUTABLE_QUEUE_STATE",
                "deadline_utc": utc_time(q["deadline_ms"]),
                "signal": state, "setup_utc": utc_time(setup["observed_ms"]) if setup else None,
                "d2_status": d2_status,
                "d2_status_origin": "D2_TERMINAL_EVENT_OBSERVED_BY_ASOF",
                "d2_observed_utc": utc_time(d2_event["observed_ms"]) if d2_event else None,
                "d2_research_liquidity_gate": depth.get("research_liquidity_gate")
                    if isinstance(depth, dict) else None,
                "d2_research_liquidity_gate_is_not_fill_proof": True,
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
        full_counts = {}
        for item in entries:
            full_counts[item["signal"]] = full_counts.get(item["signal"], 0) + 1
        full_total = len(entries)
        # Stable sort retains first_seen_ms DESC,id DESC within each research
        # state because SQL produced that chronology. No retrospective winners.
        research_rank = {
            "SETUP_RESEARCH_ONLY": 0,
            "WATCH_RESEARCH_ONLY": 1,
            "FUTURES_ONLY_SETUP": 2,
        }
        entries.sort(key=lambda item: research_rank.get(item["signal"], 3))
        visible = entries[:limit]
        return {
            "schema": "MONSTER_V4_OPERATOR_RESEARCH_SNAPSHOT_V2_WINDOW_COMPLETE",
            "asof_utc": utc_time(now_ms), "mode": "OFFLINE_SQLITE_READ_ONLY",
            "historical_asof_reconstruction": False,
            "asof_is_only_persisted_event_state_not_full_market_pit": True,
            "safe_full_window_episode_limit": MAX_WINDOW_EPISODES,
            "production": "NO_GO", "trading": "NO_GO", "g4_real_profit": "UNKNOWN",
            "data_window_hours": window_hours, "limited_to": limit,
            "display_priority_contract": "SPOT_SETUP_RESEARCH_THEN_WATCH_THEN_FUTURES_SETUP_THEN_DIAGNOSTICS; EACH_DESCENDING_FIRST_SEEN_ID",
            "sources": sources, "opportunities": visible,
            "window_total": full_total, "hidden_by_display_limit": full_total - len(visible),
            "counts_by_signal_full_window": dict(sorted(full_counts.items())),
            "displayed": len(visible),
            "note": "As-of state uses stored timestamped events; mutable quotes are not full historical PIT. SQLite read-only queries may create WAL/SHM sidecars; no live quote, trade or mail.",
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
                  + " | QUOTE_STATE=" + r["symbol_quote_state"]
                  + " | QUOTE_AGE_S=" + str(r["symbol_quote_age_seconds"])
                  + " | INVALIDATED_AT=" + str(r["invalidation_utc"])
                  + " | PRICE_STORED=" + str(r["last_stored_price"])
                  + " | COST_BPS_STORED=" + str(r["d2_instant_roundtrip_cost_bps"])
                  + " | NO_BUY")
        print("Shown " + str(result["displayed"]) + "/" + str(result["window_total"])
              + " stored episodes; hidden_by_display_limit=" + str(result["hidden_by_display_limit"])
              + " | full_window_states=" + json.dumps(result["counts_by_signal_full_window"], sort_keys=True)
              + " | research records, not current orders.")


if __name__ == "__main__":
    main()
