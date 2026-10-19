"""F0 saved getCode EOA readiness and official Router provenance. No network calls."""
import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from f0_l1_preflight import (SCHEMA, audit_offline, audit_frozen_raw,
                             official_router_addresses)
from f0_l1_window import FROZEN_PR116_BLOB, git_blob_sha1

REGISTRY = json.loads((ROOT / 'F0_ROUTER_SOURCE_CANDIDATES.json').read_text())
COHORT = json.loads((ROOT / 'fixtures/l1_fake_cohort.json').read_text())
WATCH = [r['wallet'] for r in COHORT['preliminary_wallets'] if r['role'] == 'PRIMARY']
HEIGHT = 128614660


def envelope(wallet, *, code='0x', height=HEIGHT, id=1):
    return {'wallet': wallet, 'method': 'eth_getCode', 'params': [wallet, hex(height)],
            'chain_id': 56, 'id': id,
            'rpc': {'jsonrpc': '2.0', 'id': id, 'result': code}}


def snapshot(observations=()):
    return {'schema': SCHEMA, 'mode': 'OFFLINE_SYNTHETIC_ONLY', 'chain_id': 56,
            'store_raw_payloads': False, 'checked_block': HEIGHT,
            'actual_rpc_calls': 0, 'observations': list(observations)}


def run(obs=(), registry=None, snap=None, cohort=None):
    return audit_offline(copy.deepcopy(cohort or COHORT),
                         copy.deepcopy(snap or snapshot(obs)),
                         copy.deepcopy(registry or REGISTRY))


