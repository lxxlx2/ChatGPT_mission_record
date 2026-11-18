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

from ..frank.parser import PARSER_VERSION, _program_id
from ..hashing import digest
from ..meme.holder_ranks import ALPHABET, valid_pubkey
from ..signals.classifier import classify
from .archived_account_funding import ata_account_funding
from .ata_backfill import ASSOCIATED, PROGRAMS
from .wallet_activity import CLASSES, fixed_class
from .wallet_facts import _raw, build_fact

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


def read_archived_fact(archive_root, row):
    """Return a public, independent replay for one wallet_activity projection.

    Only the original canonical transaction digest is authoritative. The index
    classification remains available even when the original is unavailable.
    """
    indexed_class = fixed_class(row.get("class"))
    result = {"schema_version": ARCHIVE_VERSION, "parser_version": PARSER_VERSION,
              "indexed_class": indexed_class, "replayed_class": None, "replayed_reason": None, "raw_sha256": None,
              "block_time_status": "UNKNOWN", "fact": None}

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
