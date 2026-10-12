"""Full read-only locally classified Frank trade history for reconciliation.

All monetary values remain local-parser observations. Cashflow totals, when
present, are not realized PnL, and missing transfer/deposit legs prevent a
wallet-wide cost or holding-time claim. Exports whitelisted evidence only.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
from typing import Any

from .db import open_production_ro
from .frank import USDC

_BUYS = {"BUY", "ADD", "REENTRY"}
_SELLS = {"SELL", "EXIT", "SELL_POSITION_UNRESOLVED"}
_FIELDS = (
    "quote_asset", "quote_amount_raw", "quote_decimals", "quote_quantity",
    "quote_normalization", "original_quote", "amount_predicate",
    "quote_usdc_status", "quote_usdc_equivalent", "token_amount_raw",
    "token_decimals", "position_after_raw", "route_amount_semantics",
    "route_intermediate_assets", "source_slot", "program_id",
)
MAX_RECORDS = 250_000


def _body(obj: str | dict | None) -> dict:
    try:
        val = obj if isinstance(obj, dict) else json.loads(obj or "{}")
        return val if isinstance(val, dict) else {}
    except (TypeError, ValueError):
        return {}


def _read_decimal(raw: Any, decimals: Any) -> str | None:
    try:
        n = int(decimals)
        if n < 0 or n > 18 or not str(raw).isascii() or not str(raw).isdecimal():
            return None
        value = Decimal(str(raw)) / (Decimal(10) ** n)
        return str(value.quantize(Decimal(1).scaleb(-n))) if value.is_finite() and value >= 0 else None
    except (InvalidOperation, ValueError, TypeError, OverflowError):
        return None


def _quote(body: dict) -> dict:
    if body.get("quote_normalization"):
        # A synthetic USDC shadow has a separate original quote. Never treat
        # SOL->USDC event-time estimation as direct USDC received or paid.
        orig = body.get("original_quote")
        if not isinstance(orig, dict):
            return {"asset": None, "quantity": None, "status": "NORMALIZED_ORIGINAL_MISSING"}
        asset = orig.get("quote_asset")
        quantity = orig.get("quote_quantity")
        try:
            q = Decimal(str(quantity))
            qty = str(q) if q.is_finite() and q >= 0 else None
        except (InvalidOperation, ValueError):
            qty = None
        return {"asset": asset, "quantity": qty, "status": "ORIGINAL_QUOTE_NOT_USDC_DIRECT"}
    asset = body.get("quote_asset")
    qty = _read_decimal(body.get("quote_amount_raw"), body.get("quote_decimals"))
    predicate = body.get("amount_predicate")
    status = (
        "LOCAL_USDC_DIRECT_PREDICATE"
        if asset == USDC and qty is not None and predicate in (None, "USDC_DIRECT_NUMERIC")
           and not body.get("route_intermediate_assets")
        else "QUOTE_UNRESOLVED_OR_NON_USDC"
    )
    return {"asset": asset, "quantity": qty, "status": status}


def export_history(path: Path, *, person_id: str = "frank") -> dict:
    db = open_production_ro(path)
    try:
        window = db.execute(
            "SELECT MIN(block_time) AS start, MAX(block_time) AS finish, COUNT(*) AS total "
            "FROM signatures WHERE person_id=?", (person_id,)).fetchone()
        rows = db.execute(
            """SELECT t.wallet,t.signature,t.mint,t.episode_id,t.block_time,
                      t.side,t.body AS trade_body,s.body AS signature_body
                 FROM trades t JOIN signatures s
                   ON s.wallet=t.wallet AND s.signature=t.signature
                 WHERE s.person_id=?
                 ORDER BY t.block_time,t.signature,t.mint,t.rowid""", (person_id,),
        )
        records = []
        duplicates = 0
        dedupe: set[str] = set()
        by_mint = defaultdict(lambda: {
            "recognized_buys": 0, "recognized_sells": 0,
            "local_usdc_buy_outflow": Decimal(0),
            "local_usdc_sell_inflow": Decimal(0),
            "unpriced_or_ambiguous_legs": 0,
            "last_time": None, "has_multileg_conflict": False,
        })
        by_tx: dict[tuple[str,str,str,int], set[tuple]] = defaultdict(set)
        for row in rows:
            if len(records) >= MAX_RECORDS:
                raise ValueError("LOCAL_TRADE_INDEX_OVER_SAFETY_LIMIT")
            body = _body(row["trade_body"])
            sig = _body(row["signature_body"])
            q = _quote(body)
            native_qty = _read_decimal(body.get("token_amount_raw"), body.get("token_decimals"))
            raw_keep = {k: body[k] for k in _FIELDS if k in body and k != "original_quote"}
            if isinstance(body.get("original_quote"), dict):
                raw_keep["original_quote"] = {
                    k: body["original_quote"].get(k)
                    for k in ("quote_asset","quote_quantity")
                }
            # No raw signature body, local paths or access credentials enter
            # exported records. Even whitelisted nested route metadata is bounded
            # to small public identifiers only.
            route = raw_keep.get("route_intermediate_assets")
            if isinstance(route, list):
                raw_keep["route_intermediate_assets"] = [
                    t for t in route[:12] if isinstance(t, str) and len(t) <= 48
                ]
            evidence = {
                "signature": row["signature"], "wallet": row["wallet"],
                "mint": row["mint"], "episode_id": row["episode_id"],
                "block_time": row["block_time"], "side": row["side"],
                "local_signature_classification": sig.get("classification"),
                "observed_quote": q, "observed_token_quantity": native_qty,
                "trade_raw_fields": raw_keep, "provenance": "LOCAL_FRANK_INDEX_ONLY",
            }
            encoded = json.dumps(evidence, sort_keys=True, ensure_ascii=False, default=str)
            fingerprint = hashlib.sha256(encoded.encode()).hexdigest()
            if fingerprint in dedupe:
                duplicates += 1
                continue
            dedupe.add(fingerprint)
            txkey = (row["signature"], row["mint"], row["side"], int(row["block_time"]))
            by_tx[txkey].add((q["asset"], q["quantity"], native_qty))
            records.append(evidence)
            group = by_mint[row["mint"]]
            group["last_time"] = int(row["block_time"])
            if row["side"] in _BUYS:
                group["recognized_buys"] += 1
            elif row["side"] in _SELLS:
                group["recognized_sells"] += 1
            if q["status"] == "LOCAL_USDC_DIRECT_PREDICATE":
                if row["side"] in _BUYS:
                    group["local_usdc_buy_outflow"] += Decimal(q["quantity"])
                elif row["side"] in _SELLS:
                    group["local_usdc_sell_inflow"] += Decimal(q["quantity"])
            else:
                group["unpriced_or_ambiguous_legs"] += 1

        conflicts = {key for key, legs in by_tx.items() if len(legs) > 1}
        # Aggregates containing multi-leg ambiguity must not imply verified
        # usable trading cashflow or PnL, even if gross figures are calculable.
        for sig_id, mint, side, _ in conflicts:
            by_mint[mint]["has_multileg_conflict"] = True
        summary = {}
        for mint, v in sorted(by_mint.items()):
            summary[mint] = {
                "recognized_buy_legs": v["recognized_buys"],
                "recognized_sell_legs": v["recognized_sells"],
                "direct_local_usdc_buy_outflow": str(v["local_usdc_buy_outflow"]),
                "direct_local_usdc_sell_inflow": str(v["local_usdc_sell_inflow"]),
                "unpriced_or_ambiguous_legs": v["unpriced_or_ambiguous_legs"],
                "has_multileg_conflict": v["has_multileg_conflict"],
                "last_indexed_trade_time": v["last_time"],
                "profitability_verified": False,
                "pnl_usd": None,
            }
        return {
            "schema_version": 1,
            "source_scope": "COMPLETE_LOCAL_RECOGNIZED_TRADES_NOT_FULL_CHAIN",
            "person_id": person_id,
            "record_count": len(records),
            "duplicate_identical_rows_omitted": duplicates,
            "distinct_mints": len(summary),
            "signature_index_window": {
                "oldest_block_time": window["start"],
                "newest_block_time": window["finish"],
                "local_signatures_count": window["total"],
            },
            "local_signature_history_chain_complete": False,
            "known_fee_and_transfer_costs_complete": False,
            "realized_pnl_usd": None,
            "wallet_usd_nav": None,
            "multileg_conflicting_trade_keys": len(conflicts),
            "records": records, "per_mint_cashflow_observations": summary,
            "limitations": [
                "Cashflow sums are local parser observations; not verified cost basis or net profit.",
                "Prior buys, deposits, rewards, sales and passive transfers may be absent from local recognized-trades table.",
                "Native SOL fees, time-aligned USD prices, and all routed swaps require independent reconstruction.",
                "Even complete local SQLite results cannot establish global wallet history completeness.",
            ],
        }
    finally:
        db.close()
