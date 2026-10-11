"""Stage32 source provenance only from completed original 36 successful GitHub jobs."""
import json
import sys
import unittest
from pathlib import Path
S=Path(__file__).parents[1]/"scripts"
if str(S) not in sys.path:sys.path.insert(0,str(S))
import monster_v4_stage32_make_real_source_proof as m

class Provenance(unittest.TestCase):
    def test_frozen_source_ci_id_and_commit(self):
        self.assertEqual(m.SOURCE_RUN,38158924838)
        self.assertEqual(m.SOURCE_COMMIT,"75ca627579cddb6b8220f7e1da36f2786cce2da6")
    def test_workflow_not_completed_fail_closed(self):
        f=lambda _:json.dumps({"status":"in_progress","conclusion":None}).encode()
        with self.assertRaisesRegex(ValueError,"NOT_COMPLETE_SOURCE_CI"):
            m.collect(f)
    def test_wrong_code_sha_not_a_real_source_proof(self):
        f=lambda _:json.dumps({"status":"completed","conclusion":"success","head_sha":"bad"}).encode()
        with self.assertRaisesRegex(ValueError,"CHANGED_POST_REGISTRATION"):
            m.collect(f)
    def test_missing_artifacts_not_full_universe(self):
        def f(url):
            if "artifacts" in url:return json.dumps({"total_count":35,"artifacts":[]}).encode()
            return json.dumps({"status":"completed","conclusion":"success","head_sha":m.SOURCE_COMMIT}).encode()
        with self.assertRaisesRegex(ValueError,"NOT_COMPLETE36_REAL_CI_ARTIFACTS"):
            m.collect(f)
if __name__=="__main__":unittest.main()
