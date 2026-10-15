#!/usr/bin/env python3
"""Monster Stage153: read-only real Stage28 queue incident and local pressure audit.

Original Stage28 shared D1 SQLite outcome ONLY. D0 stream was separately
derived Stage26 Spot WATCH, not all-market shared D0 and not actual deliveries.
No live API, deployment, schedule, order, Gmail, or database modifications.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import zipfile

ROOT = Path(__file__).resolve().parents[2] / "monster"
PROOF = ROOT / "evidence/monster_stage28_original_six_real_shared_sqlite_artifact_proof_20261011.json"
SCHEMA = "MONSTER_STAGE153_STAGE28_SIX_ORIGINAL_SHARED_D1_QUEUE_LIFECYCLE_V1"
MIN = 60_000
CAPACITY_PER_POLL = 8
POLL_MIN = 3
TTL_MIN = 15
BURST = int(datetime(2026, 2, 6, 0, 36, tzinfo=timezone.utc).timestamp()*1000)
EXPECTED_DATES = ("2025-11-04", "2025-12-04", "2026-02-04",
                  "2026-04-04", "2026-08-04", "2026-09-04")


def source_proof(proof=PROOF):
    x = json.loads(Path(proof).read_text())
    if (x.get("schema") !=
            "MONSTER_STAGE28_SIX_ORIGINAL_REAL_SHARED_SQLITE_D1_ARTIFACTS_SHA256_V1"
            or x.get("source_commit") !=
            "973891aae686b05e6bba35bdf506ddca578b1bda"
            or x.get("original_watch_events") != 1132
            or x.get("real_production_shared_d1_setups") != 828
            or x.get("production_shared_d1_LATE_REVIEW_total") != 123
            or len(x.get("artifacts", [])) != 6
            or {r["date"] for r in x["artifacts"]} != set(EXPECTED_DATES)):
        raise ValueError("STAGE153_ORIGINAL_STAGE28_PROOF_DRIFT")
    return x


def read_actual_artifact(zip_path, rec):
    """Validate both the original GitHub artifact ZIP SHA and extracted JSON."""
    archive = Path(zip_path).read_bytes()
    if hashlib.sha256(archive).hexdigest() != rec["zip_sha256"]:
        raise ValueError("STAGE153_GITHUB_ARTIFACT_ZIP_SHA_CHANGED")
    name = "monster_stage28_" + rec["date"] + "_real_shared_sqlite.json"
    with zipfile.ZipFile(zip_path) as z:
        if z.namelist() != [name] or z.getinfo(name).file_size > 15_000_000:
            raise ValueError("STAGE153_ARTIFACT_MEMBER_IDENTITY_CHANGED")
        raw = z.read(name)
    if hashlib.sha256(raw).hexdigest() != rec["raw_json_sha256"]:
        raise ValueError("STAGE153_UNCOMPRESSED_STAGE28_JSON_SHA_CHANGED")
    data = json.loads(raw)
    if (data.get("schema") !=
            "MONSTER_STAGE28_ACTUAL_PRODUCTION_SHARED_SQLITE_D1_WITH_FROZEN_WATCH_V1"
            or data.get("date") != rec["date"]
            or data.get("actual_shared_sqlite_process_queue") is not True
            or data.get("global_observe_snapshot_replayed") is not False
            or data.get("D0_invalidation_event_injection") is not False
            or data.get("actual_real_money_order_or_email") is not False):
        raise ValueError("STAGE153_FALSE_OR_CHANGED_GLOBAL_D0_CLAIM")
    return data


def audit_day(data, rec):
    """Reconcile each original candidate, WATCH, SETUP and LATE—not profit."""
    day = rec["date"]
    queue = data["queue_final"]
    if (data["watch_arrivals"] != rec["original_watch_arrivals"]
            or data["original_stage26_individual_D1_setups"] !=
            rec["original_individual_setups"]
            or len(data["setups"]) != rec["real_shared_setups"]
            or len(data["late_events"]) != rec["late"]
            or len(data["source_5m_official_SHA256"]) !=
            rec["official_5m_publisher_sha_source_count"]
            or len(queue) != data["queue_candidates"]
            or data["pending_at_end"] != 0):
        raise ValueError("STAGE153_STAGE28_ORIGINAL_TOTAL_DRIFT")
    status = Counter(row["status"] for row in queue)
    if status != Counter(data["candidate_status_counts"]):
        raise ValueError("STAGE153_QUEUE_STATUS_COUNT_DRIFT")
    if (sum(status.values()) != len(queue)
            or any(state not in ("EVALUATED", "LATE", "INVALIDATED")
                   for state in status)
            or data["event_counts"].get("WATCH_EARLY") !=
            data["watch_arrivals"]
            or data["event_counts"].get("SETUP_ACTIVE") != len(data["setups"])
            or data["event_counts"].get("LATE_REVIEW") != len(data["late_events"])):
        raise ValueError("STAGE153_SHARED_SQLITE_EVENT_COUNT_DRIFT")
    seen_ids = set()
    episode_keys = set()
    by_episode = {}
    by_symbol = {}
    details = []
    for row in queue:
        candidate_id = row["id"]
        episode_key = (row["symbol"], row["first_seen_ms"], row["deadline_ms"])
        if (type(candidate_id) is not int or candidate_id in seen_ids
                or episode_key in episode_keys or row["venue"] != "spot"
                or type(row["first_seen_ms"]) is not int
                or type(row["deadline_ms"]) is not int
                or row["deadline_ms"] - row["first_seen_ms"] != TTL_MIN*MIN
                or type(row["attempts"]) is not int or row["attempts"] < 0):
            raise ValueError("STAGE153_ILLEGAL_OR_DUPLICATED_ORIGINAL_QUEUE_EVENT")
        seen_ids.add(candidate_id)
        episode_keys.add(episode_key)
        by_episode[episode_key] = row
        by_symbol.setdefault(row["symbol"], []).append(row)
        completed_bar = row["last_evaluated_bar_ms"] is not None
        if (row["status"] == "LATE" and completed_bar):
            raise ValueError("STAGE153_LATE_WITH_RECORDED_COMPLETED_D1_BAR")
        if row["status"] == "EVALUATED" and not completed_bar:
            raise ValueError("STAGE153_EVALUATED_WITHOUT_COMPLETED_D1_BAR")
        details.append({
            "date": day, "candidate_id": row["id"],
            "venue": row["venue"], "symbol": row["symbol"],
            "first_seen_ms": row["first_seen_ms"],
            "deadline_ms": row["deadline_ms"], "status": row["status"],
            "last_evaluated_bar_ms": row["last_evaluated_bar_ms"],
            "successful_completed_5m_evaluation_observed": completed_bar,
            "http_or_retry_attempts_not_successful_evaluations": row["attempts"],
            "last_error": row["last_error"],
            "first_evaluation_clock_time": "UNKNOWN_NOT_IN_STAGE28_FINAL_ROW",
            "actual_gmail_delivery": "NOT_OBSERVED",
            "actual_trade_execution": "NOT_OBSERVED",
        })
    # Stage28 retains complete LATE payload/clock but only SETUP symbol/UTC.
    # Match exactly what the original artifact actually preserves, no D0 claims.
    remaining_late = {
        (q["symbol"], q["first_seen_ms"], q["deadline_ms"])
        for q in queue if q["status"] == "LATE"
    }
    for v in data["late_events"]:
        payload = v.get("payload", {})
        if payload.get("classification") != "STALE_NOT_ACTIONABLE":
            raise ValueError("STAGE153_LATE_EVENT_UNEXPECTED_CLASSIFICATION")
        key = (v.get("symbol"), payload.get("first_seen_ms"),
               payload.get("deadline_ms"))
        q = by_episode.get(key)
        if (q is None or q["status"] != "LATE"
                or type(v.get("observed_ms")) is not int
                or v["observed_ms"] <= q["deadline_ms"]
                or key not in remaining_late):
            raise ValueError("STAGE153_LATE_UNMATCHED_QUEUE_CANDIDATE_OR_TIME")
        remaining_late.remove(key)
    if remaining_late or len(data["late_events"]) != status["LATE"]:
        raise ValueError("STAGE153_MISSING_LATE_RECORD")

    # A Stage28 SETUP row has only symbol and UTC; correlate uniquely with a
    # completed episode whose original 15-minute D1 window covers that UTC.
    consumed_setups = set()
    for event in data["setups"]:
        try:
            stamp = event["utc"]
            if not isinstance(stamp, str) or not stamp.endswith("Z"):
                raise ValueError("BAD_UTC")
            instant = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
            if instant.tzinfo != timezone.utc:
                raise ValueError("BAD_UTC_OFFSET")
            setup_ms = int(instant.timestamp() * 1000)
            candidates = [
                q for q in by_symbol.get(event["symbol"], ())
                if q["status"] == "EVALUATED"
                and q["first_seen_ms"] <= setup_ms <= q["deadline_ms"]
            ]
        except (KeyError, TypeError, ValueError, OverflowError) as exc:
            raise ValueError("STAGE153_SETUP_EVENT_INVALID_TIME_OR_SYMBOL") from exc
        if len(candidates) != 1 or candidates[0]["id"] in consumed_setups:
            examples = [(q["id"], q["status"], q["first_seen_ms"], q["deadline_ms"]) for q in by_symbol.get(event.get("symbol"), [])[:4]]
            raise ValueError("STAGE153_SETUP_UNMATCHED_OR_DUPLICATED_CANDIDATE " + repr((event, examples)))
        consumed_setups.add(candidates[0]["id"])
    burst = [v for v in details if v["first_seen_ms"] == BURST]
    summary = {
        "date": day,
        "original_watch_events": data["watch_arrivals"],
        "candidate_queue_rows": len(queue),
        "queue_status": dict(status),
        "D1_setups": len(data["setups"]),
        "D1_LATE_REVIEW": len(data["late_events"]),
        "total_processor_selections_NOT_distinct": data["production_processor_selected_total"],
        "processor_deferred_NOT_distinct": data["production_processor_deferred_total"],
        "peak_pending_before_poll": data["max_pending_before_poll"],
        "LATE_without_completed_D1_5m_bar": sum(
            v["status"] == "LATE" and
            not v["successful_completed_5m_evaluation_observed"] for v in details),
        "LATE_with_http_or_retry_attempts": sum(
            v["status"] == "LATE" and
            v["http_or_retry_attempts_not_successful_evaluations"] > 0
            for v in details),
        "burst_2026_02_06_0036": {
            "n": len(burst),
            "late": sum(v["status"] == "LATE" for v in burst),
            "evaluated": sum(v["status"] == "EVALUATED" for v in burst),
            "successful_5m_evaluation_never_observed": sum(
                not v["successful_completed_5m_evaluation_observed"] for v in burst),
        },
        "source_zip_sha256": rec["zip_sha256"],
        "source_json_sha256": rec["raw_json_sha256"],
    }
    return summary, details


def audit_six(original_archive_dir, proof=PROOF):
    manifest = source_proof(proof)
    summaries = []
    details = []
    for rec in sorted(manifest["artifacts"], key=lambda r: r["date"]):
        path = Path(original_archive_dir) / (
            "monster_stage28_" + rec["date"] + "_real_shared_sqlite.zip")
        data = read_actual_artifact(path, rec)
        report, items = audit_day(data, rec)
        summaries.append(report)
        details.extend(items)
    total = Counter()
    for r in summaries:
        total["WATCH"] += r["original_watch_events"]
        total["queue"] += r["candidate_queue_rows"]
        total["SETUP"] += r["D1_setups"]
        total["LATE"] += r["D1_LATE_REVIEW"]
        total["EVALUATED"] += r["queue_status"].get("EVALUATED", 0)
        total["selected"] += r["total_processor_selections_NOT_distinct"]
        total["deferred"] += r["processor_deferred_NOT_distinct"]
        total["no_successful_5m"] += r["LATE_without_completed_D1_5m_bar"]
    burst = next(x["burst_2026_02_06_0036"] for x in summaries
                 if x["date"] == "2026-02-04")
    if (len(details) != 1128
            or total["WATCH"] != 1132 or total["queue"] != 1128
            or total["SETUP"] != 828 or total["LATE"] != 123
            or total["EVALUATED"] != 1005
            or total["selected"] != 3542 or total["deferred"] != 2414
            or (burst["n"],burst["late"],burst["evaluated"]) != (98,91,7)):
        raise ValueError("STAGE153_PREVIOUS_STAGE28_HISTORICAL_EVIDENCE_DRIFT")
    return {
        "schema": SCHEMA,
        "source": "ORIGINAL_STAGE28_GITHUB_ARTIFACT_ZIP_AND_RAW_JSON_BOTH_SHA256_LOCKED",
        "trigger_commit_sha": os.environ.get("GITHUB_SHA", "LOCAL_UNVERIFIED"),
        "stage153_auditor_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "source_CI_run": 38146403662,
        "source_commit": manifest["source_commit"],
        "six_exposed_historical_dates_NOT_OOS": True,
        "replayed_shared_D0_full_universe": False,
        "D0_watch_input": "STAGE26_INDEPENDENT_PER_SYMBOL_ORIGINAL_WATCH_ARRIVAL",
        "real_PIT_L2_or_execution": "UNKNOWN",
        "G0": "PARTIAL", "G1": "NOT_SCORABLE",
        "G2_G3": "NOT_PASSED", "G4": "UNKNOWN", "G6": "NO_GO",
        "total": dict(total),
        "burst_98": burst,
        "capacity_bound_first_eval_at_burst": {
            "one_poll_capacity": CAPACITY_PER_POLL,
            "minutes_between_polls": POLL_MIN,
            "ttl_minutes": TTL_MIN,
            "max_single_evaluations_across_6_polls_optimistic": 6*CAPACITY_PER_POLL,
            "minimum_unserved_optimistic_once_only_model": 98-6*CAPACITY_PER_POLL,
            "production_late_actual": burst["late"],
            "NOT_independent_real_D0_or_proven_missed_trade": True,
        },
        "per_date": summaries,
        "rows": sorted(details, key=lambda r:
                       (r["date"],r["first_seen_ms"],r["candidate_id"])),
        "no_new_schedule_mail_trade_or_deploy": True,
    }


def queue_pressure(db, asof_ms):
    """Read-only, as-of status. Do not infer unseen true first HTTP start."""
    if type(asof_ms) is not int or asof_ms <= 0:
        raise ValueError("STAGE153_INVALID_ASOF_MS")
    names = ("first_seen_ms", "deadline_ms", "retry_after_ms",
             "last_evaluated_bar_ms", "attempts", "venue", "symbol")
    pending = [dict(zip(names, r)) for r in db.execute(
        """SELECT first_seen_ms,deadline_ms,retry_after_ms,
                  last_evaluated_bar_ms,attempts,venue,symbol
           FROM candidate_queue WHERE status='PENDING'""").fetchall()]
    # Current stored PENDING snapshot cannot reconstruct an earlier queue.
    # Reject future candidates/bars instead of leaking them into as-of counts.
    for row in pending:
        if (type(row["first_seen_ms"]) is not int
                or row["first_seen_ms"] > asof_ms
                or (row["last_evaluated_bar_ms"] is not None
                    and (type(row["last_evaluated_bar_ms"]) is not int
                         or row["last_evaluated_bar_ms"] + 5*MIN > asof_ms))):
            raise ValueError("STAGE153_ASOF_FUTURE_PENDING_OR_COMPLETED_BAR")
    not_evaluated = [r for r in pending if r["last_evaluated_bar_ms"] is None]
    near_3 = [r for r in pending if r["deadline_ms"] <= asof_ms+POLL_MIN*MIN]
    near_6 = [r for r in pending if r["deadline_ms"] <= asof_ms+2*POLL_MIN*MIN]
    first_15 = [r for r in not_evaluated
                if r["deadline_ms"] <= asof_ms+TTL_MIN*MIN]
    soonest = min((r["deadline_ms"] for r in pending), default=None)
    overdue = sum(r["deadline_ms"] < asof_ms for r in pending)
    return {
        "schema": "MONSTER_STAGE153_D1_QUEUE_PRESSURE_READ_ONLY_ASOF_V1",
        "asof_ms": asof_ms,
        "snapshot_scope": "CURRENT_STORED_PENDING_ONLY_NOT_HISTORICAL_RECONSTRUCTION",
        "PENDING": len(pending),
        "PENDING_never_recorded_completed_D1_5m": len(not_evaluated),
        "PENDING_with_completed_D1_5m": len(pending)-len(not_evaluated),
        "PENDING_eligible_retry_asof": sum(r["retry_after_ms"] <= asof_ms
                                           for r in pending),
        "PENDING_in_retry_backoff": sum(r["retry_after_ms"] > asof_ms
                                        for r in pending),
        "PENDING_already_over_deadline": overdue,
        "PENDING_due_in_3m_including_overdue": len(near_3),
        "PENDING_due_in_6m_including_overdue": len(near_6),
        "nearest_deadline_remaining_ms": soonest-asof_ms if soonest else None,
        "new_unreviewed_due_by_15m": len(first_15),
        "optimistic_capacity_in_at_most_6_polls_8_each": 6*CAPACITY_PER_POLL,
        "at_least_unreviewed_cannot_all_fit_in_6_polls": max(
            0, len(first_15)-6*CAPACITY_PER_POLL),
        "capacity_estimate_assumes_at_most_six_polls_one_eval_each": True,
        "not_real_API_capacity_or_Gmail_or_trade": True,
    }


def safe_new_json_output(target, sqlite_input, result):
    """Never replace a SQLite database, its journal sidecars, or any existing file.

    The exclusive 'x' open prevents symlink/hardlink overwrite and avoids a
    check-then-truncate race. Outfile creation is intentional; SQLite is read-only.
    """
    source = Path(sqlite_input).resolve(strict=True)
    out = Path(target)
    protected = (source, Path(str(source) + "-wal"),
                 Path(str(source) + "-shm"), Path(str(source) + "-journal"))
    canonical = out.resolve(strict=False)
    for p in protected:
        if canonical == p:
            raise ValueError("STAGE153_OUTPUT_ALIASES_SQLITE_OR_SIDECAR")
        if out.exists() or out.is_symlink():
            if p.exists() and os.path.samefile(out, p):
                raise ValueError("STAGE153_OUTPUT_ALIASES_SQLITE_OR_SIDECAR")
    if out.exists() or out.is_symlink():
        raise ValueError("STAGE153_OUTPUT_EXISTS_REFUSE_OVERWRITE")
    out.parent.mkdir(parents=True, exist_ok=True)
    # 'x' uses O_CREAT | O_EXCL; refuses even racing symlink targets.
    with out.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(result, sort_keys=True, indent=2) + "\n")


def main():
    p=argparse.ArgumentParser(description=__doc__)
    group=p.add_mutually_exclusive_group(required=True)
    group.add_argument("--stage28-original-artifact-dir",type=Path)
    group.add_argument("--sqlite-readonly",type=Path)
    p.add_argument("--asof-ms",type=int)
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    if a.stage28_original_artifact_dir:
        audit=audit_six(a.stage28_original_artifact_dir)
        rows=audit.pop("rows")
        result=audit
        if a.out:
            a.out.mkdir(parents=True,exist_ok=True)
            (a.out/"monster_stage153_stage28_1128_queue_lifecycle_summary.json").write_text(
                json.dumps(result,sort_keys=True,ensure_ascii=False,indent=2)+"\n")
            (a.out/"monster_stage153_stage28_1128_queue_lifecycle_rows.jsonl").write_text(
                "".join(json.dumps(x,sort_keys=True,ensure_ascii=False)+"\n" for x in rows))
        print("MONSTER_STAGE153_REAL_STAGE28_1128_LIFECYCLE "+
              json.dumps({"total":result["total"],"burst_98":result["burst_98"]},
                         sort_keys=True))
    else:
        if a.asof_ms is None or not a.sqlite_readonly.is_file():
            raise ValueError("STAGE153_REQUIRE_EXISTING_DB_AND_EXPLICIT_ASOF")
        # mode=ro prevents SQLite file mutation even when called on owner's Mac.
        uri=a.sqlite_readonly.resolve().as_uri()+"?mode=ro"
        with sqlite3.connect(uri,uri=True) as db:
            db.execute("PRAGMA query_only=ON")
            result=queue_pressure(db,a.asof_ms)
        if a.out:
            safe_new_json_output(a.out, a.sqlite_readonly, result)
        print(json.dumps(result,sort_keys=True))


if __name__=="__main__":
    main()
