import copy,json,urllib.error,io
import pytest
from mission_agent.frank.rpc import SolanaRPC,RPCFailure,WALLET
from mission_agent.frank.parser import normalize,IncompleteTransaction,clusters,DEX_PROGRAMS
from mission_agent.frank.store import FrankStore
from mission_agent.frank.candidate import build
from mission_agent.db.repository import Repository
from mission_agent.fm.queue import ingest,validate_shadow_batch
from mission_agent.queue.batch import build_batch
from mission_agent.config import Config
from mission_agent.hashing import digest

DEX=sorted(DEX_PROGRAMS)[0]
def tx(signer=True,owned=True,swap=True):
    def bal(amount):return {'accountIndex':1,'mint':'mint1','owner':WALLET if owned else 'other','uiTokenAmount':{'amount':str(amount),'decimals':6,'uiAmount':amount/1e6}}
    value={'slot':12,'blockTime':1790760000,'version':0,'transaction':{'message':{'accountKeys':[{'pubkey':WALLET,'signer':signer},{'pubkey':'ata','signer':False}],'instructions':[{'programId':DEX if swap else 'TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA','parsed':{'type':'swap' if swap else 'transferChecked','info':{'authority':WALLET if signer else 'other'}}}]}},'meta':{'err':None,'fee':5000,'preBalances':[1000000000,2000000],'postBalances':[499995000,2000000],'preTokenBalances':[bal(0)],'postTokenBalances':[bal(1000000)],'innerInstructions':[],'logMessages':[]}}
    if swap:
        value['transaction']['message']['accountKeys'].append({'pubkey':'quote_ata','signer':False})
        value['meta']['preBalances'].append(2000000);value['meta']['postBalances'].append(2000000)
        for field,amount in [('preTokenBalances',500000),('postTokenBalances',0)]:
            q=bal(amount);q['mint']='quote_mint';q['accountIndex']=2;value['meta'][field].append(q)
    return value

def test_owned_delta_and_active_exchange():
    e=normalize('s',tx());assert e['mechanical_classification']=='ACTIVE_SWAP_LIKE';assert e['token_balance_deltas'][0]['delta']=='1000000';assert e['fee_adjusted_SOL_delta_lamports']=='-500000000'
    assert not 'wallet_is_authority' in e;assert e['authority_accounts'][0]['matches_wallet']

def test_other_owner_never_frank_position():
    e=normalize('s',tx(owned=False));assert e['mechanical_classification']=='UNKNOWN';assert not e['wallet_token_owner']

def test_passive_receipt_not_active():
    t=tx(False,swap=False);t['transaction']['message']['accountKeys'].insert(0,{'pubkey':'payer','signer':True});t['meta']['preBalances'].insert(0,1000000000);t['meta']['postBalances'].insert(0,999995000)
    for k in ('preTokenBalances','postTokenBalances'):t['meta'][k][0]['accountIndex']=2
    e=normalize('s',t);assert e['mechanical_classification']=='PASSIVE_RECEIPT_LIKE';assert not e['wallet_is_fee_payer'];assert build(e,e['token_balance_deltas'][0]) is None

@pytest.mark.parametrize('version',['legacy',0,1])
def test_supported_transaction_versions(version):
    t=tx();t['version']=version;assert normalize('s',t)['version']==version

def test_failed_transaction_not_swap():
    t=tx();t['meta']['err']={'InstructionError':[0,{'Custom':4}]};assert normalize('s',t)['mechanical_classification']=='UNKNOWN'

def test_unknown_program_not_swap():
    t=tx();t['transaction']['message']['instructions'][0]['programId']='unknown';assert normalize('s',t)['mechanical_classification']=='UNKNOWN'

def test_memo_parsed_string():
    t=tx();t['transaction']['message']['instructions'].append({'programId':'memo','parsed':'hello'});assert normalize('s',t)['instruction_count']==2

