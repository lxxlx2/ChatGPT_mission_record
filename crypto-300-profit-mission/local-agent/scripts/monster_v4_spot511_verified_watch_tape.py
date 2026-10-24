"""Read-only original-core WATCH tape admission from pinned 4088 replay bytes.

Source grade: original SQLite event export, preserved in immutable GitHub
Actions artifact #12557911034. Its original publisher 1m input was
historically archived, not a proven live quote receipt at the event time.

This does NOT perform source downloading, backfill, new research-D1 queue
polling or trading, and does not accept a caller-chosen trust digest.
"""
import hashlib
import json
from pathlib import Path

import monster_v4_shadow as original

SCHEMA = "MONSTER_SPOT511_4088_ORIGINAL_CORE_WATCH_ADMISSION_V1"
PINNED_PAIRED_REPORT_SHA256 = (
    "453ee2e740578121b0734d61e6eb357be7bb34859b90878eb314f7d3dc1690f5"
)
PINNED_WATCH_CANONICAL_SHA256 = (
    "afeba23efc9e8b561ee7fa41d9e2267551d2a6b17c8f324df1e37e7f81042f9f"
)
TICK_MS = 180_000
EXPECTED_WATCH_COUNT = 53
EXPECTED_VERIFIED_SOURCES = 4088
EXPECTED_FULL_TICKS = 2919
EXPECTED_CENSORED_TICKS = 441


class SourceIdentityError(ValueError):
    """Snapshot or event identity is not proven: do not ingest."""


def verify_original_watch_inventory(replay):
    """Check fixed original full-replay ledger, not self-authenticating hashes.

    Call through load_pinned_original_watch_tape() to gain file-integrity
    assurance; this pure validator alone does NOT establish provenance.
    """
    if not isinstance(replay, dict):
        raise SourceIdentityError("REPLAY_MUST_BE_OBJECT")
    required = {
        "mode": "OFFLINE_HISTORICAL_RESEARCH",
        "frozen_roster": 511,
        "ticks": 3360,
        "verified_full_publisher_symbol_days": EXPECTED_VERIFIED_SOURCES,
        "full_d0_ticks": EXPECTED_FULL_TICKS,
        "censored_d0_ticks": EXPECTED_CENSORED_TICKS,
        "d0_watch_count": EXPECTED_WATCH_COUNT,
        "same_d0_watch_id_and_time": True,
        "G6": "NO_GO",
    }
    if any(replay.get(k) != value for k, value in required.items()):
        raise SourceIdentityError("ORIGINAL_REPLAY_CENSUS_OR_GATE_MISMATCH")
    fifo = replay.get("fifo_watch_events")
    fair = replay.get("fair8_watch_events")
    if (not isinstance(fifo, list) or len(fifo) != EXPECTED_WATCH_COUNT
            or fifo != fair):
        raise SourceIdentityError("ORIGINAL_WATCH_LANE_DISAGREEMENT")
    inventory = []
    previous = None
    distinct = set()
    for event in fifo:
        if not isinstance(event, dict):
            raise SourceIdentityError("INVALID_ORIGINAL_EVENT")
        sym, eid, ms = (event.get("symbol"), event.get("event_id"),
                        event.get("observed_ms"))
        details = event.get("details")
        if (event.get("venue") != "spot" or event.get("event_type") != "WATCH_EARLY"
                or not isinstance(sym, str) or not sym.endswith("USDT")
                or sym == "BTCUSDT" or type(ms) is not int or ms % TICK_MS
                or not isinstance(eid, str) or len(eid) != 64
                or not isinstance(details, dict)
                or details.get("classification") != "RESEARCH_WATCH_NOT_BUY"
                or details.get("venue") != "spot"
                or details.get("observed_ms") != ms):
            raise SourceIdentityError("INVALID_ORIGINAL_WATCH_FIELDS")
        if original.event_key("spot", sym, "WATCH_EARLY", ms) != eid:
            raise SourceIdentityError("ORIGINAL_EVENT_HASH_MISMATCH")
        if eid in distinct:
            raise SourceIdentityError("DUPLICATE_ORIGINAL_EVENT_ID")
        distinct.add(eid)
        key = (ms, eid)
        if previous is not None and key < previous:
            raise SourceIdentityError("ORIGINAL_WATCH_SORT_ORDER_DRIFT")
        previous = key
        inventory.append((sym, ms, eid))
    digest = hashlib.sha256(
        ("".join(f"{sym}\t{ms}\t{eid}\n" for sym, ms, eid in inventory))
        .encode("utf-8")
    ).hexdigest()
    if digest != PINNED_WATCH_CANONICAL_SHA256:
        raise SourceIdentityError("ORIGINAL_WATCH_FINGERPRINT_DRIFT")
    # A new mutable list would let a downstream consumer modify an event, so
    # expose immutable, minimal identity tuples only; the original input stays.
    return tuple(inventory)


