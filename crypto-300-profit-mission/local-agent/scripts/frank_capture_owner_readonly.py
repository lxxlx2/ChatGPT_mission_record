"""Explicit manual Frank A05 read-only account capture into a research sidecar.

No automatic run, no production file writes, no credential output. Default is
plan-only. --execute does two finalized owner queries (SPL + Token-2022).
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
from mission_agent.mission_control.wallet_chain_capture import capture_owner
from mission_agent.mission_control.wallet_evidence_store import WalletEvidenceStore


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = ROOT / "config" / "frank_local_registry.json"
DEFAULT_SIDECAR = Path.home() / "Library" / "Application Support" / "FrankMeme" / "research-wallet-evidence.sqlite"
MAX_REPLY_BYTES = 12_000_000


def _rpc(url):
    target = urllib.parse.urlparse(url)
    if target.scheme != "https" or not target.hostname or target.username or target.password:
        raise ValueError("HTTPS_RPC_URL_REQUIRED")
    counter = 0

    def call(method, params):
        nonlocal counter
        counter += 1
        if counter > 2 or method != "getTokenAccountsByOwner":
            raise ValueError("ONLY_DUAL_TOKEN_OWNER_RPC_ALLOWED")
        raw = json.dumps({"jsonrpc": "2.0", "id": counter,
                          "method": method, "params": params}).encode()
        req = urllib.request.Request(
            url, raw, {"Content-Type": "application/json"}, method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=18) as result:
                chunk = result.read(MAX_REPLY_BYTES + 1)
        except (OSError, TimeoutError) as exc:
            raise RuntimeError("RPC_CONNECTION_UNAVAILABLE") from exc
        if len(chunk) > MAX_REPLY_BYTES:
            raise ValueError("RPC_REPLY_LIMIT_EXCEEDED")
        try:
            response = json.loads(chunk)
        except (TypeError, ValueError) as exc:
            raise RuntimeError("RPC_INVALID_JSON") from exc
        if not isinstance(response, dict) or response.get("id") != counter:
            raise ValueError("RPC_ID_MISMATCH")
        # normalize_owner_program distinguishes an RPC error from empty value.
        return response
    return call


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Explicit read-only A05 token account capture")
    parser.add_argument("--person-id", default="frank")
    parser.add_argument("--wallet")
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--sidecar", type=Path, default=DEFAULT_SIDECAR)
    parser.add_argument("--rpc-url", default=os.environ.get(
        "FRANK_RESEARCH_SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com"))
    parser.add_argument("--min-context-slot", type=int)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args(argv)

    registry = PersonRegistry.from_file(args.registry)
    wallets = registry.wallets_for(args.person_id)
    allowed = [w for w in wallets if w.chain == "solana"]
    if args.wallet is not None:
        allowed = [w for w in allowed if w.address == args.wallet]
    if len(allowed) != 1:
        raise ValueError("SELECT_EXACTLY_ONE_REGISTERED_RESEARCH_WALLET")
    wallet = allowed[0]
    if not args.execute:
        print(json.dumps({
            "status": "PLAN_ONLY", "person_id": args.person_id,
            "wallet": wallet.address, "program_query_count": 2,
            "sidecar": str(args.sidecar),
            "writes_production_sqlite": False, "sends_gmail": False,
            "network_invoked": False,
        }, sort_keys=True))
        return 0
    # Never print RPC URL; it may include a credential. This explicit command
    # is limited to two program reads and an independent research sidecar.
    result = capture_owner(wallet.address, _rpc(args.rpc_url),
                           min_context_slot=args.min_context_slot)
    store = WalletEvidenceStore(args.sidecar)
    try:
        imported = store.capture_wallet(result)
    finally:
        store.close()
    print(json.dumps({
        "status": result["status"], "captured_new": imported,
        "both_programs_observed": result["both_programs_observed"],
        "wallet_account_count": result["account_count"],
        "mint_count_observed": result["mint_count_observed"],
        "slot_min": result["slot_min"], "slot_max": result["slot_max"],
        "partial_errors": result["missing"],
        "saved_locally": True,
        "source_capture_sha256": result["capture_sha256"],
        "usd_nav_verified": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, OSError) as exc:
        print("RESEARCH_CAPTURE_FAILED " + type(exc).__name__, file=sys.stderr)
        sys.exit(1)
