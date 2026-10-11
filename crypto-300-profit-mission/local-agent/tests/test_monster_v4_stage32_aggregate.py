"""Stage32 paired market economics, source SHA, 300U not overdraft invariants."""
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
S=Path(__file__).parents[1]/"scripts"
if str(S) not in sys.path:sys.path.insert(0,str(S))
import monster_v4_stage32_aggregate as m

def row(sym="TESTUSDT",p=5,invalid=False):
    t={"watch_utc":"2025-03-20T12:00:00Z",
       "proxy_20bps":{"status":"PRICE_PROXY_ONLY","net_pct":p},
       "proxy_100bps":{"status":"PRICE_PROXY_ONLY","net_pct":p-1.6}}
    if invalid:
        t={"watch_utc":"2025-03-20T12:00:00Z",
            "proxy_20bps":{"status":"CENSORED_ZERO_VOLUME_EXIT"},
            "proxy_100bps":{"status":"CENSORED_ZERO_VOLUME_EXIT"}}
    return {"date":"2025-03-19","symbol":sym,"status":"COMPLETE_BOTH_168H",
        "V4_original3m":{"watch_count":1,"trade_proxies":[t]},
        "V4_candidate1m":{"watch_count":1,"trade_proxies":[t]}}

class Cases(unittest.TestCase):
    def test_no_one_or_five_day_partial_market_accepted(self):
        with self.assertRaisesRegex(ValueError,"MISSING_ANY_OF_36"):
            m.original_cohort({})
    def test_no_wrong_archive_hash_accepted(self):
        with tempfile.TemporaryDirectory() as td:
            x=Path(td)/"source.zip"
            with zipfile.ZipFile(x,"w") as f:f.writestr("fake.json","{}")
            with self.assertRaisesRegex(ValueError,"ARTIFACT_ZIP_SHA256_MISMATCH"):
                m.verify_zip(x,{"zip_sha256":"a"*64})
    def test_two_cost_scenarios_both_require_actual_same_candle_source(self):
        valid=[row("AUSDT",p=10),row("BUSDT",p=-5)]
        s=m.arm_economics(valid,"V4_original3m")
        self.assertEqual(s["20"]["valid_trade_proxies"],2)
        self.assertEqual((s["20"]["wins"],s["20"]["losses"]),(1,1))
        self.assertGreater(s["20"]["median_net_pct"],s["100"]["median_net_pct"])
        funded=s["20"]["cash_funded_no_overdraft"]["300U_10SLOT_20BPS_CENSORED_100PCT"]
        self.assertFalse(funded["cash_overdrawn"])
    def test_censored_missing_exit_not_written_as_profit(self):
        r=m.arm_economics([row("AUSDT",invalid=True)],"V4_candidate1m")
        self.assertEqual(r["20"]["valid_trade_proxies"],0)
        self.assertEqual(r["20"]["source_exit_censored"],1)
        good=r["20"]["cash_funded_no_overdraft"]["30U_1SLOT_20BPS_CENSORED_100PCT"]
        fail=r["20"]["cash_funded_no_overdraft"]["30U_1SLOT_20BPS_CENSORED_0PCT"]
        self.assertEqual(good["final_cash_USDT"],30)
        self.assertEqual(fail["final_cash_USDT"],0)
    def test_unexpected_status_cannot_be_traded(self):
        x=row()
        x["V4_candidate1m"]["trade_proxies"][0]["proxy_20bps"]={"status":"UNVERIFIED_PRICE","net_pct":1000}
        with self.assertRaisesRegex(ValueError,"BAD_REAL_MINUTE"):
            m.arm_economics([x],"V4_candidate1m")
if __name__=="__main__":unittest.main()
