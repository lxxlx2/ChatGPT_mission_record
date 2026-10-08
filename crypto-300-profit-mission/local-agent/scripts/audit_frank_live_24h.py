#!/usr/bin/env python3
"""Read-only Solana RPC vs local Frank signature coverage audit (24h).

Does not send mail, write SQLite, create subscriptions, or change live policy.
Only full traversal through the requested cutoff yields COMPLETE coverage.
Keep RPC URLs, tokens and response errors out of the printed report.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import time
import urllib.request
from pathlib import Path

WALLET = "498g1rVnFcnjBjpfw1xyqA1WvgQXUU8RWuELjxkjAayQ"
PAGE_SIZE = 1000
MAX_PAGES = 20


def rpc_signatures(endpoint: str, cutoff: int) -> tuple[set[str], bool, int]:
    found: set[str] = set()
    before = None
    for page in range(1, MAX_PAGES + 1):
        options = {"limit": PAGE_SIZE, "commitment": "finalized"}
        if before:
            options["before"] = before
        data = {
            "jsonrpc": "2.0", "id": page, "method": "getSignaturesForAddress",
            "params": [WALLET, options],
        }
        request = urllib.request.Request(
            endpoint, data=json.dumps(data).encode("utf-8"),
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=20) as stream:
            response = json.load(stream)
        if response.get("error") or not isinstance(response.get("result"), list):
            raise ValueError("RPC_REJECTED_REQUEST")
        results = response["result"]
        if not results:
            return found, True, page
        oldest = None
        for item in results:
            sig = item.get("signature")
            stamp = item.get("blockTime")
            if not isinstance(sig, str) or stamp is None:
                raise ValueError("RPC_BLOCK_TIME_MISSING")
            stamp = int(stamp)
            oldest = stamp if oldest is None else min(oldest, stamp)
            if stamp >= cutoff:
                found.add(sig)
        if oldest is not None and oldest < cutoff:
            return found, True, page
        if len(results) < PAGE_SIZE:
            return found, True, page
        next_before = results[-1].get("signature")
        if not next_before or next_before == before:
            raise ValueError("RPC_CURSOR_STALLED")
        before = next_before
    return found, False, MAX_PAGES


def local_signatures(database: Path, cutoff: int) -> set[str]:
    uri = database.resolve().as_uri() + "?mode=ro"
    db = sqlite3.connect(uri, uri=True)
    try:
        db.execute("PRAGMA query_only=ON")
        return {
            row[0] for row in db.execute(
                "SELECT signature FROM signatures WHERE person_id='frank' AND block_time>=?",
                (cutoff,),
            )
        }
    finally:
        db.close()


def compare(chain: set[str], local: set[str]) -> dict:
    missing = sorted(chain - local)
    extra = sorted(local - chain)
    return {
        "chain_signatures": len(chain),
        "locally_indexed_signatures": len(local),
        "matched": len(chain & local),
        "missing_from_local": len(missing),
        "missing_signatures_first_10": missing[:10],
        "local_not_in_rpc_page": len(extra),
        "local_not_in_rpc_first_10": extra[:10],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, required=True)
    parser.add_argument("--rpc-file", type=Path, required=True)
    parser.add_argument("--hours", type=int, default=24, choices=(24,))
    args = parser.parse_args()
    if not args.db.is_file() or not args.rpc_file.is_file():
        raise SystemExit("AUDIT_PRECHECK_FAILED")
    if args.rpc_file.stat().st_mode & 0o077:
        raise SystemExit("RPC_FILE_PERMISSIONS_UNSAFE")
    endpoints = [e.strip() for e in args.rpc_file.read_text().split(",") if e.strip()]
    if not endpoints or len(endpoints) > 10:
        raise SystemExit("RPC_ENDPOINT_CONFIG_INVALID")
    now = int(time.time())
    cutoff = now - args.hours * 3600
    local = local_signatures(args.db, cutoff)
    chain = None
    complete = False
    pages = 0
    # Prefer the current configured authenticated endpoint; fall back silently.
    for endpoint in endpoints:
        if not endpoint.startswith("https://"):
            continue
        try:
            chain, complete, pages = rpc_signatures(endpoint, cutoff)
            if complete:
                break
        except (OSError, ValueError, TimeoutError, KeyError, TypeError):
            continue
    if chain is None or not complete:
        print(json.dumps({
            "wallet": WALLET, "window_hours": args.hours,
            "status": "RPC_AUDIT_INCOMPLETE", "complete": False,
            "reason": "NO_ENDPOINT_RETURNED_COMPLETE_HISTORY",
        }, ensure_ascii=False, indent=2))
        return 2
    report = {
        "wallet": WALLET,
        "window_hours": args.hours,
        "cutoff_epoch": cutoff,
        "audit_at_epoch": now,
        "status": "PASS" if chain == local else "COVERAGE_MISMATCH",
        "complete": True,
        "rpc_pages": pages,
        **compare(chain, local),
        "interpretation": (
            "Complete RPC signature presence comparison for this wallet/time window; "
            "not a trade-classification or profitability audit."
        ),
        "production_writes": 0,
        "gmail_sent": 0,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if chain == local else 3


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        print("AUDIT_FAILED_NO_WRITES", file=sys.stderr)
        raise SystemExit(4)
