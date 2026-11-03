"""Exact selected-vault evidence and single-vault deduction; injected RPC only."""
import copy
import pytest
from test_meme_pool_vaults import RPC as PoolRPC,collect,account,mint as mint_bytes,k,change_data,P,MINT,QUOTE,POOL,BASE_VAULT,QUOTE_VAULT
from test_meme_holder_ranks import key
from mission_agent.meme.holder_binary import collect_holder_binary_check


def inputs(reverse=False,pool_slot=101,holder_slot=101,enum_slot=100,vault_raw=600,aux_raw=200,other_raw=20,omit_zero_vault=False):
    target=QUOTE if reverse else MINT;vault=QUOTE_VAULT if reverse else BASE_VAULT
    supply=vault_raw+aux_raw+10*other_raw
    rows=[]
    if vault_raw or not omit_zero_vault:rows.append({'token_account':vault,'owner':POOL,'raw':str(vault_raw),'decimals':0})
    rows.append({'token_account':key(9000),'owner':POOL,'raw':str(aux_raw),'decimals':0})
    rows.extend({'token_account':key(10000+i),'owner':key(8000+i),'raw':str(other_raw),'decimals':0} for i in range(10))
    ranks={'requested':True,'status':'COMPLETE_SNAPSHOT','mint':target,'program_id':P,'snapshot_slot':enum_slot,'supply_slot':enum_slot,
           'response_sha256':'a'*64,'account_count':len(rows),'accounts':rows,'owners':[],
           'supply_raw':str(supply),'total_raw':str(supply),'decimals':0,'normalization_complete':False,
           'metrics':{'GLOBAL_OWNER_TOP10_PCT':'98.0000','GLOBAL_EX_LP_OWNER_TOP10_PCT':'20.0000'}}
    mr=mint_bytes(0);mr[36:44]=supply.to_bytes(8,'little')
    data={}
    for i,row in enumerate(rows):
        owner=3000 if row['owner']==POOL else 8000+i-(2 if not omit_zero_vault else 1)
        b=bytearray(165);b[:32]=k(2000 if reverse else 1000);b[32:64]=k(owner);b[64:72]=int(row['raw']).to_bytes(8,'little');b[108]=1
        data[row['token_account']]=account(P,b)
    class HolderRPC:
        calls=0
        def call(self,method,params,ttl=0):
            self.calls+=1
            return {'context':{'slot':holder_slot},'value':[account(P,mr)]+[data[a] for a in params[0][1:]]}
    hr=HolderRPC();ranks['raw_balance_check']=collect_holder_binary_check(target,ranks,hr)
    pr=PoolRPC();pr.slot=pool_slot
    index=2 if reverse else 1
    def raw_amount(b):b[64:72]=vault_raw.to_bytes(8,'little')
    change_data(pr.values[index],raw_amount)
    pr.values[4 if reverse else 3]=account(P,mr)
    pool=collect(pr,reverse)
    return target,ranks,pool,hr,pr


def build(target,ranks,pool):
    from mission_agent.meme.pool_holder_roles import build_pool_holder_roles
    return build_pool_holder_roles(target,ranks,pool)


@pytest.mark.parametrize('reverse',[False,True])
def test_only_verified_target_vault_is_deducted_and_same_owner_auxiliary_balance_stays(reverse):
    target,r,p,hr,pr=inputs(reverse);saved=copy.deepcopy((r,p));out=build(target,r,p)
    assert out['status']=='SELECTED_VAULT_BOUND' and out['metric_status']=='SINGLE_VAULT_DEDUCTION_ONLY'
    assert out['vault_address']==(QUOTE_VAULT if reverse else BASE_VAULT)
    assert out['vault_raw']=='600' and out['pool_owner_raw_before']=='800' and out['pool_owner_raw_after']=='200'
    assert out['remaining_raw']=='400' and out['top10_raw_after']=='380'
    assert out['top10_pct_of_mint_supply']=='38.0000' and out['top10_pct_of_remaining']=='95.0000'
    assert out['all_special_roles_normalized'] is False and out['independent_provider'] is False
    assert len(pr.requests)==2 and hr.calls==1 and (r,p)==saved


