"""Replay the current parser on an original bound to an indexed wallet transaction."""

import errno
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import zlib

from ..frank.parser import PARSER_VERSION, WSOL, _program_id
from ..hashing import digest
from ..meme.holder_ranks import ALPHABET, valid_pubkey
from ..signals.classifier import classify
from .archived_account_funding import ata_account_funding
from .ata_backfill import ASSOCIATED, PROGRAMS, TOKEN_2022
from .wallet_activity import CLASSES, fixed_class
from .wallet_facts import _denomination, _integer, _raw, build_fact

SYSTEM = "11111111111111111111111111111111"
ARCHIVE_VERSION = 1
SIGNATURE = re.compile(r"[1-9A-HJ-NP-Za-km-z]{64,88}")
SOURCE_ERRORS = (ValueError, TypeError, KeyError, IndexError, AttributeError, OverflowError, RecursionError)
DIRECTORY_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW


def _signature(value):
    if not isinstance(value, str) or SIGNATURE.fullmatch(value) is None:
        return False
    integer = 0
    for char in value:
        integer = integer * 58 + ALPHABET.index(char)
    return len(value) - len(value.lstrip("1")) + (integer.bit_length() + 7) // 8 == 64


def _unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("DUPLICATE_KEY")
        result[key] = value
    return result


def _read_original(root, signature):
    # Open each component relative to a pinned descriptor. A source-row path
    # never chooses a file, including when a stored path names another archive.
    root = Path(root)
    if not root.is_absolute() or ".." in root.parts:
        raise OSError(errno.EINVAL, "invalid archive directory")
    directory = os.open(root.anchor, DIRECTORY_FLAGS)
    try:
        for part in root.parts[1:]:
            child = os.open(part, DIRECTORY_FLAGS, dir_fd=directory)
            os.close(directory)
            directory = child
        try:
            descriptor = os.open(signature + ".json.gz", os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW,
                                 dir_fd=directory)
        except FileNotFoundError:
            return None
        with os.fdopen(descriptor, "rb") as raw:
            if not stat.S_ISREG(os.fstat(raw.fileno()).st_mode):
                raise OSError(errno.EINVAL, "regular file required")
            with gzip.GzipFile(fileobj=raw, mode="rb") as gz:
                return json.load(gz, object_pairs_hook=_unique_keys)
    finally:
        os.close(directory)


def _instructions(tx):
    outer = tx["transaction"]["message"]["instructions"]
    groups = tx["meta"]["innerInstructions"]
    if not isinstance(outer, list) or not isinstance(groups, list):
        raise ValueError("INSTRUCTION_METADATA_MISSING")
    by_outer = {}
    for group in groups:
        index = group["index"]
        if type(index) is not int or not 0 <= index < len(outer) or index in by_outer:
            raise ValueError("AMBIGUOUS_INSTRUCTION_REFERENCE")
        if not isinstance(group["instructions"], list):
            raise ValueError("INSTRUCTION_METADATA_MISSING")
        by_outer[index] = group["instructions"]
    for i, ix in enumerate(outer):
        yield [i, -1], ix
        for j, child in enumerate(by_outer.get(i, [])):
            yield [i, j], child


def _native_transfers(tx, names, wallet, signature, effect):
    items = []
    invalid = False
    for ref, ix in _instructions(tx):
        parsed = ix.get("parsed")
        if not isinstance(parsed, dict):
            continue
        program = _program_id(ix, names)
        kind = parsed.get("type")
        # The legacy normalizer recognizes lifecycle labels before checking
        # program identity, and then uses them to infer token account ownership.
        # Reject ambiguous metadata before publishing any replayed transfers.
        if ((kind in ("create", "createIdempotent") and program != ASSOCIATED)
                or (kind in ("initializeAccount", "initializeAccount2", "initializeAccount3", "closeAccount")
                    and program not in PROGRAMS)):
            raise ValueError("UNSUPPORTED_LIFECYCLE_PROGRAM")
        if program != SYSTEM or kind not in ("transfer", "transferWithSeed"):
            continue
        info = parsed["info"]
        source, dest = info.get("source"), info.get("destination")
        if wallet not in (source, dest):
            continue
        amount = _raw(info.get("lamports"))
        if not valid_pubkey(source) or not valid_pubkey(dest) or amount is None:
            invalid = True
            continue
        direction = "SELF" if source == dest else "IN" if dest == wallet else "OUT"
        items.append({"instruction_ref": ref, "denomination": "SOL", "decimals": 9,
                      "direction": direction, "raw_amount": amount, "source_account": source,
                      "destination_account": dest, "instruction_effect": effect,
                      "leg_id": digest([ARCHIVE_VERSION, signature, wallet, "system_transfer", ref])})
    return items, "PARTIAL_INVALID_RECORDS" if invalid else "RECORDED"


