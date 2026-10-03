"""Read-only audit queries and isolated, always-delivery-disabled replay."""
import argparse,gzip,hashlib,json,sqlite3
from pathlib import Path
from collections import Counter
from .classifier import classify
from .registry import load
from .store import Ledger

def inspect(db,signature):
    results=[]
    for r in db.execute('SELECT * FROM signatures WHERE signature=?',(signature,)):
        value=dict(r);value['body']=json.loads(value['body'])
        trade=db.execute('SELECT body FROM trades WHERE wallet=? AND signature=?',(r['wallet'],r['signature'])).fetchone()
        value['trade_record']=json.loads(trade[0]) if trade else None
        value['signals']=[json.loads(x[0]) for x in db.execute("SELECT body FROM signals WHERE json_extract(body,'$.latest_trade_signature')=?",(signature,))]
        value['delivery_state']=[dict(x) for x in db.execute("SELECT * FROM outbox WHERE signal_id IN (SELECT signal_id FROM signals WHERE json_extract(body,'$.latest_trade_signature')=?)",(signature,))]
        for delivery in value['delivery_state']:
            if delivery['receipt']:delivery['receipt']=json.loads(delivery['receipt'])
        results.append(value)
    if not results and db.execute("SELECT 1 FROM sqlite_master WHERE name='signature_detections'").fetchone():
        for r in db.execute('SELECT * FROM signature_detections WHERE signature=?',(signature,)):
            results.append({**dict(r),'classification':'UNKNOWN_NEEDS_REVIEW','classification_reason':'RAW_PENDING_CURSOR_NOT_ADVANCED','signal_generated':False})
    return results

def audit(db,last):
    rows=[]
    for r in db.execute('SELECT * FROM signatures ORDER BY slot DESC,signature DESC LIMIT ?',(last,)):
        e=json.loads(r['body']);rows.append((r['slot'],r['block_time'],r['signature'],e['classification'],r['alert_state'],r['alert_reason']))
    if db.execute("SELECT 1 FROM sqlite_master WHERE name='signature_detections'").fetchone():
        for r in db.execute('SELECT d.* FROM signature_detections d LEFT JOIN signatures s USING(wallet,signature) WHERE s.signature IS NULL ORDER BY d.slot DESC LIMIT ?',(last,)):
            rows.append((r['slot'],r['block_time'],r['signature'],'UNKNOWN_NEEDS_REVIEW','NO','RAW_PENDING_CURSOR_NOT_ADVANCED'))
    return sorted(rows,key=lambda r:(r[0],r[2]),reverse=True)[:last]

def main():
    p=argparse.ArgumentParser();p.add_argument('--db',type=Path,required=True)
    sub=p.add_subparsers(dest='command',required=True)
    a=sub.add_parser('audit-frank');a.add_argument('--last',type=int,default=50)
    a=sub.add_parser('inspect-tx');a.add_argument('signature')
    a=sub.add_parser('replay');a.add_argument('--source-db',type=Path,required=True);a.add_argument('--raw',type=Path,action='append',required=True);a.add_argument('--registry',type=Path,required=True);a.add_argument('--since',type=int,default=0);a.add_argument('--policy',type=Path,default=Path(__file__).resolve().parents[2]/'config/frank_local_signal_v1.json')
    args=p.parse_args()
    if args.command in ('audit-frank','inspect-tx'):
        db=sqlite3.connect('file:'+str(args.db)+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
        if args.command=='inspect-tx':print(json.dumps(inspect(db,args.signature),indent=2))
        else:
            for row in audit(db,args.last):print(row[1],row[2],row[3],'alert='+row[4],row[5])
        db.close();return
    if args.db.exists():raise ValueError('REPLAY_REQUIRES_NEW_ISOLATED_DB')
    _,wallets=load(args.registry);ledger=Ledger(args.db)
    src=sqlite3.connect('file:'+str(args.source_db)+'?mode=ro',uri=True);counts=Counter();missing=[]
    for sig,body in src.execute('SELECT signature,evidence_json FROM frank_transactions WHERE block_time>=? ORDER BY block_time,slot,signature',(args.since,)):
        old=json.loads(body);wallet=old['wallet']
        if wallet not in wallets:continue
        raw=next((root/(sig+'.json.gz') for root in args.raw if (root/(sig+'.json.gz')).exists()),None)
        if raw is None:missing.append(sig);continue
        tx=json.loads(gzip.decompress(raw.read_bytes()))
        if 'status' in tx and 'signature' in tx:
            if tx['signature']!=sig:raise ValueError('RAW_SIGNATURE_BINDING')
            tx=tx['transaction']
        if tx is None:missing.append(sig);continue
        e=classify(sig,tx,wallet);counts[e['classification']]+=1
        ledger.put(wallets[wallet],e,hashlib.sha256(json.dumps(tx,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest(),str(raw),dry_run=True)
    from .policy import load_policy
    from .engine import Engine
    engine=Engine(ledger,load_policy(args.policy),dry_run=True);engine.drain()
    print(json.dumps({'mode':'DRY_RUN_AUDIT','classifications':dict(counts),'raw_missing':missing,'model':engine.summary(),'notifications_sent':0,'gmail_sent':0},indent=2));ledger.db.close();src.close()
if __name__=='__main__':main()
