#!/usr/bin/env python3
"""Offline regression tests: BSC address model V1/P1. No GMGN, RPC or credentials."""
from __future__ import annotations

import copy
import unittest

from bsc_meme_address_model_v1 import SourceValidationError, build_baseline

W_A = "0x" + "a" * 40
W_B = "0x" + "b" * 40
CA_A = "0x" + "1" * 40
CA_B = "0x" + "2" * 40
SHA = "a" * 40


def cell(name, ca, observed):
    return {
        "token": name,
        "ca": ca,
        "state": "COMPLETE_OBSERVED" if observed else "COMPLETE_ZERO_ERC20",
        "complete_in_events": 2 if observed else 0,
        "complete_out_events": 1 if observed else 0,
        "evidence": "REAL_TEST_FIXTURE_NOT_CHAIN",
    }


def synthetic():
    return {
        "summary": {
            "wallets": 2,
            "token_cas": 2,
            "cells": 4,
            "complete_cursor_cells": 4,
            "observed_transfer_pairs": 2,
            "token_quantity_closed_pairs": 2,
            "complete_zero_transfer_pairs": 2,
        },
        "cells_by_wallet": [
            {"wallet": W_A, "cells": [cell("龙虾", CA_A, True), cell("牛来", CA_B, False)]},
            {"wallet": W_B, "cells": [cell("龙虾", CA_A, False), cell("牛来", CA_B, True)]},
        ],
    }


def model(source=None):
    return build_baseline(
        synthetic() if source is None else source,
        source_git_blob_sha=SHA,
        expected_wallets=2,
        expected_tokens=2,
        expected_observed=2,
        priority_2026_names=("龙虾", "牛来"),
    )


