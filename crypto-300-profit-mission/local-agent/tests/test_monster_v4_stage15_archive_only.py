"""Offline failure-mode checks for Stage15 archived Spot inventory and same V4 replay."""
import importlib.util
import json
import sys
import tempfile
import types
import unittest
import urllib.error
from datetime import date
from pathlib import Path

FILE = Path(__file__).parents[1] / "scripts" / "monster_v4_stage15_archive_only.py"

def load():
    stub = types.ModuleType("monster_v4_archive_universe_replay")
    stub.REGISTRY = Path(tempfile.gettempdir()) / "monster-stage15-test-registry.json"
    stub.REGISTRY.write_text(json.dumps({"frozen_symbols":["AAAUSDT","BBBUSDT"]}))
    stub.validate_manifest = lambda data: data["frozen_symbols"]
    stub.source = types.SimpleNamespace(zip_url=lambda sym, day:f"https://x/{sym}-{day}")
    stub.run_symbol = lambda *args, **kwargs: None
    sys.modules[stub.__name__] = stub
    spec = importlib.util.spec_from_file_location("stage15_testable", FILE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def listing(symbols, truncated=False, continuation=None):
    prefix = "data/spot/daily/klines/"
    entries = "".join(f"<CommonPrefixes><Prefix>{prefix}{s}/</Prefix></CommonPrefixes>" for s in symbols)
    token = f"<NextContinuationToken>{continuation}</NextContinuationToken>" if continuation else ""
    return (f'<ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">'
            f"<Prefix>{prefix}</Prefix><IsTruncated>{str(truncated).lower()}</IsTruncated>"
            f"{entries}{token}</ListBucketResult>").encode()

class Stage15Tests(unittest.TestCase):
    def test_pagination_and_current504_difference(self):
        m = load()
        responses = iter([listing(["ZZZUSDT","AAAUSDT"], True, "next1"),
                          listing(["BBBUSDT","ZUSDT","BTCFDUSD"])])
        data = m.inventory(lambda url: next(responses))
        self.assertEqual(data["archive_only_symbols"], ["ZUSDT","ZZZUSDT"])
        self.assertEqual(data["all_archive_usdt_count"], 4)

    def test_repeated_continuation_rejected(self):
        m = load()
        responses = iter([listing(["AAAUSDT"], True, "same"),
                          listing(["BBBUSDT"], True, "same")])
        with self.assertRaisesRegex(ValueError, "BAD_CONTINUATION"):
            m.list_ever_spot_symbols(lambda url: next(responses))

    def test_current_missing_archive_not_silently_classified_as_delisted(self):
        m = load()
        data = m.inventory(lambda url: listing(["AAAUSDT","ZZZUSDT"]))
        self.assertEqual(data["current_missing_archive_symbols"], ["BBBUSDT"])

    def test_unavailable_historical_date_not_zero_signal(self):
        m = load()
        def respond(url, *, method):
            raise urllib.error.HTTPError(url, 404, "not found", None, None)
        self.assertEqual(m.historical_day_exists("XUSDT", date(2026,8,17), read=respond),
                         "DATE_ARCHIVE_404")
        row = m.replay_one("XUSDT", date(2026,8,17),
                           head=lambda s,d: "DATE_ARCHIVE_404",
                           runner=lambda *a,**k: 1)
        self.assertIsNone(row["watch_events"])

    def test_prod_replay_and_censoring(self):
        m = load()
        def runner(symbol, calendar_day, calendar_anchor):
            self.assertTrue(calendar_anchor.endswith("T12:00:00Z"))
            return {"symbol": symbol, "status": "COMPLETE_60H", "watch_events": 1,
                    "setups": 1, "setup_triggered_24h_proxy_20bps": [
                       {"proxy":{"status":"PRICE_PROXY_ONLY","net_pct":-3.1}},
                       {"proxy":{"status":"CENSORED_ZERO_VOLUME_EXIT"}}]}
        out = m.run_day("2026-08-17", symbols=["XUSDT"],
                        head=lambda *args: "DATE_ZIP_PRESENT", runner=runner)
        summary = out["summary"]
        self.assertEqual(summary["d1_proxy_loss"], 1)
        self.assertEqual(summary["d1_censored"], {"CENSORED_ZERO_VOLUME_EXIT": 1})
        self.assertEqual(summary["d1_proxy_median_pct"], -3.1)
        self.assertFalse(out["frozen_before_ohlcv_requests"])

    def test_unknown_date_and_mismatched_identity_rejected(self):
        m = load()
        with self.assertRaisesRegex(ValueError, "NON_FROZEN"):
            m.run_day("2026-07-15", symbols=["XUSDT"])
        with self.assertRaisesRegex(ValueError, "REPLAY_ID_MISMATCH"):
            m.replay_one("XUSDT", date(2026,8,17),
                head=lambda *args: "DATE_ZIP_PRESENT",
                runner=lambda *args,**kw: {"symbol":"YUSDT"})

    def test_html_listing_rejected(self):
        m = load()
        with self.assertRaisesRegex(ValueError, "NOT_BUCKET_RESULT"):
            m.list_ever_spot_symbols(lambda url: b"<html>this is not S3 XML</html>")

if __name__ == "__main__":
    unittest.main()
