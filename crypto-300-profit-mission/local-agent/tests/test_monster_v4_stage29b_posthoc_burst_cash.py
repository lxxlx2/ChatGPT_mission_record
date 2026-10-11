"""Stage29b source integrity and no-overdraft checks for posthoc burst subset."""
import sys
import unittest
import tempfile
from pathlib import Path
ROOT=Path(__file__).parents[1]/"scripts"
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
import monster_v4_stage29b_posthoc_burst_cash as m
from monster_v4_stage27_shared_queue_cash_ledger import money_ledger

def proxy(symbol,when,pct):
    return {"date":"2026-02-04","symbol":symbol,"watch_utc":when,
            "proxy_status":"PRICE_PROXY_ONLY","net_pct":pct}
class Tests(unittest.TestCase):
    def test_contract_explicit_posthoc_and_not_live_buy(self):
        import json
        x=json.loads(m.PRE.read_text())
        self.assertTrue(x["context"].startswith("Burst"))
        self.assertEqual(x["other_AI_review"],"NOT_DONE")
        self.assertEqual(x["deployment"],"NO_GO")
    def test_missing_original_source_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"unverified.zip";path.write_bytes(b"bogus")
            with self.assertRaisesRegex(ValueError,"SOURCE_ZIP_SHA_MISMATCH"):
                m.original(path)
    def test_all_36_source_shards_are_mandatory(self):
        with self.assertRaisesRegex(ValueError,"ALL_ORIGINAL_36_REQUIRED"):
            m.funded({}, {}, [])
    def test_same_second_one_30u_slot_uses_lexical_not_future_profit(self):
        iso="2026-02-06T00:36:00Z"
        rows=[proxy("ZZZUSDT",iso,100),proxy("AAAUSDT",iso,-20)]
        rows.sort(key=lambda r:(r["watch_utc"],r["date"],r["symbol"]))
        result=money_ledger(rows,30,1,"FIXED_30U",20,100)
        self.assertEqual(result["selected_cases"][0]["symbol"],"AAAUSDT")
        self.assertEqual(result["final_cash_USDT"],24)
        self.assertEqual(result["counts"]["skip_slots_busy"],1)
    def test_ten_slots_restrict_ninety_eight_simultaneous(self):
        iso="2026-02-06T00:36:00Z"
        rows=[proxy("S%03dUSDT"%i,iso,10) for i in range(98)]
        outcome=money_ledger(rows,300,10,"FIXED_30U",20,100)
        self.assertEqual(outcome["counts"]["selected"],10)
        self.assertEqual(outcome["counts"]["skip_slots_busy"],88)
        self.assertEqual(outcome["final_cash_USDT"],330)
    def test_censored_unknown_exit_not_real_profit(self):
        iso="2026-02-06T00:36:00Z"
        c={"date":"2026-02-04","symbol":"XYZUSDT","watch_utc":iso,
           "proxy_status":"CENSORED_ZERO_VOLUME_EXIT","net_pct":None}
        ok=money_ledger([c],30,1,"FIXED_30U",20,100)
        bad=money_ledger([c],30,1,"FIXED_30U",20,0)
        self.assertEqual(ok["final_cash_USDT"],30)
        self.assertEqual(bad["final_cash_USDT"],0)

if __name__=="__main__":unittest.main()
