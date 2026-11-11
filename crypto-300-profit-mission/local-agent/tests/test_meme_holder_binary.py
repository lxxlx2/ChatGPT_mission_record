"""Bounded binary balance mass check, injected RPC; same provider is explicit."""
import copy
import pytest
from test_meme_pool_vaults import account,mint as mint_bytes,k,change_data,P,P22
from test_meme_holder_ranks import key
from mission_agent.meme.cluster import RPCJobBudgetExceeded

MINT=key(1000)


def token(owner,amount):
    b=bytearray(165);b[:32]=k(1000);b[32:64]=k(owner);b[64:72]=amount.to_bytes(8,'little');b[108]=1
    return b


def source(n=3):
    amounts=[40,10,50] if n==3 else [1]*n
    owners=[6000,6000,6001] if n==3 else [6000+i for i in range(n)]
    rows=[{'token_account':key(5000+i),'owner':key(o),'raw':str(a),'decimals':0} for i,(o,a) in enumerate(zip(owners,amounts))]
    return {'requested':True,'status':'INCOMPLETE_EVIDENCE','reason':'SNAPSHOT_SLOT_UNRECONCILED','mint':MINT,'program_id':P,
        'snapshot_slot':100,'supply_slot':99,'supply_raw':str(sum(amounts)),'total_raw':str(sum(amounts)),
        'decimals':0,'response_sha256':'a'*64,'account_count':n,'accounts':rows,'owners':[],
        'metrics':{'GLOBAL_OWNER_TOP10_PCT':'100.0000','GLOBAL_EX_LP_OWNER_TOP10_PCT':'100.0000'}}


class RPC:
    def __init__(self,r=None):
        self.source=r or source();self.slot=101;self.requests=[];self.budget=False
        self.mint=account(self.source['program_id'],mint_bytes(0,self.source['program_id']))
        change_data(self.mint,lambda b:b.__setitem__(slice(36,44),int(self.source['supply_raw']).to_bytes(8,'little')))
        self.records={row['token_account']:account(self.source['program_id'],token(6000+i,int(row['raw']))) for i,row in enumerate(self.source['accounts'])}
        for row in self.source['accounts']:
            # Encode the exact fixture authority, even when two accounts share it.
            from mission_agent.meme.holder_ranks import ALPHABET
            val=0
            for char in row['owner']:val=val*58+ALPHABET.index(char)
            change_data(self.records[row['token_account']],lambda b,v=val:b.__setitem__(slice(32,64),v.to_bytes(32,'big')))
    def call(self,method,params,ttl=0):
        self.requests.append((method,params))
        if self.budget:raise RPCJobBudgetExceeded('RPC_JOB_WIRE_BUDGET_EXHAUSTED')
        assert method=='getMultipleAccounts' and params[0][0]==MINT
        return {'context':{'slot':self.slot},'value':[self.mint]+[self.records.get(a) for a in params[0][1:]]}


def run(r=None,rpc=None):
    from mission_agent.meme.holder_binary import collect_holder_binary_check
    r=r or source();return collect_holder_binary_check(MINT,r,rpc or RPC(r))


def test_later_actual_bank_reconciles_all_positive_balance_mass_and_aggregates_owner_without_pinning():
    r=source();rpc=RPC(r);out=run(r,rpc)
    assert out['status']=='RECONCILED_NONZERO_BALANCE_MASS'
    assert out['enumeration_slot']==100 and out['snapshot_slot']==101
    assert out['enumeration_relation']=='DIFFERENT_FINALIZED_SLOTS'
    assert rpc.requests[0][1][1]=={'encoding':'base64','commitment':'finalized','minContextSlot':100}
    assert len(rpc.requests)==1 and len(rpc.requests[0][1][0])==4
    assert out['selected_total_raw']==out['mint_supply_raw']=='100'
    assert out['owner_top10_pct']=='100.0000' and len(out['owners'])==2
    assert [o['raw'] for o in out['owners']]==['50','50']
    assert out['independent_provider'] is False and out['roles_verified'] is False
    assert out['enumeration_membership_independently_verified'] is False
    assert len(out['response_sha256'])==64


@pytest.mark.parametrize('n,expected',[ (99,99),(100,10),(150,10)])
def test_one_batch_limits_and_sampling_are_deterministic(n,expected):
    r=source(n);rpc=RPC(r);a=run(r,rpc)
    reversed_source=copy.deepcopy(r);reversed_source['accounts'].reverse();other=RPC(reversed_source);b=run(reversed_source,other)
    assert a['selected_accounts']==b['selected_accounts']
    assert len(a['selected_accounts'])==expected and len(rpc.requests[0][1][0])<=100
    if n>99:
        assert a['status']=='OBSERVED_SAMPLE_ONLY' and a['owner_top10_pct']=='UNRESOLVED'
        assert a['accounts_not_selected']==n-expected


