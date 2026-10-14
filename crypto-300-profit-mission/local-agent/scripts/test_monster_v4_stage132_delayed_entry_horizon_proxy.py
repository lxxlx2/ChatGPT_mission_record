import json
import os
from decimal import Decimal
from pathlib import Path
import tempfile
import unittest

import monster_v4_stage132_delayed_entry_horizon_proxy as m


def make_rows(n=1500):
    start=m.epoch("2025-01-25T00:00:00Z")
    rows=[]
    for i in range(n):
        base=Decimal("1")
        rows.append((start+i*m.MIN,base,Decimal("1.02"),Decimal("0.99"),base))
    return rows


class Stage132Test(unittest.TestCase):
    def test_fixed_one_minute_delay_and_all_four_fixed_horizons(self):
        bars=make_rows()
        signal=m.utc(bars[3][0])
        result=m.paths(bars,signal)
        self.assertEqual(result["entry_utc"],m.utc(bars[4][0]))
        self.assertEqual(result["entry_open"],"1")
        for h in m.HORIZONS:
            x=result["horizons"][str(h)]
            self.assertEqual(x["status"],"VALID_GROSS_OPEN_TO_OPEN_PRICE_ONLY")
            self.assertEqual(x["exit_utc"],m.utc(bars[4+h][0]))
            self.assertEqual(Decimal(x["gross_return_pct"]),Decimal("0"))
            self.assertEqual(Decimal(x["MAE_low_pct"]),Decimal("-1"))

    def test_future_high_or_low_beyond_exit_does_not_change_prior_horizon(self):
        bars=make_rows()
        first=m.paths(bars,m.utc(bars[3][0]))["horizons"]["15"]
        changed=list(bars)
        t,_,_,_,c=changed[19]
        changed[19]=(t,Decimal("1"),Decimal("1000"),Decimal("0.00001"),c)
        second=m.paths(changed,m.utc(bars[3][0]))["horizons"]["15"]
        self.assertEqual(first,second)

    def test_right_censor_at_original_fixed_window_end(self):
        bars=make_rows(30)
        r=m.paths(bars,m.utc(bars[26][0]))
        self.assertEqual(r["horizons"]["15"]["status"],"RIGHT_CENSORED_SOURCE_END")
        self.assertEqual(r["horizons"]["60"]["status"],"RIGHT_CENSORED_SOURCE_END")

    def test_gapped_or_non_finite_prices_refused(self):
        rows=make_rows(10)
        broken=rows[:3]+rows[4:]
        with self.assertRaisesRegex(ValueError,"GAPPED"):
            m.paths(broken,m.utc(rows[0][0]))
        with self.assertRaisesRegex(ValueError,"INVALID_SOURCE_PRICE"):
            m.positive("NaN")

    def test_full_source_sha_gate_is_immutable(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"stage130_real31.json"
            p.write_text("{}")
            with self.assertRaisesRegex(ValueError,"CHANGED"):
                m.audit(td)

    def test_real_full31_source_and_unmodified_g4_when_supplied(self):
        root=os.environ.get("MONSTER_STAGE130_SOURCE_ROOT")
        if not root:
            self.skipTest("Original publisher artifact not supplied to local unit-test context")
        data=m.audit(root)
        self.assertEqual(data["full_original_attempts"],31)
        self.assertEqual(data["first_unique_momentum_signals"],19)
        self.assertEqual(data["no_momentum_signal_attempts"],12)
        self.assertEqual(data["frozen_stage130_publisher_zip_pairs_verified"],147)
        self.assertEqual(data["full_minute_bars_verified"],159675)
        self.assertEqual(data["G4_actual_executable_net"],"UNKNOWN")
        self.assertEqual(data["Monster_deployment"],"NO_GO")
        self.assertEqual([data["horizon_stats"][str(h)]["valid"] for h in m.HORIZONS],[19,19,19,15])
        self.assertEqual([data["horizon_stats"][str(h)]["positive"] for h in m.HORIZONS],[6,6,5,4])
        self.assertEqual(len(data["all_original_31_rows"]),31)
        self.assertTrue(all(not x["issuer_point_in_time_verified"] for x in data["all_original_31_rows"]))


if __name__=="__main__":
    unittest.main()
