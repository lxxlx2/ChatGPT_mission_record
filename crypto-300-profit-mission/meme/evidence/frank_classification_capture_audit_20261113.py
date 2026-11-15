"""Private-input, offline classifier-context audit; no source fetch or live freshness claim."""
from pathlib import Path
from collections import Counter,defaultdict
import sys,json,hashlib,sqlite3,tempfile,shutil,time
from unittest.mock import patch
import argparse,subprocess
sys.dont_write_bytecode=True
p=argparse.ArgumentParser(description="Offline captured classifier contexts; the independent secondary result is frozen, not validated.")
p.add_argument('--agent',type=Path,required=True)
p.add_argument('--expected-sha',required=True)
p.add_argument('--capture',type=Path,required=True)
p.add_argument('--summary',type=Path,required=True)
p.add_argument('--contexts',type=Path)
p.add_argument('--derived',type=Path)
args=p.parse_args()
AGENT=args.agent;CAP=args.capture
source_sha=subprocess.check_output(['git','-C',str(AGENT),'rev-parse','HEAD']).decode().strip()
assert source_sha==args.expected_sha
assert not subprocess.check_output(['git','-C',str(AGENT),'status','--porcelain','--','mission_agent','config']).strip()
protected={(CAP/name).resolve() for name in ['report.json','checkpoint.sqlite','status.json','done.json']}
assert all(path is None or path.resolve() not in protected for path in [args.summary,args.contexts,args.derived])
sys.path.insert(0,str(AGENT))
from mission_agent.meme import cluster,pool_vaults,independent_check
from mission_agent.meme.job_checkpoint import JobCheckpoint,CheckpointRPC,CheckpointClient,canonical
from mission_agent.mission_control.server import CLUSTER_PRESETS
from mission_agent.frank.parser import normalize
from mission_agent.signals.classifier import classify
raw=(CAP/'report.json').read_bytes();report=json.loads(raw);original_cp_sha=hashlib.sha256((CAP/'checkpoint.sqlite').read_bytes()).hexdigest()
db=sqlite3.connect((CAP/'checkpoint.sqlite').resolve().as_uri()+'?mode=ro',uri=True);db.execute('PRAGMA query_only=ON');meta=json.loads(db.execute('SELECT body FROM metadata WHERE id=1').fetchone()[0]);db.close()
network=Counter()
def audit(event,args):
 if event.startswith('socket.'):
  network[event]+=1;raise AssertionError('OFFLINE_NO_SOCKET_ALLOWED')
sys.addaudithook(audit)
def deny(*args,**kwargs):raise AssertionError('MISSING_CAPTURE_READ_CANNOT_FETCH')
class DeniedRPC:
 endpoint='OFFLINE_PRIMARY';endpoints=['OFFLINE_PRIMARY','OFFLINE_FALLBACK']
 def __init__(self):
  self._last_by_endpoint={};self._cooldown_until={};self._monotonic=time.monotonic
 call=staticmethod(deny)
 def assert_can_publish(self):return None
class DeniedClient:
 token_snapshot=pool_snapshot=collect=collect_origin=staticmethod(deny)

calls=[];current={};scans=[]
scan_orig=cluster.WalletClusterAnalyzer._scan_holder
pool_orig=pool_vaults.collect_pool_vault_snapshot

def scan(self,holder,*args,**kwargs):
 current.clear();current.update(owner=holder.owner,token_account=holder.token_account,scan_index=len(scans),history_page_limit=self._history_page_limit,history_per_holder=args[2] if len(args)>2 else kwargs.get('history_limit'),historical_active=self._historical_scan_active)
 scans.append(dict(current))
 try:return scan_orig(self,holder,*args,**kwargs)
 finally:current.clear()