def _verified_exchange(replay, projection):
    detail = replay.get("trade")
    if (projection["execution_status"] != "SUCCEEDED" or replay.get("classification") != "ACTIVE_TRADE"
            or not isinstance(detail, dict) or detail.get("route_intermediate_evidence_status") !=
            "NO_INTERMEDIATE_TRANSFER_OBSERVED"):
        return None
    mint, side = detail.get("mint"), detail.get("direction")
    amount, decimals = _raw(detail.get("token_amount_raw")), _integer(detail.get("token_decimals"), high=255)
    quotes = detail.get("quote_legs")
    if (not valid_pubkey(mint) or side not in {"BUY", "SELL"} or amount in {None, "0"} or decimals is None
            or not isinstance(quotes, list) or len(quotes) != 1):
        return None
    quote = quotes[0]
    quote_mint = WSOL if quote.get("asset") == "SOL" else quote.get("asset")
    quote_amount = _raw(quote.get("raw_delta"), signed=True)
    quote_decimals = _integer(quote.get("decimals"), high=255)
    if (not valid_pubkey(quote_mint) or quote_mint == mint or quote_decimals is None
            or quote_amount in {None, "0"} or (int(quote_amount) < 0) != (side == "BUY")):
        return None
    # Require both amounts and directions to be witnessed at the wallet boundary.
    # Gross pool hops are kept in the facts without assigning their fees to a lot.
    net = {}
    for account in projection["token_account_balances"] or []:
        key = (account["mint"], account["decimals"])
        net[key] = net.get(key, 0) + int(account["delta_raw"])
    for flow in projection["transient_token_flows"] or []:
        key = (flow["mint"], flow["decimals"])
        net[key] = net.get(key, 0) + int(flow["net_transfer_raw"])
    expected = {(mint, decimals): int(amount) * (1 if side == "BUY" else -1),
                (quote_mint, quote_decimals): int(quote_amount)}
    if {k: v for k, v in net.items() if v} != expected:
        return None
    return {"basis": "VERIFIED_WALLET_BOUNDARY_SINGLE_TARGET", "mint": mint, "side": side,
            "token_amount_raw": amount, "token_decimals": decimals,
            "quotes": [{"mint": quote_mint, "denomination": _denomination(quote_mint),
                        "raw_delta": quote_amount, "decimals": quote_decimals}]}


def _supplement_transfers(projection, instructions, names, wallet, signature, effect):
    owners = {row["account"]: row["mint"] for row in projection["token_account_balances"] or []}
    for item in projection["account_creations"] or []:
        owners.setdefault(item["account"], item["mint"])
    transfers = projection["token_transfers"]
    if transfers is None:
        return
    for ref, ix in instructions:
        parsed = ix.get("parsed")
        if not isinstance(parsed, dict) or _program_id(ix, names) not in PROGRAMS:
            continue
        kind, info = parsed.get("type"), parsed.get("info")
        if not isinstance(info, dict) or kind not in {"transfer", "transferChecked", "transferCheckedWithFee"}:
            continue
        source, destination = info.get("source"), info.get("destination")
        if not valid_pubkey(source) or not valid_pubkey(destination) or source == destination:
            continue
        incoming, outgoing = destination in owners, source in owners
        explicit_fee = kind == "transferCheckedWithFee"
        if not (incoming or outgoing) or not (explicit_fee or incoming and outgoing):
            continue
        mint = info.get("mint") or owners.get(source) or owners.get(destination)
        if not valid_pubkey(mint) or any(owners[k] != mint for k in (source, destination) if k in owners):
            continue
        value = info.get("tokenAmount", {})
        if not isinstance(value, dict):
            continue
        amount = _raw(value.get("amount", info.get("amount")))
        decimals = _integer(value.get("decimals"), high=255)
        if amount is None:
            continue
        fee, net = None, None
        if explicit_fee:
            fee_value = info.get("feeAmount")
            if (_program_id(ix, names) != TOKEN_2022 or not isinstance(fee_value, dict) or decimals is None
                    or _integer(fee_value.get("decimals"), high=255) != decimals):
                continue
            fee = _raw(fee_value.get("amount"))
            if fee is None or int(fee) > int(amount):
                continue
            net = str(int(amount) - int(fee))
        transfers.append({"instruction_ref": ref, "mint": mint, "denomination": _denomination(mint),
                          "direction": "INTERNAL" if incoming and outgoing else "IN" if incoming else "OUT",
                          "raw_amount": amount, "decimals": decimals, "source_account": source,
                          "destination_account": destination, "explicit_transfer_fee_raw": fee,
                          "explicit_destination_amount_raw": net, "instruction_effect": effect,
                          "leg_id": digest([ARCHIVE_VERSION, signature, wallet, "supplemental_token_transfer", ref])})
    transfers.sort(key=lambda x: x["instruction_ref"])


