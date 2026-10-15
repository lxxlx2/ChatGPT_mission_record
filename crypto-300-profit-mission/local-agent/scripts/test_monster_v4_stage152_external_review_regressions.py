#!/usr/bin/env python3
"""Independent Claude REQUEST_CHANGES deterministic P1/P2 regression cases."""
import copy
import hashlib
import os
from pathlib import Path
import unittest
from decimal import Decimal

import monster_v4_stage151_post_d1_pullback_reclaim as core
import monster_v4_stage151_aggregate_post_d1_research as aggregate

D=Decimal
T=1_800_000_000_000


def bars(closes, start=T):
    rows=[]
    for i,v in enumerate(closes):
        c=D(str(v)); o=D("100")
        rows.append((start+i*core.MIN,o,max(o,c)+D(1),min(o,c)-D(1),
                     c,D(100000),100))
    return rows


def fake_305():
    shards=[]; original=[]; index=0
    pin=hashlib.sha256(Path(core.__file__).read_bytes()).hexdigest()
    trigger=os.environ.get("GITHUB_SHA","LOCAL_UNVERIFIED")
    for date in aggregate.DATES:
        for shard in range(4):
            rows=[]
            n=13 if index<17*13 else 12  # overridden below to exact 305
            idx=len(shards)
            n=13 if idx<17 else 12
            for _ in range(n):
                index+=1
                identity={"date":date,"symbol":f"SYNTH{index}USDT",
                          "D0_FIRST_UTC":"2025-01-01T00:00:00Z",
                          "D1_FIRST_UTC":"2025-01-01T01:00:00Z",
                          "D1_PATH":"DIRECT_AT_FIRST_D0",
                          "identity":"CRYPTO_IDENTITY_UNVERIFIED"}
                original.append(identity)
                rows.append({**identity,
                    "preregistered_decision":{"state":"NO_PULLBACK_WITHIN_120M"},
                    "old_D1_early5_gt2_evaluation_only":False,
                    "baseline_Stage88_D1_direct_24h_gross_price_only_pct":"-5",
                    "entry_and_exit_fixed_horizon_price_only":{},
                    "real_fill":"NOT_OBSERVED","G4":"UNKNOWN"})
            shards.append({"schema":core.SCHEMA,"date":date,"shard":shard,
                           "original_D1_total_expected":305,
                           "original_D0_total_reference_untouched":519,
                           "D0_only_reference_untouched":214,
                           "historical_exposed_NOT_OOS":True,
                           "G4":"UNKNOWN","G6":"NO_GO",
                           "trigger_commit_sha":trigger,
                           "stage151_core_sha256":pin,"rows":rows})
    assert index==305
    return shards,original


def synthetic_confirmed(symbol, gross, direct):
    def path(pct):
        pct=D(pct)
        return {"status":"COMPLETE_UNFILLED_PRICE_PROXY",
                "gross_pct":str(pct),
                "illustrative_20bps_each_side_pct":str(pct-D("0.4")),
                "adverse_LOW_proxy_pct_not_stop_fill":"-8",
                "entry_minute_quote_volume_USDT":"50000",
                "entry_minute_trade_count":50,
                "exit_minute_quote_volume_USDT":"20000",
                "exit_minute_trade_count":20}
    return {"date":"2025-01-30","symbol":symbol,
            "preregistered_decision":{"state":"PULLBACK_RECLAIM_CONFIRMED_PRICE_ONLY"},
            "old_D1_early5_gt2_evaluation_only":True,
            "baseline_Stage88_D1_direct_24h_gross_price_only_pct":str(direct),
            "entry_and_exit_fixed_horizon_price_only":{
                "360":path(gross),"1440":path(gross)},
            "delayed_entry_open_same_holding_horizon_price_only":{
                "1":{"360":path(D(gross)-1),"1440":path(D(gross)-1)},
                "3":{"360":path(D(gross)-3),"1440":path(D(gross)-3)}}}


