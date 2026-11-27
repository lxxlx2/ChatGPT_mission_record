"""Local, deterministic tests for lightweight holder evidence identity."""
import unittest

from mission_agent.meme.holder_ranks import LEGACY_TOKEN_PROGRAM, TOKEN_2022_PROGRAM, _b58
from mission_agent.meme.independent_check import collect_independent_balance_check

MINT = 'So11111111111111111111111111111111111111112'
ACCOUNT = _b58((31).to_bytes(32, 'big'))
OWNER = _b58((32).to_bytes(32, 'big'))
OTHER_MINT = _b58((33).to_bytes(32, 'big'))


class Provider:
    def __init__(self, *, damage=None, slot=7):
        self.damage = damage
        self.slot = slot
        self.calls = 0

    def call(self, method, params):
        self.calls += 1
        assert method == 'getMultipleAccounts'
        assert params == [[MINT, ACCOUNT], {'encoding': 'jsonParsed', 'commitment': 'finalized'}]
        mint = {'owner': LEGACY_TOKEN_PROGRAM, 'executable': False, 'data': {'parsed': {
            'type': 'mint', 'info': {'supply': '100', 'decimals': 6, 'isInitialized': True}}}}
        row = {'owner': LEGACY_TOKEN_PROGRAM, 'executable': False, 'data': {'parsed': {
            'type': 'account', 'info': {'mint': MINT, 'owner': OWNER, 'state': 'initialized',
                                        'tokenAmount': {'amount': '60', 'decimals': 6}}}}}
        values = [mint, row]
        result = {'value': values, 'context': {'slot': self.slot}}
        if self.damage:
            self.damage(result, mint, row, row['data']['parsed']['info'])
        return result


class SampleIdentityTest(unittest.TestCase):
    def test_valid_exact_mint_and_account_still_match_at_one_slot(self):
        p, s = Provider(), Provider()
        result = collect_independent_balance_check(MINT, [ACCOUNT], p, s)
        self.assertEqual(result['status'], 'SAME_SLOT_ALL_MATCH')
        self.assertEqual(result['matches'], 2)
        self.assertEqual(p.calls, 1)
        self.assertEqual(s.calls, 1)

    def test_matching_invalid_providers_are_not_verified(self):
        damages = {
            'wrong_mint': lambda r, m, a, i: i.update(mint=OTHER_MINT),
            'bad_owner': lambda r, m, a, i: i.update(owner='not a key'),
            'wrong_kind': lambda r, m, a, i: a['data']['parsed'].update(type='mint'),
            'non_token_program': lambda r, m, a, i: a.update(owner=OWNER),
            'mixed_token_program': lambda r, m, a, i: a.update(owner=TOKEN_2022_PROGRAM),
            'different_decimals': lambda r, m, a, i: i['tokenAmount'].update(decimals=5),
            'integer_not_raw_string': lambda r, m, a, i: i['tokenAmount'].update(amount=60),
            'uninitialized': lambda r, m, a, i: i.update(state='uninitialized'),
            'mint_uninitialized': lambda r, m, a, i: m['data']['parsed']['info'].update(isInitialized=False),
            'non_object_envelope': lambda r, m, a, i: r.update(context=[]),
        }
        for name, damage in damages.items():
            with self.subTest(name=name):
                p, s = Provider(damage=damage), Provider(damage=damage)
                result = collect_independent_balance_check(MINT, [ACCOUNT], p, s)
                self.assertEqual((result['status'], result.get('reason')), ('UNAVAILABLE', 'RESPONSE_INVALID'))
                self.assertEqual(s.calls, 0)

    def test_secondary_wrong_mint_is_unavailable_not_just_a_balance_difference(self):
        p, s = Provider(), Provider(damage=lambda r, m, a, i: i.update(mint=OTHER_MINT))
        result = collect_independent_balance_check(MINT, [ACCOUNT], p, s)
        self.assertEqual((result['status'], result.get('reason')), ('UNAVAILABLE', 'RESPONSE_INVALID'))
        self.assertEqual((p.calls, s.calls), (1, 1))

    def test_missing_mint_or_token_row_is_not_evidence_of_match(self):
        for index in [0, 1]:
            with self.subTest(index=index):
                result = collect_independent_balance_check(
                    MINT, [ACCOUNT], Provider(),
                    Provider(damage=lambda r, m, a, i: r['value'].__setitem__(index, None)))
                self.assertEqual(result['status'], 'SAME_SLOT_MISMATCH')
                self.assertEqual(result['missing'], 1)

    def test_valid_secondary_balance_change_preserves_slot_scope(self):
        s = Provider(slot=8, damage=lambda r, m, a, i: i['tokenAmount'].update(amount='61'))
        result = collect_independent_balance_check(MINT, [ACCOUNT], Provider(), s)
        self.assertEqual(result['status'], 'NEAR_TIME_DIFFERENCES')
        self.assertEqual(result['rows'][1]['difference_raw'], '1')

    def test_invalid_requested_mint_never_reaches_provider(self):
        p, s = Provider(), Provider()
        result = collect_independent_balance_check('wrong mint', [], p, s)
        self.assertEqual(result.get('reason'), 'INVALID_MINT')
        self.assertEqual((p.calls, s.calls), (0, 0))


if __name__ == '__main__':
    unittest.main()
