"""Manual, ZERO-RPC D2 source document exporter. No production import.

Pin and replay the already saved full owner bundle through the audited PR60
checkout, project every Mint (not just the 200 HTML rows), and exclusively
create a private JSON file OUTSIDE ANY Git repository. Do not run without
separate operator permission for the specific private output destination.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_ROOT = Path(__file__).resolve().parent
AGENT_ROOT = SCRIPT_ROOT.parent
sys.path.insert(0, str(SCRIPT_ROOT))
sys.path.insert(0, str(AGENT_ROOT))

from frank_d2_owner_preview import (
    _check_pinned_pr60, _offline_verified_replay, _private_create,
)
from mission_agent.mission_control.wallet_d2_ingress import (
    build_d2_document_from_verified_pr60_replay, validate_d2_document,
)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Manual only: fixed PR60 replay -> private complete Mint JSON")
    parser.add_argument("--pr60-checkout", required=True, type=Path)
    parser.add_argument("--bundle", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    opts = parser.parse_args(argv)
    original_pr60 = _check_pinned_pr60(opts.pr60_checkout)
    replayed = _offline_verified_replay(original_pr60, opts.bundle)
    projected = build_d2_document_from_verified_pr60_replay(replayed)
    validate_d2_document(projected)
    raw = json.dumps(projected, ensure_ascii=False, sort_keys=True,
                     separators=(",", ":"), allow_nan=False)
    # Unlike the HTML preview, this JSON includes ALL Mint-level balances.
    # The existing Git-external, symlink-denying 0700/0600 O_EXCL guard also
    # applies to this manually created private file.
    _private_create(opts.output, raw, suffix=".json")
    print(json.dumps({
        "status": "PRIVATE_D2_SOURCE_EXPORTED_NOT_IMPORTED",
        "mints": projected["mint_count"],
        "token_accounts": projected["account_count"],
        "observed_at_utc": projected["observed_at_utc"],
        "finalized_slots": [v["slot"] for v in projected["program_coverage"]],
        "same_slot_atomic": False,
        "current_chain_balance_verified": False,
        "production_imported": False,
        "new_rpc": 0,
        "deployment": False,
    }, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, TypeError) as exc:
        # Never print exception text, raw paths, source data or wallet Mint list.
        print("FRANK_D2_EXPORT_FAIL_CLOSED:" + type(exc).__name__,
              file=sys.stderr)
        sys.exit(2)
