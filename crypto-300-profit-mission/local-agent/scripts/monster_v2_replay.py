"""Chunked V2 replay: one symbol preprocessing, one weekly universe slice evaluation."""
import argparse,gzip,json,resource,sqlite3,time,types
from pathlib import Path
import numpy as np
from mission_agent.monster.features_v2 import features,HOUR
from mission_agent.monster.screen_v2 import configurations,midrank,activations,entity_id
from mission_agent.monster import ground_truth as gt
DAY=24*HOUR;WEEK=168*HOUR
START=1609459200000;TRAIN_END=1704067200000;END=1735689600000

def dump(p,value):
 with Path(p).open('x') as f:json.dump(value,f,allow_nan=False)

def load_bars(r):return json.loads(gzip.decompress(Path(r['bars_path']).read_bytes()))

def prepare(root):
 coverage=json.loads((root/'expanded-coverage.json').read_text());items=[r for r in coverage if r['bars']];db=sqlite3.connect(root/'features.sqlite');db.execute('CREATE TABLE IF NOT EXISTS feature(venue TEXT,week INTEGER,symbol INTEGER,body BLOB,PRIMARY KEY(venue,week,symbol))');db.execute('CREATE TABLE IF NOT EXISTS complete(symbol INTEGER PRIMARY KEY)');meta=[]
 btc={}
 for v in ['spot','futures']:
  r=next((r for r in items if r['venue']==v and r['symbol']=='BTCUSDT'),None);btc[v]={int(b[0]):b[4] for b in load_bars(r)} if r else {}
 for i,r in enumerate(items):
  r['index']=i;r['monster_entity_id']=entity_id(r['venue'],r['symbol'],r.get('base_asset'),r.get('identity_verified',False),bool(r.get('instrument_alias_ambiguity')));meta.append(r)
  if db.execute('SELECT 1 FROM complete WHERE symbol=?',(i,)).fetchone():continue
  bars=load_bars(r);first=bars[0][0] if bars else None
  import datetime
  month=datetime.datetime.fromtimestamp(first/1000,datetime.timezone.utc).strftime('%Y-%m') if first is not None else None
  # Full saved official catalog predates target-range filtering; never treat a truncated dataset edge as listing.
  import xml.etree.ElementTree as ET
  from mission_agent.monster.archive import NS
  listing=Path('/Users/jerson/Documents/ChatGPT/crypto-monitor-fm2-evidence-20260930/monster/listings')/r['venue'];catalog=[]
  for path in listing.glob(r['symbol']+'-*.xml'):
   catalog += [node.text[-11:-4] for node in ET.fromstring(path.read_bytes()).findall('s:Contents/s:Key',NS) if node.text.endswith('.zip')]
  true_first=min(catalog) if catalog else r.get('earliest_archive_month')
  r['earliest_verified_catalog_month']=true_first;r['verified_first_available_time']=first if true_first==month else None
  verified=first if true_first==month else None
  data=features(bars,btc[r['venue']],verified)
  times=np.asarray([b[0]+HOUR for b in bars],np.int64);valid=(times>=START)&(times<END);weeks=(times-START)//WEEK
  for w in np.unique(weeks[valid]):
   chunk=np.full((168,16),np.nan,np.float32);sel=valid&(weeks==w);ix=((times[sel]-START-int(w)*WEEK)//HOUR).astype(int);chunk[ix]=data[sel];db.execute('INSERT OR REPLACE INTO feature VALUES(?,?,?,?)',(r['venue'],int(w),i,gzip.compress(chunk.tobytes(),mtime=0)))
  db.execute('INSERT INTO complete VALUES(?)',(i,));db.commit()
  if i%50==0:print('PREPARED',i,len(items),flush=True)
  del bars,data
 dump(root/'feature-manifest.json',meta);db.close()

def discover(root,stage):
 meta=json.loads((root/'feature-manifest.json').read_text());module=types.ModuleType('gt_v2_frozen');exec(Path(gt.__file__).read_text(),module.__dict__);lo,hi=(START,TRAIN_END) if stage=='train' else (TRAIN_END,END);module.START=lo;module.END=hi;module.SPLITS={stage.upper():(lo,hi)};events=[]
 for r in meta:
  bars=load_bars(r);es,_=module.discover(bars,r['venue'],r['symbol'],r.get('earliest_archive_month'),r.get('current_active',False))
  for e in es:
   if not e['split_future_complete']:continue
   e['instrument_index']=r['index'];e['monster_entity_id']=r['monster_entity_id']
   verified=r.get('verified_first_available_time');e['first_available_history_time']=verified;e['new_listing']=(e['anchor_time']-HOUR-verified<168*HOUR) if verified is not None else None;e['age_status']='VERIFIED_FIRST_ARCHIVE_HISTORY' if verified is not None else 'AGE_LOWER_BOUND_OR_UNKNOWN';events.append(e)
 dump(root/(stage+'-instrument-events.json'),events);return events

def entity_events(events):
 merged=[]
 for entity in sorted({e['monster_entity_id'] for e in events}):
  rows=sorted([e for e in events if e['monster_entity_id']==entity],key=lambda e:e['anchor_time']);group=[];end=-1
  for e in rows:
   if group and e['anchor_time']>end:
    merged.append(group);group=[]
   group.append(e);end=max(end,e['peak_time'])
  if group:merged.append(group)
 return [{'entity_event_id':g[0]['monster_entity_id']+':'+str(min(e['anchor_time'] for e in g)),'monster_entity_id':g[0]['monster_entity_id'],'anchor_time':min(e['anchor_time'] for e in g),'peak_time':max(e['peak_time'] for e in g),'max7d':max(e['max7d'] for e in g),'crossings':{str(t):min((e['crossings'][str(t)] for e in g if e['crossings'][str(t)] is not None),default=None) for t in [2,5,10,20]},'instrument_indices':sorted({e['instrument_index'] for e in g}),'instrument_event_ids':[e['event_id'] for e in g]} for g in merged]

def metrics(events,first):
 out={}
 for threshold in [5,10,20]:
  indices=[i for i,e in enumerate(events) if e['max7d']>=threshold];hit=[i for i in indices if first[i]>=0 and first[i]<=events[i]['crossings']['2']];before=[i for i in indices if first[i]>=0 and first[i]<events[i]['crossings']['2']];leads={}
  for label in ['2','5','10','20','peak']:
   v=[((events[i]['peak_time'] if label=='peak' else events[i]['crossings'][label])-first[i])/HOUR for i in indices if first[i]>=0 and (label=='peak' or events[i]['crossings'][label] is not None)];leads[label]=float(np.median(v)) if v else None
  out[str(threshold)]={'events':len(indices),'prehit':len(hit),'recall':len(hit)/len(indices) if indices else None,'strict_before2':len(before)/len(indices) if indices else None,'lead_hours':leads}
 return out

def replay(root,stage,winner=None):
 meta=json.loads((root/'feature-manifest.json').read_text());events=discover(root,stage);entities=entity_events(events);dump(root/(stage+'-entity-events.json'),entities);configs=configurations() if winner is None else [tuple(winner['parameters'])];nc=len(configs);n=len(meta);emap={e:i for i,e in enumerate(sorted({r['monster_entity_id'] for r in meta}))};sym_to_entity=np.array([emap[r['monster_entity_id']] for r in meta]);ne=len(emap);active=np.zeros((nc,n,5),bool);fail=np.zeros((nc,n,5),np.int8);first=np.full((nc,len(events)),-1,np.int64);efirst=np.full((nc,len(entities)),-1,np.int64);db=sqlite3.connect(root/'features.sqlite');lo,hi=(START,TRAIN_END) if stage=='train' else (TRAIN_END,END);daily=[];idaily=[];ever=np.zeros((nc,ne),bool);iever=np.zeros((nc,n),bool);day=None;last_eligible=np.zeros(n,bool);cfgarray=np.array(configs);start=time.time();ea=np.array([e['anchor_time']-DAY for e in events]);ep=np.array([e['peak_time'] for e in events]);eea=np.array([e['anchor_time']-DAY for e in entities]);eep=np.array([e['peak_time'] for e in entities])
 for week in range((lo-START)//WEEK,(hi-START+WEEK-1)//WEEK):
  cube=np.full((168,n,16),np.nan,np.float32)
  for row in db.execute('SELECT symbol,body FROM feature WHERE week=?',(week,)):cube[:,row[0]]=np.frombuffer(gzip.decompress(row[1]),np.float32).reshape(168,16)
  for h in range(168):
   t=START+week*WEEK+h*HOUR
   if not lo<=t<hi:continue
   if h%24==0:
    health=root.parent/'frank/shadow/health.json'
    if health.exists():
     from datetime import datetime,timezone
     while True:
      health_data=json.loads(health.read_text());last=health_data.get('last_successful_poll')
      if last and (datetime.now(timezone.utc)-datetime.fromisoformat(last)).total_seconds()<90:break
      time.sleep(10)
   thisday=t//DAY
   if day is not None and thisday!=day:daily.append(ever.sum(axis=1).tolist());idaily.append(iever.sum(axis=1).tolist());ever[:]=False;iever[:]=False
   day=thisday;f=cube[h];eligible=np.isfinite(f[:,15]);active[:,~eligible,:]=False;fail[:,~eligible,:]=0;ranks=np.full((n,5),np.nan)
   for venue in ['spot','futures']:
    ix=np.array([r['index'] for r in meta if r['venue']==venue],dtype=int);
    for col,feature in enumerate([0,1,7,8,9]):ranks[ix,col]=midrank(f[ix,feature])
   # Only 3 alternatives per path, shared across243 configurations.
   options=[]
   for path in range(5):
    opts=[]
    for val in sorted(set(cfgarray[:,path])):
     parameters=list(configs[0]);parameters[path]=val;opts.append(activations(f,ranks,parameters)[:,path])
    options.append(np.array(opts))
   signals=np.stack([options[p][np.searchsorted(sorted(set(cfgarray[:,p])),cfgarray[:,p])] for p in range(5)],axis=2);signals[:,~eligible,:]=False;added=signals&~active;trigger=added.any(axis=2);fail=np.where(signals,0,np.minimum(fail+1,3));active|=signals;active[fail>=3]=False
   iever|=trigger
   for i in np.flatnonzero(trigger.any(axis=0)):ever[:,sym_to_entity[i]]|=trigger[:,i]
   for k in np.flatnonzero((ea<=t)&(ep>=t)):
    e=events[k]
    if True:
     mask=(first[:,k]<0)&trigger[:,e['instrument_index']];first[mask,k]=t
   for k in np.flatnonzero((eea<=t)&(eep>=t)):
    e=entities[k]
    if True:
     mask=(efirst[:,k]<0)&trigger[:,e['instrument_indices']].any(axis=1);efirst[mask,k]=t
  del cube
  if week%12==0:print('REPLAY_WEEK',stage,week,'SECONDS',round(time.time()-start),flush=True)
 if day is not None:daily.append(ever.sum(axis=1).tolist());idaily.append(iever.sum(axis=1).tolist())
 days=(hi-lo)//DAY
 # Clock loops include zero bars/day, including any absent/unavailable calendar days.
 dd=np.array(daily).T;ii=np.array(idaily).T;reports=[]
 for c,parameters in enumerate(configs):
  med=float(np.median(dd[c]));p95=float(np.quantile(dd[c],.95,method='higher'));reports.append({'config_id':f'V2-{configurations().index(tuple(parameters))+1:03}','parameters':list(parameters),'instrument':metrics(events,first[c]),'entity':metrics(entities,efirst[c]),'median_entities_day':med,'p95_entities_day':p95,'median_instruments_day':float(np.median(ii[c])),'p95_instruments_day':float(np.quantile(ii[c],.95,method='higher')),'ceiling_pass':med<=100 and p95<=150,'days':days})
 dump(root/(stage+'-grid-results.json'),reports);np.savez_compressed(root/(stage+'-first-triggers.npz'),instrument=first,entity=efirst);db.close();return reports

def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--stage',choices=['prepare','train','validation'],required=True);a=p.parse_args();start=time.time()
 if a.stage=='prepare':prepare(a.root)
 elif a.stage=='train':
  reports=replay(a.root,'train');eligible=[r for r in reports if r['ceiling_pass']]
  def key(r):
   e=r['entity'];return (-(e['10']['recall'] or 0) if e['10']['events']>=10 else 0,-(e['5']['recall'] or 0),-(e['10']['strict_before2'] or 0),-(e['20']['recall'] or 0),r['median_entities_day'],r['p95_entities_day'],r['config_id'])
  winner=min(eligible,key=key) if eligible else None;dump(a.root/'train-winner.json',{'status':'WINNER_SELECTED_TRAIN_ONLY' if winner else 'MONSTER_D1_V2_NEEDS_REDESIGN','winner':winner,'validation_opened':False});print('TRAIN_COMPLETE',winner['config_id'] if winner else 'NONE',flush=True)
 else:
  freeze=json.loads((a.root/'winner-freeze.json').read_text());assert freeze['pushed_commit'];winner=json.loads((a.root/'train-winner.json').read_text())['winner'];assert winner;reports=replay(a.root,'validation',winner);r=reports[0];e=r['entity'];adequate=e['5']['events']>=20;passed=adequate and e['5']['recall']>=.90 and r['ceiling_pass'] and (e['10']['events']<10 or (e['10']['recall']>=.90 and e['10']['strict_before2']>=.70)) and (e['20']['events']<5 or e['20']['recall']>=.90)
  status='D1_HIGH_RECALL_SCREEN_USABLE_FOR_D2' if passed else 'MONSTER_D1_V2_FAIL_VALIDATION' if adequate else 'INSUFFICIENT_DATA';dump(a.root/'validation-result.json',{'status':status,'result':r,'winner_frozen_commit':freeze['pushed_commit'],'10X_validated':passed and e['10']['events']>=10});print(status,flush=True)
 peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss;dump(a.root/(a.stage+'-resources.json'),{'seconds':time.time()-start,'peak_rss_bytes':peak,'memory_gate_pass':peak<1073741824,'single_worker':True})
if __name__=='__main__':main()
