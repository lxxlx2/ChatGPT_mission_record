import copy
import unittest
from datetime import datetime, timezone
from pathlib import Path
import json

import monster_v4_stage131_dynamic_listing_g1_population_bridge as st


class Stage131Test(unittest.TestCase):
    def test_real_immutable_stage130_and_all_31_source_rows(self):
        out=st.audit()
        self.assertEqual(out["stage130_all_original_31_case_count"],31)
        self.assertEqual(out["stage130_original_daily_sha_zip_receipts"],147)
        self.assertEqual(out["stage130_original_minute_bars"],159675)
        self.assertEqual(out["stage130_distinct_first_momentum_research_triggers"],19)
        self.assertEqual(out["stage130_gross_2x_posthoc_from_first_open"],2)
        self.assertEqual(out["stage130_momentum_early5_gross2x_exposed_only"],2)
        self.assertEqual(out["stage130_later_exchange_underlyingType_labels_NOT_ASOF_CRYPTO_PROOF"],
                         {"COIN":20,"EQUITY":7,"HK_EQUITY":4})
        self.assertEqual(out["original_Stage116_first_forward_capture_20261014_0600"],
                         "SOURCE_FAILED_NO_BACKFILL")
        self.assertEqual(out["G1_new_independent_OOS"],"NOT_SCORABLE")
        rows=out["all_retrospective_31_new_listing_population_rows"]
        self.assertEqual(len(rows),31)
        self.assertEqual(len({(x["window_anchor"],x["symbol_exact"]) for x in rows}),31)
        self.assertTrue(all(x["issuer_identity_asof"]=="UNVERIFIED" for x in rows))
        self.assertTrue(all(x["eligible_to_claim_G1_crypto_success"] is False for x in rows))
        self.assertEqual({x["symbol_exact"] for x in rows if x["research_momentum_early5_vs_gross_2x_posthoc"] is True},{"VINEUSDT","APRUSDT"})
        self.assertTrue(all(x["first_minute_close_theoretical_observable_utc"]>x["first_observed_1m_open_utc"] for x in rows))

    def test_immutable_stage130_digest_is_actually_enforced(self):
        item=st.SOURCE
        blob=item.read_bytes()
        self.assertEqual(st.git_blob(blob),st.SOURCE_BLOB_SHA)
        self.assertNotEqual(st.git_blob(blob+b" "),st.SOURCE_BLOB_SHA)

    def test_future_join_preexisting_and_new_listing_no_double_count(self):
        window="2026-10-28T06:00:00Z"
        out=st.reconcile_population(window,
                  [{"symbol":"OLDUSDT","source_status":"PUBLISHER_COMPLETE"},
                   {"symbol":"一币USDT","source_status":"CENSORED_SOURCE_MISSING"}],
                  [{"symbol":"NEWUSDT","first_observed_minute_utc":"2026-10-29T11:30:00Z",
                    "source_status":"OFFICIAL_PUBLISHER_1M_ONLY"}])
        self.assertEqual(out["raw_symbol_attempts"],3)
        self.assertEqual(out["preexisting_raw_attempts"],2)
        self.assertEqual(out["new_listing_raw_attempts"],1)
        self.assertEqual(len(out["raw_population_rows"]),3)
        self.assertEqual(out["G0"],"PARTIAL_UNTIL_INDEPENDENT_PIT_PROOF")
        self.assertTrue(all(x["asof_trading_eligibility_verified"] is False for x in out["raw_population_rows"]))
        self.assertTrue(all(x["missing_future_source_is_negative"] is False for x in out["raw_population_rows"]))
        with self.assertRaisesRegex(ValueError,"DOUBLE_COUNT"):
            st.reconcile_population(window,[{"symbol":"NEWUSDT"}],
                          [{"symbol":"NEWUSDT","first_observed_minute_utc":"2026-10-29T11:30:00Z"}])

    def test_new_listing_cannot_be_backdated_or_forced_inside_window(self):
        window="2026-10-28T06:00:00Z"
        for when in ["2026-10-28T05:59:00Z","2026-11-04T06:00:00Z","2026-11-04T10:00:00Z"]:
            with self.subTest(when=when):
                with self.assertRaisesRegex(ValueError,"OUTSIDE"):
                    st.reconcile_population(window,[],
                                           [{"symbol":"NEWUSDT","first_observed_minute_utc":when}])
        r=st.reconcile_population(window,[],[{"symbol":"NEWUSDT","first_observed_minute_utc":"2026-10-28T06:00:00Z"}])
        self.assertEqual(r["new_listing_raw_attempts"],1)

    def test_corrupt_rows_and_duplicated_unicode_rejected(self):
        window="2026-11-11T06:00:00Z"
        with self.assertRaisesRegex(ValueError,"SYMBOL_INVALID"):
            st.reconcile_population(window,[{"symbol":"DO/NOTUSDT"}],[])
        with self.assertRaisesRegex(ValueError,"DOUBLE_COUNT"):
            st.reconcile_population(window,[{"symbol":"妖币USDT"},{"symbol":"妖币USDT"}],[])
        with self.assertRaisesRegex(ValueError,"MUST_NOT_CARRY"):
            st.reconcile_population(window,[{"symbol":"ABCUSDT","first_observed_minute_utc":"2026-11-11T06:01:00Z"}],[])

    def test_hist_future_label_cannot_rewrite_earlier_research_trigger(self):
        s=st.decode_source()
        baseline=st.stage129.run()
        mapping={(r["date"],r["symbol"]):r for r in baseline["all_source_cohort_rows"]}
        rows=st.check_historical(s,mapping)[0]
        x=next(r for r in rows if r["symbol_exact"]=="VINEUSDT")
        first=x["first_frozen_momentum_research_signal_utc"]
        modified=copy.deepcopy(s)
        vine=next(r for r in modified["rows"] if r["symbol"]=="VINEUSDT")
        vine["first_gross2x_high_1m_utc"]="2025-01-25T04:54:00Z"
        # Future evaluation label moved one minute; recorded as-of trigger must remain identical.
        new=st.check_historical(modified,mapping)[0]
        new_vine=next(r for r in new if r["symbol_exact"]=="VINEUSDT")
        self.assertEqual(new_vine["first_frozen_momentum_research_signal_utc"],first)
        self.assertTrue(new_vine["research_momentum_early5_vs_gross_2x_posthoc"])

    def test_old_window_not_replaced_by_newly_manual_snapshot(self):
        r=st.audit()
        self.assertTrue(r["original_Stage116_three_window_G1_cannot_pass_without_first_window"])
        self.assertEqual(r["original_Stage93_fixed_week_2x_events_UNCHANGED"],51)
        self.assertEqual(r["G4_actual_net"],"UNKNOWN")
        self.assertEqual(r["Monster_deployment"],"NO_GO")


if __name__=="__main__":
    unittest.main()
