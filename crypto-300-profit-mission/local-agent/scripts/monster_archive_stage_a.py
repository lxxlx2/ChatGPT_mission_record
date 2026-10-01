#!/usr/bin/env python3
"""Full historical union, stratified availability probe before Stage A downloading."""
import argparse,concurrent.futures,datetime,hashlib,json,os,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from mission_agent.monster.archive import list_keys,retrieve

def main():
 p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--inventory',required=True);p.add_argument('--workers',type=int,default=12);a=p.parse_args()
 root=Path(a.root)/'monster';root.mkdir(parents=True,exist_ok=True);inv=Path(a.inventory);old=json.loads((inv/'historical-universe-complete.json').read_text());universes={}
 for venue in ('spot','futures'):
  cur=json.loads((inv/f'{venue}_universe.json').read_text())['symbols'];active={s['symbol'] for s in cur if s['status']=='TRADING'}
  syms=set(old[venue]['all_historical_symbols'])|{s['symbol'] for s in cur};universes[venue]=[(s,s in active) for s in sorted(syms) if s.endswith('USDT')]
 identity={'historical_spot':old['spot']['historical_symbols'],'historical_futures':old['futures']['historical_symbols'],'usdt_union_counts':{v:len(s) for v,s in universes.items()},'inventories_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in inv.glob('*universe*.json')}}
 (root/'universe-identity.json').write_text(json.dumps(identity,indent=2))
 def inspect(venue,symbol,active):
  prefix=f'data/{"spot" if venue=="spot" else "futures/um"}/monthly/klines/{symbol}/1h/'
  try:
   keys,pages=list_keys(prefix);target=[k for k in keys if k.endswith('.zip') and '2024-10'<=k.rsplit('-',2)[-2]+'-'+k.rsplit('-',1)[-1][:2]<='2026-09']
   # Explicit filename extraction avoids relying on symbol hyphen count.
   target=[k for k in keys if k.endswith('.zip') and '2024-10'<=k[-11:-4]<='2026-09']
   d=root/'listings'/venue;d.mkdir(parents=True,exist_ok=True)
   for i,b in enumerate(pages):(d/f'{symbol}-{i}.xml').write_bytes(b)
   available=[k[-11:-4] for k in keys if k.endswith('.zip')]
   return {'venue':venue,'symbol':symbol,'current_active':active,'status':'AVAILABLE' if target else 'NO_TARGET_PERIOD_ARCHIVE','target_keys':target,'probe_latest_key':max((k for k in keys if k.endswith('.zip')),default=None),'earliest_archive_month':min(available) if available else None,'latest_archive_month':max(available) if available else None}
  except Exception as e:return {'venue':venue,'symbol':symbol,'current_active':active,'status':type(e).__name__,'error':str(e),'target_keys':[]}
 # Deterministic strata include current and inactive, lexicographic old instruments and latest symbols.
 probe=[]
 prior_listing=root/'archive-coverage-listing.json'
 prior=json.loads(prior_listing.read_text()) if prior_listing.exists() else []
 for v,ss in universes.items():
  current=[x for x in ss if x[1]];inactive=[x for x in ss if not x[1]]
  selections={'current_trading':[x for x in current if x[0] in ('BTCUSDT','ETHUSDT','BNBUSDT')][:3],
              'historical_not_current':inactive[:3],
              'old_symbols':[x for x in prior if x['venue']==v and x.get('earliest_archive_month') and x['earliest_archive_month']<='2020-12'][:3],
              'recently_inactive_archive':[x for x in prior if x['venue']==v and not x['current_active'] and x.get('latest_archive_month') and x['latest_archive_month']>='2026-07'][:3]}
  for stratum,selected in selections.items():
   for item in selected:
    symbol,act=(item['symbol'],item['current_active']) if isinstance(item,dict) else item
    rec=inspect(v,symbol,act);rec['stratum']=stratum
    key=rec.get('probe_latest_key')
    if key:
     try:
      bars,n,h=retrieve(key,root);rec['candle_probe']={'status':'VALID','key':key,'bars':len(bars),'bytes':n,'sha256':h}
     except Exception as e:rec['candle_probe']={'status':type(e).__name__,'error':str(e),'key':key}
    else:rec['candle_probe']={'status':'NO_ARCHIVE'}
    probe.append(rec)
 (root/'archive-stratified-candle-probe-v2.json').write_text(json.dumps({'performed_before_corrected_bulk':True,'prior_attempt_directory_only':True,'results':probe,'availability_rates':{st:{'samples':sum(r['stratum']==st for r in probe),'valid':sum(r['stratum']==st and r['candle_probe']['status']=='VALID' for r in probe)} for st in selections}},indent=2))
 print('PROBE_COMPLETE',len(probe),flush=True)
 results=[];start=time.time()
 with concurrent.futures.ThreadPoolExecutor(max_workers=a.workers) as pool:
  futures={pool.submit(inspect,v,s,active):(v,s) for v,ss in universes.items() for s,active in ss}
  for f in concurrent.futures.as_completed(futures):
   x=f.result();results.append(x)
   if len(results)%100==0:print('LISTED',len(results),'elapsed',round(time.time()-start),flush=True)
 (root/'archive-coverage-listing.json').write_text(json.dumps(results,indent=2))
 def download(rec):
  bars=[];receipts=[]
  for k in rec['target_keys']:
   try:
    b,n,h=retrieve(k,root);bars.extend(b);receipts.append({'key':k,'status':'VALID','sha256':h,'bytes':n,'bars':len(b)})
   except Exception as e:receipts.append({'key':k,'status':type(e).__name__,'error':str(e)})
  # September daily fallback only when its monthly archive is absent.
  if not any(k.endswith('2026-09.zip') for k in rec['target_keys']):
   prefix=f'data/{"spot" if rec["venue"]=="spot" else "futures/um"}/daily/klines/{rec["symbol"]}/1h/'
   try:
    keys,pages=list_keys(prefix)
    for k in keys:
     if k.endswith('.zip') and '2026-09-01'<=k[-14:-4]<='2026-09-30':
      try:
       b,n,h=retrieve(k,root);bars.extend(b);receipts.append({'key':k,'status':'VALID','sha256':h,'bytes':n,'bars':len(b)})
      except Exception as e:receipts.append({'key':k,'status':type(e).__name__,'error':str(e)})
   except Exception as e:receipts.append({'status':'DAILY_LIST_'+type(e).__name__,'error':str(e)})
  unique={};conflicts=[]
  for b in bars:
   if b[0] in unique and unique[b[0]]!=b:conflicts.append(b[0])
   unique[b[0]]=b
  for t in conflicts:unique.pop(t,None)
  bars=sorted(unique.values());d=root/'bars'/rec['venue'];d.mkdir(parents=True,exist_ok=True)
  import gzip
  with gzip.open(d/f'{rec["symbol"]}.json.gz','wt') as f:json.dump(bars,f,separators=(',',':'))
  return {**{k:v for k,v in rec.items() if k!='target_keys'},'bars':len(bars),'first_bar':bars[0][0] if bars else None,'last_bar':bars[-1][0] if bars else None,'conflicting_timestamps':conflicts,'archive_receipts':receipts}
 done=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=a.workers) as pool:
  futures=[pool.submit(download,r) for r in results]
  for f in concurrent.futures.as_completed(futures):
   done.append(f.result())
   if len(done)%25==0:
    (root/'stage-a-progress.json').write_text(json.dumps({'completed':len(done),'total':len(results),'elapsed_seconds':round(time.time()-start),'bars':sum(x['bars'] for x in done)}));print('DOWNLOADED',len(done),'bars',sum(x['bars'] for x in done),'elapsed',round(time.time()-start),flush=True)
 (root/'stage-a-coverage.json').write_text(json.dumps(done,indent=2));print('STAGE_A_COMPLETE',len(done),flush=True)
if __name__=='__main__':main()
