from pathlib import Path
from collections import Counter
from decimal import Decimal
import hashlib,json,socket,sys
import argparse
parser=argparse.ArgumentParser(description='Audit the stopped private capture prefix; network denied.')
for name in ['source','capture','prefix','repeat','prior-report','output']:
    parser.add_argument('--'+name,type=Path,required=True)
args=parser.parse_args()
SOURCE=args.source
CAP=args.capture
def deny(*args,**kwargs):raise RuntimeError('SUMMARY_NETWORK_DENIED')
socket.socket.connect=socket.socket.connect_ex=socket.create_connection=socket.getaddrinfo=deny
sys.path.insert(0,str(SOURCE))
from mission_agent.meme.cluster import WalletClusterAnalyzer,load_registry
def sha(data):return hashlib.sha256(data).hexdigest()
def key(method,params):return json.dumps([method,params],sort_keys=True)
m=json.loads((CAP/'wire-manifest.json').read_bytes());oracle={};failed=set();txs={}
for e in m:
    req=json.loads((CAP/'raw'/f'{e["ordinal"]:04d}-request.json').read_bytes())
    body=json.loads((CAP/'raw'/f'{e["ordinal"]:04d}-response.bin').read_bytes())
    if e['http_status']!=200:continue
    oracle.setdefault(key(req['method'],req['params']),body['result'])
    if e['method']=='getTransaction' and isinstance(body['result'],dict):
        tx=body['result'];sig=req['params'][0]
        assert sig in tx['transaction']['signatures']
        txs[sig]=tx
        if tx.get('meta',{}).get('err') is not None:failed.add(sig)
class RPC:
    def call(self,method,params,**kwargs):return oracle[key(method,params)]
old_path=args.prior_report
old=json.loads(old_path.read_bytes())
a=WalletClusterAnalyzer(old['mint'],rpc=RPC(),special_registry=load_registry(SOURCE/'config/meme_special_addresses.json'))
supply,decimals,holders=a.holders()
part=json.loads((args.prefix/'partial-evidence.json').read_bytes())
repeat=(args.repeat/'partial-evidence.json').read_bytes()
assert sha(repeat)==sha((args.prefix/'partial-evidence.json').read_bytes())
rows=[]
for i,h in enumerate(holders,1):
    attempts=[w for w in part['history_attempts'] if w['owner']==h.owner]
    rows.append({'rank':i,'supply_pct':a._pct(h.raw,supply),'role':h.role,
                 'old_token_account_rank':next((j+1 for j,r in enumerate(old['holders']) if r['token_account']==h.token_account),None),
                 'planned_adaptive':h.owner in part['planned_adaptive_owners'],
                 'actual_history_attempts':len(attempts),
                 'history_stop_reasons':[w['stop_reason'] for w in attempts]})
counts={k:len(part[k]) for k in ['trades','funding','consolidations','edges','history_attempts','history_windows','transaction_errors']}
assert len(part['trades'])==len({(t['owner'],t['signature']) for t in part['trades']})
assert all(len(part[k])==len({json.dumps(t,sort_keys=True) for t in part[k]}) for k in ['funding','consolidations','edges'])
for k in ['trades','funding','consolidations','edges']:
    assert not any(t.get('signature') in failed or t.get('other_signature') in failed for t in part[k])
result={'status':'PASS_PREFIX_AUDIT_NOT_FULL_ANALYSIS','prior_report_sha256':sha(old_path.read_bytes()),
        'prior_unscanned_material_ordinary':[{'rank':i+1,'supply_pct':h['supply_pct']} for i,h in enumerate(old['holders']) if h['role']=='ORDINARY' and Decimal(h['supply_pct'])>=1 and not h['deep_scanned']],
        'snapshot_slots':a._snapshot_slots,'snapshot_atomic':False,'current_top20':rows,
        'current_material_ordinary_outside_shallow':[r['rank'] for r in rows if r['rank']>6 and r['role']=='ORDINARY' and Decimal(r['supply_pct'])>=1],
        'current_adaptive_planned':len(part['planned_adaptive_owners']),
        'current_owners_with_any_history_attempt':len({w['owner'] for w in part['history_attempts']}),
        'new_material_outside_prefix_history_read':False,
        'captured_transaction_responses':len(txs),'captured_failed_transactions':len(failed),
        'partial_economic_counts':counts,'duplicate_economic_records':0,'failed_tx_economic_records':0,
        'repeat_partial_hash_equal':True,'partial_sha256':sha(repeat),'real_rpc_in_audit':0,
        'success_report_written':False,'history_complete':False}
args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False))
