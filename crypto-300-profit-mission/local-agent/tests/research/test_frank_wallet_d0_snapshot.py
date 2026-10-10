"""Synthetic read-only regressions for Frank D0 historical-index diagnostics."""
import importlib.util
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[2] / 'scripts' / 'frank_wallet_d0_snapshot.py'
spec = importlib.util.spec_from_file_location('d0', SCRIPT)
d0 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(d0)
T0 = 1791670000


class D0Test(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dbpath = Path(self.tmp.name) / 'forward.sqlite'
        self.db = sqlite3.connect(str(self.dbpath))
        self.db.executescript('''
            CREATE TABLE signatures(wallet TEXT, person_id TEXT, signature TEXT, block_time INTEGER, body TEXT);
            CREATE TABLE trades(wallet TEXT, signature TEXT, mint TEXT, episode_id TEXT, block_time INTEGER, side TEXT, body TEXT);
            CREATE TABLE v1_states(person_id TEXT, mint TEXT, body TEXT);
        ''')
        self.wallet = 'synthetic_wallet'

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def add_sig(self, sig, ts, cls):
        self.db.execute('INSERT INTO signatures VALUES (?,?,?,?,?)',
                        (self.wallet, 'frank', sig, ts, json.dumps({'classification': cls})))

    def add_trade(self, sig, mint, side, ts, raw):
        self.db.execute('INSERT INTO trades VALUES (?,?,?,?,?,?,?)',
                        (self.wallet, sig, mint, None, ts, side, json.dumps({
                            'quote_asset': d0.USDC, 'quote_amount_raw': str(raw), 'quote_decimals': 6})))

    def test_old_trade_and_watch_not_erased_by_zero_24h(self):
        old = T0 - 44 * 3600
        self.add_sig('oldbuy', old, 'ACTIVE_TRADE')
        self.add_trade('oldbuy', 'MINT_A', 'BUY', old, 3300000000)
        self.add_sig('recentpassive', T0 - 100, 'PASSIVE_RECEIPT')
        self.db.execute('INSERT INTO v1_states VALUES (?,?,?)', ('frank', 'MINT_A', json.dumps({'state': 'OPEN', 'current_raw': '100'})))
        self.db.commit()
        r = d0.report(self.dbpath, T0)
        self.assertEqual(r['window_24h']['24h_indexed_signatures'], 1)
        self.assertEqual(r['window_24h'].get('24h_recognized_buys', 0), 0)
        self.assertEqual(r['watch_seed'][0]['mint'], 'MINT_A')
        self.assertEqual(r['watch_seed'][0]['local_recognized_buy_count'], 1)
        self.assertEqual(r['watch_seed'][0]['chain_balance_verification'], 'NOT_DONE_BY_LOCAL_SNAPSHOT')
        self.assertEqual(r['screenshot_amount_matches'][0]['matched_rounded_amount'], '3300.00')

    def test_passive_transfer_is_not_market_buy(self):
        self.add_sig('deposit', T0 - 2, 'PASSIVE_RECEIPT')
        self.db.commit()
        r = d0.report(self.dbpath, T0)
        self.assertEqual(r['window_24h']['24h_indexed_signatures'], 1)
        self.assertEqual(r['window_24h'].get('24h_recognized_buys', 0), 0)
        self.assertEqual(r['local_observed_mints'], 0)

    def test_exact_quoted_sell_and_signatures_dedup(self):
        self.add_sig('sellsig', T0 - 30, 'ACTIVE_TRADE')
        self.add_trade('sellsig', 'MINT_B', 'SELL', T0 - 30, 7031556770)
        self.add_trade('sellsig', 'MINT_B', 'SELL', T0 - 30, 7031556770)
        self.db.commit()
        r = d0.report(self.dbpath, T0)
        self.assertEqual(r['window_24h']['24h_recognized_sells'], 1)
        self.assertEqual(r['screenshot_amount_matches'][0]['matched_rounded_amount'], '7031.56')
        self.assertEqual(r['watch_seed'][0]['local_recognized_sell_count'], 1)

    def test_no_mutation_and_unknown_market_value(self):
        self.add_sig('buy', T0 - 10, 'ACTIVE_TRADE')
        self.add_trade('buy', 'MINT_C', 'BUY', T0 - 10, 220000000)
        self.db.commit()
        original = self.db.execute('PRAGMA data_version').fetchone()[0]
        r = d0.report(self.dbpath, T0)
        self.assertFalse(r['chain_completeness_verified'])
        self.assertEqual(r['watch_seed'][0]['pnl_completeness'], 'UNVERIFIED_HISTORY_AND_COST_BASIS')
        self.assertEqual(original, self.db.execute('PRAGMA data_version').fetchone()[0])
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM trades').fetchone()[0], 1)

    def test_missing_database_fails_closed(self):
        with self.assertRaises(FileNotFoundError):
            d0.report(Path(self.tmp.name) / 'missing.sqlite', T0)


if __name__ == '__main__':
    unittest.main()
