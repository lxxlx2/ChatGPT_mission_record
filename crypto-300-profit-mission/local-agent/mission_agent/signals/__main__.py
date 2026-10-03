"""Read-only ledger queries and explicitly delivery-disabled shadow replay."""
import argparse,gzip,json,sqlite3,hashlib
from pathlib import Path
from collections import Counter
from ..hashing import digest
from .classifier import classify
from .registry import load
from .store import Ledger

def main():
    p=argparse.ArgumentParser();p.add_argument('--db',type=Path,required=True)
    sub=p.add_subparsers(dest='command',required=True)
    a=sub.add_parser('audit-frank');a.add_argument('--last',type=int,default=50)
    a=sub.add_parser('inspect-tx');a.add_argument('signature')
    a=sub.add_parser('replay');a.add_argument('--source-db',type=Path,required=True);a.add_argument('--raw',type=Path,action='append',required=True);a.add_argument('--registry',type=Path,required=True);a.add_argument('--since',type=int,default=0)
    args=p.parse_args()
    if args.command in ('audit-frank','inspect-tx'):
        db=sqlite3.connect('file:'+str(args.db)+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
        if args.command=='inspect-tx':
            for r in db.execute('SELECT * FROM signatures WHERE signature=?',(args.signature,)):
                value=dict(r);value['body']=json.loads(value['body']);value['delivery_state']=[dict(x) for x in db.execute("SELECT * FROM outbox WHERE signal_id IN (SELECT signal_id FROM signals WHERE json_extract(body,'$.latest_trade_signature')=?)",(args.signature,))];print(json.dumps(value,indent=2))
        else:
            for r in db.execute('SELECT * FROM signatures ORDER BY slot DESC,signature DESC LIMIT ?',(args.last,)):
                e=json.loads(r['body']);print(r['block_time'],r['signature'],e['classification'],'alert='+r['alert_state'],r['alert_reason'])
        db.close();return
    _,wallets=load(args.registry);ledger=Ledger(args.db)
    src=sqlite3.connect('file:'+str(args.source_db)+'?mode=ro',uri=True)
    counts=Counter();missing=[]
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
        e=classify(sig,tx,wallet)
        counts[e['classification']]+=1;ledger.put(wallets[wallet],e,hashlib.sha256(json.dumps(tx,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest(),str(raw),dry_run=True)
    result={'mode':'DRY_RUN_AUDIT','classifications':dict(counts),'raw_missing':missing,'signal_model_status':'BLOCKED_CANONICAL_STAGE_MAPPING_REQUIRED','notifications_sent':0,'gmail_sent':0}
    print(json.dumps(result,indent=2));ledger.db.close();src.close()
if __name__=='__main__':main()
