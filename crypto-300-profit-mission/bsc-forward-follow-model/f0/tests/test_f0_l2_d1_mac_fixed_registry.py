"""D1 fixed OS-account one-use registry: ephemeral LOCAL test directories only.

No production registry, socket, real grants, signer, or user permit is read.
"""
from hashlib import sha256
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from f0_l2_d1_grant import (
    FixedLocalGrantRegistry, OfflineGrantRegistry,
)
from f0_l2_d1_protected_mac_entry import send_live as mac_send_live
from f0_l2_d1_integrated_exit import send_live as integrated_send_live

GRANT_ID = "offline-fixed-root-001"
PERMIT_SHA = "a"*64


class D1MacFixedGrantRegistryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        # macOS /var/folders is an alias: model an actual canonical OS home.
        self.home = Path(self.tmp.name).resolve() / "fake_mac_home"
        self.home.mkdir(mode=0o700)
        self.registry = (self.home / "Library" / "Application Support" /
                         "MissionEvidence" / "f0-grant-registry")
        self.registry.mkdir(mode=0o700, parents=True)
        for parent in (self.home / "Library",
                       self.home / "Library" / "Application Support",
                       self.registry.parent):
            parent.chmod(0o700)
        self.ctx = [
            patch("f0_l2_d1_grant.platform.system", return_value="Darwin"),
            patch("f0_l2_d1_grant._mac_os_account_home",
                  return_value=self.home),
            patch("f0_l2_d1_grant.PRIVATE_FIXED_REGISTRY", self.registry),
        ]
        for c in self.ctx:
            c.start()
            self.addCleanup(c.stop)

    def test_exact_os_home_root_consumes_once_and_fsync_marker(self):
        with patch("http.client.HTTPSConnection",
                   side_effect=AssertionError("NETWORK_FORBIDDEN")) as socket:
            session = FixedLocalGrantRegistry()
            result = session.consume(GRANT_ID, PERMIT_SHA)
            socket.assert_not_called()
        self.assertEqual(result["status"],
                         "CONSUMED_NOT_A_NETWORK_AUTHORIZATION")
        markers = list(self.registry.iterdir())
        self.assertEqual(len(markers), 1)
        self.assertEqual(markers[0].stat().st_mode & 0o777, 0o600)
        saved = markers[0].read_bytes()
        row = json.loads(saved)
        self.assertEqual(row["permit_sha256"], PERMIT_SHA)
        self.assertEqual(row["outcome"],"CONSUMED_OR_UNKNOWN")
        with self.assertRaisesRegex(ValueError,"GRANT_ALREADY_CONSUMED"):
            FixedLocalGrantRegistry().consume(GRANT_ID, "b"*64)
        self.assertEqual(markers[0].read_bytes(),saved)

    def test_permit_output_root_home_override_cannot_change_fixed_registry(self):
        with patch.dict(os.environ,{"HOME":str(Path(self.tmp.name)/"fake") }):
            root = FixedLocalGrantRegistry()
            self.assertEqual(root.root,self.registry)
            self.assertEqual(list(self.registry.iterdir()),[])
        with patch("f0_l2_d1_grant.PRIVATE_FIXED_REGISTRY",
                   Path(self.tmp.name).resolve()/"other-root"):
            with self.assertRaisesRegex(ValueError,"NOT_OS_HOME_BOUND"):
                FixedLocalGrantRegistry()
        self.assertEqual(list(self.registry.iterdir()),[])

    def test_symlinked_ancestor_denied_without_a_consumption_marker(self):
        original=self.home/"Library"
        renamed=self.home/"Library.real"
        original.rename(renamed)
        original.symlink_to(renamed,target_is_directory=True)
        self.addCleanup(lambda: original.is_symlink() and original.unlink())
        with self.assertRaisesRegex(ValueError,"SYMLINK_OR_NONDIR"):
            FixedLocalGrantRegistry()
        self.assertFalse(list(self.registry.iterdir()))

    def test_insecure_mode_or_missing_root_denied(self):
        self.registry.chmod(0o755)
        with self.assertRaisesRegex(ValueError,"NOT_PRIVATE_0700"):
            FixedLocalGrantRegistry()
        self.registry.chmod(0o700)
        self.registry.rmdir()
        with self.assertRaisesRegex(ValueError,"MISSING_OR_UNREADABLE"):
            FixedLocalGrantRegistry()
        self.assertFalse(self.registry.exists())

    def test_os_account_owner_and_parent_group_write_denied(self):
        lib = self.home/"Library"
        lib.chmod(0o777)
        self.addCleanup(lambda: lib.chmod(0o700))
        with self.assertRaisesRegex(ValueError,"OWNER_OR_PARENT_MODE"):
            FixedLocalGrantRegistry()
        self.assertEqual(list(self.registry.iterdir()),[])

    def test_mac_only_and_inode_replacement_deny_grant(self):
        with patch("f0_l2_d1_grant.platform.system",return_value="Linux"):
            with self.assertRaisesRegex(ValueError,"MAC_ONLY"):
                FixedLocalGrantRegistry()
        session=FixedLocalGrantRegistry()
        moved=self.registry.with_name("f0-grant-registry.old")
        self.registry.rename(moved)
        self.registry.mkdir(mode=0o700)
        with self.assertRaisesRegex(ValueError,"REPLACED"):
            session.consume(GRANT_ID,PERMIT_SHA)
        self.assertFalse(list(moved.iterdir()))
        self.assertFalse(list(self.registry.iterdir()))

    def test_opened_dir_inode_check_prevents_consumption(self):
        root=FixedLocalGrantRegistry()
        with patch.object(OfflineGrantRegistry,"consume",autospec=True,
                          wraps=None) as underlying:
            # Identity matches at the boundary; real O_EXCL is covered by
            # the successful case above.
            root.consume(GRANT_ID,PERMIT_SHA)
            self.assertEqual(underlying.call_args.kwargs["expected_dev_inode"],
                             (root.device,root.inode))
        with self.assertRaisesRegex(ValueError,"OPEN_DIR_IDENTITY_CHANGED"):
            OfflineGrantRegistry(self.registry).consume(
                GRANT_ID, PERMIT_SHA, expected_dev_inode=(0,0))
        self.assertEqual(list(self.registry.iterdir()),[])

    def test_existing_all_live_entries_still_unconditionally_denied(self):
        with patch("http.client.HTTPSConnection",
                   side_effect=AssertionError("NO_SOCKET")) as socket:
            with self.assertRaisesRegex(ValueError,"D2_D3_REQUIRED"):
                mac_send_live(execute_live=True,grant_id=GRANT_ID)
            with self.assertRaisesRegex(ValueError,"BLOCKED_AUTHORITY"):
                integrated_send_live(execute_live=True)
            socket.assert_not_called()
        self.assertFalse(list(self.registry.iterdir()))


if __name__=="__main__":
    unittest.main()
