"""Offline bounded partial-window integration checks; no network or production."""
import sys
import unittest
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import monster_v4_forward_spot511_first518_fifo8_bridge as study
import monster_v4_stage166_spot511_official_1m_intake as admitted


class First518ContractTests(unittest.TestCase):
    def test_frozen_T0_all_511_three_day_git_receipts(self):
        roster=admitted.frozen_roster()
        got=study.evidence_receipts(roster)
        self.assertEqual(len(roster),511)
        self.assertEqual(len(got),1533)
        self.assertEqual(len([x for x in roster if not x.isascii()]),2)
        self.assertEqual(set(got),{(symbol,day) for symbol in roster for day in study.DAY_UTC})

    def test_first518_clock_with_partial_right_boundary(self):
        self.assertEqual((study.END-study.START)//study.TICK_MS,518)
        self.assertEqual(study.START%study.TICK_MS,0)
        self.assertEqual(study.END%study.TICK_MS,0)
        self.assertEqual(datetime.fromtimestamp(study.END/1000,timezone.utc).isoformat(),
                         "2026-10-19T00:00:00+00:00")

    def test_tick_input_never_reads_unclosed_minute(self):
        start=study.START-1440*study.MIN_MS
        bars=[(start+i*study.MIN_MS,Decimal(1),Decimal(1),Decimal(1),
               Decimal(2),Decimal(i+1),1) for i in range(1442)]
        prefix=[Decimal(0)]
        for b in bars: prefix.append(prefix[-1]+b[5])
        got=study.tick_input(study.START,start,prefix,bars)
        self.assertEqual(got[0],study.START)
        self.assertEqual(got[1],Decimal(2))
        self.assertEqual(got[2],sum((Decimal(i+1) for i in range(1440)),Decimal(0)))
        altered=list(bars)
        altered[1440]=(altered[1440][0],Decimal(1),Decimal(1),Decimal(1),
                       Decimal(999999),Decimal(999999),1)
        self.assertEqual(got,study.tick_input(study.START,start,prefix,altered))

    def test_1m_gap_is_hard_block(self):
        start=study.START-1440*study.MIN_MS
        bars=[(start+i*study.MIN_MS,Decimal(1),Decimal(1),Decimal(1),
               Decimal(2),Decimal(1),1) for i in range(1440)]
        bars[1439]=(bars[1439][0]-study.MIN_MS,*bars[1439][1:])
        prefix=[Decimal(i) for i in range(1441)]
        with self.assertRaisesRegex(ValueError,"MISSING_CLOSED_MINUTE"):
            study.tick_input(study.START,start,prefix,bars)

    def test_source_files_must_refuse_same_filename_from_two_artifacts(self):
        with TemporaryDirectory() as a, TemporaryDirectory() as b:
            Path(a,"A-1m-2026-10-16.zip").write_bytes(b"one")
            Path(b,"A-1m-2026-10-16.zip").write_bytes(b"two")
            with self.assertRaisesRegex(ValueError,"DUPLICATED_ORIGINAL_ARCHIVE_NAME"):
                study.source_files([a,b])

    def test_source_bytes_do_not_exist_in_repo_stub(self):
        with TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError,"ORIGINAL_PUBLISHER_BYTES_MISSING"):
                study.parse_symbol_three_days("BTCUSDT",{}, {},{})


if __name__=="__main__":
    unittest.main()
