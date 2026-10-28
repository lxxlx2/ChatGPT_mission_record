"""Independent Machine.fun Mac entry point; reads Frank RPC/OAuth sources only.

No Frank import, deployment, LaunchAgent, database mutation or credential write.
Run explicitly in a foreground Terminal. Gmail sends only actual new onchain candidates.
"""
from __future__ import annotations

import argparse
import asyncio
import fcntl
import json
import os
import re
import stat
import sys
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from machine_launch_detector import Detector, Journal, Rpc, listen
from machine_launch_gmail import GmailAPI, GmailAlerts, MailBlocked, READ_SCOPE, SEND_SCOPE, private_json

SUPPORT = Path.home() / "Library" / "Application Support" / "FrankMeme"
RPC_FILE = SUPPORT / "solana_rpc_urls"
ROOT_HINT = Path.home() / ".frank_meme_control_root"
RUNNER_HINT = SUPPORT / "mission-loop.sh"
STATE = Path.home() / ".local" / "state" / "machine-fun"


class StartupBlocked(Exception):
    pass


def rpc_from_existing() -> tuple[str, str]:
    """Only read known Frank RPC source; never scan home or print secret URL."""
    try:
        if RPC_FILE.is_symlink() or not RPC_FILE.is_file():
            raise StartupBlocked("FRANK_RPC_FILE_MISSING")
        if stat.S_IMODE(RPC_FILE.stat().st_mode) & 0o077:
            raise StartupBlocked("FRANK_RPC_FILE_PERMISSIONS_NOT_600")
        raw = RPC_FILE.read_text(encoding="utf-8").strip()
        candidates = [x.strip() for x in raw.replace("\n", ",").split(",") if x.strip()]
        for candidate in candidates:
            u = urlsplit(candidate)
            if (u.scheme != "https" or u.hostname != "solana-mainnet.g.alchemy.com" or
                not re.fullmatch(r"/v2/[A-Za-z0-9_-]{8,}", u.path) or u.query or u.fragment or u.username):
                continue
            # Current Alchemy docs use *.streaming.alchemy.com for Solana PubSub.
            ws_url = urlunsplit(("wss", "solana-mainnet.streaming.alchemy.com", u.path, "", ""))
            return candidate, ws_url
        raise StartupBlocked("NO_MATCHING_SOLANA_MAINNET_ALCHEMY_RPC_IN_EXISTING_FILE")
    except (OSError, UnicodeError, ValueError) as exc:
        raise StartupBlocked("FRANK_RPC_SOURCE_UNREADABLE") from exc


def control_root() -> Path:
    if ROOT_HINT.is_file() and not ROOT_HINT.is_symlink():
        value = ROOT_HINT.read_text(encoding="utf-8").strip()
        if value and "\n" not in value:
            path = Path(value).expanduser()
            if (path / "gmail-existing-source.json").is_file():
                return path
    if RUNNER_HINT.is_file() and not RUNNER_HINT.is_symlink():
        text = RUNNER_HINT.read_text(encoding="utf-8")
        # Matches Frank's existing runner; does not execute or source shell code.
        match = re.search(r'^PROD="([^"]+)"\s*$', text, flags=re.M)
        if match:
            path = Path(match.group(1)).expanduser()
            if (path / "gmail-existing-source.json").is_file():
                return path
    raise StartupBlocked("FRANK_GMAIL_EXISTING_CONFIG_NOT_FOUND")


def gmail_from_existing() -> tuple[Path, str]:
    try:
        source = control_root() / "gmail-existing-source.json"
        if source.is_symlink() or not source.is_file():
            raise StartupBlocked("FRANK_GMAIL_CONFIG_SYMLINK_OR_MISSING")
        # Frank's config file contains only a credential path and recipient;
        # it is not itself a refresh token. The OAuth file still requires 0600.
        cfg = json.loads(source.read_text(encoding="utf-8"))
        if not isinstance(cfg, dict):
            raise StartupBlocked("FRANK_GMAIL_CONFIG_INVALID")
        raw_path, recipient = cfg.get("existing_oauth_file"), cfg.get("recipient")
        if not isinstance(raw_path, str) or not raw_path.strip():
            raise StartupBlocked("FRANK_EXISTING_OAUTH_PATH_MISSING")
        if not isinstance(recipient, str) or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", recipient):
            raise StartupBlocked("FRANK_EXISTING_GMAIL_RECIPIENT_MISSING")
        path = Path(raw_path).expanduser()
        token = private_json(path)
        scopes = token.get("scopes", [])
        scopes = scopes.split() if isinstance(scopes, str) else scopes
        if not {READ_SCOPE, SEND_SCOPE}.issubset(set(scopes)):
            raise StartupBlocked("FRANK_GMAIL_SCOPES_NOT_SEND_AND_READONLY")
        return path, recipient.strip().lower()
    except MailBlocked as exc:
        raise StartupBlocked(str(exc)) from None
    except (OSError, ValueError) as exc:
        raise StartupBlocked("FRANK_GMAIL_SOURCE_UNREADABLE") from exc


