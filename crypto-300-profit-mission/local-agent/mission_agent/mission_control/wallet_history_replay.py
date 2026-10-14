"""A04 manual finalized Solana signature pagination with crash-safe research journal.

The source chain is never altered. This module consumes an injected RPC reader,
writes only an independently selected research sidecar, and never authorizes
signals, trades, email or reconciliation. A provider pagination end is NOT
proof of complete chain history or complete wallet economic attribution.
"""
from __future__ import annotations

import hashlib
import json
from typing import Callable

from .person_registry import _solana_pubkey_32_bytes
from .wallet_economic_ledger import normalize_transaction, LedgerEvidenceError


_BASE58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
_HISTORY_SCHEMA = """
CREATE TABLE IF NOT EXISTS wallet_history_cursor (
    wallet TEXT PRIMARY KEY,
    next_before TEXT,
    pagination_end_observed INTEGER NOT NULL DEFAULT 0,
    page_count INTEGER NOT NULL DEFAULT 0,
    last_error_code TEXT
);
CREATE TABLE IF NOT EXISTS wallet_history_page (
    wallet TEXT NOT NULL,
    request_cursor TEXT NOT NULL,
    response_sha256 TEXT NOT NULL,
    next_before TEXT,
    account_count INTEGER NOT NULL,
    PRIMARY KEY(wallet, request_cursor)
);
CREATE TABLE IF NOT EXISTS wallet_history_signature (
    wallet TEXT NOT NULL,
    signature TEXT NOT NULL,
    slot INTEGER NOT NULL,
    state TEXT NOT NULL CHECK(state IN ('PENDING','CAPTURED')),
    error_code TEXT,
    PRIMARY KEY(wallet,signature)
);
CREATE INDEX IF NOT EXISTS wallet_history_pending_idx
    ON wallet_history_signature(wallet,state,slot DESC);
"""


class SourceEvidenceError(ValueError):
    """A failed source read or contradictory evidence cannot advance history."""


class SourceTemporarilyUnavailable(RuntimeError):
    """A retryable source error (e.g. 429, timeout, null transaction)."""


def _json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _hash(value: object) -> str:
    return hashlib.sha256(_json(value).encode("utf-8")).hexdigest()


def _signature(value: object) -> str:
    if not isinstance(value, str) or not 64 <= len(value) <= 88:
        raise SourceEvidenceError("INVALID_SIGNATURE_FORMAT")
    try:
        total = 0
        for char in value:
            total = total * 58 + _BASE58.index(char)
    except ValueError as exc:
        raise SourceEvidenceError("INVALID_SIGNATURE_FORMAT") from exc
    zeroes = len(value) - len(value.lstrip("1"))
    if zeroes + (total.bit_length() + 7) // 8 != 64:
        raise SourceEvidenceError("INVALID_SIGNATURE_WIDTH")
    return value


def _slot(value: object) -> int:
    if type(value) is not int or value <= 0:
        raise SourceEvidenceError("INVALID_TRANSACTION_SLOT")
    return value


def _rpc_result(body: object, method: str) -> object:
    if not isinstance(body, dict):
        raise SourceTemporarilyUnavailable(method + "_RPC_UNAVAILABLE")
    if "error" in body:
        rpc_error = body.get("error")
        code = rpc_error.get("code") if isinstance(rpc_error, dict) else None
        if code == 429:
            raise SourceTemporarilyUnavailable("RPC_RATE_LIMIT_429")
        if code == 403:
            raise SourceTemporarilyUnavailable("RPC_DENIED_403")
        raise SourceTemporarilyUnavailable(method + "_RPC_UNAVAILABLE")
    if "result" not in body:
        raise SourceTemporarilyUnavailable(method + "_RPC_UNAVAILABLE")
    return body["result"]


def _source_error_code(exc: Exception) -> str:
    """Persist code-controlled reasons only, never provider exception text."""
    if isinstance(exc, SourceTemporarilyUnavailable):
        reason = str(exc)
        if reason in {"RPC_RATE_LIMIT_429", "RPC_DENIED_403",
                      "SIGNATURE_PAGE_RPC_UNAVAILABLE",
                      "TRANSACTION_RPC_UNAVAILABLE", "TRANSACTION_NOT_AVAILABLE"}:
            return reason
        return "RPC_UNAVAILABLE"
    if isinstance(exc, SourceEvidenceError):
        reason = str(exc)
        if reason.isascii() and reason.isupper() and len(reason) <= 80:
            return reason
        return "SOURCE_EVIDENCE_INVALID"
    if isinstance(exc, LedgerEvidenceError):
        return "TRANSACTION_NORMALIZATION_INCOMPLETE"
    if isinstance(exc, TimeoutError):
        return "RPC_TIMEOUT"
    return "RPC_UNAVAILABLE"