def test_inner_authority_and_account_close():
    t=tx();t['meta']['innerInstructions']=[{'index':0,'instructions':[{'programId':'token','parsed':{'type':'closeAccount','info':{'owner':WALLET,'account':'ata','destination':WALLET}}}]}]
    e=normalize('s',t);assert e['inner_instruction_authority_evidence'][0]['account']==WALLET;assert len(e['closed_token_accounts'])==1

def test_created_and_closed_zero_balance_token():
    t=tx();t['meta']['postTokenBalances']=[];t['meta']['preTokenBalances'][0]['uiTokenAmount']['amount']='5'
    e=normalize('s',t);assert e['token_balance_deltas'][0]['post_amount']=='0';assert e['token_balance_deltas'][0]['delta']=='-5'

@pytest.mark.parametrize('mutation',[lambda t:t.update(version=2),lambda t:t.update(meta=None),lambda t:t['meta'].update(preTokenBalances=None),lambda t:t['meta'].update(postBalances=[]),lambda t:t['meta']['postTokenBalances'][0].update(owner='changed')])
def test_incomplete_or_ambiguous_rejected(mutation):
    t=tx();mutation(t)
    with pytest.raises(IncompleteTransaction):normalize('s',t)

def test_null_classified_unavailable():
    with pytest.raises(IncompleteTransaction,match='UNAVAILABLE_ON_PUBLIC_RPC'):normalize('s',None)

def test_clusters_deterministic_and_hft_suppression():
    rows=[]
    for i in range(3):
        t=tx();t['blockTime']+=i*10;rows.append(normalize(str(i),t))
    c=clusters(rows);assert c==clusters(list(reversed(rows)));assert c[0]['tx_count']==3;assert c[0]['gross_in']=='3000000';assert build(rows[0],rows[0]['token_balance_deltas'][0],c[0]) is None

def test_store_restart_dedupe_cursor_and_rollback(tmp_path):
    path=tmp_path/'db';r=Repository(path);s=FrankStore(r);e=normalize('s',tx())
    with pytest.raises(RuntimeError):s.put(e,True,True)
    assert not s.evidence() and s.cursor() is None
    assert s.put(e,True)=='INSERTED';r.close();r=Repository(path);s=FrankStore(r);assert s.put(e)=='DUPLICATE';assert s.cursor()['signature']=='s'
    t=tx();t['slot']=11
    with pytest.raises(ValueError,match='CURSOR_BACKWARD'):s.put(normalize('old',t),True)
    assert len(s.evidence())==1;r.close()

def test_candidate_queue_contract_and_duplicate(tmp_path):
    r=Repository(tmp_path/'db');e=normalize('s',tx());v=build(e,e['token_balance_deltas'][0]);assert ingest(r,v)=='INSERTED';assert ingest(r,v)=='DUPLICATE'
    b=build_batch(r,Config.for_remote(tmp_path));assert validate_shadow_batch(b)['items_verified']==1;assert r.counts()['deliveries']==1;r.close()

def test_cached_history_can_advance_forward_cursor_atomically(tmp_path):
    r=Repository(tmp_path/'db');s=FrankStore(r)
    old=tx();old['slot']=11
    s.put(normalize('old',old),True)
    evidence=normalize('cached',tx());s.put(evidence)
    with pytest.raises(RuntimeError):s.put(evidence,True,True)
    assert s.cursor()['signature']=='old'
    assert s.put(evidence,True)=='DUPLICATE'
    assert s.cursor()['signature']=='cached' and len(s.evidence())==2
    with pytest.raises(ValueError,match='CURSOR_BACKWARD'):s.put(normalize('old',old),True)
    assert s.cursor()['signature']=='cached';r.close()

def test_archive_never_replaces_published_evidence(tmp_path):
    from mission_agent.frank.archive import publish
    path=tmp_path/'evidence.json';publish(path,b'original')
    with pytest.raises(FileExistsError):publish(path,b'replacement')
    assert path.read_bytes()==b'original'
    assert path.stat().st_mode & 0o777 == 0o600
    assert list(tmp_path.iterdir())==[path]

