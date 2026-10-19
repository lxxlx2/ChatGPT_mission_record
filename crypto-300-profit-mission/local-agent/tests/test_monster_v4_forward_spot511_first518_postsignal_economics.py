"""Frozen first518 short price study: temporal leakage and cohort guardrails."""
import sys
import unittest
from decimal import Decimal
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import monster_v4_forward_spot511_first518_postsignal_economics as study


class FrozenPriceEconomicsTests(unittest.TestCase):
    def fixture(self):
        start=study.bridge.START-120*study.MIN_MS
        return [
            (start+i*study.MIN_MS,Decimal(1),Decimal(1),Decimal(1),
             Decimal(1)+(Decimal(i)/10000),Decimal(1000),10)
            for i in range(400)]

    def test_exact_original_eight_eight_event_inventory(self):
        watch,setup=study.event_inventory()
        self.assertEqual(len(watch),8)
        self.assertEqual(len(setup),8)
        self.assertEqual(len({x["symbol"] for x in watch}),8)
        self.assertEqual(len({x["symbol"] for x in setup}),8)

    def test_entry_exit_unclosed_volume_cannot_change_preadmission(self):
        bars=self.fixture()
        when=study.bridge.START
        base=study.evaluate(bars,when,15)
        self.assertEqual(base["status"],"OFFICIAL_1M_PRICE_PROXY_ONLY")
        entryi=(when+3*study.MIN_MS-bars[0][0])//study.MIN_MS
        exiti=entryi+15
        changed=list(bars)
        for i in (entryi,exiti):
            t,o,h,l,c,q,tr=changed[i]
            changed[i]=(t,o,h,l,c,Decimal(0),0)
        self.assertEqual(study.evaluate(changed,when,15),base)

    def test_closed_preentry_zero_censors(self):
        bars=self.fixture()
        when=study.bridge.START
        i=(when+3*study.MIN_MS-bars[0][0])//study.MIN_MS
        changed=list(bars)
        t,o,h,l,c,q,tr=changed[i-1]
        changed[i-1]=(t,o,h,l,c,Decimal(0),0)
        self.assertEqual(study.evaluate(changed,when,15)["status"],
                         "CENSORED_PREENTRY_ZERO_TRADES_OR_QUOTE")

    def test_missing_future_exits_are_censored_not_zero_return(self):
        bars=self.fixture()
        r=study.evaluate(bars,study.bridge.START,1440)
        self.assertEqual(r,{"status":"CENSORED_EXIT_SOURCE_NOT_AVAILABLE"})

    def test_fixed_horizon_only(self):
        with self.assertRaisesRegex(ValueError,"UNFROZEN_HOLD_HORIZON"):
            study.evaluate(self.fixture(),study.bridge.START,27)

    def test_summary_requires_all_eight_not_winner_subset(self):
        with self.assertRaisesRegex(ValueError,"ALL8_DENOMINATOR"):
            study.describe([{"result":{"status":"CENSORED_EXIT_SOURCE_NOT_AVAILABLE"}}])

if __name__=="__main__":
    unittest.main()
