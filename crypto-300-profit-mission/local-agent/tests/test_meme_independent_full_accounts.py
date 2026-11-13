"""Full supplied-set parity, with no live RPC or assertion of full enumeration."""
import json

import pytest

from mission_agent.meme.cluster import RPCError, RPCJobBudgetExceeded
from mission_agent.meme.holder_ranks import _b58
from mission_agent.meme.independent_check import collect_independent_balance_check
from mission_agent.meme.job_checkpoint import CheckpointError

MINT = 'So11111111111111111111111111111111111111112'
OWNER = '11111111111111111111111111111111'
ACCOUNTS = [_b58((i + 1).to_bytes(32, 'big')) for i in range(205)]


class Provider:
    def __init__(self, name, order, slots=(7,), *, fail=None, missing=(), changed=()):
        self.name, self.order, self.slots = name, order, slots
        self.fail, self.missing, self.changed = fail, set(missing), set(changed)
        self.requests = []
        self.calls = 0
        self.last_wire_error_code = None

    def call(self, method, params):
        assert method == 'getMultipleAccounts'
        assert params[1] == {'encoding': 'jsonParsed', 'commitment': 'finalized'}
        addresses = params[0]
        assert 1 <= len(addresses) <= 100
        self.calls += 1
        self.requests.append(list(addresses))
        self.order.append((self.name, list(addresses)))
        if self.fail and self.calls == self.fail[0]:
            self.last_wire_error_code = 'HTTP_403'
            raise self.fail[1]
        values = []
        for address in addresses:
            if address in self.missing:
                values.append(None)
                continue
            amount = '61' if address in self.changed else '60'
            info = {'supply': '100'} if address == MINT else {
                'tokenAmount': {'amount': amount}, 'owner': OWNER, 'mint': MINT}
            values.append({'data': {'parsed': {'info': info}}})
        return {'context': {'slot': self.slots[min(self.calls - 1, len(self.slots) - 1)]},
                'value': values}


def run(accounts=ACCOUNTS, *, p_slots=(7,), s_slots=(7,), **secondary_kwargs):
    order = []
    primary = Provider('primary', order, p_slots)
    secondary = Provider('secondary', order, s_slots, **secondary_kwargs)
    result = collect_independent_balance_check(MINT, accounts, primary, secondary,
                                               full_accounts=True, clock=lambda: 1)
    return result, primary, secondary, order


def test_all_supplied_addresses_are_paired_in_protocol_sized_batches():
    result, primary, secondary, order = run()
    assert result['status'] == 'SAME_SLOT_ALL_MATCH'
    assert result['provided_account_set_compared'] is True
    assert result['requested_addresses'] == result['accounts_compared'] == 206
    assert result['not_compared'] == 0 and result['matches'] == 206
    assert result['batches_completed'] == 21 and result['secondary_wire_attempts'] == 21
    assert [len(r) for r in primary.requests] == [10]*20+[6]
    assert primary.requests == secondary.requests
    assert [name for name, _ in order] == ['primary', 'secondary'] * 21
    assert [r['address'] for r in result['rows']] == [MINT] + ACCOUNTS
    assert result['scope'].endswith('NOT_INDEPENDENT_ENUMERATION')


def test_matching_per_batch_slots_do_not_claim_one_global_snapshot():
    result, _, _, _ = run(p_slots=(7, 8, 9), s_slots=(7, 8, 9))
    assert result['status'] == 'NEAR_TIME_ALL_MATCH'
    assert result['single_common_slot'] is False
    assert result['primary_slot_range'] == result['secondary_slot_range'] == [7, 9]
    assert [b['slot_gap'] for b in result['batches']] == [0]*21


def test_cross_provider_slot_difference_never_claims_same_snapshot():
    result, _, _, _ = run(p_slots=(7,), s_slots=(8,))
    assert result['status'] == 'NEAR_TIME_ALL_MATCH' and result['slot_gap'] == 1
    assert result['single_common_slot'] is False


def test_later_secondary_failure_preserves_completed_rows_and_exact_remainder():
    secret = 'https://private.invalid/KEY?token=SECRET'
    result, primary, secondary, _ = run(fail=(2, RPCError(secret)))
    assert result['status'] == 'PARTIAL' and result['reason'] == 'RPCError'
    assert result['failure_phase'] == 'SECONDARY' and result['failed_batch'] == 1
    assert result['batches_completed'] == 1 and result['accounts_compared'] == 10
    assert result['matches'] == 10 and result['not_compared'] == 196
    assert len(result['rows']) == 10 and len(result['batches']) == 1
    assert result['provided_account_set_compared'] is False
    assert result['secondary_wire_attempts'] == 2 and result['last_source_error'] == 'HTTP_403'
    assert primary.calls == secondary.calls == 2
    assert 'SECRET' not in json.dumps(result) and 'private.invalid' not in json.dumps(result)


