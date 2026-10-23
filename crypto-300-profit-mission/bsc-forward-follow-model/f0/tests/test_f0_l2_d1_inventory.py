"""Source / crypto wheel byte inventory tests: all offline."""
import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from f0_l2_d1_inventory import (
    tracked_f0_source_manifest_offline,
    installed_ed25519_distribution_inventory_offline,
)
from f0_l2_d1_grant import require_ed25519_backend

def git(root,*args):
    return subprocess.run(["git","-C",str(root),*args],check=True,
                          capture_output=True,text=True).stdout.strip()

class D1InventoryTests(unittest.TestCase):
    def fixture(self):
        temp=tempfile.TemporaryDirectory()
        root=Path(temp.name).absolute()/"repo"
        root.mkdir()
        git(root,"init","-q")
        git(root,"config","user.name","Offline Auditor")
        git(root,"config","user.email","offline@example.invalid")
        d=root/"crypto-300-profit-mission/bsc-forward-follow-model/f0"
        d.mkdir(parents=True)
        (d/"first.py").write_bytes(b"import sys\n")
        (d/"second.py").write_bytes(b"import json\n")
        git(root,"add",".")
        git(root,"commit","-qm","fixture")
        return temp,root,d,git(root,"rev-parse","HEAD")

    def test_all_tracked_files_and_clean_checkout(self):
        temp,root,d,sha=self.fixture()
        with temp:
            r=tracked_f0_source_manifest_offline(root,sha)
            self.assertEqual(r["all_tracked_f0_files_checked"],2)
            self.assertEqual(len(r["reviewed_path_digests"]),2)
            self.assertEqual(len(r["tracked_source_manifest_sha256"]),64)
            self.assertIn("NOT_INDEPENDENT_ATTESTATION",r["status"])
            (d/"first.py").write_bytes(b"tampered")
            with self.assertRaisesRegex(ValueError,"CHECKOUT_DIRTY"):
                tracked_f0_source_manifest_offline(root,sha)
            (d/"first.py").write_bytes(b"import sys\n")
            (root/"untracked").write_bytes(b"x")
            with self.assertRaisesRegex(ValueError,"CHECKOUT_DIRTY"):
                tracked_f0_source_manifest_offline(root,sha)

    def test_git_head_and_symlinked_file_cannot_pass(self):
        temp,root,d,sha=self.fixture()
        with temp:
            with self.assertRaises(ValueError):
                tracked_f0_source_manifest_offline(root,"0"*40)
            (d/"linked.py").symlink_to(d/"first.py")
            git(root,"add",".")
            git(root,"commit","-qm","symlink fixture")
            newsha=git(root,"rev-parse","HEAD")
            with self.assertRaisesRegex(ValueError,"TRACKED_SYMLINK"):
                tracked_f0_source_manifest_offline(root,newsha)

    def test_wheel_record_bytes_are_checked_but_not_authoritative(self):
        require_ed25519_backend()
        r=installed_ed25519_distribution_inventory_offline()
        self.assertEqual(r["distribution_version"],"46.0.4")
        self.assertGreater(r["files_read"],1)
        self.assertEqual(len(r["wheel_file_manifest_sha256"]),64)
        self.assertFalse(r["complete_dynamic_import_closure_attested"])
        self.assertFalse(r["interpreter_and_stdlib_externally_attested"])
        self.assertFalse(r["production_trust_roots_enrolled"])

if __name__=="__main__":
    unittest.main()
