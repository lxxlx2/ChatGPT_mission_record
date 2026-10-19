"""Offline-only capacity checks; never connect to BSC."""
import sys
import unittest
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from f0_source_budget import estimate, positive_decimal, nonnegative_int


def plan(**changes):
    values = dict(
        hours=Decimal("24"), block_seconds=Decimal("0.45"),
        watch_receipts=0, control_receipts=0,
        eligible_entry_quotes=0, eligible_exit_quotes=0,
        audit_receipts=0, ws_bytes_per_block=0, eoa_checks=0,
        max_total_rpc_calls=0, max_control_discovery_calls=0,
        cu_budget=0,
    )
    values.update(changes)
    return estimate(**values)


class OfflineBudgetTests(unittest.TestCase):
    def test_24h_bsc_blocks(self):
        r = plan()
        self.assertEqual(r["estimated_blocks"], 192000)
        self.assertEqual(r["estimated_total_rpc_calls"], 192000)
        self.assertEqual(r["estimated_total_cu"], "3840000")
        self.assertEqual(r["stop_state"], "NO_RUN")

    def test_48h_bsc_blocks(self):
        r = plan(hours=Decimal("48"))
        self.assertEqual(r["estimated_blocks"], 384000)
        self.assertEqual(r["estimated_total_cu"], "7680000")

    def test_never_implicitly_grant_run(self):
        r = plan(max_total_rpc_calls=1000000, max_control_discovery_calls=1000000,
                 cu_budget=30000000)
        self.assertEqual(r["cap_evaluation"], "WITHIN_SCENARIO_CAPS")
        self.assertFalse(r["trial_run_authorized"])
        self.assertEqual(r["stop_state"], "NO_RUN")

    def test_control_budget_is_separate(self):
        r = plan(control_receipts=50, max_total_rpc_calls=200000,
                 max_control_discovery_calls=192040, cu_budget=5000000)
        self.assertEqual(r["estimated_control_discovery_calls"], 192050)
        self.assertEqual(r["cap_evaluation"], "OVER_SCENARIO_CAPS")

    def test_ceil_blocks_for_partial_interval(self):
        r = plan(hours=Decimal("0.0002"), block_seconds=Decimal("0.5"))
        self.assertEqual(r["estimated_blocks"], 2)

    def test_quote_budget_entry_exit_and_receipt(self):
        r = plan(watch_receipts=4, control_receipts=6, eligible_entry_quotes=2,
                 eligible_exit_quotes=3, audit_receipts=5, eoa_checks=20)
        self.assertEqual(r["rpc_breakdown"]["entry_quote_calls"]["count"], 6)
        self.assertEqual(r["rpc_breakdown"]["exit_quote_calls"]["count"], 9)
        self.assertEqual(r["estimated_total_rpc_calls"], 192044)
        self.assertEqual(r["estimated_total_cu"], "3841010")

    def test_websocket_byte_cost_is_scenario(self):
        r = plan(ws_bytes_per_block=1000, cu_budget=30000000)
        self.assertEqual(r["hypothetical_websocket_bytes"], 192000000)
        self.assertEqual(r["hypothetical_websocket_cu"], "7680000.00")
        self.assertEqual(r["estimated_total_cu"], "11520000.00")
        self.assertEqual(r["cu_evaluation"], "WITHIN_HYPOTHETICAL_CU_LIMIT")

    def test_small_cu_budget_stops(self):
        r = plan(cu_budget=100)
        self.assertEqual(r["cu_evaluation"], "OVER_HYPOTHETICAL_CU_LIMIT")
        self.assertEqual(r["stop_state"], "NO_RUN")

    def test_caps_missing_even_if_cu_available(self):
        r = plan(cu_budget=30000000)
        self.assertEqual(r["cap_evaluation"], "NEEDS_EXPLICIT_CAPS")

    def test_refuse_invalid_numbers(self):
        for values in ({"hours": Decimal("0")}, {"block_seconds": Decimal("-1")},
                       {"hours": Decimal("NaN")}, {"watch_receipts": -1},
                       {"max_total_rpc_calls": 2.0}):
            with self.subTest(values=values), self.assertRaises(ValueError):
                plan(**values)

    def test_cli_parsers_negative_nan(self):
        for value in ("-1", "nan", "inf", "0"):
            with self.subTest(value=value), self.assertRaises(Exception):
                positive_decimal(value)
        with self.assertRaises(Exception):
            nonnegative_int("-2")

    def test_output_disclaims_live_source(self):
        r = plan(max_total_rpc_calls=192001, max_control_discovery_calls=192001,
                 cu_budget=30000000)
        self.assertFalse(r["live_source_tested"])
        self.assertEqual(r["source_capabilities"], "UNVERIFIED")
        self.assertEqual(r["actual_rpc_calls"], 0)
        self.assertIn("confirmed_finality_and_E2_policy", r["missing_live_evidence"])


if __name__ == "__main__":
    unittest.main()
