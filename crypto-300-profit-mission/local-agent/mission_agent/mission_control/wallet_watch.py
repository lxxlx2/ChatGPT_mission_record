"""Read-only, independent Frank observed-token watchlist.

This module never signals, sends Gmail, fetches prices, assumes profitable PnL,
or changes frozen V1 states. A local OPEN means model state only, NOT an
independently verified chain balance. Historical rows persist beyond 24 hours.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import sqlite3
from typing import Any

from .db import open_production_ro

BUY = frozenset({"BUY", "ADD", "REENTRY"})
SELL = frozenset({"SELL", "EXIT", "SELL_POSITION_UNRESOLVED"})
PERSON = "frank"
SCHEMA_VERSION = 1


def _json_obj(value: Any) -> dict:
    if isinstance(value, dict):
        return value
    try:
        obj = json.loads(value or "{}")
        return obj if isinstance(obj, dict) else {}
    except (TypeError, ValueError):
        return {}


def _positive_int(value: Any) -> int | None:
    try:
        n = int(value)
        return n if n >= 0 else None
    except (TypeError, ValueError, OverflowError):
        return None


def _amount(body: dict) -> tuple[str | None, str | None]:
    original = body.get("original_quote")
    if body.get("quote_normalization") and isinstance(original, dict):
        asset = original.get("quote_asset")
        num = original.get("quote_quantity")
        try:
            q = Decimal(str(num))
            return asset, str(q) if q.is_finite() and q >= 0 else None
        except (InvalidOperation, ValueError):
            return asset, None
    asset = body.get("quote_asset")
    raw = body.get("quote_amount_raw")
    decimals = _positive_int(body.get("quote_decimals"))
    if raw is None or decimals is None or decimals > 30:
        return asset, None
    try:
        q = Decimal(str(raw)) / (Decimal(10) ** decimals)
        return asset, str(q) if q.is_finite() and q >= 0 else None
    except (InvalidOperation, ValueError, OverflowError):
        return asset, None


def _inventory_category(state: str) -> str:
    if state == "OPEN":
        return "MODEL_OPEN_UNVERIFIED"
    if state == "CLOSED":
        return "MODEL_CLOSED_NOT_CHAIN_CONFIRMED"
    if state == "INVENTORY_UNDETERMINED":
        return "INVENTORY_UNDETERMINED"
    return "HISTORY_ONLY_UNVERIFIED"


def _watch_state(inventory: str, buy_count: int, sell_count: int) -> str:
    if inventory == "MODEL_OPEN_UNVERIFIED":
        return "MODEL_OPEN"
    if inventory == "INVENTORY_UNDETERMINED":
        return "NEEDS_INVENTORY_REVIEW"
    if inventory == "MODEL_CLOSED_NOT_CHAIN_CONFIRMED":
        return "HISTORICAL_EXIT"
    if buy_count:
        return "WATCH_UNRESOLVED"
    if sell_count:
        return "HISTORY_SELL_ONLY"
    return "MODEL_STATE_ONLY"


def _timestamp(obj: dict) -> int | None:
    try:
        n = int(obj.get("block_time"))
        return n if n > 0 else None
    except (ValueError, TypeError):
        return None


def from_seed(watch_seed: list[dict], *, as_of: int | None = None) -> dict:
    """Normalize researched historical observations without inventing inventory.

    Works with exported frank-d0-local-index.json without raw Mac SQLite.
    """
    by_mint = {}
    for row in watch_seed:
        if not isinstance(row, dict):
            continue
        mint = row.get("mint")
        if not isinstance(mint, str) or not (32 <= len(mint) <= 44):
            continue
        buys = _positive_int(row.get("local_recognized_buy_count")) or 0
        sells = _positive_int(row.get("local_recognized_sell_count")) or 0
        raw_state = row.get("local_state") or "UNKNOWN"
        inventory = _inventory_category(raw_state)
        last = row.get("latest_recognized_trade") or {}
        when = _timestamp(last)
        entry = {
            "mint": mint,
            "watch_state": _watch_state(inventory, buys, sells),
            "inventory_evidence": inventory,
            "local_model_state": raw_state,
            "local_current_raw": row.get("local_current_raw"),
            "local_recognized_buys": buys,
            "local_recognized_sells": sells,
            "last_event_time": when,
            "last_event_signature": last.get("signature"),
            "last_event_side": last.get("side"),
            "last_observed_quote_asset": last.get("quote_asset"),
            "last_observed_quote_quantity": last.get("quote_amount"),
            "last_event_evidence": "LOCAL_INDEX_MULTILEG_UNRESOLVED" if row.get("last_event_multileg_conflict") else "LOCAL_INDEX_CLASSIFICATION_ONLY",
            "last_event_multileg_conflict": bool(row.get("last_event_multileg_conflict")),
            "conflicting_trade_signatures": int(row.get("conflicting_trade_signatures") or 0),
            "current_chain_balance": None,
            "current_chain_balance_verified": False,
            "market_value_usd": None,
            "pnl_usd": None,
            "capital_at_risk_status": "UNRESOLVED",
            "is_follow_signal": False,
            "signal_authority": "SEPARATE_FROZEN_ENGINE",
        }
        if mint not in by_mint or (when or 0) >= (by_mint[mint].get("last_event_time") or 0):
            by_mint[mint] = entry
    rows = sorted(by_mint.values(), key=lambda x: (-(x["last_event_time"] or 0), x["mint"]))
    summary = {
        "total_observed": len(rows),
        "model_open": sum(x["watch_state"] == "MODEL_OPEN" for x in rows),
        "inventory_needs_review": sum(x["watch_state"] == "NEEDS_INVENTORY_REVIEW" for x in rows),
        "historical_exit": sum(x["watch_state"] == "HISTORICAL_EXIT" for x in rows),
        "unresolved_history": sum(x["watch_state"] in {"WATCH_UNRESOLVED", "HISTORY_SELL_ONLY", "MODEL_STATE_ONLY"} for x in rows),
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "scope": "LOCAL_INDEX_ONLY_NOT_COMPLETE_CHAIN",
        "chain_completeness_verified": False,
        "updated_at_utc": datetime.fromtimestamp(as_of, timezone.utc).isoformat() if as_of else None,
        "summary": summary,
        "rows": rows,
    }



def merge_signature_activity(observed: dict, signature_rows: list[dict]) -> dict:
    """Include *all* wallet-owned token-account activity, not only recognized trades.

    Raw per-token deltas are transaction evidence, NOT an actionable token
    recommendation, trusted cost basis, market-price observation, or a verified
    live balance. Missing parsed source/destination cannot be invented.
    """
    from collections import Counter

    existing = {row["mint"]: row for row in observed["rows"]}
    evidence = {}
    classes = Counter()
    no_transfer_flow = 0
    for record in signature_rows:
        if not isinstance(record, dict):
            continue
        body = _json_obj(record.get("body"))
        tx = _json_obj(body.get("evidence"))
        cls = body.get("classification") or "UNKNOWN"
        classes[cls] += 1
        flows = tx.get("wallet_token_transfer_flows")
        if not isinstance(flows, list) or not flows:
            no_transfer_flow += 1
        deltas = tx.get("token_balance_deltas") or []
        if not isinstance(deltas, list):
            continue
        # Multiple token accounts for the same mint can occur in one tx.
        by_mint: dict[str, dict] = {}
        for delta in deltas:
            if not isinstance(delta, dict) or delta.get("wallet_owned") is not True:
                continue
            mint = delta.get("mint")
            decimals = delta.get("decimals")
            raw = delta.get("delta")
            if (not isinstance(mint, str) or not 32 <= len(mint) <= 44
                or type(decimals) is not int or not 0 <= decimals <= 18
                or type(raw) not in (str, int) or
                not str(raw).lstrip("-").isascii() or
                not str(raw).lstrip("-").isdecimal()):
                continue
            k = by_mint.setdefault(mint, {"delta": 0, "decimals": decimals})
            if k["decimals"] != decimals:
                k["mixed_decimals"] = True
            k["delta"] += int(raw)
        timestamp = _positive_int(record.get("block_time"))
        for mint, item in by_mint.items():
            record_entry = evidence.setdefault(mint, {
                "in": 0, "out": 0, "zero": 0, "passive_in": 0,
                "last_timestamp": None, "last_signature": None,
                "raw_in": 0, "raw_out": 0,
                "decimals": item["decimals"], "mixed_decimals": False,
            })
            if item.get("mixed_decimals") or record_entry["decimals"] != item["decimals"]:
                record_entry["mixed_decimals"] = True
            change = item["delta"]
            if change > 0:
                record_entry["in"] += 1
                record_entry["raw_in"] += change
                if cls == "PASSIVE_TRANSFER" and tx.get("wallet_is_signer") is False:
                    record_entry["passive_in"] += 1
            elif change < 0:
                record_entry["out"] += 1
                record_entry["raw_out"] += -change
            else:
                record_entry["zero"] += 1
            if timestamp is not None and (
                record_entry["last_timestamp"] is None or
                timestamp >= record_entry["last_timestamp"]
            ):
                record_entry["last_timestamp"] = timestamp
                record_entry["last_signature"] = record.get("signature")
    new_passive = 0
    new_other = 0
    for mint, activity in evidence.items():
        row = existing.get(mint)
        if row is None:
            row = from_seed([{"mint": mint, "local_state": "UNKNOWN"}])["rows"][0]
            if activity["passive_in"]:
                row["watch_state"] = "PASSIVE_RECEIPT_ONLY"
                new_passive += 1
            else:
                row["watch_state"] = "OTHER_ACCOUNT_ACTIVITY"
                new_other += 1
            row["origin_scope"] = "SIGNATURE_TOKEN_DELTA_ONLY"
            existing[mint] = row
        else:
            row["origin_scope"] = "LOCAL_TRADE_OR_MODEL_WITH_SIGNATURE_DELTA"
        row.update({
            "signature_activity_count": activity["in"] + activity["out"] + activity["zero"],
            "signature_received_events": activity["in"],
            "signature_sent_events": activity["out"],
            "signature_zero_events": activity["zero"],
            "passive_receipt_events": activity["passive_in"],
            "last_signature_activity_time": activity["last_timestamp"],
            "last_signature_activity_signature": activity["last_signature"],
            "signature_token_amount_decimals": (
                None if activity["mixed_decimals"] else activity["decimals"]),
            "signature_observed_in_raw": (
                None if activity["mixed_decimals"] else str(activity["raw_in"])),
            "signature_observed_out_raw": (
                None if activity["mixed_decimals"] else str(activity["raw_out"])),
            "signature_delta_source": "LOCAL_NORMALIZED_TRANSACTION_TOKEN_BALANCES",
            "sender_cost_basis_usd": None,
            "transfer_counterparty_verified": False,
        })
    rows = sorted(existing.values(), key=lambda x: (
        -(x.get("last_signature_activity_time") or x.get("last_event_time") or 0),
        x["mint"],
    ))
    observed["rows"] = rows
    observed["signature_activity_provenance"] = {
        "signature_rows_scanned": len(signature_rows),
        "classified": dict(sorted(classes.items())),
        "wallet_owned_delta_mints": len(evidence),
        "signature_rows_without_parsed_counterparty_flow": no_transfer_flow,
        "counterparty_flow_is_complete": no_transfer_flow == 0,
        "chain_completeness_verified": False,
    }
    summary = observed["summary"]
    summary["original_trade_or_model_observed"] = (
        summary["total_observed"])
    summary["passive_receipt_only"] = new_passive
    summary["other_account_activity_only"] = new_other
    summary["total_observed"] = len(rows)
    summary["unpriced_new_activity"] = new_passive + new_other
    return observed



def annotate_known_ata_gaps(observed: dict, source: dict | None) -> dict:
    """Dated ATA-vs-owner-accountKeys scope audit, never inferred market trades.

    Legacy v1 evidence is only a total count, never a verified owner-index defect.
    v2 separates pre-index observations from in-window evidence.
    """
    result = dict(observed)
    rows = [dict(row) for row in observed.get("rows", [])]
    result["rows"] = rows
    for row in rows:
        row["owner_index_gap_status"] = "NOT_AUDITED"
        row["owner_index_missing_signatures"] = None
        row["ata_verified_extra_passive_receipts"] = None
        row["ata_gap_source_date"] = None
        row["ata_outside_index_window_signatures"] = None
        row["ata_inside_index_window_signatures"] = None
        row["ata_inwindow_failed_signatures"] = None
        row["ata_inwindow_success_unverified"] = None
    result["ata_gap_source_status"] = "EVIDENCE_NOT_PRESENT"
    if source is None:
        return result
    if (not isinstance(source, dict) or source.get("schema_version") not in (1, 2) or
        source.get("owner_wallet") !=
        "498g1rVnFcnjBjpfw1xyqA1WvgQXUU8RWuELjxkjAayQ" or
        not isinstance(source.get("records"), list) or
        len(source["records"]) > 300):
        raise ValueError("INVALID_ATA_GAP_SOURCE")
    by_mint = {row["mint"]: row for row in rows}
    seen = set()
    schema = source["schema_version"]
    for entry in source["records"]:
        if not isinstance(entry, dict):
            raise ValueError("INVALID_ATA_GAP_RECORD")
        mint = entry.get("mint")
        gaps = entry.get("owner_index_missing_signatures")
        verified = entry.get("verified_extra_passive_receipts")
        if (not isinstance(mint, str) or not 32 <= len(mint) <= 44 or
            mint in seen or type(gaps) is not int or gaps < 1 or
            type(verified) is not int or verified < 0 or verified > gaps or
            not isinstance(entry.get("source_date_utc"), str)):
            raise ValueError("INVALID_ATA_GAP_RECORD")
        if schema == 2:
            outside = entry.get("missing_before_index_start")
            inside = entry.get("missing_during_index_window")
            failed = entry.get("inwindow_failed")
            success_unverified = entry.get("inwindow_success_unverified")
            verified_in = entry.get("verified_extra_passive_receipts")
            if (any(type(v) is not int or v < 0 for v in
                    (outside, inside, failed, success_unverified, verified_in))
                or outside + inside != gaps
                or failed + success_unverified + verified_in > inside
                or entry.get("scope_label") != "ATA_VS_MAIN_WALLET_ACCOUNT_KEYS"):
                raise ValueError("INVALID_ATA_GAP_WINDOW_BREAKDOWN")
        seen.add(mint)
        row = by_mint.get(mint)
        if row is None:
            continue
        row["owner_index_gap_status"] = (
            "DATED_ATA_VS_OWNER_INDEX_SCOPE" if schema == 2
            else "LEGACY_UNSPLIT_ATA_INDEX_EVIDENCE"
        )
        row["owner_index_missing_signatures"] = gaps
        row["ata_verified_extra_passive_receipts"] = verified
        row["ata_gap_source_date"] = entry["source_date_utc"]
        if schema == 2:
            row["ata_outside_index_window_signatures"] = outside
            row["ata_inside_index_window_signatures"] = inside
            row["ata_inwindow_failed_signatures"] = failed
            row["ata_inwindow_success_unverified"] = success_unverified
    result["ata_gap_source_status"] = (
        "DATED_ATA_INDEX_SCOPE_V2" if schema == 2 else
        "LEGACY_UNSPLIT_ATA_INDEX_SCOPE"
    )
    result["summary"] = dict(observed.get("summary", {}))
    result["summary"]["known_ata_index_scope_mints"] = sum(
        row["owner_index_gap_status"] != "NOT_AUDITED" for row in rows)
    return result


def from_sqlite(path: Path, *, person_id: str = PERSON, as_of: int | None = None) -> dict:
    """Read the existing immutable Frank SQLite through open_production_ro."""
    db = open_production_ro(Path(path))
    try:
        states = {}
        for rec in db.execute("SELECT mint,body FROM v1_states WHERE person_id=?", (person_id,)):
            body = _json_obj(rec["body"])
            states[rec["mint"]] = {
                "mint": rec["mint"],
                "local_state": body.get("state", "UNKNOWN"),
                "local_current_raw": body.get("current_raw"),
            }
        agg = defaultdict(lambda: {"buys": 0, "sells": 0, "last": None, "conflicts": set()})
        rows = db.execute(
            """SELECT t.mint,t.side,t.signature,t.block_time,t.body
               FROM trades t INNER JOIN signatures s
                 ON t.wallet=s.wallet AND t.signature=s.signature
               WHERE s.person_id=?
               ORDER BY t.block_time ASC,t.signature ASC,t.rowid ASC""",
            (person_id,),
        )
        seen = {}
        for rec in rows:
            key = (rec["mint"], rec["signature"], rec["side"], rec["block_time"])
            mint = rec["mint"]
            if key in seen:
                if seen[key] != rec["body"]:
                    # One signature may carry multiple distinct swap legs.
                    # Count it once, but do not use an arbitrary leg as a fill.
                    g = agg[mint]
                    g["conflicts"].add(rec["signature"])
                    if g["last"] and g["last"]["signature"] == rec["signature"]:
                        g["last"]["quote_amount"] = None
                continue
            seen[key] = rec["body"]
            side = rec["side"]
            group = agg[mint]
            if side in BUY:
                group["buys"] += 1
            elif side in SELL:
                group["sells"] += 1
            asset, qty = _amount(_json_obj(rec["body"]))
            group["last"] = {
                "signature": rec["signature"], "side": side,
                "block_time": rec["block_time"],
                "quote_asset": asset, "quote_amount": qty,
            }
        seed = []
        for mint in sorted(set(states) | set(agg)):
            s = states.get(mint, {})
            g = agg.get(mint) or {"buys": 0, "sells": 0, "last": None}
            seed.append({
                "mint": mint,
                "local_state": s.get("local_state", "UNKNOWN"),
                "local_current_raw": s.get("local_current_raw"),
                "local_recognized_buy_count": g["buys"],
                "local_recognized_sell_count": g["sells"],
                "latest_recognized_trade": g["last"],
                "conflicting_trade_signatures": len(g.get("conflicts") or []),
                "last_event_multileg_conflict": bool(
                    g.get("last") and g["last"]["signature"] in g.get("conflicts", set())
                ),
            })
        result = from_seed(seed, as_of=as_of)
        signature_records = [
            dict(rec)
            for rec in db.execute(
                "SELECT signature,block_time,body FROM signatures "
                "WHERE person_id=? ORDER BY block_time,signature", (person_id,))
        ]
        if len(signature_records) > 200_000:
            raise ValueError("SIGNATURE_INDEX_OVER_LIMIT")
        result = merge_signature_activity(result, signature_records)
        result["data_source"] = "READ_ONLY_FORWARD_SQLITE"
        return result
    finally:
        db.close()