def test_archive_interrupted_publication_exposes_no_partial_file(tmp_path,monkeypatch):
    from mission_agent.frank import archive
    def fail(*args):raise OSError('injected link failure')
    monkeypatch.setattr(archive.os,'link',fail)
    with pytest.raises(OSError):archive.publish(tmp_path/'evidence.json',b'content')
    assert list(tmp_path.iterdir())==[]

class Response:
    def __init__(self,value):self.value=value
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def read(self):return json.dumps({'result':self.value}).encode()

def test_rpc_429_backoff_and_finalized_v1():
    requests=[];sleeps=[]
    def request(req,timeout):
        requests.append(json.loads(req.data))
        if len(requests)==1:raise urllib.error.HTTPError(req.full_url,429,'rate',{'Retry-After':'1'},None)
        return Response(None)
    rpc=SolanaRPC(request,sleeps.append,lambda:0,lambda:0);assert rpc.transaction('s') is None;assert rpc.calls==2 and rpc.retries==1;assert max(sleeps)>=1
    assert requests[-1]['params'][1]=={'commitment':'finalized','encoding':'jsonParsed','maxSupportedTransactionVersion':1}

def test_rpc_timeout_bounded_and_no_write_method():
    calls=[]
    def request(*a,**k):calls.append(1);raise TimeoutError()
    rpc=SolanaRPC(request,lambda x:None,lambda:0,lambda:0)
    with pytest.raises(RPCFailure):rpc.transaction('s')
    assert len(calls)==3
    with pytest.raises(ValueError):rpc.call('sendTransaction',[])
from mission_agent.frank.collector import FrankCollector

def test_forward_gate_refuses_before_manual_review(tmp_path):
    r=Repository(tmp_path/'db')
    with pytest.raises(ValueError,match='ACCEPTANCE'):FrankCollector(r,tmp_path/'raw',{})
    r.close()

def collector(tmp_path,rpc):
    r=Repository(tmp_path/'db');s=FrankStore(r);s.put(normalize('old',tx()),advance=True)
    return r,FrankCollector(r,tmp_path/'raw',{'processed':500,'manual_reviewed':50,'independent_explorer_review':True,'parser_errors':0},rpc)

def test_forward_out_of_order_duplicate_restart(tmp_path):
    class Fake:
        def signatures(self,before=None):return [{'signature':'new'},{'signature':'new'},{'signature':'old'}]
        def transaction(self,s):
            t=tx();t['slot']=13;return t
    r,c=collector(tmp_path,Fake());v=c.cycle();assert v['normalized']==1 and v['duplicates']==1 and v['cursor_gap']==0;r.close()
    r=Repository(tmp_path/'db');c=FrankCollector(r,tmp_path/'raw',{'processed':500,'manual_reviewed':50,'independent_explorer_review':True,'parser_errors':0},Fake());assert c.cycle()['normalized']==0;r.close()

def test_forward_null_does_not_advance_cursor(tmp_path):
    class Fake:
        def signatures(self,before=None):return [{'signature':'new'},{'signature':'old'}]
        def transaction(self,s):return None
    r,c=collector(tmp_path,Fake())
    with pytest.raises(ValueError,match='UNAVAILABLE'):c.cycle()
    assert c.store.cursor()['signature']=='old';r.close()

def test_forward_missing_cursor_denies_false_gap_zero(tmp_path):
    class Fake:
        def signatures(self,before=None):return []
    r,c=collector(tmp_path,Fake())
    with pytest.raises(ValueError,match='CURSOR_GAP'):c.cycle()
    r.close()

def test_initialize_owner_not_authority():
    t=tx(False,swap=False);t['transaction']['message']['instructions'][0]['parsed']={'type':'initializeAccount','info':{'owner':WALLET}}
    e=normalize('s',t);assert e['authority_accounts'][0]['matches_wallet'];assert not e['authority_accounts'][0]['is_authority_evidence'];assert not e['classification_evidence']['wallet_authority']

def test_delegation_recipient_not_executing_authority():
    t=tx(False,swap=False);t['transaction']['message']['instructions'][0]['parsed']={'type':'approve','info':{'owner':'other','delegate':WALLET}}
    assert not normalize('s',t)['classification_evidence']['wallet_authority']

