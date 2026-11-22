"""Opening-market evidence from a chain-verified Pump bonding curve."""

from collections import Counter, defaultdict
from decimal import Decimal
import hashlib

from .cluster import CA_BLOCK_SIGNATURE_OPTIONS, RPCJobBudgetExceeded
from .holder_ranks import valid_pubkey
from .launch_identity import PUMP_PROGRAM
from .transaction_batch import OPTIONS as TX_OPTIONS

SIGNATURE_PAGE = 1000
MAX_BUYERS = 70
SNIPER_SLOTS = 3
TX_TTL = 3650 * 86400
BASE58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
TOKEN_PROGRAMS = {
    "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",
    "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb",
}
PUMP_ACTIONS = {
    hashlib.sha256(f"global:{name}".encode()).digest()[:8]: action
    for action, names in {
        "CREATE": ("create", "create_v2"),
        "BUY": ("buy", "buy_exact_sol_in", "buy_v2", "buy_exact_quote_in_v2"),
        "SELL": ("sell", "sell_v2"),
        "NON_TRADE": ("migrate_bonding_curve_creator", "distribute_creator_fees_v2"),
    }.items()
    for name in names
}


class OpeningEvidenceError(ValueError):
    """Stable public reason codes for incomplete opening evidence."""


def _signature_page(page, seen, before, previous_slot):
    if not isinstance(page, list) or len(page) > SIGNATURE_PAGE:
        raise OpeningEvidenceError("MALFORMED_SIGNATURE_PAGE")
    page_signatures = set()
    for row in page:
        if not isinstance(row, dict):
            raise OpeningEvidenceError("MALFORMED_SIGNATURE_PAGE")
        signature, slot, error = row.get("signature"), row.get("slot"), row.get("err")
        if (not isinstance(signature, str) or not signature or len(signature) > 128
                or type(slot) is not int or slot < 0 or "err" not in row
                or (error is not None and not isinstance(error, (dict, str)))):
            raise OpeningEvidenceError("MALFORMED_SIGNATURE_PAGE")
        if signature == before:
            raise OpeningEvidenceError("CURSOR_STALLED")
        if signature in seen or signature in page_signatures or (previous_slot is not None and slot > previous_slot):
            raise OpeningEvidenceError("SOURCE_PAGE_CONFLICT")
        previous_slot = slot
        page_signatures.add(signature)
    seen.update(page_signatures)
    return previous_slot


