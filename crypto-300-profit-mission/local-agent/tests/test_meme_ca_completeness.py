"""Product completeness must not be inferred from task success or rank flags."""
import pytest
from mission_agent.meme.cluster import report_completeness, markdown


def snapshot():
    return {
        'token_profile': {'status': 'OK', 'is_initialized': True},
        'coverage': {'eligible_owner_rank_complete': True,
                     'sample_owner_rank_complete': True,
                     'snapshot_consistent': True,
                     'special_normalization_complete': True, 'gaps': []},
        'holder_rankings': {'requested': True, 'status': 'COMPLETE_SNAPSHOT',
                            'normalization_complete': True},
        'market': {'status': 'OK', 'source': 'DEXSCREENER_API'},
        'assessment': {'chain_permission_status': 'PASS',
                       'cluster_status': 'NO_MATERIAL_CONTROL_CLUSTER_FOUND'},
    }


def test_green_chain_and_complete_balance_ranks_do_not_complete_due_diligence():
    report=snapshot()
    result=report_completeness(report)
    assert result['status']=='INCOMPLETE_EVIDENCE'
    domains={row['id']:row for row in result['requirements']}
    assert domains['holder_balances']['status']=='VERIFIED_SNAPSHOT'
    assert domains['wallet_history']['status']=='PARTIAL'
    assert domains['narrative']['status']=='NOT_COLLECTED'
    assert domains['independent_sources']['status']=='NOT_COLLECTED'
    assert result['missing_required']==[r['id'] for r in result['requirements'] if r['status']!='VERIFIED_SNAPSHOT']
    assert all(r['cause'] and r['attempted_sources'] and r['next_source'] for r in result['requirements'])
    assert snapshot()==report  # Pure derivation, no source or report mutation.


@pytest.mark.parametrize('rank',[
    {}, {'requested': True, 'status': 'INCOMPLETE_EVIDENCE'},
    {'requested': True, 'status': 'COMPLETE_SNAPSHOT', 'normalization_complete': 'true'},
])
def test_legacy_sample_flags_cannot_promote_global_ranks_or_roles(rank):
    report=snapshot();report['holder_rankings']=rank
    rows={row['id']:row for row in report_completeness(report)['requirements']}
    if rank.get('status')!='COMPLETE_SNAPSHOT':
        assert rows['holder_balances']['status']!='VERIFIED_SNAPSHOT'
    assert rows['holder_roles']['status']!='VERIFIED_SNAPSHOT'


def test_unavailable_sources_remain_separate_from_uncollected_capabilities():
    report=snapshot();report['token_profile']={'status':'UNAVAILABLE','reason':'SECRET_PROVIDER_TEXT'}
    report['market']={'status':'UNAVAILABLE','reason':'SECRET_PROVIDER_TEXT'}
    rows={row['id']:row for row in report_completeness(report)['requirements']}
    assert rows['contract']['status']==rows['market']['status']=='UNAVAILABLE'
    assert rows['narrative']['status']=='NOT_COLLECTED'
    assert 'SECRET_PROVIDER_TEXT' not in str(rows)


def test_source_empty_pages_and_no_unresolved_edges_do_not_prove_full_history_or_control():
    report=snapshot();report['coverage']['history_windows']=[{'stop_reason':'PROVIDER_EMPTY_PAGE','signature_slots_complete':True}]
    report['unresolved_relation_edges']=[]
    rows={row['id']:row for row in report_completeness(report)['requirements']}
    assert rows['wallet_history']['status']=='PARTIAL'
    assert rows['control_attribution']['status']=='PARTIAL'


def test_markdown_exports_explicit_incomplete_outcome_and_required_gaps():
    report=snapshot();report['analysis_completeness']=report_completeness(report)
    output=markdown(report)
    assert 'Analysis completeness: INCOMPLETE_EVIDENCE' in output
    assert '## Required evidence gaps' in output
    assert 'wallet_history' in output and 'narrative' in output
    assert 'next_source' in output


def test_markdown_legacy_report_never_invents_new_acceptance():
    output=markdown(snapshot())
    assert 'Analysis completeness: NOT_ASSESSED' in output


@pytest.mark.parametrize('contract',[{'version':1,'status':'ANALYSIS_COMPLETE','requirements':[]},'COMPLETE'])
def test_markdown_does_not_endorse_unsupported_completion_claims(contract):
    report=snapshot();report['analysis_completeness']=contract
    assert 'Analysis completeness: NOT_ASSESSED' in markdown(report)


def test_disabled_market_client_is_not_claimed_as_an_attempted_source():
    report=snapshot()
    report['market']={'status':'UNAVAILABLE','source':'DEXSCREENER_API',
                      'reason':'MARKET_CLIENT_DISABLED'}
    original=report['market'].copy()
    rows={row['id']:row for row in report_completeness(report)['requirements']}
    assert rows['market']['status']=='NOT_COLLECTED'
    assert rows['market']['cause']=='MARKET_SOURCE_NOT_REQUESTED'
    assert rows['market']['attempted_sources']==['No market reference requested']
    assert report['market']==original
    report['analysis_completeness']=report_completeness(report)
    assert 'No market reference requested' in markdown(report)


def test_attempted_unavailable_market_still_records_the_source_attempt():
    report=snapshot()
    report['market']={'status':'UNAVAILABLE','source':'DEXSCREENER_API',
                      'reason':'PRIVATE_PROVIDER_ERROR'}
    rows={row['id']:row for row in report_completeness(report)['requirements']}
    assert rows['market']['status']=='UNAVAILABLE'
    assert 'DexScreener market reference' in rows['market']['attempted_sources']
    assert 'PRIVATE_PROVIDER_ERROR' not in str(rows['market'])
