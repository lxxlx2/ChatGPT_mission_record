"""A05/F02 research-only latest immutable owner-capture inventory projection.

Select exactly one latest source capture. Never resurrect a token holding from
a previous snapshot if a more recent observation is missing it. No RPC,
current-price, signal, Gmail or protected production SQLite dependencies.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json

from .person_registry import _solana_pubkey_32_bytes


def _is_address(value: object) -> bool:
    return isinstance(value, str) and _solana_pubkey_32_bytes(value)


def _parse_time(value: object) -> datetime:
    if not isinstance(value, str):
        raise ValueError("OWNER_CAPTURE_TIME_INVALID")
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("OWNER_CAPTURE_TIME_INVALID") from exc
    if dt.tzinfo is None:
        raise ValueError("OWNER_CAPTURE_TIME_INVALID")
    return dt.astimezone(timezone.utc)


def _fingerprint(document: dict) -> str:
    obj = {k: v for k, v in document.items() if k != "capture_sha256"}
    serialized = json.dumps(obj, sort_keys=True, separators=(",", ":"),
                            ensure_ascii=False)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def latest_inventory(store, *, wallet: str, mints: list[str],
                     as_of_utc: datetime, max_age_seconds: int = 300) -> dict:
    """Return observed balances, never promote this evidence to live positions.

    mints are explicit exact Solana addresses (e.g. 32 frozen target mints).
    The most recent capture is selected *before* searching for a mint. A
    partial two-program source cannot prove an absent mint is zero.
    """
    if not _is_address(wallet):
        raise ValueError("RESEARCH_WALLET_INVALID")
    if (not isinstance(mints, list) or not mints or len(mints) > 128
            or any(not _is_address(m) for m in mints)
            or len(set(mints)) != len(mints)):
        raise ValueError("TARGET_MINTS_INVALID")
    if not isinstance(as_of_utc, datetime) or as_of_utc.tzinfo is None:
        raise ValueError("AS_OF_UTC_INVALID")
    if type(max_age_seconds) is not int or not 1 <= max_age_seconds <= 86400:
        raise ValueError("MAX_AGE_INVALID")
    as_of = as_of_utc.astimezone(timezone.utc)
    snapshots = store.read_wallet_captures(wallet, limit=100)
    valid = []
    for doc in snapshots:
        if doc.get("wallet") != wallet or doc.get("network") != "solana-mainnet":
            continue
        if _fingerprint(doc) != doc.get("capture_sha256"):
            raise ValueError("CAPTURE_SOURCE_HASH_MISMATCH")
        slot = doc.get("slot_max")
        if type(slot) is not int or slot <= 0:
            raise ValueError("OWNER_CAPTURE_SLOT_INVALID")
        stamp = _parse_time(doc.get("observed_at_utc"))
        if stamp <= as_of:
            valid.append((slot, stamp, doc))
    # Source slots are the chain-state order. Never prefer an older complete
    # capture over a newer partial capture merely because it has more rows.
    latest = max(valid, key=lambda x: (x[0], x[1]))[2] if valid else None
    age = None
    fresh = False
    observed = {}
    coverage = False
    if latest is not None:
        age = max(0, int((as_of - _parse_time(latest["observed_at_utc"])).total_seconds()))
        fresh = age <= max_age_seconds
        coverage = latest.get("both_programs_observed") is True and (
            latest.get("status") == "BOTH_PROGRAMS_OBSERVED_NON_ATOMIC")
        for row in latest.get("mints", []):
            mint = row.get("mint")
            if mint in observed:
                raise ValueError("CAPTURE_DUPLICATE_MINT")
            if mint and not _is_address(mint):
                raise ValueError("CAPTURE_MINT_INVALID")
            observed[mint] = row
    rows = []
    for mint in mints:
        item = observed.get(mint)
        if latest is None:
            status, raw, dec, accounts = "NO_CAPTURE", None, None, []
        elif not fresh:
            status, raw, dec, accounts = "STALE_SNAPSHOT", None, None, []
        elif item is not None:
            status = ("OBSERVED_IN_DUAL_PROGRAM_SCAN_NON_ATOMIC" if coverage
                      else "PARTIAL_PROGRAM_OBSERVED_NOT_WHOLE_BALANCE")
            raw, dec = item.get("raw_amount_observed_sum"), item.get("decimals")
            accounts = item.get("token_accounts") or []
        elif coverage:
            # It is an observed absence in a successful double owner scan,
            # not evidence of selling or an all-history absence.
            status, raw, dec, accounts = "ABSENT_IN_LATEST_DUAL_PROGRAM_SCAN", None, None, []
        else:
            status, raw, dec, accounts = "UNKNOWN_MISSING_PROGRAM", None, None, []
        rows.append({
            "mint": mint,
            "status": status,
            "observed_raw_amount": raw,
            "decimals": dec,
            "token_accounts": accounts,
            "observed_balance_only": raw is not None,
            "historical_sale_confirmed": False,
            "current_live_balance_verified": False,
            "usd_value": None,
            "cost_basis_usd": None,
            "realized_pnl_usd": None,
        })
    counts = {}
    for item in rows:
        counts[item["status"]] = counts.get(item["status"], 0) + 1
    return {
        "schema_version": 1,
        "kind": "RESEARCH_OWNER_LATEST_CAPTURE_INVENTORY_NOT_LIVE",
        "wallet": wallet,
        "target_mint_count": len(mints),
        "target_count_equals_32": len(mints) == 32,
        "as_of_utc": as_of.isoformat(),
        "selected_capture_sha256": latest["capture_sha256"] if latest else None,
        "capture_observed_at_utc": latest["observed_at_utc"] if latest else None,
        "capture_age_seconds": age,
        "capture_fresh": fresh,
        "slot_min": latest.get("slot_min") if latest else None,
        "slot_max": latest.get("slot_max") if latest else None,
        "both_programs_observed": coverage,
        "same_slot_atomic": False,
        "source_complete_for_all_target_mints": latest is not None and fresh and coverage,
        "status_counts": counts,
        "mints": rows,
        "wallet_nav_usd": None,
        "person_beneficial_ownership_verified": False,
        "history_complete": False,
        "current_live_portfolio_verified": False,
    }