def test_different_slots_never_deduce_pool_role_at_the_other_holder_bank():
    target,r,p,_,_=inputs(pool_slot=102);out=build(target,r,p)
    assert out['status']=='OBSERVED_AT_DIFFERENT_SLOTS'
    assert out['pool_slot']==102 and out['holder_slot']==101
    assert out['top10_pct_of_mint_supply']=='UNRESOLVED' and out['top10_pct_of_remaining']=='UNRESOLVED'


@pytest.mark.parametrize('bad',['amount','owner','mint','missing','mint_supply','decimals'])
def test_known_same_bank_conflict_withholds_deduction(bad):
    target,r,p,_,_=inputs();check=r['raw_balance_check'];row=next(x for x in check['records'] if x['token_account']==p['target']['vault'])
    if bad=='amount':row['raw']='599'
    elif bad=='owner':row['owner']=key(9999)
    elif bad=='mint':row['mint']=key(9999)
    elif bad=='missing':row['status']='MISSING';row.pop('raw')
    elif bad=='mint_supply':p['target']['mint_supply_raw']='1001'
    else:p['target']['decimals']=1
    out=build(target,r,p)
    assert out['status']=='SAME_SLOT_CONTRADICTION'
    assert out['top10_pct_of_mint_supply']=='UNRESOLVED'


def test_missing_positive_vault_contradicts_a_claimed_complete_mass_at_same_slot():
    target,r,p,_,_=inputs();r['raw_balance_check']['records']=[row for row in r['raw_balance_check']['records'] if row['token_account']!=p['target']['vault']]
    # Prior proof is now malformed, so do not claim a complete-mass contradiction.
    assert build(target,r,p)['metric_status']=='UNRESOLVED'
    # A structurally valid mass proof covering OTHER accounts cannot omit this
    # independently observed positive vault at the same actual bank.
    target,r,p,_,_=inputs();c=r['raw_balance_check'];v=next(row for row in c['records'] if row['token_account']==p['target']['vault'])
    old=v['token_account'];v['token_account']=key(9998)
    c['selected_accounts']=[key(9998) if a==old else a for a in c['selected_accounts']]
    assert build(target,r,p)['status']=='SAME_SLOT_CONTRADICTION'


def test_zero_vault_absent_from_holder_batch_does_not_create_a_missing_positive_balance():
    target,r,p,_,_=inputs(vault_raw=0,aux_raw=800,omit_zero_vault=True);out=build(target,r,p)
    assert out['status']=='SELECTED_VAULT_BOUND' and out['vault_binding']=='ZERO_VAULT_NOT_SAMPLED'
    assert out['vault_raw']=='0' and out['pool_owner_raw_after']=='800'


def test_zero_remainder_has_no_remaining_denominator_percentage():
    target,r,p,_,_=inputs(vault_raw=1000,aux_raw=0,other_raw=0);out=build(target,r,p)
    assert out['remaining_raw']=='0' and out['top10_raw_after']=='0'
    assert out['top10_pct_of_mint_supply']=='0.0000' and out['top10_pct_of_remaining']=='UNRESOLVED'


@pytest.mark.parametrize('bad',['program','pool_hash','holder_hash','pool_mint','authority'])
def test_unverified_pool_or_provenance_never_uses_dex_names_as_role_evidence(bad):
    target,r,p,_,_=inputs()
    if bad=='program':p['pool_program']=P
    elif bad=='pool_hash':p['response_sha256']='BAD'
    elif bad=='holder_hash':r['raw_balance_check']['response_sha256']='BAD'
    elif bad=='pool_mint':p['mint']=QUOTE
    else:p['target']['authority']=key(9999)
    p['dex_id']='pumpswap';out=build(target,r,p)
    assert out['status'] not in {'SELECTED_VAULT_BOUND','SAME_SLOT_CONTRADICTION'}
    assert out['metric_status']=='UNRESOLVED'


