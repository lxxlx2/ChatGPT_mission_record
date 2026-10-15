"""Stage138 genuine old V4 core running against synthetic ZIPs, NOT market results."""
import copy
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import monster_v4_stage138_manual_evidence_scorecard as s138
from test_monster_v4_stage137_dynamic_t0_original_core_causal_replay import (
    Stage137Tests as OldCoreFixture)


def move_utc(utc_text, days):
    if utc_text is None:
        return None
    dt = datetime.fromisoformat(utc_text.replace("Z", "+00:00"))
    return (dt + timedelta(days=days)).isoformat().replace("+00:00", "Z")


def simulated_disjoint_copy(base, offset_days, serial):
    """Only for testing aggregation arithmetic; NEVER independent market proof."""
    item = copy.deepcopy(base)
    item["new_forward_start_utc"] = move_utc(item["new_forward_start_utc"], offset_days)
    item["new_forward_end_exclusive_utc"] = move_utc(
        item["new_forward_end_exclusive_utc"], offset_days)
    digest = hashlib.sha256(("synthetic-FUTURE-fixture-" + str(serial)).encode()).hexdigest()
    item["stage133_original_raw_packet_canonical_sha256"] = digest
    item["stage136_offline_source_plan"]["stage134_t0_source_sha256"] = digest
    item["stage135_source_audit"]["stage133_receipt_packet_SHA256"] = digest
    item["stage137_unmodified_core_replay"]["stage133_original_packet_sha256"] = digest
    item["stage136_offline_source_plan"]["window_utc_start"] = item["new_forward_start_utc"]
    item["stage136_offline_source_plan"]["window_utc_end_exclusive"] = item["new_forward_end_exclusive_utc"]
    item["stage135_source_audit"]["new_forward_start_utc"] = item["new_forward_start_utc"]
    item["stage135_source_audit"]["new_forward_end_exclusive_utc"] = item["new_forward_end_exclusive_utc"]
    item["stage137_unmodified_core_replay"]["new_forward_start_utc"] = item["new_forward_start_utc"]
    item["stage137_unmodified_core_replay"]["new_forward_end_exclusive_utc"] = item["new_forward_end_exclusive_utc"]
    for row in item["population_rows"]:
        replay = row.get("counterfactual_discovery_delay_original_D0_D1_offline")
        if replay is not None:
            replay["first_source_bar_not_verified_actual_discovery_utc"] = move_utc(
                replay["first_source_bar_not_verified_actual_discovery_utc"], offset_days)
            replay["first_source_original_2x_high_fixed_denominator_utc"] = move_utc(
                replay["first_source_original_2x_high_fixed_denominator_utc"], offset_days)
            for alt in replay["delays"].values():
                for key in ("visible_from_UTC", "first_tick_utc",
                            "D0_first_UTC", "D1_first_UTC"):
                    alt[key] = move_utc(alt[key], offset_days)
                strict=alt.get("strict_since_discovery")
                if strict is not None:
                    for key in ("first_tick_utc", "D0_first_UTC", "D1_first_UTC",
                                "earliest_possible_D1_61min_history_UTC",
                                "first_UTC_aligned_completed_5m_source_open"):
                        strict[key] = move_utc(strict[key], offset_days)
        row["D0_first_UTC"] = move_utc(row["D0_first_UTC"], offset_days)
        row["D1_first_UTC"] = move_utc(row["D1_first_UTC"], offset_days)
        if "gross_future_labels_not_real_profit" in row:
            labels = row["gross_future_labels_not_real_profit"]
            for m in (2, 5, 10):
                label = f"first_GT{m}x_HIGH_UTC_EVALUATION_ONLY"
                labels[label] = move_utc(labels[label], offset_days)
    item["manifest_self_consistency_sha256_NOT_ATTESTATION"] = s138.canonical_hash({
        k: v for k, v in item.items()
        if k != "manifest_self_consistency_sha256_NOT_ATTESTATION"})
    return item


