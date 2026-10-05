"""Additional approved wallets reuse official RPC/parser/store, with separate durable cursors."""
import gzip,json,time
from pathlib import Path
from ..frank.rpc import SolanaRPC
from ..frank.parser import normalize
from ..frank.store import FrankStore
from ..frank.archive import publish
from ..hashing import canonical

class WalletRPC(SolanaRPC):
    def __init__(self,wallet,**kwargs):super().__init__(**kwargs);self.wallet=wallet
    def signatures(self,before=None,until=None,limit=1000):
        options={'commitment':'finalized','limit':limit}
        if before:options['before']=before
        if until:options['until']=until
        rows=self.call('getSignaturesForAddress',[self.wallet,options])
        if not isinstance(rows,list):raise ValueError('INVALID_SIGNATURE_LIST')
        return rows

class WalletCollector:
    def __init__(self,repo,root,wallet,rpc=None):
        self.repo,self.store,self.root,self.wallet=repo,FrankStore(repo),Path(root),wallet;self.rpc=rpc or WalletRPC(wallet)
        for d in ['raw','detections']:(self.root/d).mkdir(parents=True,exist_ok=True,mode=0o700)
    def cycle(self):
        cursor=self.store.cursor()
        if cursor is None:
            row=self.rpc.signatures(limit=1)
            if not row:return {'normalized':0,'cursor_gap':0,'duplicates':0}
            sig=row[0]['signature'];tx=self.rpc.transaction(sig)
            if tx is None:raise ValueError('INITIAL_BOUNDARY_UNAVAILABLE')
            publish(self.root/'raw'/(sig+'.json.gz'),gzip.compress(json.dumps(tx,separators=(',',':')).encode(),mtime=0));self.store.put(normalize(sig,tx,self.wallet),advance=True)
            return {'normalized':0,'cursor_gap':0,'duplicates':0}
        pending=[];before=None;found=False
        for _ in range(10):
            page=self.rpc.signatures(before=before)
            for row in page:
                if row['signature']==cursor['signature']:found=True;break
                pending.append(row)
            if found:break
            if not page or page[-1]['signature']==before:break
            before=page[-1]['signature']
        if not found:raise ValueError('FRANK_CURSOR_GAP_UNRESOLVED')
        done=0;seen=set()
        for row in reversed(pending):
            sig=row['signature']
            if sig in seen:continue
            seen.add(sig);path=self.root/'detections'/(sig+'.json')
            if not path.exists():publish(path,canonical({'signature':sig,'detected_at':str(time.time())}))
            detected=json.loads(path.read_bytes())['detected_at'];raw=self.root/'raw'/(sig+'.json.gz')
            if raw.exists():tx=json.loads(gzip.decompress(raw.read_bytes()))
            else:
                tx=self.rpc.transaction(sig)
                if tx is None:raise ValueError('UNAVAILABLE_CURSOR_NOT_ADVANCED')
                publish(raw,gzip.compress(json.dumps(tx,separators=(',',':')).encode(),mtime=0))
            self.store.put(normalize(sig,tx,self.wallet),advance=True,observation={'detected_at':detected,'normalized_at':str(time.time())});done+=1
        return {'normalized':done,'cursor_gap':0,'duplicates':len(pending)-len(seen)}
