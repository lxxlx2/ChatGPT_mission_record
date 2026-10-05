"""Four pre-exposed V1 misses: frozen V2-001 reference, never validation."""
import gzip,json,resource,time
from pathlib import Path
import numpy as np
from mission_agent.monster.features_v2 import features,HOUR
from mission_agent.monster.screen_v2 import activations,configurations,midrank,PATHS

def main():
 old=Path('/Users/jerson/Documents/ChatGPT/crypto-monitor-fm2-evidence-20260930/monster');root=Path('/Users/jerson/Documents/ChatGPT/crypto-monitor-fm3-evidence-20261001/monster');events=json.loads((old/'ground-truth-events-v1-v2.json').read_text());coverage=json.loads((old/'stage-a-final-coverage-v2.json').read_text());wanted=[('futures','MMTUSDT'),('spot','MMTUSDT'),('futures','AVNTUSDT'),('futures','BTWUSDT')];selected=[max([e for e in events if (e['venue'],e['symbol'])==(v,s)],key=lambda e:e['max7d']) for v,s in wanted];times=sorted({t for e in selected for t in range(e['anchor_time']-24*HOUR,e['peak_time']+HOUR,HOUR)});index={t:i for i,t in enumerate(times)};cube=np.full((len(times),len(coverage),16),np.nan,np.float32);btc={}
 current={v:{r['symbol']:r for r in json.loads((old/(v+'-current-fm2.json')).read_text())['symbols']} for v in ['spot','futures']}
 for v in ['spot','futures']:btc[v]={int(b[0]):b[4] for b in json.loads(gzip.decompress((old/'bars-final'/v/'BTCUSDT.json.gz').read_bytes()))}
 for i,r in enumerate(coverage):
  p=old/r.get('final_bars_directory','bars')/r['venue']/(r['symbol']+'.json.gz')
  if not p.exists():continue
  bars=json.loads(gzip.decompress(p.read_bytes()));selected_rows=[j for j,b in enumerate(bars) if int(b[0])+HOUR in index]
  if not selected_rows:continue
  first=bars[0][0] if bars else None
  # Existing V1 event archive-first identity is verified independently, not inferred from data left edge.
  known=next((e.get('first_available_history_time') for e in selected if e['venue']==r['venue'] and e['symbol']==r['symbol']),None)
  f=features(bars,btc[r['venue']],known)
  for j in selected_rows:cube[index[int(bars[j][0])+HOUR],i]=f[j]
 results=[]
 for e in selected:
  target=next(i for i,r in enumerate(coverage) if (r['venue'],r['symbol'])==(e['venue'],e['symbol']));venueix=[i for i,r in enumerate(coverage) if r['venue']==e['venue']];first=None
  for t in times:
   if not e['anchor_time']-24*HOUR<=t<=e['peak_time']:continue
   f=cube[index[t]];ranks=np.full((len(coverage),5),np.nan)
   for j,col in enumerate([0,1,7,8,9]):ranks[venueix,j]=midrank(f[venueix,col])
   a=activations(f,ranks,configurations()[0])[target]
   if a.any():
    ret=bool(np.fmax(ranks[target,0],ranks[target,1])>=.99);vol=midrank(f[venueix,4]);rel=bool(ranks[target,3]>=.95);volume=bool(vol[venueix.index(target)]>=.95);range_ok=bool(f[target,6]>=2);q=bool(f[target,14]>=50000)
    first={'at':t,'pathways':[PATHS[i] for i in np.flatnonzero(a)],'lead_hours_to2':(e['crossings']['2']-t)/HOUR,'v1_47_AND_predicates':{'return':ret,'volume_OR_relative':volume or rel,'range':range_ok,'quote':q},'v1_failed_conditions':[k for k,v in {'return':ret,'volume_OR_relative':volume or rel,'range':range_ok,'quote':q}.items() if not v]};break
  results.append({'venue':e['venue'],'symbol':e['symbol'],'event_id':e['event_id'],'max7d':e['max7d'],'anchor_time':e['anchor_time'],'peak_time':e['peak_time'],'v2_reference':'V2-001_EXPOSED_ONLY_NOT_SELECTED_WINNER','first_trigger':first,'instrument_miss_v1':True,'entity':'BINANCE_BASE:MMT' if e['symbol']=='MMTUSDT' else None})
 result={'status':'EXPOSED_TRAINING_DIAGNOSTIC_ONLY','cases':results,'MMT_identity_verified':current['spot'].get('MMTUSDT',{}).get('baseAsset')==current['futures'].get('MMTUSDT',{}).get('baseAsset')=='MMT','MMT_instrument_misses':2,'MMT_overlapping_entity_sequence':1,'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss};(root/'v1-misses-v2-exposed-diagnostic.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
if __name__=='__main__':main()
