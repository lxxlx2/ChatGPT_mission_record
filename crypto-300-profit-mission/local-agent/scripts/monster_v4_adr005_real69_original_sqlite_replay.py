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
from urllib.parse import urlsplit

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

# Frozen pre-event official asset identity manifests are positive TYPE evidence
# only. They cannot certify historical listing/permissions at the WATCH tick.
OFFICIAL_PRE_EVENT_MANIFEST_BLOBS = {
    "crypto": ("MONSTER_SPOT511_PRE_EVENT_OFFICIAL_POSITIVE_CRYPTO_26_ASSETS_20261024.json",
               "10661b150ecb5ad5e8a3b24ad023eea2b07269af"),
    "additional": ("MONSTER_SPOT511_PRE_EVENT_REMAINING_7_TYPES_20261024.json",
                   "9b89569829d596c783903b101e15e3b6a7292421"),
    "securities": ("MONSTER_SPOT511_OFFICIAL_POSITIVE_BSTOCKS_20261024.json",
                   "4b336b92dcba2464e4f17c88d550ac47d0a05378"),
}


def _read_pinned_manifest(folder, filename, expected_blob):
    file=Path(folder)/filename
    if not file.is_file() or file.is_symlink():
        raise ValueError("OFFICIAL_POSITIVE_IDENTITY_MANIFEST_REQUIRED")
    raw=file.read_bytes()
    header=b"blob "+str(len(raw)).encode("ascii")+b"\0"
    if hashlib.sha1(header+raw).hexdigest()!=expected_blob:
        raise ValueError("OFFICIAL_POSITIVE_IDENTITY_MANIFEST_GIT_BLOB_DRIFT")
    return json.loads(raw)


