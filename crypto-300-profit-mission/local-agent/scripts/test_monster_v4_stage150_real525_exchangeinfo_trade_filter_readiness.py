#!/usr/bin/env python3
"""Stage150 real saved full525 raw source + frozen Stage120 filter tests."""
import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest

import monster_v4_stage120_exchangeinfo_execution_rules as stage120
import monster_v4_stage147_saved_real_bbo_execution_readiness as stage147
import monster_v4_stage150_real525_exchangeinfo_trade_filter_readiness as stage150


class Stage150RealExchangeInfoRules(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.real=stage150.audit()

    def test_real_saved_universe_525_all_types_preserved_no_fake_fill(self):
        report=self.real
        rows=report["full_original_market_population"]
        counts=report["original_source_venue_counts"]
        self.assertEqual(len(rows),525)
        self.assertEqual(len({r["symbol_exact"] for r in rows}),525)
        self.assertEqual(counts["COIN_ISSUER_NOT_PROVEN"],523)
        self.assertEqual(counts["INDEX_OR_OTHER_NOT_ELIGIBLE_FOR_CRYPTO_G1"],2)
        self.assertEqual(counts["all_original_usdm_venue_rows"],525)
        self.assertEqual(sum(v for k,v in counts.items() if k.startswith("filter_")),525)
        self.assertTrue(report["frozen_original_stage120_parser_reused"])
        self.assertTrue(report["frozen_stage147_real_raw_source_binding_reused"])
        self.assertTrue(report["no_default_or_implicit_quote_order_size"])
        self.assertFalse(report["source_www_mirror_identity_and_freshness_attested"])
        self.assertEqual(report["G4"],"UNKNOWN")
        self.assertEqual(report["G6"],"NO_GO")
        self.assertTrue(all(r["actual_fill"]=="NOT_OBSERVED"
                            and r["net_executable_profit"]=="UNKNOWN"
                            and r["G4_verified_executable_case"] is False
                            and r["market_rule_valid_at_later_D0_or_D1"]=="UNVERIFIED"
                            and r["contract_multiplier_independently_proven"] is False
                            for r in rows))

    def test_actual_original_filter_parser_reuse_and_minimums_not_trade(self):
        records=self.real["full_original_market_population"]
        measures=self.real["historical_filter_descriptive_only"]
        self.assertGreater(measures["minimum_quote_rule_present"],0)
        self.assertGreater(measures["market_quantity_step_present"],0)
        self.assertGreater(measures["lot_quantity_step_present"],0)
        self.assertTrue(any(r["filter_status"]=="COMPLETE_ASOF_FILTER_METADATA_NOT_EXECUTION"
                            for r in records))
        self.assertTrue(all("PRICE_FILTER" in r["filter_names_original"]
                            for r in records if r["filter_status"]=="COMPLETE_ASOF_FILTER_METADATA_NOT_EXECUTION"))
        for row in records:
            if row["filter_status"]=="COMPLETE_ASOF_FILTER_METADATA_NOT_EXECUTION":
                self.assertIsNotNone(row["MARKET_LOT_SIZE"])
                self.assertIsNotNone(row["notional_rule"])
            self.assertTrue(row["quantityPrecision_is_not_market_step"])
        # No inferred quote amount and no order preflight from snapshot.
        self.assertNotIn("order_quote",self.real)
        self.assertNotIn("actual_order_size",self.real)

    def test_frozen_stage120_missing_or_malformed_does_not_upgrade_rule(self):
        self.assertNotEqual(stage120.parse_filters({})["status"],
                            "COMPLETE_ASOF_FILTER_METADATA_NOT_EXECUTION")
        self.assertNotEqual(stage120.parse_filters({"filters":[]})["status"],
                            "COMPLETE_ASOF_FILTER_METADATA_NOT_EXECUTION")
        self.assertIn("MISSING_MARKET_LOT_SIZE",
                      stage120.parse_filters({"filters":[]})["reasons"])

    def test_stage148_verifier_still_rejects_derived_population_swap(self):
        with tempfile.TemporaryDirectory() as directory:
            target=Path(directory)/"source"
            shutil.copytree(stage147.SOURCE_DIR,target)
            derived=target/"stage139_original_T0_asof_contract_metadata.json"
            snap=json.loads(derived.read_text())
            rows=snap["initial_original_instrument_rows"]
            original=[r for r in rows if r["symbol_exact"]=="ALLUSDT"]
            self.assertEqual(len(original),1)
            original[0]["symbol_exact"]="AAPLUSDT"
            derived.write_text(json.dumps(snap))
            with self.assertRaises(ValueError):
                stage150.audit(target)

    def test_stage150_cli_no_http_no_order_and_525_json(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/"report.json"
            # Exercise same source-backed exporter behavior as CLI without a
            # mutable external dependency or mocked 525 market.
            r=stage150.audit()
            out.write_text(json.dumps(r,ensure_ascii=False))
            actual=json.loads(out.read_text())
            self.assertEqual(len(actual["full_original_market_population"]),525)
            self.assertTrue(actual["NO_MERGE_NO_DEPLOY_NO_GMAIL_NO_TRADE"])
            self.assertEqual(actual["G0"],"PARTIAL")
            self.assertEqual(actual["G1"],"NOT_SCORABLE")


if __name__=="__main__":
    unittest.main()
