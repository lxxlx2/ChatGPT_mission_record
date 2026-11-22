"""Read-only coverage of Frank's locally indexed signatures."""
from __future__ import annotations

from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import sqlite3

from .wallet_activity import CLASSES, connect, fixed_class, safe_id
from .wallet_owner_at_slot import FRANK_WALLET


_PERSON = "frank"
_CATEGORIES = tuple(sorted(CLASSES | {"OTHER_OR_UNKNOWN"}))
_UNKNOWN = "UNKNOWN"
_SCANNER_ERRORS = {
    "ValueError:CURSOR_GAP_UNRESOLVED": "CURSOR_GAP_UNRESOLVED",
    "ValueError:RAW_UNAVAILABLE_CURSOR_NOT_ADVANCED": "RAW_UNAVAILABLE_CURSOR_NOT_ADVANCED",
    "ValueError:CHAIN_SLOT_CONFLICT": "CHAIN_SLOT_CONFLICT",
    "ValueError:CHAIN_SIGNATURE_CONFLICT": "CHAIN_SIGNATURE_CONFLICT",
}
_SHA256 = re.compile(r"[0-9a-f]{64}")


class CoverageError(ValueError):
    def __init__(self, code, http_status=400):
        self.code = code
        self.http_status = http_status
        super().__init__(code)


