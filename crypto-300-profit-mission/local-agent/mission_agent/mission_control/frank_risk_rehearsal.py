"""Persisted Option3 delivery rehearsal with a synthetic receipt transport."""
from contextlib import closing, contextmanager
import math
from pathlib import Path
import sqlite3

from ..hashing import digest
from .frank_risk_runs import KINDS, _load_sealed
from .evidence_manifests import canonical


class RiskNotificationRehearsal:
    """Explicit fixture entry point. The Dashboard and V1 sender do not call it."""

    def __init__(self, root, *, kinds, max_age_seconds, clock):
        self.path = Path(root) / "option3-notification-rehearsal.sqlite"
        self.kinds = frozenset(kinds)
        if (not self.kinds or not self.kinds <= KINDS or type(max_age_seconds) is not int
                or max_age_seconds <= 0):
            raise ValueError("OPTION3_REHEARSAL_POLICY_INVALID")
        self.max_age_seconds = max_age_seconds
        self.clock = clock
        self.policy_sha256 = digest(["OPTION3_FIXTURE_POLICY_V1", sorted(self.kinds), max_age_seconds])

    @contextmanager
    def _db(self):
        if self.path.is_symlink():
            raise ValueError("OPTION3_REHEARSAL_STORE_INVALID")
        with closing(sqlite3.connect(self.path)) as db, db:
            self.path.chmod(0o600)
            db.row_factory = sqlite3.Row
            db.execute("BEGIN IMMEDIATE")
            db.execute("""CREATE TABLE IF NOT EXISTS option3_rehearsal (
                id TEXT PRIMARY KEY, update_id TEXT NOT NULL, policy_sha256 TEXT NOT NULL,
                content_sha256 TEXT NOT NULL, observed_at REAL NOT NULL, expires_at REAL NOT NULL,
                status TEXT NOT NULL, attempts INTEGER NOT NULL)""")
            yield db

    def enqueue(self, update):
        row = _load_sealed(canonical(update), "update_sha256")
        if row.get("notification_enabled") is not False:
            raise ValueError("OPTION3_REHEARSAL_REQUIRES_LOCAL_RISK_UPDATE")
        if row.get("kind") not in self.kinds:
            return None
        observed_at = row.get("observed_at")
        if (type(observed_at) not in (int, float) or not math.isfinite(observed_at)
                or observed_at < 0):
            raise ValueError("OPTION3_REHEARSAL_TIME_INVALID")
        identity = digest(["OPTION3_FAKE_CHANNEL_V1", row["update_id"]])
        content = digest(["OPTION3_FAKE_PAYLOAD_V1", self.policy_sha256, row["update_sha256"]])
        now = self.clock()
        expires_at = observed_at + self.max_age_seconds
        status = "PENDING" if observed_at <= now < expires_at else "INELIGIBLE_TIME"
        with self._db() as db:
            db.execute("INSERT OR IGNORE INTO option3_rehearsal VALUES(?,?,?,?,?,?,?,0)",
                       (identity, row["update_id"], self.policy_sha256, content, observed_at, expires_at, status))
        return identity

    @staticmethod
    def _row(db, identity):
        row = db.execute("SELECT * FROM option3_rehearsal WHERE id=?", (identity,)).fetchone()
        return dict(row) if row else None

    def process(self, identity, *, simulator):
        with self._db() as db:
            row = self._row(db, identity)
            if row is None:
                return None
            claim = row["status"] == "PENDING"
            if claim:
                now = self.clock()
                if row["policy_sha256"] != self.policy_sha256:
                    state = "POLICY_CHANGED"
                elif not row["observed_at"] <= now < row["expires_at"]:
                    state = "INELIGIBLE_TIME"
                else:
                    state = "OUTCOME_UNVERIFIED"
                db.execute("UPDATE option3_rehearsal SET status=?, attempts=attempts+? WHERE id=?",
                           (state, int(state == "OUTCOME_UNVERIFIED"), identity))
                row = self._row(db, identity)
            if row["status"] != "OUTCOME_UNVERIFIED":
                return row

        # The attempt exists on disk before crossing the synthetic transport
        # boundary. A restart only reconciles a receipt for a reserved identity.
        if claim:
            try:
                simulator.record(identity, row["content_sha256"])
            except (OSError, TimeoutError):
                return row
        try:
            receipt = simulator.lookup(identity)
        except (OSError, TimeoutError):
            return row
        if receipt != {"id": identity, "content_sha256": row["content_sha256"], "scope": "FAKE"}:
            return row
        with self._db() as db:
            db.execute("UPDATE option3_rehearsal SET status='FAKE_RECEIPT_VERIFIED' WHERE id=? AND status='OUTCOME_UNVERIFIED'",
                       (identity,))
            return self._row(db, identity)
