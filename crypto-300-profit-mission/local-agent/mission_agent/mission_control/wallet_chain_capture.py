"""A05 manual, read-only Solana owner token-account capture.

No background polling, production SQLite access or wallet signing. Both token
programs are queried explicitly at finalized commitment. Two RPC calls are not
atomic: their slots are retained separately and never promoted to a single
verified same-slot portfolio balance.

The RPC transport is injected for offline reproducible tests. Failures leave
PARTIAL_SOURCE coverage and NULL whole-wallet balances, never zero.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
from typing import Callable

from .person_registry import _solana_pubkey_32_bytes


SPL_TOKEN_PROGRAM = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
TOKEN_2022_PROGRAM = "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb"
PROGRAMS = (SPL_TOKEN_PROGRAM, TOKEN_2022_PROGRAM)
RpcRequest = Callable[[str, list], dict]


class ChainCaptureError(ValueError):
    """Invalid or contradictory chain evidence; no silent partial acceptance."""


def _uint(value: object, field: str, *, positive: bool = False) -> int:
    if type(value) is not int or value < (1 if positive else 0):
        raise ChainCaptureError("INVALID_" + field)
    return value


def _raw(value: object) -> str:
    if not isinstance(value, str) or not value.isascii() or not value.isdecimal():
        raise ChainCaptureError("INVALID_RAW_AMOUNT")
    return str(int(value))


def _pubkey(value: object, field: str) -> str:
    if not isinstance(value, str) or not _solana_pubkey_32_bytes(value):
        raise ChainCaptureError("INVALID_" + field)
    return value


def _fingerprint(document: dict) -> str:
    return hashlib.sha256(json.dumps(
        document, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")).hexdigest()


def normalize_owner_program(owner: str, program: str, response: dict) -> dict:
    """Validate one getTokenAccountsByOwner result and preserve its RPC slot."""
    _pubkey(owner, "WALLET")
    if program not in PROGRAMS:
        raise ChainCaptureError("TOKEN_PROGRAM_UNSUPPORTED")
    if not isinstance(response, dict):
        raise ChainCaptureError("RPC_RESULT_INVALID")
    # Caller supplies the RPC result body; a JSON-RPC error is never an empty
    # account list. Keep all records only when a full valid value array exists.
    if "error" in response:
        raise ChainCaptureError("RPC_RETURNED_ERROR")
    body = response.get("result", response)
    if not isinstance(body, dict) or not isinstance(body.get("value"), list):
        raise ChainCaptureError("RPC_RESULT_INCOMPLETE")
    context = body.get("context")
    if not isinstance(context, dict):
        raise ChainCaptureError("RPC_CONTEXT_MISSING")
    slot = _uint(context.get("slot"), "CONTEXT_SLOT", positive=True)
    rows = []
    seen = set()
    for entry in body["value"]:
        if not isinstance(entry, dict):
            raise ChainCaptureError("TOKEN_ACCOUNT_ENTRY_INVALID")
        account = entry.get("account")
        data = account.get("data") if isinstance(account, dict) else None
        parsed = data.get("parsed") if isinstance(data, dict) else None
        info = parsed.get("info") if isinstance(parsed, dict) else None
        if (not isinstance(info, dict) or parsed.get("type") != "account"
                or account.get("owner") != program
                or info.get("owner") != owner):
            raise ChainCaptureError("TOKEN_ACCOUNT_OWNER_MISMATCH")
        address = _pubkey(entry.get("pubkey"), "TOKEN_ACCOUNT_PUBKEY")
        mint = _pubkey(info.get("mint"), "MINT_PUBKEY")
        token_amount = info.get("tokenAmount")
        if not isinstance(token_amount, dict):
            raise ChainCaptureError("TOKEN_ACCOUNT_UNITS_MISSING")
        raw = _raw(token_amount.get("amount"))
        decimals = _uint(token_amount.get("decimals"), "TOKEN_DECIMALS")
        if decimals > 18:
            raise ChainCaptureError("TOKEN_DECIMALS_OUT_OF_SCOPE")
        state = info.get("state")
        if state not in {"initialized", "frozen"}:
            raise ChainCaptureError("TOKEN_ACCOUNT_STATE_UNRECOGNIZED")
        if address in seen:
            raise ChainCaptureError("DUPLICATE_TOKEN_ACCOUNT")
        seen.add(address)
        rows.append({
            "token_account": address, "mint": mint, "program_id": program,
            "raw_amount": raw, "decimals": decimals, "state": state,
            "owner": owner, "slot": slot,
        })
    rows.sort(key=lambda x: x["token_account"])
    return {
        "wallet": owner, "program_id": program, "slot": slot,
        "commitment": "finalized", "account_count": len(rows),
        "accounts": rows,
        "source": "SOLANA_GET_TOKEN_ACCOUNTS_BY_OWNER",
    }


def capture_owner(owner: str, rpc_request: RpcRequest, *,
                  min_context_slot: int | None = None) -> dict:
    """Explicit single-pass finalized RPC capture with useful partial results.

    A successful SPL query does not compensate for a failed Token-2022 query.
    No run ever claims complete portfolio valuation, profitable PnL, or owner
    control of the associated real-world person.
    """
    _pubkey(owner, "WALLET")
    if min_context_slot is not None:
        _uint(min_context_slot, "MIN_CONTEXT_SLOT")
    observations, missing = [], []
    lower_bound = min_context_slot
    for program in PROGRAMS:
        config = {"encoding": "jsonParsed", "commitment": "finalized"}
        if lower_bound is not None:
            config["minContextSlot"] = lower_bound
        try:
            body = rpc_request("getTokenAccountsByOwner",
                               [owner, {"programId": program}, config])
            normalized = normalize_owner_program(owner, program, body)
        except (ChainCaptureError, OSError, RuntimeError, TimeoutError,
                TypeError, ValueError, KeyError) as exc:
            # Explicit class/code only; never serialize provider URL, secret,
            # raw exception or partial invalid RPC payload to public reports.
            missing.append({"program_id": program,
                            "reason": "TOKEN_ACCOUNT_QUERY_UNAVAILABLE",
                            "error_type": type(exc).__name__})
            continue
        observations.append(normalized)
        lower_bound = max(lower_bound or 0, normalized["slot"])

    complete = len(observations) == len(PROGRAMS)
    seen_accounts = set()
    by_mint = defaultdict(list)
    for observation in observations:
        for account in observation["accounts"]:
            token_account = account["token_account"]
            if token_account in seen_accounts:
                raise ChainCaptureError("CROSS_PROGRAM_DUPLICATE_TOKEN_ACCOUNT")
            seen_accounts.add(token_account)
            by_mint[account["mint"]].append(account)
    mints = []
    for mint, accounts in sorted(by_mint.items()):
        decimals = {account["decimals"] for account in accounts}
        if len(decimals) != 1:
            raise ChainCaptureError("MINT_DECIMALS_CONFLICT")
        raw_total = sum(int(a["raw_amount"]) for a in accounts)
        account_slots = [a["slot"] for a in accounts]
        # Even if both programs return matching context slots, they are
        # separate RPC calls. Do not invent atomic read consistency.
        mints.append({
            "mint": mint,
            "raw_amount_observed_sum": str(raw_total),
            "decimals": next(iter(decimals)),
            "quantity_observed_sum": str(Decimal(raw_total) /
                                         (Decimal(10) ** next(iter(decimals)))),
            "token_accounts": accounts,
            "slot_min": min(account_slots), "slot_max": max(account_slots),
            "balance_single_atomic_slot_verified": False,
            "complete_program_coverage": complete,
            "usd_value": None, "cost_basis_usd": None, "pnl_usd": None,
        })
    all_slots = [o["slot"] for o in observations]
    result = {
        "schema_version": 1, "network": "solana-mainnet",
        "wallet": owner, "status": "BOTH_PROGRAMS_OBSERVED_NON_ATOMIC" if complete else "PARTIAL_SOURCE",
        "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "program_coverage": observations, "missing": missing,
        "account_count": len(seen_accounts), "mint_count_observed": len(mints),
        "mints": mints,
        "slot_min": min(all_slots) if all_slots else None,
        "slot_max": max(all_slots) if all_slots else None,
        "both_programs_observed": complete,
        "same_slot_atomic": False, "all_history_complete": False,
        "person_beneficial_ownership_verified": False,
        "wallet_total_balance_verified": False,
        "wallet_nav_usd": None, "realized_pnl_usd": None,
    }
    result["capture_sha256"] = _fingerprint(result)
    return result
