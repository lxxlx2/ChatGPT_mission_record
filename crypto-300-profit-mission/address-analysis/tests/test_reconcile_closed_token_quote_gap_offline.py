"""Regression: 449 roster + 5 historical token rounds, quote ≠ net PnL."""
from __future__ import annotations

import copy
from pathlib import Path
import socket
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from reconcile_closed_token_quote_gap_offline import (
    ROOT, SOURCES, audit, load_frozen_inputs,
)


class FrozenTokenQuoteGapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = load_frozen_inputs(ROOT)

    def fresh(self):
        return copy.deepcopy(self.original)

    def test_449_source_and_five_rounds_are_distinct(self):
        report = audit(self.fresh())
        self.assertEqual(report["wallet_universe"], 449)
        self.assertEqual(report["three_chain_signed_active"], 237)
        self.assertEqual(report["three_chain_signed_zero"], 212)
        self.assertEqual(report["closed_token_candidate_roundtrips"], 5)
        self.assertEqual(report["wallets_in_this_candidate_ledger"], 4)
        self.assertEqual(report["matched_wbnb_event_cases"], 3)
        self.assertEqual(report["without_matched_wbnb_event"], 2)
        self.assertEqual(report["approved_trade_net_pnl_cases"], 0)
        self.assertEqual(report["full_wallet_30d_or_lifetime_pnl_approved"], 0)
        self.assertNotIn(16, [r["source_row"] for r in report["rows"]])

    def test_independent_exact_residual_wei_signs(self):
        rows = {(r["source_row"], r["token"]): r
                for r in audit(self.fresh())["rows"]}
        self.assertEqual(rows[(227, "BOARDSEAT")]
                         ["unattributed_native_minus_wbnb_wei"],
                         "-13792578099635178")
        self.assertEqual(rows[(227, "BTCLIFE")]
                         ["unattributed_native_minus_wbnb_wei"],
                         "-10002713892967094")
        self.assertEqual(rows[(400, "BOARDSEAT")]
                         ["unattributed_native_minus_wbnb_wei"],
                         "-16825277937507272")
        self.assertEqual(rows[(2, "sauce")]
                         ["wbnb_router_event_spread_wei"], None)
        self.assertTrue(all(r["approved_wallet_trade_net_pnl"] is None
                            for r in rows.values()))

    def test_source_row_wallet_identity_not_copied_between_wallets(self):
        inputs = self.fresh()
        inputs["ledger"]["records"][0]["wallet"] = "0x" + "1" * 40
        with self.assertRaisesRegex(ValueError, "SOURCE_ROW_WALLET_MISMATCH"):
            audit(inputs)

    def test_quote_hash_mismatch_rejected(self):
        inputs = self.fresh()
        inputs["quote"]["cases"][0]["buy"] = "0x" + "0" * 64
        with self.assertRaisesRegex(
                ValueError, "QUOTE_CASE_IDENTITY_OR_TRANSACTION_MISMATCH"):
            audit(inputs)

    def test_quote_amount_mutation_rejected(self):
        inputs = self.fresh()
        inputs["quote"]["cases"][0]["sellWbnbWei"] = "483663976630184593"
        with self.assertRaisesRegex(
                ValueError, "WBNB_SPREAD_OR_DIFFERENCE_MISMATCH"):
            audit(inputs)

    def test_wallet_balance_or_mock_net_pnl_cannot_promote(self):
        inputs = self.fresh()
        inputs["ledger"]["records"][0]["wallet_trade_settlement_pnl"] = (
            "156828105278687674")
        with self.assertRaisesRegex(ValueError, "UNSUPPORTED_REALIZED_PNL_CLAIM"):
            audit(inputs)

    def test_screen_449_denominator_cherrypick_rejected(self):
        inputs = self.fresh()
        inputs["screen"]["signed_zero_source_rows"].pop()
        with self.assertRaisesRegex(ValueError, "FROZEN_449_ROWS_NOT_PARTITION"):
            audit(inputs)

    def test_changed_input_blob_fails_closed_before_math(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            for name, (relative, _sha) in SOURCES.items():
                dest = root / relative
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes((ROOT / relative).read_bytes())
            ledger = root / SOURCES["ledger"][0]
            ledger.write_bytes(ledger.read_bytes() + b" ")
            with self.assertRaisesRegex(
                    ValueError, "FROZEN_SOURCE_BLOB_CHANGED_ledger"):
                load_frozen_inputs(root)

    def test_no_network_or_execution_side_effect(self):
        with (
            patch("http.client.HTTPSConnection",
                  side_effect=AssertionError("NO_NETWORK")) as https,
            patch.object(socket, "create_connection",
                         side_effect=AssertionError("NO_SOCKET")) as sock,
        ):
            report = audit(self.fresh())
            self.assertEqual(report["mode"],
                             "OFFLINE_FROZEN_INPUT_ONLY_NO_NEW_RPC")
            https.assert_not_called()
            sock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
