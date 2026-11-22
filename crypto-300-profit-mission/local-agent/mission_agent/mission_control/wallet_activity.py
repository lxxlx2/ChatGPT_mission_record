"""Frank D1 exact-wallet indexed activity projection, extracted from PR #111.

Read-only local SQLite only; one evidence projection, not a source of trade
decisions, current holdings, PnL, portfolio completeness or live signal.
Legacy full responses are retained; paging reuses this same projection.
"""
from __future__ import annotations
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import quote
import json
import re
import sqlite3

CLASSES = {"ACTIVE_TRADE", "PASSIVE_TRANSFER", "FAILED_TX", "ATA_CREATE",
           "UNKNOWN_NEEDS_REVIEW"}
SIDES = {"BUY", "ADD", "REENTRY", "SELL", "EXIT", "SELL_POSITION_UNRESOLVED"}
B58 = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,100}$")
MINT = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$")

def safe_id(v, pattern=B58):
    return v if isinstance(v, str) and pattern.fullmatch(v) else None

def fixed_class(v):
    return v if isinstance(v, str) and v in CLASSES else "OTHER_OR_UNKNOWN"

def connect(path):
    p = Path(path)
    if p.is_symlink() or not p.is_file():
        raise ValueError("EXISTING_SOURCE_REQUIRED")
    db = sqlite3.connect("file:" + quote(str(p.resolve()), safe="/") + "?mode=ro",
                         uri=True, timeout=2, isolation_level=None)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA query_only=ON")
    return db

def activity(path, as_of, days=1, max_rows=None, *, _row_ids=None, _connection=None):
    if type(as_of) is not int or not 1_600_000_000 < as_of < 4_000_000_000:
        raise ValueError("INVALID_TIMESTAMP")
    if days != "all" and (type(days) is not int or days not in (1, 7, 30)):
        raise ValueError("INVALID_ACTIVITY_RANGE")
    if max_rows is not None and (type(max_rows) is not int or max_rows < 1):
        raise ValueError("INVALID_ACTIVITY_ROW_GUARD")
    after = None if days == "all" else as_of - 86400 * days
    db = _connection if _connection is not None else connect(path)
    try:
        if not db.in_transaction:
            db.execute("BEGIN")
        names = {x[0] for x in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if not {"signatures", "trades"}.issubset(names):
            raise ValueError("SOURCE_TABLES_MISSING")
        window = "(s.block_time<=? OR s.block_time IS NULL)" if after is None else "s.block_time BETWEEN ? AND ?"
        params = ["frank", as_of] if after is None else ["frank", after, as_of]
        where = "s.person_id=? AND " + window
        if _row_ids is not None:
            if not isinstance(_row_ids, list) or any(type(x) is not int or x < 1 for x in _row_ids):
                raise ValueError("INVALID_ACTIVITY_ROW_IDS")
            # IDs originate from the read-only page query. Validated integers
            # avoid depending on a platform-specific SQLite variable limit.
            where += " AND s.rowid IN (" + ",".join(map(str, _row_ids)) + ")"
        query = "SELECT s.rowid AS index_rowid,s.* FROM signatures s WHERE " + where + " ORDER BY s.block_time DESC,s.signature"
        if max_rows is not None:
            query += " LIMIT ?"
            params.append(max_rows+1)
        sigs = db.execute(query, params).fetchall()
        if max_rows is not None and len(sigs) > max_rows:
            raise ValueError("INDEX_WINDOW_TOO_LARGE_NOT_TRUNCATED")
        trades = db.execute(
            "SELECT t.wallet,t.signature,t.mint,t.side FROM trades t "
            "JOIN signatures s ON t.wallet=s.wallet AND t.signature=s.signature "
            "WHERE " + where,
            params[:-1] if max_rows is not None else params).fetchall()
        tmap, seen_trades = defaultdict(list), set()
        for t in trades:
            key = (t["wallet"], t["signature"], t["mint"], t["side"])
            if key in seen_trades:
                continue
            seen_trades.add(key)
            tmap[(t["wallet"], t["signature"])].append({
                "side": t["side"] if t["side"] in SIDES else "OTHER_SIDE",
                "mint": safe_id(t["mint"], MINT)})
        seen, rows = set(), []
        for s in sigs:
            key = (s["wallet"], s["signature"])
            if key in seen:
                raise ValueError("DUPLICATED_SIGNATURE")
            seen.add(key)
            try:
                body = json.loads(s["body"] or "{}")
                if not isinstance(body, dict):
                    body = {}
            except (TypeError, ValueError):
                body = {}
            cls = fixed_class(body.get("classification"))
            matched = tmap.get(key, [])
            status = ("CLASS_TRADE_MISMATCH" if matched and cls != "ACTIVE_TRADE"
                      else "ACTIVE_WITHOUT_TRADE_LEG" if not matched and cls == "ACTIVE_TRADE"
                      else "UNRESOLVED" if cls == "UNKNOWN_NEEDS_REVIEW"
                      else "MATCHED_OR_NOT_APPLICABLE")
            evidence = body.get("evidence") if isinstance(body.get("evidence"), dict) else {}
            deltas = evidence.get("token_balance_deltas")
            deltas = deltas if isinstance(deltas, list) else []
            mints = {x["mint"] for x in matched if x.get("mint")}
            mints.update(x["mint"] for x in deltas if isinstance(x, dict)
                         and x.get("wallet_owned") is True and x.get("owner") == s["wallet"]
                         and safe_id(x.get("mint"), MINT))
            raw_hash = s["raw_hash"] if "raw_hash" in s.keys() else None
            slot = s["slot"] if "slot" in s.keys() else body.get("slot")
            version = evidence.get("parser_version")
            version = str(version) if type(version) in (str, int) else None
            if version and not re.fullmatch(r"[A-Za-z0-9_.:-]{1,128}", version):
                version = None
            indexed = s["seen_at"] if "seen_at" in s.keys() else None
            if not isinstance(indexed, str) or not re.fullmatch(r"[0-9TZ:+. -]{1,64}", indexed):
                indexed = None
            rows.append({"sig": safe_id(s["signature"]), "at": s["block_time"],
                         "class": cls, "trades": matched, "status": status,
                         "trade_match_status": ("MATCHED" if matched and cls == "ACTIVE_TRADE"
                                                else "NOT_APPLICABLE" if status == "MATCHED_OR_NOT_APPLICABLE" else status),
                         "wallet": safe_id(s["wallet"], MINT), "index_rowid": s["index_rowid"],
                         "slot": slot if type(slot) is int and slot >= 0 else None,
                         "first_indexed_at": indexed, "parser_version": version,
                         "raw_sha256": raw_hash if isinstance(raw_hash, str) and re.fullmatch(r"[0-9a-f]{64}", raw_hash) else None,
                         "wallet_mints": sorted(mints)})
        return {"as_of": as_of, "days": days, "rows": rows,
                "signatures": len(rows), "trade_legs": sum(len(x["trades"]) for x in rows),
                "categories": dict(sorted(Counter(x["class"] for x in rows).items())),
                "flags": dict(sorted(Counter(x["status"] for x in rows).items())),
                "full_chain_verified": False, "current_balance_verified": False}
    finally:
        if _connection is None:
            db.close()

