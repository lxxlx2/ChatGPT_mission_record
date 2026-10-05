"""Explicitly invoked private shadow; never installs or sends notifications."""
import argparse,json,time,signal,os,gzip
from pathlib import Path
from datetime import datetime,timezone
from mission_agent.db.repository import Repository
from mission_agent.frank.collector import FrankCollector
from mission_agent.frank.parser import normalize
from mission_agent.frank.rpc import SolanaRPC
from mission_agent.hashing import canonical

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--manual',type=Path,required=True);p.add_argument('--raw',type=Path,required=True);p.add_argument('--processed',type=Path,required=True);p.add_argument('--seconds',type=int,default=7500);a=p.parse_args()
    a.root.mkdir(parents=True,exist_ok=True,mode=0o700);repo=Repository(a.root/'forward.sqlite');rpc=SolanaRPC();collector=FrankCollector(repo,a.root/'raw',{'manual':str(a.manual),'raw':str(a.raw),'processed':str(a.processed)},rpc)
    for path in sorted((a.processed/'normalized500').glob('*.json.gz')):
        collector.store.put(json.loads(gzip.decompress(path.read_bytes())))
    log=a.root/'cycles.jsonl';stopping=False
    def stop(*_):
        nonlocal stopping
        stopping=True
    signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
    def record(value):
        with log.open('ab') as f:f.write(canonical({'utc':datetime.now(timezone.utc).isoformat(),'pid':os.getpid(),**value})+b'\n');f.flush();os.fsync(f.fileno())
        log.chmod(0o600)
    if collector.store.cursor() is None:
        latest=rpc.signatures(limit=1)[0];tx=rpc.transaction(latest['signature'])
        from mission_agent.frank.archive import publish
        publish(a.root/'raw'/(latest['signature']+'.json.gz'),gzip.compress(json.dumps(tx,separators=(',',':'),allow_nan=False).encode(),mtime=0))
        collector.store.put(normalize(latest['signature'],tx),advance=True);record({'event':'INITIAL_CURSOR','cursor':collector.store.cursor()})
    record({'event':'START','cursor':collector.store.cursor(),'poll_interval':30});start=time.monotonic()
    while not stopping and time.monotonic()-start<a.seconds:
        try:record({'event':'CYCLE',**collector.cycle(),'rpc_calls':rpc.calls,'rpc_retries':rpc.retries,'rpc_429_count':rpc.rate_limits})
        except Exception as exc:record({'event':'ERROR','error':str(exc),'rpc_calls':rpc.calls,'rpc_retries':rpc.retries,'rpc_429_count':rpc.rate_limits})
        for _ in range(30):
            if stopping:break
            time.sleep(1)
    record({'event':'STOP','elapsed_seconds':str(time.monotonic()-start),'cursor':collector.store.cursor()});repo.close()
if __name__=='__main__':main()
