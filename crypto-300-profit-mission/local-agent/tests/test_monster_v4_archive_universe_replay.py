"""Hermetic Stage12 full-universe source integrity + fixed time test gate."""
import hashlib
import importlib.util
import io
import json
import urllib.error
import unittest
import zipfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

SRC=Path(__file__).resolve().parents[1]/"scripts/monster_v4_archive_universe_replay.py"
spec=importlib.util.spec_from_file_location("monster_v4_archive_universe_replay",SRC)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def archive_for_day(symbol,day):
    t=int(datetime(day.year,day.month,day.day,tzinfo=timezone.utc).timestamp()*1000)
    lines=[]
    for i in range(1440):
        ts=(t+60000*i)*1000
        lines.append(",".join([str(ts),"1","1","1","1","10",str(ts+59999999),
                               "200","1","0","0","0"]))
    memory=io.BytesIO()
    with zipfile.ZipFile(memory,"w",zipfile.ZIP_DEFLATED) as z:
        z.writestr(symbol+"-1m-"+day.isoformat()+".csv","\n".join(lines)+"\n")
    data=memory.getvalue()
    return data,(hashlib.sha256(data).hexdigest()+"  name.zip").encode()


def synthetic_downloader(url,max_bytes=m.source.MAX_ZIP_BYTES):
    bits=url.split("/")
    name=bits[-1].removesuffix(".CHECKSUM")
    symbol=name.split("-1m-")[0]
    day=date.fromisoformat(name.split("-1m-")[1].removesuffix(".zip"))
    z,h=archive_for_day(symbol,day)
    return h if url.endswith(".CHECKSUM") else z


class FullMarketArchiveReplayTests(unittest.TestCase):
    def test_all_504_current_spot_usdt_names_are_frozen(self):
        data=json.loads(m.REGISTRY.read_text(encoding="utf-8"))
        syms=m.validate_manifest(data)
        self.assertEqual(len(syms),504)
        self.assertEqual(len(set(syms)),504)
        self.assertEqual(m.ANCHOR,"2026-09-17T12:00:00Z")

    def test_official_archive_minute_source_feeds_same_real_v4(self):
        case=m.run_symbol("LTCUSDT",download=synthetic_downloader)
        self.assertEqual(case["status"],"COMPLETE_60H")
        self.assertEqual(case["verified_minute_bars"],3600)
        self.assertEqual(case["polls"],240)
        self.assertEqual(case["watch_events"],0)
        self.assertEqual(case["setups"],0)
        self.assertEqual(len(case["archive_sha256"]),3)

    def test_market_subset_never_misrepresented_as_full_universe(self):
        symbols=m.validate_manifest(json.loads(m.REGISTRY.read_text(encoding="utf-8")))
        def result(symbol):
            return {"symbol":symbol,"status":"SOURCE_MISSING"}
        r=m.run(symbols[:2],max_workers=2,worker=result)
        self.assertFalse(r["summary"]["full_universe_attempted"])
        self.assertEqual(r["summary"]["pre_registered_total"],504)
        self.assertEqual(r["summary"]["source_status_counts"],{"SOURCE_MISSING":2})
        self.assertEqual(r["summary"]["assumed_20bps_per_side_net_return_median_pct"],None)
        with self.assertRaisesRegex(ValueError,"NOT_A_MANIFEST_SUBSET"):
            m.run(["FAKEUSDT"],max_workers=1,worker=result)

    def test_tampered_checksum_blocks_scoring(self):
        def forged(url,max_bytes=m.source.MAX_ZIP_BYTES):
            if url.endswith(".CHECKSUM"):
                return b"0"*64+b"  forged.zip"
            return synthetic_downloader(url)
        d=m.run_symbol("LTCUSDT",download=forged)
        self.assertEqual(d["status"],"SOURCE_INTEGRITY_REJECTED")

    def test_historical_not_listed_404_is_explicit_not_no_watch(self):
        def unavailable(url,max_bytes=m.source.MAX_ZIP_BYTES):
            raise urllib.error.HTTPError(url,404,"Not Found",None,None)
        d=m.run_symbol("LTCUSDT",download=unavailable)
        self.assertEqual(d["status"],"SOURCE_MISSING")
        self.assertNotIn("watch_events",d)


if __name__=="__main__":
    unittest.main()
