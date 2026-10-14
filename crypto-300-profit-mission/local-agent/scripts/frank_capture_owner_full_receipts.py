"""Explicit A05 full JSON-RPC wire-byte capture or offline source replay.

No scheduler or Frank V1 interactions. Default PLAN_ONLY has no network/writes.
--execute: two HTTPS finalized owner queries, archive complete raw replies.
--replay-bundle: verify raw bytes and owner/slot off-line, without RPC.
--import-sidecar: separately authorized *research* SQLite archive only if
both full official program receipts pass independent replay checks.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
import urllib.parse
import urllib.request

from mission_agent.mission_control.person_registry import PersonRegistry
from mission_agent.mission_control.wallet_evidence_store import WalletEvidenceStore
from mission_agent.mission_control.wallet_full_rpc_evidence import (
    MAX_RAW_RPC_BYTES, collect_owner_full_receipts,
    replay_owner_full_receipts,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = ROOT / "config" / "frank_local_registry.json"
DEFAULT_SIDECAR = (Path.home() / "Library" / "Application Support" /
                   "FrankMeme" / "research-wallet-evidence.sqlite")
DEFAULT_EVIDENCE = (Path.home() / ".local" / "share" /
                    "frank-owner-full-rpc-evidence")


def _wire_rpc(url: str):
    parsed = urllib.parse.urlparse(url)
    if (parsed.scheme != "https" or not parsed.hostname
            or parsed.username is not None or parsed.password is not None
            or parsed.fragment):
        raise ValueError("HTTPS_RPC_URL_REQUIRED")
    calls = 0

    def read_raw(method, params, expected_id):
        nonlocal calls
        calls += 1
        if (method != "getTokenAccountsByOwner" or calls > 2
                or calls != expected_id):
            raise ValueError("ONLY_TWO_OWNER_READ_RPC_ALLOWED")
        request = json.dumps({
            "jsonrpc": "2.0", "id": expected_id,
            "method": method, "params": params,
        }, separators=(",", ":")).encode("utf-8")
        req = urllib.request.Request(
            url, request, {"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=25) as response:
                result = response.read(MAX_RAW_RPC_BYTES + 1)
        except (OSError, TimeoutError) as exc:
            # Never include an exception message; it may include RPC URL/key.
            raise RuntimeError("OWNER_RPC_TRANSPORT_UNAVAILABLE") from exc
        if len(result) > MAX_RAW_RPC_BYTES:
            raise ValueError("OWNER_RPC_WIRE_SIZE_LIMIT")
        return result
    return read_raw


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="A05 manual complete-wire-owner source archive and replay")
    parser.add_argument("--person-id", default="frank")
    parser.add_argument("--wallet")
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--evidence-dir", type=Path, default=DEFAULT_EVIDENCE)
    parser.add_argument("--sidecar", type=Path, default=DEFAULT_SIDECAR)
    parser.add_argument("--rpc-url", default=os.environ.get(
        "FRANK_RESEARCH_SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com"))
    parser.add_argument("--min-context-slot", type=int)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--replay-bundle", type=Path)
    parser.add_argument("--import-sidecar", action="store_true")
    args = parser.parse_args(argv)

    if args.execute and args.replay_bundle is not None:
        raise ValueError("CHOOSE_CAPTURE_OR_OFFLINE_REPLAY")
    if args.import_sidecar and not (args.execute or args.replay_bundle):
        raise ValueError("RESEARCH_IMPORT_REQUIRES_EXPLICIT_MODE")
    registry = PersonRegistry.from_file(args.registry)
    entries = [w for w in registry.wallets_for(args.person_id)
               if w.chain == "solana"
               and (args.wallet is None or w.address == args.wallet)]
    if len(entries) != 1:
        raise ValueError("SELECT_EXACTLY_ONE_REGISTERED_RESEARCH_WALLET")
    owner = entries[0].address
    if not args.execute and args.replay_bundle is None:
        print(json.dumps({
            "status": "PLAN_ONLY",
            "wallet": owner,
            "queries": 2,
            "complete_raw_rpc_required": True,
            "sidecar_import_requested": False,
            "network_invoked": False,
            "writes_production_sqlite": False,
        }, sort_keys=True))
        return 0

    if args.execute:
        capture = collect_owner_full_receipts(
            wallet=owner, evidence_root=args.evidence_dir,
            read_raw=_wire_rpc(args.rpc_url),
            min_context_slot=args.min_context_slot,
        )
        bundle = Path(capture["bundle"])
        manifest = capture["manifest"]
        if not manifest["complete"]:
            # Partial result is preserved as evidence manifest, never
            # mistaken for verified full owner account coverage.
            print(json.dumps({
                "status": "PARTIAL_SOURCE",
                "evidence_bundle": str(bundle),
                "full_receipts": len(manifest["receipts"]),
                "missing_programs": [x["program_id"]
                                     for x in manifest["missing"]],
                "research_sidecar_imported": False,
            }, sort_keys=True))
            return 2
    else:
        bundle = args.replay_bundle
        manifest = None

    snapshot = replay_owner_full_receipts(bundle, expected_wallet=owner)
    imported = None
    if args.import_sidecar:
        sidecar = WalletEvidenceStore(args.sidecar)
        try:
            imported = sidecar.capture_wallet(snapshot)
        finally:
            sidecar.close()
    print(json.dumps({
        "status": "FULL_DUAL_PROGRAM_SOURCE_REPLAY_VERIFIED",
        "wallet": owner,
        "evidence_bundle": str(bundle),
        "capture_sha256": snapshot["capture_sha256"],
        "slot_min": snapshot["slot_min"],
        "slot_max": snapshot["slot_max"],
        "token_account_count": snapshot["account_count"],
        "mint_count_observed_not_32_roster": snapshot["mint_count_observed"],
        "same_slot_atomic": False,
        "target_32_mints_verified": False,
        "research_sidecar_imported": imported,
        "writes_production_sqlite": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, OSError, RuntimeError, TypeError, KeyError):
        print("RESEARCH_OWNER_SOURCE_NOT_VERIFIED", file=sys.stderr)
        sys.exit(1)
