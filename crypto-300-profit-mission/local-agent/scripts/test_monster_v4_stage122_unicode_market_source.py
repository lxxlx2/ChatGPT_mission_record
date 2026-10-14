#!/usr/bin/env python3
"""Stage122 frozen Unicode Binance official-market intake regression.

Pure synthetic source proof fixture; NOT actual Oct14 saved Binance bytes,
NOT user approval, NOT installation and NO LIVE HTTP or trades.
"""
from __future__ import annotations
from datetime import date
from pathlib import Path
import copy
import hashlib
import json
import tempfile
import unittest
from unittest.mock import Mock,patch

try:
    import monster_v4_stage105_capture_universe_core as freeze
    import monster_v4_stage97_one_shot_usdm_capture as capture
    import monster_v4_stage99_mac_launchd_one_shot as scheduler
    import monster_v4_stage38_usdm_original_v4_1m_pilot as history
    import monster_v4_stage116_one_shot_forward_replay as future
except ImportError:
    from scripts import monster_v4_stage105_capture_universe_core as freeze
    from scripts import monster_v4_stage97_one_shot_usdm_capture as capture
    from scripts import monster_v4_stage99_mac_launchd_one_shot as scheduler
    from scripts import monster_v4_stage38_usdm_original_v4_1m_pilot as history
    from scripts import monster_v4_stage116_one_shot_forward_replay as future

VALID_UNICODE=(
    "币安人生USDT","我踏马来了USDT","龙虾USDT","牛来USDT","哈基米USDT",
)
WINDOW=freeze.WINDOWS[0]
START=freeze.verify_window(WINDOW)


def make_exchange_info():
    symbols=[{
        "symbol":sym,
        "status":"TRADING",
        "contractType":"PERPETUAL",
        "baseAsset":sym[:-4],
        "quoteAsset":"USDT",
        "onboardDate":START-86_400_000,
    } for sym in VALID_UNICODE]
    symbols.append({
        "symbol":"BTCUSDT","status":"TRADING","contractType":"PERPETUAL",
        "baseAsset":"BTC","quoteAsset":"USDT","onboardDate":START-86_400_000})
    symbols.append({
        "symbol":"BTCUSDT_261225","status":"TRADING",
        "contractType":"CURRENT_QUARTER","baseAsset":"BTC",
        "quoteAsset":"USDT","onboardDate":START-86_400_000})
    symbols.append({
        "symbol":"HALTEDUSDT","status":"BREAK",
        "contractType":"PERPETUAL","baseAsset":"HALTED",
        "quoteAsset":"USDT","onboardDate":START-86_400_000})
    return {"serverTime":START-86_400_000,"symbols":symbols}


def synthetic_clock_bundle(body):
    ts=START-12*60_000
    before=capture.fixture(capture.TIME_URL,{"serverTime":ts+100},ts,ts+200)
    market=capture.fixture(capture.EXCHANGE_URL,body,ts+200,ts+400)
    after=capture.fixture(capture.TIME_URL,{"serverTime":ts+500},ts+400,ts+600)
    return before,market,after


def actual_type_level_fixture():
    first,market,last=synthetic_clock_bundle(make_exchange_info())
    return capture.verify_time_proof(first,last,market,WINDOW)


