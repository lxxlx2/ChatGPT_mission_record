"""Isolated Machine.fun Gmail alerts reusing Frank's existing OAuth file READ-ONLY.

No Frank imports, DB writes, credential refresh persistence or new OAuth consent.
Gmail is an at-most-once API action: uncertain sends are NEVER blindly resent.
"""
from __future__ import annotations

import base64
from contextlib import contextmanager
import hashlib
import json
import os
import re
import sqlite3
import stat
import time
import urllib.error
import urllib.parse
import urllib.request
from email import policy
from email.message import EmailMessage
from email.parser import BytesParser
from pathlib import Path

SEND_SCOPE = "https://www.googleapis.com/auth/gmail.send"
READ_SCOPE = "https://www.googleapis.com/auth/gmail.readonly"
TOKEN_URI = "https://oauth2.googleapis.com/token"
GMAIL = "https://gmail.googleapis.com/gmail/v1/users/me/"


class MailBlocked(Exception):
    pass


def private_json(path: Path) -> dict:
    if path.is_symlink() or not path.is_file() or stat.S_IMODE(path.stat().st_mode) & 0o077:
        raise MailBlocked("PRIVATE_CREDENTIAL_FILE_REQUIRED_MODE_600")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise MailBlocked("PRIVATE_CREDENTIAL_UNREADABLE") from exc
    if not isinstance(data, dict):
        raise MailBlocked("CREDENTIAL_FORMAT_INVALID")
    return data


def marker_for(event: dict) -> str:
    digest = hashlib.sha256((event["signature"] + "\x00" + event["mint"] + "\x00" + event["pool"]).encode()).hexdigest()[:36]
    return "machine-fun-launch-" + digest


def message_for(event: dict, recipient: str) -> bytes:
    marker = marker_for(event)
    msg = EmailMessage()
    msg["From"] = recipient
    msg["To"] = recipient
    msg["Subject"] = "[Machine.fun] NEW ONCHAIN LAUNCH CANDIDATE " + event["mint"][:12]
    msg["Message-ID"] = "<" + marker + "@alerts.local>"
    msg["X-Machine-Fun-Event-ID"] = marker
    body = "\n".join([
        "Machine.fun 新发行候选（链上事件）",
        "注意：仅表示命中已知平台配置，不代表官方确认发行、第一枚官方币或买入建议。",
        "Token Mint: " + event["mint"],
        "Pool: " + event["pool"],
        "Creator: " + event["creator"],
        "Quote Mint: " + event["quote_mint"],
        "Platform Config: " + event["platform_config"],
        "Slot: " + str(event["slot"]),
        "Instruction: " + event["instruction"],
        "Signature: " + event["signature"],
        "Solscan: https://solscan.io/tx/" + event["signature"],
        "EVIDENCE: CHAIN_PLATFORM_CANDIDATE_UNENDORSED",
        "EVENT_ID: " + marker,
        "",
        "This is a Machine.fun-specific detector. Frank is unchanged.",
    ])
    msg.set_content(body)
    return msg.as_bytes(policy=policy.SMTP)


