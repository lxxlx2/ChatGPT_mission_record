"""A05-R2 read-only offline reconciliation of 2026-10-11 frozen 32 Frank Mints.

Requires a fully verified dual-program A05-R1 original RPC bundle. Does not
fetch RPC, inspect production SQLite, infer buys/sells/PnL, or import Sidecar.
The historical target roster is pinned by its actual Git blob identity.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from mission_agent.mission_control.person_registry import PersonRegistry
from mission_agent.mission_control.wallet_full_rpc_evidence import (
    _assert_directory, _write_exclusive, replay_owner_full_receipts,
)

ROOT = Path(__file__).resolve().parents[1]
ROSTER = ROOT.parent / "meme/evidence/frank-v2-thirty-two-mint-finalized-2026-10-11.json"
REGISTRY = ROOT / "config/frank_local_registry.json"
ROSTER_GIT_BLOB = "c6f43e4a63ea9daa1c9b820b8faed8ccefcdb2d1"


def _git_blob(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode() +
                        b"\0" + raw).hexdigest()


def load_frozen_roster(path: Path, wallet: str) -> dict:
    raw = Path(path).read_bytes()
    if _git_blob(raw) != ROSTER_GIT_BLOB:
        raise ValueError("FROZEN_32_MINT_ROSTER_BLOB_MISMATCH")
    doc = json.loads(raw)
    records = doc.get("records")
    if (doc.get("wallet") != wallet or doc.get("network") != "solana-mainnet"
            or doc.get("commitment") != "finalized"
            or doc.get("query_scope") != "EXACT_32_MINTS_FROM_MAC_D0_LOCAL_TRADE_AND_MODEL_UNION"
            or not isinstance(records, list) or len(records) != 32
            or doc.get("summary") != {"checked": 32, "nonzero": 10, "zero": 22}
            or len({r.get("mint") for r in records if isinstance(r, dict)}) != 32):
        raise ValueError("FROZEN_32_MINT_ROSTER_INVALID")
    return doc


def reconcile(snapshot: dict, roster: dict) -> dict:
    """Project only verified present accounts; missing current account != sale."""
    if (snapshot.get("wallet") != roster.get("wallet")
            or snapshot.get("status") != "BOTH_PROGRAMS_OBSERVED_NON_ATOMIC"
            or snapshot.get("both_programs_observed") is not True
            or snapshot.get("same_slot_atomic") is not False
            or snapshot.get("missing") != []
            or not isinstance(snapshot.get("capture_sha256"), str)):
        raise ValueError("DUAL_PROGRAM_VERIFIED_SOURCE_REQUIRED")
    snapshot_mints = snapshot.get("mints")
    if not isinstance(snapshot_mints, list):
        raise ValueError("CURRENT_MINTS_INVALID")
    by_mint = {x["mint"]: x for x in snapshot_mints}
    if len(by_mint) != len(snapshot_mints):
        raise ValueError("DUPLICATE_CURRENT_MINT")
    if len(snapshot_mints) != snapshot.get("mint_count_observed"):
        raise ValueError("CURRENT_MINT_COUNT_MISMATCH")
    if sum(len(x["token_accounts"]) for x in snapshot_mints) != snapshot.get("account_count"):
        raise ValueError("CURRENT_TOKEN_ACCOUNT_COUNT_MISMATCH")
    per_mint = []
    for old in roster["records"]:
        mint = old["mint"]
        now = by_mint.get(mint)
        accounts = now["token_accounts"] if now else []
        raw = int(now["raw_amount_observed_sum"]) if now else None
        quantity = now["quantity_observed_sum"] if now else None
        status = ("NO_OPEN_ACCOUNT_OBSERVED" if now is None else
                  "OPEN_ACCOUNT_NONZERO" if raw > 0 else "OPEN_ACCOUNT_ZERO")
        old_raw = int(old["raw_amount"])
        decimals_match = bool(now is not None and now["decimals"] == old["decimals"])
        per_mint.append({
            "mint": mint, "current_status": status,
            "historical_20261011": {
                "raw_amount": old["raw_amount"], "decimals": old["decimals"],
                "slot": old["slot"], "balance_class": old["balance_class"],
            },
            "observed_raw_amount": str(raw) if raw is not None else None,
            "observed_quantity": quantity,
            "observed_decimals": now["decimals"] if now else None,
            "observed_token_account_count": len(accounts),
            "token_accounts": [{
                "pubkey": a["token_account"], "program_id": a["program_id"],
                "raw_amount": a["raw_amount"], "decimals": a["decimals"],
                "state": a["state"], "observed_slot": a["slot"],
            } for a in accounts],
            "historical_to_new_raw_delta": str(raw - old_raw)
            if decimals_match else None,
            "comparison_note": ("DIFFERENT_FINALIZED_TIMES_NOT_ATOMIC_OR_TRADE_PROOF"
                                if decimals_match else
                                "NO_OPEN_ACCOUNT_OR_DECIMALS_NOT_COMPARABLE"),
            "realized_pnl_usd": None, "unrealized_pnl_usd": None,
        })
    summary = {
        "frozen_target_mints": 32,
        "historical_sample_20261011_nonzero": 10,
        "historical_sample_20261011_zero": 22,
        "whole_wallet_observed_token_accounts": snapshot["account_count"],
        "whole_wallet_observed_unique_mints": snapshot["mint_count_observed"],
        "targets_with_open_account": sum(
            x["current_status"] != "NO_OPEN_ACCOUNT_OBSERVED" for x in per_mint),
        "targets_with_positive_balance": sum(
            x["current_status"] == "OPEN_ACCOUNT_NONZERO" for x in per_mint),
        "targets_with_zero_open_account": sum(
            x["current_status"] == "OPEN_ACCOUNT_ZERO" for x in per_mint),
        "targets_with_no_open_account_observed": sum(
            x["current_status"] == "NO_OPEN_ACCOUNT_OBSERVED" for x in per_mint),
        "target_open_token_accounts": sum(
            x["observed_token_account_count"] for x in per_mint),
        "targets_with_multiple_open_accounts": sum(
            x["observed_token_account_count"] > 1 for x in per_mint),
    }
    if (summary["targets_with_open_account"] +
            summary["targets_with_no_open_account_observed"] != 32):
        raise ValueError("TARGET_RECONCILIATION_INCONSISTENT")
    return {
        "schema_version": 1,
        "kind": "FRANK_FROZEN32_OFFLINE_OWNER_RECONCILIATION_RESEARCH",
        "wallet": roster["wallet"], "source": "VERIFIED_FULL_DUAL_PROGRAM_WIRE_REPLAY",
        "full_rpc_capture_sha256": snapshot["capture_sha256"],
        "observed_at_utc": snapshot["observed_at_utc"],
        "slot_min": snapshot["slot_min"], "slot_max": snapshot["slot_max"],
        "both_programs_observed_non_atomic": True,
        "historical_roster_git_blob": ROSTER_GIT_BLOB,
        "historical_roster_date": roster["date_bangkok"],
        "historical_scope": roster["query_scope"],
        "history_complete": False,
        "current_32_mint_account_observation": "COMPLETE_TWO_PROGRAM_OWNER_ENUMERATION_NON_ATOMIC",
        "wallet_ownership_person_verified": False,
        "market_buy_sell_inferred": False,
        "verified_cost_or_pnl": False,
        "summary": summary, "mints": per_mint,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="A05-R2 offline verified RPC bundle vs frozen historical 32 Mint targets")
    parser.add_argument("--person-id", default="frank")
    parser.add_argument("--bundle", required=True, type=Path)
    parser.add_argument("--roster", type=Path, default=ROSTER)
    parser.add_argument("--registry", type=Path, default=REGISTRY)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)

    registry = PersonRegistry.from_file(args.registry)
    wallets = [w for w in registry.wallets_for(args.person_id)
               if w.chain == "solana"]
    if len(wallets) != 1:
        raise ValueError("ONE_REGISTERED_SOLANA_RESEARCH_WALLET_REQUIRED")
    wallet = wallets[0].address
    roster = load_frozen_roster(args.roster, wallet)
    capture = replay_owner_full_receipts(args.bundle, expected_wallet=wallet)
    document = reconcile(capture, roster)
    if args.output:
        output = args.output.expanduser()
        if output.is_symlink():
            raise ValueError("RESEARCH_REPORT_SYMLINK_FORBIDDEN")
        parent = _assert_directory(output.parent)
        parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        _write_exclusive(parent / output.name, json.dumps(
            document, sort_keys=True, ensure_ascii=False, indent=2
        ).encode("utf-8"))
    print(json.dumps({
        "status": "FROZEN32_OFFLINE_ACCOUNT_RECONCILIATION_COMPLETED",
        "wallet": wallet,
        "source_capture_sha256": document["full_rpc_capture_sha256"],
        "roster_git_blob": ROSTER_GIT_BLOB,
        "observed_at_utc": document["observed_at_utc"],
        "slot_min": document["slot_min"], "slot_max": document["slot_max"],
        "summary": document["summary"], "report_path": str(args.output) if args.output else None,
        "history_complete": False, "pnl_verified": False,
        "writes_production_sqlite": False, "network_invoked": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "A05_R2_SOURCE_OR_ROSTER_NOT_VERIFIED",
                          "error_type": type(exc).__name__}), file=__import__("sys").stderr)
        raise SystemExit(1)
