"""Offline-only fake-RPC checks: no remote calls or background observer."""
import datetime as dt
import hashlib
import http.client
import io
from email.message import Message
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

    def request_batch(self, jobs):
        results, packets = [], []
        for method, params in jobs:
            value, raw = self.request(method, params)
            results.append(value)
            packets.append(json.loads(raw))
        return results, json.dumps(packets, separators=(',', ':')).encode()

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



class BoundedForwardObservationTests(unittest.TestCase):
    """New finite-mode tests; old two-snapshot contract remains unchanged."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name) / 'bounded'

    def bounded(self, *, rpc=None, clock=None, budget=55, duration=36):
        rpc = rpc or FakeRPC()
        clock = clock or Clock()
        return m.capture_bounded(
            rpc, self.dir, duration_seconds=duration,
            poll_seconds=m.BOUNDED_POLL_SECONDS, rpc_budget=budget,
            clock=clock.now, monotonic_ns=clock.monotonic, sleep=clock.sleep)

    def test_real_new_pair_across_snapshots_and_original_raw(self):
        result = self.bounded()
        self.assertEqual(result['schema'], 'MONSTER_FORWARD_BSC_V2_MANUAL_BOUNDED_V1')
        self.assertGreaterEqual(len(result['snapshots']), 2)
        self.assertEqual(result['new_factory_pair_index_count'], 1)
        self.assertEqual(len(result['new_pairs_read']), 1)
        self.assertEqual(result['new_pairs_read'][0]['pool'], PAIR)
        self.assertEqual(result['unread_new_pair_count'], 0)
        self.assertFalse(result['p1_gate_passed'])
        self.assertFalse(result['trading_authorized'])
        self.assertIn(result['stop_reason'], ('DURATION_LIMIT', 'RPC_BUDGET_SAFETY_RESERVE'))
        self.assertLessEqual(result['rpc_attempt_count'], 55)
        self.assertEqual(json.loads((self.dir/'manifest.json').read_text()), result)
        for row in result['rpc_requests']:
            self.assertIn(row['method'], m.READ_METHODS)
            original = (self.dir/row['raw_file']).read_bytes()
            self.assertEqual(hashlib.sha256(original).hexdigest(), row['raw_sha256'])
            self.assertEqual(len(original), row['raw_bytes'])
            self.assertEqual(row['ordinal'], json.loads(original)['id'])
        self.assertFalse((self.dir/'failure.json').exists())

    def test_450ms_chain_requires_short_polls_not_twelve_seconds(self):
        clk = Clock()
        class FastChainRPC(FakeRPC):
            def request(self, method, params):
                if method == 'eth_blockNumber':
                    self.second_height = (
                        self.first_height + clk.advance_ns // 450_000_000)
                return super().request(method, params)
        rpc = FastChainRPC()
        result = self.bounded(rpc=rpc, clock=clk, duration=22, budget=130)
        self.assertEqual(m.BOUNDED_POLL_SECONDS, 5)
        self.assertGreaterEqual(len(result['verified_intervals']), 2)
        self.assertTrue(all(
            1 <= part['to_block'] - part['from_block'] <=
            m.MAX_BOUNDED_ANCESTOR_BLOCKS
            for part in result['verified_intervals']))
        self.assertEqual(result['new_factory_pair_index_count'], 1)
        self.assertEqual(len(result['new_pairs_read']), 1)

    def test_real_batch_transport_http_shape_and_reverse_id_order(self):
        class Response:
            status = 200
            def __init__(self, raw):
                self.raw = raw
                self.headers = Message()
                self.headers['Content-Length'] = str(len(raw))
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self, cap): return self.raw[:cap]

        class Opener:
            def __init__(self): self.requests = []
            def open(self, req, timeout):
                self.requests.append(req)
                payload = json.loads(req.data)
                self_ids = [p['id'] for p in payload]
                if self_ids != [1, 2]:
                    raise AssertionError('noncontiguous batched JSON-RPC IDs')
                children = []
                for row in reversed(payload):
                    height = int(row['params'][0], 16)
                    children.append({'jsonrpc': '2.0', 'id': row['id'],
                                     'result': block(height, block_hash(height),
                                                     block_hash(height-1))})
                return Response(json.dumps(children).encode())

        opener = Opener()
        rpc = m.ForwardRPC('https://bsc-dataseed.bnbchain.org',
                           max_requests=180, opener=opener)
        values, raw = rpc.request_batch([
            ('eth_getBlockByNumber', ['0x64', False]),
            ('eth_getBlockByNumber', ['0x65', False])])
        self.assertEqual(rpc.calls, 2)
        self.assertEqual(len(opener.requests), 1)
        self.assertEqual([int(v['number'], 16) for v in values], [100, 101])
        self.assertEqual([x['id'] for x in json.loads(raw)], [2, 1])
        self.assertEqual(values[1]['parentHash'], values[0]['hash'])

    def test_real_batch_transport_rejects_duplicate_child_id(self):
        class Response:
            status = 200
            def __init__(self, raw):
                self.raw = raw
                self.headers = Message()
                self.headers['Content-Length'] = str(len(raw))
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self, cap): return self.raw[:cap]

        class Opener:
            def open(self, req, timeout):
                inputs = json.loads(req.data)
                children = [{'jsonrpc':'2.0', 'id': inputs[0]['id'],
                             'result': block(100, block_hash(100), block_hash(99))}
                            for _ in inputs]
                return Response(json.dumps(children).encode())
        rpc = m.ForwardRPC('https://bsc-dataseed.bnbchain.org',
                           max_requests=180, opener=Opener())
        with self.assertRaisesRegex(m.ForwardProbeError,
                                    'BATCH_INVALID_MEMBER_OR_ID'):
            rpc.request_batch([('eth_getBlockByNumber', ['0x64', False]),
                               ('eth_getBlockByNumber', ['0x65', False])])
        self.assertEqual(rpc.calls, 2)

    def test_real_batch_transport_rejects_invalid_methods_or_size(self):
        rpc = m.ForwardRPC('https://bsc-dataseed.bnbchain.org',
                           max_requests=180)
        for jobs in ([],
                     [('eth_sendRawTransaction', ['0x12'])],
                     [('eth_getBlockByNumber', ['0x64', True])],
                     [('eth_getBlockByNumber', [hex(i), False]) for i in range(5)]):
            with self.subTest(jobs=jobs):
                with self.assertRaisesRegex(m.ForwardProbeError,
                                            'BATCH_INVALID_HEADER_JOB'):
                    rpc.request_batch(jobs)
        self.assertEqual(rpc.calls, 0)

    def test_batch_reduces_http_roundtrips_but_not_rpc_budget(self):
        rpc = FakeRPC(second_height=115)
        result = self.bounded(rpc=rpc, budget=115, duration=20)
        batch_receipts = [r for r in result['rpc_requests']
                          if 'batch_response_id' in r]
        self.assertGreater(len(batch_receipts), 8)
        self.assertEqual(result['rpc_attempt_count'], len(rpc.calls))
        self.assertEqual(result['rpc_attempt_count'], len(result['rpc_requests']))
        self.assertLess(result['http_response_file_count'],
                        result['rpc_attempt_count'])
        self.assertLessEqual(max(x['batch_subrequest_count']
                                 for x in batch_receipts), m.MAX_BATCH_HEADERS)
        self.assertTrue(result['verified_intervals'])
        files = {r['raw_file'] for r in batch_receipts}
        for name in files:
            raw = (self.dir/name).read_bytes()
            children = json.loads(raw)
            self.assertIsInstance(children, list)
            self.assertLessEqual(len(children), m.MAX_BATCH_HEADERS)
        self.assertEqual(result['new_factory_pair_index_count'], 1)

    def test_batch_reversed_response_order_is_valid(self):
        class ReverseRPC(FakeRPC):
            def request_batch(self, jobs):
                values, raw = super().request_batch(jobs)
                return values, json.dumps(list(reversed(json.loads(raw)))).encode()
        result = self.bounded(rpc=ReverseRPC(second_height=103))
        self.assertEqual(result['new_factory_pair_index_count'], 1)
        self.assertTrue(result['verified_intervals'])

    def test_batch_missing_child_rejected(self):
        class MissingRPC(FakeRPC):
            def request_batch(self, jobs):
                values, raw = super().request_batch(jobs)
                return values, json.dumps(json.loads(raw)[:-1]).encode()
        with self.assertRaisesRegex(m.ForwardProbeError,
                                    'BATCH_RESPONSE_SHAPE_INVALID'):
            self.bounded(rpc=MissingRPC(second_height=103))
        self.assertFalse((self.dir/'manifest.json').exists())
        self.assertTrue((self.dir/'failure.json').exists())

    def test_batch_duplicate_child_id_rejected(self):
        class DuplicateRPC(FakeRPC):
            def request_batch(self, jobs):
                values, raw = super().request_batch(jobs)
                children = json.loads(raw)
                children[1]['id'] = children[0]['id']
                return values, json.dumps(children).encode()
        with self.assertRaisesRegex(m.ForwardProbeError,
                                    'BATCH_INVALID_MEMBER_OR_ID'):
            self.bounded(rpc=DuplicateRPC(second_height=103))
        self.assertFalse((self.dir/'manifest.json').exists())

    def test_batch_child_error_rejected(self):
        class ErrorRPC(FakeRPC):
            def request_batch(self, jobs):
                values, raw = super().request_batch(jobs)
                children = json.loads(raw)
                children[0].pop('result')
                children[0]['error'] = {'code': -32000, 'message': 'provider error'}
                return values, json.dumps(children).encode()
        with self.assertRaisesRegex(m.ForwardProbeError,
                                    'BATCH_INVALID_MEMBER_OR_ID'):
            self.bounded(rpc=ErrorRPC(second_height=103))
        self.assertFalse((self.dir/'manifest.json').exists())

    def test_batch_wrong_child_result_rejected(self):
        class MutatedRPC(FakeRPC):
            def request_batch(self, jobs):
                values, raw = super().request_batch(jobs)
                children = json.loads(raw)
                children[0]['result']['hash'] = '0x'+'9'*64
                return values, json.dumps(children).encode()
        with self.assertRaisesRegex(m.ForwardProbeError,
                                    'BATCH_RESULT_NOT_VERIFIED'):
            self.bounded(rpc=MutatedRPC(second_height=103))
        self.assertFalse((self.dir/'manifest.json').exists())

    def test_slow_second_head_cannot_start_more_rpc_after_global_deadline(self):
        clk = Clock()
        class SlowHeadRPC(FakeRPC):
            def request(self, method, params):
                value = super().request(method, params)
                if method == 'eth_blockNumber' and self.head_reads == 2:
                    clk.advance_ns += 20_000_000_000
                return value
        rpc = SlowHeadRPC()
        with self.assertRaisesRegex(
                m.ForwardProbeError, 'BOUNDED_GLOBAL_DEADLINE_EXCEEDED'):
            self.bounded(rpc=rpc, clock=clk, duration=12)
        self.assertEqual(sum(method == 'eth_blockNumber'
                             for method, _ in rpc.calls), 2)
        self.assertFalse(any(method == 'eth_getBlockByNumber' and
                             params == [hex(rpc.second_height), False]
                             for method, params in rpc.calls))
        self.assertFalse((self.dir/'manifest.json').exists())
        self.assertTrue((self.dir/'failure.json').exists())

    def test_slow_batch_ancestry_cannot_initiate_post_deadline_anchor(self):
        clk = Clock()
        class SlowBatchRPC(FakeRPC):
            def request_batch(self, jobs):
                values, raw = super().request_batch(jobs)
                clk.advance_ns += 20_000_000_000
                return values, raw
        rpc = SlowBatchRPC(second_height=103)
        with self.assertRaisesRegex(
                m.ForwardProbeError, 'BOUNDED_GLOBAL_DEADLINE_EXCEEDED'):
            self.bounded(rpc=rpc, clock=clk, duration=12)
        self.assertEqual(sum(
            method == 'eth_getBlockByNumber' and params == [hex(103), False]
            for method, params in rpc.calls), 2)
        self.assertFalse((self.dir/'manifest.json').exists())
        self.assertTrue((self.dir/'failure.json').exists())


    def _run_rejected_http_batch(self, body, *, declared_length=None,
                                 chunked=False, status=200, http_error=False,
                                 raw_http_response=None,
                                 endpoint="https://bsc-dataseed.bnbchain.org"):
        """Offline real ForwardRPC HTTP-validation through a fake opener."""
        class Response:
            def __init__(self):
                self.status = status
                self.headers = Message()
                if declared_length is not None:
                    self.headers['Content-Length'] = str(declared_length)
                elif not chunked:
                    self.headers['Content-Length'] = str(len(body))
                if chunked:
                    self.headers['Transfer-Encoding'] = 'chunked'
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self, limit): return body[:limit]

        class OfflineSocket:
            def makefile(self, *args, **kwargs):
                return io.BytesIO(raw_http_response)

        class Opener:
            def open(self, req, timeout):
                if raw_http_response is not None:
                    response = http.client.HTTPResponse(OfflineSocket())
                    response.begin()
                    return response
                if http_error:
                    raise m.urllib.error.HTTPError(
                        endpoint, status, "offline failure", Message(),
                        io.BytesIO(body))
                return Response()

        class RPC(FakeRPC):
            def __init__(self):
                super().__init__(second_height=103)
                self.url = endpoint
                self.forward = m.ForwardRPC(
                    endpoint, min_interval=0, max_requests=180, opener=Opener())

            def request(self, method, params):
                result = super().request(method, params)
                self.forward.calls += 1
                return result

            def request_batch(self, jobs):
                self.calls.extend(jobs)
                return self.forward.request_batch(jobs)

        rpc = RPC()
        with self.assertRaises(m.ForwardProbeError) as caught:
            self.bounded(rpc=rpc)
        self.assertFalse((self.dir/'manifest.json').exists())
        self.assertTrue((self.dir/'failure.json').exists())
        self.assertEqual(rpc.forward.calls, len(rpc.calls))
        return caught.exception, json.loads((self.dir/'failure.json').read_text())

    def test_rejected_batch_transport_bytes_and_sha_are_private(self):
        cases = (
            (b'[{"jsonrpc":"2.0","id":12,"result":', None, False,
             'BATCH_INVALID_JSON'),
            (b'{"jsonrpc":"2.0","id":12,"error":{"code":-32000}}',
             None, False, 'BATCH_WRONG_RESPONSE_COUNT'),
            (b'[]', 25, False, 'BATCH_HTTP_BODY_TRUNCATED'),
            (b'[' + b'x' * m.MAX_RESPONSE_BYTES, None, True,
             'BATCH_RESPONSE_TOO_LARGE'),
            (b'{"jsonrpc":', None, True, 'BATCH_INVALID_JSON'),
            (b'[]', 'nonsense', False, 'BATCH_HTTP_FRAMING_INVALID'),
        )
        for i, (raw, declared, chunked, expected) in enumerate(cases):
            with self.subTest(case=i):
                self.dir = Path(self.tmp.name) / ('bad-batch-' + str(i))
                _, failure = self._run_rejected_http_batch(
                    raw, declared_length=declared, chunked=chunked)
                self.assertEqual(failure['reason'], expected)
                receipt = failure['rejected_response']
                self.assertEqual(receipt['privacy'], 'PRIVATE_RAW_SAVED')
                self.assertTrue(receipt['raw_file'].startswith('rejected-batch-'))
                saved = self.dir / receipt['raw_file']
                self.assertEqual(saved.read_bytes(), raw[:m.MAX_RESPONSE_BYTES])
                self.assertEqual(saved.stat().st_mode & 0o777, 0o600)
                self.assertEqual(receipt['raw_sha256'],
                                 hashlib.sha256(saved.read_bytes()).hexdigest())
                self.assertEqual(receipt['capture_truncated'],
                                 len(raw) > m.MAX_RESPONSE_BYTES)
                self.assertEqual(failure['rpc_attempt_count'],
                                 len(failure['completed_rpc_responses']) + 2)

    def test_rejected_non_200_batch_status_keeps_body_evidence(self):
        raw = b'{"error":"provider rejected the HTTP request"}'
        _, failure = self._run_rejected_http_batch(raw, status=503)
        self.assertEqual(failure['reason'], 'BATCH_HTTP_STATUS_NOT_200')
        receipt = failure['rejected_response']
        self.assertEqual(receipt['privacy'], 'PRIVATE_RAW_SAVED')
        self.assertEqual((self.dir/receipt['raw_file']).read_bytes(), raw)
        self.assertEqual(receipt['raw_sha256'], hashlib.sha256(raw).hexdigest())

    def test_rejected_batch_secret_echo_hash_only_without_raw(self):
        secret = 'SECRET_WITHHOLD_FORENSIC_TEST_123456'
        endpoint = 'https://bsc-dataseed.bnbchain.org/?key=' + secret
        raw = ('{"jsonrpc":"2.0","id":12,"note":"' + secret + '"}').encode()
        _, failure = self._run_rejected_http_batch(raw, endpoint=endpoint)
        self.assertEqual(failure['reason'], 'RPC_SECRET_ECHO_REJECTED')
        receipt = failure['rejected_response']
        self.assertEqual(receipt['privacy'], 'SECRET_WITHHELD_HASH_ONLY')
        self.assertIsNone(receipt['raw_file'])
        self.assertEqual(receipt['raw_sha256'], hashlib.sha256(raw).hexdigest())
        self.assertEqual(list(self.dir.glob('rejected-*')), [])
        self.assertNotIn(secret, (self.dir/'failure.json').read_text())

    def test_bounded_batch_verification_failure_archives_exact_raw(self):
        class MutatedRPC(FakeRPC):
            def request_batch(self, jobs):
                values, raw = super().request_batch(jobs)
                children = json.loads(raw)
                children[0]['result']['hash'] = '0x' + '8' * 64
                return values, json.dumps(children).encode()

        rpc = MutatedRPC(second_height=103)
        with self.assertRaisesRegex(
                m.ForwardProbeError, 'BATCH_RESULT_NOT_VERIFIED'):
            self.bounded(rpc=rpc)
        failure = json.loads((self.dir/'failure.json').read_text())
        receipt = failure['rejected_response']
        self.assertEqual(receipt['privacy'], 'PRIVATE_RAW_SAVED')
        raw = (self.dir/receipt['raw_file']).read_bytes()
        self.assertEqual(receipt['raw_sha256'], hashlib.sha256(raw).hexdigest())
        self.assertEqual(json.loads(raw)[0]['result']['hash'], '0x' + '8' * 64)

    def test_real_httpclient_chunked_truncation_keeps_partial_body(self):
        # Bytes are parsed by the stdlib HTTPResponse chunked decoder,
        # not simulated by a Response.read() method.
        partial = b'{"jsonrpc":"2.0","id":12,"result":{}'
        wire = (b'HTTP/1.1 200 OK\r\n'
                b'Transfer-Encoding: chunked\r\n'
                b'\r\n' + format(len(partial), 'x').encode() +
                b'\r\n' + partial + b'\r\n')
        _, failure = self._run_rejected_http_batch(
            b'', raw_http_response=wire)
        self.assertEqual(failure['reason'], 'RPC_NETWORK_UNAVAILABLE')
        receipt = failure['rejected_response']
        self.assertEqual(receipt['privacy'], 'PRIVATE_RAW_SAVED')
        self.assertFalse(receipt['capture_truncated'])
        self.assertEqual(receipt['raw_bytes'], len(partial))
        data = (self.dir/receipt['raw_file']).read_bytes()
        self.assertEqual(data, partial)
        self.assertEqual(receipt['raw_sha256'], hashlib.sha256(partial).hexdigest())
        self.assertEqual((self.dir/receipt['raw_file']).stat().st_mode & 0o777,
                         0o600)

    def test_real_httperror_503_keeps_actual_error_body(self):
        raw = b'{"error":"backend unavailable"}'
        _, failure = self._run_rejected_http_batch(
            raw, status=503, http_error=True)
        self.assertEqual(failure['reason'], 'RPC_HTTP_503')
        receipt = failure['rejected_response']
        self.assertEqual(receipt['privacy'], 'PRIVATE_RAW_SAVED')
        self.assertEqual((self.dir/receipt['raw_file']).read_bytes(), raw)
        self.assertEqual(receipt['raw_sha256'], hashlib.sha256(raw).hexdigest())

    def test_public_rpc_documentation_host_does_not_mask_evidence(self):
        raw = b'{"error":"see https://bsc-dataseed.bnbchain.org/docs"}'
        _, failure = self._run_rejected_http_batch(raw)
        self.assertEqual(failure['reason'], 'BATCH_WRONG_RESPONSE_COUNT')
        receipt = failure['rejected_response']
        self.assertEqual(receipt['privacy'], 'PRIVATE_RAW_SAVED')
        self.assertEqual((self.dir/receipt['raw_file']).read_bytes(), raw)

    def test_post_batch_header_failure_refs_last_completed_batch(self):
        rpc = FakeRPC(second_height=103, broken_parent_height=102)
        with self.assertRaisesRegex(
                m.ForwardProbeError, 'NONCONTIGUOUS_PARENT_HASH'):
            self.bounded(rpc=rpc)
        failure = json.loads((self.dir/'failure.json').read_text())
        self.assertEqual(failure['reason'], 'NONCONTIGUOUS_PARENT_HASH')
        self.assertNotIn('rejected_response', failure)
        receipt = failure['last_completed_batch_response']
        saved = self.dir / receipt['raw_file']
        self.assertTrue(saved.is_file())
        self.assertEqual(receipt['raw_sha256'],
                         hashlib.sha256(saved.read_bytes()).hexdigest())
        self.assertEqual(receipt['raw_bytes'], len(saved.read_bytes()))
        self.assertIn('batch_response_id', receipt)
        self.assertFalse((self.dir/'manifest.json').exists())

    def test_legacy_twelve_second_poll_rejected_as_unsafe(self):
        rpc = FakeRPC()
        with self.assertRaisesRegex(m.ForwardProbeError,
                                    'BOUNDED_CONTRACT_OUT_OF_RANGE'):
            m.capture_bounded(rpc, self.dir, duration_seconds=36,
                              poll_seconds=12, rpc_budget=55)
        self.assertFalse(self.dir.exists())

    def test_zero_delta_is_scoped_to_factory_only(self):
        result = self.bounded(rpc=FakeRPC(before=500, after=500))
        self.assertEqual(result['new_factory_pair_index_count'], 0)
        self.assertEqual(result['new_pairs_read'], [])
        self.assertEqual(result['unread_new_pair_count'], 0)
        self.assertTrue(result['zero_delta_does_not_imply_whole_market_zero'])

    def test_burst_keeps_all_missing_indices_as_explicit_denominator(self):
        result = self.bounded(rpc=FakeRPC(before=500, after=510))
        self.assertEqual(result['new_factory_pair_index_count'], 10)
        self.assertEqual(len(result['new_pairs_read']), 3)
        self.assertEqual(result['unread_new_pair_count'], 7)
        self.assertEqual(result['factory_index_identity_coverage'], 'PARTIAL')
        self.assertEqual(result['verified_intervals'][0]['unread_factory_index_start'], 503)
        self.assertEqual(result['verified_intervals'][0]['unread_factory_index_end_exclusive'], 510)
        self.assertEqual(result['verified_intervals'][0]['unread_count'], 7)

    def test_wrong_chain_writes_failure_without_manifest(self):
        with self.assertRaisesRegex(m.ForwardProbeError, 'NOT_BSC'):
            self.bounded(rpc=FakeRPC(chain=1))
        self.assertFalse((self.dir/'manifest.json').exists())
        reason = json.loads((self.dir/'failure.json').read_text())
        self.assertIn('NOT_BSC', reason['reason'])

    def test_long_gap_refused_instead_of_faking_contiguity(self):
        with self.assertRaisesRegex(m.ForwardProbeError, 'ANCESTRY_EXCEEDS_BOUNDED_DEPTH'):
            self.bounded(rpc=FakeRPC(second_height=135))
        self.assertFalse((self.dir/'manifest.json').exists())
        self.assertTrue((self.dir/'failure.json').exists())

    def test_failed_26_block_gap_retains_unverified_factory_plus_one(self):
        rpc = FakeRPC(second_height=126, before=500, after=501)
        with self.assertRaisesRegex(m.ForwardProbeError,
                                    'ANCESTRY_EXCEEDS_BOUNDED_DEPTH'):
            self.bounded(rpc=rpc)
        failure = json.loads((self.dir/'failure.json').read_text())
        interval = failure['uncommitted_counter_interval']
        self.assertEqual((interval['from_block'], interval['to_block']), (100, 126))
        self.assertEqual(interval['gap_blocks'], 26)
        self.assertEqual(interval['max_verified_gap_blocks'], 24)
        self.assertEqual((interval['factory_count_before'],
                          interval['factory_count_after']), (500, 501))
        self.assertEqual(interval['factory_counter_delta'], 1)
        self.assertEqual((interval['candidate_index_start'],
                          interval['candidate_index_end_exclusive']), (500, 501))
        self.assertEqual(interval['ancestry_and_pair_identity'], 'NOT_VERIFIED')
        self.assertEqual(interval['tradability_and_profit'], 'NOT_TESTED')
        self.assertNotIn('completed_verified_prefix_intervals', failure)
        self.assertFalse((self.dir/'manifest.json').exists())
        self.assertFalse(any(method == 'eth_call' and
                             params[0]['data'].startswith(m.PAIRS_SELECTOR)
                             for method, params in rpc.calls))
        for row in failure['completed_rpc_responses']:
            raw = (self.dir / row['raw_file']).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), row['raw_sha256'])

    def test_valid_prefix_survives_failure_without_upgrading_next_gap(self):
        class OneValidThenTooLong(FakeRPC):
            def request(self, method, params):
                if method == 'eth_blockNumber':
                    self.second_height = 101 if self.head_reads == 1 else 127
                if method == 'eth_call' and params[0]['data'] == m.COUNT_SELECTOR:
                    self.after = 500 if self.count_reads == 1 else 501
                return super().request(method, params)
        with self.assertRaisesRegex(m.ForwardProbeError,
                                    'ANCESTRY_EXCEEDS_BOUNDED_DEPTH'):
            self.bounded(rpc=OneValidThenTooLong(), budget=100)
        failure = json.loads((self.dir/'failure.json').read_text())
        verified = failure['completed_verified_prefix_intervals']
        self.assertEqual(len(verified), 1)
        self.assertEqual((verified[0]['from_block'], verified[0]['to_block']),
                         (100, 101))
        self.assertEqual(verified[0]['factory_counter_delta'], 0)
        self.assertEqual(verified[0]['p0_pit_gate'], 'NOT_PASSED')
        unverified = failure['uncommitted_counter_interval']
        self.assertEqual((unverified['from_block'], unverified['to_block']),
                         (101, 127))
        self.assertEqual(unverified['factory_counter_delta'], 1)
        self.assertEqual(unverified['candidate_index_start'], 500)
        self.assertFalse((self.dir/'manifest.json').exists())

    def test_user_reported_57_rpc_15_23_26_block_trace_replays_fail_closed(self):
        # Structural replay of user's 2026-10-28 terminal observations.
        # Header hashes here are synthetic: this is NOT original RPC/PIT proof.
        observed_heads = (130253626, 130253641, 130253664, 130253690)
        observed_counts = (3576364, 3576364, 3576364, 3576365)

        class UserTraceShape(FakeRPC):
            def __init__(self):
                super().__init__(first_height=observed_heads[0],
                                 second_height=observed_heads[1],
                                 before=observed_counts[0],
                                 after=observed_counts[1])

            def request(self, method, params):
                if method == 'eth_blockNumber':
                    index = min(self.head_reads, len(observed_heads)-1)
                    if index == 0:
                        self.first_height = observed_heads[0]
                    else:
                        self.second_height = observed_heads[index]
                if (method == 'eth_call' and
                        params[0]['data'] == m.COUNT_SELECTOR):
                    index = min(self.count_reads, len(observed_counts)-1)
                    if index == 0:
                        self.before = observed_counts[0]
                    else:
                        self.after = observed_counts[index]
                return super().request(method, params)

        with self.assertRaisesRegex(m.ForwardProbeError,
                                    'ANCESTRY_EXCEEDS_BOUNDED_DEPTH'):
            self.bounded(rpc=UserTraceShape(), budget=180, duration=180)
        failure = json.loads((self.dir/'failure.json').read_text())
        self.assertEqual(failure['rpc_attempt_count'], 57)
        self.assertEqual(len(failure['completed_rpc_responses']), 57)
        prefix = failure['completed_verified_prefix_intervals']
        self.assertEqual([(p['from_block'], p['to_block'])
                          for p in prefix],
                         [(130253626, 130253641),
                          (130253641, 130253664)])
        self.assertEqual([p['factory_counter_delta'] for p in prefix], [0, 0])
        candidate = failure['uncommitted_counter_interval']
        self.assertEqual((candidate['from_block'], candidate['to_block']),
                         (130253664, 130253690))
        self.assertEqual(candidate['gap_blocks'], 26)
        self.assertEqual(candidate['factory_counter_delta'], 1)
        self.assertEqual((candidate['candidate_index_start'],
                          candidate['candidate_index_end_exclusive']),
                         (3576364, 3576365))
        self.assertEqual(candidate['ancestry_and_pair_identity'], 'NOT_VERIFIED')
        self.assertFalse((self.dir/'manifest.json').exists())
        for row in failure['completed_rpc_responses']:
            raw = (self.dir / row['raw_file']).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), row['raw_sha256'])

    def test_untrusted_counts_do_not_create_uncommitted_candidate(self):
        with self.assertRaisesRegex(m.ForwardProbeError,
                                    'FACTORY_COUNTER_DECREASED'):
            self.bounded(rpc=FakeRPC(before=501, after=500))
        failure = json.loads((self.dir/'failure.json').read_text())
        self.assertNotIn('uncommitted_counter_interval', failure)
        self.assertFalse((self.dir/'manifest.json').exists())

    def test_one_second_poll_is_bounded_and_offline(self):
        clk = Clock()
        rpc = FakeRPC(before=500, after=500)
        result = m.capture_bounded(
            rpc, self.dir, duration_seconds=12, poll_seconds=1,
            rpc_budget=55, clock=clk.now, monotonic_ns=clk.monotonic,
            sleep=clk.sleep)
        self.assertEqual(result['poll_seconds_requested'], 1)
        self.assertTrue(result['verified_intervals'])
        self.assertLessEqual(result['rpc_attempt_count'], 55)
        self.assertFalse(result['p1_gate_passed'])
        self.assertFalse(result['trading_authorized'])
        self.assertTrue((self.dir/'manifest.json').exists())

    def test_reorg_refused_instead_of_using_stale_counter(self):
        with self.assertRaisesRegex(m.ForwardProbeError, 'FIRST_ANCHOR_CHANGED'):
            self.bounded(rpc=FakeRPC(changed_hash=True))
        self.assertFalse((self.dir/'manifest.json').exists())

    def test_bad_parent_hash_fails_closed(self):
        with self.assertRaisesRegex(m.ForwardProbeError, 'NONCONTIGUOUS_PARENT_HASH'):
            self.bounded(rpc=FakeRPC(second_height=103, broken_parent_height=102))
        self.assertFalse((self.dir/'manifest.json').exists())

    def test_clock_jump_fails_closed(self):
        with self.assertRaisesRegex(m.ForwardProbeError, 'LOCAL_CLOCK_MONOTONIC_DISAGREEMENT'):
            self.bounded(clock=Clock(utc_jump_at=9, utc_jump_seconds=4))
        self.assertFalse((self.dir/'manifest.json').exists())

    def test_transport_180_calls_stays_within_subclass_but_not_fourmeme(self):
        forward = m.ForwardRPC("https://bsc-dataseed.bnbchain.org",
                               max_requests=m.MAX_BOUNDED_CALLS)
        self.assertEqual(forward.max_requests, 180)
        self.assertEqual(forward.calls, 0)
        self.assertEqual(m.MAX_CALLS, 20)
        from mission_agent.early.fourmeme_index_source_probe import JsonRPC, ProbeError
        with self.assertRaisesRegex(ProbeError, "FOURMEME_UNSAFE_REQUEST_BUDGET"):
            JsonRPC("https://bsc-dataseed.bnbchain.org", max_requests=180)

    def test_bounds_reject_unlimited_duration_and_request_budget(self):
        for kw in ({'duration_seconds': 181, 'rpc_budget': 55},
                   {'duration_seconds': 36, 'rpc_budget': 181},
                   {'duration_seconds': 36, 'rpc_budget': 39},
                   {'duration_seconds': 36, 'rpc_budget': 55, 'poll_seconds': 13}):
            with self.subTest(kw=kw):
                with self.assertRaisesRegex(m.ForwardProbeError, 'BOUNDED_CONTRACT_OUT_OF_RANGE'):
                    m.capture_bounded(FakeRPC(), self.dir, **kw)
        self.assertFalse(self.dir.exists())

    def test_existing_output_never_overwritten(self):
        result = self.bounded()
        original = (self.dir/'manifest.json').read_bytes()
        with self.assertRaisesRegex(m.ForwardProbeError, 'OUTPUT_DIRECTORY_MUST_NOT_EXIST'):
            self.bounded()
        self.assertEqual((self.dir/'manifest.json').read_bytes(), original)


if __name__ == '__main__':
    unittest.main()
