import copy
import unittest
from datetime import datetime, timezone

import monster_v4_stage133_manual_actual_t0_forward_proof as s


def ms(utc):
    return int(datetime.fromisoformat(utc.replace("Z","+00:00")).timestamp()*1000)


def fixture():
    now=ms("2026-10-28T06:10:00Z")
    first=s.stage97.fixture(s.TIME_URL,{"serverTime":now+100},now,now+200)
    market={"serverTime":now-86400000,
            "symbols":[{"symbol":"ABCUSDT","status":"TRADING","contractType":"PERPETUAL",
                        "quoteAsset":"USDT","baseAsset":"ABC"},
                       {"symbol":"币安人生USDT","status":"TRADING","contractType":"PERPETUAL",
                        "quoteAsset":"USDT","baseAsset":"币安人生"},
                       {"symbol":"MSFTUSDT","status":"TRADING","contractType":"PERPETUAL",
                        "quoteAsset":"USDT","underlyingType":"EQUITY"},
                       {"symbol":"OLDUSDT","status":"BREAK","contractType":"PERPETUAL",
                        "quoteAsset":"USDT"},
                       {"symbol":"USDCDUAL","status":"TRADING","contractType":"PERPETUAL",
                        "quoteAsset":"USDC"}]}
    middle=s.stage97.fixture(s.EXCHANGE_URL,market,now+200,now+500)
    last=s.stage97.fixture(s.TIME_URL,{"serverTime":now+600},now+500,now+700)
    return first,middle,last


class Stage133Tests(unittest.TestCase):
    def test_full_manual_official_3_source_synthetic_unicode_and_no_crypto_upgrade(self):
        first,second,third=fixture()
        x=s.validate_three_http_records(first,second,third)
        self.assertEqual(x["exchange_full_original_symbols"],5)
        self.assertEqual(x["exchange_current_trading_perpetual_usdt"],3)
        self.assertIn("币安人生USDT",x["exact_usdt_perpetual_symbols"])
        self.assertIn("MSFTUSDT",x["exact_usdt_perpetual_symbols"])
        self.assertEqual(x["source_status_counts"],{"BREAK":1,"TRADING":4})
        self.assertEqual(x["independent_crypto_issuer_and_contract_unit_verification"],"UNVERIFIED")
        self.assertEqual(x["new_forward_start_utc"],"2026-10-28T06:20:00Z")
        self.assertEqual(x["future_all_market_7day_source"],"PENDING_WINDOW_END")
        self.assertEqual(x["historical_stage116_original_first_status"],"SOURCE_FAILED_NO_BACKFILL")
        self.assertFalse(x["automatic_followup_scheduled"])
        self.assertEqual(x["monster_deployment"],"NO_GO")
        self.assertGreater(x["time_from_final_response_to_start_ms"],300000)

    def test_network_only_when_explicit_manual_request(self):
        f,m,l=fixture()
        seen=[]
        def getter(url,*,max_bytes):
            seen.append(url)
            return (f if len(seen)==1 else m if len(seen)==2 else l)
        for req in (None,{},{"schema":s.REQUEST_SCHEMA}, {"schema":s.REQUEST_SCHEMA,"explicit_manual_request":False}):
            with self.subTest(request=req):
                with self.assertRaisesRegex(ValueError,"MANUAL_REQUEST"):
                    s.one_shot_capture(req,get=getter)
        self.assertEqual(seen,[])
        out=s.one_shot_capture({"schema":s.REQUEST_SCHEMA,"explicit_manual_request":True},get=getter)
        self.assertEqual(seen,[s.TIME_URL,s.EXCHANGE_URL,s.TIME_URL])
        self.assertEqual(out["G1"],"NOT_SCORABLE")

    def test_bad_raw_SHA_or_changed_payload_rejected(self):
        f,m,l=fixture()
        damaged=copy.deepcopy(m)
        damaged["raw_sha256"]="0"*64
        with self.assertRaisesRegex(ValueError,"SHA256_CHANGED"):
            s.validate_three_http_records(f,damaged,l)
        tamper=copy.deepcopy(m)
        tamper["json"]["symbols"][0]["symbol"]="CHANGEDUSDT"
        with self.assertRaisesRegex(ValueError,"JSON_DECODED"):
            s.validate_three_http_records(f,tamper,l)

    def test_duplicate_symbol_or_invalid_exact_unicode_fail(self):
        f,m,l=fixture()
        bad=copy.deepcopy(m)
        bad["json"]["symbols"].append(copy.deepcopy(bad["json"]["symbols"][0]))
        bad["raw"]=__import__("json").dumps(bad["json"],ensure_ascii=False)
        bad["raw_sha256"]=s.stage97.sha(bad["raw"].encode("utf-8"))
        with self.assertRaisesRegex(ValueError,"DUPLICATE"):
            s.validate_three_http_records(f,bad,l)
        bad2=copy.deepcopy(m)
        bad2["json"]["symbols"][0]["symbol"]="foo/../USDT"
        bad2["raw"]=__import__("json").dumps(bad2["json"],ensure_ascii=False)
        bad2["raw_sha256"]=s.stage97.sha(bad2["raw"].encode("utf-8"))
        with self.assertRaisesRegex(ValueError,"EXACT_UNICODE"):
            s.validate_three_http_records(f,bad2,l)

    def test_server_time_independent_exchangeInfo_timestamp(self):
        f,m,l=fixture()
        altered=copy.deepcopy(m)
        altered["json"]["serverTime"]=0
        altered["raw"]=__import__("json").dumps(altered["json"],ensure_ascii=False)
        altered["raw_sha256"]=s.stage97.sha(altered["raw"].encode())
        a=s.validate_three_http_records(f,m,l)
        b=s.validate_three_http_records(f,altered,l)
        self.assertEqual(a["new_forward_start_utc"],b["new_forward_start_utc"])

    def test_invalid_independent_clock_order_drift_and_source_missing(self):
        f,m,l=fixture()
        backward=copy.deepcopy(l)
        backward["request_start_ms"]=m["request_start_ms"]-1
        with self.assertRaisesRegex(ValueError,"UNORDERED"):
            s.validate_three_http_records(f,m,backward)
        drift=copy.deepcopy(l)
        drift["json"]["serverTime"]+=8000
        drift["raw"]=__import__("json").dumps(drift["json"])
        drift["raw_sha256"]=s.stage97.sha(drift["raw"].encode())
        with self.assertRaisesRegex(ValueError,"CLOCK_DRIFT"):
            s.validate_three_http_records(f,m,drift)
        no_time=copy.deepcopy(f)
        no_time["json"]={}
        no_time["raw"]="{}"
        no_time["raw_sha256"]=s.stage97.sha(b"{}")
        with self.assertRaisesRegex(ValueError,"TIMESTAMP"):
            s.validate_three_http_records(no_time,m,l)

    def test_cannot_use_stage123_single_connector_snapshot_as_three_sources(self):
        f,m,l=fixture()
        with self.assertRaisesRegex(ValueError,"WRONG_OFFICIAL_ENDPOINT"):
            s.validate_three_http_records(m,m,l)
        with self.assertRaisesRegex(ValueError,"WRONG_OFFICIAL_ENDPOINT"):
            s.validate_three_http_records(f,l,l)


if __name__=="__main__":
    unittest.main()
