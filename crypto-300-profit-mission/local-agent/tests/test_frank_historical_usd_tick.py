"""Local Kraken-style fixtures; never use provider or user trade data."""
import hashlib
import json
import unittest
from urllib.parse import parse_qs, urlsplit

from mission_agent.signals.historical_usd_tick import capture_url, observe_usd_tick


AT = 1795737600  # 2026-11-27T00:00:00Z
STAMP = "2026-11-27T00:00:00"


class HistoricalUSDTest(unittest.TestCase):
    def row(self, asset="USDC", **changes):
        return {"symbol": asset + "/USD", "base_asset": asset, "quote_asset": "USD",
                "trade_id": "FIXTURE1", "trade_ts": STAMP + ".000000001Z",
                "publication_ts": STAMP + ".000000050Z", "price": "0.98765432100000100", **changes}

    def compare(self, *rows, asset="USDC"):
        body = json.dumps({"result": {"count": len(rows), "trades": rows}}).encode()
        return observe_usd_tick(asset, AT, url=capture_url(asset, AT), raw=body), body

    def test_exact_half_open_second_and_unambiguous_nonpar_conversion(self):
        query = parse_qs(urlsplit(capture_url("USDC", AT)).query)
        self.assertEqual(query["from_ts"], ["2026-11-26T23:59:59.999999999Z"])
        self.assertEqual(query["to_ts"], [STAMP + ".999999999Z"])
        result, body = self.compare(self.row(), self.row(trade_id="FIXTURE2", trade_ts=STAMP+"Z"))
        self.assertEqual(result["status"], "OBSERVED_SECOND_CONVERSION")
        self.assertEqual(result["usd_per_quote_unit"], "0.987654321000001")
        self.assertEqual(result["source_sha256"], hashlib.sha256(body).hexdigest())
        self.assertEqual(result["matched_trade_count"], 2)
        self.assertEqual(result["scope"], "PAYMENT_ASSET_MARKET_TRADE_NOT_FIAT_FILL")
        sol, _ = self.compare(self.row("SOL", price="112.25"), asset="SOL")
        self.assertEqual(sol["usd_per_quote_unit"], "112.25")

    def test_wrong_time_pair_price_or_duplicate_is_unavailable(self):
        for change in ({"trade_ts": "2026-11-26T23:59:59.9Z"}, {"trade_ts": "2026-11-27T00:00:01Z"},
                       {"trade_ts": None}, {"symbol": "SOL/USDT"}, {"price": "0"}, {"price": 1}):
            with self.subTest(change=change):
                result, _ = self.compare(self.row(**change))
                self.assertEqual(result["reason"], "SOURCE_TRADE_INVALID")
        dup, _ = self.compare(self.row(), self.row())
        self.assertEqual(dup["reason"], "SOURCE_TRADE_INVALID")

    def test_ambiguous_empty_and_saturated_are_not_prices(self):
        no_print, _ = self.compare()
        self.assertEqual(no_print["reason"], "NO_TRADE_IN_SECOND")
        diff, _ = self.compare(self.row(), self.row(trade_id="FIXTURE2", price="1.005"))
        self.assertEqual(diff["reason"], "IN_SECOND_PRICES_DISAGREE")
        capped, _ = self.compare(*(self.row(trade_id=f"X{i}") for i in range(1000)))
        self.assertEqual(capped["reason"], "SOURCE_WINDOW_SATURATED")
