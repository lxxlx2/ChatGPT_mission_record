"""Bounded historical proofs must not be crowded out by repeated current accounts."""
import hashlib
import json

import pytest

from mission_agent.meme.cluster import WalletClusterAnalyzer
from mission_agent.meme.historical_accounts import MAX_OBSERVATIONS
from test_meme_historical_accounts import tx, OWNER, OTHER, ACCOUNT
from test_meme_holder_ranks import key, MINT


def proof(signature, slot, *, account=ACCOUNT, owner=OWNER, closed=False):
    value = tx(post=not closed, close=closed)
    value['slot'] = slot
    value['transaction']['signatures'] = [signature]
    value['transaction']['message']['accountKeys'][1]['pubkey'] = account
    for field in ('preTokenBalances', 'postTokenBalances'):
        for row in value['meta'][field]:
            row['owner'] = owner
    if closed:
        value['transaction']['message']['instructions'][0]['parsed']['info']['account'] = account
    return value


def collector():
    value = WalletClusterAnalyzer(MINT, rpc=object(), enumerate_holder_ranks=True)
    value._history_decimals = 0
    return value


def observe(collector, value, owner=OWNER):
    collector._observe_historical_accounts(value, value['transaction']['signatures'][0], owner, value['slot'])


def test_repeated_current_account_cannot_hide_later_owner_closed_identity():
    a = collector()
    for i in range(100):
        observe(a, proof(f'repeated-{i}', 1000-i))
    late = proof('late-closed', 50, account=key(601), owner=OTHER, closed=True)
    observe(a, late, OTHER)
    assert {(r['owner'], r['account']) for r in a._historical_frontier()} == {
        (OWNER, ACCOUNT), (OTHER, key(601)),
    }
    assert len(a.historical_accounts) == 3
    assert any(r['signature'] == 'late-closed' and r['closure_at_transaction_end'] ==
               'CONFIRMED_CLOSED_AT_TRANSACTION_END' for r in a.historical_accounts)
    c = a._historical_retention_coverage()
    assert (c['raw_valid_observations'], c['retained_observations'], c['compacted_observations']) == (201, 3, 198)
    assert c['represented_owner_accounts'] == 2 and c['limit_rejected_observations'] == 0