def test_primary_failure_on_later_batch_keeps_existing_secondary_evidence():
    order = []
    primary = Provider('primary', order, fail=(2, TimeoutError('PRIVATE')))
    secondary = Provider('secondary', order)
    result = collect_independent_balance_check(MINT, ACCOUNTS, primary, secondary, full_accounts=True)
    assert result['status'] == 'PARTIAL' and result['reason'] == 'TimeoutError'
    assert result['failure_phase'] == 'PRIMARY' and result['batches_completed'] == 1
    assert result['secondary_wire_attempts'] == secondary.calls == 1
    assert result['accounts_compared'] == 10 and result['not_compared'] == 196
    assert 'PRIVATE' not in json.dumps(result)


@pytest.mark.parametrize('error', [RPCJobBudgetExceeded('RPC_JOB_WIRE_BUDGET_EXHAUSTED'),
    CheckpointError('CA_CHECKPOINT_READ_SEQUENCE_CHANGED')])
def test_primary_hard_failures_propagate_after_a_completed_batch(error):
    order = []
    primary = Provider('primary', order, fail=(2, error))
    secondary = Provider('secondary', order)
    with pytest.raises(type(error), match=str(error)):
        collect_independent_balance_check(MINT, ACCOUNTS, primary, secondary, full_accounts=True)
    assert secondary.calls == 1


def test_secondary_checkpoint_failure_is_never_a_soft_partial_result():
    with pytest.raises(CheckpointError, match='CA_CHECKPOINT_STORAGE_UNAVAILABLE'):
        run(fail=(2, CheckpointError('CA_CHECKPOINT_STORAGE_UNAVAILABLE')))


def test_unmatched_tail_account_is_not_hidden_by_first_thirty_matches():
    result, _, _, _ = run(changed=(ACCOUNTS[-1],))
    assert result['status'] == 'SAME_SLOT_MISMATCH' and result['differences'] == 1
    assert result['matches'] == 205 and result['rows'][-1]['difference_raw'] == '1'


def test_missing_tail_account_does_not_claim_all_match():
    result, _, _, _ = run(missing=(ACCOUNTS[-1],))
    assert result['status'] == 'SAME_SLOT_MISMATCH' and result['missing'] == 1
    assert result['rows'][-1]['status'] == 'MISSING'


def test_duplicate_input_and_mint_are_compared_once():
    result, primary, secondary, _ = run(accounts=[MINT, *ACCOUNTS, *ACCOUNTS])
    assert result['requested_addresses'] == result['accounts_compared'] == 206
    assert sum(map(len, primary.requests)) == sum(map(len, secondary.requests)) == 206
    assert len({r['address'] for r in result['rows']}) == 206


def test_legacy_default_remains_thirty_accounts_and_one_mint():
    order = []
    primary, secondary = Provider('primary', order), Provider('secondary', order)
    result = collect_independent_balance_check(MINT, ACCOUNTS, primary, secondary)
    assert result['accounts_compared'] == 31
    assert len(primary.requests) == len(secondary.requests) == 1


def test_invalid_supplied_address_fails_without_silent_full_set_claim():
    result, primary, secondary, _ = run(accounts=[ACCOUNTS[0], 'INVALID_ADDRESS'])
    assert result['status'] == 'UNAVAILABLE' and result['reason'] == 'INVALID_ACCOUNT_ADDRESS'
    assert result['invalid_addresses'] == 1 and result['provided_account_set_compared'] is False
    assert primary.calls == secondary.calls == 0


def test_disabled_secondary_does_not_start_primary_batching():
    primary = Provider('primary', [])
    result = collect_independent_balance_check(MINT, ACCOUNTS, primary, None, full_accounts=True)
    assert result['status'] == 'NOT_REQUESTED' and primary.calls == 0


def test_secondary_factory_starts_once_after_first_primary_batch():
    order = []
    primary = Provider('primary', order)
    secondary = Provider('secondary', order)
    def factory():
        order.append(('factory', []))
        return secondary
    result = collect_independent_balance_check(MINT, ACCOUNTS, primary, factory, full_accounts=True)
    assert result['batches_completed'] == 21
    assert [name for name, _ in order] == ['primary', 'factory', 'secondary'] + ['primary','secondary']*20
