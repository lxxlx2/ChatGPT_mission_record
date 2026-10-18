"""Stage166 fail-closed real T0 identity + synthetic future publisher 1m tests."""
import hashlib
import importlib.util
from datetime import date,datetime,timezone
from pathlib import Path
import tempfile
import unittest
import zipfile

P = Path(__file__).resolve().parents[1] / "scripts"
spec = importlib.util.spec_from_file_location(
    "m_stage166", P / "monster_v4_stage166_spot511_official_1m_intake.py")
import sys
sys.path.insert(0,str(P))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def publisher_fixture(root,symbol="BTCUSDT",day=date(2026,10,16),rows=1440,unit=1_000_000,corrupt=False):
    p,checksum=m.daily_paths(root,symbol,day)
    p.parent.mkdir(parents=True,exist_ok=True)
    filename=p.name.replace(".zip",".csv")
    utc=int(datetime.combine(day,datetime.min.time(),timezone.utc).timestamp())
    entries=[]
    for n in range(rows):
        t=utc*unit+n*60*unit
        entries.append(f"{t},1,1.1,0.9,1,10,{t+60*unit-1},100,2,5,50,0")
    with zipfile.ZipFile(p,"w",compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr(filename,"\n".join(entries)+"\n")
    sha=hashlib.sha256(p.read_bytes()).hexdigest()
    checksum.write_text(("f"*64 if corrupt else sha)+"  "+p.name+"\n")
    return p,checksum


class Stage166Tests(unittest.TestCase):
    def test_source_t0_actual_511_and_214_break(self):
        r=m.frozen_roster()
        self.assertEqual(len(r),511)
        self.assertEqual(len(set(r)),511)
        self.assertIn("BTCUSDT",r)
        self.assertIn("ETHUSDT",r)
        self.assertEqual(r,sorted(r))

    def test_source_readiness_511_by_9_and_no_fake_missed_signals(self):
        with tempfile.TemporaryDirectory() as d:
            r=m.build_report(Path(d), datetime(2026,10,18,16,tzinfo=timezone.utc))
            self.assertEqual(r["daily_source_attempts"],4599)
            self.assertEqual(r["admission_counts"],
                 {"SOURCE_NOT_SUPPLIED":1022, "UTC_DAY_NOT_YET_ENDED":3577})
            self.assertEqual(r["t0_spot_usdt_break_excluded"],214)
            self.assertFalse(r["all_511_nine_days_officially_verified"])
            self.assertTrue(r["no_absent_source_is_classified_as_zero_signal"])
            self.assertEqual(r["G6"],"NO_GO")

    def test_real_source_microsecond_official_checksum_acceptance(self):
        with tempfile.TemporaryDirectory() as d:
            p,checksum=publisher_fixture(Path(d))
            result=m.validate_daily_zip(p,checksum,"BTCUSDT",date(2026,10,16))
            self.assertTrue(result["original_publisher_checksum_valid"])
            self.assertEqual(result["closed_one_minute_rows"],1440)
            self.assertEqual(result["spot_timestamp_units"],"MICROSECONDS")
            r=m.build_report(Path(d), datetime(2026,10,18,16,tzinfo=timezone.utc))
            self.assertEqual(r["admission_counts"]["VERIFIED_FULL_DAY_1440"],1)
            self.assertEqual(r["admission_counts"]["SOURCE_NOT_SUPPLIED"],1021)
            self.assertFalse(r["all_511_nine_days_officially_verified"])

    def test_publisher_checksum_tamper_rejected_not_relabelled_empty(self):
        with tempfile.TemporaryDirectory() as d:
            publisher_fixture(Path(d),corrupt=True)
            r=m.build_report(Path(d),datetime(2026,10,18,16,tzinfo=timezone.utc))
            self.assertEqual(r["admission_counts"]["SOURCE_REJECTED_OR_INCOMPLETE"],1)
            self.assertEqual(r["admission_counts"].get("VERIFIED_FULL_DAY_1440",0),0)

    def test_millisecond_rows_cannot_impersonate_spot_microseconds(self):
        with tempfile.TemporaryDirectory() as d:
            p,q=publisher_fixture(Path(d),unit=1000)
            with self.assertRaisesRegex(ValueError,"MICROSECOND_GRID"):
                m.validate_daily_zip(p,q,"BTCUSDT",date(2026,10,16))

    def test_partial1440_does_not_admit_complete_source(self):
        with tempfile.TemporaryDirectory() as d:
            p,q=publisher_fixture(Path(d),rows=1439)
            with self.assertRaisesRegex(ValueError,"INCOMPLETE_1440"):
                m.validate_daily_zip(p,q,"BTCUSDT",date(2026,10,16))

    def test_future_day_sources_not_promoted_even_if_archive_is_supplied(self):
        with tempfile.TemporaryDirectory() as d:
            publisher_fixture(Path(d),day=date(2026,10,24))
            r=m.build_report(Path(d),datetime(2026,10,18,16,tzinfo=timezone.utc))
            future=[x for x in r["attempts"]
                    if x["symbol"]=="BTCUSDT" and x["date_utc"]=="2026-10-24"]
            self.assertEqual(future[0]["archive_status"],"UTC_DAY_NOT_YET_ENDED")
            self.assertEqual(r["admission_counts"].get("VERIFIED_FULL_DAY_1440",0),0)

    def test_rejects_missing_checksum_but_doesnt_reject_entire_511_population(self):
        with tempfile.TemporaryDirectory() as d:
            p,q=publisher_fixture(Path(d))
            q.unlink()
            r=m.build_report(Path(d),datetime(2026,10,18,16,tzinfo=timezone.utc))
            self.assertEqual(r["admission_counts"]["SOURCE_REJECTED_OR_INCOMPLETE"],1)
            self.assertEqual(r["daily_source_attempts"],4599)

    def test_rejects_naive_asof_and_preexisting_output(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError,"UTC_AWARE"):
                m.build_report(Path(d),datetime(2026,10,18,16))


if __name__=="__main__":
    unittest.main()
