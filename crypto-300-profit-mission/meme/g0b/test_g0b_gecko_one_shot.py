"""Offline checks for one-time G0-B; never requests a public endpoint."""
import unittest
from unittest.mock import patch
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from g0b_gecko_one_shot import (
    MAX_GET, MIN_SPACING_SECONDS, PublicGet, StopPilot, load_manifest,
    close_proxy, select_pool, run,
)


class TestG0BOnce(unittest.TestCase):
    def test_frozen_cohort_membership_and_size(self):
        rows, digest = load_manifest()
        self.assertEqual(len(rows), 12)
        self.assertEqual(len(set(x["mint"] for x in rows)), 12)
        self.assertEqual(len(digest), 64)
        self.assertEqual([x["id"] for x in rows],
                         ["M1","M2","M3","M4","A1","A2","A3","A4",
                          "C1","C2","C3","C4"])
        self.assertEqual(len([x for x in rows if x["kind"] == "MULT"]),4)
        self.assertEqual(len([x for x in rows if x["kind"] == "ACC_ONLY"]),4)
        self.assertEqual(len([x for x in rows if x["kind"] == "RECOVERED_BUY_NO_SIGNAL_CONTROL"]),4)

    def test_no_network_by_default(self):
        with patch.object(PublicGet, "get", side_effect=AssertionError("NO_NETWORK")):
            result = run(execute=False, max_http=50)
        self.assertEqual(result["status"], "SELECTION_LOCKED_OFFLINE")
        self.assertEqual(result["http_used"], 0)
        self.assertEqual(result["summary"]["real_executable_quotes_verified"], 0)

    def test_exact_request_ceiling_and_spacing(self):
        self.assertEqual(MAX_GET, 50)
        self.assertGreaterEqual(MIN_SPACING_SECONDS, 12)
        for bad in (0, 51, 100):
            with self.assertRaises(ValueError):
                PublicGet(bad)

    def test_non_preexisting_pool_never_selected(self):
        mint = "MintTarget"
        usdc = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
        pool = lambda created, address: {"id":"solana_"+address,
            "attributes":{"address":address,"pool_created_at":created},
            "relationships":{"base_token":{"data":{"id":"solana_"+mint}},
                             "quote_token":{"data":{"id":"solana_"+usdc}}}}
        payload={"data":[pool("2026-09-10T00:00:00Z","a"*40),
                         pool("2026-09-03T00:00:00Z","b"*40)]}
        # 2026-09-05 00:00 UTC
        result = select_pool(payload,mint,1788566400)
        self.assertEqual(result["address"],"b"*40)
        self.assertTrue(result["present_day_selection_bias"])
        self.assertIsNone(select_pool(payload,mint,1788100000))

    def test_no_zero_volume_or_unbounded_later_price(self):
        rows=[{"t":200,"c":10,"v":0},{"t":260,"c":12,"v":3},
              {"t":600,"c":15,"v":30}]
        chosen = close_proxy(rows,220)
        self.assertEqual(chosen["candle_start"],260)
        self.assertEqual(chosen["lookahead_from_target_seconds"],100)
        self.assertIsNone(close_proxy(rows,300))

    def test_unauthorized_endpoint_stops_before_attempt(self):
        gate=PublicGet()
        with self.assertRaises(StopPilot):
            gate.get("/networks/eth/pools")
        self.assertEqual(len(gate.attempts),0)


if __name__ == "__main__":
    unittest.main()
