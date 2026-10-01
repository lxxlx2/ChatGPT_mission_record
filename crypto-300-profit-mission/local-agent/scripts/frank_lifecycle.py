"""Available-history lifecycle observations; no wallet-wide lifetime-entry claim."""
import argparse,json,sqlite3
from pathlib import Path
from collections import Counter,defaultdict
from mission_agent.frank.archive import publish
from mission_agent.hashing import canonical

def main():
 p=argparse.ArgumentParser();p.add_argument('--db',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();db=sqlite3.connect(f'file:{a.db}?mode=ro',uri=True)
 rows=[json.loads(r[0]) for r in db.execute('SELECT evidence_json FROM frank_transactions ORDER BY block_time,slot,signature')];db.close();events=defaultdict(list);held={};zero=set();counts=Counter()
 for e in rows:
  if e['mechanical_classification']!='ACTIVE_SWAP_LIKE':continue
  mints={d['mint'] for d in e['token_balance_deltas'] if d['wallet_owned'] and int(d['delta'])}
  for mint in sorted(mints):
   deltas=[d for d in e['token_balance_deltas'] if d['wallet_owned'] and d['mint']==mint];change=sum(int(d['delta']) for d in deltas);post=sum(int(d['post_amount']) for d in deltas)
   if not change:continue
   labels=[]
   if not events[mint]:labels.append('FIRST_OBSERVED_IN_AVAILABLE_HISTORY')
   if change>0:
    labels.append('ACTIVE_ADD_LIKE_MECHANICAL')
    if mint in zero:labels.append('OBSERVED_RE_ENTRY');zero.remove(mint)
    held.setdefault(mint,e['block_time'])
   else:
    labels.append('ACTIVE_REDUCE_LIKE_MECHANICAL')
    if post==0:labels.append('OBSERVED_ZERO_EXIT');zero.add(mint)
   interval=None
   if change<0 and post==0 and mint in held:
    interval=e['block_time']-held.pop(mint);labels.append('OBSERVED_ROUND_TRIP')
   for label in labels:counts[label]+=1
   events[mint].append({'signature':e['signature'],'block_time':e['block_time'],'labels':labels,'net_raw':str(change),'observed_account_post_raw':str(post),'observed_holding_interval_seconds':interval,'evidence_sha256':e['evidence_sha256']})
 result={'parsed_transactions':len(rows),'snapshot_target':18203,'active_mints':len(events),'counts':dict(counts),'lifetime_entry_proven':False,'wallet_wide_full_exit_proven':False,'scope':'AVAILABLE_HISTORY_REFERENCED_TOKEN_ACCOUNTS','limitations':['Incomplete historical fetch and transactions omitting other wallet token accounts prevent lifetime and wallet-wide holding assertions.','Re-entry and round-trip describe observed active accounts only; no realized PnL.'],'mints':dict(events)};publish(a.output,canonical(result));print(json.dumps({k:v for k,v in result.items() if k!='mints'}))
if __name__=='__main__':main()
