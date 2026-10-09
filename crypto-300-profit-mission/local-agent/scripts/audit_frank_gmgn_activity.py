#!/usr/bin/env python3
"""Read-only Frank historical GMGN-vs-Mission fill inventory.

Uses the OFFICIAL gmgn-cli Portfolio Activity (API-key read auth only).
No wallet private key, no scraper, no signals, no producer DB writes, no mail.
Third-party rows are leads until compared with immutable onchain tx evidence.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import subprocess
import sys

ROOT_WALLET = "498g1rVnFcnjBjpfw1xyqA1WvgQXUU8RWuELjxkjAayQ"
START = 1791386454
END = 1791472854
SIG = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{64,100}$")
SIDES = {"buy": "BUY", "sell": "SELL"}
DEFAULT_DB = (Path.home() / "Documents/ChatGPT/"
              "crypto-monitor-frank-only-evidence-20261003/live-v1/forward.sqlite")
DEFAULT_OUTPUT = Path.home() / "Documents/ChatGPT/frank-fomo-research"


class IncompleteEvidence(Exception):
    pass


def epoch(value):
    if isinstance(value, bool):
        raise IncompleteEvidence("GMGN_INVALID_TIME")
    if isinstance(value, (int, float)):
        n = int(value)
        if 10**12 < n < 10**14:
            n //= 1000
        if not 1_000_000_000 < n < 4_000_000_000:
            raise IncompleteEvidence("GMGN_INVALID_TIME")
        return n
    if isinstance(value, str) and value:
        if value.isdigit():
            return epoch(int(value))
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                raise ValueError("timezone absent")
            return int(dt.timestamp())
        except ValueError:
            pass
    raise IncompleteEvidence("GMGN_INVALID_TIME")


def checked_rows(payload):
    if not isinstance(payload, dict):
        raise IncompleteEvidence("GMGN_RESPONSE_INVALID")
    if "code" in payload and payload["code"] not in (0, "0"):
        raise IncompleteEvidence("GMGN_API_REJECTED")
    body = payload.get("data", payload)
    if not isinstance(body, dict) or not isinstance(body.get("activities"), list):
        raise IncompleteEvidence("GMGN_SCHEMA_CHANGED")
    cursor = body.get("next")
    if cursor is not None and not isinstance(cursor, (str, int)):
        raise IncompleteEvidence("GMGN_CURSOR_INVALID")
    if len(body["activities"]) > 200:
        raise IncompleteEvidence("GMGN_PAGE_TOO_LARGE")
    return body["activities"], str(cursor) if cursor else None


def normalize(row):
    if not isinstance(row, dict):
        raise IncompleteEvidence("GMGN_ROW_INVALID")
    signature = row.get("tx_hash") or row.get("transaction_hash")
    if not isinstance(signature, str) or not SIG.fullmatch(signature):
        raise IncompleteEvidence("GMGN_SIGNATURE_MISSING")
    kind = str(row.get("event_type") or row.get("type") or "").lower()
    if kind not in SIDES:
        return {"signature": signature, "time": epoch(row.get("timestamp")),
                "type": kind, "side": None, "mint": None}
    token = row.get("token")
    mint = (token.get("address") or token.get("token_address")
            if isinstance(token, dict) else None)
    if not isinstance(mint, str) or not mint:
        raise IncompleteEvidence("GMGN_TRADE_MINT_MISSING")
    return {"signature": signature, "time": epoch(row.get("timestamp")),
            "type": kind, "side": SIDES[kind], "mint": mint}


def collect_gmgn(wallet, start, end, pages=40, cli_path=None, run=subprocess.run):
    binary = cli_path or shutil.which("gmgn-cli")
    if not binary:
        raise IncompleteEvidence("GMGN_CLI_NOT_INSTALLED")
    try:
        auth = run([binary, "config", "--check"], capture_output=True,
                   text=True, timeout=15, check=False)
    except (OSError, subprocess.TimeoutExpired):
        raise IncompleteEvidence("GMGN_AUTH_CHECK_UNAVAILABLE") from None
    if auth.returncode:
        raise IncompleteEvidence("GMGN_KEY_NOT_CONFIGURED_OR_INVALID")
    cursor = None
    cursors = set()
    seen = set()
    rows = []
    prev_time = None
    last_time = None
    for _ in range(pages):
        cmd = [binary, "portfolio", "activity", "--chain", "sol",
               "--wallet", wallet, "--limit", "100"]
        if cursor:
            cmd += ["--cursor", cursor]
        cmd += ["--raw"]
        try:
            result = run(cmd, capture_output=True, text=True, timeout=40, check=False)
        except (OSError, subprocess.TimeoutExpired):
            raise IncompleteEvidence("GMGN_REQUEST_UNAVAILABLE") from None
        if result.returncode or len(result.stdout) > 5_000_000:
            raise IncompleteEvidence("GMGN_REQUEST_FAILED") 
        try:
            page, next_cursor = checked_rows(json.loads(result.stdout))
        except (ValueError, UnicodeError):
            raise IncompleteEvidence("GMGN_NON_JSON_RESPONSE") from None
        if not page:
            if last_time is not None and last_time < start:
                break
            raise IncompleteEvidence("GMGN_HISTORY_EMPTY_OR_INCOMPLETE")
        for raw in page:
            event = normalize(raw)
            at = event["time"]
            if prev_time is not None and at > prev_time:
                raise IncompleteEvidence("GMGN_ACTIVITY_NOT_NEWEST_FIRST")
            prev_time = at
            last_time = at
            if start <= at <= end:
                key = (event["signature"], event["mint"], event["side"])
                if key not in seen:
                    seen.add(key)
                    rows.append(event)
        if last_time < start:
            break
        if not next_cursor:
            raise IncompleteEvidence("GMGN_HISTORY_ENDS_BEFORE_WINDOW_COVERED")
        if next_cursor in cursors:
            raise IncompleteEvidence("GMGN_CURSOR_LOOP")
        cursors.add(next_cursor)
        cursor = next_cursor
    else:
        raise IncompleteEvidence("GMGN_PAGE_BUDGET_EXCEEDED")
    if last_time is None or last_time >= start:
        raise IncompleteEvidence("GMGN_OLDEST_BOUNDARY_UNVERIFIED")
    return rows, len(cursors) + 1


def local_window(db_path, start, end):
    if not db_path.is_file():
        raise IncompleteEvidence("MISSION_DB_NOT_FOUND")
    database = sqlite3.connect(db_path.resolve().as_uri() + "?mode=ro", uri=True)
    database.row_factory = sqlite3.Row
    try:
        database.execute("PRAGMA query_only=ON")
        database.execute("BEGIN")
        signatures = {
            r["signature"]
            for r in database.execute(
                "SELECT signature FROM signatures WHERE person_id='frank' "
                "AND block_time>=? AND block_time<=?",
                (start, end),
            )
        }
        records = list(database.execute(
            """SELECT DISTINCT t.signature,t.mint,t.side,t.block_time
                 FROM trades t JOIN signatures s
                   ON s.wallet=t.wallet AND s.signature=t.signature
                WHERE s.person_id='frank'
                  AND t.block_time>=? AND t.block_time<=?""",
            (start, end),
        ))
        bounds = database.execute(
            "SELECT MIN(block_time),MAX(block_time),COUNT(*) FROM signatures WHERE person_id='frank'"
        ).fetchone()
        return {
            "signatures": signatures,
            "trades": [
                {"signature":r["signature"],"mint":r["mint"],"side":r["side"],
                 "time":r["block_time"]}
                for r in records
            ],
            "ledger_first_time":bounds[0],
            "ledger_last_time":bounds[1],
            "ledger_signature_count":bounds[2],
        }
    except sqlite3.DatabaseError:
        raise IncompleteEvidence("MISSION_DB_SCHEMA_OR_READ_FAILURE") from None
    finally:
        database.close()


def diff(local, gmgn):
    local_by_sig = {r["signature"] for r in local["trades"]}
    gmgn_trades = [r for r in gmgn if r["side"] in {"BUY", "SELL"}]
    gmgn_by_sig = {r["signature"] for r in gmgn_trades}
    rows = []
    for row in gmgn_trades:
        sig = row["signature"]
        linked = [x for x in local["trades"] if x["signature"] == sig]
        if sig not in local["signatures"]:
            finding = "NOT_IN_ROOT_SIGNATURE_INDEX"
        elif sig not in local_by_sig:
            finding = "IN_ROOT_NOT_CLASSIFIED_TRADE"
        elif any(x["mint"] == row["mint"] and (
                     x["side"] in {"BUY","ADD","REENTRY"} if row["side"] == "BUY"
                     else x["side"] in {"SELL","EXIT","SELL_POSITION_UNRESOLVED"})
                 for x in linked):
            finding = "MATCH_SIDE_MINT"
        else:
            finding = "MINT_OR_SIDE_DISAGREEMENT"
        rows.append({**row, "finding":finding})
    rows.sort(key=lambda x:(x["time"],x["signature"]))
    return {
        "gmgn_window_trades":len(gmgn_trades),
        "gmgn_unique_trade_signatures":len(gmgn_by_sig),
        "gmgn_buy_events":sum(r["side"]=="BUY" for r in gmgn_trades),
        "gmgn_sell_events":sum(r["side"]=="SELL" for r in gmgn_trades),
        "mission_root_signatures":len(local["signatures"]),
        "mission_classified_trade_rows":len(local["trades"]),
        "gmgn_signatures_missing_from_root":len(gmgn_by_sig-local["signatures"]),
        "gmgn_signatures_not_in_mission_trades":len(gmgn_by_sig-local_by_sig),
        "mission_trades_not_in_gmgn":len(local_by_sig-gmgn_by_sig),
        "findings":dict(Counter(r["finding"] for r in rows)),
        "gmgn_trade_events":rows,
        "mission_trade_unmatched": [
            x for x in local["trades"] if x["signature"] not in gmgn_by_sig
        ],
        "trades_onchain_confirmed_by_this_script":0,
    }


def write_report(output, body):
    if output.is_symlink() or "FrankMeme" in str(output) or "live-v1" in str(output):
        raise IncompleteEvidence("OUTPUT_DIR_UNSAFE")
    output.mkdir(parents=True,mode=0o700,exist_ok=True)
    if output.stat().st_mode & 0o077:
        raise IncompleteEvidence("OUTPUT_DIR_PERMISSIONS")
    name = "frank-gmgn-diff-" + datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f") + ".json"
    path = output / name
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,"w",encoding="utf-8") as writer:
        json.dump(body,writer,indent=2,ensure_ascii=False)
    return path


def audit(db_path, start, end, output_dir, wallet=ROOT_WALLET,
          cli_path=None, run=subprocess.run):
    if wallet != ROOT_WALLET:
        raise IncompleteEvidence("FRANK_WALLET_NOT_ATTESTED")
    if not (start < end <= int(datetime.now(timezone.utc).timestamp())):
        raise IncompleteEvidence("WINDOW_INVALID")
    local=local_window(db_path,start,end)
    try:
        gmgn,pages=collect_gmgn(wallet,start,end,cli_path=cli_path,run=run)
    except IncompleteEvidence as exc:
        return {
            "status":"GMGN_SOURCE_UNAVAILABLE",
            "gmgn_reason":str(exc),
            "start":start,"end":end,"wallet":wallet,
            "mission_root_signatures":len(local["signatures"]),
            "mission_trades":len(local["trades"]),
            "local_ledger_first_time":local["ledger_first_time"],
            "local_ledger_last_time":local["ledger_last_time"],
            "local_ledger_signature_count":local["ledger_signature_count"],
            "comparison_complete":False,"signals_changed":False,
            "production_db_writes":0,"emails_sent":0,
        }
    comparison=diff(local,gmgn)
    return {
        "status":"THIRD_PARTY_ACTIVITY_RECONCILED_REVIEW_ONLY",
        "comparison_complete":True,
        "wallet":wallet,"start":start,"end":end,
        "gmgn_pages_retrieved":pages,
        "local_ledger_first_time":local["ledger_first_time"],
        "local_ledger_last_time":local["ledger_last_time"],
        **comparison,
        "warning":"GMGN output is independently indexed THIRD_PARTY evidence, NOT confirmed onchain execution. Differences require original tx and signer/owner reconciliation; do not automatically add trade signals.",
        "signals_changed":False,"production_db_writes":0,"emails_sent":0,
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--db",type=Path,default=DEFAULT_DB)
    p.add_argument("--start",type=int,default=START)
    p.add_argument("--end",type=int,default=END)
    p.add_argument("--output-dir",type=Path,default=DEFAULT_OUTPUT)
    args=p.parse_args()
    try:
        report=audit(args.db,args.start,args.end,args.output_dir)
        output=write_report(args.output_dir,report)
        summary={k:v for k,v in report.items()
                 if k not in {"gmgn_trade_events","mission_trade_unmatched"}}
        summary["output"]=str(output)
        if report.get("comparison_complete"):
            summary["discrepancy_sample"]=[
                {"signature":x["signature"],"time":x["time"],
                 "mint":x["mint"],"side":x["side"],"finding":x["finding"]}
                for x in report["gmgn_trade_events"] if x["finding"]!="MATCH_SIDE_MINT"
            ][:25]
        print(json.dumps(summary,ensure_ascii=False,indent=2))
        return 0 if report.get("comparison_complete") else 2
    except (IncompleteEvidence,OSError) as exc:
        reason=str(exc) if isinstance(exc,IncompleteEvidence) else "LOCAL_SOURCE_ACCESS_FAILED"
        print(json.dumps({"status":"AUDIT_BLOCKED","reason":reason,
                          "production_db_writes":0,"emails_sent":0}))
        return 2


if __name__=="__main__":
    sys.exit(main())
