"""Already exposed cases; fixed V3 parameters, not selection or holdout."""
import gzip,json,resource
from pathlib import Path
import numpy as np
from mission_agent.monster.features_v2 import features,HOUR
from mission_agent.monster.screen_v2 import midrank,entity_id,PATHS
from mission_agent.monster.screen_v3 import supplemental,Confirmations
from scripts.monster_v3_replay import dump,health

def diagnose(root):
 old=Path('/Users/jerson/Documents/ChatGPT/crypto-monitor-fm2-evidence-20260930/monster');v2=Path('/Users/jerson/Documents/ChatGPT/crypto-monitor-fm3-evidence-20261001/monster');results=json.loads((root/'train-grid-results.json').read_text());w=json.loads((root/'train-winner.json').read_text())['winner'] or min(results,key=lambda r:(r['median_entities_day'],r['p95_entities_day'],r['config_id']))
 prior=json.loads((v2/'v1-misses-v2-exposed-diagnostic.json').read_text());cases=prior['cases'];events=json.loads((old/'ground-truth-events-v1-v2.json').read_text());coverage=json.loads((old/'stage-a-final-coverage-v2.json').read_text());selected=[next(e for e in events if e['event_id']==r['event_id']) for r in cases];times=sorted({t for e in selected for t in range(e['anchor_time']-24*HOUR,e['peak_time']+HOUR,HOUR)});index={t:i for i,t in enumerate(times)};n=len(coverage);cube=np.full((len(times),n,16),np.nan,np.float32);aux=np.full((len(times),n,4),np.nan,np.float32);btc={};current={v:{r['symbol']:r for r in json.loads((old/(v+'-current-fm2.json')).read_text())['symbols']} for v in ['spot','futures']}
 for v in current:btc[v]={b[0]:b[4] for b in json.loads(gzip.decompress((old/'bars-final'/v/'BTCUSDT.json.gz').read_bytes()))}
 entities=[];venues=[r['venue'] for r in coverage]
 for i,r in enumerate(coverage):
  metadata=current[r['venue']].get(r['symbol'],{});entities.append(entity_id(r['venue'],r['symbol'],metadata.get('baseAsset'),bool(metadata.get('baseAsset')),bool(r.get('instrument_alias_ambiguity'))))
  path=old/r.get('final_bars_directory','bars')/r['venue']/(r['symbol']+'.json.gz')
  if not path.exists():continue
  bars=json.loads(gzip.decompress(path.read_bytes()));ix=[j for j,b in enumerate(bars) if b[0]+HOUR in index]
  if not ix:continue
  known=next((e.get('first_available_history_time') for e in selected if e['venue']==r['venue'] and e['symbol']==r['symbol']),None);f=features(bars,btc[r['venue']],known);a=supplemental(bars)
  for j in ix:cube[index[bars[j][0]+HOUR],i]=f[j];aux[index[bars[j][0]+HOUR],i]=a[j]
  if i%100==0:health()
 emap={e:i for i,e in enumerate(sorted(set(entities)))};mapping=np.array([emap[e] for e in entities]);state=Confirmations(n,configs=[tuple(w['parameters'])]);last=None;first={};venueix={v:np.array([i for i,x in enumerate(venues) if x==v]) for v in set(venues)}
 for t in times:
  if last is not None and t-last!=HOUR:state=Confirmations(n,configs=[tuple(w['parameters'])])
  last=t;f=cube[index[t]];ranks=np.full((n,5),np.nan)
  for ix in venueix.values():
   for k,col in enumerate([0,1,7,8,9]):ranks[ix,k]=midrank(f[ix,col])
  q,d=state.step(f,ranks,aux[index[t]],mapping,venues)
  for e in selected:
   if e['event_id'] in first or not e['anchor_time']-24*HOUR<=t<=e['peak_time']:continue
   i=next(i for i,r in enumerate(coverage) if (r['venue'],r['symbol'])==(e['venue'],e['symbol']))
   if q[0,i]:first[e['event_id']]={'at':t,'pathways':[PATHS[k] for k in np.flatnonzero(d['paths'][i])],'lead_hours_to2':(e['crossings']['2']-t)/HOUR}
 out={'status':'EXPOSED_DIAGNOSTIC_NOT_VALIDATION','v3_config':w['config_id'],'window_method':'First confirmed bar in same exposed anchor-24h-to-peak windows as V2 reference; window-local state, not full-history activation proof','cases':[{'venue':r['venue'],'symbol':r['symbol'],'v2_reference':r['first_trigger'],'v3_first_confirmed':first.get(r['event_id'])} for r in cases],'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss};dump(root/'exposed-diagnostics.json',out);return out
if __name__=='__main__':
 import sys
 print(json.dumps(diagnose(Path(sys.argv[1]))))
