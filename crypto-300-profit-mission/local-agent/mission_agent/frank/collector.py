"""Manual forward skeleton, disabled until real 500 and independent review gates pass."""
import gzip,json,os
from pathlib import Path
from .rpc import SolanaRPC
from .parser import normalize
from .store import FrankStore
from .archive import publish

class FrankCollector:
    def __init__(self,repo,raw_root,acceptance,rpc=None):
        if acceptance.get('processed')!=500 or acceptance.get('manual_reviewed',0)<50 or acceptance.get('independent_explorer_review') is not True or acceptance.get('parser_errors')!=0:
            raise ValueError('FRANK_500_MANUAL_ACCEPTANCE_REQUIRED')
        self.store=FrankStore(repo);self.raw_root=Path(raw_root);self.raw_root.mkdir(parents=True,exist_ok=True,mode=0o700);self.rpc=rpc or SolanaRPC()
    def cycle(self):
        cursor=self.store.cursor();boundary=cursor['signature'] if cursor else None
        if boundary is None:raise ValueError('EXPLICIT_INITIAL_CURSOR_REQUIRED')
        pending=[];before=None;found=False
        for _ in range(10):
            page=self.rpc.signatures(before=before)
            for row in page:
                if row['signature']==boundary:found=True;break
                pending.append(row)
            if found:break
            if not page:break
            if page[-1]['signature']==before:raise ValueError('FRANK_PAGINATION_NONADVANCING')
            before=page[-1]['signature']
        if not found:raise ValueError('FRANK_CURSOR_GAP_UNRESOLVED')
        seen=set();inserted=duplicates=0
        for row in reversed(pending):
            sig=row['signature']
            if sig in seen:duplicates+=1;continue
            seen.add(sig);path=self.raw_root/(sig+'.json.gz')
            if path.exists():tx=json.loads(gzip.decompress(path.read_bytes()))
            else:
                tx=self.rpc.transaction(sig)
                if tx is None:raise ValueError('UNAVAILABLE_ON_PUBLIC_RPC_CURSOR_NOT_ADVANCED')
                # Durable archive before SQLite reference/cursor commit.
                publish(path,gzip.compress(json.dumps(tx,separators=(',',':')).encode(),mtime=0))
            evidence=normalize(sig,tx);result=self.store.put(evidence,advance=True)
            inserted+=result=='INSERTED';duplicates+=result=='DUPLICATE'
        return {'normalized':inserted,'duplicates':duplicates,'cursor_gap':0,'cursor':self.store.cursor()}
