"""Stage30 all real source ZIP SHA provenance must fail before pretending any heldout replay success."""
import json
import sys
import unittest
from pathlib import Path
S=Path(__file__).parents[1]/"scripts"
if str(S) not in sys.path:sys.path.insert(0,str(S))
import monster_v4_stage30_make_real_source_proof as m

class Provenance(unittest.TestCase):
    def test_fixed_real_source_run_and_six_new_dates(self):
        self.assertEqual(m.RUN,38154393594)
        self.assertEqual(m.DATES,("2025-01-19","2025-04-19","2025-07-19","2025-10-19","2026-04-19","2026-07-19"))
    def test_cannot_accept_inprogress_as_success(self):
        def fake(p):
            return json.dumps({"status":"in_progress","conclusion":None}).encode()
        with self.assertRaisesRegex(ValueError,"SOURCE_RUN_NOT_COMPLETE_SUCCESS"):
            m.prove(get=fake)
    def test_cannot_replay_other_source_commit_as_authorized(self):
        def fake(p):
            return json.dumps({"status":"completed","conclusion":"success","head_sha":"different"}).encode()
        with self.assertRaisesRegex(ValueError,"PRECOMMITTED_SOURCE_HEAD_CHANGED"):
            m.prove(get=fake)
    def test_cannot_call_less_than_all_36_artifacts_full_market(self):
        def fake(p):
            if p.startswith("actions/runs/38154393594/artifacts"):
                return json.dumps({"total_count":12,"artifacts":[]}).encode()
            return json.dumps({"status":"completed","conclusion":"success","head_sha":m.SOURCE_COMMIT}).encode()
        with self.assertRaisesRegex(ValueError,"NOT_ALL_36_ARTIFACTS"):
            m.prove(get=fake)
if __name__=="__main__":unittest.main()
