"""Query adapter for the existing D1 projection; no parallel ledger or writer.

Page capacity limits one response, never total indexed history. The rowid fence
excludes new inserts. Existing rows can change between calls; this is explicitly
not a frozen snapshot, full-chain coverage, a balance or a trading signal.
"""
import base64
import hashlib
import json
from pathlib import Path

from .wallet_activity import activity, connect, CLASSES, MINT, safe_id

KINDS = CLASSES | {"ALL", "BUY", "SELL", "OTHER_OR_UNKNOWN"}
CURSOR_ERRORS = {"INVALID_ACTIVITY_CURSOR", "ACTIVITY_CURSOR_QUERY_CHANGED",
                 "ACTIVITY_CURSOR_SOURCE_CHANGED"}


def _source(path):
    p = Path(path)
    st = p.stat()
    return hashlib.sha256(json.dumps(
        [str(p.resolve()), st.st_dev, st.st_ino], separators=(",", ":")).encode()).hexdigest()


def _encode(token):
    return base64.urlsafe_b64encode(json.dumps(
        token, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).decode().rstrip("=")


def _decode(cursor):
    try:
        if not isinstance(cursor, str) or not 1 <= len(cursor) <= 4096:
            raise ValueError
        token = json.loads(base64.b64decode(
            cursor + "=" * (-len(cursor) % 4), altchars=b"-_", validate=True))
        if not isinstance(token, dict) or set(token) != {
                "v", "source", "at", "days", "fence", "kind", "mint", "after"}:
            raise ValueError
        if type(token["v"]) is not int or token["v"] != 1:
            raise ValueError
        if type(token["at"]) is not int or not 1_600_000_000 < token["at"] < 4_000_000_000:
            raise ValueError
        if token["days"] != "all" and (type(token["days"]) is not int or token["days"] not in (1, 7, 30)):
            raise ValueError
        if type(token["fence"]) is not int or not 0 <= token["fence"] <= 2**63-1:
            raise ValueError
        if not isinstance(token["kind"], str) or token["kind"] not in KINDS:
            raise ValueError
        if token["mint"] is not None and safe_id(token["mint"], MINT) is None:
            raise ValueError
        if not isinstance(token["source"], str) or len(token["source"]) != 64 or any(
                c not in "0123456789abcdef" for c in token["source"]):
            raise ValueError
        after = token["after"]
        if (not isinstance(after, list) or len(after) != 2 or
                any(type(x) is not int for x in after) or
                not 0 <= after[0] <= token["at"] or not 0 < after[1] <= token["fence"]):
            raise ValueError
        return token
    except (ValueError, TypeError, KeyError, UnicodeError, RecursionError):
        raise ValueError("INVALID_ACTIVITY_CURSOR") from None


def _where(at, days, fence, kind, mint):
    params = ["frank", fence]
    where = "s.person_id=? AND s.rowid<=?"
    if days == "all":
        where += " AND (s.block_time<=? OR s.block_time IS NULL)"
        params.append(at)
    else:
        where += " AND s.block_time BETWEEN ? AND ?"
        params.extend([at-days*86400, at])
    body = "CASE WHEN json_valid(s.body) THEN s.body ELSE '{}' END"
    cls = "json_extract(" + body + ",'$.classification')"
    if kind in ("BUY", "SELL"):
        sides = ("BUY", "ADD", "REENTRY") if kind == "BUY" else ("SELL", "EXIT", "SELL_POSITION_UNRESOLVED")
        where += (" AND " + cls + "='ACTIVE_TRADE' AND EXISTS (SELECT 1 FROM trades t "
                  "WHERE t.wallet=s.wallet AND t.signature=s.signature AND t.side IN (?,?,?))")
        params.extend(sides)
    elif kind == "OTHER_OR_UNKNOWN":
        where += " AND (" + cls + " IS NULL OR " + cls + " NOT IN (?,?,?,?,?))"
        params.extend(sorted(CLASSES))
    elif kind != "ALL":
        where += " AND " + cls + "=?"
        params.append(kind)
    if mint is not None:
        deltas = ("CASE WHEN json_type(" + body + ",'$.evidence.token_balance_deltas')='array' "
                  "THEN json_extract(" + body + ",'$.evidence.token_balance_deltas') ELSE '[]' END")
        item = "CASE WHEN json_valid(e.value) THEN e.value ELSE '{}' END"
        where += (" AND (EXISTS (SELECT 1 FROM trades t WHERE t.wallet=s.wallet AND "
                  "t.signature=s.signature AND t.mint=?) OR EXISTS (SELECT 1 FROM json_each(" +
                  deltas + ") e WHERE json_extract(" + item + ",'$.mint')=? AND "
                  "json_extract(" + item + ",'$.wallet_owned')=1 AND json_extract(" +
                  item + ",'$.owner')=s.wallet))")
        params.extend([mint, mint])
    return where, params


def activity_page(path, as_of, days=1, *, page_size=100, cursor=None, kind="ALL", mint=None):
    if type(as_of) is not int or not 1_600_000_000 < as_of < 4_000_000_000:
        raise ValueError("INVALID_TIMESTAMP")
    if days != "all" and (type(days) is not int or days not in (1, 7, 30)):
        raise ValueError("INVALID_ACTIVITY_RANGE")
    if type(page_size) is not int or not 1 <= page_size <= 1000:
        raise ValueError("INVALID_ACTIVITY_PAGE_SIZE")
    if not isinstance(kind, str) or kind not in KINDS:
        raise ValueError("INVALID_ACTIVITY_KIND")
    if mint is not None and safe_id(mint, MINT) is None:
        raise ValueError("INVALID_ACTIVITY_MINT")
    db = connect(path)
    try:
        db.execute("BEGIN")
        tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if not {"signatures", "trades"}.issubset(tables):
            raise ValueError("SOURCE_TABLES_MISSING")
        source, token = _source(path), _decode(cursor) if cursor is not None else None
        if token:
            if token["source"] != source:
                raise ValueError("ACTIVITY_CURSOR_SOURCE_CHANGED")
            if (token["days"], token["kind"], token["mint"]) != (days, kind, mint):
                raise ValueError("ACTIVITY_CURSOR_QUERY_CHANGED")
            if token["at"] > as_of:
                raise ValueError("INVALID_ACTIVITY_CURSOR")
            at, fence = token["at"], token["fence"]
        else:
            at = as_of
            fence = db.execute("SELECT COALESCE(MAX(rowid),0) FROM signatures WHERE person_id=?",
                               ("frank",)).fetchone()[0]
        where, params = _where(at, days, fence, kind, mint)
        total = db.execute("SELECT COUNT(*) FROM signatures s WHERE " + where, params).fetchone()[0]
        tail, tail_params = "", []
        if token:
            tail = " AND (COALESCE(s.block_time,0)<? OR (COALESCE(s.block_time,0)=? AND s.rowid<?))"
            tail_params = [token["after"][0], token["after"][0], token["after"][1]]
        selected = db.execute("SELECT s.rowid AS n,COALESCE(s.block_time,0) AS at "
                              "FROM signatures s WHERE " + where + tail +
                              " ORDER BY COALESCE(s.block_time,0) DESC,s.rowid DESC LIMIT ?",
                              [*params, *tail_params, page_size+1]).fetchall()
        more, selected = len(selected) > page_size, selected[:page_size]
        ids = [row["n"] for row in selected]
        # Reuse one canonical interpretation in the same read transaction.
        result = activity(path, at, days, _row_ids=ids, _connection=db)
        by_id = {row["index_rowid"]: row for row in result["rows"]}
        result["rows"] = [by_id[n] for n in ids]
        next_cursor = None
        if more:
            last = selected[-1]
            next_cursor = _encode({"v": 1, "source": source, "at": at, "days": days,
                                   "fence": fence, "kind": kind, "mint": mint,
                                   "after": [last["at"], last["n"]]})
        return {**result, "scope": "LOCAL_INDEX_ONLY_NOT_COMPLETE_CHAIN",
                "total_signatures": total, "counts_scope": "THIS_PAGE",
                "page_size": page_size, "has_more": more, "next_cursor": next_cursor,
                "kind": kind, "mint": mint, "immutable_source_snapshot": False,
                "index_read_semantics": "NEW_ROWS_FENCED; EXISTING_ROWS_MAY_BE_UPDATED",
                "untimed_source_signatures": db.execute(
                    "SELECT COUNT(*) FROM signatures WHERE person_id=? AND rowid<=? AND block_time IS NULL",
                    ("frank", fence)).fetchone()[0]}
    finally:
        db.close()

