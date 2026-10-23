"""End-to-end private preview output placement boundary (synthetic only).

Imports the REAL CLI _private_create, uses actual temporary Git repositories
and a real linked worktree. No owner data, network, RPC, or production files.
"""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import stat
import subprocess
import tempfile
import unittest

CLI = (Path(__file__).resolve().parents[1] / "scripts" /
       "frank_d2_owner_preview.py")
spec = importlib.util.spec_from_file_location("frank_d2_owner_preview_under_test", CLI)
script = importlib.util.module_from_spec(spec)
spec.loader.exec_module(script)


def git(*args):
    proc = subprocess.run(["git", *map(str, args)], check=False,
                          capture_output=True, text=True, timeout=10)
    if proc.returncode:
        raise AssertionError("synthetic git setup failed")
    return proc.stdout.strip()


class PrivateOutputPlacementTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="frank-d2-private-")
        # Mac /tmp and /var commonly are symlink aliases. Run tests with the
        # canonical temp root; the CLI rejects path aliases by design.
        self.root = Path(self.temp.name).resolve(strict=True)
        self.repo1 = self.root / "primary"
        self.repo2 = self.root / "independent"
        self.worktree = self.root / "linked-worktree"
        self.repo1.mkdir()
        self.repo2.mkdir()
        git("init", "-q", self.repo1)
        git("init", "-q", self.repo2)

    def tearDown(self):
        self.temp.cleanup()

    def _rejected(self, path, reason="PUBLIC_GIT_HTML_OUTPUT_FORBIDDEN"):
        with self.assertRaisesRegex(ValueError, reason):
            script._private_create(path, "SYNTHETIC_PRIVATE_BALANCE")
        self.assertFalse(Path(os.path.abspath(os.fspath(path))).exists())

    def test_main_checkout_refused_before_mkdir(self):
        target = self.repo1 / "artifacts" / "private" / "preview.html"
        self._rejected(target)
        self.assertFalse((self.repo1 / "artifacts").exists())

    def test_separate_independent_git_checkout_refused(self):
        target = self.repo2 / "artifacts" / "private-owner" / "preview.html"
        self._rejected(target)
        self.assertFalse((self.repo2 / "artifacts").exists())

    def test_linked_git_worktree_with_dot_git_file_refused(self):
        (self.repo1 / "README").write_text("synthetic", encoding="utf-8")
        git("-C", self.repo1, "add", "README")
        git("-C", self.repo1, "-c", "user.name=Fixture",
            "-c", "user.email=fixture@example.invalid",
            "commit", "-qm", "synthetic initial commit")
        git("-C", self.repo1, "worktree", "add", "--detach",
            "--quiet", self.worktree)
        self.assertTrue((self.worktree / ".git").is_file())
        self._rejected(self.worktree / "out" / "preview.html")

    def test_dotdot_reentering_other_checkout_is_refused(self):
        target = self.root / "outside" / ".." / "independent" / "owner" / "preview.html"
        self._rejected(target)
        self.assertFalse((self.repo2 / "owner").exists())

    def test_git_internal_metadata_path_is_also_refused(self):
        self._rejected(self.repo1 / ".git" / "nested" / "preview.html")

    def test_private_canonical_git_external_path_success_and_exclusive(self):
        target = self.root / "private" / "nested" / "owner-at-slot.html"
        saved = script._private_create(target, "SYNTHETIC_PRIVATE_BALANCE")
        self.assertEqual(saved, target)
        self.assertEqual(target.read_text(encoding="utf-8"),
                         "SYNTHETIC_PRIVATE_BALANCE")
        self.assertEqual(stat.S_IMODE(target.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(target.parent.stat().st_mode), 0o700)
        with self.assertRaises(FileExistsError):
            script._private_create(target, "SHOULD_NOT_OVERWRITE")
        self.assertEqual(target.read_text(encoding="utf-8"),
                         "SYNTHETIC_PRIVATE_BALANCE")

    def test_private_json_export_reuses_git_external_file_guard(self):
        target = self.root / "private-json" / "owner-source.json"
        saved = script._private_create(target, '{"synthetic":true}', suffix=".json")
        self.assertEqual(saved,target)
        self.assertEqual(stat.S_IMODE(target.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(target.parent.stat().st_mode), 0o700)
        with self.assertRaises(FileExistsError):
            script._private_create(target, "overwrite", suffix=".json")

    def test_private_json_export_refuses_independent_git_checkout(self):
        target=self.repo2 / "out" / "owner-source.json"
        with self.assertRaisesRegex(ValueError,"PUBLIC_GIT_HTML_OUTPUT_FORBIDDEN"):
            script._private_create(target, '{"synthetic":true}', suffix=".json")
        self.assertFalse((self.repo2 / "out").exists())

    def test_symlink_component_refused_even_to_private_external_directory(self):
        outside = self.root / "private-target"
        outside.mkdir(mode=0o700)
        alias = self.root / "alias"
        alias.symlink_to(outside, target_is_directory=True)
        target = alias / "preview.html"
        self._rejected(target, "PRIVATE_PREVIEW_SYMLINK_FORBIDDEN")

    def test_symlink_alias_to_git_checkout_refused(self):
        alias = self.root / "git-alias"
        alias.symlink_to(self.repo2, target_is_directory=True)
        self._rejected(alias / "preview.html",
                       "PRIVATE_PREVIEW_SYMLINK_FORBIDDEN")

    def test_macos_tmp_alias_policy_is_explicit(self):
        # If /tmp is a symlink (normal macOS), the CLI must reject the alias.
        if not Path("/tmp").is_symlink():
            self.skipTest("/tmp not a symlink on this runner")
        candidate = Path("/tmp") / self.root.name / "alias-preview.html"
        self._rejected(candidate, "PRIVATE_PREVIEW_SYMLINK_FORBIDDEN")


if __name__ == "__main__":
    unittest.main()
