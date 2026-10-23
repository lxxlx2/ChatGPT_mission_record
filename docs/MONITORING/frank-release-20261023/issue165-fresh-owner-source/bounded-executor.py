import pathlib,sys,json,hashlib,os,datetime,time,subprocess,importlib.util
ROOT=pathlib.Path('/tmp/frank165-pr60-offline/crypto-300-profit-mission/local-agent');sys.path.insert(0,str(ROOT))
from mission_agent.mission_control.wallet_full_rpc_evidence import collect_owner_full_receipts,replay_owner_full_receipts,_load_verified_reply,MAX_RAW_RPC_BYTES
from mission_agent.mission_control.wallet_chain_capture import PROGRAMS
from mission_agent.mission_control.person_registry import PersonRegistry
spec=importlib.util.spec_from_file_location('approved_cli',ROOT/'scripts/frank_capture_owner_full_receipts.py');cli=importlib.util.module_from_spec(spec);spec.loader.exec_module(cli)
class StopNow(BaseException):pass
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
class StrictRead:
 def __init__(self,transport,owner,journal=None):self.transport=transport;self.owner=owner;self.calls=0;self.validated=0;self.first_slot=None;self.records=[];self.journal=journal;self.failed=False
 def save(self):
  if self.journal:self.journal.write_text(json.dumps({'calls':self.calls,'validated':self.validated,'records':self.records,'failed':self.failed},indent=2))
 def __call__(self,method,params,rid):
  if self.failed or self.calls>=2 or rid!=self.calls+1 or (rid==2 and self.validated!=1):raise StopNow('STRICT_ORDER_STOP')
  cfg=params[2]
  if method!='getTokenAccountsByOwner' or params[0]!=self.owner or params[1]!={'programId':PROGRAMS[rid-1]} or cfg.get('encoding')!='jsonParsed' or cfg.get('commitment')!='finalized':raise StopNow('STRICT_SCOPE_STOP')
  if rid==2 and cfg.get('minContextSlot')!=self.first_slot:raise StopNow('STRICT_SLOT_ORDER_STOP')
  self.calls+=1;r={'request_id':rid,'program_id':PROGRAMS[rid-1],'request_started_utc':utc(),'minContextSlot':cfg.get('minContextSlot')};self.records.append(r);self.save()
  try:
   raw=self.transport(method,params,rid)
   r['response_received_utc']=utc();r['bytes']=len(raw);r['sha256']=hashlib.sha256(raw).hexdigest()
   reply,norm=_load_verified_reply(raw,rid,self.owner,PROGRAMS[rid-1])
   if rid==2 and norm['slot']<self.first_slot:raise ValueError('CONTEXT_SLOT_BELOW_MIN')
   r.update({'slot':norm['slot'],'account_count':norm['account_count'],'validated':True})
   self.validated+=1
   if rid==1:self.first_slot=norm['slot']
   self.save();return raw
  except BaseException as e:
   self.failed=True;r['failure_type']=type(e).__name__;r['finished_utc']=utc();self.save();raise StopNow('OWNER_READ_FAILED_STOP_WITHOUT_RETRY') from None

def owner():
 r=PersonRegistry.from_file(ROOT/'config/frank_local_registry.json');w=[x.address for x in r.wallets_for('frank') if x.chain=='solana'];assert len(w)==1;return w[0]

