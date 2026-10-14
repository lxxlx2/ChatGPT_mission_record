"""Offline A05/F02 research snapshot view; no RPC, writer or live decisions.

Run after an explicitly authorized manual A05 capture has been imported into
a separate research sidecar. Input exact Mints are from a caller-owned file,
not hardcoded into the model.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

from mission_agent.mission_control.wallet_evidence_store import WalletEvidenceStore
from mission_agent.mission_control.wallet_inventory_snapshot import latest_inventory

DEFAULT_SIDECAR = (Path.home() / "Library" / "Application Support" /
                   "FrankMeme" / "research-wallet-evidence.sqlite")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Read only latest captured A05 research positions")
    parser.add_argument("--wallet", required=True)
    parser.add_argument("--mint-file", required=True, type=Path,
                        help="JSON array of 1-128 exact mint addresses; 32 expected for Frank acceptance")
    parser.add_argument("--sidecar", type=Path, default=DEFAULT_SIDECAR)
    parser.add_argument("--max-age-seconds", type=int, default=300)
    args = parser.parse_args(argv)
    mints = json.loads(args.mint_file.read_text(encoding="utf-8"))
    store = WalletEvidenceStore(args.sidecar, read_only=True)
    try:
        result = latest_inventory(
            store, wallet=args.wallet, mints=mints,
            as_of_utc=datetime.now(timezone.utc),
            max_age_seconds=args.max_age_seconds,
        )
    finally:
        store.close()
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, FileNotFoundError, PermissionError, OSError):
        print("RESEARCH_LATEST_INVENTORY_UNAVAILABLE", file=sys.stderr)
        sys.exit(1)
