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
from .wallet_chain_capture import PROGRAMS


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


def _valid_unavailable_dual_program_capture(document: dict) -> bool:
    """Accept only the exact slotless shape capture_owner emits on two failures.

    A source SHA guarantees archived bytes, *not* that two missing rows
    actually identify the two different token programs. These checks prevent
    duplicate/unknown program error entries from becoming a false observation.
    """
    missing = document.get("missing")
    if (document.get("status") != "PARTIAL_SOURCE"
            or document.get("both_programs_observed") is not False
            or document.get("slot_min") is not None
            or document.get("slot_max") is not None
            or document.get("program_coverage") != []
            or document.get("mints") != []
            or type(document.get("account_count")) is not int
            or document["account_count"] != 0
            or type(document.get("mint_count_observed")) is not int
            or document["mint_count_observed"] != 0
            or document.get("same_slot_atomic") is not False
            or document.get("all_history_complete") is not False
            or document.get("wallet_total_balance_verified") is not False
            or document.get("person_beneficial_ownership_verified") is not False
            or document.get("wallet_nav_usd") is not None
            or document.get("realized_pnl_usd") is not None
            or not isinstance(missing, list)
            or len(missing) != len(PROGRAMS)):
        return False
    programs = []
    for failure in missing:
        if not isinstance(failure, dict) or set(failure) != {
                "program_id", "reason", "error_type"}:
            return False
        err_type = failure["error_type"]
        if (not isinstance(failure["program_id"], str)
                or failure["program_id"] not in PROGRAMS
                or failure["reason"] != "TOKEN_ACCOUNT_QUERY_UNAVAILABLE"
                or not isinstance(err_type, str) or not err_type.isidentifier()
                or len(err_type) > 128):
            return False
        programs.append(failure["program_id"])
    return set(programs) == set(PROGRAMS) and len(set(programs)) == len(PROGRAMS)


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
    newest_slotted = None
    newest_slotless_failure = None
    candidate_count = 0
    # Read the entire archive in bounded SQLite batches. rowid is import
    # order, NOT chain order, and cannot be used as a 100-row prefilter.
    for doc in store.iter_wallet_captures(wallet):
        if doc.get("wallet") != wallet or doc.get("network") != "solana-mainnet":
            raise ValueError("CAPTURE_SOURCE_WALLET_MISMATCH")
        if _fingerprint(doc) != doc.get("capture_sha256"):
            raise ValueError("CAPTURE_SOURCE_HASH_MISMATCH")
        stamp = _parse_time(doc.get("observed_at_utc"))
        if stamp > as_of:
            continue
        candidate_count += 1
        slot = doc.get("slot_max")
        if slot is None:
            # capture_owner() legitimately archives two failed RPC calls
            # with no observed slot. It is an attempt, NOT corrupt chain
            # evidence. Never use a previously positive wallet snapshot
            # if the latest attempt failed completely.
            if not _valid_unavailable_dual_program_capture(doc):
                raise ValueError("OWNER_CAPTURE_SLOTLESS_PROGRAM_EVIDENCE_INVALID")
            if (newest_slotless_failure is None
                    or stamp > newest_slotless_failure[0]):
                newest_slotless_failure = (stamp, doc)
            continue
        if type(slot) is not int or slot <= 0:
            raise ValueError("OWNER_CAPTURE_SLOT_INVALID")
        if (newest_slotted is None
                or (slot, stamp) > (newest_slotted[0], newest_slotted[1])):
            newest_slotted = (slot, stamp, doc)

    # A newer no-slot failure is evidence that the latest observation is
    # UNKNOWN, not permission to resurrect an older successfully captured
    # position. An older failure cannot poison a later healthy capture.
    failure_is_latest = (newest_slotless_failure is not None and
        (newest_slotted is None or
         newest_slotless_failure[0] >= newest_slotted[1]))
    if failure_is_latest:
        latest = newest_slotless_failure[1]
    else:
        latest = newest_slotted[2] if newest_slotted else None
    latest_has_no_slot = failure_is_latest
    age = None
    fresh = False
    observed = {}
    coverage = False
    if latest is not None:
        age = max(0, int((as_of - _parse_time(latest["observed_at_utc"])).total_seconds()))
        fresh = age <= max_age_seconds
        coverage = (not latest_has_no_slot and
                    latest.get("both_programs_observed") is True and
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
        elif latest_has_no_slot:
            status, raw, dec, accounts = "SOURCE_ATTEMPT_FAILED_NO_SLOT", None, None, []
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
        "capture_candidates_examined": candidate_count,
        "source_attempt_failed_no_slot": latest_has_no_slot,
        "source_observation_status": latest.get("status") if latest else "NO_CAPTURE",
        "both_programs_observed": coverage,
        "same_slot_atomic": False,
        # This reports two successful RPC queries, not a whole-wallet
        # atomic balance, a validated 32-mint registry or complete history.
        "dual_program_queries_observed_non_atomic": bool(
            latest is not None and fresh and coverage),
        "target_roster_independently_verified": False,
        "status_counts": counts,
        "mints": rows,
        "wallet_nav_usd": None,
        "person_beneficial_ownership_verified": False,
        "history_complete": False,
        "current_live_portfolio_verified": False,
    }
