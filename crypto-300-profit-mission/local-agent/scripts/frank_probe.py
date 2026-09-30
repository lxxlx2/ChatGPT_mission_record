"""F1 six-position availability before F2; immutable resumable raw evidence."""
import argparse,json,time
from pathlib import Path
from mission_agent.frank.rpc import SolanaRPC
from mission_agent.frank.archive import publish

def store(path,value):
    publish(path,(json.dumps(value,indent=2)+'\n').encode())

def run(root):
    root.mkdir(exist_ok=True,parents=True,mode=0o700);rpc=SolanaRPC();pages=sorted(root.glob('signatures-page-*.json'))
    rows=[x for p in pages for x in json.loads(p.read_text())];before=rows[-1]['signature'] if rows else None
    while not (root/'signatures-complete.json').exists():
        page=rpc.signatures(before=before)
        store(root/f'signatures-page-{len(pages):04d}.json',page);pages.append(None)
        if not page:
            store(root/'signatures-complete.json',{'total':len({x['signature'] for x in rows}),'complete':True});break
        if page[-1]['signature']==before:raise ValueError('NONADVANCING_CURSOR')
        rows.extend(page);before=page[-1]['signature']
    unique=list({x['signature']:x for x in rows}.values());n=len(unique)
    positions=[0,24,(n-1)//4,(n-1)//2,3*(n-1)//4,n-1];results=[]
    for index in positions:
        if index<0 or index>=n:continue
        row=unique[index];path=root/('probe-'+str(index)+'.json')
        if path.exists():record=json.loads(path.read_text())
        else:
            try:
                tx=rpc.transaction(row['signature']);record={**row,'position':index,'available':tx is not None,'transaction':tx,'rpc_error':None,'classification':'AVAILABLE' if tx is not None else 'UNAVAILABLE_ON_PUBLIC_RPC'}
            except Exception as e:record={**row,'position':index,'available':False,'rpc_error':str(e),'classification':'RPC_REQUEST_FAILED'}
            store(path,record)
        results.append({k:v for k,v in record.items() if k!='transaction'})
        print(json.dumps(results[-1]),flush=True)
    summary={'signature_total':n,'probe':results,'recent_available':bool(results and results[0]['available']),'full_history_feasibility':'NOT_FEASIBLE_ON_APPROVED_SOURCE' if results and results[-1]['classification']=='UNAVAILABLE_ON_PUBLIC_RPC' else 'UNDETERMINED','calls':rpc.calls,'retries':rpc.retries}
    store(root/'availability-summary.json',summary);print(json.dumps(summary),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);run(p.parse_args().root)
