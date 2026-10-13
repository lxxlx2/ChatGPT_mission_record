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


ORIGINAL_ASSERT_UNLOADED = module.assert_unloaded


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
            patch.object(module,"assert_reviewed_runtime_source",
                         return_value={"complete_execution_path_verified":8}),
            patch.object(module,"assert_unloaded",return_value=True),
            patch.object(module,"review_gate",return_value=Mock(
                validate_authorization=Mock(return_value={
                    "review_fingerprint":"a"*64}),
                interactive_install_consent=Mock(return_value=True))),
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

    def test_approved_review_installs_exact_three_isolated_launchd_jobs(self):
        try:
            import monster_v4_stage102_claude_chat_review_gate as external_ai
        except ImportError:
            from scripts import monster_v4_stage102_claude_chat_review_gate as external_ai
        now=self.start-20*60000
        with patch.object(module.sys,"platform","darwin"), \
             patch.object(module,"read_frank_launchd_labels",return_value=["frank.daemon"]), \
             patch.object(module,"isolated_checkout_preflight_local"), \
             patch.object(module,"git"), \
             patch.object(module,"launchctl",return_value=0) as launch, \
             patch.object(module.shutil,"which",return_value="/bin/launchctl"):
            installed=module.install(now=now,dry_run=False)
        self.assertEqual(len(installed),3)
        self.assertEqual(launch.call_count,3)
        for w in freeze.WINDOWS:
            plist=module.plist_path(w)
            self.assertTrue(plist.exists())
            with open(plist,"rb") as f:
                import plistlib
                data=plistlib.load(f)
            self.assertFalse(data["KeepAlive"])
            self.assertFalse(data["RunAtLoad"])
            self.assertEqual(data["ProgramArguments"][-1],w)
            self.assertTrue(data["Label"].startswith("com.lxxlx2.monster.stage99."))
            self.assertEqual(module.status()[w]["status"],"SCHEDULE_INSTALLED")
        with patch.object(module,"launchctl",return_value=0) as boot:
            for w in freeze.WINDOWS:module.bootout(w)
        self.assertEqual(boot.call_count,3)
        self.assertTrue(all(not module.plist_path(w).exists() for w in freeze.WINDOWS))

    def test_stage103_install_preflights_all_plists_before_creating_any(self):
        module.AGENTS.mkdir(parents=True,exist_ok=True)
        second=module.plist_path(freeze.WINDOWS[1])
        second.write_text("other existing stage99 job must remain")
        with patch.object(module.sys,"platform","darwin"), \
             patch.object(module,"isolated_checkout_preflight_local"), \
             patch.object(module,"git"), \
             patch.object(module,"read_frank_launchd_labels",return_value=["frank"]), \
             patch.object(module,"launchctl",return_value=0) as launch, \
             patch.object(module.shutil,"which",return_value="/bin/launchctl"):
            with self.assertRaisesRegex(RuntimeError,"PLISTS_ALREADY_EXISTS"):
                module.install(now=self.start-20*60000,dry_run=False)
        launch.assert_not_called()
        self.assertFalse(module.plist_path(freeze.WINDOWS[0]).exists())
        self.assertEqual(second.read_text(),"other existing stage99 job must remain")

    def test_stage103_bootstrap_midfailure_rolls_back_all_created_jobs(self):
        with patch.object(module.sys,"platform","darwin"), \
             patch.object(module,"isolated_checkout_preflight_local"), \
             patch.object(module,"git"), \
             patch.object(module,"read_frank_launchd_labels",return_value=["frank"]), \
             patch.object(module,"launchctl",side_effect=[0,1,0,0]) as launch, \
             patch.object(module.shutil,"which",return_value="/bin/launchctl"):
            with self.assertRaisesRegex(RuntimeError,"BOOTSTRAP_FAILED"):
                module.install(now=self.start-20*60000,dry_run=False)
        self.assertEqual(launch.call_count,4)
        self.assertTrue(all(not module.plist_path(w).exists() for w in freeze.WINDOWS))
        for w in freeze.WINDOWS[:2]:
            self.assertEqual(module.status()[w]["status"],"INSTALL_ROLLED_BACK_NO_SERVICE_ENABLED")
        self.assertEqual(module.status()[freeze.WINDOWS[2]]["status"],"NOT_INSTALLED")

    def test_stage103_frank_mutation_aborts_only_our_services(self):
        with patch.object(module.sys,"platform","darwin"), \
             patch.object(module,"isolated_checkout_preflight_local"), \
             patch.object(module,"git"), \
             patch.object(module,"read_frank_launchd_labels",
                          side_effect=[["frank.original"],["frank.original","frank.extra"]]), \
             patch.object(module,"launchctl",return_value=0) as launch, \
             patch.object(module.shutil,"which",return_value="/bin/launchctl"):
            with self.assertRaisesRegex(RuntimeError,"FRANK_LAUNCHD_COEXISTENCE_CHANGED"):
                module.install(now=self.start-20*60000,dry_run=False)
        self.assertEqual(launch.call_count,6)
        self.assertTrue(all(not module.plist_path(w).exists() for w in freeze.WINDOWS))

    def test_stage104_bootout_failed_retains_plist_and_cannot_claim_success(self):
        module.AGENTS.mkdir(parents=True,exist_ok=True)
        file=module.plist_path(self.window)
        file.write_text("keep for safety")
        with patch.object(module,"launchctl",return_value=5):
            with self.assertRaisesRegex(RuntimeError,"BOOTOUT_FAILED"):
                module.bootout(self.window)
        self.assertTrue(file.is_file())

    def test_stage104_rollback_marks_still_loaded_on_failure(self):
        with patch.object(module.sys,"platform","darwin"), \
             patch.object(module,"isolated_checkout_preflight_local"), \
             patch.object(module,"git"), \
             patch.object(module,"read_frank_launchd_labels",return_value=["frank"]), \
             patch.object(module,"launchctl",side_effect=[0,1,7,0]) as launch, \
             patch.object(module.shutil,"which",return_value="/bin/launchctl"):
            with self.assertRaisesRegex(RuntimeError,"ROLLBACK_SAFETY_UNVERIFIED"):
                module.install(now=self.start-20*60000,dry_run=False)
        self.assertEqual(launch.call_count,4)
        self.assertEqual(module.status()[freeze.WINDOWS[1]]["status"],
                         "ROLLBACK_FAILED_SERVICE_STILL_LOADED")
        self.assertTrue(module.plist_path(freeze.WINDOWS[1]).exists())
        self.assertEqual(module.status()[freeze.WINDOWS[0]]["status"],
                         "INSTALL_ROLLED_BACK_NO_SERVICE_ENABLED")
        self.assertFalse(module.plist_path(freeze.WINDOWS[0]).exists())

    def test_stage104_assert_unloaded_checks_both_registry_and_detail(self):
        from types import SimpleNamespace
        absent="PID\tStatus\tLabel\n42\t0\tcom.someone.frank\n"
        present=absent+"123\t0\t"+module.label_for(self.window)+"\n"
        def response(rc,txt=""):
            return SimpleNamespace(returncode=rc,stdout=txt,stderr="")
        with patch.object(module.subprocess,"run",side_effect=[
                response(0,absent),response(113)]):
            self.assertTrue(ORIGINAL_ASSERT_UNLOADED(self.window))
        with patch.object(module.subprocess,"run",side_effect=[
                response(0,present),response(113)]):
            with self.assertRaisesRegex(RuntimeError,"STILL_LOADED"):
                ORIGINAL_ASSERT_UNLOADED(self.window)
        with patch.object(module.subprocess,"run",side_effect=[
                response(0,absent),response(0,"still exists")]):
            with self.assertRaisesRegex(RuntimeError,"STILL_LOADED"):
                ORIGINAL_ASSERT_UNLOADED(self.window)
        with patch.object(module.subprocess,"run",side_effect=[response(1)]):
            with self.assertRaisesRegex(RuntimeError,"CANNOT_PROVE"):
                ORIGINAL_ASSERT_UNLOADED(self.window)

    def test_stage104_bootout_verification_failure_does_not_delete_plist(self):
        module.AGENTS.mkdir(parents=True,exist_ok=True)
        file=module.plist_path(self.window)
        file.write_text("do not erase the only recovery pointer")
        with patch.object(module,"launchctl",return_value=0), \
             patch.object(module,"assert_unloaded",side_effect=RuntimeError(
                 "STAGE104_SERVICE_STILL_LOADED")):
            with self.assertRaisesRegex(RuntimeError,"SERVICE_STILL_LOADED"):
                module.bootout(self.window)
        self.assertTrue(file.exists())

    def test_stage105_enospc_status_write_does_not_interrupt_other_bootouts(self):
        attempts=[]
        def fail_disk(window,status,**kwargs):
            attempts.append((window,status))
            if window==freeze.WINDOWS[1] or status.startswith("INSTALL_ROLLED"):
                raise OSError(28,"synthetic disk full")
            return None
        with patch.object(module.sys,"platform","darwin"), \
             patch.object(module,"isolated_checkout_preflight_local"), \
             patch.object(module,"git"), \
             patch.object(module,"read_frank_launchd_labels",return_value=["frank"]), \
             patch.object(module,"launchctl",return_value=0) as launch, \
             patch.object(module,"store_status",side_effect=fail_disk), \
             patch.object(module.shutil,"which",return_value="/bin/launchctl"):
            with self.assertRaisesRegex(RuntimeError,"ROLLBACK_SAFETY_UNVERIFIED"):
                module.install(now=self.start-20*60000,dry_run=False)
        self.assertEqual(launch.call_count,4)
        self.assertEqual(
            [call.args[0] for call in launch.call_args_list],
            ["bootstrap","bootstrap","bootout","bootout"])
        self.assertFalse(module.plist_path(freeze.WINDOWS[0]).exists())
        self.assertFalse(module.plist_path(freeze.WINDOWS[1]).exists())
        self.assertTrue(any(x[0]==freeze.WINDOWS[0] and
                            x[1]=="INSTALL_ROLLED_BACK_NO_SERVICE_ENABLED"
                            for x in attempts))
        self.assertTrue(any(x[0]==freeze.WINDOWS[1] and
                            x[1]=="INSTALL_ROLLED_BACK_NO_SERVICE_ENABLED"
                            for x in attempts))

    def test_stage105_disk_full_and_one_failed_unload_still_attempts_every_service(self):
        def fail_disk(window,status,**kwargs):
            if status=="SCHEDULE_INSTALLED" and window==freeze.WINDOWS[1]:
                raise OSError(28,"synthetic disk full")
            if status.startswith("INSTALL_ROLLED") or status.startswith("ROLLBACK_FAILED"):
                raise OSError(28,"synthetic rollback journal full")
        with patch.object(module.sys,"platform","darwin"), \
             patch.object(module,"isolated_checkout_preflight_local"), \
             patch.object(module,"git"), \
             patch.object(module,"read_frank_launchd_labels",return_value=["frank"]), \
             patch.object(module,"launchctl",side_effect=[0,0,7,0]) as launch, \
             patch.object(module,"store_status",side_effect=fail_disk), \
             patch.object(module.shutil,"which",return_value="/bin/launchctl"):
            with self.assertRaisesRegex(RuntimeError,"ROLLBACK_SAFETY_UNVERIFIED"):
                module.install(now=self.start-20*60000,dry_run=False)
        self.assertEqual(launch.call_count,4)
        self.assertFalse(module.plist_path(freeze.WINDOWS[0]).exists())
        self.assertTrue(module.plist_path(freeze.WINDOWS[1]).exists())

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
        with patch.object(module,"isolated_checkout_preflight_local"), patch.object(module,"git"):
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
        with patch.object(module,"isolated_checkout_preflight_local") as pre:
            ret=module.run(self.window,clock=lambda:self.start-900,
                           capture=f,git_push=push)
        self.assertEqual(ret,"ALREADY_PUSHED")
        self.assertEqual(f.call_count,1)
        pre.assert_not_called()

    def test_stale_window_fails_before_network(self):
        get=Mock()
        with patch.object(module,"isolated_checkout_preflight_local") as checkout:
            status=module.run(self.window,clock=lambda:self.start+2,
                              capture=get,git_push=Mock())
        self.assertEqual(status,"MISSED_WINDOW")
        self.assertEqual(module.status()[self.window]["status"],"MISSED_WINDOW_NO_BACKFILL")
        get.assert_not_called()
        checkout.assert_not_called()

    def test_failed_source_does_not_commit_false_evidence(self):
        get=Mock(side_effect=ValueError("synthetic no network"))
        push=Mock()
        with patch.object(module,"isolated_checkout_preflight_local"), \
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
        with patch.object(module,"isolated_checkout_preflight_local"), patch.object(module,"git"):
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
        with patch.object(module,"isolated_checkout_preflight_local"), patch.object(module,"git"):
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
        with patch.object(module,"isolated_checkout_preflight_local"), \
             patch.object(module,"git"):
            status=module.run(self.window,clock=lambda:self.start-16*60000,
                              capture=Mock(return_value=proof),
                              git_push=Mock(return_value="a"*40))
        self.assertEqual(status,"MISSED_WINDOW")

    def test_real_install_is_hard_blocked_without_other_ai_review(self):
        from unittest.mock import patch
        try:
            import monster_v4_stage102_claude_chat_review_gate as external_ai
        except ImportError:
            from scripts import monster_v4_stage102_claude_chat_review_gate as external_ai
        with patch.object(module.sys,"platform","darwin"), \
             patch.object(module,"review_gate",return_value=Mock(
                 validate_authorization=Mock(side_effect=
                     RuntimeError("STAGE103_USER_INSTALL_AUTHORIZATION_NOT_GIVEN")))) as blocked_gate, \
             patch.object(module,"isolated_checkout_preflight") as checkout, \
             patch.object(module,"launchctl") as launch:
            with self.assertRaisesRegex(RuntimeError,"AUTHORIZATION_NOT_GIVEN"):
                module.install(now=self.start-15*60000,dry_run=False)
            blocked_gate.return_value.validate_authorization.assert_called_once()
            checkout.assert_not_called()
            launch.assert_not_called()

    def test_external_ai_mock_result_never_counts_as_approval(self):
        try:
            import monster_v4_stage102_claude_chat_review_gate as external_ai
        except ImportError:
            from scripts import monster_v4_stage102_claude_chat_review_gate as external_ai
        with self.assertRaises(RuntimeError):
            external_ai.validate_authorization(root=module.CLONE,
               read_blob=lambda _: "a"*40,is_ancestor=lambda _:True)
        external_ai.selftest()
        self.assertFalse((module.CLONE / external_ai.RECEIPT).exists())

    def test_execute_git_failure_preserves_retryable_original_bytes(self):
        evidence=self.fake_official()
        with patch.object(module,"isolated_checkout_preflight_local"), \
             patch.object(module,"git"), \
             patch.object(module,"bootout") as unload:
            with patch.object(module.stage97,"now_ms",return_value=self.start-1000), \
                 patch.object(module.stage97,"capture_one",return_value=evidence), \
                 patch.object(module,"safe_git_commit_and_push",
                              side_effect=RuntimeError("synthetic push failed")):
                result=module.execute(self.window)
        self.assertEqual(result,3)
        persisted=module.status()[self.window]
        self.assertEqual(persisted["status"],"GIT_UPLOAD_FAILED_RETRYABLE")
        self.assertTrue(persisted["source_sha256"])
        self.assertTrue((module.CLONE / module.expected_path(self.window)).exists())
        unload.assert_called_once()
        with patch.object(module,"isolated_checkout_preflight_for_saved"), \
             patch.object(module,"git"), \
             patch.object(module,"safe_git_commit_and_push",return_value="a"*40), \
             patch.object(module.stage97,"capture_one") as no_second_capture:
            self.assertEqual(module.run(self.window,clock=lambda:self.start+9000),
                             "GIT_PUSH_CONFIRMED")
            no_second_capture.assert_not_called()
        self.assertEqual(module.status()[self.window]["status"],"GIT_PUSH_CONFIRMED")

    def test_uninstall_can_only_mention_our_exact_three_labels(self):
        for w in freeze.WINDOWS:
            self.assertTrue(module.label_for(w).startswith(
                "com.lxxlx2.monster.stage99.usdm."))
        self.assertNotIn("frank"," ".join(module.label_for(w) for w in freeze.WINDOWS))


if __name__=="__main__":
    unittest.main(verbosity=2)
