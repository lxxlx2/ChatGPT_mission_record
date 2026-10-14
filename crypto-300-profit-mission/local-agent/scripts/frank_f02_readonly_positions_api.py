"""F02-R1 manually launched loopback-only A05 research positions HTTP API.

This does not touch the production Dashboard HTTP server, Frank V1 or Gmail.
Source is an explicitly verified full-wire RPC bundle and a separate read-only
research ACCOUNT_CAPTURE sidecar. No RPC, scheduler, database writes or trades.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from decimal import Decimal
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import sqlite3
import sys
from urllib.parse import parse_qs, urlsplit

from mission_agent.mission_control.person_registry import PersonRegistry
from mission_agent.mission_control.wallet_evidence_store import WalletEvidenceStore
from mission_agent.mission_control.wallet_full_rpc_evidence import replay_owner_full_receipts
from mission_agent.mission_control.wallet_inventory_snapshot import latest_inventory, _parse_time
from scripts.frank_reconcile_frozen32_offline import (
    ROSTER, REGISTRY, ROSTER_GIT_BLOB, load_frozen_roster,
)


def _quantity(raw: str, decimals: int) -> str:
    if (not isinstance(raw, str) or not raw.isdecimal() or
            type(decimals) is not int or not 0 <= decimals <= 255):
        raise ValueError("F02_INVALID_RAW_QUANTITY")
    return format(Decimal(raw).scaleb(-decimals), "f")



def _latest_actual_attempt(store, *, wallet: str, as_of_utc: datetime) -> dict | None:
    """Latest research capture attempt by UTC time, independently of chain slot.

    The shared historical selector chooses the highest chain slot; a later
    failed attempt may have a lower residual slot. This F02-only availability
    check follows the actual attempt chronology without changing backfills.
    latest_inventory verifies every archive hash and source wallet first.
    """
    as_of = as_of_utc.astimezone(timezone.utc)
    latest = None
    latest_at = None
    for capture in store.iter_wallet_captures(wallet):
        observed_at = _parse_time(capture.get("observed_at_utc"))
        if observed_at > as_of:
            continue
        if (latest_at is None or observed_at > latest_at or
                (observed_at == latest_at and
                 capture.get("status") == "PARTIAL_SOURCE" and
                 latest.get("status") != "PARTIAL_SOURCE")):
            latest_at, latest = observed_at, capture
    return latest


class ResearchPositions:
    """One explicitly bound person/wallet, pinned origin and frozen target list."""

    def __init__(self, *, registry: Path, person_id: str, wallet: str | None,
                 roster: Path, bundle: Path, sidecar: Path, max_age_seconds: int):
        if type(max_age_seconds) is not int or not 1 <= max_age_seconds <= 86400:
            raise ValueError("F02_MAX_AGE_INVALID")
        bindings = [w for w in PersonRegistry.from_file(registry).wallets_for(person_id)
                    if w.chain == "solana" and (wallet is None or w.address == wallet)]
        if len(bindings) != 1:
            raise ValueError("F02_EXACTLY_ONE_RESEARCH_WALLET_REQUIRED")
        self.binding = bindings[0]
        self.person_id = person_id
        self.roster = load_frozen_roster(roster, self.binding.address)
        self.mints = [x["mint"] for x in self.roster["records"]]
        # Validate the privately stored whole-wallet *original* wire source once
        # before this listener can serve any quantity from a normalized sidecar.
        verified = replay_owner_full_receipts(bundle, expected_wallet=self.binding.address)
        if (verified.get("status") != "BOTH_PROGRAMS_OBSERVED_NON_ATOMIC" or
                verified.get("both_programs_observed") is not True or
                verified.get("missing") != []):
            raise ValueError("F02_FULL_WIRE_SOURCE_REQUIRED")
        self.verified_capture_sha256 = verified["capture_sha256"]
        self.sidecar = Path(sidecar).expanduser()
        self.max_age_seconds = max_age_seconds
        # Missing sidecars fail startup and cannot be silently created.
        store = WalletEvidenceStore(self.sidecar, read_only=True)
        store.close()

    def positions(self, *, as_of_utc: datetime | None = None) -> dict:
        instant = as_of_utc if as_of_utc is not None else datetime.now(timezone.utc)
        store = WalletEvidenceStore(self.sidecar, read_only=True)
        try:
            result = latest_inventory(
                store, wallet=self.binding.address, mints=self.mints,
                as_of_utc=instant, max_age_seconds=self.max_age_seconds)
            actual_attempt = _latest_actual_attempt(
                store, wallet=self.binding.address, as_of_utc=instant)
        finally:
            store.close()
        attempt_status = (actual_attempt.get("status") if actual_attempt is not None
                          else result["source_observation_status"])
        selected_sha = result["selected_capture_sha256"]
        selected_at = (_parse_time(result["capture_observed_at_utc"])
                       if result["capture_observed_at_utc"] else None)
        newer_attempt = (actual_attempt is not None and
                         (selected_at is None or
                          _parse_time(actual_attempt["observed_at_utc"]) > selected_at))
        selected_attempt = (actual_attempt is not None and
                            actual_attempt["capture_sha256"] == selected_sha)
        if result["source_attempt_failed_no_slot"] or (
                attempt_status == "PARTIAL_SOURCE" and
                (newer_attempt or selected_attempt)):
            readiness = "LATEST_CAPTURE_ATTEMPT_FAILED"
        elif newer_attempt:
            readiness = "LATEST_SOURCE_NOT_WIRE_VERIFIED"
        elif not result["both_programs_observed"]:
            readiness = "INCOMPLETE_OR_NO_LATEST_CAPTURE"
        elif not result["capture_fresh"]:
            readiness = "STALE_ARCHIVED_SOURCE"
        elif result["selected_capture_sha256"] != self.verified_capture_sha256:
            # A newer valid-looking DB document cannot be promoted to
            # verified provenance without a matching original-wire bundle.
            readiness = "LATEST_SOURCE_NOT_WIRE_VERIFIED"
        else:
            readiness = "FRESH_VERIFIED_ARCHIVED_OBSERVATION"
        usable = readiness == "FRESH_VERIFIED_ARCHIVED_OBSERVATION"
        entries = []
        for row in result["mints"]:
            observed = (usable and row["status"] ==
                        "OBSERVED_IN_DUAL_PROGRAM_SCAN_NON_ATOMIC")
            raw = row["observed_raw_amount"] if observed else None
            dec = row["decimals"] if observed else None
            if raw is not None:
                status = "OPEN_ACCOUNT_NONZERO" if int(raw) > 0 else "OPEN_ACCOUNT_ZERO"
            elif usable:
                status = "NO_OPEN_ACCOUNT_OBSERVED"
            else:
                status = "SOURCE_UNAVAILABLE"
            entries.append({
                "mint": row["mint"], "state": status,
                "observed_raw_amount": raw,
                "observed_decimals": dec,
                "observed_quantity": _quantity(raw, dec) if raw is not None else None,
                "token_accounts": row["token_accounts"] if observed else [],
                "token_account_count": len(row["token_accounts"]) if observed else None,
                "historical_sale_confirmed": False,
                "value_usd": None, "cost_basis_usd": None,
                "realized_pnl_usd": None, "unrealized_pnl_usd": None,
            })
        counts = {}
        for item in entries:
            counts[item["state"]] = counts.get(item["state"], 0) + 1
        return {
            "schema_version": 1, "kind": "F02_RESEARCH_ARCHIVED_OWNER_POSITIONS",
            "person_id": self.person_id, "wallet_id": self.binding.wallet_id,
            "wallet": self.binding.address, "chain": "solana",
            "wallet_binding_role": self.binding.role,
            "wallet_binding_evidence_state": self.binding.evidence_state,
            "person_beneficial_ownership_verified": False,
            "signals_allowed": False, "trades_allowed": False,
            "as_of_utc": result["as_of_utc"],
            "readiness": readiness, "archive_is_live_portfolio": False,
            "archive_observation_usable": usable,
            "max_age_seconds": self.max_age_seconds,
            "capture_age_seconds": result["capture_age_seconds"],
            "capture_fresh": result["capture_fresh"],
            "capture_observed_at_utc": result["capture_observed_at_utc"],
            "latest_capture_sha256": result["selected_capture_sha256"],
            "verified_full_wire_capture_sha256": self.verified_capture_sha256,
            "source_observation_status": result["source_observation_status"],
            "source_attempt_failed_no_slot": result["source_attempt_failed_no_slot"],
            "latest_attempt_source_status": attempt_status,
            "latest_attempt_capture_sha256": (actual_attempt["capture_sha256"]
                if actual_attempt is not None else result["selected_capture_sha256"]),
            "latest_attempt_observed_at_utc": (actual_attempt["observed_at_utc"]
                if actual_attempt is not None else result["capture_observed_at_utc"]),
            "latest_attempt_slot_max": (actual_attempt["slot_max"]
                if actual_attempt is not None else result["slot_max"]),
            "latest_attempt_missing_program_ids": ([
                row["program_id"] for row in actual_attempt.get("missing", [])
            ] if actual_attempt is not None else []),
            "slot_min": result["slot_min"], "slot_max": result["slot_max"],
            "same_slot_atomic": False,
            "historical_roster_git_blob": ROSTER_GIT_BLOB,
            "target_mint_count": len(entries), "state_counts": counts,
            "mints": entries,
            "usd_portfolio_value": None, "verified_pnl_usd": None,
            "latest_source_not_automatically_recaptured": True,
        }


WEB_ROOT = Path(__file__).resolve().parent / "frank_f02_web"
WEB_ROUTES = {
    "/research/positions": ("positions.html", "text/html; charset=utf-8"),
    "/research/positions.js": ("positions.js", "text/javascript; charset=utf-8"),
    "/research/positions.css": ("positions.css", "text/css; charset=utf-8"),
}
WEB_CSP = ("default-src 'none'; script-src 'self'; style-src 'self'; "
           "connect-src 'self'; img-src 'none'; object-src 'none'; "
           "base-uri 'none'; form-action 'none'; frame-ancestors 'none'")


def make_handler(service: ResearchPositions):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def _json(self, status: int, result: dict):
            raw = json.dumps(result, ensure_ascii=False, sort_keys=True).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def _static(self, path: str):
            filename, mime = WEB_ROUTES[path]
            # Every path is a fixed literal mapping, never a user-provided
            # filesystem path. No CORS or private original RPC bytes exposed.
            raw = (WEB_ROOT / filename).read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(raw)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Security-Policy", WEB_CSP)
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Referrer-Policy", "no-referrer")
            self.end_headers()
            self.wfile.write(raw)

        def do_GET(self):
            host = self.headers.get("Host", "").lower().split(":", 1)[0]
            if host not in {"127.0.0.1", "localhost"}:
                self._json(403, {"status": "LOCALHOST_ONLY"})
                return
            parsed = urlsplit(self.path)
            if parsed.path in WEB_ROUTES:
                try:
                    self._static(parsed.path)
                except OSError:
                    self._json(503, {"status": "RESEARCH_VIEW_UNAVAILABLE"})
                return
            if parsed.path != "/api/research/positions":
                self._json(404, {"status": "NOT_FOUND"})
                return
            q = parse_qs(parsed.query, keep_blank_values=True)
            if (set(q) - {"person_id", "wallet"} or
                    any(len(v) != 1 for v in q.values()) or
                    q.get("person_id", [service.person_id]) != [service.person_id] or
                    q.get("wallet", [service.binding.address]) != [service.binding.address]):
                self._json(400, {"status": "BOUND_RESEARCH_IDENTITY_REQUIRED"})
                return
            try:
                self._json(200, service.positions())
            except (ValueError, OSError, KeyError, TypeError, json.JSONDecodeError, sqlite3.Error):
                self._json(503, {"status": "RESEARCH_SOURCE_UNAVAILABLE"})

    return Handler


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="F02 manual loopback research API, never production")
    parser.add_argument("--person-id", default="frank")
    parser.add_argument("--wallet")
    parser.add_argument("--registry", type=Path, default=REGISTRY)
    parser.add_argument("--roster", type=Path, default=ROSTER)
    parser.add_argument("--bundle", required=True, type=Path)
    parser.add_argument("--sidecar", required=True, type=Path)
    parser.add_argument("--max-age-seconds", type=int, default=300)
    parser.add_argument("--port", type=int, default=18765)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--probe-once", action="store_true")
    mode.add_argument("--serve", action="store_true")
    args = parser.parse_args(argv)
    if not args.serve and not args.probe_once:
        print(json.dumps({"status": "PLAN_ONLY", "network_invoked": False,
                          "sidecar_opened": False, "writes_production_sqlite": False,
                          "manual_listener_required": True}, sort_keys=True))
        return 0
    if type(args.port) is not int or not 1 <= args.port <= 65535:
        raise ValueError("F02_PORT_INVALID")
    service = ResearchPositions(
        registry=args.registry, person_id=args.person_id, wallet=args.wallet,
        roster=args.roster, bundle=args.bundle, sidecar=args.sidecar,
        max_age_seconds=args.max_age_seconds)
    if args.probe_once:
        print(json.dumps(service.positions(), ensure_ascii=False, sort_keys=True))
        return 0
    with ThreadingHTTPServer(("127.0.0.1", args.port), make_handler(service)) as server:
        print(json.dumps({"status": "LOCAL_RESEARCH_HTTP_READY",
                          "host": "127.0.0.1", "port": server.server_port,
                          "route": "/api/research/positions",
                          "view": "/research/positions",
                          "writes_production_sqlite": False}, sort_keys=True), flush=True)
        server.serve_forever()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, KeyError, TypeError, json.JSONDecodeError, sqlite3.Error):
        print("F02_RESEARCH_SOURCE_UNAVAILABLE", file=sys.stderr)
        raise SystemExit(1)
