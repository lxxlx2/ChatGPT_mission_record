"""Finalized catch-up, independent of notification, Git transport and GPT."""
import gzip,json,time,hashlib
from pathlib import Path
from ..frank.rpc import SolanaRPC
from ..frank.archive import publish
from ..hashing import digest
from .classifier import classify

class WalletRPC(SolanaRPC):
    def __init__(self,wallet,**kwargs):super().__init__(**kwargs);self.wallet=wallet
    def signatures(self,before=None,limit=1000):
        opts={'commitment':'finalized','limit':limit}
        if before:opts['before']=before
        value=self.call('getSignaturesForAddress',[self.wallet,opts])
        if not isinstance(value,list):raise ValueError('INVALID_SIGNATURE_LIST')
        return value

    def finalized_clock(self):
        slot=self.call('getSlot',[{'commitment':'finalized'}]);at=self.call('getBlockTime',[slot])
        if type(slot) is not int or type(at) is not int:raise ValueError('FINALIZED_CLOCK_UNAVAILABLE')
        return {'slot':slot,'block_time':at}

class Scanner:
    def __init__(self,ledger,wallets,raw_root,rpcs=None,*,mode='SHADOW'):
        self.ledger,self.wallets,self.raw_root=ledger,wallets,Path(raw_root)
        self.mode=mode
        ledger.db.execute('CREATE TABLE IF NOT EXISTS signature_detections(wallet TEXT,signature TEXT,person_id TEXT,slot INTEGER,block_time INTEGER,seen_at REAL,state TEXT,PRIMARY KEY(wallet,signature))')
        if 'person_id' not in {r[1] for r in ledger.db.execute('PRAGMA table_info(signature_detections)')}:ledger.db.execute('ALTER TABLE signature_detections ADD COLUMN person_id TEXT')
        self.raw_root.mkdir(parents=True,exist_ok=True,mode=0o700)
        self.rpcs=rpcs or {w:WalletRPC(w) for w in wallets}
    def cycle(self,wallet):
        db=self.ledger.db;rpc=self.rpcs[wallet];cursor=self.ledger.cursor(wallet)
        if not cursor:raise ValueError('EXPLICIT_DURABLE_CHECKPOINT_REQUIRED')
        pending=[];before=None;head=None;seen=set();found=False
        try:
            for _ in range(1000):
                page=rpc.signatures(before=before)
                if head is None and page:head=page[0]
                for row in page:
                    sig=row['signature']
                    if sig==cursor['signature']:found=True;break
                    if sig not in seen:pending.append(row);seen.add(sig)
                if found:break
                if not page or page[-1]['signature']==before:raise ValueError('CURSOR_GAP_UNRESOLVED')
                before=page[-1]['signature']
            if not found:raise ValueError('CURSOR_GAP_UNRESOLVED')
            for row in pending:
                db.execute('INSERT OR IGNORE INTO signature_detections(wallet,signature,person_id,slot,block_time,seen_at,state) VALUES(?,?,?,?,?,?,?)',(wallet,row['signature'],self.wallets[wallet],row['slot'],row.get('blockTime'),time.time(),'RAW_PENDING'))
            for row in reversed(pending):
                sig=row['signature'];path=self.raw_root/(sig+'.json.gz')
                if path.exists():tx=json.loads(gzip.decompress(path.read_bytes()))
                else:
                    tx=rpc.transaction(sig)
                    if tx is None:raise ValueError('RAW_UNAVAILABLE_CURSOR_NOT_ADVANCED')
                    publish(path,gzip.compress(json.dumps(tx,sort_keys=True).encode(),mtime=0))
                if tx.get('slot')!=row['slot']:raise ValueError('CHAIN_SLOT_CONFLICT')
                signed=tx.get('transaction',{}).get('signatures')
                if signed is not None and sig not in signed:raise ValueError('CHAIN_SIGNATURE_CONFLICT')
                self.ledger.put(self.wallets[wallet],classify(sig,tx,wallet),hashlib.sha256(json.dumps(tx,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest(),str(path),advance=True,dry_run=True)
                db.execute("UPDATE signature_detections SET state='CLASSIFIED_DURABLE' WHERE wallet=? AND signature=?",(wallet,sig))
            health={'last_successful_poll':time.time(),'last_chain_signature':head['signature'] if head else None,'last_local_signature':self.ledger.cursor(wallet)['signature'],'lag_seconds':0 if head and head['signature']==self.ledger.cursor(wallet)['signature'] else None,'consecutive_errors':0,'status':'RUNNING' if self.mode=='LIVE' else 'RUNNING_SHADOW_DELIVERY_DISABLED'}
        except Exception as exc:
            old=db.execute('SELECT body FROM health WHERE wallet=?',(wallet,)).fetchone()
            health=json.loads(old[0]) if old else {};health.update(consecutive_errors=health.get('consecutive_errors',0)+1,last_error=type(exc).__name__+':'+str(exc),status='RETRY_PENDING',lag_seconds=None)
            db.execute('INSERT OR REPLACE INTO health VALUES(?,?)',(wallet,json.dumps(health)));raise
        db.execute('INSERT OR REPLACE INTO health VALUES(?,?)',(wallet,json.dumps(health)))
        return {'new_signatures':len(pending),**health}
