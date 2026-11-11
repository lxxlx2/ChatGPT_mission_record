"""Fallback Top20 evidence must reject explicit token/bank contradictions."""
import pytest

from mission_agent.meme.cluster import WalletClusterAnalyzer, SYSTEM_PROGRAM
from test_meme_holder_ranks import key, MINT

PROGRAM = 'TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA'
ACCOUNT, OWNER = key(600), key(601)


def analyzer(change=None, *, account_slot=100):
    class RPC:
        endpoint = 'OFFLINE_ONLY'
        calls = cache_hits = 0
        def call(self, method, params, ttl=0):
            if method == 'getTokenSupply':
                return {'context': {'slot': 100}, 'value': {'amount': '1000', 'decimals': 0}}
            if method == 'getTokenLargestAccounts':
                return {'context': {'slot': 100}, 'value': [{'address': ACCOUNT, 'amount': '100', 'decimals': 0}]}
            if method == 'getMultipleAccounts':
                if params[0] == [ACCOUNT]:
                    info = {'mint': MINT, 'owner': OWNER, 'state': 'initialized',
                            'tokenAmount': {'amount': '100', 'decimals': 0}}
                    token = {'owner': PROGRAM, 'executable': False,
                             'data': {'parsed': {'type': 'account', 'info': info}}}
                    if change:change(token)
                    return {'context': {'slot': account_slot}, 'value': [token]}
                return {'context': {'slot': account_slot}, 'value': [{'owner': SYSTEM_PROGRAM, 'executable': False}]}
            raise AssertionError('UNEXPECTED_OFFLINE_METHOD_' + method)
    a = WalletClusterAnalyzer(MINT, rpc=RPC(), deep_holders=1)
    a.token_profile = lambda: {'status': 'OK', 'program_id': PROGRAM, 'is_initialized': True,
                              'mint_authority': None, 'freeze_authority': None}
    a.market_snapshot = lambda: {'status': 'UNAVAILABLE', 'source': 'DEXSCREENER_API', 'reason': 'FIXTURE_DISABLED'}
    a._scan_holder = lambda *args, **kwargs: None
    a._scan_funding = lambda *args, **kwargs: None
    return a


@pytest.mark.parametrize('field', ['mint', 'type', 'decimals', 'same_slot_amount', 'negative_raw',
                                  'program', 'other_token_program', 'program_object', 'executable', 'state', 'state_object', 'missing_mint'])
def test_explicit_invalid_token_context_never_enters_holder_or_consistent_metrics(field):
    def change(token):
        parsed = token['data']['parsed'];info = parsed['info']
        if field == 'mint':info['mint'] = key(999)
        elif field == 'type':parsed['type'] = 'mint'
        elif field == 'decimals':info['tokenAmount']['decimals'] = 9
        elif field == 'same_slot_amount':info['tokenAmount']['amount'] = '900'
        elif field == 'negative_raw':info['tokenAmount']['amount'] = '-1'
        elif field == 'program':token['owner'] = SYSTEM_PROGRAM
        elif field == 'other_token_program':token['owner'] = 'TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb'
        elif field == 'program_object':token['owner'] = []
        elif field == 'executable':token['executable'] = True
        elif field == 'state':info['state'] = 'uninitialized'
        elif field == 'state_object':info['state'] = {}
        else:del info['mint']
    report = analyzer(change).analyze()
    assert report['holders'] == []
    assert report['coverage']['snapshot_consistent'] is False
    assert 'TOP_ACCOUNT_RESOLUTION_GAPS' in report['coverage']['gaps']
    assert all(value == 'UNRESOLVED' for name, value in report['metrics'].items() if name.endswith('_PCT'))
    assert report['coverage']['top_account_context_errors']


def test_valid_same_slot_context_keeps_original_sample_metrics():
    report = analyzer().analyze()
    assert report['holders'][0]['raw'] == '100'
    assert report['coverage']['snapshot_consistent'] is True
    assert report['metrics']['RAW_TOP10_PCT'] == '10.00'
    assert report['metrics']['KNOWN_EX_LP_TOP10_PCT'] == '10.0000'


def test_later_finalized_account_balance_is_an_observed_sample_not_same_bank_conflict():
    def change(token):token['data']['parsed']['info']['tokenAmount']['amount'] = '900'
    report = analyzer(change, account_slot=101).analyze()
    assert report['holders'][0]['raw'] == '900'
    assert report['coverage']['snapshot_consistent'] is False
    assert report['metrics']['EX_LP_TOP10_PCT'] == 'UNRESOLVED'
    assert report['metrics']['KNOWN_EX_LP_TOP10_PCT'] == '90.0000'
    assert 'top_account_context_errors' not in report['coverage']


