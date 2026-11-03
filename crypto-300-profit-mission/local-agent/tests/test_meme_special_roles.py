"""Multi-protocol and account-level exclusion checks, injected RPC only."""
import copy,hashlib,base64
import pytest
from mission_agent.meme.pool_programs import CPMM,AMM_V4,CLMM,WHIRLPOOL,DLMM,decode_pool,stored_bump_authority
from mission_agent.meme.special_roles import collect_special_roles,derive_special_ranks,registry_role
from test_meme_pool_vaults import MINT,QUOTE,POOL,BASE_VAULT,QUOTE_VAULT,P,account,mint,vault,market,k,collect,RPC as PumpRPC,change_data
from test_meme_pool_holder_roles import inputs
from test_meme_holder_ranks import key

# Independently transcribed upstream packed layout offsets; not generated from
# production LAYOUTS. Test forward/reverse raw reads for every adapter.
SPECS=[(CPMM,637,'PoolState',(168,200,72,104)),(AMM_V4,752,None,(400,432,336,368)),
       (CLMM,1544,'PoolState',(73,105,137,169)),(WHIRLPOOL,653,'Whirlpool',(101,181,133,213)),
       (DLMM,904,'LbPair',(88,120,152,184))]

def pool_bytes(spec):
    program,length,name,offsets=spec;b=bytearray(length)
    if name:b[:8]=hashlib.sha256(('account:'+name).encode()).digest()[:8]
    else:b[:8]=(1).to_bytes(8,'little');b[8:16]=(254).to_bytes(8,'little')
    if program==CPMM:
        from mission_agent.meme.pool_programs import pubkey_bytes
        b[328]=253;b[232:264]=pubkey_bytes(P);b[264:296]=pubkey_bytes(P)
    for off,n in zip(offsets,(1000,2000,4000,5000)):b[off:off+32]=k(n)
    return b

@pytest.mark.parametrize('spec',SPECS)
@pytest.mark.parametrize('reverse',[False,True])
def test_every_adapter_reads_exact_stored_vaults_in_one_bank(spec,reverse):
    program=spec[0];rpc=PumpRPC();b=pool_bytes(spec);d=decode_pool(account(program,b),POOL)
    rpc.discovery=account(program,b);rpc.values[0]=account(program,b)
    for idx in (1,2):change_data(rpc.values[idx],lambda v:v.__setitem__(slice(32,64),__import__('mission_agent.meme.pool_programs',fromlist=['pubkey_bytes']).pubkey_bytes(d['authority'])))
    out=collect(rpc,reverse)
    assert out['status']=='VAULT_BALANCE_SNAPSHOT' and out['pool_program']==program
    assert out['vault_authority']==d['authority'] and out['target']['authority']==d['authority']
    assert out['target']['raw']==('200' if reverse else '100')
    assert out['effective_reserves']['status']=='NOT_COMPUTED'
    assert out['price_usd']=='UNVERIFIED' and len(rpc.requests)==2
    assert out['snapshot_slot']==101 and out['discovery_slot']==100

@pytest.mark.parametrize('spec',SPECS)
@pytest.mark.parametrize('bad',['length','owner','identity','authority'])
def test_adapters_fail_closed_on_malformed_pool_or_vault(spec,bad):
    rpc=PumpRPC();rpc.discovery=account(spec[0],pool_bytes(spec));rpc.values[0]=copy.deepcopy(rpc.discovery)
    if bad=='length':change_data(rpc.discovery,lambda b:b.append(1))
    elif bad=='owner':rpc.discovery['owner']=P
    elif bad=='identity':change_data(rpc.discovery,lambda b:b.__setitem__(slice(spec[3][0],spec[3][0]+32),k(999)))
    else:change_data(rpc.values[1],lambda b:b.__setitem__(slice(32,64),k(999)))
    out=collect(rpc)
    assert out['status'] in {'INCOMPLETE_EVIDENCE','UNSUPPORTED'} and 'target' not in out

