"""Resumable official expanded-history ZIPs; bounded disk and Frank health priority."""
import argparse,concurrent.futures,gzip,hashlib,json,os,time,xml.etree.ElementTree as ET
from pathlib import Path
from mission_agent.monster.archive import list_keys,retrieve,NS

def disk_bytes(paths):
 return sum(p.stat().st_size for root in paths for p in root.rglob('*') if p.is_file())

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);a=ap.parse_args();a.root.mkdir(parents=True,exist_ok=True);old=Path('/Users/jerson/Documents/ChatGPT/crypto-monitor-fm2-evidence-20260930/monster');base=a.root.parent
 probe=json.loads((a.root/'memory-probe.json').read_text());assert probe['status']=='PASS' and probe['peak_rss_bytes']<1073741824 and probe['symbols']>=1500
 freeze=json.loads((base/'monster-v2-freeze.json').read_text());assert freeze['pushed_ancestor_commit']
 universe=json.loads((old/'universe-current-merged-v1-v2.json').read_text());current={v:{x['symbol']:x for x in json.loads((old/(v+'-current-fm2.json')).read_text())['symbols']} for v in ['spot','futures']}
 total_before=disk_bytes([old.parent,base]);audit={'status':'PROJECT_UNEXPOSED_BEFORE_V2','scope':'no prior project Monster V2 search of2021–2024; V1 used2024Q4 warmup candles, explicitly reused with provenance','existing_bytes':total_before,'freeze':freeze['pushed_ancestor_commit']};(a.root/'exposure-audit.json').write_text(json.dumps(audit,indent=2))
 def plan(r):
  v,s=r['venue'],r['symbol'];keys=[];listing=old/'listings'/v
  files=list(listing.glob(s+'-*.xml'))
  for f in files:
   tree=ET.fromstring(f.read_bytes());keys += [x.text for x in tree.findall('s:Contents/s:Key',NS)]
  if not keys:
   try:keys,pages=list_keys(f'data/{"spot" if v=="spot" else "futures/um"}/monthly/klines/{s}/1h/')
   except Exception as e:return {**r,'keys':[],'listing_error':type(e).__name__}
  keys=sorted({k for k in keys if k.endswith('.zip') and '2020-10'<=k[-11:-4]<='2024-12'})
  meta=current[v].get(s,{});return {**r,'keys':keys,'base_asset':meta.get('baseAsset'),'identity_verified':bool(meta.get('baseAsset')),'earliest_archive_month':min((k[-11:-4] for k in keys),default=None)}
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:plans=list(pool.map(plan,universe))
 (a.root/'history-plan.json').write_text(json.dumps(plans));n=sum(len(x['keys']) for x in plans)
 # Median compressed ZIP from already verified same-interval monthly sources, reserve derived/cache500MiB.
 sizes=[p.stat().st_size for p in (old/'archives').rglob('*.zip') if '/monthly/' in str(p)]
 estimate=total_before+n*(sum(sizes)/len(sizes) if sizes else 60000)+500*1024**2
 (a.root/'disk-estimate.json').write_text(json.dumps({'existing_bytes':total_before,'archives':n,'projected_bytes':int(estimate),'soft_budget':5368709120,'strategy':'reuse ZIP originals; sequential symbol gzip, no全matrix; monthly1h only'},indent=2))
 if estimate>5368709120:raise ValueError('DISK_ESTIMATE_EXCEEDS_BUDGET')
 # Real stratified ZIP probes before expansion, deterministic first/last available in each venue.
 samples=[]
 for v in ['spot','futures']:
  available=[p for p in plans if p['venue']==v and p['keys']]
  for p in available[:3]+available[-3:]:
   k=p['keys'][0];bars,num,h=retrieve(k,a.root);samples.append({'venue':v,'symbol':p['symbol'],'key':k,'bars':len(bars),'bytes':num,'sha256':h})
 (a.root/'expanded-probe.json').write_text(json.dumps(samples,indent=2));print('PLAN',n,'PROBE',len(samples),'ESTIMATED_BYTES',int(estimate),flush=True)
 health=base/'frank/shadow/health.json'
 def priority():
  if health.exists():
   h=json.loads(health.read_text());from datetime import datetime,timezone
   last=h.get('last_successful_poll');stale=not last or (datetime.now(timezone.utc)-datetime.fromisoformat(last)).total_seconds()>90
   if stale:time.sleep(10);return priority()
 def download(p):
  target=a.root/'bars'/p['venue']/(p['symbol']+'.json.gz');receipt=a.root/'coverage'/p['venue']/(p['symbol']+'.json');receipt.parent.mkdir(parents=True,exist_ok=True)
  if receipt.exists() and target.exists():return json.loads(receipt.read_text())
  bars=[];receipts=[]
  for k in p['keys']:
   priority()
   try:
    # Existing exposed2024Q4 originals reused immutably; no duplicate raw disk copy.
    oldzip=old/'archives'/k
    source=old if oldzip.exists() else a.root
    b,num,h=retrieve(k,source);bars.extend(b);receipts.append({'key':k,'status':'VALID','sha256':h,'bytes':num,'source_root':str(source)})
   except Exception as e:receipts.append({'key':k,'status':type(e).__name__,'http_status':getattr(e,'code',None)})
  unique={};conflicts=[]
  for row in bars:
   if row[0] in unique and unique[row[0]]!=row:conflicts.append(row[0])
   unique[row[0]]=row
  if conflicts:raise ValueError('CONFLICTING_CANDLES')
  target.parent.mkdir(parents=True,exist_ok=True);raw=gzip.compress(json.dumps([unique[t] for t in sorted(unique)],separators=(',',':')).encode(),mtime=0)
  from mission_agent.frank.archive import publish
  from mission_agent.monster.archive import _publish_same
  _publish_same(target,raw);rec={**p,'bars':len(unique),'bars_path':str(target),'receipts':receipts};publish(receipt,json.dumps(rec,separators=(',',':')).encode());return rec
 results=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
  for r in pool.map(download,plans):
   results.append(r)
   if len(results)%50==0:
    usage=disk_bytes([old.parent,base]);print('DOWNLOADED',len(results),'BYTES',usage,flush=True)
    if usage>5368709120:raise ValueError('ACTUAL_DISK_BUDGET_EXCEEDED')
 (a.root/'expanded-coverage.json').write_text(json.dumps(results));print('HISTORY_COMPLETE',len(results),sum(x['bars']>0 for x in results),flush=True)
if __name__=='__main__':main()