class Stage138Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        OldCoreFixture.setUpClass()
        cls.old = OldCoreFixture
        cls.packet = cls.old.packet
        cls.root = cls.old.root
        cls.arrivals = cls.old.result["all_source_population_rows"]
        cls.report = s138.plan_or_evaluate(
            cls.packet, cls.root,
            {"schema": "MONSTER_STAGE134_UNVERIFIED_ARRIVAL_CANDIDATES_V1",
             "rows": [{"symbol": "NEWUSDT",
                       "first_observed_minute_utc": "2026-10-28T06:21:00Z",
                       "source_status": "RAW_UNVERIFIED_CANDIDATE"}]},
            phase="evaluate")

    @classmethod
    def tearDownClass(cls):
        OldCoreFixture.tearDownClass()

    def test_real_stage133_to_stage137_original_core_under_one_evaluation(self):
        r = self.report
        self.assertEqual(r["phase"], "EVALUATE")
        self.assertEqual(r["stage136_offline_source_plan"]["mode"], "OFFLINE_PLAN")
        self.assertEqual(r["stage136_offline_source_plan"]["newly_fetched_checksum_verified"], 0)
        self.assertEqual(r["stage135_source_audit"]["full_market_attempts"], 4)
        self.assertEqual(r["stage137_unmodified_core_replay"]["model_attempts_scored_or_classified"], 4)
        self.assertEqual(len(r["population_rows"]), 4)
        a = r["population_summary"]
        self.assertEqual(a["full_market_attempts"], 4)
        self.assertEqual(a["original_core_source_compatible"], 2)
        self.assertEqual(a["SOURCE_CENSORED_NO_REPLAY"], 1)
        self.assertEqual(a.get("MODEL_SYMBOL_UNSUPPORTED_NOT_A_NO_WATCH", 0), 0)
        self.assertEqual(a["ORIGINAL_V4_NUMERIC_CORE_WITH_UNICODE_IDENTITY_ADAPTER_CAUSAL_OFFLINE"], 1)
        self.assertEqual(a.get("NEW_LISTING_REPLAY_NOT_YET_SUPPORTED_PIT_UNVERIFIED", 0), 0)
        self.assertEqual(a["ORIGINAL_CORE_NEW_LISTING_COLD_START_UNVERIFIED_PIT_CAUSAL_OFFLINE"], 1)
        self.assertEqual(a["cold_start_source_conditioned_issuer_unverified"], 1)
        self.assertEqual(a.get("cold_start_first_D0", 0), 0)
        self.assertEqual(a["gross_2x"], 1)
        self.assertEqual(a["D0_early5_2x"], 1)
        self.assertEqual((r["G0"], r["G1"], r["G4"], r["G6"]),
                         ("PARTIAL", "NOT_SCORABLE", "UNKNOWN", "NO_GO"))
        self.assertEqual(r["stage136_offline_source_plan"]["all_symbol_day_attempts"], 35)
        self.assertEqual(s138.verify_evaluate_manifest(r)[2], a)
        self.assertTrue(r["hypothetical_model_replay_is_not_G0_G1_proof"])

    def test_plan_on_absent_original_archives_never_downloads_or_replays(self):
        with tempfile.TemporaryDirectory() as directory:
            archived = Path(directory) / "archives-not-created"
            report = s138.plan_or_evaluate(self.packet, archived)
            self.assertFalse(archived.exists())
        self.assertEqual(report["phase"], "PLAN")
        self.assertEqual(report["stage136_offline_source_plan"]["all_symbol_day_attempts"], 27)
        self.assertEqual(report["stage136_offline_source_plan"]["pending_manual_run"], 27)
        self.assertNotIn("population_rows", report)
        self.assertEqual(report["model_buy"], "NO_GO")
        self.assertFalse(report["scheduled_collection"])
        with self.assertRaisesRegex(ValueError, "AGGREGATE_REQUIRES_EVALUATE"):
            s138.aggregate([report])

    def test_three_synthetic_nonoverlapping_windows_keep_total_attempts_not_G1(self):
        one = self.report
        two = simulated_disjoint_copy(one, 14, 2)
        three = simulated_disjoint_copy(one, 28, 3)
        all_windows = s138.aggregate([three, one, two])
        self.assertEqual(all_windows["input_manifests_count"], 3)
        self.assertEqual(all_windows["all_original_venue_population_descriptive_only"]["full_market_attempts"], 12)
        self.assertEqual(all_windows["all_original_venue_population_descriptive_only"]["SOURCE_CENSORED_NO_REPLAY"], 3)
        self.assertEqual(all_windows["all_original_venue_population_descriptive_only"]["gross_2x"], 3)
        self.assertEqual(len(all_windows["per_window_source_retained"]), 3)
        self.assertEqual((all_windows["G0"], all_windows["G1"], all_windows["G6"]),
                         ("PARTIAL", "NOT_SCORABLE", "NO_GO"))
        self.assertTrue(all_windows["raw_venue_replay_rate_diagnostics_NOT_crypto_accuracy"][
            "cannot_measure_issuer_confirmed_crypto_true_positives"])
        self.assertEqual(
            all_windows["declared_disjoint_window_count_not_verified_as_external_market_source"], 3)

    def test_stage145_claude_P1_all_cohort_2x_and_source_missing_venue_counterfactual(self):
        cases=[
            {"gross_2x":1,"D0_early5_2x":1,
             "cold_start_gross_2x":1,"cold_start_D0_early5_2x":0,
             "recent_preT0_gross_2x":1,"recent_preT0_D0_early5_2x":0,
             "SOURCE_CENSORED_NO_REPLAY":1},
            {"gross_2x":0,"D0_early5_2x":0,
             "cold_start_gross_2x":1,"cold_start_D0_early5_2x":1,
             "SOURCE_CENSORED_NO_REPLAY":1}
        ]
        first=s138.population_coverage_sensitivity(cases[0])
        self.assertEqual(first["venue_complete_case_preexisting_early5_pct"],100)
        self.assertEqual(first["venue_complete_case_all_three_cohorts_posthoc_2x"],3)
        self.assertEqual(first["venue_complete_case_all_three_cohorts_D0_early5_2x"],1)
        self.assertEqual(first["venue_complete_case_all_three_cohorts_early5_pct_not_G1"],33.333)
        self.assertEqual(first["all_three_cohort_2x_plus_assumed_missing_as_missed_2x"],4)
        self.assertEqual(
            first["pessimistic_all_three_cohorts_if_each_censored_were_missed_2x_pct_NOT_G1"],25)
        self.assertEqual(first["by_cohort_complete_case_early5_pct_NOT_G1"]["in_window_new"],0)
        self.assertEqual(first["by_cohort_complete_case_early5_pct_NOT_G1"]["recent_pre_T0"],0)
        self.assertTrue(first["pessimistic_all_cohort_scenario_not_statistically_validated_lower_bound"])
        self.assertFalse(first["G1_claimable"])
        second=s138.population_coverage_sensitivity(cases[1])
        self.assertEqual(second["venue_complete_case_all_three_cohorts_early5_pct_not_G1"],100)
        self.assertEqual(
            second["pessimistic_all_three_cohorts_if_each_censored_were_missed_2x_pct_NOT_G1"],50)
        with self.assertRaisesRegex(ValueError,"IMPOSSIBLE_2X_COHORT"):
            s138.population_coverage_sensitivity({"gross_2x":0,"D0_early5_2x":1})

    def test_stage145_full_integrated_delay_dual_info_sets_reconcile(self):
        rows=self.report["population_rows"]
        new=next(x for x in rows if x["population_lane"]=="IN_WINDOW_FIRST_TRADABLE_MINUTE_CANDIDATE")
        source=new["counterfactual_discovery_delay_original_D0_D1_offline"]
        self.assertTrue(source["two_information_sets_per_delay_readback_A_vs_strict_post_discovery_B"])
        scored=self.report["inwindow_discovery_latency_original_core_replay_research_only"]
        self.assertEqual(scored["counts"]["source_conditioned_latencies_rerun_all_four"],1)
        self.assertEqual(scored["counts"]["delay_0m_strict_post_discovery_model_replay"],1)
        self.assertEqual(scored["counts"]["delay_5m_strict_post_discovery_model_replay"],1)
        self.assertTrue(scored["A_B_not_guaranteed_mathematically_ordered_recall_bounds"])
        self.assertEqual(s138.verify_evaluate_manifest(self.report)[2]["full_market_attempts"],4)
        forged=copy.deepcopy(rows)
        evil=next(x for x in forged if x["population_lane"]=="IN_WINDOW_FIRST_TRADABLE_MINUTE_CANDIDATE")
        evil["counterfactual_discovery_delay_original_D0_D1_offline"]["delays"]["5m"]["strict_since_discovery"]["earliest_possible_D1_61min_history_UTC"]="2026-10-28T06:21:00Z"
        with self.assertRaisesRegex(ValueError,"STRICT_61M_CLOCK_DRIFT"):
            s138.original_core_discovery_delay_scorecard(forged)

    def test_stage144_real_original_core_latency_scorecard_detects_five_minute_missed_D0(self):
        from decimal import Decimal
        from monster_v4_stage137_dynamic_t0_original_core_causal_replay import (
            replay_new_arrival_cold_start, original_core_contract)
        first = s138.s131.stamp("2026-10-28T06:21:00Z")
        bars = []
        for i in range(100):
            price = Decimal("1.08") if i >= 8 else Decimal("1")
            high = Decimal("2.25") if i == 75 else price*Decimal("1.01")
            bars.append((first+i*60_000,price,high,price*Decimal("0.99"),
                         price,Decimal("150000"),1000))
        scored = replay_new_arrival_cold_start(
            "FASTUSDT",first,first+100*60_000,bars,original_core_contract(),
            include_discovery_delay_replays=True)
        scored["symbol_exact"]="FASTUSDT"
        scored["population_lane"]="IN_WINDOW_FIRST_TRADABLE_MINUTE_CANDIDATE"
        counters=s138.original_core_discovery_delay_scorecard([scored])
        c=counters["counts"]
        self.assertEqual(c["source_conditioned_latencies_rerun_all_four"],1)
        self.assertEqual(c["delay_0m_first_D0"],1)
        self.assertEqual(c.get("delay_5m_first_D0",0),0)
        self.assertEqual(c["delay_5m_missed_baseline_D0"],1)
        self.assertEqual(c["delay_0m_D0_early5_before_same_fixed_2x"],1)
        self.assertEqual(c.get("delay_5m_D0_early5_before_same_fixed_2x",0),0)
        self.assertFalse(counters.get("G1_claimable",False))
        self.assertTrue(counters["NOT_G1_G2_G3_G4_PASS"])
        corrupted=copy.deepcopy(scored)
        corrupted["counterfactual_discovery_delay_original_D0_D1_offline"][
            "delays"]["0m"]["D0_first_UTC"]=None
        with self.assertRaisesRegex(ValueError,"ZERO_LATENCY_NOT_ORIGINAL_CORE_BASELINE"):
            s138.original_core_discovery_delay_scorecard([corrupted])

    def test_stage144_full_staged_archives_preserve_source_census_and_delay_evidence(self):
        evidence=self.report["inwindow_discovery_latency_original_core_replay_research_only"]
        c=evidence["counts"]
        self.assertEqual(c["source_complete_inwindow_cold_start_rows"],1)
        self.assertEqual(c["source_conditioned_latencies_rerun_all_four"],1)
        self.assertEqual(c["delay_0m_source_conditioned_model_replay"],1)
        self.assertEqual(c["delay_5m_source_conditioned_model_replay"],1)
        self.assertEqual(c.get("legacy_cold_start_rows_without_delay_reruns",0),0)
        self.assertEqual(s138.verify_evaluate_manifest(self.report)[2]["full_market_attempts"],4)
        self.assertTrue(evidence["original_venue_issuer_PIT_and_new_listing_census_unverified"])

    def test_claude_p1_all_cohort_G3_includes_recent_and_new_listing_D1(self):
        start = s138.s131.stamp("2026-10-28T06:20:00Z")
        end=start+7*86_400_000
        no_cross = {}
        for m in (2,5,10):
            no_cross[f"first_GT{m}x_HIGH_UTC_EVALUATION_ONLY"] = None
            for k in (f"D0_first_strict_pre_GT{m}x",
                      f"D0_first_pre_GT{m}x_5m",
                      f"D1_first_pre_GT{m}x_5m"):
                no_cross[k]=False
        rows=[
            {"symbol_exact":"NEWUSDT",
             "population_lane":"IN_WINDOW_FIRST_TRADABLE_MINUTE_CANDIDATE",
             "replay_status":s138.STATES[5],
             "D0_first_UTC":"2026-10-28T06:57:00Z",
             "D1_first_UTC":"2026-10-28T07:24:00Z",
             "gross_future_labels_not_real_profit":copy.deepcopy(no_cross)},
            {"symbol_exact":"RECENTUSDT",
             "population_lane":"PREEXISTING_AT_WINDOW_START",
             "replay_status":s138.STATES[6],
             "D0_first_UTC":"2026-10-28T07:00:00Z",
             "D1_first_UTC":"2026-10-28T07:30:00Z",
             "gross_future_labels_not_real_profit":copy.deepcopy(no_cross)},
            {"symbol_exact":"ESTABLISHEDUSDT",
             "population_lane":"PREEXISTING_AT_WINDOW_START",
             "replay_status":s138.STATES[3],
             "D0_first_UTC":"2026-10-28T07:03:00Z",
             "D1_first_UTC":"2026-10-28T07:33:00Z",
             "gross_future_labels_not_real_profit":copy.deepcopy(no_cross)},
            {"symbol_exact":"CENSOREDUSDT",
             "population_lane":"PREEXISTING_AT_WINDOW_START",
             "replay_status":s138.STATES[0],
             "D0_first_UTC":None,"D1_first_UTC":None},
        ]
        summary,daily=s138.summarize_rows(rows,start,end)
        self.assertEqual(daily,[3,0,0,0,0,0,0])
        self.assertEqual(summary["all_cohort_first_D1"],3)
        self.assertEqual(summary["cold_start_first_D1"],1)
        self.assertEqual(summary["recent_preT0_first_D1"],1)
        self.assertEqual(summary["unique_first_D1"],1)
        self.assertEqual(summary["SOURCE_CENSORED_NO_REPLAY"],1)
        analysis=s138.population_coverage_sensitivity(summary)
        self.assertEqual(analysis["source_censored_or_unsupported_attempts_unknown_outcome"],1)
        self.assertIsNone(analysis["venue_complete_case_preexisting_early5_pct"])
        self.assertFalse(analysis["G1_claimable"])

    def test_duplicate_source_and_overlapping_windows_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "DUPLICATE_OR_OVERLAPPING"):
            s138.aggregate([self.report, copy.deepcopy(self.report)])
        # 6 days => window overlap even with a distinct untrusted local digest.
        other = simulated_disjoint_copy(self.report, 6, 4)
        with self.assertRaisesRegex(ValueError, "DUPLICATE_OR_OVERLAPPING"):
            s138.aggregate([self.report, other])

    def test_counter_forgery_or_manifest_edit_fails_closed(self):
        tampered = copy.deepcopy(self.report)
        tampered["population_summary"]["gross_2x"] = 999
        tampered["manifest_self_consistency_sha256_NOT_ATTESTATION"] = s138.canonical_hash({
            k: v for k, v in tampered.items()
            if k != "manifest_self_consistency_sha256_NOT_ATTESTATION"})
        with self.assertRaisesRegex(ValueError, "FORGED_OR_DRIFTED"):
            s138.aggregate([tampered])
        edited = copy.deepcopy(self.report)
        edited["G1"] = "PASS"
        with self.assertRaisesRegex(ValueError, "SELF_HASH_MISMATCH"):
            s138.aggregate([edited])
        forged = copy.deepcopy(self.report)
        forged["G1"] = "PASS"
        forged["manifest_self_consistency_sha256_NOT_ATTESTATION"] = s138.canonical_hash({
            k: v for k, v in forged.items()
            if k != "manifest_self_consistency_sha256_NOT_ATTESTATION"})
        with self.assertRaisesRegex(ValueError, "FORGED_OR_DRIFTED"):
            s138.aggregate([forged])

    def test_orig_zip_checksum_tamper_fails_evaluate_not_swallowed(self):
        with tempfile.TemporaryDirectory() as folder:
            dest = Path(folder) / "ABCUSDT"
            dest.mkdir()
            (dest / "2026-10-27.zip").write_bytes(b"bad original bytes")
            (dest / "2026-10-27.zip.CHECKSUM").write_text("0"*64)
            with self.assertRaises((ValueError, __import__("zipfile").BadZipFile)):
                s138.plan_or_evaluate(self.packet, folder, phase="evaluate")

    def test_cli_default_plan_and_evaluate_and_aggregate_json(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            t0 = root / "t0.json"
            arrivals = root / "arrivals.json"
            plan = root / "plan.json"
            evaluation = root / "evaluation.json"
            multiple = root / "multi.json"
            t0.write_text(json.dumps(self.packet, ensure_ascii=False))
            arrivals.write_text(json.dumps({
                "schema": "MONSTER_STAGE134_UNVERIFIED_ARRIVAL_CANDIDATES_V1",
                "rows": [{"symbol": "NEWUSDT",
                          "first_observed_minute_utc": "2026-10-28T06:21:00Z",
                          "source_status": "RAW_UNVERIFIED_CANDIDATE"}]},
                ensure_ascii=False))
            path = str(Path(s138.__file__))
            cmd = [sys.executable, path, "--t0", str(t0),
                   "--archive-root", str(self.root),
                   "--arrival-candidates", str(arrivals)]
            p = subprocess.run(cmd + ["--out", str(plan)], capture_output=True, text=True, timeout=50)
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertEqual(json.loads(plan.read_text())["phase"], "PLAN")
            e = subprocess.run(cmd + ["--phase", "evaluate", "--out", str(evaluation)],
                               capture_output=True, text=True, timeout=95)
            self.assertEqual(e.returncode, 0, e.stderr)
            self.assertEqual(json.loads(evaluation.read_text())["phase"], "EVALUATE")
            a = subprocess.run([sys.executable, path, "--aggregate", str(evaluation),
                                "--out", str(multiple)],
                               capture_output=True, text=True, timeout=35)
            self.assertEqual(a.returncode, 0, a.stderr)
            result = json.loads(multiple.read_text())
            self.assertEqual(result["input_manifests_count"], 1)
            self.assertEqual(result["G1"], "NOT_SCORABLE")
            self.assertEqual(result["model_buy"], "NO_GO")
            fail = subprocess.run([sys.executable, path, "--out", str(root / "no.json")],
                                  capture_output=True, text=True, timeout=20)
            self.assertNotEqual(fail.returncode, 0)
            self.assertFalse((root / "no.json").exists())


if __name__ == "__main__":
    unittest.main()
