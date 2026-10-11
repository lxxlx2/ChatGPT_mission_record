"""Read-only Stage16 seven-day label and universe integrity regression."""
import importlib.util
import json
import sys
import tempfile
import types
import unittest
import urllib.error
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

FILE = Path(__file__).parents[1] / "scripts" / "monster_v4_stage16_seven_day_labels.py"

def load():
    tmp = Path(tempfile.gettempdir()) / "monster-stage16-unit"
    tmp.mkdir(exist_ok=True)
    (tmp / "monster_stage15_archive_only_5date_actual_ci_20261011.json").write_text(
        json.dumps({"archive_only_compatible_sha256":"samplehash"}))
    fake = types.ModuleType("monster_v4_stage15_archive_only")
    fake.archive = types.SimpleNamespace(source=types.SimpleNamespace(EVIDENCE=tmp))
    fake.inventory = lambda: {
        "archive_only_sha256":"samplehash",
        "replay_eligible_archive_only_count":254,
        "frozen_current_count":504,
        "archive_only_symbols":[f"X{i}USDT" for i in range(254)],
    }
    fake.frozen_current504=lambda: {f"Y{i}USDT" for i in range(504)}
    fake.FROZEN_DATES=("2025-11-17","2026-02-17","2026-05-17","2026-08-17","2026-09-17")
    sys.modules[fake.__name__]=fake
    spec=importlib.util.spec_from_file_location("stage16_testable",FILE)
    target=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(target)
    return target,fake

def bars(day, *, shift=None):
    start=int(datetime(day.year,day.month,day.day,6,tzinfo=timezone.utc).timestamp()*1000)
    data={}
    for h in range(168):
        if h == shift:
            continue
        high=Decimal("5.4") if h==24 else Decimal("1.1")
        close=Decimal("5.1") if h==24 else Decimal("1.0")
        data[start+h*3600000]=(Decimal("1.0"),high,close,Decimal("10000"))
    return data,"deadbeef"

class Stage16Tests(unittest.TestCase):
    def test_universe_frozen_and_size(self):
        m,_=load()
        syms,proof=m.frozen_symbols()
        self.assertEqual(len(syms),758)
        self.assertEqual(proof["archive_only_sha256"],"samplehash")

    def test_universe_hash_tampering_rejected(self):
        m,fake=load()
        fake.inventory=lambda: {"archive_only_sha256":"tampered",
              "replay_eligible_archive_only_count":254,"frozen_current_count":504}
        with self.assertRaisesRegex(ValueError,"UNIVERSE_DRIFT"):
            m.frozen_symbols()

    def test_close_and_high_5x_label_distinguished(self):
        m,_=load()
        day=date(2026,8,17)
        row=m.label("XUSDT",day,month_fetch=lambda s,d: bars(d))
        self.assertTrue(row["gross_high_ge_5x"])
        self.assertTrue(row["gross_close_ge_5x"])
        self.assertFalse(row["gross_high_ge_10x"])
        self.assertEqual(row["first_high_5x_hour_index"],24)
        self.assertTrue(row["raw_high_not_a_fill"])

    def test_missing_hour_not_labeled_no_5x(self):
        m,_=load()
        row=m.label("XUSDT",date(2026,8,17),
                    month_fetch=lambda s,d:bars(d,shift=10))
        self.assertEqual(row["status"],"CENSORED_7D_HOURLY_GAP")
        self.assertNotIn("gross_high_ge_5x",row)

    def test_zip_missing_not_assumed_negative(self):
        m,_=load()
        def gone(*args,**kw):
            raise urllib.error.HTTPError("https://example.org",404,"no",None,None)
        row=m.label("XUSDT",date(2026,8,17),month_fetch=gone)
        self.assertEqual(row["status"],"MONTH_ARCHIVE_MISSING_404")

    def test_unknown_dates_rejected(self):
        m,_=load()
        with self.assertRaisesRegex(ValueError,"NON_FROZEN_DATE"):
            m.run("2026-01-01",get_symbols=lambda:([],{}))

    def test_full_run_summarizes_recall_denominator_without_trading(self):
        m,_=load()
        all_syms=[f"X{i}USDT" for i in range(758)]
        out=m.run("2026-08-17",get_symbols=lambda:(all_syms,{"archive_only_sha256":"samplehash"}),
                  evaluator=lambda s,d:{"symbol":s,"status":"VERIFIED_COMPLETE_168H",
                     **{f"gross_{kind}_ge_{n}x":bool(s=="X0USDT") for n in (2,5,10) for kind in ("high","close")}},
                  workers=2)
        self.assertEqual(out["summary"]["gross_high_ge_5x"],1)
        self.assertEqual(out["summary"]["complete_168h"],758)
        self.assertFalse(out["trading_enabled"])

if __name__ == "__main__":
    unittest.main()