def _mentions(value, account):
    if isinstance(value, dict):
        return any(_mentions(item, account) for item in value.values())
    if isinstance(value, list):
        return any(_mentions(item, account) for item in value)
    return value == account


def _close_refunds(tx, instructions, names, wallet, effect):
    items, meta = [], tx["meta"]
    for ref, ix in instructions:
        parsed = ix.get("parsed")
        if (not isinstance(parsed, dict) or parsed.get("type") != "closeAccount"
                or _program_id(ix, names) not in PROGRAMS):
            continue
        info = parsed["info"]
        account, dest, owner = info.get("account"), info.get("destination"), info.get("owner")
        if wallet not in (dest, owner) or not valid_pubkey(account) or not valid_pubkey(dest):
            continue
        amount = None
        reason = "CLOSE_BALANCE_NOT_ISOLATED"
        if effect == "ATTEMPT_ONLY":
            reason = "TRANSACTION_FAILED"
        elif effect == "EXECUTED" and account in names and account not in (names[0], dest):
            index = names.index(account)
            before, after = _raw(meta["preBalances"][index]), _raw(meta["postBalances"][index])
            ambiguous = any(
                other_ref != ref and
                (_mentions(other_ix.get("parsed"), account) or _mentions(other_ix.get("accounts"), account)
                 or _mentions(other_ix.get("accounts"), index))
                for other_ref, other_ix in instructions
            )
            if before not in (None, "0") and after == "0" and not ambiguous:
                amount, reason = before, None
        items.append({"instruction_ref": ref, "account": account, "destination": dest,
                      "destination_role": "WALLET" if dest == wallet else "OTHER",
                      "status": "CONFIRMED_CLOSE_REFUND" if amount is not None else "UNRESOLVED",
                      "amount_raw": amount, "denomination": "SOL", "reason": reason})
    return items


