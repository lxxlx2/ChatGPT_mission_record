"""F02-R3: independently recheck one previously authorized private Mac session.

NO RPC, NO DB WRITES, NO SERVER. Only aggregate, redacted output. A complete
verified original owner wire snapshot is rechecked against a read-only Sidecar
and the immutable 2026-10-11 frozen 32 Mint roster. Does not certify current
holdings or profit, and is not a generalized CA query.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import sys

from mission_agent.mission_control.person_registry import PersonRegistry
from mission_agent.mission_control.wallet_full_rpc_evidence import (
    _assert_directory, replay_owner_full_receipts,
)
from scripts.frank_f02_manual_refresh import SESSION_ROOT
from scripts.frank_f02_readonly_positions_api import ResearchPositions
from scripts.frank_reconcile_frozen32_offline import (
    REGISTRY, ROSTER, load_frozen_roster, reconcile,
)

SHA_256 = re.compile(r"[0-9a-f]{64}\Z")


def find_session(session_root: Path, expected_sha: str) -> Path:
    """Resolve unique *already existing* private manual session by source SHA."""
    if not SHA_256.fullmatch(expected_sha):
        raise ValueError("F02_R3_CAPTURE_SHA_INVALID")
    root = _assert_directory(session_root)
    if not root.is_dir():
        raise ValueError("F02_R3_SESSION_ROOT_MISSING")
    matches = []
    for session in root.iterdir():
        if (not session.name.startswith("session-") or session.is_symlink()
                or not session.is_dir()):
            continue
        manifest = session / "wire" / "manifest.json"
        if manifest.is_symlink() or not manifest.is_file():
            continue
        doc = json.loads(manifest.read_text(encoding="utf-8"))
        if doc.get("capture_sha256") == expected_sha:
            matches.append(session)
    if len(matches) != 1:
        raise ValueError("F02_R3_EXPECTED_UNIQUE_SESSION_NOT_FOUND")
    return _assert_directory(matches[0])


def attest(session: Path, expected_sha: str, *,
           registry: Path = REGISTRY, roster: Path = ROSTER,
           now_utc: datetime | None = None) -> dict:
    """Pure offline, read-only evidence corroboration; no private rows emitted."""
    if not SHA_256.fullmatch(expected_sha):
        raise ValueError("F02_R3_CAPTURE_SHA_INVALID")
    session = _assert_directory(session)
    if not session.name.startswith("session-"):
        raise ValueError("F02_R3_MANUAL_SESSION_REQUIRED")
    sidecar = session / "positions.sqlite"
    if not sidecar.is_file() or sidecar.is_symlink():
        raise ValueError("F02_R3_RESEARCH_SIDECAR_REQUIRED")
    before = hashlib.sha256(sidecar.read_bytes()).hexdigest()
    binding = [w for w in PersonRegistry.from_file(registry).wallets_for("frank")
               if w.chain == "solana"]
    if len(binding) != 1:
        raise ValueError("F02_R3_SINGLE_RESEARCH_WALLET_REQUIRED")
    wallet = binding[0].address
    frozen = load_frozen_roster(roster, wallet)
    verified = replay_owner_full_receipts(session / "wire", expected_wallet=wallet)
    if verified["capture_sha256"] != expected_sha:
        raise ValueError("F02_R3_WIRE_SHA_MISMATCH")
    exact = reconcile(verified, frozen)
    checkpoint = datetime.fromisoformat(verified["observed_at_utc"].replace(
        "Z", "+00:00")) + timedelta(seconds=1)
    service = ResearchPositions(
        registry=registry, person_id="frank", wallet=wallet, roster=roster,
        bundle=session / "wire", sidecar=sidecar, max_age_seconds=300,
    )
    archival = service.positions(as_of_utc=checkpoint)
    if (archival["readiness"] != "FRESH_VERIFIED_ARCHIVED_OBSERVATION"
            or archival["verified_full_wire_capture_sha256"] != expected_sha
            or archival["latest_capture_sha256"] != expected_sha
            or archival["target_mint_count"] != 32
            or len(archival["mints"]) != 32):
        raise ValueError("F02_R3_ARCHIVAL_SOURCE_INCONSISTENT")
    for expected, actual in zip(exact["mints"], archival["mints"]):
        if (actual["mint"] != expected["mint"]
                or actual["state"] != expected["current_status"]
                or actual["observed_raw_amount"] != expected["observed_raw_amount"]
                or actual["token_account_count"] != expected["observed_token_account_count"]
                or len(actual["token_accounts"]) != expected["observed_token_account_count"]):
            raise ValueError("F02_R3_TOKEN_ACCOUNT_OR_QUANTITY_MISMATCH")
        expected_qty = expected["observed_quantity"]
        actual_qty = actual["observed_quantity"]
        if ((expected_qty is None) != (actual_qty is None)
                or (expected_qty is not None and
                    Decimal(str(expected_qty)) != Decimal(str(actual_qty)))):
            raise ValueError("F02_R3_DECIMAL_QUANTITY_MISMATCH")
        # Compare every token-account identity/Program/state/amount, not just
        # Mint aggregates; do not print those identities to public stdout.
        from_wire = {(x["pubkey"], x["program_id"], str(x["raw_amount"]),
                      x["decimals"], x["state"]) for x in expected["token_accounts"]}
        from_store = {
            (x["token_account"], x["program_id"], str(x["raw_amount"]),
             x["decimals"], x["state"]) for x in actual["token_accounts"]
        }
        if from_wire != from_store:
            raise ValueError("F02_R3_TOKEN_ACCOUNT_WIRE_SIDECAR_CONFLICT")
    now = now_utc or datetime.now(timezone.utc)
    current = service.positions(as_of_utc=now)
    if current["readiness"] != "FRESH_VERIFIED_ARCHIVED_OBSERVATION":
        if (current["state_counts"] != {"SOURCE_UNAVAILABLE": 32}
                or any(x["observed_raw_amount"] is not None
                       or x["observed_quantity"] is not None
                       or x["token_account_count"] is not None
                       for x in current["mints"])):
            raise ValueError("F02_R3_STALE_OLD_QUANTITY_EXPOSED")
    if hashlib.sha256(sidecar.read_bytes()).hexdigest() != before:
        raise ValueError("F02_R3_READONLY_SIDECAR_CHANGED")
    summary = exact["summary"]
    return {
        "status": "F02_R3_PRIVATE_ORIGINAL_WIRE_READONLY_REPLAY_PASS",
        "code_scope": "ONE_PREVIOUSLY_AUTHORIZED_MANUAL_SESSION",
        "capture_sha256": expected_sha,
        "observed_at_utc": exact["observed_at_utc"],
        "slot_min": exact["slot_min"], "slot_max": exact["slot_max"],
        "same_slot_atomic": False,
        "whole_wallet_observed_token_accounts": summary["whole_wallet_observed_token_accounts"],
        "whole_wallet_observed_unique_mints": summary["whole_wallet_observed_unique_mints"],
        "frozen_targets": summary["frozen_target_mints"],
        "frozen_positive": summary["targets_with_positive_balance"],
        "frozen_zero": summary["targets_with_zero_open_account"],
        "frozen_no_open_account": summary["targets_with_no_open_account_observed"],
        "frozen_accounts_total": summary["target_open_token_accounts"],
        "frozen_multi_account_mints": summary["targets_with_multiple_open_accounts"],
        "frozen_max_accounts_per_mint": max(
            x["observed_token_account_count"] for x in exact["mints"]),
        "archived_all32_mint_and_individual_accounts_compared": True,
        "as_of_now_readiness": current["readiness"],
        "as_of_now_capture_age_seconds": current["capture_age_seconds"],
        "sidecar_bytes_unchanged": True, "network_invoked": False,
        "writes_production_sqlite": False, "signals_allowed": False,
        "verified_profit_or_sale": False, "whole_wallet_ui_claimed": False,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture-sha256", required=True)
    parser.add_argument("--session-root", type=Path, default=SESSION_ROOT)
    args = parser.parse_args(argv)
    try:
        session = find_session(args.session_root, args.capture_sha256)
        result = attest(session, args.capture_sha256)
    except (ValueError, OSError, KeyError, TypeError, json.JSONDecodeError,
            ArithmeticError):
        print("F02_R3_PRIVATE_SOURCE_ATTESTATION_FAILED", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
