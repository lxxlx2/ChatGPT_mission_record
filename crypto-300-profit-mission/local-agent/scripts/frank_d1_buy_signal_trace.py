#!/usr/bin/env python3
"""Frank D1: link existing 24h locally indexed BUY rows to source V1 events,
signals and Mission Control decisions WITHOUT RPC, changing policy or DB writes.

Export only totals and anonymized per-event join classifications. No mint, signature,
wallet, episode IDs, quotes, PnL, raw JSON, absolute DB paths or freeform reasons.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote
import argparse
import json
import os
import sqlite3
import sys
import tempfile
import time
from uuid import uuid4
import zipfile

BUY = ("BUY", "ADD", "REENTRY")
SIGNAL_TYPES = frozenset(("FRANK_ACCUMULATION_SIGNAL", "FRANK_MULTIPLE_SIGNAL"))
DECISIONS = frozenset(("BUY", "SMALL_BUY", "WAIT", "NO_BUY", "UNASSESSED"))
RELEVANT_TABLES = {"signatures", "trades", "v1_states", "signals", "v1_evaluations"}
AS_OF_FIXED = "2026-10-19T08:56:26+00:00"  # prior user Mac actual sample, not clock now


def _connect(path: Path) -> sqlite3.Connection:
    if not path.is_file() or path.is_symlink():
        raise RuntimeError("LOCAL_EXISTING_DB_UNAVAILABLE")
    db = sqlite3.connect("file:" + quote(str(path.resolve()), safe="/") + "?mode=ro",
                         uri=True, timeout=2, isolation_level=None)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA query_only=ON")
    db.execute("PRAGMA busy_timeout=1000")
    return db


def _tables(db: sqlite3.Connection) -> set[str]:
    return {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}


def _json(value) -> dict:
    try:
        parsed = json.loads(value or "{}")
    except (TypeError, ValueError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _date_epoch(value) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        if isinstance(value, (int, float)) or (
                isinstance(value, str) and value.strip().isdigit()):
            x = int(value)
            return x if 0 < x < 4_000_000_000 else None
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return int(parsed.timestamp()) if parsed.tzinfo else None
    except (ValueError, OverflowError, TypeError):
        return None


def _reason(body: dict) -> str:
    # Never return untrusted model content/reasons. Only bounded policy labels.
    if not body:
        return "SOURCE_EVALUATION_BODY_INVALID"
    stages = body.get("stages")
    if not isinstance(stages, list):
        return "EVALUATION_STAGES_UNAVAILABLE"
    if not stages:
        return "EVALUATED_NO_NEW_STAGE"
    return "EVALUATED_STAGE_REPORTED"


def trace(production: Path, control: Path, as_of: int) -> dict:
    if not 1_600_000_000 < as_of < 4_000_000_000:
        raise RuntimeError("INVALID_AS_OF")
    src = _connect(production)
    ctl = None
    try:
        missing = RELEVANT_TABLES - _tables(src)
        if missing:
            raise RuntimeError("SOURCE_SCHEMA_UNAVAILABLE:" + ",".join(sorted(missing)))
        cutoff = as_of - 86400
        signatures = src.execute(
            "SELECT COUNT(*) FROM signatures WHERE person_id='frank' "
            "AND block_time>=? AND block_time<=?", (cutoff, as_of)).fetchone()[0]
        records = src.execute(
            """SELECT t.signature,t.mint,t.side,t.episode_id,t.block_time,s.body AS source_body
               FROM trades t JOIN signatures s ON s.wallet=t.wallet AND s.signature=t.signature
               WHERE s.person_id=? AND t.side IN ('BUY','ADD','REENTRY')
                 AND t.block_time>=? AND t.block_time<=?
               ORDER BY t.block_time,t.signature""",
            ("frank", cutoff, as_of)).fetchall()
        control_available = control.is_file() and not control.is_symlink()
        if control_available:
            ctl = _connect(control)
            control_available = "candidate_latest" in _tables(ctl)
        rows = []
        mint_group = {}
        for i, record in enumerate(records):
            signature, mint = record["signature"], record["mint"]
            if mint not in mint_group:
                mint_group[mint] = len(mint_group) + 1
            source = _json(record["source_body"])
            source_class = source.get("classification")
            classification = ("ACTIVE_TRADE" if source_class == "ACTIVE_TRADE"
                              else "UNKNOWN_OR_MISMATCH")
            eval_rows = src.execute(
                "SELECT episode_id,at,body FROM v1_evaluations "
                "WHERE person_id=? AND mint=? AND signature=? ORDER BY at DESC",
                ("frank", mint, signature)).fetchall()
            seen_evaluations = len(eval_rows)
            evaluation = _json(eval_rows[0]["body"]) if eval_rows else {}
            state_row = src.execute(
                "SELECT body FROM v1_states WHERE person_id=? AND mint=?",
                ("frank", mint)).fetchone()
            model_state = _json(state_row["body"]) if state_row else {}
            events = model_state.get("events")
            model_events = events if isinstance(events, list) else []
            in_current_events = any(
                isinstance(event, dict) and event.get("signature") == signature
                for event in model_events)
            episode = (eval_rows[0]["episode_id"] if eval_rows else
                       record["episode_id"] if in_current_events else None)
            # A matching episode is *not* the same as a trade-triggered signal.
            source_signals = src.execute(
                "SELECT signal_type,created_at,body FROM signals WHERE person_id=? AND mint=?",
                ("frank", mint)).fetchall()
            triggered = [s for s in source_signals
                         if _json(s["body"]).get("triggering_signature") == signature]
            signal_types = sorted({
                s["signal_type"] for s in triggered
                if s["signal_type"] in SIGNAL_TYPES})
            unknown_type_count = sum(
                s["signal_type"] not in SIGNAL_TYPES for s in triggered)
            candidate = "NOT_QUERIED"
            same_episode_candidate = "NOT_VERIFIED"
            if control_available and ctl is not None:
                ctl_rows = ctl.execute(
                    "SELECT episode_id,decision,body FROM candidate_latest "
                    "WHERE person_id=? AND mint=?", ("frank", mint)).fetchall()
                matched = [c for c in ctl_rows if episode and c["episode_id"] == episode]
                same_episode_candidate = (
                    "SAME_EPISODE_PRESENT" if matched else "NO_MATCHING_EPISODE")
                # Exact signal-to-decision join: source_signal_id is in the
                # decision body, not the candidate_latest primary-key columns.
                ids = {_json(s["body"]).get("signal_id") for s in triggered}
                ids.discard(None)
                joined = [c for c in matched
                          if _json(c["body"]).get("source_signal_id") in ids]
                if joined:
                    candidate = ("SAME_EVENT_SIGNAL_DECISION_" +
                                 (joined[0]["decision"] if joined[0]["decision"] in DECISIONS
                                  else "OTHER"))
                elif matched:
                    candidate = "SAME_EPISODE_NOT_EXACT_SIGNAL"
                else:
                    candidate = "NO_EXACT_SIGNAL_DECISION_LINK"
            if triggered:
                stage = "TRADE_TRIGGERED_SIGNAL_FOUND"
            elif seen_evaluations:
                stage = "TRADE_EVALUATED_NO_TRIGGERED_SIGNAL"
            elif in_current_events:
                stage = "CURRENT_MODEL_EVENT_WITHOUT_EVALUATION"
            else:
                stage = "TRADE_NOT_JOINED_TO_MODEL_EVALUATION"
            rows.append({
                "event_ordinal": i + 1, "same_mint_group": mint_group[mint],
                "side": record["side"] if record["side"] in BUY else "OTHER",
                "source_class": classification,
                "event_age_seconds_at_sample": as_of - int(record["block_time"]),
                "exact_source_evaluation_count": seen_evaluations,
                "evaluation_status": _reason(evaluation) if seen_evaluations else "NO_EVALUATION_FOUND",
                "in_current_model_event_list": in_current_events,
                "triggered_signal_types": signal_types,
                "triggered_unknown_signal_types_count": unknown_type_count,
                "causal_stage": stage,
                "same_episode_decision_presence": same_episode_candidate,
                "exact_triggered_signal_to_decision": candidate,
            })
        distribution = dict(sorted(Counter(x["causal_stage"] for x in rows).items()))
        return {
            "kind": "FRANK_V2_D1_LOCAL_BUY_CAUSAL_TRACE",
            "as_of_utc": datetime.fromtimestamp(as_of, timezone.utc).isoformat(),
            "window": "24H_ENDING_AT_REFERENCE_MAC_SAMPLE",
            "source_scope": "LOCAL_INDEX_ONLY_NOT_FULL_CHAIN",
            "chain_completeness_verified": False,
            "production_source": "EXISTING_FORWARD_SQLITE_MODE_RO_QUERY_ONLY",
            "control_source": ("EXISTING_MISSION_CONTROL_SQLITE_MODE_RO_QUERY_ONLY"
                               if control_available else "CONTROL_CANDIDATE_LATEST_UNAVAILABLE"),
            "source_signatures_24h": signatures,
            "recognized_buy_rows_24h": len(records),
            "recognized_buys_vs_prior_mac_sample": (
                "MATCH_2" if len(records) == 2 and signatures == 273
                else "DIFF_OR_VERSION_WINDOW_UNVERIFIED"),
            "causal_stage_counts": distribution,
            "events": rows,
            "trade_authorization": False,
            "frozen_policy_unchanged": True,
            "new_rpc": False, "production_db_writes": False, "gmail": False,
            "wallet_mints_signatures_exported": False,
            "limitations": [
                "Causal join uses recorded local model evaluations/signals/decisions only.",
                "No same-signature source evaluation is not proof of missed chain trades.",
                "Stored signal and candidate presence are not live F01 eligible signals.",
                "No full-chain backfill, current owner balance, PnL or price query performed.",
            ],
        }
    finally:
        if ctl is not None:
            ctl.close()
        src.close()


def _local_paths(home: Path) -> tuple[Path, Path]:
    support = home / "Library/Application Support/FrankMeme"
    pointer = home / ".frank_meme_control_root"
    if not pointer.is_file() or pointer.is_symlink() or pointer.stat().st_size > 4096:
        raise RuntimeError("LOCAL_CONTROL_POINTER_UNAVAILABLE")
    text = pointer.read_text(encoding="utf-8").strip()
    if not text or "\n" in text:
        raise RuntimeError("INVALID_LOCAL_CONTROL_POINTER")
    control = Path(text).expanduser() / "mission-control.sqlite"
    # Existing canonical Frank source path from the already-reviewed
    # frank_pr39_predeploy_readonly.py; do not probe other directories.
    production = (home / "Documents/ChatGPT/"
                  "crypto-monitor-frank-only-evidence-20261003/live-v1/forward.sqlite")
    return production, control


def _zip(report: dict, path: Path):
    raw = json.dumps(report, sort_keys=True, ensure_ascii=False, indent=2).encode()
    if len(raw) > 64_000:
        raise RuntimeError("SUMMARY_TOO_LARGE")
    path.parent.mkdir(exist_ok=True, parents=True)
    with tempfile.TemporaryDirectory(prefix=".frank-d1-", dir=path.parent) as d:
        source = Path(d) / "evidence.zip"
        with zipfile.ZipFile(source, "x", compression=zipfile.ZIP_DEFLATED) as f:
            f.writestr("frank-d1-buy-causal-summary.json", raw)
        with zipfile.ZipFile(source) as f:
            if f.namelist() != ["frank-d1-buy-causal-summary.json"] or f.testzip():
                raise RuntimeError("EVIDENCE_ZIP_INVALID")
        os.link(source, path)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--as-of-utc", default=AS_OF_FIXED)
    args = p.parse_args()
    timestamp = _date_epoch(args.as_of_utc)
    if timestamp is None:
        p.error("invalid aware ISO8601 reference timestamp")
    try:
        source, control = _local_paths(Path.home())
        summary = trace(source, control, timestamp)
        out = (Path.home() / "Downloads"
               / ("frank-d1-causal-" + datetime.now().strftime("%Y%m%d-%H%M%S")
                  + "-" + uuid4().hex[:10] + ".zip"))
        _zip(summary, out)
        print("FRANK_D1_CAUSAL_STAGE_COUNTS=" + json.dumps(summary["causal_stage_counts"],
              ensure_ascii=False, sort_keys=True), flush=True)
        print("FRANK_D1_INDEXED_BUYS=" + str(summary["recognized_buy_rows_24h"]), flush=True)
        print("ZIP_READY=" + str(out), flush=True)
        if sys.platform == "darwin":
            import subprocess
            subprocess.run(["open", "-R", str(out)], timeout=10, check=False)
        return 0
    except (OSError, sqlite3.Error, RuntimeError, ValueError) as exc:
        # No absolute local paths, SQL/error text or records emitted.
        print("FRANK_D1_READONLY_FAILED:" + type(exc).__name__, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
