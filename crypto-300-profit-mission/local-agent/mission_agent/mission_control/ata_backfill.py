"""Bounded read-only Solana ATA history reconciliation for Frank research.

This is *not* the production Frank collector. It derives the canonical ATA
for both Token Program and Token-2022, scans their own signature histories,
checks actual post/pre token account balances by account-index and owner, and
never converts third-party receipts into model BUY signals or realized PnL.

No wallet private key, transaction signing, write RPC, automatic monitoring,
alert changes, or edits to the original collector.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
from typing import Any

WALLET = "498g1rVnFcnjBjpfw1xyqA1WvgQXUU8RWuELjxkjAayQ"
TOKEN = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
TOKEN_2022 = "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb"
ASSOCIATED = "ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL"
PROGRAMS = (TOKEN, TOKEN_2022)
B58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
FIELD = 2**255 - 19
CURVE_D = -121665 * pow(121666, FIELD - 2, FIELD) % FIELD
SQRT_M1 = pow(2, (FIELD - 1) // 4, FIELD)
SCOPE = "FRANK_CANONICAL_ATA_BOUNDED_READ_ONLY_V1"


def b58decode(address: str) -> bytes:
    if not isinstance(address, str) or not 32 <= len(address) <= 44:
        raise ValueError("INVALID_BASE58_ADDRESS")
    n = 0
    for char in address:
        try:
            n = n * 58 + B58.index(char)
        except ValueError as exc:
            raise ValueError("INVALID_BASE58_CHARACTER") from exc
    zeros = len(address) - len(address.lstrip("1"))
    result = bytes(zeros) + (n.to_bytes((n.bit_length()+7)//8, "big") if n else b"")
    if len(result) != 32:
        raise ValueError("INVALID_SOLANA_PUBLIC_KEY_BYTES")
    return result


def b58encode(value: bytes) -> str:
    if len(value) != 32:
        raise ValueError("INVALID_PUBKEY_LENGTH")
    n = int.from_bytes(value, "big")
    result = ""
    while n:
        n, rem = divmod(n, 58)
        result = B58[rem] + result
    return "1" * (len(value) - len(value.lstrip(b"\0"))) + result


def is_ed25519_point(raw: bytes) -> bool:
    """Compressed Edwards point check for Solana PDA bump derivation."""
    if len(raw) != 32:
        return False
    y = int.from_bytes(raw, "little") & ((1 << 255)-1)
    if y >= FIELD:
        return False
    y2 = y * y % FIELD
    denom = (CURVE_D * y2 + 1) % FIELD
    if not denom:
        return False
    x2 = (y2 - 1) * pow(denom, FIELD-2, FIELD) % FIELD
    x = pow(x2, (FIELD + 3)//8, FIELD)
    if x*x % FIELD != x2:
        x = x*SQRT_M1 % FIELD
    if x*x % FIELD != x2:
        return False
    if not x and raw[31] >> 7:
        return False
    return True


def derive_ata(owner: str, mint: str, token_program: str) -> tuple[str, int]:
    """Standard associated-token PDA: seeds [owner, token_program, mint]."""
    if token_program not in PROGRAMS:
        raise ValueError("TOKEN_PROGRAM_NOT_SUPPORTED")
    seeds = b58decode(owner) + b58decode(token_program) + b58decode(mint)
    program = b58decode(ASSOCIATED)
    for bump in range(255, -1, -1):
        candidate = sha256(seeds + bytes([bump]) + program +
                           b"ProgramDerivedAddress").digest()
        if not is_ed25519_point(candidate):
            return b58encode(candidate), bump
    raise ValueError("NO_VALID_PROGRAM_DERIVED_ADDRESS")


def _keys(message: dict) -> tuple[list[str], set[str]]:
    raw = message.get("accountKeys") or []
    keys = [x if isinstance(x, str) else x.get("pubkey") for x in raw]
    if any(not isinstance(x, str) for x in keys):
        return [], set()
    signers = {x.get("pubkey") for x in raw
               if isinstance(x, dict) and x.get("signer") is True}
    if not signers:
        header = message.get("header") or {}
        required = header.get("numRequiredSignatures")
        if type(required) is int and required >= 0:
            signers = set(keys[:required])
    return keys, signers


def _balance(rows: list, pubkeys: list[str], ata: str,
             mint: str, program: str, owner: str) -> dict | None:
    found = []
    for item in rows or []:
        idx = item.get("accountIndex")
        if type(idx) is not int or not 0 <= idx < len(pubkeys):
            continue
        if pubkeys[idx] != ata or item.get("mint") != mint:
            continue
        if item.get("owner") != owner or item.get("programId") != program:
            raise ValueError("TOKEN_BALANCE_OWNER_OR_PROGRAM_MISMATCH")
        token = item.get("uiTokenAmount") or {}
        raw, decimals = token.get("amount"), token.get("decimals")
        if (type(raw) is not str or not raw.isascii() or not raw.isdecimal()
                or type(decimals) is not int or not 0 <= decimals <= 18):
            raise ValueError("TOKEN_BALANCE_UNVERIFIABLE")
        found.append({"raw": int(raw), "decimals": decimals})
    if len(found) > 1:
        raise ValueError("DUPLICATE_ATA_BALANCE_IN_TRANSACTION")
    return found[0] if found else None


def validate_transaction(tx: dict, signature: str, ata: str, mint: str,
                         program: str, owner: str = WALLET) -> dict:
    """No missing pre/post balance becomes a made-up zero balance."""
    if not isinstance(tx, dict) or not isinstance(tx.get("meta"), dict):
        return {"signature": signature, "status": "TRANSACTION_UNAVAILABLE"}
    slot = tx.get("slot")
    if type(slot) is not int or slot <= 0:
        return {"signature": signature, "status": "SLOT_UNAVAILABLE"}
    if tx["meta"].get("err") is not None:
        return {"signature": signature, "slot": slot, "status": "FAILED_TX_NO_BALANCE_PROOF"}
    try:
        message = tx["transaction"]["message"]
        pubkeys, signers = _keys(message)
        if ata not in pubkeys:
            return {"signature": signature, "slot": slot, "status": "ATA_NOT_IN_TX_KEYS"}
        pre = _balance(tx["meta"].get("preTokenBalances"), pubkeys,
                       ata, mint, program, owner)
        post = _balance(tx["meta"].get("postTokenBalances"), pubkeys,
                        ata, mint, program, owner)
    except (TypeError, KeyError, ValueError) as exc:
        return {"signature": signature, "slot": slot,
                "status": "OWNER_OR_BALANCE_UNVERIFIED",
                "reason": str(exc)[:80]}
    if pre is None or post is None or pre["decimals"] != post["decimals"]:
        return {"signature": signature, "slot": slot,
                "status": "PARTIAL_PRE_POST_BALANCE_UNVERIFIED"}
    change = post["raw"] - pre["raw"]
    return {
        "signature": signature, "slot": slot, "block_time": tx.get("blockTime"),
        "ata": ata, "mint": mint, "token_program": program,
        "status": "VERIFIED_ATA_BALANCE_DELTA", "wallet_signed": owner in signers,
        "raw_before": str(pre["raw"]), "raw_after": str(post["raw"]),
        "raw_delta": str(change), "decimals": pre["decimals"],
        "direction": "IN" if change > 0 else "OUT" if change < 0 else "ZERO",
        "acquisition_cost_usd": None, "realized_pnl_usd": None,
    }


def scan_ata_mints(
    rpc: Any, mints: list[str], known_signatures: set[str] | None = None,
    *, owner: str = WALLET, since_time: int = 0, page_size: int = 100,
    max_pages_per_ata: int = 2, max_tx_fetches: int = 80,
) -> dict:
    """Injectable official read-only RPC adapter, strictly bounded.

    A signature seen on two ATA accounts is fetched only once, but the
    account-specific validation remains distinct; no duplicate token delta.
    """
    if not isinstance(mints, list) or not 1 <= len(mints) <= 12:
        raise ValueError("MINT_BATCH_MUST_BE_1_TO_12")
    if not isinstance(known_signatures, (set, type(None))):
        raise ValueError("INVALID_LOCAL_SIGNATURE_SET")
    if (type(since_time) is not int or since_time < 0 or
        type(page_size) is not int or not 1 <= page_size <= 100 or
        type(max_pages_per_ata) is not int or not 1 <= max_pages_per_ata <= 4 or
        type(max_tx_fetches) is not int or not 1 <= max_tx_fetches <= 120):
        raise ValueError("ATA_BUDGET_EXCEEDED")
    b58decode(owner)
    uniq = list(dict.fromkeys(mints))
    for mint in uniq:
        b58decode(mint)
    known = known_signatures or set()
    evidence = []
    scanned = []
    tx_cache = {}
    observed_ata_signatures = set()
    stats = Counter()
    interruption = None
    for mint in uniq:
        for program in PROGRAMS:
            account, bump = derive_ata(owner, mint, program)
            before = None
            exhausted = False
            status = "BOUNDED"
            for page in range(max_pages_per_ata):
                if len(tx_cache) >= max_tx_fetches:
                    status = "TX_FETCH_BUDGET_REACHED"
                    break
                opts = {"commitment": "finalized", "limit": page_size}
                if before:
                    opts["before"] = before
                # Same official method used by collector, but ATA NOT main wallet.
                try:
                    items = rpc.call("getSignaturesForAddress", [account, opts])
                except (OSError, RuntimeError) as exc:
                    status = "RPC_INTERRUPTED_PARTIAL"
                    interruption = type(exc).__name__
                    break
                if not isinstance(items, list):
                    raise ValueError("INVALID_ATA_SIGNATURE_LIST")
                stats["signature_pages"] += 1
                if not items:
                    exhausted, status = True, "NO_MORE_PROVIDER_SIGNATURES"
                    break
                reached_time = False
                for item in items:
                    signature = item.get("signature")
                    when = item.get("blockTime")
                    if not isinstance(signature, str) or not 70 <= len(signature) <= 100:
                        raise ValueError("INVALID_SOLANA_SIGNATURE")
                    if type(when) is int and when < since_time:
                        reached_time = True
                        break
                    pair = (account, signature)
                    if pair in observed_ata_signatures:
                        stats["duplicate_ata_signature_occurrences_skipped"] += 1
                        continue
                    observed_ata_signatures.add(pair)
                    stats["signature_occurrences"] += 1
                    if item.get("err") is not None:
                        stats["failed_signatures_not_fetched"] += 1
                        continue
                    if signature not in tx_cache:
                        if len(tx_cache) >= max_tx_fetches:
                            status = "TX_FETCH_BUDGET_REACHED"
                            break
                        try:
                            tx_cache[signature] = rpc.call("getTransaction", [
                                signature, {
                                    "commitment": "finalized", "encoding": "jsonParsed",
                                    "maxSupportedTransactionVersion": 1,
                                },
                            ])
                        except (OSError, RuntimeError) as exc:
                            status = "RPC_INTERRUPTED_PARTIAL"
                            interruption = type(exc).__name__
                            evidence.append({
                                "signature": signature, "mint": mint, "ata": account,
                                "status": "RPC_TX_LOOKUP_UNAVAILABLE",
                                "already_in_main_wallet_index": signature in known,
                            })
                            break
                    result = validate_transaction(
                        tx_cache[signature], signature, account, mint, program, owner)
                    result["already_in_main_wallet_index"] = signature in known
                    evidence.append(result)
                    stats[result["status"]] += 1
                if status in ("TX_FETCH_BUDGET_REACHED", "RPC_INTERRUPTED_PARTIAL"):
                    break
                if reached_time:
                    status = "TIME_BOUNDARY_REACHED"
                    break
                if len(items) < page_size:
                    exhausted, status = True, "NO_MORE_PROVIDER_SIGNATURES"
                    break
                previous = items[-1]["signature"]
                if previous == before:
                    status = "CURSOR_STALLED"
                    break
                before = previous
            scanned.append({
                "mint": mint, "token_program": program, "ata": account,
                "pda_bump": bump, "status": status,
                "provider_history_exhausted_in_bound": exhausted,
            })
            if interruption is not None:
                break
        if interruption is not None:
            break
    missing = sorted({
        row["signature"] for row in evidence
        if row.get("status") == "VERIFIED_ATA_BALANCE_DELTA"
        and row.get("raw_delta") != "0"
        and not row["already_in_main_wallet_index"]
    })
    return {
        "schema_version": 1, "source_scope": SCOPE,
        "wallet": owner, "since_block_time": since_time,
        "config": {"page_size": page_size, "max_pages_per_ata": max_pages_per_ata,
                   "max_tx_fetches": max_tx_fetches, "mints_count": len(uniq)},
        "accounts": scanned, "observations": evidence,
        "scan_status": "PARTIAL_RPC_INTERRUPTED" if interruption else "BOUNDED_COMPLETED",
        "interruption_type": interruption,
        "unscanned_canonical_accounts": len(uniq) * len(PROGRAMS) - len(scanned),
        "known_main_wallet_signatures_supplied": known_signatures is not None,
        "verified_nonzero_signatures_absent_from_local_index": (
            missing if known_signatures is not None else None),
        "statistics": dict(sorted(stats.items())),
        "complete_wallet_history": False, "current_inventory_verified": False,
        "cost_basis_verified": False, "trading_signal_emitted": False,
        "profit_usd": None,
        "limitations": [
            "Canonical ATA coverage only: non-associated and closed token accounts can be missed.",
            "Both Token and Token-2022 are queried independently; missing provider history is not proof of zero transfers.",
            "Successful ATA changes are not automatically market buys or a sender's acquisition cost.",
            "Bounded pagination and RPC transaction retention prevent complete-chain claims.",
        ],
    }
