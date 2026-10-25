"""Offline ADR005 forward Spot scorer admission guards (no real November sources)."""
import copy
from collections import Counter
from pathlib import Path
import tempfile
import unittest

import monster_v4_adr005_forward_spot_score_admission as gate
import monster_v4_adr005_forward_spot_t0_gate as t0
import monster_v4_adr005_forward_spot_daily_gate as daily


class ForwardScoreSourceAdmissionTests(unittest.TestCase):
    WINDOW="2026-11-02T00:00:00Z"
    FUTURE_ASOF="2026-11-16T00:00:00Z"

    def fixture(self,symbols=("AAAUSDT","BBBUSDT","BTCUSDT"),missing=()):
        """Synthetic source census with valid accounting; NOT original issuer ZIPs."""
        population=len(symbols)
        calendar=daily.source_calendar(self.WINDOW)
        absent=set(missing)
        rows=[]
        counts=Counter()
        groups={name:Counter() for name in daily.SEGMENTS}
        for symbol in symbols:
            for item in calendar:
                st=("SOURCE_NOT_SUPPLIED" if (symbol,item["utc_day"]) in absent
                    else "VERIFIED_1440_OFFICIAL_1M")
                rows.append({"symbol":symbol,"utc_day":item["utc_day"],
                             "segment":item["segment"],"source_status":st})
                counts[st]+=1
                groups[item["segment"]][st]+=1
        return {
            "schema":daily.SCHEMA,
            "window_start_utc":self.WINDOW,
            "baseline_symbol_population":population,
            "days_per_original_symbol":15,
            "expected_official_zip_checksum_pairs":population*15,
            "dynamic_listing_changes_during_window":"UNKNOWN",
            "source_publisher_archive_available_at_event_time":"UNKNOWN",
            "actual_status_counts":dict(sorted(counts.items())),
            "segment_source_status_counts":
                {name:dict(sorted(c.items())) for name,c in groups.items()},
            "verified_complete_all_15days":counts["VERIFIED_1440_OFFICIAL_1M"]==population*15,
            "t0_archive_sha256":"a"*64,
            "source_attempts":rows,
        }

    def test_synthetic_two_targets_plus_btc_45day_complete_does_not_score_model(self):
        data=gate.join_census(self.fixture())
        self.assertEqual(data["original_t0_symbols_total"],3)
        self.assertEqual(data["frozen_source_days_per_symbol"],15)
        self.assertEqual(data["technical_original_d0_source_complete_symbols"],2)
        self.assertEqual(data["technical_rbtc_d1_source_complete_symbols"],2)
        self.assertEqual(data["technical_offline_replay_source_complete_symbols"],2)
        self.assertEqual(data["technical_future_label_source_complete_symbols"],2)
        self.assertEqual(data["source_stage_status_counts"],{
            "SOURCE_COMPLETE_OFFLINE_REPLAY_ONLY":2,
            "BTC_BENCHMARK_SOURCE_COMPLETE":1})
        self.assertTrue(data["btc_benchmark_research_d1_source_ready"])
        btc=next(x for x in data["symbols"] if x["symbol"]=="BTCUSDT")
        self.assertFalse(btc["research_d1_target"])
        self.assertFalse(btc["technically_eligible_for_offline_rbtc_d1_source_replay"])
        self.assertTrue(data["all_source_15days_complete"])
        self.assertEqual(data["G1"],"NOT_SCORABLE")
        self.assertEqual(data["G2"],"UNKNOWN")
        self.assertEqual(data["G3"],"NOT_SCORABLE")
        self.assertEqual(data["G4"],"UNKNOWN")
        self.assertEqual(data["G6"],"NO_GO")
        self.assertFalse(data["metrics_from_future_labels_computed"])
        self.assertFalse(data["replay_engine_executed"])
        self.assertFalse(data["point_in_time_http_origin_attested"])
        self.assertFalse(data["ready_for_full_market_point_in_time_OOS"])
        self.assertTrue(all(not x["original_d0_core_executed"] for x in data["symbols"]))
        self.assertTrue(data["NO_AUTOMATIONS"])
        self.assertEqual(data["window_end_exclusive_utc"],"2026-11-09T00:00:00Z")

    def test_labels_missing_keeps_d0_replay_separate_from_g1_score(self):
        d=gate.join_census(self.fixture(missing={("AAAUSDT","2026-11-10")}))
        statuses={x["symbol"]:x for x in d["symbols"]}
        self.assertEqual(d["source_stage_status_counts"],{
            "D0_D1_SOURCE_READY_GT_LABELS_BLOCKED":1,
            "SOURCE_COMPLETE_OFFLINE_REPLAY_ONLY":1,
            "BTC_BENCHMARK_SOURCE_COMPLETE":1,
        })
        self.assertTrue(statuses["AAAUSDT"]["technically_eligible_for_offline_d0_d1_source_replay"])
        self.assertFalse(statuses["AAAUSDT"]["technically_eligible_for_retrospective_gt_labels"])
        self.assertIn("FUTURE_2X_LABEL_7D_MISSING_OR_INVALID",
                      statuses["AAAUSDT"]["source_blockers"])
        self.assertEqual(d["G1"],"NOT_SCORABLE")

    def test_missing_observation_source_blocks_signal_even_if_future_labels_exist(self):
        d=gate.join_census(self.fixture(missing={("AAAUSDT","2026-11-04")}))
        row=next(x for x in d["symbols"] if x["symbol"]=="AAAUSDT")
        self.assertEqual(row["status"],"D0_D1_SOURCE_BLOCKED")
        self.assertFalse(row["technically_eligible_for_offline_d0_d1_source_replay"])
        self.assertFalse(row["technically_eligible_for_retrospective_gt_labels"])
        self.assertEqual(row["original_d0_watch_event_id"],None)

    def test_baseline_absence_does_not_silently_default_volume(self):
        d=gate.join_census(self.fixture(missing={("AAAUSDT","2026-11-01")}))
        row=next(x for x in d["symbols"] if x["symbol"]=="AAAUSDT")
        self.assertIn("BASELINE_24H_MISSING_OR_INVALID",row["source_blockers"])
        self.assertFalse(row["technically_eligible_for_offline_d0_d1_source_replay"])

    def test_codex_p2_btc_observation_missing_aaa_d0_ready_but_research_d1_blocked(self):
        bad=self.fixture(symbols=("AAAUSDT","BTCUSDT"),
                         missing={("BTCUSDT","2026-11-04")})
        result=gate.join_census(bad)
        aaa=next(x for x in result["symbols"] if x["symbol"]=="AAAUSDT")
        self.assertTrue(aaa["technically_eligible_for_offline_original_d0_source_replay"])
        self.assertTrue(aaa["technically_eligible_for_original_d0_gt2x_label_sources"])
        self.assertFalse(aaa["technically_eligible_for_offline_rbtc_d1_source_replay"])
        self.assertFalse(aaa["technically_eligible_for_offline_d0_d1_source_replay"])
        self.assertFalse(aaa["technically_eligible_for_retrospective_gt_labels"])
        self.assertEqual(aaa["status"],"D0_SOURCE_READY_RBTC_D1_BLOCKED")
        self.assertIn("BTC_OBSERVATION_7D_MISSING_OR_INVALID",aaa["source_blockers"])
        self.assertEqual(result["technical_original_d0_source_complete_symbols"],1)
        self.assertEqual(result["technical_rbtc_d1_source_complete_symbols"],0)
        self.assertEqual(result["technical_offline_replay_source_complete_symbols"],0)
        self.assertEqual(result["technical_future_label_source_complete_symbols"],0)
        self.assertFalse(result["btc_benchmark_research_d1_source_ready"])
        self.assertEqual(result["G2"],"UNKNOWN")
        self.assertFalse(result["metrics_from_future_labels_computed"])
        self.assertFalse(result["replay_engine_executed"])

    def test_btc_missing_from_frozen_roster_does_not_remove_candidate_or_fake_btc(self):
        data=gate.join_census(self.fixture(symbols=("AAAUSDT","BBBUSDT")))
        self.assertEqual(data["original_t0_symbols_total"],2)
        self.assertEqual(data["technical_original_d0_source_complete_symbols"],2)
        self.assertEqual(data["technical_offline_replay_source_complete_symbols"],0)
        self.assertEqual(data["technical_future_label_source_complete_symbols"],0)
        self.assertFalse(data["btc_benchmark_in_t0_source_census"])
        self.assertEqual(data["source_stage_status_counts"],
                         {"D0_SOURCE_READY_RBTC_D1_BLOCKED":2})
        for row in data["symbols"]:
            self.assertIn("BTC_BENCHMARK_NOT_IN_T0_SOURCE_CENSUS",
                          row["source_blockers"])
            self.assertTrue(row["technically_eligible_for_offline_original_d0_source_replay"])
            self.assertFalse(row["technically_eligible_for_offline_rbtc_d1_source_replay"])

    def test_btc_complete_restores_research_d1_without_new_model_or_gt_event(self):
        data=gate.join_census(self.fixture(symbols=("AAAUSDT","BTCUSDT")))
        aaa=next(x for x in data["symbols"] if x["symbol"]=="AAAUSDT")
        self.assertTrue(aaa["technically_eligible_for_offline_original_d0_source_replay"])
        self.assertTrue(aaa["technically_eligible_for_offline_rbtc_d1_source_replay"])
        self.assertEqual(aaa["status"],"SOURCE_COMPLETE_OFFLINE_REPLAY_ONLY")
        self.assertEqual(aaa["source_blockers"],[])
        self.assertEqual(data["technical_rbtc_d1_source_complete_symbols"],1)
        self.assertTrue(data["btc_benchmark_research_d1_source_ready"])
        self.assertIsNone(aaa["original_d0_watch_event_id"])
        self.assertIsNone(aaa["original_d1_research_event_id"])
        self.assertEqual(data["G1"],"NOT_SCORABLE")
        self.assertEqual(data["G6"],"NO_GO")

    def test_btc_missing_baseline_blocks_rbtc_d1_without_erasing_d0(self):
        d=gate.join_census(self.fixture(
            symbols=("AAAUSDT","BTCUSDT"),
            missing={("BTCUSDT","2026-11-01")}))
        aaa=next(x for x in d["symbols"] if x["symbol"]=="AAAUSDT")
        self.assertTrue(aaa["technically_eligible_for_offline_original_d0_source_replay"])
        self.assertFalse(aaa["technically_eligible_for_offline_rbtc_d1_source_replay"])
        self.assertIn("BTC_BASELINE_24H_MISSING_OR_INVALID",aaa["source_blockers"])

    def test_btc_future_gt_label_missing_does_not_block_same_time_research_d1(self):
        d=gate.join_census(self.fixture(
            symbols=("AAAUSDT","BTCUSDT"),
            missing={("BTCUSDT","2026-11-11")}))
        aaa=next(x for x in d["symbols"] if x["symbol"]=="AAAUSDT")
        self.assertTrue(aaa["technically_eligible_for_offline_rbtc_d1_source_replay"])
        self.assertTrue(aaa["technically_eligible_for_retrospective_gt_labels"])
        self.assertFalse(d["all_source_15days_complete"])
        self.assertTrue(d["btc_benchmark_research_d1_source_ready"])

    def test_same_btc_observation_gap_blocks_all_targets_not_just_first(self):
        d=gate.join_census(self.fixture(
            missing={("BTCUSDT","2026-11-04")}))
        self.assertEqual(d["original_t0_symbols_total"],3)
        self.assertEqual(d["technical_original_d0_source_complete_symbols"],2)
        self.assertEqual(d["technical_rbtc_d1_source_complete_symbols"],0)
        self.assertEqual(d["source_stage_status_counts"][
            "D0_SOURCE_READY_RBTC_D1_BLOCKED"],2)
        self.assertEqual(d["source_stage_status_counts"][
            "BTC_BENCHMARK_SOURCE_INCOMPLETE"],1)

    def test_single_missing_attempt_while_pretending_complete_is_rejected(self):
        f=self.fixture()
        f["source_attempts"].pop()
        with self.assertRaisesRegex(ValueError,"FULL_SYMBOL_DAY_CENSUS"):
            gate.join_census(f)

    def test_duplication_and_disguised_symbol_are_rejected(self):
        f=self.fixture()
        f["source_attempts"][-1]=dict(f["source_attempts"][0])
        with self.assertRaisesRegex(ValueError,"ATTEMPT_ID_STATUS_OR_DAY_DRIFT"):
            gate.join_census(f)
        f=self.fixture()
        f["source_attempts"][0]["symbol"]="SECURITY/AAAUSDT"
        with self.assertRaisesRegex(ValueError,"ATTEMPT_ID_STATUS_OR_DAY_DRIFT"):
            gate.join_census(f)

    def test_source_complete_claim_with_missing_attempt_is_rejected(self):
        f=self.fixture(missing={("AAAUSDT","2026-11-08")})
        f["verified_complete_all_15days"]=True
        with self.assertRaisesRegex(ValueError,"CENSUS_COMPLETENESS_MISMATCH"):
            gate.join_census(f)

    def test_status_count_and_segment_bucket_integrity_rejected_if_tampered(self):
        f=self.fixture()
        f["actual_status_counts"]["VERIFIED_1440_OFFICIAL_1M"]=29
        with self.assertRaisesRegex(ValueError,"CENSUS_COMPLETENESS_MISMATCH"):
            gate.join_census(f)
        f=self.fixture()
        f["segment_source_status_counts"]["FUTURE_2X_LABEL_7D"]={}
        with self.assertRaisesRegex(ValueError,"CENSUS_COMPLETENESS_MISMATCH"):
            gate.join_census(f)

    def test_unregistered_window_cannot_relabel_2025_or_october(self):
        f=self.fixture()
        f["window_start_utc"]="2026-11-03T00:00:00Z"
        with self.assertRaisesRegex(ValueError,"UNVERIFIED_CENSUS_OR_PIT"):
            gate.join_census(f)

    def test_source_free_run_never_uses_old_511_or_sets_population_denominator(self):
        for start in t0.WINDOWS:
            d=gate.run(start,"2026-10-26T00:00:00Z")
            self.assertEqual(d["source_status"],"WAITING_FOR_PRESTART_SOURCE_WINDOW")
            self.assertIsNone(d["original_t0_symbols_total"])
            self.assertEqual(len(d["publisher_day_states"]),15)
            self.assertEqual(d["G0"],"POPULATION_UNKNOWN")
            self.assertIsNone(d["btc_benchmark_research_d1_source_ready"])
            self.assertIsNone(d["technical_original_d0_source_complete_symbols"])
            self.assertIsNone(d["technical_rbtc_d1_source_complete_symbols"])
            self.assertEqual(d["G1"],"NOT_SCORABLE")
            self.assertFalse(d["metrics_from_future_labels_computed"])
            self.assertEqual(d["G6"],"NO_GO")

    def test_real_october_t0_source_rejected_before_downstream_daily_scoring(self):
        real=(Path(__file__).resolve().parents[2]/"monster"/"evidence"/
              "monster_stage163_spot_original_http_t0_actual")
        with tempfile.TemporaryDirectory() as source_root:
            for window in t0.WINDOWS:
                with self.subTest(window=window):
                    with self.assertRaisesRegex(ValueError,"PRESTART_15MIN"):
                        gate.run(window,"2026-11-02T00:00:00Z",
                                 real/"source_raw_http.zip",
                                 real/"source_receipts.json",
                                 Path(source_root))

    def test_source_dir_without_t0_original_bytes_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError,"NO_OFFICIAL_SOURCE_WITHOUT_T0"):
                gate.run(self.WINDOW,"2026-11-02T00:00:00Z",official_dir=Path(d))
            with self.assertRaisesRegex(ValueError,"T0_ZIP_AND_RECEIPT_PAIR_REQUIRED"):
                gate.run(self.WINDOW,"2026-11-02T00:00:00Z",source_zip=Path(d))

    def test_identity_unknown_even_if_synthetic_sources_complete(self):
        r=gate.join_census(self.fixture())
        self.assertFalse(r["actual_market_source_is_exchange_signed"])
        self.assertFalse(r["t0_issuer_identity_and_dynamic_listing_complete"])
        self.assertEqual(r["G0"],"PARTIAL_DYNAMIC_LISTINGS_AND_CRYPTO_IDENTITY_UNKNOWN")
        self.assertTrue(all(not x["t0_listing_and_crypto_identity_independently_proven"]
                            for x in r["symbols"]))

    def test_gate_thresholds_are_frozen_metadata_not_calculated_from_exposed_data(self):
        r=gate.join_census(self.fixture())
        self.assertEqual((r["G1_min_independent_gt2x"],r["G1_min_windows"]),(20,3))
        self.assertEqual((r["G1_strict_advance_min"],r["G1_advance_5m_min"]),
                         ("0.90","0.85"))
        self.assertEqual((r["G2_retain_min"],r["G3_avg_per_day_max"],r["G3_peak_per_day_max"]),
                         ("0.80",5,12))
        self.assertEqual(r["preregistered_research_D1_model"],"D1_RBTC15_LAST5_V1")


if __name__=="__main__":
    unittest.main()
