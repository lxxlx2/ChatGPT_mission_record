"""H1/H2/H3 independent-review counterexamples for corrected post-review P4-C."""
import copy
import unittest

from bsc_meme_address_model_v1_p4c_v3_review_gate import classify, load


class V3HistoricalCohortAndCalendarReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.docs = load()

    def reject(self, change):
        t = copy.deepcopy(self.docs)
        change(t)
        with self.assertRaises(ValueError):
            classify(t)

    def test_three_original_selection_versions_all_visible(self):
        r = classify(self.docs)
        self.assertEqual(r["selection_grade"], "POST_REVIEW_OUTCOME_AWARE_EXPOSED_NOT_HOLDOUT")
        cohorts = r["three_original_cohort_comparisons"]
        self.assertEqual(cohorts["v1"]["selected_original_P2_indices"], [13,31,38,46,42])
        self.assertEqual(cohorts["v2"]["selected_original_P2_indices"], [15,31,38,46,44])
        self.assertEqual(cohorts["v3"]["selected_original_P2_indices"], [13,15,31,38,46,44])
        self.assertEqual([cohorts[x]["native_block_scope_wei"] for x in ("v1","v2","v3")],
            ["223671359895044206", "-400073738684035463", "-146773456364646148"])
        self.assertEqual((cohorts["v3"]["distinct_wallets"],cohorts["v3"]["distinct_CA"],
                          cohorts["v3"]["positive"],cohorts["v3"]["negative"]), (5,4,3,3))
        self.assertEqual(r["full_successful_receipts"],7)
        self.assertEqual(r["truncated_receipts_remaining_UNVERIFIED"],9)
        self.assertEqual(r["original_signer_block_matched_count"],16)
        self.assertEqual(r["new_cross_CA_realized_PnL"],"UNRESOLVED")
        self.assertEqual(r["P5"],"BLOCKED")
        self.assertEqual(r["PRODUCTION"],"NO_GO")

    def test_h1_missing_restored_positive_13_rejected(self):
        self.reject(lambda d:d["v3"]["corrected_scope"].update(p2_indices=[15,31,38,46,44]))

    def test_h1_silent_v1_to_v2_shift_denial_rejected(self):
        self.reject(lambda d:d["v3"]["admission_of_V1_to_V2_change"].update(
            removed_index_13_without_reason_in_prior_V2=False))

    def test_h1_only_negative_v2_report_cannot_replace_v1(self):
        self.reject(lambda d:d["v3"]["cohort_comparisons"].pop("v1"))

    def test_h1_posthoc_outcomes_cannot_be_called_untouched(self):
        self.reject(lambda d:d["v3"].update(type="PREREGISTERED_UNTOUCHED_HOLDOUT"))

    def test_h1_v1_positive_sum_or_selection_rewritten(self):
        self.reject(lambda d:d["v1"]["freeze_source"].update(episode_indices_zero_based=[15,31,38,46,44]))

    def test_h2_original_239e_march_header_timestamp_tamper_rejected(self):
        self.reject(lambda d:d["header"]["all_13_original_block_hashes_and_integer_timestamps"][4].update(
            milliTimestamp_hex="0x19cef220f6f"))

    def test_h2_restored_13_april_not_2025_rejected(self):
        self.reject(lambda d:d["header"]["all_13_original_block_hashes_and_integer_timestamps"][0].update(
            utc_from_integer_milliseconds="2025-04-20T05:53:09.350Z"))

    def test_h2_missing_239e_last_block_header_rejected(self):
        self.reject(lambda d:d["header"]["all_13_original_block_hashes_and_integer_timestamps"].pop(5))

    def test_h2_2025_wrong_calendar_episode_rejected(self):
        self.reject(lambda d:d["header"]["all_13_original_block_hashes_and_integer_timestamps"][-1].update(
            utc_from_integer_milliseconds="2026-12-29T11:18:55.000Z"))

    def test_h3_truncated_status_must_not_be_a_full_receipt(self):
        self.reject(lambda d:d["partial"]["observations"][0].update(
            provider_JSON_parseable=True,evidence_grade="FULL"))

    def test_h3_visible_status_needs_literal_provider_excerpt(self):
        self.reject(lambda d:d["partial"]["observations"][1].update(
            status_direct_raw_span="test forged string"))

    def test_h3_absent_status_cannot_be_populated_without_original_witness(self):
        self.reject(lambda d:d["partial"]["observations"][-1].update(
            status_literal_if_visible="0x1"))

    def test_h3_original_full_receipt_success_held_to_gas_and_price(self):
        self.reject(lambda d:d["A"]["cases"][0].update(gas_used=None))

    def test_h3_cannot_drop_a_truncated_unknown_record(self):
        self.reject(lambda d:d["partial"]["observations"].pop())

    def test_h1_restored_original_buy_sell_signer_tamper_rejected(self):
        self.reject(lambda d:d["extra"]["source_txs"][0].update(signer_matches=False))


if __name__ == "__main__":
    unittest.main()
