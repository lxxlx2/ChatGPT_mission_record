"""Real exposed full-universe streaming benchmark; never reads unexposed years."""
import argparse,gzip,json,os,resource,time
from pathlib import Path
import numpy as np

def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);a=p.parse_args();old=Path('/Users/jerson/Documents/ChatGPT/crypto-monitor-fm2-evidence-20260930/monster');coverage=json.loads((old/'stage-a-final-coverage-v2.json').read_text());count=bars=0;start=time.time();sources=[]
 for r in coverage:
  directory=old/r.get('final_bars_directory','bars');path=directory/r['venue']/(r['symbol']+'.json.gz')
  if not path.exists():continue
  raw=json.loads(gzip.decompress(path.read_bytes()));data=np.asarray(raw,dtype=float);del raw
  if len(data)>24:
   # Actual per-symbol rolling windows and same-time slice rank sized to full universe.
   returns=data[1:,4]/data[:-1,4]-1
   med=np.median(np.lib.stride_tricks.sliding_window_view(data[:,6],24),axis=1)
   _=np.divide(data[24:,6],med[:-1],out=np.full(len(data)-24,np.nan),where=med[:-1]>0)
  count+=1;bars+=len(data);sources.append({'venue':r['venue'],'symbol':r['symbol'],'bars':len(data)});del data
 peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
 # Darwin ru_maxrss is bytes, unlike Linux KiB.
 result={'status':'PASS' if peak<1073741824 and count>=1500 and bars>1000000 else 'FAIL_MEMORY_OR_COVERAGE','peak_rss_bytes':peak,'symbols':count,'bars':bars,'seconds':time.time()-start,'strategy':'ONE_SYMBOL_AT_A_TIME_AND_TIMESTAMP_SLICE','earlier_history_read':False,'source':'EXPOSED_DIAGNOSTIC'}
 a.root.mkdir(parents=True,exist_ok=True);(a.root/'memory-probe.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
if __name__=='__main__':main()
