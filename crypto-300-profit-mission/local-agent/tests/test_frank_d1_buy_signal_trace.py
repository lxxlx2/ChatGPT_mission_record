"""D1 contract: two local BUYs, signed event→evaluation→signal→decision join."""
from __future__ import annotations

from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
import zipfile

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "frank_d1_buy_signal_trace.py"
spec = importlib.util.spec_from_file_location("frank_d1_buy_signal_trace", SCRIPT)
d1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(d1)
REFERENCE = d1._date_epoch("2026-10-19T08:56:26+00:00")
PRIVATE_MINT = "PRIVATE_RAW_MINT_ADDR_SHOULD_NEVER_APPEAR"
PRIVATE_SIG = "PRIVATE_ONCHAIN_SIGNATURE_SHOULD_NEVER_APPEAR"
OTHER_MINT = "SECOND_PRIVATE_RAW_MINT_ADDR"


def fixture(root: Path, *, decision=True, evaluation=True, signal=True):
    source = root / "forward.sqlite"
    control = root / "mission-control.sqlite"
    with sqlite3.connect(source) as db:
        db.executescript("""
            CREATE TABLE signatures(wallet TEXT,signature TEXT,person_id TEXT,
                block_time INTEGER,body TEXT);
            CREATE TABLE trades(wallet TEXT,signature TEXT,mint TEXT,episode_id TEXT,
                block_time INTEGER,side TEXT,body TEXT);
            CREATE TABLE v1_states(person_id TEXT,mint TEXT,body TEXT);
            CREATE TABLE v1_evaluations(person_id TEXT,mint TEXT,episode_id TEXT,
                at INTEGER,signature TEXT,body TEXT);
            CREATE TABLE signals(person_id TEXT,mint TEXT,episode_id TEXT,
                signal_type TEXT,created_at TEXT,body TEXT);
        """)
        transactions = [
            ("s1", PRIVATE_MINT, "episode-one", REFERENCE - 400, "BUY", "ACTIVE_TRADE"),
            ("s2", OTHER_MINT, "episode-two", REFERENCE - 250, "REENTRY", "ACTIVE_TRADE"),
            ("other-sell", PRIVATE_MINT, "episode-one", REFERENCE - 200, "SELL", "ACTIVE_TRADE"),
            ("passive", PRIVATE_MINT, "episode-one", REFERENCE - 180, None, "PASSIVE_TRANSFER"),
            ("oldbuy", OTHER_MINT, "older-episode", REFERENCE - 100000, "BUY", "ACTIVE_TRADE"),
        ]
        for signature, mint, episode, at, side, cls in transactions:
            db.execute("INSERT INTO signatures VALUES(?,?,?,?,?)",
                       ("wallet1", signature, "frank", at,
                        json.dumps({"classification": cls, "private": PRIVATE_SIG})))
            if side:
                db.execute("INSERT INTO trades VALUES(?,?,?,?,?,?,?)",
                           ("wallet1", signature, mint, episode, at, side,
                            json.dumps({"quote_asset": PRIVATE_SIG})))
        # First BUY has evaluated non-triggering stage; second creates a real stage.
        if evaluation:
            db.execute("INSERT INTO v1_evaluations VALUES(?,?,?,?,?,?)",
                       ("frank", PRIVATE_MINT, "episode-one",
                        REFERENCE - 400, "s1", '{"stages":[]}'))
            db.execute("INSERT INTO v1_evaluations VALUES(?,?,?,?,?,?)",
                       ("frank", OTHER_MINT, "episode-two",
                        REFERENCE - 250, "s2", '{"stages":[{"stage":"ACCUMULATION"}]}'))
        db.execute("INSERT INTO v1_states VALUES(?,?,?)",
                   ("frank", PRIVATE_MINT, json.dumps({
                       "episode_id": "episode-one", "events": [
                           {"signature": "s1", "direction": "BUY"}]})))
        db.execute("INSERT INTO v1_states VALUES(?,?,?)",
                   ("frank", OTHER_MINT, json.dumps({
                       "episode_id": "episode-two", "events": [
                           {"signature": "s2", "direction": "BUY"}]})))
        if signal:
            db.execute("INSERT INTO signals VALUES(?,?,?,?,?,?)",
                       ("frank", OTHER_MINT, "episode-two", "FRANK_ACCUMULATION_SIGNAL",
                        str(REFERENCE - 250), json.dumps({
                            "signal_id": "signal-on-s2", "triggering_signature": "s2"})))
            # An old unrelated signal for the first mint must not be falsely joined.
            db.execute("INSERT INTO signals VALUES(?,?,?,?,?,?)",
                       ("frank", PRIVATE_MINT, "episode-one", "FRANK_MULTIPLE_SIGNAL",
                        str(REFERENCE - 99999), json.dumps({
                            "signal_id": "prior-signal", "triggering_signature": "unrelated"})))
    with sqlite3.connect(control) as db:
        if decision:
            db.execute("CREATE TABLE candidate_latest(person_id TEXT,mint TEXT,"
                       "episode_id TEXT,decision TEXT,body TEXT)")
            db.execute("INSERT INTO candidate_latest VALUES(?,?,?,?,?)",
                       ("frank", OTHER_MINT, "episode-two", "WAIT",
                        '{"source_signal_id":"signal-on-s2"}'))
            db.execute("INSERT INTO candidate_latest VALUES(?,?,?,?,?)",
                       ("frank", PRIVATE_MINT, "episode-one", "NO_BUY",
                        '{"source_signal_id":"prior-signal"}'))
    return source, control


