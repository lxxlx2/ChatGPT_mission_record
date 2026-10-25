"""November real future Spot publisher-day admission: synthetic tests only."""
from datetime import date,datetime,timedelta,timezone
import hashlib
from pathlib import Path
import tempfile
import unittest
import zipfile

import monster_v4_adr005_forward_spot_daily_gate as gate
import monster_v4_adr005_forward_spot_t0_gate as t0
import monster_v4_stage166_spot511_official_1m_intake as publisher


class ForwardSpotPublisherFifteenDaysTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.symbols=["COIN0USDT","COIN1USDT"]
        self.start="2026-11-02T00:00:00Z"
        self.stamp="2026-11-03T00:00:00Z"

    def accepted_fake_t0(self):
        # Pure source-calendar fixture, not asserted to be an actual market.
        return {"schema":t0.SCHEMA,"window_start_utc":self.start,
                "source_ready_state":"T0_ARCHIVE_STRUCTURALLY_ADMITTED_ORIGIN_UNVERIFIED",
                "captured_within_15m_and_completed_before_window":True,
                "source_authenticity":"SELF_REPORTED_HTTP_RECEIPTS_NOT_EXCHANGE_SIGNED",
                "t0_spot_usdt_candidates":len(self.symbols),
                "t0_spot_usdt_symbol_ids":list(self.symbols),
                "archive_sha256":"a"*64}

    def write_day(self,symbol,day,*,break_checksum=False):
        dest,checksum=publisher.daily_paths(self.root,symbol,day)
        dest.parent.mkdir(parents=True,exist_ok=True)
        day_start=int(datetime.combine(day,datetime.min.time(),timezone.utc).timestamp())*1_000_000
        lines=[]
        for i in range(1440):
            tm=day_start+i*60_000_000
            lines.append(f"{tm},1,2,0.5,1.5,100,{tm+60_000_000-1},100,10,50,50,0\n")
        with zipfile.ZipFile(dest,"w",compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr(f"{symbol}-1m-{day.isoformat()}.csv","".join(lines))
        digest=hashlib.sha256(dest.read_bytes()).hexdigest()
        checksum.write_text(f"{'0'*64 if break_checksum else digest}  {dest.name}\n")
        return dest,checksum

    def test_three_frozen_window_calendars_have_baseline_7_observation_7_labels(self):
        expected=[
            ("2026-11-02T00:00:00Z","2026-11-01","2026-11-15"),
            ("2026-11-16T00:00:00Z","2026-11-15","2026-11-29"),
            ("2026-12-01T00:00:00Z","2026-11-30","2026-12-14"),
        ]
        for start,first,last in expected:
            with self.subTest(window=start):
                d=gate.source_calendar(start)
                self.assertEqual((len(d),d[0]["utc_day"],d[-1]["utc_day"]),
                                 (15,first,last))
                self.assertEqual([sum(x["segment"]==c for x in d) for c in gate.SEGMENTS],
                                 [1,7,7])
                self.assertEqual(d[1]["segment"],"D0_D1_OBSERVATION_7D")
                self.assertEqual(d[8]["segment"],"FUTURE_2X_LABEL_7D")

    def test_before_future_utc_days_no_fake_publisher_or_t0_denominator(self):
        d=gate.planned_source_readiness(self.start,"2026-10-26T00:00:00Z")
        self.assertEqual(len(d["calendar"]),15)
        self.assertEqual({x["source_status"] for x in d["calendar"]},
                         {"UTC_DAY_NOT_YET_ENDED"})
        self.assertEqual(d["G0"],"POPULATION_UNKNOWN")
        self.assertEqual(d["G1"],"NOT_SCORABLE")
        self.assertNotIn("baseline_symbol_population",d)
        self.assertTrue(d["NO_AUTOMATIONS"])

    def test_calendar_after_event_without_t0_does_not_backfill_population(self):
        d=gate.planned_source_readiness(self.start,"2026-11-04T10:00:00Z")
        self.assertEqual([x["source_status"] for x in d["calendar"][:4]],
                         ["T0_POPULATION_MISSING_CANNOT_SCORE"]*3+
                         ["UTC_DAY_NOT_YET_ENDED"])
        self.assertEqual(d["G0"],"POPULATION_UNKNOWN")

    def test_missing_all_true_symbol_dates_keeps_every_attempt_and_unknown(self):
        d=gate.census(self.accepted_fake_t0(),self.root,self.stamp)
        self.assertEqual(d["expected_official_zip_checksum_pairs"],30)
        self.assertEqual(d["actual_status_counts"],{
            "SOURCE_NOT_SUPPLIED":4,"UTC_DAY_NOT_YET_ENDED":26})
        self.assertEqual(d["G1"],"NOT_SCORABLE")
        self.assertEqual(d["G6"],"NO_GO")
        self.assertFalse(d["verified_complete_all_15days"])

    def test_one_genuine_shape_publisher_zip_sha_valid_verified_not_gt(self):
        self.write_day("COIN0USDT",date(2026,11,1))
        d=gate.census(self.accepted_fake_t0(),self.root,self.stamp)
        self.assertEqual(d["actual_status_counts"]["VERIFIED_1440_OFFICIAL_1M"],1)
        self.assertEqual(d["actual_status_counts"]["SOURCE_NOT_SUPPLIED"],3)
        self.assertEqual(d["G1"],"NOT_SCORABLE")
        hit=next(x for x in d["source_attempts"]
                 if x["symbol"]=="COIN0USDT" and x["utc_day"]=="2026-11-01")
        self.assertEqual(hit["publisher_source_evidence"]["closed_one_minute_rows"],1440)
        self.assertTrue(hit["publisher_source_evidence"]["original_publisher_checksum_valid"])
        self.assertEqual(d["source_publisher_archive_available_at_event_time"],"UNKNOWN")

    def test_wrong_official_sha_is_rejected_not_ignored_or_negative(self):
        self.write_day("COIN0USDT",date(2026,11,1),break_checksum=True)
        d=gate.census(self.accepted_fake_t0(),self.root,self.stamp)
        self.assertEqual(d["actual_status_counts"]["SOURCE_REJECTED_OR_INCOMPLETE"],1)
        self.assertEqual(d["actual_status_counts"].get("VERIFIED_1440_OFFICIAL_1M",0),0)
        self.assertEqual(d["G6"],"NO_GO")

    def test_future_daily_data_not_loaded_as_early_current_source(self):
        self.write_day("COIN0USDT",date(2026,11,2))
        d=gate.census(self.accepted_fake_t0(),self.root,"2026-11-02T20:00:00Z")
        row=next(x for x in d["source_attempts"]
                 if x["symbol"]=="COIN0USDT" and x["utc_day"]=="2026-11-02")
        self.assertEqual(row["source_status"],"UTC_DAY_NOT_YET_ENDED")
        self.assertNotIn("VERIFIED_1440_OFFICIAL_1M",d["actual_status_counts"])

    def test_unverified_t0_tamper_fails_before_source_scan(self):
        record=self.accepted_fake_t0()
        for field in ("captured_within_15m_and_completed_before_window",
                      "source_ready_state","source_authenticity"):
            faulty=dict(record)
            faulty[field]=False
            with self.assertRaisesRegex(ValueError,"REAL_T0_ADMISSION_REQUIRED"):
                gate.census(faulty,self.root,self.stamp)

    def test_issuer_pair_symlink_is_not_opened(self):
        dest,checksum=self.write_day("COIN0USDT",date(2026,11,1))
        checksum.unlink()
        checksum.symlink_to(dest)
        d=gate.census(self.accepted_fake_t0(),self.root,self.stamp)
        row=next(x for x in d["source_attempts"]
                 if x["symbol"]=="COIN0USDT" and x["utc_day"]=="2026-11-01")
        self.assertEqual(row["source_status"],"SOURCE_REJECTED_OR_INCOMPLETE")
        self.assertEqual(row["publisher_source_evidence"],
                         "ARCHIVE_OR_CHECKSUM_SYMLINK_REFUSED")

    def test_malformed_or_unregistered_date_cannot_be_scored(self):
        with self.assertRaisesRegex(ValueError,"UNREGISTERED"):
            gate.source_calendar("2026-11-03T00:00:00Z")
        with self.assertRaises(ValueError):
            gate.planned_source_readiness(self.start,"2026-11-02T07:00:00+07:00")


if __name__=="__main__":
    unittest.main()
