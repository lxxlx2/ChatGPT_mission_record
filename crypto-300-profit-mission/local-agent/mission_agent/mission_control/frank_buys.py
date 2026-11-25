"""Read-only Frank buys over the existing signed trade ledger."""
import base64
from contextlib import closing
import hashlib
import json
import re

from .wallet_activity import connect
from .wallet_activity_paging import _source
from ..signals.buy_admission import admit_buy, exact_mint, qualification


def _encode(row):
    return base64.urlsafe_b64encode(json.dumps(row, separators=(",", ":")).encode()).decode().rstrip("=")


def _decode(cursor, binding):
    try:
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,256}", cursor):
            raise ValueError()
        values = json.loads(base64.urlsafe_b64decode(cursor + "=" * (-len(cursor) % 4)))
        version, source, cutoff, rowmax, at, rowid = values
        if version != 1 or source != binding or any(
                type(n) is not int or not 0 < n < 2**63 for n in (cutoff, rowmax, at, rowid)
        ) or at > cutoff or rowid > rowmax:
            raise ValueError()
        return cutoff, rowmax, at, rowid
    except (TypeError, ValueError):
        raise ValueError("INVALID_OR_STALE_CURSOR") from None


def read_buys(database, qualifications, *, as_of, days="7", mint=None, cursor=None):
    if days not in ("1", "7", "30", "all") or (mint is not None and not exact_mint(mint)):
        raise ValueError("INVALID_BUY_QUERY")
    try:
        assets = qualification(qualifications, as_of)
    except FileNotFoundError:
        return {"status": "QUALIFICATION_UNAVAILABLE", "rows": [], "next_cursor": None}
    source = _source(database)
    binding = hashlib.sha256(repr((source, days, mint, sorted(assets.items()))).encode()).hexdigest()
    with closing(connect(database)) as db:
        db.execute("BEGIN")
        if _source(database) != source:
            raise ValueError("INVALID_OR_STALE_CURSOR")
        where = ["s.person_id='frank'", "t.side IN ('BUY','ADD','REENTRY')"]
        if cursor is not None:
            cutoff, rowmax, at, rowid = _decode(cursor, binding)
            if cutoff > as_of:
                raise ValueError("INVALID_OR_STALE_CURSOR")
            where.append("(s.block_time,t.rowid)<(?,?)")
            params = [at, rowid]
        else:
            cutoff = as_of
            rowmax = db.execute("SELECT coalesce(max(rowid),0) FROM trades").fetchone()[0]
            params = []
        where.extend(["s.block_time BETWEEN ? AND ?", "t.rowid<=?"])
        params.extend([1 if days == "all" else cutoff - int(days)*86400, cutoff, rowmax])
        if mint is not None:
            where.append("t.mint=?")
            params.append(mint)
        where.append("t.mint IN (SELECT value FROM json_each(?))")
        params.append(json.dumps([m for m, a in assets.items() if a.status == "VERIFIED_MEME"]))
        records = db.execute(
            "SELECT t.rowid AS trade_id,t.mint,s.wallet,s.signature,s.slot,s.block_time,s.raw_hash,s.body "
            "FROM trades t JOIN signatures s ON s.wallet=t.wallet AND s.signature=t.signature WHERE "
            + " AND ".join(where) + " ORDER BY s.block_time DESC,t.rowid DESC", params)
        rows, next_cursor = [], None
        for row in records:
            try:
                event = json.loads(row["body"])
            except (ValueError, TypeError):
                continue
            item = admit_buy(event, assets, wallet=row["wallet"], signature=row["signature"],
                             slot=row["slot"], block_time=row["block_time"], raw_hash=row["raw_hash"], mint=row["mint"])
            if not item:
                continue
            if len(rows) == 30:
                next_cursor = _encode([1, binding, cutoff, rowmax, last["block_time"], last["trade_id"]])
                break
            rows.append(item)
            last = row
        return {"status": "LOCAL_EVIDENCE_ONLY", "as_of": cutoff, "rows": rows, "next_cursor": next_cursor}