def _encoding_discriminator(value):
    if not isinstance(value, str) or len(value) > 2600:
        return None
    number = 0
    try:
        for char in value:
            number = number * 58 + BASE58.index(char)
    except ValueError:
        return None
    zeros = len(value) - len(value.lstrip("1"))
    return (b"\0" * zeros + number.to_bytes((number.bit_length() + 7) // 8, "big"))[:8]


def _program(instruction, names):
    if isinstance(instruction.get("programId"), str):
        return instruction["programId"]
    index = instruction.get("programIdIndex")
    if type(index) is not int or not 0 <= index < len(names):
        raise OpeningEvidenceError("TRANSACTION_EVIDENCE_INCOMPLETE")
    return names[index]


def _action(instruction, names, mint, curve):
    if _program(instruction, names) != PUMP_PROGRAM:
        return None
    accounts = instruction.get("accounts")
    if not isinstance(accounts, list) or any(not isinstance(a, str) for a in accounts):
        raise OpeningEvidenceError("TRANSACTION_EVIDENCE_INCOMPLETE")
    if mint not in accounts or curve not in accounts:
        return None
    return PUMP_ACTIONS.get(_encoding_discriminator(instruction.get("data")), "OTHER")


def _token_accounts(meta, names, mint):
    owners = {}
    observed = set()
    complete_indexes = True
    for k in ("preTokenBalances", "postTokenBalances"):
        balances = meta.get(k)
        if not isinstance(balances, list):
            raise OpeningEvidenceError("TRANSACTION_EVIDENCE_INCOMPLETE")
        seen = set()
        for row in balances:
            if not isinstance(row, dict):
                raise OpeningEvidenceError("TRANSACTION_EVIDENCE_INCOMPLETE")
            index, owner = row.get("accountIndex"), row.get("owner")
            valid_index = type(index) is int and 0 <= index < len(names)
            if valid_index:
                observed.add(names[index])
            else:
                complete_indexes = False
            if row.get("mint") != mint:
                continue
            if not valid_index or index in seen or not isinstance(owner, str) or not owner:
                raise OpeningEvidenceError("TRANSACTION_EVIDENCE_INCOMPLETE")
            address = names[index]
            if address in owners and owners[address] != owner:
                raise OpeningEvidenceError("TRANSACTION_EVIDENCE_INCOMPLETE")
            seen.add(index)
            owners[address] = owner
    return owners, observed if complete_indexes else None


def _transient_sell_sources(instructions, grouped, names, mint, observed):
    """Prove the lifetime of a token account absent from both balance snapshots."""
    if observed is None:
        return {}
    starts = defaultdict(list)
    closes = defaultdict(list)
    ambiguous = set()
    for index, top in enumerate(instructions):
        for offset, ix in enumerate((top, *grouped.get(index, ()))):
            if not isinstance(ix, dict):
                return {}
            program = _program(ix, names)
            if program not in TOKEN_PROGRAMS:
                continue
            parsed = ix.get("parsed")
            if not isinstance(parsed, dict):
                accounts = ix.get("accounts")
                if not isinstance(accounts, list) or any(not isinstance(a, str) for a in accounts):
                    return {}
                ambiguous.update(accounts)
                continue
            kind = parsed.get("type")
            initializes = kind in ("initializeAccount", "initializeAccount2", "initializeAccount3")
            if not initializes and kind not in ("closeAccount", "setAuthority"):
                continue
            info = parsed.get("info")
            if not isinstance(info, dict):
                return {}
            account = info.get("account")
            if kind == "setAuthority":
                account = account or info.get("mint")
                if not isinstance(account, str):
                    return {}
                ambiguous.add(account)
                continue
            if not isinstance(account, str):
                return {}
            if account in observed:
                continue
            position = (index, offset)
            if initializes:
                starts[account].append((position, program, info.get("owner"), info.get("mint")))
            else:
                closes[account].append((position, program, info.get("owner")))
    sources = {}
    for account, records in starts.items():
        ended = closes.get(account, [])
        if account in ambiguous or account not in names or len(records) != 1 or len(ended) != 1:
            continue
        opened, program, owner, initialized_mint = records[0]
        closed, close_program, close_owner = ended[0]
        if (initialized_mint == mint and isinstance(owner, str) and owner in names
                and program == close_program and owner == close_owner and opened < closed):
            sources[account] = (owner, program, opened, closed)
    return sources


def _bound_transfers(instructions, names, token_owners, users, mint, curve, direction, transient_sources):
    matched = Counter()
    for position, ix in instructions:
        program = _program(ix, names)
        if program not in TOKEN_PROGRAMS:
            continue
        parsed = ix.get("parsed")
        if not isinstance(parsed, dict) or parsed.get("type") not in {"transfer", "transferChecked"}:
            continue
        info = parsed.get("info")
        if not isinstance(info, dict):
            raise OpeningEvidenceError("TRANSACTION_EVIDENCE_INCOMPLETE")
        source_address, destination_address = info.get("source"), info.get("destination")
        if not isinstance(source_address, str) or not isinstance(destination_address, str):
            raise OpeningEvidenceError("TRANSACTION_EVIDENCE_INCOMPLETE")
        source, dest = token_owners.get(source_address), token_owners.get(destination_address)
        owner = None
        if direction == "BUY" and source == curve:
            owner = dest
        if direction == "SELL" and dest == curve:
            owner = source
            if owner is None and source_address in transient_sources:
                seller, token_program, opened, closed = transient_sources[source_address]
                if token_program == program and opened < position < closed and info.get("authority") == seller:
                    owner = seller
        if owner not in users:
            continue
        if parsed["type"] == "transferChecked":
            if info.get("mint") != mint or not isinstance(info.get("tokenAmount"), dict):
                raise OpeningEvidenceError("TRANSACTION_EVIDENCE_INCOMPLETE")
            value = info["tokenAmount"].get("amount")
        else:
            value = info.get("amount")
        if not isinstance(value, str) or not value.isascii() or not value.isdecimal() or len(value) > 20:
            raise OpeningEvidenceError("TRANSACTION_EVIDENCE_INCOMPLETE")
        amount = int(value)
        if not 0 < amount < 2**64:
            raise OpeningEvidenceError("TRANSACTION_EVIDENCE_INCOMPLETE")
        matched[owner] += amount
    if len(matched) != 1:
        raise OpeningEvidenceError("TRANSACTION_EVIDENCE_INCOMPLETE")
    return next(iter(matched.items()))


def _opening_actions(tx, row, mint, curve):
    if not isinstance(tx, dict) or tx.get("slot") != row["slot"] or type(tx.get("slot")) is not int:
        raise OpeningEvidenceError("TRANSACTION_EVIDENCE_INCOMPLETE")
    wrapper, meta = tx.get("transaction"), tx.get("meta")
    block_time = tx.get("blockTime")
    listed_block_time = row.get("blockTime")
    if block_time is not None and listed_block_time is not None and block_time != listed_block_time:
        raise OpeningEvidenceError("TRANSACTION_EVIDENCE_INCOMPLETE")
    if not isinstance(wrapper, dict) or not isinstance(meta, dict) or "err" not in meta or meta["err"] is not None:
        raise OpeningEvidenceError("TRANSACTION_EVIDENCE_INCOMPLETE")
    signatures, message = wrapper.get("signatures"), wrapper.get("message")
    if not isinstance(signatures, list) or not signatures or signatures[0] != row["signature"] or not isinstance(message, dict):
        raise OpeningEvidenceError("TRANSACTION_EVIDENCE_INCOMPLETE")
    keys, instructions, inner = message.get("accountKeys"), message.get("instructions"), meta.get("innerInstructions")
    if not isinstance(keys, list) or not isinstance(instructions, list) or not isinstance(inner, list):
        raise OpeningEvidenceError("TRANSACTION_EVIDENCE_INCOMPLETE")
    names, signers = [], set()
    for key in keys:
        if not isinstance(key, dict) or not isinstance(key.get("pubkey"), str) or type(key.get("signer")) is not bool:
            raise OpeningEvidenceError("TRANSACTION_EVIDENCE_INCOMPLETE")
        names.append(key["pubkey"])
        if key["signer"]:
            signers.add(key["pubkey"])
    if not names or len(set(names)) != len(names):
        raise OpeningEvidenceError("TRANSACTION_EVIDENCE_INCOMPLETE")

    grouped = {}
    for group in inner:
        if not isinstance(group, dict):
            raise OpeningEvidenceError("TRANSACTION_EVIDENCE_INCOMPLETE")
        index, members = group.get("index"), group.get("instructions")
        if type(index) is not int or not 0 <= index < len(instructions) or index in grouped or not isinstance(members, list):
            raise OpeningEvidenceError("TRANSACTION_EVIDENCE_INCOMPLETE")
        grouped[index] = members

    actions = []
    token_owners = transient_sources = None
    for index, top in enumerate(instructions):
        nested = grouped.get(index, [])
        if any(not isinstance(ix, dict) for ix in [top, *nested]):
            raise OpeningEvidenceError("TRANSACTION_EVIDENCE_INCOMPLETE")
        group_actions = [(ix, _action(ix, names, mint, curve)) for ix in [top, *nested]]
        for offset, (ix, action) in enumerate(group_actions):
            if action == "CREATE":
                actions.append(("CREATE", None, None))
                continue
            if action in (None, "NON_TRADE"):
                continue
            if action == "OTHER":
                raise OpeningEvidenceError("TRANSACTION_EVIDENCE_INCOMPLETE")
            if token_owners is None:
                token_owners, observed = _token_accounts(meta, names, mint)
            if action == "SELL" and transient_sources is None:
                transient_sources = _transient_sell_sources(instructions, grouped, names, mint, observed)
            if offset == 0:
                children = [((index, child_offset), child)
                            for child_offset, child in enumerate(nested, start=1)]
                # A nested market invocation is not evidence for the parent's own fill.
                if any(other in {"BUY", "SELL"} for _, other in group_actions[1:]):
                    raise OpeningEvidenceError("TRANSACTION_EVIDENCE_INCOMPLETE")
            else:
                height = ix.get("stackHeight")
                if type(height) is not int or height < 2:
                    raise OpeningEvidenceError("TRANSACTION_EVIDENCE_INCOMPLETE")
                children = []
                for child_offset, child in enumerate(nested[offset:], start=offset + 1):
                    child_height = child.get("stackHeight")
                    if type(child_height) is not int:
                        raise OpeningEvidenceError("TRANSACTION_EVIDENCE_INCOMPLETE")
                    if child_height <= height:
                        break
                    if child_height == height + 1:
                        children.append(((index, child_offset), child))
            users = signers.intersection(ix["accounts"]) - {curve}
            owner, raw = _bound_transfers(children, names, token_owners, users, mint, curve, action,
                                          transient_sources or {})
            actions.append((action, owner, raw))
    return actions


def _valid_block_signature(value):
    if not isinstance(value, str) or not 64 <= len(value) <= 88:
        return False
    number = 0
    try:
        for char in value:
            number = number * 58 + BASE58.index(char)
    except ValueError:
        return False
    leading_zeros = len(value) - len(value.lstrip("1"))
    return leading_zeros + (number.bit_length() + 7) // 8 == 64


def _finalized_cutoff_order(rpc, slot, curve_signatures):
    evidence = {"basis": "FINALIZED_BLOCK_SIGNATURE_ORDER", "slot": slot}
    try:
        block = rpc.call("getBlock", [slot, CA_BLOCK_SIGNATURE_OPTIONS.copy()], ttl=TX_TTL)
    except RPCJobBudgetExceeded:
        raise
    except Exception:
        return {**evidence, "status": "SOURCE_UNAVAILABLE"}, {}
    if block is None:
        return {**evidence, "status": "SOURCE_UNAVAILABLE"}, {}
    if not isinstance(block, dict):
        return {**evidence, "status": "BLOCK_EVIDENCE_INVALID"}, {}
    signatures, blockhash, parent = block.get("signatures"), block.get("blockhash"), block.get("parentSlot")
    if (not valid_pubkey(blockhash) or type(parent) is not int or not 0 <= parent < slot
            or not isinstance(signatures, list) or not signatures
            or any(not _valid_block_signature(signature) for signature in signatures)
            or len(set(signatures)) != len(signatures)):
        return {**evidence, "status": "BLOCK_EVIDENCE_INVALID"}, {}
    positions = {signature: index for index, signature in enumerate(signatures) if signature in curve_signatures}
    if len(positions) != len(curve_signatures):
        return {**evidence, "status": "CURVE_SIGNATURES_MISSING", "blockhash": blockhash,
                "parent_slot": parent, "matched_signature_count": len(positions),
                "expected_signature_count": len(curve_signatures)}, {}
    return {**evidence, "status": "VERIFIED", "blockhash": blockhash, "parent_slot": parent,
            "curve_signature_positions": [{"signature": signature, "block_index": index}
                                          for signature, index in positions.items()]}, positions


def holding_status(bought_raw, current_raw):
    if current_raw is None or bought_raw is None:
        return "UNRESOLVED"
    if current_raw <= 0:
        return "CLEARED"
    if current_raw > bought_raw:
        return "ADDED"
    if current_raw < bought_raw:
        return "PARTIAL_REDUCED"
    return "HOLDING"


def collect_launch_flow(mint, rpc, *, launch=None, current_balances=None, supply_raw=None,
                        excluded_owners=(), progress=None):
    """Read the verified curve's finalized history, then classify its opening.

    The source is read to an explicit empty page. The parse stops only once the
    first-70 question has sufficient evidence, including the entire cutoff slot.
    Full wallet history and the Scanner do not use this opening view.
    """
    pump = (launch or {}).get("pump") or {}
    verified = (pump.get("status") == "VERIFIED_CHAIN_STATE"
                and isinstance(pump.get("bonding_curve"), str) and bool(pump["bonding_curve"]))
    curve = pump["bonding_curve"] if verified else None
    creator = pump.get("creator") if verified else None
    known_balance = current_balances is not None

    def pct(raw):
        if raw is None or not supply_raw:
            return None
        return str((Decimal(raw) * 100 / Decimal(supply_raw)).quantize(Decimal("0.0001")))

    dev = None
    if creator:
        current = current_balances.get(creator, 0) if known_balance else None
        dev = {"creator": creator, "current_raw": str(current) if current is not None else None,
               "current_pct": pct(current), "early_bought_raw": None, "status": "UNRESOLVED",
               "sell_status": "UNRESOLVED", "verified_sell": None,
               "scope": "CHAIN_VERIFIED_CREATOR; OPENING_WINDOW_TRADES"}
    out = {"version": 1, "address": curve or mint, "address_kind": "PUMP_BONDING_CURVE" if verified else "MINT",
           "creator": creator, "dev": dev, "current_balance_source": (
               "COMPLETE_MINT_ENUMERATION" if known_balance else "UNRESOLVED"),
           "limits": {"buyers": MAX_BUYERS, "sniper_slots": SNIPER_SLOTS},
           "definitions": {"sniper": "BUY_WITHIN_3_SLOTS_AFTER_CREATE_EXCLUDING_CREATOR",
                           "bundle": "BUY_IN_CREATE_SLOT_OR_MULTIPLE_BUYERS_IN_ONE_TRANSACTION",
                           "signal_scope": "BEHAVIOUR_SIGNAL_WITHIN_FIRST_BUYER_COHORT_NOT_CONTROL_PROOF",
                           "purchase": "PUMP_PROGRAM_INSTRUCTION_AND_BOUND_TOKEN_TRANSFER"}}
    if not verified:
        return {**out, "status": "UNAVAILABLE", "reason": "MARKET_LAUNCH_ADDRESS_NOT_VERIFIED"}

    pages, parsed, previous_slot, before, seen = [], 0, None, None, set()
    out.update(signature_requests=0, signature_count=0, window_method="CURVE_CURSOR_TO_PROVIDER_EMPTY")
    while True:
        options = {"commitment": "finalized", "limit": SIGNATURE_PAGE}
        if before is not None:
            options["before"] = before
        out["signature_requests"] += 1
        try:
            page = rpc.call("getSignaturesForAddress", [curve, options], ttl=300)
            previous_slot = _signature_page(page, seen, before, previous_slot)
        except RPCJobBudgetExceeded:
            raise
        except OpeningEvidenceError as exc:
            return {**out, "status": "PARTIAL", "reason": str(exc)}
        except Exception:
            return {**out, "status": "PARTIAL", "reason": "SIGNATURE_SOURCE_UNAVAILABLE"}
        if not page:
            break
        pages.append(page)
        out["signature_count"] += len(page)
        before = page[-1]["signature"]
    out["oldest_reach"] = "PROVIDER_EMPTY_PAGE"
    excluded = set(excluded_owners) | {curve}
    create, cutoff, transaction_errors = None, None, 0
    pre_creation_buys = []
    buy_evidence = {}
    multi_buyer_txs = 0

    def transactions():
        for page in reversed(pages):
            if getattr(rpc, "supports_transaction_batches", False):
                signatures = [row["signature"] for row in reversed(page) if row["err"] is None]
                rpc.prefetch_transactions(signatures, ttl=TX_TTL)
            yield from reversed(page)

    for row in transactions():
        slot, signature = row["slot"], row["signature"]
        if cutoff is not None and slot > cutoff and slot > create["slot"] + SNIPER_SLOTS:
            break
        if row["err"] is not None:
            continue
        try:
            tx = rpc.call("getTransaction", [signature, TX_OPTIONS], ttl=TX_TTL)
        except RPCJobBudgetExceeded:
            raise
        except Exception:
            transaction_errors += 1
            continue
        try:
            actions = _opening_actions(tx, row, mint, curve)
        except OpeningEvidenceError:
            transaction_errors += 1
            continue
        parsed += 1
        if progress is not None and parsed % 25 == 0:
            progress(parsed)
        if any(action == "CREATE" for action, _, _ in actions):
            if create is not None:
                return {**out, "status": "PARTIAL", "reason": "CONFLICTING_LAUNCH_CREATION"}
            create = {"signature": signature, "slot": slot, "block_time": row.get("blockTime"),
                      "create_instruction_observed": True, "basis": "PUMP_MINT_AND_CURVE_CREATE"}
        tx_buyers = Counter()
        for action, owner, amount in actions:
            if action == "BUY" and owner not in excluded:
                tx_buyers[owner] += amount
            if action == "SELL" and dev is not None and owner == creator and dev["verified_sell"] is None:
                dev["verified_sell"] = {"signature": signature, "slot": slot, "token_raw": str(amount)}
                dev["sell_status"] = "VERIFIED"
        if not tx_buyers:
            continue
        if create is None:
            pre_creation_buys.append(slot)
            continue
        multi_buyer_txs += len(tx_buyers) > 1
        for owner, amount in tx_buyers.items():
            if cutoff is not None and slot > cutoff:
                continue
            buyer = buy_evidence.setdefault(owner, {"slot": slot, "purchases": [],
                                                     "bundle": False})
            if buyer["slot"] == slot:
                buyer["purchases"].append((signature, amount, row.get("blockTime")))
            buyer["bundle"] |= owner != creator and (slot == create["slot"] or len(tx_buyers) > 1)
        if cutoff is None and len(buy_evidence) >= MAX_BUYERS:
            cutoff = slot

    out.update(create=create, parsed_transactions=parsed, transaction_errors=transaction_errors,
               multi_buyer_transactions=multi_buyer_txs,
               parse_stop="BUYER_LIMIT" if cutoff is not None else "EARLIEST_TRANSACTIONS_EXHAUSTED")
    if create is None or pre_creation_buys:
        return {**out, "status": "PARTIAL", "reason": "LAUNCH_CREATION_NOT_VERIFIED"}

    tie_overflow = len(buy_evidence) > MAX_BUYERS
    slot_counts = Counter(buyer["slot"] for buyer in buy_evidence.values())
    rank_by_slot = {}
    rank = 1
    for slot in sorted(slot_counts):
        rank_by_slot[slot] = rank if slot_counts[slot] == 1 else None
        rank += slot_counts[slot]
    ranked_cutoff = {}
    outside_cutoff = set()
    positions = {}
    ordered_buyers = list(buy_evidence.items())
    if tie_overflow and not transaction_errors:
        cutoff_signatures = {row["signature"] for page in pages for row in page if row["slot"] == cutoff}
        order_evidence, positions = _finalized_cutoff_order(rpc, cutoff, cutoff_signatures)
        out["cutoff_order"] = order_evidence
        if positions:
            previous = [(owner, evidence) for owner, evidence in ordered_buyers if evidence["slot"] != cutoff]
            cutoff_buyers = [(owner, evidence) for owner, evidence in ordered_buyers if evidence["slot"] == cutoff]
            first_indexes = {owner: min(positions[signature] for signature, _, _ in evidence["purchases"])
                             for owner, evidence in cutoff_buyers}
            cutoff_buyers.sort(key=lambda item: first_indexes[item[0]])
            seats = MAX_BUYERS - len(previous)
            if first_indexes[cutoff_buyers[seats - 1][0]] != first_indexes[cutoff_buyers[seats][0]]:
                counts = Counter(first_indexes.values())
                for index, (owner, _) in enumerate(cutoff_buyers, start=len(previous) + 1):
                    ranked_cutoff[owner] = index if counts[first_indexes[owner]] == 1 else None
                    if index > MAX_BUYERS:
                        outside_cutoff.add(owner)
                ordered_buyers = previous + cutoff_buyers
                tie_overflow = False
            else:
                order_evidence["status"] = "BOUNDARY_WITHIN_ONE_TRANSACTION"

    result, tied, excluded_at_cutoff = [], [], []
    for owner, evidence in ordered_buyers:
        slot, purchases = evidence["slot"], evidence["purchases"]
        if positions and slot == cutoff:
            purchases = sorted(purchases, key=lambda purchase: positions[purchase[0]])
        # A finalized transaction index can order multiple buys by the same
        # wallet. Buys in unresolved slots still have no established first tx.
        signature, first_amount, block_time = (
            purchases[0] if len(purchases) == 1 or (positions and slot == cutoff) else (None, None, None))
        current = current_balances.get(owner, 0) if known_balance else None
        rows = tied if tie_overflow and slot == cutoff else excluded_at_cutoff if owner in outside_cutoff else result
        buyer_rank = ranked_cutoff.get(owner, rank_by_slot[slot]) if not transaction_errors else None
        rows.append({"owner": owner, "rank": buyer_rank,
                       "first_signature": signature, "first_signatures": [s for s, _, _ in purchases],
                       "first_slot": slot, "first_block_time": block_time, "buy_count": len(purchases),
                       "bought_raw": None if first_amount is None else str(first_amount),
                       "current_raw": None if current is None else str(current), "current_pct": pct(current),
                       "status": holding_status(first_amount, current), "sol_outflow_lamports": None,
                       "is_creator": owner == creator, "bundle": evidence["bundle"],
                       "sniper": owner != creator and 0 <= slot - create["slot"] <= SNIPER_SLOTS})
    if dev is not None:
        if dev["verified_sell"] is None and not transaction_errors:
            dev["sell_status"] = "NOT_OBSERVED_IN_READ_WINDOW"
        if not transaction_errors and not tie_overflow:
            creator_buy = next((row for row in result if row["is_creator"]), None)
            if creator_buy is not None:
                dev["early_bought_raw"] = creator_buy["bought_raw"]
                dev["status"] = creator_buy["status"]
    out["buyers"] = result
    if excluded_at_cutoff:
        out["cutoff_slot"] = cutoff
        out["verified_after_cutoff_buyers"] = excluded_at_cutoff
    if tied:
        out["cutoff_slot"] = cutoff
        out["unranked_cutoff_buyers"] = tied
    if transaction_errors or tie_overflow:
        return {**out, "status": "PARTIAL", "reason": ("TRANSACTION_EVIDENCE_INCOMPLETE"
                if transaction_errors else "BUYER_ORDER_AT_CUTOFF_UNRESOLVED")}

    def group(rows):
        held = sum(int(r["current_raw"]) for r in rows) if known_balance else None
        bought = sum(int(r["bought_raw"]) for r in rows) if all(r["bought_raw"] is not None for r in rows) else None
        return {"count": len(rows), "bought_raw": None if bought is None else str(bought), "bought_pct": pct(bought),
                "current_raw": None if held is None else str(held), "current_pct": pct(held),
                "cleared": sum(r["status"] == "CLEARED" for r in rows) if known_balance else None}

    return {**out, "status": "OK", "reason": None,
            "summary": {"first_buyers": group(result), "snipers": group([r for r in result if r["sniper"]]),
                        "bundles": group([r for r in result if r["bundle"]])}}
