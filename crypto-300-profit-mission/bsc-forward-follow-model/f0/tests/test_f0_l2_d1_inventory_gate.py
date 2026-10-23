"""D1 one-use signed local inventory integration. No network, real grant or keys."""
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from f0_l2_d1_bundle import validate_offline_bundle
from f0_l2_d1_coordinator import SealedMemoryHTTPSSource
from f0_l2_d1_grant import approval_message
from f0_l2_d1_inventory_gate import (
    inventory_attestation_message, offline_inventory_statement,
    verify_test_inventory_attestation, consume_then_run_fake_once)


def git(root, *args):
    return subprocess.run(["git","-C",str(root),*args],
                          check=True,capture_output=True,
                          text=True).stdout.strip()


class D1InventoryGateTests(unittest.TestCase):
    def setUp(self):
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        tmp=Path(self.temp.name).absolute()
        self.repo=tmp/"reviewed"
        self.repo.mkdir(mode=0o700)
        git(self.repo,"init","-q")
        git(self.repo,"config","user.email","offline@example.invalid")
        git(self.repo,"config","user.name","Offline Audit")
        sub=self.repo/"crypto-300-profit-mission/bsc-forward-follow-model/f0"
        sub.mkdir(parents=True)
        (sub/"offline.py").write_text("print('no live')\n")
        git(self.repo,"add",".")
        git(self.repo,"commit","-qm","offline test")
        self.sha=git(self.repo,"rev-parse","HEAD")
        self.manifest={
            "crypto-300-profit-mission/bsc-forward-follow-model/f0/offline.py":
            sha256((sub/"offline.py").read_bytes()).hexdigest()}
        self.now=datetime(2026,10,23,8,0,30,tzinfo=timezone.utc)
        self.permit={
            "approved_commit_sha":self.sha,
            "grant_id":"offline-unique-demo-00001",
            "window_start_utc":"2026-10-23T08:00:00Z",
            "window_end_utc":"2026-10-23T08:01:00Z",
            "endpoint":"https://bsc-dataseed.bnbchain.org",
            "chain_id":56,
            "methods":["eth_chainId","eth_blockNumber","eth_getBlockByNumber"],
            "read_only":True,"free_only":True,"no_retries":True,
            "no_ws":True,"background":False,"no_proxy":True,
            "no_redirects":True,
            "max_total_attempts":9,"max_block_reads":3,
            "max_head_refreshes":4,"max_inflight":3,
            "min_start_gap_ms":250,"head_ttl_ms":4000,
            "request_timeout_ms":5000,"max_response_bytes":2000000,
            "max_dispatch_seconds":12,
        }
        self.raw=json.dumps(self.permit,separators=(",",":"),sort_keys=True).encode()
        self.keys={role:Ed25519PrivateKey.generate() for role in
                   ("user","reviewer")}
        self.trust={role:{
            "key_id":"temporary-"+role,
            "public_pem":key.public_key().public_bytes(
                Encoding.PEM,PublicFormat.SubjectPublicKeyInfo)}
            for role,key in self.keys.items()}
        digest=sha256(self.raw).hexdigest()
        self.proofs={role:{
            "key_id":self.trust[role]["key_id"],
            "signature":key.sign(approval_message(role,digest,self.sha))}
            for role,key in self.keys.items()}
        self.statement=json.dumps(
            offline_inventory_statement(self.raw,self.sha,self.repo),
            sort_keys=True,separators=(",",":")).encode()
        self.inv_proofs={role:{
            "key_id":self.trust[role]["key_id"],
            "signature":key.sign(
                inventory_attestation_message(role,self.statement,self.sha))}
            for role,key in self.keys.items()}
        self.registry=tmp/"registry"
        self.registry.mkdir(mode=0o700)
        self.out=tmp/"evidence"
        self.out.mkdir(mode=0o700)

    def verify(self,raw=None,statement=None,proofs=None):
        return verify_test_inventory_attestation(
            self.raw if raw is None else raw,self.sha,self.repo,
            self.statement if statement is None else statement,
            self.inv_proofs if proofs is None else proofs,self.trust)

    def execute_fake(self, source=None, raw=None, inv_proofs=None, now=None):
        return consume_then_run_fake_once(
            SealedMemoryHTTPSSource(delay_ms=10,growth_bps=10.0)
            if source is None else source,
            self.out,permit_raw=self.raw if raw is None else raw,
            expected_sha=self.sha,proofs=self.proofs,
            test_only_trust_roots=self.trust,
            checkout_root=self.repo,reviewed_files=self.manifest,
            now=self.now if now is None else now,
            raw_inventory_statement=self.statement,
            inventory_signatures=self.inv_proofs if inv_proofs is None else inv_proofs,
            offline_test_registry_root=self.registry)

    def test_independent_fake_signed_inventory_and_permit_are_bound(self):
        result=self.verify()
        self.assertEqual(result["status"],
                         "OFFLINE_INVENTORY_TEST_SIGNED_NOT_PRODUCTION_TRUSTED")
        self.assertFalse(result["complete_dependency_closure_attested"])
        self.assertFalse(result["production_trust_roots_enrolled"])

    def test_signed_inventory_rejects_mutation_missing_or_extra_fields(self):
        bad=dict(json.loads(self.statement),
                 python_executable_sha256="f"*64)
        with self.assertRaisesRegex(ValueError,"RUNTIME_BYTES_OR_SCOPE_MISMATCH"):
            self.verify(statement=json.dumps(bad).encode())
        altered=dict(json.loads(self.statement),new_feature="allow_network")
        with self.assertRaisesRegex(ValueError,"UNREVIEWED_FIELDS"):
            self.verify(statement=json.dumps(altered).encode())
        duplicate=self.statement[:-1]+b',"schema":"forged"}'
        with self.assertRaisesRegex(ValueError,"DUPLICATE_JSON_FIELD"):
            self.verify(statement=duplicate)
        bad=dict(json.loads(self.statement),
                 complete_dependency_closure_attested=True)
        with self.assertRaisesRegex(ValueError,"FALSE_PROVENANCE"):
            self.verify(statement=json.dumps(bad).encode())

    def test_swapped_inventory_role_and_bad_signature_denied(self):
        swapped=dict(self.inv_proofs,reviewer=self.inv_proofs["user"])
        with self.assertRaisesRegex(ValueError,"SIGNER_ROLE_MISMATCH"):
            self.verify(proofs=swapped)
        bad=dict(self.inv_proofs)
        bad["reviewer"]=dict(bad["reviewer"],signature=b"0"*64)
        with self.assertRaisesRegex(ValueError,"BAD_SIGNATURE"):
            self.verify(proofs=bad)

    def test_local_byte_change_invalidates_inventory_even_when_signed(self):
        path=self.repo/"crypto-300-profit-mission/bsc-forward-follow-model/f0/offline.py"
        path.write_text("tampered\n")
        with self.assertRaisesRegex(ValueError,"CHECKOUT_DIRTY"):
            self.verify()

    def test_registry_consumes_once_before_memory_https_and_no_retry(self):
        with patch("http.client.HTTPSConnection",
                   side_effect=AssertionError("real socket forbidden")):
            result=self.execute_fake()
        self.assertEqual(result["actual_rpc_requests"],0)
        self.assertEqual(result["mode"],
                         "OFFLINE_TEST_ONLY_ONE_USE_FAKE_SESSION")
        self.assertEqual(result["session"]["audit"]["audit_status"],
                         "OFFLINE_ACCOUNTED_NOT_LIVE")
        self.assertEqual(result["session"]["fake"]["contiguous_commits"],3)
        self.assertEqual(result["marker"]["status"],
                         "CONSUMED_NOT_A_NETWORK_AUTHORIZATION")
        entries=list(self.registry.iterdir())
        self.assertEqual(len(entries),1)
        self.assertEqual(entries[0].stat().st_mode & 0o077,0)
        with self.assertRaisesRegex(ValueError,"GRANT_ALREADY_CONSUMED"):
            self.execute_fake()
        self.assertEqual(len(list(self.registry.iterdir())),1)

    def test_bad_inputs_do_not_consume_or_start_fake(self):
        for case in ("expired","bad_inventory_signature","wrong_source"):
            with self.subTest(case=case):
                source=SealedMemoryHTTPSSource(delay_ms=0)
                if case=="wrong_source":
                    source.reply_over_memory_https=lambda *x: None
                kwargs={}
                if case=="expired":
                    kwargs["now"]=self.now+timedelta(minutes=5)
                if case=="bad_inventory_signature":
                    fake=dict(self.inv_proofs)
                    fake["user"]=dict(fake["user"],signature=b"0"*64)
                    kwargs["inv_proofs"]=fake
                with self.assertRaises(ValueError):
                    self.execute_fake(source=source,**kwargs)
                self.assertEqual(source.block_count,0)
                self.assertEqual(source.head_count,0)
                self.assertFalse(list(self.registry.iterdir()))
                self.assertFalse(list(self.out.iterdir()))

    def test_consumed_marker_survives_fake_failure_and_new_output_root(self):
        source=SealedMemoryHTTPSSource(delay_ms=0)
        # Cause a post-consume failure after the coordinator starts. Evidence
        # creation is deliberately impossible due to existing raw directory.
        (self.out/"raw_responses").mkdir(mode=0o700)
        with self.assertRaisesRegex(ValueError,"D1_RAW_DIRECTORY_ALREADY_EXISTS"):
            self.execute_fake(source=source)
        self.assertEqual(len(list(self.registry.iterdir())),1)
        self.assertEqual(source.head_count,0)
        self.out=Path(self.temp.name).absolute()/"fresh_output"
        self.out.mkdir(mode=0o700)
        with self.assertRaisesRegex(ValueError,"GRANT_ALREADY_CONSUMED"):
            self.execute_fake(source=source)
        self.assertFalse(list(self.out.iterdir()))

if __name__=="__main__":
    unittest.main()
