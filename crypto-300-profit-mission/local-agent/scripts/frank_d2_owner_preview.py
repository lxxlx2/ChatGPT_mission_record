"""Manual Frank D2 OFFLINE HTML preview from an exact PR60 verified raw bundle.

Only reads local files and executes the audited PR60 replay in an isolated,
network-denied Python child. No HTTP/RPC, production DB, signal, or scheduler.
The full owner accounts never enter the output HTML; output is mode 0600.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

LOCAL_AGENT = Path(__file__).resolve().parents[1]
REPO_ROOT = LOCAL_AGENT.parents[1]
PINNED_PR60 = "e4529ba7069e5499d12323a7160ceac08c481fae"

sys.path.insert(0, str(LOCAL_AGENT))
from mission_agent.mission_control.wallet_owner_at_slot import (
    FRANK_WALLET, project_replayed_owner, render_offline_html,
)


def _git(root, *args):
    cp = subprocess.run(["git", "-C", str(root), *args],
                        capture_output=True, text=True, timeout=15, check=False)
    if cp.returncode:
        raise ValueError("PR60_CHECKOUT_VERIFICATION_FAILED")
    return cp.stdout.strip()


def _check_pinned_pr60(root):
    root = root.resolve(strict=True)
    if _git(root, "rev-parse", "HEAD") != PINNED_PR60:
        raise ValueError("PR60_CHECKOUT_SHA_MISMATCH")
    if _git(root, "status", "--porcelain", "--untracked-files=all"):
        raise ValueError("PR60_CHECKOUT_NOT_CLEAN")
    local = root / "crypto-300-profit-mission" / "local-agent"
    required = (
        "mission_agent/mission_control/wallet_full_rpc_evidence.py",
        "mission_agent/mission_control/wallet_chain_capture.py",
        "mission_agent/mission_control/person_registry.py",
        "config/frank_local_registry.json",
    )
    for rel in required:
        candidate = local / rel
        if not candidate.is_file() or candidate.is_symlink():
            raise ValueError("PR60_CHECKOUT_FILE_MISSING")
        expected = subprocess.run(
            ["git", "-C", str(root), "show",
             PINNED_PR60 + ":crypto-300-profit-mission/local-agent/" + rel],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            timeout=15, check=True).stdout
        if candidate.read_bytes() != expected:
            raise ValueError("PR60_CHECKOUT_SOURCE_BYTES_CHANGED")
    return local


def _offline_verified_replay(pr60_agent, bundle):
    # Process isolation means the unmerged reviewed PR60 Python package,
    # rather than a similarly named deployed library, performs verification.
    code = """
import json, socket, sys
from pathlib import Path
def offline(*args, **kwargs):
    raise RuntimeError("OFFLINE_REPLAY_NETWORK_FORBIDDEN")
socket.create_connection = offline
socket.socket.connect = offline
socket.socket.connect_ex = offline
sys.path.insert(0, sys.argv[1])
from mission_agent.mission_control.wallet_full_rpc_evidence import replay_owner_full_receipts
from mission_agent.mission_control.person_registry import PersonRegistry
root = Path(sys.argv[1])
registry = PersonRegistry.from_file(root / "config/frank_local_registry.json")
wallets = [w for w in registry.wallets_for("frank") if w.chain == "solana" and w.address == sys.argv[3]]
if len(wallets) != 1:
    raise ValueError("FRANK_OWNER_REGISTRY_UNVERIFIED")
snapshot = replay_owner_full_receipts(Path(sys.argv[2]), expected_wallet=sys.argv[3])
print(json.dumps(snapshot, sort_keys=True, ensure_ascii=False, separators=(",", ":")))
"""
    proc = subprocess.run([sys.executable, "-I", "-B", "-c", code,
                           str(pr60_agent), str(bundle), FRANK_WALLET],
                          capture_output=True, timeout=90, check=False)
    if proc.returncode or len(proc.stdout) > 35_000_000:
        # Never expose stderr: traceback could contain private filesystem paths.
        raise ValueError("PINNED_PR60_OFFLINE_REPLAY_FAILED")
    try:
        return json.loads(proc.stdout)
    except (ValueError, UnicodeDecodeError) as exc:
        raise ValueError("PINNED_PR60_REPLAY_JSON_INVALID") from exc


def _read_json(path, limit):
    path = path.expanduser().resolve(strict=True)
    if not path.is_file() or path.stat().st_size > limit:
        raise ValueError("INPUT_EVIDENCE_FILE_INVALID")
    return json.loads(path.read_text(encoding="utf-8"))


def _target_mints(data):
    if isinstance(data, dict):
        data = data.get("records")
    if not isinstance(data, list):
        raise ValueError("TARGET_FILE_INVALID")
    return [row["mint"] if isinstance(row, dict) else row for row in data]


def _private_create(path, html):
    path = path.expanduser().absolute()
    if not path.is_absolute() or path.suffix.lower() != ".html":
        raise ValueError("PRIVATE_PREVIEW_PATH_INVALID")
    if path == REPO_ROOT or REPO_ROOT in path.parents:
        raise ValueError("PUBLIC_GIT_HTML_OUTPUT_FORBIDDEN")
    if path.is_symlink() or any(parent.is_symlink() for parent in path.parents):
        raise ValueError("PRIVATE_PREVIEW_SYMLINK_FORBIDDEN")
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if path.parent.stat().st_mode & 0o077:
        raise ValueError("PRIVATE_PREVIEW_PARENT_NOT_PRIVATE")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    flags |= getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(path, flags, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(html)
            f.flush()
            os.fsync(f.fileno())
    except BaseException:
        path.unlink(missing_ok=True)
        raise
    return path


def main(argv=None):
    parser = argparse.ArgumentParser(description="PR60 fixed-SHA zero-RPC Frank D2 preview")
    parser.add_argument("--pr60-checkout", type=Path, required=True)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--watchlist-json", type=Path, required=True)
    parser.add_argument("--targets-json", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    reviewed = _check_pinned_pr60(args.pr60_checkout)
    # The original replay checks raw bytes SHA, owner, both programs and slots.
    snapshot = _offline_verified_replay(reviewed, args.bundle)
    observed = _read_json(args.watchlist_json, 8_000_000)
    targets_file = args.targets_json or (
        REPO_ROOT / "crypto-300-profit-mission" / "meme" / "evidence" /
        "frank-v2-thirty-two-mint-finalized-2026-10-11.json"
    )
    targets = _target_mints(_read_json(targets_file, 500_000))
    report = project_replayed_owner(snapshot, observed, target_mints=targets)
    html = render_offline_html(report)
    result = _private_create(args.output, html)
    # Print only sanitized aggregate data; do not print private Mint lists/raw.
    print(json.dumps({
        "status": report["status"], "source": "PRIVATE_PR60_REPLAY",
        "source_observed_at_utc": report["observed_at_utc"],
        "program_slots": [p["slot"] for p in report["program_coverage"]],
        "source_account_count": report["account_count"],
        "source_mint_count": report["mint_count"],
        "watchlist_mints": report["local_watchlist_mints"],
        "visible_rows": len(report["preview_rows"]),
        "output_mode": "0600", "new_rpc": 0,
        "production_write": False, "deployed": False,
    }, sort_keys=True))
    return result


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        # Deliberately suppress actual exception contents, paths and secrets.
        print("D2_OFFLINE_PREVIEW_FAIL_CLOSED:" + type(exc).__name__,
              file=sys.stderr)
        sys.exit(2)
