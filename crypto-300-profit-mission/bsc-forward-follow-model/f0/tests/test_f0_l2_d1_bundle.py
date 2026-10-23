"""D1 compositional offline gate: transient Ed25519 keys, fake network only."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from f0_l2_d1_bundle import (run_gated_fake_session,
                             validate_offline_bundle)
from f0_l2_d1_coordinator import FakeSource
from f0_l2_d1_grant import approval_message


def run_git(folder,*args):
    result=subprocess.run(["git","-C",str(folder),*args],
                          capture_output=True,check=True,text=True)
    return result.stdout.strip()


class D1BundleTests(unittest.TestCase):
    def setUp(self):
        from cryptography.hazmat.primitives.asymmetric.ed25519 import (
            Ed25519PrivateKey)
        from cryptography.hazmat.primitives.serialization import (
            Encoding, PublicFormat)
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo=Path(self.tmp.name).absolute()/"reviewed"
        self.repo.mkdir(mode=0o700)
        run_git(self.repo,"init","-q")
        run_git(self.repo,"config","user.email","offline@example.invalid")
        run_git(self.repo,"config","user.name","Offline Review")
        self.fixture=self.repo/"fixed_module.py"
        self.fixture.write_bytes(b"OFFLINE SOURCE BYTES\n")
        run_git(self.repo,"add","fixed_module.py")
        run_git(self.repo,"commit","-qm","fake fixed code")
        self.sha=run_git(self.repo,"rev-parse","HEAD")
        self.manifest={"fixed_module.py":sha256(
            self.fixture.read_bytes()).hexdigest()}
        self.now=datetime(2026,10,23,8,0,30,tzinfo=timezone.utc)
        self.permit={
            "approved_commit_sha":self.sha,
            "grant_id":"offline-bundle-fixture-00001",
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
        self.keys={k:Ed25519PrivateKey.generate()
                   for k in ("user","reviewer")}
        self.trust={role:{
            "key_id":"ephemeral-"+role,
            "public_pem":key.public_key().public_bytes(
                Encoding.PEM,PublicFormat.SubjectPublicKeyInfo)
        } for role,key in self.keys.items()}

    def signed(self,fields=None,original=None):
        fields=self.permit if fields is None else fields
        raw=(json.dumps(fields,sort_keys=True,separators=(",",":")).encode()
             if original is None else original)
        digest=sha256(raw).hexdigest()
        proofs={
            role:{"key_id":"ephemeral-"+role,
                  "signature":key.sign(
                      approval_message(role,digest,self.sha))}
            for role,key in self.keys.items()
        }
        return raw,proofs

    def validate(self,raw,proofs,**kw):
        return validate_offline_bundle(
            raw,kw.get("sha",self.sha),proofs,
            kw.get("trust_roots",self.trust),
            self.repo,kw.get("manifest",self.manifest),
            kw.get("now",self.now))

    def test_composed_signed_scope_and_source_are_bound(self):
        raw,proofs=self.signed()
        answer=self.validate(raw,proofs)
        self.assertEqual(answer["status"],
                         "OFFLINE_BUNDLE_VALIDATED_NO_NETWORK_PERMISSION")
        self.assertEqual(answer["code_sha"],self.sha)
        self.assertTrue(answer["fake_only"])
        self.assertFalse(answer["real_grant_activated"])
        self.assertEqual(answer["manifest_entries_checked"],1)

    def test_utc_or_other_field_mutation_breaks_signed_approval(self):
        raw,proofs=self.signed()
        altered=dict(self.permit,window_end_utc="2026-10-23T08:03:00Z")
        changed,_=self.signed(altered)
        with self.assertRaisesRegex(ValueError,"D1_SIGNED_PROOF_INVALID"):
            self.validate(changed,proofs)
        for name, value in [
            ("max_total_attempts",33),
            ("no_proxy",False),
            ("approved_commit_sha","f"*40),
        ]:
            with self.subTest(name=name):
                amended=dict(self.permit,**{name:value})
                altered,proof=self.signed(amended)
                with self.assertRaises(ValueError):
                    self.validate(altered,proof)

    def test_duplicate_and_unknown_signed_fields_rejected(self):
        raw,proofs=self.signed()
        duplicate=raw[:-1]+b',"grant_id":"other-offline-grant"}'
        with self.assertRaisesRegex(ValueError,"DUPLICATE_JSON_FIELD"):
            self.validate(duplicate,proofs)
        extra=dict(self.permit,unreviewed_switch=True)
        unexpected,proof=self.signed(extra)
        with self.assertRaisesRegex(ValueError,"UNREVIEWED_PERMIT_FIELDS"):
            self.validate(unexpected,proof)

    def test_wrong_signer_and_mismatched_worktree_fails(self):
        raw,proofs=self.signed()
        changed=dict(proofs)
        changed["user"]=proofs["reviewer"]
        with self.assertRaises(ValueError):
            self.validate(raw,changed)
        with self.assertRaisesRegex(ValueError,"D1_CHECKOUT_BYTE_MISMATCH"):
            self.validate(raw,proofs,manifest={"fixed_module.py":"f"*64})
        self.fixture.write_text("altered")
        with self.assertRaisesRegex(ValueError,"D1_CHECKOUT_DIRTY"):
            self.validate(raw,proofs)

    def test_signature_gate_precedes_any_fake_source_or_disk_evidence(self):
        raw,proofs=self.signed()
        changed=dict(proofs)
        changed["reviewer"]=dict(proofs["reviewer"],signature=b"0"*64)
        output=Path(self.tmp.name).absolute()/"evidence"
        output.mkdir(mode=0o700)
        fake=FakeSource(delay_ms=0)
        with self.assertRaisesRegex(ValueError,"D1_SIGNED_PROOF_INVALID"):
            run_gated_fake_session(
                fake,output,permit_raw=raw,expected_sha=self.sha,
                proofs=changed,test_only_trust_roots=self.trust,
                checkout_root=self.repo,reviewed_files=self.manifest,
                now=self.now)
        self.assertEqual(fake.head_count,0)
        self.assertEqual(fake.block_count,0)
        self.assertEqual(list(output.iterdir()),[])

    def test_full_fake_rehearsal_parsed_and_audited_without_live_network(self):
        raw,proofs=self.signed()
        output=Path(self.tmp.name).absolute()/"evidence"
        output.mkdir(mode=0o700)
        fake=FakeSource(growth_bps=10.0,delay_ms=15)
        result=run_gated_fake_session(
            fake,output,permit_raw=raw,expected_sha=self.sha,
            proofs=proofs,test_only_trust_roots=self.trust,
            checkout_root=self.repo,reviewed_files=self.manifest,
            now=self.now)
        self.assertEqual(result["actual_rpc_requests"],0)
        self.assertEqual(result["real_permit"],"NOT_CREATED_NOT_ACTIVATED")
        self.assertEqual(result["fake"]["network_requests"],0)
        self.assertEqual(result["audit"]["audit_status"],
                         "OFFLINE_ACCOUNTED_NOT_LIVE")
        self.assertGreaterEqual(result["audit"]["contiguous_commits"],1)
        self.assertEqual(result["audit"]["contiguous_commits"],
                         result["fake"]["contiguous_commits"])
        self.assertLessEqual(result["fake"]["reserved"],9)
        self.assertLessEqual(result["fake"]["max_shared_slots"],3)
        self.assertEqual(result["production"],"NO_GO")

    def test_expired_valid_signed_bundle_stops_before_evidence_or_fake(self):
        from datetime import timedelta
        raw,proofs=self.signed()
        output=Path(self.tmp.name).absolute()/"evidence"
        output.mkdir(mode=0o700)
        source=FakeSource(delay_ms=0)
        with self.assertRaisesRegex(ValueError,"D1_UTC_WINDOW_INACTIVE"):
            run_gated_fake_session(
                source,output,permit_raw=raw,expected_sha=self.sha,
                proofs=proofs,test_only_trust_roots=self.trust,
                checkout_root=self.repo,reviewed_files=self.manifest,
                now=self.now+timedelta(hours=1))
        self.assertEqual(source.head_count,0)
        self.assertEqual(source.block_count,0)
        self.assertFalse((output/"attempts.jsonl").exists())

    def test_fake_callable_override_is_not_an_approved_source(self):
        raw,proofs=self.signed()
        root=Path(self.tmp.name).absolute()/"evidence"
        root.mkdir(mode=0o700)
        fake=FakeSource(delay_ms=0)
        fake.reply=lambda req: 0
        with self.assertRaisesRegex(ValueError,"D1_BUNDLE_FAKE_SOURCE_ONLY"):
            run_gated_fake_session(
                fake,root,permit_raw=raw,expected_sha=self.sha,
                proofs=proofs,test_only_trust_roots=self.trust,
                checkout_root=self.repo,reviewed_files=self.manifest,
                now=self.now)
        self.assertFalse((root/"attempts.jsonl").exists())


if __name__=="__main__":
    unittest.main()
