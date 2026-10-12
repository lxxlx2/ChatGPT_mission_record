"""Read-only presentation metadata for the last recorded Frank BUY.

Keep FrankReader.candidates and all frozen signal/decision adapter functions
AST-identical. This helper never alters the upstream event or trading policy.
"""
from __future__ import annotations


def latest_buy_payment_evidence(candidate: dict) -> dict:
    event = next(
        (row for row in reversed(candidate.get("events") or [])
         if isinstance(row, dict) and row.get("direction") == "BUY"),
        None,
    )
    return {
        "latest_buy_amount_predicate": (
            event.get("amount_predicate") if event else candidate.get("latest_buy_amount_predicate")
        ),
        "latest_buy_amount_predicate_reason": (
            event.get("amount_predicate_reason") if event else candidate.get("latest_buy_amount_predicate_reason")
        ),
    }