def test_missing_mint_program_keeps_a_gap_and_withholds_percentages():
    a = analyzer()
    a.token_profile = lambda: {'status': 'UNAVAILABLE'}
    report = a.analyze()
    assert report['holders'][0]['raw'] == '100'
    assert report['coverage']['snapshot_consistent'] is False
    assert report['coverage']['top_account_context_errors'] == [{'reason': 'MINT_PROGRAM_CONTEXT_UNAVAILABLE'}]
    assert all(value == 'UNRESOLVED' for name, value in report['metrics'].items() if name.endswith('_PCT'))


def test_incomplete_owner_metadata_batch_cannot_claim_consistent_snapshot():
    a = analyzer();call = a.rpc.call
    def missing_owner(method, params, ttl=0):
        if method == 'getMultipleAccounts' and params[0] == [OWNER]:
            return {'context': {'slot': 100}, 'value': []}
        return call(method, params, ttl)
    a.rpc.call = missing_owner
    report = a.analyze()
    assert report['holders'][0]['raw'] == '100'
    assert report['coverage']['snapshot_consistent'] is False
    assert report['coverage']['top_account_context_errors'] == [{'reason': 'OWNER_METADATA_BATCH_LENGTH_INVALID', 'snapshot_slot': 100}]
    assert report['metrics']['KNOWN_EX_LP_TOP10_PCT'] == 'UNRESOLVED'


@pytest.mark.parametrize('rank_slot', [100, 101])
def test_nested_rankings_withdraw_only_the_conflicting_bank(rank_slot):
    def change(token):token['data']['parsed']['info']['tokenAmount']['amount'] = '900'
    a = analyzer(change)
    ranks = {'requested': True, 'status': 'COMPLETE_SNAPSHOT', 'snapshot_slot': rank_slot,
             'owners': [{'owner': OWNER, 'raw': '1000', 'supply_pct': '100.0000'}],
             'metrics': {'GLOBAL_OWNER_TOP10_PCT': '100.0000'},
             'raw_balance_check': {'status': 'RECONCILED_NONZERO_BALANCE_MASS', 'snapshot_slot': rank_slot,
                                   'full_positive_mass_reconciled': True, 'owner_top10_pct': '100.0000',
                                   'owners': [{'owner': OWNER, 'raw': '1000', 'supply_pct': '100.0000'}]}}
    a._holder_ranks = lambda *args: ranks
    report = a.analyze();nested = report['holder_rankings']
    if rank_slot == 100:
        assert nested['status'] == 'INCOMPLETE_EVIDENCE'
        assert nested['metrics']['GLOBAL_OWNER_TOP10_PCT'] == 'UNRESOLVED'
        assert nested['owners'][0]['supply_pct'] == 'UNRESOLVED'
        assert nested['raw_balance_check']['full_positive_mass_reconciled'] is False
        assert nested['raw_balance_check']['owner_top10_pct'] == 'UNRESOLVED'
    else:
        assert nested['status'] == 'COMPLETE_SNAPSHOT'
        assert nested['metrics']['GLOBAL_OWNER_TOP10_PCT'] == '100.0000'
        assert nested['raw_balance_check']['full_positive_mass_reconciled'] is True


@pytest.mark.parametrize('stage', ['token', 'owner'])
@pytest.mark.parametrize('payload', [None, {'unexpected': 'shape'}, 'invalid', []])
def test_unavailable_batch_has_one_original_shape_reason(stage, payload):
    a = analyzer();call = a.rpc.call
    target = ACCOUNT if stage == 'token' else OWNER
    def unavailable(method, params, ttl=0):
        if method == 'getMultipleAccounts' and params[0] == [target]:
            return {'context': {'slot': 100}, 'value': payload}
        return call(method, params, ttl)
    a.rpc.call = unavailable
    report = a.analyze()
    prefix = 'TOKEN_ACCOUNT' if stage == 'token' else 'OWNER_METADATA'
    suffix = 'LENGTH_INVALID' if isinstance(payload, list) else 'INVALID'
    assert report['coverage']['top_account_context_errors'] == [
        {'reason': prefix + '_BATCH_' + suffix, 'snapshot_slot': 100}]
    assert report['coverage']['snapshot_consistent'] is False
    assert all(value == 'UNRESOLVED' for key, value in report['metrics'].items() if key.endswith('_PCT'))
