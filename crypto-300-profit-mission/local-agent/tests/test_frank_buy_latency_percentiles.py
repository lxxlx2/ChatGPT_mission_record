"""The offline buy audit reports percentiles for known clocks, not delivery."""
import sqlite3
import unittest
from unittest.mock import patch

from mission_agent.signals.buy_reconciliation import _latency, _timing, audit_buys


class BuyLatencyPercentilesTest(unittest.TestCase):
    def test_empty_and_all_unknown_do_not_become_zero_seconds(self):
        for values in ([], [None, None, None]):
            with self.subTest(values=values):
                result = _timing(values)
                self.assertEqual(result['sample_count'], 0)
                self.assertEqual(result['unknown_count'], len(values))
                for key in ('minimum_seconds', 'p50_seconds', 'p95_seconds', 'maximum_seconds'):
                    self.assertIsNone(result.get(key))

    def test_small_even_sample_uses_nearest_rank_not_an_interpolated_median(self):
        r = _timing([30, None, 1.125, 4.25, 2])
        self.assertEqual((r['sample_count'], r['unknown_count']), (4, 1))
        self.assertEqual(r.get('percentile_method'), 'NEAREST_RANK')
        self.assertEqual((r.get('p50_seconds'), r.get('p95_seconds')), (2, 30))
        self.assertEqual((r['minimum_seconds'], r['maximum_seconds']), (1.125, 30))

    def test_twenty_samples_show_p95_distinct_from_maximum(self):
        r = _timing([*range(20, 0, -1), None, None])
        self.assertEqual((r.get('p50_seconds'), r.get('p95_seconds')), (10, 19))
        self.assertEqual((r['sample_count'], r['unknown_count'], r['maximum_seconds']), (20, 2, 20))

    def test_unverified_clocks_stay_unknown_and_a_real_zero_stays_zero(self):
        t = 1_800_000_000
        r = _timing([_latency(v, t) for v in (t - 1, float('nan'), '2026-01-01', t)])
        self.assertEqual((r['sample_count'], r['unknown_count']), (1, 3))
        self.assertEqual((r.get('p50_seconds'), r.get('p95_seconds')), (0, 0))


    def test_audit_percentiles_exclude_unmatched_buys_and_keep_delivery_unverified(self):
        mint = 'So11111111111111111111111111111111111111112'
        at = 1_800_000_000
        db = sqlite3.connect(':memory:')
        self.addCleanup(db.close)
        db.row_factory = sqlite3.Row
        db.executescript('''
            CREATE TABLE signatures(wallet, signature, body, block_time, raw_hash, seen_at);
            CREATE TABLE signature_detections(wallet, signature, seen_at);
            CREATE TABLE trades(wallet, signature, side, mint);
        ''')
        reference = {'person_id': 'frank', 'wallet': 'fixture-wallet', 'transactions': []}
        result = {'rows': [], 'unexpected_indexed_signatures': []}
        for i, (indexed, detected, elapsed) in enumerate((
            ('MATCH', 'MATCH', (2.25, 4)), ('MATCH', 'UNKNOWN', (50, 5)),
            ('MISSING', 'UNKNOWN', (0, 99)),
        )):
            signature = f'synthetic-{i}'
            reference['transactions'].append({'slot': 10+i, 'expected_frank_buy': mint,
                                               'expectation_sha256': 'a'*64})
            result['rows'].append({'signature': signature, 'stages': {
                'indexed': {'status': indexed}, 'detection': {'status': detected},
            }})
            if indexed == 'MATCH':
                db.execute('INSERT INTO signatures VALUES(?,?,?,?,?,?)',
                           ('fixture-wallet', signature, '{}', at, 'b'*64, at+elapsed[1]))
                db.execute('INSERT INTO trades VALUES(?,?,?,?)', ('fixture-wallet', signature, 'BUY', mint))
                db.execute('INSERT INTO signature_detections VALUES(?,?,?)',
                           ('fixture-wallet', signature, at+elapsed[0]))
        with patch('mission_agent.signals.buy_reconciliation.qualification', return_value={}):
            with patch('mission_agent.signals.buy_reconciliation.admit_buy', return_value={'mint': mint}):
                audit = audit_buys(db, reference, result, 'fixture', 'c'*64, at)
        self.assertEqual(audit['status'], 'GAPS')
        self.assertEqual((audit['counts']['MATCHED_IN'], audit['counts']['MISSED']), (2, 1))
        self.assertEqual(audit['delivery_timing'], 'NOT_VERIFIED')
        detection, indexed = audit['chain_to_detection'], audit['chain_to_index']
        self.assertEqual((detection['sample_count'], detection['unknown_count']), (1, 1))
        self.assertEqual((detection.get('p50_seconds'), detection.get('p95_seconds')), (2.25, 2.25))
        self.assertEqual((indexed['sample_count'], indexed['unknown_count']), (2, 0))
        self.assertEqual((indexed.get('p50_seconds'), indexed.get('p95_seconds')), (4, 5))


if __name__ == '__main__':
    unittest.main()
