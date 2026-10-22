"""Offline-only fake-RPC checks: no remote calls or background observer."""
import datetime as dt
import hashlib
import importlib.util
import json
import os
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


def block_hash(height):
    return '0x' + hashlib.sha256(('offline-block-' + str(height)).encode()).hexdigest()


A = block_hash(100)
B = block_hash(101)
P = block_hash(99)
TOKEN0 = '0x' + '1' * 40
TOKEN1 = '0x' + '2' * 40
PAIR = '0x' + '3' * 40


def padded(address):
    return '0x' + '0' * 24 + address[2:]


class FakeRPC:
    source_sha256 = 'd' * 64

    def __init__(self, *, first_height=100, second_height=101,
                 before=500, after=501, chain=56, changed_hash=False,
                 bad_pair=False, bad_token=False, broken_raw=False,
                 duplicate_pool=False, duplicate_tokens=False,
                 reversed_tokens=False, broken_parent_height=None,
                 short_count=False):
        self.first_height = first_height
        self.second_height = second_height
        self.before = before
        self.after = after
        self.chain = chain
        self.changed_hash = changed_hash
        self.bad_pair = bad_pair
        self.bad_token = bad_token
        self.broken_raw = broken_raw
        self.duplicate_pool = duplicate_pool
        self.duplicate_tokens = duplicate_tokens
        self.reversed_tokens = reversed_tokens
        self.broken_parent_height = broken_parent_height
        self.short_count = short_count
        self.calls = []
        self.head_reads = 0
        self.count_reads = 0
        self.first_header_reads = 0
        self.pool_offsets = {}

    def request(self, method, params):
        self.calls.append((method, params))
        if method == 'eth_chainId':
            value = hex(self.chain) if type(self.chain) is int else self.chain
        elif method == 'eth_blockNumber':
            self.head_reads += 1
            value = hex(self.first_height if self.head_reads == 1 else self.second_height)
        elif method == 'eth_getBlockByNumber':
            height = int(params[0], 16)
            h = block_hash(height)
            if height == self.first_height:
                self.first_header_reads += 1
                if self.changed_hash and self.first_header_reads >= 3:
                    h = '0x' + 'e' * 64
            parent = ('0x' + 'f' * 64 if height == self.broken_parent_height
                      else block_hash(height - 1))
            value = block(height, h, parent)
        elif method == 'eth_call':
            data = params[0]['data']
            if data == m.COUNT_SELECTOR:
                self.count_reads += 1
                count = self.before if self.count_reads == 1 else self.after
                value = hex(count) if self.short_count else '0x' + format(count, '064x')
            elif data.startswith(m.PAIRS_SELECTOR):
                offset = int(data[len(m.PAIRS_SELECTOR):], 16) - self.before
                pair = '0x' + format(int(PAIR, 16) + (0 if self.duplicate_pool else offset), '040x')
                self.pool_offsets[pair] = offset
                value = '0x' + '0' * 64 if self.bad_pair else padded(pair)
            elif data in (m.TOKEN0_SELECTOR, m.TOKEN1_SELECTOR):
                offset = self.pool_offsets[params[0]['to']]
                if self.duplicate_tokens:
                    offset = 0
                tokens = ('0x' + format(int(TOKEN0, 16) + offset, '040x'),
                          '0x' + format(int(TOKEN1, 16) + offset, '040x'))
                if self.reversed_tokens:
                    tokens = tuple(reversed(tokens))
                if self.bad_token:
                    tokens = (tokens[0], tokens[0])
                value = padded(tokens[0 if data == m.TOKEN0_SELECTOR else 1])
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
    def __init__(self, *, step_ms=1, utc_jump_at=None, utc_jump_seconds=0):
        self.tick = 0
        self.mono = 0
        self.step_ms = step_ms
        self.advance_ns = 0
        self.utc_jump_at = utc_jump_at
        self.utc_jump_seconds = utc_jump_seconds

    def now(self):
        self.tick += 1
        jump = (self.utc_jump_seconds if self.utc_jump_at is not None
                and self.tick >= self.utc_jump_at else 0)
        return dt.datetime(2026, 10, 22, tzinfo=dt.timezone.utc) + dt.timedelta(
            milliseconds=self.tick * self.step_ms,
            microseconds=self.advance_ns // 1000, seconds=jump)

    def monotonic(self):
        self.mono += self.step_ms * 1000000
        return self.mono + self.advance_ns

    def sleep(self, seconds):
        self.advance_ns += int(seconds * 1000000000)


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

    def test_slow_second_count_enforces_actual_three_second_window(self):
        rpc = FakeRPC()
        clk = Clock()
        original = rpc.request

        def delayed(method, params):
            result = original(method, params)
            if (method == 'eth_call' and params[0]['data'] == m.COUNT_SELECTOR
                    and rpc.count_reads == 2):
                clk.advance_ns += 8_000_000_000
            return result

        rpc.request = delayed
        with self.assertRaisesRegex(m.ForwardProbeError,
                                    'ACTUAL_SNAPSHOT_INTERVAL_EXCEEDS_3_SECONDS'):
            m.capture(rpc, self.dir, pause_seconds=0, clock=clk.now,
                      monotonic_ns=clk.monotonic, sleep=clk.sleep)
        self.assertFalse((self.dir / 'manifest.json').exists())
        failure = json.loads((self.dir / 'failure.json').read_text())
        self.assertEqual(failure['status'], 'UNUSABLE_NOT_PIT_EVIDENCE')

    def test_utc_rewind_between_calls_fails_closed(self):
        rpc = FakeRPC()
        clk = Clock(utc_jump_at=9, utc_jump_seconds=-4)
        with self.assertRaisesRegex(m.ForwardProbeError, 'LOCAL_CLOCK_REVERSED'):
            m.capture(rpc, self.dir, pause_seconds=0, clock=clk.now,
                      monotonic_ns=clk.monotonic, sleep=clk.sleep)
        self.assertFalse((self.dir / 'manifest.json').exists())

    def test_utc_jump_without_monotonic_jump_fails_closed(self):
        rpc = FakeRPC()
        clk = Clock(utc_jump_at=9, utc_jump_seconds=4)
        with self.assertRaisesRegex(m.ForwardProbeError,
                                    'LOCAL_CLOCK_MONOTONIC_DISAGREEMENT'):
            m.capture(rpc, self.dir, pause_seconds=0, clock=clk.now,
                      monotonic_ns=clk.monotonic, sleep=clk.sleep)
        self.assertFalse((self.dir / 'manifest.json').exists())

    def test_two_intermediate_ancestors_are_verified(self):
        result, rpc = run(self.dir, second_height=103)
        self.assertEqual([x['number'] for x in result['verified_intermediate_headers']],
                         [102, 101])
        self.assertEqual(result['new_factory_pair_index_count'], 1)
        self.assertEqual(result['unread_new_pair_count'], 0)
        self.assertEqual(len(rpc.calls), 16)
        self.assertFalse(result['p1_gate_passed'])

    def test_broken_intermediate_parent_fails_closed(self):
        with self.assertRaisesRegex(m.ForwardProbeError,
                                    'NONCONTIGUOUS_PARENT_HASH'):
            run(self.dir, second_height=103, broken_parent_height=102)
        self.assertFalse((self.dir / 'manifest.json').exists())
        self.assertTrue((self.dir / 'failure.json').is_file())

    def test_ancestor_depth_exhausting_request_budget_fails_closed(self):
        with self.assertRaisesRegex(m.ForwardProbeError,
                                    'ANCESTRY_EXCEEDS_RPC_BUDGET'):
            run(self.dir, second_height=112)
        self.assertFalse((self.dir / 'manifest.json').exists())
        self.assertTrue((self.dir / 'failure.json').is_file())

    def test_duplicate_pair_across_indices_fails_closed(self):
        with self.assertRaisesRegex(m.ForwardProbeError,
                                    'DUPLICATE_FACTORY_POOL_IDENTITY'):
            run(self.dir, after=502, duplicate_pool=True)
        self.assertFalse((self.dir / 'manifest.json').exists())

    def test_duplicate_token_pair_across_indices_fails_closed(self):
        with self.assertRaisesRegex(m.ForwardProbeError,
                                    'DUPLICATE_FACTORY_POOL_IDENTITY'):
            run(self.dir, after=502, duplicate_tokens=True)
        self.assertFalse((self.dir / 'manifest.json').exists())

    def test_reversed_pool_token_order_fails_closed(self):
        with self.assertRaisesRegex(m.ForwardProbeError,
                                    'POOL_TOKEN_ORDER_INVALID'):
            run(self.dir, reversed_tokens=True)
        self.assertFalse((self.dir / 'manifest.json').exists())

    def test_no_future_proof_from_timestamps(self):
        result, _ = run(self.dir)
        self.assertEqual(result['time_basis'],
                         'LOCAL_RESPONSE_COMPLETED_UTC_UPPER_BOUND_NOT_FIRST_PUBLIC_AVAILABLE_AT')
        self.assertEqual(result['reorg_finality'], 'NOT_PROVEN_FINALIZED')
        self.assertNotIn('PIT_VERIFIED', json.dumps(result))


if __name__ == '__main__':
    unittest.main()
