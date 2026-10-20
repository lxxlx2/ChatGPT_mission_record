"""Offline-only checks for adaptive live entrypoint. Never uses real transport."""
import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

F0 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(F0))
import f0_l1_adaptive_live_once as one

NOW = datetime(2026, 10, 20, 10, 0, tzinfo=timezone.utc)


def valid_permit(root):
    return {
        "scope": one.SCHEMA, "user_authorized": True,
        "independent_review_required": True,
        "approved_commit_sha": "a" * 40,
        "approved_script_sha256": "b" * 64, "run_nonce": "c" * 64,
        "window_start_utc": "2026-10-20T09:59:00Z",
        "window_end_utc": "2026-10-20T10:05:00Z",
        "storage_root": str(root), "endpoint": one.ENDPOINT,
        "chain_id": 56,
        "methods": ["eth_chainId", "eth_blockNumber", "eth_getBlockByNumber"],
        "free_only": True, "read_only": True, "no_retries": True,
        "no_ws": True, "no_proxy": True, "no_redirects": True,
        "background": False, "archive_raw_public_rpc": True,
        "cost_policy": "FREE_ONLY_NO_AUTO_UPGRADE",
        "max_total_attempts": 32, "max_block_reads": 24, "max_head_polls": 6,
        "duration_ms": 60000, "min_interval_ms": 250,
        "head_poll_interval_ms": 500,
        "max_stagnant_poll_wait_ms": 8000, "refresh_after_blocks": 4,
        "max_response_bytes": 2_000_000, "timeout_ms": 5000,
    }


class AdaptivePermitGateTests(unittest.TestCase):
    def private_root(self, base):
        root = Path(base) / "private"
        root.mkdir(mode=0o700)
        return root

    def test_valid_structure_is_not_permission_to_call_post(self):
        with tempfile.TemporaryDirectory() as d:
            root = self.private_root(d)
            permit = valid_permit(root)
            self.assertEqual(one.validate_permit(permit, NOW), root)
            self.assertFalse((root / "journal.json").exists())
            self.assertFalse((root / "raw_responses").exists())

    def test_default_temp_root_outside_slash_tmp_is_accepted(self):
        # On macOS, tempfile.gettempdir() is typically /var/folders/...,
        # outside /private/tmp. Reproduce that containment on Linux too.
        with tempfile.TemporaryDirectory(dir=Path.home()) as d:
            root = self.private_root(d)
            with patch.object(one.tempfile, "gettempdir", return_value=d):
                self.assertEqual(one.validate_permit(valid_permit(root), NOW), root)
                self.assertFalse((root / "journal.json").exists())
                self.assertFalse((root / "raw_responses").exists())

    def test_disallow_all_wider_scopes_and_bool_int_coercion(self):
        with tempfile.TemporaryDirectory() as d:
            root = self.private_root(d)
            for field, value in [
                ("user_authorized", False), ("no_retries", False),
                ("no_ws", False), ("no_proxy", False),
                ("no_redirects", False), ("background", True),
                ("endpoint", "https://unapproved.invalid"),
                ("chain_id", 1), ("max_total_attempts", 33),
                ("max_total_attempts", True), ("max_block_reads", 25),
                ("max_head_polls", 7), ("duration_ms", 60001),
                ("timeout_ms", 8000), ("cost_policy", "PAID"),
            ]:
                with self.subTest(field=field, value=value):
                    permit = valid_permit(root)
                    permit[field] = value
                    with self.assertRaises(ValueError):
                        one.validate_permit(permit, NOW)

    def test_missing_extra_fields_or_expired_window_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = self.private_root(d)
            permit = valid_permit(root)
            del permit["no_redirects"]
            with self.assertRaisesRegex(ValueError, "FIELDS_INVALID"):
                one.validate_permit(permit, NOW)
            permit = valid_permit(root)
            permit["noncontract_key"] = True
            with self.assertRaisesRegex(ValueError, "FIELDS_INVALID"):
                one.validate_permit(permit, NOW)
            with self.assertRaisesRegex(ValueError, "WINDOW_INVALID"):
                one.validate_permit(valid_permit(root), NOW + timedelta(hours=1))

    def test_existing_evidence_and_symlinks_fail_before_any_write(self):
        with tempfile.TemporaryDirectory() as d:
            root = self.private_root(d)
            prior = root / "journal.json"
            prior.write_bytes(b'{"attempted_calls":1}')
            with self.assertRaisesRegex(ValueError, "NOT_PRIVATE_OR_FRESH"):
                one.validate_permit(valid_permit(root), NOW)
            self.assertEqual(prior.read_bytes(), b'{"attempted_calls":1}')
            prior.unlink()
            prior.symlink_to(Path(d) / "target")
            with self.assertRaisesRegex(ValueError, "NOT_PRIVATE_OR_FRESH"):
                one.validate_permit(valid_permit(root), NOW)

    def test_nonce_consumed_once_and_no_second_dispatch(self):
        with tempfile.TemporaryDirectory() as d:
            root = self.private_root(d)
            permit = valid_permit(root)
            raw = json.dumps(permit).encode()
            first = one.consume_nonce(root, raw, permit["run_nonce"])
            saved = first.read_bytes()
            with self.assertRaises(FileExistsError):
                one.consume_nonce(root, raw, permit["run_nonce"])
            self.assertEqual(saved, first.read_bytes())
            self.assertIn(one.digest(raw), first.read_text())

    def test_import_and_permit_validation_never_call_real_post(self):
        with tempfile.TemporaryDirectory() as d:
            root = self.private_root(d)
            with patch.object(one, "live_https_post", side_effect=AssertionError("NETWORK_IN_OFFLINE_TEST")) as post:
                self.assertEqual(one.validate_permit(valid_permit(root), NOW), root)
                post.assert_not_called()


if __name__ == "__main__":
    unittest.main()
