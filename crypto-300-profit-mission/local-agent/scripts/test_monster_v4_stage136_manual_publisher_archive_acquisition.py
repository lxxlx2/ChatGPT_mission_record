import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

import monster_v4_stage130_first_listed_minute_sha_replay as publisher
import monster_v4_stage135_full_market_publisher_minute_coverage as stage135
import monster_v4_stage136_manual_publisher_archive_acquisition as subject
from test_monster_v4_stage133_manual_actual_t0_forward_proof import fixture
import monster_v4_stage133_manual_actual_t0_forward_proof as stage133


def t0():
    return stage133.validate_three_http_records(*fixture())


def request():
    return {"schema": subject.REQUEST_SCHEMA,
            "explicit_manual_request": True,
            "allow_official_historical_publisher_fetch": True}


def after_source_ready(packet):
    return stage133.stage105.WINDOW_MS + packet["new_forward_start_epoch_ms"] + subject.PUBLISHER_MARGIN_MS + 1


def original_pair(symbol, day):
    ms = int(__import__("datetime").datetime.fromisoformat(
        day + "T00:00:00+00:00").timestamp() * 1000)
    row = ",".join((str(ms), "1", "1.1", "0.9", "1", "100",
                    "100", "1000", "10", "10", "10", "0")) + "\n"
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(symbol + "-1m-" + day + ".csv", row)
    raw = out.getvalue()
    checksum = (hashlib.sha256(raw).hexdigest() + "  " +
                symbol + "-1m-" + day + ".zip\n").encode("ascii", errors="ignore")
    return raw, checksum


def fake_transport(symbol, day, count):
    zipped, checksum = original_pair(symbol, day)
    url = publisher.source_url(symbol, day)
    def get(uri, maximum):
        count.append(uri)
        return zipped if uri == url else checksum if uri == url + ".CHECKSUM" else b""
    return get


