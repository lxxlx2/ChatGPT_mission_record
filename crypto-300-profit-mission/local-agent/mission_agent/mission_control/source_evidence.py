"""Pure evidence/precision contracts for Frank's derived, read-only facts.

No clock, transport, file or repository is opened here.  The caller owns capture
and trust: a matching content hash proves byte identity, not provider honesty.
Public references contain opaque IDs and hashes, never request arguments,
endpoint credentials, raw response bodies or private receipt paths.
"""
from __future__ import annotations

import hashlib
import math
import re
import uuid
from decimal import Decimal, InvalidOperation
from typing import Any

from ..hashing import canonical

U64_MAX = 2**64 - 1
_INTEGER = re.compile(r"(?:0|[1-9][0-9]*)\Z")
_SIGNED_INTEGER = re.compile(r"(?:0|-?[1-9][0-9]*)\Z")
_METHOD = re.compile(r"[A-Za-z][A-Za-z0-9_.]*\Z")
_CODE = re.compile(r"[A-Z][A-Z0-9_]*\Z")
_DECIMAL = re.compile(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?\Z")
COVERAGE_STATUSES = frozenset({
    "COMPLETE_WITHIN_SCOPE", "PARTIAL", "UNAVAILABLE", "NOT_SUPPORTED", "NOT_REQUESTED",
})
_COMMITMENTS = frozenset({"processed", "confirmed", "finalized"})
_SAFE_SOURCE_ERRORS = frozenset({
    "HTTP_400", "HTTP_401", "HTTP_403", "HTTP_404", "HTTP_408", "HTTP_413",
    "HTTP_429", "HTTP_500", "HTTP_502", "HTTP_503", "HTTP_504",
    "RPC_RATE_LIMITED", "RESPONSE_INVALID", "SOURCE_UNAVAILABLE",
    "SOURCE_TIMEOUT", "CONNECTION_ERROR", "JSON_INVALID",
})


class SourceEvidenceError(ValueError):
    """Errors use fixed internal codes and never include rejected input."""


def _fail(code: str):
    raise SourceEvidenceError(code)


def _plain(value: Decimal) -> str:
    if value == 0:
        return "0"
    text = format(value, "f")
    return text.rstrip("0").rstrip(".") if "." in text else text


def decimal_string(value: Any, *, positive: bool = False,
                   nonnegative: bool = False) -> str:
    """Canonical finite decimal amount.  Float/bool coercion is forbidden."""
    if isinstance(value, bool) or not isinstance(value, (str, int, Decimal)):
        _fail("DECIMAL_INVALID")
    if isinstance(value, str) and not _DECIMAL.fullmatch(value):
        _fail("DECIMAL_INVALID")
    try:
        number = Decimal(value)
    except (InvalidOperation, ValueError, TypeError):
        _fail("DECIMAL_INVALID")
    if not number.is_finite():
        _fail("DECIMAL_NOT_FINITE")
    if positive and number <= 0:
        _fail("DECIMAL_NOT_POSITIVE")
    if nonnegative and number < 0:
        _fail("DECIMAL_NEGATIVE")
    return _plain(number)


def raw_amount(value: Any, *, signed: bool = False) -> str:
    """Validate a Solana u64 balance or a signed difference of two u64s."""
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        _fail("RAW_AMOUNT_INVALID")
    text = str(value)
    if not (_SIGNED_INTEGER if signed else _INTEGER).fullmatch(text):
        _fail("RAW_AMOUNT_INVALID")
    try:
        number = int(text)
    except ValueError:
        _fail("RAW_AMOUNT_INVALID")
    if number > U64_MAX or number < (-U64_MAX if signed else 0):
        _fail("RAW_AMOUNT_OUT_OF_U64_RANGE")
    return text


def token_amount(value: Any, decimals: int) -> dict:
    """Exact strings, independent of the process Decimal precision setting."""
    raw = raw_amount(value)
    if type(decimals) is not int or not 0 <= decimals <= 255:
        _fail("TOKEN_DECIMALS_INVALID")
    # decimals is the on-chain u8 Mint field.  String placement, rather than
    # Decimal division, keeps every digit even under a low global context.
    if not decimals:
        ui = raw
    else:
        padded = raw.zfill(decimals + 1)
        ui = padded[:-decimals] + "." + padded[-decimals:]
        ui = ui.rstrip("0").rstrip(".")
    return {"raw_amount": raw, "decimals": decimals, "ui_amount": ui or "0"}


def timestamp(value: Any) -> str:
    """Finite nonnegative epoch; clocks may supply floats, amounts may not."""
    if isinstance(value, float):
        if not math.isfinite(value):
            _fail("TIMESTAMP_INVALID")
        value = str(value)
    try:
        return decimal_string(value, nonnegative=True)
    except SourceEvidenceError:
        _fail("TIMESTAMP_INVALID")


def provider_id(identity: str) -> str:
    """Opaque stable fingerprint; endpoint/key text is never returned."""
    if not isinstance(identity, str) or not identity.strip():
        _fail("PROVIDER_IDENTITY_INVALID")
    return "provider_" + hashlib.sha256(identity.encode("utf-8")).hexdigest()


def build_source_ref(*, provider_identity: str, method: str, params: Any,
                     response_bytes: bytes, observed_at: Any, received_at: Any,
                     slot: int | None = None, commitment: str | None = None,
                     receipt_id: str | None = None) -> dict:
    """Bind exact captured bytes and canonical request to an explicit clock.

    A cached response must reuse its original observed/received values.  A GET
    may add a separate served_at at the envelope level; this function never
    treats a new read of old bytes as a new source observation.
    """
    if not isinstance(method, str) or not _METHOD.fullmatch(method):
        _fail("SOURCE_METHOD_INVALID")
    if not isinstance(response_bytes, bytes):
        _fail("SOURCE_RESPONSE_BYTES_REQUIRED")
    observed, received = timestamp(observed_at), timestamp(received_at)
    if Decimal(observed) > Decimal(received):
        _fail("SOURCE_CLOCK_ORDER_INVALID")
    if slot is not None and (type(slot) is not int or slot < 0):
        _fail("SOURCE_SLOT_INVALID")
    if commitment is not None and (
        not isinstance(commitment, str) or commitment not in _COMMITMENTS
    ):
        _fail("SOURCE_COMMITMENT_INVALID")
    if receipt_id is not None:
        try:
            if not isinstance(receipt_id, str) or str(uuid.UUID(receipt_id)) != receipt_id:
                _fail("SOURCE_RECEIPT_ID_INVALID")
        except (ValueError, AttributeError, TypeError):
            _fail("SOURCE_RECEIPT_ID_INVALID")
    try:
        request_hash = hashlib.sha256(canonical({"method": method, "params": params})).hexdigest()
    except (ValueError, TypeError, OverflowError, RecursionError):
        _fail("SOURCE_REQUEST_INVALID")
    return {
        "schema_version": 1, "provider_id": provider_id(provider_identity),
        "method": method, "request_hash": request_hash,
        "response_sha256": hashlib.sha256(response_bytes).hexdigest(),
        "observed_at": observed, "received_at": received,
        "slot": slot, "commitment": commitment, "receipt_id": receipt_id,
    }


def coverage(scope: str, *, enumeration_status: str = "NOT_REQUESTED",
             history_status: str = "NOT_REQUESTED",
             classification_status: str = "NOT_REQUESTED",
             parity_status: str = "NOT_REQUESTED", missing_items=(),
             stop_reason: str | None = None) -> dict:
    """Dimension-wise completeness: no derived 'all chain complete' boolean."""
    if not isinstance(scope, str) or not _CODE.fullmatch(scope):
        _fail("COVERAGE_SCOPE_INVALID")
    statuses = {
        "enumeration_status": enumeration_status, "history_status": history_status,
        "classification_status": classification_status, "parity_status": parity_status,
    }
    if any(not isinstance(s, str) or s not in COVERAGE_STATUSES for s in statuses.values()):
        _fail("COVERAGE_STATUS_INVALID")
    if not isinstance(missing_items, (list, tuple)) or any(
        not isinstance(x, str) or not _CODE.fullmatch(x) for x in missing_items
    ):
        _fail("COVERAGE_MISSING_ITEMS_INVALID")
    if stop_reason is not None and (
        not isinstance(stop_reason, str) or not _CODE.fullmatch(stop_reason)
    ):
        _fail("COVERAGE_STOP_REASON_INVALID")
    return {"scope": scope, **statuses, "missing_items": list(dict.fromkeys(missing_items)),
            "stop_reason": stop_reason}


def safe_source_error(error: BaseException | str) -> str:
    """Whitelist transport codes; never reflect untrusted exception text."""
    if isinstance(error, TimeoutError):
        return "SOURCE_TIMEOUT"
    if isinstance(error, str):
        return error if error in _SAFE_SOURCE_ERRORS else "SOURCE_UNAVAILABLE"
    # urllib HTTPError and injected transports expose numeric .code.  Ignore
    # strings and bools to avoid reflecting arbitrary labels or request URLs.
    code = getattr(error, "code", None)
    if type(code) is int and "HTTP_" + str(code) in _SAFE_SOURCE_ERRORS:
        return "HTTP_" + str(code)
    if isinstance(error, ConnectionError):
        return "CONNECTION_ERROR"
    return "SOURCE_UNAVAILABLE"
