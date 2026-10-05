"""Additive FM4 schema in the existing durable database; baseline observations never replay."""
from ..hashing import canonical,loads,verify,digest
from ..db.connection import transaction
from .schema import candidates,run_bundle,epoch,iso

DDL=(
'CREATE TABLE IF NOT EXISTS meme_meta(key TEXT PRIMARY KEY,value TEXT NOT NULL)',
'CREATE TABLE IF NOT EXISTS meme_source_observations(wallet TEXT,signature TEXT,state TEXT NOT NULL,PRIMARY KEY(wallet,signature))',
'CREATE TABLE IF NOT EXISTS meme_facts(event_id TEXT PRIMARY KEY,event_at TEXT NOT NULL,body TEXT NOT NULL)',
'CREATE INDEX IF NOT EXISTS meme_facts_time ON meme_facts(event_at)',
'CREATE TABLE IF NOT EXISTS meme_signals(signal_id TEXT PRIMARY KEY,run_id TEXT NOT NULL,body TEXT NOT NULL)',
'CREATE TABLE IF NOT EXISTS meme_runs(run_id TEXT PRIMARY KEY,created_at TEXT NOT NULL,body TEXT NOT NULL,state TEXT NOT NULL)',
'CREATE TABLE IF NOT EXISTS meme_decisions(decision_id TEXT PRIMARY KEY,run_id TEXT NOT NULL,signal_id TEXT NOT NULL,body TEXT NOT NULL,UNIQUE(run_id,signal_id))',
'CREATE TABLE IF NOT EXISTS meme_mail_outbox(mail_run_id TEXT PRIMARY KEY,run_id TEXT NOT NULL,content_hash TEXT NOT NULL,expires_at TEXT NOT NULL,body TEXT NOT NULL,state TEXT NOT NULL,receipt TEXT)',
'CREATE TABLE IF NOT EXISTS meme_mail_signals(signal_id TEXT PRIMARY KEY,mail_run_id TEXT NOT NULL)',
'CREATE TABLE IF NOT EXISTS meme_transport(run_id TEXT PRIMARY KEY,receipt TEXT NOT NULL)')

def migrate(db,cutoff,registry,*,legacy_wallet=None):
    with transaction(db):
        for statement in DDL:db.execute(statement)
        schema=db.execute("SELECT value FROM meme_meta WHERE key='schema_hash'").fetchone()
        if schema and schema[0]!=digest(list(DDL)):raise ValueError('MEME_SQLITE_SCHEMA_DRIFT')
        db.execute('INSERT OR IGNORE INTO meme_meta VALUES(?,?)',('schema_hash',digest(list(DDL))))
        db.execute('INSERT OR IGNORE INTO meme_meta VALUES(?,?)',('schema_version','2'))
        old=db.execute("SELECT value FROM meme_meta WHERE key='migration_cutoff'").fetchone()
        if old:return old[0]
        db.execute('INSERT INTO meme_meta VALUES(?,?)',('migration_cutoff',cutoff))
        db.execute('INSERT INTO meme_meta VALUES(?,?)',('registry_at_migration',registry.sha256))
        if legacy_wallet:
            for row in db.execute('SELECT signature FROM frank_observations').fetchall():
                db.execute('INSERT OR IGNORE INTO meme_source_observations VALUES(?,?,?)',(legacy_wallet,row[0],'BASELINE_EXCLUDED'))
    return cutoff

class SignalStore:
    def __init__(self,db,registry,policy):self.db,self.registry,self.policy=db,registry,policy
    def stage(self,facts,now,*,observation=None):
        with transaction(self.db):
            for f in facts:
                verify(f)
                if f['namespace']!=self.registry.namespace:raise ValueError('FACT_NAMESPACE')
                old=self.db.execute('SELECT body FROM meme_facts WHERE event_id=?',(f['event_id'],)).fetchone();body=canonical(f).decode()
                if old and old[0]!=body:raise ValueError('FACT_IMMUTABLE_CONFLICT')
                self.db.execute('INSERT OR IGNORE INTO meme_facts VALUES(?,?,?)',(f['event_id'],f['event_at'],body))
            recent=self.db.execute('SELECT body FROM meme_facts WHERE event_at>=? ORDER BY event_at,event_id LIMIT 1001',(iso(epoch(now)-max(self.policy['consensus_window_seconds'],self.policy['ttl']['value_seconds'])),)).fetchall()
            if len(recent)>1000:raise ValueError('RECENT_FACTS_BOUND_EXCEEDED')
            rows=[loads(r[0]) for r in recent]
            all_candidates=candidates(rows,self.registry,self.policy)
            new=[c for c in all_candidates if epoch(now)<epoch(c['expires_at']) and not self.db.execute('SELECT 1 FROM meme_signals WHERE signal_id=?',(c['signal_id'],)).fetchone()]
            run=run_bundle(new[:8],self.registry.namespace) if new else None
            if run:
                self.db.execute('INSERT INTO meme_runs VALUES(?,?,?,?)',(run['run_id'],run['created_at'],canonical(run).decode(),'READY'))
                for c in run['candidates']:self.db.execute('INSERT INTO meme_signals VALUES(?,?,?)',(c['signal_id'],run['run_id'],canonical(c).decode()))
            if observation:self.db.execute('INSERT INTO meme_source_observations VALUES(?,?,?)',(*observation,'PROCESSED'))
        return run