def test_internal_same_mint_moves_not_swap():
    t=tx();t['meta']['preTokenBalances']=t['meta']['preTokenBalances'][:1];t['meta']['postTokenBalances']=t['meta']['postTokenBalances'][:1];a=copy.deepcopy(t['meta']['preTokenBalances'][0]);b=copy.deepcopy(t['meta']['postTokenBalances'][0]);a['accountIndex']=2;b['accountIndex']=2;a['uiTokenAmount']['amount']='1000000';b['uiTokenAmount']['amount']='0'
    t['transaction']['message']['accountKeys'].append({'pubkey':'second_ata','signer':False});t['meta']['preBalances'].append(2000000);t['meta']['postBalances'].append(2000000);t['meta']['preTokenBalances'].append(a);t['meta']['postTokenBalances'].append(b)
    assert normalize('s',t)['mechanical_classification']!='ACTIVE_SWAP_LIKE'

def test_sqlite_lock_preserves_cursor(tmp_path):
    import sqlite3
    r=Repository(tmp_path/'db');s=FrankStore(r);r.db.execute('PRAGMA busy_timeout=10');other=sqlite3.connect(tmp_path/'db',isolation_level=None);other.execute('BEGIN IMMEDIATE')
    try:
        with pytest.raises(sqlite3.OperationalError,match='locked'):s.put(normalize('s',tx()),True)
        assert s.cursor() is None
    finally:other.rollback();other.close();r.close()

def test_signature_same_id_hash_conflict(tmp_path):
    r=Repository(tmp_path/'db');s=FrankStore(r);s.put(normalize('s',tx()));t=tx();t['slot']=13
    with pytest.raises(ValueError,match='CONTENT_CONFLICT'):s.put(normalize('s',t))
    r.close()

def test_kill_uncommitted_sqlite_transaction_recovers(tmp_path):
    import subprocess,sys,signal
    path=tmp_path/'db';r=Repository(path);s=FrankStore(r);s.put(normalize('old',tx()),True);r.close()
    code="import sqlite3,sys,time; c=sqlite3.connect(sys.argv[1],isolation_level=None); c.execute('BEGIN IMMEDIATE'); c.execute(\"UPDATE frank_cursor SET signature='uncommitted'\"); print('READY',flush=True); time.sleep(30)"
    p=subprocess.Popen([sys.executable,'-c',code,str(path)],stdout=subprocess.PIPE,text=True)
    try:
        assert p.stdout.readline().strip()=='READY';p.kill();p.wait(timeout=5)
        r=Repository(path);s=FrankStore(r);assert s.cursor()['signature']=='old';assert r.db.execute('PRAGMA integrity_check').fetchone()[0]=='ok';r.close()
    finally:
        if p.poll() is None:p.kill();p.wait()

def test_queue_oversize_and_source_rejection(tmp_path):
    from mission_agent.hashing import seal
    r=Repository(tmp_path/'db');e=normalize('s',tx());v=build(e,e['token_balance_deltas'][0]);body={k:x for k,x in v.items() if k!='payload_sha256'}
    with pytest.raises(ValueError,match='SOURCE'):ingest(r,seal({**body,'source':'third_party'}))
    with pytest.raises(ValueError,match='2KB'):ingest(r,seal({**body,'padding':'x'*3000}))
    assert r.counts()['candidates']==0;r.close()

def test_unknown_program_cpi_transfer_not_plain_transfer():
    t=tx(swap=False);t['transaction']['message']['instructions'].append({'programId':'unknown-dex','accounts':[],'data':'unknown'})
    assert normalize('s',t)['mechanical_classification']=='UNKNOWN'

def test_sol_rent_refund_cannot_establish_swap_consideration():
    t=tx();t['meta']['preTokenBalances']=t['meta']['preTokenBalances'][:1];t['meta']['postTokenBalances']=t['meta']['postTokenBalances'][:1]
    assert normalize('rent',t)['mechanical_classification']=='UNKNOWN'
