"""Stage13 regression: prereg dates, actual calendar isolation, no data leakage."""
import hashlib
import importlib.util
import io
import json
import tempfile
import unittest
import zipfile
from datetime import date,datetime,timezone
from pathlib import Path

S=Path(__file__).resolve().parents[1]/"scripts/monster_v4_stage13_multiday.py"
sp=importlib.util.spec_from_file_location("monster_v4_stage13_multiday",S)
m=importlib.util.module_from_spec(sp)
sp.loader.exec_module(m)


def independent_official_archive_mock(url,max_bytes=12_000_000):
    """Explicit microsecond-source fixture using the same published checksum contract."""
    name=url.split("/")[-1].removesuffix(".CHECKSUM")
    symbol,stamp=name.split("-1m-")
    day=date.fromisoformat(stamp[:-4])
    start=int(datetime(day.year,day.month,day.day,tzinfo=timezone.utc).timestamp()*1000)
    lines=[]
    for i in range(1440):
        micro=(start+i*60_000)*1000
        lines.append(",".join([str(micro),"1","1","1","1","10",str(micro+59999999),
                               "200","1","0","0","0"]))
    buf=io.BytesIO()
    with zipfile.ZipFile(buf,"w",zipfile.ZIP_DEFLATED) as z:
        z.writestr(symbol+"-1m-"+day.isoformat()+".csv","\n".join(lines)+"\n")
    data=buf.getvalue()
    if url.endswith(".CHECKSUM"):
        return (hashlib.sha256(data).hexdigest()+"  "+name).encode()
    return data


class Stage13FixedCalendarTests(unittest.TestCase):
    def test_calendar_frozen_before_any_historical_query(self):
        self.assertEqual([d.isoformat() for d in m.frozen_dates()],[
            "2025-11-17","2026-02-17","2026-05-17","2026-08-17"])
        self.assertEqual(len(m.full.validate_manifest(json.loads(
            m.full.REGISTRY.read_text(encoding="utf-8")))),504)

    def test_pre_registered_dates_only(self):
        with self.assertRaisesRegex(ValueError,"DATE_OUTSIDE_FROZEN"):
            m.run_day(date(2026,9,17),symbols=[],worker=lambda _:None)

    def test_modified_manifest_must_fail_before_network(self):
        original=json.loads(m.PREREG.read_text(encoding="utf-8"))
        original["frozen_dates_utc"][0]="2025-11-18"
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"tampered.json"
            path.write_text(json.dumps(original),encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"STAGE13_CALENDAR_MODIFIED"):
                m.frozen_dates(path)

    def test_multiple_dates_use_exact_same_production_replay(self):
        for d in (date(2025,11,17),date(2026,8,17)):
            result=m.full.run_symbol("LTCUSDT",
                download=independent_official_archive_mock,
                calendar_day=d,
                calendar_anchor=d.isoformat()+"T12:00:00Z")
            self.assertEqual(result["status"],"COMPLETE_60H")
            self.assertEqual(result["verified_minute_bars"],3600)
            self.assertEqual(result["polls"],240)
            self.assertEqual(result["watch_events"],0)
            self.assertEqual(result["setups"],0)
            self.assertEqual(len(result["archive_sha256"]),3)

    def test_mismatched_date_anchor_fails_closed(self):
        with self.assertRaisesRegex(ValueError,"INVALID_CALENDAR_ANCHOR"):
            m.full.run_symbol("LTCUSDT",
                calendar_day=date(2026,5,17),
                calendar_anchor="2026-05-18T12:00:00Z",
                download=lambda *_: self.fail("MUST_NOT_FETCH_FOR_WRONG_DATE"))

    def test_subset_not_reported_as_full_and_immutable_no_go(self):
        names=m.full.validate_manifest(json.loads(m.full.REGISTRY.read_text()))
        result=m.run_day(date(2026,5,17),symbols=names[:2],
                         worker=lambda sym:{"symbol":sym,"status":"SOURCE_MISSING"},
                         max_workers=2)
        self.assertEqual(result["summary"]["full_60h_data_cases"],0)
        self.assertFalse(result["summary"]["full_universe_attempted"])
        self.assertEqual(result["anchor"],"2026-05-17T12:00:00Z")
        self.assertFalse(result["independent_out_of_sample"])
        self.assertFalse(result["has_historical_depth_or_actual_fills"])
        self.assertEqual(result["deployment"],"NO_GO")


if __name__=="__main__":
    unittest.main()
