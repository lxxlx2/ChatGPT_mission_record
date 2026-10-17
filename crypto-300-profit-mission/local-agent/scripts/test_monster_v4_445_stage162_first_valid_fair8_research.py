#!/usr/bin/env python3
"""Actual SQLite fairness-selection checks, not evidence of profitable trading."""
import tempfile
import unittest
from pathlib import Path

import monster_v4_shadow as prod
import monster_v4_445_stage162_first_valid_fair8_research as fair


class Stage162ResearchTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store=prod.open_store(Path(self.tmp.name)/"stage162.sqlite")
        self.addCleanup(self.store.close)
        self.t=1770338160000
        self.observer=fair.FairEightObserver()

    def add(self, symbol, first_seen, last_eval=None, retry=0, deadline=None):
        with self.store:
            cursor=self.store.execute("""
                INSERT INTO candidate_queue(
                    venue,symbol,first_seen_ms,last_seen_ms,priority,reason,
                    status,attempts,retry_after_ms,deadline_ms,last_evaluated_bar_ms
                ) VALUES ('spot',?,?,?,99,'TEST','PENDING',0,?,?,?)
            """,(symbol,first_seen,first_seen,retry,
                 first_seen+900000 if deadline is None else deadline,last_eval))
        return cursor.lastrowid

    def original_once(self,store,now,fetch,source_db,*,limit,original_queue,stats):
        rows=store.execute("""
            SELECT id,first_seen_ms FROM candidate_queue WHERE status='PENDING'
            AND retry_after_ms<=? ORDER BY first_seen_ms,id LIMIT ?
        """,(now,limit)).fetchall()
        with store:
            for row in rows:
                store.execute("""
                    UPDATE candidate_queue SET retry_after_ms=?,
                      last_error='NO_SETUP_YET'
                    WHERE id=?
                """,(now+60000,row["id"]))
        return {"selected":len(rows),"deferred":len(rows),
                "completed":0,"late":0}

    def invoke(self,now):
        return self.observer.instrument(self.store,now,None,None,
                    limit=8,original_queue=None,stats={})

    def test_01_qualifying_first_valid_candidates_precede_old_evaluated(self):
        old=self.add("OLDUSDT",self.t-3*60000,last_eval=self.t-5*60000)
        fresh=[self.add(f"X{i}USDT",self.t) for i in range(9)]
        self.observer.real_original_handler=self.original_once
        result=self.invoke(self.t+6*60000)
        self.assertEqual(result["selected"],8)
        self.assertEqual({q["id"] for q in self.observer.slots},set(fresh[:8]))
        self.assertNotIn(old,self.observer.first_selected)
        self.assertNotIn(fresh[8],self.observer.first_selected)
        self.assertEqual(self.store.execute("""
            SELECT retry_after_ms FROM candidate_queue WHERE id=?
        """,(old,)).fetchone()[0],0)
        self.assertEqual(self.observer.busy_ticks[0]["first_mature_fair_priority"],8)

    def test_02_before_postwatch_bar_close_same_oldest_FIFO(self):
        old=self.add("OLDUSDT",self.t-3*60000,last_eval=self.t-5*60000)
        fresh=[self.add(f"X{i}USDT",self.t) for i in range(9)]
        eligible=[dict(r) for r in self.store.execute(
            "SELECT * FROM candidate_queue ORDER BY first_seen_ms,id")]
        early=fair.plan_eligible_eight(eligible,self.t+3*60000)
        self.assertEqual([q["id"] for q in early],[old]+fresh[:7])
        later=fair.plan_eligible_eight(eligible,self.t+6*60000)
        self.assertEqual([q["id"] for q in later],fresh[:8])
        self.assertFalse(fair.first_valid_post_watch_closed_bar(self.t+3*60000,self.t))
        self.assertTrue(fair.first_valid_post_watch_closed_bar(self.t+6*60000,self.t))

    def test_03_expired_must_not_be_priority_eligible_first_valid(self):
        old=self.add("EXPIRED",self.t-12*60000,deadline=self.t)
        new=self.add("NEW",self.t)
        eligible=[dict(r) for r in self.store.execute(
            "SELECT * FROM candidate_queue ORDER BY first_seen_ms,id")]
        planned=fair.plan_eligible_eight(eligible,self.t+6*60000)
        self.assertEqual([q["id"] for q in planned],[new,old])

    def test_04_eight_slot_upper_bound_fails_closed(self):
        self.add("M1",self.t)
        xs=[dict(r) for r in self.store.execute(
            "SELECT * FROM candidate_queue")]
        with self.assertRaisesRegex(ValueError,"CAPACITY_CHANGED"):
            fair.plan_eligible_eight(xs,self.t+6*60000,capacity=9)
        xs[0]["retry_after_ms"]=self.t+99*60000
        with self.assertRaisesRegex(ValueError,"NOT_A_REAL_NOW_ELIGIBLE"):
            fair.plan_eligible_eight(xs,self.t)

    def test_05_exception_restores_all_masked_nonselected_rows(self):
        old=self.add("OLDUSDT",self.t-3*60000,last_eval=self.t-5*60000)
        for i in range(9):
            self.add(f"X{i}USDT",self.t)
        before=[dict(q) for q in self.store.execute("SELECT * FROM candidate_queue")]
        def fail(*args,**kwargs):
            raise RuntimeError("synthetic handler failed")
        self.observer.real_original_handler=fail
        with self.assertRaisesRegex(RuntimeError,"synthetic handler failed"):
            self.invoke(self.t+6*60000)
        after=[dict(q) for q in self.store.execute("SELECT * FROM candidate_queue")]
        self.assertEqual(before,after)
        self.assertEqual(self.observer.selected_total,0)

    def test_06_nonselected_mutation_does_not_get_attributed_to_selected(self):
        old=self.add("OLDUSDT",self.t-3*60000,last_eval=self.t-5*60000)
        for i in range(9):
            self.add(f"X{i}USDT",self.t)
        def original(store,now,fetch,source_db,*,limit,original_queue,stats):
            normal=self.original_once(store,now,fetch,source_db,limit=limit,
                                       original_queue=original_queue,stats=stats)
            with store:
                store.execute("""
                    UPDATE candidate_queue SET last_error='UNAUTHORIZED' WHERE id=?
                """,(old,))
            return normal
        self.observer.real_original_handler=original
        with self.assertRaisesRegex(RuntimeError,"NONSELECTED_DURABLE_ROW_MUTATED"):
            self.invoke(self.t+6*60000)

    def test_07_repeats_and_first_valid_bar_are_observed_not_inferred(self):
        for i in range(8):
            self.add(f"X{i}USDT",self.t)
        def original(store,now,fetch,source_db,*,limit,original_queue,stats):
            rows=store.execute("""
                SELECT id FROM candidate_queue WHERE status='PENDING'
                AND retry_after_ms<=? ORDER BY first_seen_ms,id LIMIT ?
            """,(now,limit)).fetchall()
            with store:
                for q in rows:
                    store.execute("""
                        UPDATE candidate_queue SET retry_after_ms=?,
                            last_evaluated_bar_ms=?
                        WHERE id=?
                    """,(now+60000,now-5*60000,q["id"]))
            return {"selected":len(rows),"deferred":len(rows),
                    "completed":0,"late":0}
        self.observer.real_original_handler=original
        self.invoke(self.t+6*60000)
        self.invoke(self.t+9*60000)
        self.assertEqual(len(self.observer.first_evaluated),8)
        self.assertEqual(self.observer.selected_total,16)
        self.assertEqual(self.observer.repeats_advanced,8)
        self.assertEqual(self.observer.repeats_no_progress,0)


    def build_synthetic_full_269_research_report(self):
        # End-to-end report path: immutable-like 269 WATCH + 120 SETUP
        # without any claim that these invented symbols are original evidence.
        frozen=[]
        watches=[]
        setups=[]
        service=[]
        for i in range(269):
            seen=fair.PEAK_MS if i<98 else fair.PEAK_MS-24*60*60000-i*60000
            q={"id":i+1,"venue":"spot","symbol":f"SYN{i:03d}USDT",
               "first_seen_ms":seen,"deadline_ms":seen+900000,
               "status":"EVALUATED"}
            frozen.append(q)
            watches.append({"event_type":"WATCH_EARLY","event_id":f"watch_{i}",
                            "symbol":q["symbol"],"observed_ms":seen})
            if i<120:
                setups.append({"event_type":"SETUP_ACTIVE","event_id":f"setup_{i}",
                               "symbol":q["symbol"],"observed_ms":seen+360000})
            service.append({"id":q["id"],"first_selected_ms":seen,
                            "first_evaluation_ms":seen+360000})
        before={"actually_complete_symbols":445,"queue_rows":frozen,
                "events":watches+setups}
        after={**before,"date":"2026-02-04",
               "execution_counts":{"polls":3360,"D1_selected":269},
               "event_type_counts":{},"queue_status_counts":{}}
        baseline={"D1_global_selected_slots":753,
                  "D1_first_selection_slots":269,
                  "D1_repeated_selection_slots":484,
                  "original_V2_every_event_and_queue_byte_semantics_equal":True,
                  "frozen_original_full_json_sha256":fair.REFERENCE_SHA,
                  "candidate_first_service":service}
        observer=fair.FairEightObserver()
        observer.ticks=3360
        observer.selected_total=269
        observer.slots=[{"id":x["id"]} for x in frozen]
        observer.first_selected={x["id"]:x["first_seen_ms"] for x in frozen}
        observer.first_evaluated={x["id"]:x["first_seen_ms"]+360000 for x in frozen}
        observer.busy_ticks=[
            {"selected_ids":[q["id"] for q in frozen[i:i+8]]}
            for i in range(0,269,8)]
        return before,after,baseline,observer

    def test_08_real_report_builder_does_not_shadow_baseline_trace(self):
        before,after,baseline,observer=self.build_synthetic_full_269_research_report()
        j=fair.build_report(after,observer,before,baseline)
        self.assertEqual(j["baseline_d1_selections"],753)
        self.assertEqual(j["setup_event_id_baseline"],120)
        self.assertEqual(j["setup_event_id_alternative"],120)
        self.assertEqual(j["setup_guardrail"],"PASS_NO_LOSS")
        self.assertEqual(j["cohort_comparison"]["PEAK_98"]["watch"],98)
        self.assertEqual(j["cohort_comparison"]["OTHER_171"]["watch"],171)

    def test_09_report_discloses_lost_original_setup_and_stays_no_go(self):
        before,after,baseline,observer=self.build_synthetic_full_269_research_report()
        after={**after,"events":[x for x in after["events"]
                                if x["event_id"]!="setup_110"]}
        j=fair.build_report(after,observer,before,baseline)
        self.assertEqual(j["setup_lost_ids"],1)
        self.assertEqual(j["setup_retained_ids"],119)
        self.assertEqual(j["setup_guardrail"],"NO_GO_LOST_EXISTING_SETUPS")
        self.assertEqual(j["cohort_comparison"]["OTHER_171"]["lost_setups"],1)


if __name__=="__main__":
    unittest.main()
