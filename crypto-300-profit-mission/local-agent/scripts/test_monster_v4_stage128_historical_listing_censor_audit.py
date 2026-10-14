import copy
import unittest
from datetime import datetime, timezone

import monster_v4_stage128_historical_listing_censor_audit as s

ANCHOR = int(datetime.fromisoformat("2025-04-19T06:00:00+00:00").timestamp()*1000)
END = ANCHOR + 7 * 86400000


def historic(status="SOURCE_404_MONTHLY_1H_NOT_OBSERVABLE",symbol="龙虾USDT"):
    return {"date":"2025-04-19","symbol":symbol,"status":status,"gt2x":""}


def current(onboard):
    return {"symbol":"龙虾USDT","onboardDate":onboard}


class Stage128Test(unittest.TestCase):
    def test_later_onboard_window_separation_with_no_exclusions(self):
        cases=[
            (END+1,"HOURLY_INCOMPLETE_LATER_ONBOARD_AT_OR_AFTER_WINDOW_END"),
            (END,"HOURLY_INCOMPLETE_LATER_ONBOARD_AT_OR_AFTER_WINDOW_END"),
            (ANCHOR+1,"HOURLY_INCOMPLETE_LATER_ONBOARD_INSIDE_WINDOW"),
            (ANCHOR+3*86400000,"HOURLY_INCOMPLETE_LATER_ONBOARD_INSIDE_WINDOW"),
            (ANCHOR,"HOURLY_INCOMPLETE_LATER_ONBOARD_AT_OR_BEFORE_ANCHOR"),
            (ANCHOR-1,"HOURLY_INCOMPLETE_LATER_ONBOARD_AT_OR_BEFORE_ANCHOR"),
        ]
        for stamp, expected in cases:
            with self.subTest(stamp=stamp):
                a=s.classify(historic(),current(stamp))
                self.assertEqual(a["later_metadata_comparison"],expected)
                self.assertFalse(a["historical_listing_trading_identity_verified"])

    def test_conflicting_complete_is_preserved_not_discarded(self):
        row=historic(s.FULL_HOUR,"币安人生USDT")
        x=s.classify(row,current(END+1000))
        self.assertEqual(x["later_metadata_comparison"],
                         "HOURLY_COMPLETE_LATER_METADATA_ONBOARD_CONTRADICTION")
        self.assertFalse(x["historical_listing_trading_identity_verified"])
        self.assertEqual(x["symbol"],"币安人生USDT")

    def test_later_source_missing_is_unverified_not_never_listed(self):
        self.assertEqual(s.classify(historic(),None)["later_metadata_comparison"],
                         "HOURLY_INCOMPLETE_ABSENT_FROM_LATER_METADATA")
        for invalid in (None,0,True,"2025-04-25T00:00:00Z"):
            with self.subTest(invalid=invalid):
                self.assertEqual(s.classify(historic(),current(invalid))["later_metadata_comparison"],
                                 "HOURLY_INCOMPLETE_LATER_ONBOARD_UNKNOWN")

    def test_invalid_history_identity_rejected(self):
        with self.assertRaises(ValueError):
            s.classify({"date":"2025-04-19","symbol":"","status":""},None)
        with self.assertRaises(ValueError):
            s.classify({"date":"2025-04-20","symbol":"AAAUSDT","status":"UNKNOWN"},None)

    def test_actual_5400_immutable_blobs_full_source_and_3_misses(self):
        result=s.run()
        self.assertEqual(result["original_exposed_symbol_date_attempts"],5400)
        self.assertEqual(result["stage37_hourly_complete"],3333)
        self.assertEqual(result["stage37_hourly_missing"],2067)
        self.assertEqual(result["stage93_full_1m_verified"],3283)
        self.assertEqual(result["stage93_full_source_censored"],2117)
        self.assertEqual(result["stage93_exposed_gross_2x"],51)
        self.assertEqual(result["stage93_exposed_D0_first_early5"],48)
        self.assertEqual(result["stage118_model"],"REJECTED_UNCHANGED")
        self.assertEqual(result["stage127_model"],"REJECTED_UNCHANGED")
        self.assertEqual(result["new_forward_validation_G1"],"NOT_SCORABLE")
        self.assertEqual(result["G4_real_net"],"UNKNOWN")
        self.assertEqual(result["monster_deployment"],"NO_GO")
        d=result["later_metadata_comparison_counts"]
        self.assertEqual(sum(d.values()),5400)
        self.assertEqual(len(result["original_source_complete_gross2x_not_early_cases"]),3)
        self.assertEqual({x["symbol"] for x in result["original_source_complete_gross2x_not_early_cases"]},
                         {"PENGUUSDT","CETUSUSDT","FUSDT"})
        self.assertEqual(len(result["later_listing_boundary_and_source_contradiction_cases"]),
                         d.get("HOURLY_INCOMPLETE_LATER_ONBOARD_INSIDE_WINDOW",0)+
                         d.get("HOURLY_COMPLETE_LATER_METADATA_ONBOARD_CONTRADICTION",0))


if __name__ == "__main__":
    unittest.main()