class GmailAPI:
    def __init__(self, oauth_path: Path, recipient: str | None, timeout: int = 12, open_url=None):
        self.oauth_path = Path(oauth_path)
        self.recipient = recipient.strip().lower() if recipient else None
        self.open_url = open_url or urllib.request.urlopen
        self.timeout = timeout
        self.token: str | None = None

    def _open(self, request: urllib.request.Request):
        with self.open_url(request, timeout=self.timeout) as response:
            return json.load(response)

    def ready(self):
        cfg = private_json(self.oauth_path)
        scopes = cfg.get("scopes", [])
        if isinstance(scopes, str):
            scopes = scopes.split()
        if not {SEND_SCOPE, READ_SCOPE}.issubset(set(scopes)):
            raise MailBlocked("GMAIL_SEND_AND_READONLY_SCOPES_REQUIRED")
        if cfg.get("token_uri", TOKEN_URI) not in {TOKEN_URI, "https://accounts.google.com/o/oauth2/token"}:
            raise MailBlocked("OAUTH_TOKEN_HOST_NOT_ALLOWLISTED")
        if not all(isinstance(cfg.get(k), str) and cfg[k] for k in ("refresh_token", "client_id", "client_secret")):
            raise MailBlocked("OAUTH_CREDENTIAL_FIELDS_MISSING")
        payload = urllib.parse.urlencode({
            "grant_type": "refresh_token",
            "refresh_token": cfg["refresh_token"],
            "client_id": cfg["client_id"],
            "client_secret": cfg["client_secret"],
        }).encode()
        request = urllib.request.Request(TOKEN_URI, payload, {"Content-Type": "application/x-www-form-urlencoded"}, method="POST")
        try:
            token_result = self._open(request)
            token = token_result.get("access_token")
            if not token:
                raise MailBlocked("OAUTH_REFRESH_TOKEN_REJECTED")
            self.token = token
            profile = self.get("profile")
            email_address = profile.get("emailAddress")
            if not isinstance(email_address, str) or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email_address.strip()):
                raise MailBlocked("GMAIL_PROFILE_EMAIL_UNAVAILABLE")
            verified_email = email_address.strip().lower()
            if self.recipient and verified_email != self.recipient:
                raise MailBlocked("GMAIL_IDENTITY_DOES_NOT_MATCH_FRANK_RECIPIENT")
            # If the old Frank config omits recipient, use the authenticated
            # Google account itself as To/From. Do not write back to Frank.
            self.recipient = verified_email
            # Require Sent read permission before enabling messages/send.
            self.get("messages?" + urllib.parse.urlencode({"q": "in:sent", "maxResults": 1}))
        except (OSError, urllib.error.URLError, ValueError, KeyError, TypeError) as exc:
            self.token = None
            raise MailBlocked("GMAIL_READONLY_AUTH_CHECK_FAILED") from exc

    def get(self, endpoint: str) -> dict:
        if not self.token:
            raise MailBlocked("GMAIL_NOT_READY")
        req = urllib.request.Request(GMAIL + endpoint, headers={"Authorization": "Bearer " + self.token})
        return self._open(req)

    def send(self, raw: bytes) -> dict:
        if not self.token:
            raise MailBlocked("GMAIL_NOT_READY")
        payload = json.dumps({"raw": base64.urlsafe_b64encode(raw).decode()}).encode()
        req = urllib.request.Request(GMAIL + "messages/send", payload, {
            "Authorization": "Bearer " + self.token,
            "Content-Type": "application/json",
        }, method="POST")
        return self._open(req)

    def sent_matches(self, event: dict) -> list[str]:
        marker = marker_for(event)
        msgid = marker + "@alerts.local"
        ids: set[str] = set()
        for q in ('in:sent rfc822msgid:' + msgid, 'in:sent "' + marker + '"'):
            result = self.get("messages?" + urllib.parse.urlencode({"q": q, "maxResults": 100}))
            for item in result.get("messages") or []:
                if isinstance(item, dict) and item.get("id"):
                    ids.add(item["id"])
        return sorted(ids)

    def verify(self, event: dict, gmail_id: str) -> bool:
        msg = self.get("messages/" + urllib.parse.quote(gmail_id, safe="") + "?format=raw")
        if "SENT" not in (msg.get("labelIds") or []):
            return False
        raw = msg.get("raw", "")
        if not raw:
            return False
        decoded = base64.urlsafe_b64decode(raw + "=" * (-len(raw) % 4))
        parsed = BytesParser(policy=policy.default).parsebytes(decoded)
        body = parsed.get_body(preferencelist=("plain",))
        content = body.get_content() if body else ""
        return (marker_for(event) in content and
                event["signature"] in content and event["mint"] in content and
                event["pool"] in content and
                parsed["Subject"] == "[Machine.fun] NEW ONCHAIN LAUNCH CANDIDATE " + event["mint"][:12] and
                str(parsed["To"]).lower() == self.recipient and
                str(parsed["From"]).lower() == self.recipient)


