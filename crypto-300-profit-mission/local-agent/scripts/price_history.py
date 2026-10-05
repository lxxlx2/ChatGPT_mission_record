"""Explicit official historical acquisition; immutable cache outside Git."""
import argparse,time,json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from mission_agent.market.sources.official import Official,parse_rest
from mission_agent.market.bar import ASSETS,MINUTE
from mission_agent.market.cache import save
from mission_agent.clock import Clock,stamp

def main(root):
 root.mkdir(parents=True,exist_ok=True,mode=0o700)
 api=Official();end=api.get('https://data-api.binance.vision/api/v3/time')['serverTime']//MINUTE*MINUTE
 evaluation=end-30*1440*MINUTE;start=evaluation-1446*MINUTE
 def download(asset):
  source=Official();rows=source.history(asset,start if asset!='HYPE' else 0,end)
  now=int(time.time()*1000);bars=[parse_rest(asset,row,now) for row in rows];bars=[b for b in bars if b.is_closed and b.open_time_utc<end]
  unique={b.open_time_utc:b for b in bars};duplicates=len(bars)-len(unique)
  effective=start if asset!='HYPE' else min(unique)
  missing=[t for t in range(effective,end,MINUTE) if t not in unique]
  repair_calls=0
  for t in missing:
   fixed=source.history(asset,t,t+MINUTE);repair_calls+=1
   for row in fixed:
    b=parse_rest(asset,row,now)
    if b.open_time_utc==t and b.is_closed:unique[t]=b
  ordered=[unique[t].value() for t in sorted(unique)]
  metadata={'source':'hyperliquid_perp' if asset=='HYPE' else 'binance_spot','symbol':asset if asset=='HYPE' else asset+'USDT','from':effective,'to':end,'evaluation_start':evaluation if asset!='HYPE' else effective,'retrieved_at':stamp(Clock().now()),'raw_rows':len(rows),'duplicates':duplicates,'missing_before_repair':len(missing),'gap_repair_calls':repair_calls,'unresolved_gaps':sum(t not in unique for t in range(effective,end,MINUTE)),'requests':source.calls,'rx_body_bytes':source.rx,'tx_body_bytes':source.tx}
  save(root/(asset+'-raw.json.gz'),rows,{**metadata,'cache_kind':'RAW_OFFICIAL'})
  manifest=save(root/(asset+'-canonical.json.gz'),ordered,{**metadata,'cache_kind':'CANONICAL_1M'})
  return {asset:manifest}
 result={}
 with ThreadPoolExecutor(max_workers=4) as pool:
  for row in pool.map(download,ASSETS):result.update(row)
 (root/'history-summary.json').write_text(json.dumps(result));(root/'history-summary.json').chmod(0o600)
 print(json.dumps({k:{'rows':v['row_count'],'unresolved_gaps':v['unresolved_gaps'],'requests':v['requests']} for k,v in result.items()}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);a=p.parse_args();main(a.root)
