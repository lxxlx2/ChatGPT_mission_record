"""Opt-in Phase 3 migration; v1 foundation ledger remains backward-compatible."""
import hashlib
from .connection import transaction
SCHEMA='''
CREATE TABLE price_bars_1m(asset TEXT NOT NULL,open_time_utc INTEGER NOT NULL,source TEXT NOT NULL,payload_json TEXT NOT NULL,is_closed INTEGER NOT NULL,source_hash TEXT NOT NULL,bar_version INTEGER NOT NULL,inserted_at TEXT NOT NULL,updated_at TEXT NOT NULL,PRIMARY KEY(asset,open_time_utc,source));
CREATE TABLE price_source_state(asset TEXT PRIMARY KEY,last_closed_bar_time INTEGER,last_source_event_time INTEGER,connection_generation INTEGER NOT NULL DEFAULT 0,reconnect_count INTEGER NOT NULL DEFAULT 0,duplicate_event_count INTEGER NOT NULL DEFAULT 0,out_of_order_count INTEGER NOT NULL DEFAULT 0,missing_bar_count INTEGER NOT NULL DEFAULT 0,rest_repair_count INTEGER NOT NULL DEFAULT 0,status TEXT NOT NULL DEFAULT 'UNKNOWN',payload_json TEXT NOT NULL DEFAULT '{}');
CREATE TABLE price_features(asset TEXT NOT NULL,window_end INTEGER NOT NULL,payload_json TEXT NOT NULL,PRIMARY KEY(asset,window_end));
CREATE TABLE price_candidates(event_id TEXT PRIMARY KEY,asset TEXT NOT NULL,window_end INTEGER NOT NULL,payload_sha256 TEXT NOT NULL,payload_json TEXT NOT NULL);
CREATE TABLE price_replay_run(run_id TEXT PRIMARY KEY,rule_version TEXT NOT NULL,started_at TEXT NOT NULL,result_json TEXT NOT NULL);
CREATE TABLE price_shadow_metrics(run_id TEXT NOT NULL,seq INTEGER NOT NULL,payload_json TEXT NOT NULL,PRIMARY KEY(run_id,seq));
'''
def migrate_price(db,now,fail_after=None):
 checksum=hashlib.sha256(SCHEMA.encode()).hexdigest()
 with transaction(db):
  db.execute('CREATE TABLE IF NOT EXISTS price_schema_migrations(version INTEGER PRIMARY KEY,checksum TEXT NOT NULL,applied_at TEXT NOT NULL)')
  rows=db.execute('SELECT * FROM price_schema_migrations').fetchall()
  if rows:
   if len(rows)!=1 or rows[0]['version']!=1 or rows[0]['checksum']!=checksum:raise ValueError('unsupported price migration')
   return
  for i,statement in enumerate(filter(str.strip,SCHEMA.split(';'))):
   db.execute(statement)
   if i==fail_after:raise RuntimeError('injected price migration failure')
  db.execute('INSERT INTO price_schema_migrations VALUES(1,?,?)',(checksum,now))
