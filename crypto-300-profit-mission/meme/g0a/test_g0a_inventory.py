"""Focused checks; run with python3 -m unittest discover -s <g0a> -v."""
import argparse
import importlib.util
import sqlite3
import tempfile
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location('g0a_inventory', Path(__file__).with_name('g0a_inventory.py'))
g = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(g)


class InventoryTests(unittest.TestCase):
    def test_unknown_is_not_sell_and_read_only_is_enforced(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'snapshot.sqlite'
            db = sqlite3.connect(path)
            db.execute('CREATE TABLE trades(wallet,signature,mint,episode_id,side,body)')
            db.executemany('INSERT INTO trades VALUES(?,?,?,?,?,?)', [
                ('w', 'a', 'm', 'e', 'BUY', '{}'),
                ('w', 'b', 'm', None, 'SELL_POSITION_UNRESOLVED', '{}'),
                ('w', 'c', 'm', None, 'FUTURE_SIDE', '{}')])
            db.commit(); db.close()
            result = g.runtime_inventory(path)
            for kind in ('BUY', 'SELL', 'UNKNOWN'):
                self.assertEqual(result[kind]['signatures'], 1)
            self.assertEqual(result['SELL']['episodes'], 0)
            db = g.ro(path)
            with self.assertRaises(sqlite3.OperationalError):
                db.execute('DELETE FROM trades')
            db.close()

    def test_missing_input_does_not_create_sqlite(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'missing.sqlite'
            with self.assertRaisesRegex(ValueError, 'INPUT_UNAVAILABLE'):
                g.ro(path)
            self.assertFalse(path.exists())
            self.assertEqual(g.runtime_inventory(path)['status'], 'UNRESOLVED')
            self.assertEqual(g.cache_inventory(Path(directory))['status'], 'UNRESOLVED')

    def test_empty_history_is_unresolved(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'empty.sqlite'
            db = sqlite3.connect(path)
            db.execute('CREATE TABLE signatures(block_time,slot,signature)'); db.close()
            with self.assertRaisesRegex(ValueError, 'EMPTY_HISTORY'):
                g.verified_rows(path, {})

    def test_missing_history_returns_partial(self):
        args = argparse.Namespace(study=g.STUDY, source=None, runtime_db=None, cache_dir=None)
        result = g.inventory(args)
        self.assertEqual(result['status'], 'G0_A_PARTIAL')
        self.assertEqual(result['history']['reason'], 'HISTORY_SOURCE_UNAVAILABLE')

    def test_network_guard_and_original_price_validity(self):
        with self.assertRaisesRegex(RuntimeError, 'NETWORK_FORBIDDEN'):
            g.deny_network('socket.connect', ())
        for amount, expected in [('0', False), ('2', True)]:
            record = {'trade': {'token_amount_raw': amount, 'token_decimals': 6,
                                'quote_amount_raw': '1', 'quote_decimals': 6}}
            self.assertEqual(g.amounts_available(record), expected)


if __name__ == '__main__':
    unittest.main()
