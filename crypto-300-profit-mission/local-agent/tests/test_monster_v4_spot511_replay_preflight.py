import copy
import json
from pathlib import Path
import tempfile
import subprocess
import sys
from datetime import date, datetime, timedelta, timezone
import unittest
from monster_v4_spot511_replay_preflight import preflight, DATES


def fixture(asof=datetime(2026, 10, 26, tzinfo=timezone.utc), verified_dates=(), verified_symbols=()):
    symbols = sorted([f"Q{i:03d}USDT" for i in range(509)] + ["BTCUSDT", "ETHUSDT"])
    rows = []
    counts = {}
    for sym in symbols:
        for d in DATES:
            ended = datetime.combine(date.fromisoformat(d) + timedelta(days=1),
                                     datetime.min.time(), timezone.utc) <= asof
            if not ended:
                status = "UTC_DAY_NOT_YET_ENDED"
            elif d in verified_dates and sym in verified_symbols:
                status = "VERIFIED_FULL_DAY_1440"
            else:
                status = "SOURCE_NOT_SUPPLIED"
            detail = ({"closed_one_minute_rows":1440,
                       "original_publisher_checksum_valid":True,
                       "spot_timestamp_units":"MICROSECONDS", "zip_sha256":"a"*64}
                      if status == "VERIFIED_FULL_DAY_1440" else None)
            rows.append({"symbol":sym,"date_utc":d,"archive_status":status,
                         "source_detail":detail})
            counts[status] = counts.get(status, 0)+1
    return {"schema":"MONSTER_STAGE166_FROZEN_T0_511_OFFICIAL_SPOT_1M_INTAKE_V1",
            "t0_eligible_symbol_ids":symbols,"t0_spot_usdt_trading":511,
            "t0_spot_usdt_break_excluded":214,"source_t0_server_time_ms":1792274680094,
            "daily_source_attempts":4599,"utc_daily_source_dates":list(DATES),
            "window_start_utc":"2026-10-17T22:06:00Z",
            "window_end_exclusive_utc":"2026-10-24T22:06:00Z",
            "three_minute_ticks_total":3360,
            "full_7d_exchange_listing_changes_proven":False,
            "asof_source_check_utc":asof.isoformat().replace("+00:00","Z"),
            "all_511_nine_days_officially_verified":counts.get("VERIFIED_FULL_DAY_1440",0)==4599,
            "admission_counts":counts,"attempts":rows}


class PreflightTests(unittest.TestCase):
    def test_no_source_does_not_make_zero_events(self):
        r=preflight(fixture())
        self.assertEqual(r["total_symbol_ticks"],511*3360)
        self.assertEqual(r["source_ready_symbol_ticks"],0)
        self.assertEqual(r["source_blocked_symbol_ticks"],511*3360)
        self.assertEqual(r["actual_d0_watch_or_d1_setup_found"],"NOT_SCORABLE")
        self.assertEqual(r["G6"],"NO_GO")

    def test_early_asof_not_published_not_reclassified(self):
        r=preflight(fixture(asof=datetime(2026,10,18,16,tzinfo=timezone.utc)))
        self.assertEqual(r["source_ready_symbol_ticks"],0)
        self.assertGreater(r["blocked_reason_symbol_ticks"].get("UTC_DAY_NOT_YET_ENDED",0),0)

    def test_all_days_admitted_only_source_ready_not_model_pass(self):
        data=fixture(verified_dates=DATES,
                     verified_symbols=["BTCUSDT","ETHUSDT"] + [f"Q{i:03d}USDT" for i in range(509)])
        r=preflight(data)
        self.assertEqual(r["source_ready_symbol_ticks"],511*3360)
        self.assertFalse(r["market_signal_replay_performed"])
        self.assertEqual(r["G0"],"PARTIAL")
        self.assertEqual(r["G1"],"NOT_SCORABLE")

    def test_exact_half_open_candle_history_and_no_double_count(self):
        data=fixture(verified_dates=DATES[:2],verified_symbols=["BTCUSDT"])
        r=preflight(data)
        row=next(x for x in r["per_symbol"] if x["symbol"]=="BTCUSDT")
        # 22:06 through 23:57 are 38 ticks, plus 00:00 prior-day-only.
        self.assertEqual(row["source_ready_ticks"],39)
        self.assertEqual(r["source_ready_symbol_ticks"],39)
        self.assertEqual(sum(r["blocked_reason_symbol_ticks"].values()),511*3360-39)

    def test_unknown_sources_must_not_be_zero(self):
        x=fixture()
        x["attempts"][0]["archive_status"]="VERIFIED_FULL_DAY_1440"
        with self.assertRaisesRegex(ValueError,"UNBACKED_VERIFIED_MINUTE_FILE"):
            preflight(x)

    def test_duplicate_and_dropped_source_rows_denied(self):
        x=fixture()
        x["attempts"][1]=copy.deepcopy(x["attempts"][0])
        with self.assertRaisesRegex(ValueError,"DUPLICATE"):
            preflight(x)
        x=fixture()
        x["attempts"].pop()
        with self.assertRaisesRegex(ValueError,"SOURCE_ATTEMPTS_INCOMPLETE"):
            preflight(x)

    def test_future_claim_or_wrong_census_fails_closed(self):
        x=fixture(asof=datetime(2026,10,18,16,tzinfo=timezone.utc))
        x["attempts"][-1]["archive_status"]="SOURCE_NOT_SUPPLIED"
        with self.assertRaisesRegex(ValueError,"FUTURE_DRIFT"):
            preflight(x)
        x=fixture()
        x["full_7d_exchange_listing_changes_proven"]=True
        with self.assertRaisesRegex(ValueError,"COHORT_OR_WINDOW_DRIFT"):
            preflight(x)

    def test_cli_report_written_once_without_network(self):
        with tempfile.TemporaryDirectory() as root:
            source = Path(root) / "stage166.json"
            dest = Path(root) / "derived.json"
            source.write_text(json.dumps(fixture()), encoding="utf-8")
            script = Path(__file__).with_name("monster_v4_spot511_replay_preflight.py")
            cmd = [sys.executable, str(script), "--stage166-report", str(source),
                   "--out", str(dest)]
            done = subprocess.run(cmd, capture_output=True, text=True, check=True)
            self.assertIn("SPOT511_PREFLIGHT_ONLY", done.stdout)
            self.assertEqual(json.loads(dest.read_text())["source_ready_symbol_ticks"], 0)
            again = subprocess.run(cmd, capture_output=True, text=True)
            self.assertNotEqual(again.returncode, 0)
            self.assertIn("REFUSE_EXISTING_PREFLIGHT_OUTPUT", again.stderr)

    def test_aggregate_tamper_and_future_labels_ignored(self):
        x=fixture()
        x["admission_counts"]["SOURCE_NOT_SUPPLIED"]-=1
        with self.assertRaisesRegex(ValueError,"SOURCE_ADMISSION_AGGREGATE_DRIFT"):
            preflight(x)
        x=fixture()
        baseline=preflight(x)
        x["future_known_winners"]=["BTCUSDT"]
        newer=preflight(x)
        self.assertEqual(baseline["source_ready_symbol_ticks"],newer["source_ready_symbol_ticks"])
        self.assertEqual(baseline["per_symbol"],newer["per_symbol"])


if __name__=='__main__':
    unittest.main()
