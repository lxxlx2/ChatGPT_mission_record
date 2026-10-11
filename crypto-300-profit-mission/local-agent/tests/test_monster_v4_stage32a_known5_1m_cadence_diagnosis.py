"""Stage32a old winners cannot be reported as new market validation."""
import sys
import unittest
from pathlib import Path
S=Path(__file__).parents[1]/"scripts"
if str(S) not in sys.path:sys.path.insert(0,str(S))
import monster_v4_stage32a_known5_1m_cadence_diagnosis as m
class Tests(unittest.TestCase):
    def test_partial_cohort_fails_closed(self):
        with self.assertRaisesRegex(ValueError,"REQUIRE_ALL18"):
            m.run([])
    def test_name_and_frozen_five_do_not_contain_new_winners(self):
        source=m.stage31.contract()
        self.assertEqual({x["symbol"] for x in source["frozen_cases"]},
                         {"PENGUUSDT","CETUSUSDT","VTHOUSDT","ALPACAUSDT","SPKUSDT"})
        self.assertEqual(len(source["frozen_cases"]),5)
    def test_stage32_model_still_no_go(self):
        d=m.trial.frozen()
        self.assertEqual(d["deploy"],"NO_GO")
if __name__=="__main__":unittest.main()
