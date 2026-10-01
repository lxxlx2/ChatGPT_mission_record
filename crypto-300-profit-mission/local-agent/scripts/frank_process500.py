"""Parse immutable official raw cache; archive compact evidence outside Git."""
import argparse,gzip,json,hashlib,random
from collections import Counter
from pathlib import Path
from mission_agent.frank.parser import normalize,clusters
from mission_agent.frank.store import FrankStore
from mission_agent.frank.candidate import build
from mission_agent.db.repository import Repository
from mission_agent.fm.queue import ingest
from mission_agent.hashing import canonical,digest
from scripts.frank_probe import store
from mission_agent.frank.archive import publish

def run(root,output=None,fixed_packet=None):
    output=output or root
    output.mkdir(exist_ok=True,parents=True,mode=0o700)
    if not (root/'fetch500-summary.json').exists():raise ValueError('F2_RAW_FETCH_INCOMPLETE')
    repo=Repository(output/'frank500.sqlite');db=FrankStore(repo);errors=[];queue_errors=[];available=unavailable=duplicates=0
    directory=output/'normalized500';directory.mkdir(exist_ok=True,mode=0o700)
    for p in sorted((root/'raw500').glob('*.json.gz')):
        record=json.loads(gzip.decompress(p.read_bytes()))
        if record['status']!='AVAILABLE':unavailable+=1;continue
        available+=1
        try:
            e=normalize(record['signature'],record['transaction']);result=db.put(e);duplicates+=result=='DUPLICATE'
            out=directory/(record['signature']+'.json.gz')
            if not out.exists():
                publish(out,gzip.compress(canonical(e),mtime=0))
        except Exception as exc:errors.append({'signature':record['signature'],'error':str(exc)})
    evidence=db.evidence();group=clusters(evidence);counts=Counter(e['mechanical_classification'] for e in evidence);candidates=Counter();seen=Counter()
    for e in evidence:
        for d in e['token_balance_deltas']:
            if not d['wallet_owned']:continue
            same=[x for x in e['token_balance_deltas'] if x['wallet_owned'] and x['mint']==d['mint']]
            if d is not same[0]:continue
            d={**d,'delta':str(sum(int(x['delta']) for x in same)),'pre_amount':str(sum(int(x['pre_amount']) for x in same)),'post_amount':str(sum(int(x['post_amount']) for x in same))}
            c=next((c for c in group if c['token']==d['mint'] and e['signature'] in c['signatures']),None)
            value=build(e,d,c,seen[d['mint']]);seen[d['mint']]+=e['mechanical_classification']=='ACTIVE_SWAP_LIKE' and bool(int(d['delta']))
            if value:
                try:candidates[ingest(repo,value)]+=1
                except ValueError as exc:queue_errors.append({'signature':e['signature'],'error':str(exc)})
    if fixed_packet is None:
        # Reproducible stratified review packet; not an automatic manual-validation PASS.
        strata={}
        for e in evidence:
            flags=[e['mechanical_classification']]
            if e['inner_instruction_count']>=8:flags.append('COMPLEX_INNER')
            if not any(int(d['delta']) for d in e['token_balance_deltas'] if d['wallet_owned']):flags.append('SOL_ONLY_OR_ZERO_TOKEN')
            for f in flags:strata.setdefault(f,[]).append(e['signature'])
        rng=random.Random(20260930);selected=[]
        for values in strata.values():
            for s in rng.sample(values,min(8,len(values))):
                if s not in selected:selected.append(s)
        largest=sorted(evidence,key=lambda e:max((abs(int(d['delta'])) for d in e['token_balance_deltas'] if d['wallet_owned']),default=0),reverse=True)
        for e in largest[:8]:
            if e['signature'] not in selected:selected.append(e['signature'])
        for s in rng.sample([e['signature'] for e in evidence],len(evidence)):
            if len(selected)>=50:break
            if s not in selected:selected.append(s)
        packet={'selection_seed':20260930,'strata':{k:len(v) for k,v in strata.items()},'sample': [{'signature':s,'classification':next(e['mechanical_classification'] for e in evidence if e['signature']==s),'explorer':'https://solscan.io/tx/'+s,'status':'PENDING_MANUAL_REVIEW'} for s in selected[:50]],'not_manual_validation':True}
    if fixed_packet is not None:
        publish(output/'review50-packet.json',fixed_packet.read_bytes())
    else:
        store(output/'review50-packet.json',packet)
    store(output/'clusters.json',group)
    summary={'requested':500,'available':available,'unavailable_public_rpc':unavailable,'parsed':len(evidence),'parser_errors':errors,'queue_errors':queue_errors,'counts':dict(counts),'unique_wallet_mints':len({d['mint'] for e in evidence for d in e['token_balance_deltas'] if d['wallet_owned']}),'active_token_mints':len({d['mint'] for e in evidence if e['mechanical_classification']=='ACTIVE_SWAP_LIKE' for d in e['token_balance_deltas'] if d['wallet_owned'] and int(d['delta'])}),'cluster_count':len(group),'hft_clusters':sum(c['tx_count']>=3 for c in group),'candidates':dict(candidates),'duplicate_replay_records':duplicates,'evidence_hash':digest(evidence),'manual_validation':'PENDING','first_time':min(e['block_time'] for e in evidence if e['block_time'] is not None),'last_time':max(e['block_time'] for e in evidence if e['block_time'] is not None)}
    store(output/'process500-summary.json',summary);repo.close();print(json.dumps(summary),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--output',type=Path);p.add_argument('--fixed-packet',type=Path);a=p.parse_args();run(a.root,a.output,a.fixed_packet)
