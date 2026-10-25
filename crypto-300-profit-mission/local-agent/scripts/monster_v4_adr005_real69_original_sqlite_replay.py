"""Frozen 69 original D0 WATCHs -> unmodified ADR005 research SQLite queue.

Only accepts the exact previously verified full 4599-source original D0 report,
plus independently SHA-pinned original 53 WATCH and exposed exploration rows.
Seventy-day-style future labels, live listing PIT, real execution and prices at
the original decision are NOT proven. No network/cron/mail/Mac/trading.
"""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import monster_v4_shadow as original
import monster_v4_spot511_closed_minute_feed as d0
from monster_v4_spot511_d0_d1_tape import VerifiedClosedMinuteTape
from monster_v4_spot511_verified_watch_tape import (
    load_pinned_original_watch_tape, PINNED_PAIRED_REPORT_SHA256,
)
from monster_v4_d1_rbtc15_episode_research import (
    admit_original_watch, create_ledger, poll_episodes, summary,
)
from monster_v4_adr005_real53_original_sqlite_replay import (
    compare_exposed_exploration, load_pinned_exploration,
)

SCHEMA = "MONSTER_ADR005_EXPOSED_REAL69_ORIGINAL_SQLITE_REPLAY_V1"
PINNED_4599_REPLAY_SHA256 = "bf8d1a1fd9916257fe39b0da1ae008fbe77e7ef35e09e1d61b24fe05641adbc1"
PINNED_69_WATCH_SHA256 = "59d005be902d19b57fd21cc67855d2e8e24b96834de42195033f609975e40f63"
TICK = 180_000
FIVE = 300_000
DAY_SOURCE_COUNT = 69


def load_pinned_69(path, old_53_tape):
    """Full original-report SHA, 511 denominator, exact 69 canonical events."""
    p = Path(path)
    if not p.is_file() or p.is_symlink():
        raise ValueError("ORIGINAL_4599_REPORT_REGULAR_FILE_REQUIRED")
    raw = p.read_bytes()
    if hashlib.sha256(raw).hexdigest() != PINNED_4599_REPLAY_SHA256:
        raise ValueError("ORIGINAL_4599_FULL_REPORT_SHA_MISMATCH")
    try:
        r = json.loads(raw)
    except (ValueError, UnicodeError) as exc:
        raise ValueError("ORIGINAL_4599_JSON_INVALID") from exc
    needed = {
        "schema": "MONSTER_SPOT511_GLOBAL_SQLITE_FIFO_FAIR8_RESEARCH_V1",
        "mode": "OFFLINE_HISTORICAL_RESEARCH",
        "frozen_roster": 511,
        "ticks": 3360,
        "verified_full_publisher_symbol_days": 4599,
        "full_d0_ticks": 3360,
        "censored_d0_ticks": 0,
        "d0_watch_count": 69,
        "same_d0_watch_id_and_time": True,
        "G6": "NO_GO",
    }
    if any(r.get(k) != v for k, v in needed.items()):
        raise ValueError("ORIGINAL_4599_COHORT_OR_GATE_DRIFT")
    events = r.get("fifo_watch_events")
    if (not isinstance(events, list) or len(events) != 69
            or events != r.get("fair8_watch_events")):
        raise ValueError("ORIGINAL_69_LANE_WATCH_IDENTITY_DRIFT")
    items = []
    seen = set()
    previous = None
    for e in events:
        symbol, ms, eid = (e.get("symbol"), e.get("observed_ms"), e.get("event_id"))
        if (e.get("venue") != "spot" or e.get("event_type") != "WATCH_EARLY"
                or not isinstance(symbol, str) or not symbol.endswith("USDT")
                or symbol == "BTCUSDT" or type(ms) is not int or ms % TICK
                or not d0.START_MS <= ms < d0.END_MS
                or not isinstance(eid, str)
                or original.event_key("spot", symbol, "WATCH_EARLY", ms) != eid
                or eid in seen):
            raise ValueError("ORIGINAL_69_WATCH_FIELDS_OR_EVENT_ID_INVALID")
        key = (ms, eid)
        if previous is not None and key < previous:
            raise ValueError("ORIGINAL_69_WATCH_SORT_ORDER_DRIFT")
        previous = key
        seen.add(eid)
        items.append((symbol, ms, eid))
    packed = "".join(f"{sym}\t{ms}\t{eid}\n" for sym, ms, eid in items)
    if hashlib.sha256(packed.encode("utf-8")).hexdigest() != PINNED_69_WATCH_SHA256:
        raise ValueError("ORIGINAL_69_CANONICAL_FINGERPRINT_DRIFT")
    old_rows = old_53_tape["watch_identity_rows"]
    if len(old_rows) != 53 or not set(old_rows).issubset(set(items)):
        raise ValueError("ORIGINAL_PINNED_53_DISAPPEARED_IN_4599")
    return tuple(items)