def test_covered_subset_can_account_for_all_positive_mass_without_claiming_all_zero_accounts_enumerated():
    r=source(100)
    for row in r['accounts'][10:]:row['raw']='0'
    r['supply_raw']=r['total_raw']='10';out=run(r)
    assert out['status']=='RECONCILED_NONZERO_BALANCE_MASS'
    assert out['accounts_not_selected']==90 and out['enumeration_membership_independently_verified'] is False


@pytest.mark.parametrize('supply',[0,101])
def test_supply_gap_or_zero_does_not_publish_full_owner_percentages(supply):
    r=source();rpc=RPC(r);change_data(rpc.mint,lambda b:b.__setitem__(slice(36,44),supply.to_bytes(8,'little')))
    out=run(r,rpc)
    assert out['status']=='OBSERVED_SAMPLE_ONLY' and out['owner_top10_pct']=='UNRESOLVED'
    assert all(o['supply_pct']=='UNRESOLVED' for o in out['owners'])


@pytest.mark.parametrize('change',['balance','authority','missing'])
def test_same_slot_representation_disagreement_is_distinct_from_later_state_change(change):
    r=source();rpc=RPC(r);address=r['accounts'][0]['token_account']
    if change=='balance':change_data(rpc.records[address],lambda b:b.__setitem__(slice(64,72),(39).to_bytes(8,'little')))
    elif change=='authority':change_data(rpc.records[address],lambda b:b.__setitem__(slice(32,64),k(9999)))
    else:rpc.records[address]=None
    later=run(r,rpc);assert later['enumeration_relation']=='DIFFERENT_FINALIZED_SLOTS'
    rpc.slot=100;same=run(r,rpc);assert same['enumeration_relation']=='SAME_SLOT_CONTRADICTION'


@pytest.mark.parametrize('bad',['base64','state','option','program','mint'])
def test_invalid_binary_account_never_becomes_zero_or_full_balance_mass(bad):
    r=source();rpc=RPC(r);a=rpc.records[r['accounts'][0]['token_account']]
    if bad=='base64':a['data']=['bad','base64']
    elif bad=='program':a['owner']=P22
    else:
        def mutate(b):
            if bad=='state':b[108]=0
            elif bad=='option':b[72:76]=(2).to_bytes(4,'little')
            else:b[:32]=k(9999)
        change_data(a,mutate)
    out=run(r,rpc)
    assert out['status']!='RECONCILED_NONZERO_BALANCE_MASS' and out['owner_top10_pct']=='UNRESOLVED'
    assert len(out['records'])==3


@pytest.mark.parametrize('bad',['duplicate','invalid_key','hash','row_count','raw_bool'])
def test_untrusted_enumeration_does_not_start_a_binary_request(bad):
    r=source()
    if bad=='duplicate':r['accounts'][1]['token_account']=r['accounts'][0]['token_account']
    elif bad=='invalid_key':r['accounts'][0]['owner']='BAD'
    elif bad=='hash':r['response_sha256']='BAD'
    elif bad=='row_count':r['account_count']=99
    else:r['accounts'][0]['raw']=True
    rpc=RPC(source());out=run(r,rpc)
    assert out['status']=='UNAVAILABLE' and not rpc.requests


def test_context_older_than_enumeration_is_not_accepted():
    r=source();rpc=RPC(r);rpc.slot=99;out=run(r,rpc)
    assert out['status']=='UNAVAILABLE' and out['reason']=='CONTEXT_BEFORE_ENUMERATION'


def test_token2022_without_mass_extensions_reconciles_and_verifies():
    from mission_agent.meme.holder_binary import verified_holder_mass
    r=source();r['program_id']=P22;rpc=RPC(r);out=run(r,rpc)
    assert out['status']=='RECONCILED_NONZERO_BALANCE_MASS' and out['token_2022_extension_types']==[]
    assert out['token_2022_mass_semantics']=='NO_WITHHELD_FEE_OR_CONFIDENTIAL_EXTENSION'
    assert verified_holder_mass(out,MINT)


def test_token2022_transfer_fee_extension_does_not_prove_economic_mass():
    from mission_agent.meme.holder_binary import token2022_extension_types
    r=source();r['program_id']=P22;rpc=RPC(r)
    # Extended mint: AccountType=1 at 165, then TLV TransferFeeConfig(type 1, len 108).
    def fee(b):
        b[165]=1;b[166:170]=(1).to_bytes(2,'little')+(108).to_bytes(2,'little');b.extend(bytes(108))
    change_data(rpc.mint,fee)
    out=run(r,rpc)
    assert out['status']=='OBSERVED_SAMPLE_ONLY' and out['reason']=='TOKEN_2022_MASS_SEMANTICS_UNVERIFIED'
    assert out['owner_top10_pct']=='UNRESOLVED' and 1 in out['token_2022_extension_types']
    assert token2022_extension_types(bytes(166)+(18).to_bytes(2,'little')+(0).to_bytes(2,'little'))==[18]


def test_job_budget_exception_is_terminal():
    r=source();rpc=RPC(r);rpc.budget=True
    with pytest.raises(RPCJobBudgetExceeded):run(r,rpc)


