#!/usr/bin/env python3
"""Preserve first attempt evidence; retry failed archives and validate final candle coverage."""
import concurrent.futures,gzip,json,math,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from mission_agent.monster.archive import retrieve
root=Path(sys.argv[1])/'monster';initial=json.loads((root/'stage-a-coverage.json').read_text())
def finalize(rec):
 bars=[];receipts=[];retry=[]
 for r in rec['archive_receipts']:
  if 'key' not in r:receipts.append(r);continue
  try:
   b,n,h=retrieve(r['key'],root);bars.extend(b);new={'key':r['key'],'status':'VALID','sha256':h,'bytes':n,'bars':len(b)}
   if r['status']!='VALID':retry.append({'first_attempt':r,'final_attempt':new})
   receipts.append(new)
  except Exception as e:receipts.append({'key':r['key'],'status':type(e).__name__,'error':str(e)})
 # An archive conflict invalidates the contiguous segment containing it, not just one row.
 unique={};conflicts=[]
 for b in bars:
  if b[0] in unique and unique[b[0]]!=b:conflicts.append(b[0])
  unique[b[0]]=b
 ordered=sorted(unique.values());valid=[];chunk=[]
 for b in ordered:
  if chunk and b[0]-chunk[-1][0]!=3600000:
   if not any(x[0] in conflicts for x in chunk):valid.extend(chunk)
   chunk=[]
  chunk.append(b)
 if chunk and not any(x[0] in conflicts for x in chunk):valid.extend(chunk)
 d=root/'bars-final'/rec['venue'];d.mkdir(parents=True,exist_ok=True)
 with gzip.open(d/f'{rec["symbol"]}.json.gz','wt') as f:json.dump(valid,f,separators=(',',':'),allow_nan=False)
 return {**rec,'bars':len(valid),'first_bar':valid[0][0] if valid else None,'last_bar':valid[-1][0] if valid else None,'conflicting_timestamps':conflicts,'archive_receipts':receipts,'retry_history':retry,'final_bars_directory':'bars-final'}
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:final=list(pool.map(finalize,initial))
(root/'stage-a-final-coverage.json').write_text(json.dumps(final,indent=2));print('FINAL_ARCHIVES',len(final),'bars',sum(r['bars'] for r in final),'retry_recoveries',sum(len(r['retry_history']) for r in final),'failed',sum(x['status']!='VALID' for r in final for x in r['archive_receipts']),flush=True)
