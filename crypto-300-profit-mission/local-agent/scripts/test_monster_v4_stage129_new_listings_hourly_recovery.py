import copy
import json
import unittest

import monster_v4_stage129_new_listings_hourly_recovery as s


class Stage129Test(unittest.TestCase):
    def setUp(self):
        shard=json.loads(s.SHARDS[0].read_text(encoding="utf-8"))
        self.record=copy.deepcopy(shard["source_replies"][0])
        self.expected={
            "anchor":self.record["anchor"],
            "symbol":self.record["symbol"],
            "later_onboard_utc":self.record["later_onboard_utc"],
        }

    def test_frozen_source_shape_and_first_hour_source(self):
        row=s.assess_one(self.record,self.expected)
        self.assertEqual(row["analysis_status"],"COMPLETE_FROM_FIRST_OBSERVED_1H_TO_END_PRICE_PROXY_ONLY")
        self.assertTrue(row["observed_partial_listing_window_is_contiguous_to_end"])
        self.assertEqual(row["first_D0_early5"],"NOT_SCORABLE_FROM_HOURLY")
        self.assertEqual(row["actual_executable_net"],"UNKNOWN")

    def test_mutated_historical_request_rejected(self):
        self.record["request"]["symbol"]="NOT_THE_FROZEN_SYMBOL"
        with self.assertRaisesRegex(ValueError,"NOT_FROZEN"):
            s.assess_one(self.record,self.expected)

    def test_missing_kline_is_censored_never_false_no2x(self):
        self.record["source_status"]="API_ERROR_NOT_A_NEGATIVE"
        self.record["raw_structured_klines"]=None
        out=s.assess_one(self.record,self.expected)
        self.assertEqual(out["analysis_status"],"UNAVAILABLE_NOT_A_NEGATIVE")
        self.assertIsNone(out["gte_2x_gross_firsthour_proxy"])

    def test_gap_is_censored_not_missed_profit(self):
        del self.record["raw_structured_klines"][10]
        out=s.assess_one(self.record,self.expected)
        self.assertEqual(out["analysis_status"],"CENSORED_PARTIAL_AFTER_FIRST_OBSERVED_1H")
        self.assertIsNone(out["gte_2x_gross_firsthour_proxy"])

    def test_tampered_candle_rejected(self):
        self.record["raw_structured_klines"][0][2]="NaN"
        with self.assertRaisesRegex(ValueError,"NONFINITE"):
            s.assess_one(self.record,self.expected)

    def test_real_six_source_shards_all31_and_no_oos_claim(self):
        out=s.run()
        self.assertEqual(out["response_count"],31)
        self.assertEqual(out["frozen_case_count"],31)
        self.assertEqual(out["source_status_counts"],
                         {"COMPLETE_FROM_FIRST_OBSERVED_1H_TO_END_PRICE_PROXY_ONLY":31})
        self.assertEqual(out["gross_first_observed_hour_to_later_high_at_least_2x_cases"],2)
        self.assertEqual(out["gross_first_observed_hour_to_later_high_at_least_5x_cases"],0)
        self.assertEqual({x["symbol"] for x in out["all_source_cohort_rows"]
                         if x["gte_2x_gross_firsthour_proxy"] is True},{"VINEUSDT","APRUSDT"})
        self.assertEqual(out["real_new_G1_crypto_full_market"],"NOT_SCORABLE")
        self.assertEqual(out["G4_real_net"],"UNKNOWN")
        self.assertEqual(out["monster_deployment"],"NO_GO")
        self.assertTrue(all(not x["exchange_label_proves_issuer_identity"]
                            for x in out["all_source_cohort_rows"]))


if __name__=="__main__":
    unittest.main()