class HistoryJournal:
    """Sidecar-backed, local-only cursor and signature/tx transaction journal.

    The global RAW_TX identity is independent of which tracked wallet first
    discovered the transaction. A WALLET_TX_VIEW is deliberately wallet-scoped
    so partial token legs never masquerade as a complete transaction view.
    """

    def __init__(self, evidence_store):
        if evidence_store.read_only:
            raise PermissionError("READ_ONLY_SIDECAR")
        self.db = evidence_store.db
        self.db.executescript(_HISTORY_SCHEMA)

    def state(self, wallet: str) -> dict:
        if not _solana_pubkey_32_bytes(wallet):
            raise ValueError("INVALID_RESEARCH_WALLET")
        current = self.db.execute(
            "SELECT * FROM wallet_history_cursor WHERE wallet=?", (wallet,),
        ).fetchone()
        counts = self.db.execute(
            "SELECT state,COUNT(*) AS n FROM wallet_history_signature "
            "WHERE wallet=? GROUP BY state", (wallet,),
        ).fetchall()
        c = {row["state"]: row["n"] for row in counts}
        return {
            "wallet": wallet,
            "next_before": current["next_before"] if current else None,
            "pagination_end_observed": bool(current["pagination_end_observed"]) if current else False,
            "page_count": current["page_count"] if current else 0,
            "last_error_code": current["last_error_code"] if current else None,
            "captured": c.get("CAPTURED", 0),
            "pending": c.get("PENDING", 0),
            "history_complete": False,
            "coverage": ("AVAILABLE_SOURCE_END_NOT_GENESIS_PROVEN"
                         if current and current["pagination_end_observed"] and not c.get("PENDING")
                         else "PARTIAL"),
            "cost_basis_usd": None,
            "realized_pnl_usd": None,
        }

    def record_error(self, wallet: str, code: str) -> None:
        if not isinstance(code, str) or not code.isascii() or not code.isupper():
            raise ValueError("INVALID_SOURCE_ERROR_CODE")
        with self.db:
            self.db.execute(
                "INSERT INTO wallet_history_cursor(wallet,last_error_code) VALUES(?,?) "
                "ON CONFLICT(wallet) DO UPDATE SET last_error_code=excluded.last_error_code",
                (wallet, code),
            )

    def record_page(self, wallet: str, before: str | None, rows: list) -> None:
        state = self.state(wallet)
        if state["pagination_end_observed"] or state["next_before"] != before:
            raise SourceEvidenceError("PAGINATION_CURSOR_MISMATCH")
        if not isinstance(rows, list) or len(rows) > 1000:
            raise SourceEvidenceError("INVALID_SIGNATURE_PAGE")
        seen, previous_slot, sanitized = set(), None, []
        for entry in rows:
            if not isinstance(entry, dict):
                raise SourceEvidenceError("INVALID_SIGNATURE_ROW")
            sig = _signature(entry.get("signature"))
            slot = _slot(entry.get("slot"))
            if sig in seen or sig == before:
                raise SourceEvidenceError("DUPLICATE_OR_LOOPED_SIGNATURE_PAGE")
            if previous_slot is not None and slot > previous_slot:
                raise SourceEvidenceError("PAGE_NOT_NEWEST_FIRST")
            status = entry.get("confirmationStatus")
            if status not in (None, "finalized"):
                raise SourceEvidenceError("SIGNATURE_NOT_FINALIZED")
            seen.add(sig)
            previous_slot = slot
            sanitized.append((sig, slot))
        last = sanitized[-1][0] if sanitized else before
        request_cursor = before or "HEAD"
        page_hash = _hash(sanitized)
        # Write page fingerprint, all signatures and next cursor in ONE DB
        # transaction; a crash cannot move cursor past missing signatures.
        with self.db:
            old = self.db.execute(
                "SELECT response_sha256 FROM wallet_history_page "
                "WHERE wallet=? AND request_cursor=?", (wallet, request_cursor)
            ).fetchone()
            if old is not None:
                if old["response_sha256"] != page_hash:
                    raise SourceEvidenceError("CONFLICTING_SOURCE_PAGE")
                raise SourceEvidenceError("SOURCE_PAGE_ALREADY_CAPTURED")
            for sig, slot in sanitized:
                old_row = self.db.execute(
                    "SELECT slot FROM wallet_history_signature WHERE wallet=? AND signature=?",
                    (wallet, sig),
                ).fetchone()
                if old_row is not None:
                    raise SourceEvidenceError("PAGE_OVERLAPS_CAPTURED_SIGNATURES")
                self.db.execute(
                    "INSERT INTO wallet_history_signature(wallet,signature,slot,state) "
                    "VALUES(?,?,?,'PENDING')", (wallet, sig, slot),
                )
            self.db.execute(
                "INSERT INTO wallet_history_page(wallet,request_cursor,response_sha256,"
                "next_before,account_count) VALUES(?,?,?,?,?)",
                (wallet, request_cursor, page_hash, last, len(sanitized)),
            )
            self.db.execute(
                "INSERT INTO wallet_history_cursor(wallet,next_before,pagination_end_observed,"
                "page_count,last_error_code) VALUES(?,?,?,?,NULL) "
                "ON CONFLICT(wallet) DO UPDATE SET "
                "next_before=excluded.next_before,"
                "pagination_end_observed=excluded.pagination_end_observed,"
                "page_count=wallet_history_cursor.page_count+1,last_error_code=NULL",
                (wallet, last, int(not sanitized), 1),
            )

    def next_pending(self, wallet: str) -> dict | None:
        row = self.db.execute(
            "SELECT signature,slot,error_code FROM wallet_history_signature "
            "WHERE wallet=? AND state='PENDING' ORDER BY slot DESC,signature LIMIT 1",
            (wallet,),
        ).fetchone()
        return dict(row) if row else None

    def record_transaction(self, wallet: str, signature: str,
                           raw: dict, wallet_view: dict) -> None:
        pending = self.db.execute(
            "SELECT slot,state FROM wallet_history_signature WHERE wallet=? AND signature=?",
            (wallet, signature),
        ).fetchone()
        if pending is None or pending["state"] != "PENDING":
            raise SourceEvidenceError("TRANSACTION_NOT_PENDING")
        slot = pending["slot"]
        if raw.get("slot") != slot or wallet_view.get("slot") != slot:
            raise SourceEvidenceError("TRANSACTION_SLOT_MISMATCH")
        if (raw.get("transaction") or {}).get("signatures", [None])[0] != signature:
            raise SourceEvidenceError("TRANSACTION_SIGNATURE_MISMATCH")
        if wallet_view.get("signature") != signature:
            raise SourceEvidenceError("TRANSACTION_VIEW_IDENTITY_MISMATCH")
        view_hash = wallet_view.get("canonical_event_sha256")
        if view_hash != _hash({k: v for k, v in wallet_view.items()
                               if k != "canonical_event_sha256"}):
            raise SourceEvidenceError("WALLET_VIEW_HASH_MISMATCH")
        documents = (
            ("RAW_TX", signature + ":" + str(slot), raw),
            ("WALLET_TX_VIEW", wallet + ":" + signature + ":" + str(slot), wallet_view),
        )
        with self.db:
            for kind, identity, doc in documents:
                content = _json(doc)
                fingerprint = hashlib.sha256(content.encode("utf-8")).hexdigest()
                old = self.db.execute(
                    "SELECT source_sha256 FROM evidence_documents "
                    "WHERE kind=? AND identity=?", (kind, identity)
                ).fetchone()
                if old is not None and old["source_sha256"] != fingerprint:
                    raise SourceEvidenceError("IMMUTABLE_TRANSACTION_CONFLICT")
                if old is None:
                    self.db.execute(
                        "INSERT INTO evidence_documents(kind,identity,source_sha256,"
                        "payload_json) VALUES(?,?,?,?)",
                        (kind, identity, fingerprint, content),
                    )
            self.db.execute(
                "UPDATE wallet_history_signature SET state='CAPTURED',error_code=NULL "
                "WHERE wallet=? AND signature=?", (wallet, signature),
            )
            self.db.execute(
                "UPDATE wallet_history_cursor SET last_error_code=NULL WHERE wallet=?",
                (wallet,),
            )

    def pending_error(self, wallet: str, signature: str, code: str) -> None:
        if not isinstance(code, str) or not code.isascii() or not code.isupper():
            raise ValueError("INVALID_SOURCE_ERROR_CODE")
        with self.db:
            self.db.execute(
                "UPDATE wallet_history_signature SET error_code=? "
                "WHERE wallet=? AND signature=? AND state='PENDING'",
                (code, wallet, signature),
            )
            self.db.execute(
                "UPDATE wallet_history_cursor SET last_error_code=? WHERE wallet=?",
                (code, wallet),
            )


