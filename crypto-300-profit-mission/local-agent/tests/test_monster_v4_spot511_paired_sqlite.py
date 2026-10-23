"""Deterministic offline full-global-queue tests; no market HTTP or trading."""
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
import tempfile
import unittest

import monster_v4_spot511_paired_sqlite as pair


def synthetic_index(dest, *, symbols=('BTCUSDT','ETHUSDT'), active_ticks=8,
                    partial_at=None, rising=True):
    symbols=tuple(sorted(symbols))
    con=sqlite3.connect(dest)
    con.executescript('''
      CREATE TABLE roster(symbol TEXT PRIMARY KEY);
      CREATE TABLE metadata(k TEXT PRIMARY KEY,v TEXT NOT NULL);
      CREATE TABLE price_ticks(tick_ms INTEGER NOT NULL,symbol TEXT NOT NULL,
           price TEXT NOT NULL,quote24 TEXT NOT NULL,PRIMARY KEY(tick_ms,symbol));
      CREATE TABLE closed5(symbol TEXT NOT NULL,open_ms INTEGER NOT NULL,
           op TEXT NOT NULL,hi TEXT NOT NULL,lo TEXT NOT NULL,cl TEXT NOT NULL,
           volume TEXT NOT NULL,quote TEXT NOT NULL,PRIMARY KEY(symbol,open_ms));
    ''')
    con.executemany('INSERT INTO roster VALUES(?)',[(x,) for x in symbols])
    con.executemany('INSERT INTO metadata VALUES(?,?)',[
        ('schema',pair.SCHEMA),('completed','YES'),
        ('source_kind','OFFICIAL_PUBLISHER_1M_RECONSTRUCTED_PROXY')])
    # Shared source stream: initial observations followed by same-time burst.
    for step in range(active_ticks):
        t=pair.feed.START_MS+step*pair.TICK_MS
        for sym in symbols:
            if partial_at is not None and step==partial_at and sym==symbols[-1]:
                continue
            px='1.00' if step==0 or not rising else '1.08'
            con.execute('INSERT INTO price_ticks VALUES(?,?,?,?)',
                        (t,sym,px,'200000'))
    # 40m preceding first D0 and 20m following => strictly closed 5m inputs.
    open_start=(pair.feed.START_MS//pair.FIVE_MS)*pair.FIVE_MS - 8*pair.FIVE_MS
    for sym in symbols:
        for ix in range(16):
            start=open_start+ix*pair.FIVE_MS
            cl=str(1+ix*.02)
            q='250' if ix>=6 else '100'
            con.execute('INSERT INTO closed5 VALUES(?,?,?,?,?,?,?,?)',
                        (sym,start,cl,'2','0.8',cl,'5',q))
    con.commit();con.close()


class PairedReplayTests(unittest.TestCase):
    def test_original_lanes_same_watch_and_no_future_buy(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'fake-source.sqlite'
            synthetic_index(p)
            report=pair.paired_replay(p,allow_synthetic_cohort=True)
            self.assertEqual(report['mode'],'OFFLINE_SYNTHETIC_TEST')
            self.assertEqual(report['ticks'],3360)
            self.assertEqual(report['full_d0_ticks'],8)
            self.assertEqual(report['censored_d0_ticks'],3352)
            self.assertTrue(report['same_d0_watch_id_and_time'])
            self.assertEqual(report['fifo_setups'],report['fair8_setups'])
            self.assertEqual(report['lost_setup_ids'],[])
            self.assertFalse(report['all_511_historical_sources_verified'])
            self.assertEqual(report['G6'],'NO_GO')
            self.assertEqual(report['net_executable_profit'],'UNKNOWN')

    def test_missing_symbol_never_claimed_as_complete_market(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'missing.sqlite'
            synthetic_index(p,partial_at=2)
            report=pair.paired_replay(p,allow_synthetic_cohort=True)
            self.assertEqual(report['full_d0_ticks'],7)
            self.assertEqual(report['censored_d0_ticks'],3353)
            self.assertEqual(report['source_censored_symbol_ticks'],
                             3352*2+1)
            self.assertTrue(report['same_d0_watch_id_and_time'])
            self.assertEqual(report['G6'],'NO_GO')

    def test_wrong_source_and_roster_cannot_be_scored(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'bad.sqlite'
            synthetic_index(p)
            with self.assertRaisesRegex(ValueError,'FROZEN_POPULATION'):
                pair.paired_replay(p)
            con=sqlite3.connect(p)
            con.execute("UPDATE metadata SET v='LIVE_TICKER' WHERE k='source_kind'")
            con.commit();con.close()
            with self.assertRaisesRegex(ValueError,'INDEX_UNAPPROVED_SOURCE_KIND'):
                pair.paired_replay(p,allow_synthetic_cohort=True)

    def test_true_fifo_and_fair_state_files_never_overwritten(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'source.sqlite'
            synthetic_index(p)
            lanes=Path(temp)/'lanes';lanes.mkdir()
            original=lanes/'fifo8.sqlite';original.write_bytes(b'preserve original')
            with self.assertRaisesRegex(ValueError,'PAIR_LANE_DB_OVERWRITE_REFUSED'):
                pair.paired_replay(p,lane_dir=lanes,allow_synthetic_cohort=True)
            self.assertEqual(original.read_bytes(),b'preserve original')

    def test_missing_db_or_partial_index_cannot_run(self):
        with tempfile.TemporaryDirectory() as temp:
            source=Path(temp)/'source.sqlite';synthetic_index(source)
            con=sqlite3.connect(source)
            con.execute("DELETE FROM metadata WHERE k='completed'")
            con.commit();con.close()
            with self.assertRaisesRegex(ValueError,'INDEX_UNCOMMITTED'):
                pair.paired_replay(source,allow_synthetic_cohort=True)


if __name__=='__main__':
    unittest.main()
