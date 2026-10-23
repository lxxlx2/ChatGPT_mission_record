"""Detached reviewer reference pins are verified before local byte checks.

Entire test is offline; keys and pins are disposable synthetic inputs.
"""
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from f0_l2_d1_grant import _public_key_fingerprint
from f0_l2_d1_inventory_gate import inventory_attestation_message
from f0_l2_d1_review_pins import OfflineReviewerPins, verify_pinned_offline_evidence
import test_f0_l2_d1_inventory_gate as fixture_module


class D1ReviewerPinsTests(unittest.TestCase):
    def setUp(self):
        self.fixture=fixture_module.D1InventoryGateTests(
            "test_independent_fake_signed_inventory_and_permit_are_bound")
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        f=self.fixture
        self.pins=OfflineReviewerPins(
            source_sha=f.sha,
            permit_digest=sha256(f.raw).hexdigest(),
            inventory_digest=sha256(f.statement).hexdigest(),
            user_fingerprint=_public_key_fingerprint(f.trust["user"]["public_pem"]),
            reviewer_fingerprint=_public_key_fingerprint(
                f.trust["reviewer"]["public_pem"]))

    def verify(self,**kwargs):
        f=self.fixture
        return verify_pinned_offline_evidence(
            kwargs.get("permit",f.raw),kwargs.get("sha",f.sha),
            f.repo,kwargs.get("inventory",f.statement),
            kwargs.get("proofs",f.inv_proofs),
            kwargs.get("roots",f.trust),
            kwargs.get("pins",self.pins))

    def test_valid_exact_pins_remain_non_authorizing(self):
        result=self.verify()
        self.assertEqual(result["status"],
                         "OFFLINE_EXTERNAL_PIN_MATCH_NOT_AUTHORIZATION")
        self.assertFalse(result["independent_pin_origin_authenticated"])
        self.assertFalse(result["complete_dependency_closure_attested"])
        self.assertFalse(result["production_trust_roots_enrolled"])
        self.assertEqual(result["actual_rpc_requests"],0)

    def test_changed_permit_or_sha_cannot_match_reviewed_reference(self):
        with self.assertRaisesRegex(ValueError,"PIN_BYTES_MISMATCH"):
            self.verify(permit=self.fixture.raw+b" ")
        with self.assertRaisesRegex(ValueError,"PIN_BYTES_MISMATCH"):
            self.verify(sha="f"*40)
        with self.assertRaisesRegex(ValueError,"PIN_FORMAT_INVALID"):
            self.verify(pins=replace(self.pins,permit_digest="bad"))

    def test_changed_inventory_requires_both_valid_pin_and_real_local_bytes(self):
        f=self.fixture
        altered=json.loads(f.statement)
        altered["python_executable_sha256"]="f"*64
        new_bytes=json.dumps(altered,sort_keys=True).encode()
        with self.assertRaisesRegex(ValueError,"PIN_BYTES_MISMATCH"):
            self.verify(inventory=new_bytes)
        new_proofs={role:dict(old,signature=f.keys[role].sign(
            inventory_attestation_message(role,new_bytes,f.sha)))
            for role,old in f.inv_proofs.items()}
        re_pinned=replace(self.pins,inventory_digest=sha256(new_bytes).hexdigest())
        with self.assertRaisesRegex(ValueError,"RUNTIME_BYTES_OR_SCOPE_MISMATCH"):
            self.verify(inventory=new_bytes,proofs=new_proofs,pins=re_pinned)

    def test_different_role_keys_fail_even_with_correct_inventory(self):
        f=self.fixture
        switched={"user":f.trust["reviewer"],"reviewer":f.trust["user"]}
        with self.assertRaisesRegex(ValueError,"PIN_KEY_MISMATCH"):
            self.verify(roots=switched)
        duplicated=replace(self.pins,
                           reviewer_fingerprint=self.pins.user_fingerprint)
        with self.assertRaisesRegex(ValueError,"PIN_ROLES_INVALID"):
            self.verify(pins=duplicated)

    def test_source_mutation_rejected_after_successful_pin_matches(self):
        f=self.fixture
        path=f.repo/"crypto-300-profit-mission/bsc-forward-follow-model/f0/offline.py"
        path.write_text("different bytes")
        with self.assertRaisesRegex(ValueError,"CHECKOUT_DIRTY"):
            self.verify()

    def test_attestation_cannot_assert_full_dependency_closure(self):
        f=self.fixture
        changed=json.loads(f.statement)
        changed["complete_dependency_closure_attested"]=True
        new_bytes=json.dumps(changed,sort_keys=True).encode()
        proofs={role:dict(old,signature=f.keys[role].sign(
            inventory_attestation_message(role,new_bytes,f.sha)))
            for role,old in f.inv_proofs.items()}
        pins=replace(self.pins,inventory_digest=sha256(new_bytes).hexdigest())
        with self.assertRaisesRegex(ValueError,"UNREVIEWED_FIELDS_OR_FALSE_PROVENANCE"):
            self.verify(inventory=new_bytes,proofs=proofs,pins=pins)


if __name__=="__main__":
    unittest.main()
