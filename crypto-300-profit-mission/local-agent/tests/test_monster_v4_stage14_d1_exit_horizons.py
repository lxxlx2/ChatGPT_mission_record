"""Stage14 isolated frozen-cohort/exits/24h parity tests; network never used."""
import importlib.util
import json
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

SOURCE=Path(__file__).resolve().parents[1]/"scripts/monster_v4_stage14_d1_exit_horizons.py"
sp=importlib.util.spec_from_file_location("monster_v4_stage14_d1_exit_horizons",SOURCE)
m=importlib.util.module_from_spec(sp)
sp.loader.exec_module(m)


class FrozenD1ExitHorizonTests(unittest.TestCase):
    def test_exactly_all_31_frozen_real_d1_events(self):
        cases,h=m.frozen_cases()
        self.assertEqual(len(cases),31)
        self.assertEqual(len(set(cases)),31)
        self.assertEqual(h,[30,120,360,720,1440])
        self.assertEqual(len({day for day,sym in cases}),5)

    def test_stage12_and_stage13_frozen_return_evidence_is_available(self):
        fixed,_=m.frozen_cases()
        prior=m.expected_24h()
        self.assertEqual(len(fixed),31)
        self.assertTrue(all((day.isoformat(),sym) in prior for day,sym in fixed))
        self.assertEqual(prior[("2026-09-17","ONEUSDT")],30.6281)
        self.assertIsNone(prior[("2026-08-17","GUNUSDT")])

    def test_horizon_research_price_proxy_default_stays_24_hours(self):
        from decimal import Decimal
        from datetime import datetime,timezone
        start=int(datetime(2026,1,1,tzinfo=timezone.utc).timestamp()*1000)
        bars=[(start+60000*i,Decimal("1"),Decimal("1"),Decimal("1"),
               Decimal("1"),Decimal("100"),1) for i in range(1550)]
        prior=m.historical._proxy_trade(bars,start,start,180000,20)
        same=m.historical._proxy_trade(bars,start,start,180000,20,1440)
        self.assertEqual(prior,same)
        short=m.historical._proxy_trade(bars,start,start,180000,20,30)
        self.assertEqual(short["status"],"PRICE_PROXY_ONLY")
        self.assertEqual(short["exit_utc"],m.historical.utc(start+(3+30)*60000))
        self.assertNotEqual(short["exit_utc"],same["exit_utc"])
        with self.assertRaisesRegex(ValueError,"INVALID_REPLAY_HOLD_MINUTES"):
            m.historical._proxy_trade(bars,start,start,180000,20,0)

    def test_same_d1_setup_rebuilt_and_all_horizons_scored(self):
        day=date(2026,9,17);sym="AVAUSDT"
        base=m.historical.parse_ms(day.isoformat()+"T12:00:00Z")-30*3600_000
        raw=[(base-360*60000+60000*i,"1","1","1","1","100",1)
             for i in range(4320)]
        def archive(symbol,d):
            offset=(d-date(2026,9,16)).days*1440
            return raw[offset:offset+1440],{"sha256":"f"*64}
        expected_setup="2026-09-17T07:00:00Z"
        def fake_proxy(bars,base,setup,delay,slip,hold_minutes=1440):
            return {"status":"PRICE_PROXY_ONLY",
                    "net_pct":-4.066663 if hold_minutes==1440 else -2.0,
                    "pnl_usdt_on_30":-1.219999 if hold_minutes==1440 else -0.6}
        with patch.object(m.historical,"replay_case",
                return_value={"setup_events":[{"utc":expected_setup}]}),\
             patch.object(m.historical,"_proxy_trade",side_effect=fake_proxy):
            result=m.run_case(day,sym,[30,120,360,720,1440],get_archive=archive)
        self.assertEqual(result["horizon_minutes_to_24h_net_price_proxy"]["1440"]["net_pct"],-4.066663)
        self.assertEqual(result["horizon_minutes_to_24h_net_price_proxy"]["30"]["net_pct"],-2.0)
        self.assertEqual(len(result["official_archive_zip_sha256"]),3)

    def test_wrong_24h_number_refused_even_if_short_horizon_is_good(self):
        day=date(2026,9,17);sym="AVAUSDT"
        base=m.historical.parse_ms("2026-09-17T12:00:00Z")-30*3600_000
        raw=[(base-360*60000+60000*i,"1","1","1","1","100",1)
             for i in range(4320)]
        def archive(symbol,d):
            offset=(d-date(2026,9,16)).days*1440
            return raw[offset:offset+1440],{"sha256":"f"*64}
        with patch.object(m.historical,"replay_case",
                return_value={"setup_events":[{"utc":"2026-09-17T07:00:00Z"}]}),\
             patch.object(m.historical,"_proxy_trade",
                return_value={"status":"PRICE_PROXY_ONLY","net_pct":50}):
            with self.assertRaisesRegex(ValueError,"STAGE14_24H_REPRODUCIBILITY_MISMATCH"):
                m.run_case(day,sym,[30,1440],get_archive=archive)

    def test_censored_remains_censored_not_zero_return(self):
        cases=[{"horizon_minutes_to_24h_net_price_proxy":{
            "30":{"status":"PRICE_PROXY_ONLY","net_pct":5,"pnl_usdt_on_30":1.5},
            "1440":{"status":"CENSORED_ZERO_VOLUME_EXIT"}}]
        stats=m.summarize(cases,[30,1440])
        self.assertEqual(stats["30"]["positive"],1)
        self.assertEqual(stats["1440"]["real_price_proxy_evaluable"],0)
        self.assertEqual(stats["1440"]["censored"],{"CENSORED_ZERO_VOLUME_EXIT":1})
        self.assertIsNone(stats["1440"]["median_net_pct"])

    def test_stage14_subset_not_claimed_to_be_all_31(self):
        pair=m.frozen_cases()[0][:1]
        def worker(day,sym,h):
            return {"day":day.isoformat(),"symbol":sym,
                    "horizon_minutes_to_24h_net_price_proxy":{
                        str(n):{"status":"CENSORED_NO_ENTRY_TRADES"} for n in h}}
        data=m.run(cases=pair,worker=worker,max_workers=1)
        self.assertEqual(data["frozen_cases_expected"],31)
        self.assertEqual(data["cases_replayed"],1)
        self.assertEqual(data["deploy_gate"],"NO_GO")
        self.assertFalse(data["historical_book_verified"])


if __name__=="__main__":
    unittest.main()
