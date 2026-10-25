"""Spot511 real69 quote source age join: no backfilled order-book proof."""
import hashlib
import tempfile
from datetime import datetime,timezone,timedelta
from pathlib import Path
import unittest

import monster_v4_spot511_d2_signal_receipt_coverage as m
import monster_v4_stage163_spot_t0_quote_friction as s163


class FrozenReal69D2ReceiptTests(unittest.TestCase):
    def snapshot(self,at_ms):
        iso=datetime.fromtimestamp(at_ms/1000,timezone.utc).isoformat().replace("+00:00","Z")
        return {
            "source_zip_sha256":s163.ZIP_SHA256,
            "schema":s163.SCHEMA,
            "t0_active_spot_usdt_denominator":511,
            "t0_causal_quote_at_t0_proven":False,
            "eligible_for_t0_asof_executable_execution_or_signal_backtest":False,
            "quote_bundle_not_available_until_client_receipt_utc":iso,
            "rows":[{"symbol":f"COIN{n}USDT","venue":"BINANCE_SPOT"} for n in range(511)]
        }

    def rows(self,ms):
        rows=[]
        for i in range(69):
            status=("RESEARCH_SETUP" if i<47 else
                    "NO_SETUP" if i<65 else "SOURCE_UNSCORED")
            rows.append({
                "watch_event_id":f"{i:064x}",
                "first_seen_ms":ms+180_000*i,
                "symbol":f"COIN{i}USDT",
                "status":status,
                "research_observed_ms":ms+180_000*(i+1) if i<47 else None,
            })
        return rows

    def test_before_receipt_fails_closed_never_uses_future_book(self):
        signal=1_792_320_000_000
        report=m.analyze(self.rows(signal),self.snapshot(signal+60_000))
        self.assertEqual(report["watch_receipt_status_counts"].get(
            "ARCHIVED_QUOTE_NOT_YET_RECEIVED_AT_EVENT_CLOCK"),1)
        self.assertEqual(report["G4"],"UNKNOWN")
        self.assertEqual(report["G4_signal_time_bidask_proven"],0)
        self.assertEqual(report["nominal_amount"],"UNSPECIFIED")
        self.assertTrue(all(e["executable_net_return"] is None for e in report["events"]))
        self.assertEqual(len(report["events"]),69)

    def test_stale_quote_after_signal_is_never_claimed_executable(self):
        signal=1_792_320_000_000
        report=m.analyze(self.rows(signal),self.snapshot(signal-1_000_000))
        self.assertEqual(report["watch_receipt_status_counts"],
                         {"ARCHIVED_QUOTE_STALE_AT_EVENT_CLOCK":69})
        self.assertEqual(report["d1_receipt_status_counts"],{
            "ARCHIVED_QUOTE_STALE_AT_EVENT_CLOCK":47,
            "NO_D1_RESEARCH_SETUP":22})
        self.assertTrue(all(not e["can_confirm_g4"] for e in report["events"]))
        self.assertTrue(report["retroactive_archive_is_not_historical_live_receive_time"])

    def test_recent_client_receipt_still_no_book_event_time_or_fill(self):
        signal=1_792_320_000_000
        report=m.analyze(self.rows(signal),self.snapshot(signal-30_000))
        self.assertEqual(report["watch_receipt_status_counts"][
            "ARCHIVED_NON_ATOMIC_BBO_WITHOUT_EXCHANGE_QUOTE_EVENT_TIME"],1)
        self.assertEqual(report["G4"],"UNKNOWN")
        self.assertFalse(report["events"][0]["historical_quote_at_signal"])

    def test_signal_receipt_clock_boundary_exact_then_stale(self):
        signal=1_792_320_000_000
        self.assertEqual(m.classify_receipt_time(signal,signal-180_000),
            "ARCHIVED_NON_ATOMIC_BBO_WITHOUT_EXCHANGE_QUOTE_EVENT_TIME")
        self.assertEqual(m.classify_receipt_time(signal,signal-180_001),
            "ARCHIVED_QUOTE_STALE_AT_EVENT_CLOCK")
        self.assertEqual(m.classify_receipt_time(signal,signal+1),
            "ARCHIVED_QUOTE_NOT_YET_RECEIVED_AT_EVENT_CLOCK")

    def test_real_analyze_microsecond_after_signal_is_future_receipt(self):
        signal=1_792_320_000_000
        snapshot=self.snapshot(signal)
        for offset_us,expected in (
                (0,"ARCHIVED_NON_ATOMIC_BBO_WITHOUT_EXCHANGE_QUOTE_EVENT_TIME"),
                (1,"ARCHIVED_QUOTE_NOT_YET_RECEIVED_AT_EVENT_CLOCK"),
                (-1,"ARCHIVED_NON_ATOMIC_BBO_WITHOUT_EXCHANGE_QUOTE_EVENT_TIME")):
            dt=(datetime.fromtimestamp(signal/1000,timezone.utc)
                +timedelta(microseconds=offset_us))
            snapshot["quote_bundle_not_available_until_client_receipt_utc"]=(
                dt.isoformat(timespec="microseconds").replace("+00:00","Z"))
            report=m.analyze(self.rows(signal),snapshot)
            self.assertEqual(report["events"][0]["watch_quote_receipt_status"],
                             expected)
            self.assertEqual(report["archived_receipt_availability_us_exact"],
                             signal*1000+offset_us)
            self.assertEqual(report["events"][0][
                "archived_quote_available_at_client_receipt_ms"],
                signal+(1 if offset_us>0 else 0))
            self.assertEqual(report["events"][0][
                "watch_vs_archived_receipt_age_us_exact"],-offset_us)
            self.assertFalse(report["events"][0]["can_confirm_g4"])

    def test_real_analyze_threshold_exact_and_one_microsecond_both_sides(self):
        signal=1_792_320_000_000
        for age_us,expected in (
                (180_000_000,"ARCHIVED_NON_ATOMIC_BBO_WITHOUT_EXCHANGE_QUOTE_EVENT_TIME"),
                (180_000_001,"ARCHIVED_QUOTE_STALE_AT_EVENT_CLOCK"),
                (179_999_999,"ARCHIVED_NON_ATOMIC_BBO_WITHOUT_EXCHANGE_QUOTE_EVENT_TIME")):
            dt=(datetime.fromtimestamp(signal/1000,timezone.utc)
                -timedelta(microseconds=age_us))
            snapshot=self.snapshot(signal)
            snapshot["quote_bundle_not_available_until_client_receipt_utc"]=(
                dt.isoformat(timespec="microseconds").replace("+00:00","Z"))
            report=m.analyze(self.rows(signal),snapshot)
            self.assertEqual(report["events"][0]["watch_quote_receipt_status"],
                             expected)
            self.assertEqual(report["events"][0][
                "watch_vs_archived_receipt_age_us_exact"],age_us)
            self.assertEqual(report["G4"],"UNKNOWN")

    def test_d1_microsecond_after_setup_is_not_yet_received(self):
        signal=1_792_320_000_000
        # D1 first setup clock is WATCH + one 3-minute tick.
        first_setup_ms=signal+180_000
        snapshot=self.snapshot(first_setup_ms)
        dt=(datetime.fromtimestamp(first_setup_ms/1000,timezone.utc)
            +timedelta(microseconds=1))
        snapshot["quote_bundle_not_available_until_client_receipt_utc"]=(
            dt.isoformat(timespec="microseconds").replace("+00:00","Z"))
        report=m.analyze(self.rows(signal),snapshot)
        self.assertEqual(report["events"][0]["d1_quote_receipt_status"],
            "ARCHIVED_QUOTE_NOT_YET_RECEIVED_AT_EVENT_CLOCK")
        self.assertEqual(report["events"][0]["watch_quote_receipt_status"],
            "ARCHIVED_QUOTE_NOT_YET_RECEIVED_AT_EVENT_CLOCK")
        self.assertEqual(report["G4_signal_time_bidask_proven"],0)

    def test_microsecond_parser_exact_including_stage163_saved_receipt(self):
        exact="2026-10-17T22:04:46.929464Z"
        timestamp=s163.parse_utc(exact)
        expected=((timestamp-datetime(1970,1,1,tzinfo=timezone.utc)).days*86400
                  +(timestamp-datetime(1970,1,1,tzinfo=timezone.utc)).seconds
                  )*1_000_000+timestamp.microsecond
        self.assertEqual(m._micros(exact),expected)
        self.assertEqual(m._micros("2026-10-18T10:40:00.000001Z"),
                         1_792_320_000_000*1000+1)
        self.assertEqual(m.classify_receipt_time_us(
            1_792_320_000_000,m._micros("2026-10-18T10:40:00.000001Z")),
            "ARCHIVED_QUOTE_NOT_YET_RECEIVED_AT_EVENT_CLOCK")

    def test_missing_symbol_is_not_silently_omitted(self):
        signal=1_792_320_000_000
        rows=self.rows(signal)
        rows[-1]["symbol"]="NONEXISTENTUSDT"
        report=m.analyze(rows,self.snapshot(signal))
        self.assertEqual(report["watch_receipt_status_counts"][
            "ARCHIVED_QUOTE_SYMBOL_NOT_IN_FROZEN_T0_ROSTER"],1)
        self.assertEqual(report["original_watch_total"],69)

    def test_archive_population_and_identity_tamper_rejected(self):
        signal=1_792_320_000_000
        snapshot=self.snapshot(signal)
        snapshot["rows"][1]["symbol"]=snapshot["rows"][0]["symbol"]
        with self.assertRaisesRegex(ValueError,"FROZEN_SPOT_QUOTE_POPULATION_INVALID"):
            m.analyze(self.rows(signal),snapshot)
        snapshot=self.snapshot(signal)
        snapshot["source_zip_sha256"]="f"*64
        with self.assertRaisesRegex(ValueError,"PROVENANCE_DRIFT"):
            m.analyze(self.rows(signal),snapshot)

    def test_no_report_forgery_via_modified_real69_json(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/"real69.json"
            p.write_text('{"frozen_original_watch_events":69}')
            with self.assertRaisesRegex(ValueError,"D2_PINNED_REAL69_BYTES_CHANGED"):
                m.load_locked_real69(p)
            p.unlink()
            p.symlink_to(Path(t)/"other.json")
            with self.assertRaisesRegex(ValueError,"D2_LOCKED_REAL69_FILE_REQUIRED"):
                m.load_locked_real69(p)

    def test_invalid_clocks_fail_instead_of_reinterpreting_age(self):
        for arguments in ((0,1),(-1,1),(1000,1001),(True,1000),
                          (1000,1000,False)):
            if len(arguments)==2 and arguments[0]==1000:
                continue
            with self.assertRaises(ValueError):
                if len(arguments)==2:
                    m.classify_receipt_time(*arguments)
                else:
                    m.classify_receipt_time(arguments[0],arguments[1],
                                           max_age_ms=arguments[2])
        for bad in (-1,3.5,True):
            with self.assertRaisesRegex(ValueError,"INVALID_RECEIPT"):
                m.classify_receipt_time(1000,1000,max_age_ms=bad)

    def test_no_user_amount_or_future_exit_claim_under_any_class(self):
        signal=1_792_320_000_000
        for diff in (-200_000, -1, 0, 1, 200_000):
            report=m.analyze(self.rows(signal),self.snapshot(signal+diff))
            self.assertEqual(report["G6"],"NO_GO")
            self.assertTrue(report["NO_TRADES"])
            self.assertTrue(report["NO_SCHEDULE"])
            self.assertFalse(any(x["can_confirm_g4"] for x in report["events"]))


if __name__=="__main__":
    unittest.main()
