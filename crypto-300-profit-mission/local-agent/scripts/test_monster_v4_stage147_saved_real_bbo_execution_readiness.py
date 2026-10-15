#!/usr/bin/env python3
"""Stage147 source-locked real 525 checks and synthetic corrupt-response gates."""
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest

import monster_v4_stage147_saved_real_bbo_execution_readiness as s147


def receipt(raw):
    return {"raw_SHA256":hashlib.sha256(raw.encode()).hexdigest(),
            "original_URL":"https://www.binance.com/fapi/v1/ticker/bookTicker",
            "request_start_ms":1000,"response_end_ms":2000,
            "original_all_market_source_rows":len(json.loads(raw))}


class Stage147OfflineTests(unittest.TestCase):

    def test_real_saved_525_joins_original_every_symbol_no_G4(self):
        r=s147.audit()
        c=r["counts"]
        self.assertEqual(c["original_venue_attempts"],525)
        self.assertEqual(c["coin_typed_issuer_unverified"],523)
        self.assertEqual(c["other_venue_type_issuer_unverified"],2)
        self.assertEqual(c["source_quote_valid_but_not_L2"],525)
        self.assertEqual(c.get("source_censored",0),0)
        self.assertEqual(c.get("source_invalid",0),0)
        self.assertEqual(len(r["all_market_population_rows"]),525)
        self.assertTrue(all(x["G4_verified_executable_case"] is False
                            and x["actual_fill"]=="NOT_OBSERVED"
                            and x["net_executable_profit"]=="UNKNOWN"
                            for x in r["all_market_population_rows"]))
        self.assertTrue(r["no_default_transaction_size"])
        self.assertIsNone(r["explicit_scenario_quote"])
        self.assertEqual(r["G4"],"UNKNOWN")
        self.assertEqual(r["G6"],"NO_GO")
        self.assertEqual(len(r["source_receipts"]),3)
        for source in r["source_receipts"].values():
            self.assertEqual(len(source["raw_SHA256"]),64)
            self.assertTrue(source["original_URL"].startswith("https://www.binance.com/fapi/"))
        self.assertGreater(float(r["descriptive_only"]["spread_bps_P50"]),3)
        self.assertLess(float(r["descriptive_only"]["spread_bps_P50"]),5)
        self.assertGreater(float(r["descriptive_only"]["ask_price_times_qty_proxy_P50"]),100)
        self.assertLess(float(r["descriptive_only"]["ask_price_times_qty_proxy_P50"]),200)

    def test_explicit_optional_scenario_never_claims_fill(self):
        r=s147.audit(quote_scenario="100")
        c=r["counts"]
        self.assertEqual(c["scenario_ask_top_proxy_below"],191)
        self.assertEqual(c["scenario_bid_top_proxy_below"],236)
        self.assertEqual(r["explicit_scenario_quote"],"100")
        self.assertFalse(r["no_default_transaction_size"])
        self.assertEqual(r["G4"],"UNKNOWN")
        for row in r["all_market_population_rows"]:
            self.assertEqual(row["status"],"HISTORICAL_BBO_ONLY_G4_NOT_SCORABLE")
            self.assertIsNone(row.get("actual_order_id"))
        for invalid in ("0","-10","NaN","Infinity",True):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    s147.audit(quote_scenario=invalid)

    def test_population_censored_join_retained_not_negative_prediction(self):
        u=[{"symbol_exact":"ABCUSDT","asof_instrument_scope":"OFFICIAL_COIN_TYPED_ISSUER_UNVERIFIED"},
           {"symbol_exact":"NEWUSDT","asof_instrument_scope":"OFFICIAL_NOT_COIN_TYPED_AT_T0"}]
        source={"bbo":{"ABCUSDT":{"symbol":"ABCUSDT","bidPrice":"1","askPrice":"1.01",
                                  "bidQty":"2","askQty":"4","time":1900}},
                "ticker24":{"ABCUSDT":{"symbol":"ABCUSDT","quoteVolume":"1000000"}},
                "mark":{"ABCUSDT":{"symbol":"ABCUSDT","markPrice":"1.00"}}}
        receipts={"bbo":{"response_end_ms":2000,"raw_SHA256":"a"*64}}
        r=s147.analyze_rows(u,source,receipts)
        self.assertEqual(r["counts"]["source_censored"],1)
        self.assertEqual(r["counts"]["original_venue_attempts"],2)
        self.assertEqual(r["all_market_population_rows"][1]["status"],
                         "SOURCE_CENSORED_MISSING_BBO_TICKER_OR_MARK")
        self.assertFalse(r["all_market_population_rows"][1]["G4_verified_executable_case"])
        self.assertEqual(r["all_market_population_rows"][1]["net_executable_profit"],"UNKNOWN")
        a=r["all_market_population_rows"][0]
        self.assertEqual(a["best_ask_displayed_price_times_quantity_proxy"],"4.04")
        self.assertFalse(a["quote_proxy_has_verified_USDT_contract_multiplier"])
        self.assertEqual(a["book_ticker_event_age_ms_relative_to_response_end"],100)
        source["bbo"]["ABCUSDT"]["askPrice"]="0.99"
        bad=s147.analyze_rows(u,source,receipts)
        self.assertEqual(bad["counts"]["source_invalid"],1)
        self.assertEqual(bad["all_market_population_rows"][0]["status"],
                         "SOURCE_INVALID_BBO_MARK_OR_TICKER")
        with self.assertRaisesRegex(ValueError,"DUPLICATE_ORIGINAL_525"):
            s147.analyze_rows(u+[u[0]],source,receipts)

    def test_original_raw_SHA_duplicate_row_and_clock_gate(self):
        name="bbo"
        data=[{"symbol":"BTCUSDT","bidPrice":"1.00","askPrice":"1.01",
               "bidQty":"1","askQty":"2","time":1000}]
        raw=json.dumps(data,sort_keys=True)
        m={"optional_all_market_marketdata_receipts":{
            s147.MANIFEST_NAMES[name]:{
                "file":s147.SOURCES[name]+"_raw_http.json",
                "raw_sha256":hashlib.sha256(raw.encode()).hexdigest(),
                "decoded_row_count":1,
                "response_end_utc":"1970-01-01T00:00:02.000Z"}}}
        obj={"raw":raw,"raw_sha256":m["optional_all_market_marketdata_receipts"][
             s147.MANIFEST_NAMES[name]]["raw_sha256"],
             "decoded_row_count":1,"decoded_top_level_type":"list",
             "url":"https://www.binance.com/fapi/v1/ticker/bookTicker",
             "request_start_ms":1000,"response_end_ms":2000}
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/(s147.SOURCES[name]+"_raw_http.json")
            path.write_text(json.dumps(obj))
            b,rec=s147.read_verified_source(Path(td),name,m)
            self.assertEqual(len(b),1)
            self.assertEqual(rec["raw_SHA256"],obj["raw_sha256"])
            obj["raw"] += " "
            path.write_text(json.dumps(obj))
            with self.assertRaisesRegex(ValueError,"RECEIPT_SHA"):
                s147.read_verified_source(Path(td),name,m)
            repeated=json.dumps(data+data,sort_keys=True)
            obj["raw"]=repeated
            obj["raw_sha256"]=hashlib.sha256(repeated.encode()).hexdigest()
            obj["decoded_row_count"]=2
            m["optional_all_market_marketdata_receipts"][
                s147.MANIFEST_NAMES[name]]["raw_sha256"]=obj["raw_sha256"]
            m["optional_all_market_marketdata_receipts"][
                s147.MANIFEST_NAMES[name]]["decoded_row_count"]=2
            path.write_text(json.dumps(obj))
            with self.assertRaisesRegex(ValueError,"DUPLICATE_ORIGINAL_MARKET_SOURCE"):
                s147.read_verified_source(Path(td),name,m)

    def test_stage148_P1_swapped_allusdt_member_same_525_must_reject(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/"archive"
            shutil.copytree(s147.SOURCE_DIR,root)
            derived=root/"stage139_original_T0_asof_contract_metadata.json"
            obj=json.loads(derived.read_text())
            changed=[x for x in obj["initial_original_instrument_rows"]
                     if x["symbol_exact"]=="ALLUSDT"]
            self.assertEqual(len(changed),1)
            changed[0]["symbol_exact"]="AAPLUSDT"
            derived.write_text(json.dumps(obj))
            with self.assertRaisesRegex(
                    ValueError,"STAGE148_RAW_STAGE133_EXCHANGEINFO_OR_DERIVED_525_ROSTER_DRIFT"):
                s147.audit(root)

    def test_stage148_P1_derived_issuer_scope_and_raw_exchange_bytes_must_reject(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/"archive"
            shutil.copytree(s147.SOURCE_DIR,root)
            derived=root/"stage139_original_T0_asof_contract_metadata.json"
            obj=json.loads(derived.read_text())
            obj["initial_original_instrument_rows"][0][
                "asof_instrument_scope"]="OFFICIAL_NOT_COIN_TYPED_AT_T0"
            derived.write_text(json.dumps(obj))
            with self.assertRaisesRegex(ValueError,"STAGE148_RAW_STAGE133"):
                s147.audit(root)
            shutil.copyfile(s147.SOURCE_DIR/derived.name,derived)
            original=root/"stage133_original_three_HTTP_T0.json"
            t0=json.loads(original.read_text())
            t0["raw_http_records"]["official_exchange_info"]["raw"]="{}"
            original.write_text(json.dumps(t0))
            with self.assertRaises(ValueError):
                s147.audit(root)
            original.unlink()
            with self.assertRaises(FileNotFoundError):
                s147.audit(root)

    def test_stage148_P2_only_modify_wrapper_time_plus_one_day_reject(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/"archive"
            shutil.copytree(s147.SOURCE_DIR,root)
            wrapper=root/"usdm_all_best_bid_ask_raw_http.json"
            obj=json.loads(wrapper.read_text())
            self.assertEqual(obj["response_end_ms"],1792000368089)
            obj["response_end_ms"]+=86_400_000
            wrapper.write_text(json.dumps(obj))
            with self.assertRaisesRegex(ValueError,"STAGE147_ORIGINAL_HTTP_RECEIPT_SHA_OR_META_MISMATCH"):
                s147.audit(root)

    def test_stage148_P2_wrong_same_host_endpoint_rejected_per_source(self):
        endpoints={
            "bbo":"https://www.binance.com/fapi/v1/premiumIndex",
            "ticker24":"https://www.binance.com/fapi/v1/ticker/bookTicker",
            "mark":"https://www.binance.com/fapi/v1/ticker/24hr",
        }
        for key,url in endpoints.items():
            with self.subTest(source=key):
                with tempfile.TemporaryDirectory() as tmp:
                    root=Path(tmp)/"archive"
                    shutil.copytree(s147.SOURCE_DIR,root)
                    wrapper=root/(s147.SOURCES[key]+"_raw_http.json")
                    obj=json.loads(wrapper.read_text())
                    obj["url"]=url
                    wrapper.write_text(json.dumps(obj))
                    with self.assertRaisesRegex(ValueError,"STAGE147_ORIGINAL_HTTP_RECEIPT_SHA_OR_META_MISMATCH"):
                        s147.audit(root)

    def test_status_unknown_when_book_zero_qty_or_future_event(self):
        base={"symbol_exact":"ABCUSDT",
              "asof_instrument_scope":"OFFICIAL_COIN_TYPED_ISSUER_UNVERIFIED"}
        q={"symbol":"ABCUSDT","bidPrice":"1.00","askPrice":"1.01",
           "bidQty":"1","askQty":"2","time":2001}
        d={"bbo":{"ABCUSDT":q},
           "ticker24":{"ABCUSDT":{"quoteVolume":"1000"}},
           "mark":{"ABCUSDT":{"markPrice":"1"}}}
        r={"bbo":{"response_end_ms":2000,"raw_SHA256":"a"*64}}
        self.assertEqual(s147.analyze_rows([base],d,r)["counts"]["source_invalid"],1)
        q["time"]=1900
        q["askQty"]="0"
        self.assertEqual(s147.analyze_rows([base],d,r)["counts"]["source_invalid"],1)


if __name__=="__main__":
    unittest.main()