class Stage152ExternalReview(unittest.TestCase):
    def test_completed_decision_not_affected_by_unseen_bad_future_bar(self):
        a=bars([100,96,98]+[100]*117)
        first=core.decision(a,D(100),T)
        a[110]=None
        self.assertEqual(core.decision(a,D(100),T),first)

    def test_no_signal_all120_must_be_source_complete(self):
        a=bars([100]*120)
        a[119]=None
        with self.assertRaisesRegex(ValueError,"OBSERVABLE"):
            core.decision(a,D(100),T)

    def test_entry_exit_activity_and_delay_source(self):
        source=bars([100]*1441)
        source[360]=(source[360][0],D(110),D(111),D(109),D(110),D(90000),150)
        data={r[0]:r for r in source}
        result=core.price_path(data,T,D(100),360)
        self.assertEqual(result["entry_minute_trade_count"],100)
        self.assertEqual(result["exit_minute_quote_volume_USDT"],"90000")
        self.assertEqual(result["real_bid_ask_fill_net"],"UNKNOWN")

    def test_missing_exit_fails_not_censored(self):
        source=bars([100]*361)
        lookup={r[0]:r for r in source[:-1]}
        with self.assertRaisesRegex(ValueError,"OBSERVABLE"):
            core.price_path(lookup,T,D(100),360)

    def test_revenue_distributions_outliers_and_matched_cohort(self):
        rows=[synthetic_confirmed("ONEUSDT",100,-20),
              synthetic_confirmed("TWOUSDT",-10,10),
              synthetic_confirmed("THREEUSDT",-20,0)]
        result=aggregate.groups(rows)
        p=result["confirmed_1440m_complete_unfilled_price_proxy"]
        self.assertEqual(D(p["full_gross_distribution"]["mean_pct"]),
                         D(70)/3)
        paired=result["paired_24h_pct_point_difference_DIFFERENT_exit_clocks"]
        self.assertEqual(D(paired["mean_pct"]),D(80)/3)
        top=result["top_winner_concentration_and_leave_top_k_out"]["1"]
        self.assertEqual(top["removed_winners"][0]["symbol"],"ONEUSDT")
        self.assertEqual(D(top["remaining_distribution"]["mean_pct"]),D(-15))
        self.assertEqual(result["original_D1_early5_2x_EVALUATION_ONLY"][
            "retained_among_model_confirmations"],3)
        tiers=result["market_1m_turnover_sensitivity_NOT_execution"]["1440"]
        self.assertEqual(tiers["10000"]["distribution_on_observed_market_activity_only"]["n"],3)
        self.assertEqual(tiers["100000"]["distribution_on_observed_market_activity_only"]["n"],0)
        self.assertEqual(result["entry_delay_price_only_sensitivity_NOT_execution"]["1440"]["3"][
            "price_only_distribution"]["n"],3)

    def test_6h_24h_liquidity_and_delay_do_not_overwrite(self):
        event=synthetic_confirmed("DIVERGEUSDT",D("10"),D("-5"))
        source=event["entry_and_exit_fixed_horizon_price_only"]
        source["360"]["exit_minute_quote_volume_USDT"]="1"
        source["1440"]["exit_minute_quote_volume_USDT"]="20000"
        source["360"]["gross_pct"]="-7"
        source["1440"]["gross_pct"]="10"
        delays=event["delayed_entry_open_same_holding_horizon_price_only"]
        delays["1"]["360"]["gross_pct"]="-50"
        delays["1"]["1440"]["gross_pct"]="9"
        result=aggregate.groups([event])
        tiers=result["market_1m_turnover_sensitivity_NOT_execution"]
        one="distribution_on_observed_market_activity_only"
        self.assertEqual(set(tiers),{"360","1440"})
        self.assertEqual(tiers["360"]["10000"][one]["n"],0)
        self.assertEqual(tiers["1440"]["10000"][one]["n"],1)
        self.assertEqual(tiers["360"]["0"][one]["median_pct"],"-7")
        self.assertEqual(tiers["1440"]["0"][one]["median_pct"],"10")
        latencies=result["entry_delay_price_only_sensitivity_NOT_execution"]
        self.assertEqual(set(latencies),{"360","1440"})
        self.assertEqual(
            latencies["360"]["1"]["price_only_distribution"]["mean_pct"],"-50")
        self.assertEqual(
            latencies["1440"]["1"]["price_only_distribution"]["mean_pct"],"9")
        self.assertEqual(result[
            "confirmed_360m_complete_unfilled_price_proxy"]["n"],1)
        self.assertEqual(result[
            "confirmed_1440m_complete_unfilled_price_proxy"]["n"],1)

    def test_6h_unsupported_cannot_hide_24h_complete(self):
        event=synthetic_confirmed("UNSUPPORTEDUSDT",D("5"),D("-5"))
        event["entry_and_exit_fixed_horizon_price_only"]["360"]={
            "status":"EXIT_NO_TRADES_PRICE_PROXY_UNSUPPORTED"}
        result=aggregate.groups([event])
        tier=result["market_1m_turnover_sensitivity_NOT_execution"]
        self.assertEqual(
            tier["360"]["0"]["distribution_on_observed_market_activity_only"]["n"],0)
        self.assertEqual(
            tier["1440"]["0"]["distribution_on_observed_market_activity_only"]["n"],1)
        self.assertEqual(result[
            "confirmed_360m_complete_unfilled_price_proxy"][
            "confirmed_but_unsupported_by_status"],
            {"EXIT_NO_TRADES_PRICE_PROXY_UNSUPPORTED":1})
        self.assertEqual(result[
            "confirmed_1440m_complete_unfilled_price_proxy"][
            "confirmed_but_unsupported_by_status"],{})
        self.assertEqual(
            result["entry_delay_price_only_sensitivity_NOT_execution"]["360"]["1"][
                "price_only_distribution"]["n"],0)
        self.assertEqual(
            result["entry_delay_price_only_sensitivity_NOT_execution"]["1440"]["1"][
                "price_only_distribution"]["n"],1)

    def test_all305_exact_shards_and_checksum_provenance(self):
        shards,original=fake_305()
        result=aggregate.aggregate(shards,original)
        self.assertEqual(result["original_305_D1_all_scored"],305)
        self.assertEqual(result["frozen_parameters"]["P0_DROP_FACTOR"],str(core.DROP))
        self.assertEqual(result["frozen_parameters"]["FIXED_HORIZONS_M"],list(core.HORIZONS))
        q=copy.deepcopy(shards)
        q[0]["stage151_core_sha256"]="0"*64
        with self.assertRaisesRegex(ValueError,"SHARD_SOURCE_SHA"):
            aggregate.aggregate(q,original)
        q=copy.deepcopy(shards)
        q[0]["trigger_commit_sha"]="WRONG_TRIGGER"
        with self.assertRaisesRegex(ValueError,"SHARD_SOURCE_SHA"):
            aggregate.aggregate(q,original)

    def test_missing_or_replaced_original_event_rejected(self):
        shards,original=fake_305()
        with self.assertRaisesRegex(ValueError,"24_ORIGINAL_DATE_SHARDS"):
            aggregate.aggregate(shards[:-1],original)
        q=copy.deepcopy(shards)
        q[0]["rows"].pop()
        with self.assertRaisesRegex(ValueError,"ORIGINAL305_DENOMINATOR"):
            aggregate.aggregate(q,original)
        q=copy.deepcopy(shards)
        q[0]["rows"][0]["D1_PATH"]="REIGNITION_AFTER_D0"
        with self.assertRaisesRegex(ValueError,"SAME_D0_D1"):
            aggregate.aggregate(q,original)


if __name__=="__main__":
    unittest.main()
