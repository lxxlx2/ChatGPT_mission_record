"""Offline-only fake-RPC checks: no remote calls or background observer."""
import datetime as dt
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

MODULE = (Path(__file__).resolve().parents[1] / 'mission_agent' /
          'early' / 'forward_observation.py')
spec = importlib.util.spec_from_file_location('monster_forward', MODULE)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def block(height, h, parent):
    return {'number': hex(height), 'hash': h, 'parentHash': parent,
            'timestamp': hex(1792600000 + height)}


A = '0x' + 'a' * 64
B = '0x' + 'b' * 64
P = '0x' + '1' * 64
TOKEN0 = '0x' + '1' * 40
TOKEN1 = '0x' + '2' * 40
PAIR = '0x' + '3' * 40


def padded(address):
    return '0x' + '0' * 24 + address[2:]


class FakeRPC:
    source_sha256 = 'd' * 64

    def __init__(self, *, first_height=100, second_height=101,
                 before=500, after=501, chain=56, changed_hash=False,
                 bad_pair=False, bad_token=False, broken_raw=False):
        self.first_height = first_height
        self.second_height = second_height
        self.before = before
        self.after = after
        self.chain = chain
        self.changed_hash = changed_hash
        self.bad_pair = bad_pair
        self.bad_token = bad_token
        self.broken_raw = broken_raw
        self.calls = []
        self.head_reads = 0
        self.count_reads = 0
        self.first_header_reads = 0

    def request(self, method, params):
        self.calls.append((method, params))
        if method == 'eth_chainId':
            value = hex(self.chain)
        elif method == 'eth_blockNumber':
            self.head_reads += 1
            value = hex(self.first_height if self.head_reads == 1 else self.second_height)
        elif method == 'eth_getBlockByNumber':
            height = int(params[0], 16)
            if height == self.first_height:
                self.first_header_reads += 1
                h = B if self.changed_hash and self.first_header_reads >= 3 else A
                value = block(height, h, P)
            else:
                value = block(height, B, A)
        elif method == 'eth_call':
            data = params[0]['data']
            if data == m.COUNT_SELECTOR:
                self.count_reads += 1
                value = hex(self.before if self.count_reads == 1 else self.after)
            elif data.startswith(m.PAIRS_SELECTOR):
                value = '0x' + '0' * 64 if self.bad_pair else padded(PAIR)
            elif data == m.TOKEN0_SELECTOR:
                value = padded(TOKEN0)
            elif data == m.TOKEN1_SELECTOR:
                value = padded(TOKEN0 if self.bad_token else TOKEN1)
            else:
                raise AssertionError('unexpected eth_call selector: ' + data)
        else:
            raise AssertionError('non-read-only RPC method')
        raw = json.dumps({'jsonrpc': '2.0', 'id': len(self.calls), 'result': value},
                         separators=(',', ':')).encode()
        if self.broken_raw:
            raw = b'{"result":"deliberately inconsistent"}'
        return value, raw


class Clock:
    def __init__(self):
        self.tick = 0
        self.mono = 0

    def now(self):
        self.tick += 1
        return dt.datetime(2026, 10, 22, tzinfo=dt.timezone.utc) + dt.timedelta(milliseconds=self.tick)

    def monotonic(self):
        self.mono += 1000000
        return self.mono


def run(root, **fake_overrides):
    rpc = FakeRPC(**fake_overrides)
    clk = Clock()
    result = m.capture(rpc, root, pause_seconds=0, clock=clk.now,
                       monotonic_ns=clk.monotonic, sleep=lambda _: None)
    return result, rpc


class ForwardObservationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name) / 'forward-one-shot'

    def test_positive_exact_two_snapshots_and_raw_hashes(self):
        result, rpc = run(self.dir)
        self.assertEqual(result['new_factory_pair_index_count'], 1)
        self.assertEqual(result['new_pairs_read'][0]['factory_index'], 500)
        self.assertEqual(result['new_pairs_read'][0]['pool'], PAIR)
        self.assertEqual(result['new_pairs_read'][0]['token0'], TOKEN0)
        self.assertEqual(result['new_pairs_read'][0]['token1'], TOKEN1)
        self.assertEqual(result['snapshots'][0]['block']['number'], 100)
        self.assertEqual(result['snapshots'][1]['block']['number'], 101)
        self.assertEqual(len(result['rpc_requests']), 14)
        self.assertFalse(result['p1_gate_passed'])
        self.assertFalse(result['trading_authorized'])
        self.assertEqual(result['p0_historical_2025_available_at'],
                         'UNKNOWN_NOT_RETROACTIVELY_RECONSTRUCTED')
        self.assertEqual(len(rpc.calls), 14)
        self.assertFalse(any('send' in method.lower() for method, _ in rpc.calls))
        disk = json.loads((self.dir / 'manifest.json').read_text())
        self.assertEqual(disk, result)
        for row in result['rpc_requests']:
            raw = (self.dir / row['raw_file']).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), row['raw_sha256'])
            self.assertGreaterEqual(row['elapsed_monotonic_ns'], 0)
            self.assertLessEqual(row['call_invoked_at_utc'],
                                 row['local_response_completed_at_utc'])
        self.assertFalse((self.dir / 'failure.json').exists())

    def test_zero_delta_not_market_empty(self):
        result, _ = run(self.dir, before=500, after=500)
        self.assertEqual(result['new_pairs_read'], [])
        self.assertEqual(result['unread_new_pair_count'], 0)
        self.assertTrue(result['interval_no_new_pair_is_not_full_market_zero'])

    def test_more_than_cap_is_partial_not_complete(self):
        result, rpc = run(self.dir, before=500, after=510)
        self.assertEqual(len(result['new_pairs_read']), 3)
        self.assertEqual(result['unread_new_pair_count'], 7)
        self.assertEqual(result['factory_index_identity_coverage'], 'PARTIAL')
        self.assertEqual(len(rpc.calls), 20)

    def test_wrong_chain_fails_and_preserves_error(self):
        with self.assertRaisesRegex(m.ForwardProbeError, 'NOT_BSC'):
            run(self.dir, chain=1)
        self.assertFalse((self.dir / 'manifest.json').exists())
        err = json.loads((self.dir / 'failure.json').read_text())
        self.assertEqual(err['status'], 'UNUSABLE_NOT_PIT_EVIDENCE')

    def test_same_height_count_disagreement_fails(self):
        with self.assertRaisesRegex(m.ForwardProbeError, 'SAME_HEIGHT'):
            run(self.dir, first_height=100, second_height=100,
                before=500, after=501)

    def test_head_regression_fails(self):
        with self.assertRaisesRegex(m.ForwardProbeError, 'HEAD_MOVED_BACKWARDS'):
            run(self.dir, first_height=101, second_height=100)

    def test_counter_regression_fails(self):
        with self.assertRaisesRegex(m.ForwardProbeError, 'FACTORY_COUNTER_DECREASED'):
            run(self.dir, before=510, after=500)

    def test_reorg_first_anchor_fails(self):
        with self.assertRaisesRegex(m.ForwardProbeError, 'FIRST_ANCHOR_CHANGED'):
            run(self.dir, changed_hash=True)

    def test_zero_pair_address_fails(self):
        with self.assertRaisesRegex(m.ForwardProbeError, 'ZERO_PAIR'):
            run(self.dir, bad_pair=True)

    def test_duplicate_token_pair_rejected(self):
        with self.assertRaisesRegex(m.ForwardProbeError, 'POOL_IDENTICAL'):
            run(self.dir, bad_token=True)

    def test_raw_must_exactly_replay_parsed_rpc(self):
        with self.assertRaisesRegex(m.ForwardProbeError, 'ORIGINAL_RPC_RESULT'):
            run(self.dir, broken_raw=True)
        self.assertFalse((self.dir / 'manifest.json').exists())

    def test_existing_output_directory_never_overwritten(self):
        run(self.dir)
        original = (self.dir / 'manifest.json').read_bytes()
        with self.assertRaisesRegex(m.ForwardProbeError, 'OUTPUT_DIRECTORY_MUST_NOT_EXIST'):
            run(self.dir)
        self.assertEqual((self.dir / 'manifest.json').read_bytes(), original)

    def test_pause_limit(self):
        with self.assertRaisesRegex(m.ForwardProbeError, 'PAUSE_OUT_OF_BOUNDS'):
            m.capture(FakeRPC(), self.dir, pause_seconds=60)
        self.assertFalse(self.dir.exists())

    def test_address_padded_required(self):
        with self.assertRaisesRegex(m.ForwardProbeError, 'BAD_ETH_CALL_ADDRESS_PADDING'):
            m.word_address('0x' + 'f' * 64)

    def test_no_future_proof_from_timestamps(self):
        result, _ = run(self.dir)
        self.assertEqual(result['time_basis'],
                         'LOCAL_RESPONSE_COMPLETED_UTC_UPPER_BOUND_NOT_FIRST_PUBLIC_AVAILABLE_AT')
        self.assertEqual(result['reorg_finality'], 'NOT_PROVEN_FINALIZED')
        self.assertNotIn('PIT_VERIFIED', json.dumps(result))


if __name__ == '__main__':
    unittest.main()
