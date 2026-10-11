#!/usr/bin/env python3
"""One-time Google Desktop OAuth recovery for the existing Frank Gmail credential.

Runs locally, requires browser consent, and never sends mail or uploads secrets.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
from pathlib import Path
import re
import secrets
import sys
import tempfile
import time
from urllib import error, parse, request
import webbrowser

CLIENT_PATH = Path.home() / "Library/Application Support/FrankMeme/mission-loop.sh"
SCOPES = (
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.readonly",
)
TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
OAUTH_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"


class RecoveryError(RuntimeError):
    pass


def existing_config():
    runner = CLIENT_PATH.read_text(encoding="utf-8")
    match = re.search(r'^PROD="([^"]+)"\s*$', runner, flags=re.M)
    if not match:
        raise RecoveryError("PRODUCTION_ROOT_NOT_FOUND")
    prod = Path(match.group(1)).expanduser()
    config_path = prod / "gmail-existing-source.json"
    cfg = json.loads(config_path.read_text(encoding="utf-8")) if config_path.is_file() else {}
    credential_path = cfg.get("existing_oauth_file") or os.environ.get("FRANK_GMAIL_EXISTING_OAUTH_FILE")
    if not credential_path:
        raise RecoveryError("EXISTING_OAUTH_PATH_NOT_CONFIGURED")
    credential_path = Path(credential_path).expanduser()
    if not credential_path.is_file():
        raise RecoveryError("EXISTING_OAUTH_FILE_NOT_FOUND")
    old = json.loads(credential_path.read_text(encoding="utf-8"))
    if not all(isinstance(old.get(k), str) and old[k] for k in ("refresh_token", "client_id", "client_secret")):
        raise RecoveryError("EXISTING_OAUTH_FIELDS_INCOMPLETE")
    if old.get("token_uri", TOKEN_ENDPOINT) not in (TOKEN_ENDPOINT, "https://accounts.google.com/o/oauth2/token"):
        raise RecoveryError("TOKEN_ENDPOINT_NOT_ALLOWED")
    if credential_path.stat().st_mode & 0o077:
        raise RecoveryError("CREDENTIAL_FILE_PERMISSIONS_TOO_BROAD_RUN_CHMOD_600_FIRST")
    return credential_path, old, cfg.get("recipient") or os.environ.get("FRANK_GMAIL_RECIPIENT")


def challenge(verifier):
    return base64.urlsafe_b64encode(hashlib.sha256(verifier.encode("ascii")).digest()).rstrip(b"=").decode("ascii")


def receive_code(expected_state):
    result = {}

    class Callback(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            try:
                parts = parse.urlsplit(self.path)
                query = parse.parse_qs(parts.query)
                if parts.path not in ("/", "") or not hmac.compare_digest(query.get("state", [""])[0], expected_state):
                    status, result["error"] = 403, "INVALID_OAUTH_STATE"
                elif query.get("error"):
                    status, result["error"] = 400, "OAUTH_CONSENT_DENIED_OR_BLOCKED"
                elif not query.get("code", [""])[0]:
                    status, result["error"] = 400, "MISSING_AUTHORIZATION_CODE"
                else:
                    status, result["code"] = 200, query["code"][0]
                self.send_response(status)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Cache-Control", "no-store")
                self.send_header("Referrer-Policy", "no-referrer")
                self.end_headers()
                self.wfile.write(b"<html><body><h2>Authorization completed. Return to Terminal.</h2></body></html>")
            except (OSError, ValueError):
                result["error"] = "CALLBACK_ERROR"

    server = HTTPServer(("127.0.0.1", 0), Callback)
    server.timeout = 1
    redirect_uri = f"http://127.0.0.1:{server.server_port}/"
    return server, result, redirect_uri


def post_token(data):
    body = parse.urlencode(data).encode("utf-8")
    req = request.Request(TOKEN_ENDPOINT, data=body, headers={"Content-Type": "application/x-www-form-urlencoded"})
    try:
        with request.urlopen(req, timeout=15) as response:
            token = json.load(response)
    except error.HTTPError as exc:
        try:
            payload = json.loads(exc.read(8192))
            reason = payload.get("error", "UNKNOWN_OAUTH_ERROR")
            if not re.fullmatch(r"[a-z_]+", reason):
                reason = "UNKNOWN_OAUTH_ERROR"
        except (ValueError, TypeError):
            reason = "UNKNOWN_OAUTH_ERROR"
        raise RecoveryError(f"OAUTH_TOKEN_HTTP_{exc.code}_{reason}") from None
    except (OSError, ValueError):
        raise RecoveryError("OAUTH_TOKEN_NETWORK_OR_RESPONSE_ERROR") from None
    return token


def api_get(token, endpoint):
    req = request.Request(
        "https://gmail.googleapis.com/gmail/v1/users/me/" + endpoint,
        headers={"Authorization": "Bearer " + token},
    )
    try:
        with request.urlopen(req, timeout=15) as response:
            return json.load(response)
    except error.HTTPError as exc:
        raise RecoveryError(f"GMAIL_API_HTTP_{exc.code}") from None
    except (OSError, ValueError):
        raise RecoveryError("GMAIL_API_NETWORK_OR_RESPONSE_ERROR") from None


def atomic_write_credentials(path, old, token):
    new = dict(old)
    new["refresh_token"] = token["refresh_token"]
    new["token"] = token["access_token"]
    new["token_uri"] = TOKEN_ENDPOINT
    new["scopes"] = list(SCOPES)
    backup = path.with_name(path.name + ".pre-reauth-" + time.strftime("%Y%m%d-%H%M%S"))
    original_bytes = path.read_bytes()
    backup_fd = os.open(backup, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(backup_fd, "wb") as out:
        out.write(original_bytes)
        out.flush()
        os.fsync(out.fileno())
    tmp = None
    try:
        fd, tmp = tempfile.mkstemp(prefix=".gmail-reauth-", suffix=".json", dir=path.parent)
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as out:
            json.dump(new, out, indent=2, ensure_ascii=False)
            out.write("\n")
            out.flush()
            os.fsync(out.fileno())
        if path.read_bytes() != original_bytes:
            raise RecoveryError("CREDENTIAL_CONCURRENT_CHANGE_ABORTED")
        os.replace(tmp, path)
    finally:
        if tmp and os.path.exists(tmp):
            os.unlink(tmp)
    return backup


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-only", action="store_true", help="Print sanitized checks without a browser or changes")
    parser.add_argument("--timeout", type=int, default=180)
    args = parser.parse_args(argv)
    if not 30 <= args.timeout <= 900:
        raise RecoveryError("TIMEOUT_OUT_OF_RANGE")
    path, old, recipient = existing_config()
    print("CREDENTIAL_FILE=FOUND", flush=True)
    print("CLIENT_ID_SUFFIX=" + old["client_id"][-24:], flush=True)
    print("RECIPIENT_CONFIGURED=" + ("YES" if recipient else "NO"), flush=True)
    print("REQUIRED_GMAIL_SCOPES=SEND_READONLY", flush=True)
    if args.check_only:
        return
    print("DESKTOP_OAUTH_CLIENT_REQUIRED=YES", flush=True)
    state = secrets.token_urlsafe(32)
    verifier = secrets.token_urlsafe(64)
    server, result, redirect_uri = receive_code(state)
    params = {
        "response_type": "code", "client_id": old["client_id"],
        "redirect_uri": redirect_uri, "scope": " ".join(SCOPES),
        "access_type": "offline", "prompt": "consent", "state": state,
        "code_challenge": challenge(verifier), "code_challenge_method": "S256",
    }
    url = OAUTH_ENDPOINT + "?" + parse.urlencode(params)
    print("OPENING_GOOGLE_AUTH_BROWSER", flush=True)
    if not webbrowser.open(url):
        print("BROWSER_OPEN_FAILED_COPY_THIS_URL_LOCALLY=" + url, flush=True)
    try:
        limit = time.monotonic() + args.timeout
        while time.monotonic() < limit and not result:
            server.handle_request()
        if "error" in result:
            raise RecoveryError(result["error"])
        if not result.get("code"):
            raise RecoveryError("OAUTH_CALLBACK_TIMEOUT")
    finally:
        server.server_close()
    print("GOOGLE_BROWSER_CONSENT=RECEIVED", flush=True)
    token = post_token({
        "grant_type": "authorization_code", "code": result["code"],
        "client_id": old["client_id"], "client_secret": old["client_secret"],
        "redirect_uri": redirect_uri, "code_verifier": verifier,
    })
    if not token.get("refresh_token") or not token.get("access_token"):
        raise RecoveryError("NEW_REFRESH_TOKEN_MISSING_NO_FILE_CHANGE")
    granted = set(token.get("scope", "").split())
    if not set(SCOPES).issubset(granted):
        raise RecoveryError("REQUIRED_SCOPE_NOT_GRANTED_NO_FILE_CHANGE")
    profile = api_get(token["access_token"], "profile")
    if not profile.get("emailAddress"):
        raise RecoveryError("GMAIL_PROFILE_UNAVAILABLE_NO_FILE_CHANGE")
    if recipient and profile["emailAddress"].casefold() != recipient.casefold():
        raise RecoveryError("WRONG_GMAIL_ACCOUNT_NO_FILE_CHANGE")
    api_get(token["access_token"], "messages?" + parse.urlencode({"q": "in:sent", "maxResults": 1}))
    print("GMAIL_PROFILE_AND_SENT_READ=PASS", flush=True)
    refreshed = post_token({
        "grant_type": "refresh_token", "refresh_token": token["refresh_token"],
        "client_id": old["client_id"], "client_secret": old["client_secret"],
    })
    if not refreshed.get("access_token"):
        raise RecoveryError("NEW_REFRESH_TOKEN_TEST_FAILED_NO_FILE_CHANGE")
    print("NEW_REFRESH_TOKEN_TEST=PASS", flush=True)
    atomic_write_credentials(path, old, token)
    print("LOCAL_CREDENTIAL_REPLACED=PASS", flush=True)
    print("BACKUP_CREATED=YES_PRIVATE_LOCAL_FILE", flush=True)
    print("GMAIL_SEND=NOT_ATTEMPTED", flush=True)
    print("MONITOR_RESTART=NOT_PERFORMED", flush=True)


if __name__ == "__main__":
    try:
        main()
    except (RecoveryError, FileNotFoundError, PermissionError, json.JSONDecodeError) as exc:
        code = str(exc) if isinstance(exc, RecoveryError) else type(exc).__name__
        print("RECOVERY=FAILED " + code, file=sys.stderr)
        sys.exit(1)
