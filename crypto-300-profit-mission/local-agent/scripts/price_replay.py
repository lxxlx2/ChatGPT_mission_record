"""Explicit immutable-cache replay. Never accesses source network or Gmail."""
import argparse,json,time,resource
from pathlib import Path
from mission_agent.market.cache import load
from mission_agent.market.bar import Bar,ASSETS
from mission_agent.market.replay import execute
from mission_agent.db.repository import Repository
from mission_agent.market.store import PriceStore
from mission_agent.hashing import canonical
from mission_agent.clock import Clock,stamp

def run(root):
 data={};starts={};coverage={}
 for asset in ASSETS:
  values,meta=load(root/'history'/(asset+'-canonical.json.gz'))
  bars=[]
  for value in values:
   value=dict(value);value.pop('close_time_utc');bars.append(Bar(**value))
  data[asset]=bars;starts[asset]=meta['evaluation_start']
  evaluation=[b for b in bars if b.open_time_utc>=starts[asset]]
  expected=(meta['to']-starts[asset])//60000
  coverage[asset]={'expected':expected,'actual':len(evaluation),'warmup_bars':len(bars)-len(evaluation),'unresolved_gaps':meta['unresolved_gaps'],'duplicates':meta['duplicates'],'gap_repair_calls':meta['gap_repair_calls'],'oldest':bars[0].open_time_utc,'newest':bars[-1].open_time_utc,'span_hours':(bars[-1].close_time_utc-bars[0].open_time_utc)/3600000}
 start=time.monotonic();repo=Repository(root/'replay-final.sqlite');store=PriceStore(repo)
 for a in ASSETS:
  for bar in data[a]:store.put(bar)
 batch=execute(data,starts,store=store)
 incremental=execute(data,starts,incremental=True)
 equivalence={a:all(batch[a][k]==incremental[a][k] for k in ('feature_hash','candidate_identity_hash','candidate_count','rule_hits')) for a in ASSETS}
 assert all(equivalence.values()),'PHASE_3_FAIL_REPLAY_LIVE_DIVERGENCE'
 result={'rule_version':'PRICE_RULE_V1','coverage':coverage,'metrics':batch,'equivalence':equivalence,'duration_seconds':time.monotonic()-start,'peak_rss':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'HYPE_status':'FORWARD_DATA_ACCUMULATING','real_gmail_sends':0}
 repo.db.execute('INSERT INTO price_replay_run VALUES(?,?,?,?) ON CONFLICT(run_id) DO UPDATE SET result_json=excluded.result_json',('phase3-20260930','PRICE_RULE_V1',stamp(Clock().now()),canonical(json.loads(json.dumps(result),parse_float=str)).decode()))
 repo.close();path=root/'replay-summary.json';path.write_text(json.dumps(result));path.chmod(0o600)
 print(json.dumps({'coverage':coverage,'candidates':{a:batch[a]['candidate_count'] for a in ASSETS},'recall':{a:batch[a]['recall'] for a in ASSETS},'rule_status':{a:batch[a]['rule_status'] for a in ASSETS},'equivalence':equivalence}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);a=p.parse_args();run(a.root)
