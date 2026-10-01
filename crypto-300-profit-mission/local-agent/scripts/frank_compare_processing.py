"""Immutable v4/final transition and candidate identity comparison."""
import argparse,gzip,json,sqlite3
from pathlib import Path
from collections import Counter
from mission_agent.frank.archive import publish
from mission_agent.hashing import canonical

def main():
 p=argparse.ArgumentParser();p.add_argument('--old',type=Path,required=True);p.add_argument('--final',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 def rows(root):return {p.name:json.loads(gzip.decompress(p.read_bytes())) for p in (root/'normalized500').glob('*.json.gz')}
 old,new=rows(a.old),rows(a.final)
 if set(old)!=set(new) or len(old)!=500:raise ValueError('DATASET_IDENTITY_CHANGED')
 changes=[];transitions=Counter()
 for sig,e in sorted(old.items()):
  n=new[sig]
  for field in ['token_balance_deltas','wallet_is_signer','wallet_is_fee_payer','authority_accounts','raw_transaction_sha256']:
   if e[field]!=n[field]:raise ValueError('CANONICAL_AXIS_CHANGED:'+field)
  if e['mechanical_classification']!=n['mechanical_classification']:
   transitions[(e['mechanical_classification'],n['mechanical_classification'])]+=1;changes.append({'signature':n['signature'],'from':e['mechanical_classification'],'to':n['mechanical_classification'],'final_evidence_sha256':n['evidence_sha256']})
 def candidates(root):
  db=sqlite3.connect(f'file:{root}/frank500.sqlite?mode=ro',uri=True);r={row[0]:json.loads(row[1]) for row in db.execute('SELECT event_id,payload_json FROM candidates')};db.close();return r
 before,after=candidates(a.old),candidates(a.final)
 pairs=lambda r:{(v['signature'],v['token_mint']) for v in r.values()}
 result={'same_500_identity':True,'canonical_axes_unchanged':True,'old_counts':dict(Counter(e['mechanical_classification'] for e in old.values())),'final_counts':dict(Counter(e['mechanical_classification'] for e in new.values())),'transitions':[{'from':x,'to':y,'count':n} for (x,y),n in sorted(transitions.items())],'changed_records':changes,'old_candidates':len(before),'final_candidates':len(after),'candidate_event_ids_removed':sorted(set(before)-set(after)),'candidate_event_ids_added':sorted(set(after)-set(before)),'candidate_signature_mint_removed':[list(x) for x in sorted(pairs(before)-pairs(after))],'candidate_signature_mint_added':[list(x) for x in sorted(pairs(after)-pairs(before))],'candidate_reason_identity_note':'FM2 allowed reasons replace v4 reason names; compare event IDs and signature/mint separately.'}
 publish(a.output,canonical(result));print(json.dumps({k:v for k,v in result.items() if k not in ['changed_records','candidate_event_ids_removed','candidate_event_ids_added','candidate_signature_mint_removed','candidate_signature_mint_added']}))
if __name__=='__main__':main()
