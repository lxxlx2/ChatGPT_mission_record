"""Reconcile a dated, externally captured owner/mint balance snapshot with Frank's
read-only observed watchlist. Never interpret a V1 model OPEN as on-chain proof.

No RPC calls, writer access, trading, alarms, local side effects or price guesses.
A source's finalized slot supports point-in-time units, not real-time USD NAV.
"""
from __future__ import annotations

from copy import deepcopy
from decimal import Decimal
from typing import Any

FRANK_WALLET = "498g1rVnFcnjBjpfw1xyqA1WvgQXUU8RWuELjxkjAayQ"
_SOURCE_STATUS = "VERIFIED_POINT_IN_TIME_MINT_FILTERED_SOLANA_ACCOUNT_READS"


class InventoryEvidenceError(ValueError):
    pass


def _positive_slot(value: Any) -> int:
    if type(value) is not int or value <= 0:
        raise InventoryEvidenceError("INVALID_SLOT")
    return value


def _validated_record(row: dict) -> dict:
    if not isinstance(row, dict):
        raise InventoryEvidenceError("BALANCE_ROW_INVALID")
    mint = row.get("mint")
    if not isinstance(mint, str) or not 32 <= len(mint) <= 44:
        raise InventoryEvidenceError("INVALID_MINT")
    raw = row.get("raw_amount")
    if not isinstance(raw, str) or not raw.isascii() or not raw.isdecimal():
        raise InventoryEvidenceError("INVALID_RAW_TOKEN_UNITS")
    decimals = row.get("decimals")
    if type(decimals) is not int or decimals < 0 or decimals > 18:
        raise InventoryEvidenceError("INVALID_DECIMALS")
    slot = _positive_slot(row.get("slot"))
    if row.get("source") != "ALCHEMY_SOLANA_FINALIZED":
        raise InventoryEvidenceError("UNSUPPORTED_BALANCE_SOURCE")
    amount = Decimal(raw) / (Decimal(10) ** decimals)
    return {
        "mint": mint,
        "raw_amount": raw,
        "decimals": decimals,
        "amount": str(amount),
        "slot": slot,
        "nonzero": bool(int(raw)),
    }


def reconcile_watchlist(watch: dict, evidence: dict) -> dict:
    """Join watch metadata with one-mint-filtered snapshot evidence.

    This imported evidence was queried previously and should be dated/slot-tagged;
    users of the result must still check whether it has become stale.
    """
    if not isinstance(watch, dict) or not isinstance(watch.get("rows"), list):
        raise InventoryEvidenceError("WATCHLIST_MISSING")
    if not isinstance(evidence, dict):
        raise InventoryEvidenceError("EVIDENCE_MISSING")
    if (evidence.get("wallet") != FRANK_WALLET or
        evidence.get("commitment") != "finalized" or
        evidence.get("status") != _SOURCE_STATUS or
        evidence.get("network") != "solana-mainnet" or
        not isinstance(evidence.get("records"), list)):
        raise InventoryEvidenceError("EVIDENCE_IDENTITY_OR_FINALITY_UNVERIFIED")
    parsed: dict[str, dict] = {}
    for row in evidence["records"]:
        item = _validated_record(row)
        if item["mint"] in parsed:
            raise InventoryEvidenceError("DUPLICATE_MINT_WITHIN_SNAPSHOT")
        parsed[item["mint"]] = item

    result = deepcopy(watch)
    result["source_scope"] = watch.get("scope", "LOCAL_INDEX_ONLY_NOT_COMPLETE_CHAIN")
    result["chain_completeness_verified"] = False
    result["snapshot_status"] = "DATED_POINT_IN_TIME_NOT_LIVE"
    result["snapshot_date_bangkok"] = evidence.get("date_bangkok")
    result["snapshot_min_slot"] = min((r["slot"] for r in parsed.values()), default=None)
    result["snapshot_max_slot"] = max((r["slot"] for r in parsed.values()), default=None)
    result["snapshot_provider_claim"] = "ALCHEMY_SOLANA_FINALIZED"
    result["market_values_verified"] = False
    result["wallet_total_nav_usd"] = None

    observed_mints: set[str] = set()
    stats = {
        "observed_rows": len(result["rows"]),
        "snapshot_mints": len(parsed),
        "matched_mints": 0,
        "nonzero_at_snapshot": 0,
        "zero_at_snapshot": 0,
        "unresolved_without_snapshot": 0,
        "model_closed_with_remaining_tokens": 0,
        "model_unknown_with_remaining_tokens": 0,
        "model_open_with_zero_tokens": 0,
        "model_uncertain_nonzero": 0,
        "additional_positive_outside_observed_watchlist": 0,
    }
    for row in result["rows"]:
        mint = row.get("mint")
        observed_mints.add(mint)
        item = parsed.get(mint)
        # "current_chain_balance_verified" is defined only for a true live RPC
        # read at response time. An imported snapshot is always historical.
        row["current_chain_balance_verified"] = False
        row["market_value_usd"] = None
        row["pnl_usd"] = None
        if item is None:
            row["snapshot_inventory_state"] = "NOT_QUERIED_IN_SNAPSHOT"
            stats["unresolved_without_snapshot"] += 1
            continue
        row.update({
            "snapshot_inventory_state": "NONZERO_AT_SLOT" if item["nonzero"] else "ZERO_AT_SLOT",
            "snapshot_token_quantity": item["amount"],
            "snapshot_raw_balance": item["raw_amount"],
            "snapshot_decimals": item["decimals"],
            "snapshot_verified_slot": item["slot"],
            "snapshot_source": "EXPORTED_FINALIZED_RPC_RECORD",
            "snapshot_usd_status": "UNPRICED",
        })
        stats["matched_mints"] += 1
        stats["nonzero_at_snapshot" if item["nonzero"] else "zero_at_snapshot"] += 1
        state = row.get("local_model_state")
        if item["nonzero"] and state == "CLOSED":
            row["model_chain_disagreement"] = "MODEL_CLOSED_WITH_RESIDUAL_BALANCE"
            stats["model_closed_with_remaining_tokens"] += 1
        elif item["nonzero"] and state == "UNKNOWN":
            row["model_chain_disagreement"] = "MODEL_UNKNOWN_WITH_POSITIVE_BALANCE"
            stats["model_unknown_with_remaining_tokens"] += 1
        elif not item["nonzero"] and state == "OPEN":
            row["model_chain_disagreement"] = "MODEL_OPEN_WITH_ZERO_BALANCE"
            stats["model_open_with_zero_tokens"] += 1
        elif item["nonzero"] and state == "INVENTORY_UNDETERMINED":
            row["model_chain_disagreement"] = "MODEL_UNCERTAIN_WITH_POSITIVE_BALANCE"
            stats["model_uncertain_nonzero"] += 1
        else:
            row["model_chain_disagreement"] = None
    for mint, item in parsed.items():
        if mint not in observed_mints and item["nonzero"]:
            stats["additional_positive_outside_observed_watchlist"] += 1
    result["snapshot_reconciliation"] = stats
    return result
