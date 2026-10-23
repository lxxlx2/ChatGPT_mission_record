"""D1 offline signed dual approval + lease denial; NO REAL CREDENTIALS."""
import json
import os
from pathlib import Path
import subprocess
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
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            anchors={}
            proofs={}
            permit=sample()
            for role in ("user","reviewer"):
                priv=root/(role+".priv.pem")
                pub=root/(role+".pub.pem")
                data=root/(role+".msg")
                sig=root/(role+".sig")
                subprocess.run(["/usr/bin/openssl","genpkey","-algorithm","ED25519",
                                "-out",str(priv)],check=True,capture_output=True)
                subprocess.run(["/usr/bin/openssl","pkey","-in",str(priv),
                                "-pubout","-out",str(pub)],check=True,capture_output=True)
                data.write_bytes(approval_message(role,sha(permit),SHA))
                subprocess.run(["/usr/bin/openssl","pkeyutl","-sign",
                                "-inkey",str(priv),"-rawin",
                                "-in",str(data),"-out",str(sig)],
                               check=True,capture_output=True)
                anchors[role]={"key_id":role+"-test-only",
                               "public_pem":pub.read_bytes()}
                proofs[role]={"key_id":role+"-test-only",
                              "signature":sig.read_bytes()}
            ok=validate_approvals_offline(permit,SHA,proofs,anchors)
            self.assertEqual(ok["verified_for"],"OFFLINE_FAKE_TEST_ONLY_NO_NETWORK")
            with self.assertRaises(ValueError):
                validate_approvals_offline(permit,SHA,
                    {"user":proofs["reviewer"],"reviewer":proofs["user"]},anchors)
            with self.assertRaisesRegex(ValueError,"SIGNED_PROOF_INVALID"):
                changed=dict(proofs)
                changed["reviewer"]=dict(proofs["reviewer"])
                changed["reviewer"]["signature"]=b"x"*64
                validate_approvals_offline(permit,SHA,changed,anchors)
            with self.assertRaisesRegex(ValueError,"SIGNED_PROOF_INVALID"):
                tampered=json.loads(permit)
                tampered["grant_id"]="a-different-offline-grant"
                validate_approvals_offline(
                    json.dumps(tampered,sort_keys=True,
                               separators=(",",":")).encode(),
                    SHA,proofs,anchors)
            # An attacker cannot relabel the SAME public key as an
            # independent reviewer, even if an alias key ID differs.
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


if __name__=="__main__":
    unittest.main()
