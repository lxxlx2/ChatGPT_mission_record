"""End-to-end offline query test against the real Monster shadow SQLite schema."""
import importlib.util
import tempfile
import unittest
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
        self.assertEqual(invalid["queue_status"], "EVALUATED")
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


if __name__ == "__main__":
    unittest.main()
