#!/usr/bin/env python3
"""USDT-quoted dated and SETTLED historical aliases, retained as separate instruments."""
import concurrent.futures,gzip,json,re,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from mission_agent.monster.archive import list_keys,retrieve
root=Path(sys.argv[1])/'monster';inv=Path(sys.argv[2]);historical=json.loads((inv/'historical-universe-complete.json').read_text())['futures']['all_historical_symbols'];cur=json.loads((inv/'futures_universe.json').read_text())['symbols'];active={s['symbol'] for s in cur if s['status']=='TRADING'}
extra=sorted((set(s for s in historical if re.fullmatch(r'.+USDT(?:_\d{6}|SETTLED)+',s))|{s['symbol'] for s in cur if s['quoteAsset']=='USDT'})-{s for s in historical if s.endswith('USDT')}-{s['symbol'] for s in cur if s['symbol'].endswith('USDT')})
(root/'usdt-contract-supplement-identity.json').write_text(json.dumps({'symbols':extra,'reason':'Official historical USDT dated contracts and SETTLED aliases remain separate; no outcome-based exclusion.'},indent=2))
def inspect(symbol):
 keys,pages=list_keys(f'data/futures/um/monthly/klines/{symbol}/1h/');d=root/'listings'/'futures';d.mkdir(parents=True,exist_ok=True)
 for i,b in enumerate(pages):(d/f'{symbol}-{i}.xml').write_bytes(b)
 months=[k[-11:-4] for k in keys if k.endswith('.zip')];target=[k for k in keys if k.endswith('.zip') and '2024-10'<=k[-11:-4]<='2026-09']
 return {'venue':'futures','symbol':symbol,'current_active':symbol in active,'earliest_archive_month':min(months) if months else None,'latest_archive_month':max(months) if months else None,'status':'AVAILABLE' if target else 'NO_TARGET_PERIOD_ARCHIVE','target_keys':target,'instrument_alias_ambiguity':'DATED_OR_SETTLED_DIRECTORY_NAME'}
probes=[inspect(s) for s in (extra[:3]+extra[-3:])];(root/'archive-contract-stratified-probe.json').write_text(json.dumps({'performed_before_supplement_bulk':True,'results':probes},indent=2));print('SUPPLEMENT_PROBE',len(probes),flush=True)
def download(symbol):
 rec=inspect(symbol);keys=rec.pop('target_keys');bars=[];receipts=[]
 if not any(k.endswith('2026-09.zip') for k in keys):
  daily,_=list_keys(f'data/futures/um/daily/klines/{symbol}/1h/');keys.extend(k for k in daily if k.endswith('.zip') and '2026-09-01'<=k[-14:-4]<='2026-09-29')
 for k in keys:
  try:b,n,h=retrieve(k,root);bars.extend(b);receipts.append({'key':k,'status':'VALID','sha256':h,'bytes':n,'bars':len(b)})
  except Exception as e:receipts.append({'key':k,'status':type(e).__name__,'error':str(e)})
 unique={};conflicts=[]
 for b in bars:
  if b[0] in unique and unique[b[0]]!=b:conflicts.append(b[0])
  unique[b[0]]=b
 for t in conflicts:unique.pop(t,None)
 bars=sorted(unique.values());d=root/'bars'/'futures';d.mkdir(parents=True,exist_ok=True)
 with gzip.open(d/f'{symbol}.json.gz','wt') as f:json.dump(bars,f,separators=(',',':'))
 return {**rec,'bars':len(bars),'first_bar':bars[0][0] if bars else None,'last_bar':bars[-1][0] if bars else None,'conflicting_timestamps':conflicts,'archive_receipts':receipts}
results=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
 for r in pool.map(download,extra):results.append(r);print('SUPPLEMENT',len(results),r['symbol'],r['bars'],flush=True)
(root/'stage-a-contract-supplement-coverage.json').write_text(json.dumps(results,indent=2));print('SUPPLEMENT_COMPLETE',len(results),flush=True)