def test_standard_flag_and_actual_analyzer_attach_check_and_downgrade_same_slot_contradiction(monkeypatch):
    from mission_agent.meme.cluster import WalletClusterAnalyzer
    from mission_agent.mission_control.server import CLUSTER_PRESETS,CLUSTER_RPC_JOB_BUDGETS
    assert CLUSTER_PRESETS['standard']['audit_holder_binary'] is True
    assert not CLUSTER_PRESETS['quick'].get('audit_holder_binary')
    assert CLUSTER_RPC_JOB_BUDGETS['standard']['max_wire_attempts']==1200
    r=source();r['status']='COMPLETE_SNAPSHOT';r['supply_slot']=100
    rpc=RPC(r);rpc.slot=100;change_data(rpc.records[r['accounts'][0]['token_account']],lambda b:b.__setitem__(slice(64,72),(39).to_bytes(8,'little')))
    monkeypatch.setattr('mission_agent.meme.cluster.collect_mint_holder_ranks',lambda *a,**kw:copy.deepcopy(r))
    a=WalletClusterAnalyzer(MINT,rpc=rpc,enumerate_holder_ranks=True,audit_holder_binary=True)
    out=a._holder_ranks({'program_id':P,'is_initialized':True},100,0)
    assert out['raw_balance_check']['enumeration_relation']=='SAME_SLOT_CONTRADICTION'
    assert out['status']=='INCOMPLETE_EVIDENCE' and out['reason']=='RAW_BINARY_REPRESENTATION_CONTRADICTION'
    assert all(v=='UNRESOLVED' for v in out['metrics'].values())
    assert out['raw_balance_check']['source_metrics_before_check']['GLOBAL_OWNER_TOP10_PCT']=='100.0000'


@pytest.mark.parametrize('bad',['initialized','option','program','encoding','length'])
def test_unverified_mint_never_publishes_mass_or_percent(bad):
    r=source();rpc=RPC(r)
    if bad=='program':rpc.mint['owner']=P22
    elif bad=='encoding':rpc.mint['data'][1]='base64+zstd'
    else:
        def mutate(b):
            if bad=='initialized':b[45]=0
            elif bad=='option':b[0:4]=(2).to_bytes(4,'little')
            else:b.extend(b'\x00')
        change_data(rpc.mint,mutate)
    out=run(r,rpc)
    assert out['status']=='UNAVAILABLE' and out['reason']=='MINT_BINARY_UNVERIFIED'
    assert out['owner_top10_pct']=='UNRESOLVED'


def test_mass_check_and_completeness_validate_proof_without_upgrading_independent_provider_or_roles():
    from mission_agent.meme.holder_binary import verified_holder_mass
    from mission_agent.meme.cluster import report_completeness,markdown
    r=source();r['raw_balance_check']=run(r)
    assert verified_holder_mass(r['raw_balance_check'],MINT)
    report={'mint':MINT,'holder_rankings':r,'assessment':{},'metrics':{},'coverage':{},'holders':[]}
    c=report_completeness(report);rows={x['id']:x for x in c['requirements']}
    assert c['status']=='INCOMPLETE_EVIDENCE' and rows['holder_balances']['status']=='VERIFIED_SNAPSHOT'
    assert rows['holder_roles']['status']=='PARTIAL' and rows['independent_sources']['status']!='VERIFIED_SNAPSHOT'
    assert 'raw_balance_check' in markdown(report)
    for bad in ['sum','owners','status','provider','mint','percent','selected_type','record_status','flags','count_bool']:
        proof=copy.deepcopy(r['raw_balance_check'])
        if bad=='sum':proof['selected_total_raw']='1'
        elif bad=='owners':proof['owners'][0]['raw']='999'
        elif bad=='status':proof['status']='COMPLETE'
        elif bad=='provider':proof['independent_provider']=True
        elif bad=='mint':proof['mint']=key(9999)
        elif bad=='selected_type':proof['selected_accounts'][0]=[]
        elif bad=='record_status':proof['records'][0]['status']={}
        elif bad=='flags':proof['flags']=1
        elif bad=='count_bool':proof['selected_account_count']=True
        else:proof['owner_top10_pct']='999.0000'
        assert not verified_holder_mass(proof,MINT)


def test_delegate_frozen_and_close_authority_are_visible_without_control_or_exclusion_claims():
    r=source();rpc=RPC(r)
    def flags(b):b[108]=2;b[72:76]=(1).to_bytes(4,'little');b[129:133]=(1).to_bytes(4,'little')
    change_data(rpc.records[r['accounts'][0]['token_account']],flags)
    out=run(r,rpc)
    assert out['status']=='RECONCILED_NONZERO_BALANCE_MASS'
    assert {'FROZEN_ACCOUNT','DELEGATE_PRESENT','CLOSE_AUTHORITY_PRESENT'}<=set(out['flags'])
    assert out['roles_verified'] is False
