#!/usr/bin/env python3
"""Read-only, single-window Frank Solana economic-fill evidence audit.

Stage A only. Matches the root wallet's finalized RPC signature set to already
cached jsonParsed transactions. It does not claim complete Frank-person history,
discover closed ATAs, infer trade PnL, or affect production signals/Gmail.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path
import re
import sys

from mission_agent.meme.fomo_crosschain import (
    FOMO_COSIGNER, SOL_CASH_WALLET, USDC, solana_events,
)
from scripts.audit_frank_fomo_crosschain import (
    IncompleteWindow, RPC, SignatureCache,
    configured_solana_endpoints, solana_signatures,
)

WSOL = "So11111111111111111111111111111111111111112"
USDT = "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB"
QUOTES = frozenset((USDC, WSOL, USDT))
DEFAULT_END = 1791472854
BASE58_SIG = re.compile(r"[1-9A-HJ-NP-Za-km-z]{64,100}\Z")


class EvidenceError(ValueError):
    pass


def read_report(path: Path, wallet: str, start: int, end: int) -> tuple[int, str]:
    if (path.is_symlink() or not path.is_file()
            or path.stat().st_mode & 0o077
            or path.stat().st_size > 30_000_000):
        raise EvidenceError("SOURCE_REPORT_UNSAFE_OR_MISSING")
    raw = path.read_bytes()
    try:
        report = json.loads(raw)
    except (ValueError, UnicodeError):
        raise EvidenceError("SOURCE_REPORT_INVALID") from None
    if (not isinstance(report, dict)
            or report.get("cutoff_epoch") != start
            or report.get("audited_at_epoch") != end):
        raise EvidenceError("SOURCE_REPORT_WRONG_WINDOW")
    entries = [
        entry for entry in report.get("chains", [])
        if isinstance(entry, dict)
        and entry.get("chain") == "SOL"
        and entry.get("wallet") == wallet
    ]
    if (len(entries) != 1 or entries[0].get("status") != "COMPLETE"
            or type(entries[0].get("signatures_scanned")) is not int
            or entries[0]["signatures_scanned"] < 0):
        raise EvidenceError("SOURCE_ROOT_COVERAGE_UNVERIFIED")
    return entries[0]["signatures_scanned"], hashlib.sha256(raw).hexdigest()


def chain_signature_window(urls: list[str], wallet: str, start: int, end: int) -> list[dict]:
    for endpoint in urls:
        try:
            return solana_signatures(RPC(endpoint), wallet, start, end)
        except (IncompleteWindow, ValueError, OSError, TimeoutError):
            continue
    raise EvidenceError("ROOT_RPC_SIGNATURES_UNAVAILABLE")


def owned_deltas(tx: dict, wallet: str) -> list[dict]:
    meta = tx.get("meta")
    if not isinstance(meta, dict) or meta.get("err") is not None:
        if isinstance(meta, dict) and meta.get("err") is not None:
            return []
        raise EvidenceError("TRANSACTION_METADATA_MISSING")
    pre = meta.get("preTokenBalances")
    post = meta.get("postTokenBalances")
    if not isinstance(pre, list) or not isinstance(post, list):
        raise EvidenceError("TOKEN_BALANCE_METADATA_MISSING")
    accounts = defaultdict(dict)
    for label, rows in (("pre", pre), ("post", post)):
        for row in rows:
            if not isinstance(row, dict) or type(row.get("accountIndex")) is not int:
                raise EvidenceError("TOKEN_ACCOUNT_INDEX_MISSING")
            idx = row["accountIndex"]
            amount = row.get("uiTokenAmount") or {}
            if not isinstance(amount, dict):
                raise EvidenceError("TOKEN_AMOUNT_INVALID")
            mint, owner = row.get("mint"), row.get("owner")
            if not isinstance(mint, str) or not isinstance(owner, str):
                raise EvidenceError("TOKEN_IDENTITY_MISSING")
            try:
                raw = int(amount["amount"])
                decimals = int(amount["decimals"])
            except (KeyError, TypeError, ValueError):
                raise EvidenceError("TOKEN_AMOUNT_INVALID") from None
            if raw < 0 or not 0 <= decimals <= 18:
                raise EvidenceError("TOKEN_AMOUNT_INVALID")
            item = accounts[idx]
            identity = (mint, owner, decimals)
            if "identity" in item and item["identity"] != identity:
                raise EvidenceError("TOKEN_ACCOUNT_IDENTITY_CONFLICT")
            item["identity"] = identity
            if label in item:
                raise EvidenceError("DUPLICATE_TOKEN_BALANCE_ROW")
            item[label] = raw
    per_mint = {}
    for item in accounts.values():
        mint, owner, decimals = item["identity"]
        if owner != wallet:
            continue
        delta = item.get("post", 0) - item.get("pre", 0)
        if mint in per_mint:
            if per_mint[mint]["decimals"] != decimals:
                raise EvidenceError("TOKEN_DECIMALS_CONFLICT")
            per_mint[mint]["raw"] += delta
        else:
            per_mint[mint] = {"raw": delta, "decimals": decimals}
    return [
        {"mint": mint, "raw": str(row["raw"]), "decimals": row["decimals"]}
        for mint, row in sorted(per_mint.items()) if row["raw"] != 0
    ]


def display_amount(raw: int, decimals: int) -> str:
    return format(Decimal(raw) / (Decimal(10) ** decimals), "f")


def inspect_tx(signature: str, tx: dict, wallet: str) -> dict:
    meta = tx.get("meta") or {}
    if not isinstance(meta, dict):
        raise EvidenceError("META_MISSING")
    keys = ((tx.get("transaction") or {}).get("message") or {}).get("accountKeys")
    if not isinstance(keys, list) or not all(
        isinstance(k, dict) and isinstance(k.get("pubkey"), str)
        for k in keys
    ):
        raise EvidenceError("JSON_PARSED_KEYS_REQUIRED")
    names = [k["pubkey"] for k in keys]
    if wallet not in names:
        raise EvidenceError("ROOT_NOT_IN_ACCOUNT_KEYS")
    signed = any(k["pubkey"] == wallet and k.get("signer") is True for k in keys)
    cosigned = any(k["pubkey"] == FOMO_COSIGNER and k.get("signer") is True for k in keys)
    evidence = solana_events(signature, tx, wallet) if meta.get("err") is None else []
    deltas = owned_deltas(tx, wallet)
    target = [x for x in deltas if x["mint"] not in QUOTES]
    quote = [x for x in deltas if x["mint"] in QUOTES]
    kinds = {x["kind"] for x in evidence}
    direction = None
    target_asset = None
    quote_asset = None
    if meta.get("err") is not None:
        category = "FAILED"
    elif "RELAY_PAY" in kinds:
        category = "RELAY_PAY"
    elif "RELAY_PAYOUT" in kinds:
        category = "RELAY_PAYOUT"
    elif "SWAP_CANDIDATE" in kinds and len(target) == 1 and len(quote) == 1:
        t, q = target[0], quote[0]
        if int(t["raw"]) * int(q["raw"]) < 0:
            category = "SWAP_CANDIDATE"
            direction = "BUY" if int(t["raw"]) > 0 else "SELL"
            target_asset = {
                "mint": t["mint"], "net_raw": t["raw"],
                "net_amount": display_amount(abs(int(t["raw"])), t["decimals"]),
            }
            quote_asset = {
                "mint": q["mint"], "net_raw": q["raw"],
                "net_amount": display_amount(abs(int(q["raw"])), q["decimals"]),
            }
        else:
            category = "UNRESOLVED_FLOW"
    elif any(int(t["raw"]) * int(q["raw"]) < 0 for t in target for q in quote):
        category = "OPPOSING_FLOW_UNVERIFIED"
    elif deltas:
        category = "TOKEN_MOVEMENT"
    else:
        category = "NO_NET_TOKEN_CHANGE"
    return {
        "signature": signature, "slot": tx.get("slot"), "block_time": tx.get("blockTime"),
        "category": category, "direction_candidate": direction,
        "wallet_signed": signed, "fomo_cosigned": cosigned,
        "target": target_asset, "quote": quote_asset,
        "owned_token_deltas": deltas,
        "solscan": "https://solscan.io/tx/" + signature,
        "trade_confirmed": False,
        "reason": ("CANDIDATE_REQUIRES_INSTRUCTION_LEVEL_REVIEW"
                   if category == "SWAP_CANDIDATE" else category),
    }


def audit(root_wallet: str, signatures: list[dict], source_count: int,
          cache: SignatureCache, start: int, end: int) -> dict:
    indexed = {}
    for row in signatures:
        sig, slot, stamp = row.get("signature"), row.get("slot"), row.get("blockTime")
        if (not isinstance(sig, str) or not BASE58_SIG.fullmatch(sig)
                or type(slot) is not int or type(stamp) is not int):
            raise EvidenceError("SIGNATURE_METADATA_INVALID")
        if not start <= stamp <= end or sig in indexed:
            raise EvidenceError("SIGNATURE_WINDOW_OR_DUPLICATE")
        indexed[sig] = row
    observations = []
    missing = []
    for signature, row in indexed.items():
        tx = cache.load(root_wallet, signature, row["slot"])
        if tx is None:
            missing.append(signature)
            continue
        try:
            observations.append(inspect_tx(signature, tx, root_wallet))
        except (EvidenceError, ValueError, TypeError, KeyError, IndexError):
            observations.append({
                "signature": signature, "category": "UNRESOLVED_PARSE",
                "trade_confirmed": False, "solscan": "https://solscan.io/tx/" + signature,
            })
    observations.sort(key=lambda r: (r.get("block_time") or 0, r["signature"]))
    mismatch = len(indexed) != source_count
    categories = dict(sorted(Counter(row["category"] for row in observations).items()))
    interesting = [
        row for row in observations
        if row["category"] in (
            "SWAP_CANDIDATE", "OPPOSING_FLOW_UNVERIFIED",
            "UNRESOLVED_FLOW", "UNRESOLVED_PARSE",
        )
    ]
    return {
        "status": ("ROOT_WINDOW_RECONCILED_OBSERVE_ONLY"
                   if not mismatch and not missing else "PARTIAL"),
        "person_attribution": "THIRD_PARTY_UNVERIFIED",
        "wallet": root_wallet, "start_epoch": start, "end_epoch": end,
        "source_report_signature_count": source_count,
        "current_rpc_signature_count": len(indexed),
        "cache_decoded_count": len(observations),
        "missing_cached_transactions": len(missing),
        "missing_cached_signature_sample": missing[:10],
        "categories": categories, "candidate_count": len(interesting),
        "candidate_trades": interesting,
        "all_root_transactions": observations,
        "warning": (
            "Root address signature completeness only. Does not cover "
            "historical closed token accounts, other person wallets or "
            "independent indexed DFlow fills. No candidate is a confirmed BUY/SELL."
        ),
        "production_writes": 0, "emails_sent": 0, "signals_changed": False,
    }


def save_report(report: dict, directory: Path) -> Path:
    directory = directory.expanduser()
    if "FrankMeme" in str(directory) or "mission-control" in str(directory):
        raise EvidenceError("OUTPUT_MUST_BE_OUTSIDE_PRODUCTION")
    if directory.is_symlink():
        raise EvidenceError("OUTPUT_DIRECTORY_SYMLINK")
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    if not directory.is_dir() or directory.stat().st_mode & 0o077:
        raise EvidenceError("OUTPUT_DIRECTORY_PERMISSIONS_UNSAFE")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")
    path = directory / ("frank-sol-root-" + stamp + ".json")
    payload = json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    fd = os.open(path, flags, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        stream.write(payload)
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Frank Solana root historical read-only audit")
    parser.add_argument("--end-epoch", type=int, default=DEFAULT_END)
    parser.add_argument("--source-report", type=Path, default=(
        Path.home() / "Documents/ChatGPT/frank-fomo-fixed-20261009-054846.json"))
    parser.add_argument("--rpc-file", type=Path, default=(
        Path.home() / "Library/Application Support/FrankMeme/solana_rpc_urls"))
    parser.add_argument("--cache-dir", type=Path, default=(
        Path.home() / "Documents/ChatGPT/frank-fomo-rpc-cache"))
    parser.add_argument("--output-dir", type=Path, default=(
        Path.home() / "Documents/ChatGPT/frank-fomo-research"))
    args = parser.parse_args()
    start = args.end_epoch - 86400
    try:
        if args.end_epoch > int(datetime.now(timezone.utc).timestamp()):
            raise EvidenceError("FUTURE_WINDOW")
        source_count, source_sha = read_report(
            args.source_report, SOL_CASH_WALLET, start, args.end_epoch)
        endpoints = configured_solana_endpoints(args.rpc_file)
        signatures = chain_signature_window(endpoints, SOL_CASH_WALLET, start, args.end_epoch)
        if args.cache_dir.is_symlink() or not args.cache_dir.is_dir():
            raise EvidenceError("CACHE_DIRECTORY_MISSING_OR_UNSAFE")
        report = audit(
            SOL_CASH_WALLET, signatures, source_count,
            SignatureCache(args.cache_dir), start, args.end_epoch)
        report["source_report_sha256"] = source_sha
        path = save_report(report, args.output_dir)
        view = {
            "status": report["status"], "wallet": SOL_CASH_WALLET,
            "rpc_signatures": report["current_rpc_signature_count"],
            "source_signatures": source_count,
            "cached_decoded": report["cache_decoded_count"],
            "missing_cache": report["missing_cached_transactions"],
            "categories": report["categories"],
            "trades_for_review": report["candidate_trades"][:25],
            "full_report": str(path), "signal_changes": False,
            "production_writes": 0, "emails_sent": 0,
        }
        print(json.dumps(view, ensure_ascii=False, indent=2))
        return 0 if report["status"] == "ROOT_WINDOW_RECONCILED_OBSERVE_ONLY" else 3
    except (EvidenceError, IncompleteWindow, OSError, ValueError) as exc:
        error = str(exc) if isinstance(exc, EvidenceError) else (
            str(exc) if isinstance(exc, IncompleteWindow)
            and re.fullmatch(r"[A-Za-z0-9_]{3,80}", str(exc))
            else "SOURCE_OR_RPC_UNAVAILABLE")
        print(json.dumps({"status": "AUDIT_BLOCKED", "reason": error,
                          "production_writes": 0, "emails_sent": 0}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
