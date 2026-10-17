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
            "budget_usdt": 30})
        self.assertEqual(d2["checked"], 1)
        record = self.report(BASE + 600_000)["opportunities"][0]
        self.assertEqual(record["signal"], "SETUP_RESEARCH_ONLY")
        self.assertEqual(record["d2_status"], "CHECKED")
        self.assertTrue(record["d2_research_liquidity_gate"])
        self.assertEqual(record["d2_assumed_budget_usdt"], 30)
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


if __name__ == "__main__":
    unittest.main()
