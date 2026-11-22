"""Offline actual-index audit for complete D1 ranges and pages.

Read an explicitly supplied private SQLite snapshot only. No RPC, listener,
source collection, notification, production database, or current-balance claim.
The underlying classifications are indexed facts, not independently revalidated
on-chain transactions. A multi-mint ledger audit is not CA end-to-end acceptance.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import time
from types import SimpleNamespace
from unittest.mock import patch
from urllib.parse import urlencode

sys.dont_write_bytecode = True
p = argparse.ArgumentParser(description=__doc__)
p.add_argument("--agent", type=Path, required=True)
p.add_argument("--expected-sha", required=True)
p.add_argument("--snapshot", type=Path, required=True)
p.add_argument("--as-of", type=int, required=True)
p.add_argument("--summary", type=Path, required=True)
a = p.parse_args()
assert a.snapshot.is_file() and not a.snapshot.is_symlink()
assert a.summary.resolve() != a.snapshot.resolve()
assert subprocess.check_output(["git", "-C", str(a.agent), "rev-parse", "HEAD"], text=True).strip() == a.expected_sha
assert not subprocess.check_output(["git", "-C", str(a.agent), "status", "--porcelain"], text=True).strip()
events = Counter()
def audit(event, args):
    if event.startswith("socket."):
        events[event] += 1
        raise AssertionError("OFFLINE_NO_SOCKET")
sys.addaudithook(audit)
sys.path.insert(0, str(a.agent))
from mission_agent.mission_control.wallet_activity import activity, MINT
from mission_agent.mission_control.wallet_activity_paging import activity_page
from mission_agent.mission_control import server

def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()

started = time.monotonic()
before = digest(a.snapshot)
db = sqlite3.connect(a.snapshot.resolve().as_uri()+"?mode=ro", uri=True)
db.execute("PRAGMA query_only=ON")
assert db.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
raw = db.execute("SELECT rowid,wallet,signature,block_time,body FROM signatures WHERE person_id=?",
                 ("frank",)).fetchall()
trades = db.execute("SELECT DISTINCT t.wallet,t.signature,t.mint,t.side FROM trades t "
                    "JOIN signatures s ON s.wallet=t.wallet AND s.signature=t.signature "
                    "WHERE s.person_id=?", ("frank",)).fetchall()
db.close()
legs = defaultdict(set)
for wallet, sig, mint, side in trades:
    legs[(wallet, sig)].add((mint, side))
expected_mints = defaultdict(set)
for rowid, wallet, sig, stamp, body in raw:
    if stamp is not None and stamp > a.as_of:
        continue
    try:
        obj = json.loads(body or "{}")
    except ValueError:
        obj = {}
    e = obj.get("evidence") if isinstance(obj, dict) else None
    deltas = e.get("token_balance_deltas") if isinstance(e, dict) else None
    if isinstance(deltas, list):
        for x in deltas:
            if (isinstance(x, dict) and x.get("wallet_owned") is True and x.get("owner") == wallet
                    and isinstance(x.get("mint"), str) and MINT.fullmatch(x["mint"])):
                expected_mints[x["mint"]].add((wallet, sig))
    for mint, side in legs[(wallet, sig)]:
        if isinstance(mint, str) and MINT.fullmatch(mint):
            expected_mints[mint].add((wallet, sig))

def pages(days, **filters):
    rows, cursor, count, total = [], None, 0, None
    while True:
        result = activity_page(a.snapshot, a.as_of, days, page_size=137, cursor=cursor, **filters)
        if total is None:
            total = result["total_signatures"]
        assert total == result["total_signatures"]
        assert not result["full_chain_verified"] and not result["immutable_source_snapshot"]
        rows += result["rows"]
        count += 1
        assert result["has_more"] == (result["next_cursor"] is not None)
        if not result["has_more"]:
            break
        cursor = result["next_cursor"]
    identities = [(r["wallet"], r["sig"]) for r in rows]
    assert len(identities) == len(set(identities)) == total
    return rows, count

windows = {}
for days in [1, 7, 30, "all"]:
    expected = {(w, s) for _, w, s, t, _ in raw
                if (t is None and days == "all") or
                (t is not None and t <= a.as_of and (days == "all" or t >= a.as_of-days*86400))}
    full = activity(a.snapshot, a.as_of, days)
    got, n = pages(days)
    assert {(r["wallet"], r["sig"]) for r in got} == expected
    assert {(r["wallet"], r["sig"]) for r in full["rows"]} == expected
    windows[str(days)] = {"signatures": len(got), "pages": n,
        "trade_legs": sum(len(r["trades"]) for r in got),
        "categories": dict(Counter(r["class"] for r in got))}
actual_trade_mints = sorted({mint for _, _, mint, _ in trades if isinstance(mint, str) and MINT.fullmatch(mint)})
mint_cases = []
for mint in actual_trade_mints:
    got, n = pages("all", mint=mint)
    assert {(r["wallet"], r["sig"]) for r in got} == expected_mints[mint]
    mint_cases.append({"mint_sha256": hashlib.sha256(mint.encode()).hexdigest(),
                       "signatures": len(got), "pages": n})
for kind in ["BUY", "SELL", "PASSIVE_TRANSFER", "FAILED_TX", "ATA_CREATE", "UNKNOWN_NEEDS_REVIEW"]:
    got, n = pages("all", kind=kind)
    if kind in {"BUY", "SELL"}:
        allowed = {"BUY", "ADD", "REENTRY"} if kind == "BUY" else {"SELL", "EXIT", "SELL_POSITION_UNRESOLVED"}
        assert all(r["class"] == "ACTIVE_TRADE" and any(t["side"] in allowed for t in r["trades"]) for r in got)
    else:
        assert all(r["class"] == kind for r in got)
state = server.DashboardState.__new__(server.DashboardState)
state.frank = SimpleNamespace(database=a.snapshot)
handler = server.Handler.__new__(server.Handler)
handler.state = state
handler._allowed_host = lambda: True
handler._json = lambda value, status=200: (value, status)
handler.path = "/api/frank-signed-activity?"+urlencode({"days":"all", "limit":137})
with patch.object(server.time, "time", return_value=a.as_of):
    response, code = handler.do_GET()
assert code == 200 and response["total_signatures"] == windows["all"]["signatures"]
assert before == digest(a.snapshot) and not events
result = {"source_sha": a.expected_sha, "snapshot_sha256": before, "as_of": a.as_of,
          "index_signature_rows": len(raw), "indexed_trade_mints": len(actual_trade_mints),
          "indexed_trade_rows": len(trades), "windows": windows,
          "actual_mint_filter_cases": mint_cases, "class_filter_cases": 6,
          "all_pages_no_duplicates_or_missing": True, "actual_handler_dispatch": "PASS",
          "underlying_chain_classification_revalidated": False,
          "ca_end_to_end_acceptance": "NOT_RUN_IN_THIS_INDEX_AUDIT",
          "full_chain_history_claimed": False, "snapshot_hash_unchanged": True,
          "socket_events": dict(events), "seconds": time.monotonic()-started,
          "verdict": "PASS_FOR_THIS_INDEXED_MULTI_MINT_BACKEND_AUDIT"}
a.summary.write_text(json.dumps(result, indent=2)+"\n")
print(json.dumps({k:v for k,v in result.items() if k != "actual_mint_filter_cases"}))