def load_pinned_original_watch_tape(path):
    """Validate the artifact-extracted paired-4088.json at its exact byte SHA.

    Input must be the unmodified paired-4088.json from GitHub Actions run
    #40087231856, artifact #12557911034; NOT its Git summary or a watch
    dictionary reconstructed from an event_key formula.
    """
    source = Path(path)
    if not source.is_file() or source.is_symlink():
        raise SourceIdentityError("ORIGINAL_PAIRED_JSON_NOT_A_REGULAR_FILE")
    raw = source.read_bytes()
    if hashlib.sha256(raw).hexdigest() != PINNED_PAIRED_REPORT_SHA256:
        raise SourceIdentityError("ORIGINAL_PAIRED_JSON_SHA_MISMATCH")
    try:
        replay = json.loads(raw)
    except (ValueError, UnicodeError) as exc:
        raise SourceIdentityError("ORIGINAL_PAIRED_JSON_INVALID") from exc
    events = verify_original_watch_inventory(replay)
    return {
        "schema": SCHEMA,
        "original_paired_json_sha256": PINNED_PAIRED_REPORT_SHA256,
        "original_artifact_id": 12557911034,
        "source_verified_publisher_symbol_days": EXPECTED_VERIFIED_SOURCES,
        "source_censored_d0_ticks": EXPECTED_CENSORED_TICKS,
        "watch_count": len(events),
        "distinct_symbols": len(set(sym for sym, _, _ in events)),
        "watch_identity_rows": events,
        "original_watch_ledger_integrity_checked": True,
        "original_live_quote_PIT_proven": False,
        "complete_seven_day_source_proven": False,
        "G6": "NO_GO",
    }



def _verify_pinned_extraction_rows(rows):
    """Fail closed on the ENTIRE 53-event tuple, not public trust flags.

    The loader has already validated the complete original paired-4088.json
    SHA. A caller may mutate or fabricate the returned dict afterwards.
    The exact canonical SHA must be checked again at every extraction; each
    tuple element is checked BEFORE interpolation, hashing, or filtering.
    """
    if not isinstance(rows, tuple) or len(rows) != EXPECTED_WATCH_COUNT:
        raise SourceIdentityError("WATCH_TAPE_EVENT_COUNT_DRIFT")
    seen = set()
    prior = None
    encoded = []
    for record in rows:
        if not isinstance(record, tuple) or len(record) != 3:
            raise SourceIdentityError("WATCH_TAPE_ROW_SHAPE_DRIFT")
        symbol, observed_ms, eid = record
        if (not isinstance(symbol, str) or not symbol.endswith("USDT")
                or symbol == "BTCUSDT"
                or type(observed_ms) is not int or observed_ms < 0
                or observed_ms % TICK_MS
                or not isinstance(eid, str) or len(eid) != 64):
            raise SourceIdentityError("WATCH_TAPE_ROW_INVALID")
        if original.event_key("spot", symbol, "WATCH_EARLY", observed_ms) != eid:
            raise SourceIdentityError("WATCH_TAPE_EVENT_HASH_MISMATCH")
        if eid in seen:
            raise SourceIdentityError("WATCH_TAPE_DUPLICATE_EVENT_ID")
        seen.add(eid)
        key = (observed_ms, eid)
        if prior is not None and key < prior:
            raise SourceIdentityError("WATCH_TAPE_EVENT_ORDER_DRIFT")
        prior = key
        encoded.append(f"{symbol}\t{observed_ms}\t{eid}\n")
    digest = hashlib.sha256("".join(encoded).encode("utf-8")).hexdigest()
    if digest != PINNED_WATCH_CANONICAL_SHA256:
        raise SourceIdentityError("WATCH_TAPE_CANONICAL_SHA_MISMATCH")
    return rows


def watches_at_tick(verified_tape, tick_ms):
    """Select all real D0 WATCHs at a tick without inferring source zeros.

    Must be called only after load_pinned_original_watch_tape. This is a
    read-only lookup, not an unconditional bulk enqueue to candidate_queue.
    """
    if (not isinstance(verified_tape, dict) or
            verified_tape.get("schema") != SCHEMA or
            verified_tape.get("original_paired_json_sha256") != PINNED_PAIRED_REPORT_SHA256 or
            verified_tape.get("original_watch_ledger_integrity_checked") is not True or
            type(tick_ms) is not int or tick_ms % TICK_MS):
        raise SourceIdentityError("WATCH_TICK_OR_PROVENANCE_REQUIRED")
    rows = _verify_pinned_extraction_rows(
        verified_tape.get("watch_identity_rows")
    )
    return tuple({
        "event_id": eid, "venue": "spot", "symbol": symbol,
        "event_type": "WATCH_EARLY", "observed_ms": observed_ms
    } for symbol, observed_ms, eid in rows if observed_ms == tick_ms)
