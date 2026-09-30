from ..hashing import loads,verify,canonical
from ..clock import parse_utc,stamp
from ..models import DECISIONS
from ..db.connection import transaction


def reconcile(repo,receipt,fail_after=None):
    try:
        receipt=loads(canonical(receipt))
        with transaction(repo.db):
            row=repo.db.execute("SELECT * FROM batches WHERE batch_id=?",(receipt['input_batch_id'],)).fetchone()
            if row is None or row['state']=='EXPIRED':
                raise ValueError('unknown/expired batch')
            batch=loads(row['payload_json']);verify(batch)
            expected={x['event_id']:x for x in batch['items']}
            decisions=receipt['decisions']
            ids=[x['event_id'] for x in decisions]
            if (type(receipt['schema_version']) is not int or receipt['schema_version']!=1 or receipt['input_payload_sha256']!=batch['payload_sha256']
                or any(type(receipt[k]) is not int or receipt[k]!=len(expected) for k in ('consumed_item_count','decision_count'))
                or len(ids)!=len(expected) or len(set(ids))!=len(ids) or set(ids)!=set(expected)):
                raise ValueError('receipt set/count/hash mismatch')
            when=parse_utc(receipt['decision_timestamp'])
            if when<parse_utc(batch['generated_at']) or when>parse_utc(batch['valid_until']):
                raise ValueError('receipt decision time outside batch lifetime')
            if not isinstance(receipt['consumer_version'],str) or not receipt['consumer_version']:
                raise ValueError('missing consumer version')
            # Validate the entire receipt before any writes, then commit every item together.
            for decision in decisions:
                if decision['decision'] not in DECISIONS or decision['item_payload_sha256']!=expected[decision['event_id']]['payload_sha256']:
                    raise ValueError('invalid item decision/hash')
                if not isinstance(decision['reason'],dict):
                    raise ValueError('reason must be structured')
                old=repo.db.execute('SELECT decision FROM decisions WHERE event_id=?',(decision['event_id'],)).fetchone()
                if old and old[0]!=decision['decision']:
                    raise ValueError('conflicting prior decision')
            now=stamp(repo.clock.now())
            for index,decision in enumerate(decisions):
                id=decision['event_id'];value=decision['decision']
                repo.db.execute('INSERT OR IGNORE INTO decisions VALUES(?,?,?,?,?,?,?)',(id,batch['batch_id'],batch['payload_sha256'],value,canonical(decision['reason']).decode(),receipt['consumer_version'],receipt['decision_timestamp']))
                state={'IGNORE':'DECIDED_IGNORE','WATCH':'DECIDED_WATCH'}.get(value,'DELIVERY_PENDING')
                repo.db.execute("UPDATE deliveries SET state=?,updated_at=? WHERE event_id=? AND state='PENDING_DECISION'",(state,now,id))
                repo.db.execute("UPDATE candidates SET status=?,updated_at_utc=? WHERE event_id=?",('DECIDED_'+value,now,id))
                repo.db.execute("UPDATE outbox SET state='CONSUMED',updated_at=? WHERE event_id=?",(now,id))
                if fail_after==index:
                    raise RuntimeError('injected receipt persistence failure')
            repo.db.execute("UPDATE batches SET state='CONSUMED' WHERE batch_id=?",(batch['batch_id'],))
        return True
    except (ValueError,KeyError,TypeError,UnicodeError) as exc:
        repo.quarantine(None,'RECEIPT_REJECTED:'+str(exc))
        return False
