"""End-to-end offline query test against the real Monster shadow SQLite schema."""
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


m = load("monster_v4_shadow")
viewer = load("monster_v4_opportunity_snapshot")
BASE = 1_800_000_000_000


def tick(symbol, price):
    return [{"symbol": symbol, "lastPrice": str(price), "quoteVolume": "200000"}]


def candles(now):
    start = (now // 300_000 - 6) * 300_000
    return [[start + i * 300_000, str(1 + i * .02), "2", ".5",
             str(1 + i * .02), "100", start + (i + 1) * 300_000 - 1,
             "200" if i >= 3 else "100", "20"] for i in range(6)]


class TestOperatorSnapshot(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "monster.sqlite"
        self.db = m.open_store(self.path)

    def tearDown(self):
        self.db.close()

    def watch(self, venue="spot", symbol="AAAUSDT"):
        m.observe_snapshot(self.db, venue, BASE, tick(symbol, "1"))
        m.observe_snapshot(self.db, venue, BASE + 180_000, tick(symbol, "1.08"))

    def report(self, t=BASE + 180_000):
        return viewer.read_snapshot(self.path, t)

    def test_live_age_watch_is_research_only(self):
        self.watch()
        r = self.report()
        self.assertEqual(r["sources"]["spot"]["state"], "RECENT_STORED_POLL")
        self.assertEqual(r["opportunities"][0]["signal"], "WATCH_RESEARCH_ONLY")
        self.assertTrue(r["opportunities"][0]["watch_evidence_present"])
        self.assertEqual(r["opportunities"][0]["watch_reason"], "SNAPSHOT_WINDOW_3MIN_PLUS_24H_LIQUIDITY_CONTEXT")
        self.assertEqual(r["opportunities"][0]["watch_observed_move_pct"], 8.0)
        self.assertEqual(r["opportunities"][0]["watch_quote24_at_trigger"], "200000")
        self.assertEqual(r["opportunities"][0]["recommendation"], "RESEARCH_REVIEW_ONLY_NO_BUY")
        self.assertEqual(r["production"], "NO_GO")
        self.assertEqual(r["opportunities"][0]["d2_status"], "NOT_CAPTURED")

    def test_setup_and_real_d2_record_do_not_become_buy(self):
        self.watch()
        m.observe_snapshot(self.db, "spot", BASE + 540_000, tick("AAAUSDT", "1.08"))
        done = m.process_queue(self.db, BASE + 600_000, lambda v, s, t: candles(t))
        self.assertEqual(done["completed"], 1)
        d2 = m.process_d2(self.db, BASE + 600_000, evaluate_spot=lambda symbol: {
            "symbol": symbol, "classification": "RESEARCH_LIQUIDITY_NOT_BUY",
            "research_liquidity_gate": True, "fee_source": "USER_UNCONFIRMED_SCENARIO",
            "budget_usdt": 30, "spread_bps": 8.5,
            "instant_roundtrip_cost_bps": 51.0, "depth_fully_filled": True})
        self.assertEqual(d2["checked"], 1)
        record = self.report(BASE + 600_000)["opportunities"][0]
        self.assertEqual(record["signal"], "SETUP_RESEARCH_ONLY")
        self.assertEqual(record["d2_status"], "CHECKED")
        self.assertEqual(record["d2_status_origin"], "D2_TERMINAL_EVENT_OBSERVED_BY_ASOF")
        self.assertTrue(record["d2_research_liquidity_gate_is_not_fill_proof"])
        self.assertTrue(record["d2_research_liquidity_gate"])
        self.assertEqual(record["d2_assumed_budget_usdt"], 30)
        self.assertEqual(record["d2_spread_bps"], 8.5)
        self.assertEqual(record["d2_instant_roundtrip_cost_bps"], 51.0)
        self.assertTrue(record["d2_depth_fully_filled"])
        self.assertEqual(record["g4_real_execution"], "UNKNOWN")

    def test_source_outage_suppresses_freshness(self):
        self.watch()
        m.mark_source_health(self.db, "spot", BASE + 180_000, "OFFLINE")
        r = self.report()
        self.assertEqual(r["sources"]["spot"]["state"], "STALE_OR_DEGRADED")
        self.assertEqual(r["opportunities"][0]["signal"], "SOURCE_STALE")

    def test_price_reversal_invalidates_watch(self):
        self.watch()
        m.observe_snapshot(self.db, "spot", BASE + 360_000, tick("AAAUSDT", ".8"))
        self.assertEqual(self.report(BASE + 360_000)["opportunities"][0]["signal"], "INVALIDATED")

    def test_evaluated_setup_invalidation_is_episode_specific_after_rewatch(self):
        self.watch()
        m.observe_snapshot(self.db, "spot", BASE + 540_000, tick("AAAUSDT", "1.08"))
        self.assertEqual(m.process_queue(self.db, BASE + 600_000,
            lambda v, s, t: candles(t))["completed"], 1)
        self.assertEqual(m.process_d2(self.db, BASE + 600_000,
            evaluate_spot=lambda sym: {"symbol": sym,
                "classification": "RESEARCH_LIQUIDITY_NOT_BUY",
                "research_liquidity_gate": True})["checked"], 1)
        original = self.report(BASE + 600_000)["opportunities"][0]
        self.assertEqual(original["signal"], "SETUP_RESEARCH_ONLY")
        self.assertEqual(original["queue_status"], "EVALUATED")

        m.observe_snapshot(self.db, "spot", BASE + 780_000, tick("AAAUSDT", ".8"))
        invalid = self.report(BASE + 780_000)["opportunities"][0]
        self.assertEqual(invalid["queue_status"], "INVALIDATED")
        self.assertEqual(invalid["queue_status_origin"], "ASOF_EVENTS_AND_DEADLINE_NOT_MUTABLE_QUEUE_STATE")
        self.assertEqual(invalid["signal"], "INVALIDATED")
        self.assertIsNotNone(invalid["invalidation_utc"])
        self.assertEqual(invalid["d2_status"], "CHECKED")

        m.observe_snapshot(self.db, "spot", BASE + 960_000, tick("AAAUSDT", ".96"))
        episodes = self.report(BASE + 960_000)["opportunities"]
        self.assertEqual(len(episodes), 2)
        self.assertEqual([r["signal"] for r in episodes],
            ["WATCH_RESEARCH_ONLY", "INVALIDATED"])
        self.assertIsNone(episodes[0]["invalidation_utc"])
        self.assertEqual(episodes[0]["d2_status"], "NOT_CAPTURED")
        self.assertEqual(episodes[1]["d2_status"], "CHECKED")

    def test_venue_poll_does_not_guarantee_symbol_quote_freshness(self):
        self.watch()
        m.observe_snapshot(self.db, "spot", BASE + 360_000, tick("BBBUSDT", "1"))
        first = self.report(BASE + 360_000)
        self.assertEqual(first["sources"]["spot"]["state"], "RECENT_STORED_POLL")
        item = first["opportunities"][0]
        self.assertEqual(item["signal"], "SYMBOL_QUOTE_NOT_SEEN_IN_LATEST_POLL")
        self.assertEqual(item["symbol_quote_age_seconds"], 180)
        self.assertFalse(item["symbol_seen_in_latest_poll"])

        m.observe_snapshot(self.db, "spot", BASE + 540_000, tick("BBBUSDT", "1"))
        m.observe_snapshot(self.db, "spot", BASE + 720_000, tick("BBBUSDT", "1"))
        second = self.report(BASE + 720_000)
        self.assertEqual(second["sources"]["spot"]["state"], "RECENT_STORED_POLL")
        aged = second["opportunities"][0]
        self.assertEqual(aged["signal"], "SYMBOL_QUOTE_STALE")
        self.assertEqual(aged["symbol_quote_state"], "STALE")
        self.assertEqual(aged["symbol_quote_age_seconds"], 540)
        self.assertFalse(aged["symbol_seen_in_latest_poll"])
        self.assertEqual(aged["recommendation"], "RESEARCH_REVIEW_ONLY_NO_BUY")

    def test_deadline_ends_research_opportunity_even_with_old_watch(self):
        self.watch()
        entry = self.report(BASE + 180_000 + 16 * 60_000)["opportunities"][0]
        self.assertEqual(entry["signal"], "EXPIRED")

    def test_futures_setup_never_becomes_spot_buy(self):
        self.watch("futures", "BBBUsDT".upper())
        m.observe_snapshot(self.db, "futures", BASE + 540_000, tick("BBBUSDT", "1.08"))
        self.assertEqual(m.process_queue(self.db, BASE + 600_000,
            lambda v, s, t: candles(t))["completed"], 1)
        self.assertEqual(m.process_d2(self.db, BASE + 600_000,
            evaluate_spot=lambda s: self.fail("not spot"))["skipped"], 1)
        record = self.report(BASE + 600_000)["opportunities"][0]
        self.assertEqual(record["signal"], "FUTURES_ONLY_SETUP")
        self.assertEqual(record["d2_status"], "FUTURES_ONLY")

    def test_reader_does_not_write_and_missing_db_fails(self):
        self.watch()
        before = self.db.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        for _ in range(3):
            self.report()
        after = self.db.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        self.assertEqual(before, after)
        with self.assertRaises(FileNotFoundError):
            viewer.read_snapshot(self.path.parent / "not_here.db", BASE)
        self.assertFalse((self.path.parent / "not_here.db").exists())

    def test_latest_episode_is_visible_without_hiding_history(self):
        self.watch()
        m.observe_snapshot(self.db, "spot", BASE + 360_000, tick("AAAUSDT", ".8"))
        m.observe_snapshot(self.db, "spot", BASE + 540_000, tick("AAAUSDT", ".96"))
        rows = self.report(BASE + 540_000)["opportunities"]
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["signal"], "WATCH_RESEARCH_ONLY")
        self.assertEqual(rows[1]["signal"], "INVALIDATED")


    def test_full_window_active_watch_survives_more_recent_invalidated_episode_limit(self):
        # Real Shadow producer creates 20 newer WATCH episodes that immediately
        # invalidate. A legitimate earlier WATCH must not be hidden by LIMIT 3.
        losers = ["LOSE" + str(i) + "USDT" for i in range(20)]
        all_symbols = ["KEEPUSDT"] + losers
        def batch(keep, lose):
            return [{"symbol": sym, "lastPrice": str(keep if sym == "KEEPUSDT" else lose),
                     "quoteVolume": "200000"} for sym in all_symbols]
        m.observe_snapshot(self.db, "spot", BASE, batch("1", "1"))
        m.observe_snapshot(self.db, "spot", BASE + 180_000, batch("1.08", "1"))
        m.observe_snapshot(self.db, "spot", BASE + 360_000, batch("1.08", "1.10"))
        m.observe_snapshot(self.db, "spot", BASE + 540_000, batch("1.08", "0.80"))

        result = viewer.read_snapshot(self.path, BASE + 540_000, limit=3)
        self.assertEqual(result["window_total"], 21)
        self.assertEqual(result["hidden_by_display_limit"], 18)
        self.assertEqual(result["displayed"], 3)
        self.assertEqual(result["counts_by_signal_full_window"],
                         {"INVALIDATED": 20, "WATCH_RESEARCH_ONLY": 1})
        self.assertEqual(result["opportunities"][0]["symbol"], "KEEPUSDT")
        self.assertEqual(result["opportunities"][0]["signal"], "WATCH_RESEARCH_ONLY")
        self.assertEqual(result["opportunities"][0]["recommendation"],
                         "RESEARCH_REVIEW_ONLY_NO_BUY")
        self.assertEqual(result["opportunities"][1]["signal"], "INVALIDATED")
        self.assertEqual(result["sources"]["spot"]["state"], "RECENT_STORED_POLL")
        self.assertEqual(result["trading"], "NO_GO")

    def test_older_spot_setup_ranks_before_newer_watch_without_becoming_buy(self):
        base = [dict(symbol="AAAUSDT", lastPrice="1", quoteVolume="200000"),
                dict(symbol="BBBUSDT", lastPrice="1", quoteVolume="200000")]
        m.observe_snapshot(self.db, "spot", BASE, base)
        m.observe_snapshot(self.db, "spot", BASE + 180_000, [
            dict(symbol="AAAUSDT", lastPrice="1.08", quoteVolume="200000"),
            dict(symbol="BBBUSDT", lastPrice="1", quoteVolume="200000")])
        m.observe_snapshot(self.db, "spot", BASE + 540_000, [
            dict(symbol="AAAUSDT", lastPrice="1.08", quoteVolume="200000"),
            dict(symbol="BBBUSDT", lastPrice="1.08", quoteVolume="200000")])
        outcome = m.process_queue(self.db, BASE + 600_000,
            lambda v, s, t: candles(t) if s == "AAAUSDT" else [])
        self.assertEqual(outcome["completed"], 1)
        self.assertEqual(outcome["deferred"], 1)
        result = viewer.read_snapshot(self.path, BASE + 600_000, limit=1)
        self.assertEqual(result["window_total"], 2)
        self.assertEqual(result["hidden_by_display_limit"], 1)
        self.assertEqual(result["counts_by_signal_full_window"],
                         {"SETUP_RESEARCH_ONLY": 1, "WATCH_RESEARCH_ONLY": 1})
        self.assertEqual(result["opportunities"][0]["symbol"], "AAAUSDT")
        self.assertEqual(result["opportunities"][0]["signal"], "SETUP_RESEARCH_ONLY")
        self.assertEqual(result["opportunities"][0]["d2_status"], "NOT_CAPTURED")
        self.assertEqual(result["opportunities"][0]["g4_real_execution"], "UNKNOWN")
        self.assertEqual(result["opportunities"][0]["recommendation"],
                         "RESEARCH_REVIEW_ONLY_NO_BUY")


    def test_asof_d2_and_source_outage_must_follow_observed_events(self):
        self.watch()
        m.observe_snapshot(self.db, "spot", BASE + 540_000, tick("AAAUSDT", "1.08"))
        self.assertEqual(m.process_queue(self.db, BASE + 600_000,
            lambda v, s, t: candles(t))["completed"], 1)
        after_setup = BASE + 650_000
        self.assertEqual(self.report(after_setup)["opportunities"][0]["d2_status"], "NOT_CAPTURED")

        m.mark_source_health(self.db, "spot", BASE + 720_000, "OFFLINE")
        self.assertEqual(m.process_d2(self.db, BASE + 720_000,
            evaluate_spot=lambda sym: {
                "symbol": sym, "classification": "RESEARCH_LIQUIDITY_NOT_BUY",
                "research_liquidity_gate": True, "fee_source": "USER_UNCONFIRMED_SCENARIO",
                "budget_usdt": 30, "spread_bps": 9.0})["checked"], 1)

        # This is queried *after* the database contains both future events:
        # neither should appear in an earlier as-of report.
        before = self.report(after_setup)
        prior = before["opportunities"][0]
        self.assertEqual(prior["signal"], "SETUP_RESEARCH_ONLY")
        self.assertEqual(prior["d2_status"], "NOT_CAPTURED")
        self.assertIsNone(prior["d2_observed_utc"])
        self.assertIsNone(prior["d2_spread_bps"])
        self.assertIsNone(prior["d2_assumed_budget_usdt"])
        self.assertEqual(before["sources"]["spot"]["state"], "RECENT_STORED_POLL")
        self.assertIsNone(before["sources"]["spot"]["degraded_since_utc"])
        self.assertEqual(before["sources"]["spot"]["health_origin"],
                         "PERSISTED_SOURCE_TRANSITION_EVENTS_ASOF")
        self.assertFalse(before["historical_asof_reconstruction"])

        during = self.report(BASE + 720_000)
        self.assertEqual(during["sources"]["spot"]["state"], "STALE_OR_DEGRADED")
        self.assertEqual(during["opportunities"][0]["signal"], "SOURCE_STALE")
        self.assertEqual(during["opportunities"][0]["d2_status"], "CHECKED")
        self.assertEqual(during["opportunities"][0]["d2_spread_bps"], 9.0)

        # The mutable source_state becomes healthy again, but the historical
        # 720s as-of must still report the outage seen before recovery.
        m.observe_snapshot(self.db, "spot", BASE + 900_000, tick("AAAUSDT", "1.08"))
        m.mark_source_health(self.db, "spot", BASE + 900_000)
        self.assertEqual(self.report(BASE + 720_000)["sources"]["spot"]["state"],
                         "STALE_OR_DEGRADED")
        self.assertEqual(self.report(BASE + 901_000)["sources"]["spot"]["state"],
                         "RECENT_STORED_POLL")

    def test_late_queue_current_status_cannot_retroactively_hide_watch(self):
        self.watch()
        cutoff = BASE + 180_000
        later = cutoff + 16 * 60_000
        self.assertEqual(m.process_queue(self.db, later,
            lambda v, s, t: self.fail("expired queue must not fetch"))["late"], 1)
        old = self.report(cutoff)["opportunities"][0]
        self.assertEqual(old["signal"], "WATCH_RESEARCH_ONLY")
        self.assertEqual(old["queue_status"], "UNRESOLVED_ASOF")
        self.assertEqual(self.report(later)["opportunities"][0]["signal"],
                         "MISSED_D1_DEADLINE")

    def test_full_window_safe_cap_fails_explicitly_without_hiding_watches(self):
        self.watch()
        m.observe_snapshot(self.db, "spot", BASE + 360_000, tick("AAAUSDT", ".8"))
        m.observe_snapshot(self.db, "spot", BASE + 540_000, tick("AAAUSDT", ".96"))
        with patch.object(viewer, "MAX_WINDOW_EPISODES", 1):
            with self.assertRaisesRegex(ValueError, "EXCEEDS_SAFE_EPISODE_LIMIT"):
                viewer.read_snapshot(self.path, BASE + 540_000, limit=1)
        normal = self.report(BASE + 540_000)
        self.assertEqual(normal["window_total"], 2)
        self.assertEqual(normal["hidden_by_display_limit"], 0)
        self.assertEqual(normal["trading"], "NO_GO")


    def test_d1_future_failure_is_not_leaked_into_same_past_asof_json_cli(self):
        # Reproduce the independent Codex P2 using the real writer, real WAL
        # SQLite schema and the real user-visible CLI (not a mocked queue).
        self.watch()
        asof = BASE + 180_000
        def cli():
            run = subprocess.run(
                [sys.executable, "-B", str(SCRIPTS / "monster_v4_opportunity_snapshot.py"),
                 "--db", str(self.path), "--asof-ms", str(asof), "--format", "json"],
                capture_output=True, text=True, check=True)
            self.assertEqual(run.returncode, 0)
            return json.loads(run.stdout)

        before = cli()
        self.assertEqual(before["window_total"], 1)
        self.assertEqual(before["opportunities"][0]["signal"], "WATCH_RESEARCH_ONLY")
        self.assertIsNone(before["opportunities"][0]["d1_last_error"])
        self.assertEqual(before["opportunities"][0]["d1_last_error_history_status"],
                         "UNRECONSTRUCTABLE_FROM_MUTABLE_QUEUE_FIELD")

        def future_d1_failure(venue, symbol, now_ms):
            raise OSError("FUTURE_D1_FETCH_FAILURE")

        failed_at = BASE + 600_000
        result = m.process_queue(self.db, failed_at, future_d1_failure)
        self.assertEqual(result["deferred"], 1)
        current_queue = self.db.execute(
            "SELECT last_error FROM candidate_queue WHERE symbol='AAAUSDT'").fetchone()
        self.assertIn("FUTURE_D1_FETCH_FAILURE", current_queue["last_error"])
        recorded = self.db.execute(
            "SELECT observed_ms FROM failures WHERE stage='D1'").fetchone()
        self.assertEqual(recorded["observed_ms"], failed_at)
        self.assertGreater(recorded["observed_ms"], asof)

        after = cli()
        self.assertEqual(before, after)
        self.assertIsNone(after["opportunities"][0]["d1_last_error"])
        self.assertNotIn("FUTURE_D1_FETCH_FAILURE", json.dumps(after))
        # Even when queried later, a mutable error cannot be assigned to
        # this episode at a precise historical time.
        later = viewer.read_snapshot(self.path, failed_at)
        self.assertIsNone(later["opportunities"][0]["d1_last_error"])
        self.assertEqual(later["opportunities"][0]["d1_last_error_history_status"],
                         "UNRECONSTRUCTABLE_FROM_MUTABLE_QUEUE_FIELD")
        self.assertEqual(later["trading"], "NO_GO")


    def test_true_partial_population_keeps_fresh_symbol_watch_but_blocks_execution(self):
        bad = [{"symbol": "币安人生USDT", "lastPrice": "1", "quoteVolume": "200000"},
               {"symbol": "牛来USDT", "lastPrice": "1", "quoteVolume": "200000"}]
        valid = [{"symbol": "AAAUSDT", "lastPrice": "1", "quoteVolume": "200000"}]
        first = m.observe_snapshot(self.db, "spot", BASE, valid + bad)
        second = m.observe_snapshot(self.db, "spot", BASE + 180_000,
                                    [{**valid[0], "lastPrice": "1.08"}] + bad)
        self.assertEqual((first["source_total"], first["valid"], first["invalid"]), (3, 1, 2))
        self.assertEqual(second["watch_new"], 1)
        result = self.report()
        source = result["sources"]["spot"]
        self.assertEqual(source["state"], "STALE_OR_DEGRADED")
        self.assertEqual(source["diagnostic_state"], "RECENT_PARTIAL_POPULATION")
        self.assertEqual(source["health_reason_codes"], ["POPULATION_PARTIALLY_SCANNED"])
        self.assertTrue(source["recent_poll_present"])
        self.assertFalse(source["full_population_scanned"])
        self.assertEqual(source["coverage_pct_of_recorded_population"], 33.3333)
        self.assertEqual(source["recorded_invalid_rows"], 2)
        item = result["opportunities"][0]
        self.assertEqual(item["signal"], "SOURCE_STALE")
        self.assertEqual(item["event_lifecycle_independent_of_source_health"],
                         "WATCH_RECORDED")
        self.assertTrue(item["symbol_has_fresh_record_despite_partial_venue"])
        self.assertEqual(item["symbol_quote_state"], "PRESENT_IN_LATEST_POLL")
        self.assertIn("SOURCE_POPULATION_PARTIAL", item["decision_blocker_codes"])
        self.assertIn("D2_BID_ASK_DEPTH_NOT_CAPTURED", item["decision_blocker_codes"])
        self.assertEqual(item["recommendation"], "RESEARCH_REVIEW_ONLY_NO_BUY")
        self.assertEqual(result["counts_by_decision_blocker_full_window"]
                         ["SOURCE_POPULATION_PARTIAL"], 1)

    def test_expired_partial_signal_is_expired_not_live_buy_or_hidden(self):
        bad = [{"symbol": "币安人生USDT", "lastPrice": "1", "quoteVolume": "200000"}]
        m.observe_snapshot(self.db, "spot", BASE, tick("AAAUSDT", "1") + bad)
        m.observe_snapshot(self.db, "spot", BASE + 180_000,
                           tick("AAAUSDT", "1.08") + bad)
        old = self.report(BASE + 180_000)
        self.assertEqual(old["opportunities"][0]
                         ["event_lifecycle_independent_of_source_health"], "WATCH_RECORDED")
        later = self.report(BASE + 180_000 + 16*60_000)
        item = later["opportunities"][0]
        self.assertEqual(item["event_lifecycle_independent_of_source_health"], "EXPIRED")
        self.assertEqual(item["signal"], "EXPIRED")
        self.assertIn("SIGNAL_EXPIRED", item["decision_blocker_codes"])
        self.assertIn("SOURCE_POPULATION_PARTIAL", item["decision_blocker_codes"])
        self.assertIn("D2_BID_ASK_DEPTH_NOT_CAPTURED", item["decision_blocker_codes"])
        self.assertEqual(item["recommendation"], "RESEARCH_REVIEW_ONLY_NO_BUY")
        self.assertEqual(later["sources"]["spot"]["diagnostic_state"], "POLL_STALE")
        self.assertEqual(later["sources"]["futures"]["diagnostic_state"], "NO_POLL")

    def test_fully_covered_recent_poll_keeps_original_research_only_watch(self):
        self.watch()
        result = self.report()
        source = result["sources"]["spot"]
        self.assertEqual(source["diagnostic_state"], "RECENT_FULL_POPULATION")
        self.assertEqual(source["health_reason_codes"], [])
        self.assertEqual(source["coverage_pct_of_recorded_population"], 100.0)
        item = result["opportunities"][0]
        self.assertEqual(item["signal"], "WATCH_RESEARCH_ONLY")
        self.assertEqual(item["event_lifecycle_independent_of_source_health"], "WATCH_RECORDED")
        self.assertFalse(item["symbol_has_fresh_record_despite_partial_venue"])
        self.assertNotIn("SOURCE_POPULATION_PARTIAL", item["decision_blocker_codes"])
        self.assertIn("D2_BID_ASK_DEPTH_NOT_CAPTURED", item["decision_blocker_codes"])
        self.assertEqual(item["recommendation"], "RESEARCH_REVIEW_ONLY_NO_BUY")



if __name__ == "__main__":
    unittest.main()
