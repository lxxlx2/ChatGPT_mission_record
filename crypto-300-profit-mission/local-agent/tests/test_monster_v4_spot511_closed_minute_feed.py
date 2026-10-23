"""Original official-format Stage166 ZIP/CHECKSUM, no external HTTP."""
import hashlib
import sys
import tempfile
import unittest
import zipfile
from datetime import date, datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import monster_v4_spot511_closed_minute_feed as m

ROSTER = ['BTCUSDT'] + [f'Q{i:03d}USDT' for i in range(510)]
ROSTER.sort()


def publisher_day(root, day, *, spike_minute=None, sha_corrupt=False):
    symbol = 'BTCUSDT'
    zip_path, checksum_path = m.stage166.daily_paths(root, symbol, day)
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    start = int(datetime.combine(day, datetime.min.time(), timezone.utc).timestamp()) * 1_000_000
    rows = []
    for j in range(1440):
        at = start + j * 60_000_000
        close = '1.10' if spike_minute is not None and j >= spike_minute else '1.00'
        rows.append(f'{at},1.00,1.11,0.90,{close},1,{at+59_999_999},1000,1,1,1000,0')
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr(f'{symbol}-1m-{day.isoformat()}.csv', '\n'.join(rows) + '\n')
    digest = hashlib.sha256(zip_path.read_bytes()).hexdigest()
    checksum_path.write_text(('f'*64 if sha_corrupt else digest) + '  ' + zip_path.name + '\n')


class MinuteFeedTests(unittest.TestCase):
    def test_valid_two_days_only_enable_first_39_ticks(self):
        with tempfile.TemporaryDirectory() as p:
            publisher_day(p, date(2026, 10, 16))
            publisher_day(p, date(2026, 10, 17), spike_minute=1327)
            report = m.symbol_tick_feed(p, 'BTCUSDT', roster=ROSTER,
                asof_utc=datetime(2026, 10, 18, 12, tzinfo=timezone.utc))
            self.assertEqual(len(report['ticks']),3360)
            self.assertEqual(report['counts']['READY_RECONSTRUCTED_TICKER_PROXY'],39)
            self.assertEqual(report['counts']['CENSORED_SOURCE_MISSING_OR_REJECTED'],3321)
            first, second = report['ticks'][:2]
            self.assertEqual(first['tick_ms'],m.START_MS)
            self.assertEqual(first['source_row']['lastPrice'],'1.00')
            self.assertEqual(second['source_row']['lastPrice'],'1.10')
            self.assertEqual(first['source_row']['quoteVolume'],'1440000')
            self.assertFalse(report['quote24_is_live_ticker'])
            self.assertEqual(report['G6'],'NO_GO')

    def test_source_rejected_does_not_make_zero_signal(self):
        with tempfile.TemporaryDirectory() as p:
            publisher_day(p, date(2026,10,16),sha_corrupt=True)
            publisher_day(p, date(2026,10,17))
            report=m.symbol_tick_feed(p, 'BTCUSDT',roster=ROSTER,
                asof_utc=datetime(2026,10,18,12,tzinfo=timezone.utc))
            self.assertIn('2026-10-16',report['source_rejected_days'])
            self.assertEqual(report['counts']['CENSORED_SOURCE_MISSING_OR_REJECTED'],3359)
            self.assertEqual(report['counts']['READY_RECONSTRUCTED_TICKER_PROXY'],1)
            ready = [x for x in report['ticks'] if x['source_row'] is not None]
            self.assertEqual(ready[0]['tick_ms'], int(datetime(2026,10,18,tzinfo=timezone.utc).timestamp()*1000))

    def test_future_day_bytes_never_admitted(self):
        with tempfile.TemporaryDirectory() as p:
            publisher_day(p,date(2026,10,16))
            publisher_day(p,date(2026,10,17))
            publisher_day(p,date(2026,10,18))
            report=m.symbol_tick_feed(p,'BTCUSDT',roster=ROSTER,
                asof_utc=datetime(2026,10,18,12,tzinfo=timezone.utc))
            self.assertIn('2026-10-18',report['source_future_days'])
            self.assertEqual(report['counts']['READY_RECONSTRUCTED_TICKER_PROXY'],39)

    def test_missing_all_days_preserves_frozen_denominator(self):
        with tempfile.TemporaryDirectory() as p:
            result=m.symbol_tick_feed(p,'BTCUSDT',roster=ROSTER,
                asof_utc=datetime(2026,10,26,tzinfo=timezone.utc))
            self.assertEqual(result['counts']['CENSORED_SOURCE_MISSING_OR_REJECTED'],3360)
            self.assertEqual(len(result['source_unavailable_days']),9)

    def test_roster_and_timezone_are_fail_closed(self):
        with tempfile.TemporaryDirectory() as p:
            with self.assertRaisesRegex(ValueError,'SPOT511_FROZEN_SYMBOL_REQUIRED'):
                m.symbol_tick_feed(p,'NOTINUSDT',roster=ROSTER,
                    asof_utc=datetime(2026,10,26,tzinfo=timezone.utc))
            with self.assertRaisesRegex(ValueError,'ASOF_MUST_BE_TIMEZONE_AWARE'):
                m.symbol_tick_feed(p,'BTCUSDT',roster=ROSTER,
                    asof_utc=datetime(2026,10,26))


if __name__ == '__main__':
    unittest.main()
