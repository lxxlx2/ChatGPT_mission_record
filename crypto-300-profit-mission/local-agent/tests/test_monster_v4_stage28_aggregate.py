"""Stage28 six original SHA artifact global D1 outcome denominator safeguards."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
SCRIPTS=Path(__file__).parents[1]/"scripts"
if str(SCRIPTS) not in sys.path:sys.path.insert(0,str(SCRIPTS))
import monster_v4_stage28_aggregate as a

def mock(day,watches,setups,independent):
    return {"date":day,"watch_arrivals":watches,
      "original_stage26_individual_D1_setups":independent,
      "queue_candidates":watches,
      "setups":[{"symbol":"S"+str(i)+"USDT","utc":day+"T12:00:00Z"} for i in range(setups)],
      "late_events":[],
      "source_5m_official_SHA256":[{"date":day,"sha256":"a"*64}],
      "production_processor_selected_total":watches,
      "production_processor_deferred_total":watches//2,
      "candidate_status_counts":{"EVALUATED":watches},
      "max_pending_before_poll":watches}

class Aggregation(unittest.TestCase):
    def test_no_one_or_two_dates_only(self):
        with self.assertRaisesRegex(ValueError,"EXACTLY_SIX"):
            a.summarize({a.DATES[0]:mock(a.DATES[0],1,0,0)})
    def test_all_1132_watch_and_826_old_setups_hard_locked(self):
        old=[260,133,269,181,182,107]
        individual=[219,1,2,3,4,5]
        individual[-1]+=826-sum(individual)
        reports={d:mock(d,w,i//3,i) for d,w,i in zip(a.DATES,old,individual)}
        result=a.summarize(reports)
        self.assertEqual(result["source_original_WATCH_count"],1132)
        self.assertEqual(result["source_original_individual_SQLite_D1_SETUPS"],826)
        self.assertEqual(result["date_count"],6)
        self.assertFalse(result["deployment"]!="NO_GO")
    def test_changed_watches_cannot_fake_success(self):
        old=[260,133,269,181,182,108]
        individual=[219,100,150,120,130,107]
        reports={d:mock(d,w,0,i) for d,w,i in zip(a.DATES,old,individual)}
        with self.assertRaisesRegex(ValueError,"ORIGINAL_SOURCE_EVENTS_CHANGED"):
            a.summarize(reports)
    def test_real_result_must_not_claim_full_D0(self):
        self.assertEqual(a.DATES[0],"2025-11-04")
        self.assertEqual(len(a.DATES),6)
    def test_sha_changed_rejected_before_json_loaded(self):
        import tempfile,zipfile
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"bad.zip"
            with zipfile.ZipFile(p,"w") as z:z.writestr("not_right.json","{}")
            with self.assertRaisesRegex(ValueError,"ORIGINAL_ZIP_SHA256_CHANGED"):
                a.read_artifact(p,{"date":"2025-11-04","zip_sha256":"a"*64})

if __name__=="__main__":unittest.main()