def required_days_69(rows):
    """Every six-closed-5m input on all original WATCH 3m ticks through deadline."""
    if not isinstance(rows, tuple) or len(rows) != 69:
        raise ValueError("FROZEN_69_WATCH_ROWS_REQUIRED")
    needed = set()
    for symbol, watch_ms, _ in rows:
        if type(watch_ms) is not int or watch_ms % TICK:
            raise ValueError("FROZEN_69_WATCH_CLOCK_INVALID")
        for tick in range(watch_ms, watch_ms + original.QUEUE_DEADLINE_MS + 1, TICK):
            end = tick // FIVE * FIVE
            for sym in (symbol, "BTCUSDT"):
                for ms in (end - 6 * FIVE, end - 1):
                    day = datetime.fromtimestamp(ms / 1000, timezone.utc).date()
                    needed.add((sym, day.isoformat()))
    if len(needed) != DAY_SOURCE_COUNT:
        raise ValueError("FROZEN_69_SOURCE_DAY_CENSUS_DRIFT")
    return tuple(sorted(needed))


def replay(*, original_4599, original_4088, old_reference, publisher_dir,
           ledger_path, asof_utc):
    if (not isinstance(asof_utc, datetime) or asof_utc.tzinfo is None
            or asof_utc.utcoffset() is None
            or asof_utc.astimezone(timezone.utc) <
                    datetime(2026, 10, 25, 7, 20, tzinfo=timezone.utc)):
        raise ValueError("SOURCE_MUST_HAVE_BEEN_OBTAINED_AT_REAL_UTC_TIME")
    old_tape = load_pinned_original_watch_tape(original_4088)
    rows = load_pinned_69(original_4599, old_tape)
    old_ref = load_pinned_exploration(old_reference)
    need = required_days_69(rows)
    symbols = sorted({sym for sym, _ in need})
    tapes = {sym: VerifiedClosedMinuteTape(publisher_dir, sym, asof_utc=asof_utc)
             for sym in symbols}
    absent = [(sym, day) for sym, day in need
              if tapes[sym].day_states.get(day) != "VERIFIED_FULL_DAY_1440"]
    if absent:
        raise ValueError("REAL69_REQUIRED_VERIFIED_SOURCE_MISSING:" +
                         json.dumps(absent, separators=(",", ":")))
    if Path(ledger_path).exists() or Path(ledger_path).is_symlink():
        raise ValueError("NEW_RESEARCH_LEDGER_REFUSE_OVERWRITE")
    index = {}
    for symbol, ms, eid in rows:
        index.setdefault(ms, []).append({
            "symbol": symbol, "observed_ms": ms, "event_id": eid,
            "venue": "spot", "event_type": "WATCH_EARLY",
        })
    db = create_ledger(ledger_path)
    count = 0
    try:
        def feed(symbol, tick_ms):
            return tapes[symbol].six_closed_5m(tick_ms)
        for tick in range(d0.START_MS, d0.END_MS, TICK):
            for e in index.get(tick, ()):
                if not admit_original_watch(db, e):
                    raise RuntimeError("REAL69_DUPLICATE_ADMISSION")
                count += 1
            poll_episodes(db, tick, feed)
        outcome = summary(db)
    finally:
        db.close()
    if count != 69 or outcome["episodes"] != 69 or outcome["status_counts"].get("PENDING", 0):
        raise RuntimeError("REAL69_SQLITE_TERMINAL_COUNT_DRIFT")
    old_ids = {eid for _, _, eid in old_tape["watch_identity_rows"]}
    old_view = {"rows":[x for x in outcome["rows"] if x["watch_event_id"] in old_ids]}
    comparison = compare_exposed_exploration(old_view, old_ref)
    if comparison["status"] != "MATCH":
        raise RuntimeError("ORIGINAL_53_RESEARCH_RESULT_DRIFT_FROM_LOCKED_REFERENCE")
    days = Counter()
    for x in outcome["rows"]:
        if x["status"] == "RESEARCH_SETUP":
            day=datetime.fromtimestamp(x["research_observed_ms"] / 1000,timezone.utc).date().isoformat()
            days[day] += 1
    old_counts = Counter(x["status"] for x in outcome["rows"] if x["watch_event_id"] in old_ids)
    additions = [x for x in outcome["rows"] if x["watch_event_id"] not in old_ids]
    if len(additions) != 16:
        raise RuntimeError("REAL69_INCREMENTAL_16_WATCH_CENSUS_DRIFT")
    return {
        "schema": SCHEMA,
        "pinned_original_4599_sha256": PINNED_4599_REPLAY_SHA256,
        "pinned_original_4088_sha256": PINNED_PAIRED_REPORT_SHA256,
        "frozen_original_watch_events": 69,
        "previous_original_watch_events_unchanged": 53,
        "official_symbol_utc_days_readmitted": len(need),
        "official_source_sha_by_symbol_day": [
            {"symbol":sym,"day":day,"sha256":tapes[sym].publisher_zip_sha[day]}
            for sym,day in need],
        "status_counts": outcome["status_counts"],
        "rechecked_original53_status_counts": dict(sorted(old_counts.items())),
        "exposed_original53_reference_comparison": comparison,
        "new_original_watch16_research_status_counts": dict(sorted(Counter(
            x["status"] for x in additions).items())),
        "research_setup_by_utc_day": dict(sorted(days.items())),
        "research_setup_daily_peak_on_preexposed_source": max(days.values(), default=0),
        "research_setup_daily_mean_on_exact_seven_day_window": (
            outcome["status_counts"].get("RESEARCH_SETUP", 0) / 7),
        "sqlite_episode_rows": outcome["rows"],
        "original_16_new_episode_rows": additions,
        "source_grade":"POSTHOC_OFFICIAL_MINUTE_NOT_HISTORICALLY_LIVE_AVAILABLE_AT",
        "historical_dynamic_listing_PIT":"UNKNOWN",
        "G0":"PARTIAL","G1":"NOT_SCORABLE","G2":"UNKNOWN",
        "G3":"RESEARCH_CANDIDATE_EXPOSED_ONLY_NOT_FORMAL_GATE",
        "G4":"UNKNOWN","G5":"NEW_FULL69_INTEGRATION_REVIEW_NOT_DONE",
        "G6":"NO_GO",
        "NO_MERGE":True,"NO_DEPLOY":True,"NO_MAC":True,
        "NO_SCHEDULE":True,"NO_GMAIL":True,"NO_TRADES":True,
    }