def _json_object(value):
    try:
        parsed = json.loads(value or "{}")
    except (TypeError, ValueError, RecursionError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _raw_ref(signature, raw_hash):
    signature = safe_id(signature)
    if signature and isinstance(raw_hash, str) and _SHA256.fullmatch(raw_hash):
        return {"signature": signature, "raw_sha256": raw_hash}
    return None


def _sql_columns(db, table):
    # Called with the fixed names of supported local source tables only.
    return {row[1] for row in db.execute(f"PRAGMA table_info({table})")}


def _fingerprint_line(digest, row):
    # Hex-encode BLOBs from old or malformed rows without interpreting them.
    values = [{"blob_hex": value.hex()} if isinstance(value, bytes) else value for value in row]
    digest.update(json.dumps(values, ensure_ascii=True, separators=(",", ":")).encode("ascii"))
    digest.update(b"\n")


def _index_coverage(db, as_of, start_at):
    columns = _sql_columns(db, "signatures")
    if not {"wallet", "signature", "person_id", "block_time", "body"}.issubset(columns):
        raise CoverageError("SOURCE_UNAVAILABLE", 503)
    raw_hash = "raw_hash" if "raw_hash" in columns else "NULL"
    timed = "typeof(block_time)='integer' AND block_time>=0"
    condition = f"NOT ({timed}) OR (block_time<=?"
    params = [_PERSON, as_of]
    if start_at is not None:
        condition += " AND block_time>=?"
        params.append(start_at)
    condition += ")"
    rows = db.execute(
        f"SELECT wallet,signature,block_time,body,{raw_hash} FROM signatures "
        f"WHERE person_id=? AND ({condition}) "
        "ORDER BY wallet COLLATE BINARY,signature COLLATE BINARY",
        params,
    )
    categories = dict.fromkeys(_CATEGORIES, 0)
    oldest = newest = oldest_ref = newest_ref = None
    timed_count = untimed_count = 0
    previous = None
    digest = hashlib.sha256()
    for row in rows:
        wallet, signature, at, body, raw_hash = row
        key = (wallet, signature)
        if key == previous:
            raise CoverageError("SOURCE_UNAVAILABLE", 503)
        previous = key
        _fingerprint_line(digest, row)
        if type(at) is int and at >= 0:
            timed_count += 1
            if oldest is None or at < oldest:
                oldest, oldest_ref = at, _raw_ref(signature, raw_hash)
            if newest is None or at > newest:
                newest, newest_ref = at, _raw_ref(signature, raw_hash)
        else:
            untimed_count += 1
            if start_at is not None:
                continue
        categories[fixed_class(_json_object(body).get("classification"))] += 1

    included_untimed = untimed_count if start_at is None else 0
    return {
        "indexed_oldest_at": oldest,
        "indexed_newest_at": newest,
        "indexed_signatures": timed_count + included_untimed,
        "timed_signatures": timed_count,
        "untimed_signatures": included_untimed,
        "untimed_source_signatures": untimed_count,
        "categories": categories,
        "parser_unresolved_signatures": categories["UNKNOWN_NEEDS_REVIEW"] + categories["OTHER_OR_UNKNOWN"],
    }, {
        "source_id": "FRANK_LOCAL_SIGNATURE_INDEX",
        "kind": "LOCAL_SQLITE_SIGNATURE_INDEX",
        "source_sha256": digest.hexdigest(),
        "oldest_indexed_raw_ref": oldest_ref,
        "newest_indexed_raw_ref": newest_ref,
    }


def _pending_detections(db, as_of, start_at):
    columns = _sql_columns(db, "signature_detections")
    if not {"wallet", "signature", "block_time", "seen_at", "state"}.issubset(columns):
        return None, None
    window = "(d.block_time IS NULL OR (typeof(d.block_time)='integer' AND d.block_time BETWEEN 0 AND ?))"
    params = [FRANK_WALLET, as_of, as_of]
    if start_at is not None:
        window = "typeof(d.block_time)='integer' AND d.block_time BETWEEN ? AND ?"
        params = [FRANK_WALLET, as_of, start_at, as_of]
    attribution = " AND (d.person_id IS NULL OR d.person_id='frank')" if "person_id" in columns else ""
    rows = db.execute(
        "SELECT d.signature,d.block_time,d.seen_at FROM signature_detections d "
        "WHERE d.wallet=? AND d.state='RAW_PENDING' AND d.signature IS NOT NULL "
        "AND typeof(d.seen_at) IN ('real','integer') AND d.seen_at>0 AND d.seen_at<=? "
        f"AND {window}{attribution} AND NOT EXISTS (SELECT 1 FROM signatures s "
        "WHERE s.wallet=d.wallet AND s.signature=d.signature AND s.person_id='frank') "
        "ORDER BY d.signature COLLATE BINARY,d.block_time,d.seen_at",
        params,
    )
    digest = hashlib.sha256()
    signatures = set()
    for row in rows:
        if safe_id(row[0]):
            signatures.add(row[0])
            _fingerprint_line(digest, row)
    return len(signatures), {
        "source_id": "FRANK_WALLET_SCANNER_DETECTIONS",
        "kind": "LOCAL_SQLITE_SIGNATURE_DETECTIONS",
        "source_sha256": digest.hexdigest(),
    }


def _recorded_stop(path, as_of, scanner):
    """Bind a timestamped service attempt to the wallet scanner's exact error."""
    error = scanner.get("last_error")
    if not isinstance(error, str) or error not in _SCANNER_ERRORS or scanner.get("status") != "RETRY_PENDING":
        return _UNKNOWN, None
    sidecar = Path(path).with_name("health.json")
    if sidecar.is_symlink() or not sidecar.is_file():
        return _UNKNOWN, None
    try:
        with sidecar.open("rb") as stream:
            raw = stream.read(256_001)
        if len(raw) > 256_000:
            return _UNKNOWN, None
        runtime = _json_object(raw)
        at = datetime.fromisoformat(runtime["last_poll_at"])
        if (runtime.get("system") == "FRANK_ONLY" and runtime.get("status") == "RETRY_PENDING"
                and runtime.get("last_error") == error and at.tzinfo is not None
                and not bool(runtime.get("source_drift")) and 0 < at.timestamp() <= as_of):
            successful = scanner.get("last_successful_poll")
            if type(successful) in (int, float) and 0 < successful <= at.timestamp():
                signature = safe_id(scanner.get("last_local_signature"))
                if signature and signature == runtime.get("last_processed_signature"):
                    return _SCANNER_ERRORS[error], at.timestamp()
    except (OSError, ValueError, TypeError, KeyError, OverflowError):
        pass
    return _UNKNOWN, None


def _scanner_coverage(db, path, as_of):
    if not {"wallet", "body"}.issubset(_sql_columns(db, "health")):
        return None, _UNKNOWN, None, None
    row = db.execute("SELECT body FROM health WHERE wallet=?", (FRANK_WALLET,)).fetchone()
    if row is None:
        return None, _UNKNOWN, None, None
    scanner = _json_object(row[0])
    observed_at = scanner.get("last_successful_poll")
    if type(observed_at) not in (int, float) or not 0 < observed_at <= as_of:
        return None, _UNKNOWN, None, None
    stop, stop_at = _recorded_stop(path, as_of, scanner)
    # Hash only the published fields of the scanner observation. In particular,
    # hashing the mutable retry state would pick up errors from after as_of.
    digest = hashlib.sha256()
    _fingerprint_line(digest, (FRANK_WALLET, observed_at, safe_id(scanner.get("last_chain_signature")),
                               safe_id(scanner.get("last_local_signature")), stop, stop_at))
    return int(observed_at), stop, int(stop_at) if stop_at is not None else None, {
        "source_id": "FRANK_WALLET_SCANNER_HEALTH",
        "kind": "LOCAL_SQLITE_WALLET_SCANNER_HEALTH",
        "source_sha256": digest.hexdigest(),
    }


def coverage_for_wallet(path, as_of, *, days="all"):
    """Read one local snapshot, applying the requested inclusive block-time window."""
    if (type(as_of) is not int or not 1_600_000_000 < as_of < 4_000_000_000
            or (days != "all" and (type(days) is not int or days not in (1, 7, 30)))):
        raise CoverageError("INVALID_INPUT")
    start_at = None if days == "all" else as_of - days * 86_400
    db = None
    try:
        db = connect(path)
        db.execute("BEGIN")
        data, index = _index_coverage(db, as_of, start_at)
        pending, detections = _pending_detections(db, as_of, start_at)
        observed_at, stop, stop_at, scanner = _scanner_coverage(db, path, as_of)
    except CoverageError:
        raise
    except (OSError, ValueError, sqlite3.Error):
        raise CoverageError("SOURCE_UNAVAILABLE", 503) from None
    finally:
        if db is not None:
            db.close()

    gaps = []
    if pending:
        gaps.append("DETECTED_SIGNATURES_NOT_INDEXED")
    if stop == "CURSOR_GAP_UNRESOLVED":
        gaps.append(stop)
    return {
        "schema_version": 1,
        "status": "PARTIAL_SOURCE",
        "as_of": as_of,
        "data": {"person_id": _PERSON, "days": days, "start_at": start_at, "end_at": as_of,
                 **data, "pending_detected_signatures": pending, "scanner_observed_at": observed_at},
        "coverage": {"full_chain_verified": False, "known_gaps": gaps or None,
                     "backfill_status": _UNKNOWN, "stop_reason": stop,
                     "stop_observed_at": stop_at},
        "sources": [source for source in (index, detections, scanner) if source is not None],
        "errors": [],
    }