class RealRootCauseCompatibility(unittest.TestCase):
    def test_all_five_current_real_binance_names_will_pass_without_normalization(self):
        self.assertEqual(len(VALID_UNICODE),5)
        for symbol in VALID_UNICODE:
            self.assertTrue(freeze.valid_exact_venue_symbol(symbol),symbol)
        self.assertTrue(freeze.valid_exact_venue_symbol("BTCUSDT_261225"))
        self.assertTrue(freeze.valid_exact_venue_symbol("1000000MOGUSDT"))
        self.assertEqual(tuple(VALID_UNICODE),
            tuple(item["symbol"] for item in make_exchange_info()["symbols"][:5]))

    def test_unsafe_and_malformed_symbol_names_still_fail(self):
        for name in ("",None,1,"lowercaseusdt","BTC USDT","龙虾 USDT",
                     "龙虾/USDT","../BTCUSDT","BTC_USDT_","_BTCUSDT",
                     "BTC__USDT","龙虾\nUSDT","龙虾\u200bUSDT","CATUSDT\\etc",
                     "BTC-USDT","[CATUSDT]"):
            self.assertFalse(freeze.valid_exact_venue_symbol(name),repr(name))

    def test_complete_full_raw_market_population_retained_all_8_rows(self):
        proof=actual_type_level_fixture()
        frozen=freeze.freeze_universe(proof["raw_market_packet"])
        self.assertEqual(frozen["population_all_exchange_symbols"],8)
        self.assertEqual(frozen["usd_m_usdt_perpetual_asof_candidates"],6)
        self.assertEqual([z["symbol"] for z in frozen["rows"][:5]],
                         list(VALID_UNICODE))
        self.assertEqual(
            len([z for z in frozen["rows"]
                 if not z["candidate_for_raw_USDM_attempt"]]),2)
        self.assertEqual(proof["snapshot_symbol_summary"][
            "population_all_exchange_symbols"],8)
        self.assertEqual(
            proof["raw_market_packet"]["raw_sha256"],
            hashlib.sha256(proof["raw_market_packet"][
                "raw_exchangeInfo_json"].encode("utf-8")).hexdigest())
        self.assertEqual(proof["crypto_only_classification"],"NOT_VERIFIED")
        self.assertEqual(proof["monster_deploy"],"NO_GO")

    def test_duplicate_or_invalid_returns_distinct_error_and_source_SHA_is_guarded(self):
        for variant,error in (
            ("龙虾USDT","STAGE91_MARKET_SYMBOL_DUPLICATE"),
            ("CATUSDT/../../evil","STAGE91_MARKET_SYMBOL_INVALID"),
        ):
            altered=make_exchange_info()
            if variant=="龙虾USDT":
                altered["symbols"].append(copy.deepcopy(altered["symbols"][2]))
            else:
                altered["symbols"][0]["symbol"]=variant
            first,exchange,last=synthetic_clock_bundle(altered)
            with self.assertRaisesRegex(ValueError,error):
                capture.verify_time_proof(first,last,exchange,WINDOW)
        proof=actual_type_level_fixture()
        tampered=copy.deepcopy(proof["raw_market_packet"])
        # The Stage97 synthetic JSON fixture uses escaped Unicode in its
        # raw body; corrupt a guaranteed present ASCII part of that byte body
        # without updating its original publisher-response SHA256.
        tampered["raw_exchangeInfo_json"]=tampered["raw_exchangeInfo_json"].replace(
            "BTCUSDT","BTCXSDT")
        with self.assertRaisesRegex(ValueError,"STAGE91_UNIVERSE_RAW_BYTE_TAMPER"):
            freeze.freeze_universe(tampered)

    def test_publisher_url_encoded_and_fixed_symbol_shard_unicode_utf8(self):
        for sym in VALID_UNICODE:
            source=history.url(sym,date(2026,10,14))
            self.assertTrue(source.startswith(history.BASE))
            self.assertNotIn("龙虾",source)
            self.assertNotIn("币安",source)
            self.assertIn("%",source)
            self.assertTrue(source.endswith("-1m-2026-10-14.zip"))
            self.assertEqual(future.shard_no(sym),future.shard_no(sym))
            self.assertIn(future.shard_no(sym),range(future.SHARDS))
        self.assertTrue(history.url("CATUSDT",date(2026,10,14)).endswith(
            "CATUSDT-1m-2026-10-14.zip"))

    def test_first_window_after_deadline_forbids_recapture_even_with_approved_fixture(self):
        with tempfile.TemporaryDirectory() as td:
            fake_capture=Mock(side_effect=AssertionError(
                "STAGE122_MUST_NOT_RECAPTURE_MISSED_OCT14"))
            with patch.object(scheduler,"STATES",Path(td)/"state"), \
                 patch.object(scheduler,"assert_reviewed_runtime_source",
                              return_value={"original":True}):
                observed=scheduler.run(WINDOW,clock=lambda:START+10*60_000,
                                       capture=fake_capture)
                self.assertEqual(observed,"MISSED_WINDOW")
                self.assertFalse(fake_capture.called)
                self.assertEqual(json.loads((Path(td)/"state"/
                    "2026-10-14.json").read_text())["status"],
                    "MISSED_WINDOW_NO_BACKFILL")

    def test_captured_unicode_response_schema_can_feed_next_fixed_dates(self):
        for w in freeze.WINDOWS:
            anchor=freeze.verify_window(w)
            at=anchor-12*60_000
            body=make_exchange_info()
            before=capture.fixture(capture.TIME_URL,
                  {"serverTime":at+100},at,at+200)
            market=capture.fixture(capture.EXCHANGE_URL,body,at+200,at+400)
            after=capture.fixture(capture.TIME_URL,
                  {"serverTime":at+500},at+400,at+600)
            result=capture.verify_time_proof(before,after,market,w)
            self.assertEqual(result["window_start_utc"],w)
            self.assertEqual(result["snapshot_symbol_summary"][
                             "population_all_exchange_symbols"],8)


if __name__=="__main__":
    unittest.main(verbosity=2)
