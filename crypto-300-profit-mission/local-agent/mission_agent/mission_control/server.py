"""Localhost-only Mission Meme V1 dashboard server."""
from __future__ import annotations

import ipaddress
import json
import mimetypes
import socket
import sqlite3
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from .db import open_control_ro
from .frank import FrankReader


def _host_is_loopback(host: str, port: int) -> bool:
    try:
        infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except socket.gaierror:
        return False
    if not infos:
        return False
    for _, _, _, _, sockaddr in infos:
        address = str(sockaddr[0]).split("%", 1)[0]
        try:
            if not ipaddress.ip_address(address).is_loopback:
                return False
        except ValueError:
            return False
    return True


def _host_header_is_loopback(value: str | None) -> bool:
    value = (value or "").strip().lower()
    if not value:
        return False
    if value.startswith("["):
        end = value.find("]")
        host = value[1:end] if end >= 0 else value
    else:
        host = value.rsplit(":", 1)[0] if ":" in value else value
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


class DashboardState:
    def __init__(self, production_root: Path, control_root: Path):
        self.frank = FrankReader(production_root)
        self.control_root = Path(control_root)
        self.control_db = self.control_root / "mission-control.sqlite"
        self.control_health = self.control_root / "mission-control-health.json"

    def _control_query(self, sql: str, params=()):
        if not self.control_db.is_file():
            return []
        db = open_control_ro(self.control_db)
        try:
            return [dict(row) for row in db.execute(sql, params).fetchall()]
        except sqlite3.DatabaseError:
            return []
        finally:
            db.close()

    def runtime(self):
        return self.frank.runtime()

    def mission_control_health(self):
        if not self.control_health.is_file():
            return {"status": "UNKNOWN", "reason": "MISSION_CONTROL_HEARTBEAT_MISSING"}
        try:
            return json.loads(self.control_health.read_text())
        except (OSError, ValueError):
            return {"status": "UNKNOWN", "reason": "MISSION_CONTROL_HEARTBEAT_UNREADABLE"}

    def candidates(self):
        candidates = self.frank.candidates()
        # candidate_latest is one mutable row per person/mint/episode, refreshed on
        # every evaluation. Immutable decision_events remain transition-only.
        latest = self._control_query(
            "SELECT person_id,mint,episode_id,decision,evaluated_at,body FROM candidate_latest ORDER BY evaluated_at DESC"
        )
        by_key = {(x["person_id"], x["mint"], x["episode_id"]): x for x in latest}
        seen = set()
        for item in candidates:
            key=(item["person_id"], item["mint"], item.get("episode_id"));seen.add(key)
            row = by_key.get(key)
            if row:
                body = json.loads(row["body"])
                item["decision"] = body["decision"]
                item["decision_created_at"] = row["evaluated_at"]
                item["metrics"] = body.get("metrics") or {}
                inputs = body.get("inputs") or {}
                item["decision_quote"] = inputs.get("quote") or {}
                item["reasons"] = body.get("reasons") or []
                item["missing"] = body.get("missing") or []
                item["invalidation"] = body.get("invalidation") or []
            else:
                item["decision"] = "UNASSESSED"
                item["metrics"] = {}
                item["decision_quote"] = {}
        # A SOL-normalized sidecar can legitimately create a follow candidate that
        # does not exist in the frozen production signal table. candidate_latest is
        # the canonical Mission Control view, so expose those rows without writing
        # anything back to Frank production.
        for key,row in by_key.items():
            if key in seen:
                continue
            body=json.loads(row["body"]);inputs=body.get("inputs") or {}
            item={k:inputs.get(k) for k in (
                "person_id","mint","episode_id","pattern","source_signal_id","source_signal_type","source_signal_at",
                "position_state","current_raw","buy_count","sell_count","latest_side","latest_signature","latest_at",
                "latest_buy_at","latest_buy_price_usdc","latest_buy_price_status","latest_buy_quote_asset",
                "latest_buy_quote_quantity","token_decimals"
            )}
            item.update({
                "decision":body["decision"],"decision_created_at":row["evaluated_at"],
                "metrics":body.get("metrics") or {},"decision_quote":inputs.get("quote") or {},
                "reasons":body.get("reasons") or [],"missing":body.get("missing") or [],
                "invalidation":body.get("invalidation") or [],"candidate_source":"MISSION_CONTROL_OVERLAY",
            })
            candidates.append(item)
        candidates.sort(key=lambda x:int(x.get("latest_at") or 0),reverse=True)
        return candidates

    def recent_trades(self):
        return self.frank.recent_trades(100)

    def decisions(self):
        rows = self._control_query("SELECT * FROM decision_events ORDER BY rowid DESC LIMIT 100")
        for row in rows:
            row["body"] = json.loads(row["body"])
        return rows


class Handler(BaseHTTPRequestHandler):
    state: DashboardState = None
    static_root: Path = Path(__file__).with_name("static")

    def log_message(self, *_):
        return

    def _allowed_host(self):
        return _host_header_is_loopback(self.headers.get("Host"))

    def _json(self, payload, status=200):
        data = json.dumps(payload, ensure_ascii=False, default=str).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _file(self, path: Path):
        if not path.is_file():
            self.send_error(404)
            return
        data = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mimetypes.guess_type(path.name)[0] or "application/octet-stream")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if not self._allowed_host():
            return self.send_error(421, "loopback Host required")
        path = urlparse(self.path).path
        if path == "/api/runtime":
            return self._json(self.state.runtime())
        if path == "/api/control-health":
            return self._json(self.state.mission_control_health())
        if path == "/api/candidates":
            return self._json(self.state.candidates())
        if path == "/api/trades":
            return self._json(self.state.recent_trades())
        if path == "/api/decisions":
            return self._json(self.state.decisions())
        if path in {"/", "/index.html"}:
            return self._file(self.static_root / "index.html")
        if path.startswith("/static/"):
            candidate = (self.static_root / path.removeprefix("/static/")).resolve()
            if self.static_root.resolve() not in candidate.parents:
                return self.send_error(403)
            return self._file(candidate)
        self.send_error(404)


class IPv6ThreadingHTTPServer(ThreadingHTTPServer):
    address_family = socket.AF_INET6


def serve(production_root: Path, control_root: Path, host: str = "127.0.0.1", port: int = 8765):
    if host not in {"127.0.0.1", "localhost", "::1"} or not _host_is_loopback(host, port):
        raise ValueError("MISSION_CONTROL_LOCALHOST_ONLY")
    Handler.state = DashboardState(production_root, control_root)
    server_cls = IPv6ThreadingHTTPServer if ":" in host else ThreadingHTTPServer
    server_cls((host, port), Handler).serve_forever()
