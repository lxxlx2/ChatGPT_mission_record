"""D1 real SQLite loop: indexed activity must not be promoted into BUY."""
from __future__ import annotations
from pathlib import Path
import importlib.util
import json
import sqlite3
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/frank_d1_activity_ledger.py"
spec = importlib.util.spec_from_file_location("frank_d1_activity_ledger", SCRIPT)
d1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(d1)
NOW = 1792400000
MINT = "7VertkgF9KLhxxJXHX6uaWuoYZTP9LdGj2bWmVXVpump"
SIGS = [c * 88 for c in "23456789"]
SECRET = "UNTRUSTED_XSS_<script>alert('private')</script>"

def fixture(root):
    path = root / "forward.sqlite"
    with sqlite3.connect(path) as db:
        db.executescript("""
        CREATE TABLE signatures(wallet TEXT, signature TEXT, person_id TEXT,
                                block_time INTEGER, body TEXT);
        CREATE TABLE trades(wallet TEXT, signature TEXT, mint TEXT,
                            side TEXT, block_time INTEGER, body TEXT);
        """)
        classes = ["ACTIVE_TRADE", "PASSIVE_TRANSFER", "UNKNOWN_NEEDS_REVIEW",
                   "FAILED_TX", "ATA_CREATE", "ACTIVE_TRADE"]
        for i, cl in enumerate(classes):
            db.execute("INSERT INTO signatures VALUES(?,?,?,?,?)",
                       ("frank_wallet", SIGS[i], "frank", NOW-100-i,
                        json.dumps({"classification": cl, "error": SECRET})))
        db.execute("INSERT INTO trades VALUES(?,?,?,?,?,?)",
                   ("frank_wallet", SIGS[0], MINT, "BUY", NOW-100,
                    json.dumps({"secret": SECRET})))
        db.execute("INSERT INTO trades VALUES(?,?,?,?,?,?)",
                   ("another_account", SIGS[1], MINT, "BUY", NOW-101, "{}"))
        db.execute("INSERT INTO signatures VALUES(?,?,?,?,?)",
                   ("another_account", SIGS[1], "not_frank", NOW-101, "{}"))
        db.execute("INSERT INTO signatures VALUES(?,?,?,?,?)",
                   ("frank_wallet", SIGS[6], "frank", NOW-120000, '{"classification":"ACTIVE_TRADE"}'))
    return path

class TestFrankD1ActivityLedger(unittest.TestCase):
    def test_signed_activity_and_passive_do_not_become_buy(self):
        with tempfile.TemporaryDirectory() as folder:
            path = fixture(Path(folder))
            source = path.read_bytes()
            report = d1.activity(path, NOW, days=1)
            self.assertEqual(report["signatures"], 6)
            self.assertEqual(report["trade_legs"], 1)
            self.assertEqual(report["categories"]["ACTIVE_TRADE"], 2)
            self.assertEqual(report["categories"]["PASSIVE_TRANSFER"], 1)
            self.assertEqual(report["categories"]["UNKNOWN_NEEDS_REVIEW"], 1)
            self.assertEqual(report["flags"]["ACTIVE_WITHOUT_TRADE_LEG"], 1)
            self.assertEqual(report["flags"]["UNRESOLVED"], 1)
            self.assertEqual(report["rows"][1]["trades"], [])
            self.assertFalse(report["full_chain_verified"])
            self.assertEqual(path.read_bytes(), source)

    def test_actual_git_corrected_ata_gap_split(self):
        records = d1.dated_ata()
        self.assertEqual(len(records), 2)
        j7 = next(x for x in records if x["mint"].startswith("J7bh"))
        bpx = next(x for x in records if x["mint"].startswith("BPxx"))
        self.assertEqual(j7["values"], [2, 0, 2, 0, 0, 2])
        self.assertEqual(bpx["values"], [66, 63, 3, 1, 1, 1])

    def test_private_html_has_exact_trades_and_only_sanitized_source(self):
        with tempfile.TemporaryDirectory() as folder:
            report = d1.activity(fixture(Path(folder)), NOW)
            content = d1.render(report, d1.dated_ata())
            self.assertEqual(content.count('data-class="'), 6)
            self.assertIn("https://solscan.io/tx/", content)
            self.assertIn("https://solscan.io/token/", content)
            self.assertIn("ACTIVE_WITHOUT_TRADE_LEG", content)
            self.assertIn("被动转入", content)
            self.assertIn("不等于索引器故障", content)
            self.assertNotIn(SECRET, content)
            self.assertNotIn("another_account", content)
            self.assertNotIn("frank_wallet", content)
            out = d1.publish(content, Path(folder) / "Downloads")
            self.assertEqual(out.read_text("utf-8"), content)
            self.assertEqual(len(list((Path(folder) / "Downloads").glob("*.html"))), 1)

    def test_misclassified_trade_is_highlighted_not_suppressed(self):
        with tempfile.TemporaryDirectory() as folder:
            path = fixture(Path(folder))
            with sqlite3.connect(path) as db:
                db.execute("INSERT INTO trades VALUES(?,?,?,?,?,?)",
                           ("frank_wallet", SIGS[1], MINT, "SELL", NOW-101, "{}"))
            r = d1.activity(path, NOW)
            self.assertEqual(r["trade_legs"], 2)
            mismatch = [x for x in r["rows"] if x["status"] == "CLASS_TRADE_MISMATCH"]
            self.assertEqual(len(mismatch), 1)
            self.assertEqual(mismatch[0]["class"], "PASSIVE_TRANSFER")

    def test_untrusted_class_and_sqlite_source_fail_closed(self):
        with tempfile.TemporaryDirectory() as folder:
            path = fixture(Path(folder))
            with sqlite3.connect(path) as db:
                db.execute("UPDATE signatures SET body=? WHERE signature=?",
                           (json.dumps({"classification": SECRET}), SIGS[3]))
            r = d1.activity(path, NOW)
            self.assertEqual(r["categories"]["OTHER_OR_UNKNOWN"], 1)
            self.assertNotIn(SECRET, d1.render(r, d1.dated_ata()))
            with self.assertRaises(ValueError):
                d1.activity(path, NOW, days=30)
            with self.assertRaises(ValueError):
                d1.activity(Path(folder) / "missing.sqlite", NOW)

    def test_row_limit_never_silently_drops_activity(self):
        with tempfile.TemporaryDirectory() as folder:
            path = fixture(Path(folder))
            with self.assertRaisesRegex(ValueError, "NOT_TRUNCATED"):
                d1.activity(path, NOW, max_rows=3)
            with self.assertRaises(ValueError):
                d1.render({"full_chain_verified": True, "rows": []}, [])

if __name__ == "__main__":
    unittest.main()
