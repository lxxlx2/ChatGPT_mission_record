"""No-data, no-network, no-side-effects tests for ADR-005 candidate."""
from copy import deepcopy
import unittest

import monster_v4_shadow as original
from monster_v4_d1_rbtc15_last5_research import evaluate_research_candidate


FIVE = 300_000
TICK = 3_600_000
WATCH = 3_240_000
DEADLINE = WATCH + 900_000


def bars(closes, *, later_quote=20):
    assert len(closes) == 6
    out = []
    for idx, close in enumerate(closes):
        start = 1_800_000 + idx*FIVE
        op = closes[idx-1] if idx else close
        out.append([start, str(op), str(max(op,close)+1),
                    str(min(op,close)-1), str(close), "100",
                    start+FIVE-1, str(10 if idx < 3 else later_quote)])
    return out


class ResearchCandidateTests(unittest.TestCase):
    def setUp(self):
        self.coin = bars([100,100,100,104,108,112])
        self.btc = bars([200,200,200,201,202,203])

    def call(self, **extra):
        options=dict(symbol="COINUSDT",observed_ms=TICK,watch_ms=WATCH,
                     deadline_ms=DEADLINE,coin_closed5=self.coin,btc_closed5=self.btc)
        options.update(extra)
        return evaluate_research_candidate(**options)

    def test_current_btc_relative_candidate_pass(self):
        report=self.call()
        self.assertEqual(report["state"],"RESEARCH_SETUP")
        self.assertTrue(report["research_setup_candidate"])
        self.assertTrue(report["original_d1_candidate"])
        self.assertEqual(report["coin_minus_btc_15m_percentage_points"],"10.500")
        self.assertEqual(report["historical_executable_net_profit"],"UNKNOWN")

    def test_original_d1_input_is_not_modified(self):
        c=deepcopy(self.coin);b=deepcopy(self.btc)
        result=self.call()
        self.assertEqual(result["original_d1_features"],original.evaluate_closed_5m(c,TICK))
        self.assertEqual(c,self.coin);self.assertEqual(b,self.btc)

    def test_btc_outperformance_rejects_but_original_d1_unchanged(self):
        btc=bars([200,200,200,225,245,265])
        self.assertTrue(original.evaluate_closed_5m(self.coin,TICK)["setup_candidate"])
        result=self.call(btc_closed5=btc)
        self.assertEqual(result["state"],"RESEARCH_NO_SETUP_YET")
        self.assertFalse(result["research_setup_candidate"])
        self.assertTrue(result["original_d1_candidate"])

    def test_last_closed_coin_5m_negative_rejects_old_positive(self):
        coin=bars([100,100,100,110,120,119])
        self.assertTrue(original.evaluate_closed_5m(coin,TICK)["setup_candidate"])
        result=self.call(coin_closed5=coin)
        self.assertFalse(result["last5_nonnegative"])
        self.assertFalse(result["research_setup_candidate"])

    def test_not_promote_when_original_d1_did_not_pass(self):
        coin=bars([100,100,100,104,108,112],later_quote=12)
        self.assertFalse(original.evaluate_closed_5m(coin,TICK)["setup_candidate"])
        result=self.call(coin_closed5=coin)
        self.assertFalse(result["research_setup_candidate"])
        self.assertFalse(result["original_d1_candidate"])

    def test_missing_btc_is_censored_not_non_setup(self):
        result=self.call(btc_closed5=self.btc[:-1])
        self.assertEqual(result["state"],"SOURCE_CENSORED")
        self.assertIsNone(result["research_setup_candidate"])

    def test_btc_previous_5m_stale_even_if_six_rows(self):
        btc=deepcopy(self.btc)
        for bar in btc:bar[0]-=FIVE;bar[6]-=FIVE
        self.assertEqual(self.call(btc_closed5=btc)["state"],"SOURCE_CENSORED")

    def test_wrong_btc_timestamp_mismatch(self):
        btc=deepcopy(self.btc);btc[3][0]+=FIVE;btc[3][6]+=FIVE
        self.assertEqual(self.call(btc_closed5=btc)["state"],"SOURCE_CENSORED")

    def test_open_future_candle_not_used(self):
        coin=deepcopy(self.coin);coin[-1][6]+=1
        result=self.call(coin_closed5=coin)
        self.assertEqual(result["state"],"SOURCE_CENSORED")

    def test_negative_price_not_silent_zero(self):
        coin=deepcopy(self.coin);coin[-1][4]="-99"
        self.assertIsNone(self.call(coin_closed5=coin)["research_setup_candidate"])

    def test_wait_for_first_postwatch_complete_5m(self):
        result=self.call(watch_ms=TICK,deadline_ms=TICK+900_000)
        self.assertEqual(result["state"],"WAIT_POST_WATCH_CLOSED_5M")
        self.assertIsNone(result["research_setup_candidate"])

    def test_no_duplicate_same_closed_bar(self):
        self.assertEqual(self.call(last_reviewed_open_ms=3_300_000)["state"],
                         "SAME_BAR_NO_DUPLICATE")

    def test_expiration_not_extended_for_new_confirmation(self):
        result=self.call(observed_ms=4_320_000)
        self.assertEqual(result["state"],"EXPIRED")

    def test_reject_btc_as_target(self):
        with self.assertRaises(ValueError):
            self.call(symbol="BTCUSDT")

    def test_reject_non_3m_clock(self):
        with self.assertRaises(ValueError):
            self.call(observed_ms=TICK+1)

    def test_invalid_source_candle_quote_censored(self):
        btc=deepcopy(self.btc);btc[-1][7]="0"
        self.assertEqual(self.call(btc_closed5=btc)["state"],"SOURCE_CENSORED")

    def test_exact_zero_relative_strength_inclusive(self):
        # Identical 15m price curves at different nominal prices:
        # 100->112 vs 200->224. Boundary is defined by >= 0.
        btc=bars([200,200,200,208,216,224])
        self.assertTrue(self.call(btc_closed5=btc)["research_setup_candidate"])

    def test_missing_symbol_cannot_sneak_into_eligible_research(self):
        with self.assertRaises(ValueError):
            self.call(symbol="NOTUSDC")


if __name__=="__main__":
    unittest.main()