class TestBscMemeAddressModelV1(unittest.TestCase):
    def test_valid_matrix_complete_even_if_absent(self):
        d = model()
        self.assertEqual(d["cohort"]["cells"], 4)
        self.assertEqual(d["cohort"]["ERC20_present"], 2)
        self.assertEqual(d["cohort"]["ERC20_absent"], 2)
        self.assertEqual(len(d["wallets"]), 2)
        self.assertEqual(d["input_source"]["git_blob_sha"], SHA)

    def test_no_fake_wallet_profit_or_win_rate_or_missed_chance(self):
        d = model()
        self.assertFalse(d["ranking_contract"]["unknown_profit_is_zero"])
        self.assertEqual(d["ranking_contract"]["rankable_realized_profit_wallets"], 0)
        for wallet in d["wallets"]:
            self.assertIsNone(wallet["profit_rank"])
            self.assertIsNone(wallet["independently_closed_positive_major_count"])
            self.assertEqual(wallet["recent_30d_activity_state"], "UNRESOLVED")
            for c in wallet["cells"]:
                self.assertEqual(c["realized_cashflow_and_profit"], "UNRESOLVED")
                self.assertEqual(c["major_opportunity_eligible_miss"], "UNRESOLVED")
                self.assertEqual(c["owner_signed_buy_state"], "UNRESOLVED")
                self.assertEqual(c["recent_30d_true_signed_meme_swap"], "UNRESOLVED")

    def test_2026_priority_not_proven_swap(self):
        d = model()
        for wallet in d["wallets"]:
            self.assertEqual(wallet["priority_2026_major_transfer_present_count"], 1)
            self.assertEqual(len(wallet["priority_2026_major_transfer_present"]), 1)
            self.assertIsNone(wallet["last_confirmed_true_swap_UTC"])

    def test_deterministic_output_not_dependent_on_source_wallet_order(self):
        src = synthetic()
        base = model(src)
        src["cells_by_wallet"].reverse()
        other = model(src)
        self.assertEqual(base, other)
        self.assertEqual([w["wallet"] for w in base["wallets"]], [W_A, W_B])

    def test_missing_wallet_rejected(self):
        src = synthetic()
        del src["cells_by_wallet"][1]
        with self.assertRaisesRegex(SourceValidationError, "wallet count"):
            model(src)

    def test_duplicate_wallet_rejected(self):
        src = synthetic()
        src["cells_by_wallet"][1]["wallet"] = W_A
        with self.assertRaisesRegex(SourceValidationError, "duplicate EOA"):
            model(src)

    def test_incomplete_cursor_rejected(self):
        src = synthetic()
        src["summary"]["complete_cursor_cells"] = 3
        with self.assertRaisesRegex(SourceValidationError, "incomplete cursor"):
            model(src)

    def test_transfer_count_conflict_rejected(self):
        src = synthetic()
        src["cells_by_wallet"][0]["cells"][1]["complete_in_events"] = 1
        with self.assertRaisesRegex(SourceValidationError, "presence/count conflict"):
            model(src)

    def test_partial_cell_rejected(self):
        src = synthetic()
        src["cells_by_wallet"][0]["cells"][0]["state"] = "PARTIAL"
        with self.assertRaisesRegex(SourceValidationError, "partial or unrecognized"):
            model(src)

    def test_token_ca_drift_rejected(self):
        src = synthetic()
        src["cells_by_wallet"][1]["cells"][0]["ca"] = "0x" + "3" * 40
        with self.assertRaisesRegex(SourceValidationError, "identity mismatch"):
            model(src)

    def test_duplicate_exact_ca_rejected(self):
        src = synthetic()
        src["cells_by_wallet"][0]["cells"][1]["ca"] = CA_A
        with self.assertRaisesRegex(SourceValidationError, "duplicated exact CA"):
            model(src)

    def test_missing_2026_priority_name_rejected(self):
        with self.assertRaisesRegex(SourceValidationError, "priority 2026 name missing"):
            build_baseline(
                synthetic(), source_git_blob_sha=SHA,
                expected_wallets=2, expected_tokens=2, expected_observed=2,
                priority_2026_names=("MARSCOIN",),
            )

    def test_missing_source_sha_rejected(self):
        with self.assertRaisesRegex(SourceValidationError, "blob sha"):
            build_baseline(
                synthetic(), source_git_blob_sha="not-a-sha",
                expected_wallets=2, expected_tokens=2, expected_observed=2,
                priority_2026_names=("龙虾", "牛来"),
            )

    def test_no_source_mutation(self):
        src = synthetic()
        before = copy.deepcopy(src)
        model(src)
        self.assertEqual(src, before)

    def test_present_with_null_count_kept_unknown_not_zero(self):
        src = synthetic()
        src["cells_by_wallet"][0]["cells"][0]["complete_in_events"] = None
        src["cells_by_wallet"][0]["cells"][0]["complete_out_events"] = None
        d = model(src)
        self.assertEqual(d["cohort"]["observed_cells_with_null_complete_event_counts"], 1)
        row = next(x for x in d["wallets"][0]["cells"] if x["token"] == "龙虾")
        self.assertIsNone(row["complete_in_events"])
        self.assertIsNone(row["complete_out_events"])
        self.assertEqual(row["ERC20_presence"], "PRESENT")
        self.assertEqual(row["complete_event_count_state"],
                         "PRESENT_WITH_NULL_COMPLETE_COUNTS_IN_V21_OVERLAY")

    def test_zero_transfer_with_null_count_rejected(self):
        src = synthetic()
        src["cells_by_wallet"][0]["cells"][1]["complete_in_events"] = None
        src["cells_by_wallet"][0]["cells"][1]["complete_out_events"] = None
        with self.assertRaisesRegex(SourceValidationError, "zero-ERC20 count is null"):
            model(src)

    def test_half_null_counts_rejected(self):
        src = synthetic()
        src["cells_by_wallet"][0]["cells"][0]["complete_in_events"] = None
        with self.assertRaisesRegex(SourceValidationError, "incomplete"):
            model(src)


if __name__ == "__main__":
    unittest.main()
