"""Stage22 pre-signal source SHA / aggressor classification / no-lookahead."""
import hashlib
import importlib.util
import io
import json
import sys
import types
import unittest
import zipfile
from datetime import datetime,timezone
from pathlib import Path

FILE=Path(__file__).parents[1]/"scripts"/"monster_v4_stage22_aggtrade_flow.py"

def load():
    fake=types.ModuleType("monster_v4_stage21_aggregate")
    fake.ROOT=Path(__file__).parents[2]/"monster"/"evidence"
    fake.read_zip=lambda p,e: {}
    sys.modules[fake.__name__]=fake
    spec=importlib.util.spec_from_file_location("stage22_unit",FILE)
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

def fixture(symbol="XUSDT",day="2025-04-09", setup="2025-04-09T12:00:00Z",
            corrupt_checksum=False, future_only=False):
    base=int(datetime(2025,4,9,12,tzinfo=timezone.utc).timestamp()*1000000)
    lines=[
        [0,"10","5",0,0,str(base-55*60*1000000),"true","true"],
        [1,"10","10",1,1,str(base-12*60*1000000),"false","true"],
        [2,"10","8",2,2,str(base-4*60*1000000),"true","true"],
        [3,"20","9",3,3,str(base),"false","true"],
    ]
    if future_only:
        lines=[lines[-1]]
    data=("\n".join(",".join(map(str,row)) for row in lines)+"\n").encode()
    buff=io.BytesIO()
    with zipfile.ZipFile(buff,"w") as f:
        f.writestr(f"{symbol}-aggTrades-{day}.csv",data)
    zipped=buff.getvalue()
    sha=hashlib.sha256(zipped).hexdigest()
    def fetch(url,n):
        if url.endswith(".CHECKSUM"):
            return (("0"*64 if corrupt_checksum else sha)+"  file.zip\n").encode()
        return zipped
    return fetch

class SourceTests(unittest.TestCase):
    def test_official_aggressor_sell_and_buy_direction(self):
        m=load()
        value=m.analyze("XUSDT","2025-04-09","2025-04-09T12:00:00Z",fixture())
        self.assertEqual(value["status"],"VERIFIED_PRE_SIGNAL_AGGTRADES")
        self.assertEqual(value["prior_60m_aggtrade_rows"],3)
        self.assertAlmostEqual(value["prior_60m_aggressor_buy_quote_share"],100/230,places=6)
        self.assertAlmostEqual(value["prior_5m_aggressor_buy_quote_share"],0)
        self.assertTrue(value["strictly_before_setup"])
    def test_future_trade_excluded_even_at_exact_setup(self):
        m=load()
        r=m.analyze("XUSDT","2025-04-09","2025-04-09T12:00:00Z",
                    fixture(future_only=True))
        self.assertEqual(r["status"],"CENSORED_NO_PRE_SIGNAL_AGGTRADES")
    def test_bad_checksum_rejected(self):
        m=load()
        with self.assertRaisesRegex(ValueError,"PUBLISHED_SHA_MISMATCH"):
            m.analyze("XUSDT","2025-04-09","2025-04-09T12:00:00Z",
                      fixture(corrupt_checksum=True))
    def test_evaluation_fail_closed_and_not_counted_no_sell(self):
        m=load()
        case={"date":"2025-04-09","symbol":"XUSDT","setup_utc":"2025-04-09T12:00:00Z",
              "exit_label":"STOP","exit_status":"PRICE_PROXY_ONLY",
              "exit_utc":None,"original_net_pct":-8,"original_quality":{}}
        res=m.evaluate(case,fetch=fixture(corrupt_checksum=True))
        self.assertEqual(res["flow"]["status"],"SOURCE_INTEGRITY_REJECTED")
        s=m.summary([res])
        self.assertEqual(s["STOP"]["n"],1)
        self.assertEqual(s["STOP"]["verified"],0)
    def test_no_arbitrary_symbol_untrusted_urls(self):
        m=load()
        with self.assertRaisesRegex(ValueError,"UNSAFE_SYMBOL"):
            m.source_url("X/../../BTCUSDT","2025-04-09")
    def test_frozen_aggregate_not_production(self):
        m=load()
        case={"date":"2025-04-09","symbol":"XUSDT","setup_utc":"2025-04-09T12:00:00Z",
              "exit_label":"STOP","exit_status":"PRICE_PROXY_ONLY",
              "exit_utc":None,"original_net_pct":-8,"original_quality":{}}
        out=m.evaluate(case,fetch=fixture())
        self.assertEqual(m.summary([out])["STOP"]["verified"],1)
        self.assertNotIn("buy_signal",out)
if __name__=="__main__":
    unittest.main()
