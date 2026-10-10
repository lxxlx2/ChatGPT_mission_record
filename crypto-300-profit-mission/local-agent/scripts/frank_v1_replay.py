"""Raw-bound historical replay. Delivery is unconditionally disabled."""
import argparse,gzip,hashlib,json,sqlite3
from pathlib import Path
from mission_agent.signals.policy import load_policy
from mission_agent.signals.store import Ledger
from mission_agent.signals.engine import Engine
from mission_agent.signals.classifier import classify

def raw_hash(tx):return hashlib.sha256(json.dumps(tx,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def import_ledger(ledger,source):
    db=sqlite3.connect('file:'+str(source)+'?mode=ro',uri=True);db.row_factory=sqlite3.Row;count=0
    rows=db.execute('SELECT * FROM signatures ORDER BY block_time,slot,signature')
    for row in rows:
        record=json.loads(gzip.decompress(Path(row['raw_reference']).read_bytes()))
        if 'status' in record and 'signature' in record:
            if record['signature']!=row['signature']:raise ValueError('RAW_SIGNATURE_BINDING')
            tx=record['transaction']
        else:tx=record
        if raw_hash(tx)!=row['raw_hash']:raise ValueError('RAW_HASH_CONFLICT')
        e=classify(row['signature'],tx,row['wallet'])
        if e['classification']!=json.loads(row['body'])['classification']:raise ValueError('CLASSIFICATION_DRIFT')
        count+=ledger.put(row['person_id'],e,row['raw_hash'],row['raw_reference'],dry_run=True)
    db.close();return count

def report(engine,path):
    db=engine.db;value=engine.summary();value['active_trades']=db.execute("SELECT count(*) FROM signatures WHERE json_extract(body,'$.classification')='ACTIVE_TRADE'").fetchone()[0]
    value['signals']=[json.loads(r[0]) for r in db.execute('SELECT body FROM signals ORDER BY CAST(created_at AS INTEGER),signal_id')]
    value['predicate_evaluations']=db.execute('SELECT count(*) FROM v1_evaluations').fetchone()[0]
    value['notifications_sent']=0;value['gmail_sent']=0
    if db.execute("SELECT count(*) FROM outbox WHERE status IS NOT 'DRY_RUN_AUDIT'").fetchone()[0]:raise ValueError('HISTORICAL_DELIVERY_MUST_BE_DISABLED')
    Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n');return value

def main():
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,action='append',required=True);p.add_argument('--db',type=Path,required=True);p.add_argument('--policy',type=Path,required=True);p.add_argument('--report',type=Path,required=True);a=p.parse_args()
    if a.db.exists():raise ValueError('REPLAY_REQUIRES_NEW_ISOLATED_DB')
    l=Ledger(a.db);engine=Engine(l,load_policy(a.policy),dry_run=True)
    for source in a.source:import_ledger(l,source)
    engine.drain();value=report(engine,a.report);print(json.dumps({k:v for k,v in value.items() if k!='signals'},ensure_ascii=False));l.db.close()
if __name__=='__main__':main()
