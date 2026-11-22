"""Private, persistent Frank user metadata, separate from chain and signal facts.

Only an explicit update creates/writes the existing research database. Reads use
SQLite mode=ro, and list/audit pages bind to a metadata revision and DB identity.
There is no transport, sender, source-ledger writer, timer, or total row cap.
"""
from __future__ import annotations

import base64
from contextlib import contextmanager
import hashlib
import json
import math
from pathlib import Path
import sqlite3
import time
import threading
import unicodedata
from urllib.parse import quote
import uuid

from ..meme.holder_ranks import valid_pubkey

PERSON = "frank"
CHAIN = "solana"
OVERRIDES = frozenset({"FOLLOW", "HIDE", "DEFAULT"})
_MAX_REVISION = 2**63 - 1


class WatchMetadataError(ValueError):
    """Public errors are fixed codes, never SQL, paths or rejected user values."""
    def __init__(self, code, http_status=400):
        self.code = code
        self.http_status = http_status
        super().__init__(code)


def _json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False)


def _hash(value):
    return hashlib.sha256(_json(value).encode()).hexdigest()


def _mint(value):
    if not valid_pubkey(value):
        raise WatchMetadataError("INVALID_METADATA_MINT")
    return value


def _text(value, capacity, code, *, multiline=False, nonempty=False):
    if not isinstance(value, str) or len(value) > capacity or (nonempty and not value):
        raise WatchMetadataError(code)
    if any(unicodedata.category(c) in {"Cc", "Cs"} and
           not (multiline and c in "\n\r\t") for c in value):
        raise WatchMetadataError(code)
    return value


def _default(mint):
    return {"person_id": PERSON, "chain": CHAIN, "mint": mint,
            "pinned": False, "note": "", "watch_override": "DEFAULT",
            "revision": 0, "created_at": None, "updated_at": None,
            "last_event_id": None, "persisted": False}


def _metadata(row):
    if row is None:
        return None
    try:
        if (row["person_id"] != PERSON or row["chain"] != CHAIN or
                row["pinned"] not in (0, 1) or
                type(row["revision"]) is not int or row["revision"] < 1 or
                row["watch_override"] not in OVERRIDES):
            raise ValueError
        _mint(row["mint"])
        _text(row["note"], 4000, "INVALID_METADATA_NOTE", multiline=True)
        if any(type(row[k]) not in (int, float) or not math.isfinite(row[k]) or row[k] < 0
               for k in ("created_at", "updated_at")):
            raise ValueError
        return {"person_id": PERSON, "chain": CHAIN, "mint": row["mint"],
                "pinned": bool(row["pinned"]), "note": row["note"],
                "watch_override": row["watch_override"], "revision": row["revision"],
                "created_at": row["created_at"], "updated_at": row["updated_at"],
                "last_event_id": row["last_event_id"], "persisted": True}
    except (ValueError, KeyError, TypeError):
        raise WatchMetadataError("WATCH_METADATA_INVALID_STORED_DATA", 503) from None


