#!/usr/bin/env python3
"""Read-only Frank live funnel from EXISTING Mac localhost GET APIs.

No wallet scan, RPC, SQLite access, production mutation, orders, Gmail, or
backend SHA claim. ZIP holds aggregates only, not source response bodies.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from http.client import HTTPConnection, HTTPException
from pathlib import Path
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from uuid import uuid4
import zipfile

ENDPOINTS = ("/api/runtime", "/api/control-health", "/api/coverage",
             "/api/candidates", "/api/frank-observed-watchlist",
             "/api/follow-opportunities")
MAX_BODY = 2_000_000
KNOWN_REASONS = frozenset((
    "NOT_APPROVED_FRANK_SCOPE", "NOT_FROZEN_FRANK_SOURCE", "FRANK_RUNTIME_NOT_LIVE",
    "NOT_ACTIONABLE_DECISION", "MODEL_POSITION_NOT_OPEN", "LATEST_ACTION_NOT_BUY",
    "MODEL_INVENTORY_UNKNOWN_OR_ZERO", "SOURCE_SIGNAL_UNVERIFIED", "FRANK_BUY_STALE",
    "DECISION_STALE", "QUOTE_NOT_EXECUTABLE", "QUOTE_STALE",
    "POLICY_OR_SOURCE_UNAVAILABLE",
))
KNOWN_DECISIONS = frozenset(("BUY", "SMALL_BUY", "WAIT", "NO_BUY", "UNASSESSED"))
KNOWN_STATES = frozenset(("OPEN", "CLOSED", "INVENTORY_UNDETERMINED"))
KNOWN_SIDES = frozenset(("BUY", "ADD", "REENTRY", "SELL", "EXIT", "SELL_POSITION_UNRESOLVED"))
KNOWN_WATCH = frozenset(("MODEL_OPEN", "NEEDS_INVENTORY_REVIEW", "HISTORICAL_EXIT",
                         "WATCH_UNRESOLVED", "HISTORY_SELL_ONLY", "MODEL_STATE_ONLY",
                         "PASSIVE_RECEIPT_ONLY", "OTHER_ACCOUNT_ACTIVITY"))
KNOWN_RUNTIME = frozenset(("LIVE", "OFFLINE", "DEGRADED", "UNKNOWN"))
KNOWN_API_STATUS = frozenset(("OK", "RUNTIME_UNAVAILABLE", "POLICY_OR_SOURCE_UNAVAILABLE",
                              "SOURCE_UNAVAILABLE", "UNAVAILABLE"))


def _label(value, approved):
    return value if isinstance(value, str) and value in approved else "OTHER_OR_UNKNOWN"


def _counts(rows, key, names):
    return dict(sorted(Counter(_label(x.get(key), names) for x in rows
                               if isinstance(x, dict)).items()))


def _age(value, now):
    if isinstance(value, bool) or value is None:
        return None
    try:
        if isinstance(value, str) and "T" in value:
            stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if stamp.tzinfo is None:
                return None
            stamp = stamp.timestamp()
        else:
            stamp = float(value)
        if not 0 < stamp < now + 30:
            return None
        return round(max(0.0, now - stamp), 1)
    except (ValueError, TypeError, OverflowError):
        return None


def dashboard_port(home: Path) -> int:
    support = home / "Library/Application Support/FrankMeme"
    options = []
    runner = support / "dashboard.sh"
    if runner.is_file() and not runner.is_symlink() and runner.stat().st_size < 50000:
        match = re.search(r'^LOCAL_AGENT="([^"]+)"\s*$',
                          runner.read_text(encoding="utf-8"), re.M)
        if match:
            options.append(Path(match.group(1)).expanduser()
                           / "mission_agent/mission_control/dashboard.port")
    options.append(support / "dashboard_port")
    for candidate in options:
        if candidate.is_symlink() or not candidate.is_file() or candidate.stat().st_size > 8:
            continue
        raw = candidate.read_text(encoding="ascii").strip()
        if raw.isdecimal() and 1024 <= int(raw) <= 65535:
            return int(raw)
    raise RuntimeError("EXISTING_LOCAL_DASHBOARD_PORT_NOT_FOUND")


def get_json(port: int, path: str) -> tuple[dict, object | None]:
    if path not in ENDPOINTS or not 1024 <= port <= 65535:
        raise ValueError("INVALID_GET_TARGET")
    start = time.monotonic()
    conn = HTTPConnection("127.0.0.1", port, timeout=3.0)
    try:
        conn.request("GET", path, headers={"Accept": "application/json",
                                           "Connection": "close"})
        res = conn.getresponse()
        info = {"http_status": res.status,
                "elapsed_ms": round((time.monotonic() - start) * 1000, 1)}
        if res.status != 200:
            info["result"] = ("ROUTE_NOT_AVAILABLE" if res.status == 404
                              else "HTTP_NON_200")
            return info, None
        content_type = (res.getheader("Content-Type") or "").split(";", 1)[0].strip().lower()
        size = res.getheader("Content-Length")
        if content_type != "application/json" or not size or not size.isascii() or not size.isdecimal():
            info["result"] = "INVALID_JSON_WIRE_METADATA"
            return info, None
        n = int(size)
        if not 0 < n <= MAX_BODY:
            info["result"] = "BODY_SIZE_OUT_OF_BOUND"
            return info, None
        body = res.read(n)
        if len(body) != n or res.read(1):
            info["result"] = "TRUNCATED_OR_OVERLONG_HTTP_BODY"
            return info, None
        document = json.loads(body)
        if not isinstance(document, (dict, list)):
            info["result"] = "UNEXPECTED_JSON_TYPE"
            return info, None
        info["result"] = "READ_ONLY_JSON_OK"
        info["bytes_read"] = n
        return info, document
    except (OSError, ValueError, UnicodeError, HTTPException, OverflowError, json.JSONDecodeError):
        return {"http_status": None, "elapsed_ms": round((time.monotonic() - start) * 1000, 1),
                "result": "LOCAL_GET_READ_FAILED"}, None
    finally:
        conn.close()


def _positive_int(v):
    return v if isinstance(v, int) and not isinstance(v, bool) and 0 <= v <= 100_000_000 else None


def summarize(path: str, source: object, now: float) -> dict:
    if path == "/api/runtime":
        if not isinstance(source, dict):
            return {"shape": "INVALID"}
        heartbeat = source.get("heartbeat_age_seconds")
        return {"status": _label(source.get("status"), KNOWN_RUNTIME),
                "heartbeat_age_seconds": round(float(heartbeat), 1)
                    if type(heartbeat) in (int, float) and 0 <= heartbeat < 86400 else None,
                "pid_alive": source.get("pid_alive")
                    if type(source.get("pid_alive")) is bool else None,
                "production_db_readable": source.get("production_db_readable")
                    if type(source.get("production_db_readable")) is bool else None,
                "source_drift": source.get("source_drift")
                    if type(source.get("source_drift")) is bool else None}
    if path == "/api/control-health":
        if not isinstance(source, dict):
            return {"shape": "INVALID"}
        return {"schema": "DICT_PRESENT", "source_entries": len(source)}
    if path == "/api/coverage":
        if not isinstance(source, dict):
            return {"shape": "INVALID"}
        windows = {}
        for window in ("24h", "7d", "30d"):
            w = (source.get("windows") or {}).get(window) or {}
            if not isinstance(w, dict):
                w = {}
            windows[window] = {k: _positive_int(w.get(k)) for k in (
                "indexed_signatures", "recognized_trades", "recognized_buys",
                "recognized_sells", "unknown_needs_review")}
        return {"status": _label(source.get("status"), KNOWN_API_STATUS),
                "scope": "LOCAL_INDEX_ONLY_NOT_FULL_CHAIN",
                "chain_completeness_verified": False,
                "latest_indexed_age_seconds": _age(source.get("latest_indexed_block_time"), now),
                "windows": windows}
    if path == "/api/candidates":
        if not isinstance(source, list):
            return {"shape": "INVALID"}
        rows = [x for x in source if isinstance(x, dict)]
        return {"rows": len(source), "valid_rows": len(rows),
                "stored_decision_labels_NOT_CURRENT_BUY": _counts(rows, "decision", KNOWN_DECISIONS),
                "model_position_states_NOT_CHAIN_BALANCE": _counts(rows, "position_state", KNOWN_STATES),
                "latest_model_sides": _counts(rows, "latest_side", KNOWN_SIDES),
                "latest_candidate_action_age_seconds": min(
                    (v for v in (_age(x.get("latest_at"), now) for x in rows)
                     if v is not None), default=None)}
    if path == "/api/frank-observed-watchlist":
        if not isinstance(source, dict):
            return {"shape": "INVALID"}
        rows = source.get("rows")
        if not isinstance(rows, list):
            rows = []
        snapshot = source.get("snapshot_status")
        return {"status": _label(source.get("status"), KNOWN_API_STATUS),
                "scope": "LOCAL_INDEX_ONLY_NOT_COMPLETE_CHAIN",
                "chain_completeness_verified": False,
                "rows": len(rows), "watch_state_counts": _counts(rows, "watch_state", KNOWN_WATCH),
                "snapshot_present": snapshot != "SNAPSHOT_NOT_PRESENT"
                    if isinstance(snapshot, str) else None}
    if path == "/api/follow-opportunities":
        if not isinstance(source, dict):
            return {"shape": "INVALID"}
        eligible, excluded = source.get("eligible"), source.get("not_followed")
        if not isinstance(eligible, list) or not isinstance(excluded, list):
            return {"shape": "INVALID_F01_LISTS"}
        return {"status": _label(source.get("status"), KNOWN_API_STATUS),
                "scope": "F01_PRESENTATION_ONLY_NOT_TRADE_AUTHORIZATION",
                "eligible_count_reported": _positive_int(source.get("eligible_count")),
                "eligible_rows": len(eligible),
                "excluded_count_reported": _positive_int(source.get("excluded_count")),
                "excluded_rows": len(excluded),
                "exclusion_reasons": _counts(excluded, "exclusion_reason", KNOWN_REASONS),
                "as_of_age_seconds": _age(source.get("as_of_epoch"), now)}
    raise ValueError("UNRECOGNIZED_LOCAL_ENDPOINT")


def sample(port: int, now: float | None = None) -> dict:
    now = time.time() if now is None else now
    endpoints = {}
    for path in ENDPOINTS:
        info, data = get_json(port, path)
        if data is not None:
            info["aggregate"] = summarize(path, data, now)
        endpoints[path] = info
    f01 = endpoints["/api/follow-opportunities"]
    classification = ("F01_ROUTE_NOT_INSTALLED_IN_RUNNING_BACKEND"
                      if f01.get("http_status") == 404 else
                      "F01_SOURCE_READ_OK_ELIGIBILITY_NOT_TRADE_AUTHORIZATION"
                      if f01.get("result") == "READ_ONLY_JSON_OK" else
                      "F01_SOURCE_UNAVAILABLE_OR_UNVERIFIED")
    return {"observed_at_utc": datetime.fromtimestamp(now, timezone.utc).isoformat(),
            "local_f01_interface": classification, "endpoints": endpoints}


def bundle(report: dict, output: Path) -> None:
    """Atomic no-clobber private aggregate ZIP, never raw API JSON."""
    payload = json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8")
    if len(payload) > 120_000:
        raise RuntimeError("AGGREGATE_OUT_OF_BOUND")
    output.parent.mkdir(exist_ok=True, parents=True)
    with tempfile.TemporaryDirectory(dir=output.parent, prefix=".frank-funnel-bundle-") as root:
        temp = Path(root) / "staging.zip"
        with zipfile.ZipFile(temp, "x", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("frank-live-funnel-summary.json", payload)
        with zipfile.ZipFile(temp) as check:
            if check.namelist() != ["frank-live-funnel-summary.json"] or check.testzip() is not None:
                raise RuntimeError("ZIP_SELF_CHECK_FAILED")
        os.link(temp, output)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples", type=int, default=2)
    parser.add_argument("--interval-seconds", type=float, default=6.0)
    args = parser.parse_args(argv)
    if not 1 <= args.samples <= 3 or not 0 <= args.interval_seconds <= 10:
        parser.error("samples=1..3 and interval=0..10 only")
    try:
        port = dashboard_port(Path.home())
    except (OSError, ValueError, UnicodeError, RuntimeError):
        print("FRANK_LOCAL_DASHBOARD_PORT_UNAVAILABLE", flush=True)
        return 2
    report = {"kind": "FRANK_READ_ONLY_LIVE_FUNNEL_V1",
              "source": "EXISTING_MAC_LOCALHOST_GET",
              "production_backend_sha": "UNVERIFIED",
              "full_chain_coverage_verified": False, "automated_trading_authorized": False,
              "new_rpc": False, "new_scan": False, "sqlite_opened": False,
              "production_writes": False, "gmail_sent": False, "samples": []}
    for index in range(args.samples):
        if index:
            time.sleep(args.interval_seconds)
        report["samples"].append(sample(port))
    output = Path.home() / "Downloads" / (
        "frank-live-funnel-" + datetime.now().strftime("%Y%m%d-%H%M%S")
        + "-" + uuid4().hex[:10] + ".zip")
    bundle(report, output)
    for idx, record in enumerate(report["samples"], 1):
        stats = record["endpoints"].get("/api/candidates", {}).get("aggregate", {})
        cov = record["endpoints"].get("/api/coverage", {}).get("aggregate", {})
        count = cov.get("windows", {}).get("24h", {}).get("indexed_signatures", "UNAVAILABLE")
        print(f"FRANK_SAMPLE_{idx}=F01:{record['local_f01_interface']} "
              f"CANDIDATES:{stats.get('rows', 'UNAVAILABLE')} 24H_INDEXED:{count}", flush=True)
    print("ZIP_READY=" + str(output), flush=True)
    if sys.platform == "darwin":
        try:
            subprocess.run(["open", "-R", str(output)], check=False, timeout=8)
        except (OSError, subprocess.SubprocessError):
            pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
