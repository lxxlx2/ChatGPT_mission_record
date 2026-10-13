"""Manual, read-only person/mint source report from an existing research sidecar."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from mission_agent.mission_control.person_registry import PersonRegistry
from mission_agent.mission_control.research_wallet_facts import PersonResearchReader
from mission_agent.mission_control.wallet_capture_provider import CapturedWalletFactsProvider
from mission_agent.mission_control.wallet_evidence_store import WalletEvidenceStore


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SIDECAR = Path.home() / "Library" / "Application Support" / "FrankMeme" / "research-wallet-evidence.sqlite"


def main(argv=None):
    parser = argparse.ArgumentParser(description="Read archived Frank research wallet mint balances; no RPC")
    parser.add_argument("--registry", type=Path, default=ROOT / "config" / "frank_local_registry.json")
    parser.add_argument("--sidecar", type=Path, default=DEFAULT_SIDECAR)
    parser.add_argument("--person-id", default="frank")
    parser.add_argument("--mint", required=True)
    parser.add_argument("--as-of-slot", type=int, required=True)
    args = parser.parse_args(argv)
    # Read-only sidecar requires an existing file and may not create a
    # misleading empty database or access production forward.sqlite.
    store = WalletEvidenceStore(args.sidecar, read_only=True)
    try:
        registry = PersonRegistry.from_file(args.registry)
        reader = PersonResearchReader(registry, CapturedWalletFactsProvider(store))
        result = reader.mint_observations(
            person_id=args.person_id, mint=args.mint, as_of_slot=args.as_of_slot)
    finally:
        store.close()
    print(json.dumps(result, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, KeyError, PermissionError, OSError):
        print("RESEARCH_READ_FAILED", file=sys.stderr)
        sys.exit(1)
