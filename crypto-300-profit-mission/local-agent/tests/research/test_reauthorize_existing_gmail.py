"""Offline regression tests for the local Gmail reauthorization helper."""
import importlib.util
import json
import os
from pathlib import Path
import stat
import tempfile
import unittest
from unittest import mock

MODULE = Path(__file__).resolve().parents[2] / "scripts" / "reauthorize_existing_gmail.py"
spec = importlib.util.spec_from_file_location("reauthorize_existing_gmail", MODULE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class SafeReauthTests(unittest.TestCase):
    def test_pkce_is_urlsafe_stable_and_unpadded(self):
        verifier = "x" * 64
        self.assertEqual(mod.challenge(verifier), "fOEAlx9k5wAej-WlGXPs3-HO1Cvv5-6NX9YhlQa1OTw")
        self.assertNotIn("=", mod.challenge(verifier))

    def test_atomic_replacement_preserves_existing_fields_and_private_backup(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "oauth.json"
            prior = {"client_id": "example.apps.googleusercontent.com", "client_secret": "original", "refresh_token": "expired", "scopes": ["legacy"], "extra": "keep"}
            path.write_text(json.dumps(prior))
            os.chmod(path, 0o600)
            backup = mod.atomic_write_credentials(path, prior, {"refresh_token": "new", "access_token": "access"})
            result = json.loads(path.read_text())
            self.assertEqual(result["client_secret"], "original")
            self.assertEqual(result["extra"], "keep")
            self.assertEqual(result["refresh_token"], "new")
            self.assertEqual(result["scopes"], list(mod.SCOPES))
            self.assertEqual(json.loads(backup.read_text()), prior)
            self.assertEqual(stat.S_IMODE(backup.stat().st_mode), 0o600)
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)


    def test_missing_recipient_fails_before_browser_or_network(self):
        with tempfile.TemporaryDirectory() as td:
            oauth = Path(td) / "oauth.json"
            oauth.write_text('{"refresh_token":"old","client_id":"x","client_secret":"y"}')
            os.chmod(oauth, 0o600)
            with mock.patch.object(mod, "existing_config",
                                   return_value=(oauth, {"client_id": "client"}, None)), \
                 mock.patch.object(mod, "receive_code") as callback, \
                 mock.patch.object(mod.webbrowser, "open") as browser, \
                 mock.patch.object(mod, "post_token") as token:
                with self.assertRaisesRegex(mod.RecoveryError, "RECIPIENT_REQUIRED_FOR_ACCOUNT_CHECK"):
                    mod.main([])
                callback.assert_not_called()
                browser.assert_not_called()
                token.assert_not_called()
            self.assertEqual(json.loads(oauth.read_text())["refresh_token"], "old")

    def test_two_backups_same_second_do_not_collide(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "oauth.json"
            prior = {"client_id": "id", "client_secret": "secret", "refresh_token": "old"}
            path.write_text(json.dumps(prior))
            os.chmod(path, 0o600)
            token = {"refresh_token": "new", "access_token": "short-lived"}
            with mock.patch.object(mod.time, "strftime", return_value="20261011-231000"):
                first = mod.atomic_write_credentials(path, prior, token)
                second = mod.atomic_write_credentials(path, prior, token)
            self.assertNotEqual(first, second)
            self.assertTrue(first.is_file())
            self.assertTrue(second.is_file())
            self.assertEqual(stat.S_IMODE(first.stat().st_mode), 0o600)
            self.assertEqual(stat.S_IMODE(second.stat().st_mode), 0o600)

    def test_short_lived_bearer_never_persisted(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "oauth.json"
            old = {"refresh_token": "original", "token": "stale-bearer",
                   "client_id": "id", "client_secret": "secret"}
            path.write_text(json.dumps(old))
            os.chmod(path, 0o600)
            mod.atomic_write_credentials(path, old, {
                "refresh_token": "fresh", "access_token": "new-bearer"})
            saved = json.loads(path.read_text())
            self.assertNotIn("token", saved)
            self.assertNotIn("access_token", saved)
            self.assertEqual(saved["refresh_token"], "fresh")

    def test_concurrent_change_aborts_and_preserves_source(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "oauth.json"
            path.write_text('{"refresh_token":"original"}')
            os.chmod(path, 0o600)
            original_read = Path.read_bytes
            calls = 0

            def racing_read(p):
                nonlocal calls
                calls += 1
                if calls == 2 and p == path:
                    return b"concurrently changed"
                return original_read(p)

            with mock.patch.object(Path, "read_bytes", racing_read):
                with self.assertRaisesRegex(mod.RecoveryError, "CREDENTIAL_CONCURRENT_CHANGE_ABORTED"):
                    mod.atomic_write_credentials(path, {}, {"refresh_token": "new", "access_token": "new"})
            self.assertEqual(path.read_text(), '{"refresh_token":"original"}')

    def test_configuration_requires_private_credential(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            prod = root / "prod"
            prod.mkdir()
            runner = root / "mission-loop.sh"
            runner.write_text(f'PROD="{prod}"\n')
            credential = root / "credentials.json"
            credential.write_text(json.dumps({"client_id": "id", "client_secret": "secret", "refresh_token": "old"}))
            (prod / "gmail-existing-source.json").write_text(json.dumps({"existing_oauth_file": str(credential), "recipient": "user@example.com"}))
            with mock.patch.object(mod, "CLIENT_PATH", runner):
                with self.assertRaisesRegex(mod.RecoveryError, "CREDENTIAL_FILE_PERMISSIONS_TOO_BROAD"):
                    mod.existing_config()
                os.chmod(credential, 0o600)
                path, old, recipient = mod.existing_config()
                self.assertEqual(path, credential)
                self.assertEqual(recipient, "user@example.com")
                self.assertEqual(old["refresh_token"], "old")

    def test_browser_callback_uses_loopback_server(self):
        server, result, uri = mod.receive_code("expected")
        self.assertTrue(uri.startswith("http://127.0.0.1:"))
        self.assertLess(server.timeout, 5)
        server.server_close()
        self.assertEqual(result, {})


if __name__ == "__main__":
    unittest.main()
