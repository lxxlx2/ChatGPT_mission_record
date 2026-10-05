#!/usr/bin/env python3
"""Latest official exchangeInfo additions, before GT discovery; bounded archives only."""
import gzip,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from mission_agent.monster.archive import list_keys,retrieve
root=Path(sys.argv[1])/'monster';refresh=json.loads((root/'current-inventory-refresh.json').read_text());records=[];probes=[]
for venue in ('spot','futures'):
 for symbol in refresh[venue]['new_usdt_symbols_since_fm1']:
  path='spot' if venue=='spot' else 'futures/um';keys,pages=list_keys(f'data/{path}/monthly/klines/{symbol}/1h/');months=[k[-11:-4] for k in keys if k.endswith('.zip')];target=[k for k in keys if k.endswith('.zip') and '2024-10'<=k[-11:-4]<='2026-09'];d=root/'listings'/venue;d.mkdir(parents=True,exist_ok=True)
  for i,b in enumerate(pages):(d/f'{symbol}-{i}.xml').write_bytes(b)
  probes.append({'venue':venue,'symbol':symbol,'target_monthly_archives':len(target),'earliest_archive_month':min(months) if months else None})
  daily,dp=list_keys(f'data/{path}/daily/klines/{symbol}/1h/');target.extend(k for k in daily if k.endswith('.zip') and '2026-09-01'<=k[-14:-4]<='2026-09-29');bars=[];receipts=[]
  for k in target:
   try:b,n,h=retrieve(k,root);bars.extend(b);receipts.append({'key':k,'status':'VALID','sha256':h,'bytes':n,'bars':len(b)})
   except Exception as e:receipts.append({'key':k,'status':type(e).__name__,'error':str(e)})
  bars=sorted({b[0]:b for b in bars}.values());d=root/'bars'/venue;d.mkdir(parents=True,exist_ok=True)
  with gzip.open(d/f'{symbol}.json.gz','wt') as f:json.dump(bars,f,separators=(',',':'))
  records.append({'venue':venue,'symbol':symbol,'current_active':True,'status':'AVAILABLE' if target else 'NO_TARGET_PERIOD_ARCHIVE','earliest_archive_month':min(months) if months else None,'latest_archive_month':max(months) if months else None,'bars':len(bars),'first_bar':bars[0][0] if bars else None,'last_bar':bars[-1][0] if bars else None,'conflicting_timestamps':[],'archive_receipts':receipts,'current_inventory_provenance':refresh[venue]['sha256']});print('CURRENT_ADDITION',symbol,len(bars),flush=True)
(root/'archive-current-supplement-probes.json').write_text(json.dumps(probes,indent=2));(root/'stage-a-current-supplement-coverage.json').write_text(json.dumps(records,indent=2))