class GmailDetector(Detector):
    def __init__(self, rpc: Rpc, journal: Journal, alerts: GmailAlerts, **kwargs):
        super().__init__(rpc, journal, **kwargs)
        self.alerts = alerts

    async def deliver(self) -> None:
        # Already-marked stdout output is a separate sink. Gmail has its own
        # independent durable queue, so an ambiguous send never gets retried.
        await super().deliver()
        rows = self.journal.db.execute(
            "SELECT payload FROM events WHERE state IN ('STDOUT_EMITTED','LOCAL_ACCEPTED','CANDIDATE') AND payload IS NOT NULL ORDER BY slot"
        ).fetchall()
        for (payload,) in rows:
            try:
                for event in json.loads(payload):
                    self.alerts.enqueue(event)
            except (ValueError, KeyError, TypeError):
                print("MACHINE_GMAIL_EVENT_PARSE_BLOCKED", file=sys.stderr)
        # Keep the websocket handler responsive while Google API requests run.
        await asyncio.to_thread(self.alerts.drain)


def state_directory() -> Path:
    STATE.mkdir(mode=0o700, parents=True, exist_ok=True)
    if STATE.is_symlink() or stat.S_IMODE(STATE.stat().st_mode) & 0o077:
        raise StartupBlocked("MACHINE_STATE_DIRECTORY_NOT_PRIVATE")
    return STATE


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Machine.fun independent read-only detection + existing Gmail alerts")
    p.add_argument("command", choices=["check", "probe", "run"])
    p.add_argument("--notify-local", action="store_true", help="Additional macOS Notification Center signal")
    args = p.parse_args(argv)

    http_rpc, ws_rpc = rpc_from_existing()
    oauth_file, recipient = gmail_from_existing()
    print("MACHINE_CONFIG=PASS; ALCHEMY_RPC=REUSED_READ_ONLY; GMAIL_OAUTH=REUSED_READ_ONLY; FRANK=UNTOUCHED")
    if args.command == "check":
        print("NO_NETWORK_NO_MAIL_NO_DAEMON")
        return 0

    # Live read-only credential checks and bounded health RPC before any send.
    provider = GmailAPI(oauth_file, recipient)
    try:
        provider.ready()
        health = Rpc(http_rpc).call("getHealth", [])
        if health != "ok":
            raise StartupBlocked("SOLANA_RPC_HEALTH_NOT_OK")
    except StartupBlocked:
        raise
    except Exception as exc:
        raise StartupBlocked("LIVE_GMAIL_OR_SOLANA_PROBE_FAILED") from None
    print("LIVE_PROBE=PASS; SOLANA_HTTP_AND_GMAIL_PROFILE_SENT_READ=OK")
    if args.command == "probe":
        print("NO_EMAIL_SENT; FRANK_UNTOUCHED")
        return 0

    state = state_directory()
    lock_file = state / "machine-fun-run.lock"
    with lock_file.open("a") as lock:
        os.chmod(lock_file, 0o600)
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise StartupBlocked("MACHINE_FUN_ALREADY_RUNNING") from None
        journal = Journal(state / "launch-events.sqlite")
        try:
            alerts = GmailAlerts(state / "gmail-alerts.sqlite", oauth_file, recipient)
            detector = GmailDetector(Rpc(http_rpc), journal, alerts, local_notification=args.notify_local)
            print("MACHINE_LIVE_START=YES; EMAIL_ONLY_REAL_NEW_CHAIN_CANDIDATES; CTRL_C_TO_STOP")
            asyncio.run(listen(ws_rpc, detector))
        except KeyboardInterrupt:
            print("MACHINE_LIVE_STOPPED_BY_USER")
        finally:
            journal.close()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (StartupBlocked, MailBlocked) as err:
        # Never display any secret URLs, OAuth JSON, request bodies or full tracebacks.
        print("MACHINE_START_BLOCKED: " + str(err), file=sys.stderr)
        raise SystemExit(2) from None