class SourcePreflightTests(unittest.TestCase):
    def test_exact_official_documented_router_registry(self):
        addresses = official_router_addresses(REGISTRY)
        self.assertEqual(len(addresses), 2)
        self.assertIn('0xd9c500dff816a1da21a48a732d3498bf09dc9aeb', addresses)
        self.assertIn('0x1a0a18ac4becddbd6389559687d1a73d8927e416', addresses)

    def test_readiness_without_any_rpc_is_explicitly_unverified(self):
        r = run()
        self.assertEqual((r['primary_count'], r['counts']['NOT_CHECKED']), (20, 20))
        self.assertEqual(r['stop_state'], 'NO_RUN')
        self.assertFalse(r['live_watchlist_enabled'])
        self.assertFalse(r['live_control_enabled'])
        self.assertEqual(r['actual_rpc_calls'], 0)
        self.assertEqual(r['real_technical_eoa_eligibility'], 'NOT_ESTABLISHED')

    def test_saved_no_code_does_not_grant_real_eoa_identity(self):
        r = run([envelope(WATCH[0])])
        self.assertEqual(r['counts']['NO_CODE_AT_SAMPLED_BLOCK'], 1)
        first = next(x for x in r['per_primary'] if x['wallet'] == WATCH[0])
        self.assertFalse(first['real_eoa_attested'])
        self.assertFalse(first['wallet_live_eligible'])
        self.assertEqual(first['checked_block'], HEIGHT)

    def test_saved_nonempty_code_is_not_an_eoa_candidate(self):
        r = run([envelope(WATCH[1], code='0x60806040')])
        self.assertEqual(r['counts']['HAS_RUNTIME_CODE_AT_SAMPLED_BLOCK'], 1)
        self.assertEqual(r['counts']['NOT_CHECKED'], 19)
        self.assertFalse(r['live_watchlist_enabled'])

    def test_documented_router_addresses_do_not_enable_live_control(self):
        r = run([envelope(WATCH[0])])
        self.assertEqual(len(r['router_documented_candidates']), 2)
        self.assertFalse(r['router_onchain_code_verified'])
        self.assertFalse(r['router_swap_causality_verified'])
        self.assertFalse(r['live_control_enabled'])

    def test_reject_router_address_substitution(self):
        v = copy.deepcopy(REGISTRY)
        v['routers'][0]['address'] = '0x' + '1' * 40
        with self.assertRaisesRegex(ValueError, 'ROUTER_SOURCE_OR_ADDRESS_MISMATCH'):
            run(registry=v)

    def test_reject_router_approval_assertion(self):
        v = copy.deepcopy(REGISTRY)
        v['control_eligible'] = True
        with self.assertRaisesRegex(ValueError, 'ROUTER_PREMATURE_APPROVAL'):
            run(registry=v)

    def test_reject_contract_check_pretended_in_official_registry(self):
        v = copy.deepcopy(REGISTRY)
        v['routers'][0]['onchain_runtime_code_check'] = 'VERIFIED'
        with self.assertRaisesRegex(ValueError, 'ROUTER_SOURCE_OR_ADDRESS_MISMATCH'):
            run(registry=v)

    def test_reject_extra_or_duplicate_code_observation(self):
        outsider = '0x' + 'ff' * 20
        with self.assertRaisesRegex(ValueError, 'CODE_OUTSIDE_FROZEN_PRIMARY_OR_DUPLICATE'):
            run([envelope(outsider)])
        with self.assertRaisesRegex(ValueError, 'CODE_OUTSIDE_FROZEN_PRIMARY_OR_DUPLICATE'):
            run([envelope(WATCH[0]), envelope(WATCH[0], id=2)])

    def test_reject_wrong_block_or_chain(self):
        with self.assertRaisesRegex(ValueError, 'CODE_REQUEST_IDENTITY_MISMATCH'):
            run([envelope(WATCH[0], height=HEIGHT+1)])
        a = envelope(WATCH[0])
        a['chain_id'] = 97
        with self.assertRaisesRegex(ValueError, 'CODE_REQUEST_IDENTITY_MISMATCH'):
            run([a])

    def test_saved_rpc_error_counted_without_wallet_approval(self):
        x = envelope(WATCH[0]); x['rpc'] = {
            'jsonrpc': '2.0', 'id': 1,
            'error': {'code': -32000, 'message': 'fake PRIVATE_KEY_123'}}
        r = run([x])
        self.assertEqual(r['counts']['RPC_ERROR_AT_SAMPLED_BLOCK'], 1)
        self.assertEqual(r['counts']['NOT_CHECKED'], 19)
        self.assertEqual(r['saved_getcode_attempts'], 1)
        self.assertEqual(r['saved_getcode_rpc_errors'], 1)
        self.assertEqual(r['saved_getcode_success_responses'], 0)
        self.assertEqual(r['saved_attempts_provider_billed'], 'UNVERIFIED')
        self.assertFalse(r['per_primary'][0]['wallet_live_eligible'])
        self.assertNotIn('PRIVATE_KEY_123', json.dumps(r))

    def test_reject_rpc_error_wrong_id_even_if_valid_error(self):
        x = envelope(WATCH[0]); x['rpc']['id'] = 999
        x['rpc']['error'] = {'code': -32000, 'message': 'bad'}
        with self.assertRaisesRegex(ValueError, 'CODE_RESPONSE_IDENTITY_MISMATCH'):
            run([x])

    def test_transport_attempt_counted_separately_from_never_checked(self):
        x = envelope(WATCH[0])
        x['rpc'] = None
        x['attempted'] = True
        x['transport_error_code'] = 'NETWORK_TIMEOUT'
        r = run([x])
        self.assertEqual(r['saved_getcode_attempts'], 1)
        self.assertEqual(r['saved_getcode_transport_failures'], 1)
        self.assertEqual(r['saved_getcode_rpc_errors'], 0)
        self.assertEqual(r['saved_getcode_not_checked'], 19)
        row = next(t for t in r['per_primary'] if t['wallet'] == WATCH[0])
        self.assertEqual(row['observed_code_state'], 'TRANSPORT_FAILED_AT_SAMPLED_BLOCK')
        self.assertIsNone(row['response_sha256'])
        self.assertFalse(row['real_eoa_attested'])
        self.assertEqual(r['actual_rpc_calls'], 0)

    def test_mixed_failure_code_and_unchecked_preserves_20_denominator(self):
        error = envelope(WATCH[0])
        error['rpc'] = {'jsonrpc': '2.0', 'id': 1, 'error': {'code': -32603}}
        timeout = envelope(WATCH[1], id=2)
        timeout.update({'rpc': None, 'attempted': True,
                        'transport_error_code': 'NETWORK_ERROR'})
        no_code = envelope(WATCH[2], id=3)
        contract = envelope(WATCH[3], id=4, code='0x6000')
        report = run([error, timeout, no_code, contract])
        self.assertEqual(report['saved_getcode_attempts'], 4)
        self.assertEqual(report['saved_getcode_rpc_errors'], 1)
        self.assertEqual(report['saved_getcode_transport_failures'], 1)
        self.assertEqual(report['saved_getcode_success_responses'], 2)
        self.assertEqual(report['saved_getcode_not_checked'], 16)
        self.assertEqual(sum(report['counts'].values()), 20)
        self.assertFalse(report['live_watchlist_enabled'])

    def test_unknown_or_missing_transport_attempt_rejected(self):
        x = envelope(WATCH[0])
        x.update({'rpc': None, 'attempted': True,
                  'transport_error_code': 'SECRET_EXFIL_ERROR'})
        with self.assertRaisesRegex(ValueError, 'TRANSPORT_FAILURE_INVALID'):
            run([x])
        x['transport_error_code'] = 'NETWORK_TIMEOUT'
        x.pop('attempted')
        with self.assertRaisesRegex(ValueError, 'TRANSPORT_FAILURE_INVALID'):
            run([x])

    def test_wrong_chain_height_request_even_in_transport_failure(self):
        x = envelope(WATCH[0], height=HEIGHT+1)
        x.update({'rpc': None, 'attempted': True,
                  'transport_error_code': 'NETWORK_TIMEOUT'})
        with self.assertRaisesRegex(ValueError, 'CODE_REQUEST_IDENTITY_MISMATCH'):
            run([x])

    def test_rpc_error_with_result_rejected_as_ambiguous(self):
        x = envelope(WATCH[0])
        x['rpc']['error'] = {'code': -32000}
        with self.assertRaisesRegex(ValueError, 'MALFORMED_RPC_ERROR_ENVELOPE'):
            run([x])

    def test_invalid_error_envelope_rejected(self):
        x = envelope(WATCH[0])
        x['rpc'] = {'jsonrpc': '2.0', 'id': 1, 'error': {'code': True}}
        with self.assertRaisesRegex(ValueError, 'MALFORMED_RPC_ERROR_ENVELOPE'):
            run([x])

    def test_no_error_rows_no_new_network_in_success_report(self):
        r = run([envelope(WATCH[0]), envelope(WATCH[1], id=2, code='0x6000')])
        self.assertEqual(r['saved_getcode_attempts'], 2)
        self.assertEqual(r['saved_getcode_success_responses'], 2)
        self.assertEqual(r['saved_getcode_rpc_errors'], 0)
        self.assertEqual(r['saved_getcode_transport_failures'], 0)
        self.assertEqual(r['actual_rpc_calls'], 0)
        self.assertEqual(r['stop_state'], 'NO_RUN')

    def test_reject_bad_hex_result(self):
        with self.assertRaisesRegex(ValueError, 'INVALID_RETURNED_CODE_HEX'):
            run([envelope(WATCH[0], code='0x0')])
        with self.assertRaisesRegex(ValueError, 'INVALID_RETURNED_CODE_HEX'):
            run([envelope(WATCH[0], code='0xzz')])

    def test_reject_live_count_or_permission_flag(self):
        f = snapshot()
        f['actual_rpc_calls']=1
        with self.assertRaisesRegex(ValueError, 'LIVE_NETWORK_CLAIM_FORBIDDEN'):
            run(snap=f)
        f = snapshot(); f['user_authorized']=True
        with self.assertRaisesRegex(ValueError, 'LIVE_NETWORK_CLAIM_FORBIDDEN'):
            run(snap=f)

    def test_reject_changed_frozen_manifest_blob(self):
        fake = json.dumps(COHORT).encode()
        self.assertNotEqual(git_blob_sha1(fake), FROZEN_PR116_BLOB)
        with self.assertRaisesRegex(ValueError, 'FROZEN_COHORT_GIT_BLOB_MISMATCH'):
            audit_frozen_raw(fake, snapshot(), REGISTRY)

    @unittest.skipUnless((ROOT/'F0_COHORT_PRESELECTION.json').is_file(),
                         'Actual PR116 manifest is included only in full Git checkout')
    def test_actual_frozen_pr116_20_primary_report_all_unverified(self):
        raw = (ROOT/'F0_COHORT_PRESELECTION.json').read_bytes()
        self.assertEqual(git_blob_sha1(raw), FROZEN_PR116_BLOB)
        result = audit_frozen_raw(raw, snapshot(), REGISTRY)
        self.assertEqual(result['primary_count'], 20)
        self.assertEqual(result['counts']['NOT_CHECKED'], 20)
        self.assertEqual(result['cohort_source'], 'VERIFIED_PR116_BLOB_OFFLINE')
        self.assertFalse(result['live_watchlist_enabled'])


if __name__ == '__main__':
    unittest.main()
