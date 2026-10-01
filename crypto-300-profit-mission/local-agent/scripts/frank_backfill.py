"""Bounded resumable official RPC history; checkpoint every result, batch summaries100."""
import argparse,gzip,json,os,time,signal
from pathlib import Path
from mission_agent.frank.rpc import SolanaRPC
from mission_agent.frank.parser import normalize,PARSER_VERSION
from mission_agent.frank.store import FrankStore
from mission_agent.frank.archive import publish
from mission_agent.db.repository import Repository
from mission_agent.hashing import canonical

def main():
 p=argparse.ArgumentParser();p.add_argument('--snapshot',type=Path,required=True);p.add_argument('--root',type=Path,required=True);p.add_argument('--seconds',type=int,default=7500);a=p.parse_args()
 rows=[r for path in sorted(a.snapshot.glob('signatures-page-*.json')) for r in json.loads(path.read_text())];rows=list({r['signature']:r for r in rows}.values())
 a.root.mkdir(parents=True,exist_ok=True,mode=0o700);raw=a.root/'raw';raw.mkdir(exist_ok=True,mode=0o700);repo=Repository(a.root/('history-'+PARSER_VERSION+'.sqlite'));store=FrankStore(repo);rpc=SolanaRPC(min_interval=2);log=a.root/'progress.jsonl';seen={};stopping=False
 if log.exists():
  for line in log.read_text().splitlines():
   r=json.loads(line)
   if r.get('status')=='UNAVAILABLE' or (r.get('status')=='PARSED' and r.get('parser_version')==PARSER_VERSION):seen[r['signature']]=r
 def stop(*_):
  nonlocal stopping
  stopping=True
 signal.signal(signal.SIGTERM,stop)
 start=time.monotonic()
 for i,row in enumerate(rows):
  if stopping or time.monotonic()-start>=a.seconds:break
  sig=row['signature']
  if sig in seen:continue
  status='ERROR';error=None
  try:
   old=a.snapshot/'raw500'/(sig+'.json.gz');path=raw/(sig+'.json.gz')
   if old.exists():record=json.loads(gzip.decompress(old.read_bytes()))
   elif path.exists():record=json.loads(gzip.decompress(path.read_bytes()))
   else:
    tx=rpc.transaction(sig);record={'signature':sig,'status':'AVAILABLE' if tx is not None else 'UNAVAILABLE_ON_PUBLIC_RPC','transaction':tx};publish(path,gzip.compress(json.dumps(record,sort_keys=True,separators=(',',':'),allow_nan=False).encode(),mtime=0))
   if record['transaction'] is None:status='UNAVAILABLE'
   else:store.put(normalize(sig,record['transaction']));status='PARSED'
  except Exception as exc:error=str(exc)
  result={'pid':os.getpid(),'parser_version':PARSER_VERSION,'signature':sig,'snapshot_index':i,'status':status,'error':error,'rpc_calls':rpc.calls,'rpc_retries':rpc.retries,'rpc_429_count':rpc.rate_limits,'recorded_at':str(time.time())}
  with log.open('ab') as f:f.write(canonical(result)+b'\n');f.flush();os.fsync(f.fileno())
  log.chmod(0o600)
  if status in ('PARSED','UNAVAILABLE'):seen[sig]=result
  if (i+1)%100==0:print(json.dumps({'checkpoint_index':i,'processed':len(seen),'rpc_calls':rpc.calls,'429':rpc.rate_limits}),flush=True)
 repo.close()
if __name__=='__main__':main()