def test_oldest_binding_replaces_redundant_context_and_preserves_original_hash():
    a = collector()
    values = [proof('newest', 100), proof('oldest', 70), proof('middle', 90)]
    for value in values:
        observe(a, value)
    digest = hashlib.sha256(json.dumps(values[1], sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    assert len(a.historical_accounts) == 2
    assert all(r['signature'] == 'oldest' and r['slot'] == 70 and r['response_sha256'] == digest
               for r in a.historical_accounts)
    assert a._historical_retention_coverage()['compacted_observations'] == 4


def test_earlier_nonclosure_cannot_overwrite_independent_closure_proof():
    a = collector()
    for value in (proof('closed', 90, closed=True), proof('earlier-open', 70), proof('later-close', 100, closed=True)):
        observe(a, value)
    closed = [r for r in a.historical_accounts if r['closure_at_transaction_end'] == 'CONFIRMED_CLOSED_AT_TRANSACTION_END']
    assert len(closed) == 1 and closed[0]['signature'] == 'closed'
    assert len(a.historical_accounts) == 3
    assert a._historical_frontier()[0]['signature'] == 'earlier-open'


def test_equal_slot_retains_first_seen_proof_without_inventing_transaction_order():
    a = collector()
    observe(a, proof('z-first-observed', 100))
    observe(a, proof('a-observed-later', 100))
    assert len(a.historical_accounts) == 2
    assert all(row['signature'] == 'z-first-observed' for row in a.historical_accounts)
    assert a._historical_retention_coverage()['compacted_observations'] == 2


def test_same_account_reassigned_to_other_owner_keeps_separate_transaction_bound_proofs():
    a = collector()
    for value, owner in ((proof('former-later', 80), OWNER),
                         (proof('current-later', 100, owner=OTHER), OTHER),
                         (proof('former-earlier', 50), OWNER),
                         (proof('current-earlier', 90, owner=OTHER), OTHER)):
        observe(a, value, owner)
    assert len(a.historical_accounts) == 4
    assert {(r['owner'], r['slot']) for r in a._historical_frontier()} == {(OWNER, 50), (OTHER, 90)}
    assert a._historical_retention_coverage()['represented_owner_accounts'] == 2


def test_distinct_group_limit_remains_hard_but_earlier_existing_group_can_replace_at_capacity():
    a = collector()
    for i in range(MAX_OBSERVATIONS + 1):
        observe(a, proof(f'distinct-{i}', 1000-i, account=key(1000+i), closed=i < MAX_OBSERVATIONS))
    observe(a, proof('earliest-replacement', 1, account=key(1000), closed=True))
    assert len(a.historical_accounts) == MAX_OBSERVATIONS
    assert any(r['signature'] == 'earliest-replacement' for r in a.historical_accounts)
    c = a._historical_retention_coverage()
    assert c['raw_valid_observations'] == MAX_OBSERVATIONS + 3
    assert c['retained_observations'] == c['represented_owner_accounts'] == c['max_observations'] == MAX_OBSERVATIONS
    assert c['limit_rejected_observations'] == 2 and c['compacted_observations'] == 1
    assert a._historical_evidence_limited is True
    assert c['raw_valid_observations'] == c['retained_observations'] + c['compacted_observations'] + c['limit_rejected_observations']
    assert c['complete_history'] is False


@pytest.mark.parametrize('bad_context', ['failed', 'wrong_signature', 'slot_conflict', 'missing_slot'])
def test_unverified_or_conflicting_context_never_consumes_retention_capacity(bad_context):
    a = collector()
    value = proof('requested', 100)
    if bad_context == 'failed':
        value['meta']['err'] = {'InstructionError': [0, 'Custom']}
    elif bad_context == 'wrong_signature':
        value['transaction']['signatures'] = ['not-requested']
    elif bad_context == 'slot_conflict':
        value['slot'] = 101
    else:
        del value['slot']
    a._observe_historical_accounts(value, 'requested', OWNER, 100)
    assert a.historical_accounts == [] and sum(a._historical_errors.values()) == 1
    c = a._historical_retention_coverage()
    assert c['raw_valid_observations'] == c['retained_observations'] == c['compacted_observations'] == c['limit_rejected_observations'] == 0


def test_duplicate_owner_signature_observation_is_not_counted_again():
    a = collector()
    value = proof('same-source', 100)
    observe(a, value)
    observe(a, value)
    c = a._historical_retention_coverage()
    assert c['raw_valid_observations'] == c['retained_observations'] == 2
    assert c['compacted_observations'] == c['limit_rejected_observations'] == 0


def test_report_exposes_compaction_and_keeps_incomplete_history(monkeypatch):
    from test_meme_owner_account_history import analyzer
    a, _ = analyzer(monkeypatch)
    a._scan_funding = lambda *args: None
    for value in (proof('recent', 100), proof('older', 80)):
        observe(a, value)
    report = a.analyze()
    c = report['coverage']['historical_account_retention']
    assert c == {'version': 1, 'mode': 'OLDEST_VALID_PER_OWNER_ACCOUNT_PHASE_CLOSURE_STATUS',
                 'raw_valid_observations': 4, 'retained_observations': 2,
                 'compacted_observations': 2, 'limit_rejected_observations': 0,
                 'represented_owner_accounts': 1, 'max_observations': MAX_OBSERVATIONS,
                 'complete_history': False}
    assert 'HISTORICAL_ACCOUNT_EVIDENCE_COMPACTED' in report['coverage']['gaps']
    assert report['analysis_completeness']['status'] == 'INCOMPLETE_EVIDENCE'
