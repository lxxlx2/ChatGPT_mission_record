"""Frank D2: manually imported, private, immutable at-slot projection GET source.

Only the already audited PR60 offline replay may create a projection; this
module neither fetches RPC nor imports data automatically. No SQL, writers,
signals, notifications, prices, PnL, trading, or continuous balance claims.
"""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import stat
import time

from .wallet_owner_at_slot import (
    FRANK_WALLET, PROGRAMS, _mint_key, _utc,
    project_replayed_owner,
)

SOURCE_NAME = "frank-d2-owner-at-slot.json"
SOURCE_KIND = "PR60_OFFLINE_VERIFIED_FULL_OWNER_TWO_PROGRAMS"
STATUS = "BALANCE_AT_OBSERVED_FINALIZED_SLOTS_NOT_LIVE"
MAX_SOURCE_BYTES = 4_000_000
MAX_MINTS = 50_000
PAGE_SIZE = 100


class D2IngressError(ValueError):
    """Untrusted, missing, inconsistent, or unsafe at-slot projection."""


def _need(condition, reason):
    if not condition:
        raise D2IngressError(reason)


def _digest(doc):
    """Accidental modification check, NOT a source signature or authentication."""
    subset = {k: v for k, v in doc.items() if k != "document_sha256"}
    raw = json.dumps(subset, sort_keys=True, separators=(",", ":"),
                     ensure_ascii=False, allow_nan=False).encode("utf-8")
    return sha256(raw).hexdigest()


def build_d2_document_from_verified_pr60_replay(snapshot):
    """Only call after PR60's pinned original raw-receipt offline replay.

    A full source covers *each Token Account*, not only a previous 200-row
    HTML subset. Omit token_account pubkeys from this derived private document.
    """
    proof = project_replayed_owner(snapshot, {"rows": []}, target_mints=())
    records = []
    for item in snapshot["mints"]:
        mint = item["mint"]
        accounts = item["token_accounts"]
        programs = sorted({account["program_id"] for account in accounts})
        _need(programs and all(p in PROGRAMS for p in programs),
              "UNEXPECTED_ACCOUNT_PROGRAM")
        records.append({
            "mint": mint,
            "raw_amount": item["raw_amount_observed_sum"],
            "decimals": item["decimals"],
            "account_count": len(accounts),
            "program_ids": programs,
            "slot_min": item["slot_min"],
            "slot_max": item["slot_max"],
        })
    records.sort(key=lambda x: x["mint"])
    doc = {
        "schema_version": 1,
        "source_kind": SOURCE_KIND,
        "status": STATUS,
        "wallet": FRANK_WALLET,
        "source_capture_sha256": proof["source_capture_sha256"],
        "observed_at_utc": proof["observed_at_utc"],
        "program_coverage": proof["program_coverage"],
        "same_slot_atomic": False,
        "current_chain_balance_verified": False,
        "usd_value_verified": False,
        "pnl_verified": False,
        "account_count": proof["account_count"],
        "mint_count": proof["mint_count"],
        "nonzero_mint_count": proof["nonzero_mint_count"],
        "mints": records,
    }
    doc["document_sha256"] = _digest(doc)
    validate_d2_document(doc)
    return doc


