"""Frozen V3 replay, one instrument preparation and one weekly slice at a time."""
import argparse,gzip,hashlib,json,resource,sqlite3,subprocess,time
from pathlib import Path
from datetime import datetime,timezone
import numpy as np
from mission_agent.monster.screen_v3 import configurations,Confirmations,supplemental,daily_stats,winner,validation_status,search
from mission_agent.monster.screen_v2 import midrank,PATHS
from scripts.monster_v2_replay import START,WARMUP,TRAIN_END,END,HOUR,DAY,WEEK,load_bars,metrics,entity_events,dump,discover
MODULE=Path(__file__).resolve().parents[1]
RUNTIME=Path('/Users/jerson/Documents/ChatGPT/crypto-monitor-fm3-evidence-20261001/frank/shadow')

def health():
 h=json.loads((RUNTIME/'health.json').read_text());last=datetime.fromisoformat(h['last_successful_poll']);assert (datetime.now(timezone.utc)-last).total_seconds()<90,'MEME_STALE_ABORT'
 assert h['identifier']=='com.jerson.crypto-monitor-meme-shadow' and h['status']=='RUNNING' and h['gap_count']==h['unresolved_gap_count']==h['candidate_duplicate_count']==0,'MEME_HEALTH_ABORT'
 return {k:h[k] for k in ['pid','poll_count','rpc_429_count','rpc_error_count','timeouts','gap_count','candidate_duplicate_count']}

def verify_freeze(root):
 freeze=json.loads((root/'freeze.json').read_text());sha=freeze['commit']
 for name,expected in freeze['files'].items():
  value=subprocess.check_output(['git','show',sha+':crypto-300-profit-mission/local-agent/'+name],cwd=MODULE)
  assert hashlib.sha256(value).hexdigest()==expected and (MODULE/name).read_bytes()==value,'V3_FREEZE_DRIFT'
 subprocess.run(['git','merge-base','--is-ancestor',sha,'HEAD'],check=True,cwd=MODULE)
 assert len(configurations())==search()['config_count']==72
 return freeze

