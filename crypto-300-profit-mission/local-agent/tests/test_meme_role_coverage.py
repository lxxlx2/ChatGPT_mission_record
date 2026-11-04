"""Role coverage is an account balance partition, never whole-Owner identity."""
import copy
import pytest
from mission_agent.meme.special_roles import derive_special_ranks
from test_meme_special_roles import role_inputs,label
from test_meme_pool_vaults import POOL,BASE_VAULT


def test_chain_vault_does_not_promote_auxiliary_balance_to_whole_owner_identity():
    mint,c,p=role_inputs();r=derive_special_ranks(mint,c,p)
    coverage=r['role_coverage'];assert coverage['chain_role_raw']=='600'
    assert coverage['unknown_role_raw']=='400' and coverage['attribution_claim_raw']=='0'
    assert coverage['observed_raw']=='1000' and coverage['unknown_pct_of_mint_supply']=='40.0000'
    owner=next(x for x in coverage['owners'] if x['owner']==POOL)
    assert owner['raw']=='800' and owner['unknown_role_raw']=='200' and owner['mixed_evidence'] is True
    assert owner['chain_roles']==['PROTOCOL_VAULT'] and owner['claimed_roles']==[]
    assert coverage['unknown_nonzero_owner_count']==11
    assert coverage['holder_snapshot_slot']==c['snapshot_slot'] and coverage['holder_response_sha256']==c['response_sha256']
    assert coverage['all_special_roles_normalized'] is False


def test_scoped_attribution_and_chain_evidence_are_separate_partitions():
    mint,c,p=role_inputs();aux=next(x for x in c['records'] if x['owner']==POOL and x['raw']=='200')
    r=derive_special_ranks(mint,c,p,{'role_evidence':[label(mint,aux['token_account'],'LOCK')]})
    coverage=r['role_coverage'];o=next(x for x in coverage['owners'] if x['owner']==POOL)
    assert (coverage['chain_role_raw'],coverage['attribution_claim_raw'],coverage['unknown_role_raw'])==('600','200','200')
    assert o['claimed_roles']==['LOCK'] and o['unknown_role_raw']=='0' and o['mixed_evidence'] is True
    assert coverage['unknown_nonzero_owner_count']==10
    assert coverage['status']=='EXACT_OBSERVED_ROLE_PARTITION'


@pytest.mark.parametrize('bad',['expired','conflict','unversioned'])
def test_rejected_registry_claim_remains_in_unknown_partition(bad):
    mint,c,p=role_inputs();aux=next(x for x in c['records'] if x['owner']==POOL and x['raw']=='200')
    row=label(mint,aux['token_account'],'LOCK');rows=[row]
    if bad=='expired':row['valid_until_slot']=100
    elif bad=='conflict':rows.append({**row,'role':'CEX'})
    else:row.pop('label_version')
    v=derive_special_ranks(mint,c,p,{'role_evidence':rows})['role_coverage']
    assert v['unknown_role_raw']=='400' and v['attribution_claim_raw']=='0'


@pytest.mark.parametrize('bad',['sample','supply','role_conflict'])
def test_unverified_mass_or_role_conflict_cannot_certify_coverage_percentage(bad):
    mint,c,p=role_inputs();reg={}
    if bad=='sample':c['status']='OBSERVED_SAMPLE_ONLY'
    elif bad=='supply':c['mint_supply_raw']='1001'
    else:reg={'role_evidence':[label(mint,BASE_VAULT,'LOCK')]}
    v=derive_special_ranks(mint,c,p,reg)['role_coverage']
    assert v['status']=='OBSERVED_ROLE_PARTITION_ONLY'
    assert v['unknown_pct_of_mint_supply']=='UNRESOLVED'
    assert v['all_special_roles_normalized'] is False


def test_coverage_is_deterministic_and_does_not_mutate_sources():
    mint,c,p=role_inputs();before=copy.deepcopy((c,p));a=derive_special_ranks(mint,c,p)['role_coverage']
    c['records'].reverse();b=derive_special_ranks(mint,c,p)['role_coverage']
    assert a==b
    c['records'].reverse();assert (c,p)==before
    assert a['owners']==sorted(a['owners'],key=lambda o:(-int(o['raw']),o['owner']))
    assert sum(int(o['unknown_role_raw']) for o in a['owners'])==400


def test_no_pools_or_claims_leave_every_observed_balance_unknown():
    mint,c,_=role_inputs();v=derive_special_ranks(mint,c,[])['role_coverage']
    assert v['chain_role_raw']=='0' and v['unknown_role_raw']=='1000'
    assert v['unknown_pct_of_mint_supply']=='100.0000'
    assert all(o['mixed_evidence'] is False for o in v['owners'])