def validate_d2_document(doc):
    _need(isinstance(doc, dict) and doc.get("schema_version") == 1 and
          doc.get("source_kind") == SOURCE_KIND and
          doc.get("status") == STATUS and
          doc.get("wallet") == FRANK_WALLET,
          "D2_SCHEMA_OR_OWNER_INVALID")
    # Do not admit hidden private metadata under a self-recomputed checksum.
    _need(set(doc) == {
        "schema_version", "source_kind", "status", "wallet",
        "source_capture_sha256", "observed_at_utc", "program_coverage",
        "same_slot_atomic", "current_chain_balance_verified",
        "usd_value_verified", "pnl_verified", "account_count",
        "mint_count", "nonzero_mint_count", "mints", "document_sha256",
    }, "D2_DOCUMENT_FIELDS_INVALID")
    _need(doc.get("same_slot_atomic") is False and
          doc.get("current_chain_balance_verified") is False and
          doc.get("usd_value_verified") is False and
          doc.get("pnl_verified") is False,
          "D2_SOURCE_MUST_BE_DATED_UNPRICED")
    fingerprint = doc.get("source_capture_sha256")
    checksum = doc.get("document_sha256")
    _need(isinstance(fingerprint, str) and len(fingerprint) == 64 and
          all(c in "0123456789abcdef" for c in fingerprint),
          "D2_PROVENANCE_DIGEST_INVALID")
    _need(isinstance(checksum, str) and len(checksum) == 64 and
          checksum == _digest(doc), "D2_DOCUMENT_DIGEST_MISMATCH")
    try:
        observed = _utc(doc.get("observed_at_utc"))
    except (ValueError, TypeError) as exc:
        raise D2IngressError("D2_OBSERVATION_TIME_INVALID") from exc
    _need(observed.timestamp() <= time.time() + 60, "D2_FUTURE_OBSERVATION")
    covers = doc.get("program_coverage")
    _need(isinstance(covers, list) and len(covers) == 2, "D2_TWO_PROGRAMS_REQUIRED")
    slot_by_program = {}
    count = 0
    for program, row in zip(PROGRAMS, covers):
        _need(isinstance(row, dict) and
              set(row) == {"program_id", "slot", "account_count"} and
              row.get("program_id") == program and
              type(row.get("slot")) is int and row["slot"] > 0 and
              type(row.get("account_count")) is int and
              0 <= row["account_count"] <= MAX_MINTS,
              "D2_PROGRAM_PROVENANCE_INVALID")
        slot_by_program[program] = row["slot"]
        count += row["account_count"]
    _need(slot_by_program[PROGRAMS[0]] <= slot_by_program[PROGRAMS[1]],
          "D2_PROGRAM_SLOT_ORDER_INVALID")
    mints = doc.get("mints")
    _need(isinstance(mints, list) and len(mints) <= MAX_MINTS,
          "D2_MINT_LIST_INVALID")
    _need(type(doc.get("account_count")) is int and
          doc["account_count"] == count and
          type(doc.get("mint_count")) is int and
          doc["mint_count"] == len(mints) and
          type(doc.get("nonzero_mint_count")) is int,
          "D2_SUMMARY_COUNT_INVALID")
    seen, unique_accounts, observed_nonzero = set(), 0, 0
    accounts_by_program = {p: 0 for p in PROGRAMS}
    for row in mints:
        _need(isinstance(row, dict) and
              set(row) == {"mint", "raw_amount", "decimals", "account_count",
                           "program_ids", "slot_min", "slot_max"},
              "D2_MINT_ROW_SCHEMA_INVALID")
        mint = row["mint"]
        raw = row["raw_amount"]
        programs = row["program_ids"]
        _need(_mint_key(mint) and mint not in seen,
              "D2_MINT_IDENTITY_DUPLICATE_OR_INVALID")
        seen.add(mint)
        _need(isinstance(raw, str) and raw.isascii() and raw.isdecimal() and
              (raw == "0" or not raw.startswith("0")) and
              type(row["decimals"]) is int and 0 <= row["decimals"] <= 18 and
              type(row["account_count"]) is int and row["account_count"] > 0,
              "D2_MINT_QUANTITY_INVALID")
        # A Solana Mint account belongs to one token program; ambiguous
        # cross-program aggregates lack a verifiable per-program allocation.
        _need(isinstance(programs, list) and len(programs) == 1 and
              all(p in slot_by_program for p in programs),
              "D2_MINT_PROGRAM_INVALID")
        declared_slots = sorted(slot_by_program[p] for p in programs)
        _need(type(row["slot_min"]) is int and
              type(row["slot_max"]) is int and
              row["slot_min"] == declared_slots[0] and
              row["slot_max"] == declared_slots[-1],
              "D2_MINT_SLOT_INVALID")
        unique_accounts += row["account_count"]
        accounts_by_program[programs[0]] += row["account_count"]
        observed_nonzero += int(int(raw) > 0)
    _need(unique_accounts == count and
          observed_nonzero == doc["nonzero_mint_count"],
          "D2_MINT_ACCOUNT_AGGREGATES_INVALID")
    _need(all(accounts_by_program[p] == cover["account_count"]
              for p, cover in zip(PROGRAMS, covers)),
          "D2_PROGRAM_ACCOUNT_AGGREGATES_INVALID")
    return doc


def _unavailable(reason):
    return {
        "status": "SOURCE_NOT_IMPORTED" if reason == "SOURCE_NOT_IMPORTED"
                  else "SOURCE_REJECTED",
        "reason": reason,
        "scope": "MANUAL_PRIVATE_D2_SOURCE_ONLY",
        "current_chain_balance_verified": False,
        "rows": [],
    }


