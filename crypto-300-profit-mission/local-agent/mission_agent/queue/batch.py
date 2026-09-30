from datetime import timedelta
from ..clock import stamp
from ..hashing import canonical, loads, seal, digest
from ..db.connection import transaction


def item(row):
    return {"schema_version":row['schema_version'],"event_id":row['event_id'],"event_type":row['event_type'],
            "source":row['source'],"asset":row['asset'],"observed_at_utc":row['observed_at_utc'],
            "created_at_utc":row['created_at_utc'],"priority":row['priority'],
            "payload":loads(row['payload_json']),"payload_sha256":row['payload_sha256']}


def build_batch(repo, config):
    from ..storage import admit
    admit(config.runtime_root, config.max_batch_bytes * 2 + 65536, config.disk_budget_bytes)
    now=stamp(repo.clock.now())
    expiry=stamp(repo.clock.now()+timedelta(seconds=config.batch_ttl_seconds))
    with transaction(repo.db):
        seq=int(repo.db.execute("SELECT value FROM meta WHERE key='batch_seq'").fetchone()[0])+1
        ns=repo.db.execute("SELECT value FROM meta WHERE key='install_namespace'").fetchone()[0]
        batch_id=f"{ns}:{seq:012d}"
        envelope={"schema_version":1,"batch_id":batch_id,"generated_at":now,"valid_until":expiry,"item_count":0,"items":[]}
        counts={0:0,1:0}
        rows=repo.db.execute("SELECT c.* FROM candidates c JOIN outbox o USING(event_id) WHERE o.state='PENDING' ORDER BY c.priority DESC,c.observed_at_utc,c.event_id").fetchall()
        for row in rows:
            value=item(row)
            if len(canonical(value))>config.max_item_bytes:
                key=digest({"id":row['event_id'],"reason":"ITEM_TOO_LARGE"})
                repo.db.execute("INSERT OR IGNORE INTO quarantine VALUES(?,?,?,?)",(key,row['event_id'],'ITEM_TOO_LARGE',now))
                repo.db.execute("UPDATE candidates SET status='QUARANTINED',updated_at_utc=? WHERE event_id=?",(now,row['event_id']))
                repo.db.execute("UPDATE outbox SET state='QUARANTINED',last_error='ITEM_TOO_LARGE',updated_at=? WHERE event_id=?",(now,row['event_id']))
                continue
            priority=row['priority']
            limit=config.urgent_limit if priority else config.normal_limit
            if counts[priority]>=limit:
                continue
            proposal={**envelope,"items":envelope['items']+[value],"item_count":envelope['item_count']+1}
            if len(canonical(seal(proposal)))>config.max_batch_bytes:
                continue
            envelope=proposal
            counts[priority]+=1
        if not envelope['items']:
            return None
        batch=seal(envelope)
        repo.db.execute("INSERT INTO batches VALUES(?,?,?,?,?,?,?,?,?)",(batch_id,1,now,expiry,batch['item_count'],batch['payload_sha256'],canonical(batch).decode(),'BUILT',now))
        repo.db.execute("UPDATE meta SET value=? WHERE key='batch_seq'",(str(seq),))
        for ordinal,value in enumerate(batch['items']):
            repo.db.execute("INSERT INTO batch_items VALUES(?,?,?)",(batch_id,value['event_id'],ordinal))
            repo.db.execute("UPDATE outbox SET state='BATCHED',batch_id=?,updated_at=? WHERE event_id=?",(batch_id,now,value['event_id']))
        return batch


def publish(repo,transport,batch_id):
    row=repo.db.execute("SELECT * FROM batches WHERE batch_id=?",(batch_id,)).fetchone()
    if row is None or row['state'] in ('EXPIRED','CONSUMED'):
        raise ValueError('not publishable')
    try:
        batch=loads(row['payload_json'])
        transport.publish_batch(batch)
    except Exception as exc:
        with transaction(repo.db):
            repo.db.execute("UPDATE outbox SET attempt_count=attempt_count+1,last_error=? WHERE batch_id=?",(type(exc).__name__,batch_id))
        raise
    with transaction(repo.db):
        repo.db.execute("UPDATE batches SET state='PUBLISHED' WHERE batch_id=?",(batch_id,))
        repo.db.execute("UPDATE outbox SET state='PUBLISHED',attempt_count=attempt_count+1,last_error=NULL,updated_at=? WHERE batch_id=?",(stamp(repo.clock.now()),batch_id))
