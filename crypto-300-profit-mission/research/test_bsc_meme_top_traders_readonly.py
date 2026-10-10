#!/usr/bin/env python3
"""Offline tests: all fixtures fabricated. No external API, secrets, trading or alerts."""
import csv
import json
import tempfile
import unittest
from pathlib import Path

from bsc_meme_top_traders_readonly import TOKENS, analyze, unwrap


class ReadOnlyTopTraderTests(unittest.TestCase):
    def test_declared_universe_contains_exact_19_distinct_contracts(self):
        self.assertEqual(len(TOKENS), 19)
        self.assertEqual(len({ca.lower() for _, ca, _ in TOKENS}), 19)
        self.assertTrue(all(len(ca) == 42 and ca.startswith("0x") for _, ca, _ in TOKENS))

    def test_vendor_response_must_contain_valid_list(self):
        self.assertEqual(unwrap({"code": 0, "data": {"list": [{"address": "x"}]}}),
                         [{"address": "x"}])
        with self.assertRaises(ValueError):
            unwrap({"code": 429, "message": "RATE_LIMIT"})
        with self.assertRaises(ValueError):
            unwrap({"data": {"not_a_list": 1}})

    def test_two_winners_and_transfer_in_are_separated(self):
        buyer = "0x" + "a" * 40
        received_tokens = "0x" + "b" * 40
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for label in ("我踏马来了", "龙虾"):
                contract = next(ca for name, ca, _ in TOKENS if name == label)
                payload = {
                    "contract": contract,
                    "response": {
                        "code": 0,
                        "data": {
                            "list": [
                                {"address": buyer,
                                 "realized_profit": 125,
                                 "profit": 250,
                                 "buy_tx_count_cur": 4,
                                 "sell_tx_count_cur": 2,
                                 "history_transfer_in_amount": 0,
                                 "last_active_timestamp": 1791000000},
                                {"address": received_tokens,
                                 "realized_profit": 9999,
                                 "buy_tx_count_cur": 0,
                                 "history_transfer_in_amount": 1234}
                            ]
                        }
                    }
                }
                path = root / "raw" / f"{label}_profit.json"
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            self.assertEqual(analyze(root), 0)
            with (root / "analysis" / "cross_token_wallets.csv").open(
                    encoding="utf-8-sig", newline="") as file:
                cross = {row["wallet"]: row for row in csv.DictReader(file)}
            self.assertEqual(int(cross[buyer]["provisional_winning_tokens"]), 2)
            self.assertEqual(int(cross[received_tokens]["provisional_winning_tokens"]), 0)
            self.assertEqual(cross[buyer]["signal"], "OBSERVE_ONLY")
            self.assertEqual(cross[buyer]["independent_pnl_verified"], "False")
            report = json.loads((root / "analysis" / "summary.json").read_text())
            self.assertEqual(report["tokens"], 19)
            self.assertEqual(report["tokens_with_vendor_rows"], 2)
            self.assertFalse(report["FULL_HISTORICAL_TOP100_PNL_VERIFIED"])
            self.assertEqual(report["PRODUCTION_TRADING"], "NO_GO")

    def test_empty_inputs_never_claim_rankings(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertEqual(analyze(root), 3)
            report = json.loads((root / "analysis" / "summary.json").read_text())
            self.assertEqual(report["tokens_with_vendor_rows"], 0)
            self.assertFalse(report["FULL_HISTORICAL_TOP100_PNL_VERIFIED"])


if __name__ == "__main__":
    unittest.main()
