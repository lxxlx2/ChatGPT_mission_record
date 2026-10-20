"""Frank Option 3 P4: exact source-to-V1 causal join for ten recent local trades.

Source rows: the user's EXISTING localhost Frank 8766 read-only GET.
Verification: EXISTING forward.sqlite + optional mission-control.sqlite, both
SQLite mode=ro / query_only=ON. The report outputs anonymized bounded enums
and counts ONLY: no CA, wallet, signature, quote, recipient, DB path or PnL.

IMPORTANT: a trade's matching mint, episode or older unrelated V1 signal is
never evidence that this precise signed transaction triggered a source alert.
No external network, RPC, notifications, wallet actions, DB writes or deploy.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
import sys
from urllib.parse import quote
from urllib.request import build_opener, ProxyHandler, HTTPRedirectHandler, Request

LOCAL_AGENT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LOCAL_AGENT / "scripts"))
from frank_option3_p4_history import select_cases  # noqa: E402

SOURCE = "http://127.0.0.1:8766/api/trades"
SIGNALS = {"FRANK_ACCUMULATION_SIGNAL", "FRANK_MULTIPLE_SIGNAL"}
BUY_SIDES = {"BUY", "ADD", "REENTRY"}


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


def get_existing_trades() -> list[dict]:
    with build_opener(ProxyHandler({}), NoRedirect).open(
        Request(SOURCE, method="GET"), timeout=8,
    ) as resp:
        data = resp.read(6_000_001)
    if len(data) > 6_000_000:
        raise RuntimeError("LOCAL_GET_RESPONSE_TOO_LARGE")
    parsed = json.loads(data)
    if not isinstance(parsed, list):
        raise RuntimeError("LOCAL_TRADES_NOT_LIST")
    return parsed


def open_ro(path: Path) -> sqlite3.Connection:
    if not path.is_file() or path.is_symlink():
        raise RuntimeError("EXPLICIT_EXISTING_DATABASE_UNAVAILABLE")
    db = sqlite3.connect(
        "file:" + quote(str(path.resolve()), safe="/") + "?mode=ro",
        uri=True, isolation_level=None, timeout=2,
    )
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA query_only=ON")
    db.execute("PRAGMA busy_timeout=1000")
    return db


def safe_json(value) -> dict:
    try:
        obj = json.loads(value or "{}")
    except (TypeError, ValueError):
        return {}
    return obj if isinstance(obj, dict) else {}


def tables(db: sqlite3.Connection) -> set[str]:
    return {r[0] for r in db.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    )}


def check_source_schema(db: sqlite3.Connection) -> None:
    needed = {"signatures", "trades", "v1_states", "signals", "v1_evaluations"}
    if not needed <= tables(db):
        raise RuntimeError("FRANK_SOURCE_SCHEMA_INCOMPLETE")


def checked_source(db: sqlite3.Connection, case: dict) -> tuple[str, dict | None]:
    rows = db.execute(
        """SELECT t.signature,t.mint,t.side,t.block_time,t.episode_id,
                  s.body AS signature_body
           FROM trades t JOIN signatures s
             ON s.wallet=t.wallet AND s.signature=t.signature
           WHERE s.person_id='frank' AND t.signature=? AND t.mint=?""",
        (case["signature"], case["mint"]),
    ).fetchall()
    if len(rows) != 1:
        return "SOURCE_TRADE_EXACT_MATCH_UNAVAILABLE", None
    row = dict(rows[0])
    if row["side"] != case["indexed_side"] or (
        not isinstance(row["block_time"], (int, float))
        or int(row["block_time"]) != int(case["block_time"])
    ):
        return "SOURCE_TRADE_CHANGED_SINCE_LOCAL_HTTP_CAPTURE", None
    signature_info = safe_json(row["signature_body"])
    if signature_info.get("classification") != "ACTIVE_TRADE":
        return "SOURCE_SIGNER_CLASSIFICATION_NOT_ACTIVE_TRADE", None
    return "EXACT_LOCAL_SOURCE_TRADE_VERIFIED", row


def causal_status(db: sqlite3.Connection, case: dict, row: dict) -> dict:
    evals = db.execute(
        """SELECT episode_id,at,body FROM v1_evaluations
           WHERE person_id='frank' AND mint=? AND signature=? ORDER BY at DESC""",
        (case["mint"], case["signature"]),
    ).fetchall()
    signals = db.execute(
        """SELECT signal_id,signal_type,episode_id,created_at,body
           FROM signals WHERE person_id='frank' AND mint=?""",
        (case["mint"],),
    ).fetchall()
    exact_signals = [s for s in signals if
                     safe_json(s["body"]).get("triggering_signature") == case["signature"]
                     and s["signal_type"] in SIGNALS]
    unknown_types = [s for s in signals if
                     safe_json(s["body"]).get("triggering_signature") == case["signature"]
                     and s["signal_type"] not in SIGNALS]
    evaluation_episode = str(evals[0]["episode_id"]) if evals else None
    signal_types = sorted({str(s["signal_type"]) for s in exact_signals})
    exact_ids = {s["signal_id"] for s in exact_signals}
    bound_active_ids: set[str] = set()
    bound_hourly_ids: set[str] = set()
    for evaluation in evals:
        payload = safe_json(evaluation["body"])
        emitted = payload.get("signal_ids")
        if not isinstance(emitted, list):
            continue
        bound = {sig["signal_id"] for sig in exact_signals
                 if sig["signal_id"] in emitted
                 and str(sig["episode_id"]) == str(evaluation["episode_id"])}
        if payload.get("kind") == "ACTIVE_TRADE":
            bound_active_ids.update(bound)
        elif payload.get("kind") == "HOURLY_29":
            bound_hourly_ids.update(bound)
    matched_emission_ids = bound_active_ids | bound_hourly_ids
    evaluation_binding_complete = (
        bool(exact_ids) and matched_emission_ids == exact_ids
    )
    conflicting_signal_episode = bool(
        exact_signals and evals and
        any(not any(str(sig["episode_id"]) == str(e["episode_id"])
                    for e in evals) for sig in exact_signals)
    )
    if case["indexed_side"] in BUY_SIDES:
        if conflicting_signal_episode:
            causal = "SIGNAL_EVALUATION_EPISODE_MISMATCH"
        elif bound_active_ids and evaluation_binding_complete:
            causal = "SOURCE_SIGNAL_EMITTED_BY_ACTIVE_TRADE_EVALUATION"
        elif bound_hourly_ids and evaluation_binding_complete:
            causal = "SIGNAL_REFERENCES_BUY_SIGNATURE_EMITTED_ON_HOURLY_TICK"
        elif exact_signals:
            causal = "SIGNAL_REFERENCES_SIGNATURE_BUT_EVALUATION_LINK_UNPROVEN"
        elif evals:
            causal = "EXACT_TRANSACTION_EVALUATED_NO_NEW_SIGNAL"
        else:
            causal = "EXACT_BUY_EVALUATION_NOT_FOUND"
    else:
        if exact_signals:
            causal = "SELL_HAS_EXACT_V1_BUY_SIGNAL_NEEDS_SOURCE_REVIEW"
        elif evals:
            causal = "SELL_EVALUATED_NO_V1_BUY_SIGNAL"
        else:
            causal = "SELL_NO_V1_BUY_SIGNAL_EXPECTED"
    model = db.execute(
        "SELECT body FROM v1_states WHERE person_id='frank' AND mint=?",
        (case["mint"],),
    ).fetchone()
    state = safe_json(model["body"]) if model else {}
    current_events = state.get("events")
    in_current_episode = (
        any(isinstance(ev, dict) and ev.get("signature") == case["signature"]
            for ev in current_events)
        if isinstance(current_events, list) else False
    )
    return {
        "causal_status": causal,
        "source_eval_count_exact_signature": len(evals),
        "source_signal_count_exact_triggering_signature": len(exact_signals),
        "source_signal_types_exact": signal_types,
        "unexpected_signal_type_count": len(unknown_types),
        "source_episode_exact": evaluation_episode,
        "in_current_v1_state_event_list": in_current_episode,
        "triggered_signal_ids": {s["signal_id"] for s in exact_signals},
        "signal_evaluation_episode_conflict": conflicting_signal_episode,
        "signal_emitted_by_active_trade_eval": bool(bound_active_ids),
        "signal_emitted_by_hourly_tick_eval": bool(bound_hourly_ids),
        "signal_emission_evaluation_binding_complete": evaluation_binding_complete,
    }


def control_link(ctl: sqlite3.Connection | None, case: dict,
                 evidence: dict) -> str:
    if ctl is None:
        return "CONTROL_NOT_AVAILABLE"
    if evidence["source_signal_count_exact_triggering_signature"] == 0:
        return "NO_EXACT_TRIGGERED_V1_SIGNAL_TO_JOIN"
    if evidence["signal_evaluation_episode_conflict"]:
        return "SIGNAL_EVALUATION_EPISODE_MISMATCH_NO_JOIN"
    if not evidence["signal_emission_evaluation_binding_complete"]:
        return "SIGNAL_REFERENCES_SIGNATURE_BUT_EMISSION_LINK_UNPROVEN"
    episode = evidence["source_episode_exact"]
    if episode is None:
        return "SIGNAL_PRESENT_BUT_EXACT_EVALUATION_EPISODE_UNKNOWN"
    rows = ctl.execute(
        """SELECT episode_id,decision,body FROM candidate_latest
           WHERE person_id='frank' AND mint=?""", (case["mint"],),
    ).fetchall()
    matched = [c for c in rows if str(c["episode_id"]) == episode]
    if not matched:
        return "NO_SAME_EPISODE_CONTROL_CANDIDATE"
    exact = [c for c in matched
             if safe_json(c["body"]).get("source_signal_id")
             in evidence["triggered_signal_ids"]]
    if not exact:
        return "SAME_EPISODE_BUT_NO_EXACT_SIGNAL_ID_LINK"
    choice = str(exact[0]["decision"])
    return ("EXACT_SIGNAL_TO_CONTROL_" + choice
            if choice in {"BUY", "SMALL_BUY", "WAIT", "NO_BUY", "UNASSESSED"}
            else "EXACT_SIGNAL_TO_CONTROL_OTHER_DECISION")


def analyze(forward: Path, control: Path | None) -> dict:
    selected = select_cases(get_existing_trades())
    db = open_ro(forward)
    ctl = None
    try:
        check_source_schema(db)
        if control is not None and control.is_file() and not control.is_symlink():
            ctl = open_ro(control)
            if "candidate_latest" not in tables(ctl):
                ctl.close()
                ctl = None
        rows = []
        for i, case in enumerate(selected, 1):
            source_status, source = checked_source(db, case)
            if source is None:
                rows.append({
                    "case_ordinal": i,
                    "indexed_side": case["indexed_side"],
                    "source_match": source_status,
                    "causal_status": "NOT_EVALUATED_SOURCE_INCONSISTENT",
                    "control_link": "NOT_QUERIED",
                })
                continue
            causal = causal_status(db, case, source)
            joined = control_link(ctl, case, causal)
            rows.append({
                "case_ordinal": i,
                "indexed_side": case["indexed_side"],
                "source_match": source_status,
                "causal_status": causal["causal_status"],
                "exact_source_evaluations": causal["source_eval_count_exact_signature"],
                "exact_v1_signals": causal["source_signal_count_exact_triggering_signature"],
                "v1_signal_types": causal["source_signal_types_exact"],
                "active_trade_signal_emission_proven": causal["signal_emitted_by_active_trade_eval"],
                "hourly_tick_signal_emission_proven": causal["signal_emitted_by_hourly_tick_eval"],
                "in_current_model_episode": causal["in_current_v1_state_event_list"],
                "unexpected_source_signal_types": causal["unexpected_signal_type_count"],
                "control_link": joined,
            })
        complete = len(selected) == 10 and len(rows) == 10
        exact_sources = sum(
            x["source_match"] == "EXACT_LOCAL_SOURCE_TRADE_VERIFIED"
            for x in rows
        )
        return {
            "kind": "FRANK_OPTION3_TEN_TRADE_EXACT_CAUSAL_JOIN",
            "status": (
                "TEN_LOCAL_SOURCE_ROWS_RECONCILED" if complete and exact_sources == 10
                else "LOCAL_SOURCE_RECONCILIATION_INCOMPLETE_NOT_ZERO_TRADES"
            ),
            "sampled_at_utc": datetime.now(timezone.utc).isoformat(),
            "scope": "LOCAL_INDEX_ONLY_NOT_CHAIN_VERIFIED",
            "source_database": "EXISTING_FORWARD_SQLITE_MODE_RO_QUERY_ONLY",
            "control_database": ("EXISTING_CONTROL_SQLITE_MODE_RO_QUERY_ONLY"
                                 if ctl else "UNAVAILABLE_NOT_ZERO"),
            "distinct_locally_indexed_rows": len(selected),
            "distinct_transaction_signatures_selected": len(selected),
            "source_reconciled_rows": exact_sources,
            "source_status_counts": dict(Counter(x["source_match"] for x in rows)),
            "buy_causal_counts": dict(Counter(
                x["causal_status"] for x in rows
                if x["indexed_side"] in BUY_SIDES
            )),
            "control_link_counts": dict(Counter(x["control_link"] for x in rows)),
            "rows": rows,
            "no_signatures_wallets_mints_amounts_paths_exported": True,
            "chain_completeness_verified": False,
            "real_notification_verified": False,
            "new_rpc_or_network_provider_called": False,
            "production_db_write": False,
            "trade_authorization": False,
        }
    finally:
        if ctl is not None:
            ctl.close()
        db.close()


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--forward-db", required=True, type=Path)
    p.add_argument("--control-db", type=Path)
    args = p.parse_args()
    try:
        out = analyze(args.forward_db.expanduser(),
                      args.control_db.expanduser() if args.control_db else None)
    except (RuntimeError, sqlite3.Error, OSError, ValueError,
            TypeError, json.JSONDecodeError) as err:
        print("P4_CAUSAL_READONLY_ERROR=" + type(err).__name__, file=sys.stderr)
        return 2
    print("P4_CAUSAL_READONLY=" + json.dumps(out, ensure_ascii=False,
                                           sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
