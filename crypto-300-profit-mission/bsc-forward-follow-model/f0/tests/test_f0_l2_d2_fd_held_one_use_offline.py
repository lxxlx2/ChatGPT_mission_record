"""Test the SAME D1 one-use atomic marker on disposable, fd-held roots."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import json
import os
import shutil
from pathlib import Path
import socket
import stat
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import f0_l2_d2_fd_held_one_use_offline as held
from f0_l2_d1_grant import (
    OfflineGrantRegistry, _consume_once_using_open_dirfd,
)


class HeldFDOnceOnlyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(
            prefix="bsc-f0-once-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.root.chmod(0o700)
        self.grant_id = "offline-test-unique-grant-0001"
        self.permit_digest = "a" * 64

    def marker(self):
        return self.root / (
            sha256(self.grant_id.encode()).hexdigest() + ".consumed.json")

    def run_once(self, **updates):
        args = dict(test_root=self.root, grant_id=self.grant_id,
                    permit_sha256=self.permit_digest)
        args.update(updates)
        return held.rehearse_held_test_registry_once_offline(**args)

    def test_one_once_spent_and_fsynced_under_same_dirfd(self):
        with (
            patch("http.client.HTTPSConnection",
                  side_effect=AssertionError("NO_TLS")) as tls,
            patch.object(socket, "create_connection",
                         side_effect=AssertionError("NO_SOCKET")) as sock,
        ):
            result = self.run_once()
            tls.assert_not_called()
            sock.assert_not_called()
        self.assertEqual(result["status"],
                         "TEST_MARKER_CONSUMED_NOT_PRODUCTION")
        self.assertFalse(result["real_human_authority_verified"])
        self.assertFalse(result["production_marker_consumed"])
        self.assertEqual(result["network_requests"], 0)
        self.assertTrue(result["directory_fd_closed"])
        self.assertEqual(result["production"], "PRODUCTION_NO_GO")
        marker = self.marker()
        self.assertTrue(marker.is_file())
        self.assertEqual(stat.S_IMODE(marker.stat().st_mode), 0o600)
        record = json.loads(marker.read_bytes())
        self.assertEqual(record["grant_id_sha256"],
                         sha256(self.grant_id.encode()).hexdigest())
        self.assertEqual(record["permit_sha256"], self.permit_digest)
        self.assertEqual(record["outcome"], "CONSUMED_OR_UNKNOWN")

    def test_second_attempt_same_id_any_digest_rejected_no_reset(self):
        self.run_once()
        first = self.marker().read_bytes()
        for digest in (self.permit_digest, "b" * 64):
            with self.assertRaisesRegex(
                    ValueError, "D1_GRANT_ALREADY_CONSUMED"):
                self.run_once(permit_sha256=digest)
        self.assertEqual(self.marker().read_bytes(), first)
        self.assertEqual(len(list(self.root.iterdir())), 1)

    def test_concurrent_same_id_only_one_wins_atomic_open(self):
        def attempt(_n):
            try:
                self.run_once()
                return "spent"
            except ValueError as exc:
                return str(exc)
        with ThreadPoolExecutor(max_workers=2) as pool:
            answers = list(pool.map(attempt, (1, 2)))
        self.assertEqual(sorted(answers),
                         ["D1_GRANT_ALREADY_CONSUMED", "spent"])
        self.assertEqual(len(list(self.root.iterdir())), 1)

    def test_regular_non_disposable_path_refused_before_write(self):
        with tempfile.TemporaryDirectory(prefix="generic-other-") as other:
            root = Path(other).resolve()
            with self.assertRaisesRegex(
                    ValueError, "D2_ONCE_TEST_ROOT_NOT_DISPOSABLE"):
                self.run_once(test_root=root)
            self.assertEqual(list(root.iterdir()), [])

    def test_symlink_root_refused_and_original_untouched(self):
        link = self.root.parent / (self.root.name + "-alias")
        link.symlink_to(self.root, target_is_directory=True)
        self.addCleanup(link.unlink)
        with self.assertRaisesRegex(
                ValueError, "D2_ONCE_TEST_ROOT_NOT_DISPOSABLE"):
            self.run_once(test_root=link)
        self.assertFalse(self.marker().exists())

    def test_nonprivate_test_directory_fails_without_consumption(self):
        self.root.chmod(0o750)
        self.addCleanup(lambda: self.root.chmod(0o700))
        with self.assertRaisesRegex(
                ValueError, "D2_ONCE_TEST_DIR_OWNER_OR_MODE_INVALID"):
            self.run_once()
        self.assertEqual(list(self.root.iterdir()), [])

    def test_path_inode_replacement_after_open_detected_no_success(self):
        original = held._consume_once_using_open_dirfd
        moved = self.root.with_name(self.root.name + "-moved")
        def swap_after_real_consume(dfd, grant_id, digest):
            report = original(dfd, grant_id, digest)
            self.root.rename(moved)
            self.root.mkdir(mode=0o700)
            return report
        self.addCleanup(shutil.rmtree, moved, ignore_errors=True)
        with patch.object(held, "_consume_once_using_open_dirfd",
                          side_effect=swap_after_real_consume) as writer:
            with self.assertRaisesRegex(
                    ValueError, "D2_ONCE_TEST_DIR_CHANGED_AFTER_CONSUME"):
                self.run_once()
            writer.assert_called_once()
        self.assertEqual(list(self.root.iterdir()), [])
        moved_marker = moved / self.marker().name
        self.assertEqual(json.loads(moved_marker.read_text())["outcome"],
                         "CONSUMED_OR_UNKNOWN")
        # Root replacement is a STOP/UNKNOWN event. No claim of cross-inode
        # replay protection against a malicious privileged/owning process.

    def test_file_fd_refused_by_shared_original_writer(self):
        sentinel = self.root / "innocent"
        sentinel.write_bytes(b"preserve")
        fd = os.open(sentinel, os.O_RDONLY)
        try:
            with self.assertRaisesRegex(
                    ValueError, "D1_REGISTRY_OPENED_DIR_NOT_PRIVATE"):
                _consume_once_using_open_dirfd(
                    fd, self.grant_id, self.permit_digest)
        finally:
            os.close(fd)
        self.assertEqual(sentinel.read_bytes(), b"preserve")
        self.assertFalse(self.marker().exists())

    def test_existing_D1_registry_uses_same_shared_writer(self):
        old = OfflineGrantRegistry(self.root)
        result = old.consume(self.grant_id, self.permit_digest)
        self.assertEqual(result["status"],
                         "CONSUMED_NOT_A_NETWORK_AUTHORIZATION")
        with self.assertRaisesRegex(
                ValueError, "D1_GRANT_ALREADY_CONSUMED"):
            self.run_once()
        self.assertEqual(len(list(self.root.iterdir())), 1)

    def test_live_entry_stays_denied_for_a_positive_test_marker(self):
        report = self.run_once()
        with self.assertRaisesRegex(
                ValueError, "D2_ONCE_TEST_NOT_LIVE_AUTHORITY"):
            held.send_live(report, real=True)
        self.assertFalse(report["production_marker_consumed"])


if __name__ == "__main__":
    unittest.main()
