"""Hermetic read-only export test: 40 events, 3904 metadata, no Mac needed."""
import csv
import gzip
import hashlib
import importlib.util
import json
import tempfile
import unittest
import zipfile
from datetime import datetime, timezone
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/monster_v4_export_event_packet.py"
spec = importlib.util.spec_from_file_location("monster_v4_packet", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class TestResearchEvidencePacket(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.fm2 = self.home / "crypto-monitor-fm2-evidence-20260930/monster"
        self.fm3 = self.home / "crypto-monitor-fm3-evidence-20261001/monster"
        self.fm2.mkdir(parents=True)
        self.fm3.mkdir(parents=True)
        for name, root in (
            ("train-instrument-events.json", self.fm3),
            ("validation-instrument-events.json", self.fm3),
            ("ground-truth-events-v1.json", self.fm2),
        ):
            (root / name).write_text("[]", encoding="utf-8")
        self.anchor = datetime(2022, 1, 1, tzinfo=timezone.utc)
        self.anchor_ms = int(self.anchor.timestamp() * 1000)
        with (self.home / "monster-history-all-events.csv").open(
            "w", newline="", encoding="utf-8"
        ) as f:
            w = csv.DictWriter(f, fieldnames=["period", "venue", "symbol", "anchor_utc"])
            w.writeheader()
            for _ in range(3904):
                w.writerow({"period": "TRAIN_2021_2023", "venue": "spot",
                            "symbol": "TESTUSDT", "anchor_utc": self.anchor.isoformat()})
        with (self.home / "monster-history-5x-plus.csv").open(
            "w", newline="", encoding="utf-8"
        ) as f:
            w = csv.DictWriter(f, fieldnames=["period", "venue", "symbol", "anchor_utc"])
            w.writeheader()
            for i in range(40):
                w.writerow({"period": "EXPOSED_2025_2026" if i == 39 else "TRAIN_2021_2023",
                            "venue": "spot", "symbol": "TESTUSDT",
                            "anchor_utc": self.anchor.isoformat()})
        bars = [
            [self.anchor_ms + i * 3600000, 1, 2, 1, 1.5, 10, 100, 20]
            for i in range(-730, 178)
        ]
        self.bar_source = self.fm3 / "bars/spot/TESTUSDT.json.gz"
        self.bar_source.parent.mkdir(parents=True)
        with gzip.open(self.bar_source, "wt", encoding="utf-8") as f:
            json.dump(bars, f)
        exposed = self.fm2 / "bars/spot/TESTUSDT.json.gz"
        exposed.parent.mkdir(parents=True)
        exposed.write_bytes(self.bar_source.read_bytes())
        (self.fm3 / "expanded-coverage.json").write_text(json.dumps([
            {"venue": "spot", "symbol": "TESTUSDT",
             "bars_path": str(self.bar_source)}
        ]))

    def test_packet_contains_both_csv_all_gt_and_all_40_hourly_windows(self):
        result = module.export(self.home, self.home / "packet.zip")
        self.assertEqual(result["EVENT_ROWS"], 3904)
        self.assertEqual(result["POSITIVE_ROWS"], 40)
        self.assertEqual(result["HISTORICAL_WINDOWS"], 40)
        self.assertEqual(result["HISTORICAL_1H_BARS"], 40 * 889)
        self.assertEqual(result["MISSING"], [])
        blob = result["PACKET"]
        self.assertEqual(hashlib.sha256(Path(blob).read_bytes()).hexdigest(), result["SHA256"])
        with zipfile.ZipFile(blob) as z:
            self.assertEqual(z.testzip(), None)
            manifest = json.loads(z.read("packet-manifest.json"))
            self.assertEqual(len(manifest["windows"]), 40)
            self.assertEqual(len(manifest["source_file_hashes"]), 5)
            first = json.loads(z.read(manifest["windows"][0]["entry"]))
            self.assertEqual(len(first["bars"]), 889)
            self.assertEqual(first["bars"][0][0], self.anchor_ms - 720 * 3600000)
            self.assertEqual(first["bars"][-1][0], self.anchor_ms + 168 * 3600000)

    def test_missing_source_is_visible_and_not_silently_claimed_complete(self):
        (self.fm3 / "bars/spot/TESTUSDT.json.gz").unlink()
        out = module.export(self.home, self.home / "missing.zip")
        self.assertEqual(out["HISTORICAL_WINDOWS"], 1)
        self.assertEqual(len(out["MISSING"]), 39)
        with zipfile.ZipFile(out["PACKET"]) as z:
            self.assertEqual(len(json.loads(z.read("packet-manifest.json"))["missing"]), 39)

    def test_wrong_event_count_aborts_before_packaging(self):
        with (self.home / "monster-history-5x-plus.csv").open(
            "a", encoding="utf-8"
        ) as f:
            f.write("TRAIN_2021_2023,spot,ADDEDUSDT,2022-01-01T00:00:00+00:00\n")
        with self.assertRaisesRegex(ValueError, "UNEXPECTED_EVENT_COUNTS"):
            module.export(self.home, self.home / "should-not-exist.zip")
        self.assertFalse((self.home / "should-not-exist.zip").exists())


if __name__ == "__main__":
    unittest.main()
