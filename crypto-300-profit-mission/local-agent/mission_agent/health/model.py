import shutil
from datetime import timedelta
from ..clock import stamp,parse_utc
from ..hashing import canonical
from ..db.connection import transaction
from .evaluator import SOURCE_FIELDS,evaluate


def storage_bytes(root):
    from ..storage import used_bytes
    return used_bytes(root)


def snapshot(repo,config,host_boot_id='synthetic-host',last_e2e='UNKNOWN'):
    now=repo.clock.now();root=config.runtime_root
    pending=repo.db.execute("SELECT COUNT(*),MIN(created_at_utc) FROM candidates WHERE status='PENDING_DECISION'").fetchone()
    unsynced=repo.db.execute("SELECT COUNT(*) FROM outbox WHERE state IN('PENDING','BATCHED')").fetchone()[0]
    with transaction(repo.db):
        seq=int(repo.db.execute("SELECT value FROM meta WHERE key='health_seq'").fetchone()[0])+1
        value={k:'UNKNOWN' for k in SOURCE_FIELDS}
        value.update({'seq':seq,'generated_at':stamp(now),'valid_until':stamp(now+timedelta(minutes=20)),
                      'host_boot_id':host_boot_id,'collector_version':'synthetic-only-v0.1.0','sqlite_writable':True,
                      'disk_free_bytes':shutil.disk_usage(root).free,'storage_used_bytes':storage_bytes(root),
                      'unsynced_events':unsynced,'gpt_pending_events':pending[0],
                      'oldest_pending_age_sec':max(0,int((now-parse_utc(pending[1])).total_seconds())) if pending[1] else 0,
                      'last_e2e_canary':last_e2e,'last_e2e_canary_at':'UNKNOWN','restart_count_24h':'UNKNOWN',
                      'sleep_gap_detected':'UNKNOWN'})
        value['overall']=evaluate(value,now,config.disk_budget_bytes)['overall']
        repo.db.execute('INSERT INTO health VALUES(?,?,?,?,?)',(seq,value['generated_at'],value['valid_until'],value['overall'],canonical(value).decode()))
        repo.db.execute("UPDATE meta SET value=? WHERE key='health_seq'",(str(seq),))
        repo.db.execute('DELETE FROM health WHERE seq<=?',(seq-1000,))
    return value
