"""Stage139 tests: artificial saved original-format T0 and contractInfo frames only."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import monster_v4_stage131_dynamic_listing_g1_population_bridge as s131
import monster_v4_stage133_manual_actual_t0_forward_proof as s133
import monster_v4_stage134_t0_population_readiness_bridge as s134
import monster_v4_stage139_official_t0_and_saved_contractinfo_evidence as s139
from test_monster_v4_stage133_manual_actual_t0_forward_proof import fixture


def original_t0():
    return s133.validate_three_http_records(*fixture())


def epoch_ms(text):
    from datetime import datetime
    return int(datetime.fromisoformat(
        text.replace("Z", "+00:00")).timestamp() * 1000)


def raw_event(symbol, state="TRADING", at="2026-10-28T06:20:12Z",
              recv="2026-10-28T06:20:25Z", st=1, ct="PERPETUAL"):
    payload = {
        "e": "contractInfo", "E": epoch_ms(at), "s": symbol,
        "ot": epoch_ms("2026-10-28T06:20:00Z"), "cs": state,
        "st": st, "ct": ct,
    }
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return {
        "raw": raw, "raw_sha256": hashlib.sha256(raw.encode()).hexdigest(),
        "received_ms": epoch_ms(recv), "source_stream": "!contractInfo"}


def saved(*rows):
    return {"schema": s139.EVENT_SCHEMA, "rows": list(rows)}


class Stage139Tests(unittest.TestCase):
    def test_t0_official_underlying_type_never_makes_verified_issuer(self):
        r = s139.inspect(original_t0())
        self.assertEqual(r["initial_USDM_perpetual_USDT_attempts"], 3)
        x = {v["symbol_exact"]: v for v in r["initial_original_instrument_rows"]}
        self.assertEqual(x["MSFTUSDT"]["asof_instrument_scope"],
                         "OFFICIAL_NOT_COIN_TYPED_AT_T0")
        self.assertEqual(x["ABCUSDT"]["asof_instrument_scope"], "UNKNOWN_TYPE_ASOF_T0")
        self.assertEqual(x["币安人生USDT"]["asof_instrument_scope"], "UNKNOWN_TYPE_ASOF_T0")
        self.assertEqual(r["original_full_T0_exchangeinfo_symbol_count"], 5)
        self.assertEqual(r["stage134_all_source_attempts"], 3)
        self.assertFalse(r["issuer_identity_independently_verified"])
        self.assertEqual(r["G1"], "NOT_SCORABLE")
        self.assertFalse(r["continuous_seven_day_stream_capture_proven"])
        self.assertEqual(r["historical_stage116_first"], "SOURCE_FAILED_NO_BACKFILL")

    def test_explicit_coin_typed_still_needs_independent_issuer(self):
        f, mid, last = fixture()
        original = copy.deepcopy(mid)
        original["json"]["symbols"][0]["underlyingType"] = "COIN"
        original["raw"] = json.dumps(original["json"], ensure_ascii=False)
        original["raw_sha256"] = hashlib.sha256(original["raw"].encode()).hexdigest()
        p = s133.validate_three_http_records(f, original, last)
        r = s139.inspect(p)
        abc = next(x for x in r["initial_original_instrument_rows"]
                   if x["symbol_exact"] == "ABCUSDT")
        self.assertEqual(abc["asof_instrument_scope"],
                         "OFFICIAL_COIN_TYPED_ISSUER_UNVERIFIED")
        self.assertFalse(abc["eligible_to_claim_crypto_G1"])

    def test_original_saved_event_to_stage134_candidate_no_backdating(self):
        events = saved(raw_event("NEWUSDT"),
                       raw_event("OLDUSDT", recv="2026-10-28T06:20:39Z"),
                       raw_event("币安人生USDT", recv="2026-10-28T06:20:45Z"))
        p = original_t0()
        r = s139.inspect(p, events)
        self.assertEqual(r["raw_event_receipts_supplied"], 3)
        self.assertEqual(r["in_window_UNVERIFIED_event_candidates"], 2)
        self.assertEqual(r["stage134_all_source_attempts"], 5)
        a = r["stage134_compatible_unverified_candidate_rows"]
        self.assertEqual({x["symbol"] for x in a["rows"]}, {"NEWUSDT", "OLDUSDT"})
        self.assertTrue(all(x["first_observed_minute_utc"] ==
                            "2026-10-28T06:21:00Z" for x in a["rows"]))
        self.assertTrue(all(x["source_status"] == "RAW_UNVERIFIED_CANDIDATE"
                            for x in a["rows"]))
        after = s134.reconcile(p, a)
        self.assertEqual(after["stage131_reconciled_population"]["raw_symbol_attempts"], 5)
        self.assertEqual(r["event_classification_counts"][
            "T0_EXISTING_ACTIVE_CONTRACT_UPDATE_NOT_ARRIVAL"], 1)
        self.assertFalse(r["in_window_listing_population_complete"])

    def test_ignores_nontrading_and_coin_margined_and_non_usdt(self):
        r = s139.inspect(original_t0(), saved(
            raw_event("FOOUSDT", state="BREAK"),
            raw_event("BARUSDT", st=2),
            raw_event("OTHERUSDC"),
            raw_event("QUARTERUSDT", state="TRADING", ct="CURRENT_QUARTER")))
        self.assertEqual(r["in_window_UNVERIFIED_event_candidates"], 0)
        self.assertEqual(r["event_classification_counts"][
            "NONTRADING_CONTRACT_EVENT_NOT_LISTING"], 1)
        self.assertEqual(r["event_classification_counts"]["NOT_USDM_CONTRACT_EVENT"], 1)
        self.assertEqual(r["event_classification_counts"][
            "NOT_USDT_PERPETUAL_CONTRACT_EVENT"], 2)

    def test_sha_and_receive_clock_are_required_not_onboard_as_trade_clock(self):
        good = raw_event("NEWUSDT")
        bad = copy.deepcopy(good)
        bad["raw_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "SHA256_DRIFT"):
            s139.inspect(original_t0(), saved(bad))
        before_event = copy.deepcopy(good)
        before_event["received_ms"] = epoch_ms("2026-10-28T06:20:00Z")
        with self.assertRaisesRegex(ValueError, "RECEIPT_CLOCK_UNTRUSTWORTHY"):
            s139.inspect(original_t0(), saved(before_event))
        too_late = copy.deepcopy(good)
        too_late["received_ms"] = epoch_ms("2026-10-28T06:40:00Z")
        with self.assertRaisesRegex(ValueError, "RECEIPT_CLOCK_UNTRUSTWORTHY"):
            s139.inspect(original_t0(), saved(too_late))

    def test_same_raw_duplicate_censored_and_conflicting_same_clock_fail(self):
        e = raw_event("NEWUSDT")
        r = s139.inspect(original_t0(), saved(e, copy.deepcopy(e)))
        self.assertEqual(r["in_window_UNVERIFIED_event_candidates"], 1)
        self.assertEqual(r["event_classification_counts"]["duplicate_exact_receipt"], 1)
        changed = raw_event("NEWUSDT", state="BREAK")
        with self.assertRaisesRegex(ValueError, "SAME_EVENT_CLOCK_CONFLICT"):
            s139.inspect(original_t0(), saved(e, changed))
        # Observed after the end-exclusive window is not retroactively admitted.
        beyond = raw_event("NEWUSDT", at="2026-11-04T06:19:10Z",
                           recv="2026-11-04T06:19:59Z")
        r2 = s139.inspect(original_t0(), saved(beyond))
        self.assertEqual(r2["in_window_UNVERIFIED_event_candidates"], 0)
        self.assertEqual(r2["event_classification_counts"][
            "OUT_OF_NEW_FORWARD_WINDOW_NOT_CANDIDATE"], 1)

    def test_offline_cli_only_saved_bytes_no_http_no_schedule(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            tp, ep = base/"t0.json", base/"events.json"
            output, arrivals = base/"report.json", base/"arrivals.json"
            tp.write_text(json.dumps(original_t0(), ensure_ascii=False))
            ep.write_text(json.dumps(saved(raw_event("NEWUSDT")), ensure_ascii=False))
            cmd = [sys.executable, str(Path(s139.__file__)), "--t0",
                   str(tp), "--saved-contract-events", str(ep),
                   "--out", str(output), "--arrivals-out", str(arrivals)]
            c = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            self.assertEqual(c.returncode, 0, c.stderr)
            report = json.loads(output.read_text())
            self.assertEqual(report["in_window_UNVERIFIED_event_candidates"], 1)
            arr = json.loads(arrivals.read_text())
            self.assertEqual(arr["rows"][0]["symbol"], "NEWUSDT")
            self.assertFalse(report["scheduled_capture"])
            self.assertEqual(report["model_buy"], "NO_GO")
            failed = subprocess.run([sys.executable, str(Path(s139.__file__)),
                                     "--out", str(base/"no-t0.json")],
                                    capture_output=True, text=True)
            self.assertNotEqual(failed.returncode, 0)
            self.assertFalse((base/"no-t0.json").exists())


if __name__ == "__main__":
    unittest.main()
