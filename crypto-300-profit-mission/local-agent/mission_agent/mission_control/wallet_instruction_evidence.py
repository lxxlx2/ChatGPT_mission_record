"""A04 Solana parsed transfer instruction evidence, including inner instructions.

A matched SPL transfer instruction is evidence of a token movement, not
market BUY/SELL, common control, cost basis or same-person economic profit.
No transactions are sent. Unknown/unparsed instructions remain visible gaps.
"""
from __future__ import annotations

from .wallet_chain_capture import SPL_TOKEN_PROGRAM, TOKEN_2022_PROGRAM
from .wallet_economic_ledger import LedgerEvidenceError


def _amount(value):
    if isinstance(value, str) and value.isascii() and value.isdecimal():
        return str(int(value))
    return None


def transfer_instructions(tx: dict, normalized: dict) -> dict:
    if not isinstance(tx, dict) or not isinstance(normalized, dict):
        raise LedgerEvidenceError("TRANSFER_SOURCE_INVALID")
    message = (tx.get("transaction") or {}).get("message") or {}
    meta = tx.get("meta") or {}
    if (not isinstance(message, dict) or not isinstance(meta, dict)
        or tx.get("slot") != normalized.get("slot")
        or (tx.get("transaction") or {}).get("signatures", [None])[0]
                != normalized.get("signature")):
        raise LedgerEvidenceError("TRANSFER_TRANSACTION_ID_MISMATCH")
    outer = message.get("instructions")
    if not isinstance(outer, list):
        raise LedgerEvidenceError("TRANSFER_INSTRUCTIONS_MISSING")
    inner = meta.get("innerInstructions")
    if inner is None:
        inner = []
    if not isinstance(inner, list):
        raise LedgerEvidenceError("TRANSFER_INNER_INSTRUCTIONS_INVALID")
    failed = meta.get("err") is not None
    if failed != (normalized.get("status") == "FAILED"):
        raise LedgerEvidenceError("TRANSFER_EXECUTION_STATUS_MISMATCH")
    by_account = {}
    for leg in normalized.get("token_legs", []):
        key = leg["token_account"]
        owner = leg["owner"]
        if key in by_account and by_account[key] != owner:
            raise LedgerEvidenceError("TRANSFER_ACCOUNT_OWNER_CONFLICT")
        by_account[key] = owner

    candidates = []
    for i, item in enumerate(outer):
        candidates.append((i, None, item))
    for group in inner:
        if not isinstance(group, dict) or type(group.get("index")) is not int:
            raise LedgerEvidenceError("TRANSFER_INNER_GROUP_INVALID")
        parent_index = group["index"]
        if parent_index < 0 or parent_index >= len(outer):
            raise LedgerEvidenceError("TRANSFER_INNER_INDEX_OUT_OF_RANGE")
        items = group.get("instructions")
        if not isinstance(items, list):
            raise LedgerEvidenceError("TRANSFER_INNER_GROUP_MISSING")
        for j, item in enumerate(items):
            candidates.append((parent_index, j, item))
    events, gaps = [], []
    for outer_idx, inner_idx, raw in candidates:
        if not isinstance(raw, dict):
            gaps.append({"outer_index": outer_idx, "inner_index": inner_idx,
                         "reason": "INSTRUCTION_INVALID"})
            continue
        program_id = raw.get("programId")
        if program_id not in {SPL_TOKEN_PROGRAM, TOKEN_2022_PROGRAM}:
            continue
        parsed = raw.get("parsed")
        if not isinstance(parsed, dict):
            gaps.append({"outer_index": outer_idx, "inner_index": inner_idx,
                         "reason": "TOKEN_INSTRUCTION_UNPARSED"})
            continue
        kind = parsed.get("type")
        if kind not in {"transfer", "transferChecked"}:
            # Other instructions (mintTo, burn, closeAccount...) are not
            # transfers and will need their own economic classification.
            continue
        info = parsed.get("info")
        if not isinstance(info, dict):
            gaps.append({"outer_index": outer_idx, "inner_index": inner_idx,
                         "reason": "TOKEN_TRANSFER_INFO_MISSING"})
            continue
        source = info.get("source")
        destination = info.get("destination")
        q = info.get("tokenAmount")
        amount = _amount(q.get("amount")) if isinstance(q, dict) else None
        if amount is None:
            amount = _amount(info.get("amount"))
        if (not isinstance(source, str) or not source or
            not isinstance(destination, str) or not destination or
            amount is None):
            gaps.append({"outer_index": outer_idx, "inner_index": inner_idx,
                         "reason": "TOKEN_TRANSFER_FIELDS_INCOMPLETE"})
            continue
        sender, receiver = by_account.get(source), by_account.get(destination)
        if sender is not None and receiver is not None and sender == receiver:
            relation = "SAME_TRACKED_WALLET_TOKEN_TRANSFER"
        elif sender is not None and receiver is not None:
            relation = "TRACKED_TO_TRACKED_TOKEN_TRANSFER"
        elif sender is not None or receiver is not None:
            relation = "ONE_TRACKED_ENDPOINT_TRANSFER"
        else:
            relation = "UNATTRIBUTED_TOKEN_TRANSFER"
        events.append({
            "outer_index": outer_idx, "inner_index": inner_idx,
            "program_id": program_id, "instruction_type": kind,
            "source_token_account": source,
            "destination_token_account": destination,
            "source_wallet_owner": sender, "destination_wallet_owner": receiver,
            "raw_amount": amount, "mint_hint": info.get("mint"),
            "classification": ("FAILED_TRANSACTION_INSTRUCTION_NOT_EXECUTED"
                               if failed else relation),
            "source_status": ("FAILED_TRANSACTION_INSTRUCTION_NOT_EXECUTED"
                              if failed else "PARSED_TOKEN_INSTRUCTION_CONFIRMED"),
            "executed": not failed,
            "market_buy_confirmed": False, "market_sell_confirmed": False,
            "realized_pnl_usd": None,
        })
    return {
        "schema_version": 1,
        "chain": "solana",
        "signature": normalized["signature"], "slot": normalized["slot"],
        "transfer_count": len(events),
        "executed_transfer_count": 0 if failed else len(events),
        "transaction_executed": not failed,
        "unparsed_token_instruction_count": len(gaps),
        "transfers": events, "evidence_gaps": gaps,
        "active_market_trades_verified": False,
        "person_pnl_usd": None,
    }
