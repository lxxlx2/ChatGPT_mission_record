"""Explicit, bounded, read-only Frank ATA forensic backfill.

Example from research branch (no install, restart, or writer policy change):
python -m scripts.frank_ata_backfill --database /path/to/forward.sqlite \
  --mint J7bhFegCHZAeRzdYDwmbSp1CJ1bDJkutSg26B4SXpump \
  --output /path/to/j7-ata-readonly.json

Only getSignaturesForAddress/getTransaction against official Solana RPC.
No signer, order submission, Git upload, background daemon or monitoring.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path

from mission_agent.frank.rpc import SolanaRPC
from mission_agent.mission_control.db import open_production_ro
from mission_agent.mission_control.ata_backfill import scan_ata_mints
from mission_agent.mission_control.evidence_sync import (
    EvidenceSpool, GitEvidencePublisher, PREFIX, MAX_REMOTE_BYTES,
    canonical, safe, digest,
)


def run(argv: list[str] | None = None, *, rpc=None) -> dict:
    parser = argparse.ArgumentParser(description="Read-only bounded Frank ATA source audit")
    parser.add_argument("--database", required=True, type=Path)
    parser.add_argument("--mint", required=True, action="append",
                        help="Explicit Solana token Mint, repeat <=12 times")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--since-time", type=int, default=0,
                        help="UTC Unix timestamp lower-bound (0 = bounded recent history only)")
    parser.add_argument("--page-size", type=int, default=50)
    parser.add_argument("--pages-per-ata", type=int, default=2)
    parser.add_argument("--max-transactions", type=int, default=40)
    parser.add_argument("--sync-git", action="store_true",
                        help="Opt-in readback verified publication to existing evidence Git branch")
    args = parser.parse_args(argv)
    if args.output.exists():
        raise FileExistsError("OUTPUT_ALREADY_EXISTS_NO_OVERWRITE")
    with open_production_ro(args.database) as conn:
        rows = conn.execute(
            "SELECT signature FROM signatures WHERE person_id='frank'")
        known = {row["signature"] for row in rows}
    snapshot = scan_ata_mints(
        rpc if rpc is not None else SolanaRPC(), args.mint, known,
        since_time=args.since_time, page_size=args.page_size,
        max_pages_per_ata=args.pages_per_ata,
        max_tx_fetches=args.max_transactions,
    )
    snapshot["local_signature_index_count"] = len(known)
    snapshot["local_signature_source"] = "READ_ONLY_FORWARD_SQLITE"
    payload = json.dumps(snapshot, ensure_ascii=False,
                         sort_keys=True, separators=(",", ":")).encode("utf-8")
    if len(payload) > 2_000_000:
        raise ValueError("ATA_EVIDENCE_OVER_2MB")
    # Exclusive create is intentional; never replace a forensic artifact.
    args.output.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(str(args.output), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        args.output.unlink(missing_ok=True)
        raise
    result = {"output": str(args.output), "size": len(payload),
              "sha256": hashlib.sha256(payload).hexdigest(),
              "absent_verified_signatures": len(
                  snapshot["verified_nonzero_signatures_absent_from_local_index"] or []),
              "wallet_history_complete": False,
              "production_modified": False, "git_sync": "NOT_REQUESTED"}
    if args.sync_git:
        try:
            cleaned = canonical(safe(snapshot))
            if len(cleaned) > MAX_REMOTE_BYTES:
                raise ValueError("GIT_ATA_EVIDENCE_OVER_REMOTE_LIMIT")
            # Safe, immutable SHA-addressed output on the existing separate
            # evidence branch, NOT main and NOT a live Frank service.
            identifier = digest(cleaned)
            spool = EvidenceSpool(args.output.parent / ".frank-ata-git-spool")
            destination = f"{PREFIX}/frank-ata-backfill/{identifier}.json"
            GitEvidencePublisher(spool)._upload(destination, cleaned)
            result["git_sync"] = "SYNC_OK_READBACK_VERIFIED"
            result["git_snapshot_id"] = identifier
        except (OSError, RuntimeError, ValueError) as exc:
            result["git_sync"] = "SYNC_FAILED_LOCAL_FILE_RETAINED"
            result["git_error_type"] = type(exc).__name__
    return result


def main(argv: list[str] | None = None) -> int:
    result = run(argv)
    print(json.dumps(result, sort_keys=True))
    return 2 if result["git_sync"] == "SYNC_FAILED_LOCAL_FILE_RETAINED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