class GmailAlerts:
    """Separate SQLite state; no access to Frank state or DB."""

    def __init__(self, path: Path, oauth_path: Path, recipient: str, provider_factory=None):
        self.path = Path(path)
        self.oauth_path = Path(oauth_path)
        self.recipient = recipient
        self.provider_factory = provider_factory or (lambda: GmailAPI(self.oauth_path, self.recipient))
        self.path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        if stat.S_IMODE(self.path.parent.stat().st_mode) & 0o077:
            raise MailBlocked("ALERT_STATE_DIR_NOT_PRIVATE")
        if self.path.is_symlink():
            raise MailBlocked("ALERT_STATE_SYMLINK_REJECTED")
        with self._db() as conn:
            conn.execute("""CREATE TABLE IF NOT EXISTS alerts(
                event_id TEXT PRIMARY KEY,
                event_json TEXT NOT NULL,
                state TEXT NOT NULL,
                gmail_id TEXT,
                created_at INTEGER NOT NULL,
                updated_at INTEGER NOT NULL)""")

    @contextmanager
    def _db(self):
        if self.path.exists() and stat.S_IMODE(self.path.stat().st_mode) & 0o077:
            raise MailBlocked("ALERT_DB_PERMISSIONS_TOO_BROAD")
        conn = sqlite3.connect(self.path)
        os.chmod(self.path, 0o600)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def enqueue(self, event: dict) -> None:
        if event.get("evidence") != "CHAIN_PLATFORM_CANDIDATE_UNENDORSED":
            return
        key = marker_for(event)
        value = json.dumps(event, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        now = int(time.time())
        with self._db() as conn:
            conn.execute("INSERT OR IGNORE INTO alerts(event_id,event_json,state,created_at,updated_at) VALUES(?,?, 'QUEUED',?,?)",
                         (key, value, now, now))

    def _set(self, key: str, state: str, gmail_id: str | None = None) -> None:
        with self._db() as conn:
            conn.execute("UPDATE alerts SET state=?,gmail_id=COALESCE(?,gmail_id),updated_at=? WHERE event_id=?",
                         (state, gmail_id, int(time.time()), key))

    def summary(self) -> dict:
        with self._db() as conn:
            return {r["state"]: r["n"] for r in conn.execute("SELECT state,COUNT(*) AS n FROM alerts GROUP BY state")}

    def drain(self, batch: int = 10) -> dict:
        with self._db() as conn:
            rows = conn.execute("SELECT * FROM alerts WHERE state NOT IN ('SENT_VERIFIED','CONFLICT') ORDER BY created_at,event_id LIMIT ?", (batch,)).fetchall()
        if not rows:
            return self.summary()
        try:
            provider = self.provider_factory()
            provider.ready()
        except Exception:
            print("MACHINE_GMAIL_CREDENTIAL_BLOCKED: existing Frank credential read-only; no email sent", file=__import__("sys").stderr)
            return self.summary()
        for row in rows:
            key = row["event_id"]
            event = json.loads(row["event_json"])
            state = row["state"]
            try:
                existing = provider.sent_matches(event)
                matches = [mid for mid in existing if provider.verify(event, mid)]
                if len(matches) == 1:
                    self._set(key, "SENT_VERIFIED", matches[0])
                    print("MACHINE_GMAIL_SENT_VERIFIED " + key, flush=True)
                    continue
                if len(matches) > 1 or (existing and not matches):
                    self._set(key, "CONFLICT")
                    print("MACHINE_GMAIL_CONFLICT " + key, file=__import__("sys").stderr)
                    continue
                if state != "QUEUED":
                    self._set(key, "SEND_UNCERTAIN")
                    continue  # Never blindly resend an ambiguous Gmail submission.
                self._set(key, "SEND_UNCERTAIN")  # Durable fence BEFORE network send.
                response = provider.send(message_for(event, provider.recipient))
                gmail_id = response.get("id")
                if gmail_id:
                    self._set(key, "SENT_UNVERIFIED", gmail_id)
                    if provider.verify(event, gmail_id):
                        self._set(key, "SENT_VERIFIED", gmail_id)
                        print("MACHINE_GMAIL_SENT_VERIFIED " + key, flush=True)
                    # Otherwise retry Sent reconciliation in a subsequent drain.
            except Exception:
                # Network exceptions may occur after Google accepted a message.
                # Keep SEND_UNCERTAIN / SENT_UNVERIFIED and reconcile on later passes.
                print("MACHINE_GMAIL_SEND_OR_READBACK_UNCERTAIN " + key, file=__import__("sys").stderr)
        return self.summary()
