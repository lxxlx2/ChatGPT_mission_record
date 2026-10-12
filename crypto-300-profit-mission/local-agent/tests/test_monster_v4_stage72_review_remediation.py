"""Stage72 repair tests: historical-only repo checkout, never production or email."""
import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

S=Path(__file__).resolve().parents[1]/"scripts"
sys.path.insert(0,str(S))
import monster_v4_stage70_historical_watch_projection_sqlite as sqlite_projection
import monster_v4_stage65_new3_full900_official_hourly_SHA as first_source
import monster_v4_stage66_new3_original_1m_D0_first5_vs_P1v03 as minute_source
import monster_v4_stage72_imported_dependency_integrity as integrity


class Stage72CorrectiveRegressions(unittest.TestCase):
    def command(self, directory):
        root=Path(directory)
        return [sys.executable,"-B",str(S/"monster_v4_stage70_historical_watch_projection_sqlite.py"),
                "--db",str(root/"monster-only-research.sqlite3"),
                "--out",str(root/"read-model")]

    def exports(self,directory):
        folder=Path(directory)/"read-model"
        return {p.name:p.read_bytes() for p in folder.iterdir() if p.is_file()}

    def run_command(self,command):
        finished=subprocess.run(command,text=True,capture_output=True,timeout=90)
        self.assertEqual(finished.returncode,0,finished.stderr)
        return finished.stdout

    def test_stage70_first_import_then_same_database_second_and_third_equal_exports(self):
        with tempfile.TemporaryDirectory() as temp:
            command=self.command(temp)
            first=self.run_command(command)
            self.assertIn('"newly_ingested_this_invocation": 937',first)
            baseline=self.exports(temp)
            self.assertEqual(len(baseline),2)
            for i in range(2):
                stdout=self.run_command(command)
                self.assertIn('"newly_ingested_this_invocation": 0',stdout)
                self.assertEqual(baseline,self.exports(temp))
            with sqlite3.connect(Path(temp)/"monster-only-research.sqlite3") as db:
                self.assertEqual(sqlite_projection.counts(db),{
                    "journal_events":937,"unique_first_D0_watch":715,
                    "P1_upgraded":222,"stage_counts":{
                        "WATCH":493,"URGENT_RESEARCH":161,"CAP_DEFERRED_RESEARCH":61
                    }})

    def test_stage70_partial_valid_database_adds_remainder_without_deleting_state(self):
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as clean:
            original=sqlite_projection.source()
            self.assertEqual(len(original),937)
            dbpath=Path(temp)/"monster-only-research.sqlite3"
            with sqlite3.connect(dbpath,isolation_level=None) as db:
                sqlite_projection.setup(db)
                self.assertEqual(sqlite_projection.ingest(db,original[:252]),252)
            stdout=self.run_command(self.command(temp))
            self.assertIn('"newly_ingested_this_invocation": 685',stdout)
            self.run_command(self.command(clean))
            self.assertEqual(self.exports(temp),self.exports(clean))
            self.assertIn('"newly_ingested_this_invocation": 0',
                          self.run_command(self.command(temp)))

    def test_stage70_conflicting_prior_payload_aborts_without_rewriting(self):
        with tempfile.TemporaryDirectory() as temp:
            command=self.command(temp)
            self.run_command(command)
            baseline=self.exports(temp)
            events=sqlite_projection.source()
            conflict=dict(events[0],some_unexpected_field="tamper")
            db=Path(temp)/"monster-only-research.sqlite3"
            with sqlite3.connect(db,isolation_level=None) as conn:
                before=sqlite_projection.snapshot(conn)
                with self.assertRaisesRegex(ValueError,"DIFFERENT_IMMUTABLE"):
                    sqlite_projection.ingest(conn,[conflict])
                self.assertEqual(before,sqlite_projection.snapshot(conn))
            self.assertEqual(baseline,self.exports(temp))

    def test_stage65_actual_imported_hourly_chain_matches_original_manifest(self):
        expected=first_source.frozen()
        self.assertEqual(len(expected),900)
        audit=integrity.assert_integrity_stage65(first_source.orig44)
        self.assertEqual(set(audit),{
            "monster_v4_stage44_six_blind_hourly_truth",
            "monster_v4_stage37_usdm_sixdate_full900_hourly_labels",
        })

    def test_stage66_actual_minute_and_hourly_import_graph_is_locked(self):
        originals=minute_source.frozen()
        self.assertEqual(len(originals),2700)
        audit=integrity.assert_integrity_stage66(
            minute_source.src,minute_source.baseline,
            minute_source.oldp1,minute_source.hourly_original.orig44)
        self.assertEqual(len(audit),7)

    def test_stage72_alias_swap_to_unrelated_module_is_rejected(self):
        original=minute_source.oldp1.originalV4
        try:
            minute_source.oldp1.originalV4=minute_source.src
            with self.assertRaisesRegex(ValueError,"ALIAS_GRAPH_CHANGED"):
                integrity.assert_integrity_stage66(
                    minute_source.src,minute_source.baseline,
                    minute_source.oldp1,minute_source.hourly_original.orig44)
        finally:
            minute_source.oldp1.originalV4=original

    def test_stage72_unknown_unpinned_import_and_path_shadow_rejected(self):
        with self.assertRaisesRegex(ValueError,"UNKNOWN_UNPINNED_MODULE"):
            integrity.assert_modules({"unknown-module":minute_source.src})
        from types import SimpleNamespace
        name="monster_v4_stage39_usdm_all900_sixday_original_1m"
        dummy=SimpleNamespace(__name__=name,__file__="/tmp/other/monster_v4_stage39_usdm_all900_sixday_original_1m.py")
        with self.assertRaisesRegex(ValueError,"PATH_SHADOWED"):
            integrity.assert_modules({name:dummy})


if __name__=="__main__":
    unittest.main()
