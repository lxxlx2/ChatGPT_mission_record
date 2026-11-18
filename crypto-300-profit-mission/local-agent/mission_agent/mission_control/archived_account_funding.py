"""Project wallet-related ATA opening deposits from a previously bound jsonParsed transaction."""

from collections import Counter, defaultdict

from ..meme.holder_ranks import valid_pubkey
from .ata_backfill import ASSOCIATED, PROGRAMS, derive_ata


SYSTEM = "11111111111111111111111111111111"
MISSING = object()


def _parsed(instruction):
    value = instruction.get("parsed") if isinstance(instruction, dict) else None
    return value if isinstance(value, dict) else {}


def _ata(instruction):
    return (isinstance(instruction, dict) and instruction.get("programId") == ASSOCIATED
            and _parsed(instruction).get("type") in ("create", "createIdempotent"))


def _call_tree(outer, inner):
    """Return immediate CPI children and mark reentrant ATA calls by instruction index."""
    calls = {-1: outer}
    children = defaultdict(list)
    stack = [-1]
    reentrant = set()
    for index, instruction in enumerate(inner):
        height = instruction.get("stackHeight") if isinstance(instruction, dict) else None
        if type(height) is not int or not 2 <= height <= len(stack) + 1:
            return None, set()
        del stack[height - 1:]
        children[stack[-1]].append((index, instruction))
        if _ata(instruction):
            ancestors = [ref for ref in stack if _ata(calls[ref])]
            if ancestors:
                reentrant.update([index, *ancestors])
        stack.append(index)
        calls[index] = instruction
    return children, reentrant


def _pre_balances(message, meta):
    keys, balances = message.get("accountKeys"), meta.get("preBalances")
    if not isinstance(keys, list) or not isinstance(balances, list) or len(keys) != len(balances):
        return {}
    names = [key.get("pubkey") if isinstance(key, dict) else key for key in keys]
    if not all(isinstance(key, str) for key in names) or len(set(names)) != len(names):
        return {}
    return dict(zip(names, balances))


def _funding_item(instruction, reference, wallet, pre, children, reason):
    parsed = _parsed(instruction)
    info = parsed.get("info")
    if not isinstance(info, dict) or wallet not in (info.get("source"), info.get("wallet")):
        return None
    item = {"instruction_ref": reference, "operation": parsed["type"], "status": "UNRESOLVED",
            "amount_raw": None, "funding_instruction_ref": None}
    payer, owner, account, mint, program = (info.get(k) for k in ("source", "wallet", "account", "mint", "tokenProgram"))
    if not all(valid_pubkey(key) for key in (payer, owner, account, mint, program)):
        return {**item, "reason": "ATA_ACCOUNT_IDENTITY_INVALID"}
    item.update(payer=payer, owner=owner, account=account, mint=mint, token_program=program,
                payer_role="WALLET" if payer == wallet else "OTHER",
                owner_role="WALLET" if owner == wallet else "OTHER")
    if reason:
        return {**item, "reason": reason, "status": "ATTEMPT_ONLY" if reason == "TRANSACTION_FAILED" else "UNRESOLVED"}
    if (program not in PROGRAMS or info.get("systemProgram") != SYSTEM or account == payer
            or derive_ata(owner, mint, program)[0] != account):
        return {**item, "reason": "ATA_ACCOUNT_IDENTITY_INVALID"}
    if type(pre.get(account)) is not int or pre[account] != 0:
        return {**item, "reason": "OPENING_ZERO_BALANCE_UNVERIFIED"}
    creates = []
    for child_index, child in children:
        call = _parsed(child)
        funds = call.get("info")
        if (child.get("programId") == SYSTEM and call.get("type") == "createAccount"
                and isinstance(funds, dict) and funds.get("newAccount") == account):
            creates.append((child_index, funds))
    if len(creates) != 1:
        return {**item, "reason": "DIRECT_SYSTEM_CREATE_NOT_UNIQUE_OR_ABSENT"}
    child_index, funds = creates[0]
    amount = funds.get("lamports")
    if (funds.get("source") != payer or funds.get("owner") != program or type(amount) is not int
            or not 0 < amount < 2**64):
        return {**item, "reason": "SYSTEM_FUNDING_FIELDS_UNVERIFIED"}
    return {**item, "status": "CONFIRMED_INITIAL_FUNDING", "amount_raw": str(amount),
            "funding_instruction_ref": [reference[0], child_index]}


def ata_account_funding(tx, wallet):
    """Report exact initial lamports transferred by a proven System createAccount CPI.

    Payment by the observed wallet and opening an account owned by that wallet
    are separate roles. Later flows, rent-exempt reserves and closure refunds
    cannot be derived from the opening deposit.
    """
    result = {"status": "UNRESOLVED", "instruction_count": 0, "unresolved_count": 0,
              "unit": "LAMPORT", "rent_status": "UNRESOLVED", "items": []}
    if not isinstance(tx, dict) or not valid_pubkey(wallet):
        return result
    meta, transaction = tx.get("meta"), tx.get("transaction")
    message = transaction.get("message") if isinstance(transaction, dict) else None
    if not isinstance(message, dict) or not isinstance(meta, dict) or not isinstance(message.get("instructions"), list):
        return result
    outer = message["instructions"]
    raw_groups = meta.get("innerInstructions")
    incomplete = not isinstance(raw_groups, list)
    groups = {}
    for group in raw_groups if isinstance(raw_groups, list) else ():
        index = group.get("index") if isinstance(group, dict) else None
        if type(index) is not int or not 0 <= index < len(outer):
            incomplete = True
            continue
        trace = group.get("instructions")
        if index in groups or not isinstance(trace, list):
            incomplete = True
            groups[index] = None
        else:
            groups[index] = trace
    pre = _pre_balances(message, meta)
    items = result["items"]
    error = meta.get("err", MISSING)
    for top, parent in enumerate(outer):
        trace = groups.get(top, [])
        children, reentrant = _call_tree(parent, trace) if trace is not None else (None, set())
        if children is None or not isinstance(parent, dict):
            incomplete = True
        for inner, instruction in [(-1, parent), *enumerate(trace or [])]:
            if not _ata(instruction):
                continue
            reason = None
            if error is MISSING:
                reason = "EXECUTION_STATUS_UNVERIFIED"
            elif error is not None:
                reason = "TRANSACTION_FAILED"
            elif children is None or raw_groups is None:
                reason = "CPI_TRACE_UNVERIFIED"
            elif inner in reentrant:
                reason = "REENTRANT_ATA_CALL"
            item = _funding_item(instruction, [top, inner], wallet, pre,
                                 children.get(inner, []) if children is not None else [], reason)
            if item is not None:
                items.append(item)
    accounts = Counter(i["account"] for i in items if i["status"] == "CONFIRMED_INITIAL_FUNDING")
    for item in items:
        if item["status"] == "CONFIRMED_INITIAL_FUNDING" and accounts[item["account"]] > 1:
            item.update(status="UNRESOLVED", reason="MULTIPLE_OPENINGS_OF_ACCOUNT",
                        amount_raw=None, funding_instruction_ref=None)
    unresolved = sum(item["status"] != "CONFIRMED_INITIAL_FUNDING" for item in items)
    status = "PARTIAL" if incomplete or unresolved else ("CONFIRMED" if items else "NO_RELEVANT_PARSED_ATA")
    result.update(status=status, instruction_count=len(items), unresolved_count=unresolved)
    return result
