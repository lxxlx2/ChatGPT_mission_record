#!/usr/bin/env python3
"""Offline Stage153 D1 queue incident and read-only pressure regressions."""
import hashlib
import json
from contextlib import redirect_stdout
from datetime import datetime, timezone
from io import StringIO
from unittest.mock import patch
import sys
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest
import zipfile

import monster_v4_stage153_source_locked_d1_queue_lifecycle as m


def queue_db():
    db=sqlite3.connect(":memory:")
    db.execute("""CREATE TABLE candidate_queue(
        id INTEGER PRIMARY KEY,venue TEXT,symbol TEXT,
        first_seen_ms INTEGER,deadline_ms INTEGER,retry_after_ms INTEGER,
        last_evaluated_bar_ms INTEGER,attempts INTEGER,status TEXT)""")
    return db


def add_pending(db, n=98, *, start=1_800_000_000_000):
    for i in range(n):
        db.execute("""INSERT INTO candidate_queue VALUES
            (?,?,?,?,?,?,?,?,?)""",(i+1,"spot",f"S{i}USDT",
            start,start+15*m.MIN,0,None,0,"PENDING"))


def tiny_day(date="2026-02-04"):
    epoch=1_800_000_000_000
    return {"schema":"MONSTER_STAGE28_ACTUAL_PRODUCTION_SHARED_SQLITE_D1_WITH_FROZEN_WATCH_V1",
            "date":date,"actual_shared_sqlite_process_queue":True,
            "global_observe_snapshot_replayed":False,
            "D0_invalidation_event_injection":False,
            "actual_real_money_order_or_email":False,
            "watch_arrivals":2,
            "original_stage26_individual_D1_setups":1,
            "setups":[{"symbol":"AUSDT","utc":datetime.fromtimestamp((epoch+6*m.MIN)/1000, timezone.utc).isoformat().replace("+00:00","Z")}],
            "late_events":[{"symbol":"BUSDT","observed_ms":epoch+16*m.MIN,
                "payload":{"classification":"STALE_NOT_ACTIONABLE",
                           "first_seen_ms":epoch,"deadline_ms":epoch+15*m.MIN}}],
            "source_5m_official_SHA256":[],"queue_candidates":2,
            "pending_at_end":0,
            "candidate_status_counts":{"EVALUATED":1,"LATE":1},
            "event_counts":{"WATCH_EARLY":2,"SETUP_ACTIVE":1,
                            "LATE_REVIEW":1},
            "production_processor_selected_total":5,
            "production_processor_deferred_total":3,
            "max_pending_before_poll":2,
            "queue_final":[
                {"id":1,"venue":"spot","symbol":"AUSDT",
                 "first_seen_ms":epoch,"deadline_ms":epoch+15*m.MIN,
                 "status":"EVALUATED","attempts":0,"last_error":None,
                 "last_evaluated_bar_ms":epoch+5*m.MIN,
                 "retry_after_ms":epoch},
                {"id":2,"venue":"spot","symbol":"BUSDT",
                 "first_seen_ms":epoch,"deadline_ms":epoch+15*m.MIN,
                 "status":"LATE","attempts":1,"last_error":"bad_data",
                 "last_evaluated_bar_ms":None,"retry_after_ms":epoch+m.MIN}]}


def mini_zip(tmp, data, date="2026-02-04"):
    name=f"monster_stage28_{date}_real_shared_sqlite.json"
    zpath=Path(tmp)/f"monster_stage28_{date}_real_shared_sqlite.zip"
    raw=json.dumps(data,sort_keys=True).encode()
    with zipfile.ZipFile(zpath,"w") as z:
        z.writestr(name,raw)
    rec={"date":date,"zip_sha256":hashlib.sha256(zpath.read_bytes()).hexdigest(),
         "raw_json_sha256":hashlib.sha256(raw).hexdigest(),
         "original_watch_arrivals":2,"original_individual_setups":1,
         "real_shared_setups":1,"late":1,"official_5m_publisher_sha_source_count":0}
    return zpath,rec


