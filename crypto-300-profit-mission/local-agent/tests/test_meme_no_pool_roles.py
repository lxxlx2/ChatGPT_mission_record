"""Pool discovery must not gate dated special-account attribution or balance audit."""
import copy
import pytest
from mission_agent.meme.special_roles import collect_special_roles
from mission_agent.meme.pool_programs import pubkey_bytes
from test_meme_pool_holder_roles import inputs
from test_meme_special_roles import label
from test_meme_pool_vaults import P, POOL, BASE_VAULT, account, market


def setup_case(slot=101):
    mint,source,_,_,_=inputs()
    m=bytearray(82);m[36:44]=(1000).to_bytes(8,'little');m[45]=1
    values={mint:account(P,m),POOL:account(P,b'unsupported')}
    for row in source['accounts']:
        b=bytearray(165);b[:32]=pubkey_bytes(mint);b[32:64]=pubkey_bytes(row['owner'])
        b[64:72]=int(row['raw']).to_bytes(8,'little');b[108]=1
        values[row['token_account']]=account(P,b)
    class RPC:
        def __init__(self):self.calls=[]
        def call(self,method,params,ttl=0):
            self.calls.append((method,copy.deepcopy(params)))
            assert method=='getMultipleAccounts' and len(params[0])<=100
            return {'context':{'slot':slot},'value':[values[a] for a in params[0]]}
    return mint,source,values,RPC()


@pytest.mark.parametrize('discovery',['none','unsupported','invalid_response'])
def test_no_pool_still_audits_exact_account_claims_and_preserves_other_owner_balance(discovery):
    mint,source,values,rpc=setup_case();registry={'role_evidence':[label(mint,BASE_VAULT,'LOCK')]}
    index=market() if discovery!='none' else {'status':'UNAVAILABLE'}
    if discovery=='invalid_response':
        original=rpc.call
        def call(method,params,ttl=0):
            if params[0]==[POOL]:
                rpc.calls.append((method,copy.deepcopy(params)));return {'context':{'slot':101},'value':[]}
            return original(method,params,ttl)
        rpc.call=call
    out=collect_special_roles(mint,source,index,rpc,registry)
    assert out['audit_path']=='HOLDER_ONLY_NO_BOUND_POOL'
    assert out['rankings']['holder_mass_verified'] is True
    lp=out['rankings']['metrics']['known_ex_lp'];special=out['rankings']['metrics']['known_ex_special']
    assert lp['deducted_raw']=='0' and special['deducted_raw']=='600'
    assert special['remaining_raw']=='400' and special['top10_pct_of_mint_supply']=='38.0000'
    assert special['top10_pct_of_remaining']=='95.0000' and special['unknown_role_raw']=='400'
    assert {'owner':POOL,'raw':'200'} in special['owners']
    assert next(r for r in out['rankings']['records'] if r['token_account']==BASE_VAULT)['classification']=='ATTRIBUTION_CLAIM'
    assert out['all_special_roles_normalized'] is False
    assert len(rpc.calls)==(1 if discovery=='none' else 2)
    assert rpc.calls[-1][1][0][0]==mint and POOL not in rpc.calls[-1][1][0]
    assert rpc.calls[-1][1][1]['minContextSlot']>=source['snapshot_slot']


@pytest.mark.parametrize('bad',['expired','other_mint','missing_hash','conflict','none'])
def test_no_pool_never_promotes_stale_or_conflicting_claims(bad):
    mint,source,_,rpc=setup_case();r=label(mint,BASE_VAULT,'LOCK');rows=[r]
    if bad=='expired':r['valid_until_slot']=100
    elif bad=='other_mint':r['mint']=POOL
    elif bad=='missing_hash':r.pop('evidence_sha256')
    elif bad=='conflict':rows.append({**r,'role':'CEX'})
    else:rows=[]
    out=collect_special_roles(mint,source,{},rpc,{'role_evidence':rows})
    assert out['rankings']['metrics']['known_ex_special']['deducted_raw']=='0'
    assert out['rankings']['metrics']['known_ex_special']['unknown_role_raw']=='1000'
    assert not any(r['classification']=='CHAIN_ACCOUNT_ROLE' for r in out['rankings']['records'])


@pytest.mark.parametrize('bad',['missing','wrong_mint','supply','older'])
def test_no_pool_invalid_holder_snapshot_withholds_exact_ratios(bad):
    mint,source,values,rpc=setup_case(slot=99 if bad=='older' else 101)
    if bad=='missing':values[BASE_VAULT]=None
    elif bad=='wrong_mint':
        import base64
        b=bytearray(base64.b64decode(values[BASE_VAULT]['data'][0]));b[:32]=pubkey_bytes(POOL)
        values[BASE_VAULT]=account(P,b)
    elif bad=='supply':
        m=bytearray(82);m[36:44]=(1001).to_bytes(8,'little');m[45]=1;values[mint]=account(P,m)
    out=collect_special_roles(mint,source,{},rpc,{'role_evidence':[label(mint,BASE_VAULT,'LOCK')]})
    assert out['rankings']['metrics']['known_ex_special']['status']=='UNRESOLVED'


def test_no_pool_budget_is_terminal_and_unrequested_source_does_not_read():
    from mission_agent.meme.cluster import RPCJobBudgetExceeded
    mint,source,_,rpc=setup_case()
    def exhausted(*a,**kw):raise RPCJobBudgetExceeded('RPC_JOB_WIRE_BUDGET_EXHAUSTED')
    rpc.call=exhausted
    with pytest.raises(RPCJobBudgetExceeded):collect_special_roles(mint,source,{},rpc)
    assert collect_special_roles(mint,{'requested':False},{},rpc)['status']=='NOT_REQUESTED'


def test_holder_fallback_preserves_discovery_slot_lower_bound():
    mint,source,_,rpc=setup_case(slot=102);original=rpc.call
    def call(method,params,ttl=0):
        result=original(method,params,ttl)
        if params[0]==[POOL]:result['context']['slot']=103
        return result
    rpc.call=call
    out=collect_special_roles(mint,source,market(),rpc)
    assert rpc.calls[-1][1][1]['minContextSlot']==103
    assert out['rankings']['metrics']['known_ex_special']['status']=='UNRESOLVED'
