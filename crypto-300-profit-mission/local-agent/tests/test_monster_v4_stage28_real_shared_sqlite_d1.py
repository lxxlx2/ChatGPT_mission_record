"""Stage28 real production process_queue on an actual shared SQLite."""
import hashlib
import io
import sys
import unittest
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).parents[1]/"scripts"
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
import monster_v4_stage28_real_shared_sqlite_d1 as m

def moment(s):
    return int(datetime.fromisoformat(s.replace("Z","+00:00")).timestamp()*1000)

class CandleSource:
    def __init__(self,raise_on_load=False):
        self.calls=0
        self.raise_on_load=raise_on_load
    def closed_before(self,venue,symbol,now_ms):
        self.calls+=1
        if self.raise_on_load:raise ValueError("NO_GENUINE_5M_SOURCE")
        start=(now_ms//300000)*300000
        rows=[]
        for i in range(8):
            opening=start-(8-i)*300000
            rows.append([opening,"1","1.1","0.9",str(1.00+.001*i),
                "100",opening+299999,str(100+i*5)])
        return rows
    def metadata(self):
        return [{"date":"2026-02-06","sha256":"e"*64,"publisher_verified":True}]

class SharedProcessor(unittest.TestCase):
    def test_frozen_original_production_sha_and_queue_params(self):
        contract=m.frozen()
        self.assertEqual(contract["shared_queue_contract"]["process_queue_limit"],8)
        self.assertEqual(contract["watch_events_expected"],1132)
        self.assertEqual(m.git_blob_sha(m.production.__file__),
            contract["production_source_blob_sha1"])
    def test_daily_5m_sha_and_us_microsecond_timestamp(self):
        day=datetime(2026,2,6,tzinfo=timezone.utc).date()
        start=moment("2026-02-06T00:00:00Z")
        name="TESTUSDT-5m-2026-02-06.csv"
        rows=[]
        for i in range(288):
            tick=start+i*300000
            rows.append(",".join([str(tick*1000),"1","1.1","0.9","1","50",str((tick+299999)*1000),"100","4","0","0","0"]))
        payload=("\n".join(rows)+"\n").encode()
        b=io.BytesIO()
        with zipfile.ZipFile(b,"w",zipfile.ZIP_DEFLATED) as z:z.writestr(name,payload)
        zip_data=b.getvalue()
        sha=hashlib.sha256(zip_data).hexdigest().encode()+b"  "+name.encode()
        candles,proof=m.extract_5m_zip(zip_data,sha,"TESTUSDT",day)
        self.assertEqual(len(candles),288)
        self.assertEqual(candles[0][0],start)
        self.assertEqual(candles[0][6],start+299999)
        self.assertTrue(proof["publisher_verified"])
        with self.assertRaisesRegex(ValueError,"PUBLISHER_SHA_MISMATCH"):
            m.extract_5m_zip(zip_data,b"0"*64,"TESTUSDT",day)
    def test_real_shared_SQLite_98_WATCH_burst_expires_candidates(self):
        t=moment("2026-02-06T00:36:00Z")
        arrivals=[(t,f"TEST{i:03d}USDT") for i in range(98)]
        source=CandleSource()
        result=m.shared_production_replay(arrivals,"2026-02-04",market=source)
        self.assertEqual(result["watch_arrivals"],98)
        self.assertEqual(result["queue_candidates"],98)
        self.assertEqual(result["max_pending_before_poll"],98)
        self.assertEqual(result["event_counts"]["WATCH_EARLY"],98)
        self.assertGreaterEqual(result["candidate_status_counts"].get("LATE",0),50)
        self.assertTrue(result["actual_shared_sqlite_process_queue"])
        self.assertFalse(result["global_observe_snapshot_replayed"])
        self.assertGreater(source.calls,0)
    def test_non_aligned_watch_causes_fail_closed(self):
        t=moment("2026-02-06T00:37:00Z")
        with self.assertRaisesRegex(ValueError,"WATCH_NOT_ON_ORIGINAL_THREE_MINUTE_POLL"):
            m.shared_production_replay([(t,"TESTUSDT")],"2026-02-04",market=CandleSource())
    def test_bad_source_fails_instead_of_claiming_no_setup(self):
        t=moment("2026-02-06T00:36:00Z")
        with self.assertRaisesRegex(ValueError,"NO_GENUINE_5M_SOURCE"):
            m.shared_production_replay([(t,"TESTUSDT")],"2026-02-04",
                                    market=CandleSource(raise_on_load=True))
    def test_source_parser_rejects_unsupported_timestamp_units(self):
        with self.assertRaisesRegex(ValueError,"UNKNOWN_OFFICIAL_TIMESTAMP_UNIT"):
            m.normalize_ts(1000)
    def test_queue_injected_watch_does_not_place_orders_or_send_email(self):
        t=moment("2026-02-06T00:36:00Z")
        result=m.shared_production_replay([(t,"TESTUSDT")],"2026-02-04",market=CandleSource())
        self.assertFalse(result["actual_real_money_order_or_email"])
        self.assertEqual(result["queue_candidates"],1)

if __name__=="__main__":
    unittest.main()
