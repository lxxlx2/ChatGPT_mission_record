"""November full-market offline proxy research engine tests. Not actual OOS."""
from pathlib import Path
import tempfile
import unittest

import monster_v4_adr005_forward_spot_full_market_replay as scan
import monster_v4_adr005_forward_spot_score_admission as admission
import monster_v4_adr005_forward_spot_t0_gate as t0


class SyntheticFrozenTape:
    """Time-consistent deterministic testing source; not Binance data."""
    def __init__(self,symbol,start_ms):
        self.symbol=symbol
        self.start_ms=start_ms
        self.probed=[]
    def original_d0_context(self,tick):
        if tick < self.start_ms or (tick-self.start_ms)%scan.TICK_MS:
            raise ValueError("FAKE_TAPE_POLL_GRID")
        # All listed symbols remain in the source denominator at every tick.
        last=("110" if self.symbol=="AAAUSDT" and tick>=self.start_ms+scan.TICK_MS
              else "100")
        return {"symbol":self.symbol,"lastPrice":last,"quoteVolume":"200000"}
    def six_closed_5m(self,tick):
        end=tick//scan.FIVE_MS*scan.FIVE_MS
        return [
            [end-6*scan.FIVE_MS+i*scan.FIVE_MS,
             "100","100","100","100","1",
             end-5*scan.FIVE_MS+i*scan.FIVE_MS-1,"100"]
            for i in range(6)
        ]


class FrozenSourceProxyCohortTests(unittest.TestCase):
    START="2026-11-02T00:00:00Z"

    def setUp(self):
        self.start_ms=t0.frozen_window(self.START)//1000
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)

    def report(self,symbols=("AAAUSDT","BTCUSDT")):
        return {
            "schema":admission.SCHEMA,
            "window_start_utc":self.START,
            "original_market_census_venue":"BINANCE_SPOT",
            "replay_engine_executed":False,
            "metrics_from_future_labels_computed":False,
            "original_t0_symbols_total":len(symbols),
            "btc_benchmark_research_d1_source_ready":True,
            "symbols":[{
                "symbol":s,
                "baseline_24h_source_verified":True,
                "candidate_own_observation_7d_source_verified":True,
                "technically_eligible_for_offline_rbtc_d1_source_replay":s!="BTCUSDT",
            } for s in symbols],
        }

    def factory(self,symbol):
        return SyntheticFrozenTape(symbol,self.start_ms)

    def test_full_3360_ticks_all_original_cohort_and_durable_original_watch_rbtc_queue(self):
        doc=scan.replay_with_source_tapes(self.report(),self.factory,self.root)
        self.assertEqual(doc["original_spot_t0_symbol_population"],2)
        self.assertEqual(doc["utc_3minute_full_cohort_polls"],3360)
        self.assertEqual(doc["source_proxy_context_rows"],2*3360)
        self.assertTrue(doc["all_t0_market_symbols_seen_every_poll"])
        self.assertEqual(doc["proxy_nonbtc_original_d0_watch_count"],1)
        self.assertEqual(doc["proxy_original_d0_watch_count"],1)
        self.assertEqual(len(doc["proxy_original_d0_watch_rows"]),1)
        self.assertEqual(doc["proxy_original_d0_watch_rows"][0]["symbol"],"AAAUSDT")
        self.assertEqual(doc["isolated_proxy_research_D1_episode_count"],1)
        self.assertEqual(sum(doc["isolated_proxy_research_D1_status_counts"].values()),1)
        self.assertEqual(len(doc["isolated_proxy_research_D1_rows"]),1)
        self.assertFalse(doc["proxy_watch_events_are_real_historical_signals"])
        self.assertFalse(doc["proxy_setup_events_are_real_historical_signals"])
        self.assertFalse(doc["true_original_pit_event_stream_proven"])
        self.assertFalse(doc["actual_live_24h_ticker_at_original_tick_proven"])
        self.assertFalse(doc["can_score_preregistered_forward_G1_G2_G3"])
        self.assertEqual(doc["G1"],"NOT_SCORABLE")
        self.assertEqual(doc["G2"],"UNKNOWN")
        self.assertEqual(doc["G3"],"NOT_SCORABLE")
        self.assertEqual(doc["G6"],"NO_GO")
        self.assertTrue(doc["NO_TRADES"])
        self.assertTrue(doc["NO_AUTOMATIONS"])

    def test_missing_btc_from_original_population_fails_before_any_spool(self):
        with self.assertRaisesRegex(ValueError,"BTC_BENCHMARK_SOURCE_REQUIRED"):
            scan.verified_cohort(self.report(("AAAUSDT",)))
        self.assertEqual(list(self.root.iterdir()),[])

    def test_missing_btc_own_observation_fails_before_creating_db(self):
        r=self.report()
        r["symbols"][-1]["candidate_own_observation_7d_source_verified"]=False
        with self.assertRaisesRegex(ValueError,"ALL_T0_SYMBOLS_OBSERVATION_SOURCE_REQUIRED"):
            scan.replay_with_source_tapes(r,self.factory,self.root)
        self.assertEqual(list(self.root.iterdir()),[])

    def test_nonbtc_not_research_d1_ready_fails_with_no_fake_original_negative(self):
        r=self.report()
        r["symbols"][0]["technically_eligible_for_offline_rbtc_d1_source_replay"]=False
        with self.assertRaisesRegex(ValueError,"CANDIDATE_RBTC_D1_SOURCE_REQUIRED"):
            scan.verified_cohort(r)

    def test_duplicate_or_truncated_population_fails(self):
        r=self.report()
        r["symbols"].append(dict(r["symbols"][0]))
        r["original_t0_symbols_total"]=3
        with self.assertRaisesRegex(ValueError,"INVALID_OR_DUPLICATE_SYMBOL"):
            scan.verified_cohort(r)
        r=self.report()
        r["original_t0_symbols_total"]=3
        with self.assertRaisesRegex(ValueError,"T0_COHORT_INCOMPLETE"):
            scan.verified_cohort(r)

    def test_spool_symbol_identity_mismatch_refuses_fake_rows(self):
        def bad_factory(symbol):
            return SyntheticFrozenTape("OTHERUSDT",self.start_ms)
        with self.assertRaisesRegex(ValueError,"TAPE_IDENTITY_OR_START_DRIFT"):
            scan.replay_with_source_tapes(self.report(),bad_factory,self.root)

    def test_existing_database_file_is_not_overwritten(self):
        (self.root/"original-proxy-d0.sqlite").write_text("private")
        with self.assertRaisesRegex(ValueError,"REFUSE_PREEXISTING_DATABASE"):
            scan.replay_with_source_tapes(self.report(),self.factory,self.root)
        self.assertEqual((self.root/"original-proxy-d0.sqlite").read_text(),"private")

    def test_does_not_accept_october_t0_as_november_full_market_source(self):
        real=(Path(__file__).resolve().parents[2]/"monster/evidence/"
              "monster_stage163_spot_original_http_t0_actual")
        with self.assertRaisesRegex(ValueError,"PRESTART_15MIN"):
            scan.run(self.START,"2026-11-02T00:00:00Z",
                     real/"source_raw_http.zip",real/"source_receipts.json",self.root)
        self.assertEqual(list(self.root.iterdir()),[])


if __name__=="__main__":
    unittest.main()
