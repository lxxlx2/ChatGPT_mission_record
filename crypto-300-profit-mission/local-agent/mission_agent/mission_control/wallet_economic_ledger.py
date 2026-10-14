"""A04 read-only normalized Solana transaction quantity legs.

A token balance delta is not proof of market BUY/SELL. Keep account-index,
mint, owner and instruction ambiguity explicit. The same signature appears
once globally even when two tracked wallets are involved; wallet-perspective
legs are retained without doubling transactions or inventing cost/PnL.
"""
from __future__ import annotations

from collections import defaultdict
import hashlib
import json

from .person_registry import _solana_pubkey_32_bytes


class LedgerEvidenceError(ValueError):
    pass


def _required_key(value, name):
    if not isinstance(value, str) or not _solana_pubkey_32_bytes(value):
        raise LedgerEvidenceError("INVALID_" + name)
    return value


def _uint(value, name):
    if type(value) is not int or value < 0:
        raise LedgerEvidenceError("INVALID_" + name)
    return value


def _hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=False).encode()).hexdigest()


def _balance_map(rows, keys):
    if not isinstance(rows, list):
        raise LedgerEvidenceError("MISSING_TOKEN_BALANCES")
    result = {}
    for raw in rows:
        if not isinstance(raw, dict):
            raise LedgerEvidenceError("INVALID_BALANCE_ROW")
        idx = _uint(raw.get("accountIndex"), "ACCOUNT_INDEX")
        if idx >= len(keys):
            raise LedgerEvidenceError("ACCOUNT_INDEX_OUT_OF_RANGE")
        mint = _required_key(raw.get("mint"), "MINT")
        owner = raw.get("owner")
        if not isinstance(owner, str) or not _solana_pubkey_32_bytes(owner):
            # Do not silently reassign an ATA to its fee payer. Missing owner
            # is unresolved, and is forbidden for tracked owner attribution.
            owner = None
        amount = raw.get("uiTokenAmount")
        if not isinstance(amount, dict):
            raise LedgerEvidenceError("AMOUNT_MISSING")
        number = amount.get("amount")
        decimals = amount.get("decimals")
        if (not isinstance(number, str) or not number.isascii()
                or not number.isdecimal() or type(decimals) is not int
                or not 0 <= decimals <= 18):
            raise LedgerEvidenceError("INVALID_TOKEN_AMOUNT")
        key = (idx, mint)
        if key in result:
            raise LedgerEvidenceError("DUPLICATE_TOKEN_BALANCE_ROW")
        result[key] = {
            "owner": owner, "token_account": keys[idx],
            "mint": mint, "decimals": decimals, "raw": int(number),
            "account_index": idx,
        }
    return result


def _native_sol_coverage(meta, message, keys, tracked):
    """Differentiate ordinary fee-only token transactions from native SOL flow.

    This is a wallet-scoped *observation*, not a proven SOL cost or an
    economic transfer classification. Missing balance arrays remain unknown.
    """
    before, after = meta.get("preBalances"), meta.get("postBalances")
    if (not isinstance(before, list) or not isinstance(after, list)
            or len(before) != len(keys) or len(after) != len(keys)):
        return ("NATIVE_SOL_BALANCE_EVIDENCE_MISSING", "BALANCE_DATA_MISSING")
    if any(type(x) is not int or x < 0 for x in before + after):
        return ("NATIVE_SOL_BALANCE_EVIDENCE_MISSING", "BALANCE_DATA_INVALID")
    fee = _uint(meta.get("fee"), "FEE_LAMPORTS")
    failed = meta.get("err") is not None
    system_program = "11111111111111111111111111111111"
    instructions = message.get("instructions")
    if not isinstance(instructions, list):
        return ("NATIVE_SOL_BALANCE_EVIDENCE_MISSING", "INSTRUCTIONS_MISSING")
    inner = meta.get("innerInstructions") or []
    if not isinstance(inner, list):
        return ("NATIVE_SOL_BALANCE_EVIDENCE_MISSING", "INNER_INSTRUCTIONS_INVALID")
    all_instructions = list(instructions)
    for group in inner:
        if not isinstance(group, dict) or not isinstance(group.get("instructions"), list):
            return ("NATIVE_SOL_BALANCE_EVIDENCE_MISSING", "INNER_INSTRUCTIONS_INVALID")
        all_instructions.extend(group["instructions"])
    if not failed:
        for item in all_instructions:
            if not isinstance(item, dict) or item.get("programId") != system_program:
                continue
            parsed = item.get("parsed")
            if not isinstance(parsed, dict) or parsed.get("type") not in (
                "transfer", "transferWithSeed", "createAccount",
                "createAccountWithSeed", "withdrawNonceAccount",
            ):
                continue
            info = parsed.get("info")
            if not isinstance(info, dict):
                return ("NATIVE_SOL_FLOW_UNCLASSIFIED",
                        "SYSTEM_VALUE_INSTRUCTION_UNPARSED")
            # An unrelated fee payer may fund a tracked wallet's ATA; this
            # is not a native lamport movement of the wallet owner itself.
            if any(info.get(field) in tracked
                   for field in ("source", "destination", "newAccount",
                                 "base", "nonceAccount", "authority")):
                return ("NATIVE_SOL_FLOW_UNCLASSIFIED",
                        "SYSTEM_VALUE_INSTRUCTION")
    for index, address in enumerate(keys):
        if address not in tracked:
            continue
        observed = after[index] - before[index]
        fee_only = -fee if index == 0 else 0
        if observed != fee_only:
            return ("NATIVE_SOL_FLOW_UNCLASSIFIED", "NON_FEE_NATIVE_BALANCE_CHANGE")
    return ("NO_NATIVE_SOL_FLOW_OBSERVED", "TRACKED_BALANCES_FEE_ONLY")


