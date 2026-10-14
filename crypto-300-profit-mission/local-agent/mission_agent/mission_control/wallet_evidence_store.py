"""A04/A05 optional, manually populated local sidecar for immutable evidence.

Never opens Frank forward.sqlite or Mission Control audit SQLite for writing.
Only explicit caller-supplied normalized captures can be imported. This store
does not import secrets, initiate RPC, evaluate follow decisions or send alerts.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sqlite3
from urllib.parse import quote

from .wallet_economic_ledger import transaction_identity


_PROTECTED_NAMES = frozenset({"forward.sqlite", "mission-control.sqlite",
                             "sol-normalized-v1.sqlite"})


def _json(value: dict) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


class WalletEvidenceStore:
    """Append-only snapshots/transactions, source conflicts fail closed."""

    def __init__(self, path: Path, *, read_only: bool = False):
        original = Path(path).expanduser()
        if original.is_symlink():
            raise ValueError("SIDE_CAR_SYMLINK_FORBIDDEN")
        path = original.resolve()
        if path.name in _PROTECTED_NAMES or path.suffix != ".sqlite":
            raise ValueError("SIDE_CAR_PATH_NOT_ALLOWED")
        self.read_only = bool(read_only)
        if self.read_only:
            if not path.is_file():
                raise FileNotFoundError("SIDE_CAR_NOT_FOUND")
            uri = "file:" + quote(str(path), safe="/") + "?mode=ro"
            self.db = sqlite3.connect(uri, uri=True)
        else:
            path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            self.db = sqlite3.connect(path)
        self.db.row_factory = sqlite3.Row
        if not self.read_only:
            self.db.execute("PRAGMA journal_mode=WAL")
            self.db.executescript("""
                CREATE TABLE IF NOT EXISTS evidence_documents (
                    kind TEXT NOT NULL,
                    identity TEXT NOT NULL,
                    source_sha256 TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    PRIMARY KEY(kind,identity)
                );
                CREATE INDEX IF NOT EXISTS evidence_documents_kind_idx
                    ON evidence_documents(kind);
            """)

    def close(self):
        self.db.close()

    def _append(self, kind: str, identity: str, document: dict) -> bool:
        if self.read_only:
            raise PermissionError("READ_ONLY_SIDECAR")
        raw = _json(document)
        sha = _sha(raw)
        with self.db:
            old = self.db.execute(
                "SELECT source_sha256 FROM evidence_documents WHERE kind=? AND identity=?",
                (kind, identity),
            ).fetchone()
            if old:
                if old["source_sha256"] != sha:
                    raise ValueError("IMMUTABLE_EVIDENCE_CONFLICT")
                return False
            self.db.execute(
                "INSERT INTO evidence_documents(kind,identity,source_sha256,payload_json) "
                "VALUES(?,?,?,?)",
                (kind, identity, sha, raw),
            )
        return True

    def capture_wallet(self, document: dict) -> bool:
        if (not isinstance(document, dict) or document.get("schema_version") != 1
            or document.get("network") != "solana-mainnet"
            or not document.get("wallet") or
            not document.get("capture_sha256")):
            raise ValueError("CAPTURE_INVALID")
        payload = {k: v for k, v in document.items() if k != "capture_sha256"}
        if _sha(_json(payload)) != document["capture_sha256"]:
            raise ValueError("CAPTURE_HASH_MISMATCH")
        # Repeat a proven identical snapshot is idempotent; each capture hash
        # is an immutable historical source, never "current balance".
        return self._append("ACCOUNT_CAPTURE", document["wallet"] + ":" +
                            document["capture_sha256"], document)

    def record_transaction(self, document: dict) -> bool:
        """Append a versioned derived TX, never rewrite historical V2 entries.

        Previously imported SOL_TOKEN_VIEW_V2 TX documents have the legacy
        identity solana:<signature>:<slot>. That exact key is permanent.
        SOL_TOKEN_VIEW_V3 uses its own :v3 suffix within the same TX kind,
        so re-normalizing an unchanged RAW_TX cannot collide with prior V2.
        An algorithm changing normalized content must get a new version/key.
        """
        chain, signature, slot = transaction_identity(document)
        payload = {k: v for k, v in document.items() if k != "canonical_event_sha256"}
        if _sha(_json(payload)) != document.get("canonical_event_sha256"):
            raise ValueError("TRANSACTION_HASH_MISMATCH")
        schema_version = document.get("schema_version")
        normalizer_version = document.get("normalizer_version")
        if (type(schema_version) is int and schema_version == 2
                and normalizer_version == "SOL_TOKEN_VIEW_V2"):
            suffix = ""  # Immutable historical TX key; never auto-migrate.
        elif (type(schema_version) is int and schema_version == 3
              and normalizer_version == "SOL_TOKEN_VIEW_V3"):
            suffix = ":v3"
        else:
            raise ValueError("UNSUPPORTED_TRANSACTION_NORMALIZER_VERSION")
        identity = chain + ":" + signature + ":" + str(slot) + suffix
        return self._append("TX", identity, document)

    def read_wallet_captures(self, wallet: str, limit: int = 30) -> list[dict]:
        if type(limit) is not int or not 1 <= limit <= 100:
            raise ValueError("INVALID_READ_LIMIT")
        rows = self.db.execute(
            "SELECT payload_json FROM evidence_documents WHERE kind='ACCOUNT_CAPTURE' "
            "AND identity LIKE ? ORDER BY rowid DESC LIMIT ?",
            (wallet + ":%", limit),
        ).fetchall()
        return [json.loads(row["payload_json"]) for row in rows]

    def iter_wallet_captures(self, wallet: str):
        """Stream the *entire* archived owner-capture set without rowid limits.

        The older read_wallet_captures() method intentionally returns only
        recent imports for bounded historical views. It is not safe for
        latest-slot inventory selection: imported backfill may have older
        Solana slots. This read-only iterator has no implicit 100-row cap.
        """
        if not isinstance(wallet, str) or not wallet:
            raise ValueError("RESEARCH_WALLET_INVALID")
        cursor = self.db.execute(
            "SELECT payload_json FROM evidence_documents "
            "WHERE kind='ACCOUNT_CAPTURE' AND identity LIKE ? "
            "ORDER BY rowid DESC",
            (wallet + ":%",),
        )
        while True:
            rows = cursor.fetchmany(256)
            if not rows:
                break
            for row in rows:
                yield json.loads(row["payload_json"])

    def count(self, kind: str) -> int:
        if kind not in {"TX", "ACCOUNT_CAPTURE", "RAW_TX", "WALLET_TX_VIEW", "WALLET_TX_VIEW_V2", "WALLET_TX_VIEW_V3"}:
            raise ValueError("INVALID_EVIDENCE_KIND")
        return int(self.db.execute(
            "SELECT COUNT(*) FROM evidence_documents WHERE kind=?", (kind,)
        ).fetchone()[0])
