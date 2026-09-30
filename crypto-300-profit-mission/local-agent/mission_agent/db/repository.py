import hashlib
from pathlib import Path
from ..clock import Clock, stamp
from ..hashing import canonical, digest, loads
from ..models import Event, EVENT_TYPES
from .connection import connect, transaction
from .migrations import migrate


class Repository:
    def __init__(self, path, clock=None, policy="at_least_once", disk_budget_bytes=5_000_000_000):
        if policy not in ("at_least_once", "at_most_once"):
            raise ValueError("invalid delivery policy")
        self.path = Path(path)
        self.clock = clock or Clock()
        self.policy = policy
        self.disk_budget_bytes = disk_budget_bytes
        self.db = connect(path)
        try:
            migrate(self.db, stamp(self.clock.now()))
        except BaseException:
            self.db.close()
            raise

    def close(self):
        self.db.close()

    def quarantine(self, event_id, reason, raw=b""):
        key = hashlib.sha256((str(event_id) + reason).encode() + raw).hexdigest()
        with transaction(self.db):
            self.db.execute("INSERT OR IGNORE INTO quarantine VALUES(?,?,?,?)",
                            (key, event_id, reason, stamp(self.clock.now())))
        return key

    def ingest_json(self, raw):
        try:
            args = loads(raw)
            event = Event.synthetic(**args)
        except (ValueError, TypeError, KeyError, UnicodeError):
            self.quarantine(None, "CORRUPT_INPUT", raw.encode() if isinstance(raw, str) else raw)
            return "QUARANTINED"
        return self.ingest(event)

    def ingest(self, event, fail_at=None):
        if event.source != "synthetic" or event.event_type not in EVENT_TYPES:
            raise ValueError("PHASE 1 only permits synthetic events")
        payload = canonical(event.payload).decode()
        sha = digest(event.payload)
        now = stamp(self.clock.now())
        from ..storage import admit
        with transaction(self.db):
            old = self.db.execute("SELECT * FROM candidates WHERE event_id=?", (event.event_id,)).fetchone()
            if old:
                identity = (event.event_type, event.source, event.asset, event.observed_at_utc, event.priority, sha)
                prior = tuple(old[k] for k in ("event_type", "source", "asset", "observed_at_utc", "priority", "payload_sha256"))
                if identity != prior:
                    key = digest({"event_id": event.event_id, "sha": sha, "reason": "ID_CONFLICT"})
                    self.db.execute("INSERT OR IGNORE INTO quarantine VALUES(?,?,?,?)", (key, event.event_id, "ID_CONFLICT", now))
                    return "QUARANTINED"
                return "DUPLICATE"
            admit(self.path.parent, len(payload.encode()) + 65536, self.disk_budget_bytes)
            self.db.execute("INSERT INTO candidates VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                            (event.event_id,event.event_type,event.source,event.asset,event.observed_at_utc,now,1,
                             event.priority,payload,sha,"PENDING_DECISION",now))
            if fail_at == "candidate":
                raise RuntimeError("injected candidate failure")
            self.db.execute("INSERT INTO outbox(event_id,state,created_at,updated_at) VALUES(?,'PENDING',?,?)", (event.event_id,now,now))
            self.db.execute("INSERT INTO deliveries(event_id,policy,state,updated_at) VALUES(?,?,'PENDING_DECISION',?)", (event.event_id,self.policy,now))
            if fail_at == "outbox":
                raise RuntimeError("injected outbox failure")
        return "CREATED"

    def counts(self):
        return {t:self.db.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                for t in ("candidates","outbox","batches","decisions","deliveries","quarantine","health")}

    def expire_batch(self, batch_id):
        from ..clock import parse_utc
        with transaction(self.db):
            row=self.db.execute("SELECT * FROM batches WHERE batch_id=?",(batch_id,)).fetchone()
            if row is None or self.clock.now() <= parse_utc(row['valid_until']):
                raise ValueError("batch not expired")
            if row['state']=='CONSUMED':
                return
            self.db.execute("UPDATE batches SET state='EXPIRED' WHERE batch_id=?",(batch_id,))
            self.db.execute("UPDATE outbox SET state='PENDING',batch_id=NULL,updated_at=? WHERE batch_id=? AND state!='CONSUMED'",(stamp(self.clock.now()),batch_id))

    def backup(self, destination):
        import sqlite3
        destination=Path(destination)
        if destination.resolve()==self.path.resolve():
            raise ValueError("backup destination must be distinct")
        with sqlite3.connect(destination) as dest:
            self.db.backup(dest)
            if dest.execute('PRAGMA integrity_check').fetchone()[0]!='ok':
                raise ValueError('backup integrity failure')
        destination.chmod(0o600)
