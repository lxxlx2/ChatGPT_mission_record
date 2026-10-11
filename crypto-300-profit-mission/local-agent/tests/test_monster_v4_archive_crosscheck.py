"""Offline unit tests for Binance public ZIP source verification and ms/us rules."""
import hashlib
import importlib.util
import io
import unittest
import zipfile
from datetime import date, datetime, timezone
from pathlib import Path

P=Path(__file__).resolve().parents[1]/"scripts/monster_v4_archive_crosscheck.py"
sp=importlib.util.spec_from_file_location("monster_v4_archive_crosscheck",P)
m=importlib.util.module_from_spec(sp)
sp.loader.exec_module(m)


def sample_zip(symbol="ADAUSDT", day=date(2026,9,17)):
    beginning=int(datetime(day.year,day.month,day.day,tzinfo=timezone.utc).timestamp()*1000)
    rows=[]
    for i in range(1440):
        us=(beginning+i*60000)*1000
        rows.append(",".join([str(us),"1.0","1.0","1.0","1.0","0",
                               str(us+59999999),"100.0","0","0","0","0"]))
    filename=symbol+"-1m-"+day.isoformat()+".csv"
    memory=io.BytesIO()
    with zipfile.ZipFile(memory,"w",zipfile.ZIP_DEFLATED) as z:
        z.writestr(filename,"\n".join(rows)+"\n")
    data=memory.getvalue()
    return data,(hashlib.sha256(data).hexdigest()+"  "+filename+".zip\n").encode()


class BinanceArchiveCrosscheckTests(unittest.TestCase):
    def test_real_frozen_rest_input_four_preregistered(self):
        self.assertEqual(len(m.PILOT),4)
        for symbol in m.PILOT:
            with self.subTest(symbol=symbol):
                self.assertEqual(len(m.load_rest(symbol)),3600)

    def test_exact_timestamp_microseconds_converts_to_milliseconds(self):
        compressed,checksum=sample_zip()
        rows,meta=m.extract_verified_archive(compressed,checksum,"ADAUSDT",date(2026,9,17))
        self.assertEqual(len(rows),1440)
        self.assertEqual(rows[1][0]-rows[0][0],60000)
        self.assertTrue(meta["verified_published_sha256"])

    def test_checksum_tamper_fails_before_csv_open(self):
        compressed,checksum=sample_zip()
        with self.assertRaisesRegex(ValueError,"CHECKSUM_MISMATCH"):
            m.extract_verified_archive(compressed+b"altered",checksum,"ADAUSDT",date(2026,9,17))

    def test_wrong_symbol_member_rejected(self):
        compressed,checksum=sample_zip(symbol="BNBUSDT")
        with self.assertRaisesRegex(ValueError,"UNEXPECTED_ARCHIVE_CSV_MEMBER"):
            m.extract_verified_archive(compressed,checksum,"ADAUSDT",date(2026,9,17))

    def test_fake_interval_or_date_is_rejected(self):
        compressed,checksum=sample_zip(day=date(2026,9,16))
        with self.assertRaisesRegex(ValueError,"GAPPED_ARCHIVE_DAY|UNEXPECTED_ARCHIVE_CSV_MEMBER"):
            m.extract_verified_archive(compressed,checksum,"ADAUSDT",date(2026,9,17))

    def test_only_exact_frozen_symbol_is_allowed(self):
        with self.assertRaisesRegex(ValueError,"NOT_FROZEN_STAGE10"):
            m.verify_crosscheck("BTCUSDT",lambda url,n=1000: b"")


if __name__=="__main__":
    unittest.main()