def exposed_g3_positive_identity_partition(rows, manifest_dir):
    """No default-crypto class. Preserve every setup; partition purely for G3.

    Official crypto *identity* evidence is independent of account eligibility,
    actual historical listing status, trade notional, or realized returns.
    """
    manifests={key:_read_pinned_manifest(manifest_dir,*item)
               for key,item in OFFICIAL_PRE_EVENT_MANIFEST_BLOBS.items()}
    crypto=manifests["crypto"]
    additional=manifests["additional"]
    securities=manifests["securities"]
    if (crypto.get("schema") != "MONSTER_SPOT511_PRE_EVENT_OFFICIAL_POSITIVE_CRYPTO_ASSET_ID_V1"
            or crypto.get("freeze_replay_sha") != PINNED_PAIRED_REPORT_SHA256
            or crypto.get("positive_crypto_type_symbols") != 26
            or additional.get("schema") != "MONSTER_SPOT511_SEVEN_PRE_EVENT_REMAINING_ASSET_IDENTITIES_V1"
            or additional.get("fixed_original_replay_sha256") != PINNED_PAIRED_REPORT_SHA256
            or securities.get("schema") != "MONSTER_SPOT_HISTORIC_POSITIVE_BSTOCKS_V1"):
        raise ValueError("OFFICIAL_PRE_EVENT_MANIFEST_SCHEMA_OR_CENSUS_DRIFT")
    positives=set()
    for item in crypto["rows"]:
        symbol=item["symbol"]
        published=item["published_utc_date"]
        url=urlsplit(item["source_url"])
        if (item.get("classification")!="CRYPTO_ASSET_IDENTITY_POSITIVE_ONLY"
                or symbol in positives or not published < "2026-10-17"
                or url.scheme!="https" or url.hostname!="www.binance.com"):
            raise ValueError("CRYPTO_OFFICIAL_PRE_EVENT_POSITIVE_ROW_INVALID")
        positives.add(symbol)
    fan=set()
    for item in additional["official_positive_identity_rows"]:
        symbol=item["symbol"]
        url=urlsplit(item["official_url"])
        if (symbol in positives or symbol in fan
                or item["source_published_utc"] >= "2026-10-17T22:06:00Z"
                or url.scheme!="https" or url.hostname!="www.binance.com"):
            raise ValueError("ADDITIONAL_OFFICIAL_PRE_EVENT_ROW_INVALID")
        if item["category"]=="CRYPTO_NETWORK_PROTOCOL_UTILITY":
            positives.add(symbol)
        elif item["category"]=="FAN_TOKEN_SCOPE_REQUIRES_DECISION":
            fan.add(symbol)
        else:
            raise ValueError("ADDITIONAL_OFFICIAL_IDENTITY_CATEGORY_INVALID")
    bstock=set()
    for announcement in securities["announcements"]:
        for symbol in announcement["positive_bstock_symbols"]:
            if symbol in bstock or symbol in positives or symbol in fan:
                raise ValueError("OFFICIAL_POSITIVE_IDENTITY_COLLISION")
            bstock.add(symbol)
    counts=Counter()
    unresolved=[]
    by_day={}
    for row in rows:
        if row["status"]!="RESEARCH_SETUP":
            continue
        sym=row["symbol"]
        if sym in positives: classification="CRYPTO_TYPE_POSITIVE"
        elif sym in fan: classification="CHILIZ_FAN_TOKEN_SEPARATE"
        elif sym in bstock: classification="TOKENIZED_EQUITY_EXCLUDED"
        else:
            classification="UNRESOLVED_NOT_DEFAULT_CRYPTO"
            unresolved.append(sym)
        counts[classification]+=1
        day=datetime.fromtimestamp(row["research_observed_ms"]/1000,timezone.utc).date().isoformat()
        by_day.setdefault(day,Counter())[classification]+=1
    if sum(counts.values())!=sum(r["status"]=="RESEARCH_SETUP" for r in rows):
        raise ValueError("G3_POSITIVE_IDENTITY_PARTITION_CENSUS_DRIFT")
    positive=counts["CRYPTO_TYPE_POSITIVE"]
    return {
        "classification":"PINNED_PRE_EVENT_POSITIVE_ASSET_TYPE_ONLY",
        "seven_day_crypto_type_positive_setup_count":positive,
        "seven_day_raw_setup_count":sum(counts.values()),
        "counts":dict(sorted(counts.items())),
        "unresolved_symbols":sorted(set(unresolved)),
        "daily_by_utc":{day:dict(sorted(group.items())) for day,group in sorted(by_day.items())},
        "crypto_type_only_numeric_attention_max_35":35,
        "crypto_type_only_research_G3":(
            "EXPOSED_NOT_PASSED" if positive>35 or
            any(group["CRYPTO_TYPE_POSITIVE"]>12 for group in by_day.values())
            else "EXPOSED_NUMERIC_WITHIN_LIMIT_NOT_FORMAL_PASS"),
        "historical_dynamic_listing_and_account_permission_PIT":"UNKNOWN",
        "does_not_certify_actually_trade_eligible_events":True,
    }



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
           ledger_path, asof_utc, manifest_dir=None):
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
    comparison = compare_exposed_exploration(
        old_view, old_ref, allow_semantic_deadline_repair=True)
    if comparison["status"] == "DIFFERENCE_FAIL_CLOSED":
        raise RuntimeError("ORIGINAL_53_NON_SEMANTIC_RESULT_DRIFT_FROM_LOCKED_REFERENCE")
    days = Counter()
    for x in outcome["rows"]:
        if x["status"] == "RESEARCH_SETUP":
            day=datetime.fromtimestamp(x["research_observed_ms"] / 1000,timezone.utc).date().isoformat()
            days[day] += 1
    old_counts = Counter(x["status"] for x in outcome["rows"] if x["watch_event_id"] in old_ids)
    additions = [x for x in outcome["rows"] if x["watch_event_id"] not in old_ids]
    if len(additions) != 16:
        raise RuntimeError("REAL69_INCREMENTAL_16_WATCH_CENSUS_DRIFT")
    manifest_dir = (Path(__file__).resolve().parents[2]/"monster"/"evidence"
                    if manifest_dir is None else Path(manifest_dir))
    g3_identity = exposed_g3_positive_identity_partition(outcome["rows"], manifest_dir)
    return {
        "schema": SCHEMA,
        "pinned_original_4599_sha256": PINNED_4599_REPLAY_SHA256,
        "pinned_original_4088_sha256": PINNED_PAIRED_REPORT_SHA256,
        "frozen_original_watch_events": 69,
        "previous_original_watch_events_unchanged": len(old_view["rows"]),
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
        "research_setup_daily_peak_on_exposed_october_window": max(days.values(), default=0),
        "research_setup_daily_mean_on_exact_seven_day_window": (
            outcome["status_counts"].get("RESEARCH_SETUP", 0) / 7),
        "research_G3_raw_setup_mean_ceiling": 5,
        "research_G3_raw_setup_peak_ceiling": 12,
        "research_G3_raw_setup_attention": (
            "EXPOSED_NOT_PASSED" if
            outcome["status_counts"].get("RESEARCH_SETUP", 0) > 35 or
            max(days.values(), default=0) > 12 else "EXPOSED_NUMERIC_ONLY"),
        "research_G3_identity_partition_status": "PINNED_PRE_EVENT_POSITIVE_TYPE_OVERLAY",
        "research_G3_positive_asset_identity": g3_identity,
        "sqlite_episode_rows": outcome["rows"],
        "original_16_new_episode_rows": additions,
        "source_grade":"POSTHOC_OFFICIAL_MINUTE_NOT_HISTORICALLY_LIVE_AVAILABLE_AT",
        "historical_dynamic_listing_PIT":"UNKNOWN",
        "G0":"PARTIAL","G1":"NOT_SCORABLE","G2":"UNKNOWN",
        "G3":"EXPOSED_NOT_PASSED_NUMERIC_FORMAL_ELIGIBILITY_PIT_UNKNOWN",
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
        "previous53":report["exposed_original53_reference_comparison"]["status"],"G6":"NO_GO"},sort_keys=True))


if __name__ == "__main__":
    main()