class WatchMetadataStore:
    _write_lock = threading.RLock()
    def __init__(self, root, clock=time.time):
        self.root = Path(root)
        self.path = self.root / "frank-research.sqlite"
        self.clock = clock

    def _identity(self):
        if self.path.is_symlink():
            raise WatchMetadataError("WATCH_METADATA_UNAVAILABLE", 503)
        stat = self.path.stat()
        return _hash([str(self.path.resolve()), stat.st_dev, stat.st_ino])

    @contextmanager
    def _reader(self):
        if not self.path.exists():
            if self.path.is_symlink():
                raise WatchMetadataError("WATCH_METADATA_UNAVAILABLE", 503)
            yield None, None
            return
        db = None
        try:
            identity = self._identity()
            uri = "file:" + quote(str(self.path.resolve()), safe="/") + "?mode=ro"
            db = sqlite3.connect(uri, uri=True, timeout=5, isolation_level=None)
            db.row_factory = sqlite3.Row
            db.execute("PRAGMA query_only=ON")
            db.execute("PRAGMA busy_timeout=5000")
            db.execute("BEGIN")
            if self._identity() != identity:
                raise WatchMetadataError("WATCH_METADATA_SOURCE_CHANGED", 409)
            yield db, identity
            if self._identity() != identity:
                raise WatchMetadataError("WATCH_METADATA_SOURCE_CHANGED", 409)
        except (OSError, sqlite3.Error):
            raise WatchMetadataError("WATCH_METADATA_UNAVAILABLE", 503) from None
        finally:
            if db is not None:
                db.close()

    @contextmanager
    def _writer(self):
        # Serialize schema/WAL initialization across HTTP threads and store
        # instances. SQLite still arbitrates with other research writers.
        with self._write_lock:
            with self._writer_transaction() as db:
                yield db

    @contextmanager
    def _writer_transaction(self):
        db = None
        try:
            self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
            if self.path.is_symlink():
                raise WatchMetadataError("WATCH_METADATA_UNAVAILABLE", 503)
            db = sqlite3.connect(self.path, timeout=5, isolation_level=None)
            db.row_factory = sqlite3.Row
            self.path.chmod(0o600)
            db.execute("PRAGMA foreign_keys=ON")
            db.execute("PRAGMA journal_mode=WAL")
            db.execute("PRAGMA synchronous=FULL")
            db.execute("PRAGMA busy_timeout=5000")
            db.execute("BEGIN IMMEDIATE")
            # No executescript: all schema/data/request/audit changes commit as
            # one transaction, with no use of shared PRAGMA user_version.
            for statement in (
                """CREATE TABLE IF NOT EXISTS frank_watch_meta_state(
                  id INTEGER PRIMARY KEY CHECK(id=1), schema_version INTEGER NOT NULL,
                  epoch INTEGER NOT NULL CHECK(epoch>=0))""",
                """CREATE TABLE IF NOT EXISTS frank_watch_metadata(
                  person_id TEXT NOT NULL,chain TEXT NOT NULL,mint TEXT NOT NULL,
                  pinned INTEGER NOT NULL CHECK(pinned IN(0,1)),note TEXT NOT NULL,
                  watch_override TEXT NOT NULL CHECK(watch_override IN('FOLLOW','HIDE','DEFAULT')),
                  revision INTEGER NOT NULL CHECK(revision>0),created_at REAL NOT NULL,
                  updated_at REAL NOT NULL,last_event_id TEXT NOT NULL,
                  PRIMARY KEY(person_id,chain,mint))""",
                """CREATE TABLE IF NOT EXISTS frank_watch_metadata_events(
                  seq INTEGER PRIMARY KEY AUTOINCREMENT,event_id TEXT NOT NULL UNIQUE,
                  person_id TEXT NOT NULL,chain TEXT NOT NULL,mint TEXT NOT NULL,
                  revision INTEGER NOT NULL,before_body TEXT NOT NULL,after_body TEXT NOT NULL,
                  request_hash TEXT NOT NULL,created_at REAL NOT NULL,
                  UNIQUE(person_id,chain,mint,revision),
                  FOREIGN KEY(person_id,chain,mint) REFERENCES frank_watch_metadata(person_id,chain,mint))""",
                """CREATE INDEX IF NOT EXISTS frank_watch_events_mint
                  ON frank_watch_metadata_events(person_id,chain,mint,seq)""",
                """CREATE TABLE IF NOT EXISTS frank_watch_metadata_requests(
                  person_id TEXT NOT NULL,chain TEXT NOT NULL,idempotency_key TEXT NOT NULL,
                  request_hash TEXT NOT NULL,response_body TEXT NOT NULL,
                  PRIMARY KEY(person_id,chain,idempotency_key))""",
            ):
                db.execute(statement)
            db.execute("INSERT OR IGNORE INTO frank_watch_meta_state VALUES(1,1,0)")
            version = db.execute("SELECT schema_version FROM frank_watch_meta_state WHERE id=1").fetchone()
            if version is None or version[0] != 1:
                raise WatchMetadataError("WATCH_METADATA_SCHEMA_UNSUPPORTED", 503)
            yield db
            db.commit()
        except (OSError, sqlite3.Error):
            if db is not None:
                db.rollback()
            raise WatchMetadataError("WATCH_METADATA_UNAVAILABLE", 503) from None
        except BaseException:
            if db is not None:
                db.rollback()
            raise
        finally:
            if db is not None:
                db.close()

    @staticmethod
    def _epoch(db):
        if db is None:
            return 0
        if db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='frank_watch_meta_state'").fetchone() is None:
            return 0
        row = db.execute("SELECT schema_version,epoch FROM frank_watch_meta_state WHERE id=1").fetchone()
        if row is None or row[0] != 1 or type(row[1]) is not int or row[1] < 0:
            raise WatchMetadataError("WATCH_METADATA_SCHEMA_UNSUPPORTED", 503)
        return row[1]

    @staticmethod
    def _row(db, mint, epoch):
        if db is None or epoch == 0:
            return None
        return db.execute("SELECT * FROM frank_watch_metadata WHERE person_id=? AND chain=? AND mint=?",
                          (PERSON, CHAIN, mint)).fetchone()

    def get(self, mint):
        mint = _mint(mint)
        with self._reader() as (db, _):
            epoch = self._epoch(db)
            return _metadata(self._row(db, mint, epoch)) or _default(mint)

    @staticmethod
    def _request(mint, body):
        if not isinstance(body, dict):
            raise WatchMetadataError("INVALID_METADATA_PATCH")
        allowed = {"expected_revision", "idempotency_key", "pinned", "note", "watch_override"}
        if (set(body) - allowed or not {"expected_revision", "idempotency_key"} <= set(body) or
                not set(body) & {"pinned", "note", "watch_override"}):
            raise WatchMetadataError("INVALID_METADATA_PATCH")
        if type(body["expected_revision"]) is not int or not 0 <= body["expected_revision"] <= _MAX_REVISION:
            raise WatchMetadataError("INVALID_METADATA_REVISION")
        _text(body["idempotency_key"], 256, "INVALID_METADATA_IDEMPOTENCY_KEY", nonempty=True)
        if "pinned" in body and type(body["pinned"]) is not bool:
            raise WatchMetadataError("INVALID_METADATA_PINNED")
        if "note" in body:
            _text(body["note"], 4000, "INVALID_METADATA_NOTE", multiline=True)
        if "watch_override" in body and (not isinstance(body["watch_override"], str) or body["watch_override"] not in OVERRIDES):
            raise WatchMetadataError("INVALID_METADATA_WATCH_OVERRIDE")
        return _hash({"person_id": PERSON, "chain": CHAIN, "mint": mint, "body": body})

    def update(self, mint, body):
        mint = _mint(mint)
        request_hash = self._request(mint, body)
        with self._writer() as db:
            prior = db.execute("SELECT request_hash,response_body FROM frank_watch_metadata_requests WHERE person_id=? AND chain=? AND idempotency_key=?",
                               (PERSON, CHAIN, body["idempotency_key"])).fetchone()
            if prior is not None:
                if prior["request_hash"] != request_hash:
                    raise WatchMetadataError("IDEMPOTENCY_CONFLICT", 409)
                try:
                    return json.loads(prior["response_body"])
                except (ValueError, TypeError):
                    raise WatchMetadataError("WATCH_METADATA_INVALID_STORED_DATA", 503) from None
            epoch = self._epoch(db)
            before = _metadata(self._row(db, mint, epoch)) or _default(mint)
            if before["revision"] != body["expected_revision"]:
                raise WatchMetadataError("REVISION_CONFLICT", 409)
            if before["revision"] == _MAX_REVISION or epoch == _MAX_REVISION:
                raise WatchMetadataError("WATCH_METADATA_REVISION_EXHAUSTED", 503)
            now = self.clock()
            if type(now) not in (int, float) or not math.isfinite(now) or now < 0:
                raise WatchMetadataError("WATCH_METADATA_CLOCK_INVALID", 503)
            event_id = str(uuid.uuid4())
            after = {**before, **{k: body[k] for k in ("pinned", "note", "watch_override") if k in body},
                     "revision": before["revision"] + 1, "created_at": before["created_at"] if before["persisted"] else now,
                     "updated_at": now, "last_event_id": event_id, "persisted": True}
            db.execute("""INSERT INTO frank_watch_metadata VALUES(?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(person_id,chain,mint) DO UPDATE SET pinned=excluded.pinned,note=excluded.note,
                watch_override=excluded.watch_override,revision=excluded.revision,updated_at=excluded.updated_at,
                last_event_id=excluded.last_event_id""",
                       (PERSON, CHAIN, mint, int(after["pinned"]), after["note"], after["watch_override"],
                        after["revision"], after["created_at"], now, event_id))
            db.execute("INSERT INTO frank_watch_metadata_events(event_id,person_id,chain,mint,revision,before_body,after_body,request_hash,created_at) VALUES(?,?,?,?,?,?,?,?,?)",
                       (event_id, PERSON, CHAIN, mint, after["revision"], _json(before), _json(after), request_hash, now))
            response = {**after, "event_id": event_id}
            db.execute("INSERT INTO frank_watch_metadata_requests VALUES(?,?,?,?,?)",
                       (PERSON, CHAIN, body["idempotency_key"], request_hash, _json(response)))
            db.execute("UPDATE frank_watch_meta_state SET epoch=epoch+1 WHERE id=1")
            return response

    @staticmethod
    def _limit(limit):
        if type(limit) is not int or not 1 <= limit <= 1000:
            raise WatchMetadataError("INVALID_METADATA_PAGE_SIZE")

    @staticmethod
    def _decode(cursor, kind, source, epoch, mint):
        if cursor is None:
            return None
        try:
            if not isinstance(cursor, str) or not 1 <= len(cursor) <= 4096:
                raise ValueError
            def pairs(items):
                obj = {}
                for key, value in items:
                    if key in obj:
                        raise ValueError
                    obj[key] = value
                return obj
            token = json.loads(base64.b64decode(cursor + "=" * (-len(cursor) % 4), altchars=b"-_", validate=True),
                               object_pairs_hook=pairs)
            if (not isinstance(token, dict) or set(token) != {"v", "kind", "source", "epoch", "mint", "after"} or
                    type(token["v"]) is not int or token["v"] != 1 or type(token["epoch"]) is not int or
                    not 0 <= token["epoch"] <= _MAX_REVISION or
                    not isinstance(token["source"], str) or len(token["source"]) != 64 or
                    any(c not in "0123456789abcdef" for c in token["source"])):
                raise ValueError
            if kind == "list":
                _mint(token["after"])
            elif type(token["after"]) is not int or not 1 <= token["after"] <= _MAX_REVISION:
                raise ValueError
            if token["kind"] != kind or token["mint"] != mint:
                raise WatchMetadataError("CURSOR_QUERY_CHANGED", 409)
            if token["source"] != source:
                raise WatchMetadataError("WATCH_METADATA_SOURCE_CHANGED", 409)
            if token["epoch"] != epoch:
                raise WatchMetadataError("CURSOR_REVISION_CHANGED", 409)
            return token["after"]
        except WatchMetadataError:
            raise
        except (ValueError, TypeError, KeyError, UnicodeError, RecursionError):
            raise WatchMetadataError("INVALID_METADATA_CURSOR") from None

    @staticmethod
    def _page(rows, total, limit, kind, source, epoch, mint):
        more = len(rows) > limit
        page = rows[:limit]
        next_cursor = None
        if more:
            after = page[-1]["mint"] if kind == "list" else page[-1]["_seq"]
            token = {"v": 1, "kind": kind, "source": source, "epoch": epoch, "mint": mint, "after": after}
            next_cursor = base64.urlsafe_b64encode(_json(token).encode()).decode().rstrip("=")
        return {"schema_version": 1, "status": "OK", "scope": "FRANK_USER_METADATA_ONLY",
                "person_id": PERSON, "chain": CHAIN, "metadata_revision": epoch,
                "rows": [{k: v for k, v in row.items() if k != "_seq"} for row in page],
                "total_matching": total, "returned": len(page), "limit": limit, "next_cursor": next_cursor}

    def list(self, mint=None, limit=100, cursor=None):
        self._limit(limit)
        if mint is not None:
            mint = _mint(mint)
        with self._reader() as (db, source):
            epoch = self._epoch(db)
            after = self._decode(cursor, "list", source, epoch, mint)
            if mint is not None:
                row = _metadata(self._row(db, mint, epoch)) or _default(mint)
                return self._page([row] if after is None else [], 1, limit, "list", source, epoch, mint)
            if db is None or epoch == 0:
                return self._page([], 0, limit, "list", source, epoch, mint)
            where = "person_id=? AND chain=?"
            params = [PERSON, CHAIN]
            total = db.execute("SELECT count(*) FROM frank_watch_metadata WHERE " + where, params).fetchone()[0]
            if after is not None:
                where += " AND mint>?"
                params.append(after)
            result = db.execute("SELECT * FROM frank_watch_metadata WHERE " + where + " ORDER BY mint LIMIT ?", params + [limit + 1])
            rows = [_metadata(row) for row in result]
            return self._page(rows, total, limit, "list", source, epoch, mint)

    def preferences(self):
        """One consistent read for the user-view overlay; never expose notes."""
        with self._reader() as (db, _):
            epoch = self._epoch(db)
            if db is None or epoch == 0:
                return epoch, []
            rows = [_metadata(row) for row in db.execute(
                "SELECT * FROM frank_watch_metadata WHERE person_id=? AND chain=? ORDER BY mint",
                (PERSON, CHAIN))]
            return epoch, [{k: r[k] for k in ("mint", "pinned", "watch_override", "revision")} for r in rows]

    def events(self, mint, limit=100, cursor=None):
        mint = _mint(mint)
        self._limit(limit)
        with self._reader() as (db, source):
            epoch = self._epoch(db)
            after = self._decode(cursor, "events", source, epoch, mint)
            if db is None or epoch == 0:
                return self._page([], 0, limit, "events", source, epoch, mint)
            where = "person_id=? AND chain=? AND mint=?"
            params = [PERSON, CHAIN, mint]
            total = db.execute("SELECT count(*) FROM frank_watch_metadata_events WHERE " + where, params).fetchone()[0]
            if after is not None:
                where += " AND seq<?"
                params.append(after)
            result = db.execute("SELECT * FROM frank_watch_metadata_events WHERE " + where + " ORDER BY seq DESC LIMIT ?", params + [limit + 1])
            try:
                rows = [{"event_id": row["event_id"], "person_id": PERSON, "chain": CHAIN,
                         "mint": row["mint"], "revision": row["revision"],
                         "before": json.loads(row["before_body"]), "after": json.loads(row["after_body"]),
                         "request_hash": row["request_hash"], "created_at": row["created_at"], "_seq": row["seq"]}
                        for row in result]
            except (ValueError, TypeError):
                raise WatchMetadataError("WATCH_METADATA_INVALID_STORED_DATA", 503) from None
            return self._page(rows, total, limit, "events", source, epoch, mint)
