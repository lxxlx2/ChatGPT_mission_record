"""Localhost-only Mission Meme V1 dashboard server."""
from __future__ import annotations

import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from .db import open_control_ro
from .frank import FrankReader


class DashboardState:
    def __init__(self, production_root: Path, control_root: Path):
        self.frank = FrankReader(production_root)
        self.control_db = Path(control_root) / "mission-control.sqlite"

    def _control_query(self, sql: str, params=()):
        if not self.control_db.is_file():
            return []
        db = open_control_ro(self.control_db)
        try:
            return [dict(row) for row in db.execute(sql, params).fetchall()]
        finally:
            db.close()

    def runtime(self):
        return self.frank.runtime()

    def candidates(self):
        candidates = self.frank.candidates()
        snapshots = self._control_query(
            "SELECT s.* FROM decision_snapshots s JOIN (SELECT person_id,mint,episode_id,MAX(rowid) AS rid FROM decision_snapshots GROUP BY person_id,mint,episode_id) x ON s.rowid=x.rid ORDER BY s.rowid DESC"
        )
        by_key = {(x["person_id"], x["mint"], x["episode_id"]): x for x in snapshots}
        for item in candidates:
            snapshot = by_key.get((item["person_id"], item["mint"], item.get("episode_id")))
            if snapshot:
                body = json.loads(snapshot["body"])
                item["decision"] = body["decision"]
                item["decision_created_at"] = body["created_at"]
                item["metrics"] = body.get("metrics") or {}
                item["reasons"] = body.get("reasons") or []
                item["missing"] = body.get("missing") or []
                item["invalidation"] = body.get("invalidation") or []
            else:
                item["decision"] = "UNASSESSED"
                item["metrics"] = {}
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
        path = urlparse(self.path).path
        if path == "/api/runtime":
            return self._json(self.state.runtime())
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


def serve(production_root: Path, control_root: Path, host: str = "127.0.0.1", port: int = 8765):
    if host not in {"127.0.0.1", "localhost", "::1"}:
        raise ValueError("MISSION_CONTROL_LOCALHOST_ONLY")
    Handler.state = DashboardState(production_root, control_root)
    ThreadingHTTPServer((host, port), Handler).serve_forever()
