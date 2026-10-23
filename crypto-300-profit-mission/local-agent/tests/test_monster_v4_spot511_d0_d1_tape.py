"""Stage166-verified cross-day D0 and actual OHLC 5m D1 test fixtures."""
import hashlib
import sys
import tempfile
import unittest
import zipfile
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import monster_v4_spot511_d0_d1_tape as m

ROSTER = sorted(["BTCUSDT"]+[f"Q{i:03d}USDT" for i in range(510)])


def official_day(root, day, *, signal_at=None, zero_at=None, corrupt_sha=False):
    zip_path,checksum = m.d0.stage166.daily_paths(root,"BTCUSDT",day)
    zip_path.parent.mkdir(parents=True,exist_ok=True)
    ts = int(datetime.combine(day,datetime.min.time(),timezone.utc).timestamp())*1_000_000
    rows=[]
    for i in range(1440):
        at=ts+i*60_000_000
        price=Decimal("1.12") if signal_at is not None and i>=signal_at else Decimal("1.00")
        open_price=price
        high=price+Decimal("0.01")
        low=price-Decimal("0.01")
        quote=Decimal(0) if zero_at==i else Decimal(1200)
        rows.append(f"{at},{open_price},{high},{low},{price},10,{at+59_999_999},{quote},1,1,1,0")
    with zipfile.ZipFile(zip_path,"w",zipfile.ZIP_DEFLATED) as z:
        z.writestr(f"BTCUSDT-1m-{day.isoformat()}.csv","\n".join(rows)+"\n")
    digest=hashlib.sha256(zip_path.read_bytes()).hexdigest()
    checksum.write_text(("f"*64 if corrupt_sha else digest)+"  "+zip_path.name+"\n")


class TapeTests(unittest.TestCase):
    def load(self,path,asof="2026-10-18T12:00:00+00:00"):
        return m.VerifiedClosedMinuteTape(path,"BTCUSDT",roster=ROSTER,
             asof_utc=datetime.fromisoformat(asof))

    def test_first_tick_d0_and_d1_are_closed_only(self):
        with tempfile.TemporaryDirectory() as root:
            official_day(root,date(2026,10,16))
            official_day(root,date(2026,10,17),signal_at=1327)
            t=self.load(root)
            self.assertEqual(t.d0_at(m.d0.START_MS)["lastPrice"],"1.00")
            self.assertEqual(t.d0_at(m.d0.START_MS)["quoteVolume"],"1728000")
            self.assertEqual(t.d0_at(m.d0.START_MS+3*60_000)["lastPrice"],"1.12")
            bars=t.six_closed_5m(m.d0.START_MS)
            self.assertEqual(len(bars),6)
            self.assertEqual(bars[-1][6],int(datetime(2026,10,17,22,5,tzinfo=timezone.utc).timestamp()*1000)-1)
            self.assertEqual(bars[-1][4],"1.00")
            future_bar=t.six_closed_5m(m.d0.START_MS+6*60_000)
            self.assertEqual(future_bar[-1][4],"1.12")
            self.assertEqual(future_bar[-1][7],"6000")
            self.assertEqual(t.d1_fetch("spot","BTCUSDT",m.d0.START_MS),bars)
            self.assertFalse(t.readiness()["d0_quote24_is_live_ticker"])

    def test_missing_day_blocks_d0_but_d1_unblocks_after_30min(self):
        with tempfile.TemporaryDirectory() as root:
            official_day(root,date(2026,10,17))
            t=self.load(root)
            self.assertIsNone(t.d0_at(m.d0.START_MS))
            self.assertEqual(len(t.six_closed_5m(m.d0.START_MS)),6)
            at=int(datetime(2026,10,18,0,30,tzinfo=timezone.utc).timestamp()*1000)
            with self.assertRaisesRegex(ValueError,"TAPE_D1_CENSORED"):
                t.six_closed_5m(at)

    def test_sha_tamper_censors_both_inputs(self):
        with tempfile.TemporaryDirectory() as root:
            official_day(root,date(2026,10,16),corrupt_sha=True)
            official_day(root,date(2026,10,17))
            t=self.load(root)
            self.assertIn("SOURCE_REJECTED_OR_INCOMPLETE",t.readiness()["day_counts"])
            self.assertIsNone(t.d0_at(m.d0.START_MS))
            self.assertEqual(len(t.six_closed_5m(m.d0.START_MS)),6)

    def test_future_date_bytes_must_not_appear(self):
        with tempfile.TemporaryDirectory() as root:
            official_day(root,date(2026,10,17))
            official_day(root,date(2026,10,18))
            t=self.load(root)
            self.assertIn("2026-10-18",t.readiness()["day_states"])
            self.assertEqual(t.readiness()["day_states"]["2026-10-18"],"UTC_DAY_NOT_YET_ENDED")
            at=int(datetime(2026,10,18,0,6,tzinfo=timezone.utc).timestamp()*1000)
            with self.assertRaisesRegex(ValueError,"TAPE_D1_CENSORED"):
                t.six_closed_5m(at)

    def test_zero_quote_kept_as_zero_original_d1_may_reject_it(self):
        with tempfile.TemporaryDirectory() as root:
            official_day(root,date(2026,10,16))
            official_day(root,date(2026,10,17),zero_at=1320)
            t=self.load(root)
            bars=t.six_closed_5m(m.d0.START_MS)
            self.assertEqual(len(bars),6)
            self.assertEqual(bars[0][7],"6000")
            self.assertEqual(bars[-1][7],"4800")

    def test_reject_wrong_venue_and_timing(self):
        with tempfile.TemporaryDirectory() as root:
            t=self.load(root)
            with self.assertRaisesRegex(ValueError,"VENUE_OR_SYMBOL"):
                t.d1_fetch("futures","BTCUSDT",m.d0.START_MS)
            with self.assertRaisesRegex(ValueError,"TAPE_D0_REQUIRES_3MIN"):
                t.d0_at(m.d0.START_MS+60_000)
            with self.assertRaisesRegex(ValueError,"TAPE_D1_REQUIRES_3MIN"):
                t.six_closed_5m(m.d0.START_MS+60_000)
            with self.assertRaisesRegex(ValueError,"TAPE_ASOF_NEEDS_TIMEZONE"):
                m.VerifiedClosedMinuteTape(root,"BTCUSDT",asof_utc=datetime(2026,10,18),roster=ROSTER)
