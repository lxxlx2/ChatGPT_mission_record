"""Stage25 event-window chronology, source identity and no trading-label leakage."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
SCRIPT=Path(__file__).parents[1]/"scripts"
if str(SCRIPT) not in sys.path:sys.path.insert(0,str(SCRIPT))
import monster_v4_stage25_event_time_diagnostic as m

def row(threshold,cls,lead=15):
    return {"date":"2026-08-04","symbol":"TUTUSDT",
            "threshold":threshold,"status":"COMPLETE_CAUSAL_1M_REPLAY",
            "classification":cls,"lead_minutes_if_watch":lead}
class SourceCheck(unittest.TestCase):
    def test_only_confirmed_event_first_crossing_not_true_unbiased_fullmarket(self):
        out=m.summary([row(2,"WATCH_BEFORE_OR_AT_FIRST_1M_CROSS"),
           row(5,"NO_WATCH_IN_EVENT_ALIGNED_12H",None),
           row(10,"WATCH_AFTER_FIRST_1M_CROSS",-2)])
        self.assertEqual(out["attempted"],3)
        self.assertEqual(out["by_multiple"]["2x"]["early_or_same_minute"],1)
        self.assertEqual(out["by_multiple"]["5x"]["no_watch_in_aligned_12h"],1)
        self.assertEqual(out["by_multiple"]["10x"]["late"],1)
    def test_original_scorer_blob_lock_constant(self):
        import json
        frozen=json.loads(m.PRE.read_text())
        self.assertEqual(m.git_blob(m.scorer.__file__),frozen["exact_existing_event_scorer_git_blob_sha1"])
        self.assertEqual(m.git_blob(m.production.__file__),frozen["exact_original_production_v4_replayer_git_blob_sha1"])
    def test_incomplete_frozen_source_fails_closed(self):
        with self.assertRaisesRegex(ValueError,"STAGE25_REQUIRE_SIX"):
            m.frozen_original_events([])
    def test_event_outcome_invalid_is_not_no_watch(self):
        x={"date":"2026-08-04","symbol":"TUTUSDT","threshold":2,
           "status":"CENSORED_OR_SOURCE_FAILED","reason":"MISSING_REAL_ARCHIVE"}
        out=m.summary([x])
        self.assertEqual(out["complete"],0)
        self.assertEqual(out["by_multiple"]["2x"]["no_watch_in_aligned_12h"],0)
if __name__=="__main__":
    unittest.main()