class Stage136Tests(unittest.TestCase):
    def test_population_full_market_and_unicode_safe_planned_urls(self):
        base, planned = subject.planned_files(t0())
        self.assertEqual(base["t0_active_usdt_perpetual_attempts"], 3)
        self.assertEqual(len(planned), 27)
        self.assertEqual(len({(x["symbol"], x["day"]) for x in planned}), 27)
        self.assertEqual(len({x["day"] for x in planned}), 9)
        self.assertTrue(any("%" in x["publisher_zip_url"] for x in planned
                            if x["symbol"] == "币安人生USDT"))
        self.assertEqual(base["G1"], "NOT_SCORABLE")

    def test_offline_plan_never_requests_network_or_writes_archive(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / "not_created"
            seen = []
            r = subject.acquire(t0(), root, get=lambda u, n: seen.append(u))
            self.assertEqual(seen, [])
            self.assertFalse(root.exists())
            self.assertEqual(r["mode"], "OFFLINE_PLAN")
            self.assertEqual(r["pending_manual_run"], 27)
            self.assertEqual(r["G1"], "NOT_SCORABLE")
            self.assertFalse(r["scheduled_automation_created"])

    def test_manual_fetch_requires_explicit_two_part_permission_and_future_end(self):
        for bad in (None, {}, {"schema": subject.REQUEST_SCHEMA},
                    {"schema": subject.REQUEST_SCHEMA, "explicit_manual_request": True},
                    {"schema": subject.REQUEST_SCHEMA, "explicit_manual_request": False,
                     "allow_official_historical_publisher_fetch": True}):
            with self.subTest(bad=bad), tempfile.TemporaryDirectory() as folder:
                seen = []
                with self.assertRaisesRegex(ValueError, "EXPLICIT_USER_MANUAL"):
                    subject.acquire(t0(), folder, fetch_manual=True,
                                    capture_request=bad, get=lambda u,n: seen.append(u))
                self.assertEqual(seen, [])
        with tempfile.TemporaryDirectory() as folder:
            seen = []
            with self.assertRaisesRegex(ValueError, "PUBLISHER_MARGIN"):
                subject.acquire(t0(), folder, fetch_manual=True,
                                capture_request=request(),
                                now_ms=t0()["new_forward_start_epoch_ms"] +
                                168 * 3600_000, get=lambda u,n: seen.append(u))
            self.assertEqual(seen, [])

    def test_authorized_original_publisher_two_receipt_fetch_and_resume(self):
        t = t0()
        with tempfile.TemporaryDirectory() as folder:
            base, planned = subject.planned_files(t)
            first = planned[0]
            seen = []
            fetch = fake_transport(first["symbol"], first["day"], seen)
            r = subject.acquire(t, folder, fetch_manual=True,
                                capture_request=request(), now_ms=after_source_ready(t),
                                max_fetch_files=1, get=fetch)
            self.assertEqual(seen, [first["publisher_zip_url"],
                                    first["publisher_zip_url"] + ".CHECKSUM"])
            self.assertEqual(r["newly_fetched_checksum_verified"], 1)
            self.assertEqual(r["pending_manual_run"], 26)
            self.assertEqual(r["unavailable_not_negative"], 0)
            self.assertIsNotNone(stage135.locally_verified_day(
                folder, first["symbol"], first["day"])[0])
            second_calls = []
            r2 = subject.acquire(t, folder, fetch_manual=True,
                                 capture_request=request(), now_ms=after_source_ready(t),
                                 max_fetch_files=1,
                                 get=lambda uri, limit: second_calls.append(uri) or
                                     (_ for _ in ()).throw(FileNotFoundError("404")))
            self.assertEqual(r2["reused_checksum_verified"], 1)
            self.assertEqual(r2["unavailable_not_negative"], 1)
            self.assertEqual(len(second_calls), 1)
            self.assertEqual(r2["newly_fetched_checksum_verified"], 0)

    def test_existing_corrupt_pair_fails_without_mutation_or_replacement(self):
        t = t0()
        with tempfile.TemporaryDirectory() as folder:
            _, planned = subject.planned_files(t)
            first = planned[0]
            loc = Path(folder) / first["symbol"]
            loc.mkdir()
            (loc / (first["day"]+".zip")).write_bytes(b"malformed zip")
            (loc / (first["day"]+".zip.CHECKSUM")).write_bytes(b"0"*64)
            seen = []
            with self.assertRaises((ValueError, zipfile.BadZipFile)):
                subject.acquire(t, folder, fetch_manual=True,
                                capture_request=request(), now_ms=after_source_ready(t),
                                get=lambda u, n: seen.append(u))
            self.assertEqual(seen, [])
            self.assertEqual((loc / (first["day"]+".zip")).read_bytes(), b"malformed zip")

    def test_publisher_checksum_mismatch_fails_without_committing(self):
        t = t0()
        with tempfile.TemporaryDirectory() as folder:
            _, planned = subject.planned_files(t)
            first = planned[0]
            zip_bytes, checksum = original_pair(first["symbol"], first["day"])
            url = first["publisher_zip_url"]
            def broken(u, n):
                return zip_bytes if u == url else b"0"*64
            with self.assertRaisesRegex(ValueError, "CHECKSUM_MISMATCH"):
                subject.acquire(t, folder, fetch_manual=True,
                                capture_request=request(), now_ms=after_source_ready(t),
                                max_fetch_files=1, get=broken)
            self.assertFalse((Path(folder) / first["symbol"] /
                              (first["day"]+".zip")).exists())

    def test_offline_404_is_censored_no_future_positive_or_negative_assumption(self):
        t = t0()
        with tempfile.TemporaryDirectory() as folder:
            def missing(uri, max_bytes):
                raise FileNotFoundError("publisher 404")
            r = subject.acquire(t, folder, fetch_manual=True,
                                capture_request=request(), now_ms=after_source_ready(t),
                                max_fetch_files=2, get=missing)
            self.assertEqual(r["unavailable_not_negative"], 2)
            self.assertEqual(r["pending_manual_run"], 25)
            self.assertEqual(r["G0"], "PARTIAL")
            self.assertEqual(r["G4"], "UNKNOWN")
            self.assertEqual(r["model_buy"], "NO_GO")

    def test_offline_cli_plan_and_fail_closed_live_flag(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            t0_file = root / "stage133.json"
            t0_file.write_text(json.dumps(t0(), ensure_ascii=False), encoding="utf-8")
            result = root / "plan.json"
            cmd = [sys.executable, str(Path(subject.__file__)),
                   "--t0", str(t0_file), "--archive-root", str(root/"archives"),
                   "--out", str(result)]
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=25)
            self.assertEqual(r.returncode, 0, r.stderr)
            out = json.loads(result.read_text(encoding="utf-8"))
            self.assertEqual(out["all_symbol_day_attempts"], 27)
            self.assertEqual(out["newly_fetched_checksum_verified"], 0)
            self.assertFalse((root/"archives").exists())
            denied = subprocess.run(cmd + ["--fetch-manual"], capture_output=True,
                                    text=True, timeout=25)
            self.assertNotEqual(denied.returncode, 0)
            self.assertIn("capture-request", denied.stderr)


if __name__ == "__main__":
    unittest.main()
