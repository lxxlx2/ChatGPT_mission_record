"""Frank D1 exact-wallet indexed activity projection, extracted from PR #111.

Read-only local SQLite only; one evidence projection, not a source of trade
decisions, current holdings, PnL, portfolio completeness or live signal.
Original authored activity(path, as_of, days=1, max_rows=5000) retained.
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

def activity(path, as_of, days=1, max_rows=5000):
    if type(as_of) is not int or not 1_600_000_000 < as_of < 4_000_000_000:
        raise ValueError("INVALID_TIMESTAMP")
    if days not in (1, 7) or not 1 <= max_rows <= 5000:
        raise ValueError("BOUNDED_WINDOW_REQUIRED")
    after = as_of - 86400 * days
    db = connect(path)
    try:
        names = {x[0] for x in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if not {"signatures", "trades"}.issubset(names):
            raise ValueError("SOURCE_TABLES_MISSING")
        sigs = db.execute(
            "SELECT wallet,signature,block_time,body FROM signatures "
            "WHERE person_id=? AND block_time BETWEEN ? AND ? "
            "ORDER BY block_time DESC,signature LIMIT ?",
            ("frank", after, as_of, max_rows+1)).fetchall()
        if len(sigs) > max_rows:
            raise ValueError("INDEX_WINDOW_TOO_LARGE_NOT_TRUNCATED")
        trades = db.execute(
            "SELECT t.wallet,t.signature,t.mint,t.side FROM trades t "
            "JOIN signatures s ON t.wallet=s.wallet AND t.signature=s.signature "
            "WHERE s.person_id=? AND s.block_time BETWEEN ? AND ?",
            ("frank", after, as_of)).fetchall()
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
            rows.append({"sig": safe_id(s["signature"]), "at": s["block_time"],
                         "class": cls, "trades": matched, "status": status})
        return {"as_of": as_of, "days": days, "rows": rows,
                "signatures": len(rows), "trade_legs": sum(len(x["trades"]) for x in rows),
                "categories": dict(sorted(Counter(x["class"] for x in rows).items())),
                "flags": dict(sorted(Counter(x["status"] for x in rows).items())),
                "full_chain_verified": False, "current_balance_verified": False}
    finally:
        db.close()