def read_d2_source(control_root: Path):
    """Read only one allowlisted private file. No scanning, fallback or writes."""
    path = Path(control_root) / SOURCE_NAME
    try:
        info = path.lstat()
    except FileNotFoundError:
        return None, _unavailable("SOURCE_NOT_IMPORTED")
    except OSError:
        return None, _unavailable("D2_PRIVATE_SOURCE_UNREADABLE")
    if not stat.S_ISREG(info.st_mode) or info.st_mode & 0o077:
        return None, _unavailable("D2_SOURCE_TYPE_OR_PERMISSIONS_INVALID")
    if path.parent.is_symlink():
        return None, _unavailable("D2_PARENT_SYMLINK_INVALID")
    try:
        if path.parent.stat().st_mode & 0o077:
            return None, _unavailable("D2_PARENT_NOT_PRIVATE")
        if not 0 < info.st_size <= MAX_SOURCE_BYTES:
            return None, _unavailable("D2_SIZE_INVALID")
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        fd = os.open(path, flags)
        with os.fdopen(fd, "rb") as handle:
            current = os.fstat(handle.fileno())
            if not stat.S_ISREG(current.st_mode) or current.st_mode & 0o077:
                return None, _unavailable("D2_CHANGED_FILE_PERMISSIONS")
            raw = handle.read(MAX_SOURCE_BYTES + 1)
        if len(raw) > MAX_SOURCE_BYTES:
            return None, _unavailable("D2_SIZE_INVALID")
        parsed = json.loads(raw)
        validate_d2_document(parsed)
        return parsed, None
    except (OSError, ValueError, TypeError, OverflowError, KeyError):
        return None, _unavailable("D2_INVALID_PRIVATE_DOCUMENT")


def query_d2(control_root: Path, *, mint=None, page=0):
    """Explicit exact Mint or one bounded page; never stream entire inventory."""
    if mint is not None:
        if not _mint_key(mint):
            raise D2IngressError("INVALID_D2_MINT")
    else:
        if type(page) is not int or not (0 <= page <= 999):
            raise D2IngressError("INVALID_D2_PAGE")
    doc, failure = read_d2_source(control_root)
    if failure is not None:
        return failure
    observed = _utc(doc["observed_at_utc"])
    metadata = {
        "status": STATUS,
        "scope": "TWO_PROGRAMS_AT_SEPARATE_FINALIZED_SLOTS_NOT_LIVE",
        "source_kind": doc["source_kind"],
        "source_capture_sha256": doc["source_capture_sha256"],
        "source_document_sha256": doc["document_sha256"],
        "observed_at_utc": doc["observed_at_utc"],
        "observed_at_bangkok": observed.astimezone(
            __import__("zoneinfo").ZoneInfo("Asia/Bangkok")).isoformat(),
        "age_seconds_at_response": max(0, int(time.time() - observed.timestamp())),
        # Defense in depth: never serialize unchecked source objects.
        "program_coverage": [
            {"program_id": p, "slot": row["slot"],
             "account_count": row["account_count"]}
            for p, row in zip(PROGRAMS, doc["program_coverage"])
        ],
        "same_slot_atomic": False,
        "current_chain_balance_verified": False,
        "usd_value_verified": False,
        "pnl_verified": False,
        "account_count": doc["account_count"],
        "mint_count": doc["mint_count"],
        "nonzero_mint_count": doc["nonzero_mint_count"],
        "page_size": PAGE_SIZE,
    }
    mints = doc["mints"]
    if mint is not None:
        row = next((x for x in mints if x["mint"] == mint), None)
        return {
            **metadata,
            "lookup_mint": mint,
            "lookup_state": ("NONZERO_AT_SLOT" if int(row["raw_amount"]) else
                             "ZERO_AT_SLOT") if row else
                            "NO_ACTIVE_OWNER_TOKEN_ACCOUNT_OBSERVED_AT_SLOTS",
            "rows": [row] if row else [],
            "result_count": int(row is not None),
        }
    start = page * PAGE_SIZE
    # Even a 50,000-row imported document produces at most 100 rows per GET.
    return {
        **metadata,
        "page": page,
        "total_pages": (len(mints) + PAGE_SIZE - 1) // PAGE_SIZE,
        "rows": mints[start:start + PAGE_SIZE],
        "result_count": len(mints[start:start + PAGE_SIZE]),
    }
