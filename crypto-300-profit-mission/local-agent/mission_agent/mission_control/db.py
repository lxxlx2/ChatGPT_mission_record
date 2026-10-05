"""Database boundaries for Mission Meme V1.

The Frank production database is opened read-only. Mission Control owns a
separate writable database for snapshots, decision transitions and delivery
receipts. No code in this module can mutate the Frank ledger.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

from ..hashing import digest


def utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def open_production_ro(path: Path) -> sqlite3.Connection:
    path = Path(path).resolve()
    if not path.is_file():
        raise FileNotFoundError(path)
    uri = "file:" + quote(str(path), safe="/") + "?mode=ro"
    db = sqlite3.connect(uri, uri=True, timeout=2, isolation_level=None)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA query_only=ON")
    db.execute("PRAGMA busy_timeout=1000")
    return db


def open_control_ro(path: Path) -> sqlite3.Connection:
    return open_production_ro(path)


class ControlDB:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.db = sqlite3.connect(self.path, timeout=5, isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.execute("PRAGMA busy_timeout=5000")
        self.db.executescript(
            """
            CREATE TABLE IF NOT EXISTS decision_snapshots(
                snapshot_id TEXT PRIMARY KEY,
                person_id TEXT NOT NULL,
                mint TEXT NOT NULL,
                episode_id TEXT,
                source_signal_id TEXT,
                source_signal_type TEXT NOT NULL,
                decision TEXT NOT NULL,
                policy_id TEXT NOT NULL,
                policy_hash TEXT NOT NULL,
                input_hash TEXT NOT NULL,
                created_at TEXT NOT NULL,
                body TEXT NOT NULL,
                UNIQUE(person_id,mint,episode_id,input_hash)
            );
            CREATE TABLE IF NOT EXISTS decision_events(
                decision_id TEXT PRIMARY KEY,
                person_id TEXT NOT NULL,
                mint TEXT NOT NULL,
                episode_id TEXT,
                snapshot_id TEXT NOT NULL,
                decision TEXT NOT NULL,
                previous_decision TEXT,
                created_at TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                body TEXT NOT NULL,
                FOREIGN KEY(snapshot_id) REFERENCES decision_snapshots(snapshot_id)
            );
            CREATE INDEX IF NOT EXISTS idx_decision_events_entity
                ON decision_events(person_id,mint,episode_id,created_at);
            CREATE TABLE IF NOT EXISTS decision_outbox(
                decision_id TEXT NOT NULL,
                channel TEXT NOT NULL,
                status TEXT NOT NULL,
                attempts INTEGER NOT NULL DEFAULT 0,
                content_hash TEXT NOT NULL,
                created_at TEXT NOT NULL,
                last_error TEXT,
                receipt TEXT,
                PRIMARY KEY(decision_id,channel),
                FOREIGN KEY(decision_id) REFERENCES decision_events(decision_id)
            );
            CREATE TABLE IF NOT EXISTS gmail_delivery(
                decision_id TEXT PRIMARY KEY,
                delivery_mode TEXT NOT NULL,
                delivery_forbidden INTEGER NOT NULL CHECK(delivery_forbidden IN (0,1)),
                subject TEXT NOT NULL,
                body TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                wire_message_id TEXT NOT NULL UNIQUE,
                status TEXT NOT NULL,
                attempt_count INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                last_attempt_at TEXT,
                sent_at TEXT,
                gmail_message_id TEXT,
                gmail_thread_id TEXT,
                readback_verified INTEGER NOT NULL DEFAULT 0,
                last_error TEXT,
                receipt TEXT,
                FOREIGN KEY(decision_id) REFERENCES decision_events(decision_id)
            );
            CREATE TABLE IF NOT EXISTS local_delivery(
                decision_id TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                created_at TEXT NOT NULL,
                delivered_at TEXT,
                mechanism TEXT,
                last_error TEXT,
                receipt TEXT,
                FOREIGN KEY(decision_id) REFERENCES decision_events(decision_id)
            );
            CREATE TABLE IF NOT EXISTS market_cache(
                cache_key TEXT PRIMARY KEY,
                observed_at TEXT NOT NULL,
                expires_at REAL NOT NULL,
                body TEXT NOT NULL
            );
            """
        )
        try:
            self.path.chmod(0o600)
        except OSError:
            pass

    def close(self) -> None:
        self.db.close()

    def cache_get(self, key: str, now_ts: float):
        row = self.db.execute(
            "SELECT body FROM market_cache WHERE cache_key=? AND expires_at>=?",
            (key, now_ts),
        ).fetchone()
        return json.loads(row[0]) if row else None

    def cache_put(self, key: str, body: dict, expires_at: float) -> None:
        self.db.execute(
            "INSERT OR REPLACE INTO market_cache VALUES(?,?,?,?)",
            (key, utc(), expires_at, json.dumps(body, sort_keys=True)),
        )

    def latest_event(self, person_id: str, mint: str, episode_id: str | None):
        if episode_id is None:
            row = self.db.execute(
                "SELECT * FROM decision_events WHERE person_id=? AND mint=? AND episode_id IS NULL ORDER BY rowid DESC LIMIT 1",
                (person_id, mint),
            ).fetchone()
        else:
            row = self.db.execute(
                "SELECT * FROM decision_events WHERE person_id=? AND mint=? AND episode_id=? ORDER BY rowid DESC LIMIT 1",
                (person_id, mint, episode_id),
            ).fetchone()
        return dict(row) if row else None

    def record(self, payload: dict, policy_id: str, policy_hash: str) -> dict:
        """Persist an immutable snapshot and create an event only on decision change."""
        person_id = payload["person_id"]
        mint = payload["mint"]
        episode_id = payload.get("episode_id")
        input_hash = digest(payload["inputs"])
        snapshot_id = digest(
            {
                "person_id": person_id,
                "mint": mint,
                "episode_id": episode_id,
                "policy_id": policy_id,
                "policy_hash": policy_hash,
                "input_hash": input_hash,
            }
        )
        encoded = json.dumps(payload, sort_keys=True)
        self.db.execute(
            "INSERT OR IGNORE INTO decision_snapshots VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                snapshot_id,
                person_id,
                mint,
                episode_id,
                payload.get("source_signal_id"),
                payload["source_signal_type"],
                payload["decision"],
                policy_id,
                policy_hash,
                input_hash,
                payload["created_at"],
                encoded,
            ),
        )
        previous = self.latest_event(person_id, mint, episode_id)
        if previous and previous["decision"] == payload["decision"]:
            return {"changed": False, "snapshot_id": snapshot_id, "event": previous}
        decision_id = digest(
            {
                "snapshot_id": snapshot_id,
                "decision": payload["decision"],
                "previous": previous["decision"] if previous else None,
            }
        )
        event_body = {
            **payload,
            "decision_id": decision_id,
            "snapshot_id": snapshot_id,
            "previous_decision": previous["decision"] if previous else None,
        }
        content_hash = digest(event_body)
        self.db.execute(
            "INSERT OR IGNORE INTO decision_events VALUES(?,?,?,?,?,?,?,?,?,?)",
            (
                decision_id,
                person_id,
                mint,
                episode_id,
                snapshot_id,
                payload["decision"],
                previous["decision"] if previous else None,
                payload["created_at"],
                content_hash,
                json.dumps(event_body, sort_keys=True),
            ),
        )
        row = self.db.execute(
            "SELECT * FROM decision_events WHERE decision_id=?", (decision_id,)
        ).fetchone()
        return {"changed": True, "snapshot_id": snapshot_id, "event": dict(row)}

    def enqueue(self, decision_id: str, channel: str, content_hash: str, status: str) -> None:
        self.db.execute(
            "INSERT OR IGNORE INTO decision_outbox(decision_id,channel,status,content_hash,created_at) VALUES(?,?,?,?,?)",
            (decision_id, channel, status, content_hash, utc()),
        )

    def recent_events(self, limit: int = 100) -> list[dict]:
        rows = self.db.execute(
            "SELECT * FROM decision_events ORDER BY rowid DESC LIMIT ?", (limit,)
        ).fetchall()
        result = []
        for row in rows:
            item = dict(row)
            item["body"] = json.loads(item["body"])
            result.append(item)
        return result
