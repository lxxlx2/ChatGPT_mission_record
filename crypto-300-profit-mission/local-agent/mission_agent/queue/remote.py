"""Durable remote publication proof in existing SQLite meta, no schema change."""
from ..hashing import canonical, loads
from ..clock import stamp
from ..db.connection import transaction


def publish_remote(repo, transport, batch_id):
    row = repo.db.execute('SELECT * FROM batches WHERE batch_id=?', (batch_id,)).fetchone()
    if row is None or row['state'] in ('EXPIRED', 'CONSUMED'):
        raise ValueError('not publishable')
    key = 'remote-current:' + transport.namespace + ':ingest'
    prior = repo.db.execute('SELECT value FROM meta WHERE key=?', (key,)).fetchone()
    expected = loads(prior[0])['blob_sha'] if prior else None
    batch = loads(row['payload_json'])
    try:
        proof = transport.publish_batch(batch, expected_sha=expected)
        if proof.value != batch or proof.branch != 'mac-data' or proof.path != transport._path('ingest'):
            raise ValueError('remote proof mismatch')
    except Exception as exc:
        with transaction(repo.db):
            repo.db.execute('UPDATE outbox SET attempt_count=attempt_count+1,last_error=? WHERE batch_id=?',
                            (type(exc).__name__, batch_id))
        raise
    value = canonical({'branch': proof.branch, 'path': proof.path, 'blob_sha': proof.blob_sha,
                       'commit_sha': proof.commit_sha, 'batch_id': batch_id,
                       'payload_sha256': batch['payload_sha256']}).decode()
    with transaction(repo.db):
        for name in (key, 'remote-proof:' + transport.namespace + ':' + batch_id):
            repo.db.execute('INSERT INTO meta VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value', (name, value))
        repo.db.execute("UPDATE batches SET state='REMOTE_CONFIRMED' WHERE batch_id=?", (batch_id,))
        repo.db.execute("UPDATE outbox SET state='REMOTE_CONFIRMED',attempt_count=attempt_count+1,last_error=NULL,updated_at=? WHERE batch_id=?",
                        (stamp(repo.clock.now()), batch_id))
    return proof