def main():
    import argparse
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--original-4599",type=Path,required=True)
    p.add_argument("--original-4088",type=Path,required=True)
    p.add_argument("--original53-exploration",type=Path,required=True)
    p.add_argument("--publisher-dir",type=Path,required=True)
    p.add_argument("--ledger-out",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--asof-utc",required=True)
    a=p.parse_args()
    if a.out.exists() or a.out.is_symlink():
        p.error("FULL69_REPORT_REFUSE_EXISTING_OUTPUT")
    asof=datetime.fromisoformat(a.asof_utc.replace("Z","+00:00"))
    report=replay(original_4599=a.original_4599,
                  original_4088=a.original_4088,
                  old_reference=a.original53_exploration,
                  publisher_dir=a.publisher_dir,ledger_path=a.ledger_out,asof_utc=asof)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    with a.out.open("x",encoding="utf-8") as f:
        json.dump(report,f,ensure_ascii=False,indent=2,sort_keys=True)
        f.write("\n")
    print(json.dumps({
        "status_counts":report["status_counts"],
        "incremental_16_statuses":report["new_original_watch16_research_status_counts"],
        "daily_setup":report["research_setup_by_utc_day"],
        "previous53":"MATCH","G6":"NO_GO"},sort_keys=True))


if __name__ == "__main__":
    main()
