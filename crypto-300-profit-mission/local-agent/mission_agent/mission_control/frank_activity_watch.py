"""Source-backed Frank trading activity for read-only Dashboard research.

Not a V1 ACCUMULATION/MULTIPLE signal, prior alert delivery confirmation,
live chain balance, price assessment, user order or notification. No I/O here.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Mapping
import re

_BASE58 = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,88}$")
_BUY = frozenset(("BUY", "ADD", "REENTRY"))
_SELL = frozenset(("SELL", "EXIT", "SELL_POSITION_UNRESOLVED"))
_ALL = _BUY | _SELL


def summarize_activity(
    trades: list[Mapping[str, Any]],
    candidates: list[Mapping[str, Any]],
    *,
    as_of: float,
) -> dict[str, Any]:
    """Keep real signed sales even when old mints have left current candidates.

    Source is the existing FrankReader.recent_trades(100), not a fresh scan.
    Source row count and gaps must never imply full-chain coverage.
    """
    if not isinstance(trades, list) or len(trades) > 100:
        raise ValueError("INVALID_BOUNDED_TRADE_SOURCE")
    if not isinstance(candidates, list):
        raise ValueError("INVALID_CANDIDATE_SOURCE")
    if (not isinstance(as_of, (int, float)) or isinstance(as_of, bool)
            or not 1_600_000_000 < as_of < 4_000_000_000):
        raise ValueError("INVALID_CAPTURE_TIME")
    current_mints = {
        c["mint"] for c in candidates
        if isinstance(c, Mapping) and isinstance(c.get("mint"), str)
    }
    seen: dict[str, tuple[str, str, int]] = {}
    skipped: Counter[str] = Counter()
    rows: list[dict[str, Any]] = []
    for trade in trades:
        if not isinstance(trade, Mapping):
            skipped["INVALID_ROW"] += 1
            continue
        signature, mint, side = (
            trade.get("signature"), trade.get("mint"), trade.get("side")
        )
        stamp = trade.get("block_time")
        body = trade.get("body")
        if (
            not isinstance(signature, str) or not _BASE58.fullmatch(signature)
            or not isinstance(mint, str) or not _BASE58.fullmatch(mint)
            or side not in _ALL or isinstance(stamp, bool)
            or not isinstance(stamp, (float, int))
            or stamp < 1_600_000_000 or stamp > as_of
            or not isinstance(body, Mapping)
        ):
            skipped["SOURCE_FIELDS_NOT_VERIFIED"] += 1
            continue
        if body.get("direction") != ("BUY" if side in _BUY else "SELL"):
            skipped["SOURCE_DIRECTION_CONFLICT"] += 1
            continue
        identity = (mint, side, int(stamp))
        if signature in seen:
            if seen[signature] != identity:
                raise ValueError("CONFLICTING_SAME_SIGNATURE_FACTS")
            skipped["DUPLICATE_SIGNATURE"] += 1
            continue
        seen[signature] = identity
        rows.append({
            "mint": mint,
            "signature": signature,
            "source_side": side,
            "block_time": int(stamp),
            "kind": ("OBSERVED_SELL_RESEARCH" if side in _SELL
                     else "OBSERVED_BUY_RESEARCH"),
            "in_current_candidate_mint_set": mint in current_mints,
            "position_status": "CURRENT_BALANCE_NOT_VERIFIED",
            "linked_prior_v1_signal": "NOT_VERIFIED",
            "recipient_alert_delivery": "NOT_VERIFIED",
            "market_reference": "NOT_REQUESTED",
            "order_amount_usdc": None,
            "send_allowed": False,
        })
    rows.sort(key=lambda x: (-x["block_time"], x["signature"]))
    return {
        "status": "LOCAL_SOURCE_ACTIVITY_RESEARCH_ONLY",
        "scope": "LATEST_100_INDEXED_TRADES_NOT_COMPLETE_CHAIN",
        "captured_at": as_of,
        "source_rows_considered": len(trades),
        "displayed_transactions": len(rows),
        "counts": {
            "buy_category": sum(x["source_side"] in _BUY for x in rows),
            "sell_category": sum(x["source_side"] in _SELL for x in rows),
            "sell_outside_current_candidate_mint_set": sum(
                x["source_side"] in _SELL
                and not x["in_current_candidate_mint_set"] for x in rows
            ),
            "sell_position_unresolved": sum(
                x["source_side"] == "SELL_POSITION_UNRESOLVED" for x in rows
            ),
            "excluded": dict(skipped),
        },
        "rows": rows,
        "notification_authorized": False,
        "chain_completeness_verified": False,
        "user_order_amount_usdc": None,
    }
