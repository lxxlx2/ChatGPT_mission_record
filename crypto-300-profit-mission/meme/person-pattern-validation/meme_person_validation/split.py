import hashlib,json
from pathlib import Path
def chronological(episodes,fractions=(.6,.2,.2)):
    rows=sorted(episodes,key=lambda e:(e['first_market_buy_time'],e['episode_id']))
    a=int(len(rows)*fractions[0]); b=int(len(rows)*(fractions[0]+fractions[1]))
    # Boundary-straddling episodes are purged rather than leaking later outcomes into TRAIN.
    boundaries=[rows[a]['first_market_buy_time'] if a<len(rows) else float('inf'),rows[b]['first_market_buy_time'] if b<len(rows) else float('inf')]
    result={'TRAIN':[],'VALIDATION':[],'HOLDOUT':[],'PURGED':[]}
    for e in rows:
        start=e['first_market_buy_time']; end=e.get('full_exit_time')
        index=0 if start<boundaries[0] else 1 if start<boundaries[1] else 2
        if index<2 and (end is None or end>=boundaries[index]): result['PURGED'].append(e)
        else: result[['TRAIN','VALIDATION','HOLDOUT'][index]].append(e)
    return result
def freeze(path,config):
    encoded=json.dumps(config,sort_keys=True,separators=(',',':'));digest=hashlib.sha256(encoded.encode()).hexdigest();p=Path(path)
    if p.exists() and json.loads(p.read_text())['sha256']!=digest: raise ValueError('FROZEN_CONFIG_CHANGED_NEW_HOLDOUT_REQUIRED')
    if not p.exists(): p.write_text(json.dumps({'sha256':digest,'config':config},indent=2)+'\n')
    return digest
class ForwardInterface:
    state='NOT_STARTED'
    def ingest_finalized(self,event): raise RuntimeError('OFFLINE_ONLY_FORWARD_NOT_AUTHORIZED')
