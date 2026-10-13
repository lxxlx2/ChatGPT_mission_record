#!/usr/bin/env python3
"""Stage103 real LOCAL Git integration: no mocks for Git, no network, no installs."""
from __future__ import annotations
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import Mock,patch

try:
    import monster_v4_stage99_mac_launchd_one_shot as stage99
except ImportError:
    from scripts import monster_v4_stage99_mac_launchd_one_shot as stage99


def command(*args,cwd=None):
    result=subprocess.run(list(args),cwd=cwd,check=True,text=True,
                          stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=35)
    return result.stdout.strip()


class LocalGitUploaderIntegration(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        t=Path(self.temp.name)
        self.remote=t/"remote.git"
        self.seed=t/"seed"
        self.second=t/"second"
        self.clone=t/"private"/"repo"
        command("git","init","--bare",str(self.remote))
        command("git","init",str(self.seed))
        command("git","-C",str(self.seed),"switch","-c",stage99.BRANCH)
        (self.seed/"README.md").write_text("stage103 git test origin\n")
        self.review_target=(
            "crypto-300-profit-mission/local-agent/scripts/"
            "monster_v4_stage105_capture_universe_core.py")
        original=self.seed/self.review_target
        original.parent.mkdir(parents=True,exist_ok=True)
        original.write_text("FROZEN_REVIEWED_SOURCE_FIXTURE=1\n")
        command("git","-C",str(self.seed),"add","--all")
        command("git","-C",str(self.seed),"-c","user.name=fixture",
                "-c","user.email=fixture@example.test","commit","-m","initial local")
        command("git","-C",str(self.seed),"remote","add","origin",str(self.remote))
        command("git","-C",str(self.seed),"push","origin",
                "HEAD:refs/heads/"+stage99.BRANCH)
        self.clone.parent.mkdir(parents=True)
        command("git","clone","-b",stage99.BRANCH,str(self.remote),str(self.clone))
        command("git","clone","-b",stage99.BRANCH,str(self.remote),str(self.second))
        patch_clone=patch.object(stage99,"CLONE",self.clone)
        patch_clone.start();self.addCleanup(patch_clone.stop)
        review=patch.object(stage99,"review_gate",return_value=Mock(
            validate_authorization=Mock(return_value={"review_fingerprint":"a"*64})))
        review.start();self.addCleanup(review.stop)
        self.window=stage99.stage91.WINDOWS[0]
        self.path=stage99.expected_path(self.window)
        original=self.clone/self.path
        original.parent.mkdir(parents=True,exist_ok=True)
        original.write_text(json.dumps({
            "schema":"TEST_CAPTURE_BYTES_NOT_ACTUAL_BINANCE",
            "window_start_utc":self.window,"proof":"fixed synthetic bytes"},
            sort_keys=True)+"\n")
        self.original=original
        self.local_head=command("git","-C",str(self.clone),"rev-parse","HEAD")

    def another_commit(self, name, content):
        path=self.second/name
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(content)
        command("git","-C",str(self.second),"add","--",name)
        command("git","-C",str(self.second),"-c","user.name=independent",
                "-c","user.email=independent@example.test","commit","-m","unrelated")
        command("git","-C",str(self.second),"push","origin",
                "HEAD:refs/heads/"+stage99.BRANCH)

    def test_actual_local_bare_git_source_push_preserves_remote_changes_and_reviewed_clone(self):
        self.another_commit("unrelated_remote_change.md","do not overwrite\n")
        pushed=stage99.safe_git_commit_and_push(self.window)
        self.assertEqual(len(pushed),40)
        self.assertEqual(command("git","-C",str(self.clone),"rev-parse","HEAD"),
                         self.local_head)
        self.assertEqual(command("git","-C",str(self.clone),"branch","--show-current"),
                         stage99.BRANCH)
        self.assertEqual(command("git","-C",str(self.clone),"ls-files",self.path),"")
        self.assertFalse((self.clone/".git"/"rebase-merge").exists())
        self.assertFalse((self.clone/".git"/"rebase-apply").exists())
        fetched=t=Path(self.temp.name)/"checked"
        command("git","clone","-b",stage99.BRANCH,str(self.remote),str(fetched))
        self.assertEqual((fetched/self.path).read_bytes(),self.original.read_bytes())
        self.assertEqual((fetched/"unrelated_remote_change.md").read_text(),"do not overwrite\n")
        second=stage99.safe_git_commit_and_push(self.window)
        self.assertEqual(second,pushed)

    def test_reviewed_runtime_git_tree_rejects_dirty_and_recommitted_sources(self):
        one=self.review_target
        pinned=self.local_head
        frozen=command("git","-C",str(self.clone),"rev-parse",pinned+":"+one)
        gate=Mock(
            REQUIRED_SOURCES=(one,),
            validate_authorization=Mock(return_value={"review_fingerprint":"f"*64}),
            validate_review=Mock(return_value={
                "reviewed_commit":pinned,
                "reviewed_file_git_blobs":{one:frozen}}))
        with patch.object(stage99,"review_gate",return_value=gate):
            clean=stage99.assert_reviewed_runtime_source()
            self.assertEqual(clean["actual_head"],pinned)
            self.assertEqual(clean["complete_execution_path_verified"],1)
            local=self.clone/one
            local.write_text("MALICIOUS_DIRTY_CHANGE=1\n")
            with self.assertRaisesRegex(RuntimeError,"EXECUTABLE_FILES_DIRTY"):
                stage99.assert_reviewed_runtime_source()
            # Deliberately commit a different executable in the same branch.
            command("git","-C",str(self.clone),"add","--",one)
            command("git","-C",str(self.clone),"-c","user.name=fixture",
                    "-c","user.email=fixture@example.test",
                    "commit","-m","unreviewed tracked source")
            with self.assertRaisesRegex(RuntimeError,"TREE_BLOB_NOT_REVIEWED"):
                stage99.assert_reviewed_runtime_source()
            gate.validate_authorization.assert_called()

    def test_push_race_remote_moves_between_fetch_and_push_then_retries(self):
        actual=stage99._git_in_worktree
        raced=[False]
        def advance_then_git(where,*args,**kwargs):
            if args and args[0]=="push" and not raced[0]:
                raced[0]=True
                self.another_commit("just_before_push.md","race from second clone\n")
            return actual(where,*args,**kwargs)
        with patch.object(stage99,"_git_in_worktree",side_effect=advance_then_git):
            newcommit=stage99.safe_git_commit_and_push(self.window)
        self.assertTrue(raced[0])
        self.assertEqual(len(newcommit),40)
        self.assertEqual(command("git","-C",str(self.clone),"rev-parse","HEAD"),self.local_head)
        check=Path(self.temp.name)/"race_checked"
        command("git","clone","-b",stage99.BRANCH,str(self.remote),str(check))
        self.assertEqual((check/self.path).read_bytes(),self.original.read_bytes())
        self.assertEqual((check/"just_before_push.md").read_text(),"race from second clone\n")

    def test_remote_archive_conflict_never_overwrites_known_file(self):
        remote=self.second/self.path
        remote.parent.mkdir(parents=True,exist_ok=True)
        remote.write_text('{"window_start_utc":"2026-10-14T06:00:00Z","other":"conflict"}')
        command("git","-C",str(self.second),"add","--",self.path)
        command("git","-C",str(self.second),"-c","user.name=independent",
                "-c","user.email=independent@example.test",
                "commit","-m","existing different archive")
        command("git","-C",str(self.second),"push","origin",
                "HEAD:refs/heads/"+stage99.BRANCH)
        with self.assertRaisesRegex(RuntimeError,"REMOTE_ARCHIVE_DIFFERS"):
            stage99.safe_git_commit_and_push(self.window)
        self.assertEqual(command("git","-C",str(self.clone),"rev-parse","HEAD"),
                         self.local_head)
        self.assertEqual(self.original.exists(),True)


if __name__=="__main__":
    unittest.main(verbosity=2)
