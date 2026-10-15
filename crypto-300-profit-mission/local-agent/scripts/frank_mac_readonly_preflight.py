"""Mac-only passive Frank F01/C02/F02 preflight: metadata, never content.

Reads local Git object identities, known research-session *existence*, and
loopback listening-port metadata. Never fetches, writes, imports SQLite,
starts listeners or services, connects to RPC, reads private raw payloads,
prints paths, lists wallet/CA identities, or cleans anything.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess

EXPECTED_PINS = {
    "main_snapshot": "662ba4aceb9d53cb7a541ad3f251f9e12b8c09ea",
    "pr73_reviewed": "5755b8b96080f21635eaa5354588cbb8f6561ab0",
    "f01": "516e3335a134c608f477019b79027982f43af32a",
    "c02": "8898134a8a302e1187138f7fb3da87a554567e6d",
    "pr71_reviewed": "d998fb5966fac2eee5dbeedca5f78126d1b51b6d",
}
EVIDENCE_REF = "refs/remotes/origin/evidence/frank-ca-local"
EXPECTED_EVIDENCE_SHA = "b9fb6e6df9032a0e6f49c1274bb4ba61c9e4c2da"
PORTS = {"f02_research": 18765, "f01_c02_control": 18766,
         "readonly_bridge": 18777}
SESSION_SCAN_LIMIT = 200


def safe_exec(argv: list[str], *, cwd: Path | None = None) -> tuple[int, str]:
    """Read-only preflight: suppress configured Git fsmonitor executables."""
    if argv and argv[0] == "git":
        # GIT_OPTIONAL_LOCKS=0 does not prevent git status from executing
        # core.fsmonitor. Git's command-scope -c overrides repository/global
        # helpers for every Git read in this preflight.
        argv = ["git", "-c", "core.fsmonitor=false", *argv[1:]]
    try:
        result = subprocess.run(
            argv, cwd=cwd, stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            text=True, timeout=8, check=False,
            env={**os.environ, "GIT_OPTIONAL_LOCKS": "0",
                 "GIT_TERMINAL_PROMPT": "0", "GIT_TRACE": "0"},
        )
        return result.returncode, result.stdout[:4096].strip()
    except (FileNotFoundError, OSError, subprocess.TimeoutExpired):
        return 125, ""


def inspect_repo(path: Path) -> dict:
    if path.is_symlink() or not path.is_dir():
        return {"state": "NOT_FOUND_OR_UNSAFE"}
    # The --git-dir lookup must not treat a random enclosing repository as the
    # exact existing user clone. Do not fetch/reset/check out branches.
    code, root = safe_exec(
        ["git", "-C", str(path), "rev-parse", "--show-toplevel"])
    if code != 0 or not root or Path(root).resolve() != path.resolve():
        return {"state": "NOT_A_STANDALONE_REPO"}
    code, head = safe_exec(["git", "-C", str(path), "rev-parse", "HEAD"])
    if code != 0 or len(head) != 40:
        return {"state": "GIT_HEAD_UNAVAILABLE"}
    # Deliberately do not inspect working-tree content here. git status and
    # git diff can invoke filter.<driver>.clean from tracked .gitattributes,
    # even when fsmonitor is disabled. A passive metadata check cannot prove
    # that the checkout is clean without crossing that execution boundary.
    status = "UNKNOWN_NOT_CHECKED_PASSIVE_ONLY"
    pins = {}
    for label, sha in EXPECTED_PINS.items():
        code, resolved = safe_exec(
            ["git", "-C", str(path), "rev-parse", "--verify",
             f"{sha}^{{commit}}"])
        pins[label] = "PRESENT" if code == 0 and resolved == sha else "NOT_LOCAL"
    code, evidence = safe_exec(
        ["git", "-C", str(path), "rev-parse", "--verify", EVIDENCE_REF])
    evidence_status = (
        "EXPECTED_LOCAL_SHA" if code == 0 and evidence == EXPECTED_EVIDENCE_SHA
        else "DIFFERENT_LOCAL_SHA" if code == 0
        else "NOT_LOCAL"
    )
    return {
        "state": "READ_ONLY_INSPECTED",
        "head_matches_reviewed_pr73": head == EXPECTED_PINS["pr73_reviewed"],
        "head_matches_previous_pr68": head.startswith("2d2e4d5c"),
        "source_changes": status,
        "fixed_git_objects": pins,
        "historical_evidence_ref": evidence_status,
    }


def _limited_directories(root: Path, *, prefix: str) -> tuple[list[Path], bool]:
    if root.is_symlink() or not root.is_dir():
        return [], False
    matches: list[Path] = []
    truncated = False
    try:
        with os.scandir(root) as entries:
            for entry in entries:
                if not entry.name.startswith(prefix):
                    continue
                if entry.is_symlink() or not entry.is_dir(follow_symlinks=False):
                    continue
                if len(matches) >= SESSION_SCAN_LIMIT:
                    truncated = True
                    break
                matches.append(Path(entry.path))
    except OSError:
        return [], True
    return matches, truncated


def inspect_private_sessions(root: Path) -> dict:
    """Existence only. No manifest JSON, wire, wallet, token or SQLite read."""
    if root.is_symlink():
        return {"state": "UNSAFE_SYMLINK", "sessions": None}
    if not root.is_dir():
        return {"state": "NOT_FOUND", "sessions": 0}
    sessions, truncated = _limited_directories(root, prefix="session-")
    sidecars = bundles = paired = 0
    for session in sessions:
        sidecar = session / "positions.sqlite"
        has_sidecar = sidecar.is_file() and not sidecar.is_symlink()
        has_manifest = False
        wire = session / "wire"
        owners, _ = _limited_directories(wire, prefix="owner-")
        for owner in owners:
            manifest = owner / "manifest.json"
            if manifest.is_file() and not manifest.is_symlink():
                has_manifest = True
                break
        sidecars += int(has_sidecar)
        bundles += int(has_manifest)
        paired += int(has_sidecar and has_manifest)
    return {
        "state": "INVENTORY_ONLY",
        "sessions": len(sessions),
        "session_scan_truncated": truncated,
        "sessions_with_sidecar_file": sidecars,
        "sessions_with_wire_manifest": bundles,
        "sessions_with_both_files": paired,
        "contents_or_sha_verified": False,
        "session_freshness_verified": False,
    }


def inspect_port(port: int) -> str:
    """Read listening socket list; does not connect, bind or start service."""
    if shutil.which("lsof") is None:
        return "CANNOT_CHECK_NO_LSOF"
    code, output = safe_exec(
        ["lsof", "-nP", "-iTCP:" + str(port), "-sTCP:LISTEN", "-F", "p"])
    if code == 0:
        return "LISTENER_PRESENT" if output else "CHECK_UNCERTAIN"
    if code == 1:
        return "NO_LISTENER_SEEN"
    return "CHECK_UNAVAILABLE"


def run(*, home: Path, repo: Path | None = None) -> dict:
    repo = repo if repo is not None else (
        home / ".local/share/frank-f02-r3-review")
    research = home / ".local/share/frank-f02-research/manual-sessions"
    repo_result = inspect_repo(repo)
    sessions_result = inspect_private_sessions(research)
    ports = {name: inspect_port(value) for name, value in PORTS.items()}
    return {
        "schema": "FRANK_MAC_PASSIVE_PREFLIGHT_V1",
        "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "READ_EXISTING_LOCAL_METADATA_ONLY",
        "known_review_clone": repo_result,
        "private_f02_session_inventory": sessions_result,
        "loopback_port_listener_presence": ports,
        "not_a_live_portfolio_or_current_f01_verification": True,
        "next_gate": "USER_REVIEW_OF_SANITIZED_RESULT_BEFORE_ANY_SERVICE",
        "side_effects": {
            "git_fetch_or_checkout": False,
            "files_written_or_deleted": False,
            "sqlite_opened": False,
            "private_wire_read": False,
            "http_or_rpc_requested": False,
            "service_or_socket_started": False,
            "gmail_trade_automation": False,
        },
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=None,
                        help="Existing local repository; read-only")
    args = parser.parse_args(argv)
    print(json.dumps(run(home=Path.home(), repo=args.repo),
                     ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
