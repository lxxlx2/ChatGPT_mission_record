#!/usr/bin/env python3
"""Official 5m windows for objective largest events and misses, preserving V1 1h labels."""
import argparse,concurrent.futures,datetime,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from mission_agent.monster.archive import retrieve
from mission_agent.monster.ground_truth import HOUR
ap=argparse.ArgumentParser();ap.add_argument('root');ap.add_argument('--attempt',default='v2');a=ap.parse_args();root=Path(a.root)/'monster';events=json.loads((root/f'ground-truth-events-v1-{a.attempt}.json').read_text());result=json.loads((root/f'd1-result-v1-{a.attempt}.json').read_text());result=result.get('DIAGNOSTIC',result);byid={e['event_id']:e for e in events};selected=sorted(events,key=lambda e:(-e['max7d'],e['event_id']))[:20]
for split in ('TRAIN','VALIDATION','AUDIT'):
 for r in result.get(split,{}).get('largest_misses',[])[:10]:selected.append(byid[r['event_id']])
selected={e['event_id']:e for e in selected};plans=[]
cutoff=datetime.datetime.now(datetime.timezone.utc).replace(hour=0,minute=0,second=0,microsecond=0)
for e in selected.values():
 day=datetime.datetime.fromtimestamp((e['anchor_time']-24*HOUR)/1000,datetime.timezone.utc).replace(hour=0,minute=0,second=0,microsecond=0);end=datetime.datetime.fromtimestamp((e['peak_time']+24*HOUR)/1000,datetime.timezone.utc);keys=[]
 while day<=end and day<cutoff:
  d=day.strftime('%Y-%m-%d');v='spot' if e['venue']=='spot' else 'futures/um';keys.append(f'data/{v}/daily/klines/{e["symbol"]}/5m/{e["symbol"]}-5m-{d}.zip');day+=datetime.timedelta(days=1)
 plans.append({'event_id':e['event_id'],'venue':e['venue'],'symbol':e['symbol'],'keys':keys})
(root/f'stage-b-plan-{a.attempt}.json').open('x').write(json.dumps({'selection':'largest20 objective events plus top10 misses per split; no label changes','interval':'5m','plans':plans},indent=2));keys=sorted({k for p in plans for k in p['keys']})
def get(k):
 try:b,n,h=retrieve(k,root,300000);return {'key':k,'status':'VALID','sha256':h,'bytes':n,'bars':len(b)}
 except Exception as e:return {'key':k,'status':type(e).__name__,'error':str(e)}
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:receipts=list(pool.map(get,keys))
(root/f'stage-b-receipts-{a.attempt}.json').open('x').write(json.dumps({'events':len(plans),'archives':len(receipts),'valid':sum(r['status']=='VALID' for r in receipts),'receipts':receipts,'ground_truth_v1_unchanged':True},indent=2));print('STAGE_B_COMPLETE',len(plans),len(receipts),sum(r['status']=='VALID' for r in receipts),flush=True)