class D1BuyCausalTests(unittest.TestCase):
    def test_exact_event_join_and_no_old_signal_false_positive(self):
        with tempfile.TemporaryDirectory() as temp:
            source, control = fixture(Path(temp))
            result = d1.trace(source, control, REFERENCE)
            self.assertEqual(result["recognized_buy_rows_24h"], 2)
            self.assertEqual(result["source_signatures_24h"], 4)
            self.assertFalse(result["chain_completeness_verified"])
            first, second = result["events"]
            self.assertEqual(first["causal_stage"], "TRADE_EVALUATED_NO_TRIGGERED_SIGNAL")
            self.assertEqual(first["same_episode_decision_presence"],
                             "SAME_EPISODE_PRESENT")
            self.assertEqual(first["exact_triggered_signal_to_decision"],
                             "SAME_EPISODE_NOT_EXACT_SIGNAL")
            self.assertEqual(second["causal_stage"], "TRADE_TRIGGERED_SIGNAL_FOUND")
            self.assertEqual(second["triggered_signal_types"],
                             ["FRANK_ACCUMULATION_SIGNAL"])
            self.assertEqual(second["exact_triggered_signal_to_decision"],
                             "SAME_EVENT_SIGNAL_DECISION_WAIT")
            self.assertEqual(result["recognized_buys_vs_prior_mac_sample"],
                             "DIFF_OR_VERSION_WINDOW_UNVERIFIED")
            full = json.dumps(result)
            for forbidden in (PRIVATE_MINT, OTHER_MINT, PRIVATE_SIG, "signal-on-s2",
                              "prior-signal", "forward.sqlite", "mission-control.sqlite"):
                self.assertNotIn(forbidden, full)
            path = Path(temp) / "data.zip"
            d1._zip(result, path)
            with zipfile.ZipFile(path) as z:
                self.assertEqual(z.namelist(), ["frank-d1-buy-causal-summary.json"])
                self.assertIsNone(z.testzip())
                self.assertNotIn(PRIVATE_MINT, z.read(z.namelist()[0]).decode())
            with self.assertRaises(FileExistsError):
                d1._zip(result, path)

    def test_model_present_without_eval_not_promoted_to_buy(self):
        with tempfile.TemporaryDirectory() as temp:
            source, control = fixture(Path(temp), evaluation=False, signal=False)
            result = d1.trace(source, control, REFERENCE)
            self.assertEqual(result["recognized_buy_rows_24h"], 2)
            self.assertTrue(all(x["causal_stage"] == "CURRENT_MODEL_EVENT_WITHOUT_EVALUATION"
                                for x in result["events"]))
            self.assertEqual(result["events"][0]["exact_triggered_signal_to_decision"],
                             "SAME_EPISODE_NOT_EXACT_SIGNAL")

    def test_control_db_missing_is_missing_not_no_decision(self):
        with tempfile.TemporaryDirectory() as temp:
            source, control = fixture(Path(temp))
            control.unlink()
            result = d1.trace(source, control, REFERENCE)
            self.assertEqual(result["control_source"], "CONTROL_CANDIDATE_LATEST_UNAVAILABLE")
            self.assertTrue(all(x["exact_triggered_signal_to_decision"] == "NOT_QUERIED"
                                for x in result["events"]))

    def test_read_only_sqlite_does_not_mutate_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            source, control = fixture(Path(temp))
            original = (source.read_bytes(), control.read_bytes())
            for _ in range(2):
                d1.trace(source, control, REFERENCE)
            self.assertEqual(original, (source.read_bytes(), control.read_bytes()))

    def test_schema_absence_fails_closed_not_zero(self):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp) / "forward.sqlite"
            with sqlite3.connect(p) as db:
                db.execute("CREATE TABLE trades(id INT)")
            with self.assertRaisesRegex(RuntimeError, "SOURCE_SCHEMA_UNAVAILABLE"):
                d1.trace(p, Path(temp) / "nothing.sqlite", REFERENCE)

    def test_zero_source_buy_is_zero_local_only(self):
        with tempfile.TemporaryDirectory() as temp:
            source, control = fixture(Path(temp))
            result = d1.trace(source, control, REFERENCE - 200_000)
            self.assertEqual(result["recognized_buy_rows_24h"], 0)
            self.assertFalse(result["chain_completeness_verified"])


if __name__ == "__main__":
    unittest.main()