@pytest.mark.parametrize('program,seed,bump',[(CPMM,b'vault_and_lp_mint_auth_seed',253),(AMM_V4,b'amm authority',254)])
def test_program_stored_bump_authority_matches_exact_seed_hash(program,seed,bump):
    from mission_agent.meme.pool_programs import pubkey_bytes
    from mission_agent.meme.pool_vaults import _key
    expected=_key(hashlib.sha256(seed+bytes([bump])+pubkey_bytes(program)+b'ProgramDerivedAddress').digest())
    assert stored_bump_authority(program,seed,bump)==expected
    with pytest.raises(ValueError):stored_bump_authority(program,seed,256)


def role_inputs():
    target,ranks,pool,_,_=inputs()
    d={'base_mint':target,'quote_mint':QUOTE,'base_vault':BASE_VAULT,'quote_vault':QUOTE_VAULT,
       'authority':POOL,'program':pool['pool_program'],'reference_blob':'d907b16a91f035aeb3c3182bfa0972a91bf23a86'}
    pools=[{'pool_address':POOL,'status':'POOL_IDENTITY_BOUND','snapshot_slot':101,'decoded':d}]
    return target,ranks['raw_balance_check'],pools


def test_multi_pool_deduction_keeps_auxiliary_owner_and_never_double_deducts_a_vault():
    target,c,p=role_inputs();out=derive_special_ranks(target,c,p+p)
    metric=out['metrics']['known_ex_lp']
    assert metric['deducted_raw']=='600' and metric['remaining_raw']=='400'
    assert metric['top10_pct_of_mint_supply']=='38.0000' and metric['top10_pct_of_remaining']=='95.0000'
    assert any(r['owner']==POOL and r['raw']=='200' for r in metric['owners'])
    assert metric['unknown_role_raw']=='400' and metric['global_exhaustive_top10']=='UNRESOLVED'
    assert out['all_special_roles_normalized'] is False

@pytest.mark.parametrize('bad',['slot','authority','supply','mass','registry'])
def test_role_failure_withholds_exact_global_conclusion(bad):
    target,c,p=role_inputs();registry={}
    if bad=='slot':p[0]['snapshot_slot']=102
    elif bad=='authority':p[0]['decoded']['authority']=key(9999)
    elif bad=='supply':c['mint_supply_raw']='1001'
    elif bad=='mass':c['status']='OBSERVED_SAMPLE_ONLY'
    else:registry={'normalization_complete':True,'addresses':{POOL:{'role':'CEX','source':'random'}}}
    out=derive_special_ranks(target,c,p,registry)
    assert out['all_special_roles_normalized'] is False
    assert out['metrics']['known_ex_special']['global_exhaustive_top10']=='UNRESOLVED'
    if bad in {'supply','mass','authority'}:assert out['metrics']['known_ex_lp']['status']=='UNRESOLVED'
    if bad=='slot':assert out['metrics']['known_ex_lp']['deducted_raw']=='0'


def label(target,address,role='CEX',scope='TOKEN_ACCOUNT'):
    return dict(mint=target,address=address,role=role,scope=scope,valid_from_slot=100,valid_until_slot=102,
                evidence_url='https://official.example/attribution',evidence_sha256='a'*64,label_version='1',classification='VERIFIED_ATTRIBUTION')

@pytest.mark.parametrize('role',['CEX','BRIDGE','ESCROW','VESTING','LOCK','BURN','ROUTER','PUBLIC_INFRA','PUBLIC_PROGRAM','MARKET_MAKER'])
def test_all_supported_registry_categories_preserve_source_and_claim_level(role):
    target,c,p=role_inputs();aux=c['records'][1]
    # Choose exact auxiliary token account by authority and raw amount.
    aux=next(r for r in c['records'] if r['owner']==POOL and r['raw']=='200')
    reg={'role_evidence':[label(target,aux['token_account'],role)]}
    out=derive_special_ranks(target,c,p,reg);row=next(r for r in out['records'] if r['token_account']==aux['token_account'])
    assert row['role']==role and row['classification']=='ATTRIBUTION_CLAIM'
    assert row['evidence_sha256']=='a'*64
    assert out['metrics']['known_ex_special']['deducted_raw']=='800'
    assert out['metrics']['known_ex_lp']['deducted_raw']=='600'