def read_archived_fact(archive_root, row, *, legacy_archive_root=None):
    """Return a public, independent replay for one wallet_activity projection.

    Only the original canonical transaction digest is authoritative. The index
    classification remains available even when the original is unavailable.
    """
    indexed_class = fixed_class(row.get("class"))
    result = {"schema_version": ARCHIVE_VERSION, "parser_version": PARSER_VERSION,
              "indexed_class": indexed_class, "replayed_class": None, "replayed_reason": None, "raw_sha256": None,
              "block_time_status": "UNKNOWN", "archive_tier": None, "fact": None}

    def unavailable(reason):
        return {**result, "status": "UNAVAILABLE", "reason": reason}

    def unresolved(reason):
        return {**result, "status": "UNRESOLVED", "reason": reason}

    if archive_root is None:
        return unavailable("ARCHIVE_NOT_CONFIGURED")
    signature, wallet = row.get("sig"), row.get("wallet")
    expected_hash, slot, at = row.get("raw_sha256"), row.get("slot"), row.get("at")
    if (not _signature(signature) or not valid_pubkey(wallet) or type(slot) is not int or slot < 0
            or not isinstance(expected_hash, str) or re.fullmatch(r"[a-f0-9]{64}", expected_hash) is None
            or (at is not None and type(at) is not int)):
        return unresolved("INDEX_IDENTITY_INCOMPLETE")
    try:
        tx = _read_original(archive_root, signature)
        tier = "CURRENT"
        if tx is None and legacy_archive_root is not None and legacy_archive_root != archive_root:
            tx = _read_original(legacy_archive_root, signature)
            tier = "LEGACY"
        if tx is None:
            return unavailable("ARCHIVE_NOT_FOUND")
        encoded = json.dumps(tx, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
        if hashlib.sha256(encoded).hexdigest() != expected_hash:
            return unresolved("ARCHIVE_HASH_MISMATCH")
    except (gzip.BadGzipFile, EOFError, zlib.error, *SOURCE_ERRORS):
        return unresolved("ARCHIVE_INVALID_JSON")
    except OSError:
        return unavailable("ARCHIVE_FILE_UNAVAILABLE")

    try:
        signatures = tx["transaction"]["signatures"]
        if not isinstance(signatures, list) or not signatures or signatures[0] != signature:
            return unresolved("ARCHIVE_SIGNATURE_MISMATCH")
        if type(tx.get("slot")) is not int or tx["slot"] != slot:
            return unresolved("ARCHIVE_SLOT_MISMATCH")
        raw_time = tx.get("blockTime")
        if raw_time != at or (raw_time is not None and type(raw_time) is not int):
            return unresolved("ARCHIVE_TIME_MISMATCH")
        names = [key["pubkey"] for key in tx["transaction"]["message"]["accountKeys"]]
        if names.count(wallet) != 1 or len(set(names)) != len(names):
            return unresolved("ARCHIVE_WALLET_MISMATCH")
        result["raw_sha256"] = expected_hash
        result["archive_tier"] = tier
        result["block_time_status"] = "MATCHED" if at is not None else "UNKNOWN"
        replay = classify(signature, tx, wallet)
        evidence = replay.get("evidence")
        if not isinstance(evidence, dict):
            return unresolved("ARCHIVE_METADATA_UNSUPPORTED")
        projected = build_fact({**row, "parser_version": PARSER_VERSION}, evidence, [])
        if projected["coverage"]["normalized_evidence"] != "BOUND":
            return unresolved("ARCHIVE_PROJECTION_UNVERIFIED")
        effect = {"SUCCEEDED": "EXECUTED", "FAILED": "ATTEMPT_ONLY"}.get(projected["execution_status"],
                                                                         "UNRESOLVED")
        transfers, component = _native_transfers(tx, names, wallet, signature, effect)
        projected["native_transfers"] = transfers
        projected["coverage"]["components"]["native_transfers"] = component
        projected["coverage"]["native_transfer_scope"] = "PARSED_SYSTEM_TRANSFER_WALLET_ENDPOINTS"
        projected["fee"]["payer_account"] = names[0] if valid_pubkey(names[0]) else None
        for balance in projected["token_account_balances"] or []:
            account = names[balance["account_index"]]
            balance["account"] = account if valid_pubkey(account) else None
        instructions = tuple(_instructions(tx))
        _supplement_transfers(projected, instructions, names, wallet, signature, effect)
        projected["account_close_refunds"] = _close_refunds(tx, instructions, names, wallet, effect)
        projected["economic_exchange"] = _verified_exchange(replay, projected)
        projected["source_ref"]["scope"] = "LOCAL_HASH_VERIFIED_ARCHIVED_TRANSACTION"
        # Indexed trade rows belong to the original projection. An empty list
        # here would be ambiguous about whether the current parser found trades.
        del projected["trade_legs"], projected["coverage"]["trade_amount_scope"]
        del projected["coverage"]["components"]["trade_legs"]
        projected["account_funding"] = ata_account_funding(tx, wallet)
    except SOURCE_ERRORS:
        return unresolved("ARCHIVE_METADATA_UNSUPPORTED")
    replayed_class = replay["classification"]
    reason = replay.get("classification_reason")
    return {**result, "status": "VERIFIED", "reason": "ARCHIVE_HASH_AND_IDENTITY_VERIFIED",
            "replayed_class": replayed_class if replayed_class in CLASSES | {"FEE"} else "OTHER_OR_UNKNOWN",
            "replayed_reason": reason if isinstance(reason, str) and re.fullmatch(r"[A-Z0-9_]{1,96}", reason) else None,
            "fact": projected}
