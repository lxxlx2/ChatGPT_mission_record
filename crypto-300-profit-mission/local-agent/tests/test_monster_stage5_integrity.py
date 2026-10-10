"""Reproducibility and tamper-resistance tests for Stage5 historical cohort output."""
import csv
import importlib.util
import shutil
import tempfile
import unittest
from pathlib import Path

SCRIPT=Path(__file__).resolve().parents[1]/"scripts/monster_stage5_integrity.py"
spec=importlib.util.spec_from_file_location("monster_stage5_integrity",SCRIPT)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class Stage5IntegrityTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.home=Path(self.tmp.name)
        for name in (mod.BASELINE,mod.FULL,mod.SHORT):
            shutil.copy2(mod.EVIDENCE/name,self.home/name)
    def tearDown(self):
        self.tmp.cleanup()
    def mutate(self,name,callback):
        path=self.home/name
        with path.open(newline="") as f:
            r=csv.DictReader(f)
            columns=r.fieldnames
            rows=list(r)
        callback(rows)
        with path.open("w",newline="") as f:
            w=csv.DictWriter(f,fieldnames=columns)
            w.writeheader()
            w.writerows(rows)

    def test_all_60_identity_and_18_partial_histories_pass(self):
        report=mod.validate(self.home)
        self.assertEqual(report["frozen_total"],60)
        self.assertEqual(report["short_rows"],18)
        self.assertEqual(report["full_24h_valid"],
            {"FULLMARKET_SAMPLED":20,"GT5X_PREHIT_POSITIVE":22})
        self.assertEqual(report["short_listing_recovered"],
            {"FULLMARKET_SAMPLED":10,"GT5X_PREHIT_POSITIVE":8})

    def test_reject_missing_short_listing_row(self):
        self.mutate(mod.SHORT,lambda r:r.pop())
        with self.assertRaisesRegex(ValueError,"UNEXPECTED_FROZEN_COUNTS"):
            mod.validate(self.home)

    def test_reject_modified_historical_outcome(self):
        self.mutate(mod.FULL,lambda r:r[0].__setitem__("now_ret24_pct","999"))
        with self.assertRaisesRegex(ValueError,"OUTCOME_SOURCE_MISMATCH"):
            mod.validate(self.home)

    def test_reject_future_labels_rewritten(self):
        self.mutate(mod.FULL,lambda r:r[30].__setitem__("gt_maxclose_x","500"))
        with self.assertRaisesRegex(ValueError,"FUTURE_LABEL_CHANGED"):
            mod.validate(self.home)

    def test_reject_fake_complete_baseline_for_new_listing(self):
        self.mutate(mod.FULL,lambda r:r[20].__setitem__("ret4_pct","0"))
        with self.assertRaisesRegex(ValueError,"SHORT_HISTORY_SHOULD_NOT_PRETEND_FULL24"):
            mod.validate(self.home)

    def test_reject_invented_four_hour_return_from_two_hours(self):
        def change(rows):
            x=next(x for x in rows if x["symbol"]=="MMTUSDT")
            self.assertEqual(x["available_closed_hours"],"2")
            x["ret4_pct"]="3.0"
        self.mutate(mod.SHORT,change)
        with self.assertRaisesRegex(ValueError,"INVENTED_INSUFFICIENT_SHORT_HISTORY"):
            mod.validate(self.home)

    def test_reject_bad_btc_relative_arithmetic(self):
        self.mutate(mod.FULL,lambda r:r[0].__setitem__("relative1_pct","-900"))
        with self.assertRaisesRegex(ValueError,"BTC_RELATIVE_ARITHMETIC_MISMATCH"):
            mod.validate(self.home)

    def test_reject_duplicate_event_key(self):
        self.mutate(mod.FULL,lambda r:r[1].update(
            {k:r[0][k] for k in mod.IDENTITY}))
        with self.assertRaisesRegex(ValueError,"STAGE5_DUPLICATE_OR_INCOMPLETE_IDENTITY"):
            mod.validate(self.home)

if __name__=="__main__":
    unittest.main()