@pytest.mark.parametrize('bad',['mint','scope','expiry','unversioned','hash','url','legacy'])
def test_bad_or_expired_attribution_does_not_silently_exclude(bad):
    r=label(MINT,BASE_VAULT)
    if bad=='mint':r['mint']=QUOTE
    elif bad=='scope':r['scope']='ANY'
    elif bad=='expiry':r['valid_until_slot']=100
    elif bad=='unversioned':r.pop('label_version')
    elif bad=='hash':r['evidence_sha256']='bad'
    elif bad=='url':r['evidence_url']='http://example.org'
    else:r['classification']='LOCAL_REGISTRY'
    assert registry_role(MINT,BASE_VAULT,POOL,101,{'role_evidence':[r]}) is None


def test_conflicting_registry_and_chain_role_withholds_metrics_and_keeps_both():
    target,c,p=role_inputs();out=derive_special_ranks(target,c,p,{'role_evidence':[label(target,BASE_VAULT)]})
    assert out['conflicts'] and out['metrics']['known_ex_special']['status']=='UNRESOLVED'
    assert next(r for r in out['records'] if r['token_account']==BASE_VAULT)['registry_conflict']['role']=='CEX'


def test_multi_pool_cohort_uses_at_most_two_bounded_reads_and_actual_same_slot():
    target,source,_,_,_=inputs()
    rpc=PumpRPC();responses=[]
    from mission_agent.meme.pool_programs import pubkey_bytes
    m=bytearray(82);m[36:44]=(1000).to_bytes(8,'little');m[45]=1
    binary={target:account(P,m),POOL:rpc.discovery}
    for row in source['accounts']:
        b=bytearray(165);b[:32]=pubkey_bytes(target);b[32:64]=pubkey_bytes(row['owner']);b[64:72]=int(row['raw']).to_bytes(8,'little');b[108]=1
        binary[row['token_account']]=account(P,b)
    class Cohort:
        def call(self,method,params,ttl=0):
            responses.append((method,params));return {'context':{'slot':102},'value':[binary[a] for a in params[0]]}
    out=collect_special_roles(target,source,market(),Cohort())
    assert len(responses)==2 and all(len(params[0])<=100 for _,params in responses)
    assert out['snapshot_slot']==102 and out['pools'][0]['snapshot_slot']==102
    assert out['rankings']['metrics']['known_ex_lp']['deducted_raw']=='600'
    assert out['balance_check']['snapshot_slot']==102
    assert out['balance_check']['enumeration_relation']=='DIFFERENT_FINALIZED_SLOTS'


def test_dex_program_owner_is_not_a_specific_vault_role():
    from test_meme_wallet_cluster import analyzer
    from mission_agent.frank.parser import DEX_PROGRAMS
    a=analyzer();role,source=a._role(key(123),{'value':{'owner':next(iter(DEX_PROGRAMS)),'executable':False}})
    assert role=='PROGRAM_OWNED_UNRESOLVED' and 'NOT_VAULT_PROOF' in source

@pytest.mark.parametrize('bad',['discriminator','bump'])
def test_anchor_discriminator_and_legacy_bump_are_not_accepted_by_name(bad):
    from mission_agent.meme.pool_vaults import PoolSourceError
    spec=SPECS[0] if bad=='discriminator' else SPECS[1];b=pool_bytes(spec)
    if bad=='discriminator':b[0]^=1
    else:b[8:16]=(256).to_bytes(8,'little')
    with pytest.raises(PoolSourceError):decode_pool(account(spec[0],b),POOL)


def test_multi_pool_budget_exception_is_terminal_and_never_published_as_partial_success():
    from mission_agent.meme.cluster import RPCJobBudgetExceeded
    target,source,_,_,_=inputs()
    class BudgetRPC:
        def call(self,*args,**kwargs):raise RPCJobBudgetExceeded('RPC_JOB_WIRE_BUDGET_EXHAUSTED')
    with pytest.raises(RPCJobBudgetExceeded):collect_special_roles(target,source,market(),BudgetRPC())


def test_discovery_is_capped_and_unsupported_pool_reasons_are_retained():
    target,source,_,_,_=inputs();hints=[{'pair_address':key(3000+i),'base_address':target,'quote_address':QUOTE} for i in range(12)]
    seen=[]
    class Unsupported:
        def call(self,method,params,ttl=0):
            seen.append(params);return {'context':{'slot':100},'value':[account(P,b'bad') for _ in params[0]]}
    out=collect_special_roles(target,source,{**market(),'pool_candidates':hints},Unsupported())
    assert len(seen)==1 and len(seen[0][0])==8 and out['not_selected_pool_hints']==4
    assert len(out['pools'])==8 and all(p['reason']=='UNSUPPORTED_POOL_PROGRAM' for p in out['pools'])


