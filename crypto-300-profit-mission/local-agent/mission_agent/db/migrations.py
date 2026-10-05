import hashlib
from .connection import transaction

SCHEMA = """
CREATE TABLE meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);
CREATE TABLE candidates(event_id TEXT PRIMARY KEY,event_type TEXT NOT NULL,source TEXT NOT NULL,
 asset TEXT,observed_at_utc TEXT NOT NULL,created_at_utc TEXT NOT NULL,schema_version INTEGER NOT NULL,
 priority INTEGER NOT NULL CHECK(priority IN(0,1)),payload_json TEXT NOT NULL,payload_sha256 TEXT NOT NULL,
 status TEXT NOT NULL,updated_at_utc TEXT NOT NULL);
CREATE TABLE outbox(id INTEGER PRIMARY KEY,event_id TEXT UNIQUE NOT NULL REFERENCES candidates(event_id),
 state TEXT NOT NULL,attempt_count INTEGER NOT NULL DEFAULT 0,last_error TEXT,batch_id TEXT,
 created_at TEXT NOT NULL,updated_at TEXT NOT NULL);
CREATE TABLE batches(batch_id TEXT PRIMARY KEY,schema_version INTEGER NOT NULL,generated_at TEXT NOT NULL,
 valid_until TEXT NOT NULL,item_count INTEGER NOT NULL,payload_sha256 TEXT NOT NULL,payload_json TEXT NOT NULL,
 state TEXT NOT NULL,created_at TEXT NOT NULL);
CREATE TABLE batch_items(batch_id TEXT NOT NULL REFERENCES batches(batch_id),event_id TEXT NOT NULL REFERENCES candidates(event_id),
 ordinal INTEGER NOT NULL,PRIMARY KEY(batch_id,event_id),UNIQUE(batch_id,ordinal));
CREATE TABLE decisions(event_id TEXT PRIMARY KEY REFERENCES candidates(event_id),batch_id TEXT NOT NULL REFERENCES batches(batch_id),
 input_payload_sha256 TEXT NOT NULL,decision TEXT NOT NULL,reason_json TEXT NOT NULL,consumer_version TEXT NOT NULL,decided_at TEXT NOT NULL);
CREATE TABLE deliveries(event_id TEXT PRIMARY KEY REFERENCES candidates(event_id),policy TEXT NOT NULL,state TEXT NOT NULL,
 lease_token TEXT,fence INTEGER NOT NULL DEFAULT 0,lease_expires_at TEXT,provider_message_id TEXT,last_sent_attempt_at TEXT,
 cooldown_until TEXT,last_error TEXT,updated_at TEXT NOT NULL);
CREATE TABLE health(seq INTEGER PRIMARY KEY,generated_at TEXT NOT NULL,valid_until TEXT NOT NULL,
 overall TEXT NOT NULL,payload_json TEXT NOT NULL);
CREATE TABLE quarantine(id TEXT PRIMARY KEY,event_id TEXT,reason TEXT NOT NULL,observed_at TEXT NOT NULL);
CREATE INDEX outbox_state_idx ON outbox(state,id);
"""


def migrate(db, now, fail_after=None):
    # Both bootstrap and DDL/version row are in one explicit transaction.
    checksum = hashlib.sha256(SCHEMA.encode()).hexdigest()
    with transaction(db):
        db.execute("CREATE TABLE IF NOT EXISTS schema_migrations(version INTEGER PRIMARY KEY,checksum TEXT NOT NULL,applied_at TEXT NOT NULL)")
        rows = db.execute("SELECT * FROM schema_migrations ORDER BY version").fetchall()
        if rows:
            if len(rows) != 1 or rows[0]["version"] != 1 or rows[0]["checksum"] != checksum:
                raise ValueError("unsupported schema version/checksum")
            return
        for i, statement in enumerate(filter(str.strip, SCHEMA.split(";"))):
            db.execute(statement)
            if fail_after == i:
                raise RuntimeError("injected migration interruption")
        db.execute("INSERT INTO schema_migrations VALUES(1,?,?)", (checksum, now))
        db.execute("INSERT INTO meta VALUES('batch_seq','0')")
        db.execute("INSERT INTO meta VALUES('health_seq','0')")
        db.execute("INSERT INTO meta VALUES('install_namespace',?)", ("synthetic-local-v1",))