def prepare(source,root):
 meta=json.loads((source/'feature-manifest.json').read_text());db=sqlite3.connect(root/'supplemental.sqlite');db.execute('CREATE TABLE IF NOT EXISTS feature(week INTEGER,symbol INTEGER,body BLOB,PRIMARY KEY(week,symbol))');baseline=health()
 for i,r in enumerate(meta):
  bars=load_bars(r);data=supplemental(bars);times=np.array([b[0]+HOUR for b in bars],np.int64);weeks=(times-START)//WEEK;valid=(times>=WARMUP)&(times<END)
  for w in np.unique(weeks[valid]):
   chunk=np.full((168,4),np.nan,np.float32);sel=valid&(weeks==w);ix=((times[sel]-START-int(w)*WEEK)//HOUR).astype(int);chunk[ix]=data[sel];db.execute('INSERT INTO feature VALUES(?,?,?)',(int(w),r['index'],gzip.compress(chunk.tobytes(),mtime=0)))
  db.commit();del bars,data
  if i%50==0:
   h=health();assert h['rpc_429_count']==baseline['rpc_429_count'],'MEME_429_INCREASE_ABORT';print('V3_PREPARE',i,len(meta),flush=True)
 db.close();dump(root/'prepare-complete.json',{'instruments':len(meta),'source':str(source),'memory_bounded':True,'final_meme_health':health()})

def locked_winner(root):
 path=MODULE/'config/monster_d1_v3_winner.json';v=json.loads(path.read_text());assert v['status']=='MONSTER_D1_V3_TRAIN_PASS' and v['winner'] and v['winner']['ceiling_pass'],'VALIDATION_LOCK_NO_WINNER'
 committed=subprocess.check_output(['git','show','HEAD:crypto-300-profit-mission/local-agent/config/monster_d1_v3_winner.json'],cwd=MODULE);assert committed==path.read_bytes(),'WINNER_NOT_COMMITTED'
 assert v==json.loads((root/'train-winner.json').read_text()),'WINNER_CONTENT_DRIFT'
 return v['winner']

def replay(source,root,stage,selected=None,audit=False):
 meta=json.loads((source/'feature-manifest.json').read_text());lo,hi=(START,TRAIN_END) if stage=='train' else (TRAIN_END,END)
 if stage=='validation':assert selected and locked_winner(root)['config_id']==selected['config_id']
 # No 2024 outcomes read/computed until committed winner gate passed above.
 if stage=='train':events=json.loads((source/'train-instrument-events.json').read_text())
 else:
  if not (root/'feature-manifest.json').exists():dump(root/'feature-manifest.json',meta)
  events=discover(root,'validation')
 entities=entity_events(events)
 for e in entities:e['candidate_instrument_indices']=[r['index'] for r in meta if r['monster_entity_id']==e['monster_entity_id']]
 allcfg=configurations();cfg=[tuple(selected['parameters'])] if selected else allcfg;nc=len(cfg);n=len(meta);emap={e:i for i,e in enumerate(sorted({r['monster_entity_id'] for r in meta}))};mapping=np.array([emap[r['monster_entity_id']] for r in meta]);venues=[r['venue'] for r in meta];ne=len(emap)
 state=Confirmations(n,configs=cfg);active=np.zeros((nc,n),bool);failed=np.zeros((nc,n),np.int8);first=np.full((nc,len(events)),-1,np.int64);efirst=np.full((nc,len(entities)),-1,np.int64);db=sqlite3.connect(f'file:{source / "features.sqlite"}?mode=ro',uri=True);auxdb=sqlite3.connect(f'file:{root / "supplemental.sqlite"}?mode=ro',uri=True)
 daily=[];idaily=[];dates=[];ever=np.zeros((nc,ne),bool);iever=np.zeros((nc,n),bool);day=None;baseline=health();health_samples=[baseline];attribution={'broad_path_observations':[0]*5,'confirmed_path_observations':[0]*5,'broad_hours':0,'rejected_broad_hours':0,'extreme_range_broad_hours':0,'low_activity_broad_hours':0};records=[];ea=np.array([e['anchor_time']-DAY for e in events]);ep=np.array([e['peak_time'] for e in events]);eea=np.array([e['anchor_time']-DAY for e in entities]);eep=np.array([e['peak_time'] for e in entities]);venueix={v:np.array([i for i,x in enumerate(venues) if x==v]) for v in set(venues)}
 for week in range((WARMUP-START)//WEEK,(hi-START+WEEK-1)//WEEK):
  cube=np.full((168,n,16),np.nan,np.float32);auxcube=np.full((168,n,4),np.nan,np.float32)
  for i,body in db.execute('SELECT symbol,body FROM feature WHERE week=?',(week,)):cube[:,i]=np.frombuffer(gzip.decompress(body),np.float32).reshape(168,16)
  for i,body in auxdb.execute('SELECT symbol,body FROM feature WHERE week=?',(week,)):auxcube[:,i]=np.frombuffer(gzip.decompress(body),np.float32).reshape(168,4)
  for hour in range(168):
   t=START+week*WEEK+hour*HOUR
   if not WARMUP<=t<hi:continue
   if hour%24==0:
    h=health();assert h['rpc_429_count']==baseline['rpc_429_count'],'MEME_429_INCREASE_ABORT';health_samples.append(h)
    assert resource.getrusage(resource.RUSAGE_SELF).ru_maxrss<1073741824,'MEMORY_ABORT'
   today=t//DAY
   if day is not None and day!=today:
    if day>=lo//DAY:daily.append(ever.sum(axis=1));idaily.append(iever.sum(axis=1));dates.append(day)
    ever[:]=False;iever[:]=False
   day=today;f=cube[hour];aux=auxcube[hour];ranks=np.full((n,5),np.nan)
   for ix in venueix.values():
    for k,col in enumerate([0,1,7,8,9]):ranks[ix,k]=midrank(f[ix,col])
   qualified,detail=state.step(f,ranks,aux,mapping,venues);eligible=np.isfinite(f[:,15]);active[:,~eligible]=False;failed[:,~eligible]=0;trigger=qualified&~active;failed=np.where(qualified,0,np.minimum(failed+1,3));active|=qualified;active[failed>=3]=False
   if t>=lo:
    iever|=trigger
    for i in np.flatnonzero(trigger.any(axis=0)):ever[:,mapping[i]]|=trigger[:,i]
    if audit:
     paths=detail['paths'];broad=paths.any(axis=1);attribution['broad_hours']+=int(broad.sum());attribution['rejected_broad_hours']+=int((broad&~qualified[0]).sum());attribution['extreme_range_broad_hours']+=int((broad&(aux[:,0]>=1)).sum());attribution['low_activity_broad_hours']+=int((broad&(f[:,14]<50000)).sum())
     for p in range(5):attribution['broad_path_observations'][p]+=int(paths[:,p].sum());attribution['confirmed_path_observations'][p]+=int((paths[:,p]&qualified[0]).sum())
     for i in np.flatnonzero(trigger[0]):
      ps=[PATHS[p] for p in np.flatnonzero(paths[i])];q,rs=detail['families'][cfg[0][0]];limit=cfg[0][1]*(.5 if detail['young'][i] else 1);quality=bool(q[0][i]>=limit and q[1][i] and f[i,14]>=limit*.5) if isinstance(q,tuple) else False
      records.append({'instrument_index':int(i),'entity':meta[i]['monster_entity_id'],'at':int(t),'primary_path':ps[0],'supporting_paths':ps[1:],'confirmations':{'persistence':'PASS','close_retention':'PASS','overextension':'PASS','quality':'PASS' if quality else 'FAIL','relative_strength':'PASS' if rs[i] else 'FAIL','dual':'PASS' if detail['dual_pass'][i] else 'FAIL' if detail['dual_applicable'][i] else 'UNAVAILABLE_EXEMPT'},'age':'YOUNG' if detail['young'][i] else 'OLD_OR_UNKNOWN','quote':float(f[i,14]),'intrahour_range':float(aux[i,0])})
   for k in np.flatnonzero((ea<=t)&(ep>=t)):
    mask=(first[:,k]<0)&trigger[:,events[k]['instrument_index']];first[mask,k]=t
   for k in np.flatnonzero((eea<=t)&(eep>=t)):
    mask=(efirst[:,k]<0)&trigger[:,entities[k]['candidate_instrument_indices']].any(axis=1);efirst[mask,k]=t
  if week%12==0:print('V3_WEEK',stage,week,flush=True)
 if day is not None and day>=lo//DAY:daily.append(ever.sum(axis=1));idaily.append(iever.sum(axis=1));dates.append(day)
 dd=np.array(daily).T;ii=np.array(idaily).T;reports=[]
 for c,param in enumerate(cfg):
  es=daily_stats(dd[c]);ins=daily_stats(ii[c]);years={}
  for year in ([2021,2022,2023] if stage=='train' else [2024]):
   ylo=int(datetime(year,1,1,tzinfo=timezone.utc).timestamp()*1000);yhi=int(datetime(year+1,1,1,tzinfo=timezone.utc).timestamp()*1000);ix=[k for k,e in enumerate(entities) if ylo<=e['anchor_time']<yhi];dayix=[k for k,d in enumerate(dates) if ylo//DAY<=d<yhi//DAY];ys=daily_stats(dd[c,dayix]);years[str(year)]={'median_entities_day':ys['median'],'p95_entities_day':ys['p95'],'entity':metrics([entities[k] for k in ix],efirst[c,ix])}
  reports.append({'config_id':f'V3-{allcfg.index(tuple(param))+1:03}','parameters':list(param),'entity':metrics(entities,efirst[c]),'instrument':metrics(events,first[c]),'median_entities_day':es['median'],'p95_entities_day':es['p95'],'median_instruments_day':ins['median'],'p95_instruments_day':ins['p95'],'ceiling_pass':es['median']<=100 and es['p95']<=150,'days':len(dates),'years':years})
 tag=stage+('-audit' if audit else '');dump(root/(tag+'-grid-results.json'),reports);np.savez_compressed(root/(tag+'-first-triggers.npz'),entity=efirst,instrument=first,daily_entity=dd,daily_instrument=ii);dump(root/(tag+'-health.json'),health_samples)
 if audit:dump(root/(tag+'-candidates.json'),records);dump(root/(tag+'-attribution.json'),attribution)
 db.close();auxdb.close();return reports

def main():
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--root',type=Path,required=True);p.add_argument('--stage',choices=['prepare','train','validation','audit'],required=True);a=p.parse_args();freeze=verify_freeze(a.root);start=time.time();cpu=resource.getrusage(resource.RUSAGE_SELF)
 if a.stage=='prepare':prepare(a.source,a.root)
 elif a.stage=='train':
  assert (a.root/'prepare-complete.json').exists();rs=replay(a.source,a.root,'train');w=winner(rs);dump(a.root/'train-winner.json',{'status':'MONSTER_D1_V3_TRAIN_PASS' if w else 'MONSTER_D1_V3_NEEDS_REDESIGN','winner':w,'validation_opened':False,'spec_freeze_commit':freeze['commit']});print('TRAIN_WINNER',w['config_id'] if w else 'NONE',flush=True)
 elif a.stage=='audit':
  rs=json.loads((a.root/'train-grid-results.json').read_text());w=winner(rs) or min(rs,key=lambda r:(r['median_entities_day'],r['p95_entities_day'],r['config_id']));replay(a.source,a.root,'train',selected=w,audit=True)
 else:
  w=locked_winner(a.root);r=replay(a.source,a.root,'validation',selected=w,audit=True)[0];dump(a.root/'validation-result.json',{'status':validation_status(r),'result':r,'winner_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'10X_validated':r['entity']['10']['events']>=10 and validation_status(r)=='MONSTER_D1_V3_VALIDATION_PASS'})
 u=resource.getrusage(resource.RUSAGE_SELF);elapsed=time.time()-start;dump(a.root/(a.stage+'-resources.json'),{'seconds':elapsed,'cpu_seconds':u.ru_utime+u.ru_stime-cpu.ru_utime-cpu.ru_stime,'mean_cpu_percent':100*(u.ru_utime+u.ru_stime-cpu.ru_utime-cpu.ru_stime)/elapsed,'peak_rss_bytes':u.ru_maxrss,'memory_gate_pass':u.ru_maxrss<1073741824})
if __name__=='__main__':main()
