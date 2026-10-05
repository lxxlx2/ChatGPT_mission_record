"""Read-only legacy import into a separate shadow ledger; no delivery or service mutation."""
import argparse,gzip,json,sqlite3
from pathlib import Path
from mission_agent.signals.classifier import classify
from mission_agent.signals.registry import load
from mission_agent.signals.store import Ledger
from mission_agent.signals.engine import Engine
from mission_agent.signals.policy import load_policy
from scripts.frank_v1_replay import raw_hash

BASELINE='2026-10-02T22:02:49.509370+00:00'

def snapshot(source,path):
    src=sqlite3.connect('file:'+str(source)+'?mode=ro',uri=True);target=sqlite3.connect(path);src.backup(target);target.close();src.close();Path(path).chmod(0o600)

def import_legacy(ledger,source,raw_root,registry,*,baseline=BASELINE):
    from datetime import datetime
    timestamp=datetime.fromisoformat(baseline).timestamp();_,wallets=load(registry);src=sqlite3.connect('file:'+str(source)+'?mode=ro',uri=True);src.row_factory=sqlite3.Row;inserted=0
    for row in src.execute('SELECT t.* FROM frank_transactions t JOIN frank_observations o USING(signature) WHERE t.block_time>=? ORDER BY t.block_time,t.slot,t.signature',(timestamp,)):
        raw=Path(raw_root)/(row['signature']+'.json.gz');record=json.loads(gzip.decompress(raw.read_bytes()));tx=record['transaction'] if 'status' in record else record
        e=classify(row['signature'],tx,next(iter(wallets)));inserted+=ledger.put(wallets[e['wallet']],e,raw_hash(tx),str(raw),dry_run=True)
    cursor=dict(src.execute('SELECT * FROM frank_cursor').fetchone());src.close();return {'imported':inserted,'cursor':cursor}

def main():
    p=argparse.ArgumentParser();p.add_argument('--legacy-db',type=Path,required=True);p.add_argument('--legacy-raw',type=Path,required=True);p.add_argument('--root',type=Path,required=True);p.add_argument('--registry',type=Path,required=True);p.add_argument('--policy',type=Path,required=True);a=p.parse_args();a.root.mkdir(parents=True,exist_ok=True,mode=0o700)
    backup=a.root/'legacy-bootstrap-snapshot.sqlite';snapshot(a.legacy_db,backup);ledger=Ledger(a.root/'forward.sqlite');result=import_legacy(ledger,backup,a.legacy_raw,a.registry);engine=Engine(ledger,load_policy(a.policy),dry_run=True);engine.drain();_,wallets=load(a.registry)
    if not ledger.cursor(next(iter(wallets))):ledger.checkpoint(next(iter(wallets)),result['cursor']['signature'],result['cursor']['slot'])
    result.update(mode='SHADOW_DELIVERY_DISABLED',model=engine.summary(),baseline=BASELINE,integrity=ledger.db.execute('PRAGMA integrity_check').fetchone()[0]);(a.root/'bootstrap.json').write_text(json.dumps(result,indent=2));print(json.dumps(result));ledger.db.close()
if __name__=='__main__':main()
