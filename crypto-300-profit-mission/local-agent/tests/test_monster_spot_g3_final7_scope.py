"""Frozen 46 original SETUP identity partition against Binance pre-event notices."""
from copy import deepcopy
import json
from pathlib import Path
import unittest

from mission_agent.early.spot_g3_final7_scope import resolve_all_46_asset_types
from mission_agent.early.spot_g3_positive_bound import PositiveBoundError


EVIDENCE = Path(__file__).resolve().parents[2] / "monster/evidence"


class Final7ScopeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.replay = json.loads((EVIDENCE /
            "MONSTER_SPOT511_4088_REAL_GLOBAL_FIFO8_FAIR8_46_SETUP_EVENTS_20261024.json").read_text())
        cls.base = json.loads((EVIDENCE /
            "MONSTER_SPOT511_PRE_EVENT_OFFICIAL_POSITIVE_CRYPTO_26_ASSETS_20261024.json").read_text())
        cls.stocks = json.loads((EVIDENCE /
            "MONSTER_SPOT511_OFFICIAL_POSITIVE_BSTOCKS_20261024.json").read_text())
        cls.final = json.loads((EVIDENCE /
            "MONSTER_SPOT511_PRE_EVENT_REMAINING_7_TYPES_20261024.json").read_text())

    def audit(self, replay=None, base=None, stocks=None, final=None):
        return resolve_all_46_asset_types(
            self.replay if replay is None else replay,
            self.base if base is None else base,
            self.stocks if stocks is None else stocks,
            self.final if final is None else final
        )

    def test_actual_full_source_research_original46_partition(self):
        v = self.audit()
        self.assertEqual((v["raw_setup_count"],v["crypto_protocol_utility_setups"],
                          v["separately_scoped_chiliz_fan_token_setups"],
                          v["verified_tokenized_stock_setups"],
                          v["asset_identity_unresolved_setups"]),(46,41,3,2,0))
        self.assertEqual(v["full_seven_day_G3_attention_ceiling"],35)
        self.assertEqual(v["G3_crypto_type_signal_lower_bound"],41)
        self.assertTrue(v["G3_raw_upgrade_events_are_attention_not_trade_orders"])
        self.assertTrue(v["G3_over_ceiling_even_if_remaining_source_has_zero_new_setups"])
        self.assertEqual(v["G3_historical_subset_attention_ceiling_status"],
                         "EXCEEDED_WITH_CRYPTO_TYPE_POSITIVE_EVIDENCE")
        self.assertEqual(v["G3_full_4599_publisher_source_and_PIT"],"NOT_PROVEN")
        self.assertEqual(v["G3"],"NOT_PASSED_G3_ATTENTION_LOWER_BOUND_EXCEEDED_BUT_FULL_SOURCE_AND_PIT_PENDING")
        self.assertEqual(v["G6"],"NO_GO")
        self.assertEqual(v["fan_token_in_scope_formal_decision"],
                         "UNRESOLVED_FROZEN_SCOPE_INTERPRETATION")

    def test_monitoring_tag_applies_only_to_g4_account_quiz(self):
        result=self.audit()
        sensitivity=result["G4_monitoring_tag_account_permission_sensitivity"]
        self.assertEqual(sensitivity["affected_crypto_type_setup_events"],6)
        self.assertEqual(sensitivity["if_all_accounts_cannot_trade_tagged_core_events"],35)
        self.assertEqual(sensitivity["if_fan_tokens_included_and_all_tagged_unavailable"],38)
        self.assertTrue(sensitivity["cannot_subtract_from_G3_attention_events"])
        self.assertNotIn("core_if_all_monitor_tag_deferred",result)
        self.assertNotIn("core_plus_fans_if_all_monitor_tag_deferred",result)
        self.assertEqual(result["G3_crypto_type_signal_lower_bound"],41)

    def test_even_excluding_all_three_fans_attention_exceeds_cap(self):
        result=self.audit()
        self.assertEqual(result["crypto_protocol_utility_setups"],41)
        self.assertEqual(result["separately_scoped_chiliz_fan_token_setups"],3)
        self.assertGreater(result["crypto_protocol_utility_setups"],
                           result["full_seven_day_G3_attention_ceiling"])
        self.assertEqual(result["G3_full_4599_publisher_source_and_PIT"],"NOT_PROVEN")

    def test_original_event_ids_timestamps_and_input_unchanged(self):
        prior=deepcopy(self.replay)
        records=self.audit()["actual_events"]
        self.assertEqual([(r["event_id"],r["symbol"],r["observed_ms"]) for r in records],
                         [(r["event_id"],r["symbol"],r["observed_ms"])
                          for r in prior["complete_46_original_core_setups"]])
        self.assertEqual(self.replay,prior)

    def test_all_three_fan_tokens_are_distinct_from_securities(self):
        r=self.audit()
        symbols={x["symbol"] for x in r["actual_events"]
                 if x["asset_identity_class"]=="FAN_TOKEN_SCOPE_REQUIRES_DECISION"}
        self.assertEqual(symbols,{"ACMUSDT","ATMUSDT","BARUSDT"})

    def test_missing_positive_row_fails_closed(self):
        f=deepcopy(self.final);f["official_positive_identity_rows"].pop()
        with self.assertRaises(PositiveBoundError):self.audit(final=f)

    def test_retyped_fan_to_core_changes_frozen_partition_and_rejected(self):
        f=deepcopy(self.final);f["official_positive_identity_rows"][4]["category"]="CRYPTO_NETWORK_PROTOCOL_UTILITY"
        with self.assertRaises(PositiveBoundError):self.audit(final=f)

    def test_future_publication_rejected(self):
        f=deepcopy(self.final);f["official_positive_identity_rows"][0]["source_published_utc"]="2026-10-20T00:00:00Z"
        with self.assertRaises(PositiveBoundError):self.audit(final=f)

    def test_wrong_spot_pair_symbol_rejected(self):
        f=deepcopy(self.final);f["official_positive_identity_rows"][0]["symbol"]="AFAKEUSDT"
        with self.assertRaises(PositiveBoundError):self.audit(final=f)

    def test_duplicate_source_symbol_rejected(self):
        f=deepcopy(self.final);f["official_positive_identity_rows"][1]["symbol"]="AUSDT"
        with self.assertRaises(PositiveBoundError):self.audit(final=f)

    def test_unofficial_host_rejected(self):
        f=deepcopy(self.final);f["official_positive_identity_rows"][0]["official_url"]="https://www.binance.com.evil.test/en/research/projects/a"
        with self.assertRaises(PositiveBoundError):self.audit(final=f)

    def test_missing_replay_provenance_rejected(self):
        f=deepcopy(self.final);f["fixed_original_replay_sha256"]="f"*64
        with self.assertRaises(PositiveBoundError):self.audit(final=f)

    def test_forged_setup_original_event_id_rejected(self):
        v=deepcopy(self.replay)
        v["complete_46_original_core_setups"][0]["event_id"]="bad-id"
        with self.assertRaises(PositiveBoundError):self.audit(replay=v)

    def test_known_securities_not_crypto(self):
        v=self.audit()
        stocks={x["symbol"] for x in v["actual_events"]
                if x["asset_identity_class"]=="TOKENIZED_STOCK_OUT_OF_SCOPE"}
        self.assertEqual(stocks,{"IBMBUSDT","SHAZBUSDT"})


if __name__=="__main__":
    unittest.main()