def classify_logged(sig,tx,owner):
 c=classify(sig,tx,owner)
 row={'signature':sig,'owner':owner,'classification':c['classification'],'classification_reason':c['classification_reason'],**current}
 e=c.get('evidence') or {}
 row.update(mechanical_classification=e.get('mechanical_classification'),wallet_is_signer=e.get('wallet_is_signer'),wallet_authority=e.get('classification_evidence',{}).get('wallet_authority'),program_ids=e.get('program_ids'),tx_sha256=hashlib.sha256(canonical(tx).encode()).hexdigest())
 deltas=[z for z in e.get('token_balance_deltas',[]) if z.get('wallet_owned')]
 row['changed_assets']=[{'mint':z['mint'],'delta':z['delta']} for z in deltas if int(z['delta'])]
 row['target_delta_raw']=str(sum(int(z['delta']) for z in deltas if z['mint']==report['mint'])) if e else None
 row['target_balance_rows']=sum(z['mint']==report['mint'] for z in deltas)
 row['native_incoming']=bool(e.get('native_incoming_transfer_evidence'))
 row['created_token_accounts_count']=len(e.get('created_token_accounts',[]))
 row['closed_token_accounts_count']=len(e.get('closed_token_accounts',[]))
 if c['classification']=='UNKNOWN_NEEDS_REVIEW':
  try:normalize(sig,tx,owner)
  except Exception as exc:row['normalize_exception']=type(exc).__name__+':'+str(exc)
 calls.append(row);return c

def independent_replay(mint,accounts,primary,secondary,**kwargs):
 addresses=[mint]+[a for a in dict.fromkeys(accounts) if independent_check.valid_pubkey(a) and a!=mint][:independent_check.MAX_ACCOUNTS]
 independent_check._read(primary,addresses)
 return json.loads(canonical(report['independent_balance_check']))
def pool_clock(*args,**kwargs):
 with patch.object(cluster.time,'time',return_value=report['pool_vaults']['observed_at']):return pool_orig(*args,**kwargs)

with tempfile.TemporaryDirectory(prefix='frank-classify-capture-') as temp:
 root=Path(temp);root.chmod(0o700);target=root/(meta['job_id']+'.sqlite');shutil.copyfile(CAP/'checkpoint.sqlite',target);target.chmod(0o600)
 cp=JobCheckpoint(root,meta['job_id'],readonly=True,clock=lambda:meta['last_saved_at'])
 try:
  rpc=CheckpointRPC(cp,DeniedRPC());clients={name:CheckpointClient(cp,DeniedClient(),name) for name in ['market_client','independent_market_client','narrative_client']}
  with patch.object(cluster,'classify',classify_logged),patch.object(cluster.WalletClusterAnalyzer,'_scan_holder',scan),patch.object(cluster.time,'time',return_value=report['observed_at']),patch.object(pool_vaults,'collect_pool_vault_snapshot',pool_clock),patch.object(independent_check,'collect_independent_balance_check',independent_replay):
   analyzer=cluster.WalletClusterAnalyzer(meta['mint'],rpc=rpc,special_registry=cluster.load_registry(AGENT/'config/meme_special_addresses.json'),independent_rpc=object(),**CLUSTER_PRESETS[meta['preset']],**clients)
   derived=analyzer.analyze()
  rpc.assert_can_publish();assert cp.replayed==cp.index==meta['entry_count']
  assert [(e.get('signature'),e.get('phase'),e.get('error')) for e in derived['transaction_errors']]==[(e.get('signature'),e.get('phase'),e.get('error')) for e in report['transaction_errors']], 'ERROR_IDENTITY_SEQUENCE_CHANGED'
  cp_used=cp.replayed
 finally:cp.close()
unknown=[r for r in calls if r['classification']=='UNKNOWN_NEEDS_REVIEW']
assert len(unknown)==sum(e.get('error')=='CLASSIFICATION_UNRESOLVED' for e in report['transaction_errors'])
assert [(r['signature'],'holder_classify','CLASSIFICATION_UNRESOLVED') for r in unknown]==[(e.get('signature'),e.get('phase'),e.get('error')) for e in report['transaction_errors'] if e.get('error')=='CLASSIFICATION_UNRESOLVED']
unique={}
for row in unknown:
 key=(row['owner'],row['signature'])
 if key not in unique:unique[key]={**row,'observations':0,'contexts':[]}
 unique[key]['observations']+=1;unique[key]['contexts'].append({k:row[k] for k in ['token_account','scan_index','history_page_limit','historical_active']})
