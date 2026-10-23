"""Single-coordinator concrete HTTPS code exercised ONLY via sealed memory TLS.

Every relevant test patches the real HTTPSConnection constructor to deny.
There is no live permit, signer, RPC/WS, or untrusted transport callback.
"""
from dataclasses import replace
from datetime import timedelta
from hashlib import sha256
from pathlib import Path
import importlib
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import test_f0_l2_d1_integrated_exit as integrated_fixture
from f0_l2_d1_concrete_https import (
    SealedConcreteOfflineSource, _review_concrete_https_once,
    _REVIEW_TEST_ONLY_CAPABILITY, send_live as concrete_send_live)
from f0_l2_d1_integrated_exit import send_live as integrated_send_live
from f0_l2_d1_mac_provenance import (
    CRITICAL_MODULES, review_loaded_runtime_offline,
)


class D1ConcreteCoordinatorIntegrationTests(unittest.TestCase):
    def setUp(self):
        f=integrated_fixture.D1IntegratedExitTests(
            "test_exact_end_to_end_test_reference_once_raw_audit_and_exit_blocked")
        f.setUp()
        self.addCleanup(f.doCleanups)
        self.f=f

    def run_sealed(self, **options):
        source=options.pop("source",
                            SealedConcreteOfflineSource(
                                delay_ms=10, growth_bps=10.0))
        with patch("http.client.HTTPSConnection",
                   side_effect=AssertionError("EXTERNAL_SOCKET_FORBIDDEN")) as con:
            result=self.f.execute(source=source, **options)
            con.assert_not_called()
        return result, source

    def test_pinned_concrete_tls_connection_to_single_coordinator_and_audit(self):
        r,source=self.run_sealed()
        fake=r["test_one_use_session"]["session"]["fake"]
        self.assertEqual(fake["mode"],"D1_OFFLINE_CONCRETE_HTTPS_SEALED_NO_SOCKET")
        self.assertEqual(fake["reserved"],6)
        self.assertEqual(fake["settled"],6)
        self.assertEqual(fake["physically_started_fake"],6)
        self.assertEqual(fake["fake_post_utc_checks"],6)
        self.assertGreaterEqual(fake["min_actual_fake_start_gap_ms"],248.5)
        self.assertEqual(fake["contiguous_commits"],3)
        self.assertEqual(r["audit_status"],"OFFLINE_ACCOUNTED_NOT_LIVE")
        self.assertEqual(r["actual_rpc_requests"],0)
        self.assertEqual(source.block_count,3)
        self.assertEqual(len(list(self.f.f.registry.iterdir())),1)
        self.assertEqual(r["d1_exit"]["status"],"D1_BLOCKED_AUTHORITY")

    def test_expired_final_utc_with_concrete_tls_keeps_once_marker(self):
        f=self.f.f
        result, source=self.run_sealed(
            clock=lambda:f.now+timedelta(minutes=5))
        fake=result["test_one_use_session"]["session"]["fake"]
        self.assertEqual(fake["reserved"],1)
        self.assertEqual(fake["settled"],1)
        self.assertEqual(fake["physically_started_fake"],0)
        self.assertEqual(source.head_count,0)
        self.assertEqual(source.block_count,0)
        self.assertEqual(fake["contiguous_commits"],0)
        self.assertEqual(result["audit_status"],
                         "INVALID_FOR_PERFORMANCE_CLAIM")
        self.assertEqual(len(list(f.registry.iterdir())),1)
        newout=Path(f.temp.name).absolute()/"new_evidence"
        newout.mkdir(mode=0o700)
        f.out=newout
        with self.assertRaisesRegex(ValueError,"GRANT_ALREADY_CONSUMED"):
            self.run_sealed()

    def test_wrong_pin_rejected_before_concrete_connection_and_grant(self):
        f=self.f.f
        bad=replace(self.f.pins,permit_digest="a"*64)
        with self.assertRaisesRegex(ValueError,"PIN_BYTES_MISMATCH"):
            self.run_sealed(pins=bad)
        self.assertFalse(list(f.registry.iterdir()))
        self.assertFalse(list(f.out.iterdir()))

    def test_failure_503_fails_accounting_with_no_auto_retry(self):
        source=SealedConcreteOfflineSource(
            delay_ms=0,fail_head_after=1)
        r,_=self.run_sealed(source=source)
        fake=r["test_one_use_session"]["session"]["fake"]
        self.assertEqual(fake["stop"],"RPC_OR_HEAD_FAULT")
        self.assertEqual(fake["contiguous_commits"],0)
        self.assertEqual(fake["reserved"],fake["settled"])
        self.assertEqual(source.head_count,1)
        self.assertEqual(r["audit_status"],"INVALID_FOR_PERFORMANCE_CLAIM")
        self.assertEqual(len(list(self.f.f.registry.iterdir())),1)

    def test_concrete_raw_503_keeps_original_request_and_never_commits(self):
        source=SealedConcreteOfflineSource(
            delay_ms=0, fail_block_ordinal=1)
        r,_=self.run_sealed(source=source)
        fake=r["test_one_use_session"]["session"]["fake"]
        self.assertEqual(fake["stop"],"RPC_OR_HEAD_FAULT")
        self.assertEqual(fake["contiguous_commits"],0)
        self.assertEqual(r["audit_status"],"INVALID_FOR_PERFORMANCE_CLAIM")
        self.assertTrue((self.f.f.out/"attempts.jsonl").is_file())

    def test_unreviewed_constructor_or_live_entry_is_denied(self):
        request={"jsonrpc":"2.0","id":1,
                 "method":"eth_chainId","params":[]}
        with patch("http.client.HTTPSConnection",
                   side_effect=AssertionError("NO_NETWORK")) as ctor:
            with self.assertRaisesRegex(ValueError,"UNREVIEWED_FACTORY"):
                _review_concrete_https_once(
                    request,final_post_guard=lambda _:None,
                    _test_capability=_REVIEW_TEST_ONLY_CAPABILITY,
                    _sealed_offline_factory=lambda *_args,**_kwargs:None)
            with self.assertRaisesRegex(ValueError,"LIVE_DISABLED_REQUIRES_D2"):
                concrete_send_live()
            with self.assertRaisesRegex(ValueError,"BLOCKED_AUTHORITY"):
                integrated_send_live(execute_live=True)
            ctor.assert_not_called()


