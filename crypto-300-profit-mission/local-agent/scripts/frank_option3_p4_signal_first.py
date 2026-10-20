"""Frank P4: bounded source-signal-FIRST to later sale correlation.

Historical research only. Scan existing source SQLite in read-only/query-only
mode, verify frozen V1 signal body and exact emitted source evaluation, then
find later same-mint/same-episode locally classified sale. A generated signal
is NOT proof that a notification was delivered. Does not infer wallet balance,
trade profitability, current price, or source observability at event time.
No RPC, HTTP, mail, outbox changes, wallet ops, or new data acquisition.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
import sys

from frank_option3_p4_causal_ro import open_ro, safe_json, check_source_schema

VALID_SIGNAL_TYPES = {"FRANK_ACCUMULATION_SIGNAL", "FRANK_MULTIPLE_SIGNAL"}
VALID_SALE_SIDES = {"SELL", "EXIT", "SELL_POSITION_UNRESOLVED"}
FROZEN_POLICY = "FRANK_LOCAL_SIGNAL_V1"
MAX_SIGNAL_ROWS = 1000
WINDOW_DAYS = 60


def epoch(value):
    if isinstance(value, bool):
        return None
    try:
        ts = int(value)
    except (ValueError, TypeError, OverflowError):
        return None
    return ts if 1_600_000_000 <= ts < 4_000_000_000 else None


def scan(db: sqlite3.Connection, *, as_of: int) -> dict:
    if epoch(as_of) != as_of:
        raise ValueError("AS_OF_UNVERIFIED")
    check_source_schema(db)
    since = as_of - WINDOW_DAYS * 86400
    rows = db.execute(
        """SELECT signal_id,signal_type,episode_id,mint,created_at,body
           FROM signals
           WHERE person_id='frank'
             AND signal_type IN ('FRANK_ACCUMULATION_SIGNAL','FRANK_MULTIPLE_SIGNAL')
             AND CAST(created_at AS INTEGER)>=?
             AND CAST(created_at AS INTEGER)<=?
           ORDER BY CAST(created_at AS INTEGER),signal_id LIMIT ?""",
        (since, as_of, MAX_SIGNAL_ROWS + 1),
    ).fetchall()
    if len(rows) > MAX_SIGNAL_ROWS:
        raise RuntimeError("SIGNAL_SCAN_EXCEEDS_BOUND_NOT_TRUNCATED")
    signals_ok = []
    rejected = Counter()
    for sig in rows:
        body = safe_json(sig["body"])
        ts = epoch(sig["created_at"])
        episode = sig["episode_id"]
        if (body.get("policy_id") != FROZEN_POLICY
                or body.get("signal_id") != sig["signal_id"]
                or body.get("episode_id") != episode
                or body.get("mint") != sig["mint"]
                or ts is None or ts < since or ts > as_of):
            rejected["SIGNAL_BODY_OR_TIME_UNVERIFIED"] += 1
            continue
        trigger = body.get("triggering_signature")
        if not isinstance(trigger, str) or not trigger:
            rejected["SOURCE_TRIGGER_SIGNATURE_UNAVAILABLE"] += 1
            continue
        evals = db.execute(
            """SELECT body,episode_id FROM v1_evaluations
               WHERE person_id='frank' AND mint=? AND signature=?
                 AND episode_id=? ORDER BY at DESC LIMIT 64""",
            (sig["mint"], trigger, episode),
        ).fetchall()
        source_emit_mode = set()
        for evaluation in evals:
            obj = safe_json(evaluation["body"])
            if sig["signal_id"] in (obj.get("signal_ids") or []):
                if obj.get("kind") in {"ACTIVE_TRADE", "HOURLY_29"}:
                    source_emit_mode.add(obj["kind"])
        if not source_emit_mode:
            rejected["SOURCE_EVALUATION_EMISSION_LINK_UNVERIFIED"] += 1
            continue
        signals_ok.append((sig, ts, tuple(sorted(source_emit_mode))))
    verified_later_sales = {}
    signals_with_later_sales = 0
    for sig, source_ts, emit_modes in signals_ok:
        sale_rows = db.execute(
            """SELECT t.signature,t.side,t.block_time,s.body AS signature_body
               FROM trades t JOIN signatures s
               ON s.wallet=t.wallet AND s.signature=t.signature
               WHERE s.person_id='frank' AND t.mint=? AND t.episode_id=?
               AND t.block_time>? AND t.block_time<=?
               AND t.side IN ('SELL','EXIT','SELL_POSITION_UNRESOLVED')
               ORDER BY t.block_time,t.signature LIMIT 1001""",
            (sig["mint"], sig["episode_id"], source_ts, as_of),
        ).fetchall()
        if len(sale_rows) > 1000:
            raise RuntimeError("LATER_SALE_SCAN_EXCEEDS_BOUND_NOT_TRUNCATED")
        valid = 0
        for sale in sale_rows:
            source_row = safe_json(sale["signature_body"])
            if source_row.get("classification") != "ACTIVE_TRADE":
                continue
            key = sale["signature"]
            if key is None:
                continue
            valid += 1
            curr = verified_later_sales.get(key)
            if curr is None:
                verified_later_sales[key] = {
                    "side": sale["side"],
                    "emission_mode": set(emit_modes),
                    "mint": sig["mint"],
                    "episode": sig["episode_id"],
                }
            else:
                curr["emission_mode"].update(emit_modes)
        if valid:
            signals_with_later_sales += 1
    by_side = Counter(x["side"] for x in verified_later_sales.values())
    by_emit_mode = Counter(
        m for x in verified_later_sales.values()
        for m in x["emission_mode"]
    )
    distinct_episodes = {
        (x["mint"], x["episode"]) for x in verified_later_sales.values()
    }
    return {
        "kind": "FRANK_P4_SIGNAL_FIRST_LATER_SELL_LOCAL_READONLY",
        "status": ("SOME_PRIOR_SIGNAL_TO_LATER_SELL_LOCAL_FACTS"
                   if verified_later_sales else "NO_PROVEN_MATCH_IN_BOUNDED_LOCAL_WINDOW"),
        "as_of_utc": datetime.fromtimestamp(as_of, timezone.utc).isoformat(),
        "window_days": WINDOW_DAYS,
        "scope": "LOCAL_INDEX_ONLY_NOT_COMPLETE_CHAIN",
        "signal_rows_examined": len(rows),
        "source_signal_emission_bound": len(signals_ok),
        "signals_with_same_episode_later_sell": signals_with_later_sales,
        "distinct_verified_sale_signatures": len(verified_later_sales),
        "distinct_linked_episodes": len(distinct_episodes),
        "linked_sale_sides": dict(by_side),
        "source_emission_modes_for_sales": dict(by_emit_mode),
        "rejected_signal_counts": dict(rejected),
        "same_episode_signal_before_sell_proven": bool(verified_later_sales),
        "signal_generation_proves_notification_delivery": False,
        "recipient_delivery_verified": False,
        "current_wallet_balance_verified": False,
        "chain_signature_independently_rechecked": False,
        "notification_or_trade_authorized": False,
        "source_db_writes": False,
        "non_user_approved_provider_calls": False,
        "raw_mints_wallets_signatures_amounts_or_paths_exported": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--forward-db", required=True, type=Path)
    args = parser.parse_args()
    try:
        db = open_ro(args.forward_db.expanduser())
        try:
            output = scan(db, as_of=int(datetime.now(timezone.utc).timestamp()))
        finally:
            db.close()
    except (OSError, sqlite3.Error, RuntimeError, TypeError, ValueError) as exc:
        print("P4_SIGNAL_FIRST_READONLY_ERROR=" + type(exc).__name__, file=sys.stderr)
        return 2
    print("P4_SIGNAL_FIRST_READONLY=" + json.dumps(output, sort_keys=True,
                                                ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
