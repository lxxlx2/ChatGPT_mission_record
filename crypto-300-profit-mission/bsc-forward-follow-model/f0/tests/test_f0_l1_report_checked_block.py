"""Offline regression for reported, verified block height; NO networking or permits."""
import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from f0_l1_code_probe import fixture_sender, probe
from test_f0_l1_code_probe import COHORT, REGISTRY, sequence


def replay(rows=None, sender=None):
    if sender is None:
        items = rows if rows is not None else sequence()['responses']
        sender = fixture_sender({'mode': 'OFFLINE_SYNTHETIC_ONLY', 'trial': True,
                                 'responses': items})
    return probe(sender, copy.deepcopy(COHORT), copy.deepcopy(REGISTRY),
                 sleep=lambda _: None)


class CheckedBlockReportTests(unittest.TestCase):
    def test_full_24_read_success_emits_exact_confirmed_height(self):
        r = replay()
        self.assertEqual((r['checked_block'], r['requested_height']), (100, 100))
        self.assertEqual((r['attempted_rpc_calls'], r['attempted_primary_getcode'],
                          r['attempted_router_getcode']), (24, 20, 2))
        self.assertEqual({x['checked_block'] for x in r['per_primary']}, {100})
        self.assertEqual(r['actual_rpc_calls'], 0)

    def test_wrong_chain_must_not_claim_internal_placeholder_as_checked_height(self):
        x = sequence()['responses']
        x[0]['result'] = '0x1'
        r = replay(rows=x)
        self.assertIsNone(r['checked_block'])
        self.assertEqual(r['stop_state'], 'BLOCKED_SOURCE')
        self.assertEqual(r['attempted_rpc_calls'], 1)
        self.assertEqual(r['actual_rpc_calls'], 0)

    def test_block_number_unavailable_must_keep_checked_height_null(self):
        x = sequence()['responses']
        x[1]['result'] = '0x0'
        r = replay(rows=x)
        self.assertIsNone(r['checked_block'])
        self.assertEqual(r['stop_state'], 'BLOCKED_SOURCE')
        self.assertEqual(r['attempted_rpc_calls'], 2)

    def test_partial_getcode_timeout_still_preserves_confirmed_height(self):
        def sender(endpoint, payload, cap):
            if payload['id'] == 1:
                return {'jsonrpc': '2.0', 'id': 1, 'result': '0x38'}
            if payload['id'] == 2:
                return {'jsonrpc': '2.0', 'id': 2, 'result': '0x64'}
            raise TimeoutError('synthetic timeout')
        r = replay(sender=sender)
        self.assertEqual(r['checked_block'], 100)
        self.assertEqual(r['stop_state'], 'BLOCKED_SOURCE')
        self.assertEqual(r['attempted_rpc_calls'], 5)
        self.assertEqual(r['saved_getcode_transport_failures'], 3)
        self.assertEqual(r['saved_getcode_not_checked'], 17)
        self.assertEqual(r['actual_rpc_calls'], 0)

    def test_saved_full_fixture_matches_new_report_field_exactly(self):
        fixture = json.loads((ROOT / 'fixtures/l1_code_probe_24_mock.json').read_text())
        r = replay(sender=fixture_sender(fixture))
        frozen = json.loads((ROOT / 'fixture_l1_code_probe_24_report.json').read_text())
        self.assertEqual(r, frozen)
        self.assertEqual(frozen['checked_block'], 100)
        self.assertEqual(frozen['actual_rpc_calls'], 0)


if __name__ == '__main__':
    unittest.main()