def test_observed_pool_role_with_incomplete_holder_mass_never_computes_filtered_percentages():
    target,r,p,_,_=inputs();r['raw_balance_check']['status']='OBSERVED_SAMPLE_ONLY';r['raw_balance_check']['full_positive_mass_reconciled']=False
    out=build(target,r,p)
    assert out['status']=='SELECTED_VAULT_BOUND' and out['metric_status']=='UNRESOLVED'
    assert out['reason']=='HOLDER_MASS_NOT_VERIFIED'


def test_conflict_application_withdraws_derived_binary_and_pool_ratios_but_keeps_raw_facts():
    from mission_agent.meme.pool_holder_roles import attach_pool_holder_roles
    target,r,p,_,_=inputs(enum_slot=101);r['raw_balance_check']['mint_supply_raw']='1001'
    p['market_comparison']={'status':'UNALIGNED_RATIO_COMPARISON','difference_indexer_minus_model':'0.1','difference_pct_of_model':'1.0000'}
    out=attach_pool_holder_roles(target,r,p)
    assert out['status']=='SAME_SLOT_CONTRADICTION'
    assert r['status']=='INCOMPLETE_EVIDENCE' and all(v=='UNRESOLVED' for v in r['metrics'].values())
    assert r['raw_balance_check']['owner_top10_pct']=='UNRESOLVED'
    assert r['raw_balance_check']['full_positive_mass_reconciled'] is False
    assert p['target']['raw']=='600' and p['effective_reserves']['effective_quote_per_target']=='UNRESOLVED'
    assert p['market_comparison']['status']=='UNAVAILABLE' and p['market_comparison']['difference_indexer_minus_model'] is None
    assert out['withdrawn_metrics']['holder_owner_top10_pct']=='98.0000'


def test_actual_analyze_attaches_roles_and_completeness_never_promotes_all_roles():
    from test_meme_wallet_cluster import analyzer
    from mission_agent.meme.cluster import report_completeness,markdown
    target,r,p,_,_=inputs();a=analyzer();a.mint=target
    a._holder_ranks=lambda *args:r;a.pool_vault_snapshot=lambda *args:p;a._scan_holder=lambda *args,**kw:None
    out=a.analyze()
    assert out['pool_holder_roles']['top10_pct_of_mint_supply']=='38.0000'
    c=report_completeness(out);rows={x['id']:x for x in c['requirements']}
    assert c['status']=='INCOMPLETE_EVIDENCE' and rows['holder_roles']['status']=='PARTIAL'
    assert 'pool_holder_roles' in markdown(out)


def test_same_slot_conflict_reaches_report_coverage_and_both_completeness_domains():
    from test_meme_wallet_cluster import analyzer
    from mission_agent.meme.cluster import report_completeness
    target,r,p,_,_=inputs();p['target']['mint_supply_raw']='1001'
    a=analyzer();a.mint=target;a._holder_ranks=lambda *args:r;a.pool_vault_snapshot=lambda *args:p
    a._scan_holder=lambda *args,**kwargs:None
    a._snapshot_slots={'supply':101,'largest_accounts':101,'account_batches':[101,101]}
    report=a.analyze()
    assert report['coverage']['snapshot_consistent'] is False
    assert 'POOL_HOLDER_SAME_SLOT_CONTRADICTION' in report['coverage']['gaps']
    assert all(value=='UNRESOLVED' for key,value in report['metrics'].items() if key.endswith('_PCT'))
    assert all(row['supply_pct']=='UNRESOLVED' for row in report['holders'])
    rows={x['id']:x for x in report_completeness(report)['requirements']}
    assert rows['holder_balances']['status']=='PARTIAL'
    assert rows['market']['cause']=='POOL_HOLDER_SAME_SLOT_CONTRADICTION'


@pytest.mark.parametrize('bad',['owner_type','status_type','program_type'])
def test_malformed_stored_fields_are_not_mistaken_for_verified_same_slot_conflicts(bad):
    target,r,p,_,_=inputs()
    if bad=='program_type':p['target']['token_program']=[]
    else:
        row=next(x for x in r['raw_balance_check']['records'] if x['token_account']==p['target']['vault'])
        row['owner' if bad=='owner_type' else 'status']=[]
    out=build(target,r,p)
    assert out['status'] not in {'SELECTED_VAULT_BOUND','SAME_SLOT_CONTRADICTION'}
