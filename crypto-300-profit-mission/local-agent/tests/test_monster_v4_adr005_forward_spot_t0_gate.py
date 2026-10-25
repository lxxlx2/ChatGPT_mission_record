"""ADR005 future Spot T0: real archived-old rejection + synthetic boundary probes.

Fake packets only exercise validator; NEVER represent actual November captures.
"""
import copy
from datetime import datetime,timezone,timedelta
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

import monster_v4_adr005_forward_spot_t0_gate as gate
import monster_v4_stage163_spot_one_shot_raw_http_source as old


class FrozenNovemberSpotT0Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.zip=self.root/"original-http.zip"
        self.receipts=self.root/"receipts.json"
        self.start="2026-11-02T00:00:00Z"
        self.start_dt=datetime(2026,11,2,tzinfo=timezone.utc)

    def stamp(self,dt):
        return dt.isoformat(timespec="microseconds").replace("+00:00","Z")

    def fake_bundle(self,first_seconds_before=120,*,after_start=False):
        """Build a well-formed but purely synthetic Stage163-format six-HTTP ZIP."""
        base=self.start_dt-timedelta(seconds=first_seconds_before)
        if after_start:
            base=self.start_dt-timedelta(seconds=3)
        start_of={}
        end_of={}
        for index,(name,_) in enumerate(old.ENDPOINTS):
            start_of[name]=base+timedelta(seconds=2*index)
            end_of[name]=start_of[name]+timedelta(seconds=1)
        server_ms=lambda dt:int((dt-datetime(1970,1,1,tzinfo=timezone.utc)).total_seconds()*1000)
        entries=[
            {"symbol":f"COIN{i}USDT","baseAsset":f"COIN{i}",
             "quoteAsset":"USDT","status":"TRADING",
             "isSpotTradingAllowed":True}
            for i in range(1100)]
        entries.extend([
            {"symbol":"BREAK1USDT","quoteAsset":"USDT","status":"BREAK",
             "isSpotTradingAllowed":True},
            {"symbol":"OLD1USDT","quoteAsset":"USDT","status":"TRADING",
             "isSpotTradingAllowed":False},
            {"symbol":"OTHERBTC","quoteAsset":"BTC","status":"TRADING",
             "isSpotTradingAllowed":True}])
        bodies={
            "clock_before":{"serverTime":server_ms(start_of["clock_before"]+timedelta(milliseconds=500))},
            "exchangeInfo":{"serverTime":server_ms(start_of["exchangeInfo"]+timedelta(milliseconds=500)),"symbols":entries},
            "bookTicker":[{"symbol":x["symbol"],"bidPrice":"1","askPrice":"1.01",
                           "bidQty":"3","askQty":"3"} for x in entries],
            "ticker24":[{"symbol":x["symbol"],"quoteVolume":"100"} for x in entries],
            "depth_BTCUSDT_probe":{"lastUpdateId":1,"bids":[["1","2"]],"asks":[["1.01","2"]]},
            "clock_after":{"serverTime":server_ms(start_of["clock_after"]+timedelta(milliseconds=500))}
        }
        raw={name:json.dumps(payload,sort_keys=True).encode() for name,payload in bodies.items()}
        receipts={}
        for name,endpoint in old.ENDPOINTS:
            receipts[name]={
                "url":old.BASE+endpoint,"start_utc":self.stamp(start_of[name]),
                "end_utc":self.stamp(end_of[name]),
                "http_status":200,"body_byte_length":len(raw[name]),
                "body_sha256":hashlib.sha256(raw[name]).hexdigest(),
                "raw_http_bytes_available":True,
            }
        # All six are synthesised local test fixtures, never third-party capture.
        stats=old.validate_payload(
            raw, {name:{"end_utc":self.stamp(end_of[name])} for name in raw})
        summary={
            "schema":old.SCHEMA,"source_venue":"Binance Spot",
            "allowed_base":old.BASE,
            "source_is_true_http_response_body_bytes":True,
            "source_sha_receipts":receipts,"stats":stats,
        }
        internal=copy.deepcopy(summary)
        with zipfile.ZipFile(self.zip,"w",zipfile.ZIP_DEFLATED) as z:
            for name,payload in raw.items():
                z.writestr(name+".response.raw.json",payload)
            z.writestr("source_manifest.json",
                       json.dumps(internal,sort_keys=True).encode())
        summary["source_zip_sha256"]=hashlib.sha256(self.zip.read_bytes()).hexdigest()
        self.receipts.write_text(json.dumps(summary,sort_keys=True))
        return summary

    def test_three_frozen_windows_have_exact_source_free_readiness(self):
        for start in gate.WINDOWS:
            t=gate.parse_us(start)
            self.assertEqual(gate.preflight(start,"2026-10-25T16:00:00Z")[
                "source_ready_state"],"WAITING_FOR_PRESTART_SOURCE_WINDOW")
            at=datetime.fromisoformat(start.replace("Z","+00:00"))
            stamp=self.stamp
            self.assertEqual(gate.preflight(start,stamp(at-timedelta(minutes=1)))[
                "source_ready_state"],"T0_CAPTURE_WINDOW_NO_SOURCE_SUPPLIED")
            self.assertEqual(gate.preflight(start,stamp(at+timedelta(microseconds=1)))[
                "source_ready_state"],"T0_MISSING_CANNOT_RETROACTIVELY_PASS_PIT")
            self.assertEqual(t%1_000_000,0)

    def test_synthetic_valid_prestart_complete_exchangeinfo_admitted_only_as_unverified(self):
        self.fake_bundle()
        result=gate.preflight(self.start,self.stamp(self.start_dt),self.zip,self.receipts)
        self.assertEqual(result["source_ready_state"],
                         "T0_ARCHIVE_STRUCTURALLY_ADMITTED_ORIGIN_UNVERIFIED")
        self.assertEqual(result["t0_spot_usdt_candidates"],1100)
        self.assertEqual(result["all_market_symbol_attempts"],1103)
        self.assertEqual(len(result["all_market_original_rows"]),1103)
        self.assertEqual(len(result["t0_spot_usdt_symbol_ids"]),1100)
        self.assertEqual(result["G0"],"PARTIAL_NOT_FULL_DYNAMIC_PIT")
        self.assertEqual(result["G1"],"NOT_SCORABLE")
        self.assertEqual(result["G6"],"NO_GO")
        self.assertEqual(result["source_authenticity"],
                         "SELF_REPORTED_HTTP_RECEIPTS_NOT_EXCHANGE_SIGNED")
        self.assertTrue(all(r["crypto_asset_type_at_event"]=="UNKNOWN"
                            for r in result["all_market_original_rows"]))
        self.assertEqual(sum(r["eligible_spot_usdt_t0"]
                             for r in result["all_market_original_rows"]),1100)

    def test_synthetic_after_start_cannot_be_backdated_as_prestart_t0(self):
        self.fake_bundle(after_start=True)
        with self.assertRaisesRegex(ValueError,"PRESTART_15MIN"):
            gate.admit_window(self.start,self.zip,self.receipts)

    def test_synthetic_older_than_15min_is_not_window_T0(self):
        self.fake_bundle(first_seconds_before=901)
        with self.assertRaisesRegex(ValueError,"PRESTART_15MIN"):
            gate.admit_window(self.start,self.zip,self.receipts)

    def test_an_alleged_capture_after_supplied_asof_is_not_admitted(self):
        self.fake_bundle()
        asof=self.start_dt-timedelta(minutes=2,seconds=1)
        with self.assertRaisesRegex(ValueError,"FUTURE_RECEIPT_RELATIVE_TO_ASOF"):
            gate.preflight(self.start,self.stamp(asof),self.zip,self.receipts)

    def test_real_october_stage163_old_T0_is_rejected_for_all_november_dates(self):
        archive=(Path(__file__).resolve().parents[2]/"monster/evidence/"
                 "monster_stage163_spot_original_http_t0_actual")
        for start in gate.WINDOWS:
            with self.subTest(start=start),self.assertRaisesRegex(ValueError,"PRESTART_15MIN"):
                gate.admit_window(start,archive/"source_raw_http.zip",
                                  archive/"source_receipts.json")

    def test_fake_capture_cannot_take_over_old_unregistered_dates(self):
        self.fake_bundle()
        for date in ("2026-10-17T22:06:00Z","2026-11-03T00:00:00Z",
                     "2026-11-09T00:00:00Z"):
            with self.assertRaisesRegex(ValueError,"UNREGISTERED"):
                gate.admit_window(date,self.zip,self.receipts)

    def test_zip_sha_and_original_endpoint_body_hash_are_binding(self):
        self.fake_bundle()
        obj=json.loads(self.receipts.read_text())
        obj["source_zip_sha256"]="0"*64
        self.receipts.write_text(json.dumps(obj))
        with self.assertRaisesRegex(ValueError,"SOURCE_ZIP_SHA256"):
            gate.admit_window(self.start,self.zip,self.receipts)
        self.fake_bundle()
        obj=json.loads(self.receipts.read_text())
        obj["source_sha_receipts"]["exchangeInfo"]["body_sha256"]="f"*64
        self.receipts.write_text(json.dumps(obj))
        with self.assertRaisesRegex(ValueError,"MANIFEST_OR_RECEIPT"):
            gate.admit_window(self.start,self.zip,self.receipts)

    def test_external_http_endpoint_url_mismatch_rejected_without_source_calls(self):
        self.fake_bundle()
        obj=json.loads(self.receipts.read_text())
        obj["source_sha_receipts"]["exchangeInfo"]["url"]="https://other.example/api/v3/exchangeInfo"
        self.receipts.write_text(json.dumps(obj))
        with self.assertRaisesRegex(ValueError,"MANIFEST_OR_RECEIPT"):
            gate.admit_window(self.start,self.zip,self.receipts)

    def test_symlink_and_orphan_archive_rejected(self):
        self.fake_bundle()
        symlink=self.root/"link.zip"
        symlink.symlink_to(self.zip)
        with self.assertRaisesRegex(ValueError,"ARCHIVE_MISSING_OR_SYMLINK"):
            gate.admit_window(self.start,symlink,self.receipts)
        with self.assertRaisesRegex(ValueError,"BOTH_ARCHIVE_AND_RECEIPTS"):
            gate.preflight(self.start,self.stamp(self.start_dt),self.zip,None)

    def test_clock_iso_timezone_and_microsecond_precision(self):
        for bad in ("2026-11-02T00:00:00+07:00",
                    "2026-11-02T00:00:00","not-a-time"):
            with self.assertRaises(ValueError):
                gate.parse_us(bad)
        t=gate.parse_us("2026-11-02T00:00:00.000001Z")
        self.assertEqual(t-gate.parse_us("2026-11-02T00:00:00Z"),1)

    def test_source_free_t0_does_not_promote_gates_or_create_fake_roster(self):
        report=gate.preflight(self.start,"2026-10-26T00:00:00Z")
        self.assertNotIn("t0_spot_usdt_symbol_ids",report)
        self.assertEqual(report["G0"],"POPULATION_UNKNOWN")
        self.assertEqual(report["G5"],"INDEPENDENT_REVIEW_PENDING")
        self.assertTrue(report["NO_AUTOMATIONS"])
        self.assertTrue(report["NO_TRADES"])


if __name__=="__main__":
    unittest.main()