def git(root,*args):
    return subprocess.run(
        ["git","-C",str(root),*args],
        check=True,capture_output=True,text=True).stdout.strip()


class D1ActualModuleOriginAuditTests(unittest.TestCase):
    def setUp(self):
        self.dir=tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.root=Path(self.dir.name).absolute()
        git(self.root,"init","-q")
        git(self.root,"config","user.name","Test Source")
        git(self.root,"config","user.email","test@example.invalid")
        self.f0=(self.root/"crypto-300-profit-mission"/
                 "bsc-forward-follow-model"/"f0")
        self.f0.mkdir(parents=True)
        self.modules={}
        for modname in CRITICAL_MODULES:
            path=self.f0/(modname+".py")
            path.write_text("REVIEW_ONLY_FIXTURE=1\n")
            self.modules[modname]=types.SimpleNamespace(
                __file__=str(path),
                __spec__=types.SimpleNamespace(origin=str(path)))
        git(self.root,"add",".")
        git(self.root,"commit","-qm","synthetic audit baseline")
        self.sha=git(self.root,"rev-parse","HEAD")
        self.wheel={"distribution_version":"46.0.4",
                    "wheel_file_manifest_sha256":"a"*64,
                    "record_entries_without_hash":["RECORD"]}
    def test_actual_resolved_module_paths_digest_and_cryptography_report(self):
        with patch.dict(sys.modules,self.modules):
            with patch("f0_l2_d1_mac_provenance."
                       "installed_ed25519_distribution_inventory_offline",
                       return_value=self.wheel):
                report=review_loaded_runtime_offline(self.root,self.sha)
        self.assertEqual(report["source_commit_sha"],self.sha)
        self.assertEqual(len(report["critical_module_origins_checked"]),
                         len(CRITICAL_MODULES))
        self.assertEqual(report["wheel_entries_without_record_hash"],1)
        self.assertFalse(report["independent_reference_verified"])
        self.assertFalse(report["full_native_runtime_attested"])
        self.assertEqual(report["network_requests"],0)

    def test_import_shadowing_and_dirty_git_checkout_fail_closed(self):
        mod=CRITICAL_MODULES[0]
        orig=self.modules[mod]
        self.modules[mod]=types.SimpleNamespace(
            __file__="/tmp/other.py",
            __spec__=types.SimpleNamespace(origin="/tmp/other.py"))
        with patch.dict(sys.modules,self.modules):
            with self.assertRaisesRegex(ValueError,
                                        "UNREVIEWED_IMPORT_ORIGIN"):
                review_loaded_runtime_offline(self.root,self.sha)
        self.modules[mod]=orig
        (self.f0/(mod+".py")).write_text("modified\n")
        with patch.dict(sys.modules,self.modules):
            with self.assertRaisesRegex(ValueError,
                                        "CHECKOUT_DIRTY|CHECKOUT_BYTE_MISMATCH"):
                review_loaded_runtime_offline(self.root,self.sha)

    def test_missing_module_or_edited_sha_cannot_pass(self):
        self.modules.pop(CRITICAL_MODULES[0])
        with patch.dict(sys.modules,self.modules):
            with self.assertRaisesRegex(ValueError,
                                        "CRITICAL_MODULE_NOT_LOADED"):
                review_loaded_runtime_offline(self.root,self.sha)
        with self.assertRaises(ValueError):
            review_loaded_runtime_offline(self.root,"0"*40)


if __name__=="__main__":
    unittest.main()