def normalize_transaction(result: dict, *, tracked_wallets: set[str]) -> dict:
    """Accept one finalized getTransaction jsonParsed result, never call RPC.

    Caller must have requested finalized commitment. RPC getTransaction does
    not itself return a commitment proof; keep this as a source assertion.
    """
    if not isinstance(result, dict) or not isinstance(tracked_wallets, set):
        raise LedgerEvidenceError("TRANSACTION_INPUT_INVALID")
    tracked = {_required_key(w, "TRACKED_WALLET") for w in tracked_wallets}
    transaction = result.get("transaction")
    meta = result.get("meta")
    if not isinstance(transaction, dict) or not isinstance(meta, dict):
        raise LedgerEvidenceError("TRANSACTION_META_MISSING")
    signatures = transaction.get("signatures")
    if not isinstance(signatures, list) or not signatures or not isinstance(signatures[0], str) or not signatures[0]:
        raise LedgerEvidenceError("SIGNATURE_MISSING")
    signature = signatures[0]
    slot = _uint(result.get("slot"), "SLOT")
    if slot == 0:
        raise LedgerEvidenceError("INVALID_SLOT")
    message = transaction.get("message")
    account_keys = message.get("accountKeys") if isinstance(message, dict) else None
    if not isinstance(account_keys, list):
        raise LedgerEvidenceError("ACCOUNT_KEYS_MISSING")
    keys = []
    for entry in account_keys:
        key = entry if isinstance(entry, str) else entry.get("pubkey") if isinstance(entry, dict) else None
        keys.append(_required_key(key, "TRANSACTION_ACCOUNT_KEY"))
    failed = meta.get("err") is not None
    native_status, native_reason = _native_sol_coverage(
        meta, message, keys, tracked)
    before = _balance_map(meta.get("preTokenBalances"), keys)
    after = _balance_map(meta.get("postTokenBalances"), keys)
    legs = []
    coverage_gaps = []
    for k in sorted(set(before) | set(after)):
        first = before.get(k)
        last = after.get(k)
        entry = last or first
        pre = first["raw"] if first else 0
        post = last["raw"] if last else 0
        delta = post - pre
        if first is not None and last is not None and (
            first["decimals"] != last["decimals"]
        ):
            raise LedgerEvidenceError("ACCOUNT_DECIMALS_CONFLICT")
        owners = {r["owner"] for r in (first, last) if r is not None}
        known = {owner for owner in owners if owner is not None}
        intersects = bool(known & tracked)
        if failed and delta != 0:
            raise LedgerEvidenceError("FAILED_TRANSACTION_NONZERO_TOKEN_DELTA")
        if len(known) > 1:
            if intersects:
                raise LedgerEvidenceError("ACCOUNT_OWNER_CHANGED_WITH_TRACKED_BALANCE")
            coverage_gaps.append("UNTRACKED_ACCOUNT_OWNER_CHANGED")
            continue
        if None in owners:
            # A missing owner in either pre or post must NEVER fabricate
            # -pre/+post. When a tracked owner appears in one side, only
            # equal quantities can be ignored safely; nonzero delta
            # remains unresolved and blocks immutable source ingestion.
            coverage_gaps.append("TOKEN_OWNER_UNRESOLVED")
            # Unknown ownership of a nonzero delta is an economic gap even
            # when *neither* side names a tracked owner. We cannot infer the
            # missing ATA belongs elsewhere; fail before persisting any
            # "CAPTURED" economic view.
            if delta != 0:
                raise LedgerEvidenceError("TOKEN_OWNER_UNRESOLVED_DELTA")
            continue
        if not intersects:
            continue
        legs.append({
            "owner": entry["owner"], "token_account": entry["token_account"],
            "account_index": entry["account_index"], "mint": entry["mint"],
            "decimals": entry["decimals"], "pre_raw": str(pre),
            "post_raw": str(post), "delta_raw": str(delta),
            "direction": "IN" if delta > 0 else "OUT" if delta < 0 else "ZERO",
            "economic_type": "UNVERIFIED_TOKEN_DELTA" if delta
                             else "NO_BALANCE_CHANGE",
            "market_execution_verified": False, "usd_value": None,
            "cost_basis_usd": None, "realized_pnl_usd": None,
        })
    # Equal opposite changes among tracked owners suggest peer flow; parsed
    # instruction indices/provenance are required before calling it a transfer.
    by_mint = defaultdict(list)
    for index, leg in enumerate(legs):
        if int(leg["delta_raw"]) != 0:
            by_mint[(leg["mint"], leg["decimals"])].append(index)
    possible_internal = []
    for (mint, decimals), indices in by_mint.items():
        owners = {legs[i]["owner"] for i in indices}
        balance = sum(int(legs[i]["delta_raw"]) for i in indices)
        if len(owners) >= 2 and balance == 0:
            possible_internal.append({
                "mint": mint, "decimals": decimals,
                "tracked_owners": sorted(owners),
                "classification": "POSSIBLE_PEER_FLOW_NEEDS_INSTRUCTION_PROOF",
            })
    normalized = {
        "schema_version": 2, "normalizer_version": "SOL_TOKEN_VIEW_V2",
        "chain": "solana",
        "signature": signature, "slot": slot,
        "source": "GET_TRANSACTION_JSON_PARSED_FINALIZED_REQUEST",
        "finality_proven_by_response": False,
        "status": "FAILED" if failed else "SUCCEEDED",
        "token_legs": legs, "tracked_wallet_count": len(
            {leg["owner"] for leg in legs}),
        "possible_peer_flows": possible_internal,
        "coverage_gaps": sorted(set(coverage_gaps)),
        "token_owner_coverage_complete": not coverage_gaps,
        "native_sol_coverage_status": native_status,
        "native_sol_observation_reason": native_reason,
        "native_sol_flow_lamports": None,
        "active_market_buys_confirmed": 0,
        "active_market_sells_confirmed": 0,
        "person_pnl_usd": None,
        "fees_lamports": _uint(meta.get("fee"), "FEE_LAMPORTS"),
    }
    normalized["canonical_event_sha256"] = _hash(normalized)
    return normalized


def transaction_identity(document: dict) -> tuple[str, str, int]:
    if not isinstance(document, dict) or document.get("chain") != "solana":
        raise LedgerEvidenceError("NORMALIZED_EVENT_INVALID")
    signature = document.get("signature")
    slot = _uint(document.get("slot"), "SLOT")
    if not isinstance(signature, str) or not signature or slot == 0:
        raise LedgerEvidenceError("NORMALIZED_EVENT_ID_INVALID")
    return ("solana", signature, slot)


def dedupe_transactions(documents: list[dict]) -> list[dict]:
    """Deduplicate one signature across wallets without masking conflicts."""
    seen = {}
    for row in documents:
        identity = transaction_identity(row)
        original = seen.get(identity)
        if original is None:
            seen[identity] = row
        elif original.get("canonical_event_sha256") != row.get("canonical_event_sha256"):
            raise LedgerEvidenceError("CONFLICTING_TRANSACTION_EVIDENCE")
    return list(seen.values())
