"""Stage23 evidence reaggregation and chronological limited-capital safeguards."""
import importlib.util
import unittest
from pathlib import Path
SOURCE=Path(__file__).parents[1]/"scripts"/"monster_v4_stage23_aggregate.py"
spec=importlib.util.spec_from_file_location("stage23_aggregator_test",SOURCE)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

ARM=m.ARMS[1]

def make(symbol,time,price):
    p={"status":"PRICE_PROXY_ONLY","net_pct":price,
       "exit_utc":"2025-03-23T12:00:00Z"}
    return ("2025-03-23",{"symbol":symbol,"first_v4_d1_utc":time,
         "frozen_arm_proxies":{ARM:p}})

class AggregatorTests(unittest.TestCase):
    def test_slot_is_deterministic_when_two_same_second_setups(self):
        a=make("AAAUSDT","2025-03-23T10:00:00Z",-8)
        b=make("BBBUSDT","2025-03-23T10:00:00Z",18)
        result=m.single_slot([b,a],ARM)
        self.assertEqual(result["selected_by_clock"],1)
        self.assertEqual(result["skipped_capital_busy"],1)
        self.assertEqual(result["simulated_30u_net_usdt"],-2.4)
    def test_censored_is_never_zero_pnl(self):
        trades=[{"status":"PRICE_PROXY_ONLY","net_pct":-8.55},
                {"status":"CENSORED_ZERO_VOLUME_EXIT"}]
        result=m.metrics(trades)
        self.assertEqual(result["censored"],1)
        self.assertEqual(result["evaluable"],1)
        self.assertEqual(result["sum_independent_30u"],-2.565)
    def test_empty_arm_cannot_pass(self):
        result=m.metrics([])
        self.assertIsNone(result["median_net_pct"])
        self.assertEqual(result["selected"],0)
    def test_source_digests_not_optional(self):
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".zip") as f:
            f.write(b"invalid");f.flush()
            with self.assertRaisesRegex(ValueError,"SHA256_MISMATCH"):
                m.read_zip(Path(f.name),{"date":"2025-03-23",
                    "zip_sha256":"a"*64,"raw_json_sha256":"b"*64})
if __name__=="__main__":
    unittest.main()
