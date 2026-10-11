"""Stage30 predeclared new-calendar capital/burst gate source QA."""
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
SCRIPTS=Path(__file__).parents[1]/"scripts"
if str(SCRIPTS) not in sys.path:sys.path.insert(0,str(SCRIPTS))
import monster_v4_stage30_aggregate as m

def event(symbol,utc,return_pct):
    return {"date":"2025-01-19","symbol":symbol,"watch_utc":utc,
      "cost_proxies":{"20":{"status":"PRICE_PROXY_ONLY","net_pct":return_pct},
                      "100":{"status":"PRICE_PROXY_ONLY","net_pct":return_pct-1.5}},
      "bucket":"BURST_8PLUS","gross_high_2x_in_frozen_168h":False,
      "minutes_until_first_2x_if_valid":None}
class Tests(unittest.TestCase):
    def test_six_frozen_new_months_before_source_fetch(self):
        p=m.immutable()
        self.assertEqual(p["new_dates_UTC"],["2025-01-19","2025-04-19","2025-07-19","2025-10-19","2026-04-19","2026-07-19"])
        self.assertTrue(p["must_not_tune_after_new_data"])
    def test_missing_frozen_dates_or_shards_not_accepted_as_success(self):
        with self.assertRaisesRegex(ValueError,"INCOMPLETE_FULL_SIX_DATE_SHARDS"):
            m.register({})
    def test_original_source_SHA_failure_stops_read(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"fake.zip"
            with zipfile.ZipFile(path,"w") as z:z.writestr("test","wrong")
            with self.assertRaisesRegex(ValueError,"SOURCE_ZIP_SHA_CHANGED"):
                m.decode(path,{"date":"2025-01-19","shard":0,"zip_sha256":"f"*64})
    def test_concurrent_98_watches_ten_slots_never_overfund(self):
        now="2025-01-20T00:36:00Z"
        rows=[event(f"T{i:03d}USDT",now,10) for i in range(98)]
        v=m.funded(rows,20)
        out=v["funded_cash_by_recovery_assumption"]["300USDT_10SLOT_CENSORED_RECOVERY_100PCT"]
        self.assertEqual(out["counts"]["selected"],10)
        self.assertEqual(out["counts"]["skip_slots_busy"],88)
        self.assertEqual(out["realized_proxy_profit_USDT"],30)
    def test_proxy_censor_and_original_overlap_not_called_real_fills(self):
        a=event("AUSDT","2025-01-20T00:36:00Z",-6)
        b=event("BUSDT","2025-01-20T00:36:00Z",0)
        b["cost_proxies"]["20"]={"status":"CENSORED_ZERO_VOLUME_EXIT","net_pct":None}
        c=event("CUSDT","2025-01-20T00:36:00Z",0)
        c["cost_proxies"]["20"]={"status":"SKIP_SAME_SYMBOL_24H_CAPITAL_OCCUPIED"}
        out=m.arm_censored([a,b,c],20)
        self.assertEqual(out["proxy_evaluable"],1)
        self.assertEqual(out["source_censored_excluding_overlap"],1)
        self.assertEqual(out["same_symbol_24h_overlap_skip"],1)
    def test_new_research_not_prematurely_production(self):
        p=m.immutable()
        self.assertEqual(p["monster_deployment"],"NO_GO")
        self.assertEqual(p["independent_other_AI_review"],"NOT_DONE")
if __name__=="__main__":unittest.main()
