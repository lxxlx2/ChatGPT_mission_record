#!/usr/bin/env python3
"""Small isolated SQLite behavioral tests for the real 445 research D1 observer."""
from pathlib import Path
import tempfile
import unittest

import monster_v4_shadow as prod
import monster_v4_445_first_service_trace_replay as trace


class FirstServiceTraceTests(unittest.TestCase):
    def setUp(self):
        self.dir=tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.db=prod.open_store(Path(self.dir.name)/"queue.sqlite")
        self.addCleanup(self.db.close)
        self.t=1770338160000
        with self.db:
            for i in range(9):
                self.db.execute("""
                    INSERT INTO candidate_queue
                    (venue,symbol,first_seen_ms,last_seen_ms,priority,reason,
                     status,attempts,retry_after_ms,deadline_ms)
                    VALUES (?,?,?,?,?,?, 'PENDING',0,0,?)
                """,("spot",f"T{i}USDT",self.t,self.t,99,"FIXTURE",self.t+900000))
        self.obs=trace.FirstServiceObserver()

    def test_01_original_eight_selected_and_ninth_does_not_get_slot(self):
        calls=[]
        def original(store,now,fetch,source_db,*,limit,original_queue,stats):
            calls.append(now)
            selected=store.execute("""
                SELECT id FROM candidate_queue WHERE status='PENDING'
                AND retry_after_ms<=? ORDER BY first_seen_ms,id LIMIT ?
            """,(now,limit)).fetchall()
            with store:
                for x in selected:
                    store.execute("UPDATE candidate_queue SET retry_after_ms=? WHERE id=?",
                                  (now+180000,x["id"]))
            return {"selected":len(selected),"deferred":len(selected),
                    "completed":0,"late":0}
        self.obs.original_handler=original
        self.obs.instrument(self.db,self.t,None,None,limit=8,
                            original_queue=None,stats={})
        self.assertEqual(calls,[self.t])
        self.assertEqual(len(self.obs.slots),8)
        self.assertEqual(self.obs.selected_count,8)
        self.assertEqual(len(self.obs.first_selected),8)
        self.assertEqual(self.obs.busy_ticks[0]["unselected_eligible"],1)
        self.assertNotIn(9,self.obs.first_selected)
        self.assertEqual(self.db.execute(
            "SELECT COUNT(*) FROM candidate_queue WHERE status='PENDING'"
        ).fetchone()[0],9)

    def test_02_repeated_selections_not_counted_as_first_service(self):
        def original(store,now,fetch,source_db,*,limit,original_queue,stats):
            selected=store.execute("""
                SELECT id FROM candidate_queue WHERE status='PENDING'
                AND retry_after_ms<=? ORDER BY first_seen_ms,id LIMIT ?
            """,(now,limit)).fetchall()
            with store:
                for x in selected:
                    store.execute("""
                        UPDATE candidate_queue
                        SET retry_after_ms=?,last_evaluated_bar_ms=?
                        WHERE id=?
                    """,(now+180000,(now if now>self.t else None),x["id"]))
            return {"selected":len(selected),"deferred":len(selected),
                    "completed":0,"late":0}
        self.obs.original_handler=original
        for tick in (self.t,self.t+180000):
            self.obs.instrument(self.db,tick,None,None,limit=8,
                                original_queue=None,stats={})
        self.assertEqual(self.obs.selected_count,16)
        self.assertEqual(len(self.obs.first_selected),8)
        self.assertEqual(sum(v-1 for v in self.obs.slots_by_id.values()),8)
        self.assertEqual(len(self.obs.first_evaluated),8)
        self.assertTrue(all(v==self.t+180000
                            for v in self.obs.first_evaluated.values()))

    def test_03_mismatched_actual_original_selection_fails_closed(self):
        self.obs.original_handler=lambda *args,**kwargs:{
            "selected":9,"deferred":9,"completed":0,"late":0}
        with self.assertRaisesRegex(RuntimeError,"actual_d1_selection_changed"):
            self.obs.instrument(self.db,self.t,None,None,limit=8,
                                original_queue=None,stats={})

    def test_04_final_model_mismatch_does_not_make_trace_success(self):
        model={"execution_counts":{"D1_selected":1},"queue_rows":[]}
        frozen={"execution_counts":{"D1_selected":2},"queue_rows":[]}
        with self.assertRaisesRegex(RuntimeError,"model_drift_execution_counts"):
            trace.summarize_original_trace(model,frozen,self.obs)

    def test_05_original_reference_digest_must_match_before_model(self):
        fake=Path(self.dir.name)/"bad_full.json"
        fake.write_text("{}")
        with self.assertRaisesRegex(RuntimeError,"original_raw_full_SHA_drift"):
            trace.run_trace(Path(self.dir.name),fake)


if __name__=="__main__":
    unittest.main()
