"""D1 offline signed dual approval + lease denial; NO REAL CREDENTIALS."""
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from multiprocessing import Process, Queue

F0 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(F0))
from f0_l2_d1_grant import (
    OfflineGrantRegistry, approval_message, sha,
    validate_approvals_offline, validate_live_trust_roots_not_enrolled)

SHA = "1"*40
GRANT = "offline-fixture-grant-0001"


def sample():
    return json.dumps({
        "approved_commit_sha":SHA, "grant_id":GRANT,
        "endpoint":"https://bsc-dataseed.bnbchain.org", "chain_id":56,
        "methods":["eth_chainId","eth_blockNumber","eth_getBlockByNumber"],
        "max_total_attempts":32, "max_block_reads":24,
        "max_head_refreshes":6, "min_start_gap_ms":250,
        "read_only":True, "free_only":True, "no_retries":True,
        "no_ws":True, "background":False,
    },sort_keys=True,separators=(",",":")).encode()


def take_claim(root, grant_id, digest, out):
    try:
        res=OfflineGrantRegistry(Path(root)).consume(grant_id,digest)
        out.put(res["status"])
    except ValueError as exc:
        out.put(str(exc))


class D1GrantGateTests(unittest.TestCase):
    def private(self):
        holder=tempfile.TemporaryDirectory()
        root=Path(holder.name)/"private"
        root.mkdir(mode=0o700)
        return holder,root

    def test_global_grant_id_not_reusable_even_if_output_changes(self):
        context,root=self.private()
        with context:
            lease=OfflineGrantRegistry(root)
            self.assertEqual(lease.consume(GRANT,sha(sample()))["status"],
                             "CONSUMED_NOT_A_NETWORK_AUTHORIZATION")
            with self.assertRaisesRegex(ValueError,"ALREADY_CONSUMED"):
                OfflineGrantRegistry(root).consume(GRANT, "f"*64)
            self.assertEqual(len(list(root.glob("*.consumed.json"))),1)

    def test_fixed_registry_factory_ignores_operator_output_directory(self):
        from unittest.mock import patch
        from f0_l2_d1_grant import FixedLocalGrantRegistry
        context,output_root=self.private()
        with context:
            # The fixed production root now binds to OS account home. Never
            # patch only PRIVATE_FIXED_REGISTRY to an arbitrary output root.
            fake_home=Path(context.name).resolve()/"simulated_mac_home"
            root=(fake_home/"Library"/"Application Support"/
                  "MissionEvidence"/"f0-grant-registry")
            root.mkdir(mode=0o700,parents=True)
            for folder in (fake_home, fake_home/"Library",
                           fake_home/"Library"/"Application Support",
                           root.parent):
                folder.chmod(0o700)
            with patch("f0_l2_d1_grant.platform.system",
                       return_value="Darwin"), patch(
                    "f0_l2_d1_grant._mac_os_account_home",
                    return_value=fake_home), patch(
                    "f0_l2_d1_grant.PRIVATE_FIXED_REGISTRY",root):
                FixedLocalGrantRegistry().consume(GRANT,sha(sample()))
                with self.assertRaisesRegex(ValueError,"ALREADY_CONSUMED"):
                    FixedLocalGrantRegistry().consume(GRANT,sha(sample()))
                self.assertFalse(list(output_root.iterdir()))

    def test_two_processes_compete_and_only_one_consumes(self):
        context,root=self.private()
        with context:
            out=Queue()
            p=[Process(target=take_claim,args=(str(root),GRANT,sha(sample()),out))
               for _ in range(2)]
            for t in p:t.start()
            for t in p:t.join(timeout=6)
            self.assertTrue(all(t.exitcode == 0 for t in p))
            outcomes=[out.get(timeout=3) for _ in p]
            self.assertEqual(outcomes.count("CONSUMED_NOT_A_NETWORK_AUTHORIZATION"),1)
            self.assertEqual(outcomes.count("D1_GRANT_ALREADY_CONSUMED"),1)

    def test_registry_cannot_be_symlink_or_world_readable(self):
        context,root=self.private()
        with context:
            alias=root.parent/"redirect"
            alias.symlink_to(root)
            with self.assertRaisesRegex(ValueError,"NOT_PRIVATE"):
                OfflineGrantRegistry(alias)
            root.chmod(0o755)
            with self.assertRaisesRegex(ValueError,"NOT_PRIVATE"):
                OfflineGrantRegistry(root)

    def test_registry_fsync_error_keeps_single_use_marker_consumed(self):
        from unittest.mock import patch
        context,root=self.private()
        with context:
            with patch("f0_l2_d1_grant.os.fsync",
                       side_effect=OSError("fault injection")):
                with self.assertRaisesRegex(ValueError,"CONSUMPTION_UNCERTAIN"):
                    OfflineGrantRegistry(root).consume(GRANT,sha(sample()))
            self.assertEqual(len(list(root.glob("*.consumed.json"))),1)
            with self.assertRaisesRegex(ValueError,"ALREADY_CONSUMED"):
                OfflineGrantRegistry(root).consume(GRANT,sha(sample()))

    def test_d1_has_no_enrolled_live_trust_roots(self):
        with self.assertRaisesRegex(ValueError,"NO_LIVE_TRUST_ROOT"):
            validate_live_trust_roots_not_enrolled()

    def test_cryptographic_signatures_are_role_bound_and_cannot_swap(self):
        from cryptography.hazmat.primitives.asymmetric.ed25519 import (
            Ed25519PrivateKey)
        from cryptography.hazmat.primitives.serialization import (
            Encoding, PublicFormat)
        from f0_l2_d1_grant import require_ed25519_backend
        require_ed25519_backend()
        anchors, proofs = {}, {}
        permit = sample()
        for role in ("user", "reviewer"):
            tempkey = Ed25519PrivateKey.generate()
            pub = tempkey.public_key().public_bytes(
                Encoding.PEM, PublicFormat.SubjectPublicKeyInfo)
            signature = tempkey.sign(approval_message(role, sha(permit), SHA))
            anchors[role] = {"key_id":role+"-test-only","public_pem":pub}
            proofs[role] = {"key_id":role+"-test-only","signature":signature}
        ok = validate_approvals_offline(permit,SHA,proofs,anchors)
        self.assertEqual(ok["verified_for"],"OFFLINE_FAKE_TEST_ONLY_NO_NETWORK")
        with self.assertRaises(ValueError):
            validate_approvals_offline(permit,SHA,
                {"user":proofs["reviewer"],"reviewer":proofs["user"]},anchors)
        with self.assertRaisesRegex(ValueError,"SIGNED_PROOF_INVALID"):
            changed={k:dict(v) for k,v in proofs.items()}
            changed["reviewer"]["signature"]=b"x"*64
            validate_approvals_offline(permit,SHA,changed,anchors)
        with self.assertRaisesRegex(ValueError,"SIGNED_PROOF_INVALID"):
            tampered=json.loads(permit)
            tampered["grant_id"]="a-different-offline-grant"
            validate_approvals_offline(
                json.dumps(tampered,sort_keys=True,
                           separators=(",",":")).encode(),SHA,proofs,anchors)
        with self.assertRaisesRegex(ValueError,"SAME_SIGNER_FORBIDDEN"):
            aliased={k:dict(v) for k,v in anchors.items()}
            aliased["reviewer"]["public_pem"]=aliased["user"]["public_pem"]
            forged={k:dict(v) for k,v in proofs.items()}
            forged["reviewer"]["signature"]=proofs["user"]["signature"]
            validate_approvals_offline(permit,SHA,forged,aliased)
        with self.assertRaisesRegex(ValueError,"PERMIT_SCOPE_INVALID"):
            tampered=json.loads(permit)
            tampered["max_total_attempts"]=33
            validate_approvals_offline(json.dumps(tampered).encode(),
                                       SHA,proofs,anchors)
        with self.assertRaisesRegex(ValueError,"PERMIT_SCOPE_INVALID"):
            tampered=json.loads(permit)
            tampered["approved_commit_sha"]="2"*40
            validate_approvals_offline(json.dumps(tampered).encode(),
                                       SHA,proofs,anchors)

    def test_backend_missing_or_wrong_version_denies_not_skips(self):
        from unittest.mock import patch
        from importlib.metadata import PackageNotFoundError
        from f0_l2_d1_grant import require_ed25519_backend
        with patch("f0_l2_d1_grant.version",return_value="0.0.0"):
            with self.assertRaisesRegex(ValueError,
                                        "D1_ED25519_BACKEND_VERSION_MISMATCH"):
                require_ed25519_backend()
        with patch("f0_l2_d1_grant.version",
                   side_effect=PackageNotFoundError("cryptography")):
            with self.assertRaisesRegex(ValueError,
                                        "D1_ED25519_BACKEND_UNAVAILABLE"):
                require_ed25519_backend()

    def test_other_algorithm_and_corrupted_ed25519_key_denied(self):
        from cryptography.hazmat.primitives.asymmetric import ec
        from cryptography.hazmat.primitives.serialization import (
            Encoding, PublicFormat)
        from f0_l2_d1_grant import _public_key_fingerprint
        another = ec.generate_private_key(
            ec.SECP256R1()).public_key().public_bytes(
                Encoding.PEM,PublicFormat.SubjectPublicKeyInfo)
        with self.assertRaisesRegex(ValueError,"D1_PUBLIC_KEY_NOT_ED25519"):
            _public_key_fingerprint(another)
        with self.assertRaisesRegex(ValueError,"D1_PUBLIC_KEY_PARSE_FAILED"):
            _public_key_fingerprint(b"-----BEGIN PUBLIC KEY-----\nnot-a-key\n")


if __name__=="__main__":
    unittest.main()
