"""Resumable F2 raw acquisition; no full-history shortcut."""
import argparse,json,gzip,time
from pathlib import Path
from mission_agent.frank.rpc import SolanaRPC,RPCFailure
from scripts.frank_probe import store
from mission_agent.frank.archive import publish

def run(root):
    summary=json.loads((root/'availability-summary.json').read_text())
    if len(summary['probe'])<6 or not all(x['available'] for x in summary['probe']):raise ValueError('F1_PROBE_GATE_NOT_PASS')
    rows=[r for p in sorted(root.glob('signatures-page-*.json')) for r in json.loads(p.read_text())][:500]
    target=root/'raw500';target.mkdir(exist_ok=True,mode=0o700);rpc=SolanaRPC();start=time.monotonic()
    for index,row in enumerate(rows):
        path=target/(row['signature']+'.json.gz')
        if path.exists():
            cached=json.loads(gzip.decompress(path.read_bytes()))
            if cached.get('signature')!=row['signature'] or cached.get('status') not in ('AVAILABLE','UNAVAILABLE_ON_PUBLIC_RPC'):
                raise ValueError('F2_CACHE_IDENTITY_OR_STATUS_INVALID')
            if (cached['transaction'] is None)!=(cached['status']=='UNAVAILABLE_ON_PUBLIC_RPC'):
                raise ValueError('F2_CACHE_STATUS_CONTENT_MISMATCH')
            continue
        try:
            value=rpc.transaction(row['signature']);record={'signature':row['signature'],'status':'AVAILABLE' if value is not None else 'UNAVAILABLE_ON_PUBLIC_RPC','transaction':value}
        except RPCFailure as e:
            store(target/(row['signature']+'.error.json'),{'signature':row['signature'],'error':str(e)});continue
        publish(path,gzip.compress(json.dumps(record,separators=(',',':')).encode(),mtime=0))
        if (index+1)%50==0:print('F2 acquired',index+1,flush=True)
    store(root/'fetch500-summary.json',{'requested':len(rows),'cached_responses':len(list(target.glob('*.json.gz'))),'request_failures':len(list(target.glob('*.error.json'))),'rpc_calls':rpc.calls,'retries':rpc.retries,'wall_seconds':str(time.monotonic()-start)})
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);run(p.parse_args().root)
