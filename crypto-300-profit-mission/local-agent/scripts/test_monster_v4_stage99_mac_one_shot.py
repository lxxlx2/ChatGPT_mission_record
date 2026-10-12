#!/usr/bin/env python3
"""No-network Stage99 orchestration tests: never launch a real job or touch Mac state."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch
from zoneinfo import ZoneInfo

try:
    import monster_v4_stage99_mac_launchd_one_shot as module
    import monster_v4_stage97_one_shot_usdm_capture as stage97
    import monster_v4_stage91_forward_oos_replay_gate as freeze
except ImportError:
    from scripts import monster_v4_stage99_mac_launchd_one_shot as module
    from scripts import monster_v4_stage97_one_shot_usdm_capture as stage97
    from scripts import monster_v4_stage91_forward_oos_replay_gate as freeze


class OneShotIsolatedTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root=Path(self.tmp.name)
        self.patches=[
            patch.object(module,"ROOT",root),
            patch.object(module,"CLONE",root/"repo"),
            patch.object(module,"STATES",root/"state"),
            patch.object(module,"LOGS",root/"logs"),
            patch.object(module,"AGENTS",root/"LaunchAgents"),
        ]
        for item in self.patches:
            item.start()
            self.addCleanup(item.stop)
        module.CLONE.mkdir(parents=True,exist_ok=True)
        module.STATES.mkdir(parents=True,exist_ok=True)
        self.window=freeze.WINDOWS[0]
        self.start=freeze.verify_window(self.window)

    def fake_official(self):
        # No Internet involved: a hash-bound artificial reference for isolation tests.
        t=self.start-2*60000
        market={
            "serverTime":t-86_400_000,
            "symbols":[{
                "symbol":"SYNTHUSDT","status":"TRADING",
                "contractType":"PERPETUAL","baseAsset":"SYNTH",
                "quoteAsset":"USDT","onboardDate":t-3600000
            }]}
        first=stage97.fixture(stage97.TIME_URL,{"serverTime":t+100},t,t+200)
        exchange=stage97.fixture(stage97.EXCHANGE_URL,market,t+200,t+400)
        last=stage97.fixture(stage97.TIME_URL,{"serverTime":t+500},t+400,t+600)
        return stage97.verify_time_proof(first,last,exchange,self.window)

    def test_mac_plist_has_exactly_one_calendar_run_and_no_periodic_monitor(self):
        b=module.job_plist(self.window,Path("/tmp/repo/source.py"),Path("/usr/bin/python3"),
            user_tz=ZoneInfo("Asia/Bangkok"))
        self.assertFalse(b["RunAtLoad"])
        self.assertFalse(b["KeepAlive"])
        self.assertNotIn("StartInterval",b)
        self.assertNotIn("WatchPaths",b)
        self.assertNotIn("Program",b)
        self.assertEqual(b["StartCalendarInterval"],
            {"Month":10,"Day":14,"Hour":12,"Minute":48})
        us=module.job_plist(self.window,Path("/tmp/repo/source.py"),Path("/usr/bin/python3"),
            user_tz=ZoneInfo("America/Los_Angeles"))
        self.assertEqual(us["StartCalendarInterval"],
            {"Month":10,"Day":13,"Hour":22,"Minute":48})
        self.assertIn(self.window,b["ProgramArguments"])

    def test_offline_install_never_performs_network_or_writes_plist(self):
        out=module.install(now=self.start-15*60000,dry_run=True)
        self.assertEqual(len(out),3)
        self.assertFalse(module.AGENTS.exists())
        self.assertTrue(all(x in out for x in freeze.WINDOWS))

    def test_no_frozen_date_can_be_replaced(self):
        with self.assertRaises(ValueError):
            module.label_for("2026-10-15T06:00:00Z")
        with self.assertRaises(ValueError):
            module.install(now=self.start+1000,windows=(self.window,),dry_run=True)

    def test_real_path_is_exact_original_pr_not_main(self):
        expected=module.expected_path(self.window)
        self.assertIn("monster_stage97_point_in_time_usdm_2026-10-14_raw_https.json",expected)
        self.assertEqual(module.BRANCH,"research/monster-v4-local-discovery-20261010")
        self.assertNotIn("main",expected)

    def test_capture_and_git_push_full_success_with_replay_guard(self):
        proof=self.fake_official()
        f=Mock(return_value=proof)
        push=Mock(return_value="f"*40)
        with patch.object(module,"isolated_checkout_preflight"), patch.object(module,"git"):
            result=module.run(self.window,clock=lambda:self.start-1000,
                              capture=f,git_push=push)
        self.assertEqual(result,"GIT_PUSH_CONFIRMED")
        self.assertEqual(f.call_count,1)
        self.assertEqual(push.call_count,1)
        archive=module.CLONE/module.expected_path(self.window)
        saved=json.loads(archive.read_text())
        self.assertEqual(saved["window_start_utc"],self.window)
        status=module.status()[self.window]
        self.assertEqual(status["status"],"GIT_PUSH_CONFIRMED")
        self.assertTrue(status["source_sha256"])
        with patch.object(module,"isolated_checkout_preflight") as pre:
            ret=module.run(self.window,clock=lambda:self.start-900,
                           capture=f,git_push=push)
        self.assertEqual(ret,"ALREADY_PUSHED")
        self.assertEqual(f.call_count,1)
        pre.assert_not_called()

    def test_stale_window_fails_before_network(self):
        get=Mock()
        with patch.object(module,"isolated_checkout_preflight") as checkout:
            status=module.run(self.window,clock=lambda:self.start+2,
                              capture=get,git_push=Mock())
        self.assertEqual(status,"MISSED_WINDOW")
        self.assertEqual(module.status()[self.window]["status"],"MISSED_WINDOW_NO_BACKFILL")
        get.assert_not_called()
        checkout.assert_not_called()

    def test_failed_source_does_not_commit_false_evidence(self):
        get=Mock(side_effect=ValueError("synthetic no network"))
        push=Mock()
        with patch.object(module,"isolated_checkout_preflight"), \
             patch.object(module.time,"sleep"), \
             patch.object(module,"git"):
            status=module.run(self.window,clock=lambda:self.start-120000,
                              capture=get,git_push=push)
        self.assertEqual(status,"SOURCE_FAILED")
        self.assertEqual(get.call_count,3)
        push.assert_not_called()
        self.assertEqual(module.status()[self.window]["status"],"SOURCE_FAILED_NO_BACKFILL")

    def test_git_failure_preserves_sha_and_retry_never_recaptures(self):
        evidence=self.fake_official()
        fail=Mock(side_effect=RuntimeError("fake git push denied"))
        with patch.object(module,"isolated_checkout_preflight"), patch.object(module,"git"):
            with self.assertRaisesRegex(RuntimeError,"fake git push"):
                module.run(self.window,clock=lambda:self.start-1000,
                           capture=lambda _:evidence,git_push=fail)
        archive=module.CLONE/module.expected_path(self.window)
        self.assertTrue(archive.exists())
        self.assertEqual(module.status()[self.window]["status"],
                         "CAPTURE_VALIDATED_GIT_PUSH_PENDING")
        with patch.object(module,"isolated_checkout_preflight_for_saved"), \
             patch.object(module,"git"), \
             patch.object(module,"safe_git_commit_and_push",return_value="a"*40):
            result=module.retry_saved_push(self.window)
        self.assertEqual(result,"a"*40)
        self.assertTrue(module.status()[self.window][
            "uploaded_from_original_official_raw_without_recapture"])
        self.assertEqual(module.status()[self.window]["status"],"GIT_PUSH_CONFIRMED")

    def test_tampered_saved_evidence_cannot_upload(self):
        proof=self.fake_official()
        with patch.object(module,"isolated_checkout_preflight"), patch.object(module,"git"):
            with self.assertRaises(RuntimeError):
                module.run(self.window,clock=lambda:self.start-1000,
                           capture=lambda _:proof,
                           git_push=Mock(side_effect=RuntimeError("blocked")))
        path=module.CLONE/module.expected_path(self.window)
        path.write_text(path.read_text()+" ")
        with patch.object(module,"isolated_checkout_preflight_for_saved"), \
             patch.object(module,"git"), \
             patch.object(module,"safe_git_commit_and_push") as push:
            with self.assertRaisesRegex(RuntimeError,"MODIFIED_SHA"):
                module.retry_saved_push(self.window)
            push.assert_not_called()

    def test_raw_frozen_15min_window_not_extended_by_retry(self):
        proof=self.fake_official()
        self.assertEqual(proof["snapshot_symbol_summary"][
            "usd_m_usdt_perpetual_asof_candidates"],1)
        with patch.object(module,"isolated_checkout_preflight"), \
             patch.object(module,"git"):
            status=module.run(self.window,clock=lambda:self.start-16*60000,
                              capture=Mock(return_value=proof),
                              git_push=Mock(return_value="a"*40))
        self.assertEqual(status,"MISSED_WINDOW")

    def test_uninstall_can_only_mention_our_exact_three_labels(self):
        for w in freeze.WINDOWS:
            self.assertTrue(module.label_for(w).startswith(
                "com.lxxlx2.monster.stage99.usdm."))
        self.assertNotIn("frank"," ".join(module.label_for(w) for w in freeze.WINDOWS))


if __name__=="__main__":
    unittest.main(verbosity=2)