class WalletHistoryCollector:
    """Bounded manual historical backfill, resuming persisted exact cursors."""

    def __init__(self, journal: HistoryJournal, rpc: Callable, *,
                 wallet: str, page_size: int = 100):
        if not _solana_pubkey_32_bytes(wallet):
            raise ValueError("INVALID_RESEARCH_WALLET")
        if type(page_size) is not int or not 1 <= page_size <= 1000:
            raise ValueError("INVALID_PAGE_SIZE")
        self.journal, self.rpc = journal, rpc
        self.wallet, self.page_size = wallet, page_size

    def _signatures(self, cursor: str | None) -> list:
        config = {"limit": self.page_size, "commitment": "finalized"}
        if cursor is not None:
            config["before"] = cursor
        rows = _rpc_result(
            self.rpc("getSignaturesForAddress", [self.wallet, config]),
            "SIGNATURE_PAGE",
        )
        if not isinstance(rows, list):
            raise SourceEvidenceError("SIGNATURE_PAGE_FORMAT_INVALID")
        return rows

    def _transaction(self, signature: str, slot: int) -> tuple[dict, dict]:
        raw = _rpc_result(
            self.rpc("getTransaction", [signature, {
                "encoding": "jsonParsed",
                "commitment": "finalized",
                "maxSupportedTransactionVersion": 0,
            }]),
            "TRANSACTION",
        )
        if raw is None:
            raise SourceTemporarilyUnavailable("TRANSACTION_NOT_AVAILABLE")
        if not isinstance(raw, dict):
            raise SourceEvidenceError("TRANSACTION_FORMAT_INVALID")
        if raw.get("slot") != slot:
            raise SourceEvidenceError("TRANSACTION_SLOT_MISMATCH")
        view = normalize_transaction(raw, tracked_wallets={self.wallet})
        if view.get("signature") != signature:
            raise SourceEvidenceError("TRANSACTION_SIGNATURE_MISMATCH")
        return raw, view

    def collect(self, *, max_pages: int = 2, tx_budget: int = 100) -> dict:
        if (type(max_pages) is not int or not 0 <= max_pages <= 20 or
                type(tx_budget) is not int or not 0 <= tx_budget <= 2000):
            raise ValueError("INVALID_REPLAY_BUDGET")
        new_pages = 0
        imported = 0
        while True:
            state = self.journal.state(self.wallet)
            pending = self.journal.next_pending(self.wallet)
            if pending is not None:
                if imported >= tx_budget:
                    break
                sig, slot = pending["signature"], pending["slot"]
                try:
                    raw, view = self._transaction(sig, slot)
                    self.journal.record_transaction(self.wallet, sig, raw, view)
                except (SourceTemporarilyUnavailable, SourceEvidenceError,
                        LedgerEvidenceError, OSError, RuntimeError, ValueError) as exc:
                    self.journal.pending_error(
                        self.wallet, sig, _source_error_code(exc))
                    break
                imported += 1
                continue
            if state["pagination_end_observed"] or new_pages >= max_pages:
                break
            try:
                rows = self._signatures(state["next_before"])
                self.journal.record_page(self.wallet, state["next_before"], rows)
            except (SourceTemporarilyUnavailable, SourceEvidenceError,
                    OSError, RuntimeError, ValueError) as exc:
                self.journal.record_error(
                    self.wallet, _source_error_code(exc))
                break
            new_pages += 1
            if not rows:
                break
        result = self.journal.state(self.wallet)
        result.update({
            "pages_fetched_this_run": new_pages,
            "transactions_imported_this_run": imported,
            "status": ("SOURCE_LIMITED" if result["last_error_code"]
                       else "AVAILABLE_SOURCE_END_NOT_GENESIS_PROVEN"
                       if result["pagination_end_observed"] and result["pending"] == 0
                       else "PARTIAL"),
            "production_written": False,
            "signals_or_delivery_enabled": False,
        })
        return result
