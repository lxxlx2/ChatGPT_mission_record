"""Stage33 regressions: descriptive labels, immutable sources and cash attribution."""
import sys
import tempfile
import unittest
from pathlib import Path

S = Path(__file__).parents[1] / "scripts"
if str(S) not in sys.path:
    sys.path.insert(0,str(S))
import monster_v4_stage33_readonly_loss_attribution as m


class Stage33Tests(unittest.TestCase):
    def test_missing_36_originals_rejected_before_source_download(self):
        with self.assertRaisesRegex(ValueError,"NOT_ALL_TRUE_STAGE32_ORIGINALS"):
            m.actual_reports([])

    def test_frozen_final_byte_sha_refused(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)/"fake-final.zip"
            p.write_bytes(b"not the frozen final")
            with self.assertRaisesRegex(ValueError,"FINAL_ZIP_SHA_CHANGED"):
                m.load_frozen_final(p)

    def test_24h_loss_and_future_high_are_diagnostic_only(self):
        cases = [{
            "V4_original3m":{"trade_proxies":[
                {"proxy_20bps":{"status":"PRICE_PROXY_ONLY","net_pct":-12.5,
                                "max_high_excursion_pct":12.3}},
                {"proxy_20bps":None},
                {"proxy_20bps":{"status":"CENSORED_ZERO_VOLUME_EXIT"}}
            ]}
        }]
        r = m.inspect(cases,"V4_original3m",20)
        self.assertEqual(r["all_watch"],3)
        self.assertEqual(r["losing"],1)
        self.assertEqual(r["winning"],0)
        self.assertEqual(r["losing_with_high_excursion_over_10pct"],1)
        self.assertEqual(r["status_counts"]["SKIP_SAME_SYMBOL_24H_CAPITAL_OCCUPIED"],1)
        self.assertIn("not an executable",r["warning"])

    def test_cash_gross_conservation_and_by_date(self):
        sample = {"selected_cases":[
            {"date":"2025-03-19","symbol":"AUSDT","watch_utc":"2025-03-19T09:00:00Z",
             "entry_USDT":30,"assumed_exit_USDT":21,"source_status":"PRICE_PROXY_ONLY"},
            {"date":"2025-03-19","symbol":"BUSDT","watch_utc":"2025-03-20T09:00:00Z",
             "entry_USDT":30,"assumed_exit_USDT":36,"source_status":"PRICE_PROXY_ONLY"},
            {"date":"2025-06-19","symbol":"CUSDT","watch_utc":"2025-06-20T09:00:00Z",
             "entry_USDT":30,"assumed_exit_USDT":30,"source_status":"CENSORED_ZERO_VOLUME_EXIT"},
        ]}
        r=m.split_funded(sample)
        self.assertEqual((r["gross_selected_losses_USDT"],r["gross_selected_gains_USDT"]),(9,6))
        self.assertEqual(r["by_date"]["2025-03-19"]["settled_proxy_PnL_USDT"],-3)
        self.assertEqual(r["by_date"]["2025-06-19"]["unverified_exit"],1)
        self.assertEqual(r["top10_gross_loss_fraction"],1)

    def test_empty_book_has_no_invented_returns(self):
        r=m.split_funded({"selected_cases":[]})
        self.assertEqual(r["gross_selected_losses_USDT"],0)
        self.assertEqual(r["gross_selected_gains_USDT"],0)
        self.assertIsNone(r["top10_gross_loss_fraction"])

if __name__=="__main__":
    unittest.main()