def test_reserved_pool_keys_reduce_full_binary_batch_without_exceeding100():
    from mission_agent.meme.holder_binary import _selected
    rows=[{'token_account':key(20000+i),'owner':key(30000+i),'raw':'1','decimals':0} for i in range(99)]
    chosen,scope=_selected(rows,91)
    assert len(chosen)==10 and scope=='BOUNDED_OWNER_SAMPLE'
    chosen,scope=_selected(rows[:91],91)
    assert len(chosen)==91 and scope=='ALL_ENUMERATED_ONE_BATCH'
    assert 1+len(chosen)+8==100


def test_registry_owner_scope_is_explicit_and_conflicting_claims_stay_unknown():
    target,c,p=role_inputs();r=label(target,POOL,'CEX','OWNER')
    out=derive_special_ranks(target,c,[],{'role_evidence':[r]})
    assert out['metrics']['known_ex_special']['deducted_raw']=='800'
    reg={'role_evidence':[r,{**r,'role':'LOCK'}]}
    row=registry_role(target,BASE_VAULT,POOL,101,reg)
    assert row['role']=='UNKNOWN' and row['reason']=='CONFLICTING_REGISTRY_ATTRIBUTION'


def test_actual_analyzer_attaches_a_separate_cohort_and_never_claims_normalization():
    from test_meme_wallet_cluster import analyzer
    from mission_agent.meme.cluster import report_completeness,markdown
    target,r,p,_,_=inputs();a=analyzer();a.mint=target;a._holder_ranks=lambda *args:r
    a.pool_vault_snapshot=lambda *args:p;a._scan_holder=lambda *args,**kwargs:None
    expected={'version':1,'status':'INCOMPLETE_EVIDENCE','reason':'BOUNDARY_TEST'}
    a.special_role_snapshot=lambda *args:expected
    out=a.analyze()
    assert out['special_address_roles']==expected and 'special_address_roles' in markdown(out)
    role=next(x for x in report_completeness(out)['requirements'] if x['id']=='holder_roles')
    assert role['status']=='PARTIAL' and 'special_address_roles' in role['evidence_paths']


def test_special_audit_does_not_run_on_get_default_cli_or_disabled_flags():
    from test_meme_wallet_cluster import analyzer
    a=analyzer();a.read_pool_vaults=False;a.audit_holder_binary=True
    assert a.special_role_snapshot({},{} )['status']=='NOT_REQUESTED'
    a.read_pool_vaults=True;a.audit_holder_binary=False
    assert a.special_role_snapshot({},{} )['status']=='NOT_REQUESTED'

@pytest.mark.parametrize('kind',['token_program','decimals'])
def test_pool_declared_token_semantics_must_match_actual_mint_and_vault(kind):
    rpc=PumpRPC();b=pool_bytes(SPECS[0]);d=decode_pool(account(CPMM,b),POOL)
    from mission_agent.meme.pool_programs import pubkey_bytes
    for idx in (1,2):change_data(rpc.values[idx],lambda v:v.__setitem__(slice(32,64),pubkey_bytes(d['authority'])))
    if kind=='token_program':b[232:264]=pubkey_bytes(key(9999))
    else:b[331]=6
    rpc.discovery=account(CPMM,b);rpc.values[0]=account(CPMM,b)
    out=collect(rpc)
    assert out['status']=='INCOMPLETE_EVIDENCE' and 'target' not in out
    assert out['reason'] in {'POOL_TOKEN_PROGRAM_MISMATCH','POOL_MINT_DECIMALS_MISMATCH'}


def test_expired_registry_is_not_renewed_by_reading_a_saved_report():
    target,c,p=role_inputs();r=label(target,BASE_VAULT);r['valid_until_slot']=100
    prior=copy.deepcopy(r)
    derive_special_ranks(target,c,p,{'role_evidence':[r]})
    assert r==prior
