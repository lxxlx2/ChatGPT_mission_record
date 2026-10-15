"""Explicitly started loopback-only F01/C02/F02 read-only query aggregator.

Reads existing GET endpoints ONLY, does not POST/start CA research, capture RPC,
open production SQLite, issue trades, serve a UI, or enable notification.
The browser/product integration is separately gated. No automatic refresh.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from http.client import HTTPConnection, HTTPException
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import math
from socket import timeout as SocketTimeout
import sys
import time
from urllib.parse import parse_qs, quote, urlsplit

from mission_agent.mission_control.frank_ca_f02_alignment import (
    align_frank_ca_f02,
)

_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
_SOURCE_LIMIT = 8 * 1024 * 1024


def valid_solana_mint(mint: str) -> bool:
    """Require canonical Base58 for exactly 32 bytes; never match by symbol."""
    if not isinstance(mint, str) or not 32 <= len(mint) <= 44:
        return False
    n = 0
    for c in mint:
        index = _ALPHABET.find(c)
        if index < 0:
            return False
        n = n * 58 + index
    leading = len(mint) - len(mint.lstrip("1"))
    decoded = b"\x00" * leading
    if n:
        decoded += n.to_bytes((n.bit_length() + 7) // 8, "big")
    return len(decoded) == 32 and (
        ("1" * leading + _encode_base58(n)) == mint)


def _encode_base58(value: int) -> str:
    encoded = ""
    while value:
        value, remainder = divmod(value, 58)
        encoded = _ALPHABET[remainder] + encoded
    return encoded


class _SourceUnavailable(Exception):
    """Opaque failure: never surface local transport/server credentials."""


def _existing_json(port: int, path: str, *, missing_allowed=False) -> dict | None:
    """GET read-only localhost only, no redirects, no proxy, bounded body/time."""
    conn = HTTPConnection("127.0.0.1", port, timeout=2.5)
    try:
        conn.request("GET", path, headers={"Accept": "application/json"})
        res = conn.getresponse()
        if res.status == 404 and missing_allowed:
            return None
        if res.status != 200:
            raise _SourceUnavailable()
        if res.getheader("Content-Type", "").split(";", 1)[0].strip() != "application/json":
            raise _SourceUnavailable()
        # Native F01/C02/F02 JSON APIs all send Content-Length. Accepting
        # close-delimited or truncated bytes can promote partial wire as an
        # authoritative BUY or CA report despite an early TCP EOF.
        declared = res.getheader("Content-Length")
        if (not isinstance(declared, str) or not declared
                or len(declared) > 12 or not declared.isascii()
                or not declared.isdecimal()):
            raise _SourceUnavailable()
        expected = int(declared)
        if expected <= 0 or expected > _SOURCE_LIMIT:
            raise _SourceUnavailable()
        raw = res.read(expected)
        if len(raw) != expected:
            raise _SourceUnavailable()
        result = json.loads(raw)
        if not isinstance(result, dict):
            raise _SourceUnavailable()
        return result
    except (OSError, SocketTimeout, HTTPException, UnicodeError, ValueError,
            OverflowError, json.JSONDecodeError) as exc:
        raise _SourceUnavailable() from exc
    finally:
        conn.close()


def _recent_f01(doc: dict) -> bool:
    # Native F01 contract is a partition, not merely {status, time}. A
    # missing or corrupted eligible list cannot mean a confirmed NO_BUY.
    eligible = doc.get("eligible")
    excluded = doc.get("not_followed")
    if (doc.get("status") != "OK"
            or type(doc.get("schema_version")) is not int
            or doc["schema_version"] != 1
            or doc.get("scope") != "FRANK_FROZEN_DECISIONS_PRESENTATION_ONLY"
            or not isinstance(eligible, list)
            or not isinstance(excluded, list)
            or type(doc.get("eligible_count")) is not int
            or type(doc.get("excluded_count")) is not int
            or doc["eligible_count"] != len(eligible)
            or doc["excluded_count"] != len(excluded)
            or any(not isinstance(row, dict) for row in eligible)
            or any(not isinstance(row, dict) for row in excluded)):
        return False
    stamp = doc.get("as_of_epoch")
    if isinstance(stamp, bool) or not isinstance(stamp, (int, float)):
        return False
    now = time.time()
    return math.isfinite(stamp) and -2 <= now - stamp <= 8


class JointReadOnly:
    def __init__(self, *, control_port: int, f02_port: int):
        if (type(control_port) is not int or type(f02_port) is not int
                or not 1 <= control_port <= 65535
                or not 1 <= f02_port <= 65535
                or control_port == f02_port):
            raise ValueError("JOINT_LOOPBACK_SOURCE_PORTS_INVALID")
        self.control_port = control_port
        self.f02_port = f02_port

    def query(self, mint: str) -> dict:
        if not valid_solana_mint(mint):
            raise ValueError("JOINT_INVALID_EXACT_SOLANA_MINT")
        status = {}
        follow = None
        ca_report = None
        f02 = None

        try:
            candidate = _existing_json(
                self.control_port, "/api/follow-opportunities")
            if candidate is not None and _recent_f01(candidate):
                follow = candidate
                status["f01"] = "SOURCE_READ"
            else:
                status["f01"] = "SOURCE_UNAVAILABLE"
        except _SourceUnavailable:
            status["f01"] = "SOURCE_UNAVAILABLE"

        try:
            ca_report = _existing_json(
                self.control_port,
                "/api/cluster-latest?mint=" + quote(mint, safe=""),
                missing_allowed=True)
            status["c02"] = ("ARCHIVED_REPORT_READ" if ca_report is not None
                             else "NOT_QUERIED")
        except _SourceUnavailable:
            ca_report = None
            status["c02"] = "SOURCE_UNAVAILABLE"

        try:
            f02 = _existing_json(
                self.f02_port, "/api/research/positions")
            status["f02"] = ("SOURCE_READ" if f02 is not None
                             else "SOURCE_UNAVAILABLE")
        except _SourceUnavailable:
            status["f02"] = "SOURCE_UNAVAILABLE"

        view = align_frank_ca_f02(
            mint=mint, follow=follow,
            ca_report=ca_report, f02_positions=f02)

        if status["f01"] != "SOURCE_READ":
            view["f01"].update({
                "status": "F01_SOURCE_UNAVAILABLE",
                "frozen_decision": None,
                "source_signal_id": None,
            })
        if status["c02"] == "SOURCE_UNAVAILABLE":
            view["c02"].update({
                "status": "CA_SOURCE_UNAVAILABLE",
                "exact_mint_label": None,
                "narrative_status": "UNVERIFIED",
            })
        if status["f02"] == "SOURCE_UNAVAILABLE":
            view["f02"].update({
                "state": "SOURCE_UNAVAILABLE",
                "observed_quantity": None,
                "token_account_count": None,
                "capture_observed_at_utc": None,
                "capture_sha256": None,
            })
        missing = any(x == "SOURCE_UNAVAILABLE" for x in status.values())
        return {
            "schema_version": 1,
            "kind": "FRANK_EXISTING_SOURCE_HTTP_ALIGNMENT",
            "as_of_utc": datetime.now(timezone.utc).isoformat(),
            "status": ("PARTIAL_SOURCES" if missing else
                       "CA_NOT_QUERIED" if status["c02"] == "NOT_QUERIED"
                       else "EXISTING_ARCHIVED_SOURCES_ONLY"),
            "upstream": status,
            "alignment": view,
            "ca_query_executed": False,
            "archive_is_live_wallet_portfolio": False,
            "combined_trade_permission": False,
            "writes_production_sqlite": False,
            "initiated_solana_rpc": False,
        }


def make_handler(service: JointReadOnly):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            # Do not leak wallet or CA path into local background service logs.
            pass

        def _json(self, code, body):
            raw = json.dumps(body, ensure_ascii=False, sort_keys=True,
                             allow_nan=False).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.send_header("Cache-Control", "no-store, max-age=0")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", "default-src 'none'")
            self.end_headers()
            self.wfile.write(raw)

        def do_GET(self):
            if self.headers.get("Host") != f"127.0.0.1:{self.server.server_port}":
                return self._json(421, {"status": "LOOPBACK_HOST_REQUIRED"})
            url = urlsplit(self.path)
            if url.path != "/api/research/alignment":
                return self._json(404, {"status": "NOT_FOUND"})
            args = parse_qs(url.query, keep_blank_values=True)
            if set(args) != {"mint"} or len(args["mint"]) != 1:
                return self._json(400, {"status": "EXACT_MINT_REQUIRED"})
            try:
                doc = service.query(args["mint"][0])
            except ValueError:
                return self._json(400, {"status": "INVALID_SOLANA_MINT"})
            except Exception:
                # Private local upstream failures must never expose traceback.
                return self._json(503, {"status": "JOINT_RESEARCH_SOURCE_UNAVAILABLE"})
            return self._json(200, doc)

        def do_POST(self):
            self._json(405, {"status": "READ_ONLY_GET_ONLY"})

    return Handler


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--serve", action="store_true")
    mode.add_argument("--probe-once", action="store_true")
    parser.add_argument("--mint")
    parser.add_argument("--control-port", type=int)
    parser.add_argument("--f02-port", type=int)
    parser.add_argument("--listen-port", type=int, default=18777)
    args = parser.parse_args(argv)
    if not args.serve and not args.probe_once:
        print(json.dumps({"status": "PLAN_ONLY", "network_invoked": False,
                          "server_started": False, "ca_query_executed": False}))
        return 0
    if args.control_port is None or args.f02_port is None:
        parser.error("--control-port and --f02-port required")
    if args.serve and args.mint:
        parser.error("--mint only valid with --probe-once")
    if args.probe_once and not args.mint:
        parser.error("--probe-once requires --mint")
    if args.listen_port < 1024 or args.listen_port > 65535:
        parser.error("--listen-port must be 1024..65535")
    try:
        service = JointReadOnly(control_port=args.control_port,
                                f02_port=args.f02_port)
    except ValueError:
        parser.error("invalid source ports")
    if args.probe_once:
        try:
            print(json.dumps(service.query(args.mint),
                             ensure_ascii=False, sort_keys=True))
            return 0
        except ValueError:
            print("JOINT_INVALID_EXACT_SOLANA_MINT", file=sys.stderr)
            return 1
    server = ThreadingHTTPServer(("127.0.0.1", args.listen_port),
                                 make_handler(service))
    try:
        print(json.dumps({"status": "JOINT_LOOPBACK_READONLY_READY",
                          "host": "127.0.0.1", "port": server.server_port,
                          "route": "/api/research/alignment",
                          "writes_production_sqlite": False}), flush=True)
        server.serve_forever()
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