private={'source_sha':source_sha,'report_sha256':hashlib.sha256(raw).hexdigest(),'original_checkpoint_sha256':original_cp_sha,'checkpoint_reads_replayed':cp_used,'scope':'EXACT_ANALYZER_CONTEXT_REPLAY; SECONDARY_RESULT_FROZEN_NOT_VERIFIED','unknown_records':unknown,'unique_owner_signature_records':list(unique.values()),'scan_invocations':scans,'all_classification_calls':calls}
summary={'source_sha':private['source_sha'],'report_sha256':private['report_sha256'],'checkpoint_reads_replayed':cp_used,'reported_unknown_records':sum(e.get('error')=='CLASSIFICATION_UNRESOLVED' for e in report['transaction_errors']),'reproduced_unknown_records':len(unknown),'unique_unknown_signatures':len({r['signature'] for r in unknown}),'unique_unknown_owner_signature_pairs':len(unique),'duplicate_owner_signature_observations':len(unknown)-len(unique),'owners_with_unknown':len({r['owner'] for r in unknown}),'all_classification_calls':len(calls),'reason_counts_records':dict(Counter(r['classification_reason'] for r in unknown)),'reason_counts_unique_owner_signature':dict(Counter(r['classification_reason'] for r in unique.values())),'normalize_exception_records':dict(Counter(r.get('normalize_exception') for r in unknown)),'normalize_exception_unique_owner_signature':dict(Counter(r.get('normalize_exception') for r in unique.values())),'mechanical_counts_unique_owner_signature':dict(Counter(r['mechanical_classification'] for r in unique.values())),'signer_counts_unique_owner_signature':dict(Counter(str(r['wallet_is_signer']) for r in unique.values())),'target_delta_sign_counts_unique_owner_signature':dict(Counter('UNAVAILABLE' if r['target_delta_raw'] is None else 'POSITIVE' if int(r['target_delta_raw'])>0 else 'NEGATIVE' if int(r['target_delta_raw'])<0 else 'ZERO' for r in unique.values())),'network_events':dict(network),'checkpoint_sha256_unchanged':hashlib.sha256((CAP/'checkpoint.sqlite').read_bytes()).hexdigest()==original_cp_sha}
assert summary['checkpoint_sha256_unchanged'] and not network
expected=json.loads(raw)
for key in ['ca_job_id','assessment_history','assessment_history_context','collection_checkpoint']:expected.pop(key,None)
expected['coverage'].pop('rpc_call_count_scope',None)
comparison=json.loads(canonical(derived))
# Only locally received timestamps and transport endpoint labels are normalized;
# source payloads/slots, TTLs, deadlines and economic fields remain untouched.
for section,key in [('holder_rankings','raw_balance_check'),('special_address_roles','balance_check')]:
 if 'result_received_at' in (expected.get(section,{}).get(key) or {}):
  comparison[section][key]['result_received_at']=expected[section][key]['result_received_at']
comparison['rpc_endpoint']=expected['rpc_endpoint']
summary['comparison_normalizations']=['holder_rankings.raw_balance_check.result_received_at','special_address_roles.balance_check.result_received_at','rpc_endpoint']
summary['business_diff_keys']=sorted(k for k in set(expected)|set(comparison) if expected.get(k)!=comparison.get(k))
summary['first_acquisition_statuses']=dict(Counter((h.get('first_acquisition') or {}).get('status') for h in derived['holders']))
summary['classification_gap_coverage']=derived['coverage'].get('holder_classification_gaps')
summary['replay_scope']='PRIMARY_CAPTURE_CONTEXT_REPLAY; SECONDARY_RESULT_FROZEN_NOT_INDEPENDENTLY_VERIFIED'
if args.contexts:args.contexts.write_text(json.dumps(private,indent=2)+'\n')
if args.derived:args.derived.write_text(json.dumps(derived,indent=2)+'\n')
args.summary.write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
