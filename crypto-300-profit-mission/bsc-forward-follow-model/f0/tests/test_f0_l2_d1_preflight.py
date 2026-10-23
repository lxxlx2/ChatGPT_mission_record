"""D1 preflight: isolated Git repository fixtures, no network or permit."""
from datetime import datetime, timezone, timedelta
import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from f0_l2_d1_preflight import (validate_window_contract,
                                verify_fixed_checkout_offline)

def test_permit():
    return dict(
        window_start_utc="2026-10-23T08:00:00Z",
        window_end_utc="2026-10-23T08:01:00Z",
        approved_commit_sha="a"*40,
        endpoint="https://bsc-dataseed.bnbchain.org", chain_id=56,
        methods=["eth_chainId","eth_blockNumber","eth_getBlockByNumber"],
        read_only=True, no_ws=True, no_retries=True, free_only=True,
        background=False, no_proxy=True, no_redirects=True,
        max_total_attempts=32, max_block_reads=24, max_head_refreshes=6,
        max_inflight=3, min_start_gap_ms=250, head_ttl_ms=4000,
        request_timeout_ms=5000, max_response_bytes=2_000_000,
        max_dispatch_seconds=60)

def git(root, *args):
    subprocess.run(["git","-C",str(root),*args],check=True,
                   capture_output=True)

class D1PreflightTests(unittest.TestCase):
    def test_utc_contract_exact_bounds_and_unknown_authority(self):
        p=test_permit()
        now=datetime(2026,10,23,8,0,30,tzinfo=timezone.utc)
        out=validate_window_contract(p,now)
        self.assertEqual(out["validated_for"],
                         "OFFLINE_SCOPE_ONLY_NO_LIVE_PERMISSION")
        self.assertEqual(out["dispatch_seconds_cap"],60)
        for later in (now-timedelta(days=1),now+timedelta(minutes=5)):
            with self.assertRaisesRegex(ValueError,"WINDOW_INACTIVE"):
                validate_window_contract(p,later)
        for invalid in ("2026-10-23T08:00:00+00:00",
                        "2026-10-23T08:00:00", "bad"):
            mutated=dict(p,window_start_utc=invalid)
            with self.assertRaises(ValueError):
                validate_window_contract(mutated,now)
        p["window_start_utc"]="2026-10-23T08:00:00Z"
        p["window_end_utc"]="2026-10-23T08:11:00Z"
        with self.assertRaisesRegex(ValueError,"WINDOW_INACTIVE"):
            validate_window_contract(p,now)

    def test_utc_contract_resource_and_destination_fail_closed(self):
        now=datetime(2026,10,23,8,0,30,tzinfo=timezone.utc)
        examples=(
            ("max_total_attempts",33),("max_inflight",4),
            ("min_start_gap_ms",249),("request_timeout_ms",5001),
            ("max_response_bytes",2000001),("head_ttl_ms",4001),
            ("max_dispatch_seconds",61),("endpoint","https://example.org"),
            ("no_proxy",False),("read_only",False),("max_block_reads",25),
        )
        for k,v in examples:
            with self.subTest(field=k):
                with self.assertRaises(ValueError):
                    validate_window_contract(dict(test_permit(),**{k:v}),now)

    def test_exact_git_head_clean_files_and_symlink_denial(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d).absolute()/"repo"
            root.mkdir()
            git(root,"init","-q")
            git(root,"config","user.email","offline-test@example.invalid")
            git(root,"config","user.name","Offline Test")
            script=root/"src"
            script.mkdir()
            f=script/"coordinator.py"
            f.write_text("offline only\n")
            git(root,"add","src/coordinator.py")
            git(root,"commit","-qm","offline fixture")
            sha=subprocess.run(["git","-C",str(root),"rev-parse","HEAD"],
                               capture_output=True,check=True,text=True).stdout.strip()
            manifest={"src/coordinator.py":hashlib.sha256(f.read_bytes()).hexdigest()}
            self.assertEqual(verify_fixed_checkout_offline(root,sha,manifest)
                             ["verified_files"],1)
            with self.assertRaisesRegex(ValueError,"HEAD_MISMATCH"):
                verify_fixed_checkout_offline(root,"0"*40,manifest)
            f.write_text("mutated\n")
            with self.assertRaisesRegex(ValueError,"DIRTY"):
                verify_fixed_checkout_offline(root,sha,manifest)
            f.write_text("offline only\n")
            (root/"scratch").write_text("untracked")
            with self.assertRaisesRegex(ValueError,"DIRTY"):
                verify_fixed_checkout_offline(root,sha,manifest)
            (root/"scratch").unlink()
            with self.assertRaisesRegex(ValueError,"BYTE_MISMATCH"):
                verify_fixed_checkout_offline(root,sha,{"src/coordinator.py":"f"*64})
            alias=root/"link"
            alias.symlink_to(script,target_is_directory=True)
            git(root,"add","link")
            git(root,"commit","-qm","tracked symlink fixture")
            tracked_sha=subprocess.run(["git","-C",str(root),"rev-parse","HEAD"],
                                      capture_output=True,check=True,
                                      text=True).stdout.strip()
            with self.assertRaisesRegex(ValueError,"SYMLINK_DISALLOWED"):
                verify_fixed_checkout_offline(root,tracked_sha,
                    {"link/coordinator.py":manifest["src/coordinator.py"]})
            with self.assertRaisesRegex(ValueError,"MANIFEST_INVALID"):
                verify_fixed_checkout_offline(root,tracked_sha,{"../bad":"a"*64})

if __name__=="__main__":
    unittest.main()