class Stage153Tests(unittest.TestCase):
    def test_frozen_real_stage28_proof_counts_and_dates(self):
        p=m.source_proof()
        self.assertEqual(p["original_watch_events"],1132)
        self.assertEqual(len(p["artifacts"]),6)
        self.assertEqual(p["feb2026_burst"]["actual_LATE"],91)

    def test_original_zip_and_json_both_hash_locked(self):
        with tempfile.TemporaryDirectory() as d:
            z,rec=mini_zip(d,tiny_day())
            real=m.read_actual_artifact(z,rec)
            self.assertEqual(real["watch_arrivals"],2)
            other=dict(rec,zip_sha256="0"*64)
            with self.assertRaisesRegex(ValueError,"ZIP_SHA"):
                m.read_actual_artifact(z,other)
            other=dict(rec,raw_json_sha256="0"*64)
            with self.assertRaisesRegex(ValueError,"JSON_SHA"):
                m.read_actual_artifact(z,other)

    def test_actual_shared_queue_accounting(self):
        with tempfile.TemporaryDirectory() as d:
            z,rec=mini_zip(d,tiny_day())
            s,rows=m.audit_day(m.read_actual_artifact(z,rec),rec)
            self.assertEqual(s["D1_LATE_REVIEW"],1)
            self.assertEqual(s["LATE_without_completed_D1_5m_bar"],1)
            self.assertEqual(s["LATE_with_http_or_retry_attempts"],1)
            self.assertEqual(len(rows),2)
            self.assertFalse(rows[1]["successful_completed_5m_evaluation_observed"])
            self.assertEqual(rows[0]["first_evaluation_clock_time"],
                             "UNKNOWN_NOT_IN_STAGE28_FINAL_ROW")

    def test_late_event_missing_cannot_hide(self):
        with tempfile.TemporaryDirectory() as d:
            day=tiny_day()
            z,rec=mini_zip(d,day)
            broken=json.loads(json.dumps(day))
            broken["late_events"][0]["symbol"]="OTHERUSDT"
            with self.assertRaisesRegex(ValueError,"UNMATCHED_QUEUE"):
                m.audit_day(broken,rec)
            broken=json.loads(json.dumps(day))
            broken["queue_final"][1]["last_evaluated_bar_ms"]=12345
            with self.assertRaisesRegex(ValueError,"LATE_WITH_RECORDED"):
                m.audit_day(broken,rec)

    def test_duplicate_queue_candidate_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            day=tiny_day()
            z,rec=mini_zip(d,day)
            day["queue_final"][1]["id"]=1
            day["queue_final"][1]["symbol"]="AUSDT"
            day["queue_final"][1]["first_seen_ms"]=day["queue_final"][0]["first_seen_ms"]
            with self.assertRaisesRegex(ValueError,"DUPLICATED"):
                m.audit_day(day,rec)

    def test_98_same_poll_all_visible_and_pressure_bound(self):
        db=queue_db()
        at=1_800_000_000_000
        add_pending(db,98,start=at)
        h=m.queue_pressure(db,at)
        self.assertEqual(h["PENDING"],98)
        self.assertEqual(h["PENDING_never_recorded_completed_D1_5m"],98)
        self.assertEqual(h["PENDING_eligible_retry_asof"],98)
        self.assertEqual(h["new_unreviewed_due_by_15m"],98)
        self.assertEqual(h["at_least_unreviewed_cannot_all_fit_in_6_polls"],50)
        self.assertEqual(h["optimistic_capacity_in_at_most_6_polls_8_each"],48)
        self.assertEqual(db.execute("SELECT COUNT(*) FROM candidate_queue").fetchone()[0],98)
        db.close()

    def test_pending_due_retry_overdue_and_completed_bar(self):
        db=queue_db()
        at=1_800_000_000_000
        add_pending(db,5,start=at)
        db.execute("UPDATE candidate_queue SET retry_after_ms=? WHERE id IN(1,2)",
                   (at+300_000,))
        db.execute("UPDATE candidate_queue SET last_evaluated_bar_ms=? WHERE id=3",
                   (at-300_000,))
        db.execute("UPDATE candidate_queue SET deadline_ms=? WHERE id=4",
                   (at-1,))
        h=m.queue_pressure(db,at)
        self.assertEqual(h["PENDING_in_retry_backoff"],2)
        self.assertEqual(h["PENDING_with_completed_D1_5m"],1)
        self.assertEqual(h["PENDING_already_over_deadline"],1)
        self.assertEqual(h["PENDING_due_in_3m_including_overdue"],1)
        self.assertEqual(h["nearest_deadline_remaining_ms"],-1)
        self.assertEqual(h["PENDING"],5)
        db.close()

    def test_not_pending_excluded_and_invalid_clock_rejected(self):
        db=queue_db()
        at=1_800_000_000_000
        add_pending(db,3,start=at)
        db.execute("UPDATE candidate_queue SET status='LATE' WHERE id=2")
        self.assertEqual(m.queue_pressure(db,at)["PENDING"],2)
        for bad in (0,-1,1.0,"x"):
            with self.assertRaisesRegex(ValueError,"INVALID_ASOF"):
                m.queue_pressure(db,bad)
        db.close()

    def test_actual_file_readonly_connection_never_mutates(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"queue.db"
            db=sqlite3.connect(path)
            db.execute("""CREATE TABLE candidate_queue(
                first_seen_ms INTEGER,deadline_ms INTEGER,
                retry_after_ms INTEGER,last_evaluated_bar_ms INTEGER,
                attempts INTEGER,venue TEXT,symbol TEXT,status TEXT)""")
            db.execute("""INSERT INTO candidate_queue VALUES
                (?,?,?,?,?,?,?,?)""",
                (1_800_000_000_000,1_800_000_900_000,0,None,0,
                 "spot","TESTUSDT","PENDING"))
            db.commit()
            db.close()
            original=path.read_bytes()
            uri=path.resolve().as_uri()+"?mode=ro"
            with sqlite3.connect(uri,uri=True) as ro:
                ro.execute("PRAGMA query_only=ON")
                self.assertEqual(m.queue_pressure(ro,1_800_000_000_000)["PENDING"],1)
                with self.assertRaises(sqlite3.OperationalError):
                    ro.execute("UPDATE candidate_queue SET status='LATE'")
            self.assertEqual(path.read_bytes(),original)


    def test_readonly_cli_refuses_sqlite_main_relative_symlink_hardlink(self):
        with tempfile.TemporaryDirectory() as root:
            folder=Path(root)
            db_path=folder/"source.sqlite"
            db=sqlite3.connect(db_path)
            db.execute("""CREATE TABLE candidate_queue(
                first_seen_ms INTEGER,deadline_ms INTEGER,
                retry_after_ms INTEGER,last_evaluated_bar_ms INTEGER,
                attempts INTEGER,venue TEXT,symbol TEXT,status TEXT)""")
            db.execute("INSERT INTO candidate_queue VALUES(?,?,?,?,?,?,?,?)",
                (1_800_000_000_000,1_800_000_900_000,0,None,0,
                 "spot","TESTUSDT","PENDING"))
            db.commit()
            db.close()
            original=db_path.read_bytes()
            symlink=folder/"linked.db"
            symlink.symlink_to(db_path)
            hardlink=folder/"hardlinked.db"
            os.link(db_path,hardlink)
            variants=[db_path,folder/"./source.sqlite",
                      symlink,hardlink]
            for target in variants:
                with self.subTest(path=str(target)):
                    with patch.object(sys,"argv",[
                        "program","--sqlite-readonly",str(db_path),
                        "--asof-ms","1800000000000","--out",str(target)]):
                        with redirect_stdout(StringIO()):
                            with self.assertRaisesRegex(ValueError,
                                    "OUTPUT_ALIASES_SQLITE"):
                                m.main()
                    self.assertEqual(db_path.read_bytes(),original)
                    with sqlite3.connect(db_path) as conn:
                        self.assertEqual(conn.execute(
                            "PRAGMA integrity_check").fetchone()[0],"ok")
            self.assertEqual(symlink.read_bytes(),original)
            self.assertEqual(hardlink.read_bytes(),original)

    def test_readonly_cli_refuses_main_sidecars_and_existing_output(self):
        with tempfile.TemporaryDirectory() as root:
            folder=Path(root)
            db_path=folder/"source.sqlite"
            with sqlite3.connect(db_path) as db:
                db.execute("""CREATE TABLE candidate_queue(
                    first_seen_ms INTEGER,deadline_ms INTEGER,
                    retry_after_ms INTEGER,last_evaluated_bar_ms INTEGER,
                    attempts INTEGER,venue TEXT,symbol TEXT,status TEXT)""")
            original=db_path.read_bytes()
            for suffix in ("-wal","-shm","-journal"):
                target=Path(str(db_path)+suffix)
                with self.subTest(sidecar=suffix):
                    with self.assertRaisesRegex(ValueError,
                            "OUTPUT_ALIASES_SQLITE"):
                        m.safe_new_json_output(target,db_path,{"n":1})
                    self.assertFalse(target.exists())
                    self.assertEqual(db_path.read_bytes(),original)
            out=folder/"safe-result.json"
            with patch.object(sys,"argv",[
                "program","--sqlite-readonly",str(db_path),
                "--asof-ms","1800000000000","--out",str(out)]):
                with redirect_stdout(StringIO()):
                    m.main()
            saved=out.read_bytes()
            self.assertEqual(json.loads(saved)["PENDING"],0)
            self.assertTrue(saved.endswith(b"\n"))
            with patch.object(sys,"argv",[
                "program","--sqlite-readonly",str(db_path),
                "--asof-ms","1800000000000","--out",str(out)]):
                with redirect_stdout(StringIO()):
                    with self.assertRaisesRegex(ValueError,
                            "OUTPUT_EXISTS_REFUSE_OVERWRITE"):
                        m.main()
            self.assertEqual(out.read_bytes(),saved)
            self.assertEqual(db_path.read_bytes(),original)

    def test_readonly_cli_refuses_wal_hardlink_or_symlink(self):
        with tempfile.TemporaryDirectory() as root:
            folder=Path(root)
            db_path=folder/"source.sqlite"
            with sqlite3.connect(db_path) as db:
                db.execute("CREATE TABLE test(id INT)")
            wal=Path(str(db_path)+"-wal")
            wal.write_bytes(b"readonly-test-wal-untouched")
            alias=folder/"linked-wal"
            alias.symlink_to(wal)
            hard=folder/"hardlinked-wal"
            os.link(wal,hard)
            for out in (wal,alias,hard):
                with self.subTest(out=str(out)):
                    with self.assertRaisesRegex(ValueError,
                            "OUTPUT_ALIASES_SQLITE"):
                        m.safe_new_json_output(out,db_path,{"n":1})
                    self.assertEqual(wal.read_bytes(),
                                     b"readonly-test-wal-untouched")

    def test_asof_rejects_future_first_seen_and_future_evaluated_bar(self):
        db=queue_db()
        at=1_800_000_000_000
        add_pending(db,98,start=at+m.MIN)
        with self.assertRaisesRegex(ValueError,"ASOF_FUTURE"):
            m.queue_pressure(db,at)
        db.execute("UPDATE candidate_queue SET first_seen_ms=?", (at,))
        db.execute("UPDATE candidate_queue SET last_evaluated_bar_ms=? WHERE id=1",
                   (at+m.MIN,))
        with self.assertRaisesRegex(ValueError,"ASOF_FUTURE"):
            m.queue_pressure(db,at)
        db.execute("UPDATE candidate_queue SET last_evaluated_bar_ms=NULL WHERE id=1")
        self.assertEqual(m.queue_pressure(db,at)["PENDING"],98)
        self.assertEqual(m.queue_pressure(db,at)["snapshot_scope"],
            "CURRENT_STORED_PENDING_ONLY_NOT_HISTORICAL_RECONSTRUCTION")
        db.close()

    def test_duplicate_candidate_primary_key_different_symbol_rejected(self):
        day=tiny_day()
        day["queue_final"][1]["id"]=day["queue_final"][0]["id"]
        with self.assertRaisesRegex(ValueError,"DUPLICATED_ORIGINAL_QUEUE"):
            m.audit_day(day,{
                "date":day["date"],"original_watch_arrivals":2,
                "original_individual_setups":1,"real_shared_setups":1,
                "late":1,"official_5m_publisher_sha_source_count":0})

    def test_fake_setup_symbol_and_clock_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            _,rec=mini_zip(root,tiny_day())
            day=tiny_day()
            day["setups"][0]["symbol"]="NONEXISTENTUSDT"
            with self.assertRaisesRegex(ValueError,"SETUP_UNMATCHED"):
                m.audit_day(day,rec)
            day=tiny_day()
            day["setups"][0]["utc"]=datetime.fromtimestamp(
                (day["queue_final"][0]["first_seen_ms"]-m.MIN)/1000,
                timezone.utc).isoformat().replace("+00:00","Z")
            with self.assertRaisesRegex(ValueError,"SETUP_UNMATCHED"):
                m.audit_day(day,rec)

    def test_late_before_watch_and_duplicate_event_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            _,rec=mini_zip(root,tiny_day())
            day=tiny_day()
            day["late_events"][0]["observed_ms"] = (
                day["queue_final"][1]["first_seen_ms"]-m.MIN)
            with self.assertRaisesRegex(ValueError,"LATE_UNMATCHED"):
                m.audit_day(day,rec)
            day=tiny_day()
            late=dict(day["queue_final"][1])
            late.update(id=3,symbol="CUSDT")
            day["queue_final"].append(late)
            day["queue_candidates"]=3
            day["watch_arrivals"]=3
            day["candidate_status_counts"]["LATE"]=2
            day["event_counts"]["LATE_REVIEW"]=2
            day["event_counts"]["WATCH_EARLY"]=3
            day["late_events"].append({
                "symbol":"CUSDT",
                "observed_ms":late["deadline_ms"]+m.MIN,
                "payload":{"classification":"STALE_NOT_ACTIONABLE",
                           "first_seen_ms":late["first_seen_ms"],
                           "deadline_ms":late["deadline_ms"]}})
            rec["original_watch_arrivals"]=3
            rec["late"]=2
            valid,items=m.audit_day(day,rec)
            self.assertEqual(len(items),3)
            day["late_events"][1]=json.loads(json.dumps(day["late_events"][0]))
            with self.assertRaisesRegex(ValueError,"LATE_UNMATCHED"):
                m.audit_day(day,rec)



if __name__=="__main__":
    unittest.main()
