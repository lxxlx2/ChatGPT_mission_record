"""Manual fresh F02 research session: two owner reads, wire replay, new Sidecar.

Default is PLAN_ONLY. --execute explicitly authorizes bounded RPC and a NEW
private session; --serve additionally opens the isolated loopback view. Never
updates the existing archived research Sidecar or the production Dashboard.
"""
from __future__ import annotations

import argparse
from http.server import ThreadingHTTPServer
import json
import os
from pathlib import Path
import sqlite3
import sys
import uuid

from mission_agent.mission_control.person_registry import PersonRegistry
from mission_agent.mission_control.wallet_evidence_store import WalletEvidenceStore
from mission_agent.mission_control.wallet_full_rpc_evidence import (
    _assert_directory, collect_owner_full_receipts, replay_owner_full_receipts,
)
from scripts.frank_capture_owner_full_receipts import _wire_rpc
from scripts.frank_f02_readonly_positions_api import ResearchPositions, make_handler
from scripts.frank_reconcile_frozen32_offline import REGISTRY, ROSTER, load_frozen_roster, reconcile

SESSION_ROOT = Path.home() / ".local/share/frank-f02-research/manual-sessions"


def refresh_session(*, session_root: Path, read_raw, registry: Path = REGISTRY,
                    roster: Path = ROSTER) -> tuple[dict, ResearchPositions | None]:
    wallets = [w for w in PersonRegistry.from_file(registry).wallets_for("frank")
               if w.chain == "solana"]
    if len(wallets) != 1:
        raise ValueError("F02_EXACTLY_ONE_RESEARCH_WALLET_REQUIRED")
    wallet = wallets[0].address
    targets = load_frozen_roster(roster, wallet)
    root = _assert_directory(session_root)
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    # Each attempted acquisition has a distinct directory. There is no
    # old-source fallback or caller-supplied existing SQLite destination.
    session = root / ("session-" + uuid.uuid4().hex)
    session.mkdir(mode=0o700)
    capture = collect_owner_full_receipts(
        wallet=wallet, evidence_root=session / "wire", read_raw=read_raw)
    summary = {
        "status": "PARTIAL_SOURCE", "session_directory": str(session),
        "evidence_bundle": capture["bundle"], "network_invoked": True,
        "rpc_query_limit": 2, "sidecar_created": False,
        "old_source_reused": False, "writes_production_sqlite": False,
        "signals_allowed": False, "trades_allowed": False,
    }
    if not capture["manifest"]["complete"]:
        summary["missing_program_count"] = len(capture["manifest"]["missing"])
        return summary, None
    bundle = Path(capture["bundle"])
    verified = replay_owner_full_receipts(bundle, expected_wallet=wallet)
    reconciliation = reconcile(verified, targets)
    sidecar = session / "positions.sqlite"
    store = WalletEvidenceStore(sidecar)
    try:
        store.capture_wallet(verified)
    finally:
        store.close()
    sidecar.chmod(0o600)
    service = ResearchPositions(
        registry=registry, person_id="frank", wallet=wallet, roster=roster,
        bundle=bundle, sidecar=sidecar, max_age_seconds=300)
    view = service.positions()
    summary.update({
        "status": "VERIFIED_MANUAL_RESEARCH_SESSION", "sidecar_created": True,
        "sidecar": str(sidecar), "capture_sha256": verified["capture_sha256"],
        "readiness": view["readiness"], "capture_age_seconds": view["capture_age_seconds"],
        "slot_min": view["slot_min"], "slot_max": view["slot_max"],
        "same_slot_atomic": False, "target_mint_count": view["target_mint_count"],
        "state_counts": view["state_counts"],
        "whole_wallet_observed_mints": reconciliation["summary"]["whole_wallet_observed_unique_mints"],
        "scope": "FROZEN_32_TARGETS_NOT_ARBITRARY_CA_QUERY",
    })
    return summary, service


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true",
                        help="authorize two HTTPS reads and one new private research session")
    parser.add_argument("--serve", action="store_true",
                        help="manually serve the new session on loopback; Ctrl-C stops it")
    parser.add_argument("--port", type=int, default=18766)
    args = parser.parse_args(argv)
    if args.serve and not args.execute:
        parser.error("--serve requires --execute")
    if not 1 <= args.port <= 65535:
        parser.error("port must be 1..65535")
    if not args.execute:
        print(json.dumps({
            "status": "PLAN_ONLY", "network_invoked": False,
            "sidecar_created": False, "session_root": str(SESSION_ROOT),
            "rpc_query_limit": 2, "source_ttl_seconds": 300,
            "writes_production_sqlite": False,
        }, sort_keys=True))
        return 0
    # Reserve the requested port BEFORE RPC or SQLite writes. Never replace
    # another listener; acquisition failure closes this unstarted server.
    server = ThreadingHTTPServer(("127.0.0.1", args.port), make_handler(None)) if args.serve else None
    try:
        summary, service = refresh_session(
            session_root=SESSION_ROOT,
            read_raw=_wire_rpc(os.environ.get("FRANK_RESEARCH_SOLANA_RPC_URL",
                                             "https://api.mainnet-beta.solana.com")))
        print(json.dumps(summary, sort_keys=True), flush=True)
        if service is None:
            return 2
        if server is not None:
            server.RequestHandlerClass = make_handler(service)
            print(json.dumps({"status": "LOCAL_RESEARCH_HTTP_READY",
                              "url": f"http://127.0.0.1:{server.server_port}/research/positions",
                              "automatic_rpc": False}, sort_keys=True), flush=True)
            server.serve_forever()
    finally:
        if server is not None:
            server.server_close()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("F02_MANUAL_RESEARCH_LISTENER_STOPPED")
    except (ValueError, OSError, RuntimeError, KeyError, TypeError, sqlite3.Error):
        print("F02_MANUAL_REFRESH_UNAVAILABLE", file=sys.stderr)
        raise SystemExit(1)
