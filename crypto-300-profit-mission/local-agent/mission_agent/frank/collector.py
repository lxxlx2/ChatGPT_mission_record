"""Official RPC forward evidence, candidates and cursor after bound manual gates."""
import gzip,json,time
from .candidate import build
from pathlib import Path
from .rpc import SolanaRPC
from .parser import normalize,clusters
from .store import FrankStore
from .archive import publish

def verify_acceptance(acceptance):
    from scripts.frank_manual_gate import verify
    if not isinstance(acceptance,dict) or set(acceptance)!={'manual','raw','processed'}:raise ValueError('FRANK_500_MANUAL_ACCEPTANCE_REQUIRED')
    result=verify(*(Path(acceptance[k]) for k in ('manual','raw','processed')))
    if result['FRANK_500_VALIDATED'] is not True:raise ValueError('FRANK_500_MANUAL_ACCEPTANCE_REQUIRED')

class FrankCollector:
    def __init__(self,repo,raw_root,acceptance,rpc=None,*,durable_detection=False):
        verify_acceptance(acceptance)
        self.repo=repo
        self.durable_detection=durable_detection
        self.store=FrankStore(repo);self.raw_root=Path(raw_root);self.raw_root.mkdir(parents=True,exist_ok=True,mode=0o700);self.rpc=rpc or SolanaRPC()
        self.detection_root=self.raw_root.parent/'detections'
        if durable_detection:self.detection_root.mkdir(parents=True,exist_ok=True,mode=0o700)
    def cycle(self):
        cursor=self.store.cursor();boundary=cursor['signature'] if cursor else None
        if boundary is None:raise ValueError('EXPLICIT_INITIAL_CURSOR_REQUIRED')
        pending=[];before=None;found=False;detection_times={}
        for _ in range(10):
            page=self.rpc.signatures(before=before)
            for row in page:
                if row['signature']==boundary:found=True;break
                pending.append(row);detection_times.setdefault(row['signature'],str(time.time()))
            if found:break
            if not page:break
            if page[-1]['signature']==before:raise ValueError('FRANK_PAGINATION_NONADVANCING')
            before=page[-1]['signature']
        if not found:raise ValueError('FRANK_CURSOR_GAP_UNRESOLVED')
        seen=set();inserted=duplicates=candidate_count=0;latencies=[]
        for row in reversed(pending):
            sig=row['signature']
            if sig in seen:duplicates+=1;continue
            seen.add(sig);path=self.raw_root/(sig+'.json.gz')
            if self.durable_detection:
                detected=self.detection_root/(sig+'.json')
                if not detected.exists():
                    from ..hashing import canonical
                    publish(detected,canonical({'signature':sig,'detected_at':detection_times[sig]}))
                receipt=json.loads(detected.read_bytes())
                if receipt['signature']!=sig:raise ValueError('DETECTION_IDENTITY_CONFLICT')
                detection_times[sig]=receipt['detected_at']
            if path.exists():tx=json.loads(gzip.decompress(path.read_bytes()))
            else:
                tx=self.rpc.transaction(sig)
                if tx is None:raise ValueError('UNAVAILABLE_ON_PUBLIC_RPC_CURSOR_NOT_ADVANCED')
                # Durable archive before SQLite reference/cursor commit.
                publish(path,gzip.compress(json.dumps(tx,separators=(',',':')).encode(),mtime=0))
            evidence=normalize(sig,tx);normalized_at=str(time.time())
            history=self.store.evidence();candidates=[];active_clusters=clusters(history+[evidence])
            owned={}
            for d in evidence['token_balance_deltas']:
                if not d['wallet_owned']:continue
                owned.setdefault(d['mint'],[]).append(d)
            for mint,rows in owned.items():
                d={**rows[0],'delta':str(sum(int(x['delta']) for x in rows)),'pre_amount':str(sum(int(x['pre_amount']) for x in rows)),'post_amount':str(sum(int(x['post_amount']) for x in rows))}
                recent=sum(e['mechanical_classification']=='ACTIVE_SWAP_LIKE' and any(x['wallet_owned'] and x['mint']==mint and int(x['delta']) for x in e['token_balance_deltas']) for e in history)
                cluster=next((x for x in active_clusters if x['token']==mint and sig in x['signatures']),None)
                c=build(evidence,d,cluster=cluster,recent_count=recent)
                if c:candidates.append(c)
            observation={'detected_at':detection_times[sig],'normalized_at':normalized_at}
            result=self.store.put(evidence,advance=True,candidates=candidates,observation=observation)
            if result=='INSERTED':candidate_count+=len(candidates)
            latencies.append({'signature':sig,'block_time':evidence['block_time'],**observation,'classification':evidence['mechanical_classification']})
            inserted+=result=='INSERTED';duplicates+=result=='DUPLICATE'
        return {'candidates':candidate_count,'latencies':latencies,'normalized':inserted,'duplicates':duplicates,'cursor_gap':0,'cursor':self.store.cursor()}