def test():
 import tempfile,copy
 o=owner();old=pathlib.Path.home()/'.local/share/frank-f02-research/manual-sessions/session-756658113be74ce9a302736797f15104/wire/owner-6951760af67d4adbb1479d7348053dac';good=json.loads((old/'spl-token.json').read_text());cases=[]
 cases.append(('transport_error',None));cases.append(('bad_json',b'{'))
 for name,mutate in [('rpc_error',lambda d:d.update(error={'code':-1})),('wrong_id',lambda d:d.update(id=99)),('missing_context',lambda d:d['result'].pop('context')),('owner_mismatch',lambda d:d['result']['value'][0]['account']['data']['parsed']['info'].update(owner='2'*32)),('program_mismatch',lambda d:d['result']['value'][0]['account'].update(owner=PROGRAMS[1])),('duplicate_account',lambda d:d['result']['value'].append(d['result']['value'][0]))]:
  d=copy.deepcopy(good);mutate(d);cases.append((name,json.dumps(d).encode()))
 results=[]
 for name,raw in cases:
  inv=[]
  def tx(method,params,rid):
   inv.append(rid)
   if raw is None:raise TimeoutError()
   return raw
  s=StrictRead(tx,o)
  with tempfile.TemporaryDirectory() as td:
   try:collect_owner_full_receipts(wallet=o,evidence_root=pathlib.Path(td).resolve(),read_raw=s)
   except StopNow:pass
   else:raise AssertionError('failure not stopped')
  assert inv==[1] and s.calls==1 and s.validated==0,(name,inv);results.append({'case':name,'pass':True,'transport_calls':1,'second_call':False})
 # Verify two-success order/minContextSlot and denial of a third invocation.
 data=[(old/n).read_bytes() for n in ['spl-token.json','token-2022.json']];inv=[]
 def tx2(method,params,rid):inv.append(rid);return data[rid-1]
 s=StrictRead(tx2,o)
 with tempfile.TemporaryDirectory() as td:
  cap=collect_owner_full_receipts(wallet=o,evidence_root=pathlib.Path(td).resolve(),read_raw=s);assert cap['manifest']['complete'];assert s.calls==s.validated==2
  try:s('getTokenAccountsByOwner',[o,{'programId':PROGRAMS[1]},{'encoding':'jsonParsed','commitment':'finalized','minContextSlot':s.first_slot}],3)
  except StopNow:pass
  else:raise AssertionError('third call allowed')
 assert inv==[1,2];results.append({'case':'two_success_order_and_third_denied','pass':True,'transport_calls':2})
 print(json.dumps({'offline_gate_tests':results,'real_rpc':0},indent=2))

def execute():
 from urllib.parse import urlsplit
 run=pathlib.Path('/tmp/frank165-fresh-rpc-run');pre=json.loads((run/'billing-preflight.json').read_text());assert pre['zero_extra_cost_gate'] is True and pre['plan']=='Free' and pre['remaining_cu']>20
 assert time.time()-pre['verified_unix']<900
 assert subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD'],text=True).strip()=='e4529ba7069e5499d12323a7160ceac08c481fae'
 assert not subprocess.check_output(['git','-C',str(ROOT),'status','--porcelain'],text=True).strip()
 keyfile=pathlib.Path.home()/'Library/Application Support/FrankMeme/solana_rpc_urls';url=keyfile.read_text().strip();u=urlsplit(url);assert u.scheme=='https' and u.hostname=='solana-mainnet.g.alchemy.com' and not u.query and not u.fragment
 assert hashlib.sha256(u.path.rsplit('/',1)[-1].encode()).hexdigest()==pre['key_sha256_private']
 private=pathlib.Path.home()/'.local/share/frank-issue165-authorized-source-20261023';private.mkdir(mode=0o700,exist_ok=True);os.chmod(private,0o700)
 latch=private/'ONE_BOUNDED_RUN_STARTED';fd=os.open(latch,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600);os.write(fd,utc().encode());os.close(fd)
 journal=private/'execution-private.json';s=StrictRead(cli._wire_rpc(url),owner(),journal)
 outcome={'fixed_sha':'e4529ba7069e5499d12323a7160ceac08c481fae','started_utc':utc(),'private_root':str(private)}
 try:
  cap=collect_owner_full_receipts(wallet=owner(),evidence_root=private,read_raw=s);assert cap['manifest']['complete'] is True
  snap=replay_owner_full_receipts(cap['bundle'],expected_wallet=owner());assert snap['both_programs_observed'] is True
  outcome.update(status='FRESH_DUAL_PROGRAM_SOURCE_REPLAY_VERIFIED_DATED',bundle=str(cap['bundle']),snapshot=snap)
 except BaseException as e:outcome.update(status='FRESH_SOURCE_PARTIAL',failure_type=type(e).__name__)
 outcome.update(finished_utc=utc(),rpc_calls=s.calls,validated_calls=s.validated,request_records=s.records)
 (private/'outcome-private.json').write_text(json.dumps(outcome));os.chmod(private/'outcome-private.json',0o600);s.save()
 (run/'private-pointer').write_text(str(private));print(json.dumps({k:v for k,v in outcome.items() if k not in ['private_root','bundle','snapshot','request_records']},indent=2))
if __name__=='__main__':
 if sys.argv[1:]==['--test']:test()
 elif sys.argv[1:]==['--one-authorized-execution']:execute()
 else:raise SystemExit('EXPLICIT_TEST_OR_SINGLE_EXECUTION_REQUIRED')
